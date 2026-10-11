"""Gera as tabelas do relatório a partir de data/ e de results/, para baterem sempre com os resultados.

Para cada caso (haste, par articular, stent, scaffold, implante dentário):
  relatorio/tabelas/<chave>_criterios.md    critério, tipo, alvo, peso e justificação (criterios.csv)
  relatorio/tabelas/<chave>_resultados.md   pontuação e posição nos três métodos, cenários A e B, com o ΔC
  relatorio/tabelas/<chave>_robustez.md     Monte Carlo, η e P-foco em frases curtas geradas dos resultados
Só para os casos quantitativos (haste, stent, scaffold; cenário A), de results/robustez_extra_*.csv
(correr antes scripts/robustez_extra.py):
  relatorio/tabelas/<chave>_retirar.md        retirar uma alternativa de cada vez (reversão de ranking)
  relatorio/tabelas/<chave>_dimensoes.md      dupla contagem: pesos redistribuídos dentro de cada dimensão
  relatorio/tabelas/<chave>_ajuste_minimo.md  pesos e valores mais sensíveis (menor ajuste que troca o 1.º)
Os casos quantitativos leem results/pontuacoes.csv, results/monte_carlo.csv e results/rankings_cenarios.csv
(correr antes scripts/run_all.py); os semiquantitativos calculam as pontuações com as mesmas funções e
leem results/semiquantitativos.csv.
Uso: python scripts/tabelas_relatorio.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

from biomat_mcdm.io import DATA, build_problem, load_data
from biomat_mcdm.pipeline import METODOS, consenso_borda, fmt_pt, rank_all_methods

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
import robustez_extra as rx  # noqa: E402

RESULTS = RAIZ / "results"
DESTINO = RAIZ / "relatorio" / "tabelas"
LIMIAR_EMPATE = 0.01  # ΔC (TOPSIS) abaixo do qual dois materiais contam como empatados

# chave: (nome em criterios.csv, nome em results/, quantitativo?)
CASOS = {
    "haste": ("Prótese da anca | Haste femoral", "Haste", True),
    "par": ("Prótese da anca | Par articular", "Par articular", False),
    "stent": ("Stent vascular", "Stent", True),
    "scaffold": ("Scaffold (regeneração óssea)", "Scaffold", True),
    "dentario": ("Implante dentário", "Implante dentário", False),
}
TIPOS = {"Benefício": "benefício", "Custo": "custo", "Alvo": "alvo", "Estrito": "eliminatório"}
SCORE = {"TOPSIS": ("C_TOPSIS", False), "WASPAS": ("Q_WASPAS", False), "VIKOR": ("P_VIKOR", True)}


def num(x: float | str, casas: int = 3) -> str:
    """Número em português (vírgula decimal); texto e vazios passam como estão."""
    if isinstance(x, str) or pd.isna(x):
        return "" if pd.isna(x) else x
    return fmt_pt(float(x), casas)


def pct(v: float) -> str:
    """Percentagem com uma casa, ou duas quando a uma casa arredondaria para 0 ou 100 sem o ser."""
    casas = 2 if (99.95 <= v < 100) or (0 < v < 0.05) else 1
    return f"{fmt_pt(v, casas)} %"


def contagem(v: float, n_iter: int) -> str:
    """Número de iterações correspondente a uma % (ex.: 99,99 % de 10 000 -> "9 999"), com espaço nos milhares.

    Em linguagem simples: quando um material fica em 1.º quase sempre, "9 999 das 10 000" diz mais do que "99,99 %".
    """
    return f"{round(v * n_iter / 100):,}".replace(",", " ")


def larguras(df: pd.DataFrame) -> list[int]:
    """Número de traços do separador de cada coluna (o pandoc usa-os como larguras relativas nas tabelas largas).

    Em linguagem simples: cada coluna fica pelo menos tão larga como a sua palavra mais comprida (para não partir
    nomes como "Hidroxiapatite") e cresce um pouco com o comprimento médio do texto das células (o LaTeX parte
    as frases compridas em várias linhas, mas não consegue partir bem nomes próprios).
    """
    out = []
    for col in df.columns:
        textos = [str(col)] + [str(v) for v in df[col]]
        palavra = max(len(w) for s in textos for w in (s.split() or [""]))
        media = sum(len(s) for s in textos) / len(textos)
        out.append(max(3, round(palavra + 1 + 0.15 * media)))  # +1: folga entre colunas
    return out


def md(df: pd.DataFrame) -> str:
    """Tabela em Markdown (cabeçalho, separador e linhas), sem dependências externas."""
    linhas = ["| " + " | ".join(df.columns) + " |", "|" + "".join("-" * w + "|" for w in larguras(df))]
    linhas += ["| " + " | ".join(str(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join(linhas)


def tabela_criterios(caso: str, data_dir: Path = DATA) -> pd.DataFrame:
    """Critérios de um caso como estão em criterios.csv, com o tipo por extenso.

    Em linguagem simples: a tabela "Candidatos e critérios" do relatório; os critérios
    eliminatórios aparecem sem peso, porque só servem para a triagem.
    """
    c = pd.read_csv(data_dir / "criterios.csv")
    c = c[c["caso_componente"] == caso]
    peso = c["peso"].map(lambda p: "" if pd.isna(p) else fmt_pt(float(p), 2))
    alvo = [("" if pd.isna(a) else f"{a} {u}".replace(" -", "").strip()) for a, u in zip(c["alvo"], c["unidade"])]
    return pd.DataFrame({"Critério": c["criterio"].to_numpy(), "Tipo": c["tipo"].map(TIPOS).to_numpy(),
                         "Alvo": alvo, "Peso": peso.to_numpy(),
                         "Justificação": c["justificacao"].fillna("").map(justificacao_relatorio).to_numpy()})


def justificacao_relatorio(texto: str) -> str:
    """Justificação de criterios.csv como sai no relatório: sem a marca "SEMIQUANTITATIVO" (o texto já o diz) e sem a
    remissão para a folha Cenarios da base de dados (o leitor do relatório não a tem)."""
    texto = re.sub(r"^SEMIQUANTITATIVO \(ordinais > 50 %\)\.\s*", "", texto)
    return texto.replace("CENÁRIO de referência, ver folha Cenarios", "valor de referência, testado nos cenários T (secção 6.4)")


def nota_pesos(caso: str, data_dir: Path = DATA) -> str:
    """Nota sob a tabela quando os pesos do cenário A não somam 1 (critérios só do cenário B)."""
    c = pd.read_csv(data_dir / "criterios.csv")
    c = c[(c["caso_componente"] == caso) & (c["tipo"] != "Estrito")]
    so_b = c["criterio"].str.contains("só cenário B")
    soma_a = c.loc[~so_b, "peso"].sum()
    if abs(soma_a - 1) < 1e-9:
        return ""
    return (f"\n\nPesos da base de dados. No cenário A, sem os critérios só do cenário B, somam "
            f"{fmt_pt(soma_a, 2)} e são renormalizados para somar 1.")


def pontuacoes(chave: str, data_dir: Path = DATA, results: Path = RESULTS) -> pd.DataFrame:
    """Pontuações e posições nos cenários A e B (quantitativos: de results/pontuacoes.csv)."""
    caso, rotulo, quant = CASOS[chave]
    if quant:
        pt = pd.read_csv(results / "pontuacoes.csv")
        return pt[pt["caso"] == rotulo].reset_index(drop=True)
    partes = [consenso_borda(rank_all_methods(build_problem(caso, cen, data_dir))).assign(caso=rotulo, cenario=cen)
              for cen in ("A", "B")]
    return pd.concat(partes, ignore_index=True)


def delta_c(pt: pd.DataFrame, cenario: str) -> float:
    """Diferença de C (TOPSIS) entre o 1.º e o 2.º lugar num cenário."""
    c = pt[pt["cenario"] == cenario]["C_TOPSIS"].sort_values(ascending=False).to_numpy()
    return float(c[0] - c[1])


def tabela_resultados(pt: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por cenário e material, ordenada pela posição no TOPSIS."""
    linhas = []
    for cen, g in pt.groupby("cenario", sort=True):
        for r in g.sort_values("pos_TOPSIS").itertuples():
            linhas.append({"Cenário": cen, "Material": r.material,
                           "C (TOPSIS)": num(r.C_TOPSIS), "Pos. T": r.pos_TOPSIS,
                           "Q (WASPAS)": num(r.Q_WASPAS), "Pos. W": r.pos_WASPAS,
                           "P (VIKOR)": num(r.P_VIKOR), "Pos. V": r.pos_VIKOR,
                           "Consenso (Borda)": f"{r.pos_Borda} ({r.pontos_Borda} pts)"})
    return pd.DataFrame(linhas)


def frase_delta(pt: pd.DataFrame) -> str:
    """Frase com o ΔC de cada cenário e a indicação de empate."""
    partes = []
    for cen in sorted(pt["cenario"].unique()):
        d = delta_c(pt, cen)
        partes.append(f"cenário {cen}: ΔC = {fmt_pt(d, 3)}" + (" (empate, abaixo de 0,01)" if d < LIMIAR_EMPATE else ""))
    return "Diferença de C entre o 1.º e o 2.º no TOPSIS: " + "; ".join(partes) + "."


def vencedor(g: pd.DataFrame) -> str:
    return " = ".join(sorted(g[g["posicao"] == 1]["material"]))


def gama_eta(eta: pd.DataFrame, vencedor_base: str) -> str:
    """Valores de η em que o vencedor de um método difere do vencedor com η = 1, em forma compacta."""
    vals = sorted(float(v.replace("η = ", "").replace(",", ".")) for v, g in eta.groupby("variante")
                  if vencedor(g) != vencedor_base)
    if not vals:
        return "nunca"
    passo = [round(0.1 * k, 1) for k in range(len(vals))]
    if vals == passo:
        return "η = 0" if len(vals) == 1 else f"η de 0 a {fmt_pt(vals[-1], 1)}"
    return ", ".join(f"η = {fmt_pt(v, 1)}" for v in vals)


def linha_monte_carlo(mc: pd.DataFrame, rotulo: str) -> str:
    """Frase com a % (ou o número) de iterações em 1.º lugar de cada material, para uma análise de Monte Carlo.

    Em linguagem simples: `mc` são as linhas de results/monte_carlo.csv de um caso e de uma análise (propriedades
    ou pesos); quando o vencedor fica em 1.º quase sempre, diz-se "9 999 das 10 000" em vez de "99,99 %".
    """
    piv = mc.pivot(index="material", columns="metodo", values="pct_primeiro")[METODOS]
    piv = piv[piv.max(axis=1) >= 1].sort_values("TOPSIS", ascending=False)
    n_iter = int(mc["n_iter"].iloc[0])
    n = contagem(100, n_iter)
    if piv.iloc[0].min() >= 99.9:
        a, row = piv.index[0], piv.iloc[0]
        return (f"- {rotulo} ({n} iterações, cenário A), repetições em 1.º lugar (TOPSIS / WASPAS / VIKOR): "
                f"{a} {' / '.join(contagem(v, n_iter) for v in row)} das {n}.")
    return (f"- {rotulo} ({n} iterações, cenário A), % de 1.º lugar (TOPSIS / WASPAS / VIKOR): "
            + "; ".join(f"{a} {' / '.join(pct(v) for v in row)}" for a, row in piv.iterrows()) + ".")


NOMES_CENARIOS = {"Q": "Sem critérios ordinais (Q)", "T-haste": "Valores-alvo (T)", "T-scaffold": "Valores-alvo (T)",
                  "R-sentinela": "Tempo de reabsorção dos permanentes (R-sentinela, cenário B)"}


def linhas_cenarios(rk: pd.DataFrame) -> list[str]:
    """Frases com o vencedor por método nos cenários Q, T e R-sentinela de um caso (de rankings_cenarios.csv).

    Em linguagem simples: quando todas as variantes de um cenário dão os mesmos vencedores, fica uma só frase
    com as variantes entre parênteses; senão, uma frase por variante.
    """
    L = []
    for cen in NOMES_CENARIOS:
        g = rk[rk["cenario"] == cen]
        if g.empty:
            continue
        variantes = list(dict.fromkeys(g["variante"]))
        venc = {v: tuple(vencedor(g[(g["variante"] == v) & (g["metodo"] == m)]) for m in METODOS) for v in variantes}
        nome = NOMES_CENARIOS[cen]
        # variantes com os mesmos vencedores ficam juntas na mesma frase (pela ordem em que aparecem)
        grupos: dict[tuple, list[str]] = {}
        for v in variantes:
            grupos.setdefault(venc[v], []).append(v)
        for w, vs in grupos.items():
            cab = nome if cen == "Q" else f"{nome}, {'; '.join(vs)}"
            L.append(f"- {cab}: " + "; ".join(f"{m} {x}" for m, x in zip(METODOS, w)) + ".")
    return L


def robustez_linhas(chave: str, results: Path = RESULTS) -> list[str]:
    """Frases curtas, geradas dos resultados, para a secção "Robustez" de cada caso."""
    caso, rotulo, quant = CASOS[chave]
    L = []
    if quant:
        mc = pd.read_csv(results / "monte_carlo.csv")
        mc = mc[mc["caso"] == rotulo]
        L.append(linha_monte_carlo(mc[mc["analise"] == "MC propriedades"], "Monte Carlo das propriedades"))
        pesos = mc[mc["analise"].str.startswith("W pesos")]
        if not pesos.empty:
            L.append(linha_monte_carlo(pesos, "Monte Carlo dos pesos, ±20 %"))
        rk = pd.read_csv(results / "rankings_cenarios.csv")
        rk = rk[rk["caso"] == rotulo]
        base = {m: vencedor(rk[(rk["cenario"] == "A") & (rk["metodo"] == m)]) for m in METODOS}
        eta = rk[rk["cenario"] == "η"]
        partes = [f"{m}: {gama_eta(eta[eta['metodo'] == m], base[m])}" for m in METODOS]
        L.append("- Combinação com pesos objetivos (η de 0 a 1; η = 1 é o resultado principal), η em que o "
                 "vencedor muda: " + "; ".join(partes) + ".")
        foco = rk[rk["cenario"] == "P-foco"]
    else:
        foco = pd.read_csv(results / "semiquantitativos.csv")
        foco = foco[(foco["caso"] == rotulo) & (foco["cenario"] != "A")]
        L.append("- Caso semiquantitativo (escalas ordinais com mais de 50 % do peso): o ranking é uma indicação.")
    for (cen, var), g in foco.groupby(["cenario", "variante"], sort=False):
        rot = f"P-foco ({var})" if cen == "P-foco" else f"Sensibilidade ({var})"
        L.append(f"- {rot}: " + "; ".join(f"{m} {vencedor(g[g['metodo'] == m])}" for m in METODOS) + ".")
    if quant:
        L += linhas_cenarios(rk)
    return L


def tabela_spearman(results: Path = RESULTS) -> pd.DataFrame:
    """ρ de Spearman entre os pares de métodos, nos cenários A, B e Q, para os três casos quantitativos.

    Em linguagem simples: mede quanto as ordenações de dois métodos se parecem (1 = iguais); vem de
    results/spearman.csv, calculado pelo run_all.py.
    """
    sp = pd.read_csv(results / "spearman.csv")
    pares = ["TOPSIS-WASPAS", "TOPSIS-VIKOR", "WASPAS-VIKOR"]
    nomes = {"A": "A", "B": "B", "Q": "Q (sem ordinais)"}
    linhas = []
    for caso in ("Haste", "Stent", "Scaffold"):
        for cen, rot in nomes.items():
            g = sp[(sp["caso"] == caso) & (sp["cenario"] == cen)].set_index("par")["rho"]
            if g.empty:
                continue
            linhas.append({"Caso": caso, "Cenário": rot,
                           **{p.replace("-", " / "): fmt_pt(float(g[p]), 2) for p in pares}})
    return pd.DataFrame(linhas)


def tabela_propriedades(chave: str, data_dir: Path = DATA) -> pd.DataFrame:
    """Propriedades que caracterizam os candidatos: valor típico de cada critério, por material (cenário B).

    Em linguagem simples: é a matriz de decisão que entra nos métodos (todos os candidatos, incluindo os de
    investigação), com uma linha por critério e uma coluna por material. Os valores ainda "A verificar" levam *;
    os valores de modelação levam †: os que não existem na base (ou têm o típico vazio) e foram preenchidos pelo
    pior valor observado, e os que têm o estado "Valor de modelação".
    """
    caso = CASOS[chave][0]
    p = build_problem(caso, "B", data_dir)
    mat, crit = load_data(data_dir)
    mat = mat[mat["caso_componente"] == caso]
    crit = crit[crit["caso_componente"] == caso]
    unid = {c.replace(" (só cenário B)", ""): u for c, u in zip(crit["criterio"], crit["unidade"])}
    linhas = []
    for j, cr in enumerate(p.criteria):
        u = unid.get(cr, "-")
        nome = cr if u in ("-", "", "unidade") or pd.isna(u) else f"{cr} ({u})"
        linha = {"Propriedade": nome.replace("10^7", "10⁷").replace("K_IC", "K~IC~").replace("m^0.5", "m^1/2^")}
        for i, a in enumerate(p.alternatives):
            v = float(p.X[i, j])
            casas = 4 if abs(v) < 0.1 and v != 0 else (3 if abs(v) < 1 else 2)
            txt = num(v, casas)
            if "," in txt:
                txt = txt.rstrip("0").rstrip(",")
            reg = mat[(mat["material"] == a) & (mat["propriedade"] == cr)]
            if reg.empty or pd.isna(reg["tipico"].iloc[0]) or str(reg["estado"].iloc[0]) == "Valor de modelação":
                txt += " †"
            elif not str(reg["estado"].iloc[0]).startswith("Verificado"):
                txt += " *"
            linha[a] = txt
        linhas.append(linha)
    return pd.DataFrame(linhas)


NOTA_PROPRIEDADES = ("Valor típico da base de dados (o mesmo que entra nos métodos), com todos os candidatos (cenário B); "
                     "escalas ordinais de 1 a 5 (Anexo C). * valor ainda \"A verificar\"; † valor de modelação (número "
                     "fixado por uma regra do trabalho, secção 2.4). Mínimos, máximos e fontes no anexo digital.")

NOTAS_PROPRIEDADES_CASO = {
    "haste": "Na haste, a resistência à fadiga (σmax, R = 0,1) dos quatro materiais ensaiados por Okazaki (2012) é a tensão máxima a 10⁷ "
             "ciclos num ensaio de tração-tração (R = 0,1); a amplitude correspondente é 0,45 vezes esse valor, por "
             "isso pode ficar acima da tensão de cedência (Co-Cr-Mo).",
    "stent": "Os 48 meses de reabsorção das ligas permanentes são o pior valor observado (máximo do PLLA), atribuído "
             "a materiais que não reabsorvem (secção 9.9); não são um tempo de reabsorção.",
    "scaffold": "O tempo de degradação da HA é um valor de modelação: a HA praticamente não reabsorve, e o número "
                "não tem fonte própria.",
}


def nota_propriedades(chave: str) -> str:
    """Legenda da tabela de propriedades de um caso: a nota comum e, se houver, a nota própria do caso.

    Em linguagem simples: explica os símbolos (* e †) e, na haste, no stent e no scaffold, o valor que um leitor
    podia ler mal (a fadiga acima da cedência no Co-Cr-Mo; os 48 meses dos metais; a HA).
    """
    extra = NOTAS_PROPRIEDADES_CASO.get(chave)
    return NOTA_PROPRIEDADES + (" " + extra if extra else "")


def tabela_dados(caso: str, data_dir: Path = DATA) -> pd.DataFrame:
    """Anexo B: todos os valores da base de um caso, com a fonte e o estado de cada um.

    Em linguagem simples: a tabela completa de dados, como está em data/materiais.csv (mín.,
    máx. e típico; propriedades categóricas pelo texto), sem as notas longas.
    """
    m = pd.read_csv(data_dir / "materiais.csv")
    m = m[m["caso"] == caso]
    linhas = []
    for r in m.itertuples():
        if pd.isna(r.min) and pd.isna(r.max):
            valor = "" if pd.isna(r.valor_texto) else str(r.valor_texto)
        elif r.min == r.max:
            valor = num(r.min, 4).rstrip("0").rstrip(",")
        else:
            valor = f"{num(r.min, 4).rstrip('0').rstrip(',')} a {num(r.max, 4).rstrip('0').rstrip(',')}"
        tip = "" if pd.isna(r.tipico) else num(r.tipico, 4).rstrip("0").rstrip(",")
        fonte = "" if pd.isna(r.referencia) else str(r.referencia)
        if not pd.isna(r.doi_url):
            fonte += f" ({r.doi_url})"
        linhas.append({"Material": r.material, "Propriedade": r.propriedade,
                       "Unidade": "" if r.unidade == "-" else r.unidade, "Valor": valor, "Típico": tip,
                       "Estado": r.estado, "Fonte": fonte.replace("|", "/")})
    return pd.DataFrame(linhas)


def anexo_b(data_dir: Path = DATA) -> str:
    """Texto do anexo B: uma tabela por caso, com a contagem de valores por estado."""
    m = pd.read_csv(data_dir / "materiais.csv")
    L = ["# Anexo B. Base de dados completa", "",
         "Valores de data/materiais.csv (versão usada neste relatório). Valor: mínimo a máximo da base; Típico: o "
         "valor usado nos métodos. Estados: \"Verificado\" (confirmado na fonte indicada), \"Verificado "
         "(fornecedor)\" (ficha técnica de fornecedor), \"Verificado (derivado)\" (calculado a partir de valores "
         "publicados na fonte), \"Verificado (composição química)\" (deduzido da composição do material), "
         "\"Verificado (composição nominal)\" (deduzido da composição nominal publicada da liga), \"Valor de modelação\" "
         "(número fixado por uma regra do trabalho, sem fonte numérica própria; por exemplo, o tempo de degradação da "
         "HA e o tempo de reabsorção das ligas permanentes do stent) e \"A verificar\" (valor de partida ainda não confirmado "
         "na fonte original). As notas de cada valor estão na base de dados.", ""]
    contagem = m["estado"].value_counts()
    L += ["Contagem por estado: " + "; ".join(f"{k}: {v}" for k, v in contagem.items()) + f" (total: {len(m)}).", ""]
    for caso in m["caso"].drop_duplicates():
        L += [f"## {caso}", "", md(tabela_dados(caso, data_dir)), ""]
    return "\n".join(L)


def contagem_estados(data_dir: Path = DATA) -> pd.DataFrame:
    """Número de valores por estado, por caso e no total (linhas: casos e Total; colunas: estados)."""
    m = pd.read_csv(data_dir / "materiais.csv")
    t = pd.crosstab(m["caso"], m["estado"], margins=True, margins_name="Total")
    return t.rename_axis(index=None, columns=None)


def anexo_b_resumo(data_dir: Path = DATA) -> str:
    """Anexo B do relatório: só a contagem por estado e a remissão para o anexo digital."""
    t = contagem_estados(data_dir)
    tab = pd.DataFrame({"Caso": t.index, **{c: t[c].to_numpy() for c in t.columns}})
    return "\n".join([
        "# Anexo B. Base de dados", "",
        "A base de dados completa, com o valor, a fonte, o estado e as notas de cada uma das "
        f"{int(t.loc['Total', 'Total'])} linhas, é entregue em anexo digital (base_dados_biomateriais.xlsx); a Tabela B.1 resume o número de valores por "
        "caso e por estado.", "",
        "Estados: \"Verificado\" (confirmado na fonte indicada), \"Verificado (fornecedor)\" (ficha técnica de "
        "fornecedor), \"Verificado (derivado)\" (calculado a partir de valores publicados na fonte), \"Verificado "
        "(composição química)\" (deduzido da composição do material), \"Verificado (composição nominal)\" "
        "(deduzido da composição nominal publicada da liga), \"Valor de modelação\" (número fixado por uma regra do "
        "trabalho, sem fonte numérica própria; por exemplo, o tempo de degradação da HA, que praticamente não "
        "reabsorve, e o tempo de reabsorção das ligas permanentes do stent) e \"A verificar\" (valor de partida ainda não "
        "confirmado na fonte original).", "",
        "**Tabela B.1.** Número de valores da base de dados por caso e por estado.", "", md(tab)])


# Comparação com estudos anteriores: só o que foi lido em cada artigo (texto completo ou resumo).
ESTUDOS = [
    ("Petković et al. 2025", "placa de fixação óssea; corpo da haste femoral", "15 materiais metálicos; 10 critérios em cada caso",
     "TOPSIS, VIKOR e WASPAS estendidos", "sim (módulo de Young, alvo de 14 GPa)",
     "valores da literatura, sem verificação indicada na fonte original", "nível de confiança η de 0,7 a 1",
     "dois casos de estudo e concordância qualitativa com a literatura; sem reprodução numérica"),
    ("Bahraminasab e Jahan 2011", "componente femoral da prótese total do joelho", "não indicado", "VIKOR abrangente",
     "não indicado", "não indicado", "sensibilidade dos pesos", "não indicado"),
    ("Hafezalkotob e Hafezalkotob 2017", "componente femoral da prótese da anca e do joelho", "anca: 11 materiais, 9 critérios",
     "MULTIMOORA com critérios-alvo e dados em intervalos", "sim (densidade e módulo de Young)",
     "matriz de um estudo anterior, sem verificação na fonte original", "não indicado",
     "comparação das ordenações com outros métodos publicados"),
    ("Kumar et al. 2021", "componente femoral da prótese total do joelho", "11 materiais, 8 critérios",
     "WSM, WPM, WASPAS, EDAS e TOPSIS, combinados", "não indicado", "não indicado",
     "troca do esquema de pesos (desvio-padrão, entropia, AHP difuso)", "não indicado"),
    ("Este trabalho", "haste femoral, par articular, stent coronário, scaffold ósseo, implante dentário",
     "4 a 8 materiais e 7 a 11 critérios por caso", "TOPSIS, WASPAS e VIKOR; consenso de Borda",
     "sim (haste, scaffold, implante dentário e tempo de reabsorção do stent)",
     "@@N_VERIFICADOS@@ dos @@N_TOTAL@@ valores verificados em fontes primárias; regras da forma e da porosidade",
     "Monte Carlo das propriedades e dos pesos; η de 0 a 1; cenários Q, T, C-custo, P-foco e O-orçamento",
     "reprodução numérica dos casos 1 e 2 de Petković et al. 2025"),
]
COLUNAS_ESTUDOS = ["Estudo", "Dispositivo", "Materiais e critérios", "Métodos", "Critérios-alvo",
                   "Verificação dos dados", "Robustez", "Validação da implementação"]


def tabela_estudos() -> pd.DataFrame:
    """Tabela da secção "Comparação com estudos anteriores" (última linha: este trabalho)."""
    return pd.DataFrame(ESTUDOS, columns=COLUNAS_ESTUDOS)


N_PESOS_AJUSTE = 4    # pesos mais sensíveis na tabela do ajuste mínimo
N_VALORES_AJUSTE = 6  # valores mais sensíveis na tabela do ajuste mínimo


def ler_robustez_extra(rotulo: str, cenario: str = "A", results: Path = RESULTS) -> dict[str, pd.DataFrame]:
    """Linhas de um caso e cenário nos quatro ficheiros results/robustez_extra_*.csv.

    Em linguagem simples: vai buscar os resultados já calculados por scripts/robustez_extra.py
    (retirar uma alternativa, dimensões, ajuste dos pesos e dos valores) só do caso pedido.
    """
    out = {}
    for k in ("retirar", "dimensoes", "pesos", "valores"):
        df = pd.read_csv(results / f"robustez_extra_{k}.csv")
        out[k] = df[(df["caso"] == rotulo) & (df["cenario"] == cenario)].reset_index(drop=True)
    return out


def texto_retirar(rotulo: str, results: Path = RESULTS) -> str:
    """Tabela "retirar uma alternativa" (cenário A) com a frase sobre o 1.º lugar entre os restantes."""
    t = ler_robustez_extra(rotulo, "A", results)
    return (md(rx.tabela_retirar(t["retirar"])) + "\n\nCenário A, valores típicos, η = 1. Cada linha refaz o "
            "ranking sem o material indicado; \"sim\" quer dizer que pelo menos um par dos restantes troca de ordem. "
            + rx.frase_vencedor_retirar(t["retirar"]))


def texto_dimensoes(rotulo: str, results: Path = RESULTS) -> str:
    """Tabela da dupla contagem (cenário A): pesos iguais dentro da dimensão e Monte Carlo de Dirichlet."""
    t = ler_robustez_extra(rotulo, "A", results)
    dm = t["dimensoes"]
    n = contagem(100, int(dm["n_iter"].iloc[0]))
    return ("Peso total por dimensão (fixo): " + dm["pesos_dimensao"].iloc[0] + ".\n\n" + md(rx.tabela_dimensoes(dm))
            + f"\n\nCenário A, η = 1. Monte Carlo: {n} repartições ao acaso do peso de cada dimensão pelos seus "
            f"critérios (Dirichlet, α = 1, seed {int(dm['seed'].iloc[0])}); mapa critério → dimensão em "
            "data/dimensoes_criterios.csv.")


def texto_ajuste(rotulo: str, results: Path = RESULTS) -> str:
    """Tabelas curtas do menor ajuste que troca o 1.º lugar (cenário A): valores e pesos mais sensíveis."""
    t = ler_robustez_extra(rotulo, "A", results)
    L = ["Valores típicos mais sensíveis (variação de um só valor; ordinais em passos inteiros):", "",
         md(rx.tabela_valores(t["valores"], N_VALORES_AJUSTE)), ""]
    pw = t["pesos"]
    trocam = min(N_PESOS_AJUSTE, int(rx.mais_sensiveis(pw, ["criterio"])["var_min"].notna().sum()))
    if trocam:
        L += ["Pesos mais sensíveis (variação relativa de um só peso; os outros renormalizados):", "",
              md(rx.tabela_pesos(pw, trocam)), ""]
    resto = pw["criterio"].nunique() - trocam
    frase = f"Cenário A, η = 1; procura até ±{round(100 * rx.LIMITE_VALOR)} % nos valores e ±{round(100 * rx.LIMITE_PESO)} % nos pesos. "
    if resto:
        frase += f"Os outros {resto} pesos não aparecem na tabela (menos sensíveis ou sem troca). "
    L.append(frase + rx.frase_empate_topsis(pw, t["valores"]))
    return "\n".join(L)


def gerar(destino: Path = DESTINO, data_dir: Path = DATA, results: Path = RESULTS) -> list[Path]:
    """Escreve as tabelas de cada caso (e as três da robustez complementar nos quantitativos); devolve os caminhos."""
    destino.mkdir(parents=True, exist_ok=True)
    feitos = []
    for chave, (caso, rotulo, quant) in CASOS.items():
        pt = pontuacoes(chave, data_dir, results)
        aviso = "" if quant else "\n\nSemiquantitativo: escalas ordinais com mais de 50 % do peso; o ranking é uma indicação."
        textos = {"criterios": md(tabela_criterios(caso, data_dir)) + nota_pesos(caso, data_dir),
                  "resultados": md(tabela_resultados(pt)) + "\n\n" + frase_delta(pt) + aviso,
                  "robustez": "\n".join(robustez_linhas(chave, results)),
                  "propriedades": md(tabela_propriedades(chave, data_dir)) + "\n\n" + nota_propriedades(chave)}
        if quant:
            textos.update({"retirar": texto_retirar(rotulo, results), "dimensoes": texto_dimensoes(rotulo, results),
                           "ajuste_minimo": texto_ajuste(rotulo, results)})
        for nome, texto in textos.items():
            p = destino / f"{chave}_{nome}.md"
            p.write_text(f"<!-- gerado por scripts/tabelas_relatorio.py; não editar à mão -->\n{texto}\n", encoding="utf-8")
            feitos.append(p)
    for nome, texto in (("anexo_b_dados", anexo_b(data_dir)), ("anexo_b_resumo", anexo_b_resumo(data_dir)),
                        ("comparacao_estudos", md(tabela_estudos())),
                        ("concordancia_spearman", md(tabela_spearman(results)))):
        p = destino / f"{nome}.md"
        p.write_text("<!-- gerado por scripts/tabelas_relatorio.py; não editar à mão -->\n" + texto + "\n",
                     encoding="utf-8")
        feitos.append(p)
    return feitos


if __name__ == "__main__":
    for p in gerar():
        print(p)
