"""Testes de scripts/estilo_graficos.py."""

import importlib.util
from pathlib import Path

import pytest

CAMINHO = Path(__file__).resolve().parents[1] / "scripts" / "estilo_graficos.py"
spec = importlib.util.spec_from_file_location("estilo_graficos", CAMINHO)
eg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eg)


def test_numero_usa_virgula_e_espaco_fino():
    assert eg.numero(0.5104, 3) == "0,510"
    assert eg.numero(10000, 0) == "10 000"
    assert eg.numero(-1.5, 1) == "−1,5"


def test_virgula_formata_eixo():
    assert eg.virgula(1, " %")(12.34, None) == "12,3 %"


def test_aplicar_carrega_inter_e_temas():
    t = eg.aplicar("escura")
    import matplotlib.pyplot as plt
    assert plt.rcParams["font.family"] == ["Inter"]
    assert t["texto"] == eg.TINTA["escura"]["texto"]
    with pytest.raises(ValueError):
        eg.aplicar("azul")


def test_gravar_cria_tres_formatos(tmp_path):
    import matplotlib.pyplot as plt
    eg.aplicar()
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    eg.rotulo(ax, 1, 1, "Ti-6Al-4V", "#0072B2")
    caminhos = eg.gravar(fig, "teste", tmp_path)
    assert {p.suffix for p in caminhos} == {".svg", ".pdf", ".png"} and all(p.exists() for p in caminhos)
