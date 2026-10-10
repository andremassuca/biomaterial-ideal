"""Testes de scripts/nomes_simples.py e scripts/animacoes_diap.py."""
import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]


def _carregar(nome):
    spec = importlib.util.spec_from_file_location(nome, RAIZ / "scripts" / f"{nome}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nome] = mod
    spec.loader.exec_module(mod)
    return mod


ns = _carregar("nomes_simples")
ad = _carregar("animacoes_diap")


def test_todos_os_materiais_da_base_tem_nome_simples():
    m = set(pd.read_csv(RAIZ / "data" / "materiais.csv")["material"])
    assert m <= set(ns.NOMES)


def test_nomes_definidos_pelo_andre():
    assert ns.com_codigo("Ti-6Al-4V ELI") == "Liga de titânio (Ti-6Al-4V)"
    assert ns.com_codigo("Compósito PCL/β-TCP (impressão 3D)") == "Polímero com cerâmica (PCL/β-TCP)"
    assert ns.com_codigo("ZTA / ZTA (CoC)") == "Cerâmica contra cerâmica (ZTA)"
    assert ns.com_codigo("Ti cp grau 4") == "Titânio puro (grau 4)"
    assert ns.nome("desconhecido") == "desconhecido" and ns.codigo("desconhecido") == ""


def test_rotulo_material_em_duas_linhas():
    assert ad.rotulo_material("Pt-Cr") == "Platina-crómio\nPt-Cr"


@pytest.mark.parametrize("nome", list(ad.ANIMACOES))
def test_animacoes_diap_dao_imagens_1920x1080(nome):
    frame = next(ad.ANIMACOES[nome](50))
    assert frame.shape == (1080, 1920, 3)
