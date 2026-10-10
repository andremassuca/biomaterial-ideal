"""Testes da CFD do stent: soluções analíticas, onda, geometria dos struts, dicionários do OpenFOAM e
pós-processamento (sem correr o OpenFOAM)."""

import numpy as np
import pytest

from biomat_mcdm.cfd import analitico as an
from biomat_mcdm.cfd import geometria as geo
from biomat_mcdm.cfd import onda as on
from biomat_mcdm.cfd import openfoam as of
from biomat_mcdm.cfd import posproc as pp


# ------------------------------------------------------------------ analítico

def test_poiseuille_perfil_e_corte():
    R, U, mu = 1.5e-3, 0.1, 0.0035
    assert an.perfil_poiseuille(0.0, R, U) == pytest.approx(2 * U)
    assert an.perfil_poiseuille(R, R, U) == pytest.approx(0.0)
    # média da parábola na secção = U
    r = np.linspace(0, R, 20001)
    media = np.trapezoid(an.perfil_poiseuille(r, R, U) * 2 * np.pi * r, r) / (np.pi * R ** 2)
    assert media == pytest.approx(U, rel=1e-6)
    # tau = mu |du/dr| na parede
    du = (an.perfil_poiseuille(R - 1e-9, R, U) - an.perfil_poiseuille(R, R, U)) / 1e-9
    assert an.tensao_corte_poiseuille(mu, R, U) == pytest.approx(mu * du, rel=1e-5)
    # equilíbrio: queda de pressão x área = atrito na parede x perímetro
    assert an.gradiente_pressao_poiseuille(mu, R, U) * np.pi * R ** 2 == pytest.approx(
        an.tensao_corte_poiseuille(mu, R, U) * 2 * np.pi * R)


def test_numeros_adimensionais():
    assert an.velocidade_media(np.pi * 1e-6, 1e-3) == pytest.approx(1.0)
    assert an.reynolds(1000, 1, 0.01, 0.001) == pytest.approx(10000)
    assert an.womersley(1.5e-3, 1 / 1.06, 1060, 0.0035) == pytest.approx(2.0, abs=0.05)


# ------------------------------------------------------------------ onda

def test_onda_coronaria_bate_com_a_fonte():
    o = on.onda_coronaria()
    t = np.linspace(0, o.periodo_s, 2001)
    u_eixo = 2 * o.velocidade(t) * 100  # cm/s no eixo
    assert u_eixo.mean() == pytest.approx(on.U_EIXO_MEDIA_CMS, rel=1e-3)
    assert u_eixo.max() - u_eixo.min() == pytest.approx(on.U_EIXO_MAX_CMS - on.U_EIXO_MIN_CMS, rel=1e-3)
    assert t[np.argmax(u_eixo)] == pytest.approx(on.FRACAO_PICO * o.periodo_s, abs=1e-3)
    # a série de Fourier dá o mesmo fator
    (a, b), = o.coeficientes()
    w = 2 * np.pi / o.periodo_s
    assert np.allclose(1 + a * np.cos(w * t) + b * np.sin(w * t), o.fator(t))


# ------------------------------------------------------------------ geometria

ST = geo.Stent(raio_mm=1.5, n_losangos=8, altura_anel_mm=0.589, n_aneis=4, z0_mm=1.0, espessura_um=79,
               largura_um=90)


def test_linha_struts_em_zigue_zague():
    v = geo.linha_struts(ST)
    assert len(v) == ST.n_aneis + 1
    assert set(np.round(v[:, 0], 9)) == {0.0, round(ST.arco_mm, 9)}
    assert np.allclose(np.diff(v[:, 1]), ST.altura_anel_mm)
    assert ST.angulo_strut_graus == pytest.approx(45.0, abs=0.1)


def test_solido_fechado_com_volume_certo():
    v, f = geo.solido_struts(ST, tamanho_mm=0.03)
    arestas = np.sort(np.vstack([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), axis=1)
    _, cont = np.unique(arestas, axis=0, return_counts=True)
    assert set(cont) == {2}  # cada aresta em dois triângulos: superfície fechada
    p, t = geo.poligono_struts(ST, 0.03)
    area = geo.area_com_sinal(p, t).sum()
    vol = geo.volume_triangulado(v, f)
    assert vol > 0  # normais para fora
    assert vol == pytest.approx(geo.volume_esperado(ST, area), rel=1e-3)
    # o strut entra no lúmen exatamente a espessura
    r = np.hypot(v[:, 0], v[:, 1])
    assert r.min() == pytest.approx(ST.raio_mm - ST.espessura_um / 1000)


def test_area_dos_struts_perto_do_esperado():
    p, t = geo.poligono_struts(ST, 0.03)
    area = geo.area_com_sinal(p, t).sum()
    comp = np.hypot(ST.arco_mm, ST.altura_anel_mm)
    w = ST.largura_um / 1000
    # n retângulos de (comprimento + w) x w, menos as sobreposições nos vértices (no máximo w² por vértice)
    bruto = ST.n_aneis * (comp + w) * w
    assert bruto - (ST.n_aneis - 1) * 2 * w ** 2 <= area <= bruto


def test_stl_em_metros(tmp_path):
    v, f = geo.solido_struts(ST, tamanho_mm=0.05)
    caminho = tmp_path / "s.stl"
    geo.escrever_stl(caminho, v, f)
    texto = caminho.read_text(encoding="ascii")
    assert texto.startswith("solid struts") and texto.count("facet normal") == len(f)
    x = float(texto.split("vertex")[1].split()[0])
    assert abs(x) < 0.01  # metros


# ------------------------------------------------------------------ OpenFOAM

M = of.Malha(raio_mm=1.5, setor_rad=np.pi / 8, comprimento_mm=6.0, z_stent=(0.7, 3.9), delta_mm=0.02)


def test_contagens_dao_o_tamanho_pedido():
    c = of.contagens(M)
    assert 1.5 * np.pi / 8 / (2 * c["n_h"]) == pytest.approx(0.02, rel=0.1)
    assert 3.2 / c["n_meio"] == pytest.approx(0.02, rel=0.05)
    assert c["n_celulas"] == (c["n_h"] ** 2 + 2 * c["n_h"] * c["n_r"]) * (c["n_ent"] + c["n_meio"] + c["n_sai"])


def test_block_mesh_tem_os_patches():
    t = of.block_mesh(M)
    for nome in ("entrada", "saida", "parede", "simetria0", "simetria1"):
        assert f"    {nome}\n" in t
    assert "hex (0 1 2 3 7 8 9 10)" in t and "convertToMeters 0.001" in t
    assert "cyclic" not in t and "cyclic" in of.block_mesh(M, ciclico=True)


def test_campo_u_tem_a_onda():
    o = on.onda_coronaria()
    t = of.campo_u(1.5e-3, o.u_media, of.fourier_expr(o.coeficientes(), o.frequencia_hz))
    assert "exprFixedValue" in t and "cos(1*" in t and f"{o.u_media:.9e}" in t
    assert of.fourier_expr([], 1.0) == "1.0"


def test_control_dict_pulsatil_tem_medias():
    t = of.control_dict("pimpleFoam", 2.12, 0.00053, 1.06, inicio_media=1.06)
    assert "fieldAverage" in t and "timeStart 1.06" in t and "mag(wallShearStress)" in t
    assert "fieldAverage" not in of.control_dict("simpleFoam", 3000, 1, 3000)


# ------------------------------------------------------------------ pós-processamento

def test_osi_e_fracao():
    vetor = np.array([[1.0, 0, 0], [0.0, 0, 0], [0.5, 0, 0]])
    mag = np.array([1.0, 1.0, 1.0])
    assert np.allclose(pp.osi(vetor, mag), [0.0, 0.5, 0.25])
    assert pp.fracao_abaixo(np.array([0.1, 0.5, 0.3]), np.array([1.0, 2.0, 1.0]), 0.4) == pytest.approx(0.5)
    assert np.allclose(pp.magnitude_tensao(np.array([[3e-4, 4e-4, 0]]), 1000), [0.5])


def test_erro_perfil_nulo_na_parabola():
    r = np.linspace(0, 1.5e-3, 50)
    e = pp.erro_perfil(r, an.perfil_poiseuille(r, 1.5e-3, 0.1), 1.5e-3, 0.1)
    assert e["erro_max"] == pytest.approx(0, abs=1e-12)


def test_gci_recupera_ordem_e_limite():
    # f(h) = 1 + h², h = 1, raiz(2), 2: ordem 2 e limite 1
    g = pp.indice_convergencia(2.0, 3.0, 5.0, np.sqrt(2))
    assert g["ordem"] == pytest.approx(2.0)
    assert g["extrapolado"] == pytest.approx(1.0)
    assert g["gci_fina"] == pytest.approx(1.25 * 0.5 / 1.0)
    assert np.isnan(pp.indice_convergencia(2.0, 3.0, 2.5, 2.0)["ordem"])  # oscilatória
    assert np.isnan(pp.indice_convergencia(2.0, 3.0, 3.5, 2.0)["ordem"])  # diferenças que não diminuem


def test_desenrolar():
    p = np.array([[1.5, 0, 2.0], [1.5 * np.cos(0.2), 1.5 * np.sin(0.2), 3.0]])
    assert np.allclose(pp.desenrolar(p, 1.5), [[0, 2.0], [0.3, 3.0]])


def test_juntar_series_de_caso_retomado(tmp_path):
    # 1.ª corrida de 0 a 1,5 s (parada a meio do 2.º ciclo); retoma em 1,0 s com valores diferentes
    for sub, t, v in [("0", [0.5, 1.0, 1.25, 1.5], 1.0), ("1", [1.25, 1.5, 2.0], 2.0)]:
        (tmp_path / sub).mkdir()
        linhas = "\n".join(f"{x}\t{v}" for x in t)
        (tmp_path / sub / "surfaceFieldValue.dat").write_text("# Time\tvalor\n" + linhas + "\n", encoding="utf-8")
    (tmp_path / "outra").mkdir()  # pastas sem nome de instante são ignoradas
    d = pp.juntar_series(tmp_path)
    assert d[:, 0].tolist() == [0.5, 1.0, 1.25, 1.5, 2.0]
    assert d[:, 1].tolist() == [1.0, 1.0, 2.0, 2.0, 2.0]  # depois da retoma vale a corrida nova
    assert pp.juntar_series(tmp_path / "nao_existe") is None
