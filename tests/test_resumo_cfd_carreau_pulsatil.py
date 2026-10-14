"""Testes de scripts/resumo_cfd_carreau_pulsatil.py (funções puras e ficheiro de resultados gravado)."""
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
import resumo_cfd_carreau_pulsatil as rc  # noqa: E402


def _caso(tau, frac, esp=79.0):
    return {"espessura_um": esp, "tau_media": tau, "fracao_baixa": frac}


def test_comparar_diferencas():
    r = rc.comparar(_caso(0.4, 0.5), _caso(0.5, 0.4))
    assert r["dif_fracao_pp"] == pytest.approx(-10.0)
    assert r["dif_tau_rel"] == pytest.approx(0.25)
    assert r["newtoniano"] == {"tau_media": 0.4, "fracao_baixa": 0.5}
    assert r["carreau"]["fracao_baixa"] == 0.4


def test_ordem_mantida_deteta_inversao():
    casos = {"Pt-Cr": rc.comparar(_caso(0.4, 0.5), _caso(0.5, 0.4)),
             "316L": rc.comparar(_caso(0.2, 0.8, 135), _caso(0.3, 0.7, 135))}
    assert rc.ordem_mantida(casos, "fracao_baixa", "carreau") and rc.ordem_mantida(casos, "tau_media", "newtoniano")
    casos["316L"]["carreau"]["fracao_baixa"] = 0.3  # o grosso passaria a ter menos área de corte baixo
    assert not rc.ordem_mantida(casos, "fracao_baixa", "carreau")


def test_ficheiro_gravado_tem_os_dois_materiais_e_ordem_mantida():
    d = json.loads(rc.DESTINO.read_text(encoding="utf-8"))
    assert set(d["casos"]) == {"Pt-Cr", "316L"} and d["limiar_pa"] == 0.4 and d["ordem_mantida"] is True
