"""Vídeo da FEA da haste femoral: os 4 materiais lado a lado, com a deformação ampliada e a tensão de von Mises.

Uso:
    python scripts/video_fea_haste.py [--saida PASTA] [--fator N] [--duracao S] [--fps N] [--so-fotograma]

Só lê os resultados que já existem (trabalho_fea\\mapdl\\<material>\\haste.rst); não resolve nada
de novo e não precisa de licença do Ansys. Reutiliza do mapas_von_mises_mapdl.py a leitura do .rst, a média
nodal por corpo, a escala de cores comum (MPa) e os nomes dos materiais.

Os deslocamentos são os nodais do .rst (em mm), multiplicados por um fator de ampliação escrito no ecrã. A
câmara faz uma órbita lenta de vaivém em torno do eixo vertical da haste, igual nos 4 painéis. Os 4 painéis
mostram o corte coronal (plano z = 0), como nos mapas estáticos.
"""
from __future__ import annotations

import argparse
import math
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

SAIDA_PADRAO = Path(r"partilha\videos_sim")
LARGURA, ALTURA = 1920, 1080
FPS_PADRAO = 30
DURACAO_PADRAO = 16.0
FATOR_PADRAO = 5
ORBITA_GRAUS = 30.0          # amplitude do vaivém da câmara (+/- graus)
RAMPA_S = 4.0                # a ampliação cresce de 0 ao valor final nestes segundos
ORDEM = ("Aco316L", "CoCrMo", "Ti6Al4V", "Ti6Al4V_poroso")
NOMES_CURTOS = {"Aco316L": "Aço inox 316L", "CoCrMo": "Co-Cr-Mo", "Ti6Al4V": "Ti-6Al-4V",
                "Ti6Al4V_poroso": "Ti-6Al-4V poroso"}
TITULO = "Haste femoral: deformação e tensão de von Mises"
AVISO = "Verificação numérica, não previsão clínica"
# layout em pixéis (origem no canto superior esquerdo)
TOPO_PAINEIS, BASE_PAINEIS = 215, 985
LARGURA_PAINEIS = 1780


# ---------------------------------------------------------------- funções puras (testadas)

def numero_de_fotogramas(duracao_s: float, fps: int) -> int:
    """Quantos fotogramas tem um vídeo: duração vezes fotogramas por segundo (arredondado)."""
    if duracao_s <= 0 or fps <= 0:
        raise ValueError("duração e fps têm de ser positivos")
    return int(round(duracao_s * fps))


def smoothstep(x: float) -> float:
    """Transição suave de 0 a 1 (0 abaixo de 0 e 1 acima de 1), sem arranques bruscos."""
    x = min(max(float(x), 0.0), 1.0)
    return x * x * (3.0 - 2.0 * x)


def rampa_deformacao(t: float, rampa_s: float = RAMPA_S) -> float:
    """Fração (0 a 1) da deformação mostrada no instante t: cresce suavemente durante `rampa_s` e fica em 1.

    Em linguagem simples: o vídeo começa com a haste sem deformação e a carga 'entra' devagar. Como o modelo
    é linear, a deformação é proporcional à carga, por isso mostrar frações do deslocamento é fiel."""
    if rampa_s <= 0:
        return 1.0
    return smoothstep(t / rampa_s)


def azimute_orbita(t: float, duracao_s: float, amplitude_graus: float = ORBITA_GRAUS) -> float:
    """Ângulo da câmara (graus) em torno do eixo vertical: vaivém sinusoidal, começa e acaba em 0.

    Em linguagem simples: a câmara anda um pouco para a esquerda, volta, vai para a direita e regressa ao
    ponto de partida, sempre com velocidade suave (o vídeo pode repetir-se sem salto)."""
    return float(amplitude_graus * math.sin(2.0 * math.pi * t / duracao_s))


def posicao_camara(centro: tuple[float, float, float], distancia: float, azimute_graus: float,
                   elevacao_graus: float = 0.0) -> tuple[float, float, float]:
    """Posição da câmara numa órbita em torno de `centro` (y é o eixo vertical; azimute 0 olha de +z)."""
    az, el = math.radians(azimute_graus), math.radians(elevacao_graus)
    cx, cy, cz = centro
    return (cx + distancia * math.cos(el) * math.sin(az),
            cy + distancia * math.sin(el),
            cz + distancia * math.cos(el) * math.cos(az))


def pontos_deformados(base: np.ndarray, desloc: np.ndarray, fator: float) -> np.ndarray:
    """Posições dos nós deformadas: base + fator * deslocamento (mm); o fator tem de ser finito."""
    if not np.isfinite(fator):
        raise ValueError("fator inválido")
    base = np.asarray(base, dtype=float)
    desloc = np.asarray(desloc, dtype=float)
    if base.shape != desloc.shape:
        raise ValueError("pontos e deslocamentos com formas diferentes")
    return base + fator * desloc


def escolher_fator(desloc_max_mm: float, alvo_mm: float = 60.0, opcoes=(2, 5, 10, 20, 50, 100)) -> int:
    """Fator de ampliação da lista `opcoes` que deixa o maior deslocamento mais perto de `alvo_mm`."""
    if desloc_max_mm <= 0:
        raise ValueError("o deslocamento máximo tem de ser positivo")
    return int(min(opcoes, key=lambda f: abs(f * desloc_max_mm - alvo_mm)))


def texto_fator(fator: float) -> str:
    """Texto do fator no ecrã, com sinal de vezes e vírgula decimal quando não é inteiro."""
    if abs(fator - round(fator)) < 0.05:
        return f"×{int(round(fator))}"
    return "×" + f"{fator:.1f}".replace(".", ",")


def legenda_material(chave: str, e_gpa: float | None, pico_mpa: float | None, desloc_mm: float) -> list[str]:
    """Linhas de texto de um painel: nome, módulo de Young, pico de von Mises da haste e deslocamento máximo."""
    from mapas_von_mises_mapdl import fmt_pt
    nome = NOMES_CURTOS.get(chave, chave)
    return [nome,
            "E = " + fmt_pt(e_gpa, 1) + " GPa",
            "pico da haste: " + fmt_pt(pico_mpa, 1) + " MPa",
            "desloc. máx.: " + fmt_pt(desloc_mm, 1) + " mm"]


def viewport_painel(i: int, n: int = 4, largura: int = LARGURA, largura_paineis: int = LARGURA_PAINEIS,
                    topo: int = TOPO_PAINEIS, base: int = BASE_PAINEIS, altura: int = ALTURA):
    """Viewport (x0, y0, x1, y1, fração 0 a 1, origem em baixo à esquerda) do painel i de n colunas iguais."""
    w = largura_paineis / n
    return (i * w / largura, 1.0 - base / altura, (i + 1) * w / largura, 1.0 - topo / altura)


# ---------------------------------------------------------------- leitura

def ler_deslocamentos(caminho: Path) -> np.ndarray:
    """Deslocamentos nodais (n_nós, 3) em mm do passo 0 do .rst, na mesma ordem dos nós usada em ler_caso."""
    import warnings
    warnings.filterwarnings("ignore")
    from ansys.mapdl import reader
    rst = reader.read_binary(str(caminho))
    nn, d = rst.nodal_displacement(0)
    if not np.array_equal(np.asarray(nn), np.asarray(rst.mesh.nnum)):
        raise ValueError("a ordem dos nós do deslocamento difere da da malha")
    out = np.asarray(d, dtype=float)
    del rst
    return out


def preparar_caso(chave: str, rst_dir: Path, escala_max: float | None = None) -> dict:
    """Lê um material e devolve, por corpo, a superfície do corte coronal com 'vm' e 'disp' nos nós.

    Em linguagem simples: corta o conjunto pelo plano z = 0 uma só vez (na forma sem deformação); o
    deslocamento de cada nó vai junto, para depois só mover os pontos em cada fotograma."""
    from mapas_von_mises_mapdl import (PLANO_CORTE_Z, grelha_do_corpo, ler_caso, maximos_por_corpo,
                                       media_nodal_por_corpo)
    caminho = rst_dir / chave / "haste.rst"
    c = ler_caso(caminho)
    disp = ler_deslocamentos(caminho)
    medias = media_nodal_por_corpo(c["conn"], c["tens"], c["corpo"], len(c["pontos"]))
    maximos = maximos_por_corpo(medias)
    superficies = []
    for corpo in (1, 2, 3):
        sel = c["corpo"] == corpo
        if not sel.any():
            continue
        g = grelha_do_corpo(c["pontos"], c["conn"][sel], medias[corpo])
        usados = np.unique(c["conn"][sel].ravel())
        g.point_data["disp"] = disp[usados]
        g = g.clip(normal=(0, 0, 1), origin=(0, 0, PLANO_CORTE_Z), invert=True)
        if g.n_cells == 0:
            continue
        s = g.extract_surface(algorithm="dataset_surface").clean()
        s.point_data["base"] = np.asarray(s.points).copy()
        superficies.append(s)
    return {"chave": chave, "E": c["E_haste_GPa"], "maximos": maximos, "superficies": superficies,
            "desloc_max": float(np.linalg.norm(disp, axis=1).max()),
            "p95_haste": float(np.nanpercentile(medias[3], 95)) if not np.all(np.isnan(medias[3])) else None,
            "limites": (c["pontos"].min(0), c["pontos"].max(0))}


# ---------------------------------------------------------------- imagem estática (texto, barra de cores)

def _registar_letra():
    """Regista a letra Inter do projeto no matplotlib e carrega o estilo dos gráficos."""
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import font_manager
    for f in (RAIZ / "design" / "fontes").glob("Inter-*.ttf"):
        font_manager.fontManager.addfont(str(f))
    import matplotlib.pyplot as plt
    plt.style.use(str(RAIZ / "design" / "biomat.mplstyle"))


def sobreposicao(casos: dict[str, dict], escala: dict, fator: float) -> "np.ndarray":
    """Imagem RGBA 1920x1080 com título, legendas, barra de cores e avisos; as zonas dos painéis ficam
    transparentes para se ver a renderização por baixo."""
    _registar_letra()
    import matplotlib.pyplot as plt
    from matplotlib import cm, colors
    from matplotlib.patches import Rectangle
    from mapas_von_mises_mapdl import fmt_pt, ticks_da_escala
    fig = plt.figure(figsize=(LARGURA / 100, ALTURA / 100), dpi=100)
    fig.patch.set_alpha(0.0)
    fundo = fig.add_axes([0, 0, 1, 1])
    fundo.set_xlim(0, LARGURA)
    fundo.set_ylim(ALTURA, 0)
    fundo.axis("off")
    fundo.patch.set_alpha(0.0)
    branco = dict(facecolor="white", edgecolor="none", zorder=0)
    fundo.add_patch(Rectangle((0, 0), LARGURA, TOPO_PAINEIS, **branco))
    fundo.add_patch(Rectangle((0, BASE_PAINEIS), LARGURA, ALTURA - BASE_PAINEIS, **branco))
    fundo.add_patch(Rectangle((LARGURA_PAINEIS, 0), LARGURA - LARGURA_PAINEIS, ALTURA, **branco))
    fundo.text(40, 52, TITULO, fontsize=30, fontweight="bold", color="#14171a", va="center")
    fundo.text(40, 100, f"Corte coronal, 4 materiais, mesma carga (pico da marcha) e mesma escala de cores. "
               f"Deformação ampliada {texto_fator(fator)}", fontsize=17, color="#3c4046", va="center")
    fundo.text(40, 134, "Modelo de elementos finitos linear (MAPDL, malha de 3,0 mm); interface osso-haste colada.",
               fontsize=14, color="#55595e", va="center")
    w = LARGURA_PAINEIS / len(ORDEM)
    for i, k in enumerate(ORDEM):
        c = casos[k]
        linhas = legenda_material(k, c["E"], c["maximos"].get("Haste"), c["desloc_max"])
        x = i * w + w / 2
        fundo.text(x, 168, linhas[0], fontsize=22, fontweight="bold", ha="center", va="center", color="#14171a")
        fundo.text(x, 198, linhas[1] + "   |   " + linhas[2].replace("pico da haste: ", "pico "),
                   fontsize=14.5, ha="center", va="center", color="#3c4046")
    # barra de cores
    cax = fig.add_axes([1822 / LARGURA, 1 - 880 / ALTURA, 26 / LARGURA, 560 / ALTURA])
    cb = fig.colorbar(cm.ScalarMappable(norm=colors.Normalize(escala["min"], escala["max"]), cmap="viridis"),
                      cax=cax, extend="max")
    pos, rot = ticks_da_escala(escala)
    cb.set_ticks(pos)
    cb.set_ticklabels(rot)
    cb.ax.tick_params(labelsize=15, length=5)
    cb.outline.set_linewidth(0.8)
    fundo.text(1835, 270, "von Mises\n(MPa)", fontsize=16, fontweight="bold", ha="center", va="center",
               color="#14171a")
    fundo.text(1835, 920, f"acima de {fmt_pt(escala['saturacao'], 0)}\nMPa a cor\nsatura", fontsize=12.5,
               ha="center", va="center", color="#55595e")
    # rodapé
    fundo.text(40, 1012, "Deslocamentos nodais lidos do .rst (mm) e multiplicados pelo fator indicado; "
               "a escala de cores é a dos valores reais de von Mises, sem ampliação.", fontsize=13.5,
               color="#55595e", va="center")
    fundo.text(40, 1044, AVISO, fontsize=19, fontweight="bold", color="#a23b00", va="center")
    fundo.text(LARGURA - 40, 1044, "Média nodal feita dentro de cada corpo; picos locais dependem da malha.",
               fontsize=13.5, color="#55595e", va="center", ha="right")
    fig.canvas.draw()
    img = np.asarray(fig.canvas.buffer_rgba()).copy()
    plt.close(fig)
    return img


# ---------------------------------------------------------------- renderização

def criar_plotter(casos: dict[str, dict], escala: dict):
    """Plotter fora do ecrã com os 4 painéis (viewports) e as malhas de cada material."""
    import pyvista as pv
    pl = pv.Plotter(off_screen=True, window_size=(LARGURA, ALTURA), shape=(1, len(ORDEM)), border=False)
    pl.set_background("white")
    for i, k in enumerate(ORDEM):
        pl.subplot(0, i)
        pl.set_background("white")
        for s in casos[k]["superficies"]:
            pl.add_mesh(s, scalars="vm", cmap="viridis", clim=(escala["min"], escala["max"]),
                        show_scalar_bar=False, smooth_shading=False, interpolate_before_map=True,
                        ambient=0.35, diffuse=0.65, specular=0.0)
        pl.renderers[i].SetViewport(*viewport_painel(i))
    return pl


def posicionar(pl, casos, centro, t, duracao, fator):
    """Deforma as malhas e coloca a câmara (igual nos 4 painéis) para o instante t."""
    f = fator * rampa_deformacao(t)
    az = azimute_orbita(t, duracao)
    pos = posicao_camara(centro, 900.0, az, 6.0)
    for i, k in enumerate(ORDEM):
        for s in casos[k]["superficies"]:
            s.points = pontos_deformados(s.point_data["base"], s.point_data["disp"], f)
        pl.subplot(0, i)
        pl.camera.position = pos
        pl.camera.focal_point = centro
        pl.camera.up = (0, 1, 0)
        pl.camera.view_angle = 21.0
        pl.camera.clipping_range = (300.0, 1800.0)
        pl.renderers[i].camera_set = True  # impede o pyvista de repor a câmara no primeiro render
    return f


def fotograma(pl, sobre: np.ndarray, f_atual: float, fator: float, t: float):
    """Fotograma final (RGB uint8): renderização + sobreposição + indicador do fator e do instante."""
    from PIL import Image, ImageDraw, ImageFont
    pl.render()
    base = Image.fromarray(pl.screenshot(return_img=True)).convert("RGBA")
    base.alpha_composite(Image.fromarray(sobre))
    d = ImageDraw.Draw(base)
    fonte = ImageFont.truetype(str(RAIZ / "design" / "fontes" / "Inter-Bold.ttf"), 22)
    d.text((LARGURA - 40, 52), f"deformação ampliada {texto_fator(f_atual)}", font=fonte, fill="#14171a",
           anchor="rm")
    fp = ImageFont.truetype(str(RAIZ / "design" / "fontes" / "Inter-Regular.ttf"), 15)
    d.text((LARGURA - 40, 84), f"fator final {texto_fator(fator)}", font=fp, fill="#55595e", anchor="rm")
    return np.asarray(base.convert("RGB"))


def correr(rst_dir: Path, saida: Path, fator: float | None, duracao: float, fps: int, so_fotograma: bool) -> dict:
    """Lê os 4 .rst, renderiza o vídeo (e o fotograma representativo) e devolve um resumo."""
    import imageio.v2 as imageio
    from mapas_von_mises_mapdl import escala_comum
    saida.mkdir(parents=True, exist_ok=True)
    casos = {k: preparar_caso(k, rst_dir) for k in ORDEM}
    # a escala é a mesma dos mapas estáticos: percentil 95 da haste mais esforçada (inclui o Intacto? não)
    escala = escala_comum([c["p95_haste"] for c in casos.values()])
    dmax = max(c["desloc_max"] for c in casos.values())
    if fator is None:
        fator = escolher_fator(dmax)
    lo = np.min([c["limites"][0] for c in casos.values()], axis=0)
    hi = np.max([c["limites"][1] for c in casos.values()], axis=0)
    centro = tuple(float(x) for x in (lo + hi) / 2)
    centro = (centro[0] - 4.0, centro[1], centro[2])  # a deformação puxa a haste para -x; desloca-se a órbita
    print("escala:", escala, "| fator:", fator, "| desloc. máx. (mm):", round(dmax, 2))
    sobre = sobreposicao(casos, escala, fator)
    pl = criar_plotter(casos, escala)
    n = numero_de_fotogramas(duracao, fps)
    # fotograma representativo: câmara a ~ +25 graus, ampliação completa
    t_rep = 0.0
    t_rep = max(t_rep, RAMPA_S + 0.5)
    f = posicionar(pl, casos, centro, t_rep, duracao, fator)
    imageio.imwrite(saida / "fea_fotograma.png", fotograma(pl, sobre, f, fator, t_rep))
    print("fotograma:", saida / "fea_fotograma.png", "az", round(azimute_orbita(t_rep, duracao), 1))
    if so_fotograma:
        pl.close()
        return {"fator": fator}
    destino = saida / "fea_haste_4materiais.mp4"
    w = imageio.get_writer(str(destino), fps=fps, codec="libx264", quality=None, macro_block_size=1,
                           ffmpeg_params=["-crf", "18", "-preset", "medium"])
    for i in range(n):
        t = i / fps
        f = posicionar(pl, casos, centro, t, duracao, fator)
        w.append_data(fotograma(pl, sobre, f, fator, t))
        if i % 60 == 0:
            print(f"fotograma {i}/{n}", flush=True)
    w.close()
    pl.close()
    versao_web(destino, saida / "fea_haste_4materiais_web.mp4")
    return {"fator": fator, "duracao": n / fps, "fps": fps}


def versao_web(origem: Path, destino: Path, limite_mb: float = 3.0) -> None:
    """Versão leve 1280x720 (H.264, sem áudio, faststart); baixa o débito até ficar abaixo de `limite_mb`."""
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    for crf in (20, 22, 24, 26, 28, 30, 32, 34, 36):
        subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(origem), "-vf", "scale=1280:720:flags=lanczos",
                        "-c:v", "libx264", "-crf", str(crf), "-preset", "slow", "-pix_fmt", "yuv420p", "-an",
                        "-movflags", "+faststart", str(destino)], check=True)
        mb = destino.stat().st_size / 1e6
        print(f"web crf {crf}: {mb:.2f} MB")
        if mb <= limite_mb:
            return


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rst-dir", type=Path, default=Path(r"trabalho_fea\mapdl"))
    ap.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    ap.add_argument("--fator", type=float, default=FATOR_PADRAO)
    ap.add_argument("--duracao", type=float, default=DURACAO_PADRAO)
    ap.add_argument("--fps", type=int, default=FPS_PADRAO)
    ap.add_argument("--so-fotograma", action="store_true")
    a = ap.parse_args()
    os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")
    print(correr(a.rst_dir, a.saida, a.fator, a.duracao, a.fps, a.so_fotograma))


if __name__ == "__main__":
    main()
