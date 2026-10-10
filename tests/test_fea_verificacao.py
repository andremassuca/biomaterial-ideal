"""Verificação analítica da FEA: barra de Ti-6Al-4V à compressão e à flexão (viga em consola).

Compara com a teoria: compressão, delta = F L / (E A); flexão, viga de Timoshenko,
delta = F L^3 / (3 E I) + F L / (kappa G A), com kappa = 10 (1 + nu) / (12 + 11 nu) (secção retangular).
Erro abaixo de 2 % com as malhas usadas: tetraedros quadráticos do gmsh (scikit-fem) e hexaedros de vóxel
(o elemento do modelo do fémur).
"""

import numpy as np
import pytest

skfem = pytest.importorskip("skfem")
pytest.importorskip("gmsh")

from biomat_mcdm.fea import malha, materiais, solver  # noqa: E402

E, NU = materiais.materiais_haste()["Ti-6Al-4V"]
L, A_LADO, F = 200.0, 10.0, 1000.0  # mm, mm, N
AREA, I = A_LADO ** 2, A_LADO ** 4 / 12


def flecha_timoshenko():
    G = E / (2 * (1 + NU))
    kappa = 10 * (1 + NU) / (12 + 11 * NU)
    return F * L ** 3 / (3 * E * I) + F * L / (kappa * G * AREA)


def _tetraedros():
    m = malha.malha_barra_gmsh(L, A_LADO, A_LADO, 5.0)
    el = skfem.ElementTetP2()
    b = skfem.Basis(m, skfem.ElementVector(el))
    ponta = m.facets_satisfying(lambda x: np.isclose(x[0], L))
    fb = skfem.FacetBasis(m, b.elem, facets=ponta)
    return m, el, b, fb


def test_e_do_ti64_vem_da_base():
    assert E == pytest.approx(105500.0)


def test_compressao_tetraedros_gmsh():
    m, el, b, fb = _tetraedros()

    @skfem.LinearForm
    def tracao(v, w):
        return -F / AREA * v[0]

    f = skfem.asm(tracao, fb)
    base = b.get_dofs(lambda x: np.isclose(x[0], 0))
    canto = b.get_dofs(lambda x: np.isclose(x[0], 0) & np.isclose(x[1], -A_LADO / 2) & np.isclose(x[2], -A_LADO / 2))
    canto2 = b.get_dofs(lambda x: np.isclose(x[0], 0) & np.isclose(x[1], A_LADO / 2) & np.isclose(x[2], -A_LADO / 2))
    D = np.concatenate([base.all(["u^1"]), canto.all(), canto2.all(["u^3"])])
    _, u = solver.resolver_skfem(m, el, E, NU, D, f)
    ux = -u[b.get_dofs(lambda x: np.isclose(x[0], L)).nodal["u^1"]].mean()
    assert ux == pytest.approx(F * L / (E * AREA), rel=0.02)


def test_flexao_tetraedros_gmsh():
    m, el, b, fb = _tetraedros()

    @skfem.LinearForm
    def corte(v, w):
        return -F / AREA * v[2]

    f = skfem.asm(corte, fb)
    D = b.get_dofs(lambda x: np.isclose(x[0], 0)).all()
    _, u = solver.resolver_skfem(m, el, E, NU, D, f)
    flecha = -u[b.get_dofs(lambda x: np.isclose(x[0], L)).nodal["u^3"]].mean()
    assert flecha == pytest.approx(flecha_timoshenko(), rel=0.02)


def _barra_voxeis(h):
    ativos = np.ones((int(L / h), int(A_LADO / h), int(A_LADO / h)), bool)
    p, lig, _ = malha.malha_voxeis(ativos, [0, -A_LADO / 2, -A_LADO / 2], h)
    ponta = np.flatnonzero(np.isclose(p[:, 0], L))
    # forças nodais consistentes numa face de elementos bilineares: cantos 1/4, arestas 1/2, interior 1
    w = np.where(np.isclose(abs(p[ponta, 1]), A_LADO / 2), 0.5, 1) * np.where(np.isclose(abs(p[ponta, 2]), A_LADO / 2), 0.5, 1)
    return p, lig, ponta, w / w.sum()


def test_flexao_hexaedros_voxel():
    h = 1.25  # 8 elementos na espessura
    p, lig, ponta, w = _barra_voxeis(h)
    f = np.zeros(3 * len(p))
    f[3 * ponta + 2] = -F * w
    presos = np.flatnonzero(np.isclose(p[:, 0], 0))
    u = solver.resolver_voxeis(lig, np.full(len(lig), E), np.full(len(lig), NU), h, p, f, presos)
    flecha = -u[3 * ponta + 2].mean()
    assert flecha == pytest.approx(flecha_timoshenko(), rel=0.02)


def test_compressao_hexaedros_voxel_e_energia():
    h = 2.5
    p, lig, ponta, w = _barra_voxeis(h)
    f = np.zeros(3 * len(p))
    f[3 * ponta] = -F * w
    base = np.flatnonzero(np.isclose(p[:, 0], 0))
    # rolete na base (só x preso) e dois pontos para tirar os movimentos de corpo rígido
    fixos = [3 * base]
    c0 = np.flatnonzero(np.isclose(p[:, 0], 0) & np.isclose(p[:, 1], -5) & np.isclose(p[:, 2], -5))
    c1 = np.flatnonzero(np.isclose(p[:, 0], 0) & np.isclose(p[:, 1], 5) & np.isclose(p[:, 2], -5))
    fixos += [3 * c0 + 1, 3 * c0 + 2, 3 * c1 + 2]
    nE = np.full(len(lig), E)
    nN = np.full(len(lig), NU)
    K = solver.montar_voxeis(lig, nE, nN, h, len(p))
    u = solver.resolver(K, f, np.concatenate(fixos))
    delta = F * L / (E * AREA)
    assert -u[3 * ponta].mean() == pytest.approx(delta, rel=1e-6)
    # energia de deformação = trabalho da força / 2 = F delta / 2
    W = solver.energia_voxeis(lig, nE, nN, h, u)
    assert W.sum() == pytest.approx(F * delta / 2, rel=1e-6)
