import importlib.util
import math
from pathlib import Path

import numpy as np
import pytest

RAIZ = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(RAIZ / "scripts"))
spec = importlib.util.spec_from_file_location("video_fea", RAIZ / "scripts" / "video_fea_haste.py")
vf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vf)


def test_numero_de_fotogramas():
    assert vf.numero_de_fotogramas(16, 30) == 480
    with pytest.raises(ValueError):
        vf.numero_de_fotogramas(0, 30)


def test_smoothstep_e_rampa():
    assert vf.smoothstep(-1) == 0 and vf.smoothstep(2) == 1
    assert vf.smoothstep(0.5) == pytest.approx(0.5)
    assert vf.rampa_deformacao(0) == 0
    assert vf.rampa_deformacao(vf.RAMPA_S) == 1
    assert vf.rampa_deformacao(100) == 1
    assert vf.rampa_deformacao(1.0, rampa_s=0) == 1


def test_azimute_orbita_fecha_o_ciclo():
    d = 16.0
    assert vf.azimute_orbita(0, d) == pytest.approx(0)
    assert vf.azimute_orbita(d, d) == pytest.approx(0, abs=1e-9)
    assert vf.azimute_orbita(d / 4, d, 30) == pytest.approx(30)
    assert vf.azimute_orbita(3 * d / 4, d, 30) == pytest.approx(-30)


def test_posicao_camara():
    assert vf.posicao_camara((0, 0, 0), 100, 0) == pytest.approx((0, 0, 100))
    x, y, z = vf.posicao_camara((1, 2, 3), 100, 90)
    assert (x, y, z) == pytest.approx((101, 2, 3))
    assert math.dist(vf.posicao_camara((0, 0, 0), 50, 33, 10), (0, 0, 0)) == pytest.approx(50)


def test_pontos_deformados():
    base = np.zeros((2, 3))
    d = np.array([[1.0, 0, 0], [0, 2.0, 0]])
    assert np.allclose(vf.pontos_deformados(base, d, 5), [[5, 0, 0], [0, 10, 0]])
    assert np.allclose(vf.pontos_deformados(base, d, 0), base)
    with pytest.raises(ValueError):
        vf.pontos_deformados(base, d[:1], 2)
    with pytest.raises(ValueError):
        vf.pontos_deformados(base, d, float("nan"))


def test_escolher_fator():
    assert vf.escolher_fator(7.5, alvo_mm=40) == 5
    assert vf.escolher_fator(0.5, alvo_mm=40) == 100
    with pytest.raises(ValueError):
        vf.escolher_fator(0)


def test_texto_fator():
    assert vf.texto_fator(5) == "×5"
    assert vf.texto_fator(2.5) == "×2,5"
    assert vf.texto_fator(0) == "×0"


def test_legenda_material():
    sys.path.insert(0, str(RAIZ / "scripts"))
    l = vf.legenda_material("Aco316L", 207.5, 171.9, 6.28)
    assert l[0] == "Aço inox 316L" and l[1] == "E = 207,5 GPa" and "171,9" in l[2] and "6,3" in l[3]


def test_viewport_painel():
    v0 = vf.viewport_painel(0)
    v3 = vf.viewport_painel(3)
    assert v0[0] == 0 and v3[2] == pytest.approx(vf.LARGURA_PAINEIS / vf.LARGURA)
    assert v0[1] < v0[3] and v0[2] == pytest.approx(vf.viewport_painel(1)[0])
