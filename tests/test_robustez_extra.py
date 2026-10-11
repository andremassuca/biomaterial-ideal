"""Testes de src/biomat_mcdm/robustez_extra.py (retirar uma alternativa, dimensões, ajuste mínimo)."""
import numpy as np
import pandas as pd
import pytest

from biomat_mcdm import robustez_extra as rx
from biomat_mcdm.io import DATA, DecisionProblem, build_problem


def problema(X, types, weights, criteria=None, alts=None, targets=None):
    """Problema pequeno com valores fixos (mín. = máx. = típico)."""
    X = np.asarray(X, float)
    m, n = X.shape
    return DecisionProblem(alternatives=alts or [f"M{i}" for i in range(m)],
                           criteria=criteria or [f"c{j}" for j in range(n)],
                           X_min=X.copy(), X_max=X.copy(), X_tipico=X.copy(), types=list(types),
                           targets=targets or [None] * n, weights=np.asarray(weights, float))


SIMETRICO = problema([[2, 1], [1, 2]], ["benefit", "benefit"], [0.6, 0.4], alts=["A", "B"])


def test_merito_vikor_troca_o_sinal():
    p = SIMETRICO
    for m in rx.METODOS:
        assert int(np.argmax(rx.merito(p, m))) == 0  # A é o melhor nos três métodos
    assert rx.merito(p, "VIKOR")[0] == pytest.approx(0.0)


def test_folga():
    assert rx.folga(np.array([0.5, 0.2, 0.45]), 0) == pytest.approx(0.05)
    assert rx.folga(np.array([0.5, 0.2, 0.45]), 1) == pytest.approx(-0.3)


def test_retirar_alternativa():
    p = problema([[1], [2], [3]], ["benefit"], [1.0])
    q = rx.retirar_alternativa(p, "M1")
    assert q.alternatives == ["M0", "M2"]
    assert q.X[:, 0].tolist() == [1.0, 3.0]


def test_pares_trocados():
    alts = ["a", "b", "c"]
    assert rx.pares_trocados(alts, {"a": 3, "b": 2, "c": 1}, {"a": 3, "b": 2, "c": 1}) == []
    assert rx.pares_trocados(alts, {"a": 3, "b": 2, "c": 1}, {"a": 1, "b": 2, "c": 3}) == [
        ("a", "b"), ("a", "c"), ("b", "c")]
    assert rx.pares_trocados(alts, {"a": 2, "b": 2, "c": 1}, {"a": 1, "b": 2, "c": 0}) == []  # empate antes


def test_reversao_com_um_criterio_nunca_muda():
    p = problema([[1], [4], [2], [3]], ["benefit"], [1.0])
    r = rx.reversao_ranking(p)
    assert len(r) == 4 * 3 and not r["alterado"].any()


def test_reversao_no_stent_real():
    r = rx.reversao_ranking(build_problem("Stent vascular", "A"))
    t = r[(r["retirado"] == "Aço inox 316L") & (r["metodo"] == "TOPSIS")].iloc[0]
    assert t["alterado"] and "Pt-Cr ↔ Co-Cr L605" in t["pares"]
    assert t["vencedor_antes"] == "Pt-Cr" and t["vencedor_depois"] == "Co-Cr L605"


def test_dimensoes_cobrem_todos_os_criterios_dos_casos_quantitativos():
    crit = pd.read_csv(DATA / "criterios.csv")
    dims = pd.read_csv(DATA / "dimensoes_criterios.csv")
    assert set(dims["dimensao"]) <= {"mecânica", "biológica", "clínica", "económica"}
    assert dims["nota"].notna().all()
    for caso in ("Prótese da anca | Haste femoral", "Stent vascular", "Scaffold (regeneração óssea)"):
        c = crit[(crit["caso_componente"] == caso) & (crit["tipo"] != "Estrito")]
        assert set(dims[dims["caso"] == caso]["criterio"]) == set(c["criterio"])
        for cen in ("A", "B"):
            p = build_problem(caso, cen)
            g = rx.grupos_dimensao(p.criteria, rx.carregar_dimensoes(caso))
            assert sorted(j for idx in g.values() for j in idx) == list(range(len(p.criteria)))


def test_grupos_dimensao_falha_sem_dimensao():
    with pytest.raises(ValueError):
        rx.grupos_dimensao(["a", "b"], {"a": "mecânica"})


def test_pesos_iguais_na_dimensao():
    w = rx.pesos_iguais_na_dimensao(np.array([0.1, 0.3, 0.6]), {"x": [0, 1], "y": [2]})
    assert w.tolist() == pytest.approx([0.2, 0.2, 0.6])


def test_sortear_na_dimensao_mantem_o_total_de_cada_dimensao():
    rng = np.random.default_rng(0)
    w0 = np.array([0.1, 0.3, 0.2, 0.4])
    g = {"x": [0, 1], "y": [2], "z": [3]}
    for _ in range(20):
        w = rx.sortear_na_dimensao(w0, g, rng)
        assert w[[0, 1]].sum() == pytest.approx(0.4) and w[2] == 0.2 and w[3] == 0.4
        assert (w >= 0).all()


def test_dupla_contagem_com_alternativa_dominante_mantem_sempre():
    p = problema([[3, 3, 3], [1, 2, 1], [2, 1, 2]], ["benefit"] * 3, [0.3, 0.3, 0.4])
    d = rx.dupla_contagem(p, {"c0": "mecânica", "c1": "mecânica", "c2": "clínica"}, n_iter=200)
    assert (d["pct_mantem"] == 100).all() and (d["vencedor_iguais"] == "M0").all()
    assert (d["outro_vencedor"] == "").all()


def test_dupla_contagem_pesos_iguais_trocam_o_vencedor():
    # A ganha porque c0 pesa mais do que c1 na mesma dimensão; com pesos iguais fica empate (fica A, o 1.º índice)
    # e com c1 a pesar mais ganha B: o Monte Carlo dá cerca de metade das vezes a cada um
    d = rx.dupla_contagem(SIMETRICO, {"c0": "mecânica", "c1": "mecânica"}, n_iter=2000, seed=1)
    t = d.set_index("metodo")
    assert 40 < t.loc["TOPSIS", "pct_mantem"] < 60
    assert t.loc["TOPSIS", "outro_vencedor"] == "B"


def test_menor_variacao():
    assert rx.menor_variacao(lambda d: d >= 0.237, 1.0) == pytest.approx(0.237, abs=2e-4)
    assert rx.menor_variacao(lambda d: d <= -0.1, -1.0) == pytest.approx(-0.1, abs=2e-4)
    assert rx.menor_variacao(lambda d: False, 0.5) is None
    assert rx.menor_variacao(lambda d: d >= 0.5, 0.5) == pytest.approx(0.5)


def test_ajuste_minimo_pesos_caso_simetrico():
    # X simétrico: troca quando os dois pesos ficam iguais (0,5): c0 de 0,6 para 0,5 (-16,7 %), c1 de 0,4 para 0,5 (+25 %)
    a = rx.ajuste_minimo_pesos(SIMETRICO)
    for m in rx.METODOS:
        r0 = a[(a["criterio"] == "c0") & (a["metodo"] == m)].iloc[0]
        r1 = a[(a["criterio"] == "c1") & (a["metodo"] == m)].iloc[0]
        assert r0["var"] == pytest.approx(-1 / 6, abs=1e-3) and r0["novo_vencedor"] == "B"
        assert r1["var"] == pytest.approx(0.25, abs=1e-3)
    t = a[(a["criterio"] == "c0") & (a["metodo"] == "TOPSIS")].iloc[0]
    assert -1 / 6 < t["var_empate"] < 0  # o empate (ΔC < 0,01) chega antes da troca
    assert a[a["metodo"] != "TOPSIS"]["var_empate"].isna().all()


def test_ajuste_minimo_valores_quantitativo_e_ordinal():
    p = problema([[10, 5], [8, 3]], ["benefit", "benefit"], [0.5, 0.5],
                 criteria=["Resistência", "Bioatividade (ordinal 1-5)"], alts=["A", "B"])
    a = rx.ajuste_minimo_valores(p)
    ordn = a[(a["criterio"] == "Bioatividade (ordinal 1-5)") & (a["metodo"] == "WASPAS")].set_index("material")
    assert ordn["ordinal"].all()
    assert ordn.loc["B", "var"] is None or pd.isna(ordn.loc["B", "var"])  # B não passa de 5: não chega para trocar
    assert ordn.loc["A", "pontos"] in (-2, -3, -4)  # passos inteiros
    q = a[(a["criterio"] == "Resistência") & (a["metodo"] == "TOPSIS")].set_index("material")
    assert not q["ordinal"].any() and pd.isna(q.loc["A", "pontos"])
    v = q.loc["A", "var"]
    assert pd.isna(v) or -0.5 <= v < 0  # A domina: pode não trocar até -50 %


def test_ajuste_minimo_valores_um_criterio_resultado_conhecido():
    p = problema([[10], [8]], ["benefit"], [1.0], alts=["A", "B"])
    a = rx.ajuste_minimo_valores(p).set_index(["material", "metodo"])
    for m in rx.METODOS:
        assert a.loc[("A", m), "var"] == pytest.approx(-0.2, abs=2e-4)   # 10 -> abaixo de 8
        assert a.loc[("B", m), "var"] == pytest.approx(0.25, abs=2e-4)   # 8 -> acima de 10
    o = problema([[5], [3]], ["benefit"], [1.0], criteria=["Nota (ordinal 1-5)"], alts=["A", "B"])
    b = rx.ajuste_minimo_valores(o).set_index(["material", "metodo"])
    assert b.loc[("A", "TOPSIS"), "pontos"] == -3 and b.loc[("A", "TOPSIS"), "var"] == pytest.approx(-0.6)
    assert pd.isna(b.loc[("B", "TOPSIS"), "pontos"])  # 3 + 2 = 5 só empata; não troca


def test_mais_sensiveis_ordena_pelo_menor_valor_absoluto():
    aj = pd.DataFrame({"criterio": ["a", "a", "b", "b", "c"], "metodo": ["TOPSIS", "VIKOR", "TOPSIS", "VIKOR", "TOPSIS"],
                       "peso": [0.2, 0.2, 0.3, 0.3, 0.5], "var": [0.4, -0.1, None, 0.05, None],
                       "novo_vencedor": ["X", "Y", None, "Z", None]})
    s = rx.mais_sensiveis(aj, ["criterio"])
    assert s["criterio"].tolist() == ["b", "a", "c"]
    assert s.loc[0, "metodos"] == "VIKOR" and s.loc[1, "var_min"] == pytest.approx(-0.1)
    assert s.loc[2, "var_min"] is None or pd.isna(s.loc[2, "var_min"])


def test_fmt_var():
    assert rx.fmt_var(0.123, 0.5) == "+12,3 %"
    assert rx.fmt_var(-0.2, 0.5, -1) == "-1 ponto (-20,0 %)"
    assert rx.fmt_var(-0.6, 0.5, -3.0) == "-3 pontos (-60,0 %)"
    assert rx.fmt_var(None, 0.5) == "não troca até ±50 %"
    assert rx.fmt_var(float("nan"), 1.0) == "não troca até ±100 %"


def test_referencia_curta():
    assert rx.referencia_curta("Navarro M, Michiardi A, Castaño O. Biomaterials. J R Soc Interface 2008;5") == "Navarro et al. 2008"
    assert rx.referencia_curta("Okazaki Y. Materials 2012;5:1439") == "Okazaki 2012"
    assert rx.referencia_curta("Alleima, ficha 316LVM (tubo)") == "Alleima"
    assert rx.referencia_curta("FDA 510(k) K120152 (Cerasorb Plus); FDA") == "FDA 510(k) K120152"
    assert rx.referencia_curta(float("nan")) == "sem referência"


def test_fontes_celulas_tem_estado_para_os_valores_do_problema():
    f = rx.fontes_celulas("Stent vascular")
    p = build_problem("Stent vascular", "A")
    chaves = set(zip(f["material"], f["propriedade"]))
    assert all((a, c) in chaves for a in p.alternatives for c in p.criteria)
    assert f["estado"].notna().all()
