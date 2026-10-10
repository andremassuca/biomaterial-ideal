"""Zonas de Gruen à volta da haste (Gruen, McNeice e Amstutz 1979, Clin Orthop Relat Res 141:17-27,
doi:10.1097/00003086-197906000-00002).

Na radiografia de frente, o osso à volta da haste divide-se em 7 zonas: 1 a 3 do lado lateral (de cima para
baixo), 4 abaixo da ponta, 5 a 7 do lado medial (de baixo para cima). Aqui, a parte da haste dentro do osso
divide-se em terços ao longo do eixo; a fronteira lateral/medial é o plano do eixo da haste (x = 0). A
divisão em terços e a altura da zona 4 são a convenção usual [confirmar a definição exata no original].
"""

from __future__ import annotations

import numpy as np


def zonas_gruen(pontos, comprimento_intraosseo: float, altura_zona4: float | None = None) -> np.ndarray:
    """Zona de Gruen (1 a 7) de cada ponto no referencial da haste; 0 fora das zonas.

    Em linguagem simples: y é a altura ao longo da haste (ponta em y = 0) e x > 0 é o lado lateral. O terço
    de cima dá as zonas 1 (lateral) e 7 (medial); o do meio, 2 e 6; o de baixo, 3 e 5; abaixo da ponta, até
    um terço do comprimento (por defeito), fica a zona 4. As zonas 1 e 7 não têm limite superior: vão até onde
    houver osso (grande trocânter e calcar).
    """
    p = np.asarray(pontos, float)
    x, y = p[:, 0], p[:, 1]
    L = float(comprimento_intraosseo)
    h4 = L / 3 if altura_zona4 is None else float(altura_zona4)
    z = np.zeros(len(p), int)
    lateral = x >= 0
    terco = np.where(y >= 2 * L / 3, 0, np.where(y >= L / 3, 1, np.where(y >= 0, 2, -1)))
    z[(terco == 0) & lateral], z[(terco == 1) & lateral], z[(terco == 2) & lateral] = 1, 2, 3
    z[(terco == 2) & ~lateral], z[(terco == 1) & ~lateral], z[(terco == 0) & ~lateral] = 5, 6, 7
    z[(y < 0) & (y >= -h4)] = 4
    return z


def comprimento_intraosseo(base_colo, d_colo, alem_base: float = 3.0) -> float:
    """Altura (ao longo da haste) onde o plano da osteotomia corta o eixo da haste (x = 0, z = 0).

    Em linguagem simples: o plano do corte do colo é normal ao eixo do colo e passa 'alem_base' mm além da
    base do colo; a parte da haste abaixo desse ponto do eixo é a que fica dentro do osso.
    """
    b, d = np.asarray(base_colo, float), np.asarray(d_colo, float)
    q = b + alem_base * d
    # (p - q) . d = 0 com p = (0, y, 0)
    return float(q[1] + q[0] * d[0] / d[1] + q[2] * d[2] / d[1])
