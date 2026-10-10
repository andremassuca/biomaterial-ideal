"""Testes de scripts/geometria_3d.py (o script carrega-se pelo caminho)."""

import importlib.util
from pathlib import Path

import numpy as np
import pytest

CAMINHO = Path(__file__).resolve().parents[1] / "scripts" / "geometria_3d.py"
spec = importlib.util.spec_from_file_location("geometria_3d", CAMINHO)
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


def test_giroide_e_zero_na_origem_e_periodico():
    assert g.campo_giroide(0, 0, 0) == pytest.approx(0)
    assert g.campo_giroide(0.3, 0.1, 0.7, 2.0) == pytest.approx(g.campo_giroide(2.3, 0.1, 2.7, 2.0))


def test_porosidade_com_limiar_zero_e_metade():
    assert g.porosidade_giroide(0.0) == pytest.approx(0.5, abs=0.01)


def test_porosidade_cresce_com_o_limiar():
    valores = [g.porosidade_giroide(t, 32) for t in (-0.8, -0.3, 0.0, 0.3, 0.8)]
    assert valores == sorted(valores)


def test_limiar_para_porosidade_inverte_a_porosidade():
    for p in (0.3, 0.6, 0.8):
        assert g.porosidade_giroide(g.limiar_para_porosidade(p)) == pytest.approx(p, abs=0.01)


def test_limiar_para_porosidade_recusa_fora_do_intervalo():
    with pytest.raises(ValueError):
        g.limiar_para_porosidade(0.99)


def test_rede_stent_fica_no_cilindro_e_no_comprimento():
    linhas = g.rede_stent(raio=1.5, comprimento=18, n_coroas=8, n_picos=6)
    pts = np.vstack(linhas)
    assert np.allclose(np.hypot(pts[:, 0], pts[:, 1]), 1.5)
    assert pts[:, 2].min() >= 0 and pts[:, 2].max() <= 18
    # 8 anéis e 3 pontes entre cada par de anéis vizinhos
    assert len(linhas) == 8 + 7 * 3


def test_rede_stent_recusa_poucas_coroas():
    with pytest.raises(ValueError):
        g.rede_stent(1.5, 18, 1, 6)


def test_perfil_balao_tem_cilindro_e_acaba_no_cateter():
    p = g.perfil_balao(raio=1.6, comprimento=20, cone=3, raio_cateter=0.4)
    assert p[0, 0] == pytest.approx(0.4) and p[-1, 0] == pytest.approx(0.4)
    assert p[0, 1] == pytest.approx(-3) and p[-1, 1] == pytest.approx(23)
    assert p[:, 0].max() == pytest.approx(1.6)
    assert np.all(np.diff(p[:, 1]) > 0)


def test_rede_stent_sem_folga_e_so_aneis_em_losango():
    linhas = g.rede_stent(raio=1.5, comprimento=16, n_coroas=8, n_picos=6, folga=0)
    assert len(linhas) == 8
    # o topo de um anel toca na base do seguinte
    assert linhas[0][:, 2].max() == pytest.approx(linhas[1][:, 2].min())


def test_rede_stent_recusa_folga_invalida():
    with pytest.raises(ValueError):
        g.rede_stent(1.5, 16, 8, 6, folga=1.0)


def test_ajustar_esfera_recupera_centro_e_raio():
    rng = np.random.default_rng(1)
    d = rng.normal(size=(200, 3))
    d /= np.linalg.norm(d, axis=1)[:, None]
    c, r = g.ajustar_esfera(np.array([10, -5, 3]) + 22.8 * d)
    assert np.allclose(c, [10, -5, 3]) and r == pytest.approx(22.8)


def test_eixo_principal_aponta_para_cima():
    t = np.linspace(-50, 50, 101)
    pts = np.c_[0.1 * t, np.zeros_like(t), -t]
    c, e = g.eixo_principal(pts)
    assert np.allclose(c, 0, atol=1e-9) and e[2] > 0
    assert abs(e @ np.array([0.1, 0, -1]) / np.linalg.norm([0.1, 0, -1])) == pytest.approx(1)


def test_colocar_haste_poe_a_cabeca_no_centro_anatomico():
    H = np.array([-87.2, -78.9, 811.4])
    C0, a = np.array([-90.8, -81.0, 567.9]), np.array([-0.111, 0.018, 0.994])
    T, s, m = g.colocar_haste(H, C0, a)
    assert np.linalg.norm(s) == pytest.approx(1) and np.linalg.norm(m) == pytest.approx(1)
    assert s @ m == pytest.approx(0, abs=1e-12)
    assert np.allclose(T + 140 * s + 41 * m, H)
    # a ponta fica no eixo do canal
    v = T - C0
    a_u = a / np.linalg.norm(a)
    assert np.linalg.norm(v - (v @ a_u) * a_u) == pytest.approx(0, abs=1e-9)


def test_colocar_haste_recusa_canal_longe_da_cabeca():
    with pytest.raises(ValueError):
        g.colocar_haste([500, 0, 0], [0, 0, 0], [0, 0, 1])


def _quadrado():
    v = np.array([[0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0], [0, 0, 10], [10, 0, 10], [10, 10, 10], [0, 10, 10]], float)
    f = np.array([[0, 1, 2], [0, 2, 3], [4, 6, 5], [4, 7, 6], [0, 4, 5], [0, 5, 1], [1, 5, 6], [1, 6, 2],
                  [2, 6, 7], [2, 7, 3], [3, 7, 4], [3, 4, 0]])
    return v, f


def test_ler_obj(tmp_path):
    p = tmp_path / "t.obj"
    p.write_text("# c\nv 0 0 0\nv 1 0 0\nv 1 1 0\nv 0 1 0\nf 1 2 3 4\n", encoding="utf-8")
    v, f = g.ler_obj(p)
    assert v.shape == (4, 3) and f.tolist() == [[0, 1, 2], [0, 2, 3]]


def test_cortar_malha_e_dentro_da_seccao():
    v, f = _quadrado()
    segs = g.cortar_malha(v, f, (0, 1, 0), (0, 5, 0))
    s2 = segs[:, :, [0, 2]]
    assert len(segs) > 0 and np.allclose(segs[:, :, 1], 5)
    dentro = g.dentro_da_seccao([[5, 5], [12, 5], [0.5, 9.5]], s2)
    assert dentro.tolist() == [True, False, True]
    assert g.distancia_aos_segmentos([[5, 5]], s2)[0] == pytest.approx(5)
