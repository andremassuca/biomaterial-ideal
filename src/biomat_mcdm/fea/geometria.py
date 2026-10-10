"""Referencial do fémur e da haste (o mesmo dos renders) e etiquetas das regiões numa grelha de vóxeis.

A posição da haste reproduz a de scripts/renders_blender.py (_cabeca_e_eixo e _montagem_anca): referencial
local com origem no centro da cabeça e o plano y = 0 no plano que contém o centro da cabeça e o eixo da
diáfise; a haste é posta por geometria_3d.colocar_haste com as cotas de design/cad/cotas.md. Aqui tudo se
passa para o referencial da haste (o do STL do SolidWorks): x lateral (positivo) e medial (negativo) no plano
frontal da haste, y ao longo da haste (ponta em y = 0), z normal a esse plano. Medidas em mm.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage

from .malha import dentro_da_malha, dentro_por_raios

# etiquetas da grelha
VAZIO, CORTICAL, TRABECULAR, HASTE, CABECA = 0, 1, 2, 3, 4
NOMES = {CORTICAL: "osso cortical", TRABECULAR: "osso trabecular", HASTE: "haste", CABECA: "cabeça"}

# parâmetros de desenho copiados da cena da anca dos renders (scripts/renders_blender.py, cena_anca)
CORTE_ABAIXO_PONTA = 100.0  # corte da diáfise, 100 mm abaixo da ponta da haste
DESLOCAMENTO_ALTURA = 146.0  # h = (altura a partir do centro da cabeça) + 146 mm
TRABECULAR_ACIMA_H = 50.0  # osso trabecular acima de h = 50 (96 mm abaixo da cabeça); abaixo, canal medular
OSTEOTOMIA_ALEM_BASE = 3.0  # plano da osteotomia 3 mm além da base do colo, normal ao eixo do colo
OSTEOTOMIA_RAIO = 24.0  # cilindro à volta do eixo do colo que limita a osteotomia (poupa o trocânter)


def espessura_cortical(h):
    """Espessura da camada cortical (mm) em função da altura h dos renders.

    Em linguagem simples: 4,8 mm na diáfise e 1,8 mm em cima (metáfise e cabeça), a afinar linearmente
    entre h = 55 e h = 95 (valores de desenho dos renders, ilustrativos).
    """
    return np.clip((95.0 - np.asarray(h, float)) / 40.0, 0.0, 1.0) * 3.0 + 1.8


def cabeca_e_eixo(vf):
    """Centro e raio da cabeça do fémur e eixo do canal na diáfise proximal (como nos renders).

    Em linguagem simples: ajusta uma esfera aos vértices do topo medial do fémur (refinando 4 vezes com os
    vértices perto da esfera) e tira o eixo principal dos vértices entre 70 e 230 mm abaixo da cabeça.
    """
    from ._scripts import geo

    vf = np.asarray(vf, float)
    topo = vf[:, 2].max()
    cand = vf[(vf[:, 2] > topo - 50) & (vf[:, 0] > np.percentile(vf[:, 0], 70))]
    H, r = geo.ajustar_esfera(cand)
    for _ in range(4):
        H, r = geo.ajustar_esfera(vf[np.abs(np.linalg.norm(vf - H, axis=1) - r) < 3])
    C0, a = geo.eixo_principal(vf[(vf[:, 2] > H[2] - 230) & (vf[:, 2] < H[2] - 70)])
    return H, r, C0, a


def montagem(vf_global, cotas: dict) -> dict:
    """Posição da haste no fémur e mudança para o referencial da haste.

    Em linguagem simples: repete os passos dos renders (referencial local, centro da cabeça, eixo do canal,
    colocar_haste) e devolve: os vértices do fémur no referencial da haste ('vf'), o centro e o raio da
    cabeça anatómica, a base e a direção do colo, e os eixos anatómicos (medial, anterior, proximal) também
    no referencial da haste, que servem para orientar as cargas.
    """
    from ._scripts import cad, geo

    vf_global = np.asarray(vf_global, float)
    H, r, C0, a = cabeca_e_eixo(vf_global)
    n = np.cross(H - C0, a)
    n /= np.linalg.norm(n)
    if n[1] > 0:  # anterior é y negativo no BodyParts3D
        n = -n
    ey = -n
    ez = np.array([0, 0, 1.0]) - ey[2] * ey
    ez /= np.linalg.norm(ez)
    ex = np.cross(ey, ez)
    R = np.array([ex, ey, ez])
    vl = vf_global @ R.T - R @ H
    H, r, C0, a = cabeca_e_eixo(vl)
    colo = cad.eixo_colo(cotas)
    T, s, med = geo.colocar_haste(H, C0, a, altura=colo["centro"][1], offset=cotas["haste_offset"])
    hx, hy = -med, s
    Q = np.array([hx, hy, np.cross(hx, hy)])  # linhas: eixos da haste no referencial local

    def para_haste(p):
        return (np.asarray(p, float) - T) @ Q.T

    anterior = Q @ (R @ np.array([0, -1.0, 0]))
    proximal = Q @ a
    anterior = anterior - (anterior @ proximal) * proximal
    anterior /= np.linalg.norm(anterior)
    Hh = para_haste(H)
    medial = np.cross(anterior, proximal)
    eixo_ponto = para_haste(C0)
    lado = (Hh - eixo_ponto) - ((Hh - eixo_ponto) @ proximal) * proximal
    if medial @ lado < 0:  # a cabeça fica do lado medial da diáfise
        medial = -medial
    d_colo = np.array([colo["direcao"][0], colo["direcao"][1], 0.0])
    base_colo = np.array([colo["base"][0], colo["base"][1], 0.0])
    return {"vf": para_haste(vl), "H": Hh, "r": r, "centro_haste": np.array([*colo["centro"], 0.0]),
            "d_colo": d_colo, "base_colo": base_colo, "medial": medial, "anterior": anterior,
            "proximal": proximal}


def grelha(vf, h: float, fator: int = 2, margem: float = 6.0, y_min: float = -CORTE_ABAIXO_PONTA):
    """Origem e dimensões da grelha de cálculo (passo h) e da grelha fina (passo h / fator).

    Em linguagem simples: uma caixa à volta da parte do fémur acima do corte da diáfise, com uma margem; as
    dimensões da grelha fina são múltiplas do fator para cada vóxel de cálculo conter fator^3 vóxeis finos.
    """
    vf = np.asarray(vf, float)
    acima = vf[vf[:, 1] >= y_min - margem]
    lo = acima.min(0) - margem
    hi = acima.max(0) + margem
    lo[1] = y_min  # a grelha começa exatamente no plano do corte
    forma = np.ceil((hi - lo) / h).astype(int)
    return lo, forma, forma * fator


def etiquetas(vf, faces, haste_v, haste_f, g: dict, origem, h_fino: float, forma_fina, implantado: bool,
              raio_cabeca_protese: float) -> np.ndarray:
    """Etiqueta de cada vóxel fino: vazio, osso cortical, osso trabecular, haste ou cabeça da prótese.

    Em linguagem simples: o interior do fémur vem do teste de raios; a profundidade de cada ponto é a
    distância à superfície do osso; a camada exterior com a espessura dos renders é cortical; por dentro,
    acima da altura h = 50, é trabecular e abaixo é canal medular (vazio, hipótese). Com a haste, retira-se a
    cabeça e o colo (osteotomia) e põe-se a haste e a cabeça da prótese.
    """
    origem = np.asarray(origem, float)
    forma_fina = tuple(int(v) for v in forma_fina)
    # o teste de interior faz-se numa grelha que desce 10 mm abaixo do corte: assim o corte não cria uma
    # "tampa" cortical (a profundidade mede-se só até à superfície anatómica)
    extra = int(np.ceil(10.0 / h_fino))
    origem_ext = origem - np.array([0, extra * h_fino, 0])
    forma_ext = (forma_fina[0], forma_fina[1] + extra, forma_fina[2])
    dentro = dentro_da_malha(vf, faces, origem_ext, h_fino, forma_ext)
    prof = ndimage.distance_transform_edt(dentro, sampling=h_fino) - h_fino / 2
    dentro, prof = dentro[:, extra:, :], prof[:, extra:, :]
    eixos = [origem[i] + h_fino * (np.arange(forma_fina[i]) + 0.5) for i in range(3)]
    X, Y, Z = np.meshgrid(*eixos, indexing="ij", sparse=True)
    altura = (Y - g["H"][1]) + DESLOCAMENTO_ALTURA
    esp = espessura_cortical(altura)
    et = np.zeros(forma_fina, np.int8)
    et[dentro & (prof < esp)] = CORTICAL
    et[dentro & (prof >= esp) & (altura > TRABECULAR_ACIMA_H)] = TRABECULAR
    if implantado:
        d, b = g["d_colo"], g["base_colo"]
        plano = (X - (b[0] + OSTEOTOMIA_ALEM_BASE * d[0])) * d[0] + (Y - (b[1] + OSTEOTOMIA_ALEM_BASE * d[1])) * d[1] \
            + (Z - b[2]) * d[2]
        # distância ao segmento do eixo do colo (de 60 mm antes a 90 mm depois da base), como a cápsula dos renders
        t = np.clip((X - b[0]) * d[0] + (Y - b[1]) * d[1] + (Z - b[2]) * d[2], -60.0, 90.0)
        dist = np.sqrt((X - b[0] - t * d[0]) ** 2 + (Y - b[1] - t * d[1]) ** 2 + (Z - b[2] - t * d[2]) ** 2)
        et[(plano > 0) & (dist < OSTEOTOMIA_RAIO)] = VAZIO
        c = g["centro_haste"]
        cabeca = (X - c[0]) ** 2 + (Y - c[1]) ** 2 + (Z - c[2]) ** 2 < raio_cabeca_protese ** 2
        et[cabeca] = CABECA
        et[dentro_por_raios(haste_v, haste_f, origem, h_fino, forma_fina, eixo=1)] = HASTE
    return et


def ler_stl(caminho):
    """Lê um STL binário e funde os vértices repetidos (o SolidWorks grava cada triângulo solto).

    Em linguagem simples: devolve vértices (n, 3) e triângulos (m, 3) como os de geometria_3d.ler_obj.
    """
    import struct

    dados = open(caminho, "rb").read()
    n = struct.unpack("<I", dados[80:84])[0]
    reg = np.frombuffer(dados[84:84 + 50 * n], dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
    pts = reg["v"].reshape(-1, 3).astype(float)
    unicos, inv = np.unique(np.round(pts, 4), axis=0, return_inverse=True)
    return unicos, inv.reshape(-1, 3)
