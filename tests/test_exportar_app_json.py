"""Testes de scripts/exportar_app_json.py e scripts/referencias_rust.py (carregados pelo caminho)."""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from biomat_mcdm.io import build_problem

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _carregar(nome):
    spec = importlib.util.spec_from_file_location(nome, SCRIPTS / f"{nome}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ex = _carregar("exportar_app_json")
rr = _carregar("referencias_rust")


def test_nome_ficheiro_sem_acentos():
    assert ex.nome_ficheiro("Implante dentário") == "caso_implante_dentario.json"
    assert ex.nome_ficheiro("Par articular") == "caso_par_articular.json"
    assert rr.nome_ficheiro("Stent", "A") == "referencia_stent_A.json"


def test_problema_json_igual_ao_build_problem():
    p = build_problem("Stent vascular", "B")
    d = ex.problema_json(p)
    assert d["alternativas"] == p.alternatives and d["tipos"] == p.types
    np.testing.assert_allclose(d["x_tipico"], p.X)
    np.testing.assert_allclose(d["pesos"], p.weights)
    assert d["alvos"][d["criterios"].index("Tempo de reabsorção")] == 12
    assert d["ordinal"][d["criterios"].index("Radiopacidade (ordinal 1-5)")] is True


def test_caso_json_do_stent_tem_niquel_regras_e_perfis():
    d = ex.caso_json("Stent")
    assert set(d["cenarios"]) == {"A", "B"}
    assert d["propriedades_extra"]["Teor de níquel"]["Pt-Cr"]["tipico"] == pytest.approx(9.0)
    assert {r["id"] for r in d["regras"]} == {"S-NI", "S-VASO", "S-DIAB", "S-RM", "S-CO", "S-CO-NOTA", "S-IRC", "S-IDOSO"}
    assert set(d["perfis_referencia"]) == {"S1", "S2"}
    assert d["parametros"]["fator_foco_problema"] == 2.0
    json.dumps(d)  # tem de ser serializável (sem NaN)


def test_exportar_grava_um_ficheiro_por_caso(tmp_path):
    caminhos = ex.exportar(tmp_path)
    assert len(caminhos) == 5
    d = json.loads((tmp_path / "caso_scaffold.json").read_text(encoding="utf-8"))
    assert "Porosidade" in d["problemas_criticos"]["direta"]


def test_referencia_tem_metodos_e_monte_carlo():
    r = rr.referencia("Stent vascular", "A", n_iter=5)
    assert len(r["C_TOPSIS"]) == len(r["alternativas"]) == 4
    assert r["monte_carlo"]["n_iter"] == 5
    assert sum(r["monte_carlo"]["propriedades_TOPSIS"]["pct_primeiro"]) >= 100 - 1e-9
    assert sum(r["pesos_objetivos"]) == pytest.approx(1)


def test_gerar_grava_seis_referencias(tmp_path):
    assert len(rr.gerar(n_iter=3, saida=tmp_path)) == 6


# ------------------------------------------------------------------ dados extra da interface (app.json)

def test_nomes_json_tem_nome_e_codigo():
    n = ex.nomes_json()
    assert n["Ti-6Al-4V ELI"] == {"nome": "Liga de titânio", "codigo": "Ti-6Al-4V"}
    assert n["Pt-Cr"]["nome"] == "Platina-crómio"


def test_fichas_json_tem_fonte_e_estado_sem_nan():
    f = ex.fichas_json()
    linha = next(r for r in f["materiais"] if r["material"] == "Aço inox 316L" and r["propriedade"] == "Módulo de Young")
    assert linha["estado"] and linha["referencia"]
    assert any(r["tecido"] == "Osso cortical" for r in f["tecido"])
    json.dumps(f, allow_nan=False)


def test_filtros_json_tem_rm_iso_e_esterilizacao():
    f = ex.filtros_json()
    por_material = {r["material"]: r for r in f["materiais"]}
    assert por_material["Aço inox 316L"]["rm"] == "passa"
    assert por_material["PLLA"]["iso10993"] == "por demonstrar no dispositivo final"
    assert set(f["metodos"]) == {"vapor", "oxido_etileno", "radiacao_gama"}
    vapor_stent_b = [r for r in f["esterilizacao"] if r["caso"] == "Stent" and r["cenario"] == "B" and r["metodo"] == "vapor"]
    assert vapor_stent_b and vapor_stent_b[0]["muda"]


def test_espectro_json_ordenado_pelo_delta_c():
    e = ex.espectro_json()
    assert {c["caso"] for c in e} == {"Haste", "Stent", "Scaffold", "Par articular", "Implante dentário"}
    assert [c["delta_c"] for c in e] == sorted((c["delta_c"] for c in e), reverse=True)
    haste = next(c for c in e if c["caso"] == "Haste")
    assert haste["vencedor"] == "Ti-6Al-4V ELI" and 0 <= haste["pct_primeiro_min"] <= haste["pct_primeiro_max"] <= 100
    semi = next(c for c in e if c["caso"] == "Par articular")
    assert semi["semiquantitativo"] and semi["versoes_mantem"] <= semi["versoes_total"]


def test_fea_json_tem_zonas_1_e_7_e_comparacao():
    f = ex.fea_json()
    assert f is not None and {z["zona"] for z in f["zonas"]} == {1, 7}
    intacto = [z for z in f["zonas"] if z["material"] == "Fémur intacto"]
    assert all(z["razao"] == pytest.approx(1.0) for z in intacto) and intacto[0]["material_base"] is None
    assert any(z["material_base"] == "Ti-6Al-4V ELI" for z in f["zonas"])
    assert {c["material"] for c in f["comparacao"]} >= {"Ti-6Al-4V ELI", "Aço inox 316L"}
    assert ex.fea_json(Path("pasta_que_nao_existe")) is None


def test_massa_json_volume_e_desvio():
    m = ex.massa_json()
    assert m is not None
    for r in m["materiais"]:
        assert r["massa_g"] == pytest.approx(m["volume_cm3"] * r["densidade_g_cm3"])
    assert m["desvio_max_mm"] == pytest.approx(m["diferenca_g"] / 1000 * m["distancia_max_m"] / m["massa_corpo_kg"] * 1000)


def test_cfd_json_none_sem_resultados(tmp_path):
    assert ex.cfd_json(tmp_path) is None
    (tmp_path / "cfd_pulsatil.json").write_text('{"Pt-Cr": {"espessura_um": 79}}', encoding="utf-8")
    assert ex.cfd_json(tmp_path)["Pt-Cr"]["espessura_um"] == 79


def test_cfd_carreau_json_valores_do_relatorio_v11_1(tmp_path):
    assert ex.cfd_carreau_json(tmp_path) is None
    c = ex.cfd_carreau_json()["casos"]
    assert c["Pt-Cr"]["espessura_um"] == 79 and c["316L"]["espessura_um"] == 135
    assert round(100 * c["Pt-Cr"]["carreau"]["fracao_baixa"], 1) == 36.8
    assert round(100 * c["316L"]["carreau"]["fracao_baixa"], 1) == 69.2
    assert round(100 * c["Pt-Cr"]["newtoniano"]["fracao_baixa"], 1) == 46.5
    assert round(100 * c["316L"]["newtoniano"]["fracao_baixa"], 1) == 82.1
    assert round(c["Pt-Cr"]["carreau"]["tau_media"], 3) == 0.508
    assert round(c["316L"]["carreau"]["tau_media"], 3) == 0.296
    # o caso newtoniano é o mesmo da CFD principal
    for mat, r in ex.cfd_json().items():
        assert c[mat]["newtoniano"]["fracao_baixa"] == pytest.approx(r["fracao_baixa"])
        assert c[mat]["newtoniano"]["tau_media"] == pytest.approx(r["tau_media"])


def test_micromovimento_json_valores_do_relatorio_v11_1(tmp_path):
    assert ex.micromovimento_json(tmp_path) is None
    m = ex.micromovimento_json()
    assert m["limiar_um"] == 150 and m["mu"] == 0.4 and m["outras_variantes"] == 4
    assert round(m["principal"]["max_um"], 1) == 65.7
    assert round(m["principal"]["mediana_um"], 1) == 35.2
    assert m["principal"]["fracao_acima_limiar"] == 0 and m["outras_fracao_acima_limiar_max"] == 0
    assert round(m["outras_max_min_um"], 1) == 63.9 and round(m["outras_max_max_um"], 1) == 99.1


def test_app_json_e_exportar_extras(tmp_path):
    d = ex.app_json()
    assert set(d) >= {"nomes", "fichas", "filtros", "espectro", "limiar_empate", "fea", "massa", "textos",
                      "cfd_carreau", "micromovimento"}
    json.dumps(d, allow_nan=False)
    caminhos = ex.exportar_extras(tmp_path)
    assert caminhos[0].name == "app.json" and caminhos[0].exists()


def test_registos_troca_nan_por_none():
    import pandas as pd
    assert ex._registos(pd.DataFrame({"a": [1.0, float("nan")]})) == [{"a": 1.0}, {"a": None}]
