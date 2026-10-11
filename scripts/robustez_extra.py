"""Robustez complementar dos três casos quantitativos (haste, stent, scaffold), cenários A e B, η = 1.

Três análises (funções em src/biomat_mcdm/robustez_extra.py):
  a) retirar uma alternativa de cada vez e ver se a ordem das restantes muda (reversão de ranking);
  b) dupla contagem: peso de cada dimensão fixo (data/dimensoes_criterios.csv), redistribuído dentro
     da dimensão (pesos iguais e Monte Carlo de Dirichlet);
  c) menor ajuste de um peso (até ±100 %) ou de um valor típico (até ±50 %; ordinais em passos
     inteiros) que troca o 1.º lugar de cada método.
Gera:
  results/robustez_extra.md              texto legível com as três análises por caso
  results/robustez_extra_retirar.csv     a) por caso, cenário, material retirado e método
  results/robustez_extra_dimensoes.csv   b) por caso, cenário e método
  results/robustez_extra_pesos.csv       c) pesos, por caso, cenário, critério e método
  results/robustez_extra_valores.csv     c) valores, por caso, cenário, material, critério e método
Uso: python scripts/robustez_extra.py [--n-iter 10000] [--seed 42]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from biomat_mcdm.io import DATA, PIOR_OBSERVADO, build_problem
from biomat_mcdm.pipeline import METODOS, fmt_pt
from biomat_mcdm.robustez_extra import (LIMIAR_EMPATE, ajuste_minimo_pesos, ajuste_minimo_valores,
                                        carregar_dimensoes, dupla_contagem, fmt_var, fontes_celulas,
                                        mais_sensiveis, merito, pesos_por_dimensao, referencia_curta,
                                        reversao_ranking)

RESULTS = Path(__file__).resolve().parents[1] / "results"
CASOS = {"Haste": "Prótese da anca | Haste femoral", "Stent": "Stent vascular",
         "Scaffold": "Scaffold (regeneração óssea)"}
CENARIOS = ("A", "B")
LIMITE_PESO = 1.0    # ±100 % do peso
LIMITE_VALOR = 0.5   # ±50 % do valor típico (quantitativos)
SEM_VALOR = "sem valor na base (pior observado, opção O2)"


def com_fontes(av: pd.DataFrame, caso: str, data_dir: Path = DATA) -> pd.DataFrame:
    """Acrescenta o estado e a referência de data/materiais.csv a cada valor do ajuste mínimo.

    Em linguagem simples: diz de onde vem cada número; os valores imputados pelo pior observado
    (tempo de reabsorção dos stents permanentes, cenário B) não têm linha na base e ficam assinalados.
    """
    f = fontes_celulas(caso, data_dir).rename(columns={"propriedade": "criterio"})
    out = av.merge(f, on=["material", "criterio"], how="left")
    imput = out["estado"].isna() & out["criterio"].map(lambda c: (caso, c) in PIOR_OBSERVADO)
    out.loc[imput, "estado"] = SEM_VALOR
    out["estado"] = out["estado"].fillna("sem linha na base")
    out["ref_curta"] = out["referencia"].map(referencia_curta)
    return out


def correr(n_iter: int = 10_000, seed: int = 42, data_dir: Path = DATA) -> dict[str, pd.DataFrame]:
    """Corre as três análises em cada caso e cenário; devolve as quatro tabelas (não grava)."""
    t = {"retirar": [], "dimensoes": [], "pesos": [], "valores": []}
    for caso, nome in CASOS.items():
        dims = carregar_dimensoes(nome, data_dir)
        for cen in CENARIOS:
            p = build_problem(nome, cen, data_dir)
            tag = {"caso": caso, "cenario": cen}
            t["retirar"].append(reversao_ranking(p).assign(**tag))
            pd_dim = pesos_por_dimensao(p, dims)
            t["dimensoes"].append(dupla_contagem(p, dims, n_iter, seed).assign(
                **tag, pesos_dimensao="; ".join(f"{d} {fmt_pt(w, 2)}" for d, w in pd_dim.items())))
            t["pesos"].append(ajuste_minimo_pesos(p, LIMITE_PESO).assign(**tag))
            t["valores"].append(com_fontes(ajuste_minimo_valores(p, LIMITE_VALOR), nome, data_dir).assign(**tag))
    return {k: pd.concat(v, ignore_index=True) for k, v in t.items()}


def vencedores_base(caso: str, cen: str, data_dir: Path = DATA) -> str:
    """Frase com o 1.º lugar de cada método e a folga do TOPSIS (ΔC)."""
    p = build_problem(CASOS[caso], cen, data_dir)
    partes = []
    for m in METODOS:
        s = merito(p, m)
        ordem = s.argsort()[::-1]
        txt = f"{m} {p.alternatives[ordem[0]]}"
        if m == "TOPSIS":
            d = s[ordem[0]] - s[ordem[1]]
            txt += f" (ΔC = {fmt_pt(d, 3)}{', empate' if d < LIMIAR_EMPATE else ''})"
        partes.append(txt)
    return "; ".join(partes)


def celula_retirar(g: pd.DataFrame) -> str:
    """"sim", "sim (empate)" ou "não" para um método e material retirado."""
    r = g.iloc[0]
    if not r["alterado"]:
        return "não"
    return "sim (só empates, ΔC < 0,01)" if r["so_empates"] else "sim"


def tabela_retirar(rt: pd.DataFrame) -> pd.DataFrame:
    """Tabela da análise a): uma linha por material retirado."""
    linhas = []
    for mat, g in rt.groupby("retirado", sort=False):
        pares = [f"{m}: {g[g['metodo'] == m]['pares'].iloc[0]}" for m in METODOS
                 if g[g["metodo"] == m]["alterado"].iloc[0]]
        linhas.append({"Retirado": mat, **{m: celula_retirar(g[g["metodo"] == m]) for m in METODOS},
                       "Pares que trocam": "; ".join(pares) if pares else "nenhum"})
    return pd.DataFrame(linhas)


def frase_vencedor_retirar(rt: pd.DataFrame) -> str:
    """Diz se o 1.º lugar entre os restantes muda quando se retira um material que não é o vencedor."""
    muda = rt[rt["vencedor_antes"] != rt["vencedor_depois"]]
    if muda.empty:
        return "O 1.º lugar entre os restantes nunca muda ao retirar um material."
    return "O 1.º lugar entre os restantes muda em: " + "; ".join(
        f"{r.metodo} sem {r.retirado} ({r.vencedor_antes} → {r.vencedor_depois})" for r in muda.itertuples()) + "."


def tabela_dimensoes(dm: pd.DataFrame) -> pd.DataFrame:
    """Tabela da análise b): vencedor com os pesos da base, com pesos iguais na dimensão e % no MC."""
    linhas = []
    for r in dm.itertuples():
        mc = f"{fmt_pt(r.pct_mantem, 1)} %"
        if r.metodo == "TOPSIS" and r.pct_mantem_ou_empate > r.pct_mantem:
            mc += f" ({fmt_pt(r.pct_mantem_ou_empate, 1)} % com empates)"
        outro = f"{r.outro_vencedor} ({fmt_pt(r.pct_outro, 1)} %)" if r.outro_vencedor else "nenhum"
        linhas.append({"Método": r.metodo, "Vencedor (pesos da base)": r.vencedor_base,
                       "Pesos iguais na dimensão": r.vencedor_iguais, "MC: mantém o 1.º": mc,
                       "Outro 1.º mais frequente": outro})
    return pd.DataFrame(linhas)


def tabela_pesos(pw: pd.DataFrame, n: int | None = None) -> pd.DataFrame:
    """Tabela da análise c) para os pesos: variação que troca o 1.º em cada método, mais sensíveis primeiro."""
    ordem = mais_sensiveis(pw, ["criterio"])["criterio"]
    if n is not None:
        ordem = ordem.head(n)
    linhas = []
    for c in ordem:
        g = pw[pw["criterio"] == c].set_index("metodo")
        cel = {}
        for m in METODOS:
            r = g.loc[m]
            cel[m] = fmt_var(r["var"], LIMITE_PESO) + (f" ({r['novo_vencedor']})" if pd.notna(r["var"]) else "")
        linhas.append({"Critério": c, "Peso": fmt_pt(g["peso"].iloc[0], 3), **cel})
    return pd.DataFrame(linhas)


def tabela_valores(pv: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Tabela da análise c) para os valores: os n mais sensíveis, com o estado e a referência da fonte."""
    s = mais_sensiveis(pv, ["material", "criterio"])
    s = s[s["var_min"].notna()].head(n)
    fontes = pv.drop_duplicates(["material", "criterio"]).set_index(["material", "criterio"])
    linhas = []
    for r in s.itertuples():
        f = fontes.loc[(r.material, r.criterio)]
        valor = f"{r.valor:g}".replace(".", ",") + (" (ordinal)" if r.ordinal else "")
        linhas.append({"Material": r.material, "Critério": r.criterio, "Valor": valor,
                       "Variação que troca": fmt_var(r.var_min, LIMITE_VALOR, r.pontos if r.ordinal else None),
                       "Método(s)": r.metodos, "Novo 1.º": r.novo_vencedor,
                       "Estado": f["estado"], "Fonte": f["ref_curta"]})
    return pd.DataFrame(linhas)


def md(df: pd.DataFrame) -> str:
    """Tabela em Markdown simples."""
    linhas = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    return "\n".join(linhas + ["| " + " | ".join(str(v) for v in r) + " |" for r in df.itertuples(index=False)])


def frase_empate_topsis(pw: pd.DataFrame, pv: pd.DataFrame) -> str:
    """Menor variação (peso e valor) que põe o vencedor do TOPSIS em empate (ΔC < 0,01)."""
    partes = []
    for nome, df, chaves, lim in (("peso", pw, ["criterio"], LIMITE_PESO),
                                  ("valor", pv, ["material", "criterio"], LIMITE_VALOR)):
        t = df[(df["metodo"] == "TOPSIS") & df["var_empate"].notna()]
        if t.empty:
            partes.append(f"nenhum {nome} o põe em empate até ±{round(100 * lim)} %")
            continue
        r = t.loc[t["var_empate"].abs().idxmin()]
        if r["var_empate"] == 0:
            return "No TOPSIS, o vencedor já está em empate (ΔC < 0,01) no caso de base."
        alvo = " / ".join(str(r[k]) for k in chaves)
        ordinal = r.get("ordinal")
        e_ord = isinstance(ordinal, (bool, np.bool_)) and bool(ordinal)
        pontos = round(r["var_empate"] * r["valor"]) if e_ord else None  # passo inteiro do empate
        partes.append(f"{nome}: {alvo} {fmt_var(r['var_empate'], lim, pontos)}")
    return "No TOPSIS, menor variação que deixa o vencedor em empate (ΔC < 0,01): " + "; ".join(partes) + "."


def relatorio_md(t: dict[str, pd.DataFrame], n_iter: int, seed: int, data_dir: Path = DATA) -> str:
    """Texto de results/robustez_extra.md com as três análises por caso e cenário."""
    L = ["# Robustez complementar (PRELIMINAR: dados por verificar)", "",
         f"Valores típicos da base, η = 1. Monte Carlo das dimensões: {n_iter} iterações, seed {seed}, "
         "Dirichlet com α = 1 dentro de cada dimensão (peso total da dimensão fixo; "
         "mapa critério → dimensão em data/dimensoes_criterios.csv).", "",
         "Regra de empate: no TOPSIS, ΔC < 0,01 conta como empate. As trocas de vencedor são estritas "
         "(outro material passa a ter melhor pontuação); no TOPSIS indica-se também quando o vencedor "
         "deixa de ter folga de 0,01 (empate), que acontece sempre antes da troca. Na reversão de ranking, "
         "os pares do TOPSIS que trocam com ΔC < 0,01 (antes ou depois) ficam marcados como empate.", "",
         f"Menor ajuste: pesos de -100 % a +{round(100 * LIMITE_PESO)} % (um peso de cada vez, os outros "
         f"renormalizados na mesma proporção); valores típicos até ±{round(100 * LIMITE_VALOR)} % "
         "(ordinais 1-5 em passos inteiros dentro da escala); varrimento em passos de 0,5 % e bisseção.", ""]
    for caso in CASOS:
        for cen in CENARIOS:
            sel = {k: v[(v["caso"] == caso) & (v["cenario"] == cen)] for k, v in t.items()}
            L += [f"## {caso}, cenário {cen}", "", "Vencedores: " + vencedores_base(caso, cen, data_dir) + ".", "",
                  "### a) Retirar uma alternativa", "", md(tabela_retirar(sel["retirar"])), "",
                  frase_vencedor_retirar(sel["retirar"]), "",
                  "### b) Dupla contagem (pesos redistribuídos dentro de cada dimensão)", "",
                  "Peso por dimensão: " + sel["dimensoes"]["pesos_dimensao"].iloc[0] + ".", "",
                  md(tabela_dimensoes(sel["dimensoes"])), "",
                  "### c) Menor ajuste que troca o 1.º lugar", "", "**Pesos**", "",
                  md(tabela_pesos(sel["pesos"])), "", "**Valores típicos (os 12 mais sensíveis)**", "",
                  md(tabela_valores(sel["valores"], 12)), "",
                  frase_empate_topsis(sel["pesos"], sel["valores"]), ""]
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--n-iter", type=int, default=10_000)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    t = correr(a.n_iter, a.seed)
    RESULTS.mkdir(exist_ok=True)
    for k, df in t.items():
        df.to_csv(RESULTS / f"robustez_extra_{k}.csv", index=False)
    texto = relatorio_md(t, a.n_iter, a.seed)
    (RESULTS / "robustez_extra.md").write_text(texto, encoding="utf-8")
    print(f"Gravado {RESULTS / 'robustez_extra.md'}")


if __name__ == "__main__":
    main()
