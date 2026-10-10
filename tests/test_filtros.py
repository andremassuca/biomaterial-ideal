"""Testes de src/biomat_mcdm/filtros.py (filtros de RM e ISO 10993-1 e cenário da esterilização)."""
import pandas as pd
import pytest

from biomat_mcdm import filtros as fl


@pytest.fixture(scope="module")
def tabela():
    return fl.ler_filtros_material()


def test_tabela_cobre_todos_os_materiais_da_base(tabela):
    m = pd.read_csv(fl.DATA / "materiais.csv")
    assert set(tabela.index) == set(m["material"])
    for col in ("ferromagnetico", "vapor", "oxido_etileno", "radiacao_gama"):
        assert set(tabela[col]) <= {"sim", "não", "compatível", "incompatível", "com restrições", "A verificar"}


def test_filtro_rm():
    t = pd.DataFrame({"ferromagnetico": ["sim", "não", "A verificar"]}, index=["a", "b", "c"])
    assert fl.filtro_rm(["a", "b", "c", "d"], t) == {"a": "exclui", "b": "passa", "c": "A verificar",
                                                    "d": "A verificar"}


def test_filtro_rm_nao_exclui_ninguem_na_base(tabela):
    assert "exclui" not in fl.filtro_rm(list(tabela.index), tabela).values()


def test_filtro_iso10993_nao_exclui():
    r = fl.filtro_iso10993({"x": "Clínico (uso limitado)", "y": "Investigação", "z": "Descontinuado (Absorb, 2017)",
                            "w": "Excluído (autoexpansível: só discussão)"})
    assert r == {"x": "avaliada em dispositivos clínicos", "y": "por demonstrar no dispositivo final",
                 "z": "avaliada em dispositivos clínicos", "w": "fora do ranking"}


def test_incompativeis_e_metodo_desconhecido(tabela):
    assert "PCL" in fl.incompativeis(["PCL", "Ti cp grau 4"], tabela, "vapor")
    assert fl.incompativeis(["PCL", "Ti cp grau 4"], tabela, "radiacao_gama") == []
    with pytest.raises(ValueError):
        fl.incompativeis(["PCL"], tabela, "plasma")


def test_cenario_esterilizacao_scaffold_a_vapor():
    r = fl.cenario_esterilizacao("Scaffold", "vapor", "A")
    assert "Compósito PCL/β-TCP (impressão 3D)" in r["saem"]
    assert r["antes"]["TOPSIS"] == "Compósito PCL/β-TCP (impressão 3D)"
    assert r["depois"]["WASPAS"] == "β-TCP poroso"


def test_cenario_sem_incompativeis_nao_muda():
    r = fl.cenario_esterilizacao("Haste", "radiacao_gama", "A")
    assert r["saem"] == [] and r["depois"] == r["antes"]


def test_filtros_md_tem_as_duas_partes():
    md = fl.filtros_md()
    assert "## RM (ASTM F2503) e ISO 10993-1" in md and "## Esterilização imposta (sensibilidade)" in md
    assert "—" not in md
