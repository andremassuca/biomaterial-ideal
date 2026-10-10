"""Gera os ficheiros de referência (JSON) contra os quais se testa o núcleo Rust (app-nativa/crates/mcdm).

Para a haste, o stent e o scaffold, nos cenários A e B: pontuações dos três métodos (C, Q, S,
R e P), posições, consenso de Borda, pesos objetivos do desvio-padrão e pesos com η = 0,5, e
o Monte Carlo (propriedades e pesos) com N_ITER iterações. Os perfis de doente testam-se
contra results/perfis_referencia.csv (scripts/run_all.py).

Uso: python scripts/referencias_rust.py [--n-iter 10000]
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np

from biomat_mcdm.io import DATA, build_problem, load_parametros
from biomat_mcdm.methods.vikor import vikor
from biomat_mcdm.pipeline import METODOS, consenso_borda, rank_all_methods
from biomat_mcdm.robustness import com_eta, monte_carlo, pct_primeiro
from biomat_mcdm.weights import std_dev_weights

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "app-nativa" / "crates" / "mcdm" / "tests" / "referencias"
CASOS = {"Haste": "Prótese da anca | Haste femoral", "Stent": "Stent vascular",
         "Scaffold": "Scaffold (regeneração óssea)"}
CENARIOS = ("A", "B")
ETA_TESTE = 0.5
SPREAD = 0.2  # W pesos ±20 % (como em scripts/run_all.py)


def referencia(nome: str, cenario: str, n_iter: int, seed: int = 42, data_dir: Path = DATA) -> dict:
    """Valores de referência de um caso e cenário, como dicionário pronto para JSON.

    Em linguagem simples: corre em Python tudo o que o Rust também calcula (os três métodos,
    o consenso, os pesos objetivos e o Monte Carlo) e guarda os números para os comparar.
    """
    p = build_problem(nome, cenario, data_dir)
    df = consenso_borda(rank_all_methods(p))
    v = vikor(p.X, p.weights, p.types, p.targets)
    out = {"caso_componente": nome, "cenario": cenario, "alternativas": list(p.alternatives),
           "C_TOPSIS": df["C_TOPSIS"].tolist(), "Q_WASPAS": df["Q_WASPAS"].tolist(),
           "S_VIKOR": v["S"].tolist(), "R_VIKOR": v["R"].tolist(), "P_VIKOR": df["P_VIKOR"].tolist(),
           **{f"pos_{m}": df[f"pos_{m}"].astype(int).tolist() for m in [*METODOS, "Borda"]},
           "pontos_Borda": df["pontos_Borda"].astype(int).tolist()}
    try:
        out["pesos_objetivos"] = std_dev_weights(p.X, p.types).tolist()
        pe = com_eta(p, ETA_TESTE)
        r = rank_all_methods(pe)
        out["eta"] = {"eta": ETA_TESTE, "pesos": pe.weights.tolist(), "C_TOPSIS": r["C_TOPSIS"].tolist(),
                      "Q_WASPAS": r["Q_WASPAS"].tolist(), "P_VIKOR": r["P_VIKOR"].tolist()}
    except ValueError:
        out["pesos_objetivos"] = None  # ex.: valores nulos, que o desvio-padrão aqui não aceita
        out["eta"] = None
    inc = load_parametros(data_dir).get("incerteza_valor_unico", 0.0)
    mc = {"n_iter": n_iter, "seed": seed, "incerteza_valor_unico": inc, "spread": SPREAD}
    for variar in ("propriedades", "pesos"):
        for m in METODOS:
            r = monte_carlo(p, m, n_iter, seed, variar=variar, spread=SPREAD, incerteza_valor_unico=inc)
            mc[f"{variar}_{m}"] = {"pct_primeiro": pct_primeiro(r).tolist(),
                                   "posicao_media": r.mean(axis=0).tolist()}
    out["monte_carlo"] = mc
    return out


def nome_ficheiro(caso: str, cenario: str) -> str:
    """Nome do ficheiro de referência, ex.: referencia_stent_A.json."""
    return f"referencia_{re.sub(r'[^a-z0-9]+', '_', caso.lower())}_{cenario}.json"


def gerar(n_iter: int = 10_000, saida: Path = SAIDA, data_dir: Path = DATA) -> list[Path]:
    """Grava as referências dos casos e cenários em `saida`; devolve os caminhos."""
    saida.mkdir(parents=True, exist_ok=True)
    caminhos = []
    for caso, nome in CASOS.items():
        for c in CENARIOS:
            f = saida / nome_ficheiro(caso, c)
            f.write_text(json.dumps(referencia(nome, c, n_iter, data_dir=data_dir), ensure_ascii=False, indent=1),
                         encoding="utf-8")
            caminhos.append(f)
    return caminhos


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--n-iter", type=int, default=10_000)
    for f in gerar(ap.parse_args().n_iter):
        print(f.relative_to(RAIZ))


if __name__ == "__main__":
    main()
