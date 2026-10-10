"""Massa e centro de massa da haste femoral com cada material, e efeito no centro de massa do corpo.

Em linguagem simples: a haste tem sempre a mesma forma (o mesmo volume); muda só a densidade do metal. A massa é
volume x densidade. Trocar uma haste leve por uma pesada desloca o centro de massa do corpo, no máximo, de
(diferença de massa) x (distância da haste ao centro de massa do corpo) / (massa do corpo).
"""

from __future__ import annotations

import numpy as np


def volume_e_centroide(v: np.ndarray, f: np.ndarray) -> tuple[float, np.ndarray]:
    """Volume e centroide de um sólido fechado triangulado (teorema da divergência, tetraedros à origem).

    v: vértices (n, 3); f: triângulos (m, 3) com as normais para fora. Devolve (volume, centroide) nas unidades
    dos vértices.
    """
    a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    vol_t = np.einsum("ij,ij->i", a, np.cross(b, c)) / 6.0
    vol = float(vol_t.sum())
    centro = (vol_t[:, None] * (a + b + c) / 4.0).sum(axis=0) / vol
    return vol, centro


def massas_g(volume_cm3: float, densidades: dict[str, float]) -> dict[str, float]:
    """Massa em gramas de cada material: volume (cm³) x densidade (g/cm³)."""
    return {m: volume_cm3 * rho for m, rho in densidades.items()}


def desvio_centro_massa_mm(delta_massa_kg: float, distancia_m: float, massa_corpo_kg: float) -> float:
    """Deslocamento do centro de massa do corpo (mm) ao trocar uma massa delta_massa num ponto à distância dada.

    O centro de massa é a média das posições pesada pelas massas; mudar a massa de um ponto em dm desloca-o
    de dm x d / M (aproximação para dm muito menor do que M).
    """
    return 1000.0 * delta_massa_kg * distancia_m / massa_corpo_kg
