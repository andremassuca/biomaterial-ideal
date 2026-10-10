"""Testes das funções de dados de scripts/graficos.py."""

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

CAMINHO = Path(__file__).resolve().parents[1] / "scripts" / "graficos.py"
spec = importlib.util.spec_from_file_location("graficos", CAMINHO)
gr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gr)


def test_dados_espectro_calcula_delta_c():
    pt = pd.DataFrame({"caso": ["Stent"] * 3, "cenario": ["A"] * 3, "material": ["a", "b", "c"],
                       "C_TOPSIS": [0.60, 0.70, 0.65]})
    d = gr.dados_espectro(pt)
    assert d.iloc[0]["vencedor"] == "b" and d.iloc[0]["delta_c"] == pytest.approx(0.05)


def test_dados_mc_stent_ordena_por_topsis():
    mc = pd.DataFrame({"caso": ["Stent"] * 6, "analise": ["MC propriedades"] * 6,
                       "metodo": ["TOPSIS", "WASPAS", "VIKOR"] * 2, "material": ["x"] * 3 + ["y"] * 3,
                       "pct_primeiro": [70, 60, 65, 30, 40, 35]})
    d = gr.dados_mc_stent(mc)
    assert list(d.index) == ["y", "x"] and list(d.columns) == ["TOPSIS", "WASPAS", "VIKOR"]


def test_espalhar_afasta_rotulos_proximos():
    e = gr.espalhar({"a": 0.50, "b": 0.505, "c": 0.70}, 0.02)
    assert e["b"] - e["a"] >= 0.02 - 1e-12 and e["c"] > e["b"]


def _tab_funil():
    etapas = [e for e, _ in gr.ETAPAS_FUNIL]
    return pd.DataFrame({"nivel": [1, 2, 2, 2, 3, 3], "etapa": etapas, "n": [271325, 200000, 120000, 6000, 30, 5]})


def test_dados_funil_larguras_decrescem_e_terminam_em_5():
    d = gr.dados_funil(_tab_funil())
    assert d["n"].tolist()[-1] == 5 and d["largura"].iloc[0] == pytest.approx(1.0)
    assert (d["largura"].diff().dropna() < 0).all()


@pytest.mark.parametrize("tema", ["clara", "escura"])
def test_fig_funil_desenha(tema):
    fig = gr.fig_funil(_tab_funil(), tema)
    textos = [t.get_text() for t in fig.axes[0].texts]
    assert gr.eg.numero(271325, 0) in textos and "5" in textos
    gr.plt.close(fig)


def test_sem_titulo_tira_so_os_textos_da_figura():
    fig = gr.fig_funil(_tab_funil(), "clara")
    n_ax = len(fig.axes[0].texts)
    assert len(fig.texts) == 2
    gr.sem_titulo(fig)
    assert len(fig.texts) == 0 and len(fig.axes[0].texts) == n_ax
    gr.plt.close(fig)
