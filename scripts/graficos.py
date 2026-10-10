"""Gráficos do poster e da apresentação no estilo do projeto (design/biomat.mplstyle).

Uso:
    python scripts/graficos.py

Saída: design/graficos/<clara|escura>/<nome>.svg, .pdf e .png (300 ppp). O relatório entregue não usa estes
gráficos (fica com scripts/figuras.py). Os números vêm de results/ e data/ (através de scripts/figuras.py,
scripts/animacoes.py e do pacote biomat_mcdm).

Gráficos:
  espectro       ΔC do TOPSIS entre o 1.º e o 2.º em cada caso e cenário: quanto maior, mais claro o vencedor
  mc_stent       % de repetições em 1.º lugar no Monte Carlo das propriedades do stent (cenário A), por método
  gibson_ashby   E = E_s (1 − p)² das ligas da haste até ao alvo de 17 GPa, com a faixa do osso cortical
  scaffold       C do TOPSIS do scaffold nas duas leituras do problema crítico (ampla e literal)
  funil          funil de triagem: do Materials Project até um material por dispositivo (results/funil.csv)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
import estilo_graficos as eg  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

from figuras import COR_MATERIAL, LIMIAR_EMPATE, curto  # noqa: E402

RESULTS = RAIZ / "results"
DATA = RAIZ / "data"
SAIDA = RAIZ / "design" / "graficos"
METODOS = ("TOPSIS", "WASPAS", "VIKOR")
MARCA_METODO = {"TOPSIS": "o", "WASPAS": "D", "VIKOR": "s"}


# ---------------------------------------------------------------- dados (funções puras, testadas)

def dados_espectro(pt: pd.DataFrame) -> pd.DataFrame:
    """ΔC do TOPSIS (1.º menos 2.º) e o vencedor de cada caso e cenário quantitativo.

    Em linguagem simples: mede a distância entre o primeiro e o segundo classificados; um ΔC pequeno quer dizer
    que a escolha depende dos dados, um ΔC grande quer dizer que o vencedor é claro.
    """
    linhas = []
    for (caso, cen), g in pt.groupby(["caso", "cenario"], sort=False):
        g = g.sort_values("C_TOPSIS", ascending=False)
        linhas.append({"caso": caso, "cenario": cen, "vencedor": g.iloc[0]["material"],
                       "segundo": g.iloc[1]["material"], "delta_c": float(g.iloc[0]["C_TOPSIS"] - g.iloc[1]["C_TOPSIS"])})
    return pd.DataFrame(linhas)


def dados_mc_stent(mc: pd.DataFrame) -> pd.DataFrame:
    """% de repetições em 1.º lugar por material e método no Monte Carlo das propriedades do stent."""
    t = mc[(mc["caso"] == "Stent") & (mc["analise"] == "MC propriedades")]
    return t.pivot(index="material", columns="metodo", values="pct_primeiro")[list(METODOS)].sort_values(
        "TOPSIS", ascending=True)


ETAPAS_FUNIL = [  # (etapa em results/funil.csv, texto no gráfico)
    ("Materials Project (todos os compostos)", "compostos inorgânicos no Materials Project"),
    ("Sem elementos excluídos", "sem elementos tóxicos ou radioativos"),
    ("Estáveis", "estáveis"),
    ("Módulo de Young dentro do intervalo", "com rigidez calculada adequada"),
    ("Base verificada (materiais por componente)", "na base verificada, com fontes publicadas"),
    ("Recomendação (um material por dispositivo)", "recomendados: um por dispositivo"),
]


def dados_funil(tab: pd.DataFrame) -> pd.DataFrame:
    """Etapas do funil a mostrar, com o número e a largura relativa da barra (escala logarítmica).

    Em linguagem simples: os números vão de centenas de milhares até 5; numa escala normal as últimas barras nem
    se viam, por isso a largura segue o número de algarismos (logaritmo), e o número exato fica escrito ao lado.
    """
    n = tab.set_index("etapa")["n"]
    d = pd.DataFrame([{"etapa": e, "texto": txt, "n": int(n[e])} for e, txt in ETAPAS_FUNIL])
    d["largura"] = np.log10(d["n"].clip(lower=1) + 1) / np.log10(d["n"].max() + 1)
    return d


# ---------------------------------------------------------------- gráficos

def _titulo(fig, titulo, subtitulo, t):
    fig.text(0.0, 1.02, titulo, ha="left", va="bottom", fontsize=14, fontweight="bold", color=t["texto"],
             transform=fig.transFigure)
    fig.text(0.0, 0.975, subtitulo, ha="left", va="bottom", fontsize=10.5, color=t["texto2"],
             transform=fig.transFigure)


def fig_espectro(pt: pd.DataFrame, tema="clara"):
    t = eg.aplicar(tema)
    d = dados_espectro(pt)
    fig, ax = plt.subplots(figsize=(8.0, 3.1))
    ordem = {"Haste": 2, "Stent": 1, "Scaffold": 0}
    xmax = max(0.12, d["delta_c"].max() * 1.15)
    ax.axvspan(0, LIMIAR_EMPATE, color=t["grelha"], lw=0, zorder=0)
    ax.text(LIMIAR_EMPATE / 2, 2.62, "empate\n(ΔC < 0,01)", ha="center", va="bottom", fontsize=8.5, color=t["texto2"])
    for _, r in d.iterrows():
        y = ordem[r["caso"]] + (0.14 if r["cenario"] == "A" else -0.14)
        cor = COR_MATERIAL[r["caso"]][r["vencedor"]]
        ax.plot([0, r["delta_c"]], [y, y], color=cor, lw=1.2, alpha=0.5, solid_capstyle="round")
        ax.scatter([r["delta_c"]], [y], s=46, color=cor, zorder=3, edgecolor=t["fundo"] if tema == "escura" else "white",
                   linewidth=1.2)
        ax.annotate(f"{r['cenario']}: {curto(r['vencedor'])}  ΔC = {eg.numero(r['delta_c'], 3)}",
                    xy=(r["delta_c"], y), xytext=(8, 0), textcoords="offset points", va="center", fontsize=9,
                    color=t["texto"])
    ax.set_yticks([2, 1, 0], ["Haste femoral", "Stent", "Scaffold ósseo"])
    ax.set_xlim(0, xmax)
    ax.set_ylim(-0.6, 2.9)
    from matplotlib.ticker import MultipleLocator
    ax.xaxis.set_major_locator(MultipleLocator(0.05))
    ax.xaxis.set_major_formatter(eg.virgula(2))
    ax.set_xlabel("ΔC do TOPSIS entre o 1.º e o 2.º classificados")
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    _titulo(fig, "Quanto maior o ΔC, mais claro o vencedor",
            "Cenários A (base) e B (com materiais em investigação); TOPSIS com critérios-alvo", t)
    return fig


def fig_mc_stent(mc: pd.DataFrame, tema="clara"):
    t = eg.aplicar(tema)
    d = dados_mc_stent(mc)
    fig, ax = plt.subplots(figsize=(8.0, 3.3))
    for i, (mat, r) in enumerate(d.iterrows()):
        cor = COR_MATERIAL["Stent"][mat]
        lo, hi = r.min(), r.max()
        ax.plot([lo, hi], [i, i], color=cor, lw=6, alpha=0.25, solid_capstyle="round")
        for m in METODOS:
            ax.scatter(r[m], i, marker=MARCA_METODO[m], s=42, color=cor, zorder=3,
                       edgecolor=t["fundo"] if tema == "escura" else "white", linewidth=1.0)
        faixa = f"{eg.numero(lo, 0)} a {eg.numero(hi, 0)} %" if hi - lo >= 0.5 else f"{eg.numero(hi, 0)} %"
        ax.annotate(faixa, xy=(hi, i), xytext=(12, 0), textcoords="offset points", va="center", fontsize=9.5,
                    color=t["texto"], fontweight="bold" if i == len(d) - 1 else "normal")
    ax.set_yticks(range(len(d)), [curto(m) for m in d.index])
    ax.set_xlim(-2, 100)
    ax.xaxis.set_major_formatter(eg.virgula(0, " %"))
    ax.set_xlabel("Repetições em que o material fica em 1.º lugar (Monte Carlo das propriedades)")
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    # chave das marcas (métodos) numa linha, por cima do gráfico
    for m in METODOS:
        ax.scatter([], [], marker=MARCA_METODO[m], color=t["texto2"], s=30, label=m)
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=3, handletextpad=0.3, columnspacing=1.2,
              fontsize=9, labelcolor=t["texto2"])
    n = int(mc[(mc["caso"] == "Stent") & (mc["analise"] == "MC propriedades")]["n_iter"].iloc[0])
    _titulo(fig, "No stent, o Pt-Cr ganha na maioria das repetições, mas não em todas",
            f"Cenário A; {eg.numero(n, 0)} repetições com as propriedades a variar dentro dos intervalos da base", t)
    return fig


def fig_gibson_ashby(tema="clara"):
    import animacoes as an

    t = eg.aplicar(tema)
    E_ti, alvo = an.modulo_e_alvo_haste()
    tec = pd.read_csv(DATA / "tecido.csv")
    cort = tec[(tec["tecido"] == "Osso cortical") & (tec["propriedade"] == "Módulo de Young")].iloc[0]
    p = np.linspace(0, 0.85, 200)
    fig, ax = plt.subplots(figsize=(8.0, 3.6))
    ax.axhspan(cort["min"], cort["max"], color="#E69F00", alpha=0.16, lw=0)
    ax.text(84.5, cort["max"] + 1.5,
            f"osso cortical\n{eg.numero(cort['min'], 0)} a {eg.numero(cort['max'], 0)} GPa",
            ha="right", va="bottom", fontsize=9, color=t["texto2"])
    cor = COR_MATERIAL["Haste"]["Ti-6Al-4V ELI"]
    ax.plot(p * 100, an.gibson_ashby(p, E_ti), color=cor, lw=2.2)
    ps = an.porosidade_para(alvo, E_ti)
    ax.plot([ps * 100, ps * 100], [0, alvo], color=t["texto2"], lw=0.8, ls=(0, (3, 3)))
    ax.scatter([ps * 100], [alvo], s=60, color=cor, zorder=4, edgecolor="white", linewidth=1.2)
    ax.annotate(f"{eg.numero(alvo, 0)} GPa com p = {eg.numero(ps * 100, 0)} %", xy=(ps * 100, alvo),
                xytext=(10, 14), textcoords="offset points", fontsize=10, fontweight="bold", color=t["texto"])
    ax.annotate(f"Ti-6Al-4V ELI maciço: {eg.numero(E_ti, 1)} GPa", xy=(0, E_ti), xytext=(10, -4),
                textcoords="offset points", va="top", fontsize=9.5, color=t["texto"])
    ax.set_xlim(0, 85)
    ax.set_ylim(0, E_ti * 1.08)
    ax.xaxis.set_major_formatter(eg.virgula(0, " %"))
    ax.set_xlabel("Porosidade p")
    ax.set_ylabel("Módulo efetivo E (GPa)")
    _titulo(fig, "A porosidade baixa a rigidez do titânio até à do osso",
            "Gibson e Ashby: E = E maciço × (1 − p)²; alvo da haste e módulo do maciço da base de dados", t)
    return fig


def espalhar(valores: dict, distancia: float) -> dict:
    """Posições dos rótulos afastadas pelo menos 'distancia' (mesma ordem dos valores), para não se sobreporem.

    Em linguagem simples: ordena os rótulos pela altura e empurra para cima os que ficam demasiado perto do de
    baixo; no fim volta a centrar o grupo para os rótulos não fugirem das linhas.
    """
    itens = sorted(valores.items(), key=lambda kv: kv[1])
    pos = []
    for _, v in itens:
        pos.append(max(v, pos[-1] + distancia) if pos else v)
    desvio = (sum(v for _, v in itens) - sum(pos)) / len(pos)
    return {k: q + desvio for (k, _), q in zip(itens, pos)}


def fig_scaffold(tema="clara"):
    import animacoes as an

    t = eg.aplicar(tema)
    l = an.leituras_scaffold()
    a = l["ampla"].set_index("material")["TOPSIS"]
    b = l["literal"].set_index("material")["TOPSIS"]
    fig, ax = plt.subplots(figsize=(8.0, 3.8))
    destaque = {a.idxmax(), b.idxmax()}
    ya, yb = espalhar(a.to_dict(), 0.016), espalhar(b.to_dict(), 0.016)
    for mat in a.index:
        cor = COR_MATERIAL["Scaffold"][mat]
        forte = mat in destaque
        ax.plot([0, 1], [a[mat], b[mat]], color=cor if forte else t["eixo"], lw=2.4 if forte else 1.2,
                alpha=1 if forte else 0.8, marker="o", ms=6 if forte else 4)
        ax.annotate(f"{curto(mat)}  {eg.numero(a[mat], 3)}", xy=(0, a[mat]), xytext=(-0.03, ya[mat]),
                    textcoords="data", ha="right", va="center", fontsize=9.5 if forte else 9,
                    fontweight="bold" if forte else "normal", color=t["texto"] if forte else t["texto2"])
        ax.annotate(f"{eg.numero(b[mat], 3)}  {curto(mat)}", xy=(1, b[mat]), xytext=(1.03, yb[mat]),
                    textcoords="data", ha="left", va="center", fontsize=9.5 if forte else 9,
                    fontweight="bold" if forte else "normal", color=t["texto"] if forte else t["texto2"])
    ax.set_xlim(-0.05, 1.05)
    ax.set_xticks([0, 1], ["Leitura ampla\n(ligação direta e indireta)", "Leitura literal\n(só ligação direta)"])
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.grid(False)
    ax.tick_params(axis="x", length=0, labelsize=10)
    _titulo(fig, "No scaffold, o vencedor depende de como se lê o problema crítico",
            "C do TOPSIS com o peso dos critérios do problema crítico reforçado (cenário P-foco)", t)
    return fig


def fig_funil(tab: pd.DataFrame, tema="clara"):
    t = eg.aplicar(tema)
    d = dados_funil(tab)
    fig, ax = plt.subplots(figsize=(8.0, 4.0))
    cor_ini, cor_fim = np.array([0.62, 0.66, 0.70]), np.array([0.0, 0.447, 0.698])  # cinzento até azul (Okabe e Ito)
    k = len(d)
    for i, r in d.iterrows():
        y = k - 1 - i
        cor = cor_ini + (cor_fim - cor_ini) * (i / (k - 1))
        w = 0.08 + 0.92 * r["largura"]
        ax.barh(y, w, left=-w / 2, height=0.72, color=cor, lw=0)
        ax.text(0.56, y, eg.numero(r["n"], 0), ha="left", va="center", fontsize=12, fontweight="bold",
                color=t["texto"])
        ax.text(0.56, y - 0.3, r["texto"], ha="left", va="center", fontsize=9, color=t["texto2"])
    ax.set_xlim(-0.55, 1.35)
    ax.set_ylim(-0.7, k - 0.5)
    ax.axis("off")
    fig.subplots_adjust(top=0.96, bottom=0.02)
    _titulo(fig, "De centenas de milhares de materiais até um por dispositivo",
            "Materials Project: propriedades calculadas, só para filtrar; a decisão usa a base verificada", t)
    return fig


def sem_titulo(fig):
    """Tira o título e o subtítulo da figura (para os diapositivos, em que o título do diapositivo já diz a frase)."""
    for txt in list(fig.texts):
        txt.remove()
    return fig


def main():
    pt = pd.read_csv(RESULTS / "pontuacoes.csv")
    mc = pd.read_csv(RESULTS / "monte_carlo.csv")
    funil = pd.read_csv(RESULTS / "funil.csv") if (RESULTS / "funil.csv").exists() else None
    for tema in ("clara", "escura"):
        figs = [("espectro", lambda: fig_espectro(pt, tema)), ("mc_stent", lambda: fig_mc_stent(mc, tema)),
                ("gibson_ashby", lambda: fig_gibson_ashby(tema)), ("scaffold", lambda: fig_scaffold(tema))]
        if funil is not None:
            figs.append(("funil", lambda: fig_funil(funil, tema)))
        for nome, fn in figs:
            for p in eg.gravar(fn(), nome, SAIDA / tema):
                print(p.relative_to(RAIZ))
            for p in eg.gravar(sem_titulo(fn()), f"{nome}_diap", SAIDA / tema, formatos=("png",)):
                print(p.relative_to(RAIZ))


if __name__ == "__main__":
    main()
