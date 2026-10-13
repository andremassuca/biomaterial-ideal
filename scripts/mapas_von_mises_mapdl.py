"""Mapas de von Mises da haste femoral a partir dos resultados do MAPDL (só leitura dos ficheiros .rst).

Uso:
    python scripts/mapas_von_mises_mapdl.py [--rst-dir PASTA] [--saida PASTA] [--json CAMINHO] [--so-json]

Entradas: <rst-dir>/<chave>/haste.rst para as chaves Intacto, Aco316L, CoCrMo, Ti6Al4V e Ti6Al4V_poroso
(malha de 3,0 mm, SOLID187). Não se resolve nada de novo e não é preciso licença do Ansys: o leitor
ansys-mapdl-reader abre os .rst diretamente.

Saídas (em --saida, por omissão results/figures/fea_mapdl/):
    <chave>_von_mises_frente.png, <chave>_von_mises_corte_coronal.png e comparacao_von_mises.png;
    results/fea_haste_mapdl_mapas.json com os máximos por corpo, a escala e os nomes dos ficheiros.

Método: a tensão de cada nó é a média dos elementos que o rodeiam, feita só dentro de cada corpo (cortical,
trabecular, haste), como no mapdl_haste.py (a média sobre todos os elementos mistura materiais na interface e
baixa o pico: 160,6 contra 171,9 MPa no 316L). São usados os 4 nós de canto de cada elemento.
Todas as figuras partilham a mesma câmara e a mesma escala de cores.
"""
from __future__ import annotations

import argparse
import json
import os
import warnings
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
RST_DIR_PADRAO = Path(r"trabalho_fea\mapdl")
SAIDA_PADRAO = RAIZ / "results" / "figures" / "fea_mapdl"
JSON_PADRAO = RAIZ / "results" / "fea_haste_mapdl_mapas.json"

# chave (nome da pasta) -> nome para mostrar nas figuras
CASOS = {
    "Intacto": "Fémur intacto (sem haste)",
    "Aco316L": "Haste de aço inox 316L",
    "CoCrMo": "Haste de Co-Cr-Mo",
    "Ti6Al4V": "Haste de Ti-6Al-4V",
    "Ti6Al4V_poroso": "Haste de Ti-6Al-4V poroso",
}
CORPOS = {1: "Osso cortical", 2: "Osso trabecular", 3: "Haste"}
MALHA_MM = 3.0
NOTA_MALHA = ("MAPDL, malha de 3,0 mm (SOLID187). Valores de pico locais dependem da malha; o pico fica junto a "
              "cantos e interfaces.")
NOTA_MEDIA = ("A média nodal é feita dentro de cada corpo (cortical, trabecular, haste), para não misturar "
              "materiais na interface.")
# máximos publicados (results/fea_haste_mapdl.md) para a validação, em MPa
PUBLICADO_MPA = {"Intacto": 48.3, "Aco316L": 171.9, "CoCrMo": 172.4, "Ti6Al4V": 167.1, "Ti6Al4V_poroso": 163.9}

# câmara comum (mm): corte pelo plano z = 0, que passa pelo centro do canal medular (a haste vai de z = -7,5 a
# 7,5 e o fémur de -25 a 25); o fémur vê-se de frente olhando de +z para -z, com y para cima
PLANO_CORTE_Z = 0.0
LARGURA_PX, ALTURA_PX = 780, 1800


# ---------------------------------------------------------------- funções puras (testadas)

def vm_de_tensor(tensores: np.ndarray) -> np.ndarray:
    """Tensão de von Mises a partir das 6 componentes (sx, sy, sz, sxy, syz, sxz), na última dimensão.

    Em linguagem simples: junta as 6 tensões de cada ponto num único número que diz quão "esforçado" está o
    material; é o valor que se compara com a resistência do metal."""
    t = np.asarray(tensores, dtype=float)
    sx, sy, sz, sxy, syz, sxz = (t[..., i] for i in range(6))
    return np.sqrt(0.5 * ((sx - sy) ** 2 + (sy - sz) ** 2 + (sz - sx) ** 2) + 3.0 * (sxy ** 2 + syz ** 2 + sxz ** 2))


def media_nodal_por_corpo(conectividade: np.ndarray, tensores: np.ndarray, corpo: np.ndarray, n_nos: int,
                          ids_corpos=(1, 2, 3)) -> dict[int, np.ndarray]:
    """von Mises nodal com a média das componentes feita só dentro de cada corpo.

    Em linguagem simples: cada nó recebe a tensão de vários elementos vizinhos. Na fronteira entre dois
    materiais, misturar as tensões dos dois baixa o pico; por isso faz-se a média separadamente em cada corpo.
    `conectividade` é (n_elem, k) com o índice (0 a n_nos-1) dos k nós de canto; `tensores` é (n_elem, k, 6);
    `corpo` é (n_elem,). Devolve, por corpo, um vetor de n_nos valores (NaN nos nós que o corpo não toca)."""
    conectividade = np.asarray(conectividade)
    tensores = np.asarray(tensores, dtype=float)
    corpo = np.asarray(corpo)
    saida = {}
    for c in ids_corpos:
        sel = corpo == c
        soma = np.zeros((n_nos, 6))
        cont = np.zeros(n_nos)
        if sel.any():
            nos = conectividade[sel].ravel()
            np.add.at(soma, nos, tensores[sel].reshape(-1, 6))
            np.add.at(cont, nos, 1.0)
        vm = np.full(n_nos, np.nan)
        usado = cont > 0
        vm[usado] = vm_de_tensor(soma[usado] / cont[usado, None])
        saida[c] = vm
    return saida


def maximos_por_corpo(medias: dict[int, np.ndarray]) -> dict[str, float | None]:
    """Máximo local de von Mises de cada corpo (None se o corpo não existe) e o global (o maior de todos)."""
    out: dict[str, float | None] = {}
    for c, v in medias.items():
        out[CORPOS.get(c, str(c))] = None if np.all(np.isnan(v)) else float(np.nanmax(v))
    vals = [x for x in out.values() if x is not None]
    out["Global"] = max(vals) if vals else None
    return out


def escala_comum(p95_por_caso: list[float], passo: float = 10.0) -> dict[str, float]:
    """Escala de cores comum a todas as figuras: de 0 ao maior percentil 95 da haste, arredondado para cima.

    Em linguagem simples: o pico de uma haste (cerca de 170 MPa) é só um canto; se a escala fosse até ao pico,
    o osso (até 48 MPa) e quase toda a haste ficariam com a mesma cor escura. Por isso a escala acaba onde
    ficam 95 % dos nós da haste mais esforçada (arredondado para cima a múltiplos de `passo`); acima disso a
    cor satura e a barra di-lo ('acima de X MPa'). O mínimo é 0 (sem tensão)."""
    if not p95_por_caso:
        raise ValueError("faltam percentis para definir a escala")
    topo = float(np.ceil(max(p95_por_caso) / passo) * passo)
    return {"min": 0.0, "max": topo, "saturacao": topo}


def fmt_pt(valor: float | None, casas: int = 1) -> str:
    """Número com vírgula decimal (formato português); 'n.d.' se não existir."""
    return "n.d." if valor is None else f"{valor:.{casas}f}".replace(".", ",")


def ticks_da_escala(escala: dict[str, float]) -> tuple[list[float], list[str]]:
    """Posições e rótulos da barra de cores: 0, 20, 40... e o último rótulo diz que acima dele a cor satura."""
    topo = escala["saturacao"]
    pos = [float(x) for x in np.arange(0, topo, 20.0) if x < topo - 10.0] + [topo]
    rot = [fmt_pt(p, 0) for p in pos[:-1]] + [f"{fmt_pt(topo, 0)}+"]
    return pos, rot


def nome_ficheiro(chave: str, vista: str) -> str:
    """Nome do PNG de uma chave e vista ('frente' ou 'corte_coronal')."""
    return f"{chave}_von_mises_{vista}.png"


def dentro_da_tolerancia(obtido: float, esperado: float, tol: float = 0.01) -> bool:
    """True se `obtido` difere de `esperado` menos de `tol` (fração; 0,01 = 1 %)."""
    return abs(obtido - esperado) <= tol * abs(esperado)


def montar_json(casos: dict[str, dict], escala: dict[str, float]) -> dict:
    """Estrutura final do JSON: um bloco por chave, a escala comum e a nota sobre a malha."""
    return {"nota": NOTA_MALHA + " " + NOTA_MEDIA, "escala_MPa": escala, "malha_mm": MALHA_MM, "casos": casos}


# ---------------------------------------------------------------- leitura do .rst

def ler_caso(caminho: Path) -> dict:
    """Lê um haste.rst: nós, tetraedros (4 nós de canto), corpo de cada elemento, tensões e E da haste.

    Em linguagem simples: o .rst guarda, para cada elemento, as 6 tensões nos cantos e o número do material
    (1 cortical, 2 trabecular, 3 haste). Os dois elementos de massa do ponto de carga (RBE3) não têm tensão e
    ficam de fora (só se aceitam elementos com 4 nós de canto)."""
    warnings.filterwarnings("ignore")
    from ansys.mapdl import reader
    rst = reader.read_binary(str(caminho))
    enum, es, enode = rst.element_stress(0, principal=False)
    mat = dict(zip(rst.grid.cell_data["ansys_elem_num"], rst.grid.cell_data["ansys_material_type"]))
    nnum = np.asarray(rst.mesh.nnum)
    pontos = np.asarray(rst.mesh.nodes, dtype=float)
    bons = [i for i, nd in enumerate(enode) if len(nd) == 4 and np.isfinite(es[i]).all()]
    conn = np.searchsorted(nnum, np.stack([enode[i] for i in bons]))
    tens = np.stack([es[i] for i in bons])
    corpo = np.array([mat[int(enum[i])] for i in bons], dtype=int)
    E3 = rst.materials.get(3, {}).get("EX")
    n_elem = int(sum(1 for t in rst.grid.cell_data["ansys_etype"] if t == 187))
    out = {"pontos": pontos, "conn": conn, "tens": tens, "corpo": corpo,
           "E_haste_GPa": None if E3 is None else float(E3) / 1000.0,
           "elementos": int(len(bons)), "nos": int(len(nnum)), "n_elem_187": n_elem}
    del rst
    return out


# ---------------------------------------------------------------- renderização

def grelha_do_corpo(pontos: np.ndarray, conn: np.ndarray, vm: np.ndarray):
    """Malha do pyvista (tetraedros lineares) de um corpo, com o von Mises nodal como escalar 'vm'."""
    import pyvista as pv
    usados, inv = np.unique(conn.ravel(), return_inverse=True)
    n = len(conn)
    celulas = np.hstack([np.full((n, 1), 4), inv.reshape(n, 4)]).ravel()
    g = pv.UnstructuredGrid(celulas, np.full(n, pv.CellType.TETRA), pontos[usados])
    g.point_data["vm"] = vm[usados]
    return g


def renderizar(caso: dict, medias: dict[int, np.ndarray], escala: dict[str, float], vista: str,
               camara: dict) -> np.ndarray:
    """Imagem (RGB) do conjunto visto de frente ou cortado pelo plano coronal, fora do ecrã."""
    import pyvista as pv
    pl = pv.Plotter(off_screen=True, window_size=(LARGURA_PX, ALTURA_PX))
    pl.set_background("white")
    for c in (1, 2, 3):
        sel = caso["corpo"] == c
        if not sel.any():
            continue
        g = grelha_do_corpo(caso["pontos"], caso["conn"][sel], medias[c])
        if vista == "corte_coronal":
            g = g.clip(normal=(0, 0, 1), origin=(0, 0, PLANO_CORTE_Z), invert=True)
            if g.n_cells == 0:
                continue
        sup = g.extract_surface(algorithm="dataset_surface").clean()
        pl.add_mesh(sup, scalars="vm", cmap="viridis", clim=(escala["min"], escala["max"]), show_scalar_bar=False,
                    smooth_shading=False, interpolate_before_map=True, show_edges=False, ambient=0.35,
                    diffuse=0.65, specular=0.0)
        if vista == "corte_coronal":
            # contorno fino de cada corpo na face do corte (só as arestas de fronteira da face plana)
            sn = sup.compute_normals(cell_normals=True, point_normals=False, auto_orient_normals=False)
            tampa = sn.extract_cells(np.nonzero(sn.cell_data["Normals"][:, 2] > 0.99)[0])
            if tampa.n_cells:
                arestas = tampa.extract_surface(algorithm="dataset_surface").extract_feature_edges(
                    boundary_edges=True, feature_edges=False, non_manifold_edges=False, manifold_edges=False)
                if arestas.n_cells:
                    pl.add_mesh(arestas, color="#1b1b1b", line_width=2.0)
    pl.enable_parallel_projection()
    cx, cy = camara["centro"]
    pl.camera_position = [(cx, cy, 500.0), (cx, cy, 0.0), (0, 1, 0)]
    pl.camera.parallel_scale = camara["meia_altura"]
    pl.enable_anti_aliasing("ssaa")
    img = pl.screenshot(return_img=True)
    pl.close()
    return img


def camara_comum(caminhos: list[Path]) -> dict:
    """Câmara igual para todos: centro e meia altura que cobrem os nós de todos os casos, com 3 % de margem."""
    warnings.filterwarnings("ignore")
    from ansys.mapdl import reader
    lo = np.full(3, np.inf)
    hi = np.full(3, -np.inf)
    for p in caminhos:
        rst = reader.read_binary(str(p))
        n = np.asarray(rst.mesh.nodes)
        lo, hi = np.minimum(lo, n.min(0)), np.maximum(hi, n.max(0))
        del rst
    return {"centro": ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2), "meia_altura": float((hi[1] - lo[1]) / 2 * 1.03)}


def caixa_comum(imagens: list[np.ndarray], margem: int = 12) -> tuple[int, int, int, int]:
    """Caixa (linha0, linha1, coluna0, coluna1) que contém todos os pixéis não brancos de todas as imagens.

    Em linguagem simples: as imagens têm muito fundo branco à volta do fémur; esta caixa, igual para todas
    (por isso a câmara continua a ser a mesma), serve para recortar e deixar o osso maior na figura final."""
    l0 = c0 = 10 ** 9
    l1 = c1 = 0
    for im in imagens:
        nao_branco = (np.asarray(im)[..., :3] < 245).any(axis=-1)
        ls, cs = np.nonzero(nao_branco)
        if len(ls):
            l0, l1, c0, c1 = min(l0, ls.min()), max(l1, ls.max()), min(c0, cs.min()), max(c1, cs.max())
    h, w = np.asarray(imagens[0]).shape[:2]
    return max(l0 - margem, 0), min(l1 + margem + 1, h), max(c0 - margem, 0), min(c1 + margem + 1, w)


def compor_figura(img: np.ndarray, titulo: str, subtitulo: str, maximos: dict, escala: dict, destino: Path) -> None:
    """Figura final 1600x1200: texto à esquerda, imagem ao centro, barra de cores à direita, rodapé em baixo."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import cm, colors
    fig = plt.figure(figsize=(16, 12), dpi=100)
    fig.patch.set_facecolor("white")
    fig.text(0.04, 0.945, titulo, fontsize=26, fontweight="bold", color="#111111", va="center")
    fig.text(0.04, 0.905, subtitulo, fontsize=18, color="#444444", va="center")
    ax = fig.add_axes([0.30, 0.095, 0.38, 0.80])
    ax.imshow(img)
    ax.axis("off")
    # texto à esquerda: máximo local de cada corpo
    fig.text(0.04, 0.74, "Máximo local de von Mises", fontsize=17, fontweight="bold", color="#111111")
    y = 0.70
    for nome in ("Haste", "Osso cortical", "Osso trabecular"):
        v = maximos.get(nome)
        if v is None:
            continue
        fig.text(0.04, y, nome, fontsize=16, color="#333333")
        fig.text(0.255, y, f"{fmt_pt(v)} MPa", fontsize=16, fontweight="bold", color="#111111", ha="right")
        y -= 0.045
    # barra de cores
    cax = fig.add_axes([0.78, 0.12, 0.022, 0.70])
    norm = colors.Normalize(escala["min"], escala["max"])
    cb = fig.colorbar(cm.ScalarMappable(norm=norm, cmap="viridis"), cax=cax, extend="max")
    pos, rot = ticks_da_escala(escala)
    cb.set_ticks(pos)
    cb.set_ticklabels(rot)
    cb.ax.tick_params(labelsize=16, length=6)
    cb.outline.set_linewidth(0.8)
    fig.text(0.79, 0.865, "Tensão de von Mises (MPa)", fontsize=17, fontweight="bold", color="#111111", ha="center")
    fig.text(0.79, 0.085, f"Acima de {fmt_pt(escala['saturacao'], 0)} MPa a cor satura", fontsize=14,
             color="#444444", ha="center")
    rodape = NOTA_MALHA + "\n" + NOTA_MEDIA + f" Escala comum a todos os materiais e vistas (0 a {fmt_pt(escala['max'], 0)} MPa)."
    fig.text(0.04, 0.03, rodape, fontsize=12.5, color="#555555", va="center", linespacing=1.5)
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino, dpi=100, facecolor="white")
    plt.close(fig)
    otimizar_png(destino)


def otimizar_png(caminho: Path, cores: int = 256) -> None:
    """Reduz o PNG para uma paleta de `cores` cores, sem ruído de dithering (fica bem mais leve)."""
    from PIL import Image
    im = Image.open(caminho).convert("RGB")
    q = im.quantize(colors=cores, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    q.save(caminho, optimize=True)


def montagem(imagens: dict[str, dict[str, np.ndarray]], textos: dict[str, tuple[str, dict]], escala: dict,
             destino: Path) -> None:
    """comparacao_von_mises.png: os materiais lado a lado (linha de cima: frente; baixo: corte), mesma câmara."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import cm, colors
    chaves = list(imagens)
    fig = plt.figure(figsize=(24, 14), dpi=100)
    fig.patch.set_facecolor("white")
    fig.text(0.02, 0.965, "Tensão de von Mises na haste e no fémur: materiais lado a lado", fontsize=26,
             fontweight="bold", color="#111111", va="center")
    larg = 0.84 / len(chaves)
    for j, k in enumerate(chaves):
        x0 = 0.02 + j * larg
        nome, mx = textos[k]
        fig.text(x0 + larg / 2, 0.915, nome, fontsize=16, fontweight="bold", ha="center", color="#111111")
        pico = mx.get("Haste") if mx.get("Haste") is not None else mx.get("Osso cortical")
        rot = "pico da haste" if mx.get("Haste") is not None else "pico do osso"
        fig.text(x0 + larg / 2, 0.885, f"{rot}: {fmt_pt(pico)} MPa", fontsize=14, ha="center", color="#333333")
        for i, vista in enumerate(("frente", "corte_coronal")):
            ax = fig.add_axes([x0, 0.50 - 0.40 * i + 0.0, larg, 0.38 + 0.0])
            ax.imshow(imagens[k][vista])
            ax.axis("off")
    for i, nome in enumerate(("Vista de frente", "Corte coronal")):
        fig.text(0.012, 0.69 - 0.40 * i + 0.0, nome, fontsize=14, rotation=90, va="center", color="#444444")
    cax = fig.add_axes([0.915, 0.15, 0.014, 0.68])
    cb = fig.colorbar(cm.ScalarMappable(norm=colors.Normalize(escala["min"], escala["max"]), cmap="viridis"),
                      cax=cax, extend="max")
    pos, rot_t = ticks_da_escala(escala)
    cb.set_ticks(pos)
    cb.set_ticklabels(rot_t)
    cb.ax.tick_params(labelsize=14)
    fig.text(0.92, 0.855, "Tensão de von Mises (MPa)", fontsize=15, fontweight="bold", ha="center", color="#111111")
    fig.text(0.92, 0.115, f"Acima de {fmt_pt(escala['saturacao'], 0)} MPa\na cor satura", fontsize=12,
             ha="center", color="#444444")
    fig.text(0.02, 0.035, NOTA_MALHA + "\n" + NOTA_MEDIA + " Mesma escala de cores e mesma câmara em todos os painéis.",
             fontsize=13, color="#555555", va="center", linespacing=1.5)
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino, dpi=100, facecolor="white")
    plt.close(fig)
    otimizar_png(destino, 256)


# ---------------------------------------------------------------- ponto de entrada

def correr(rst_dir: Path, saida: Path, caminho_json: Path, so_json: bool = False) -> dict:
    """Lê os 5 .rst (um de cada vez), valida os máximos, gera as figuras e o JSON; devolve o JSON."""
    caminhos = {k: rst_dir / k / "haste.rst" for k in CASOS}
    faltam = [str(p) for p in caminhos.values() if not p.exists()]
    if faltam:
        raise FileNotFoundError("faltam ficheiros .rst: " + ", ".join(faltam))
    # passo 1: máximos, percentis e câmara (um .rst de cada vez; as tensões não ficam em memória)
    resumo = {}
    p95 = []
    for k, p in caminhos.items():
        c = ler_caso(p)
        medias = media_nodal_por_corpo(c["conn"], c["tens"], c["corpo"], len(c["pontos"]))
        mx = maximos_por_corpo(medias)
        resumo[k] = {"maximos": mx, "E": c["E_haste_GPa"], "elementos": c["elementos"], "nos": c["nos"]}
        if k != "Intacto":
            p95.append(float(np.nanpercentile(medias[3], 95)))
        print(f"{k}: " + ", ".join(f"{n} {fmt_pt(v)}" for n, v in mx.items()))
        esperado = PUBLICADO_MPA[k]
        if not dentro_da_tolerancia(mx["Global"], esperado):
            print(f"  AVISO: máximo global {mx['Global']:.2f} difere do publicado {esperado} MPa (mais de 1 %)")
        del c, medias
    escala = escala_comum(p95)
    print("escala:", escala)
    casos_json = {}
    imagens, textos = {}, {}
    camara = None if so_json else camara_comum(list(caminhos.values()))
    if not so_json:
        for k, p in caminhos.items():
            c = ler_caso(p)
            medias = media_nodal_por_corpo(c["conn"], c["tens"], c["corpo"], len(c["pontos"]))
            imagens[k] = {v: renderizar(c, medias, escala, v, camara) for v in ("frente", "corte_coronal")}
            del c, medias
        l0, l1, c0, c1 = caixa_comum([im for d in imagens.values() for im in d.values()])
        imagens = {k: {v: im[l0:l1, c0:c1] for v, im in d.items()} for k, d in imagens.items()}
    for k in caminhos:
        r = resumo[k]
        nome = CASOS[k]
        e = r["E"]
        etiqueta = nome + (f" (E = {fmt_pt(e, 1)} GPa)" if e is not None else "")
        ficheiros = {"frente": nome_ficheiro(k, "frente"), "corte_coronal": nome_ficheiro(k, "corte_coronal")}
        if not so_json:
            for vista, sub in (("frente", "Vista de frente (plano coronal)"),
                               ("corte_coronal", "Corte coronal pelo centro do canal medular")):
                compor_figura(imagens[k][vista], etiqueta, sub, r["maximos"], escala, saida / ficheiros[vista])
            textos[k] = (nome if e is None else f"{nome}\nE = {fmt_pt(e, 1)} GPa", r["maximos"])
        casos_json[k] = {
            "material": nome, "E_haste_GPa": e,
            "vm_max_MPa": {n: (None if v is None else round(v, 3)) for n, v in r["maximos"].items()},
            "malha_mm": MALHA_MM, "elementos": r["elementos"], "nos": r["nos"], "escala_MPa": escala,
            "ficheiros": ficheiros,
        }
    if not so_json:
        montagem(imagens, textos, escala, saida / "comparacao_von_mises.png")
    dados = montar_json(casos_json, escala)
    dados["ficheiro_comparacao"] = "comparacao_von_mises.png"
    caminho_json.write_text(json.dumps(dados, indent=1, ensure_ascii=False), encoding="utf-8")
    return dados


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rst-dir", type=Path, default=RST_DIR_PADRAO)
    ap.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    ap.add_argument("--json", type=Path, default=JSON_PADRAO)
    ap.add_argument("--so-json", action="store_true", help="só calcula máximos e escreve o JSON (sem figuras)")
    a = ap.parse_args()
    os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")
    correr(a.rst_dir, a.saida, a.json, a.so_json)


if __name__ == "__main__":
    main()
