"""Testes do preenchimento dos números da CFD no relatório."""
import importlib.util
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("preencher", RAIZ / "scripts" / "preencher_cfd_relatorio.py")
pc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pc)

V = {"poiseuille": {"erro_perfil_max": 0.0149, "erro_tau": 0.0024, "erro_dp": 0.0044},
     "malha_max_variacao_area": 0.0148, "passo_variacao_area": 0.004, "ciclos_max": 0.012,
     "pulsatil": {"Pt-Cr": {"espessura_um": 79.0, "tau_media": 0.41, "fracao_baixa": 0.46, "osi_media": 0.012},
                  "316L": {"espessura_um": 135.0, "tau_media": 0.23, "fracao_baixa": 0.81, "osi_media": 0.031}}}


def test_marcas_com_virgula_e_valores():
    m = pc.textos(V)
    assert m["@@CFD_POIS_PERFIL@@"] == "1,5" and m["@@CFD_POIS_TAU@@"] == "0,24"
    assert m["@@CFD_PASSO@@"] == "0,4" and m["@@CFD_CICLOS@@"] == "1,2"
    assert "46 %" in m["@@CFD_RESULTADOS@@"] and "81 %" in m["@@CFD_RESULTADOS@@"]
    assert "Table: " in m["@@CFD_RESULTADOS@@"]
    assert m["@@CFD_DISC@@"].endswith("316L.")


def test_preencher_troca_todas_as_marcas():
    texto = "erro de @@CFD_POIS_PERFIL@@ % e @@CFD_DISC@@"
    out = pc.preencher(texto, pc.textos(V))
    assert "@@" not in out and "1,5 %" in out
