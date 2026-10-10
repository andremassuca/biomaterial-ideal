import importlib.util
from pathlib import Path

import numpy as np
import pytest

CAMINHO = Path(__file__).resolve().parents[1] / "scripts" / "animacoes.py"
spec = importlib.util.spec_from_file_location("animacoes", CAMINHO)
an = importlib.util.module_from_spec(spec)
spec.loader.exec_module(an)


def test_alvo_haste_ordena_pela_nota_e_usa_o_alvo_da_base():
    df, alvo, (o_min, o_max) = an.dados_alvo_haste()
    assert alvo == 17
    assert o_min <= alvo <= o_max
    assert list(df["nota"]) == sorted(df["nota"], reverse=True)
    assert df["nota"].between(0, 1).all()
    # a mais próxima do alvo tem a melhor nota
    assert df.iloc[0]["E_tip"] == df["E_tip"].min()


def test_mc_acumulado_termina_na_percentagem_de_1_lugar():
    alts, acum = an.mc_acumulado("Stent", n_iter=40, seed=1)
    from biomat_mcdm.robustness import monte_carlo, pct_primeiro
    p = an.problema("Stent")
    r = monte_carlo(p, "TOPSIS", 40, 1, incerteza_valor_unico=an.incerteza())
    assert np.allclose(acum["TOPSIS"][-1], pct_primeiro(r))
    assert acum["WASPAS"].shape == (40, len(alts))


def test_gibson_ashby_e_porosidade_do_alvo():
    E_s, alvo = an.modulo_e_alvo_haste()
    p = an.porosidade_para(alvo, E_s)
    assert an.gibson_ashby(p, E_s) == pytest.approx(alvo)
    assert round(100 * p, 1) == 59.9
    assert an.gibson_ashby(0, E_s) == pytest.approx(E_s)


def test_leituras_scaffold_dao_o_resultado_do_relatorio():
    lt = an.leituras_scaffold()
    for leitura, esperado in (("ampla", "Compósito PCL/β-TCP (impressão 3D)"), ("literal", "β-TCP poroso")):
        d = lt[leitura]
        assert d.loc[d["TOPSIS"].idxmax(), "material"] == esperado
        assert d.loc[d["VIKOR"].idxmin(), "material"] == esperado
    assert lt["literal"].loc[lt["literal"]["WASPAS"].idxmax(), "material"] == "Compósito PCL/β-TCP (impressão 3D)"


def test_vencedores_eta_nos_extremos():
    v = an.vencedores_eta(np.array([0.0, 1.0]))
    um = v[v["eta"] == 1.0].set_index(["caso", "metodo"])["vencedor"]
    assert um[("Haste", "TOPSIS")] == "Ti-6Al-4V ELI"
    assert um[("Stent", "TOPSIS")] == "Pt-Cr" and um[("Stent", "WASPAS")] == "Co-Cr L605"
    zero = v[v["eta"] == 0.0].set_index(["caso", "metodo"])["vencedor"]
    assert zero[("Haste", "VIKOR")] == "Ti cp grau 4"


def test_mc_pontuacoes_haste_tem_o_ti64_quase_sempre_a_frente():
    alts, s = an.mc_pontuacoes_haste(n_iter=50, seed=42)
    assert s.shape == (50, len(alts))
    assert (s.argmax(axis=1) == alts.index("Ti-6Al-4V ELI")).mean() >= 0.98


def test_varrimento_peso_no_peso_do_trabalho_reproduz_o_cenario_a():
    from biomat_mcdm.robustness import pontuacoes
    p = an.problema("Stent")
    w0 = float(p.weights[p.criteria.index(an.CRIT_STRUT)])
    alts, sc, w = an.varrimento_peso("Stent", an.CRIT_STRUT, np.array([0.0, w0, 0.5]))
    assert w == pytest.approx(w0)
    assert np.allclose(sc["TOPSIS"][1], pontuacoes(p.X, p.weights, p.types, p.targets, "TOPSIS"))


def test_cruzamentos_por_interpolacao():
    x = np.array([0.0, 1.0, 2.0])
    assert an.cruzamentos(x, np.array([0, 2, 2]), np.array([1, 1, 1])) == [pytest.approx(0.5)]
    assert an.cruzamentos(x, np.array([3, 3, 3]), np.array([1, 1, 1])) == []


def test_limiar_porosidade_da_a_fracao_de_vazio_pedida():
    campo, _ = an.campo_giroide(n=24)
    for p in (0.3, 0.6):
        assert (campo > an.limiar_porosidade(campo, p)).mean() == pytest.approx(p, abs=0.01)
    assert (campo > an.limiar_porosidade(campo, 0.0)).mean() == 0


def test_indices_recuo_e_tempos_de_degradacao_vem_da_base():
    idx = an.indices_recuo(["Pt-Cr", "Co-Cr L605", "Aço inox 316L"])
    assert idx["Pt-Cr"] > idx["Co-Cr L605"] > idx["Aço inox 316L"] > 0
    T, ref = an.tempos_degradacao(["β-TCP poroso", "Compósito PCL/β-TCP (impressão 3D)"])
    assert ref == 9
    assert T["β-TCP poroso"] < T["Compósito PCL/β-TCP (impressão 3D)"]


def test_massa_restante_linear_e_limitada():
    assert an.massa_restante(0, 12) == 100
    assert an.massa_restante(6, 12) == pytest.approx(50)
    assert an.massa_restante(30, 12) == 0


def test_malha_stent_mantem_o_comprimento_dos_struts():
    for raio in (0.5, 1.2):
        anel = an.malha_stent(raio)[0]
        seg = np.linalg.norm(np.diff(anel, axis=0), axis=1)
        # corda entre pico e vale: aproxima o comprimento do strut (o arco é ligeiramente maior que a corda)
        assert seg.max() == pytest.approx(0.62, rel=0.05)


def test_iteracoes_ate_cresce_ate_ao_total():
    assert an.iteracoes_ate(0, 1, 2, 100) == 1
    assert an.iteracoes_ate(5, 1, 2, 100) == 100
