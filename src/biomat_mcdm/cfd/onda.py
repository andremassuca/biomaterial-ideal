"""Caudal pulsátil na artéria coronária ao longo do ciclo cardíaco.

Fonte dos números: Chodzyński KJ et al. Biomed Eng Online 2015;14:77 (doi:10.1186/s12938-015-0065-x, texto
completo em PMC4527114), Tabela 1, doente 1 (descendente anterior proximal, D = 3,39 mm, o diâmetro mais
próximo dos 3 mm do modelo): velocidade máxima do Doppler (fio ComboWire) mínima 3,7, média 18,6 e máxima
32,9 cm/s; período 1,06 s.

Hipóteses (valores de desenho):
- a velocidade do Doppler é a do eixo; com perfil parabólico, a velocidade média na secção é metade;
- a forma da onda é um só harmónico (cosseno) com o pico na diástole (Davies 2006: "Coronary blood flow peaks
  in diastole"), ajustado à média e à amplitude do doente 1; a onda real tem mais harmónicos.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

U_EIXO_MIN_CMS = 3.7
U_EIXO_MEDIA_CMS = 18.6
U_EIXO_MAX_CMS = 32.9
PERIODO_S = 1.06
FRACAO_PICO = 0.65  # pico a 65 % do ciclo, na diástole (valor de desenho)


@dataclass(frozen=True)
class Onda:
    """Onda de um harmónico: u(t) = u_media (1 + A cos(w (t - t_pico)))."""

    u_media: float  # velocidade média na secção (m/s), média no tempo
    amplitude: float  # A, fração da média
    periodo_s: float
    t_pico_s: float

    @property
    def frequencia_hz(self) -> float:
        return 1.0 / self.periodo_s

    def fator(self, t):
        """Fator multiplicativo da velocidade média no instante t."""
        w = 2 * np.pi / self.periodo_s
        return 1.0 + self.amplitude * np.cos(w * (np.asarray(t, dtype=float) - self.t_pico_s))

    def velocidade(self, t):
        return self.u_media * self.fator(t)

    def coeficientes(self) -> list[tuple[float, float]]:
        """Coeficientes (a1, b1) da série de Fourier do fator: A cos(w t_pico), A sin(w t_pico)."""
        w = 2 * np.pi / self.periodo_s
        return [(self.amplitude * np.cos(w * self.t_pico_s), self.amplitude * np.sin(w * self.t_pico_s))]


def onda_coronaria() -> Onda:
    """Onda do doente 1 de Chodzyński 2015, com a velocidade média na secção = metade da do eixo.

    Em linguagem simples: o sangue nas coronárias acelera e abranda a cada batimento, com mais caudal quando o
    coração relaxa (diástole). A amplitude é metade da diferença entre o máximo e o mínimo medidos, em fração
    da média: (32,9 - 3,7) / 2 / 18,6 = 0,785.
    """
    amplitude = (U_EIXO_MAX_CMS - U_EIXO_MIN_CMS) / 2 / U_EIXO_MEDIA_CMS
    return Onda(u_media=U_EIXO_MEDIA_CMS / 2 / 100, amplitude=amplitude, periodo_s=PERIODO_S,
                t_pico_s=FRACAO_PICO * PERIODO_S)
