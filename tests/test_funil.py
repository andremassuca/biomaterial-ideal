"""Testes de src/biomat_mcdm/funil.py (funil de triagem em três níveis)."""
import numpy as np
import pandas as pd
import pytest

from biomat_mcdm import funil as fn

FILTROS = {"e_hull_max": 0.025, "densidade_max": 17, "modulo_min": 10, "modulo_max": 450}


def test_modulo_young_formula_e_casos_invalidos():
    # K = G: E = 9G²/(4G) = 2,25 G
    assert fn.modulo_young(100, 100) == pytest.approx(225.0)
    e = fn.modulo_young([100, np.nan, 50, 80], [100, 30, -5, 0])
    assert e[0] == pytest.approx(225.0)
    assert np.isnan(e[1:]).all()


def test_ler_filtros_do_repositorio():
    f = fn.ler_filtros()
    assert set(FILTROS) <= set(f)
    assert f["modulo_min"] < f["modulo_max"]


def test_elementos_excluidos_motivos():
    el = pd.DataFrame({
        "simbolo": ["U", "Cd", "Be", "Ni", "Ti"],
        "radioativo": ["sim", "não", "não", "não", "não"],
        "classe_ich_q3d": ["", "1", "", "2A", ""],
        "iarc_elemento": ["", "1", "1", "2B", ""],
    })
    m = fn.elementos_excluidos(el)
    assert set(m) == {"U", "Cd", "Be"}
    assert m["Cd"] == "ICH Q3D classe 1; IARC grupo 1"
    assert "Ni" not in m  # o níquel metálico é 2B: não elimina


def _mp():
    return pd.DataFrame({
        "material_id": list("abcdef"),
        "formula": ["TiO2", "CdTe", "Al2O3", "WC", "Fe", "Os"],
        "elementos": [["Ti", "O"], ["Cd", "Te"], ["Al", "O"], ["W", "C"], ["Fe"], ["Os"]],
        "e_hull": [0.0, 0.0, 0.01, 0.0, 0.1, 0.0],
        "densidade": [4.2, 5.9, 4.0, 15.6, 7.9, 22.6],
        "k_vrh": [200, 40, 250, 400, 170, 400],
        "g_vrh": [110, 20, 160, 280, 80, 270],
    })


def test_aplicar_filtros_contagens_por_etapa():
    d, c = fn.aplicar_filtros(_mp(), {"Cd"}, FILTROS)
    assert c["n"].tolist() == [6, 5, 4, 3, 3, 2]
    assert c["nivel"].tolist() == [1, 2, 2, 2, 2, 2]
    assert sorted(d["formula"]) == ["Al2O3", "TiO2"]  # WC sai pelo módulo (> 450 GPa)
    assert (d["modulo"] > 0).all()


def test_aplicar_filtros_sem_dados_elasticos():
    mp = _mp().assign(k_vrh=np.nan)
    d, c = fn.aplicar_filtros(mp, set(), FILTROS)
    assert len(d) == 0 and c["n"].iloc[-1] == 0


def test_base_verificada_conta_materiais_distintos():
    m = pd.DataFrame({"caso": ["A", "A", "A", "B"], "componente": ["x", "x", "x", "y"],
                      "material": ["m1", "m1", "m2", "m3"]})
    b = fn.base_verificada(m)
    assert b.set_index("componente")["n"].to_dict() == {"x": 2, "y": 1}


def test_script_funil_corre_e_escreve(tmp_path):
    import importlib.util
    from pathlib import Path
    raiz = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("funil_script", raiz / "scripts" / "funil.py")
    sc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sc)
    data = tmp_path / "data"
    (data / "funil").mkdir(parents=True)
    pd.DataFrame({"simbolo": ["Cd", "Ti"], "radioativo": ["não", "não"], "classe_ich_q3d": ["1", ""],
                  "iarc_elemento": ["1", ""]}).to_csv(data / "funil" / "elementos.csv", index=False)
    pd.DataFrame({"norma": ["ASTM F67", "ASTM F136"]}).to_csv(data / "funil" / "normas.csv", index=False)
    (data / "funil" / "filtros.csv").write_text(
        "parametro,valor\ne_hull_max,0.025\ndensidade_max,17\nmodulo_min,10\nmodulo_max,450\n", encoding="utf-8")
    pd.DataFrame({"caso": ["A"] * 3, "componente": ["x"] * 3, "material": ["m1", "m2", "m2"]}).to_csv(
        data / "materiais.csv", index=False)
    r = sc.correr(_mp(), data)
    assert r["excluidos"] == {"Cd": "ICH Q3D classe 1; IARC grupo 1"}
    sc.escrever(r, tmp_path / "results")
    tab = pd.read_csv(tmp_path / "results" / "funil.csv")
    assert tab["n"].tolist() == [6, 5, 4, 3, 3, 2, 2, 2, 2, 5]
    md = (tmp_path / "results" / "funil.md").read_text(encoding="utf-8")
    assert "| 1 | Materials Project (todos os compostos) | 6 |" in md and "- Cd: ICH Q3D classe 1" in md


def test_ler_mp_tira_obsoletos_e_le_vrh(tmp_path):
    import importlib.util
    from pathlib import Path
    import pyarrow as pa
    import pyarrow.parquet as pq
    raiz = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("funil_script2", raiz / "scripts" / "funil.py")
    sc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sc)
    t = pa.table({
        "material_id": ["a", "b"], "formula_pretty": ["TiO2", "Fe"], "elements": [["Ti", "O"], ["Fe"]],
        "energy_above_hull": [0.0, 0.0], "density": [4.2, 7.9],
        "bulk_modulus": [{"voigt": 1.0, "reuss": 1.0, "vrh": 200.0}, None],
        "shear_modulus": [{"voigt": 1.0, "reuss": 1.0, "vrh": 110.0}, None],
        "deprecated": [False, True]})
    pq.write_table(t, tmp_path / "summary_v.parquet")
    mp = sc.ler_mp(tmp_path, "v")
    assert mp["material_id"].tolist() == ["a"]
    assert mp.loc[0, "k_vrh"] == 200.0 and mp.loc[0, "elementos"] == ["Ti", "O"]
