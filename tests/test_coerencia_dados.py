"""Coerência física da base de dados (data/materiais.csv).

Em linguagem simples: em cada material, a tensão de cedência não pode passar da resistência à tração (o material
cede antes de partir), e em cada valor o mínimo, o típico e o máximo têm de estar por ordem.
"""

import pandas as pd
import pytest

from biomat_mcdm.io import DATA

MAT = pd.read_csv(DATA / "materiais.csv")


def _pares_cedencia_tracao():
    chave = ["caso", "componente", "material"]
    ced = MAT[MAT["propriedade"] == "Tensão de cedência"].set_index(chave)
    tra = MAT[MAT["propriedade"] == "Resistência à tração"].set_index(chave)
    comuns = ced.index.intersection(tra.index)
    return [(k, ced.loc[k], tra.loc[k]) for k in comuns]


@pytest.mark.parametrize("chave,ced,tra", _pares_cedencia_tracao(), ids=lambda v: " | ".join(v) if isinstance(v, tuple) else "")
def test_cedencia_nao_passa_da_tracao(chave, ced, tra):
    if pd.isna(ced["tipico"]) or pd.isna(tra["tipico"]):
        pytest.skip("sem valor típico")
    assert ced["tipico"] <= tra["tipico"], (
        f"{chave}: cedência típica {ced['tipico']} MPa acima da tração típica {tra['tipico']} MPa")
    if not pd.isna(ced["min"]) and not pd.isna(tra["max"]):
        assert ced["min"] <= tra["max"], f"{chave}: cedência mínima acima da tração máxima"


def test_minimo_tipico_maximo_por_ordem():
    num = MAT[["min", "tipico", "max"]].apply(pd.to_numeric, errors="coerce")
    fora = MAT[(num["min"] > num["max"] + 1e-9) | (num["tipico"] < num["min"] - 1e-9) | (num["tipico"] > num["max"] + 1e-9)]
    assert fora.empty, fora[["material", "propriedade", "min", "tipico", "max"]].to_string()
