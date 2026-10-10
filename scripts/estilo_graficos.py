"""Funções de apoio ao estilo dos gráficos (design/biomat.mplstyle) para o poster, a apresentação e os vídeos.

- aplicar(tema): regista a letra Inter, carrega o estilo e ajusta as cores ao tema claro ou escuro;
- virgula(): formatador dos eixos com vírgula decimal;
- rotulo(): rótulo direto ao lado de uma série, com o texto em tinta de texto e um traço na cor da série;
- gravar(): grava SVG e PDF vetoriais e PNG a 300 ppp.
Os números dos gráficos vêm de results/ e data/; aqui só há aparência.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
ESTILO = RAIZ / "design" / "biomat.mplstyle"
FONTES = RAIZ / "design" / "fontes"

TINTA = {"clara": {"texto": "#14171a", "texto2": "#55595e", "grelha": "#e6e8eb", "eixo": "#9aa0a6",
                   "fundo": "#f7f6f2"},
         "escura": {"texto": "#f1f2f4", "texto2": "#a9aeb5", "grelha": "#2a2e34", "eixo": "#5b6168",
                    "fundo": "#121417"}}


def registar_inter() -> bool:
    """Regista os ficheiros da Inter (design/fontes) no matplotlib. Devolve True se a letra ficou disponível."""
    for f in sorted(FONTES.glob("Inter-*.ttf")):
        font_manager.fontManager.addfont(str(f))
    return any(f.name == "Inter" for f in font_manager.fontManager.ttflist)


def aplicar(tema: str = "clara") -> dict:
    """Carrega o estilo do projeto e as cores do tema ('clara' ou 'escura'); devolve as cores de texto do tema.

    Em linguagem simples: todos os gráficos ficam com a mesma letra, as mesmas espessuras e a mesma grelha; no
    tema escuro, o texto e a grelha passam a tons claros sobre fundo escuro.
    """
    if tema not in TINTA:
        raise ValueError("o tema tem de ser 'clara' ou 'escura'")
    registar_inter()
    plt.style.use(str(ESTILO))
    t = TINTA[tema]
    plt.rcParams.update({"text.color": t["texto"], "axes.labelcolor": t["texto2"], "xtick.color": t["eixo"],
                         "ytick.color": t["eixo"], "xtick.labelcolor": t["texto2"], "ytick.labelcolor": t["texto2"],
                         "grid.color": t["grelha"], "axes.edgecolor": t["eixo"]})
    return t


def numero(v: float, casas: int = 2) -> str:
    """Número com vírgula decimal e espaço fino nos milhares (por exemplo 10 000 e 0,51)."""
    s = f"{v:,.{casas}f}".replace(",", " ").replace(".", ",")
    return s.replace("-", "−")


def virgula(casas: int = 1, sufixo: str = "") -> FuncFormatter:
    """Formatador dos eixos com vírgula decimal (e um sufixo opcional, por exemplo ' %')."""
    return FuncFormatter(lambda v, _p: numero(v, casas) + sufixo)


def rotulo(ax, x, y, texto, cor, tema="clara", lado="direita", tamanho=10, negrito=False, dx=6):
    """Rótulo direto de uma série: um ponto pequeno na cor da série e o texto em tinta de texto ao lado.

    Em linguagem simples: em vez de uma legenda solta, o nome fica ao lado da própria linha ou ponto; o texto não
    usa a cor da série (legibilidade), só a marca pequena a usa. Devolve o objeto do texto.
    """
    t = TINTA[tema]
    s = 1 if lado == "direita" else -1
    ax.annotate("●", xy=(x, y), xytext=(s * dx, 0), textcoords="offset points", ha="center", va="center",
                fontsize=tamanho * 0.75, color=cor, annotation_clip=False)
    return ax.annotate(texto, xy=(x, y), xytext=(s * (dx + 8), 0), textcoords="offset points",
                       ha="left" if s > 0 else "right", va="center", fontsize=tamanho, color=t["texto"],
                       fontweight="bold" if negrito else "normal", annotation_clip=False)


def gravar(fig, nome: str, pasta: Path, formatos=("svg", "pdf", "png")) -> list[Path]:
    """Grava a figura em SVG e PDF (vetoriais) e PNG a 300 ppp; devolve os caminhos."""
    pasta.mkdir(parents=True, exist_ok=True)
    saida = []
    for f in formatos:
        p = pasta / f"{nome}.{f}"
        fig.savefig(p)
        saida.append(p)
    plt.close(fig)
    return saida
