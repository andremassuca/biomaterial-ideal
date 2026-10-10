"""Animações para a apresentação e o poster (apresentacao/media/).

Cada animação sai em MP4 (H.264, 1920 × 1080, 30 fps), em GIF de reserva (960 × 540, 15 fps) e em duas
imagens PNG: a primeira e a última imagem do vídeo (<nome>_inicio.png e <nome>_final.png).
Os números vêm sempre de data/ e de results/, através do pacote biomat_mcdm; nada é inventado.
Cada vídeo tem no canto um rótulo fixo:
  "Simulação com os dados do trabalho": cálculo real com a base de dados;
  "Esquema ilustrativo": geometria para explicar um conceito (os números mostrados vêm da base).

Animações:
  alvo_haste          módulo de cada liga da haste contra o alvo de 17 GPa e a nota normalizada
  mc_stent            % acumulada de 1.º lugar no Monte Carlo do stent (cenário A, seed 42)
  gibson_ashby        E = E_s (1 − p)² até ao alvo de 17 GPa
  scaffold_leitura    ranking do scaffold da leitura ampla para a literal (P-foco)
  sensibilidade_eta   vencedor de cada caso quantitativo com η de 0 a 1
  mc_haste            distribuição do C do TOPSIS de cada liga da haste no Monte Carlo
  pesos_stent         ranking do stent com o peso da espessura dos struts a variar
  rede_porosa         rede porosa (giroide) com o módulo de Gibson e Ashby num mostrador (3D)
  stent_expansao      stent a expandir com o balão e a recuar, recuo proporcional a σy/E (3D)
  scaffold_degradacao massa restante do β-TCP poroso e do compósito ao longo do tempo
Uso: python scripts/animacoes.py [nomes ...] [--n-iter 10000]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable, Iterator

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Wedge  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
from figuras import COR_MATERIAL, curto  # noqa: E402
from run_all import BASE, CASOS, LIGACOES_FOCO  # noqa: E402

from biomat_mcdm.io import DATA, DecisionProblem, build_problem, criterios_do_problema, load_parametros  # noqa: E402
from biomat_mcdm.normalization import normalize_column  # noqa: E402
from biomat_mcdm.pipeline import METODOS, fmt_pt  # noqa: E402
from biomat_mcdm.robustness import (com_eta, com_foco, com_peso, monte_carlo, monte_carlo_pontuacoes,  # noqa: E402
                                    pontuacoes)

MEDIA = RAIZ / "apresentacao" / "media"
FPS, LARGURA, ALTURA = 30, 1920, 1080
ROTULO_SIM = "Simulação com os dados do trabalho"
ROTULO_ESQ = "Esquema ilustrativo"
AZUL_FE = "#0595D1"
TEXTO, TEXTO_2, GRELHA, OSSO = "#14171a", "#55595e", "#e6e8eb", "#f3dfb4"  # tinta do estilo dos gráficos
F_TIT, F_SUB, F_EIXO, F_MARCA = 34, 21, 21, 18
CRIT_MODULO = "Módulo de Young"
CRIT_STRUT = "Espessura típica de strut"
CRIT_RECUO = "Índice material de recuo elástico σy/E (proxy)"
CRIT_DEGRADACAO = "Tempo de degradação"
MATERIAIS_MC_STENT = ["Pt-Cr", "Co-Cr L605", "Co-Ni-Cr-Mo MP35N"]

import estilo_graficos as eg  # noqa: E402

eg.registar_inter()  # letra Inter do estilo dos gráficos (design/fontes); sem ela, Segoe UI
plt.rcParams.update({"font.family": ["Inter", "Segoe UI", "DejaVu Sans"], "axes.unicode_minus": True,
                     "svg.fonttype": "none"})


# ---------------------------------------------------------------- dados (funções puras)

def problema(caso: str, cenario: str = BASE, data_dir: Path = DATA) -> DecisionProblem:
    """Problema de decisão de um caso quantitativo ("Haste", "Stent" ou "Scaffold")."""
    return build_problem(CASOS[caso], cenario, data_dir)


def incerteza(data_dir: Path = DATA) -> float:
    """Incerteza dos valores únicos no Monte Carlo (data/parametros.csv), a mesma do resultado principal."""
    return load_parametros(data_dir).get("incerteza_valor_unico", 0.0)


def dados_alvo_haste(data_dir: Path = DATA) -> tuple[pd.DataFrame, float, tuple[float, float]]:
    """Módulo de cada liga da haste (todos os candidatos, cenário B) e a sua nota normalizada com alvo.

    Em linguagem simples: a nota (eq. 2, a do TOPSIS) é 1 no alvo e desce com a distância a ele.
    Devolve a tabela ordenada da melhor para a pior nota, o alvo e o intervalo do osso cortical.
    """
    p = problema("Haste", "B", data_dir)
    j = p.criteria.index(CRIT_MODULO)
    nota = normalize_column(p.X[:, j], p.types[j], p.targets[j])
    df = pd.DataFrame({"material": p.alternatives, "E_min": p.X_min[:, j], "E_tip": p.X[:, j],
                       "E_max": p.X_max[:, j], "nota": nota})
    df["investigacao"] = ~df["material"].isin(problema("Haste", "A", data_dir).alternatives)
    tec = pd.read_csv(data_dir / "tecido.csv")
    osso = tec[(tec["tecido"] == "Osso cortical") & (tec["propriedade"] == CRIT_MODULO)].iloc[0]
    return df.sort_values("nota", ascending=False).reset_index(drop=True), float(p.targets[j]), \
        (float(osso["min"]), float(osso["max"]))


def mc_acumulado(caso: str, n_iter: int = 10_000, seed: int = 42,
                 data_dir: Path = DATA) -> tuple[list[str], dict[str, np.ndarray]]:
    """% acumulada de iterações em 1.º lugar ao longo do Monte Carlo das propriedades (cenário A).

    Em linguagem simples: depois de k iterações, que fração das k ficou com cada material em 1.º.
    A última linha é a % do relatório (mesma seed e mesma incerteza dos valores únicos).
    """
    p = problema(caso, BASE, data_dir)
    out = {}
    for m in METODOS:
        r = monte_carlo(p, m, n_iter, seed, incerteza_valor_unico=incerteza(data_dir))
        out[m] = 100 * np.cumsum(r == 1, axis=0) / np.arange(1, n_iter + 1)[:, None]
    return p.alternatives, out


def modulo_e_alvo_haste(data_dir: Path = DATA) -> tuple[float, float]:
    """(E típico do Ti-6Al-4V ELI, alvo do módulo da haste), em GPa, da base de dados."""
    p = problema("Haste", BASE, data_dir)
    j = p.criteria.index(CRIT_MODULO)
    return float(p.X[p.alternatives.index("Ti-6Al-4V ELI"), j]), float(p.targets[j])


def gibson_ashby(p: np.ndarray | float, E_s: float) -> np.ndarray | float:
    """Módulo de uma estrutura porosa: E = E_s (1 − p)² (Gibson e Ashby, constante C = 1)."""
    return E_s * (1 - np.asarray(p)) ** 2


def porosidade_para(E: float, E_s: float) -> float:
    """Porosidade com que a estrutura atinge o módulo E: p = 1 − √(E / E_s)."""
    return float(1 - np.sqrt(E / E_s))


def leituras_scaffold(data_dir: Path = DATA) -> dict[str, pd.DataFrame]:
    """Pontuações do scaffold com a leitura ampla (ligações direta e indireta) e a literal (só direta).

    Em linguagem simples: é o cenário P-foco do relatório (peso dos critérios do problema crítico
    multiplicado pelo fator da base); a leitura literal é a que põe o β-TCP à frente no TOPSIS e no VIKOR.
    """
    base = problema("Scaffold", BASE, data_dir)
    fator = load_parametros(data_dir).get("fator_foco_problema", 2.0)
    out = {}
    for rot, lig in (("ampla", LIGACOES_FOCO["direta + indireta"]), ("literal", LIGACOES_FOCO["direta"])):
        q = com_foco(base, criterios_do_problema(CASOS["Scaffold"], lig, data_dir), fator)
        out[rot] = pd.DataFrame({"material": q.alternatives,
                                 **{m: pontuacoes(q.X, q.weights, q.types, q.targets, m) for m in METODOS}})
    return out


def vencedor(scores: np.ndarray, metodo: str, alternativas: list[str]) -> str:
    """Material com a melhor pontuação (no VIKOR, a menor)."""
    return alternativas[int(np.argmin(scores) if metodo == "VIKOR" else np.argmax(scores))]


def vencedores_eta(etas: np.ndarray, data_dir: Path = DATA) -> pd.DataFrame:
    """Vencedor de cada caso quantitativo e método para cada η (cenário A)."""
    linhas = []
    for caso in CASOS:
        p = problema(caso, BASE, data_dir)
        for eta in etas:
            q = com_eta(p, float(eta))
            for m in METODOS:
                linhas.append({"caso": caso, "metodo": m, "eta": float(eta),
                               "vencedor": vencedor(pontuacoes(q.X, q.weights, q.types, q.targets, m), m,
                                                    q.alternatives)})
    return pd.DataFrame(linhas)


def mc_pontuacoes_haste(n_iter: int = 10_000, seed: int = 42,
                        data_dir: Path = DATA) -> tuple[list[str], np.ndarray]:
    """C do TOPSIS de cada liga da haste em cada iteração do Monte Carlo das propriedades (cenário A)."""
    p = problema("Haste", BASE, data_dir)
    return p.alternatives, monte_carlo_pontuacoes(p, "TOPSIS", n_iter, seed, incerteza(data_dir))


def varrimento_peso(caso: str, criterio: str, pesos: np.ndarray,
                    data_dir: Path = DATA) -> tuple[list[str], dict[str, np.ndarray], float]:
    """Pontuações com o peso de um critério a variar (os outros renormalizados): {método: (len(pesos), m)}.

    Devolve também o peso que o critério tem no trabalho (cenário A).
    """
    p = problema(caso, BASE, data_dir)
    out = {m: np.empty((len(pesos), len(p.alternatives))) for m in METODOS}
    for k, w in enumerate(pesos):
        q = com_peso(p, criterio, float(w))
        for m in METODOS:
            out[m][k] = pontuacoes(q.X, q.weights, q.types, q.targets, m)
    return p.alternatives, out, float(p.weights[p.criteria.index(criterio)])


def cruzamentos(x: np.ndarray, a: np.ndarray, b: np.ndarray) -> list[float]:
    """Valores de x em que as curvas a e b se cruzam (interpolação linear entre pontos)."""
    d = np.asarray(a, float) - np.asarray(b, float)
    out = []
    for k in range(len(d) - 1):
        if d[k] == 0:
            out.append(float(x[k]))
        elif d[k] * d[k + 1] < 0:
            out.append(float(x[k] + (x[k + 1] - x[k]) * d[k] / (d[k] - d[k + 1])))
    return out


def limiar_porosidade(campo: np.ndarray, p: float) -> float:
    """Nível do campo abaixo do qual fica o sólido, para que a fração de vazio seja p."""
    return float(np.quantile(campo, 1 - p)) if p > 0 else float(np.max(campo)) + 1.0


def indices_recuo(materiais: list[str], data_dir: Path = DATA) -> dict[str, float]:
    """Índice σy/E (valor típico da base) dos materiais do stent pedidos."""
    p = problema("Stent", BASE, data_dir)
    j = p.criteria.index(CRIT_RECUO)
    return {m: float(p.X[p.alternatives.index(m), j]) for m in materiais}


def tempos_degradacao(materiais: list[str], data_dir: Path = DATA) -> tuple[dict[str, float], float]:
    """Tempo de degradação típico (meses) dos materiais do scaffold e o valor do cenário de referência."""
    p = problema("Scaffold", BASE, data_dir)
    j = p.criteria.index(CRIT_DEGRADACAO)
    return {m: float(p.X[p.alternatives.index(m), j]) for m in materiais}, float(p.targets[j])


def massa_restante(t: np.ndarray | float, T: float) -> np.ndarray:
    """Massa restante (%) com a forma assumida no esquema: perda linear até zero no tempo típico T."""
    return np.clip(100 * (1 - np.asarray(t, float) / T), 0, 100)


# ---------------------------------------------------------------- utilitários de desenho

def suave(x: float) -> float:
    """Rampa suave de 0 a 1 (entrada e saída lentas)."""
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def fase(t: float, a: float, b: float) -> float:
    """Progresso suave (0 a 1) entre os instantes a e b."""
    return suave((t - a) / (b - a))


def pct(v: float, casas: int = 1) -> str:
    return f"{fmt_pt(v, casas)} %"


def nova_figura() -> plt.Figure:
    return plt.figure(figsize=(LARGURA / 100, ALTURA / 100), dpi=100, facecolor="white")


def cabecalho(fig: plt.Figure, titulo: str, subtitulo: str, rotulo: str) -> None:
    """Título, subtítulo e o rótulo fixo do canto (simulação ou esquema)."""
    fig.text(0.035, 0.94, titulo, fontsize=F_TIT, fontweight="bold", color=TEXTO, va="top")
    fig.text(0.035, 0.875, subtitulo, fontsize=F_SUB, color=TEXTO_2, va="top")
    cor = AZUL_FE if rotulo == ROTULO_SIM else "#9a8450"
    fig.text(0.975, 0.035, rotulo, fontsize=16, color=cor, ha="right", va="bottom", fontweight="bold",
             bbox=dict(boxstyle="round,pad=0.55", fc="#f2f5f8", ec="none"))


def rodape(fig: plt.Figure, texto: str) -> None:
    fig.text(0.035, 0.035, texto, fontsize=16, color=TEXTO_2, va="bottom")


def estilo(ax: plt.Axes, grelha: str = "x") -> None:
    for lado in ax.spines.values():
        lado.set_visible(False)
    ax.tick_params(colors=TEXTO_2, labelsize=F_MARCA, length=0)
    if grelha:
        ax.grid(axis=grelha, color=GRELHA, lw=1.0)
        ax.set_axisbelow(True)


def virgulas(ax: plt.Axes, casas: int = 1) -> None:
    """Marcas dos eixos com vírgula decimal."""
    from matplotlib.ticker import FuncFormatter
    f = FuncFormatter(lambda v, _: fmt_pt(v, casas))
    ax.xaxis.set_major_formatter(f)
    ax.yaxis.set_major_formatter(f)


def imagem(fig: plt.Figure) -> np.ndarray:
    fig.canvas.draw()
    return np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()


def cor_caso(caso: str, material: str) -> str:
    return COR_MATERIAL[caso][material]


def gravar(nome: str, frames: Iterator[np.ndarray], destino: Path = MEDIA, gif: bool = True) -> Path:
    """Grava <nome>.mp4 (H.264), <nome>.gif (reserva) e as imagens inicial e final em PNG."""
    import imageio.v2 as imageio
    from PIL import Image

    destino.mkdir(parents=True, exist_ok=True)
    mp4 = destino / f"{nome}.mp4"
    escritor = imageio.get_writer(mp4, fps=FPS, codec="libx264", quality=8, pixelformat="yuv420p",
                                  macro_block_size=8, ffmpeg_params=["-movflags", "+faststart"])
    gif_frames, ultimo, n = [], None, 0
    for k, frame in enumerate(frames):
        escritor.append_data(frame)
        if k == 0:
            Image.fromarray(frame).save(destino / f"{nome}_inicio.png")
        if gif and k % 2 == 0:
            gif_frames.append(Image.fromarray(frame).resize((960, 540), Image.LANCZOS))
        ultimo, n = frame, k + 1
    escritor.close()
    Image.fromarray(ultimo).save(destino / f"{nome}_final.png")
    if gif and gif_frames:
        paleta = gif_frames[len(gif_frames) // 2].quantize(colors=160, method=Image.MEDIANCUT)
        q = [f.quantize(palette=paleta, dither=Image.Dither.NONE) for f in gif_frames]
        q[0].save(destino / f"{nome}.gif", save_all=True, append_images=q[1:], duration=1000 // 15,
                  loop=0, optimize=True)
    print(f"{mp4.name}: {n} imagens ({n / FPS:.1f} s)")
    return mp4


# ---------------------------------------------------------------- animações 2D

def anim_alvo_haste(n_iter: int = 10_000) -> Iterator[np.ndarray]:
    df, alvo, (o_min, o_max) = dados_alvo_haste()
    n = len(df)
    inicio, passo, dur = 1.0, 1.55, 13.0
    for i in range(int(dur * FPS)):
        t = i / FPS
        fig = nova_figura()
        cabecalho(fig, "Critério-alvo: o melhor módulo é o do osso, não o maior",
                  f"Haste femoral, todos os candidatos: módulo de Young (típico e intervalo da base) e nota "
                  f"normalizada com alvo de {fmt_pt(alvo, 0)} GPa", ROTULO_SIM)
        ax = fig.add_axes((0.24, 0.13, 0.47, 0.66))
        bx = fig.add_axes((0.76, 0.13, 0.19, 0.66))
        ax.axvspan(o_min, o_max, color=OSSO, zorder=0)
        ax.axvline(alvo, color=TEXTO, lw=2.5, zorder=1)
        ax.text(alvo + 3, n - 0.35, f"alvo {fmt_pt(alvo, 0)} GPa\n(osso cortical {fmt_pt(o_min, 0)} a "
                f"{fmt_pt(o_max, 0)} GPa)", fontsize=17, color=TEXTO, va="bottom")
        for k, r in df.iterrows():
            y = n - 1 - k
            a = fase(t, inicio + passo * k, inicio + passo * k + 0.5)
            b = fase(t, inicio + passo * k + 0.5, inicio + passo * k + 1.3)
            c = cor_caso("Haste", r.material)
            nome = curto(r.material).replace(" (TNZT)", "") + ("\n(em investigação)" if r.investigacao else "")
            ax.text(-6, y, nome, ha="right", va="center", fontsize=F_EIXO, color=TEXTO, alpha=max(a, 0.18))
            if a > 0:
                x0 = alvo + (r.E_tip - alvo) * a
                ax.plot([r.E_min, r.E_max], [y, y], color=c, lw=9, alpha=0.35 * a, solid_capstyle="round")
                ax.plot([x0], [y], "o", ms=22, color=c, mec="white", mew=2.5, alpha=a)
                ax.text(r.E_tip + 7, y + 0.28, f"{fmt_pt(r.E_tip, 1)} GPa", fontsize=17, color=TEXTO_2, alpha=a)
                if b > 0:
                    ax.annotate("", xy=(alvo, y - 0.32), xytext=(r.E_tip, y - 0.32),
                                arrowprops=dict(arrowstyle="<->", color=c, lw=2, alpha=b))
            if b > 0:
                bx.barh(y, r.nota * b, height=0.62, color=c)
                bx.text(r.nota * b + 0.02, y, fmt_pt(r.nota * b, 2), va="center", fontsize=F_EIXO, color=TEXTO)
        ax.set_xlim(0, 250)
        ax.set_ylim(-0.7, n - 0.1)
        ax.set_yticks([])
        ax.set_xlabel("Módulo de Young (GPa)", fontsize=F_EIXO, color=TEXTO_2)
        estilo(ax)
        bx.set_xlim(0, 1.18)
        bx.set_ylim(-0.7, n - 0.1)
        bx.set_yticks([])
        bx.set_xticks([0, 0.5, 1])
        bx.set_xticklabels(["0", "0,5", "1"])
        bx.set_xlabel("Nota normalizada (1 = no alvo)", fontsize=F_EIXO, color=TEXTO_2)
        estilo(bx)
        rodape(fig, "Nota = 1 − |E − alvo| / (maior − menor valor da coluna, incluindo o alvo), "
                    "normalização com critérios-alvo de Petković et al. (2025)")
        yield imagem(fig)
        plt.close(fig)


def iteracoes_ate(t: float, a: float, b: float, n_iter: int) -> int:
    """Iterações mostradas no instante t: crescem devagar no início e depressa no fim."""
    x = min(max((t - a) / (b - a), 0.0), 1.0)
    return max(1, int(round(n_iter * x ** 2)))


def anim_mc_stent(n_iter: int = 10_000) -> Iterator[np.ndarray]:
    alts, acum = mc_acumulado("Stent", n_iter)
    dur, a, b = 13.0, 0.8, 10.5
    xs = np.arange(1, n_iter + 1)
    for i in range(int(dur * FPS)):
        t = i / FPS
        k = iteracoes_ate(t, a, b, n_iter)
        fig = nova_figura()
        cabecalho(fig, "Stent: o Pt-Cr fica mais vezes em 1.º lugar, mas não sempre",
                  "Monte Carlo das propriedades, cenário A: percentagem acumulada de iterações em 1.º lugar",
                  ROTULO_SIM)
        for c, m in enumerate(METODOS):
            ax = fig.add_axes((0.06 + c * 0.315, 0.16, 0.27, 0.56))
            for mat in MATERIAIS_MC_STENT:
                j = alts.index(mat)
                y = acum[m][:k, j]
                ax.plot(xs[:k], y, color=cor_caso("Stent", mat), lw=3.2, label=curto(mat))
                ax.plot([xs[k - 1]], [y[-1]], "o", ms=10, color=cor_caso("Stent", mat))
                if t > b:
                    ax.text(n_iter * 1.03, y[-1], pct(y[-1]), fontsize=F_EIXO, color=cor_caso("Stent", mat),
                            va="center", fontweight="bold", alpha=fase(t, b, b + 0.6))
            ax.set_xlim(0, n_iter * 1.3)
            ax.set_ylim(0, 100)
            ax.set_title(m, fontsize=26, color=TEXTO, fontweight="bold", loc="left")
            ax.set_xticks([0, n_iter // 2, n_iter])
            ax.set_xticklabels(["0", f"{n_iter // 2:,}".replace(",", " "), f"{n_iter:,}".replace(",", " ")])
            ax.set_yticks([0, 25, 50, 75, 100])
            ax.set_yticklabels(["0 %", "25 %", "50 %", "75 %", "100 %"])
            ax.set_xlabel("iteração", fontsize=F_EIXO, color=TEXTO_2)
            estilo(ax, "y")
            if c == 0:
                fig.legend(*ax.get_legend_handles_labels(), loc="upper left", bbox_to_anchor=(0.03, 0.835), ncol=3,
                           fontsize=F_EIXO, frameon=False)
        fig.text(0.975, 0.80, f"iteração {k:,} de {n_iter:,}".replace(",", " "), fontsize=F_EIXO,
                 color=TEXTO_2, ha="right")
        rodape(fig, f"{n_iter:,} iterações".replace(",", " ") + ", seed 42; valores únicos com ±10 %; "
               "uma frequência sob as hipóteses do modelo, não uma probabilidade clínica")
        yield imagem(fig)
        plt.close(fig)


def anim_gibson_ashby(n_iter: int = 10_000) -> Iterator[np.ndarray]:
    E_s, alvo = modulo_e_alvo_haste()
    p_alvo = porosidade_para(alvo, E_s)
    tec = pd.read_csv(DATA / "tecido.csv")
    osso = tec[(tec["tecido"] == "Osso cortical") & (tec["propriedade"] == CRIT_MODULO)].iloc[0]
    ps = np.linspace(0, 0.8, 400)
    dur = 11.0
    for i in range(int(dur * FPS)):
        t = i / FPS
        x = p_alvo * fase(t, 1.0, 7.5)
        fig = nova_figura()
        cabecalho(fig, "A mesma liga, porosa, chega ao módulo do osso",
                  f"Relação de Gibson e Ashby para estruturas celulares (C = 1), com E_s = {fmt_pt(E_s, 1)} GPa "
                  "(valor típico do Ti-6Al-4V ELI na base)", ROTULO_SIM)
        ax = fig.add_axes((0.08, 0.14, 0.6, 0.64))
        ax.axhspan(float(osso["min"]), float(osso["max"]), color=OSSO, zorder=0)
        ax.text(79, float(osso["max"]) + 1.5, "osso cortical", ha="right", fontsize=F_EIXO, color="#8a5a00")
        ax.axhline(alvo, color=TEXTO, lw=2, ls=(0, (4, 3)))
        ax.plot(ps * 100, gibson_ashby(ps, E_s), color=GRELHA, lw=3)
        sel = ps <= x
        ax.plot(ps[sel] * 100, gibson_ashby(ps[sel], E_s), color=AZUL_FE, lw=5)
        ax.plot([x * 100], [gibson_ashby(x, E_s)], "o", ms=20, color=AZUL_FE, mec="white", mew=3)
        ax.text(1, E_s + 3, f"liga maciça: {fmt_pt(E_s, 1)} GPa", fontsize=F_EIXO, color=TEXTO_2)
        f = fase(t, 7.5, 8.5)
        if f > 0:
            ax.plot([p_alvo * 100] * 2, [0, alvo], color=AZUL_FE, lw=2, ls=":", alpha=f)
            ax.annotate(f"p = {fmt_pt(100 * p_alvo, 1)} %\nE = {fmt_pt(alvo, 0)} GPa (alvo)",
                        xy=(p_alvo * 100, alvo), xytext=(p_alvo * 100 + 4, alvo + 30), fontsize=24,
                        color=TEXTO, fontweight="bold", alpha=f,
                        arrowprops=dict(arrowstyle="->", color=TEXTO, lw=2, alpha=f))
        ax.set_xlim(0, 80)
        ax.set_ylim(0, 115)
        ax.set_xlabel("Porosidade p (%)", fontsize=F_EIXO, color=TEXTO_2)
        ax.set_ylabel("Módulo E (GPa)", fontsize=F_EIXO, color=TEXTO_2)
        estilo(ax, "both")
        fig.text(0.74, 0.62, "E = E_s (1 − p)²", fontsize=40, color=TEXTO, fontweight="bold")
        fig.text(0.74, 0.50, f"p = {fmt_pt(100 * x, 1)} %", fontsize=34, color=AZUL_FE)
        fig.text(0.74, 0.42, f"E = {fmt_pt(float(gibson_ashby(x, E_s)), 1)} GPa", fontsize=34, color=AZUL_FE)
        rodape(fig, "Gibson e Ashby (1997), cap. 5; cálculo de primeira ordem, não substitui uma análise estrutural")
        yield imagem(fig)
        plt.close(fig)


def _barras_ranking(ax: plt.Axes, valores: dict[str, float], ordem: dict[str, float], caso: str,
                    destaque: set[str], xmax: float) -> None:
    for mat, v in valores.items():
        y = ordem[mat]
        c = cor_caso(caso, mat)
        al = 1 if mat in destaque else 0.4
        ax.barh(y, v, height=0.66, color=c, alpha=al)
        ax.text(v + xmax * 0.015, y, fmt_pt(v, 3), va="center", fontsize=17, color=TEXTO, alpha=max(al, 0.6))
        ax.text(-xmax * 0.02, y, curto(mat).replace("Vidro bioativo ", "").replace(" poroso", "")
                .replace(" porosa", ""), ha="right", va="center", fontsize=18, color=TEXTO, alpha=max(al, 0.6))


def anim_scaffold_leitura(n_iter: int = 10_000) -> Iterator[np.ndarray]:
    lt = leituras_scaffold()
    amp, lit = lt["ampla"].set_index("material"), lt["literal"].set_index("material")
    mats = list(amp.index)
    destaque = {"β-TCP poroso", "Compósito PCL/β-TCP (impressão 3D)"}
    dur = 13.0
    for i in range(int(dur * FPS)):
        t = i / FPS
        f = fase(t, 3.5, 8.5)
        fig = nova_figura()
        cabecalho(fig, "Scaffold: a resposta depende da leitura do problema",
                  "Cenário P-foco: peso dos critérios do problema crítico duplicado (suporte celular e "
                  "degradação controlada)", ROTULO_SIM)
        rot = ("Leitura ampla: inclui o suporte mecânico" if f < 0.5
               else "Leitura literal: só porosidade, bioatividade e degradação")
        fig.text(0.5, 0.80, rot, ha="center", fontsize=28, color=AZUL_FE, fontweight="bold",
                 alpha=abs(2 * f - 1) if 0 < f < 1 else 1)
        for c, m in enumerate(METODOS):
            ax = fig.add_axes((0.10 + c * 0.315, 0.12, 0.22, 0.6))
            v = {mat: (1 - f) * amp.loc[mat, m] + f * lit.loc[mat, m] for mat in mats}
            menor = m == "VIKOR"
            pos_a = {mt: k for k, mt in enumerate(sorted(mats, key=lambda z: amp.loc[z, m], reverse=not menor))}
            pos_l = {mt: k for k, mt in enumerate(sorted(mats, key=lambda z: lit.loc[z, m], reverse=not menor))}
            ordem = {mt: len(mats) - 1 - ((1 - f) * pos_a[mt] + f * pos_l[mt]) for mt in mats}
            xmax = max(amp[m].max(), lit[m].max()) * 1.25
            _barras_ranking(ax, v, ordem, "Scaffold", destaque, xmax)
            ax.set_xlim(0, xmax)
            ax.set_ylim(-0.6, len(mats) - 0.4)
            ax.set_yticks([])
            ax.set_title(f"{m}: {'P, menor é melhor' if menor else ('C' if m == 'TOPSIS' else 'Q') + ', maior é melhor'}",
                         fontsize=22, color=TEXTO, loc="left", fontweight="bold")
            estilo(ax, "x")
            ax.set_xticks([])
        rodape(fig, "Cenário A; a mesma base de dados nas duas leituras, só mudam os pesos")
        yield imagem(fig)
        plt.close(fig)


def anim_sensibilidade_eta(n_iter: int = 10_000) -> Iterator[np.ndarray]:
    etas = np.round(np.linspace(0, 1, 101), 2)
    v = vencedores_eta(etas)
    dur, a, b = 13.0, 1.0, 10.0
    for i in range(int(dur * FPS)):
        t = i / FPS
        e_atual = fase(t, a, b)
        fig = nova_figura()
        cabecalho(fig, "Quem ganha quando os pesos passam de objetivos a subjetivos",
                  "w = η · w(subjetivos) + (1 − η) · w(objetivos); η = 1 é o resultado principal; cenário A",
                  ROTULO_SIM)
        for r, caso in enumerate(CASOS):
            ax = fig.add_axes((0.15, 0.62 - r * 0.235, 0.50, 0.17))
            sub = v[v["caso"] == caso]
            for c, m in enumerate(METODOS):
                s = sub[sub["metodo"] == m].sort_values("eta")
                y = 2 - c
                for e, mat in zip(s["eta"], s["vencedor"]):
                    if e <= e_atual + 1e-9:
                        ax.barh(y, 0.0101, left=e - 0.005, height=0.8, color=cor_caso(caso, mat), lw=0)
                ax.text(-0.015, y, m, ha="right", va="center", fontsize=17, color=TEXTO_2)
            ax.axvline(e_atual, color=TEXTO, lw=2.5)
            ax.set_xlim(-0.005, 1.005)
            ax.set_ylim(-0.6, 2.6)
            ax.set_yticks([])
            ax.set_xticks([0, 0.25, 0.5, 0.75, 1])
            ax.set_xticklabels(["0", "0,25", "0,5", "0,75", "1"] if r == 2 else [])
            estilo(ax, "")
            fig.text(0.02, 0.62 - r * 0.235 + 0.085, {"Haste": "Haste", "Stent": "Stent", "Scaffold": "Scaffold"}[caso],
                     fontsize=26, fontweight="bold", color=TEXTO, va="center")
            atuais = sub[np.isclose(sub["eta"], np.round(e_atual, 2))]
            mats = list(dict.fromkeys(sub["vencedor"]))
            for k, mat in enumerate(mats):
                fig.text(0.68, 0.62 - r * 0.235 + 0.14 - k * 0.04, "■", color=cor_caso(caso, mat), fontsize=22,
                         va="center")
                ganha = ", ".join(atuais[atuais["vencedor"] == mat]["metodo"])
                fig.text(0.698, 0.62 - r * 0.235 + 0.14 - k * 0.04,
                         curto(mat) + (f"  ({ganha})" if ganha else ""), fontsize=18, va="center",
                         color=TEXTO if ganha else TEXTO_2, fontweight="bold" if ganha else "normal")
        fig.text(0.15 + 0.50 * e_atual, 0.065, f"η = {fmt_pt(e_atual, 2)}", ha="center", fontsize=24,
                 color=AZUL_FE, fontweight="bold")
        rodape(fig, "Pesos objetivos pelo método do desvio-padrão; cálculo em passos de 0,01")
        yield imagem(fig)
        plt.close(fig)


def anim_mc_haste(n_iter: int = 10_000) -> Iterator[np.ndarray]:
    alts, s = mc_pontuacoes_haste(n_iter)
    ordem = list(np.argsort(s.mean(axis=0))[::-1])
    bins = np.linspace(0, 1, 101)
    hist_max = {j: np.histogram(s[:, j], bins)[0].max() for j in range(len(alts))}
    primeiro = (s.argmax(axis=1) == alts.index("Ti-6Al-4V ELI")).sum()
    dur, a, b = 13.0, 0.8, 10.5
    for i in range(int(dur * FPS)):
        t = i / FPS
        k = iteracoes_ate(t, a, b, n_iter)
        fig = nova_figura()
        cabecalho(fig, "Haste: o Ti-6Al-4V ELI fica à frente em praticamente todas as iterações",
                  "Monte Carlo das propriedades, cenário A: distribuição do coeficiente C do TOPSIS de cada liga "
                  "(altura relativa em cada linha)",
                  ROTULO_SIM)
        for r, j in enumerate(ordem):
            ax = fig.add_axes((0.24, 0.68 - r * 0.125, 0.66, 0.11))
            h = np.histogram(s[:k, j], bins)[0]
            ax.bar(bins[:-1], h, width=0.0095, align="edge", color=cor_caso("Haste", alts[j]))
            ax.set_xlim(0, 1)
            ax.set_ylim(0, hist_max[j] * 1.05)
            ax.set_yticks([])
            ax.set_xticks(np.linspace(0, 1, 11))
            ax.set_xticklabels([fmt_pt(x, 1) for x in np.linspace(0, 1, 11)] if r == len(ordem) - 1 else [])
            estilo(ax, "x")
            fig.text(0.225, 0.68 - r * 0.125 + 0.04, curto(alts[j]), ha="right", va="center", fontsize=F_EIXO,
                     color=TEXTO)
        fig.text(0.57, 0.035, "Coeficiente C do TOPSIS (0 a 1, maior é melhor)", ha="center", fontsize=F_EIXO,
                 color=TEXTO_2)
        fig.text(0.035, 0.81, f"iteração {k:,} de {n_iter:,}".replace(",", " "), fontsize=F_EIXO, color=TEXTO_2)
        if t > b:
            fig.text(0.975, 0.81, f"Ti-6Al-4V ELI em 1.º: {primeiro:,} de {n_iter:,}".replace(",", " "),
                     fontsize=24, color=cor_caso("Haste", "Ti-6Al-4V ELI"), ha="right", fontweight="bold",
                     alpha=fase(t, b, b + 0.6))
        yield imagem(fig)
        plt.close(fig)


def anim_pesos_stent(n_iter: int = 10_000) -> Iterator[np.ndarray]:
    pesos = np.linspace(0, 0.8, 161)
    alts, sc, w0 = varrimento_peso("Stent", CRIT_STRUT, pesos)
    i_ptcr, i_l605 = alts.index("Pt-Cr"), alts.index("Co-Cr L605")
    cruz = {m: cruzamentos(pesos, sc[m][:, i_ptcr], sc[m][:, i_l605]) for m in METODOS}
    dur, a, b = 13.0, 1.0, 10.0
    for i in range(int(dur * FPS)):
        t = i / FPS
        wa = 0.8 * fase(t, a, b)
        k = int(np.searchsorted(pesos, wa, side="right"))
        fig = nova_figura()
        cabecalho(fig, "Stent: o peso dos struts só troca Pt-Cr e L605 no WASPAS",
                  "Peso da espessura dos struts de 0 a 0,8 (os outros renormalizados para somar 1); cenário A",
                  ROTULO_SIM)
        for c, m in enumerate(METODOS):
            ax = fig.add_axes((0.06 + c * 0.315, 0.16, 0.27, 0.54))
            for j, mat in enumerate(alts):
                ax.plot(pesos[:max(k, 1)], sc[m][:max(k, 1), j], color=cor_caso("Stent", mat), lw=3.2,
                        label=curto(mat))
            ax.axvline(w0, color=TEXTO_2, lw=1.5, ls=":")
            ax.text(w0 + 0.01, 0.02, f"peso do trabalho\n({fmt_pt(w0, 2)})", transform=ax.get_xaxis_transform(),
                    fontsize=15, color=TEXTO_2)
            ax.axvline(wa, color=TEXTO, lw=2)
            for x in cruz[m]:
                if x <= wa:
                    y = float(np.interp(x, pesos, sc[m][:, i_ptcr]))
                    ax.plot([x], [y], "o", ms=18, mfc="none", mec=TEXTO, mew=3)
                    ax.annotate(f"trocam em {fmt_pt(x, 2)}", xy=(x, y), xytext=(10, 22), textcoords="offset points",
                                fontsize=17, color=TEXTO, fontweight="bold")
            lo = min(sc[m].min(), 0)
            hi = sc[m].max()
            ax.set_xlim(0, 0.8)
            ax.set_ylim((hi * 1.08, lo - 0.04 * hi) if m == "VIKOR" else (lo, hi * 1.12))
            ax.set_title(f"{m}: {'P (menor é melhor)' if m == 'VIKOR' else ('C' if m == 'TOPSIS' else 'Q')}",
                         fontsize=22, color=TEXTO, loc="left", fontweight="bold")
            ax.set_xlabel("peso da espessura dos struts", fontsize=F_EIXO, color=TEXTO_2)
            estilo(ax, "y")
            virgulas(ax)
            if c == 0:
                fig.legend(*ax.get_legend_handles_labels(), loc="upper left", bbox_to_anchor=(0.03, 0.835), ncol=4,
                           fontsize=19, frameon=False)
        fig.text(0.975, 0.80, f"peso = {fmt_pt(wa, 2)}", fontsize=24, color=AZUL_FE, ha="right", fontweight="bold")
        rodape(fig, "No VIKOR o eixo está invertido (para cima é melhor); o Pt-Cr fica em 1.º no TOPSIS e no VIKOR "
                    "em todo o intervalo")
        yield imagem(fig)
        plt.close(fig)


def anim_scaffold_degradacao(n_iter: int = 10_000) -> Iterator[np.ndarray]:
    mats = ["β-TCP poroso", "Compósito PCL/β-TCP (impressão 3D)"]
    T, ref = tempos_degradacao(mats)
    tmax = 24.0
    ts = np.linspace(0, tmax, 481)
    dur, a, b = 12.0, 1.0, 9.5
    for i in range(int(dur * FPS)):
        t = i / FPS
        agora = tmax * fase(t, a, 7.5) + (ref - tmax) * fase(t, 8.0, b)
        fig = nova_figura()
        cabecalho(fig, "Degradação: o β-TCP aproxima-se mais do cenário de referência",
                  f"Massa restante ao longo do tempo, com o tempo de degradação típico da base; cenário de "
                  f"referência: {fmt_pt(ref, 0)} meses", ROTULO_ESQ)
        ax = fig.add_axes((0.08, 0.16, 0.58, 0.6))
        ax.axvline(ref, color=TEXTO, lw=2.5, ls=(0, (5, 3)))
        ax.text(ref - 0.25, 103, f"referência: {fmt_pt(ref, 0)} meses", fontsize=F_EIXO, color=TEXTO, ha="right")
        for mat in mats:
            sel = ts <= agora
            c = cor_caso("Scaffold", mat)
            ax.plot(ts, massa_restante(ts, T[mat]), color=c, lw=2, alpha=0.18)
            ax.plot(ts[sel], massa_restante(ts[sel], T[mat]), color=c, lw=5, label=f"{curto(mat)}: "
                    f"{fmt_pt(T[mat], 0)} meses")
            ax.plot([agora], [float(massa_restante(agora, T[mat]))], "o", ms=16, color=c, mec="white", mew=2.5)
        ax.axvline(agora, color=TEXTO_2, lw=1.2)
        ax.set_xlim(0, tmax)
        ax.set_ylim(0, 110)
        ax.set_xticks(range(0, 25, 3))
        ax.set_xlabel("tempo (meses)", fontsize=F_EIXO, color=TEXTO_2)
        ax.set_ylabel("massa restante (%)", fontsize=F_EIXO, color=TEXTO_2)
        estilo(ax, "both")
        ax.legend(loc="upper right", fontsize=F_EIXO, frameon=False)
        # blocos do scaffold a desaparecer, um por material
        for k, mat in enumerate(mats):
            bx = fig.add_axes((0.72, 0.47 - k * 0.3, 0.24, 0.24))
            frac = float(massa_restante(agora, T[mat])) / 100
            rng = np.random.default_rng(7 + k)
            cel = rng.random((10, 10))
            bx.imshow(np.where(cel < frac, 1.0, np.nan), cmap=matplotlib.colors.ListedColormap([cor_caso("Scaffold", mat)]),
                      vmin=0, vmax=1)
            bx.set_xticks([])
            bx.set_yticks([])
            for lado in bx.spines.values():
                lado.set_color(GRELHA)
            bx.set_title(f"{curto(mat)}: {fmt_pt(100 * frac, 0)} %", fontsize=19, color=TEXTO, loc="left")
        fig.text(0.72, 0.80, f"t = {fmt_pt(agora, 1)} meses", fontsize=26, color=AZUL_FE, fontweight="bold")
        rodape(fig, "Forma da curva assumida: perda de massa linear até à reabsorção completa no tempo típico "
                    "(esquema; a cinética real não é linear)")
        yield imagem(fig)
        plt.close(fig)


# ---------------------------------------------------------------- animações 3D (pyvista)

def _plotter(tamanho: tuple[int, int]):
    import pyvista as pv
    pv.OFF_SCREEN = True
    pl = pv.Plotter(off_screen=True, window_size=list(tamanho), lighting="three lights")
    pl.set_background("white")
    pl.enable_anti_aliasing("ssaa")
    return pl


def campo_giroide(n: int = 96, celulas: float = 2.0) -> tuple[np.ndarray, float]:
    """Campo do giroide sin x cos y + sin y cos z + sin z cos x numa grelha n³ (celulas períodos por lado)."""
    x = np.linspace(0, 2 * np.pi * celulas, n)
    X, Y, Z = np.meshgrid(x, x, x, indexing="ij")
    return np.sin(X) * np.cos(Y) + np.sin(Y) * np.cos(Z) + np.sin(Z) * np.cos(X), x[1] - x[0]


def anim_rede_porosa(n_iter: int = 10_000) -> Iterator[np.ndarray]:
    import pyvista as pv
    E_s, alvo = modulo_e_alvo_haste()
    p_alvo = porosidade_para(alvo, E_s)
    campo, h = campo_giroide()
    n = campo.shape[0]
    grade = pv.ImageData(dimensions=(n, n, n), spacing=(h, h, h))
    grade.point_data["f"] = campo.ravel(order="F")
    pl = _plotter((1000, 1000))
    cache: dict[float, pv.PolyData] = {}
    dur = 13.0
    for i in range(int(dur * FPS)):
        t = i / FPS
        if t < 8.0:
            p = 0.70 * fase(t, 0.8, 8.0)
        else:
            p = 0.70 + (p_alvo - 0.70) * fase(t, 8.0, 9.5)
        pq = round(p, 3)
        if pq not in cache:
            if pq <= 0.0005:
                cache[pq] = pv.Box(bounds=grade.bounds).triangulate()
            else:
                solido = grade.clip_scalar(scalars="f", value=limiar_porosidade(campo, pq), invert=True)
                cache[pq] = solido.extract_surface(algorithm="dataset_surface").compute_normals(
                    auto_orient_normals=True, split_vertices=True, feature_angle=45)
            if len(cache) > 40:
                cache.pop(next(iter(cache)))
        for ator in list(pl.actors):
            pl.remove_actor(ator)
        pl.add_mesh(cache[pq], color="#aeb8c2", smooth_shading=True, specular=0.5, specular_power=25,
                    ambient=0.2, diffuse=0.8)
        centro = np.array(grade.center)
        teta, fi = np.deg2rad(30 + 2.5 * t), np.deg2rad(28)  # rotação lenta, sem chegar a uma vista de face
        d = 4.6 * grade.length / 2
        pos = centro + d * np.array([np.cos(fi) * np.cos(teta), np.cos(fi) * np.sin(teta), np.sin(fi)])
        pl.camera_position = [tuple(pos), tuple(centro), (0, 0, 1)]
        pl.camera.view_angle = 30.0
        render = pl.screenshot(return_img=True)
        E = float(gibson_ashby(p, E_s))
        fig = nova_figura()
        cabecalho(fig, "Mais porosidade, menos rigidez: o alvo do osso aos 59,9 %",
                  f"Rede porosa (giroide) de Ti-6Al-4V; módulo pela relação de Gibson e Ashby, "
                  f"E = {fmt_pt(E_s, 1)} × (1 − p)² GPa", ROTULO_ESQ)
        ax3 = fig.add_axes((0.02, 0.06, 0.52, 0.76))
        ax3.imshow(render)
        ax3.axis("off")
        _mostrador(fig, E, E_s, alvo, p)
        if t > 9.5:
            fig.text(0.79, 0.12, f"p = {fmt_pt(100 * p_alvo, 1)} %  →  E = {fmt_pt(alvo, 0)} GPa", ha="center",
                     fontsize=30, fontweight="bold", color=AZUL_FE, alpha=fase(t, 9.5, 10.2))
        yield imagem(fig)
        plt.close(fig)
    pl.close()


def _mostrador(fig: plt.Figure, E: float, E_s: float, alvo: float, p: float) -> None:
    """Mostrador semicircular do módulo (0 a E_s) com a faixa do osso e o alvo."""
    tec = pd.read_csv(DATA / "tecido.csv")
    osso = tec[(tec["tecido"] == "Osso cortical") & (tec["propriedade"] == CRIT_MODULO)].iloc[0]
    ax = fig.add_axes((0.58, 0.30, 0.40, 0.48))
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-0.35, 1.2)
    ax.axis("off")
    ang = lambda v: 180 - 180 * v / E_s  # noqa: E731
    ax.add_patch(Wedge((0, 0), 1, 0, 180, width=0.18, color=GRELHA))
    ax.add_patch(Wedge((0, 0), 1, ang(float(osso["max"])), ang(float(osso["min"])), width=0.18, color="#e2b765"))
    a = np.deg2rad(ang(alvo))
    ax.plot([0.8 * np.cos(a), 1.04 * np.cos(a)], [0.8 * np.sin(a), 1.04 * np.sin(a)], color=TEXTO, lw=3)
    ax.text(1.12 * np.cos(a), 1.12 * np.sin(a), f"{fmt_pt(alvo, 0)}", fontsize=18, color=TEXTO, ha="center",
            va="center")
    for v in (0, 25, 50, 75, 100):
        b = np.deg2rad(ang(v))
        ax.text(1.12 * np.cos(b), 1.12 * np.sin(b), str(v), fontsize=16, color=TEXTO_2, ha="center", va="center")
    b = np.deg2rad(ang(E))
    ax.plot([0, 0.78 * np.cos(b)], [0, 0.78 * np.sin(b)], color=AZUL_FE, lw=6, solid_capstyle="round")
    ax.plot([0], [0], "o", ms=18, color=AZUL_FE)
    ax.text(0, -0.2, f"E = {fmt_pt(E, 1)} GPa", ha="center", fontsize=34, fontweight="bold", color=TEXTO)
    fig.text(0.78, 0.22, f"porosidade p = {fmt_pt(100 * p, 1)} %", ha="center", fontsize=26, color=TEXTO_2)
    fig.text(0.78, 0.80, "faixa do osso cortical a dourado; traço = alvo", ha="center", fontsize=17, color=TEXTO_2)


def malha_stent(raio: float, comprimento_strut: float = 0.62, coroas: int = 8, aneis: int = 6,
                passo: float = 0.95) -> list[np.ndarray]:
    """Linhas (pontos 3D) de um stent de anéis em ziguezague; os struts mantêm o comprimento ao abrir.

    Em linguagem simples: ao aumentar o raio, os ziguezagues abrem e encurtam na direção do eixo, como
    num stent real; é só geometria para explicar o conceito.
    """
    meio_passo = np.pi * raio / coroas  # distância circunferencial entre um pico e um vale
    altura = np.sqrt(max(comprimento_strut ** 2 - meio_passo ** 2, 0.02))
    linhas = []
    for k in range(aneis):
        z0 = k * passo
        ang = np.linspace(0, 2 * np.pi, 2 * coroas + 1)
        z = z0 + np.where(np.arange(2 * coroas + 1) % 2 == 0, 0, altura)
        linhas.append(np.column_stack([raio * np.cos(ang), raio * np.sin(ang), z]))
        if k < aneis - 1:
            for c in range(0, 2 * coroas, 4):
                a = ang[c + 1]
                linhas.append(np.array([[raio * np.cos(a), raio * np.sin(a), z0 + altura],
                                        [raio * np.cos(a), raio * np.sin(a), z0 + passo]]))
    return linhas


def anim_stent_expansao(n_iter: int = 10_000) -> Iterator[np.ndarray]:
    import pyvista as pv
    mats = ["Pt-Cr", "Co-Cr L605", "Aço inox 316L"]
    idx = indices_recuo(mats)
    r0, r1 = 0.5, 1.25
    recuo_max = 0.14  # fração do raio expandido para o maior índice; escala só ilustrativa
    escala = recuo_max / max(idx.values())
    roda = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], float)  # eixo do stent passa a ser x
    pl = _plotter((1840, 820))
    dur = 13.0
    for i in range(int(dur * FPS)):
        t = i / FPS
        expande = fase(t, 1.0, 5.0)
        sai = fase(t, 6.0, 8.5)
        for ator in list(pl.actors):
            pl.remove_actor(ator)
        for k, mat in enumerate(mats):
            recuo = escala * idx[mat] * r1
            raio = r0 + (r1 - r0) * expande - recuo * sai
            centro = np.array([0.0, 0.0, (1 - k) * 3.1])
            for ln in malha_stent(raio):
                pts = (ln - np.array([0, 0, 2.6])) @ roda.T + centro
                pl.add_mesh(pv.Spline(pts, len(pts) * 6 if len(pts) > 2 else 2).tube(radius=0.05),
                            color=cor_caso("Stent", mat), smooth_shading=True, specular=0.7, specular_power=40)
            raio_balao = (r0 * 0.9 + (r1 * 0.96 - r0 * 0.9) * expande) * (1 - 0.85 * sai)
            if raio_balao > 0.05:
                bal = pv.Cylinder(center=centro, direction=(1, 0, 0), radius=raio_balao, height=6.6, resolution=72)
                pl.add_mesh(bal, color="#8fc9ea", opacity=0.30, smooth_shading=True)
            pl.add_mesh(pv.Cylinder(center=centro, direction=(1, 0, 0), radius=0.07, height=9.0), color="#9aa3ab")
            if sai > 0:
                fantasma = pv.Cylinder(center=centro, direction=(1, 0, 0), radius=r1, height=5.6, resolution=72,
                                       capping=False)
                pl.add_mesh(fantasma.extract_feature_edges(boundary_edges=True, feature_edges=False,
                                                           manifold_edges=False),
                            color=TEXTO, line_width=3, opacity=0.55 * sai)
        pl.camera_position = [(0.0, -16.0, 2.0), (0.0, 0.0, 0.0), (0, 0, 1)]
        pl.camera.view_angle = 30.0
        render = pl.screenshot(return_img=True)
        fig = nova_figura()
        cabecalho(fig, "Expansão com balão e recuo elástico",
                  "Recuo proporcional ao índice σy/E da base (valor típico); o recuo real depende do desenho",
                  ROTULO_ESQ)
        ax3 = fig.add_axes((0.17, 0.08, 0.82, 0.76))
        ax3.imshow(render)
        ax3.axis("off")
        estado = ("crimpado no balão" if expande < 0.05 else
                  ("a expandir" if expande < 1 else ("balão retirado: recuo" if sai > 0 else "expandido")))
        fig.text(0.975, 0.86, estado, ha="right", fontsize=24, color=AZUL_FE, fontweight="bold")
        for k, mat in enumerate(mats):
            y = 0.67 - k * 0.235
            fig.text(0.035, y, curto(mat), fontsize=28, fontweight="bold", color=cor_caso("Stent", mat), va="center")
            fig.text(0.035, y - 0.055, f"σy/E = {fmt_pt(idx[mat] * 1000, 2)} × 10⁻³", fontsize=20, color=TEXTO,
                     va="center")
        if sai > 0:
            fig.text(0.6, 0.115, "contorno: diâmetro com o balão", fontsize=18, color=TEXTO_2, alpha=sai)
        rodape(fig, "Recuo proporcional ao índice σy/E; o recuo real depende do desenho (escala do recuo ampliada "
                    "para se ver)")
        yield imagem(fig)
        plt.close(fig)
    pl.close()


ANIMACOES: dict[str, Callable[[int], Iterator[np.ndarray]]] = {
    "alvo_haste": anim_alvo_haste, "mc_stent": anim_mc_stent, "gibson_ashby": anim_gibson_ashby,
    "scaffold_leitura": anim_scaffold_leitura, "sensibilidade_eta": anim_sensibilidade_eta,
    "mc_haste": anim_mc_haste, "pesos_stent": anim_pesos_stent, "rede_porosa": anim_rede_porosa,
    "stent_expansao": anim_stent_expansao, "scaffold_degradacao": anim_scaffold_degradacao,
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("nomes", nargs="*", default=list(ANIMACOES))
    ap.add_argument("--n-iter", type=int, default=10_000)
    a = ap.parse_args()
    for nome in a.nomes:
        gravar(nome, ANIMACOES[nome](a.n_iter))


if __name__ == "__main__":
    main()
