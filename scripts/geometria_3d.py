"""Geometria dos modelos 3D dos dispositivos (só numpy, sem Blender).

As funções daqui são usadas pelo scripts/renders_blender.py (dentro do Blender) e podem vir a ser usadas pela
aplicação. Todas as medidas estão em milímetros.

As formas são ilustrativas: servem para os renders e não para fabrico.
"""

from __future__ import annotations

import numpy as np


def campo_giroide(x, y, z, periodo: float = 1.0):
    """Valor da superfície giroide em cada ponto.

    Em linguagem simples: o giroide é uma superfície curva que divide o espaço em dois labirintos ligados. A
    fórmula sin(x)cos(y) + sin(y)cos(z) + sin(z)cos(x) dá 0 em cima da superfície, valores positivos de um lado e
    negativos do outro. O período é o tamanho de uma célula (em mm).
    """
    k = 2 * np.pi / periodo
    x, y, z = k * np.asarray(x), k * np.asarray(y), k * np.asarray(z)
    return np.sin(x) * np.cos(y) + np.sin(y) * np.cos(z) + np.sin(z) * np.cos(x)


def porosidade_giroide(limiar: float, n: int = 48) -> float:
    """Fração de vazio de um giroide sólido cortado no limiar dado.

    Em linguagem simples: o material fica onde o campo do giroide é maior do que o limiar; o resto é poro. Conta-se
    numa grelha de n × n × n pontos de uma célula a fração de pontos que ficam vazios. Limiar 0 dá 50 % de poros;
    limiares maiores dão mais poros.
    """
    t = (np.arange(n) + 0.5) / n
    x, y, z = np.meshgrid(t, t, t, indexing="ij")
    return float(np.mean(campo_giroide(x, y, z) <= limiar))


def limiar_para_porosidade(porosidade: float, n: int = 48) -> float:
    """Limiar do giroide que dá a porosidade pedida (entre 0,05 e 0,95).

    Em linguagem simples: procura por bisseção o limiar em que a fração de poros é a pedida; serve para o
    deslizador de porosidade da aplicação e para o render do scaffold.
    """
    if not 0.05 <= porosidade <= 0.95:
        raise ValueError("a porosidade tem de estar entre 0,05 e 0,95")
    baixo, alto = -1.5, 1.5
    for _ in range(40):
        meio = (baixo + alto) / 2
        if porosidade_giroide(meio, n) < porosidade:
            baixo = meio
        else:
            alto = meio
    return (baixo + alto) / 2


def rede_stent(raio: float, comprimento: float, n_coroas: int, n_picos: int, ligacoes_por_anel: int = 3,
               folga: float = 0.2):
    """Linhas centrais dos struts de um stent em anéis de zigue-zague (malha de losangos).

    Em linguagem simples: um stent expansível por balão é feito de anéis em zigue-zague (coroas) ligados por pontes.
    Cada anel tem n_picos picos à volta do tubo; anéis vizinhos estão desfasados meio pico. A folga é a fração do
    passo entre anéis: com folga 0 os picos de um anel tocam nos vales do seguinte e a malha fica toda em losangos
    fechados (sem pontes); com folga maior há pontes. Devolve uma lista de polilinhas; cada polilinha é um array
    (k, 3) de pontos em mm, com o eixo do stent em z.
    """
    if n_coroas < 2 or n_picos < 3:
        raise ValueError("são precisas pelo menos 2 coroas e 3 picos")
    if not 1 <= ligacoes_por_anel <= n_picos:
        raise ValueError("as ligações por anel têm de estar entre 1 e o número de picos")
    if not 0 <= folga < 1:
        raise ValueError("a folga tem de estar entre 0 e 1")
    passo = comprimento / n_coroas
    altura = (1 - folga) * passo
    k = 0.97  # arredondamento das coroas: perto de 1, struts direitos e curvas apertadas nos picos
    theta = np.linspace(0, 2 * np.pi, 48 * n_picos + 1)
    linhas = []
    for i in range(n_coroas):
        z0 = i * passo + (passo - altura) / 2
        fase = (i % 2) * np.pi / n_picos  # anéis alternados desfasados meio pico: formam losangos
        w = np.arcsin(k * np.cos(n_picos * theta)) / np.arcsin(k)
        a = theta + fase
        linhas.append(np.column_stack([raio * np.cos(a), raio * np.sin(a), z0 + altura * (1 - w) / 2]))
        if i < n_coroas - 1 and folga > 0:
            # pontes do topo deste anel à base do seguinte (os dois estão no mesmo ângulo por causa do desfasamento)
            z1, z2 = z0 + altura, z0 + passo
            for j in range(ligacoes_por_anel):
                pico = (j * n_picos) // ligacoes_por_anel
                ang = fase + (2 * pico + 1) * np.pi / n_picos
                t = np.linspace(0, 1, 8)
                curva = ang + 0.25 * (np.pi / n_picos) * np.sin(2 * np.pi * t) * (z2 - z1) / passo
                linhas.append(np.column_stack([raio * np.cos(curva), raio * np.sin(curva), z1 + (z2 - z1) * t]))
    return linhas


def perfil_balao(raio: float, comprimento: float, cone: float, raio_cateter: float, n: int = 24):
    """Perfil (r, z) de um balão de angioplastia insuflado, para rodar à volta do eixo z.

    Em linguagem simples: o balão é um cilindro com dois cones nas pontas que acabam no cateter. Devolve os pontos
    do contorno de baixo para cima; os cones são suavizados com um cosseno.
    """
    t = np.linspace(0, 1, n)
    suave = (1 - np.cos(np.pi * t)) / 2
    baixo = np.column_stack([raio_cateter + (raio - raio_cateter) * suave, -cone + cone * t])
    meio = np.array([[raio, 0.0], [raio, comprimento]])
    cima = np.column_stack([raio - (raio - raio_cateter) * suave, comprimento + cone * t])
    return np.vstack([baixo[:-1], meio, cima[1:]])


def ajustar_esfera(pontos):
    """Centro e raio da esfera que melhor passa pelos pontos (mínimos quadrados).

    Em linguagem simples: serve para achar o centro da cabeça do fémur e do acetábulo a partir dos vértices da
    malha anatómica. Resolve |p - c|² = r² como um sistema linear.
    """
    p = np.asarray(pontos, dtype=float)
    A = np.c_[2 * p, np.ones(len(p))]
    b = (p ** 2).sum(1)
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    centro = sol[:3]
    return centro, float(np.sqrt(sol[3] + centro @ centro))


def eixo_principal(pontos, para_cima=(0, 0, 1)):
    """Centro e direção principal de uma nuvem de pontos (análise de componentes principais).

    Em linguagem simples: a direção em que os pontos mais se espalham; serve para o eixo da diáfise do fémur e o
    eixo longo do dente. O sinal escolhe-se para apontar para o mesmo lado de 'para_cima'.
    """
    p = np.asarray(pontos, dtype=float)
    centro = p.mean(0)
    _, _, vt = np.linalg.svd(p - centro, full_matrices=False)
    eixo = vt[0] * (1 if vt[0] @ np.asarray(para_cima) >= 0 else -1)
    return centro, eixo


def colocar_haste(cabeca, ponto_eixo, eixo, altura=140.0, offset=41.0):
    """Posição e orientação da haste no fémur: ponta no eixo do canal e centro da cabeça no centro anatómico.

    Em linguagem simples: no referencial da haste o centro da cabeça está à altura 'altura' e ao 'offset' medial
    da ponta. Procura-se o ponto T do eixo do canal (abaixo da cabeça) cuja distância à cabeça é igual à da
    haste; depois roda-se a haste no plano coronal para o centro da cabeça cair exatamente no centro anatómico.
    Devolve a ponta (origem), o eixo da haste e a direção medial da haste (vetores unitários).
    """
    H, C0, a = (np.asarray(v, dtype=float) for v in (cabeca, ponto_eixo, eixo))
    a = a / np.linalg.norm(a)
    v = H - C0
    m = v - (v @ a) * a
    m /= np.linalg.norm(m)
    D = np.hypot(altura, offset)
    # |C0 + t a - H|² = D²  →  t² - 2 t (v·a) + |v|² - D² = 0 ; a raiz menor fica abaixo da cabeça
    va = v @ a
    disc = va ** 2 - (v @ v - D ** 2)
    if disc < 0:
        raise ValueError("o eixo do canal está longe demais da cabeça para esta haste")
    T = C0 + (va - np.sqrt(disc)) * a
    w = (H - T) / D
    ang_w = np.arctan2(w @ m, w @ a)
    ang_s = ang_w - np.arctan2(offset, altura)
    eixo_haste = np.cos(ang_s) * a + np.sin(ang_s) * m
    medial = -np.sin(ang_s) * a + np.cos(ang_s) * m
    return T, eixo_haste, medial


def ler_obj(caminho):
    """Lê vértices e triângulos de um ficheiro OBJ simples (como os do BodyParts3D).

    Em linguagem simples: guarda as linhas 'v x y z' como vértices e as linhas 'f a b c' como triângulos
    (índices a começar em 0); ignora normais e texturas.
    """
    verts, faces = [], []
    with open(caminho, encoding="utf-8", errors="ignore") as f:
        for linha in f:
            if linha.startswith("v "):
                verts.append([float(v) for v in linha.split()[1:4]])
            elif linha.startswith("f "):
                idx = [int(p.split("/")[0]) - 1 for p in linha.split()[1:]]
                faces += [[idx[0], idx[i], idx[i + 1]] for i in range(1, len(idx) - 1)]
    return np.array(verts), np.array(faces, dtype=int)


def cortar_malha(verts, faces, normal, ponto):
    """Segmentos da interseção de uma malha de triângulos com um plano.

    Em linguagem simples: para cada triângulo que atravessa o plano, calcula os dois pontos onde as arestas o
    cortam; o conjunto dos segmentos desenha o contorno da secção (como numa radiografia de uma fatia).
    Devolve um array (k, 2, 3).
    """
    n = np.asarray(normal, float)
    d = (np.asarray(verts, float) - np.asarray(ponto, float)) @ n
    segs = []
    for tri in faces:
        dt = d[tri]
        pts = []
        for i, j in ((0, 1), (1, 2), (2, 0)):
            if (dt[i] > 0) != (dt[j] > 0):
                s = dt[i] / (dt[i] - dt[j])
                pts.append(verts[tri[i]] + s * (verts[tri[j]] - verts[tri[i]]))
        if len(pts) == 2:
            segs.append(pts)
    return np.array(segs)


def dentro_da_seccao(pontos2d, segmentos2d):
    """Diz, para cada ponto 2D, se está dentro da secção limitada pelos segmentos (regra par-ímpar).

    Em linguagem simples: lança um raio horizontal a partir do ponto e conta quantas vezes cruza o contorno;
    um número ímpar de cruzamentos quer dizer que o ponto está dentro.
    """
    p = np.asarray(pontos2d, float)
    a, b = segmentos2d[:, 0], segmentos2d[:, 1]
    dentro = np.zeros(len(p), bool)
    for (x0, y0), (x1, y1) in zip(a, b):
        cruza = (y0 > p[:, 1]) != (y1 > p[:, 1])
        with np.errstate(divide="ignore", invalid="ignore"):
            xc = x0 + (p[:, 1] - y0) * (x1 - x0) / (y1 - y0)
        dentro ^= cruza & (p[:, 0] < xc)
    return dentro


def distancia_aos_segmentos(pontos2d, segmentos2d):
    """Distância de cada ponto 2D ao segmento mais próximo do contorno."""
    p = np.asarray(pontos2d, float)[:, None, :]
    a, b = segmentos2d[None, :, 0], segmentos2d[None, :, 1]
    ab = b - a
    t = np.clip(((p - a) * ab).sum(-1) / np.maximum((ab * ab).sum(-1), 1e-12), 0, 1)
    return np.linalg.norm(p - (a + t[..., None] * ab), axis=-1).min(1)
