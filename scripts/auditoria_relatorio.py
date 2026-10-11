"""Auditoria do relatório: confere o texto, as tabelas e as figuras contra os resultados e os dados.

Seis verificações, cada uma com achados de nível "erro", "aviso" ou "ok":
  1. números dos resumos (resumo, abstract, resumo executivo, discussão e conclusões) contra results/: contagens do
     Monte Carlo ("9 999 das 10 000"), combinações ("5 das 6"), percentagens, ΔC e vencedores citados;
  2. percentagens do Monte Carlo (results/monte_carlo.csv) a somar 100 % por caso, análise e método;
  3. todas as alternativas de cada caso e cenário (data/, via biomat_mcdm.io) em results/pontuacoes.csv e nas
     tabelas relatorio/tabelas/<caso>_resultados.md;
  4. posições coerentes com as pontuações e a direção de cada método (C e Q decrescentes, P crescente; Borda);
  5. figuras do relatório (marcadores <!-- figura: ... -->) geradas com os dados atuais: as de scripts/figuras.py
     são refeitas em memória e comparadas com o SVG gravado; as outras pela data de modificação;
  6. semente, número de iterações e versões do software declarados em relatorio/RELATORIO.md, com uma frase
     proposta (versões lidas do ambiente e do repositório) para o que faltar.
Grava results/auditoria_relatorio.md e sai com código 1 se houver erros.
Uso: python scripts/auditoria_relatorio.py
"""
from __future__ import annotations

import importlib.metadata
import importlib.util
import io
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "src"))
from run_all import CASOS  # noqa: E402

from biomat_mcdm.io import DATA, build_problem  # noqa: E402

REL = RAIZ / "relatorio"
RESULTS = RAIZ / "results"
FIGURAS = RESULTS / "figures"
SAIDA = RESULTS / "auditoria_relatorio.md"
RESUMOS = ("resumo_rascunho.md", "abstract_rascunho.md", "00_resumo_executivo.md", "discussao_rascunho.md",
           "conclusao_rascunho.md")
INGLES = {"abstract_rascunho.md"}
METODOS = ("TOPSIS", "WASPAS", "VIKOR")
TABELAS = {"Haste": "haste", "Stent": "stent", "Scaffold": "scaffold"}
TOLERANCIA_PCT = 0.1
NOMES_VERIFICACAO = {1: "Números dos resumos", 2: "Somas do Monte Carlo", 3: "Alternativas e cenários",
                     4: "Rankings coerentes", 5: "Figuras atualizadas", 6: "Semente e versões"}

# Nomes alternativos usados no texto (português e inglês) para os materiais dos dados.
ALIASES = {
    "Pt-Cr": ["platina-crómio", "platinum-chromium"],
    "Co-Cr L605": ["L605", "cobalto-crómio L605", "cobalt-chromium L605"],
    "Co-Ni-Cr-Mo MP35N": ["MP35N"],
    "Aço inox 316L": ["316L"],
    "Co-Cr-Mo forjado": ["Co-Cr-Mo"],
    "Ti-35Nb-7Zr-5Ta (TNZT)": ["TNZT", "Ti-35Nb-7Zr-5Ta"],
    "β-TCP poroso": ["porous β-TCP", "β-TCP"],
    "Compósito PCL/β-TCP (impressão 3D)": ["compósito PCL/β-TCP", "PCL/β-TCP composite", "compósito",
                                           "composite"],
    "Hidroxiapatite (HA) porosa": ["HA porosa", "porous HA"],
    "Vidro bioativo 45S5 poroso": ["45S5"],
    "Liga de Mg WE43 (bioabsorvível)": ["WE43"],
    "Ti cp grau 4": ["titânio comercialmente puro de grau 4", "commercially pure grade 4 titanium"],
    "ZTA / ZTA (CoC)": ["ZTA/ZTA", "cerâmica-cerâmica", "ceramic-on-ceramic"],
    "Ti-Zr (~15% Zr)": ["Ti-Zr"],
    "Zircónia Y-TZP": ["Y-TZP"],
}
PALAVRAS_CASO = {"Haste": ("haste", "femoral stem"), "Stent": ("stent",), "Scaffold": ("scaffold",),
                 "Par articular": ("par articular", "bearing couple"),
                 "Implante dentário": ("implante dentário", "dental implant")}

SEP = r"[ \u00a0\u202f,]"
INTEIRO = rf"\d{{1,3}}(?:{SEP}\d{{3}})+|\d+"
CONTAGEM_MC = re.compile(rf"(pelo menos |at least )?({INTEIRO}) (?:d[ao]s|de|of the|of) ({INTEIRO}) "
                         r"(?:Monte Carlo )?(?:repetições|iterações|repetitions|iterations)")
COMBINACOES = re.compile(r"(\d+) (?:das|of the) (\d+) (?:combinações|method and scenario combinations)")
CONTAGEM = re.compile(rf"(?<![\d,])({INTEIRO}) (?:d[ao]s|de|of the|of) ({INTEIRO})(?![\d,]| ?%)")
INTERVALO_PCT = re.compile(r"(\d+(?:[.,]\d+)?) (?:a|to) (\d+(?:[.,]\d+)?) ?%")
DELTA = re.compile(r"ΔC = (\d+[.,]\d+)(?: \(([AB])\b| em ([AB])| in ([AB]))?")
CONTEXTO_MC = re.compile(r"Monte Carlo|incerteza|uncertainty|1\.º|first|vezes|often|pesos ±|weights|triangular",
                         re.IGNORECASE)
TRES_DOIS = re.compile(r"(?:ficou|fica) em 1\.º lugar com os três métodos, nos dois cenários|"
                       r"ranked first with all three methods, in both scenarios")
MAIS_VEZES = re.compile(r"(?:ficou|fica) mais vezes em 1\.º|ranked first more often")
MELHOR = re.compile(r"obteve a melhor pontuação|obtained the best score")
PERCENT = re.compile(r"(±)?(\d+(?:[.,]\d+)?) ?%")
FIGURA = re.compile(r"<!-- figura: ([\w/]+) -->")


@dataclass
class Achado:
    verificacao: int  # 1 a 6
    nivel: str  # "erro", "aviso", "nota" (fora do alcance desta auditoria) ou "ok"
    onde: str
    mensagem: str


# ---------------------------------------------------------------- utilitários de texto

def mil(n: int) -> str:
    """Número inteiro com espaço a separar os milhares (10000 dá "10 000")."""
    return f"{n:,}".replace(",", " ")


def ler_numero(txt: str, ingles: bool = False) -> float:
    """Converte um número escrito no texto ("9 999", "66,9"; em inglês "9,999", "66.9") num float.

    Em linguagem simples: tira os separadores de milhares e troca a vírgula decimal por ponto.
    """
    t = re.sub(r"[ \u00a0\u202f]", "", txt)
    t = t.replace(",", "") if ingles else t.replace(".", "").replace(",", ".")
    return float(t)


def casas_decimais(txt: str) -> int:
    """Número de casas decimais de um número escrito ("66,9" dá 1; "100" dá 0)."""
    m = re.search(r"[.,](\d+)$", txt)
    return len(m.group(1)) if m else 0


def caso_no_texto(texto: str) -> str | None:
    """Caso (Haste, Stent, ...) mencionado mais perto do fim do texto, ou None.

    Em linguagem simples: lê o que vem antes de um número e vê qual foi o último dispositivo nomeado.
    """
    melhor, pos = None, -1
    baixo = texto.casefold()
    for caso, palavras in PALAVRAS_CASO.items():
        for p in palavras:
            i = baixo.rfind(p)
            if i > pos:
                melhor, pos = caso, i
    return melhor


def materiais_no_texto(texto: str, materiais: list[str]) -> list[tuple[int, str]]:
    """(posição, material) de cada material dos dados citado no texto, pela ordem em que aparece.

    Em linguagem simples: procura o nome de cada material (e os nomes alternativos de ALIASES), do mais
    comprido para o mais curto, sem contar duas vezes o mesmo pedaço de texto (o "β-TCP" dentro de
    "PCL/β-TCP" não conta como β-TCP poroso).
    """
    nomes = []
    for m in materiais:
        for a in [m, re.sub(r"\s*\(.*?\)", "", m)] + ALIASES.get(m, []):
            if a:
                nomes.append((a, m))
    nomes.sort(key=lambda x: -len(x[0]))
    ocupado: list[tuple[int, int]] = []
    out = []
    for alias, mat in nomes:
        for mm in re.finditer(rf"(?<![\w/]){re.escape(alias)}(?![\w])", texto, flags=re.IGNORECASE):
            if any(a < mm.end() and mm.start() < b for a, b in ocupado):
                continue
            ocupado.append((mm.start(), mm.end()))
            out.append((mm.start(), mat))
    return sorted(out)


def material_antes(texto: str, materiais: list[str]) -> str | None:
    """O material citado mais perto do fim do texto (o sujeito de "ficou em 1.º"), ou None."""
    achados = materiais_no_texto(texto, materiais)
    return achados[-1][1] if achados else None


def oracao_seguinte(linha: str, inicio: int) -> str:
    """O resto da oração a partir de uma posição: até à próxima vírgula, ";" ou ponto final (o "1.º" não conta)."""
    resto = linha[inicio:]
    m = re.search(r"[,;]|\.(?!º)(?:\s|$)", resto)
    return resto[:m.start()] if m else resto


# ---------------------------------------------------------------- verificação 1

def contagens_mc(mc: pd.DataFrame, caso: str, material: str) -> dict[tuple[str, str], int]:
    """{(análise, método): iterações em que o material ficou em 1.º} para um caso do Monte Carlo."""
    sub = mc[(mc["caso"] == caso) & (mc["material"] == material)]
    return {(r.analise, r.metodo): int(round(r.pct_primeiro * r.n_iter / 100)) for r in sub.itertuples()}


def lider_mc(mc: pd.DataFrame, caso: str, analise: str, metodo: str) -> str:
    """Material que fica mais vezes em 1.º num caso, análise e método do Monte Carlo."""
    sub = mc[(mc["caso"] == caso) & (mc["analise"] == analise) & (mc["metodo"] == metodo)]
    return sub.sort_values("pct_primeiro", ascending=False)["material"].iloc[0]


def frase_em(linha: str, pos: int) -> str:
    """A frase (entre pontos finais ou ";") que contém a posição dada; o "1.º" e os decimais não cortam a frase."""
    cortes = [0] + [m.end() for m in re.finditer(r";|\.(?![º\d])(?:\s|$)", linha)] + [len(linha)]
    ini = max(c for c in cortes if c <= pos)
    fim = min((c for c in cortes if c > pos), default=len(linha))
    return linha[ini:fim]


def percentagens_resultados(mc: pd.DataFrame, triangular: pd.DataFrame | None = None) -> pd.DataFrame:
    """Todas as percentagens de 1.º lugar dos resultados (Monte Carlo e, se houver, a variante triangular).

    Colunas: caso, analise, metodo, material, pct_primeiro. Na variante de results/mc_triangular.csv a análise
    chama-se "MC <distribuição>".
    """
    partes = [mc[["caso", "analise", "metodo", "material", "pct_primeiro"]]]
    if triangular is not None and not triangular.empty:
        t = triangular.assign(analise="MC " + triangular["distribuicao"].astype(str))
        partes.append(t[["caso", "analise", "metodo", "material", "pct_primeiro"]])
    return pd.concat(partes, ignore_index=True)


def numeros_do_resumo(texto: str, ficheiro: str, pts: pd.DataFrame, mc: pd.DataFrame,
                      semi: pd.DataFrame, pcts: pd.DataFrame | None = None) -> list[Achado]:
    """Confere os números e os vencedores citados num texto de resumo contra os resultados.

    Em linguagem simples: lê cada linha, encontra as frases-tipo ("pelo menos 9 999 das 10 000 repetições",
    "em 5 das 6 combinações", "ficou mais vezes em 1.º", "56 a 70 %", percentagens, ΔC) e vê se os números e
    os materiais batem com pontuacoes.csv, monte_carlo.csv (e mc_triangular.csv) e semiquantitativos.csv.
    O que é sobre o Monte Carlo mas não consegue ligar a um resultado fica como aviso; as percentagens e
    contagens que não falam do Monte Carlo (registos, porosidades, regras) ficam como nota.
    """
    from verificar_delta_c import delta_resultados
    pcts = percentagens_resultados(mc) if pcts is None else pcts
    ingles = ficheiro in INGLES
    todos = sorted(set(pts["material"]) | set(semi["material"]))
    n_iter = int(mc["n_iter"].iloc[0])
    out: list[Achado] = []

    def achado(nivel: str, n: int, msg: str) -> None:
        out.append(Achado(1, nivel, f"{ficheiro}:{n}", msg))

    def sujeito(antes: str) -> tuple[str | None, str | None]:
        return caso_no_texto(antes), material_antes(antes, todos)

    for n, linha in enumerate(texto.splitlines(), 1):
        usados: list[tuple[int, int]] = []

        def livre(m: re.Match) -> bool:
            return not any(a < m.end() and m.start() < b for a, b in usados)

        for m in CONTAGEM_MC.finditer(linha):
            usados.append(m.span())
            k, tot = ler_numero(m.group(2), ingles), ler_numero(m.group(3), ingles)
            caso, mat = sujeito(linha[:m.start()])
            txt = m.group(0)
            if tot != n_iter:
                achado("erro", n, f'"{txt}": o Monte Carlo tem {mil(n_iter)} iterações, não {tot:.0f}')
                continue
            cont = contagens_mc(mc, caso, mat) if caso and mat else {}
            if not cont:
                achado("aviso", n, f'"{txt}": não confirmado (caso ou material não identificado)')
                continue
            minimo = min(cont.values())
            ok = minimo >= k if m.group(1) else k in cont.values()
            achado("ok" if ok else "erro", n, f'"{txt}" ({mat}, {caso}): mínimo nos resultados = {mil(minimo)} '
                   "(três métodos, propriedades e pesos)")
        for m in COMBINACOES.finditer(linha):
            usados.append(m.span())
            k, tot = int(m.group(1)), int(m.group(2))
            caso, mat = sujeito(linha[:m.start()])
            sub = pts[(pts["caso"] == caso) & (pts["material"] == mat)] if caso and mat else pts.iloc[:0]
            if sub.empty:
                achado("aviso", n, f'"{m.group(0)}": não confirmado (caso ou material não identificado)')
                continue
            primeiros = int(sum((sub[f"pos_{x}"] == 1).sum() for x in METODOS))
            total = len(METODOS) * pts.loc[pts["caso"] == caso, "cenario"].nunique()
            ok = (k, tot) == (primeiros, total)
            achado("ok" if ok else "erro", n, f'"{m.group(0)}" ({mat}, {caso}): nos resultados, 1.º em '
                   f"{primeiros} de {total}")
        for m in INTERVALO_PCT.finditer(linha):
            usados.append(m.span())
            frase = frase_em(linha, m.start())
            caso, mat = sujeito(linha[:m.start()])
            if not CONTEXTO_MC.search(frase):
                achado("nota", n, f'"{m.group(0)}": não é resultado do Monte Carlo; não verificado')
                continue
            analise = "W pesos ±20 %" if re.search(r"pesos|weights", frase) else "MC propriedades"
            sub = mc[(mc["caso"] == caso) & (mc["material"] == mat) & (mc["analise"] == analise)]
            if sub.empty:
                achado("aviso", n, f'"{m.group(0)}": não confirmado (caso ou material não identificado)')
                continue
            a, b = (ler_numero(g, ingles) for g in m.groups())
            d = max(casas_decimais(g) for g in m.groups())
            lo, hi = round(sub["pct_primeiro"].min(), d), round(sub["pct_primeiro"].max(), d)
            ok = abs(lo - a) < 1e-9 and abs(hi - b) < 1e-9
            achado("ok" if ok else "erro", n, f'"{m.group(0)}" ({mat}, {caso}, {analise}): nos resultados, '
                   f"{sub['pct_primeiro'].min():.2f} a {sub['pct_primeiro'].max():.2f} %")
        for m in CONTAGEM.finditer(linha):
            if livre(m):
                usados.append(m.span())
                nivel = "aviso" if CONTEXTO_MC.search(frase_em(linha, m.start())) else "nota"
                achado(nivel, n, f'contagem "{m.group(0)}": não confirmada automaticamente')
        for m in TRES_DOIS.finditer(linha):
            caso, mat = sujeito(linha[:m.start()])
            sub = pts[(pts["caso"] == caso) & (pts["material"] == mat)] if caso and mat else pts.iloc[:0]
            if sub.empty:
                achado("aviso", n, f'"{m.group(0)}": não confirmado (caso ou material não identificado)')
                continue
            falhas = [f"{x} {r.cenario}" for r in sub.itertuples() for x in METODOS if getattr(r, f"pos_{x}") != 1]
            achado("erro" if falhas else "ok", n, f"{mat} 1.º com os três métodos nos dois cenários ({caso})"
                   + (f": não é 1.º em {', '.join(falhas)}" if falhas else ""))
        for m in MAIS_VEZES.finditer(linha):
            depois = oracao_seguinte(linha, m.end())
            caso, mat = sujeito(linha[:m.start()])
            if not caso or mat is None or caso not in set(mc["caso"]):
                achado("aviso", n, f'"{m.group(0)}": não confirmado (caso ou material não identificado)')
                continue
            analise = "W pesos ±20 %" if re.search(r"pesos|weights", depois) else "MC propriedades"
            pedidos = [x for x in METODOS if x in depois] or list(METODOS)
            lidera = [x for x in pedidos if lider_mc(mc, caso, analise, x) == mat]
            explicito = bool(re.search(r"três métodos|three methods|TOPSIS|WASPAS|VIKOR", depois))
            if len(lidera) == len(pedidos):
                nivel = "ok"
            elif lidera and not explicito:
                nivel = "aviso"
            else:
                nivel = "erro"
            achado(nivel, n, f"{mat} mais vezes em 1.º ({caso}, {analise}): lidera em "
                   f"{', '.join(lidera) or 'nenhum método'} de {', '.join(pedidos)}")
        for m in MELHOR.finditer(linha):
            depois = oracao_seguinte(linha, m.end())
            caso, mat = sujeito(linha[:m.start()])
            sub = semi[semi["caso"] == caso] if caso else semi.iloc[:0]
            if sub.empty or mat is None:
                achado("aviso", n, f'"{m.group(0)}": não confirmado (caso ou material não identificado)')
                continue
            if not re.search(r"todas as versões|every version", depois):
                sub = sub[sub["cenario"] == "A"]
            linhas_mat = sub[sub["material"] == mat]
            ok = not linhas_mat.empty and (linhas_mat["posicao"] == 1).all()
            achado("ok" if ok else "erro", n, f"{mat} com a melhor pontuação ({caso}): 1.º em "
                   f"{int((linhas_mat['posicao'] == 1).sum())} de {len(linhas_mat)} combinações")
        for m in PERCENT.finditer(linha):
            if not livre(m):
                continue
            txt = m.group(0)
            if m.group(1):
                ok = any(txt.replace(" ", "") in a.replace(" ", "") for a in mc["analise"].unique())
                achado("ok" if ok else "nota", n, f'"{txt}": {"análise do Monte Carlo" if ok else "não verificado"}')
                continue
            v, d = ler_numero(m.group(2), ingles), casas_decimais(m.group(2))
            frase = frase_em(linha, m.start())
            caso = caso_no_texto(linha[:m.start()])
            sub = pcts[pcts["caso"] == caso] if caso in set(pcts["caso"]) else pcts.iloc[:0] if caso else pcts
            hit = sub[(sub["pct_primeiro"].round(d) - v).abs() < 1e-9]
            if not CONTEXTO_MC.search(frase) or (caso and sub.empty):
                achado("nota", n, f'"{txt}": não é resultado do Monte Carlo; não verificado')
            elif not hit.empty:
                r = hit.iloc[0]
                achado("ok", n, f'"{txt}": {r.material}, {r.analise}, {r.metodo} ({r.pct_primeiro:.2f} %)')
            else:
                achado("aviso", n, f'"{txt}": não confirmado (não é uma percentagem de 1.º lugar do Monte Carlo'
                       f"{' (' + caso + ')' if caso else ''})")
        for m in DELTA.finditer(linha):
            pares = [(m.group(1), m.group(2) or m.group(3) or m.group(4))]
            m2 = re.match(r" e (\d+[.,]\d+)(?: \(([AB])\b| em ([AB]))", linha[m.end():])
            if m2:
                pares.append((m2.group(1), m2.group(2) or m2.group(3)))
            caso = caso_no_texto(linha[:m.start()]) or caso_no_texto(ficheiro.replace("_", " "))
            for txt, cen in pares:
                if cen is None:
                    antes = re.findall(r"(?:cenário|scenario) ([AB])", linha[:m.start()])
                    cen = antes[-1] if antes else None
                if caso not in set(pts["caso"]) or cen is None:
                    achado("aviso", n, f"ΔC = {txt}: não confirmado (caso ou cenário não identificado)")
                    continue
                d = delta_resultados(pts, caso, cen)
                ok = round(d, 3) == round(ler_numero(txt, ingles), 3)
                achado("ok" if ok else "erro", n, f"ΔC = {txt} ({caso}, {cen}): resultados {d:.4f}")
    return out


# ---------------------------------------------------------------- verificação 2

def somas_monte_carlo(mc: pd.DataFrame, tolerancia: float = TOLERANCIA_PCT) -> list[Achado]:
    """Confere que as percentagens de 1.º, 2.º e 3.º lugar somam 100 % em cada caso, análise e método.

    Em linguagem simples: em cada iteração há exatamente um 1.º, um 2.º e um 3.º lugar, por isso a soma das
    percentagens de todos os materiais tem de dar 100 % (com uma pequena folga para os arredondamentos).
    """
    out = []
    for (caso, analise, metodo), g in mc.groupby(["caso", "analise", "metodo"], sort=False):
        for col in ("pct_primeiro", "pct_segundo", "pct_terceiro"):
            s = float(g[col].sum())
            ok = abs(s - 100) <= tolerancia
            out.append(Achado(2, "ok" if ok else "erro", f"{caso}, {analise}, {metodo}",
                              f"soma de {col} = {s:.3f} %"))
    return out


# ---------------------------------------------------------------- verificações 3 e 4

def materiais_esperados(data_dir: Path = DATA) -> dict[tuple[str, str], list[str]]:
    """{(caso, cenário): materiais} lidos dos dados (data/) com biomat_mcdm.io.build_problem."""
    return {(caso, cen): list(build_problem(nome, cen, data_dir).alternatives)
            for caso, nome in CASOS.items() for cen in ("A", "B")}


def ler_tabela_resultados(texto: str) -> pd.DataFrame:
    """Lê uma tabela relatorio/tabelas/<caso>_resultados.md para as colunas de results/pontuacoes.csv.

    Em linguagem simples: cada linha "| A | Pt-Cr | 0,653 | 1 | 0,848 | 2 | 0,000 | 1 | 1 (8 pts) |" passa a
    cenário, material, C, posição no TOPSIS, Q, posição no WASPAS, P, posição no VIKOR, posição e pontos de Borda.
    """
    linhas = []
    for linha in texto.splitlines():
        c = [x.strip() for x in linha.strip().strip("|").split("|")]
        if len(c) != 9 or not re.fullmatch(r"[AB]", c[0]):
            continue
        b = re.fullmatch(r"(\d+) \((\d+) pts?\)", c[8])
        linhas.append({"cenario": c[0], "material": c[1], "C_TOPSIS": ler_numero(c[2]), "pos_TOPSIS": int(c[3]),
                       "Q_WASPAS": ler_numero(c[4]), "pos_WASPAS": int(c[5]), "P_VIKOR": ler_numero(c[6]),
                       "pos_VIKOR": int(c[7]), "pos_Borda": int(b.group(1)) if b else None,
                       "pontos_Borda": int(b.group(2)) if b else None})
    return pd.DataFrame(linhas)


def ler_tabelas(rel: Path = REL) -> dict[str, pd.DataFrame]:
    """{caso: tabela de resultados do relatório} para os casos quantitativos (as que existirem)."""
    out = {}
    for caso, nome in TABELAS.items():
        f = rel / "tabelas" / f"{nome}_resultados.md"
        if f.exists():
            out[caso] = ler_tabela_resultados(f.read_text(encoding="utf-8")).assign(caso=caso)
    return out


def presenca(esperados: dict[tuple[str, str], list[str]], pts: pd.DataFrame,
             tabelas: dict[str, pd.DataFrame]) -> list[Achado]:
    """Confere que cada material de cada caso e cenário está nos resultados e na tabela do relatório (e nada a mais).

    Em linguagem simples: compara a lista de materiais que os dados dizem que entram com a que aparece em
    pontuacoes.csv e na tabela de resultados; reporta os que faltam e os que sobram.
    """
    out = []
    for (caso, cen), mats in esperados.items():
        fontes = {"results/pontuacoes.csv": pts}
        fontes[f"tabelas/{TABELAS[caso]}_resultados.md"] = tabelas.get(caso)
        for nome, df in fontes.items():
            onde = f"{nome}, {caso} {cen}"
            if df is None:
                out.append(Achado(3, "erro", onde, "tabela não encontrada"))
                continue
            tem = set(df.loc[(df["caso"] == caso) & (df["cenario"] == cen), "material"])
            falta, sobra = sorted(set(mats) - tem), sorted(tem - set(mats))
            if falta or sobra:
                out.append(Achado(3, "erro", onde, f"faltam {falta}; sobram {sobra}"))
            else:
                out.append(Achado(3, "ok", onde, f"{len(mats)} materiais, todos presentes"))
    return out


def coerencia_rankings(df: pd.DataFrame, origem: str) -> list[Achado]:
    """Confere as posições contra as pontuações em cada caso e cenário de uma tabela de resultados.

    Em linguagem simples: ordenando pela posição, o C do TOPSIS e o Q do WASPAS têm de descer e o P do VIKOR
    de subir (empates permitidos, porque a tabela do relatório está arredondada); as posições têm de ser
    1, 2, ..., m; os pontos de Borda são a soma de (m - posição) nos três métodos e a posição de Borda
    ordena esses pontos (empate desfeito pela posição no TOPSIS).
    """
    out = []
    direcao = {"TOPSIS": ("C_TOPSIS", False), "WASPAS": ("Q_WASPAS", False), "VIKOR": ("P_VIKOR", True)}
    for (caso, cen), g in df.groupby(["caso", "cenario"], sort=False):
        onde, m, erros = f"{origem}, {caso} {cen}", len(g), []
        for metodo, (col, crescente) in direcao.items():
            pos = f"pos_{metodo}"
            if sorted(g[pos]) != list(range(1, m + 1)):
                erros.append(f"{pos} não é 1..{m}")
                continue
            v = g.sort_values(pos)[col].to_numpy()
            dif = v[1:] - v[:-1]
            if (dif < -1e-12).any() if crescente else (dif > 1e-12).any():
                erros.append(f"{pos} não segue {col} {'crescente' if crescente else 'decrescente'}")
        if g["pontos_Borda"].notna().all():
            pontos = sum(m - g[f"pos_{x}"] for x in METODOS)
            if (pontos != g["pontos_Borda"]).any():
                erros.append("pontos de Borda diferentes da soma de (m - posição)")
            ordem = g.sort_values(["pontos_Borda", "pos_TOPSIS"], ascending=[False, True])
            if list(ordem["pos_Borda"]) != list(range(1, m + 1)):
                erros.append("pos_Borda não ordena os pontos de Borda")
        out.append(Achado(4, "erro" if erros else "ok", onde, "; ".join(erros) or f"{m} materiais coerentes"))
    return out


def tabela_igual_resultados(tab: pd.DataFrame, pts: pd.DataFrame, casas: int = 3) -> list[Achado]:
    """Confere que a tabela do relatório tem as mesmas pontuações (a 3 casas) e posições que pontuacoes.csv."""
    out = []
    cols_v = ["C_TOPSIS", "Q_WASPAS", "P_VIKOR"]
    cols_p = ["pos_TOPSIS", "pos_WASPAS", "pos_VIKOR", "pos_Borda", "pontos_Borda"]
    j = tab.merge(pts, on=["caso", "cenario", "material"], suffixes=("_tab", "_res"))
    for r in j.itertuples(index=False):
        d = r._asdict()
        dif = [c for c in cols_v if abs(round(d[f"{c}_res"], casas) - d[f"{c}_tab"]) > 10 ** -casas / 2 + 1e-12]
        dif += [c for c in cols_p if d[f"{c}_tab"] is not None and int(d[f"{c}_tab"]) != int(d[f"{c}_res"])]
        if dif:
            out.append(Achado(4, "erro", f"tabela {r.caso} {r.cenario}, {r.material}",
                              f"diferente de pontuacoes.csv em {', '.join(dif)}"))
    if not out:
        out.append(Achado(4, "ok", f"tabela {tab['caso'].iloc[0] if len(tab) else '?'}",
                          f"{len(j)} linhas iguais a pontuacoes.csv"))
    return out


# ---------------------------------------------------------------- verificação 5

def marcadores_figuras(rel: Path = REL) -> dict[str, list[str]]:
    """{figura: rascunhos onde aparece} a partir dos marcadores <!-- figura: ... --> de relatorio/*.md."""
    out: dict[str, list[str]] = {}
    for f in sorted(rel.glob("*.md")):
        if f.name.startswith("RELATORIO"):
            continue
        for nome in FIGURA.findall(f.read_text(encoding="utf-8")):
            out.setdefault(nome, [])
            if f.name not in out[nome]:
                out[nome].append(f.name)
    return out


def caminho_figura(nome: str, caminhos: dict[str, str] | None = None) -> Path:
    """Ficheiro PNG de uma figura, como o montar_relatorio.py o resolve (CAMINHOS ou results/figures/<nome>.png)."""
    if caminhos and nome in caminhos:
        return (REL / caminhos[nome]).resolve()
    return FIGURAS / f"{nome}.png"


def svg_igual(fig, caminho_svg: Path) -> bool:
    """Diz se a figura, gravada agora em SVG, é igual ao SVG gravado (ignorando as mudanças de linha CRLF/LF).

    Em linguagem simples: o scripts/figuras.py grava SVG sem data e com identificadores fixos, por isso a
    mesma figura feita com os mesmos dados dá sempre o mesmo ficheiro; se for diferente, os dados mudaram
    depois de a figura ter sido gerada.
    """
    import matplotlib.pyplot as plt
    b = io.BytesIO()
    fig.savefig(b, format="svg", dpi=300, metadata={"Date": None})
    plt.close(fig)
    if not caminho_svg.exists():
        return False
    return b.getvalue().replace(b"\r\n", b"\n") == caminho_svg.read_bytes().replace(b"\r\n", b"\n")


def figuras_atualizadas(marcadores: dict[str, list[str]], geradas: dict[str, object],
                        fontes: list[Path], caminhos: dict[str, str] | None = None) -> list[Achado]:
    """Confere se cada figura do relatório corresponde aos dados atuais.

    Em linguagem simples: as figuras do scripts/figuras.py (em `geradas`, já refeitas com os dados atuais)
    comparam-se pelo conteúdo do SVG; as outras (funil, FEA, CFD), que vêm de outros scripts, comparam-se
    pela data: se o ficheiro for mais antigo do que algum dos `fontes`, fica um aviso.
    """
    out = []
    for nome, onde in marcadores.items():
        loc = ", ".join(onde)
        png = caminho_figura(nome, caminhos)
        if nome in geradas:
            ok = svg_igual(geradas[nome], png.with_suffix(".svg"))
            out.append(Achado(5, "ok" if ok else "erro", f"{nome} ({loc})",
                              "igual à figura refeita com os dados atuais" if ok else
                              "diferente da figura refeita com os dados atuais: correr scripts/figuras.py"))
            continue
        if not png.exists():
            out.append(Achado(5, "erro", f"{nome} ({loc})", f"ficheiro em falta: {png}"))
            continue
        novas = [f.name for f in fontes if f.exists() and f.stat().st_mtime > png.stat().st_mtime]
        out.append(Achado(5, "aviso" if novas else "ok", f"{nome} ({loc})",
                          f"mais antiga do que {', '.join(novas)} (gerada por outro script; confirmar se depende "
                          "destes dados)" if novas else "posterior aos dados e às pontuações"))
    return out


def figuras_refeitas() -> dict[str, object]:
    """As figuras do scripts/figuras.py refeitas em memória com os resultados atuais (nada é gravado)."""
    spec = importlib.util.spec_from_file_location("figuras", RAIZ / "scripts" / "figuras.py")
    fg = importlib.util.module_from_spec(spec)
    sys.modules["figuras"] = fg
    spec.loader.exec_module(fg)
    rk = pd.read_csv(RESULTS / "rankings_cenarios.csv")
    pts = pd.read_csv(RESULTS / "pontuacoes.csv")
    mc = pd.read_csv(RESULTS / "monte_carlo.csv")
    return fg.todas(rk, pts, mc)


# ---------------------------------------------------------------- verificação 6

BIBLIOTECAS = {"numpy": "NumPy", "pandas": "pandas", "scipy": "SciPy", "matplotlib": "Matplotlib",
               "gmsh": "gmsh", "scikit-fem": "scikit-fem", "pyamg": "pyamg"}
OBRIGATORIAS = ("numpy", "pandas", "scipy")  # as outras só se o relatório as citar


def versoes_ambiente() -> dict[str, str | None]:
    """{"python": "3.12.10", "numpy": "...", ...} lidos do Python em uso (None se a biblioteca não estiver)."""
    out: dict[str, str | None] = {"python": ".".join(map(str, sys.version_info[:3]))}
    for pacote in BIBLIOTECAS:
        try:
            out[pacote] = importlib.metadata.version(pacote)
        except importlib.metadata.PackageNotFoundError:
            out[pacote] = None
    return out


def versoes_ferramentas(raiz: Path = RAIZ, pasta_ansys: Path = Path("<pasta local> Inc")) -> dict[str, str]:
    """Versões das ferramentas externas, lidas do repositório (e do Ansys, da pasta de instalação).

    Em linguagem simples: OpenFOAM em results/cfd_stent.md, SOLIDWORKS em docs/FEA_HASTE_SW.md, MATLAB em
    results/validacao_matlab.md; o Ansys pela pasta vNNN (v261 = 2026 R1). Só entra o que for encontrado.
    """
    out = {}
    regras = {"OpenFOAM": ("results/cfd_stent.md", r"OpenFOAM (v\d{4})"),
              "SOLIDWORKS": ("docs/FEA_HASTE_SW.md", r"SOLIDWORKS (\d{4}(?: SP\d+)?)"),
              "MATLAB": ("results/validacao_matlab.md", r"\((R\d{4}[ab])\)")}
    for nome, (ficheiro, padrao) in regras.items():
        f = raiz / ficheiro
        m = re.search(padrao, f.read_text(encoding="utf-8"), re.IGNORECASE) if f.exists() else None
        if m:
            out[nome] = m.group(1)
    versoes = sorted(p.name for p in pasta_ansys.glob("*/v[0-9][0-9][0-9]")) if pasta_ansys.exists() else []
    if versoes:
        v = versoes[-1]
        edicao = " Student" if any("Student" in p.parent.name for p in pasta_ansys.glob(f"*/{v}")) else ""
        out["Ansys"] = f"20{v[1:3]} R{v[3]} ({v}{edicao})"
    return out


def declaracoes(texto: str, semente: int, n_iter: int, versoes: dict[str, str | None],
                ferramentas: dict[str, str]) -> list[Achado]:
    """Procura no relatório a semente, as iterações e as versões do software; reporta o que falta.

    Em linguagem simples: para repetir o trabalho é preciso saber a semente do gerador aleatório, quantas
    iterações correu o Monte Carlo e com que versões. As bibliotecas obrigatórias são NumPy, pandas e SciPy;
    as outras e as ferramentas (OpenFOAM, Ansys, SOLIDWORKS, MATLAB) só se o relatório as citar.
    """
    out = []

    def conferir(onde: str, padrao: str, citado: bool = True) -> None:
        if not citado:
            return
        ok = re.search(padrao, texto, re.IGNORECASE) is not None
        out.append(Achado(6, "ok" if ok else "erro", onde, "declarado" if ok else "em falta no relatório"))

    conferir(f"semente ({semente})", rf"semente[^.\n]{{0,40}}\b{semente}\b|\b{semente}\b[^.\n]{{0,20}}semente")
    iteracoes = mil(n_iter).replace(" ", "[ \u00a0\u202f]")
    conferir(f"iterações ({mil(n_iter)})", rf"{iteracoes} (iterações|repetições)")
    conferir("versão do Python", r"Python \d+\.\d+")
    for pacote, nome in BIBLIOTECAS.items():
        citado = pacote in OBRIGATORIAS or re.search(rf"\b{re.escape(nome)}\b", texto, re.IGNORECASE)
        conferir(f"versão de {nome}", rf"\b{re.escape(nome)}\s+v?\d+\.\d+", bool(citado))
    padroes = {"OpenFOAM": r"OpenFOAM v?\d{4}", "Ansys": r"Ansys[^.\n]{0,40}(20\d{2} R\d|v\d{3})",
               "SOLIDWORKS": r"SOLIDWORKS 20\d{2}", "MATLAB": r"MATLAB[^.\n]{0,20}R20\d{2}[ab]"}
    for nome, padrao in padroes.items():
        conferir(f"versão do {nome}", padrao, re.search(nome, texto, re.IGNORECASE) is not None)
    return out


def frase_versoes(semente: int, n_iter: int, versoes: dict[str, str | None], ferramentas: dict[str, str],
                  texto: str = "") -> str:
    """Uma frase pronta para a secção de métodos com a semente, as iterações e as versões reais.

    Em linguagem simples: junta o que foi lido do ambiente e do repositório numa só frase; as bibliotecas
    da FEA e as ferramentas só entram se o relatório as citar (ou se o texto não for dado).
    """
    def citado(nome: str) -> bool:
        return not texto or re.search(re.escape(nome), texto, re.IGNORECASE) is not None

    libs = [f"{BIBLIOTECAS[p]} {versoes[p]}" for p in ("numpy", "pandas", "scipy", "matplotlib") if versoes.get(p)]
    fea = [f"{BIBLIOTECAS[p]} {versoes[p]}" for p in ("gmsh", "scikit-fem", "pyamg")
           if versoes.get(p) and citado(BIBLIOTECAS[p])]

    def lista(xs: list[str]) -> str:
        return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " e " + xs[-1]

    frase = f"Os cálculos foram feitos em Python {versoes['python']}"
    if libs:
        frase += f", com {lista(libs)}"
    if fea:
        frase += f" (FEA com {lista(fea)})"
    frase += f", e o Monte Carlo usou {mil(n_iter)} iterações com a semente {semente}"
    extra = []
    if "MATLAB" in ferramentas and citado("MATLAB"):
        extra.append(f"a validação independente usou o MATLAB {ferramentas['MATLAB']}")
    fea_ext = [f"o SOLIDWORKS {ferramentas['SOLIDWORKS']}"] if "SOLIDWORKS" in ferramentas and citado("SOLIDWORKS") else []
    if "Ansys" in ferramentas and citado("Ansys Mechanical"):
        fea_ext.append(f"o Ansys Mechanical APDL {ferramentas['Ansys']}")
    if fea_ext:
        extra.append(f"a FEA de comparação {lista(fea_ext)}")
    cfd = [f"o OpenFOAM {ferramentas['OpenFOAM']}"] if "OpenFOAM" in ferramentas and citado("OpenFOAM") else []
    if "Ansys" in ferramentas and citado("Fluent"):
        cfd.append(f"o Ansys Fluent {ferramentas['Ansys'].split(' (')[0]}")
    if cfd:
        extra.append(f"a CFD {lista(cfd)}")
    if extra:
        frase += "; " + lista(extra)
    return frase + "."


# ---------------------------------------------------------------- relatório

def auditar(rel: Path = REL, results: Path = RESULTS, data_dir: Path = DATA,
            geradas: dict[str, object] | None = None) -> tuple[list[Achado], str]:
    """Corre as seis verificações; devolve os achados e a frase proposta das versões."""
    pts = pd.read_csv(results / "pontuacoes.csv")
    mc = pd.read_csv(results / "monte_carlo.csv")
    semi = pd.read_csv(results / "semiquantitativos.csv")
    tri = results / "mc_triangular.csv"
    pcts = percentagens_resultados(mc, pd.read_csv(tri) if tri.exists() else None)
    achados: list[Achado] = []
    for nome in RESUMOS:
        f = rel / nome
        if f.exists():
            achados += numeros_do_resumo(f.read_text(encoding="utf-8"), nome, pts, mc, semi, pcts)
        else:
            achados.append(Achado(1, "aviso", nome, "ficheiro não encontrado"))
    achados += somas_monte_carlo(mc)
    tabelas = ler_tabelas(rel)
    achados += presenca(materiais_esperados(data_dir), pts, tabelas)
    achados += coerencia_rankings(pts, "results/pontuacoes.csv")
    for caso, tab in tabelas.items():
        achados += coerencia_rankings(tab, f"tabelas/{TABELAS[caso]}_resultados.md")
        achados += tabela_igual_resultados(tab, pts)
    import montar_relatorio as mr
    fontes = [data_dir / "materiais.csv", data_dir / "criterios.csv", results / "pontuacoes.csv"]
    achados += figuras_atualizadas(marcadores_figuras(rel), figuras_refeitas() if geradas is None else geradas,
                                   fontes, mr.CAMINHOS)
    texto = (rel / "RELATORIO.md").read_text(encoding="utf-8")
    semente, n_iter = int(mc["seed"].iloc[0]), int(mc["n_iter"].iloc[0])
    versoes, ferramentas = versoes_ambiente(), versoes_ferramentas()
    achados += declaracoes(texto, semente, n_iter, versoes, ferramentas)
    return achados, frase_versoes(semente, n_iter, versoes, ferramentas, texto)


def relatorio_md(achados: list[Achado], frase: str) -> str:
    """Texto de results/auditoria_relatorio.md: resumo por verificação, erros e avisos, e os ok para rastrear."""
    linhas = ["# Auditoria do relatório", "",
              "Gerado por scripts/auditoria_relatorio.py. Erros: o texto, as tabelas ou as figuras não batem com os "
              "resultados. Avisos: sobre resultados deste trabalho, mas não foi possível confirmar automaticamente. "
              "Notas: números de outras fontes (registos, literatura, parâmetros), fora do alcance desta auditoria.", "",
              "| Verificação | Erros | Avisos | Notas | Ok |", "|---|---|---|---|---|"]
    for k, nome in NOMES_VERIFICACAO.items():
        sub = [a for a in achados if a.verificacao == k]
        linhas.append(f"| {k}. {nome} | {sum(a.nivel == 'erro' for a in sub)} | "
                      f"{sum(a.nivel == 'aviso' for a in sub)} | {sum(a.nivel == 'nota' for a in sub)} | "
                      f"{sum(a.nivel == 'ok' for a in sub)} |")
    for nivel, titulo in (("erro", "Erros"), ("aviso", "Avisos"),
                          ("nota", "Notas (números que não são resultados deste trabalho; não verificados)"),
                          ("ok", "Confirmado")):
        sub = [a for a in achados if a.nivel == nivel]
        linhas += ["", f"## {titulo} ({len(sub)})", ""]
        linhas += [f"- [{a.verificacao}] {a.onde}: {a.mensagem}" for a in sub] or ["- nenhum"]
    if any(a.verificacao == 6 and a.nivel == "erro" for a in achados):
        linhas += ["", "## Frase proposta para a secção de métodos", "", frase]
    return "\n".join(linhas) + "\n"


def main() -> None:
    for fluxo in (sys.stdout, sys.stderr):
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8")
    achados, frase = auditar()
    texto = relatorio_md(achados, frase)
    SAIDA.write_text(texto, encoding="utf-8")
    print(texto)
    erros = sum(a.nivel == "erro" for a in achados)
    if erros:
        sys.exit(f"{erros} erro(s) na auditoria do relatório")


if __name__ == "__main__":
    main()
