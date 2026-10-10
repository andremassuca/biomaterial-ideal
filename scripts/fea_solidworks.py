"""Confirmação independente da FEA da haste femoral em SOLIDWORKS Simulation (API COM, pywin32).

Uso (arranca uma instância própria do SolidWorks e fecha-a no fim):
    python scripts/fea_solidworks.py anatomico      # tentativa com o fémur anatómico FJ3365 (malha STL como sólido)
    python scripts/fea_solidworks.py geometria      # fémur simplificado, intacto e com a haste (design/cad/fea/)
    python scripts/fea_solidworks.py estudos [--malhas 5,3.5]   # estudos estáticos, energias e imagens
    python scripts/fea_solidworks.py tudo

O que faz: constrói um fémur simplificado (cortical e trabecular, cotas em design/cad/cotas_femur_fea.md) no mesmo
referencial da haste Corail tamanho 8 (design/cad/haste_femoral.SLDPRT), faz o corte do colo e a cavidade da
haste, cria um estudo estático por material da haste (e o fémur intacto como referência), com a carga da marcha
(Heller et al. 2005, a partir de Bergmann et al. 2001) e encastramento distal, e soma a energia de deformação do
osso nas zonas de Gruen. Hipóteses e fontes: docs/FEA_HASTE_SW.md. Resumo: results/fea_haste_sw.md.

As funções puras (cotas, perfis, cargas, zonas, somas) estão separadas das que falam com o SolidWorks e têm testes
em tests/test_fea_solidworks.py. Medidas em mm nas funções puras; a API de modelação usa metros.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import logging
import math
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
COTAS_FEMUR = RAIZ / "design" / "cad" / "cotas_femur_fea.md"
HASTE = RAIZ / "design" / "cad" / "haste_femoral.SLDPRT"
PASTA_FEA = RAIZ / "design" / "cad" / "fea"
PASTA_FIG = RAIZ / "results" / "figures" / "fea_sw"
RESULTADOS = RAIZ / "results" / "fea_haste_sw.json"
FEMUR_OBJ = Path(r"recursos\bodyparts3d\obj\FJ3365.obj")

_spec = importlib.util.spec_from_file_location("cad_solidworks", RAIZ / "scripts" / "cad_solidworks.py")
cad = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cad)

PESO_KG = 75.0  # peso corporal de desenho
G = 9.81

# Heller et al. 2005 (J Biomech 38:1155-1163, doi:10.1016/j.jbiomech.2004.05.022), caso da marcha, em % do peso
# corporal, no referencial do fémur de Bergmann/Heller (x medial, y anterior, z superior). Valores lidos na
# reprodução de Baharuddin et al. 2014 (BMC Musculoskelet Disord 15:30, doi:10.1186/1471-2474-15-30, Tabela 3,
# em N para 700 N); o original não foi lido: [confirmar].
# Resto do caso da marcha de Heller 2005 (mesma fonte e mesmo referencial), usado só na análise de sensibilidade:
# tensor da fáscia lata (partes proximal e distal) e vasto lateral.
HELLER_MARCHA_RESTO_PCT_BW = {
    "tensor_fascia_lata_proximal": (7.2, 11.6, 13.2),
    "tensor_fascia_lata_distal": (-0.5, -0.7, -19.0),
    "vasto_lateral": (-0.9, 18.5, -92.9),
}
HELLER_MARCHA_PCT_BW = {
    "contacto_anca": (-54.0, -32.8, -229.2),
    "abdutores": (58.0, 4.3, 86.5),
}

# Osso (elástico linear e isotrópico). Li Y et al. Materials 2014;7:1709, doi:10.3390/ma7031709 (texto completo
# lido a 8 out 2026): Tabela 2, fémur, compressão: E = 17,6 GPa; Tabela 3, fémur (osso esponjoso): E = 0,39 GPa.
# Coeficiente de Poisson 0,3 para osso e implantes, como em Li et al., Int J Surg 2024;110(1):296-305,
# doi:10.1097/js9.0000000000000810 (hipótese de modelação de outro estudo, não medição).
OSSO = {
    "Osso cortical": {"E_GPa": 17.6, "nu": 0.3},
    "Osso trabecular": {"E_GPa": 0.39, "nu": 0.3},
}
MATERIAIS_HASTE = ["Aço inox 316L", "Co-Cr-Mo forjado", "Ti-6Al-4V ELI", "Ti-6Al-4V poroso"]
E_TI_POROSO_GPA = 17.0  # valor de desenho (haste isoelástica hipotética)
NU_METAL = 0.3  # ver a nota de OSSO; A verificar para cada liga

log = logging.getLogger("fea_sw")


# ---------------------------------------------------------------- funções puras (testadas)

def ler_cotas_femur(caminho: Path = COTAS_FEMUR) -> dict[str, float]:
    """Lê as cotas do fémur simplificado (mesma tabela em Markdown que design/cad/cotas.md).

    Em linguagem simples: reaproveita o leitor de cotas da haste e devolve chave → número.
    """
    return cad.ler_cotas(caminho)


def geometria_colo(cf: dict, ch: dict) -> dict:
    """Centro da cabeça, direção do colo e ponto onde o eixo do colo cruza o eixo da diáfise.

    Em linguagem simples: o colo do fémur sai do eixo da diáfise para o lado medial (x negativo) com o ângulo
    cervicodiafisário; a cabeça fica no centro dado pelas cotas (o mesmo da cabeça da haste). Devolve também a
    base do colo da haste (ch, cotas da haste), por onde passa o corte do colo.
    """
    a = math.radians(180 - cf["colo_ccd"])
    d = (-math.sin(a), math.cos(a))
    centro = (-cf["cabeca_offset"], cf["cabeca_altura"])
    t = cf["cabeca_offset"] / math.sin(a)
    p0 = (centro[0] - t * d[0], centro[1] - t * d[1])
    base_haste = cad.eixo_colo(ch)["base"]
    return {"direcao": d, "centro": centro, "p0": p0, "base_haste": base_haste, "inclinacao": a}


def perfil_exterior(cf: dict) -> list[tuple[float, float]]:
    """Pares (y, raio) da superfície exterior da diáfise e da metáfise, de baixo para cima.

    Em linguagem simples: um tubo do raio da diáfise que alarga, entre y = 40 e 105 mm, até ao raio da metáfise
    (transição de desenho) e acaba em y = 120 mm.
    """
    rd, rm = cf["diafise_raio"], cf["metafise_raio"]
    return [(cf["fixacao_y"], rd), (40.0, rd), (60.0, rd + 2.0), (75.0, rd + 4.5), (90.0, rm - 2.0),
            (105.0, rm), (120.0, rm)]


def perfil_interior(cf: dict, y0: float) -> list[tuple[float, float]]:
    """Pares (y, raio) da superfície interior da cortical (canal e metáfise), a partir da altura y0.

    Em linguagem simples: o canal tem o raio do istmo até à ponta da haste (y = 0) e depois alarga até deixar uma
    cortical da espessura de desenho na metáfise; acaba 3 mm abaixo do topo da metáfise (y = 120 mm). Com este
    perfil a haste fica toda dentro do osso trabecular, com pelo menos 2 mm de folga (ver o teste), o que evita
    superfícies quase tangentes, que fazem falhar as operações booleanas do SolidWorks.
    """
    ext = dict(perfil_exterior(cf))
    tm = cf["cortical_metafise"]
    pts = [(y0, cf["canal_raio"]), (0.0, cf["canal_raio"]), (50.0, 11.0), (75.0, ext[75.0] - tm),
           (90.0, ext[90.0] - tm), (105.0, ext[105.0] - tm), (120.0 - tm, ext[120.0] - tm)]
    return [p for p in pts if p[0] >= y0]


def poligono_offset(pts: list[tuple[float, float]], t: float) -> list[tuple[float, float]]:
    """Polígono convexo (anti-horário) deslocado para dentro de t mm em todas as arestas.

    Em linguagem simples: empurra cada aresta para dentro, paralela a si própria, e o novo vértice é o cruzamento
    das duas arestas vizinhas. Serve para a superfície interior da cortical do grande trocânter.
    """
    n = len(pts)
    linhas = []
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy)
        nx, ny = -dy / L, dx / L  # normal para dentro num polígono anti-horário
        linhas.append(((x0 + t * nx, y0 + t * ny), (dx, dy)))
    out = []
    for i in range(n):
        (p, u), (q, v) = linhas[i - 1], linhas[i]
        det = u[0] * (-v[1]) - u[1] * (-v[0])
        s = ((q[0] - p[0]) * (-v[1]) - (q[1] - p[1]) * (-v[0])) / det
        out.append((p[0] + s * u[0], p[1] + s * u[1]))
    return out


def poligono_trocanter(cf: dict) -> list[tuple[float, float]]:
    """Contorno do grande trocânter visto de frente (lado lateral, x positivo), anti-horário.

    Em linguagem simples: um bloco de cantos cortados que vai da fossa trocantérica (x = limite do corte do colo)
    até à distância lateral medida e sobe até ao topo medido; valores intermédios de desenho.
    """
    xl, xm, top = cf["trocanter_lateral"], cf["osteotomia_lateral"], cf["trocanter_topo"]
    return [(xm, 95.0), (xl - 3.0, 98.0), (xl, 112.0), (xl - 2.0, 126.0), (xl - 7.0, top), (xm + 6.0, top),
            (xm, top - 8.0)]


def y_corte_colo(x: float, geo: dict) -> float:
    """Altura do plano do corte do colo na abcissa x (o plano é perpendicular ao eixo do colo).

    Em linguagem simples: o corte passa pela base do colo da haste e faz com a horizontal o ângulo de inclinação
    do colo; para cada x devolve a altura y da linha de corte.
    """
    bx, by = geo["base_haste"]
    return by + (x - bx) * math.tan(geo["inclinacao"])


def poligono_osteotomia(cf: dict, geo: dict) -> list[tuple[float, float]]:
    """Região retirada pelo corte do colo, vista de frente: acima da linha de corte e medial à fossa trocantérica.

    Em linguagem simples: tudo o que fica por cima da linha de corte, do lado medial até x = osteotomia_lateral,
    sai (cabeça e colo); o grande trocânter, mais lateral, fica.
    """
    xm = cf["osteotomia_lateral"]
    return [(-90.0, y_corte_colo(-90.0, geo)), (xm, y_corte_colo(xm, geo)), (xm, 250.0), (-90.0, 250.0)]


def removido_pelo_corte(x: float, y: float, cf: dict, geo: dict) -> bool:
    """Diz se o ponto (x, y) do plano frontal fica na região retirada pelo corte do colo."""
    return x < cf["osteotomia_lateral"] and y > y_corte_colo(x, geo)


def zona_gruen(x: float, y: float, comprimento_haste: float, cf: dict, geo: dict) -> int | None:
    """Zona de Gruen (1 a 7) de um ponto do osso, ou None se não pertencer a nenhuma.

    Em linguagem simples: como em Gruen et al. 1979 (radiografia anteroposterior), o osso à volta da haste divide-se
    em terços do comprimento da haste: lateral 1 (proximal), 2, 3; 4 abaixo da ponta; medial 5, 6, 7 (proximal,
    o calcar). Aqui: lateral é x > 0 (eixo da haste), o terço proximal vai de 2/3 do comprimento até ao corte do
    colo (e inclui o grande trocânter), e a zona 4 vai da ponta até 20 mm abaixo (valor de desenho). Os pontos
    acima do corte do colo (cabeça e colo do fémur intacto) não contam, para o intacto e o implantado serem
    comparados na mesma região.
    """
    if removido_pelo_corte(x, y, cf, geo):
        return None
    L = comprimento_haste
    if y < -20.0:
        return None
    if y < 0.0:
        return 4
    terco = 0 if y < L / 3 else (1 if y < 2 * L / 3 else 2)
    if x > 0:
        return (3, 2, 1)[terco]
    return (5, 6, 7)[terco]


def forcas_marcha(peso_kg: float = PESO_KG, completo: bool = False) -> dict[str, tuple[float, float, float]]:
    """Forças da marcha (N) no referencial do modelo: x lateral, y superior, z anterior (fémur esquerdo).

    Em linguagem simples: converte as percentagens do peso corporal de Heller et al. 2005 em newtons e troca os
    eixos: x de Heller (medial) passa a -x do modelo (o modelo tem o lado medial em x negativo), z de Heller
    (superior) passa a y, e y de Heller (anterior) passa a z.
    """
    bw = peso_kg * G
    tabela = dict(HELLER_MARCHA_PCT_BW, **(HELLER_MARCHA_RESTO_PCT_BW if completo else {}))
    return {k: (-v[0] / 100 * bw, v[2] / 100 * bw, v[1] / 100 * bw) for k, v in tabela.items()}


def ler_modulos_haste(caminho: Path = RAIZ / "data" / "materiais.csv") -> dict[str, float]:
    """Módulo de Young típico (GPa) de cada material da haste, da coluna "tipico" de data/materiais.csv.

    Em linguagem simples: procura as linhas da haste femoral com o módulo de Young e junta o Ti-6Al-4V poroso
    com o valor de desenho de 17 GPa.
    """
    out = {}
    with open(caminho, encoding="utf-8") as fh:
        for linha in csv.DictReader(fh):
            if linha["componente"] == "Haste femoral" and linha["propriedade"] == "Módulo de Young":
                out[linha["material"]] = float(linha["tipico"])
    out["Ti-6Al-4V poroso"] = E_TI_POROSO_GPA
    return {m: out[m] for m in MATERIAIS_HASTE}


def somar_por_zona(elementos: list[tuple[float, float, float]], comprimento_haste: float, cf: dict,
                   geo: dict) -> dict[int, dict[str, float]]:
    """Soma, por zona de Gruen, a energia dos elementos do osso e conta-os.

    Em linguagem simples: cada elemento vem como (x, y, energia) com x e y do centro do elemento (mm) e a energia
    de deformação do elemento (J); o resultado é, por zona, a energia total e o número de elementos.
    """
    zonas: dict[int, dict[str, float]] = {z: {"energia_J": 0.0, "n": 0} for z in range(1, 8)}
    for x, y, e in elementos:
        z = zona_gruen(x, y, comprimento_haste, cf, geo)
        if z is not None:
            zonas[z]["energia_J"] += e
            zonas[z]["n"] += 1
    return zonas


def razao_ao_intacto(zonas: dict, zonas_intacto: dict) -> dict[int, float]:
    """Energia de cada zona a dividir pela do fémur intacto (1 = igual; abaixo de 1 = menos carga no osso).

    Em linguagem simples: mede o efeito de blindagem de tensões (stress shielding) em cada zona.
    """
    return {z: (zonas[z]["energia_J"] / zonas_intacto[z]["energia_J"]) if zonas_intacto[z]["energia_J"] else
            float("nan") for z in zonas}


def pares_id_valor(vals) -> list[tuple[int, float]]:
    """Separa o vetor [id, valor, id, valor, ...] devolvido pela Simulation em pares (id do elemento, valor)."""
    vals = list(vals)
    if len(vals) % 2:
        raise ValueError("número ímpar de valores")
    return [(int(vals[i]), float(vals[i + 1])) for i in range(0, len(vals), 2)]


def centros_dos_elementos(dados, por_elemento: int = 16) -> dict[int, tuple[float, float, float]]:
    """Centro (mm) de cada elemento, a partir do vetor de GetElementDataFromEntity.

    Em linguagem simples: a API devolve, por elemento tetraédrico de 10 nós, 16 números seguidos: o id, os 10
    nós, as coordenadas x, y, z do centro (em metros), a razão de aspeto e o jacobiano. Fica-se com o id e o
    centro, convertido para mm.
    """
    dados = list(dados)
    if len(dados) % por_elemento:
        raise ValueError("o vetor não tem um número inteiro de elementos")
    out = {}
    for i in range(0, len(dados), por_elemento):
        bloco = dados[i:i + por_elemento]
        out[int(bloco[0])] = (bloco[11] * 1000.0, bloco[12] * 1000.0, bloco[13] * 1000.0)
    return out


def soma_cargas(peso_kg: float = PESO_KG) -> tuple[float, float, float]:
    """Soma vetorial (N) das cargas aplicadas; num modelo em equilíbrio, a reação no apoio é o seu simétrico."""
    f = forcas_marcha(peso_kg)
    return tuple(sum(v[i] for v in f.values()) for i in range(3))


def erro_equilibrio(reacao, cargas) -> float:
    """Erro relativo (%) entre a reação no apoio e a soma das cargas: |R + F| / |F| x 100."""
    return math.dist([-c for c in cargas], list(reacao)) / math.hypot(*cargas) * 100.0


def flecha_consola(cf: dict, peso_kg: float = PESO_KG) -> dict[str, float]:
    """Estimativa de viga (tubo da diáfise encastrado em baixo) do deslocamento horizontal no topo.

    Em linguagem simples: trata o fémur como um tubo de secção constante (raios exterior e do canal da diáfise),
    encastrado no corte distal e com comprimento livre até à altura do centro da cabeça. As cargas dão um momento
    no plano frontal (sobretudo a força vertical da anca a 38,3 mm do eixo) e uma força anteroposterior; a flecha
    é M L^2 / (2 E I) no plano frontal e F L^3 / (3 E I) no anteroposterior. Serve só para ver se a ordem de
    grandeza do deslocamento máximo da Simulation é a de uma flexão da diáfise.
    """
    f = forcas_marcha(peso_kg)
    p = {"contacto_anca": (-cf["cabeca_offset"], cf["cabeca_altura"]),
         "abdutores": (17.0, cf["trocanter_topo"])}
    L = cf["cabeca_altura"] - cf["fixacao_y"]
    E = OSSO["Osso cortical"]["E_GPa"] * 1000.0  # N/mm2
    I = math.pi / 4 * (cf["diafise_raio"] ** 4 - cf["canal_raio"] ** 4)
    M = sum(p[k][0] * f[k][1] - (p[k][1] - cf["fixacao_y"]) * f[k][0] for k in f)  # momento no apoio, plano XY
    Fz = sum(v[2] for v in f.values())
    frontal = abs(M) * L ** 2 / (2 * E * I)
    ap = abs(Fz) * L ** 3 / (3 * E * I)
    return {"L_mm": L, "I_mm4": I, "momento_frontal_Nmm": M, "Fz_N": Fz, "flecha_frontal_mm": frontal,
            "flecha_ap_mm": ap, "flecha_total_mm": math.hypot(frontal, ap)}


def percentil(valores, q: float) -> float:
    """Percentil q (0 a 100) por interpolação linear entre os valores ordenados."""
    v = sorted(valores)
    if not v:
        raise ValueError("lista vazia")
    k = (len(v) - 1) * q / 100.0
    i = int(math.floor(k))
    j = min(i + 1, len(v) - 1)
    return v[i] + (v[j] - v[i]) * (k - i)


def stl_binario(vertices, faces, caminho: Path) -> None:
    """Grava uma malha triangular em STL binário (mm).

    Em linguagem simples: escreve o cabeçalho, o número de triângulos e, por triângulo, a normal e os três
    vértices, no formato que o SolidWorks importa.
    """
    import struct

    import numpy as np

    v = np.asarray(vertices, dtype=float)
    f = np.asarray(faces, dtype=int)
    with open(caminho, "wb") as fh:
        fh.write(b"fea_solidworks".ljust(80, b" "))
        fh.write(struct.pack("<I", len(f)))
        for tri in f:
            a, b, c = v[tri[0]], v[tri[1]], v[tri[2]]
            n = np.cross(b - a, c - a)
            n = n / (np.linalg.norm(n) or 1.0)
            fh.write(struct.pack("<12fH", *n, *a, *b, *c, 0))


def femur_no_referencial_da_haste(cf: dict):
    """Vértices e faces do fémur FJ3365 no referencial do modelo (eixo do canal em y, cabeça medial em x < 0).

    Em linguagem simples: ajusta a cabeça e o eixo do canal como no planeamento da haste e roda e desloca o fémur
    para o eixo do canal ficar no eixo y, a cabeça do lado de x negativo e o centro da cabeça à altura das cotas.
    """
    import numpy as np

    sys.path.insert(0, str(RAIZ / "scripts"))
    import geometria_3d as geo3
    from planeamento_haste import cabeca_e_eixo

    v, f = geo3.ler_obj(FEMUR_OBJ)
    H, _, C0, a = cabeca_e_eixo(v)
    a = a / np.linalg.norm(a)
    P = C0 + ((H - C0) @ a) * a
    med = (H - P) / np.linalg.norm(H - P)
    ez = np.cross(-med, a)  # x lateral, y superior: z = x × y
    loc = np.stack([(v - P) @ (-med), (v - P) @ a, (v - P) @ ez], 1)
    loc[:, 1] += cf["cabeca_altura"]
    return loc, f


def medir_femur_anatomico(cf: dict) -> dict[str, float]:
    """Medidas do fémur FJ3365 usadas nas cotas (raio da cabeça, offset e meias larguras a várias alturas).

    Em linguagem simples: corta o fémur por planos perpendiculares ao eixo do canal e mede, em cada corte, até
    onde vai o osso para o lado lateral e para o lado medial.
    """
    import numpy as np

    sys.path.insert(0, str(RAIZ / "scripts"))
    import geometria_3d as geo3
    from planeamento_haste import cabeca_e_eixo

    v, f = geo3.ler_obj(FEMUR_OBJ)
    H, r, C0, a = cabeca_e_eixo(v)
    a = a / np.linalg.norm(a)
    P = C0 + ((H - C0) @ a) * a
    out = {"cabeca_raio": float(r), "cabeca_offset": float(np.linalg.norm(H - P))}
    med = (H - P) / np.linalg.norm(H - P)
    for dz in (0, -10, -20, -40, -100, -140):
        s = geo3.cortar_malha(v, f, a, P + dz * a).reshape(-1, 3)
        q = (s - P) @ med
        out[f"lateral_{-dz}"] = float(-q.min())
        out[f"medial_{-dz}"] = float(q.max())
    return out


def linhas_resumo(resultados: dict) -> list[dict]:
    """Uma linha por caso e por malha: energias nas zonas de Gruen 1 e 7 e razão ao fémur intacto da mesma malha.

    Em linguagem simples: lê o dicionário gravado em results/fea_haste_sw.json e, para cada material e tamanho de
    malha, divide a energia de cada zona pela do fémur intacto calculado com o mesmo tamanho de malha.
    """
    casos = resultados["casos"]
    out = []
    for nome, por_malha in casos.items():
        for h, r in por_malha.items():
            ref = casos.get("Intacto", {}).get(h)
            linha = {"caso": nome, "h_mm": float(h), "nos": r["nos"], "elementos": r["elementos"]}
            for z in ("1", "7"):
                e = r["zonas"][z]["energia_J"]
                linha[f"g{z}_mJ"] = e * 1000.0
                linha[f"g{z}_razao"] = e / ref["zonas"][z]["energia_J"] if ref else float("nan")
            out.append(linha)
    return out


def ordem_por_zona(resultados: dict, zona: str, h: str) -> list[str]:
    """Materiais da haste por ordem decrescente de energia na zona (mais energia = menos blindagem de tensões)."""
    casos = {k: v[h] for k, v in resultados["casos"].items() if k != "Intacto" and h in v}
    return sorted(casos, key=lambda k: casos[k]["zonas"][zona]["energia_J"], reverse=True)


def variacao_entre_malhas(resultados: dict, caso: str, zona: str) -> float:
    """Diferença relativa (%) da energia da zona entre a malha mais grossa e a mais fina do mesmo caso."""
    por_malha = resultados["casos"][caso]
    hs = sorted(por_malha, key=float)
    fina, grossa = por_malha[hs[0]]["zonas"][zona]["energia_J"], por_malha[hs[-1]]["zonas"][zona]["energia_J"]
    return (grossa - fina) / fina * 100.0


def _num(v: float, casas: int = 2) -> str:
    return f"{v:.{casas}f}".replace(".", ",")


def resumo_markdown(resultados: dict) -> str:
    """Texto de results/fea_haste_sw.md: tabelas por malha, ordem dos materiais e sensibilidade à malha."""
    E = ler_modulos_haste()
    hs = sorted({h for v in resultados["casos"].values() for h in v}, key=float)
    fina = hs[0]
    L = ["# FEA da haste femoral em SOLIDWORKS Simulation (confirmação independente)", "",
         "Gerado por `python scripts/fea_solidworks.py resumo` a partir de results/fea_haste_sw.json. Hipóteses, "
         "fontes e limitações em docs/FEA_HASTE_SW.md; cotas do fémur em design/cad/cotas_femur_fea.md.", "",
         "O que se mediu: energia de deformação total (J) dos elementos de osso (cortical e trabecular) cujo centro "
         "fica em cada zona de Gruen, obtida por elemento na Simulation (componente ENERGY), com o centro de cada "
         "elemento lido na malha. Zona 1: lateral (x > 0), do terço proximal da haste (y de 2L/3 = 76,7 mm) até ao "
         "corte do colo, incluindo o grande trocânter; zona 7: medial (x < 0), mesma faixa de alturas (calcar). A "
         "razão é a energia na zona com a haste a dividir pela do fémur intacto com o mesmo tamanho de malha "
         "(1 = igual ao intacto; abaixo de 1 = blindagem de tensões).", ""]
    for h in hs:
        L += [f"## Malha de {_num(float(h), 1)} mm (tetraedros parabólicos)", "",
              "| caso | E da haste (GPa) | nós | elementos | Gruen 1 (mJ) | Gruen 1 / intacto | Gruen 7 (mJ) | "
              "Gruen 7 / intacto |", "|---|---|---|---|---|---|---|---|"]
        for ln in linhas_resumo(resultados):
            if ln["h_mm"] != float(h):
                continue
            e = "-" if ln["caso"] == "Intacto" else _num(E[ln["caso"]], 1)
            L.append(f"| {ln['caso']} | {e} | {ln['nos']} | {ln['elementos']} | {_num(ln['g1_mJ'])} | "
                     f"{_num(ln['g1_razao'])} | {_num(ln['g7_mJ'])} | {_num(ln['g7_razao'])} |")
        L.append("")
    L += [f"## Ordem dos materiais (malha de {_num(float(fina), 1)} mm, da maior para a menor energia no osso)", ""]
    for z in ("1", "7"):
        L.append(f"- Gruen {z}: " + " > ".join(ordem_por_zona(resultados, z, fina)))
    L += ["", "Leitura da haste de Ti-6Al-4V poroso: deixa no osso proximal uma carga próxima da do osso intacto "
          "(razões um pouco acima de 1), porque a interface é colada e a rigidez da haste é igual à do osso "
          "cortical (17 GPa, valor de desenho). Lê-se como próxima do osso intacto: a parte acima de 1 é efeito "
          "do modelo (haste colada, de rigidez igual à da cortical, dentro de osso trabecular mole), não um ganho "
          "clínico."]
    if len(hs) > 1:
        L += ["", f"## Sensibilidade à malha ({_num(float(hs[-1]), 1)} mm face a {_num(float(fina), 1)} mm)", "",
              "| caso | Gruen 1 (%) | Gruen 7 (%) | mesma ordem nas duas malhas |", "|---|---|---|---|"]
        mesma = {z: ordem_por_zona(resultados, z, hs[0]) == ordem_por_zona(resultados, z, hs[-1]) for z in "17"}
        for caso in resultados["casos"]:
            if len(resultados["casos"][caso]) < 2:
                continue
            L.append(f"| {caso} | {_num(variacao_entre_malhas(resultados, caso, '1'), 1)} | "
                     f"{_num(variacao_entre_malhas(resultados, caso, '7'), 1)} | "
                     f"Gruen 1: {'sim' if mesma['1'] else 'não'}; Gruen 7: {'sim' if mesma['7'] else 'não'} |")
    L += ["", f"## Deslocamento máximo e tensão máxima (malha de {_num(float(fina), 1)} mm)", "",
          "Nos modelos com a haste a Simulation mostra o aviso de deslocamentos excessivos, respondido com No (ver "
          "docs/FEA_HASTE_SW.md); os deslocamentos máximos ficam perto dos do fémur intacto. As imagens em "
          "results/figures/fea_sw/ têm a forma deformada exagerada e a escala de cores automática de cada estudo.", "",
          "| caso | deslocamento máximo (mm) | von Mises máximo no modelo (MPa) |", "|---|---|---|"]
    for caso, por_malha in resultados["casos"].items():
        r = por_malha.get(fina)
        if r and "ures_max_mm" in r:
            L.append(f"| {caso} | {_num(r['ures_max_mm'])} | {_num(r['vm_max_MPa'], 1)} |")
    L.append("")
    return "\n".join(L)


def figura_gruen(resultados: dict, destino_base: Path) -> None:
    """Gráfico de barras da razão ao intacto nas zonas de Gruen 1 e 7, por material (malha mais fina), PNG e SVG."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    hs = sorted({h for v in resultados["casos"].values() for h in v}, key=float)
    linhas = [ln for ln in linhas_resumo(resultados) if ln["h_mm"] == float(hs[0]) and ln["caso"] != "Intacto"]
    fig, ax = plt.subplots(figsize=(7, 4), dpi=150)
    n = len(linhas)
    for i, z in enumerate(("1", "7")):
        ax.bar([k + (i - 0.5) * 0.38 for k in range(n)], [ln[f"g{z}_razao"] for ln in linhas], width=0.36,
               label=f"Gruen {z}", color=("#3b6ea8", "#c9733a")[i])
    ax.axhline(1.0, color="#444", lw=0.8, ls="--")
    ax.set_xticks(range(n), [ln["caso"] for ln in linhas])
    ax.set_ylabel("energia no osso / fémur intacto")
    ax.set_title(f"SOLIDWORKS Simulation, malha de {_num(float(hs[0]), 1)} mm")
    ax.legend(frameon=False)
    fig.tight_layout()
    destino_base.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino_base.with_suffix(".png"), dpi=300)
    fig.savefig(destino_base.with_suffix(".svg"))
    plt.close(fig)


# ---------------------------------------------------------------- SolidWorks (COM)

def _vt():
    import pythoncom
    from win32com.client import VARIANT
    return pythoncom, VARIANT


def _nulo():
    pythoncom, VARIANT = _vt()
    return VARIANT(pythoncom.VT_DISPATCH, None)


def _ent(objs):
    pythoncom, VARIANT = _vt()
    return VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_VARIANT, list(objs))


def _int():
    pythoncom, VARIANT = _vt()
    return VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)


def _call0(obj, nome):
    m = getattr(obj, nome)
    return m() if callable(m) else m


class SwFEA(cad.Sw):
    """Instância própria do SolidWorks (arrancada por este script), com as operações de cad_solidworks.Sw."""

    def __init__(self, visivel: bool = True):
        import pythoncom
        import win32com.client
        from win32com.client import gencache

        self.pythoncom = pythoncom
        self.mod = gencache.EnsureModule("{83A33D31-27C5-11CE-BFD4-00400513BB57}", 0, 33, 0)
        self.c = gencache.EnsureModule("{4687F359-55D0-4CD3-B6CF-2EB42C11F989}", 0, 33, 0).constants
        self.late = win32com.client.Dispatch("SldWorks.Application")
        self.late.Visible = visivel
        self.late.UserControl = False
        self.app = self.mod.ISldWorks(self.late._oleobj_)
        log.info("SolidWorks %s", _call0(self.late, "RevisionNumber"))

    def fechar(self):
        try:
            self.late.CloseAllDocuments(True)
        finally:
            self.late.ExitApp()

    # ---- geometria
    def esboco_revolucao(self, nome, eixo, pts, corte=False, juntar=True):
        """Revolução de um polígono fechado à volta de uma linha de construção (pontos em mm, plano frontal)."""
        def desenhar(sk):
            sk.CreateCenterLine(cad._m(eixo[0][0]), cad._m(eixo[0][1]), 0, cad._m(eixo[1][0]), cad._m(eixo[1][1]), 0)
            self.polilinha(pts, fechar=True)
        self.esboco(self.frontal, f"Esboço {nome}", desenhar)
        self.revolucao(f"Esboço {nome}", nome, juntar=juntar, corte=corte)

    def esfera(self, nome, centro, raio, direcao, corte=False):
        """Esfera por revolução de meio círculo à volta do eixo do colo."""
        cx, cy = centro
        a = (cx - raio * direcao[0], cy - raio * direcao[1])
        b = (cx + raio * direcao[0], cy + raio * direcao[1])

        def desenhar(sk):
            sk.CreateCenterLine(cad._m(a[0]), cad._m(a[1]), 0, cad._m(b[0]), cad._m(b[1]), 0)
            sk.CreateArc(cad._m(cx), cad._m(cy), 0, cad._m(a[0]), cad._m(a[1]), 0, cad._m(b[0]), cad._m(b[1]), 0, 1)
            sk.CreateLine(cad._m(b[0]), cad._m(b[1]), 0, cad._m(a[0]), cad._m(a[1]), 0)
        self.esboco(self.frontal, f"Esboço {nome}", desenhar)
        self.revolucao(f"Esboço {nome}", nome, corte=corte)

    def cilindro_colo(self, nome, geo, raio, corte=False):
        p0, c, d = geo["p0"], geo["centro"], geo["direcao"]
        n = (d[1], -d[0])
        pts = [p0, (p0[0] + raio * n[0], p0[1] + raio * n[1]), (c[0] + raio * n[0], c[1] + raio * n[1]), c]
        self.esboco_revolucao(nome, (p0, c), pts, corte=corte)

    def extrusao_poligono(self, nome, pts, espessura, corte=False, atravessar=False):
        self.esboco(self.frontal, f"Esboço {nome}", lambda sk: self.polilinha(pts, fechar=True))
        if atravessar:
            # nos dois sentidos (Sd = False); o corte_atravessar de cad_solidworks só corta para um lado do plano
            self.m.ClearSelection2(True)
            self.selecionar(f"Esboço {nome}", "SKETCH")
            ta = self.c.swEndCondThroughAll
            f = self.fm.FeatureCut4(False, False, False, ta, ta, 0, 0, False, False, False, False, 0, 0, False, False,
                                    False, False, False, False, True, False, True, False, 0, 0, False, False)
            if f is None:
                raise RuntimeError(f"o corte '{nome}' falhou")
            self.t(f, "IFeature").Name = nome
        elif corte:
            self.m.ClearSelection2(True)
            self.selecionar(f"Esboço {nome}", "SKETCH")
            mp = self.c.swEndCondMidPlane
            f = self.fm.FeatureCut4(True, False, False, mp, 0, cad._m(espessura), 0, False, False, False, False, 0, 0,
                                    False, False, False, False, False, False, True, False, False, False, 0, 0,
                                    False, False)
            if f is None:
                raise RuntimeError(f"o corte '{nome}' falhou")
            self.t(f, "IFeature").Name = nome
        else:
            self.extrusao_simetrica(f"Esboço {nome}", nome, espessura)

    def inserir_peca(self, caminho: Path):
        parte = self.t(self.m, "IPartDoc")
        f = parte.InsertPart3(str(caminho), 1 | 512, "")  # sólidos, sem ligação ao ficheiro de origem
        if f is None:
            raise RuntimeError(f"InsertPart3 falhou: {caminho}")
        return f

    def subtrair_haste(self):
        """Insere a haste e tira-a do corpo de osso; se não se tocarem, só apaga a haste inserida.

        Em linguagem simples: primeiro tenta a operação Combinar (subtração); se a API a recusar, faz a subtração
        com corpos temporários (Operations2), cria um corpo novo com o resultado e apaga os dois corpos de origem.
        """
        self.inserir_peca(HASTE)
        doc = self.late.ActiveDoc
        bs = list(doc.GetBodies2(0, False))
        vols = [b.GetMassProperties(1.0)[3] for b in bs]
        osso_l, haste_l = bs[vols.index(max(vols))], bs[vols.index(min(vols))]
        inter = osso_l.Copy().Operations2(15901, haste_l.Copy())
        v_inter = sum(b.GetMassProperties(1.0)[3] for b in (inter[0] or [])) * 1e9 if inter[0] else 0.0
        log.info("volume comum osso/haste: %.1f mm3 (erro %s)", v_inter, inter[1])
        if v_inter < 1.0:
            doc.ClearSelection2(True)
            haste_l.Select2(False, None)
            doc.FeatureManager.InsertDeleteBody2(False)
            return
        corpos = self.corpos()
        vols = []
        for b in corpos:
            mp = b.GetMassProperties(1.0)
            vols.append(mp[3])
        osso = corpos[max(range(len(corpos)), key=lambda i: vols[i])]
        ferramenta = [b for b in corpos if b is not osso]
        _, VARIANT = _vt()
        pc = self.pythoncom
        f = None
        tentativas = (lambda: ferramenta,
                      lambda: VARIANT(pc.VT_ARRAY | pc.VT_DISPATCH, [b._oleobj_ for b in ferramenta]),
                      lambda: VARIANT(pc.VT_ARRAY | pc.VT_VARIANT, [b._oleobj_ for b in ferramenta]))
        for i, arr in enumerate(tentativas):
            try:
                f = self.fm.InsertCombineFeature(15902, osso, arr())
            except Exception as exc:  # o tipo do array aceite pela API não está documentado para pywin32
                log.info("Combinar, tentativa %d: %r", i, exc)
                f = None
            if f is not None:
                break
        if f is not None:
            self.t(f, "IFeature").Name = "Cavidade da haste"
            return
        r, erro = osso_l.Copy().Operations2(15902, haste_l.Copy())
        if not r:
            raise RuntimeError(f"a subtração da haste falhou (erro {erro})")
        doc.ClearSelection2(True)
        osso_l.Select2(False, None)
        haste_l.Select2(True, None)
        doc.FeatureManager.InsertDeleteBody2(False)
        for corpo in r:
            if doc.CreateFeatureFromBody3(corpo, False, 0) is None:
                raise RuntimeError("não foi possível criar o corpo com a cavidade da haste")
        log.info("cavidade feita com corpos temporários (Combinar recusado)")

    def gravar(self, caminho: Path):
        caminho.parent.mkdir(parents=True, exist_ok=True)
        self.m.ForceRebuild3(False)
        self.m.ShowNamedView2("*Front", 1)
        self.m.ViewZoomtofit2()
        ok = self.ext.SaveAs3(str(caminho), 0, 1, None, None, 0, 0)
        log.info("gravado %s (%s); corpos: %d", caminho.name, ok, len(self.corpos()))


def construir_osso(sw: SwFEA, cf: dict, ch: dict, tipo: str, implantado: bool) -> Path:
    """Constrói a cortical ou o trabecular do fémur simplificado (intacto ou com corte do colo e cavidade)."""
    geo = geometria_colo(cf, ch)
    sw.nova_peca()
    troc = poligono_trocanter(cf)
    if tipo == "cortical":
        ext = perfil_exterior(cf)
        sw.esboco_revolucao("Diáfise e metáfise", ((0, ext[0][0] - 5), (0, 200)),
                            [(0, ext[0][0])] + [(r, y) for y, r in ext] + [(0, ext[-1][0])])
        sw.cilindro_colo("Colo", geo, cf["colo_raio"])
        sw.esfera("Cabeça", geo["centro"], cf["cabeca_raio"], geo["direcao"])
        sw.extrusao_poligono("Grande trocânter", troc, cf["trocanter_largura"])
        # interior (vazio): canal e região trabecular
        yb = cf["fixacao_y"] - 1.0
        ins = perfil_interior(cf, yb)
        sw.esboco_revolucao("Canal e metáfise interior", ((0, yb - 5), (0, 200)),
                            [(0, yb)] + [(r, y) for y, r in ins] + [(0, ins[-1][0])], corte=True)
        sw.cilindro_colo("Colo interior", geo, cf["colo_raio"] - cf["cortical_colo"], corte=True)
        sw.esfera("Cabeça interior", geo["centro"], cf["cabeca_raio"] - cf["cortical_cabeca"], geo["direcao"],
                  corte=True)
        sw.extrusao_poligono("Trocânter interior", poligono_offset(troc, cf["cortical_metafise"]),
                             cf["trocanter_largura"] - 2 * cf["cortical_metafise"], corte=True)
    else:
        y0 = cf["trabecular_base"]
        ins = perfil_interior(cf, y0)
        sw.esboco_revolucao("Trabecular da metáfise", ((0, y0 - 5), (0, 200)),
                            [(0, y0)] + [(r, y) for y, r in ins] + [(0, ins[-1][0])])
        sw.cilindro_colo("Trabecular do colo", geo, cf["colo_raio"] - cf["cortical_colo"])
        sw.esfera("Trabecular da cabeça", geo["centro"], cf["cabeca_raio"] - cf["cortical_cabeca"], geo["direcao"])
        sw.extrusao_poligono("Trabecular do trocânter", poligono_offset(troc, cf["cortical_metafise"]),
                             cf["trocanter_largura"] - 2 * cf["cortical_metafise"])
    if implantado:
        sw.extrusao_poligono("Corte do colo", poligono_osteotomia(cf, geo), 0, atravessar=True)
        sw.subtrair_haste()
    if len(sw.corpos()) != 1:
        raise RuntimeError(f"{tipo}: esperava 1 corpo, há {len(sw.corpos())}")
    sw.nomear_corpos([f"Osso {tipo}"])
    caminho = PASTA_FEA / f"osso_{tipo}_{'implantado' if implantado else 'intacto'}.SLDPRT"
    sw.gravar(caminho)
    sw.late.CloseAllDocuments(True)
    return caminho


def montar_modelo(sw: SwFEA, pecas: list[Path], nome: str, nomes: list[str]) -> Path:
    """Peça multicorpo com os corpos das peças indicadas (sem ligação às peças de origem), para a Simulation."""
    sw.nova_peca()
    for p in pecas:
        sw.inserir_peca(p)
    corpos = sw.corpos()
    if len(corpos) != len(pecas):
        raise RuntimeError(f"{nome}: {len(corpos)} corpos para {len(pecas)} peças")
    # a ordem dos corpos não é a de inserção: cada corpo é reconhecido pela altura mínima (y) da caixa envolvente
    cf = ler_cotas_femur()
    y_alvo = {"Osso cortical": cf["fixacao_y"], "Osso trabecular": cf["trabecular_base"], "Haste": 0.0}
    parte = sw.t(sw.m, "IPartDoc")
    lista = [sw.t(b, "IBody2") for b in parte.GetBodies2(sw.c.swSolidBody, False)]
    for b in lista:
        ymin = b.GetBodyBox()[1] * 1000.0
        n = min(nomes, key=lambda k: abs(y_alvo[k] - ymin))
        b.Name = n
        log.info("%s: corpo com y mínimo %.1f mm, volume %.0f mm3", n, ymin, b.GetMassProperties(1.0)[3] * 1e9)
    caminho = PASTA_FEA / f"{nome}.SLDPRT"
    sw.gravar(caminho)
    sw.late.CloseAllDocuments(True)
    return caminho


def geometria(sw: SwFEA) -> dict:
    cf, ch = ler_cotas_femur(), cad.ler_cotas()
    pecas = {}
    for implantado in (False, True):
        for tipo in ("cortical", "trabecular"):
            pecas[(tipo, implantado)] = construir_osso(sw, cf, ch, tipo, implantado)
    intacto = montar_modelo(sw, [pecas[("cortical", False)], pecas[("trabecular", False)]], "fea_femur_intacto",
                            ["Osso cortical", "Osso trabecular"])
    implantado = montar_modelo(sw, [pecas[("cortical", True)], pecas[("trabecular", True)], HASTE],
                               "fea_femur_haste", ["Osso cortical", "Osso trabecular", "Haste"])
    return {"intacto": intacto, "implantado": implantado}


# ---- Simulation

def _selecionar_face(doc, ponto, corpo: str | None = None):
    """Face que passa pelo ponto (mm): a de menor distância ao ponto, procurada em todos os corpos.

    Em linguagem simples: o SelectByID2 por coordenadas falha em algumas faces planas; aqui percorre-se cada face
    e pede-se ao SolidWorks o ponto da face mais próximo do ponto dado.
    """
    x, y, z = (c / 1000.0 for c in ponto)
    melhor, dmin = None, float("inf")
    for b in doc.GetBodies2(0, False):
        if corpo and _call0(b, "Name") != corpo:
            continue
        for f in _call0(b, "GetFaces"):
            q = f.GetClosestPointOn(x, y, z)
            d = math.dist((x, y, z), tuple(q[:3]))
            if d < dmin:
                melhor, dmin = f, d
    if melhor is None or dmin > 1e-4:
        raise RuntimeError(f"nenhuma face em {ponto} (distância mínima {dmin * 1000:.3f} mm)")
    return melhor


def _cw(obj, interface: str):
    """Converte um objeto da Simulation na interface tipada (biblioteca de tipos cosworks.tlb)."""
    from win32com.client import gencache

    mod = gencache.EnsureModule("{4B6A9EBF-8638-4C95-98C9-81AE0A7E3B24}", 0, 18, 0)
    return getattr(mod, interface)(obj._oleobj_ if hasattr(obj, "_oleobj_") else obj)


def _material(corpo_cw, nome, E_Pa, nu):
    err = _int()
    corpo_cw = _cw(corpo_cw, "ICWSolidBody")
    from win32com.client import dynamic

    mat = dynamic.Dispatch(corpo_cw.GetDefaultMaterial()._oleobj_)
    mat.MaterialName = nome
    for prop, valor in (("EX", E_Pa), ("NUXY", nu)):
        for metodo in ("SetPropertyByName", "SetPropertyByName2"):
            try:
                getattr(mat, metodo)(prop, valor, 0)
                break
            except Exception as exc:  # a assinatura aceite varia entre versões
                log.info("%s(%s) falhou: %r", metodo, prop, exc)
        else:
            raise RuntimeError(f"não foi possível definir {prop}")
    rc = corpo_cw.SetSolidBodyMaterial(mat)
    lido = dynamic.Dispatch(corpo_cw.GetSolidBodyMaterial()._oleobj_).GetPropertyByName(0, "EX", _bool())
    lido = lido[0] if isinstance(lido, tuple) else lido
    if abs(lido - E_Pa) > 1e-6 * E_Pa:
        raise RuntimeError(f"material {nome}: EX lido {lido} diferente de {E_Pa}")
    log.info("material %s: E = %.4g Pa, nu = %.2f (rc %s)", nome, E_Pa, nu, rc)
    _ = err


def _raio_exterior(cf: dict, y: float) -> float:
    ext = perfil_exterior(cf)
    for (y0, r0), (y1, r1) in zip(ext, ext[1:]):
        if y0 <= y <= y1:
            return r0 + (r1 - r0) * (y - y0) / (y1 - y0)
    raise ValueError(y)


def pontos_de_carga(cf: dict, ch: dict) -> dict:
    """Pontos (mm) das faces de carga e de fixação e centro da cabeça, para selecionar as faces por coordenadas."""
    geo = geometria_colo(cf, ch)
    cx, cy = geo["centro"]
    col = cad.eixo_colo(ch)
    d, base = col["direcao"], col["base"]
    s_cone0 = ch["haste_colo"] - ch["cone_comprimento"] + 3
    meio = s_cone0 + ch["cone_comprimento"] / 2
    rc = (ch["cone_maior"] + ch["cone_menor"]) / 4
    troc = poligono_trocanter(cf)
    return {
        "centro_cabeca": (cx, cy, 0.0),
        # fora do plano frontal, onde ficam as arestas de costura das revoluções
        "cabeca_femur": (cx, cy + cf["cabeca_raio"] * math.cos(math.radians(30)),
                         cf["cabeca_raio"] * math.sin(math.radians(30))),
        "cone": (base[0] + meio * d[0], base[1] + meio * d[1], rc),
        "trocanter_topo": ((troc[4][0] + troc[5][0]) / 2, cf["trocanter_topo"], 0.0),
        "fixacao": ((cf["canal_raio"] + cf["diafise_raio"]) / 2, cf["fixacao_y"], 0.0),
        # origem do vasto lateral (crista do vasto, lateral, logo abaixo do grande trocânter): valor de desenho
        "vasto_lateral": (_raio_exterior(cf, 85.0), 85.0, 0.0),
    }


def estudo(sw: SwFEA, doc, cw, nome: str, materiais: dict, implantado: bool, h_mm: float, cf: dict, ch: dict,
           fator: float = 1.0, completo: bool = False):
    """Cria, malha e resolve um estudo estático (cargas multiplicadas por fator); devolve estudo e resultados."""
    err = _int()
    st = cw.ActiveDoc.StudyManager.CreateNewStudy3(nome, 0, 0, err)
    if st is None:
        raise RuntimeError(f"CreateNewStudy3 falhou ({err.value})")
    comp = st.SolidManager.GetComponentAt(0, err)
    corpos_cw = {}
    for i in range(comp.SolidBodyCount):
        b = comp.GetSolidBodyAt(i, err)
        corpos_cw[_call0(b, "SolidBodyName")] = b
    log.info("corpos no estudo: %s", list(corpos_cw))
    for nome_corpo, b in corpos_cw.items():
        chave = next(k for k in materiais if nome_corpo.startswith(k) or k in nome_corpo)
        E, nu = materiais[chave]
        _material(b, chave, E, nu)

    p = pontos_de_carga(cf, ch)
    f = {k: tuple(fator * c for c in v) for k, v in forcas_marcha(completo=completo).items()}
    if completo:  # o tensor da fáscia lata atua no grande trocânter, com os abdutores (Baharuddin 2014, ponto P1)
        f["abdutores"] = tuple(f["abdutores"][i] + f["tensor_fascia_lata_proximal"][i]
                               + f["tensor_fascia_lata_distal"][i] for i in range(3))
    lbc = st.LoadsAndRestraintsManager
    fix = lbc.AddRestraint(0, _ent([_selecionar_face(doc, p["fixacao"])]), _nulo(), err)
    if fix is None:
        raise RuntimeError(f"encastramento falhou ({err.value})")
    face_cabeca = _selecionar_face(doc, p["cone"] if implantado else p["cabeca_femur"])
    face_troc = _selecionar_face(doc, p["trocanter_topo"])
    grupos = [("contacto_anca", [face_cabeca], p["centro_cabeca"], f["contacto_anca"]),
              ("abdutores", [face_troc], p["trocanter_topo"], f["abdutores"])]
    if completo:
        grupos.append(("vasto_lateral", [_selecionar_face(doc, p["vasto_lateral"])], p["vasto_lateral"],
                       f["vasto_lateral"]))
    for rotulo, faces, local, F in grupos:
        rl = lbc.AddRemoteLoad(0, _ent(faces), 0, local[0], local[1], local[2], err)
        if rl is None:
            raise RuntimeError(f"carga remota {rotulo} falhou ({err.value})")
        _call0(rl, "RemoteLoadBeginEdit")
        rl.SetForceOrTranslationValues(1, 1, F[0], 1, F[1], 1, F[2])
        rc = _call0(rl, "RemoteLoadEndEdit")
        log.info("carga %s em %s: F = (%.1f, %.1f, %.1f) N (rc %s)", rotulo, local, *F, rc)

    mesh = st.Mesh
    mesh.Quality = 1
    t0 = time.time()
    rc = st.CreateMesh(0, h_mm, h_mm / 20.0)
    if rc:
        raise RuntimeError(f"malha falhou (h = {h_mm} mm, erro {rc})")
    log.info("malha h = %.2f mm: %d nós, %d elementos (%.0f s)", h_mm, mesh.NodeCount, mesh.ElementCount,
             time.time() - t0)
    rc = _call0(st, "RunAnalysis")
    if rc:
        raise RuntimeError(f"análise falhou (erro {rc})")
    res = st.Results
    if res is None:
        raise RuntimeError("estudo sem resultados")
    log.info("resolvido em %.0f s", time.time() - t0)
    return st, res, corpos_cw, mesh


def energias_osso(doc, res, mesh, cf, ch) -> tuple[dict, dict]:
    """Energia de deformação por elemento nos corpos de osso, somada por zona de Gruen."""
    geo = geometria_colo(cf, ch)
    err = _int()
    bodies = list(doc.GetBodies2(0, False))
    totais, elementos = {}, []
    for b in bodies:
        nome = _call0(b, "Name")
        if not nome.startswith("Osso"):
            continue
        vals = res.GetStrainForEntities(8, 1, _nulo(), _ent([b]), err)  # 8 = ENERGY, por elemento
        vals = list(vals or [])
        ids = mesh.GetElementDataFromEntity(b, _int())
        ids = list(ids or [])
        log.info("%s: %d valores de energia, %d ids de elementos (erro %s); primeiros %s / %s", nome, len(vals),
                 len(ids), err.value, vals[:4], ids[:4])
        centros = centros_dos_elementos(ids)
        pares = pares_id_valor(vals)
        tot = 0.0
        for el, e in pares:
            cx, cy, _ = centros[el]
            elementos.append((cx, cy, e))
            tot += e
        totais[nome] = tot
    return somar_por_zona(elementos, ch["haste_comprimento"], cf, geo), totais


def _bool():
    pythoncom, VARIANT = _vt()
    return VARIANT(pythoncom.VT_BYREF | pythoncom.VT_BOOL, False)


def _int_dbl():
    pythoncom, VARIANT = _vt()
    return VARIANT(pythoncom.VT_BYREF | pythoncom.VT_R8, 0.0)


def estudos(sw: SwFEA, malhas: list[float], so: list[str] | None = None) -> dict:
    from win32com.client import Dispatch

    cf, ch = ler_cotas_femur(), cad.ler_cotas()
    E = ler_modulos_haste()
    base_osso = {k: (v["E_GPa"] * 1e9, v["nu"]) for k, v in OSSO.items()}
    resultados = {"malhas_mm": malhas, "casos": {}}
    casos = [("Intacto", None)] + [(m, m) for m in MATERIAIS_HASTE]
    if so:
        casos = [c for c in casos if _curto(c[0]) in so]
    for nome_caso, mat in casos:
        implantado = mat is not None
        ficheiro = PASTA_FEA / ("fea_femur_haste.SLDPRT" if implantado else "fea_femur_intacto.SLDPRT")
        e1, e2 = _int(), _int()
        doc = sw.late.OpenDoc6(str(ficheiro), 1, 1, "", e1, e2)
        if doc is None:
            raise RuntimeError(f"OpenDoc6 falhou ({e1.value})")
        addin = sw.late.GetAddInObject("SldWorks.Simulation")
        if addin is None:
            sw.late.LoadAddIn(r"<pasta local> Corp\SOLIDWORKS\Simulation\cosworks.dll")
            addin = sw.late.GetAddInObject("SldWorks.Simulation")
        cw = Dispatch(addin).CosmosWorks
        materiais = dict(base_osso)
        if implantado:
            materiais["Haste"] = (E[mat] * 1e9, NU_METAL)
        for h in malhas:
            rotulo = f"{_curto(nome_caso)}_h{str(h).replace('.', 'p')}"
            t_caso = time.time()
            st, res, _, mesh = estudo(sw, doc, cw, rotulo, materiais, implantado, h, cf, ch)
            zonas, totais = energias_osso(doc, res, mesh, cf, ch)
            err = _int()
            vm = res.GetMinMaxStress(9, 0, 1, _nulo(), 3, err)
            ures = res.GetMinMaxDisplacement(3, 1, _nulo(), 0, err)
            r = {"nos": mesh.NodeCount, "elementos": mesh.ElementCount, "zonas": zonas, "energia_osso_J": totais,
                 "vm_max_MPa": vm[3], "ures_max_mm": ures[3], "segundos": round(time.time() - t_caso)}
            log.info("%s: Gruen 1 = %.4g J, Gruen 7 = %.4g J, URES máx = %.3f mm, vM máx = %.1f MPa", rotulo,
                     zonas[1]["energia_J"], zonas[7]["energia_J"], ures[3], vm[3])
            resultados["casos"].setdefault(nome_caso, {})[str(h)] = r
            imagens(sw, doc, res, rotulo)
            _gravar_json(resultados)
        doc.Save3(1, e1, e2)
        sw.late.CloseAllDocuments(True)
    return resultados


def _no_mais_proximo(nos: dict, ponto) -> int:
    return min(nos, key=lambda n: math.dist(nos[n], ponto))


def verificar(sw: SwFEA) -> dict:
    """Verificações de sanidade: equilíbrio, unidades, deformações no cortical, deslocamento e o aviso modal.

    Em linguagem simples: volta a resolver, sem gravar as peças, o fémur intacto e a haste de Co-Cr-Mo com a malha
    de 5 mm (e a haste com 10 % da carga, para ver se o aviso de deslocamentos excessivos depende do tamanho do
    deslocamento) e lê da Simulation as reações no apoio, os mesmos resultados em unidades diferentes, as
    deformações principais no cortical e o nó e o valor do deslocamento máximo.
    """
    from win32com.client import Dispatch

    cf, ch = ler_cotas_femur(), cad.ler_cotas()
    E = ler_modulos_haste()
    base = {k: (v["E_GPa"] * 1e9, v["nu"]) for k, v in OSSO.items()}
    out = {"soma_cargas_N": soma_cargas(), "flecha_viga": flecha_consola(cf), "casos": {}}
    vigia = VigiaDialogos.ativo
    for rotulo, implantado, fator in (("Intacto", False, 1.0), ("Co-Cr-Mo forjado", True, 1.0),
                                      ("Co-Cr-Mo forjado, 10 % da carga", True, 0.1)):
        ficheiro = PASTA_FEA / ("fea_femur_haste.SLDPRT" if implantado else "fea_femur_intacto.SLDPRT")
        e1, e2 = _int(), _int()
        doc = sw.late.OpenDoc6(str(ficheiro), 1, 1, "", e1, e2)
        addin = sw.late.GetAddInObject("SldWorks.Simulation")
        if addin is None:
            sw.late.LoadAddIn(r"<pasta local> Corp\SOLIDWORKS\Simulation\cosworks.dll")
            addin = sw.late.GetAddInObject("SldWorks.Simulation")
        cw = Dispatch(addin).CosmosWorks
        mats = dict(base)
        if implantado:
            mats["Haste"] = (E["Co-Cr-Mo forjado"] * 1e9, NU_METAL)
        cliques0 = vigia.cliques if vigia else 0
        st, res, _, mesh = estudo(sw, doc, cw, f"Verif_{len(out['casos'])}", mats, implantado, 5.0, cf, ch, fator)
        err = _int()
        r: dict = {"fator_carga": fator, "avisos_deslocamentos": (vigia.cliques - cliques0) if vigia else None}
        reac = list(res.GetReactionForcesAndMoments(1, _nulo(), 0, err) or [])
        r["reacoes_api"] = [float(v) for v in reac]
        log.info("%s: GetReactionForcesAndMoments = %s (erro %s)", rotulo, reac, err.value)
        vm_pa = res.GetMinMaxStress(9, 0, 1, _nulo(), 0, err)[3]
        vm_mpa = res.GetMinMaxStress(9, 0, 1, _nulo(), 3, err)[3]
        d_mm = res.GetMinMaxDisplacement(3, 1, _nulo(), 0, err)
        d_m = res.GetMinMaxDisplacement(3, 1, _nulo(), 2, err)[3]
        r.update({"vm_max_Pa": vm_pa, "vm_max_MPa": vm_mpa, "ures_max_mm": d_mm[3], "ures_max_m": d_m})
        nos_l = list(_call0(mesh, "GetNodes") or [])
        nos = {int(nos_l[i]): (nos_l[i + 1] * 1000, nos_l[i + 2] * 1000, nos_l[i + 3] * 1000)
               for i in range(0, len(nos_l), 4)}
        r["no_ures_max"] = {"no": int(d_mm[2]), "xyz_mm": nos.get(int(d_mm[2]))}

        ut = list(res.GetTranslationalDisplacement(1, _nulo(), 0, err) or [])
        passo = 4 if len(ut) == 4 * len(nos) else 5
        log.info("GetTranslationalDisplacement: %d valores para %d nós (início %s)", len(ut), len(nos), ut[:10])
        desl = {int(ut[i]): tuple(float(v) for v in ut[i + 1:i + 4]) for i in range(0, len(ut), passo)}

        def u_no(n):
            u = desl.get(n, (float("nan"),) * 3)
            return [*u, math.hypot(*u)]
        perfil = {}
        for y in (cf["fixacao_y"] + 1, -100.0, -50.0, 0.0, 50.0, 100.0):
            n = _no_mais_proximo(nos, (cf["diafise_raio"], y, 0.0) if y < 60 else (20.0, y, 0.0))
            perfil[f"{y:.0f}"] = {"no": n, "xyz_mm": nos[n], "u_mm": u_no(n)}
        n_cab = _no_mais_proximo(nos, (-cf["cabeca_offset"], cf["cabeca_altura"], 0.0))
        perfil["centro_cabeca"] = {"no": n_cab, "xyz_mm": nos[n_cab], "u_mm": u_no(n_cab)}
        r["deslocamentos"] = perfil
        pts = pontos_de_carga(cf, ch)
        f = forcas_marcha()
        trab = 0.0
        for k, ponto in (("contacto_anca", pts["centro_cabeca"]), ("abdutores", pts["trocanter_topo"])):
            u = u_no(_no_mais_proximo(nos, ponto))
            trab += 0.5 * sum(fator * f[k][i] * u[i] / 1000.0 for i in range(3))
        en = 0.0
        for b in doc.GetBodies2(0, False):
            en += sum(v for _, v in pares_id_valor(res.GetStrainForEntities(8, 1, _nulo(), _ent([b]), err) or []))
        r.update({"trabalho_cargas_J": trab, "energia_total_J": en})
        if not implantado:
            cort = next(b for b in doc.GetBodies2(0, False) if _call0(b, "Name") == "Osso cortical")
            centros = centros_dos_elementos(mesh.GetElementDataFromEntity(cort, _int()))
            e1v = dict(pares_id_valor(res.GetStrainForEntities(9, 1, _nulo(), _ent([cort]), err)))
            e3v = dict(pares_id_valor(res.GetStrainForEntities(11, 1, _nulo(), _ent([cort]), err)))

            def faixa(y0, y1):
                ids = [i for i in e1v if y0 <= centros[i][1] <= y1]
                return {"n": len(ids), "E1_max_ue": max(e1v[i] for i in ids) * 1e6,
                        "E1_p95_ue": percentil([e1v[i] for i in ids], 95) * 1e6,
                        "E3_min_ue": min(e3v[i] for i in ids) * 1e6,
                        "E3_p5_ue": percentil([e3v[i] for i in ids], 5) * 1e6}
            r["deformacoes_cortical"] = {"diafise_-100_a_0": faixa(-100, 0), "proximal_0_a_100": faixa(0, 100),
                                         "todo": faixa(-1e9, 1e9)}
        out["casos"][rotulo] = r
        log.info("%s: %s", rotulo, json.dumps(r, ensure_ascii=False, default=str)[:3000])
        sw.late.CloseAllDocuments(True)  # sem gravar: os estudos de verificação não ficam nas peças
        (RAIZ / "results" / "fea_haste_sw_verificacoes.json").write_text(
            json.dumps(out, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    return out


def sensibilidade(sw: SwFEA, h: float = 5.0) -> dict:
    """Os cinco casos com o caso da marcha completo de Heller 2005 (mais tensor da fáscia lata e vasto lateral).

    Em linguagem simples: repete os estudos com a malha de 5 mm e com todos os músculos do caso da marcha, sem
    gravar as peças, para ver se a ordem dos materiais e as razões ao intacto mudam quando a flexão da diáfise
    diminui.
    """
    from win32com.client import Dispatch

    cf, ch = ler_cotas_femur(), cad.ler_cotas()
    E = ler_modulos_haste()
    base = {k: (v["E_GPa"] * 1e9, v["nu"]) for k, v in OSSO.items()}
    out = {"malhas_mm": [h], "casos": {}}
    for nome_caso, mat in [("Intacto", None)] + [(m, m) for m in MATERIAIS_HASTE]:
        implantado = mat is not None
        ficheiro = PASTA_FEA / ("fea_femur_haste.SLDPRT" if implantado else "fea_femur_intacto.SLDPRT")
        e1, e2 = _int(), _int()
        doc = sw.late.OpenDoc6(str(ficheiro), 1, 1, "", e1, e2)
        addin = sw.late.GetAddInObject("SldWorks.Simulation")
        if addin is None:
            sw.late.LoadAddIn(r"<pasta local> Corp\SOLIDWORKS\Simulation\cosworks.dll")
            addin = sw.late.GetAddInObject("SldWorks.Simulation")
        cw = Dispatch(addin).CosmosWorks
        mats = dict(base)
        if implantado:
            mats["Haste"] = (E[mat] * 1e9, NU_METAL)
        st, res, _, mesh = estudo(sw, doc, cw, f"Sens_{_curto(nome_caso)}", mats, implantado, h, cf, ch,
                                  completo=True)
        zonas, totais = energias_osso(doc, res, mesh, cf, ch)
        err = _int()
        ures = res.GetMinMaxDisplacement(3, 1, _nulo(), 0, err)
        r = {"nos": mesh.NodeCount, "elementos": mesh.ElementCount, "zonas": zonas, "energia_osso_J": totais,
             "ures_max_mm": ures[3], "vm_max_MPa": res.GetMinMaxStress(9, 0, 1, _nulo(), 3, err)[3]}
        if not implantado:
            cort = next(b for b in doc.GetBodies2(0, False) if _call0(b, "Name") == "Osso cortical")
            centros = centros_dos_elementos(mesh.GetElementDataFromEntity(cort, _int()))
            e1v = dict(pares_id_valor(res.GetStrainForEntities(9, 1, _nulo(), _ent([cort]), err)))
            e3v = dict(pares_id_valor(res.GetStrainForEntities(11, 1, _nulo(), _ent([cort]), err)))
            ids = [i for i in e1v if -100 <= centros[i][1] <= 0]
            r["deformacoes_diafise"] = {"E1_p95_ue": percentil([e1v[i] for i in ids], 95) * 1e6,
                                        "E3_p5_ue": percentil([e3v[i] for i in ids], 5) * 1e6}
        log.info("sensibilidade %s: Gruen 1 = %.4g J, Gruen 7 = %.4g J, URES máx = %.3f mm", nome_caso,
                 zonas[1]["energia_J"], zonas[7]["energia_J"], ures[3])
        out["casos"][nome_caso] = {str(h): r}
        sw.late.CloseAllDocuments(True)
        (RAIZ / "results" / "fea_haste_sw_sensibilidade.json").write_text(
            json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    return out


def _curto(nome):
    return {"Intacto": "Intacto", "Aço inox 316L": "Aco316L", "Co-Cr-Mo forjado": "CoCrMo",
            "Ti-6Al-4V ELI": "Ti6Al4V", "Ti-6Al-4V poroso": "Ti6Al4V_poroso"}[nome]


def imagens(sw, doc, res, rotulo):
    """Imagens, vistas de frente, dos mapas de von Mises e da densidade de energia de deformação do estudo ativo.

    Em linguagem simples: ativa o gráfico de tensões que a Simulation cria por omissão, grava-o em PNG, cria um
    gráfico da densidade de energia de deformação (por elemento) e grava-o também. As escalas de cores são as
    automáticas de cada estudo (não são iguais entre materiais).
    """
    PASTA_FIG.mkdir(parents=True, exist_ok=True)
    try:
        nomes = list(_call0(res, "GetPlotNames") or [])
        if nomes:
            res.ActivatePlot(nomes[0])
        _gravar_vista(doc, PASTA_FIG / f"{rotulo}_von_mises.png")
        err = _int()
        plot = res.CreatePlot(3, 7, 0, True, err)  # deformação, SEDENS, SI, por elemento
        nomes2 = list(_call0(res, "GetPlotNames") or [])
        if plot is not None and len(nomes2) > len(nomes):
            res.ActivatePlot(nomes2[-1])
            _gravar_vista(doc, PASTA_FIG / f"{rotulo}_densidade_energia.png")
        else:
            log.warning("gráfico de densidade de energia não criado (erro %s)", err.value)
    except Exception as exc:  # a imagem não deve parar os estudos
        log.warning("imagem falhou: %r", exc)


def _gravar_vista(doc, destino: Path):
    doc.ShowNamedView2("*Front", 1)
    doc.ViewZoomtofit2()
    ok = doc.Extension.SaveAs3(str(destino), 0, 1, _nulo(), _nulo(), _int(), _int())
    log.info("imagem %s (%s, existe: %s)", destino.name, ok, destino.exists())


def _gravar_json(resultados):
    RESULTADOS.parent.mkdir(parents=True, exist_ok=True)
    RESULTADOS.write_text(json.dumps(resultados, indent=1, ensure_ascii=False), encoding="utf-8")


def anatomico(sw: SwFEA) -> dict:
    """Tentativa com o fémur anatómico: importa o STL do FJ3365 como sólido e tenta malhá-lo na Simulation."""
    from win32com.client import Dispatch

    cf = ler_cotas_femur()
    v, f = femur_no_referencial_da_haste(cf)
    stl = PASTA_FEA / "femur_FJ3365.stl"
    PASTA_FEA.mkdir(parents=True, exist_ok=True)
    stl_binario(v, f, stl)
    sw.app.SetUserPreferenceIntegerValue(208, 2)  # swImportStlVrmlModelType = sólido
    sw.app.SetUserPreferenceIntegerValue(210, 0)  # unidades de importação: mm
    err = _int()
    t0 = time.time()
    doc = sw.late.LoadFile4(str(stl), "r", _nulo(), err)
    out = {"faces_stl": int(len(f)), "importado": doc is not None, "erro_import": err.value}
    if doc is None:
        return out
    corpos = list(doc.GetBodies2(0, False) or [])
    out["corpos_solidos"] = len(corpos)
    out["faces_corpo"] = len(list(_call0(corpos[0], "GetFaces"))) if corpos else 0
    out["segundos_import"] = round(time.time() - t0)
    destino = PASTA_FEA / "femur_FJ3365_solido.SLDPRT"
    doc.Extension.SaveAs3(str(destino), 0, 1, _nulo(), _nulo(), _int(), _int())
    if corpos:
        addin = sw.late.GetAddInObject("SldWorks.Simulation")
        if addin is None:
            sw.late.LoadAddIn(r"<pasta local> Corp\SOLIDWORKS\Simulation\cosworks.dll")
            addin = sw.late.GetAddInObject("SldWorks.Simulation")
        cw = Dispatch(addin).CosmosWorks
        st = cw.ActiveDoc.StudyManager.CreateNewStudy3("Teste_malha", 0, 0, err)
        st.Mesh.Quality = 1
        t0 = time.time()
        rc = st.CreateMesh(0, 5.0, 0.25)
        out.update({"malha_rc": rc, "malha_elementos": st.Mesh.ElementCount, "segundos_malha": round(time.time() - t0)})
        doc.Save3(1, _int(), _int())
    sw.late.CloseAllDocuments(True)
    log.info("anatómico: %s", out)
    return out


class VigiaDialogos:
    """Responde "No" ao aviso modal de deslocamentos excessivos da Simulation, que bloqueia o RunAnalysis.

    Em linguagem simples: de 2 em 2 segundos procura uma janela de diálogo com o título "Simulation" que tenha os
    botões Yes, No e Cancel e a ligação para o artigo QA00000118617 (o aviso de deslocamentos excessivos); carrega
    em "No", que manda acabar a análise linear sem passar a grandes deslocamentos (a opção que mantém as hipóteses
    do estudo). Cada clique fica no registo.
    """

    def __init__(self):
        import threading

        self.parar = threading.Event()
        self.cliques = 0
        self.fio = threading.Thread(target=self._ciclo, daemon=True)

    ativo = None

    def __enter__(self):
        VigiaDialogos.ativo = self
        self.fio.start()
        return self

    def __exit__(self, *exc):
        VigiaDialogos.ativo = None
        self.parar.set()
        self.fio.join(timeout=5)

    def _ciclo(self):
        import ctypes
        from ctypes import wintypes

        u = ctypes.windll.user32
        proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def texto(h):
            buf = ctypes.create_unicode_buffer(512)
            u.GetWindowTextW(h, buf, 512)
            return buf.value

        def classe(h):
            buf = ctypes.create_unicode_buffer(256)
            u.GetClassNameW(h, buf, 256)
            return buf.value

        while not self.parar.wait(2.0):
            dialogos = []
            u.EnumWindows(proc(lambda h, _l: (dialogos.append(h) if u.IsWindowVisible(h) and texto(h) == "Simulation"
                                              and classe(h) == "#32770" else None) or True), 0)
            for d in dialogos:
                filhos = []
                u.EnumChildWindows(d, proc(lambda h, _l: filhos.append(h) or True), 0)
                nomes = {texto(h): h for h in filhos}
                if {"Yes", "No", "Cancel"} <= set(nomes) and any("QA00000118617" in t for t in nomes):
                    u.SendMessageW(nomes["No"], 0x00F5, 0, 0)  # BM_CLICK
                    self.cliques += 1
                    log.warning("aviso de deslocamentos excessivos da Simulation respondido com No (n.º %d)",
                                self.cliques)


def main(argv=None) -> int:
    args = list(argv if argv is not None else sys.argv[1:]) or ["tudo"]
    malhas = [5.0, 3.5]
    if "--malhas" in args:
        malhas = [float(v) for v in args[args.index("--malhas") + 1].split(",")]
    qual = args[0]
    so = args[args.index("--casos") + 1].split(",") if "--casos" in args else None
    if qual == "resumo":
        resultados = json.loads(RESULTADOS.read_text(encoding="utf-8"))
        (RAIZ / "results" / "fea_haste_sw.md").write_text(resumo_markdown(resultados), encoding="utf-8")
        figura_gruen(resultados, PASTA_FIG / "gruen_razao_intacto")
        return 0
    PASTA_FEA.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S",
                        handlers=[logging.StreamHandler(sys.stdout),
                                  logging.FileHandler(PASTA_FEA / f"fea_solidworks_{qual}.log", mode="w",
                                                      encoding="utf-8")])
    sw = SwFEA()
    try:
        with VigiaDialogos():
            if qual == "anatomico":
                r = anatomico(sw)
                (PASTA_FEA / "anatomico.json").write_text(json.dumps(r, indent=1), encoding="utf-8")
            if qual in ("geometria", "tudo"):
                geometria(sw)
            if qual == "verificar":
                verificar(sw)
            if qual == "sensibilidade":
                sensibilidade(sw)
            if qual in ("estudos", "tudo"):
                estudos(sw, malhas, so)
        return 0
    finally:
        sw.fechar()


if __name__ == "__main__":
    sys.exit(main())
