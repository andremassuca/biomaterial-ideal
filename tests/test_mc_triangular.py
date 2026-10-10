import importlib.util
from pathlib import Path

import pytest

CAMINHO = Path(__file__).resolve().parents[1] / "scripts" / "mc_triangular.py"
spec = importlib.util.spec_from_file_location("mc_triangular", CAMINHO)
mt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mt)


@pytest.fixture(scope="module")
def df():
    return mt.comparacao(n_iter=50, seed=1)


def test_comparacao_tem_as_duas_distribuicoes_e_percentagens_validas(df):
    assert set(df["distribuicao"]) == {"uniform", "triangular"}
    assert set(df["caso"]) == set(mt.CASOS)
    # em cada caso, método e distribuição, as % de 1.º lugar somam pelo menos 100 (empates contam para todos)
    soma = df.groupby(["caso", "metodo", "distribuicao"])["pct_primeiro"].sum()
    assert (soma >= 100 - 1e-9).all()


def test_resumo_md_tem_uma_linha_por_caso_e_metodo(df):
    texto = mt.resumo_md(df)
    linhas = [l for l in texto.splitlines() if l.startswith("| ") and not l.startswith("| Caso")]
    assert len(linhas) == 3 * 3
    assert "Uniforme" in texto and "Triangular" in texto
