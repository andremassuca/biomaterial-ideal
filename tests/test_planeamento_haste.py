"""Testes de scripts/planeamento_haste.py (só a regra de escolha; o resto precisa da malha anatómica)."""

import importlib.util
from pathlib import Path

CAMINHO = Path(__file__).resolve().parents[1] / "scripts" / "planeamento_haste.py"
spec = importlib.util.spec_from_file_location("planeamento_haste", CAMINHO)
plan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plan)


def _r(t, A, frac, folga):
    return {"tamanho": t, "A": A, "fracao_dentro": frac, "folga_minima": folga}


def test_escolhe_o_maior_que_cabe_com_folga():
    res = [_r(8, 115, 1.0, 4.0), _r(9, 130, 1.0, 2.5), _r(10, 140, 1.0, 1.0), _r(11, 145, 0.97, -1.0)]
    assert plan.escolher_tamanho(res)["tamanho"] == 9


def test_sem_nenhum_que_caiba_fica_o_de_maior_folga():
    res = [_r(8, 115, 0.99, -0.5), _r(9, 130, 0.95, -2.0)]
    assert plan.escolher_tamanho(res)["tamanho"] == 8


def test_contorno_denso_tem_passo_pedido():
    p = plan.contorno_denso([(0, 0), (10, 0)], 1.0)
    assert len(p) == 10 and p[-1][0] == 9


def test_cotas_do_tamanho_usam_catalogo_e_encolhem_larguras():
    base = {"haste_largura_ombro": 30.0, "haste_largura_ponta": 9.0, "haste_espessura": 14.0, "haste_espessura_ponta": 7.0,
            "haste_ccd": 135}
    c = plan.cotas_do_tamanho(base, 115, 93, 38.3, 39)
    assert (c["haste_comprimento"], c["haste_comprimento_b"], c["haste_offset"], c["haste_colo"]) == (115, 93, 38.3, 39)
    assert c["haste_largura_ombro"] == 23.0 and c["haste_espessura_ponta"] == 5.4
