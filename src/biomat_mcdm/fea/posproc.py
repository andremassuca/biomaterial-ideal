"""Pós-processamento: energia por zona, razão face ao fémur intacto, stress shielding e convergência."""

from __future__ import annotations

import numpy as np


def energia_por_zona(W, volume_elemento: float, zonas, mascara, lista=(1, 7)) -> dict[int, tuple[float, float]]:
    """Energia total (mJ, com N e mm) e por volume (mJ/mm3, o mesmo que MJ/m3) do osso em cada zona.

    Em linguagem simples: soma a energia dos elementos de osso ('mascara') que caem em cada zona e divide
    pelo volume desses elementos. Devolve zona -> (energia total, energia por volume).
    """
    W, zonas, mascara = np.asarray(W, float), np.asarray(zonas), np.asarray(mascara, bool)
    saida = {}
    for z in lista:
        sel = mascara & (zonas == z)
        total = float(W[sel].sum())
        vol = sel.sum() * volume_elemento
        saida[z] = (total, total / vol if vol > 0 else float("nan"))
    return saida


def razao_e_shielding(implantado: float, intacto: float) -> tuple[float, float]:
    """Razão implantado / intacto e stress shielding (1 menos a razão).

    Em linguagem simples: se o osso à volta da haste guarda metade da energia que guardava sem a haste, a
    razão é 0,5 e o stress shielding é 0,5 (50 % da carga deixou de passar pelo osso).
    """
    r = implantado / intacto
    return r, 1.0 - r


def variacao_relativa(fino: float, anterior: float) -> float:
    """Variação relativa (em %) entre a malha mais fina e a anterior: 100 |fino - anterior| / |fino|."""
    return 100.0 * abs(fino - anterior) / abs(fino)


def corresponder(ijk_a, ijk_b, forma) -> np.ndarray:
    """Para cada elemento de b, o índice do elemento de a no mesmo vóxel (ou -1 se não existir).

    Em linguagem simples: as duas malhas (fémur intacto e implantado) usam a mesma grelha; isto liga os
    elementos que ocupam o mesmo cubo, para comparar a energia no mesmo osso.
    """
    forma = np.asarray(forma)
    chave = lambda ijk: (np.asarray(ijk) * np.array([forma[1] * forma[2], forma[2], 1])).sum(1)
    ka, kb = chave(ijk_a), chave(ijk_b)
    ordem = np.argsort(ka)
    pos = np.searchsorted(ka[ordem], kb)
    pos = np.clip(pos, 0, len(ka) - 1)
    ok = ka[ordem][pos] == kb
    return np.where(ok, ordem[pos], -1)
