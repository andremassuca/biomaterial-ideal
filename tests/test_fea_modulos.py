"""Testes rápidos dos módulos da FEA (malhas pequenas, sem o fémur)."""

import numpy as np
import pytest

pytest.importorskip("skfem")

from biomat_mcdm.fea import cargas, geometria, gruen, malha, materiais, posproc, solver  # noqa: E402


# ---------------------------------------------------------------- materiais

def test_materiais_haste_da_base_e_poroso():
    m = materiais.materiais_haste()
    assert set(m) == {"316L", "Co-Cr-Mo", "Ti-6Al-4V", "Ti-6Al-4V poroso"}
    assert m["316L"][0] == pytest.approx(207500.0)
    assert m["Co-Cr-Mo"][0] == pytest.approx(225000.0)
    assert m["Ti-6Al-4V poroso"] == (17000.0, m["Ti-6Al-4V"][1])


def test_materiais_osso():
    o = materiais.materiais_osso()
    assert o["trabecular"][0] == pytest.approx(390.0)  # Li 2014, o mesmo do estudo no SOLIDWORKS
    assert o["cortical"][0] == pytest.approx(17500.0)  # ponto médio de 15-20 GPa
    assert materiais.modulo_trabecular(1.0) == pytest.approx(6850.0)
    assert 0 < o["trabecular"][0] < o["cortical"][0]


def test_lame():
    lam, mu = solver.lame(200.0, 0.25)
    assert mu == pytest.approx(80.0)
    assert lam == pytest.approx(80.0)


# ---------------------------------------------------------------- solver

def test_rigidez_cubo_simetrica_e_com_modos_rigidos():
    K, cantos = solver.rigidez_cubo(0.3, 2.0)
    assert K.shape == (24, 24)
    assert np.allclose(K, K.T)
    B = solver.modos_rigidos(cantos.astype(float))
    assert np.abs(K @ B).max() < 1e-9  # movimentos de corpo rígido não fazem força
    assert np.linalg.matrix_rank(K) == 18


def test_montagem_em_blocos_igual_a_montagem_simples():
    p, lig, _ = malha.malha_voxeis(np.ones((5, 3, 2), bool), [0, 0, 0], 1.0)
    E = np.linspace(1, 2, len(lig))
    nu = np.where(np.arange(len(lig)) % 2, 0.3, 0.34)
    K = solver.montar_voxeis(lig, E, nu, 1.0, len(p)).toarray()
    presos = np.flatnonzero(p[:, 0] == 0)
    Kb, livres = solver.montar_voxeis_blocos(lig, E, nu, 1.0, len(p), presos, bloco=7)
    g = (3 * livres[:, None] + np.arange(3)).ravel()
    assert np.allclose(Kb.toarray(), K[np.ix_(g, g)])


def test_resolver_voxeis_igual_ao_direto():
    p, lig, _ = malha.malha_voxeis(np.ones((10, 3, 3), bool), [0, 0, 0], 1.0)
    E, nu = np.full(len(lig), 1000.0), np.full(len(lig), 0.3)
    presos = np.flatnonzero(p[:, 0] == 0)
    f = np.random.default_rng(1).normal(size=3 * len(p))
    u1 = solver.resolver(solver.montar_voxeis(lig, E, nu, 1.0, len(p)), f, (3 * presos[:, None] + np.arange(3)).ravel())
    u2 = solver.resolver_voxeis(lig, E, nu, 1.0, p, f, presos, tol=1e-12)
    assert np.allclose(u1, u2, atol=1e-8 * np.abs(u1).max())


# ---------------------------------------------------------------- malha

def test_malha_voxeis_partilha_nos():
    ativos = np.zeros((2, 1, 1), bool)
    ativos[:] = True
    p, lig, ijk = malha.malha_voxeis(ativos, [0, 0, 0], 2.0)
    assert len(p) == 12 and lig.shape == (2, 8)
    assert len(np.intersect1d(lig[0], lig[1])) == 4
    assert p.max(0).tolist() == [4.0, 2.0, 2.0]


def test_maior_componente_tira_pedacos_soltos():
    a = np.zeros((6, 3, 3), bool)
    a[:3] = True
    a[5, 1, 1] = True
    assert malha.maior_componente(a).sum() == 27


def test_etiquetas_grossas_por_maioria():
    fina = np.zeros((4, 2, 2), np.int8)
    fina[:2] = 1
    fina[2:, :, :1] = 2  # metade 2, metade 0 no segundo vóxel grosso: empate
    g = malha.etiquetas_grossas(fina, 2)
    assert g.shape == (2, 1, 1)
    assert g[0, 0, 0] == 1 and g[1, 0, 0] == 2


def test_etiquetas_grossas_empate_pelo_canto():
    fina = np.zeros((2, 2, 2), np.int8)
    fina[:, :, 1] = 1  # 4 contra 4; o canto (0, 0, 0) é 0
    assert malha.etiquetas_grossas(fina, 2)[0, 0, 0] == 0
    assert malha.etiquetas_grossas(fina[::-1, ::-1, ::-1].copy(), 2)[0, 0, 0] == 1


def _cubo():
    v = np.array([[x, y, z] for x in (0, 1) for y in (0, 1) for z in (0, 1)], float) * 10 - 5
    f = np.array([[0, 1, 3], [0, 3, 2], [4, 6, 7], [4, 7, 5], [0, 4, 5], [0, 5, 1],
                  [2, 3, 7], [2, 7, 6], [0, 2, 6], [0, 6, 4], [1, 5, 7], [1, 7, 3]])
    return v, f


@pytest.mark.parametrize("eixo", [0, 1, 2])
def test_dentro_por_raios_num_cubo(eixo):
    v, f = _cubo()
    d = malha.dentro_por_raios(v, f, [-8, -8, -8], 1.0, (16, 16, 16), eixo)
    assert d.sum() == 1000  # 10 x 10 x 10 centros dentro
    assert d[8, 8, 8] and not d[0, 0, 0]


def test_dentro_da_malha_vota_entre_eixos():
    v, f = _cubo()
    assert malha.dentro_da_malha(v, f, [-8, -8, -8], 1.0, (16, 16, 16)).sum() == 1000


def test_malha_barra_gmsh():
    pytest.importorskip("gmsh")
    m = malha.malha_barra_gmsh(20.0, 4.0, 2.0, 2.0)
    assert m.p[0].max() == pytest.approx(20.0)
    assert m.p[1].min() == pytest.approx(-2.0)
    vol = sum(abs(np.linalg.det(m.p[:, t[1:]] - m.p[:, t[[0]]])) / 6 for t in m.t.T)
    assert vol == pytest.approx(160.0)


# ---------------------------------------------------------------- geometria

def test_espessura_cortical():
    assert geometria.espessura_cortical(0) == pytest.approx(4.8)
    assert geometria.espessura_cortical(200) == pytest.approx(1.8)
    assert geometria.espessura_cortical(75) == pytest.approx(3.3)


def test_etiquetas_num_cubo_de_osso():
    v, f = _cubo()
    v = v * 2  # cubo de 20 mm
    g = {"H": np.array([0, 0.0, 0])}  # altura h = y + 146: tudo acima de 50 (trabecular por dentro)
    et = geometria.etiquetas(v, f, None, None, g, [-12, -12, -12], 1.0, (24, 24, 24), False, 16)
    assert (et == geometria.CORTICAL).any() and (et == geometria.TRABECULAR).any()
    assert et[12, 12, 12] == geometria.TRABECULAR
    assert et[3, 12, 12] == geometria.CORTICAL  # a 1 mm da superfície
    assert et[0, 0, 0] == geometria.VAZIO


def test_ler_stl(tmp_path):
    import struct

    v, f = _cubo()
    corpo = b"".join(struct.pack("<3f", 0, 0, 0) + v[t].astype("<f4").tobytes() + b"\0\0" for t in f)
    caminho = tmp_path / "cubo.stl"
    caminho.write_bytes(b"\0" * 80 + struct.pack("<I", len(f)) + corpo)
    vv, ff = geometria.ler_stl(caminho)
    assert len(vv) == 8 and ff.shape == (12, 3)


# ---------------------------------------------------------------- cargas

def test_forcas_marcha():
    f = cargas.forcas_marcha(75.0)
    # módulo do caso de Heller 2005 (238,4 % do peso) igual, a menos de 1 %, ao pico de Bergmann 2001 (238 %)
    assert np.linalg.norm(f["contacto"]) == pytest.approx(cargas.CONTACTO_BERGMANN_PCT / 100 * 75 * 9.81, rel=0.01)
    assert f["contacto"][2] == pytest.approx(-2.292 * 75 * 9.81)
    assert f["contacto"][2] < 0 and f["contacto"][0] < 0  # para baixo e para fora
    assert f["abdutores"][2] > 0 and f["abdutores"][0] > 0  # para cima e para dentro
    assert f["abdutores"][0] == pytest.approx(0.58 * 75 * 9.81)


def test_angulos_contacto_dentro_das_medicoes_in_vivo():
    frontal, sagital = cargas.angulos_contacto()
    assert frontal == pytest.approx(13.3, abs=0.1) and sagital == pytest.approx(8.1, abs=0.1)
    assert 9 <= frontal <= 21  # intervalo da marcha em Bergmann et al. 2016, Tabela 5


def test_para_referencial_e_distribuir():
    v = cargas.para_referencial([1, 2, 3], [0, 0, 1], [1, 0, 0], [0, 1, 0])
    assert v.tolist() == [2, 3, 1]
    f = cargas.distribuir([0, 2], np.array([2.0, 0, -4]), 3)
    assert f.reshape(3, 3).sum(0).tolist() == [2.0, 0, -4]


def test_nos_superficie_calote_e_trocanter():
    p, lig, _ = malha.malha_voxeis(np.ones((4, 4, 4), bool), [-2, -2, -2], 1.0)
    sup = cargas.nos_superficie(lig, len(p))
    assert sup.sum() == 125 - 27
    topo = cargas.nos_calote(p, sup, [0, 0, 0], [0, -1, 0], 10, 30)
    assert len(topo) > 0 and np.all(p[topo, 1] == 2)
    topo = cargas.topo_trocanter(np.array([[-3.0, 9, 0], [2, 2, 2], [1, 1, 1]]))
    assert topo.tolist() == [2, 2, 2]
    tr = cargas.nos_trocanter(p, sup, topo, raio=1.1)
    assert len(tr) == 4 and np.all(np.linalg.norm(p[tr] - topo, axis=1) < 1.1)


# ---------------------------------------------------------------- Gruen e pós-processamento

def test_zonas_gruen():
    pts = np.array([[5, 90, 0], [-5, 90, 0], [5, 50, 0], [-5, 50, 0], [5, 10, 0], [-5, 10, 0], [0, -10, 0],
                    [0, -60, 0]])
    assert gruen.zonas_gruen(pts, 120).tolist() == [1, 7, 2, 6, 3, 5, 4, 0]


def test_comprimento_intraosseo():
    d = np.array([-1, 1, 0]) / np.sqrt(2)
    b = np.array([-10.0, 100.0, 0])
    L = gruen.comprimento_intraosseo(b, d, 0.0)
    assert L == pytest.approx(110.0)  # o plano passa pela base, normal a d: y = 100 + 10


def test_energia_por_zona_e_razao():
    W = np.array([1.0, 2.0, 3.0, 4.0])
    zonas = np.array([1, 1, 7, 7])
    res = posproc.energia_por_zona(W, 2.0, zonas, np.array([True, True, True, False]))
    assert res[1] == (3.0, 0.75) and res[7] == (3.0, 1.5)
    r, ss = posproc.razao_e_shielding(3.0, 4.0)
    assert r == 0.75 and ss == 0.25
    assert posproc.variacao_relativa(100, 96) == pytest.approx(4.0)


def test_corresponder():
    a = np.array([[0, 0, 0], [1, 0, 0], [2, 1, 0]])
    b = np.array([[2, 1, 0], [3, 0, 0], [0, 0, 0]])
    assert posproc.corresponder(a, b, (4, 2, 1)).tolist() == [2, -1, 0]


# ---------------------------------------------------------------- verificações (equilíbrio e deformações)

def test_forcas_internas_equilibram_as_cargas():
    p, lig, _ = malha.malha_voxeis(np.ones((8, 3, 3), bool), [0, 0, 0], 1.0)
    E, nu = np.full(len(lig), 1000.0), np.full(len(lig), 0.3)
    presos = np.flatnonzero(p[:, 0] == 0)
    ponta = np.flatnonzero(p[:, 0] == 8)
    f = cargas.distribuir(ponta, np.array([5.0, -20.0, 3.0]), len(p))
    u = solver.resolver_voxeis(lig, E, nu, 1.0, p, f, presos, tol=1e-12)
    fint = solver.forcas_internas(lig, E, nu, 1.0, u, len(p)).reshape(-1, 3)
    reacao = fint[presos].sum(0)
    assert np.allclose(reacao + f.reshape(-1, 3).sum(0), 0, atol=1e-6)
    livres = np.setdiff1d(np.arange(len(p)), presos)
    assert np.allclose(fint[livres], f.reshape(-1, 3)[livres], atol=1e-6)


def test_deformacoes_centro_de_um_campo_linear():
    p, lig, _ = malha.malha_voxeis(np.ones((2, 2, 2), bool), [0, 0, 0], 0.5)
    G = np.array([[1e-3, 2e-4, 0], [0, -3e-4, 0], [4e-4, 0, 5e-4]])
    u = (p @ G.T).ravel()
    eps = solver.deformacoes_centro(lig, 0.5, u)
    assert np.allclose(eps, 0.5 * (G + G.T)[None], atol=1e-12)
    ep = solver.deformacoes_principais(eps)
    assert np.allclose(ep[0], np.linalg.eigvalsh(0.5 * (G + G.T)))
