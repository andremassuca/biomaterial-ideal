"""Corre o funil de triagem e grava results/funil.csv e results/funil.md.

Uso: python scripts/funil.py [--mp PASTA]

Lê o resumo do Materials Project (dados abertos no AWS, CC BY 4.0; descarregado para
recursos\\materials_project por scripts/obter_recursos.py), a tabela dos elementos
(data/funil/elementos.csv), as normas ASTM (data/funil/normas.csv), os filtros (data/funil/filtros.csv) e a
base verificada (data/materiais.csv). As propriedades do Materials Project são calculadas e só servem para
filtrar.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from biomat_mcdm import funil as fn  # noqa: E402
from biomat_mcdm.io import DATA  # noqa: E402

MP_PASTA = Path(r"recursos\materials_project")
VERSAO_MP = "2026-09-28"
RESULTS = RAIZ / "results"


def ler_mp(pasta: Path = MP_PASTA, versao: str = VERSAO_MP) -> pd.DataFrame:
    """Lê o resumo do Materials Project e devolve as colunas do funil (sem as entradas obsoletas)."""
    import pyarrow.parquet as pq
    cols = ["material_id", "formula_pretty", "elements", "energy_above_hull", "density", "bulk_modulus",
            "shear_modulus", "deprecated"]
    t = pq.read_table(pasta / f"summary_{versao}.parquet", columns=cols).to_pandas()
    t = t[~t["deprecated"].fillna(False)]

    def vrh(x):
        return dict(x).get("vrh") if x is not None and not isinstance(x, float) else None

    return pd.DataFrame({
        "material_id": t["material_id"], "formula": t["formula_pretty"],
        "elementos": [list(e) for e in t["elements"]], "e_hull": t["energy_above_hull"],
        "densidade": t["density"], "k_vrh": [vrh(x) for x in t["bulk_modulus"]],
        "g_vrh": [vrh(x) for x in t["shear_modulus"]],
    }).reset_index(drop=True)


def correr(mp: pd.DataFrame, data: Path = DATA) -> dict:
    """Corre os três níveis e devolve as tabelas (contagem do MP, elementos, normas, base verificada)."""
    elementos = pd.read_csv(data / "funil" / "elementos.csv", dtype=str).fillna("")
    normas = pd.read_csv(data / "funil" / "normas.csv", dtype=str).fillna("")
    excluidos = fn.elementos_excluidos(elementos)
    final, contagem = fn.aplicar_filtros(mp, excluidos, fn.ler_filtros(data / "funil" / "filtros.csv"))
    base = fn.base_verificada(pd.read_csv(data / "materiais.csv"))
    return {"contagem": contagem, "final": final, "excluidos": excluidos, "elementos": elementos,
            "normas": normas, "base": base}


def escrever(r: dict, destino: Path = RESULTS) -> None:
    """Grava results/funil.csv (contagem por nível e etapa) e results/funil.md (resumo legível)."""
    destino.mkdir(exist_ok=True)
    n_base = int(r["base"]["n"].sum())
    linhas = [*r["contagem"].itertuples(index=False),
              (1, "Elementos avaliados", len(r["elementos"])),
              (1, "Normas ASTM de materiais para implantes", len(r["normas"])),
              (3, "Base verificada (materiais por componente)", n_base),
              (3, "Recomendação (um material por dispositivo)", 5)]
    tab = pd.DataFrame(linhas, columns=["nivel", "etapa", "n"])
    tab.to_csv(destino / "funil.csv", index=False)
    md = ["# Funil de triagem", "",
          f"Gerado por scripts/funil.py. Materials Project: versão {VERSAO_MP} dos dados abertos (CC BY 4.0); "
          "propriedades calculadas (DFT), usadas só para filtrar.", "",
          "| Nível | Etapa | N |", "|---|---|---|"]
    md += [f"| {a} | {b} | {c:,} |".replace(",", " ") for a, b, c in linhas]  # etapas sem vírgulas
    md += ["", "Elementos excluídos e motivo:", ""]
    md += [f"- {s}: {m}" for s, m in sorted(r["excluidos"].items())]
    md += ["", "Base verificada por componente:", ""]
    md += [f"- {c} | {k}: {n}" for c, k, n in r["base"].itertuples(index=False)]
    (destino / "funil.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mp", type=Path, default=MP_PASTA)
    a = ap.parse_args()
    r = correr(ler_mp(a.mp))
    escrever(r)
    print(r["contagem"].to_string(index=False))


if __name__ == "__main__":
    main()
