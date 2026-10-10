"""Soluções analíticas para verificar a CFD: escoamento de Poiseuille num tubo e números adimensionais."""

from __future__ import annotations

import numpy as np


def velocidade_media(caudal_m3s: float, raio_m: float) -> float:
    """Velocidade média (m/s) de um caudal (m³/s) num tubo de raio dado: U = Q / (pi R²)."""
    return caudal_m3s / (np.pi * raio_m ** 2)


def perfil_poiseuille(r_m, raio_m: float, u_media: float):
    """Velocidade axial (m/s) do escoamento de Poiseuille à distância r do eixo.

    Em linguagem simples: num tubo comprido e direito, com escoamento lento e estável, a velocidade é máxima no
    eixo (o dobro da média) e zero na parede, com a forma de uma parábola: u(r) = 2 U (1 - r²/R²).
    """
    r = np.asarray(r_m, dtype=float)
    return 2.0 * u_media * (1.0 - (r / raio_m) ** 2)


def tensao_corte_poiseuille(mu_pas: float, raio_m: float, u_media: float) -> float:
    """Tensão de corte na parede (Pa) do escoamento de Poiseuille: tau = mu |du/dr| em r = R = 4 mu U / R.

    Em linguagem simples: é o "atrito" do sangue na parede; cresce com a viscosidade e a velocidade e diminui
    com o raio do tubo.
    """
    return 4.0 * mu_pas * u_media / raio_m


def gradiente_pressao_poiseuille(mu_pas: float, raio_m: float, u_media: float) -> float:
    """Queda de pressão por metro (Pa/m) que mantém o escoamento de Poiseuille: dp/dz = 8 mu U / R²."""
    return 8.0 * mu_pas * u_media / raio_m ** 2


def reynolds(rho: float, u_media: float, diametro_m: float, mu_pas: float) -> float:
    """Número de Reynolds Re = rho U D / mu (abaixo de cerca de 2000 o escoamento num tubo é laminar)."""
    return rho * u_media * diametro_m / mu_pas


def womersley(raio_m: float, frequencia_hz: float, rho: float, mu_pas: float) -> float:
    """Número de Womersley alfa = R sqrt(omega rho / mu).

    Em linguagem simples: compara a rapidez da pulsação com o tempo que a viscosidade leva a "acertar" o perfil.
    Com alfa pequeno (perto de 1 a 3), o perfil acompanha a pulsação quase como se cada instante fosse estável.
    """
    return raio_m * np.sqrt(2.0 * np.pi * frequencia_hz * rho / mu_pas)
