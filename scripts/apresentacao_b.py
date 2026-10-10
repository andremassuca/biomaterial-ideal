"""Apresentação no estilo B (15 out 2026): 10 minutos, 13 diapositivos e diapositivos de reserva.

Uso:
    python scripts/apresentacao_b.py [--exportar] [--renders PASTA]

Saída: apresentacao/apresentacao_b.pptx; com --exportar (PowerPoint instalado), também apresentacao_b.pdf,
apresentacao_plano_B.pdf (o mesmo conteúdo, para a pen USB, sem depender dos vídeos) e
apresentacao/imagens_b/diapositivo_NN.png. O pptx exportado leva as letras embutidas.

Estilo B: capa e conclusão em azul-noite, conteúdo em branco, letra Inter, títulos-afirmação (o título diz a
conclusão do diapositivo), cartões claros e um só destaque quente. Imagens: renders do Blender
(scripts/renders_blender.py, variante transparente), gráficos de scripts/graficos.py e vídeos de
scripts/animacoes.py. Todos os números vêm de results/ e de data/.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import pandas as pd
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "src"))
import apresentacao as ap  # noqa: E402
import nomes_simples as ns  # noqa: E402
from figuras import curto  # noqa: E402

APRES = RAIZ / "apresentacao"
CACHE = APRES / "imagens_b" / "recursos"
DESTINO = APRES / "apresentacao_b.pptx"
RENDERS = [Path(r"partilha\renders\final"), Path(r"partilha\renders\rapida_8out")]

AUTOR = "André Oliveira Massuça"
ORIENTADOR = ""
CABECALHO = "Próteses e Órgãos Artificiais · Licenciatura em Engenharia Biomédica · Universidade Lusófona"
AVISO = "Ferramenta educativa; não é um dispositivo médico."

# tokens de cor do estilo B (os mesmos de scripts/design_direcoes.py)
NOITE = RGBColor(0x0B, 0x1B, 0x2E)
AZUL = RGBColor(0x05, 0x95, 0xD1)
AZUL_TEXTO = RGBColor(0x04, 0x77, 0xA8)
TEXTO = RGBColor(0x0F, 0x17, 0x20)
CINZA = RGBColor(0x55, 0x60, 0x6B)
CARTAO = RGBColor(0xF2, 0xF5, 0xF8)
LINHA = RGBColor(0xD5, 0xDD, 0xE5)
SUB_NOITE = RGBColor(0x9F, 0xB6, 0xC9)
QUENTE = RGBColor(0xE8, 0x83, 0x3A)
QUENTE_FUNDO = RGBColor(0xFD, 0xF0, 0xE6)
BRANCO = RGBColor(0xFF, 0xFF, 0xFF)
LETRA = "Inter"

DISPOSITIVOS = [  # (render, nome, o que tem de aguentar: o problema crítico indicado pelo docente)
    ("anca", "Haste femoral", "carga de anos sem soltar o osso"),
    ("articulacao", "Par articular", "desgaste e partículas"),
    ("stent_arteria", "Stent coronário", "abrir a artéria sem a ferir"),
    ("scaffold", "Scaffold ósseo", "suportar células e desaparecer a tempo"),
    ("dentario", "Implante dentário", "ligar-se ao osso sem corroer"),
]


# ---------------------------------------------------------------- dados (funções puras, testadas)

def pasta_renders(candidatas: list[Path] = RENDERS) -> Path:
    """Primeira pasta com os renders transparentes das cinco cenas (o 4K final, se já existir)."""
    for p in candidatas:
        if all((p / f"{c}_transparente.png").exists() for c, _, _ in DISPOSITIVOS):
            return p
    raise FileNotFoundError("sem renders transparentes das cinco cenas em " + ", ".join(map(str, candidatas)))


def confianca(numeros: ap.Numeros, leitura_muda_scaffold: bool,
              simples: bool = False) -> list[tuple[str, str, str, str]]:
    """Espectro de confiança: (dispositivo, material, nível, frase simples) para os cinco dispositivos.

    Em linguagem simples: cada escolha recebe um nível pelas regras do trabalho. Sólida: o vencedor ganha em
    pelo menos 99,9 % das repetições do Monte Carlo com os três métodos. Empate técnico: a margem ΔC fica abaixo
    de 0,01 em algum cenário. Depende da leitura: o vencedor muda com a leitura do problema crítico.
    Indicação (ou "Indicativo", com simples=True): casos semiquantitativos (notas de 1 a 5), em que o ranking só se
    lê como indicação. Com simples=True, os materiais levam os nomes simples (decisão de 8 out 2026); sem ele, ficam
    os nomes da versão 1 (usados pelo poster, que deixou de ser desenvolvido neste projeto)."""
    hc = numeros.mc_haste
    solida = min(hc.values()) >= 0.999 * numeros.n_iter
    stent_empate = min(numeros.dc_stent.values()) < 0.01
    if simples:
        mats = [ns.com_codigo("Ti-6Al-4V ELI"), "Platina-crómio ou cobalto-crómio (Pt-Cr ou L605)",
                ns.com_codigo("Compósito PCL/β-TCP (impressão 3D)"), ns.com_codigo(numeros.vencedor_par),
                ns.com_codigo(numeros.vencedor_dentario)]
        semi, f_par, f_dent = ("Indicativo", "a melhor nota no desgaste (notas de 1 a 5)",
                               "em 1.º em todas as versões, pela osteointegração (notas de 1 a 5)")
    else:
        mats = ["Ti-6Al-4V ELI", "Pt-Cr ou L605", "PCL/β-TCP", curto(numeros.vencedor_par),
                curto(numeros.vencedor_dentario)]
        semi, f_par, f_dent = ("Indicação", "a melhor nota no desgaste, numa escala de 1 a 5",
                               "em 1.º em todas as versões, pela osteointegração")
    return [
        ("Haste femoral", mats[0], "Sólida" if solida else "Provável",
         "ganha com os três métodos em quase todas as repetições"),
        ("Stent coronário", mats[1], "Empate técnico" if stent_empate else "Provável",
         "dois materiais quase iguais; decide a fonte que falta confirmar"),
        ("Scaffold ósseo", mats[2], "Depende da leitura" if leitura_muda_scaffold else "Provável",
         "muda para β-TCP se só contarem as células e a degradação"),
        ("Par articular", mats[3], semi, f_par),
        ("Implante dentário", mats[4], semi, f_dent),
    ]


def funil(results: Path = ap.RESULTS) -> dict[str, int]:
    """Números do funil de triagem (results/funil.csv, gerado por scripts/funil.py)."""
    t = pd.read_csv(results / "funil.csv")
    n = t.set_index("etapa")["n"]
    return {"mp": int(n["Materials Project (todos os compostos)"]),
            "nivel2": int(n["Módulo de Young dentro do intervalo"]),
            "elementos": int(n["Elementos avaliados"]), "normas": int(n["Normas ASTM de materiais para implantes"]),
            "base": int(n["Base verificada (materiais por componente)"]),
            "final": int(n["Recomendação (um material por dispositivo)"])}


def perfis_exemplo(results: Path = ap.RESULTS) -> list[tuple[str, str, str, str]]:
    """Perfis de referência em que o 1.º lugar (Borda) muda: (perfil, caso, antes, depois)."""
    p = pd.read_csv(results / "perfis_referencia.csv")
    saida = []
    for (_pid, desc, caso), g in p.groupby(["perfil", "descricao", "caso"], sort=False):
        antes = g.sort_values("pos_ref_Borda")["material"].iloc[0]
        depois = g.sort_values("pos_Borda")["material"].iloc[0]
        excl = str(g["excluidos"].iloc[0]) if pd.notna(g["excluidos"].iloc[0]) else ""
        if antes != depois or (excl and antes in excl):
            base = p[(p["caso"] == caso)].drop_duplicates("material")
            ref = base.sort_values("pos_ref_Borda")["material"].iloc[0]
            saida.append((desc, caso, ref, depois))
    return saida


def n_verificados(data: Path = ap.DATA) -> tuple[int, int]:
    """(linhas verificadas, linhas da base) em data/materiais.csv.

    Em linguagem simples: conta quantos valores da base têm um estado que começa por "Verificado" (fonte primária,
    fornecedor, derivado ou composição) e quantos valores há ao todo; os outros estão "A verificar"."""
    m = pd.read_csv(data / "materiais.csv")
    return int(m["estado"].astype(str).str.startswith("Verificado").sum()), len(m)


def mc_primeiro(caso: str, results: Path = ap.RESULTS) -> dict[str, dict[str, float]]:
    """% de repetições em 1.º lugar no Monte Carlo das propriedades: {material: {método: %}}.

    Em linguagem simples: lê do results/monte_carlo.csv, para um caso, quantas vezes (em %) cada material ficou em
    1.º lugar com cada método."""
    mc = pd.read_csv(results / "monte_carlo.csv")
    t = mc[(mc["caso"] == caso) & (mc["analise"] == "MC propriedades")]
    return {m: g.set_index("metodo")["pct_primeiro"].astype(float).to_dict() for m, g in t.groupby("material")}


def intervalo(material: str, propriedade: str, data: Path = ap.DATA) -> tuple[float, float, str]:
    """Mínimo, máximo e unidade de uma propriedade de um material na base verificada (primeira linha)."""
    m = pd.read_csv(data / "materiais.csv")
    r = m[(m["material"] == material) & (m["propriedade"] == propriedade)].iloc[0]
    return float(r["min"]), float(r["max"]), str(r["unidade"])


FEA_CSV = ap.RESULTS / "fea_haste.csv"
FEA_MAPA = ap.RESULTS / "figures" / "fea" / "sed_corte_coronal_diap.png"
FEA_ORDEM = ["Ti-6Al-4V poroso", "Ti-6Al-4V", "316L", "Co-Cr-Mo"]
FEA_NOMES = {"Ti-6Al-4V poroso": "Liga de titânio porosa\n(17 GPa)", "Ti-6Al-4V": "Liga de titânio\n(Ti-6Al-4V)",
             "316L": "Aço inoxidável\n(316L)", "Co-Cr-Mo": "Cobalto-crómio\n(Co-Cr-Mo)"}


def razoes_fea(csv: Path = FEA_CSV) -> dict[str, tuple[float, float]]:
    """Razão implantado / intacto da energia no osso (zonas de Gruen 1 e 7) na malha mais fina da FEA em Python."""
    d = pd.read_csv(csv)
    d = d[(d["malha_mm"] == d["malha_mm"].min()) & (d["material"].isin(FEA_ORDEM))]
    p = d.pivot(index="material", columns="zona", values="razao")
    return {m: (float(p.loc[m, 1]), float(p.loc[m, 7])) for m in FEA_ORDEM if m in p.index}


def gravar_diap(fig, destino: Path) -> Path:
    """Grava a figura com o tamanho exato que tem no diapositivo (sem recorte), em PNG a 300 ppp e fundo branco.

    Em linguagem simples: o estilo do projeto recorta as margens ao gravar, o que muda o tamanho da imagem e, ao
    encaixá-la na caixa do diapositivo, encolhe a letra; aqui a imagem fica com as polegadas da caixa, por isso 14 pt
    no gráfico são 14 pt no diapositivo."""
    import matplotlib.pyplot as plt
    destino.parent.mkdir(parents=True, exist_ok=True)
    with plt.rc_context({"savefig.bbox": "standard"}):  # o estilo do projeto usa "tight", que recorta
        fig.savefig(destino, dpi=300, transparent=False, facecolor="white")
    plt.close(fig)
    return destino


def grafico_fea(razoes: dict[str, tuple[float, float]], destino: Path, w: float = 5.25, h: float = 4.3) -> Path:
    """Gráfico das razões em Gruen 1 e 7, desenhado ao tamanho do diapositivo (letra mínima de 14 pt)."""
    import estilo_graficos as eg
    import matplotlib.pyplot as plt
    import numpy as np
    eg.aplicar("clara")
    fig, ax = plt.subplots(figsize=(w, h), dpi=300)
    mats = [m for m in FEA_ORDEM if m in razoes]
    y = np.arange(len(mats))[::-1]
    g1 = [razoes[m][0] for m in mats]
    g7 = [razoes[m][1] for m in mats]
    ax.barh(y + 0.19, g1, 0.36, color="#0072B2", label="Gruen 1")
    ax.barh(y - 0.19, g7, 0.36, color="#E69F00", label="Gruen 7 (junto ao colo)")
    ax.axvline(1, color="#55595e", lw=1, ls="--")
    ax.text(1.02, len(mats) - 0.45, "osso sem\nprótese", fontsize=14, color="#55595e", va="top")
    ax.set_yticks(y, [FEA_NOMES[m] for m in mats], fontsize=14)
    ax.set_xlim(0, 1.45)
    ax.set_xticks([0, 0.5, 1], ["0", "0,5", "1"], fontsize=14)
    ax.set_xlabel("Energia no osso face ao osso sem prótese", fontsize=14)
    ax.legend(fontsize=14, loc="lower left", bbox_to_anchor=(-0.02, 1.0), ncol=2, frameon=False, handlelength=1.0,
              columnspacing=0.8)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    return gravar_diap(fig, destino)


CFD_JSON = ap.RESULTS / "cfd_pulsatil.json"
CFD_MAPA = ap.RESULTS / "figures" / "cfd" / "tawss_mapas_diap.png"
CFD_ORDEM = ["Pt-Cr", "316L"]
CFD_NOMES = {"Pt-Cr": "Platina-crómio\n(79 µm)", "316L": "Aço inoxidável\n(135 µm)"}


def dados_cfd(js: Path = CFD_JSON) -> dict[str, dict]:
    """Resultados do fluxo pulsátil (results/cfd_pulsatil.json, gerado por scripts/cfd_stent.py resumo)."""
    import json
    return json.loads(js.read_text(encoding="utf-8"))


def grafico_cfd(dados: dict[str, dict], destino: Path, w: float = 5.25, h: float = 4.3) -> Path:
    """Barras da área da parede com corte baixo (TAWSS abaixo de 0,4 Pa), ao tamanho do diapositivo."""
    import estilo_graficos as eg
    import matplotlib.pyplot as plt
    import numpy as np
    eg.aplicar("clara")
    fig, ax = plt.subplots(figsize=(w, h), dpi=300)
    mats = [m for m in CFD_ORDEM if m in dados]
    v = [100 * dados[m]["fracao_baixa"] for m in mats]
    x = np.arange(len(mats))
    ax.bar(x, v, 0.55, color="#E67100")
    for xi, vi in zip(x, v):
        ax.text(xi, vi + 1.5, f"{vi:.0f} %", ha="center", va="bottom", fontsize=16, fontweight="bold")
    ax.set_xticks(x, [CFD_NOMES[m].replace("(79 µm)", f"({dados[m]['espessura_um']:.0f} µm)").replace(
        "(135 µm)", f"({dados[m]['espessura_um']:.0f} µm)") for m in mats], fontsize=14)
    ax.set_ylim(0, max(v) * 1.25 + 5)
    ax.set_yticks([])
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.set_title("Parede entre os struts com\nfluxo lento (abaixo de 0,4 Pa)", fontsize=14, loc="left")
    ax.grid(visible=False)
    fig.tight_layout()
    return gravar_diap(fig, destino)


def grafico_funil(tab: pd.DataFrame, destino: Path, w: float = 7.9, h: float = 4.9) -> Path:
    """Funil de triagem ao tamanho do diapositivo: números a 18 pt e legendas a 14 pt.

    Em linguagem simples: as mesmas etapas e larguras de scripts/graficos.py (largura pelo número de algarismos), mas
    com letra legível no diapositivo; na base de dados, a legenda diz que cada valor tem fonte e estado (nem todos
    estão verificados)."""
    import estilo_graficos as eg
    import graficos as gr
    import matplotlib.pyplot as plt
    import numpy as np
    t = eg.aplicar("clara")
    d = gr.dados_funil(tab)
    d.loc[d["etapa"] == "Base verificada (materiais por componente)", "texto"] = \
        "na base de dados, com fonte e estado por valor"
    fig = plt.figure(figsize=(w, h), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1])
    cor_ini, cor_fim = np.array([0.62, 0.66, 0.70]), np.array([0.0, 0.447, 0.698])
    k = len(d)
    for i, r in d.iterrows():
        y = k - 1 - i
        cor = cor_ini + (cor_fim - cor_ini) * (i / (k - 1))
        largura = 0.08 + 0.92 * r["largura"]
        ax.barh(y, largura, left=-largura / 2, height=0.7, color=cor, lw=0)
        ax.text(0.56, y + 0.13, eg.numero(r["n"], 0), ha="left", va="center", fontsize=18, fontweight="bold",
                color=t["texto"])
        ax.text(0.56, y - 0.22, r["texto"], ha="left", va="center", fontsize=14, color=t["texto2"])
    ax.set_xlim(-0.55, 2.1)
    ax.set_ylim(-0.6, k - 0.4)
    ax.axis("off")
    return gravar_diap(fig, destino)


def grafico_mc_stent(pct: dict[str, dict[str, float]], destino: Path, w: float = 5.55, h: float = 4.7) -> Path:
    """% de repetições em 1.º lugar no Monte Carlo do stent (três métodos), ao tamanho do diapositivo (14 pt).

    Em linguagem simples: uma linha por material, do método em que ganha menos ao método em que ganha mais, com uma
    marca por método e a faixa escrita ao lado (por exemplo, "56 a 70 %")."""
    import estilo_graficos as eg
    import matplotlib.pyplot as plt
    from figuras import COR_MATERIAL
    t = eg.aplicar("clara")
    metodos, marcas = ("TOPSIS", "WASPAS", "VIKOR"), {"TOPSIS": "o", "WASPAS": "D", "VIKOR": "s"}
    mats = sorted(pct, key=lambda m: pct[m].get("TOPSIS", 0))
    fig, ax = plt.subplots(figsize=(w, h), dpi=300)
    for i, m in enumerate(mats):
        v = [pct[m][k] for k in metodos]
        lo, hi = min(v), max(v)
        cor = COR_MATERIAL["Stent"].get(m, t["texto2"])
        ax.plot([lo, hi], [i, i], color=cor, lw=9, alpha=0.25, solid_capstyle="round")
        for k in metodos:
            ax.scatter(pct[m][k], i, marker=marcas[k], s=90, color=cor, zorder=3, edgecolor="white", linewidth=1.0)
        faixa = f"{eg.numero(lo, 0)} a {eg.numero(hi, 0)} %" if round(hi) != round(lo) else f"{eg.numero(hi, 0)} %"
        ax.annotate(nb(faixa), xy=(hi, i), xytext=(12, 0), textcoords="offset points", va="center", fontsize=14,
                    fontweight="bold" if i == len(mats) - 1 else "normal", color=t["texto"])
    ax.set_yticks(range(len(mats)), [ns.com_codigo(m).replace(" (", "\n(") for m in mats], fontsize=14)
    ax.set_xlim(-3, 100)
    ax.set_xticks([0, 50, 100], ["0 %", "50 %", "100 %"], fontsize=14)
    ax.set_xlabel("Repetições em 1.º lugar", fontsize=14)
    ax.grid(axis="y", visible=False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    for k in metodos:
        ax.scatter([], [], marker=marcas[k], color=t["texto2"], s=60, label=k)
    ax.legend(loc="lower right", bbox_to_anchor=(1.0, 1.0), ncol=3, handletextpad=0.1, columnspacing=0.5,
              fontsize=14, frameon=False)
    fig.tight_layout()
    return gravar_diap(fig, destino)


def grafico_gibson(destino: Path, w: float = 5.55, h: float = 4.7, data: Path = ap.DATA) -> Path:
    """Gibson e Ashby, E = E maciço × (1 − p)², ao tamanho do diapositivo (14 pt), com a faixa do osso cortical.

    Em linguagem simples: a curva mostra quanto a rigidez da liga de titânio cai com a porosidade; o ponto marca a
    porosidade em que chega ao alvo do osso. Os rótulos ficam em zonas livres para não se taparem."""
    import animacoes as an
    import estilo_graficos as eg
    import matplotlib.pyplot as plt
    import numpy as np
    from figuras import COR_MATERIAL
    t = eg.aplicar("clara")
    e_ti, alvo = an.modulo_e_alvo_haste(data)
    tec = pd.read_csv(data / "tecido.csv")
    cort = tec[(tec["tecido"] == "Osso cortical") & (tec["propriedade"] == "Módulo de Young")].iloc[0]
    cor = COR_MATERIAL["Haste"]["Ti-6Al-4V ELI"]
    p = np.linspace(0, 0.85, 200)
    ps = an.porosidade_para(alvo, e_ti)
    fig, ax = plt.subplots(figsize=(w, h), dpi=300)
    ax.axhspan(cort["min"], cort["max"], color="#E69F00", alpha=0.18, lw=0)
    ax.text(1, cort["max"] + 2, nb(f"osso cortical ({eg.numero(cort['min'], 0)} a {eg.numero(cort['max'], 0)} GPa)"),
            ha="left", va="bottom", fontsize=14, color=t["texto2"])
    ax.plot(p * 100, an.gibson_ashby(p, e_ti), color=cor, lw=2.6)
    ax.plot([ps * 100, ps * 100], [0, alvo], color=t["texto2"], lw=1.0, ls=(0, (3, 3)))
    ax.scatter([ps * 100], [alvo], s=90, color=cor, zorder=4, edgecolor="white", linewidth=1.2)
    ax.annotate(nb(f"{eg.numero(alvo, 0)} GPa") + "\n" + nb(f"com p = {eg.numero(ps * 100, 0)} %"),
                xy=(ps * 100, alvo), xytext=(8, 22), textcoords="offset points", ha="left", va="bottom", fontsize=14,
                fontweight="bold", color=t["texto"])
    ax.annotate(nb(f"Ti-6Al-4V maciço: {eg.numero(e_ti, 1)} GPa"), xy=(0, e_ti), xytext=(14, 4),
                textcoords="offset points", ha="left", va="bottom", fontsize=14, color=t["texto"])
    ax.set_xlim(0, 85)
    ax.set_ylim(0, e_ti * 1.22)
    ax.set_xticks([0, 20, 40, 60, 80], [f"{v} %" for v in (0, 20, 40, 60, 80)], fontsize=14)
    ax.set_yticks([0, 50, 100], ["0", "50", "100"], fontsize=14)
    ax.set_xlabel("Porosidade p", fontsize=14)
    ax.set_ylabel("Módulo E (GPa)", fontsize=14)
    fig.tight_layout()
    return gravar_diap(fig, destino)


def nb(s: str) -> str:
    """Troca os espaços por espaços que não partem a linha (para "10 000" ou "9 999 | 10 000" ficarem juntos)."""
    return str(s).replace(" ", "\u00a0").replace("\u2009", "\u00a0")


def mil(v) -> str:
    return nb(ap.milhares(v))


def n_regras(data: Path = ap.DATA) -> int:
    return len(pd.read_csv(data / "perfis_doente.csv"))


def imagem_reduzida(origem: Path, largura: int, destino_pasta: Path = CACHE) -> Path:
    """Cópia da imagem com a largura dada (os renders 4K pesariam dezenas de MB na apresentação)."""
    destino_pasta.mkdir(parents=True, exist_ok=True)
    d = destino_pasta / f"{origem.stem}_{largura}.png"
    if not d.exists() or d.stat().st_mtime < origem.stat().st_mtime:
        im = Image.open(origem)
        if im.width > largura:
            im = im.resize((largura, round(im.height * largura / im.width)), Image.LANCZOS)
        im.save(d, optimize=True)
    return d


def recortar_transparente(origem: Path, destino_pasta: Path = CACHE, margem: float = 0.06,
                          esbater: float = 0.10) -> Path:
    """Recorta a imagem transparente ao objeto e esbate a sombra junto às margens do recorte.

    Em linguagem simples: a caixa do recorte segue só o objeto (píxeis quase opacos), com uma margem; a sombra de
    contacto, que é meio transparente e se estende para lá do objeto, vai ficando transparente perto das margens,
    para não aparecer cortada a direito sobre fundos escuros."""
    import numpy as np
    destino_pasta.mkdir(parents=True, exist_ok=True)
    d = destino_pasta / f"{origem.stem}_recorte.png"
    if not d.exists() or d.stat().st_mtime < origem.stat().st_mtime:
        im = Image.open(origem).convert("RGBA")
        objeto = im.getchannel("A").point(lambda a: 255 if a > 230 else 0)
        x0, y0, x1, y1 = objeto.getbbox() or (0, 0, im.width, im.height)
        m = round(margem * max(x1 - x0, y1 - y0))
        im = im.crop((max(0, x0 - m), max(0, y0 - m), min(im.width, x1 + m), min(im.height, y1 + m)))
        a = np.asarray(im, dtype=np.float32).copy()
        h, w = a.shape[:2]
        e = max(1.0, esbater * max(w, h))
        dx = np.minimum(np.arange(w), np.arange(w)[::-1]) / e
        dy = np.minimum(np.arange(h), np.arange(h)[::-1]) / e
        rampa = np.clip(np.minimum.outer(dy, dx), 0, 1)
        sombra = a[..., 3] < 230  # só a sombra se esbate; o objeto fica intacto
        a[..., 3] = np.where(sombra, a[..., 3] * rampa, a[..., 3])
        Image.fromarray(a.astype(np.uint8), "RGBA").save(d)
    return d


def logotipo_branco(origem: Path, destino_pasta: Path = CACHE) -> Path:
    """Versão branca de um logótipo com transparência (para a capa escura)."""
    destino_pasta.mkdir(parents=True, exist_ok=True)
    d = destino_pasta / f"{origem.stem}_branco.png"
    im = Image.open(origem).convert("RGBA")
    branco = Image.new("RGBA", im.size, (255, 255, 255, 0))
    branco.putalpha(im.getchannel("A"))
    branco.save(d)
    return d


# ---------------------------------------------------------------- desenho

def caixa(slide, x, y, w, h, linhas, tamanho=18, cor=TEXTO, negrito=False, alinha=PP_ALIGN.LEFT,
          ancora=MSO_ANCHOR.TOP, nome=None, espaco=1.0):
    """Caixa de texto na letra do estilo; `linhas` é uma str ou uma lista de str ou de (str, tamanho, cor, negrito)."""
    return ap.texto(slide, x, y, w, h, linhas, tamanho, cor, negrito, LETRA, alinha, ancora, nome, espaco)


def cartao(slide, x, y, w, h, cor=CARTAO, nome=None):
    c = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    c.adjustments[0] = min(0.12, 0.16 / min(w, h))
    c.fill.solid()
    c.fill.fore_color.rgb = cor
    c.line.fill.background()
    c.shadow.inherit = False
    if nome:
        c.name = nome
    return c


def numero_grande(slide, x, y, w, valor, legenda, cor=AZUL, tam=40, nome=None):
    return caixa(slide, x, y, w, 1.4, [(valor, tam, cor, True), (legenda, 15, CINZA, False)], nome=nome)


def titulo(slide, frase: str, kicker: str | None = None, n: int | None = None, escuro=False) -> list:
    """Título-afirmação no topo (posição fixa), com o kicker por cima e o rodapé; devolve as formas a animar."""
    formas = []
    if kicker:
        formas.append(caixa(slide, 0.6, 0.38, 10.0, 0.4, kicker.upper(), 14, SUB_NOITE if escuro else AZUL_TEXTO,
                            True, nome="!!kicker"))
    formas.append(caixa(slide, 0.6, 0.72, 12.1, 0.9, frase, 30, BRANCO if escuro else TEXTO, True, nome="!!titulo",
                        ancora=MSO_ANCHOR.TOP))
    if n is not None:
        caixa(slide, 0.6, 6.98, 10.0, 0.32, f"{AUTOR}  ·  Qual é o biomaterial ideal?", 14, CINZA, nome="!!rodape")
        caixa(slide, 12.0, 6.98, 0.73, 0.32, str(n), 14, CINZA, alinha=PP_ALIGN.RIGHT, nome="!!numero")
    return formas


def figura(slide, caminho: Path, x, y, w=None, h=None, nome=None):
    f = slide.shapes.add_picture(str(caminho), Inches(x), Inches(y), Inches(w) if w else None,
                                 Inches(h) if h else None)
    if nome:
        f.name = nome
    return f


def figura_caixa(slide, caminho: Path, x, y, w, h, nome=None):
    """Imagem dentro da caixa (x, y, w, h), centrada e sem deformar."""
    im = Image.open(caminho)
    r = im.width / im.height
    if w / h > r:
        ww, hh = h * r, h
    else:
        ww, hh = w, w / r
    return figura(slide, caminho, x + (w - ww) / 2, y + (h - hh) / 2, ww, hh, nome)


def video(slide, nome: str, x, y, w, nome_forma=None):
    """Vídeo 16:9 com a última imagem como capa; devolve (forma, duração em ms)."""
    import imageio_ffmpeg
    mp4 = ap.MEDIA / f"{nome}.mp4"
    _, seg = imageio_ffmpeg.count_frames_and_secs(str(mp4))
    capa = ap.MEDIA / f"{nome}_final.png"
    f = slide.shapes.add_movie(str(mp4), Inches(x), Inches(y), Inches(w), Inches(w * 9 / 16),
                               poster_frame_image=str(capa), mime_type="video/mp4")
    if nome_forma:
        f.name = nome_forma
    return f, int(seg * 1000)


def fundo(slide, cor):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = cor


# ---------------------------------------------------------------- diapositivos

def construir(numeros: ap.Numeros | None = None, destino: Path = DESTINO, renders: Path | None = None) -> Path:
    n = numeros or ap.ler_numeros()
    R = renders or pasta_renders()
    fu = funil()
    rend = {c: imagem_reduzida(recortar_transparente(R / f"{c}_transparente.png"), 1400) for c, _, _ in DISPOSITIVOS}
    rend["stent"] = imagem_reduzida(recortar_transparente(R / "stent_transparente.png"), 1400)
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    vazio = prs.slide_layouts[6]
    plano: list[tuple] = []  # (slide, entradas, vídeos, esquema)

    def novo(escuro=False):
        s = prs.slides.add_slide(vazio)
        fundo(s, NOITE if escuro else BRANCO)
        return s

    # 1. Capa
    s = novo(True)
    figura(s, logotipo_branco(ap.LOGOS / "lusofona.png"), 0.6, 0.5, h=0.75)
    figura(s, ap.LOGOS / "fe.png", 1.85, 0.5, h=0.75)
    figura_caixa(s, rend["articulacao"], 7.3, 0.9, 5.6, 5.9, nome="!!render_capa")
    k = caixa(s, 3.05, 0.66, 9.7, 0.44, CABECALHO, 14, SUB_NOITE, ancora=MSO_ANCHOR.MIDDLE)
    t = caixa(s, 0.6, 2.3, 7.0, 2.0, "Qual é o biomaterial ideal?", 50, BRANCO, True, nome="!!titulo")
    sub = caixa(s, 0.6, 4.45, 6.6, 1.0, "Como escolher o material de cinco implantes com dados verificados e "
                "testes de robustez", 20, SUB_NOITE)
    aut = caixa(s, 0.6, 5.75, 6.6, 0.9, [(AUTOR, 18, BRANCO, True)])
    ap.notas(s, "Bom dia. Quando um hospital escolhe uma prótese, escolhe também o material que vai viver dentro do "
                "corpo durante anos. A pergunta deste trabalho é simples: qual é o biomaterial ideal? A resposta "
                "honesta é que depende, e o objetivo foi medir de quê. Comparei materiais para cinco implantes, com "
                "dados verificados nas fontes e três métodos de decisão, e testei se cada escolha resiste quando os "
                "dados mudam.")
    plano.append((s, [k, t, sub, aut], [], "capa"))

    # 2. O problema
    s = novo()
    f = titulo(s, "Que material pôr dentro do corpo?", "O problema", 2)
    cols = []
    cartao(s, 0.6, 1.85, 12.13, 3.75, NOITE)
    for i, (c, nome, desafio) in enumerate(DISPOSITIVOS):
        x = 0.6 + i * 2.426
        figura_caixa(s, rend[c], x + 0.05, 1.95, 2.33, 3.55)
        cols.append(caixa(s, x + 0.1, 5.75, 2.25, 1.15, [(nome, 16, TEXTO, True), (desafio, 14, CINZA, False)],
                          espaco=1.05))
    ap.notas(s, "Estes são os cinco implantes do trabalho: a haste e o par articular da prótese da anca, o stent "
                "coronário, o scaffold para regenerar osso e o implante dentário. Cada um tem um problema crítico, "
                "indicado pelo docente. A haste tem de aguentar anos de carga sem soltar o osso; o par articular "
                "não pode desgastar-se nem largar partículas; o stent tem de abrir a artéria sem a ferir; o scaffold "
                "tem de suportar as células e desaparecer a tempo; o implante dentário tem de se ligar ao osso sem "
                "corroer. As imagens são ilustrações feitas para o trabalho.")
    plano.append((s, f + cols, [], "conteudo"))

    # 3. Critérios-alvo
    s = novo()
    f = titulo(s, "Mais rígido não é melhor: o alvo é o osso", "A ideia", 3)
    v, d = video(s, "alvo_haste_diap", 0.6, 1.95, 8.6, "!!video_principal")  # 8,6 pol.: a largura do desenho
    lado = caixa(s, 9.45, 2.05, 3.3, 4.75, [
        ("Os métodos clássicos", 17, AZUL_TEXTO, True), ("só sabem que mais é melhor, ou que menos é melhor.", 16,
                                                         TEXTO, False),
        ("", 8, TEXTO, False),
        ("Os critérios-alvo", 17, AZUL_TEXTO, True), (f"dão a nota máxima a quem fica perto do valor ideal: na haste, "
                                                      f"o módulo do osso cortical ({ap.pt(n.extra['alvo'], 0)} GPa).",
                                                      16, TEXTO, False),
        ("", 8, TEXTO, False),
        ("Porquê?", 17, AZUL_TEXTO, True), ("Uma haste muito mais rígida do que o osso tira-lhe a carga, e o osso "
                                            "perde massa (stress shielding).", 16, TEXTO, False)], espaco=1.05)
    ap.notas(s, "Os métodos clássicos de decisão só sabem que mais é melhor ou que menos é melhor. Mas no corpo isso "
                "nem sempre é verdade. Uma haste muito mais rígida do que o osso fica com a carga toda, o osso à volta "
                "deixa de ser estimulado e perde massa; chama-se stress shielding. Por isso usei critérios-alvo, "
                f"segundo Petković e colegas, 2025: a nota máxima vai para o material mais perto do valor ideal, aqui "
                f"o módulo do osso cortical, {ap.pt(n.extra['alvo'], 0)} GPa. O vídeo mostra cada liga no seu módulo e a "
                "nota que recebe.")
    plano.append((s, f + [lado], [(v, d, True)], "conteudo"))

    # 4. Funil
    s = novo()
    f = titulo(s, f"De {mil(fu['mp'])} materiais a um por dispositivo", "Os dados", 4)
    nv, nt = n_verificados()
    g = figura_caixa(s, grafico_funil(pd.read_csv(ap.RESULTS / "funil.csv"), CACHE / "funil.png"), 0.5, 1.95, 7.9,
                     4.9, nome="!!grafico")
    niveis = caixa(s, 8.75, 2.05, 4.0, 4.7, [
        ("1  Triagem em larga escala", 16, AZUL_TEXTO, True),
        (f"Materials Project (propriedades calculadas), {fu['elementos']} elementos com toxicidade de fontes "
         f"oficiais e {fu['normas']} normas ASTM de implantes.", 14, TEXTO, False),
        ("", 6, TEXTO, False),
        ("2  Filtros automáticos", 16, AZUL_TEXTO, True),
        ("Sem elementos tóxicos ou radioativos, estáveis, densidade e rigidez adequadas.", 14, TEXTO, False),
        ("", 6, TEXTO, False),
        ("3  Base verificada", 16, AZUL_TEXTO, True),
        (f"{fu['base']} materiais com norma ou uso clínico; cada valor com fonte e estado: {nv} dos {nt} "
         "verificados em fontes primárias. É aqui que se decide.", 14, TEXTO, False)], espaco=1.05)
    ap.notas(s, f"A escolha começa larga. O Materials Project, uma base aberta, tem {mil(fu['mp'])} compostos "
                "inorgânicos com propriedades calculadas por computador; usei-as só para filtrar. Tirei os que têm "
                "elementos tóxicos ou radioativos, segundo as tabelas oficiais da ICH e da IARC, os instáveis e os de "
                f"densidade ou rigidez desadequadas: ficam {mil(fu['nivel2'])}. A decisão faz-se na base "
                f"verificada, com {fu['base']} materiais com norma ou uso clínico, cada valor com a sua fonte e o seu "
                f"estado: {nv} dos {nt} valores estão verificados em fontes primárias, a começar pelos que mais "
                "pesam no resultado; os outros ficam marcados a verificar. No fim fica um material recomendado por "
                "dispositivo.")
    plano.append((s, f + [g, niveis], [], "conteudo"))

    # 5. Os métodos
    s = novo()
    f = titulo(s, f"Três métodos e {mil(n.n_iter)} repetições por escolha", "O método", 5)
    metodos = [("TOPSIS", "Fica mais perto do ideal e mais longe do pior?"),
               ("WASPAS", "Soma e multiplica as notas: uma nota muito baixa pesa."),
               ("VIKOR", "Procura o compromisso: olha para o pior critério."),
               ("Borda", "Junta as três ordens numa só, por pontos.")]
    cs = []
    for i, (m, frase) in enumerate(metodos):
        x = 0.6 + i * 3.07
        cartao(s, x, 2.05, 2.87, 1.95)
        cs.append(caixa(s, x + 0.2, 2.2, 2.5, 1.7, [(m, 20, AZUL_TEXTO, True), (frase, 14, TEXTO, False)],
                        espaco=1.05))
    mc = cartao(s, 0.6, 4.3, 12.13, 1.85, QUENTE_FUNDO)
    mct = caixa(s, 0.85, 4.45, 7.6, 2.1, [
        ("Monte Carlo", 20, QUENTE, True),
        (f"Os dados reais têm intervalos, não valores exatos. Repete-se a decisão {mil(n.n_iter)} vezes, cada vez com valores "
         "sorteados dentro desses intervalos, e conta-se quantas vezes cada material fica em 1.º lugar.", 15, TEXTO,
         False)], espaco=1.05)
    big = caixa(s, 8.7, 4.45, 3.8, 1.6, [(mil(n.n_iter), 44, QUENTE, True),
                                         ("repetições por caso e método", 14, CINZA, False)])
    ap.notas(s, "Para não depender de um só método, usei três, que tratam os compromissos de forma diferente. O "
                "TOPSIS mede a distância à solução ideal; o WASPAS soma e multiplica as notas, por isso castiga uma "
                "nota muito baixa; o VIKOR procura o compromisso e olha para o pior critério. O método de Borda junta "
                "as três ordens numa só. Depois, como os dados reais têm intervalos, repeti cada decisão "
                f"{mil(n.n_iter)} vezes com valores sorteados dentro desses intervalos: é o Monte Carlo. Se um "
                "material ganha quase sempre, a escolha é sólida.")
    plano.append((s, f + cs + [mc, mct, big], [], "conteudo"))

    # 6 a 8. Casos quantitativos (mesmo esquema: Morph entre eles)
    def caso(nt, kicker, frase, render, video_nome, numeros_caso, nota):
        s = novo()
        f = titulo(s, frase, kicker, nt)
        v, d = video(s, video_nome, 0.6, 1.95, 8.6, "!!video_principal")
        im = figura_caixa(s, rend[render], 9.45, 1.85, 3.3, 1.7, nome="!!render_caso")
        nums = []
        for i, (val, leg) in enumerate(numeros_caso):
            y = 3.66 + i * 1.08
            cartao(s, 9.45, y, 3.3, 1.0)
            nums.append(caixa(s, 9.62, y + 0.04, 3.0, 0.92, [(val, 20, AZUL, True), (leg, 14, CINZA, False)],
                              ancora=MSO_ANCHOR.MIDDLE, nome=f"!!numero_{i}"))
        ap.notas(s, nota)
        plano.append((s, f + [im] + nums, [(v, d, True)], "caso"))

    hc = n.mc_haste
    caso(6, "Haste femoral", "Haste: a liga de titânio (Ti-6Al-4V) ganha quase sempre", "anca", "mc_haste_diap",
         [(f"{mil(hc['TOPSIS'])} a {mil(hc['VIKOR'])}", f"vitórias em {mil(n.n_iter)}, nos três métodos"),
          (f"C = {ap.pt(n.c_haste)}", "TOPSIS, cenário A"),
          (f"{round(n.extra['rigidez'])} ×", "mais rígido do que o alvo")],
         f"Na haste femoral, o Ti-6Al-4V ELI fica em 1.º lugar com os três métodos e nos dois cenários. No Monte "
         f"Carlo ganha em {mil(hc['TOPSIS'])} das {mil(n.n_iter)} repetições no TOPSIS, em "
         f"{mil(hc['WASPAS'])} no WASPAS e em {mil(hc['VIKOR'])} no VIKOR; é a escolha mais sólida "
         "do trabalho. Mas mesmo o "
         f"titânio continua cerca de {round(n.extra['rigidez'])} vezes mais rígido do que o alvo. Pela relação de "
         f"Gibson e Ashby, a mesma liga com {ap.pt(100 * n.extra['p_alvo'], 0)} % de porosidade chegaria ao alvo: a "
         "solução para o stress shielding pode estar no desenho da haste, não noutra liga.")
    lo, hi = n.mc_stent_ptcr
    # Monte Carlo triangular do stent com o WASPAS: RELATORIO.md, secção 2.8 (results/mc_triangular.md)
    tri_l605, tri_ptcr = "52,7", "46,8"
    caso(7, "Stent coronário", "Stent: platina-crómio e cobalto-crómio quase empatados", "stent_arteria", "mc_stent_diap",
         [(f"ΔC = {ap.pt(n.dc_stent['A'])}", "margem no cenário A"),
          (f"ΔC = {ap.pt(n.dc_stent['B'])}", "cenário B: empate"),
          (nb(f"{ap.pt(lo, 0)} a {ap.pt(hi, 0)} %"), "vitórias do Pt-Cr no Monte Carlo, consoante o método")],
         f"No stent, a escolha é frágil. No cenário A, o platina-crómio ganha no TOPSIS e no VIKOR e o "
         f"cobalto-crómio L605 no WASPAS, com uma margem de {ap.pt(n.dc_stent['A'])}; no cenário B ficam empatados, "
         f"com {ap.pt(n.dc_stent['B'])}. No Monte Carlo, o Pt-Cr ganha em {ap.pt(lo, 0)} a {ap.pt(hi, 0)} % das "
         "repetições, consoante o método; o vídeo mostra o TOPSIS. Com distribuições triangulares em vez de "
         f"uniformes, o WASPAS passa a dar mais vitórias ao L605, {tri_l605} % contra {tri_ptcr} %. É um empate "
         "técnico, e o modelo mostra-o em vez de o esconder. O 1.º lugar do Pt-Cr depende ainda de confirmar o seu "
         "módulo, a sua resistência à tração e o seu alongamento numa fonte primária, o O'Brien de 2010.")
    sc = mc_primeiro("Scaffold")
    tcp, comp = sc["β-TCP poroso"], sc["Compósito PCL/β-TCP (impressão 3D)"]
    caso(8, "Scaffold ósseo", "Scaffold: a resposta depende de como se lê o problema", "scaffold", "scaffold_leitura_diap",
         [(f"ΔC = {ap.pt(n.dc_scaffold['A'])}", "margem no cenário A"),
          (f"ΔC = {ap.pt(n.dc_scaffold['B'])}", "margem no cenário B"),
          ("Cerâmica porosa", "(β-TCP) ganha na leitura literal")],
         f"No scaffold, o compósito PCL com beta-TCP impresso em 3D fica em 1.º com os três métodos, com margens de "
         f"{ap.pt(n.dc_scaffold['A'])} e {ap.pt(n.dc_scaffold['B'])}. Mas a resposta depende de como se lê o "
         "problema crítico: se contarmos só o suporte celular e a degradação, o beta-TCP poroso passa à frente no "
         "TOPSIS e no VIKOR, como mostra o vídeo. Também depende da incerteza dos dados: no Monte Carlo, o beta-TCP "
         f"ganha em mais repetições do que o compósito com o TOPSIS, {ap.pt(tcp['TOPSIS'], 0)} % contra "
         f"{ap.pt(comp['TOPSIS'], 0)} %, mas não com o WASPAS, {ap.pt(tcp['WASPAS'], 0)} % contra "
         f"{ap.pt(comp['WASPAS'], 0)} %, nem com o VIKOR, {ap.pt(tcp['VIKOR'], 0)} % contra "
         f"{ap.pt(comp['VIKOR'], 0)} %. E houve outra lição: com os valores de partida ganhava o beta-TCP; a "
         "verificação das fontes mudou o vencedor.")

    # 9. Espectro de confiança
    s = novo()
    f = titulo(s, "Nem todas as escolhas merecem a mesma confiança", "Os resultados", 9)
    niveis = confianca(n, True, simples=True)
    cor_nivel = {"Sólida": AZUL, "Indicativo": CINZA, "Empate técnico": QUENTE, "Depende da leitura": QUENTE,
                 "Provável": AZUL_TEXTO}
    linhas = []
    for i, (disp, mat, nivel, frase) in enumerate(niveis):
        y = 2.0 + i * 0.95
        cartao(s, 0.6, y, 12.13, 0.82)
        chip = cartao(s, 0.8, y + 0.2, 2.1, 0.42, cor_nivel[nivel])
        tf = chip.text_frame
        tf.margin_left = tf.margin_right = Inches(0.05)
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = nivel
        r.font.size, r.font.bold, r.font.name, r.font.color.rgb = Pt(14), True, LETRA, BRANCO
        linhas.append(caixa(s, 3.15, y + 0.04, 5.4, 0.76, [(disp, 16, TEXTO, True), (mat, 14, AZUL_TEXTO, True)],
                            ancora=MSO_ANCHOR.MIDDLE))
        linhas.append(caixa(s, 8.75, y + 0.06, 3.9, 0.72, [(frase, 14, CINZA, False)], ancora=MSO_ANCHOR.MIDDLE))
    ap.notas(s, "Junto os cinco resultados num espectro de confiança. A haste é sólida: o titânio ganha em quase "
                "todas as repetições. O stent é um empate técnico entre dois materiais quase iguais. No scaffold, a "
                "resposta depende de como se lê o problema crítico e também da incerteza dos dados: no Monte Carlo, "
                "o beta-TCP ganha mais vezes com o TOPSIS. No par articular e no implante dentário, a maior "
                "parte do peso cabe a escalas de 1 a 5, por isso o ranking lê-se como indicação: a cerâmica ZTA no "
                "par articular e o titânio de grau 4 no implante dentário. Saber quanto confiar numa escolha é tão "
                "importante como a própria escolha.")
    plano.append((s, f + linhas, [], "conteudo"))

    # 10. Perfis de doente
    s = novo()
    f = titulo(s, "E o doente? Uma condição clínica pode mudar a escolha", "Extensão: perfis de doente", 10)
    exemplos = perfis_exemplo()
    cs = []
    exemplos = exemplos[:3]
    wc = (12.13 - 0.3 * (len(exemplos) - 1)) / max(1, len(exemplos))
    for i, (desc, caso_, antes, depois) in enumerate(exemplos):
        x = 0.6 + i * (wc + 0.3)
        cartao(s, x, 2.05, wc, 3.15)
        cs.append(caixa(s, x + 0.35, 2.25, wc - 0.7, 2.9, [
            (caso_, 14, AZUL_TEXTO, True), (desc, 22, TEXTO, True), ("", 10, TEXTO, False),
            ("sem perfil", 14, CINZA, False), (ns.com_codigo(antes), 18, CINZA, False), ("", 6, TEXTO, False),
            ("com o perfil", 14, CINZA, False), (ns.com_codigo(depois), 22, QUENTE, True)], espaco=1.02))
    regras = caixa(s, 0.6, 5.55, 8.6, 1.2, [
        (f"{n_regras()} regras com fonte por regra", 17, TEXTO, True),
        ("Excluem materiais (alergia confirmada) ou reforçam critérios (osteoporose, diabetes, tabagismo, "
         "radioterapia, RM frequente, entre outras).", 14, CINZA, False)], espaco=1.05)
    aviso = cartao(s, 9.45, 5.65, 3.28, 0.95, QUENTE_FUNDO)
    av = caixa(s, 9.6, 5.72, 3.0, 0.85, [(AVISO, 14, TEXTO, True)], ancora=MSO_ANCHOR.MIDDLE)
    ap.notas(s, "A última camada é o doente. Uma tabela de regras, cada uma com a sua fonte, liga condições "
                "clínicas aos critérios: uma alergia confirmada exclui materiais, e condições como a osteoporose, a "
                "diabetes ou o tabagismo reforçam o peso de um critério. Nos exemplos, um defeito ósseo sem carga "
                "troca o compósito pelo beta-TCP, e uma alergia ao titânio confirmada por teste troca o implante "
                "dentário de titânio pela zircónia. Os fatores de peso são valores de desenho. É uma ferramenta "
                "educativa, não um dispositivo médico.")
    plano.append((s, f + cs + [regras, aviso, av], [], "conteudo"))

    # 11. Aplicação
    s = novo()
    f = titulo(s, "Uma aplicação para explorar as escolhas", "A aplicação", 11)
    demo = APRES / "media" / "demo_app.mp4"
    vids = []
    if demo.exists():
        import imageio_ffmpeg
        _, seg = imageio_ffmpeg.count_frames_and_secs(str(demo))
        capa = APRES / "media" / "demo_app_inicio.png"
        v = s.shapes.add_movie(str(demo), Inches(0.6), Inches(1.95), Inches(8.4), Inches(4.725),
                               poster_frame_image=str(capa) if capa.exists() else None, mime_type="video/mp4")
        v.name = "!!video_principal"
        vids.append((v, int(seg * 1000), True))
        corpo = [v]
    else:
        m = cartao(s, 0.6, 1.95, 8.4, 4.725, NOITE, nome="!!video_principal")
        for i, c in enumerate(("stent", "dentario", "scaffold")):
            figura_caixa(s, rend[c], 1.0 + i * 2.65, 2.6, 2.4, 2.6)
        caixa(s, 0.9, 5.55, 7.8, 0.8, [("Aplicação nativa para Windows, em desenvolvimento", 16, BRANCO, True),
                                       ("Demonstração em vídeo nesta versão final", 14, SUB_NOITE, False)])
        corpo = [m]
    lista = caixa(s, 9.35, 2.05, 3.4, 4.6, [
        ("Ranking ao vivo", 16, AZUL_TEXTO, True), ("os pesos mudam e a ordem reage", 14, TEXTO, False),
        ("Monte Carlo", 16, AZUL_TEXTO, True), ("10 000 repetições no núcleo Rust", 14, TEXTO, False),
        ("Fluxo do doente", 16, AZUL_TEXTO, True), ("as regras aplicadas e porquê", 14, TEXTO, False),
        ("Modelos 3D", 16, AZUL_TEXTO, True), ("os implantes, para rodar e ver", 14, TEXTO, False),
        ("Secção Porquê", 16, AZUL_TEXTO, True), ("cada método explicado com um exemplo", 14, TEXTO, False)],
        espaco=1.02)
    ap.notas(s, "Para explorar estas escolhas fiz uma aplicação nativa. Escolhe-se o caso, ajustam-se os pesos e o "
                "ranking dos três métodos reage na hora; um botão corre o Monte Carlo no núcleo, escrito em Rust e "
                "testado contra o código Python. Há um fluxo para o doente, que mostra que regras se aplicam e "
                "porquê, os modelos 3D dos implantes e uma secção que explica cada método com um exemplo simples.")
    plano.append((s, f + corpo + [lista], vids, "conteudo"))

    # 12. Impacto no doente: a haste (FEA)
    s = novo()
    f = titulo(s, "Impacto no doente: a haste", "Extensão exploratória", 12)
    corpo = []
    if FEA_CSV.exists():
        corpo.append(figura_caixa(s, FEA_MAPA if FEA_MAPA.exists() else FEA_MAPA.with_name("sed_corte_coronal.png"),
                                  0.5, 1.75, 6.9, 4.3, nome="!!mapa_fea"))
        corpo.append(figura_caixa(s, grafico_fea(razoes_fea(), CACHE / "fea_razoes.png"), 7.55, 1.75, 5.25, 4.3,
                                  nome="!!grafico_fea"))
    frase = caixa(s, 0.6, 6.15, 9.4, 0.5, "Quanto mais rígida a haste, menos carga chega ao osso junto ao colo.", 18,
                  TEXTO, True)
    rot = caixa(s, 10.0, 6.15, 2.75, 0.62, "Simulação exploratória; hipóteses no relatório", 14, CINZA,
                alinha=PP_ALIGN.RIGHT)
    ap.notas(s, "Para ver o efeito no doente, simulei a haste dentro de um fémur anatómico por elementos finitos, com a "
                "carga do pico da marcha. O mapa mostra a energia de deformação no osso: com uma haste muito rígida, o "
                "osso junto ao colo quase deixa de trabalhar, e osso que não trabalha perde massa. No gráfico, em "
                "relação ao osso sem prótese: o cobalto-crómio e o aço deixam só uma pequena parte da carga no osso "
                "junto ao colo; a liga de titânio deixa mais; a liga de titânio porosa fica próxima do osso intacto, "
                "num modelo com a interface colada e a rigidez igual à do osso. Confirmei a ordem com um segundo "
                "programa, o SOLIDWORKS Simulation.")
    plano.append((s, f + corpo + [frase, rot], [], "conteudo"))

    # 13. Impacto no doente: o stent (CFD)
    s = novo()
    f = titulo(s, "Impacto no doente: o stent", "Extensão exploratória", 13)
    corpo = []
    notas_cfd = ("Para o stent, simulei o sangue a passar numa artéria coronária de 3 mm com o stent, com o fluxo a "
                 "pulsar como no coração. ")
    if CFD_JSON.exists() and CFD_MAPA.exists():
        d = dados_cfd()
        corpo.append(figura_caixa(s, CFD_MAPA, 0.5, 1.75, 6.9, 4.3, nome="!!mapa_cfd"))
        corpo.append(figura_caixa(s, grafico_cfd(d, CACHE / "cfd_area_baixa.png"), 7.55, 1.75, 5.25, 4.3,
                                  nome="!!grafico_cfd"))
        p, a = d.get("Pt-Cr"), d.get("316L")
        if p and a:
            notas_cfd += (f"O mapa é a parede aberta como uma folha: a branco os struts, a laranja a parede onde o "
                          f"sangue roça devagar, abaixo de 0,4 pascal, o valor associado a uma parede que tende a "
                          f"engrossar. Com os struts finos de platina-crómio, {100 * p['fracao_baixa']:.0f} % da "
                          f"parede entre os struts fica nessa zona; com os struts grossos de aço, "
                          f"{100 * a['fracao_baixa']:.0f} %. ").replace(".", ",", 0)
    frase = caixa(s, 0.6, 6.15, 9.4, 0.5, "Struts mais grossos deixam mais parede com o sangue a passar devagar.", 18,
                  TEXTO, True)
    rot = caixa(s, 10.0, 6.15, 2.75, 0.62, "Simulação exploratória; hipóteses no relatório", 14, CINZA,
                alinha=PP_ALIGN.RIGHT)
    ap.notas(s, notas_cfd + "A espessura do strut é do dispositivo, não só do material, e isto é um indicador do "
                            "fluxo, não uma previsão de reestenose.")
    plano.append((s, f + corpo + [frase, rot], [], "conteudo"))

    # 14. Conclusão
    s = novo(True)
    q = caixa(s, 0.6, 0.9, 8.0, 2.2, "Um ranking só vale o que valem os dados que o alimentam", 38, BRANCO, True,
              nome="!!titulo")
    pts = caixa(s, 0.6, 3.35, 7.6, 3.0, [
        ("O ideal depende do corpo: os critérios-alvo dão nota máxima ao meio-termo certo.", 18, BRANCO, False),
        ("", 8, BRANCO, False),
        ("Medir a confiança separa escolhas sólidas (haste) de empates (stent).", 18, BRANCO, False),
        ("", 8, BRANCO, False),
        ("Verificar as fontes mudou um vencedor (scaffold).", 18, BRANCO, False)], espaco=1.1)
    fim = caixa(s, 0.6, 6.4, 7.0, 0.6, "Obrigado.", 22, AZUL, True)
    figura_caixa(s, rend["dentario"], 8.7, 1.2, 4.2, 5.4)
    ap.notas(s, "Fecho com três ideias. Primeira: o ideal depende do corpo; os critérios-alvo dão a nota máxima ao "
                "meio-termo certo, como a rigidez do osso. Segunda: medir a confiança é tão importante como escolher; "
                "separa escolhas sólidas, como a haste, de empates, como o stent. Terceira, a mais importante: um "
                "ranking só vale o que valem os dados; verificar as fontes mudou o vencedor do scaffold. Obrigado.")
    plano.append((s, [q, pts, fim], [], "capa"))

    # Reserva
    s = novo(True)
    t = caixa(s, 0.6, 2.8, 12.1, 1.2, "Diapositivos de reserva", 40, BRANCO, True, nome="!!titulo")
    sub = caixa(s, 0.6, 3.9, 12.1, 0.8, "Porquê cada ferramenta, em linguagem simples", 20, SUB_NOITE)
    ap.notas(s, "Diapositivos de reserva, para as perguntas.")
    plano.append((s, [t, sub], [], "capa"))

    def reserva(nt, frase, kicker, blocos, nota, imagem=None):
        s = novo()
        f = titulo(s, frase, kicker, nt)
        extra = []
        if imagem:
            corpo = caixa(s, 0.6, 2.05, 6.3, 4.7, blocos, espaco=1.05)
            extra.append(figura_caixa(s, imagem, 7.2, 2.0, 5.55, 4.7))
        else:  # pares (cabeçalho, texto) em cartões, duas colunas
            pares = [blocos[i:i + 2] for i in range(0, len(blocos), 2)]
            linhas_ = (len(pares) + 1) // 2
            hc = min(2.6, (4.7 - 0.3 * (linhas_ - 1)) / linhas_)
            caixas_ = []
            for i, (cab, corpo_) in enumerate(pares):
                x, y = 0.6 + (i % 2) * 6.21, 2.05 + (i // 2) * (hc + 0.3)
                cartao(s, x, y, 5.92, hc)
                caixas_.append(caixa(s, x + 0.3, y + 0.25, 5.32, hc - 0.4,
                                     [(cab[0], 20, AZUL_TEXTO, True), (corpo_[0], 16, TEXTO, False)], espaco=1.08))
            corpo = caixas_[0]
            extra += caixas_[1:]
        ap.notas(s, nota)
        plano.append((s, f + [corpo] + extra, [], "conteudo"))

    lo316, hi316, u316 = intervalo("Aço inox 316L", "Módulo de Young")
    reserva(16, "Porquê Monte Carlo? Porque os dados têm intervalos", "Reserva: estatística", [
        ("A ideia", 17, AZUL_TEXTO, True),
        (f"Um valor como o módulo de uma liga vem num intervalo (por exemplo {ap.pt(lo316, 0)} a {ap.pt(hi316, 0)} "
         f"{u316} no aço 316L). Em vez de "
         "usar só o meio, sorteia-se um valor dentro do intervalo, decide-se, e repete-se.", 15, TEXTO, False),
        ("Exemplo", 17, AZUL_TEXTO, True),
        (f"Na haste, em {mil(n.n_iter)} repetições o Ti-6Al-4V ficou em 1.º em {mil(hc['TOPSIS'])} "
         "(TOPSIS). Isto não é uma probabilidade clínica: é a estabilidade da decisão face aos dados.", 15, TEXTO,
         False),
        ("Também testado", 17, AZUL_TEXTO, True),
        ("Distribuição triangular em vez de uniforme, pesos a variar, pesos objetivos e cenários.", 15, TEXTO,
         False)],
            "O Monte Carlo serve para uma pergunta simples: a escolha mantém-se quando os dados variam dentro do que "
            "as fontes dizem? Sorteia-se cada valor dentro do seu intervalo, decide-se de novo e conta-se. A "
            "frequência mede a estabilidade da decisão, não a probabilidade de sucesso clínico. O gráfico é o do "
            "stent: o Pt-Cr ganha na maioria das repetições com os três métodos, mas não em todas. Com distribuições "
            f"triangulares, os vencedores mantêm-se, exceto no stent com o WASPAS: o L605 passa a {tri_l605} % "
            f"contra {tri_ptcr} % do Pt-Cr.",
            grafico_mc_stent(mc_primeiro("Stent"), CACHE / "mc_stent.png"))
    reserva(17, "Porquê três métodos? Porque discordam de forma útil", "Reserva: os algoritmos", [
        ("TOPSIS", 17, AZUL_TEXTO, True),
        ("Calcula a distância de cada material ao ideal (o melhor em tudo) e ao pior; C perto de 1 é bom. Um ponto "
         "forte pode compensar um fraco.", 15, TEXTO, False),
        ("WASPAS", 17, AZUL_TEXTO, True),
        ("Média de uma soma e de um produto das notas: no produto, uma nota quase nula puxa tudo para baixo.", 15,
         TEXTO, False),
        ("VIKOR", 17, AZUL_TEXTO, True),
        ("Pesa o desempenho médio e o pior critério de cada material e procura o compromisso.", 15, TEXTO, False),
        ("Borda", 17, AZUL_TEXTO, True),
        ("Cada método dá pontos pela posição (1.º de 5 vale 4 pontos); somam-se os pontos dos três.", 15, TEXTO,
         False)],
            "Usei três métodos porque discordam de forma útil. O TOPSIS deixa compensar; o WASPAS castiga notas "
            "muito baixas; o VIKOR olha para o pior critério. Quando os três concordam, como na haste, a escolha é "
            "forte; quando discordam, como no stent, é sinal de empate. O Borda junta as três ordens.")
    reserva(18, "A rigidez certa pode vir do desenho, não só do material", "Reserva: Gibson e Ashby", [
        ("A relação", 17, AZUL_TEXTO, True),
        ("Num material poroso, o módulo cai com a porosidade: " + nb("E = Es (1 − p)²") + ", em que Es é o módulo "
         "da liga maciça.", 15, TEXTO, False),
        ("Na haste", 17, AZUL_TEXTO, True),
        (f"O Ti-6Al-4V maciço é cerca de {round(n.extra['rigidez'])} vezes mais rígido do que o alvo; com cerca de "
         f"{ap.pt(100 * n.extra['p_alvo'], 0)} % de porosidade chegaria aos {ap.pt(n.extra['alvo'], 0)} GPa.", 15,
         TEXTO, False),
        ("Limite", 17, AZUL_TEXTO, True),
        ("É uma aproximação de primeira ordem; a resistência à fadiga também cai com a porosidade.", 15, TEXTO,
         False)],
            "A relação de Gibson e Ashby diz que o módulo de um material poroso cai com o quadrado da fração sólida. "
            "Serve para mostrar que o stress shielding se pode atacar pelo desenho, com titânio poroso, e não só "
            "trocando de liga. É uma aproximação, e a fadiga também cai.",
            grafico_gibson(CACHE / "gibson_ashby.png"))
    reserva(19, "O modelo reproduz o artigo de referência", "Reserva: validação", [
        ("Reprodução", 17, AZUL_TEXTO, True),
        ("O caso da prótese da anca de Petković et al. (2025) foi reproduzido: os 15 coeficientes C publicados, com "
         "diferença máxima de cerca de 5 × 10⁻⁶; o WASPAS e o VIKOR dos casos 1 e 2 também batem (abaixo de 10⁻⁵).",
         15, TEXTO, False),
        ("Pormenor", 17, AZUL_TEXTO, True),
        ("Uma célula da tabela impressa do artigo difere do valor que reproduz os resultados publicados; ficou "
         "documentada no relatório.", 15, TEXTO, False)],
            "Antes de usar o código nos meus casos, reproduzi o caso publicado por Petković e colegas: os quinze "
            "coeficientes batem certo. Os pormenores da diferença numa célula estão no relatório.")
    reserva(20, "Os dados vêm de fontes abertas e verificadas", "Reserva: fontes e licenças", [
        ("Materials Project", 17, AZUL_TEXTO, True),
        ("Dados abertos (licença CC BY 4.0), propriedades calculadas por DFT; só para filtrar. Jain et al., APL "
         "Materials, 2013.", 15, TEXTO, False),
        ("Toxicidade dos elementos", 17, AZUL_TEXTO, True),
        ("ICH Q3D(R2), classes das impurezas elementares; monografias da IARC; elementos sem isótopos estáveis.", 15,
         TEXTO, False),
        ("Normas e base verificada", 17, AZUL_TEXTO, True),
        (f"{fu['normas']} normas ASTM de materiais para implantes; cada valor da base com mínimo, máximo, típico, "
         "fonte e estado.", 15, TEXTO, False)],
            "As fontes da triagem são abertas: o Materials Project sob licença CC BY 4.0, a guideline ICH Q3D e as "
            "monografias da IARC para a toxicidade, e as normas ASTM. Os valores que entram na decisão vêm só da base "
            "verificada.")

    massa_csv = ap.RESULTS / "massa_haste.csv"
    if massa_csv.exists():
        mh = pd.read_csv(massa_csv).set_index("material")["massa_g"]
        dm = mh.max() - mh.min()
        reserva(21, "A massa da haste não pesa; os iões contam", "Reserva: impacto no doente", [
            ("Massa da haste (a mesma forma)", 17, AZUL_TEXTO, True),
            (f"Cobalto-crómio {mh['Co-Cr-Mo forjado']:.0f} g, aço {mh['Aço inox 316L']:.0f} g, liga de titânio "
             f"{mh['Ti-6Al-4V ELI']:.0f} g: {dm:.0f} g de diferença.", 15, TEXTO, False),
            ("Centro de massa do corpo", 17, AZUL_TEXTO, True),
            # results/massa_haste.md e RELATORIO.md, secção 8.5 (Orendurff et al., 2004)
            ("Muda no máximo 0,6 mm: desprezável. A cada passo, o centro de massa sobe e desce 2,7 a 4,8 cm.", 15,
             TEXTO, False),
            ("Iões de cobalto e crómio", 17, AZUL_TEXTO, True),
            ("Raramente, com níveis muito altos no sangue: coração, tiroide, audição e visão. No Reino Unido, a "
             "partir de 7 µg/L há seguimento apertado.", 15, TEXTO, False),
            ("Níquel", 17, AZUL_TEXTO, True),
            ("Todas as ligas permanentes do stent têm níquel (9 a 35 %); a alergia ao níquel afeta 8 a 19 % dos "
             "adultos europeus.", 15, TEXTO, False)],
                f"Duas perguntas que costumam aparecer. A massa: a haste de cobalto-crómio pesa cerca de "
                f"{mh['Co-Cr-Mo forjado']:.0f} gramas e a de titânio cerca de {mh['Ti-6Al-4V ELI']:.0f}; trocar uma "
                "pela outra muda o centro de massa do corpo no máximo 0,6 milímetros, o que é desprezável. Os iões: o "
                "cobalto e o crómio só dão efeitos no corpo todo raramente, com níveis muito altos, sobretudo com "
                "desgaste de pares metal-metal; o níquel conta no stent, porque todas as ligas permanentes o têm, e é "
                "por isso que existe o perfil de doente com alergia ao níquel. Fontes: Bradberry 2014, MHRA 2017, "
                "Ahlström 2019, Orendurff 2004.")

    for k, (s, entradas, vids, esquema) in enumerate(plano):
        morph = k > 0 and plano[k - 1][3] == esquema == "caso"
        ap.aplicar_animacao(s, entradas, vids, morph)
    destino.parent.mkdir(parents=True, exist_ok=True)
    prs.save(destino)
    return destino


def exportar(pptx: Path = DESTINO) -> None:
    """No PowerPoint: guarda com as letras embutidas, exporta o PDF, o plano B e as imagens (1920 × 1080)."""
    import shutil

    import win32com.client
    app = win32com.client.DispatchEx("PowerPoint.Application")
    try:
        pres = app.Presentations.Open(str(pptx.resolve()), False, False, False)
        pres.SaveAs(str(pptx.resolve()), 24, True)  # 24 = ppSaveAsOpenXMLPresentation; True = embutir letras
        pres.SaveAs(str(pptx.with_suffix(".pdf").resolve()), 32)
        pasta = APRES / "imagens_b"
        pasta.mkdir(exist_ok=True)
        for i in range(1, pres.Slides.Count + 1):
            pres.Slides(i).Export(str(pasta / f"diapositivo_{i:02d}.png"), "PNG", 1920, 1080)
        pres.Close()
    finally:
        app.Quit()
    shutil.copyfile(pptx.with_suffix(".pdf"), APRES / "apresentacao_plano_B.pdf")


def main() -> None:
    a = argparse.ArgumentParser()
    a.add_argument("--exportar", action="store_true")
    a.add_argument("--renders", type=Path, default=None)
    args = a.parse_args()
    p = construir(renders=args.renders)
    print(p.relative_to(RAIZ))
    if args.exportar:
        exportar(p)


if __name__ == "__main__":
    main()
