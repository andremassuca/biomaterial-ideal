"""Testes da massa e do centro de massa da haste."""

import numpy as np
import pytest

from biomat_mcdm.massa import desvio_centro_massa_mm, massas_g, volume_e_centroide


def cubo(lado=2.0, origem=(1.0, 2.0, 3.0)):
    """Cubo triangulado com as normais para fora."""
    o = np.asarray(origem)
    v = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]]) * lado + o
    f = np.array([[0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7], [0, 1, 5], [0, 5, 4],
                  [1, 2, 6], [1, 6, 5], [2, 3, 7], [2, 7, 6], [3, 0, 4], [3, 4, 7]])
    return v.astype(float), f


def test_volume_e_centroide_do_cubo():
    v, f = cubo()
    vol, c = volume_e_centroide(v, f)
    assert vol == pytest.approx(8.0)
    assert np.allclose(c, [2.0, 3.0, 4.0])


def test_massas_e_desvio():
    m = massas_g(23.8, {"Ti": 4.43, "CoCr": 8.28})
    assert m["Ti"] == pytest.approx(105.434)
    # 0,1 kg a 0,5 m num corpo de 75 kg: 0,667 mm
    assert desvio_centro_massa_mm(0.1, 0.5, 75) == pytest.approx(0.6667, rel=1e-3)


def test_haste_real_tem_volume_plausivel():
    import sys
    from pathlib import Path
    raiz = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(raiz / "scripts"))
    import massa_haste
    v, f = massa_haste.ler_stl(massa_haste.STL)
    vol, _ = volume_e_centroide(v, f)
    assert 15_000 < vol < 40_000  # mm³: uma haste de tamanho médio tem dezenas de cm³
