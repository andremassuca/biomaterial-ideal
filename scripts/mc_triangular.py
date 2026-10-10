"""Sensibilidade do Monte Carlo das propriedades à distribuição: uniforme contra triangular.

Corre o Monte Carlo das propriedades (cenário A) nos três casos quantitativos com a distribuição
uniforme (a do resultado principal) e com a triangular (mínimo, típico, máximo), com a mesma
semente e a mesma incerteza dos valores únicos, e grava:
  results/mc_triangular.csv   % de 1.º lugar por caso, método, material e distribuição
  results/mc_triangular.md    vencedor mais frequente e % de 1.º lugar, lado a lado
Uso: python scripts/mc_triangular.py [--n-iter 10000] [--seed 42]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_all import BASE, CASOS, RESULTS  # noqa: E402

from biomat_mcdm.io import DATA, build_problem, load_parametros  # noqa: E402
from biomat_mcdm.pipeline import METODOS, fmt_pt  # noqa: E402
from biomat_mcdm.robustness import monte_carlo, pct_primeiro  # noqa: E402

DISTRIBUICOES = {"uniform": "uniforme", "triangular": "triangular (mín., típico, máx.)"}


def comparacao(n_iter: int = 10_000, seed: int = 42, data_dir: Path = DATA) -> pd.DataFrame:
    """% de 1.º lugar de cada material, por caso, método e distribuição (cenário A).

    Em linguagem simples: repete o Monte Carlo das propriedades com as duas formas de sortear os
    valores e conta quantas vezes cada material fica em 1.º, para ver se o vencedor depende da
    distribuição escolhida.
    """
    inc = load_parametros(data_dir).get("incerteza_valor_unico", 0.0)
    linhas = []
    for caso, nome in CASOS.items():
        p = build_problem(nome, BASE, data_dir)
        for metodo in METODOS:
            for dist in DISTRIBUICOES:
                r = monte_carlo(p, metodo, n_iter, seed, dist=dist, incerteza_valor_unico=inc)
                for mat, pct in zip(p.alternatives, pct_primeiro(r)):
                    linhas.append({"caso": caso, "metodo": metodo, "distribuicao": dist, "material": mat,
                                   "pct_primeiro": pct, "n_iter": n_iter, "seed": seed})
    return pd.DataFrame(linhas)


def resumo_md(df: pd.DataFrame) -> str:
    """Tabela markdown: material mais vezes em 1.º e a sua %, uniforme ao lado da triangular."""
    n_iter, seed = int(df["n_iter"].iloc[0]), int(df["seed"].iloc[0])
    out = ["# Monte Carlo das propriedades: uniforme contra triangular", "",
           f"Cenário A, {n_iter} iterações, seed {seed}; mesma incerteza dos valores únicos do resultado principal.",
           "", "| Caso | Método | Uniforme | Triangular (mín., típico, máx.) |", "|---|---|---|---|"]
    for (caso, metodo), g in df.groupby(["caso", "metodo"], sort=False):
        celulas = []
        for dist in DISTRIBUICOES:
            h = g[g["distribuicao"] == dist].sort_values("pct_primeiro", ascending=False).iloc[0]
            celulas.append(f"{h['material']} ({fmt_pt(h['pct_primeiro'], 1)} %)")
        out.append(f"| {caso} | {metodo} | {celulas[0]} | {celulas[1]} |")
    return "\n".join(out) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-iter", type=int, default=10_000)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    df = comparacao(a.n_iter, a.seed)
    df.to_csv(RESULTS / "mc_triangular.csv", index=False)
    (RESULTS / "mc_triangular.md").write_text(resumo_md(df), encoding="utf-8")
    print(resumo_md(df))


if __name__ == "__main__":
    main()
