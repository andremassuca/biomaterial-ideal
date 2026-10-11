"""Testes de src/biomat_mcdm/perfis.py (regras de data/perfis_doente.csv)."""
import json

import numpy as np
import pandas as pd
import pytest

from biomat_mcdm.io import build_problem, load_parametros
from biomat_mcdm import perfis as pf

FADIGA = "Resistência à fadiga a 10⁷ ciclos (σmax, R = 0,1)"


def test_ler_regras_tem_as_44_regras_e_colunas():
    r = pf.ler_regras()
    assert len(r) == 44
    assert {"id", "dispositivo", "condicao_codigo", "efeito", "alvo_do_efeito", "valor", "fonte",
            "doi_url", "estado"} <= set(r.columns)
    assert set(r["dispositivo"]) <= set(pf.CASOS.values())


@pytest.mark.parametrize("codigo, perfil, esperado", [
    ("idade<60; atividade=alta", {"idade": 40, "atividade": "alta"}, True),
    ("idade<60; atividade=alta", {"idade": 60, "atividade": "alta"}, False),
    ("idade<60; atividade=alta", {"idade": 40}, False),           # dado em falta: não se verifica
    ("imc>=35", {"imc": 35}, True),
    ("imc>=35", {"imc": "34,9"}, False),                          # vírgula decimal
    ("vaso_mm<3.0", {"vaso_mm": 2.75}, True),
    ("osteoporose=sim", {"osteoporose": "Sim"}, True),
    ("defeito=com_carga", {"defeito": "sem_carga"}, False),
    ("gengiva_mm<2", {"gengiva_mm": 2}, False),
])
def test_condicao_cumprida(codigo, perfil, esperado):
    assert pf.condicao_cumprida(codigo, perfil) is esperado


def test_condicao_ilegivel_ou_nao_numerica_da_erro():
    with pytest.raises(ValueError):
        pf.condicao_cumprida("idade ~ 60", {"idade": 3})
    with pytest.raises(ValueError):
        pf.condicao_cumprida("idade<60", {"idade": "jovem"})


def test_regras_ativas_so_do_dispositivo_e_sem_regra_para_o_sexo():
    r = pf.regras_ativas("Haste", {"idade": 40, "atividade": "alta", "alergia_niquel": "sim"})
    assert list(r["id"]) == ["H-JOV"]  # alergia ao níquel é regra do stent, não da haste
    assert pf.regras_ativas("Haste", {"sexo": "F"}).empty
    assert pf.regras_ativas("Haste", {"sexo": "M", "idade": 80}).empty


def test_perfil_vazio_da_o_ranking_de_referencia():
    for caso, nome in pf.CASOS.items():
        res = pf.avaliar_perfil(caso, {})
        base = build_problem(nome, "A")
        assert res.regras.empty and not res.excluidos and not res.notas
        np.testing.assert_allclose(res.problema.weights, base.weights)


def test_peso_multiplicado_e_renormalizado():
    base = build_problem(pf.CASOS["Haste"], "A")
    res = pf.avaliar_perfil("Haste", {"idade": 40, "atividade": "alta"})
    j = base.criteria.index(FADIGA)
    w = base.weights.copy()
    w[j] *= 2
    np.testing.assert_allclose(res.problema.weights, w / w.sum())
    assert res.problema.weights.sum() == pytest.approx(1)


def test_varias_regras_no_mesmo_criterio_usam_o_maior_fator():
    """H-JOV e H-IMC sobem ambas a fadiga: fator 2, não 4."""
    so_um = pf.avaliar_perfil("Haste", {"idade": 40, "atividade": "alta"})
    dois = pf.avaliar_perfil("Haste", {"idade": 40, "atividade": "alta", "imc": 38})
    assert list(dois.regras["id"]) == ["H-JOV", "H-IMC"]
    np.testing.assert_allclose(dois.problema.weights, so_um.problema.weights)


def test_multiplicar_pesos_valida():
    base = build_problem(pf.CASOS["Haste"], "A")
    with pytest.raises(ValueError):
        pf.multiplicar_pesos(base, {"Critério inexistente": 2})
    with pytest.raises(ValueError):
        pf.multiplicar_pesos(base, {FADIGA: 0})


def test_niquel_entra_com_peso_020_mesmo_com_outra_regra():
    base = build_problem(pf.CASOS["Stent"], "A")
    s1 = pf.avaliar_perfil("Stent", {"alergia_niquel": "sim"})
    p = s1.problema
    assert p.criteria[-1] == "Teor de níquel" and p.types[-1] == "cost" and p.targets[-1] is None
    assert p.weights[-1] == pytest.approx(0.20)
    np.testing.assert_allclose(p.weights[:-1], base.weights * 0.80)
    # valores da base (materiais.csv): Pt-Cr 9 %, MP35N típico entre 33 e 37 %
    i = p.alternatives.index("Pt-Cr")
    assert p.X[i, -1] == pytest.approx(9.0)
    assert p.X_min.shape == p.X_max.shape == p.X.shape
    s2 = pf.avaliar_perfil("Stent", {"alergia_niquel": "sim", "vaso_mm": 2.5})
    assert s2.problema.weights[-1] == pytest.approx(0.20)
    assert s2.problema.weights.sum() == pytest.approx(1)


def test_niquel_no_cenario_b_funciona_com_zero_no_plla_e_no_mg():
    """PLLA e Mg WE43 sem níquel (0 %): o WASPAS usa a eq. 11 com T = 0 e o perfil funciona no cenário B."""
    r = pf.avaliar_perfil("Stent", {"alergia_niquel": "sim"}, cenario="B")
    p = r.problema
    j = p.criteria.index("Teor de níquel")
    assert p.weights[j] == pytest.approx(0.20)
    sem_ni = [a for a, v in zip(p.alternatives, p.X_tipico[:, j]) if v == 0]
    assert set(sem_ni) == {"PLLA (bioabsorvível)", "Liga de Mg WE43 (bioabsorvível)"}
    assert np.isfinite(r.ranking.select_dtypes("number").to_numpy(float)).all()


def test_acrescentar_criterio_valida_o_peso():
    base = build_problem(pf.CASOS["Stent"], "A")
    with pytest.raises(ValueError):
        pf.acrescentar_criterio(base, "Stent", "Teor de níquel", "cost", 1.0)


def test_titanio_so_excluido_com_alergia_confirmada():
    conf = pf.avaliar_perfil("Implante dentário", {"alergia_titanio_confirmada": "sim"})
    assert sorted(conf.excluidos) == ["Ti cp grau 4", "Ti-6Al-4V ELI", "Ti-Zr (~15% Zr)"]
    assert set(conf.problema.alternatives) == {"Zircónia Y-TZP", "PEEK"}
    susp = pf.avaliar_perfil("Implante dentário", {"hipersens_titanio_suspeita": "sim"})
    assert not susp.excluidos
    assert susp.notas == ["recomenda-se avaliação clínica; testes pouco fiáveis"]
    ref = pf.avaliar_perfil("Implante dentário", {})
    pd.testing.assert_frame_equal(susp.ranking, ref.ranking)


def test_excluir_nao_deixa_menos_de_dois():
    base = build_problem(pf.CASOS["Implante dentário"], "A")
    with pytest.raises(ValueError):
        pf.excluir(base, base.alternatives[1:])
    p, sai = pf.excluir(base, ["Material que não existe"])
    assert sai == [] and p.alternatives == base.alternatives


def test_leitura_do_problema_do_scaffold_igual_ao_p_foco():
    from biomat_mcdm.io import criterios_do_problema
    from biomat_mcdm.robustness import com_foco
    nome = pf.CASOS["Scaffold"]
    base = build_problem(nome, "A")
    fator = load_parametros()["fator_foco_problema"]
    for perfil, lig in (("com_carga", ("direta", "indireta")), ("sem_carga", ("direta",))):
        res = pf.avaliar_perfil("Scaffold", {"defeito": perfil})
        esperado = com_foco(base, criterios_do_problema(nome, lig), fator)
        np.testing.assert_allclose(res.problema.weights, esperado.weights)


def test_valor_da_leitura_igual_ao_fator_foco_problema():
    r = pf.ler_regras()
    fator = load_parametros()["fator_foco_problema"]
    assert (r[r["efeito"] == "leitura do problema"]["valor"].astype(float) == fator).all()


def test_efeito_desconhecido_da_erro():
    base = build_problem(pf.CASOS["Haste"], "A")
    regras = pd.DataFrame([{"id": "X", "efeito": "inventado", "alvo_do_efeito": FADIGA, "valor": "2"}])
    with pytest.raises(ValueError):
        pf.aplicar_regras(base, "Haste", regras)


def test_caso_desconhecido_da_erro():
    with pytest.raises(ValueError):
        pf.avaliar_perfil("Joelho", {})


def test_tabela_referencia():
    t = pf.tabela_referencia()
    assert list(dict.fromkeys(t["perfil"])) == list(pf.PERFIS_REFERENCIA)
    for pid, g in t.groupby("perfil"):
        m = len(g)
        for k in ("TOPSIS", "WASPAS", "VIKOR", "Borda"):
            assert set(g[f"pos_{k}"]) <= set(range(1, m + 1))
        pesos = json.loads(g["pesos"].iloc[0])
        assert sum(pesos.values()) == pytest.approx(1, abs=1e-8)
    assert t[t["perfil"] == "D3"]["material"].tolist() == ["Zircónia Y-TZP", "PEEK"]
    assert set(t[t["perfil"] == "S1"]["regras"]) == {"S-NI"}
    # o ranking de referência (pos_ref_*) é o do perfil vazio
    ref = pf.avaliar_perfil("Haste", {}).ranking.set_index("material")["pos_TOPSIS"]
    h1 = t[t["perfil"] == "H1"].set_index("material")["pos_ref_TOPSIS"]
    assert (h1 == ref.loc[h1.index]).all()
