"""Cargas da marcha: força de contacto da anca e força dos abdutores, e a sua distribuição pelos nós.

Fontes (ver docs/FEA_HASTE.md, capítulo 4):
- caso de carga da marcha de Heller et al. 2005 (J Biomech 38:1155-1163, doi:10.1016/j.jbiomech.2004.05.022):
  contacto da anca (-54,0; -32,8; -229,2) % do peso corporal e abdutores (58,0; 4,3; 86,5) % do peso, no
  referencial do fémur de Heller (x medial, y anterior, z proximal). O original não foi lido; os valores
  coincidem em duas reproduções independentes: Baharuddin et al. 2014 (BMC Musculoskelet Disord 15:30,
  doi:10.1186/1471-2474-15-30, Tabela 3, em N para 700 N, citando Heller 2005) e, para os abdutores, Johnson et
  al. 2023 (Biomed Eng Comput Biol 14, doi:10.1177/11795972231166240, Tabela 2) [confirmar no original];
- o módulo do contacto (238,4 % do peso) bate com o pico medido na marcha do doente médio, 238 % do peso
  (Bergmann et al. 2001, J Biomech 34:859-871, doi:10.1016/S0021-9290(01)00040-9, resumo, lido no original);
- a direção é coerente com a das cargas normalizadas medidas in vivo na marcha (Bergmann et al. 2016, PLOS ONE
  11:e0155612, doi:10.1371/journal.pone.0155612, Tabela 5: 17° no plano frontal, intervalo 9° a 21°, e 11° no
  sagital); aqui 13° e 8°.
"""

from __future__ import annotations

import numpy as np

G = 9.81  # m/s2
PESO_DESENHO_KG = 75.0  # valor de desenho

CONTACTO_PCT = (-54.0, -32.8, -229.2)  # Heller et al. 2005, marcha (via Baharuddin et al. 2014, Tabela 3)
ABDUTORES_PCT = (58.0, 4.3, 86.5)  # Heller et al. 2005, marcha (Baharuddin 2014, Tabela 3; Johnson 2023, Tabela 2)
CONTACTO_BERGMANN_PCT = 238.0  # Bergmann et al. 2001, resumo: pico da marcha do doente médio (verificação)


def forcas_marcha(peso_kg: float = PESO_DESENHO_KG) -> dict[str, np.ndarray]:
    """Forças (N) no referencial anatómico (medial, anterior, proximal) no pico da marcha.

    Em linguagem simples: converte em newtons as percentagens do peso corporal do caso de carga da marcha
    de Heller 2005 (contacto da anca e abdutores), tal como estão.
    """
    pc = peso_kg * G / 100.0
    return {"contacto": np.asarray(CONTACTO_PCT, float) * pc, "abdutores": np.asarray(ABDUTORES_PCT, float) * pc}


def angulos_contacto(v=CONTACTO_PCT) -> tuple[float, float]:
    """Ângulos (graus) da força de contacto com o eixo do fémur nos planos frontal e sagital.

    Em linguagem simples: o quanto a força se inclina para o lado (frontal, atan |Fx| / |Fz|) e para a frente
    ou para trás (sagital, atan |Fy| / |Fz|); servem para comparar com as cargas medidas de Bergmann 2016.
    """
    x, y, z = (abs(float(c)) for c in v)
    return float(np.degrees(np.arctan2(x, z))), float(np.degrees(np.arctan2(y, z)))


def para_referencial(v_anatomico, medial, anterior, proximal) -> np.ndarray:
    """Passa um vetor de (medial, anterior, proximal) para o referencial da malha.

    Em linguagem simples: cada componente multiplica o eixo anatómico correspondente, já escrito nas
    coordenadas da malha.
    """
    v = np.asarray(v_anatomico, float)
    return v[0] * np.asarray(medial) + v[1] * np.asarray(anterior) + v[2] * np.asarray(proximal)


def nos_superficie(ligacoes: np.ndarray, n_nos: int) -> np.ndarray:
    """Nós da superfície de uma malha de vóxeis: os que pertencem a menos de 8 cubos.

    Em linguagem simples: um nó no meio do material está rodeado por 8 cubos; à superfície tem menos.
    """
    return np.bincount(np.asarray(ligacoes).ravel(), minlength=n_nos) < 8


def nos_calote(pontos, superficie, centro, direcao_forca, raio_max: float, angulo_graus: float = 30.0):
    """Nós da superfície da cabeça onde a força de contacto entra (uma calote esférica).

    Em linguagem simples: ficam os nós à superfície, a menos de raio_max do centro da cabeça, e dentro de um
    cone com o eixo virado para onde a força vem (a força aponta para dentro da cabeça).
    """
    v = np.asarray(pontos, float) - np.asarray(centro, float)
    dist = np.linalg.norm(v, axis=1)
    u = -np.asarray(direcao_forca, float) / np.linalg.norm(direcao_forca)
    with np.errstate(invalid="ignore", divide="ignore"):
        cos = (v @ u) / dist
    return np.flatnonzero(superficie & (dist < raio_max) & (cos > np.cos(np.radians(angulo_graus))))


def topo_trocanter(vf, x_min: float = 0.0) -> np.ndarray:
    """Topo do grande trocânter: o vértice mais alto (y) da malha anatómica do lado lateral (x > x_min).

    Em linguagem simples: calcula-se na malha do fémur e não na malha de cálculo, para o sítio da carga dos
    abdutores ser o mesmo em todos os tamanhos de malha.
    """
    vf = np.asarray(vf, float)
    lado = vf[vf[:, 0] > x_min]
    return lado[np.argmax(lado[:, 1])]


def nos_trocanter(pontos, superficie_osso, topo, raio: float = 10.0):
    """Nós da zona de inserção dos abdutores no topo do grande trocânter.

    Em linguagem simples: a força dos abdutores reparte-se pelos nós da superfície do osso a menos de 'raio'
    mm do topo do trocânter (raio: valor de desenho).
    """
    p = np.asarray(pontos, float)
    cand = np.flatnonzero(superficie_osso)
    return cand[np.linalg.norm(p[cand] - np.asarray(topo, float), axis=1) < raio]


def distribuir(nos, forca, n_nos: int) -> np.ndarray:
    """Vetor de forças nodais com a força total repartida igualmente pelos nós dados.

    Em linguagem simples: cada nó recebe a mesma fração da força; a soma é a força total.
    """
    f = np.zeros(3 * n_nos)
    nos = np.asarray(nos, int)
    if len(nos) == 0:
        raise ValueError("nenhum nó para aplicar a força")
    for c in range(3):
        f[3 * nos + c] += forca[c] / len(nos)
    return f
