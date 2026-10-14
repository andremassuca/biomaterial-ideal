"""Vídeo da CFD do stent (Pt-Cr 79 µm contra 316L 135 µm, sangue de Carreau, 2.º ciclo cardíaco).

Usa só resultados que já existem em trabalho_cfd (nenhuma simulação nova):
  - mapa da TAWSS na parede: campo "mag(wallShearStress)Mean", média do 2.º ciclo (1,06 a 2,12 s);
  - linhas de corrente: campo de velocidade U gravado só no instante t = 2,12 s (fim do 2.º ciclo);
  - séries no tempo (postProcessing): caudal à entrada e tensão de corte média da parede, passo a passo.
Não existe mais nenhum campo 3D ou de parede ao longo do ciclo, por isso o vídeo NÃO anima o campo:
os mapas e as linhas de corrente são fixos e o que se move é o cursor do ciclo sobre as séries reais.

Uso:
    python scripts/video_cfd_stent.py            # gera o vídeo completo, a versão web e o fotograma
    python scripts/video_cfd_stent.py --teste    # só dois fotogramas (verificação rápida)
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

TRABALHO = Path(r"trabalho_cfd")
SAIDA = Path(r"partilha\videos_sim")
RHO = 1060.0  # kg/m3 (a tensão guardada pelo OpenFOAM é cinemática: m2/s2)
LIMIAR_PA = 0.4  # limiar operacional do estudo (Malek et al., JAMA 1999)
ESCALA_MAX_PA = 1.0  # mesma escala de cores nos dois casos: 0 a 1 Pa
T_INICIO, T_FIM = 1.06, 2.12  # 2.º ciclo (período de 1,06 s)
PERIODO = T_FIM - T_INICIO
FPS, LARGURA, ALTURA = 30, 1920, 1080
S_INICIO, S_VARRIMENTO, S_FIM = 1.5, 12.0, 2.5  # segundos de vídeo: espera, ciclo, espera

CASOS = {
    "Pt-Cr": {"pasta": "pulsatil_Pt-Cr_media_1000_carreau", "titulo": "Pt-Cr, strut fino de 79 µm",
              "cor": "#0072B2"},
    "316L": {"pasta": "pulsatil_316L_media_1000_carreau", "titulo": "Aço 316L, strut grosso de 135 µm",
             "cor": "#D55E00"},
}
FUNDO, TEXTO, TEXTO_2 = "#f7f6f2", "#14171a", "#55595e"
COR_LIMIAR = "#c1121f"


# ----------------------------------------------------------------------------- funções puras

def fmt_pt(x: float, casas: int = 2) -> str:
    """Número com vírgula decimal (0,51) e sinal menos tipográfico."""
    return f"{x:.{casas}f}".replace(".", ",").replace("-", "−")


def velocidade_cm_s(caudal_m3_s: np.ndarray | float, area_m2: float) -> np.ndarray | float:
    """Velocidade média na entrada (cm/s) a partir do caudal (m3/s) e da área (m2); o sinal do caudal não conta."""
    return np.abs(caudal_m3_s) / area_m2 * 100.0


def fase_do_ciclo(t: float, t0: float = T_INICIO, periodo: float = PERIODO) -> float:
    """Fase do ciclo em % (0 no início do 2.º ciclo, 100 no fim)."""
    return float(np.clip((t - t0) / periodo, 0.0, 1.0) * 100.0)


def tempo_do_quadro(i: int, fps: int = FPS, s_inicio: float = S_INICIO, s_varrimento: float = S_VARRIMENTO,
                    t0: float = T_INICIO, periodo: float = PERIODO) -> float:
    """Instante do ciclo (s) mostrado no quadro i: espera no início, varrimento do ciclo, espera no fim."""
    s = i / fps
    f = np.clip((s - s_inicio) / s_varrimento, 0.0, 1.0)
    return float(t0 + f * periodo)


def n_quadros(fps: int = FPS, s_inicio: float = S_INICIO, s_varrimento: float = S_VARRIMENTO,
              s_fim: float = S_FIM) -> int:
    """Número total de quadros do vídeo."""
    return int(round((s_inicio + s_varrimento + s_fim) * fps))


def recortar(t: np.ndarray, y: np.ndarray, t0: float = T_INICIO, t1: float = T_FIM) -> tuple[np.ndarray, np.ndarray]:
    """Fica só com os pontos da série entre t0 e t1 (inclusive, com folga de 1e-9)."""
    m = (t >= t0 - 1e-9) & (t <= t1 + 1e-9)
    return t[m], y[m]


def valor_em(t: np.ndarray, y: np.ndarray, instante: float) -> float:
    """Valor da série no instante dado (interpolação linear entre os dois passos vizinhos, sem sair da série)."""
    return float(np.interp(instante, t, y))


def percentagem_abaixo(valores: np.ndarray, areas: np.ndarray, limiar: float = LIMIAR_PA) -> float:
    """Percentagem da área onde o valor fica abaixo do limiar (0 a 100)."""
    valores, areas = np.asarray(valores), np.asarray(areas, dtype=float)
    return float(100.0 * areas[valores < limiar].sum() / areas.sum())


def media_ponderada(valores: np.ndarray, pesos: np.ndarray) -> float:
    """Média dos valores ponderada pela área de cada face."""
    return float((np.asarray(valores) * np.asarray(pesos)).sum() / np.asarray(pesos).sum())


def texto_instante(t: float) -> str:
    """Texto do instante no ecrã, por exemplo 't = 1,62 s (fase 53 % do 2.º ciclo)'."""
    return f"t = {fmt_pt(t, 2)} s (fase {fmt_pt(fase_do_ciclo(t), 0)} % do 2.º ciclo)"


# ----------------------------------------------------------------------------- leitura dos resultados

def ler_serie(nome: str, pasta: str) -> np.ndarray:
    """Lê uma série do postProcessing (tempo, valor)."""
    return np.loadtxt(TRABALHO / nome / "postProcessing" / pasta / "0" / "surfaceFieldValue.dat", comments="#")


def area_entrada(nome: str) -> float:
    """Área da entrada (m2) escrita no cabeçalho da série do caudal."""
    for linha in (TRABALHO / nome / "postProcessing" / "caudais" / "0" / "surfaceFieldValue.dat").read_text().splitlines():
        if linha.startswith("# Area"):
            return float(linha.split(":")[1])
    raise ValueError("área da entrada não encontrada")


def ler_parede(nome: str) -> dict:
    """Parede da artéria: TAWSS (Pa) por face, áreas, polígonos desenrolados e janela do stent."""
    from biomat_mcdm.cfd import posproc as pp

    meta = json.loads((TRABALHO / nome / "caso.json").read_text(encoding="utf-8"))
    st = meta["stent"]
    z0 = st["z0_mm"] / 1000
    z1 = (st["z0_mm"] + st["n_aneis"] * st["altura_anel_mm"]) / 1000
    pasta = next((TRABALHO / nome / "VTK").glob("*_2000")) / "boundary"
    w = pp.ler(pasta / "parede.vtp").compute_cell_sizes()
    centros = np.asarray(w.cell_centers().points)
    area = np.asarray(w.cell_data["Area"])
    tau = RHO * np.asarray(w.cell_data["mag(wallShearStress)Mean"])
    k = pp.janela_z(centros, z0, z1)
    pol = [pp.desenrolar(np.asarray(w.get_cell(i).points), meta["stent"]["raio_mm"] / 1000) * 1000
           for i in range(w.n_cells)]
    return {"tau": tau, "area": area, "k": k, "poligonos": pol, "z0": z0 * 1000, "z1": z1 * 1000,
            "espessura_um": st["espessura_um"], "raio_mm": st["raio_mm"], "mesh": w, "pasta": pasta,
            "tawss": media_ponderada(tau[k], area[k]), "abaixo": percentagem_abaixo(tau[k], area[k])}


def preparar_caso_leitura(nome: str, destino: Path) -> Path:
    """Monta numa pasta temporária um caso mínimo (malha final + campos de t = 2,12 s) para o leitor do OpenFOAM."""
    c = destino / nome
    if c.exists():
        shutil.rmtree(c)
    (c / "constant").mkdir(parents=True)
    (c / "system").mkdir()
    shutil.copytree(TRABALHO / nome / "polyMesh_final", c / "constant" / "polyMesh")
    shutil.copytree(TRABALHO / nome / "ultimo", c / "2.12")
    for f in ("controlDict", "fvSchemes", "fvSolution"):
        shutil.copy(TRABALHO / nome / "system" / f, c / "system" / f)
    (c / "c.foam").write_text("", encoding="utf-8")
    return c / "c.foam"


# ----------------------------------------------------------------------------- 3D (pyvista)

def render_3d(nome: str, parede: dict, tmp: Path, tam: tuple[int, int]) -> np.ndarray:
    """Imagem do meio tubo visto por dentro: parede pintada com a TAWSS, struts a cinzento e linhas de corrente (t = 2,12 s)."""
    import pyvista as pv

    pv.OFF_SCREEN = True
    leitor = pv.OpenFOAMReader(str(preparar_caso_leitura(nome, tmp)))
    leitor.set_active_time_value(2.12)
    interno = leitor.read()["internalMesh"]
    r_mm = parede["raio_mm"] / 1000
    # sementes na entrada: duas coroas (junto à parede, onde há recirculação, e a meio do raio)
    sem = []
    for raio, angs in ((0.45, (0.19,)), (0.70, (0.19,)), (0.85, (0.1, 0.28)), (0.92, (0.06, 0.19, 0.32)),
                       (0.97, (0.04, 0.12, 0.19, 0.26, 0.34)), (0.99, (0.08, 0.30))):
        for ang in angs:
            sem.append((raio * r_mm * np.cos(ang), raio * r_mm * np.sin(ang), 4e-5))
    linhas = interno.streamlines_from_source(pv.PolyData(np.array(sem)), vectors="U", max_length=0.02,
                                             initial_step_length=0.02, integration_direction="forward",
                                             terminal_speed=1e-9, max_step_length=0.5, max_steps=20000)
    tubos = linhas.tube(radius=5e-6) if linhas.n_points else linhas
    struts = pv.read(str(parede["pasta"] / "struts.vtp"))
    w = parede["mesh"].copy()
    w.clear_data()
    w.cell_data["TAWSS"] = parede["tau"]

    def meio_tubo(m):
        pares = [m, m.reflect((0, 1, 0), inplace=False)]
        return [p.rotate_z(45.0 * k, point=(0, 0, 0), inplace=False) for k in range(4) for p in pares]

    pl = pv.Plotter(off_screen=True, window_size=list(tam))
    pl.set_background(FUNDO)
    for p in meio_tubo(w):
        pl.add_mesh(p, scalars="TAWSS", cmap="viridis", clim=(0, ESCALA_MAX_PA), show_scalar_bar=False,
                    lighting=False)
    for p in meio_tubo(struts):
        pl.add_mesh(p, color="#8d939a", smooth_shading=True)
    for p in meio_tubo(tubos):
        pl.add_mesh(p, color="#ffffff", lighting=False)
    pl.camera_position = [(0, -0.03, 0.00377), (0, 0.0, 0.00377), (-1, 0, 0)]
    pl.enable_parallel_projection()
    pl.camera.parallel_scale = 0.00175
    pl.camera.focal_point = (-0.0001, 0, 0.00377)
    pl.camera.position = (-0.0001, -0.03, 0.00377)
    pl.render()
    img = np.asarray(pl.screenshot(return_img=True))
    pl.close()
    return img


# ----------------------------------------------------------------------------- composição dos quadros

class Quadro:
    """Figura única do vídeo; em cada quadro só mudam o cursor, o instante e os valores instantâneos."""

    def __init__(self, dados: dict, imagens: dict):
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.collections import PolyCollection
        from matplotlib.colors import Normalize
        from matplotlib.tri import Triangulation
        import estilo_graficos as eg

        eg.aplicar("clara")
        plt.rcParams.update({"axes.facecolor": "none", "figure.facecolor": FUNDO, "savefig.transparent": False})
        self.plt, self.dados = plt, dados
        self.fig = plt.figure(figsize=(LARGURA / 100, ALTURA / 100), dpi=100, facecolor=FUNDO)
        norm = Normalize(0, ESCALA_MAX_PA)

        def eixo(x, y, w, h, **kw):
            """Eixos em píxeis (origem no canto superior esquerdo)."""
            return self.fig.add_axes([x / LARGURA, 1 - (y + h) / ALTURA, w / LARGURA, h / ALTURA], **kw)

        def texto(x, y, s, **kw):
            return self.fig.text(x / LARGURA, 1 - y / ALTURA, s, **kw)

        texto(40, 52, "Stent coronário: tensão de corte na parede ao longo do 2.º ciclo cardíaco", fontsize=27,
              fontweight="bold", va="center")
        texto(40, 88, "Sangue de Carreau (não newtoniano), parede rígida, geometria idealizada; sangue da esquerda para a direita",
              fontsize=14.5, color=TEXTO_2, va="center")
        self.fig.patches.append(plt.Rectangle((1478 / LARGURA, 1 - 100 / ALTURA), 402 / LARGURA, 62 / ALTURA,
                                              transform=self.fig.transFigure, facecolor="#fff1d6", edgecolor="#c98a00",
                                              linewidth=1.2))
        texto(1679, 69, "Verificação numérica,\nnão previsão clínica", fontsize=15, ha="center", va="center",
              fontweight="bold", color="#7a5200", linespacing=1.15)

        self.vivos = {}
        colunas = {"Pt-Cr": 40, "316L": 990}
        for mat, x0 in colunas.items():
            d, cfg = dados[mat], CASOS[mat]
            texto(x0, 128, cfg["titulo"], fontsize=21, fontweight="bold", color=cfg["cor"], va="center")
            self.fig.add_artist(plt.Line2D([x0 / LARGURA, (x0 + 890) / LARGURA], [1 - 146 / ALTURA] * 2,
                                           color=cfg["cor"], linewidth=2.2))
            ax3 = eixo(x0, 152, 890, 272)
            ax3.imshow(imagens[mat], aspect="auto")
            ax3.axis("off")
            texto(x0 + 4, 300, "escoamento\n→", fontsize=12, color=TEXTO_2, va="center", linespacing=1.1)
            texto(x0 + 6, 164, "Linhas de corrente (brancas) e TAWSS na parede, vista por dentro", fontsize=11.5,
                  color="#ffffff", va="center", fontweight="bold",
                  bbox=dict(facecolor="#14171a", alpha=0.55, edgecolor="none", pad=3))
            texto(x0 + 884, 412, "campo de velocidade do instante t = 2,12 s", fontsize=11.5, color="#ffffff",
                  va="center", ha="right", bbox=dict(facecolor="#14171a", alpha=0.55, edgecolor="none", pad=3))
            # mapa desenrolado
            ax = eixo(x0 + 50, 452, 840, 112)
            pol = d["poligonos"]
            espelho = [q * np.array([-1, 1]) for q in pol]
            cores = np.concatenate([d["tau"], d["tau"]])
            pc = PolyCollection([q[:, ::-1] for q in pol + espelho], array=cores, cmap="viridis", norm=norm,
                                edgecolors="face", linewidths=0.1)
            ax.add_collection(pc)
            cx = np.array([q[:, 1].mean() for q in pol])
            cy = np.array([q[:, 0].mean() for q in pol])
            tri = Triangulation(np.concatenate([cx, cx]), np.concatenate([cy, -cy]))
            xs, ys = tri.x[tri.triangles], tri.y[tri.triangles]
            lados = np.max(np.hypot(xs - np.roll(xs, 1, axis=1), ys - np.roll(ys, 1, axis=1)), axis=1)
            tri.set_mask(lados > 0.07)  # não atravessa os struts
            ax.tricontour(tri, cores, levels=[LIMIAR_PA], colors=COR_LIMIAR, linewidths=2.2)
            ax.set_facecolor("#9aa0a6")
            a = d["raio_mm"] * np.pi / 8
            ax.set_xlim(d["z0"] - 0.5, d["z1"] + 1.6)
            ax.set_ylim(-a, a)
            ax.set_yticks([])
            ax.set_xlabel("Comprimento ao longo da artéria (mm)", fontsize=11, labelpad=2)
            ax.tick_params(labelsize=10, pad=2)
            ax.grid(False)
            for s in ("left", "bottom"):
                ax.spines[s].set_visible(True)
            ax.set_title("Mapa da parede aberta: TAWSS média do 2.º ciclo (linha vermelha: 0,4 Pa; dentro dos losangos fica abaixo)", fontsize=12,
                         loc="left", fontweight="normal", pad=4)
            texto(x0, 632, f"Parede abaixo de 0,4 Pa: {fmt_pt(d['abaixo'], 1)} %   |   TAWSS média: {fmt_pt(d['tawss'], 3)} Pa",
                  fontsize=17, fontweight="bold", va="center")
            self.vivos[mat] = texto(x0, 660, "", fontsize=14.5, color=TEXTO_2, va="center")

        # escala de cores comum
        cax = eixo(560, 686, 800, 16)
        cb = self.fig.colorbar(pc, cax=cax, orientation="horizontal")
        cb.set_ticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
        cb.set_ticklabels(["0", "0,2", "0,4", "0,6", "0,8", "1,0"])
        cb.ax.tick_params(labelsize=11.5, length=3)
        cb.outline.set_linewidth(0.6)
        cax.axvline(LIMIAR_PA, color=COR_LIMIAR, linewidth=3.2)
        texto(540, 694, "TAWSS (Pa)", fontsize=14, ha="right", va="center", fontweight="bold")
        texto(560 + 800 * LIMIAR_PA / ESCALA_MAX_PA, 678, "limiar 0,4 Pa", fontsize=12.5, color=COR_LIMIAR,
              ha="center", va="center", fontweight="bold")
        texto(1378, 694, "escala igual nos dois casos (acima de 1 Pa: cor máxima)", fontsize=11, color=TEXTO_2,
              va="center")

        # séries no tempo com cursor
        c = dados["caudal"]
        self.axq = eixo(100, 790, 700, 158)
        self.axw = eixo(960, 790, 900, 158)
        self.axq.plot(c[0], c[1], color="#3c4046", linewidth=2.0)
        self.axq.set_ylabel("Velocidade média\nna entrada (cm/s)", fontsize=11.5)
        self.axq.set_title("Escoamento imposto (igual nos dois casos)", fontsize=13, loc="left", pad=6)
        for mat in CASOS:
            tt, ww = dados[mat]["wss_t"]
            self.axw.plot(tt, ww, color=CASOS[mat]["cor"], linewidth=2.0, label=CASOS[mat]["titulo"].split(",")[0])
        self.axw.axhline(LIMIAR_PA, color=COR_LIMIAR, linewidth=1.6, linestyle="--")
        self.axw.text(T_INICIO + 0.01, LIMIAR_PA + 0.03, "0,4 Pa", color=COR_LIMIAR, fontsize=11.5, ha="left",
                      va="bottom", fontweight="bold")
        self.axw.set_ylabel("Tensão de corte média\nda parede (Pa)", fontsize=11.5)
        self.axw.set_title("Tensão de corte média na parede do modelo todo (instantânea)", fontsize=13, loc="left", pad=6)
        self.axw.legend(loc="upper left", fontsize=11, ncol=2, bbox_to_anchor=(0.0, 1.02))
        for ax in (self.axq, self.axw):
            ax.set_xlim(T_INICIO, T_FIM)
            ax.set_xlabel("Tempo (s)", fontsize=11.5)
            ax.xaxis.set_major_formatter(lambda v, _p: fmt_pt(v, 2))
            ax.yaxis.set_major_formatter(lambda v, _p: fmt_pt(v, 1))
        self.cursores = [ax.axvline(T_INICIO, color=TEXTO, linewidth=1.6) for ax in (self.axq, self.axw)]
        self.ponto_q, = self.axq.plot([T_INICIO], [0], "o", color=TEXTO, markersize=8)
        self.pontos_w = {m: self.axw.plot([T_INICIO], [0], "o", color=CASOS[m]["cor"], markersize=8,
                                          markeredgecolor="white")[0] for m in CASOS}
        for ax in (self.axq, self.axw):  # instante do campo 3D e da escala: fim do ciclo
            ax.axvline(2.12, color=TEXTO_2, linewidth=1.0, linestyle=":")
        self.axq.text(2.118, self.axq.get_ylim()[0], "instante do\ncampo 3D", fontsize=10, color=TEXTO_2, ha="right",
                      va="bottom")
        self.tempo = texto(40, 748, "", fontsize=19, fontweight="bold", va="center")
        texto(40, 1012, "Dados: OpenFOAM v2406 (pimpleFoam), malha média de 20 µm, 1000 passos por ciclo, 2.º ciclo "
                        "(1,06 a 2,12 s); strut de 79 µm e de 135 µm, mesma geometria e mesmo escoamento imposto; só muda a espessura do strut.",
              fontsize=11.5, color=TEXTO_2, va="center")
        texto(40, 1036, "Limitações: o mapa de TAWSS e as linhas de corrente são fixos (só existe o campo 3D de t = 2,12 s); o que se move é "
                        "o cursor do ciclo sobre as séries calculadas. Sem validação experimental; 0,4 Pa é um limiar operacional.",
              fontsize=11.5, color=TEXTO_2, va="center")
        texto(40, 1060, "Setor de 22,5° de uma artéria de 3,0 mm (espelhado e repetido para mostrar meio tubo); sem lesão, sem pontes entre células.",
              fontsize=11.5, color=TEXTO_2, va="center")

    def desenhar(self, t: float) -> np.ndarray:
        """Atualiza o cursor e os valores para o instante t e devolve o quadro RGB (altura x largura x 3)."""
        c = self.dados["caudal"]
        v = valor_em(c[0], c[1], t)
        for cur in self.cursores:
            cur.set_xdata([t, t])
        self.ponto_q.set_data([t], [v])
        for m in CASOS:
            w = valor_em(*self.dados[m]["wss_t"], t)
            self.pontos_w[m].set_data([t], [w])
            self.vivos[m].set_text(f"Agora: tensão de corte média da parede {fmt_pt(w, 2)} Pa")
        self.tempo.set_text(f"Instante do ciclo: {texto_instante(t)}   |   velocidade média na entrada {fmt_pt(v, 1)} cm/s")
        self.fig.canvas.draw()
        return np.asarray(self.fig.canvas.buffer_rgba())[:, :, :3].copy()


def carregar_tudo(tmp: Path) -> tuple[dict, dict]:
    """Lê as séries e as paredes dos dois casos e gera as duas imagens 3D."""
    dados, imagens = {}, {}
    for mat, cfg in CASOS.items():
        nome = cfg["pasta"]
        d = ler_parede(nome)
        q = ler_serie(nome, "caudais")
        tp = ler_serie(nome, "tensaoParede")
        tq, vq = recortar(q[:, 0], velocidade_cm_s(q[:, 1], area_entrada(nome)))
        tw, ww = recortar(tp[:, 0], RHO * tp[:, 1])
        d["wss_t"] = (tw, ww)
        dados[mat] = d
        dados.setdefault("caudal", (tq, vq))
        imagens[mat] = render_3d(nome, d, tmp, (1780, 544))
    return dados, imagens


def codificar_web(origem: Path, destino: Path, limite_mb: float = 3.0) -> None:
    """Versão leve 1280x720 (H.264, sem som, faststart); baixa a qualidade até caber no limite de tamanho."""
    import imageio_ffmpeg

    exe = imageio_ffmpeg.get_ffmpeg_exe()
    for crf in (26, 28, 30, 32, 34, 36, 38):
        subprocess.run([exe, "-y", "-loglevel", "error", "-i", str(origem), "-vf", "scale=1280:720:flags=lanczos",
                        "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-pix_fmt", "yuv420p", "-an",
                        "-movflags", "+faststart", str(destino)], check=True)
        if destino.stat().st_size <= limite_mb * 1_000_000:
            print(f"web: crf {crf}, {destino.stat().st_size / 1e6:.2f} MB")
            return
    raise RuntimeError("não coube nos 3 MB")


def main() -> None:
    import imageio.v2 as imageio

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--teste", action="store_true", help="só dois fotogramas, sem vídeo")
    args = ap.parse_args()
    SAIDA.mkdir(parents=True, exist_ok=True)
    tmp = Path(__import__("tempfile").mkdtemp(prefix="cfd_video_"))
    try:
        dados, imagens = carregar_tudo(tmp)
        q = Quadro(dados, imagens)
        if args.teste:
            imageio.imwrite(SAIDA / "teste_a.png", q.desenhar(1.60))
            return
        imageio.imwrite(SAIDA / "cfd_fotograma.png", q.desenhar(1.62))
        mp4 = SAIDA / "cfd_stent_2ciclo.mp4"
        with imageio.get_writer(str(mp4), fps=FPS, codec="libx264", pixelformat="yuv420p", macro_block_size=1,
                                ffmpeg_params=["-crf", "18", "-preset", "medium", "-movflags", "+faststart"]) as w:
            for i in range(n_quadros()):
                w.append_data(q.desenhar(tempo_do_quadro(i)))
        codificar_web(mp4, SAIDA / "cfd_stent_2ciclo_web.mp4")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
