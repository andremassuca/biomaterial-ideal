"""Testes das funções puras de scripts/fea_solidworks.py (as que não precisam do SolidWorks)."""

import importlib.util
import math
from pathlib import Path

import pytest

CAMINHO = Path(__file__).resolve().parents[1] / "scripts" / "fea_solidworks.py"
spec = importlib.util.spec_from_file_location("fea_solidworks", CAMINHO)
fea = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fea)


@pytest.fixture(scope="module")
def cf():
    return fea.ler_cotas_femur()


@pytest.fixture(scope="module")
def ch():
    return fea.cad.ler_cotas()


@pytest.fixture(scope="module")
def geo(cf, ch):
    return fea.geometria_colo(cf, ch)


def _interp(perfil, y):
    for (y0, r0), (y1, r1) in zip(perfil, perfil[1:]):
        if y0 <= y <= y1:
            return r0 + (r1 - r0) * (y - y0) / (y1 - y0)
    raise ValueError(y)


def _envolvente_haste(ch, y):
    """Maior distância ao eixo da haste à altura y (contorno frontal e afilamento anteroposterior)."""
    pts = fea.cad.contorno_haste(ch)
    L = ch["haste_comprimento"]
    xs = [x0 + (y - y0) * (x1 - x0) / (y1 - y0) for (x0, y0), (x1, y1) in zip(pts, pts[1:])
          if (y0 - y) * (y1 - y) <= 0 and y0 != y1]
    e0, e1 = ch["haste_espessura_ponta"] / 2, ch["haste_espessura"] / 2
    e = e0 + (e1 - e0) * min(y / (0.6 * L), 1)
    return max(math.hypot(x, e) for x in xs)


def test_cotas_do_femur(cf):
    for chave in ("cabeca_raio", "cabeca_offset", "cabeca_altura", "diafise_raio", "canal_raio", "fixacao_y",
                  "trabecular_base", "trocanter_topo", "osteotomia_lateral"):
        assert chave in cf
    assert cf["fixacao_y"] == -150 and cf["cabeca_raio"] == pytest.approx(22.8)


def test_cabeca_igual_a_da_haste(cf, ch, geo):
    centro_haste = fea.cad.eixo_colo(ch)["centro"]
    assert geo["centro"][0] == pytest.approx(centro_haste[0])
    assert geo["centro"][1] == pytest.approx(centro_haste[1], abs=0.05)
    assert geo["p0"][0] == pytest.approx(0.0, abs=1e-9)
    assert geo["p0"][1] == pytest.approx(cf["cabeca_altura"] - cf["cabeca_offset"])  # 135°: inclinação de 45°


def test_perfis_e_espessura_da_cortical(cf):
    ext = fea.perfil_exterior(cf)
    ins = fea.perfil_interior(cf, cf["fixacao_y"] - 1)
    assert ext[0][0] == cf["fixacao_y"]
    assert all(r1 >= r0 for (_, r0), (_, r1) in zip(ext, ext[1:]))
    for y in range(-140, 118, 5):
        assert _interp(ext, y) - _interp(ins, y) >= cf["cortical_metafise"] - 1e-9


def test_haste_dentro_do_trabecular_com_folga(cf, ch):
    ins = fea.perfil_interior(cf, cf["trabecular_base"])
    for y in range(0, 106, 5):
        assert _interp(ins, y) - _envolvente_haste(ch, y) >= 1.9


def test_poligono_offset_de_um_quadrado():
    q = [(0, 0), (10, 0), (10, 10), (0, 10)]
    out = fea.poligono_offset(q, 2)
    assert out == [pytest.approx(p) for p in [(2, 2), (8, 2), (8, 8), (2, 8)]]


def test_trocanter_convexo_anti_horario(cf):
    pts = fea.poligono_trocanter(cf)
    area = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1])) / 2
    assert area > 0
    n = len(pts)
    for i in range(n):
        (ax, ay), (bx, by), (cx, cy) = pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        assert (bx - ax) * (cy - by) - (by - ay) * (cx - bx) > 0
    interior = fea.poligono_offset(pts, cf["cortical_metafise"])
    assert min(y for _, y in interior) > min(y for _, y in pts)


def test_corte_do_colo(cf, geo):
    bx, by = geo["base_haste"]
    assert fea.y_corte_colo(bx, geo) == pytest.approx(by)
    assert fea.removido_pelo_corte(*geo["centro"], cf, geo)
    assert not fea.removido_pelo_corte(17.0, 133.0, cf, geo)  # grande trocânter fica
    assert not fea.removido_pelo_corte(-14.0, 50.0, cf, geo)  # diáfise fica
    pol = fea.poligono_osteotomia(cf, geo)
    assert pol[1] == pytest.approx((cf["osteotomia_lateral"], fea.y_corte_colo(cf["osteotomia_lateral"], geo)))


def test_zonas_de_gruen(cf, ch, geo):
    L = ch["haste_comprimento"]
    z = lambda x, y: fea.zona_gruen(x, y, L, cf, geo)  # noqa: E731
    assert z(20, 100) == 1 and z(20, 50) == 2 and z(20, 10) == 3
    assert z(0, -5) == 4 and z(5, -30) is None
    assert z(-20, 10) == 5 and z(-20, 50) == 6 and z(-20, 85) == 7
    assert z(-38.3, 131.3) is None  # cabeça, retirada pelo corte


def test_forcas_da_marcha():
    f = fea.forcas_marcha(75)
    bw = 75 * 9.81
    anca = f["contacto_anca"]
    assert math.hypot(*anca) / bw == pytest.approx(2.377, abs=0.01)  # 238 % do peso (Bergmann et al. 2001)
    assert anca[0] > 0 and anca[1] < 0  # para lateral e para baixo, na cabeça
    abd = f["abdutores"]
    assert abd[0] < 0 and abd[1] > 0  # puxa o trocânter para medial e para cima


def test_modulos_da_haste():
    E = fea.ler_modulos_haste()
    assert E == {"Aço inox 316L": 207.5, "Co-Cr-Mo forjado": 225.0, "Ti-6Al-4V ELI": 105.5,
                 "Ti-6Al-4V poroso": 17.0}


def test_somas_e_razoes(cf, ch, geo):
    L = ch["haste_comprimento"]
    els = [(20, 100, 1.0), (20, 100, 0.5), (-20, 85, 2.0), (-38.3, 131.3, 9.0)]
    zonas = fea.somar_por_zona(els, L, cf, geo)
    assert zonas[1] == {"energia_J": 1.5, "n": 2} and zonas[7]["energia_J"] == 2.0
    assert sum(z["n"] for z in zonas.values()) == 3
    r = fea.razao_ao_intacto(zonas, {k: {"energia_J": 3.0, "n": 1} for k in zonas})
    assert r[1] == pytest.approx(0.5) and r[2] == 0.0


def test_pares_e_centros():
    assert fea.pares_id_valor([7, 0.5, 9, 1.5]) == [(7, 0.5), (9, 1.5)]
    with pytest.raises(ValueError):
        fea.pares_id_valor([1, 2, 3])
    bloco = [5] + list(range(10)) + [0.001, 0.002, -0.003, 1.5, 1.0]
    assert fea.centros_dos_elementos(bloco) == {5: pytest.approx((1.0, 2.0, -3.0))}


def test_stl_binario(tmp_path):
    destino = tmp_path / "t.stl"
    fea.stl_binario([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [(0, 1, 2)], destino)
    assert destino.stat().st_size == 84 + 50


@pytest.mark.skipif(not fea.FEMUR_OBJ.exists(), reason="malha do FJ3365 não disponível")
def test_medidas_do_femur_anatomico(cf):
    m = fea.medir_femur_anatomico(cf)
    assert m["cabeca_raio"] == pytest.approx(22.8, abs=0.1)
    assert m["cabeca_offset"] == pytest.approx(33.4, abs=0.1)
    v, f = fea.femur_no_referencial_da_haste(cf)
    assert len(f) == 3102
    assert v[:, 1].max() == pytest.approx(cf["cabeca_altura"] + 22.9, abs=1.0)


def _resultados_falsos():
    def caso(g1, g7):
        return {"nos": 10, "elementos": 5, "zonas": {"1": {"energia_J": g1, "n": 1}, "7": {"energia_J": g7, "n": 1}}}
    return {"malhas_mm": [5.0, 3.5], "casos": {
        "Intacto": {"5.0": caso(0.040, 0.040), "3.5": caso(0.042, 0.044)},
        "Co-Cr-Mo forjado": {"5.0": caso(0.020, 0.010), "3.5": caso(0.021, 0.011)},
        "Ti-6Al-4V poroso": {"5.0": caso(0.035, 0.030), "3.5": caso(0.036, 0.033)},
    }}


def test_linhas_e_ordem():
    r = _resultados_falsos()
    linhas = fea.linhas_resumo(r)
    cocr = next(ln for ln in linhas if ln["caso"] == "Co-Cr-Mo forjado" and ln["h_mm"] == 3.5)
    assert cocr["g1_mJ"] == pytest.approx(21.0) and cocr["g7_razao"] == pytest.approx(0.25)
    assert fea.ordem_por_zona(r, "7", "3.5") == ["Ti-6Al-4V poroso", "Co-Cr-Mo forjado"]
    assert fea.variacao_entre_malhas(r, "Intacto", "7") == pytest.approx((0.040 - 0.044) / 0.044 * 100)


def test_resumo_markdown_e_figura(tmp_path):
    r = _resultados_falsos()
    texto = fea.resumo_markdown(r)
    assert "Gruen 1: Ti-6Al-4V poroso > Co-Cr-Mo forjado" in texto
    assert "| Co-Cr-Mo forjado | 225,0 |" in texto
    assert chr(0x2014) not in texto
    assert "próxima da do osso intacto" in texto and "melhor do que o osso" not in texto
    fea.figura_gruen(r, tmp_path / "g")
    assert (tmp_path / "g.png").exists() and (tmp_path / "g.svg").exists()


def test_soma_cargas_e_equilibrio():
    s = fea.soma_cargas(75)
    f = fea.forcas_marcha(75)
    assert s == pytest.approx(tuple(f["contacto_anca"][i] + f["abdutores"][i] for i in range(3)))
    assert fea.erro_equilibrio([-v for v in s], s) == pytest.approx(0.0)
    assert fea.erro_equilibrio([-1.01 * v for v in s], s) == pytest.approx(1.0)


def test_caso_completo_de_heller():
    f = fea.forcas_marcha(75, completo=True)
    assert set(f) == {"contacto_anca", "abdutores", "tensor_fascia_lata_proximal", "tensor_fascia_lata_distal",
                      "vasto_lateral"}
    assert f["vasto_lateral"][1] == pytest.approx(-0.929 * 75 * 9.81)  # puxa para baixo


def test_flecha_da_consola(cf):
    v = fea.flecha_consola(cf)
    assert v["L_mm"] == pytest.approx(281.3)
    assert v["I_mm4"] == pytest.approx(math.pi / 4 * (14.5 ** 4 - 6.5 ** 4))
    assert 4.0 < v["flecha_total_mm"] < 9.0


def test_percentil_e_raio_exterior(cf):
    assert fea.percentil([1, 2, 3, 4, 5], 50) == 3
    assert fea.percentil([0, 10], 95) == pytest.approx(9.5)
    with pytest.raises(ValueError):
        fea.percentil([], 50)
    assert fea._raio_exterior(cf, 82.5) == pytest.approx((19.0 + 23.0) / 2)


def test_escolher_graficos_separa_malha_e_tensao():
    g = fea.escolher_graficos(["Mesh Quality1", "Stress1 (-vonMises-)", "Displacement1"])
    assert g == {"malha": "Mesh Quality1", "tensao": "Stress1 (-vonMises-)"}
    # o primeiro da lista não é o de tensões: foi esse engano que deu os antigos *_von_mises.png
    assert fea.escolher_graficos(["Mesh Quality1"]) == {"malha": "Mesh Quality1", "tensao": None}
    assert fea.escolher_graficos([]) == {"malha": None, "tensao": None}
    assert fea.escolher_graficos(None) == {"malha": None, "tensao": None}
