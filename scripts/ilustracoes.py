"""Ilustrações técnicas dos cinco dispositivos (desenho próprio), em SVG de traço uniforme.

Todas usam viewBox 0 0 120 120, sem preenchimento, traço com cantos redondos e a cor herdada do texto
(currentColor), para servirem na apresentação, no poster, no folheto e na aplicação.
A malha do stent e a treliça do scaffold são calculadas (projeção de pontos 3D), não desenhadas à mão.
"""
from __future__ import annotations

import math

NOMES = {"haste": "Haste femoral", "par": "Par articular", "stent": "Stent coronário", "scaffold": "Scaffold ósseo",
         "dentario": "Implante dentário"}


def _f(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".")


def _linha(pontos: list[tuple[float, float]]) -> str:
    return "M" + " L".join(f"{_f(x)} {_f(y)}" for x, y in pontos)


# ------------------------------------------------------------------ haste femoral
def haste() -> str:
    """Haste cónica com colo inclinado e cabeça esférica, dentro do contorno do fémur (tracejado)."""
    femur = ('<path d="M48 116 V86 C48 74 44 64 36 57" stroke-dasharray="3 5"/>'
             '<path d="M48 30 C54 32 60 32 66 28 C72 22 82 22 87 30 C91 38 88 52 85 64 C84 70 84 76 84 84 V116" '
             'stroke-dasharray="3 5"/>')
    corpo = ('<path d="M61 106 C60 92 58 78 56 68 C55 61 51 56 46 52"/>'
             '<path d="M67 106 C69 88 72 68 74 52 C75 46 72 43 67 42 L51 38"/>'
             '<path d="M61 106 C62 111 66 111 67 106"/>')
    cabeca = '<circle cx="36" cy="42" r="13"/>'
    return femur + corpo + cabeca


# ------------------------------------------------------------------ par articular
def par() -> str:
    """Corte da cabeça dentro da taça acetabular, com o revestimento (liner) entre as duas."""
    cx, cy = 60, 62
    taca = (f'<path d="M14 {cy} A46 46 0 0 1 106 {cy} H96 A36 36 0 0 0 24 {cy} Z"/>')
    liner_int = f'<path d="M30 {cy} A30 30 0 0 1 90 {cy}"/><path d="M24 {cy} H30 M90 {cy} H96"/>'
    # tracejado radial do revestimento: torna visível a camada entre a taça e a cabeça
    riscas = []
    for a in range(15, 180, 15):
        t = math.radians(a)
        riscas.append(_linha([(cx + 31.5 * math.cos(t), cy - 31.5 * math.sin(t)),
                              (cx + 34.5 * math.cos(t), cy - 34.5 * math.sin(t))]))
    cabeca = f'<circle cx="{cx}" cy="{cy + 1}" r="25"/>'
    d = (math.cos(math.radians(60)), math.sin(math.radians(60)))
    n = (-d[1], d[0])
    a0 = (cx + 24 * d[0], cy + 1 + 24 * d[1])
    a1 = (cx + 50 * d[0], cy + 1 + 50 * d[1])
    colo = (f'<path d="{_linha([(a0[0] + 6 * n[0], a0[1] + 6 * n[1]), (a1[0] + 7 * n[0], a1[1] + 7 * n[1])])}"/>'
            f'<path d="{_linha([(a0[0] - 6 * n[0], a0[1] - 6 * n[1]), (a1[0] - 7 * n[0], a1[1] - 7 * n[1])])}"/>')
    return taca + liner_int + f'<path d="{" ".join(riscas)}" stroke-width="1.6"/>' + cabeca + colo


# ------------------------------------------------------------------ stent
def _stent_ponto(u: float, t: float) -> tuple[float, float]:
    """Ponto da superfície do cilindro: u ao longo do eixo (0 a 1), t em graus à volta (-90 a 90, face visível)."""
    x0, x1, cy, R, rx = 26, 94, 60, 26, 9
    r = math.radians(t)
    return x0 + u * (x1 - x0) + rx * math.cos(r), cy + R * math.sin(r)


def stent(celulas_u: int = 4, celulas_t: int = 3) -> str:
    """Cilindro em perspetiva com malha em losangos (duas famílias de hélices)."""
    partes = ['<ellipse cx="26" cy="60" rx="9" ry="26"/>', '<path d="M26 34 H94 M26 86 H94"/>',
              '<path d="M94 34 A9 26 0 0 1 94 86"/>']
    dt, du = 180 / celulas_t, 1 / celulas_u
    malha = []
    for sinal in (1, -1):
        for k in range(-2 * celulas_u - 2, 2 * celulas_t + 2):
            c = -90 + k * dt
            pts = [_stent_ponto(i / 60, c + sinal * dt / du * i / 60) for i in range(61)
                   if -90 <= c + sinal * dt / du * i / 60 <= 90]
            if len(pts) > 1:
                malha.append(_linha(pts))
    partes.append(f'<path d="{" ".join(malha)}" stroke-width="1.6"/>')
    return "".join(partes)


# ------------------------------------------------------------------ scaffold
def _proj(x: float, y: float, z: float, escala: float = 30, cx: float = 60, cy: float = 64) -> tuple[float, float]:
    """Projeção axonométrica (rotação de 35° e inclinação de 28°), com y para cima."""
    a, b = math.radians(35), math.radians(28)
    xr = x * math.cos(a) - z * math.sin(a)
    zr = x * math.sin(a) + z * math.cos(a)
    yr = y * math.cos(b) - zr * math.sin(b)
    return cx + escala * xr, cy - escala * yr


def scaffold(camadas: int = 5, filamentos: int = 4) -> str:
    """Cubo poroso impresso em 3D: camadas de filamentos cruzadas a 90° (estrutura em grelha de toros).

    Cada filamento é desenhado como um traço largo da cor do texto com um traço mais estreito da cor do
    fundo por cima (contorno com pontas redondas); a ordem de trás para a frente esconde o que fica atrás.
    A cor do fundo vem da variável CSS --fundo (branco por omissão).
    """
    largo, estreito = 13, 8
    passo = 2.0 / filamentos
    pos = [-1 + passo / 2 + k * passo for k in range(filamentos)]
    altura = 0.40
    y0 = -(camadas - 1) * altura / 2
    pecas = []
    for c in range(camadas):
        y = y0 + c * altura
        for q in pos:
            if c % 2 == 0:
                p0, p1 = (-0.92, y, q), (0.92, y, q)
            else:
                p0, p1 = (q, y, -0.92), (q, y, 0.92)
            meio = [(a_ + b_) / 2 for a_, b_ in zip(p0, p1)]
            a_, b_ = math.radians(35), math.radians(28)
            zr = meio[0] * math.sin(a_) + meio[2] * math.cos(a_)
            prof = meio[1] * math.sin(b_) + zr * math.cos(b_)
            pecas.append((c, prof, _linha([_proj(*p0, escala=34, cy=62), _proj(*p1, escala=34, cy=62)])))
    pecas.sort(key=lambda x: (x[0], x[1]))
    return "".join(f'<path d="{d}" stroke-width="{largo}"/><path d="{d}" stroke-width="{estreito}" '
                   f'style="stroke:var(--fundo,#fff)"/>' for _, _, d in pecas)


# ------------------------------------------------------------------ implante dentário
def dentario() -> str:
    """Parafuso com rosca, pilar e coroa."""
    coroa = ('<path d="M38 26 C38 16 46 13 52 17 C56 13 64 13 68 17 C74 13 82 16 82 26 C82 36 78 42 74 44 '
             'H46 C42 42 38 36 38 26 Z"/>')
    pilar = '<path d="M50 44 L52 56 H68 L70 44"/>'
    # corpo cónico com rosca: perfil em dente de serra dos dois lados
    esq, dir_ = [], []
    y, k = 58.0, 0
    while y <= 100:
        w = 11 - (y - 58) * 0.08
        dente = 3.2 if k % 2 == 0 else 0
        esq.append((60 - w - dente, y))
        dir_.append((60 + w + dente, y + 2.5))
        y += 4.5
        k += 1
    corpo = _linha([(48, 56)] + esq + [(55, 106)]) + " Q60 110 65 106 " + \
        " ".join(f"L{_f(x)} {_f(yy)}" for x, yy in reversed(dir_)) + " L72 56"
    rosca = " ".join(_linha([(esq[i][0] + 2, esq[i][1]), (dir_[i][0] - 2, dir_[i][1])])
                     for i in range(0, len(esq), 2))
    return coroa + pilar + f'<path d="{corpo}"/><path d="{rosca}" stroke-width="1.6"/>'


ILUSTRACOES = {"haste": haste(), "par": par(), "stent": stent(), "scaffold": scaffold(), "dentario": dentario()}


def svg_icone(nome: str, tamanho: int = 96, traco: float = 2.5) -> str:
    """Ilustração de um dispositivo em SVG: traço uniforme, cantos redondos, cor herdada (currentColor)."""
    return (f'<svg viewBox="0 0 120 120" width="{tamanho}" height="{tamanho}" fill="none" stroke="currentColor" '
            f'stroke-width="{traco}" stroke-linecap="round" stroke-linejoin="round" role="img" '
            f'aria-label="{NOMES[nome]}">{ILUSTRACOES[nome]}</svg>')
