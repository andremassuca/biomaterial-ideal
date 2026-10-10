"""Vídeos dos diapositivos 3, 6, 7 e 8 da apresentação, desenhados ao tamanho em que aparecem.

Uso:
    python scripts/animacoes_diap.py [nomes ...] [--n-iter 10000]

Os vídeos de scripts/animacoes.py foram pensados para ecrã inteiro; no diapositivo ocupam 8,6 polegadas de largura e
a letra ficava a 8 ou 9 pt. Estes são desenhados numa figura de 8,6 × 4,84 polegadas (1920 × 1080 píxeis), por isso
os pontos da letra são os do diapositivo: mínimo de 14 pt. Sem título dentro do gráfico (o título é o do diapositivo),
com menos elementos e com os nomes simples dos materiais (scripts/nomes_simples.py).

Vídeos (apresentacao/media/<nome>.mp4, com a primeira e a última imagem em PNG):
  alvo_haste_diap        cada liga no seu módulo e a nota que recebe com o alvo do osso
  mc_haste_diap          C do TOPSIS de cada liga ao longo das repetições do Monte Carlo
  mc_stent_diap          % de repetições em 1.º lugar ao longo do Monte Carlo, só o TOPSIS
  scaffold_leitura_diap  C do TOPSIS do scaffold a passar da leitura ampla para a literal
Os números vêm das mesmas funções de scripts/animacoes.py (as do relatório).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable, Iterator

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "src"))
import animacoes as an  # noqa: E402
import estilo_graficos as eg  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import nomes_simples as ns  # noqa: E402

LARGURA_POL = 8.6  # largura do vídeo no diapositivo (polegadas)
DPI = 1920 / LARGURA_POL
F = 14  # letra mínima (pt no diapositivo)
F_NUM = 18
FPS = an.FPS


def figura():
    t = eg.aplicar("clara")
    fig = plt.figure(figsize=(LARGURA_POL, LARGURA_POL * 9 / 16), dpi=DPI, facecolor="white")
    return fig, t


def suave(x: float) -> float:
    return an.suave(min(1.0, max(0.0, x)))


def rotulo_material(m: str) -> str:
    """Nome simples numa linha e o código na seguinte (para os eixos)."""
    c = ns.codigo(m)
    return f"{ns.nome(m)}\n{c}" if c else ns.nome(m)


def _eixo_limpo(ax, t):
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.tick_params(axis="both", labelsize=F, length=0, colors=t["texto2"])
    ax.grid(axis="x", color=t["grelha"], lw=0.8)
    ax.set_axisbelow(True)


# ---------------------------------------------------------------- diapositivo 3: critérios-alvo

def anim_alvo_haste(n_iter: int = 10_000, segundos: float = 10.0) -> Iterator[np.ndarray]:
    df, alvo, osso = an.dados_alvo_haste()
    df = df[~df["investigacao"]].reset_index(drop=True)  # menos elementos: só as ligas em uso clínico
    n = len(df)
    for k in range(int(segundos * FPS)):
        tt = k / FPS
        fig, t = figura()
        ax = fig.add_axes([0.30, 0.15, 0.40, 0.78])
        bx = fig.add_axes([0.76, 0.15, 0.20, 0.78])
        ax.axvspan(osso[0], osso[1], color="#f3dfb4", lw=0, zorder=0)
        ax.axvline(alvo, color=an.AZUL_FE, lw=1.6, zorder=1)
        ax.text(alvo + 4, -0.45, f"alvo: {an.fmt_pt(alvo, 0)} GPa (osso)", fontsize=F, color=an.AZUL_FE,
                va="center")
        for i, r in df.iterrows():
            y = n - 1 - i
            a = suave((tt - 0.4 - 0.6 * i) / 0.6)
            cor = an.cor_caso("Haste", r["material"])
            ax.plot([alvo, r["E_tip"]], [y, y], color=cor, lw=1.2, alpha=0.45 * a)
            ax.scatter([r["E_tip"]], [y], s=90, color=cor, alpha=a, zorder=3)
            if a > 0.5:
                ax.text(r["E_tip"] + 6, y + 0.18, f"{an.fmt_pt(r['E_tip'], 0)} GPa", fontsize=F, color=t["texto2"],
                        alpha=a)
            b = suave((tt - 0.4 - 0.6 * n - 0.4 * i) / 0.8)
            bx.barh(y, r["nota"] * b, color=cor, height=0.55)
            if b > 0.95:
                bx.text(r["nota"] + 0.03, y, an.fmt_pt(r["nota"], 2), va="center", fontsize=F, color=t["texto"])
        ax.set_yticks(range(n), [rotulo_material(m) for m in df["material"][::-1]], fontsize=F)
        ax.set_xlim(0, 260)
        ax.set_ylim(-0.6, n - 0.2)
        ax.set_xlabel("Rigidez: módulo de Young (GPa)", fontsize=F, color=t["texto2"])
        _eixo_limpo(ax, t)
        bx.set_xlim(0, 1.25)
        bx.set_ylim(-0.6, n - 0.2)
        bx.set_yticks([])
        bx.set_xticks([0, 1], ["0", "1"])
        bx.set_xlabel("Nota (1 = no alvo)", fontsize=F, color=t["texto2"])
        _eixo_limpo(bx, t)
        yield an.imagem(fig)
        plt.close(fig)


# ---------------------------------------------------------------- diapositivo 6: Monte Carlo da haste

def anim_mc_haste(n_iter: int = 10_000, segundos: float = 11.0) -> Iterator[np.ndarray]:
    alts, C = an.mc_pontuacoes_haste(n_iter)
    ordem = np.argsort(-np.median(C, axis=0))
    bins = np.linspace(0, 1, 61)
    vence = np.argmax(C, axis=1)
    nf = int(segundos * FPS)
    for k in range(nf):
        frac = suave(k / (nf - 1.5 * FPS))
        it = max(1, int(round(frac * n_iter)))
        fig, t = figura()
        ax = fig.add_axes([0.30, 0.17, 0.66, 0.70])
        for r, j in enumerate(ordem):
            y = len(alts) - 1 - r
            h, _ = np.histogram(C[:it, j], bins=bins)
            h = 0.8 * h / max(1, h.max())
            ax.bar(bins[:-1], h, width=bins[1] - bins[0], bottom=y - 0.4, align="edge",
                   color=an.cor_caso("Haste", alts[j]), lw=0)
        venc = alts[ordem[0]]
        n_v = int((vence[:it] == alts.index(venc)).sum())
        fig.text(0.96, 0.92, f"{ns.nome(venc)} em 1.º: {eg.numero(n_v, 0)} de {eg.numero(it, 0)}",
                 ha="right", fontsize=F_NUM, color=t["texto"], fontweight="bold")
        ax.set_yticks(range(len(alts)), [rotulo_material(alts[j]) for j in ordem[::-1]], fontsize=F)
        ax.set_xlim(0, 1)
        ax.set_ylim(-0.6, len(alts) - 0.1)
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1], ["0", "0,25", "0,5", "0,75", "1"])
        ax.set_xlabel("Pontuação C do TOPSIS (1 = melhor)", fontsize=F, color=t["texto2"])
        _eixo_limpo(ax, t)
        yield an.imagem(fig)
        plt.close(fig)


# ---------------------------------------------------------------- diapositivo 7: Monte Carlo do stent (TOPSIS)

def anim_mc_stent(n_iter: int = 10_000, segundos: float = 11.0) -> Iterator[np.ndarray]:
    alts, acc = an.mc_acumulado("Stent", n_iter)
    y = acc["TOPSIS"]
    mats = [m for m in an.MATERIAIS_MC_STENT if m in alts]
    nf = int(segundos * FPS)
    x = np.arange(1, n_iter + 1)
    for k in range(nf):
        frac = suave(k / (nf - 1.5 * FPS))
        it = max(2, int(round(frac * n_iter)))
        fig, t = figura()
        ax = fig.add_axes([0.14, 0.17, 0.52, 0.78])
        for m in mats:
            j = alts.index(m)
            cor = an.cor_caso("Stent", m)
            ax.plot(x[:it], y[:it, j], color=cor, lw=2.2)
            ax.scatter([x[it - 1]], [y[it - 1, j]], s=40, color=cor, zorder=3)
            ax.annotate(f"{ns.nome(m)} ({ns.codigo(m)})\n{an.fmt_pt(y[it - 1, j], 1)} %", xy=(n_iter, y[it - 1, j]),
                        xytext=(14, 0), textcoords="offset points", va="center", fontsize=F, color=t["texto"],
                        fontweight="bold" if m == "Pt-Cr" else "normal", annotation_clip=False)
        ax.set_xlim(0, n_iter)
        ax.set_ylim(0, 100)
        ax.set_yticks([0, 25, 50, 75, 100], ["0 %", "25 %", "50 %", "75 %", "100 %"])
        ax.set_xticks([0, n_iter // 2], ["0", eg.numero(n_iter // 2, 0)])
        ax.set_xlabel("Repetições do Monte Carlo (TOPSIS)", fontsize=F, color=t["texto2"])
        ax.set_ylabel("Vezes em 1.º lugar", fontsize=F, color=t["texto2"])
        ax.grid(axis="y", color=t["grelha"], lw=0.8)
        for lado in ("top", "right"):
            ax.spines[lado].set_visible(False)
        ax.tick_params(labelsize=F, colors=t["texto2"], length=0)
        yield an.imagem(fig)
        plt.close(fig)


# ---------------------------------------------------------------- diapositivo 8: as duas leituras do scaffold

def anim_scaffold_leitura(n_iter: int = 10_000, segundos: float = 10.0) -> Iterator[np.ndarray]:
    L = an.leituras_scaffold()
    a, b = L["ampla"].set_index("material")["TOPSIS"], L["literal"].set_index("material")["TOPSIS"]
    mats = list(a.sort_values(ascending=False).index)
    nf = int(segundos * FPS)
    for k in range(nf):
        tt = k / FPS
        f = suave((tt - 3.0) / 3.0)  # 3 s na leitura ampla, 3 s de transição, o resto na literal
        v = {m: (1 - f) * a[m] + f * b[m] for m in mats}
        ordem = sorted(mats, key=lambda m: -v[m])
        fig, t = figura()
        ax = fig.add_axes([0.32, 0.17, 0.60, 0.70])
        for r, m in enumerate(ordem):
            y = len(mats) - 1 - r
            cor = an.cor_caso("Scaffold", m)
            ax.barh(y, v[m], color=cor, height=0.6)
            ax.text(v[m] + 0.01, y, an.fmt_pt(v[m], 3), va="center", fontsize=F, color=t["texto"],
                    fontweight="bold" if r == 0 else "normal")
        ax.set_yticks(range(len(mats)), [rotulo_material(m) for m in ordem[::-1]], fontsize=F)
        ax.set_xlim(0, 0.85)
        ax.set_ylim(-0.6, len(mats) - 0.4)
        ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8], ["0", "0,2", "0,4", "0,6", "0,8"])
        ax.set_xlabel("Pontuação C do TOPSIS (1 = melhor)", fontsize=F, color=t["texto2"])
        _eixo_limpo(ax, t)
        leitura = "Leitura ampla: inclui o suporte mecânico" if f < 0.5 else \
            "Leitura literal: só células e degradação"
        fig.text(0.32, 0.92, leitura, fontsize=F_NUM, color=an.AZUL_FE, fontweight="bold")
        yield an.imagem(fig)
        plt.close(fig)


ANIMACOES: dict[str, Callable[[int], Iterator[np.ndarray]]] = {
    "alvo_haste_diap": anim_alvo_haste,
    "mc_haste_diap": anim_mc_haste,
    "mc_stent_diap": anim_mc_stent,
    "scaffold_leitura_diap": anim_scaffold_leitura,
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("nomes", nargs="*", default=list(ANIMACOES))
    ap.add_argument("--n-iter", type=int, default=10_000)
    a = ap.parse_args()
    for nome in a.nomes:
        an.gravar(nome, ANIMACOES[nome](a.n_iter), gif=False)


if __name__ == "__main__":
    main()
