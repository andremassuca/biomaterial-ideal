"""Malhas: barra de verificação (gmsh, tetraedros) e malhas de vóxeis (hexaedros) a partir de etiquetas."""

from __future__ import annotations

import numpy as np
from scipy import ndimage

from .solver import rigidez_cubo


def malha_barra_gmsh(comprimento: float, largura: float, altura: float, tamanho: float):
    """Barra retangular (x de 0 ao comprimento) em tetraedros, gerada pelo gmsh e lida pelo scikit-fem.

    Em linguagem simples: desenha uma caixa no gmsh, pede uma malha de tetraedros com o tamanho dado e passa
    os nós e os tetraedros para o scikit-fem (MeshTet). A secção fica centrada em y = 0 e z = 0.
    """
    import gmsh
    import skfem

    iniciado = gmsh.isInitialized()
    if not iniciado:
        gmsh.initialize(interruptible=False)
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add("barra")
        gmsh.model.occ.addBox(0, -largura / 2, -altura / 2, comprimento, largura, altura)
        gmsh.model.occ.synchronize()
        gmsh.option.setNumber("Mesh.MeshSizeMin", tamanho)
        gmsh.option.setNumber("Mesh.MeshSizeMax", tamanho)
        gmsh.model.mesh.generate(3)
        tags, coords, _ = gmsh.model.mesh.getNodes()
        p = coords.reshape(-1, 3)
        indice = np.full(int(tags.max()) + 1, -1)
        indice[tags.astype(int)] = np.arange(len(tags))
        _, nos = gmsh.model.mesh.getElementsByType(4)  # 4 = tetraedro de 4 nós
        t = indice[nos.astype(int).reshape(-1, 4)]
        gmsh.model.remove()
    finally:
        if not iniciado:
            gmsh.finalize()
    usados = np.unique(t)
    novo = np.full(len(p), -1)
    novo[usados] = np.arange(len(usados))
    return skfem.MeshTet(np.ascontiguousarray(p[usados].T), np.ascontiguousarray(novo[t].T))


def dentro_por_raios(verts, faces, origem, h: float, forma, eixo: int = 2) -> np.ndarray:
    """Diz, para cada centro de vóxel de uma grelha, se está dentro de uma malha de triângulos fechada.

    Em linguagem simples: lança raios paralelos a um eixo, um por coluna de vóxeis, e regista onde cada raio
    atravessa a superfície; ao longo do raio, o ponto fica dentro depois de um número ímpar de travessias
    (regra par-ímpar). Os centros dos vóxeis estão em origem + (i + 0,5) h. Devolve um array booleano 'forma'.
    """
    v = (np.asarray(verts, float) - np.asarray(origem, float)) / h - 0.5  # coordenadas em índices de vóxel
    f = np.asarray(faces, int)
    a, b = [i for i in range(3) if i != eixo]
    na, nb, nr = forma[a], forma[b], forma[eixo]
    P = v[f]  # (nt, 3, 3)
    pa, pb, pr = P[:, :, a], P[:, :, b], P[:, :, eixo]
    ia0 = np.clip(np.ceil(pa.min(1)), 0, na).astype(int)
    ia1 = np.clip(np.floor(pa.max(1)), -1, na - 1).astype(int)
    ib0 = np.clip(np.ceil(pb.min(1)), 0, nb).astype(int)
    ib1 = np.clip(np.floor(pb.max(1)), -1, nb - 1).astype(int)
    ca, cb = np.maximum(ia1 - ia0 + 1, 0), np.maximum(ib1 - ib0 + 1, 0)
    n = ca * cb
    tri = np.repeat(np.arange(len(f)), n)
    k = np.arange(n.sum()) - np.repeat(np.cumsum(n) - n, n)
    I = ia0[tri] + k // np.maximum(cb[tri], 1)
    J = ib0[tri] + k % np.maximum(cb[tri], 1)
    # coordenadas baricêntricas do centro da coluna na projeção do triângulo (com um desvio mínimo para não
    # cair exatamente em arestas ou vértices)
    x, y = I + 1.234e-7, J + 2.345e-7
    x0, y0 = pa[tri, 0], pb[tri, 0]
    x1, y1 = pa[tri, 1], pb[tri, 1]
    x2, y2 = pa[tri, 2], pb[tri, 2]
    det = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
    with np.errstate(divide="ignore", invalid="ignore"):
        l1 = ((x - x0) * (y2 - y0) - (x2 - x0) * (y - y0)) / det
        l2 = ((x1 - x0) * (y - y0) - (x - x0) * (y1 - y0)) / det
        ok = (det != 0) & (l1 >= 0) & (l2 >= 0) & (l1 + l2 <= 1)
    I, J, tri, l1, l2 = I[ok], J[ok], tri[ok], l1[ok], l2[ok]
    zr = (1 - l1 - l2) * pr[tri, 0] + l1 * pr[tri, 1] + l2 * pr[tri, 2]
    kz = np.clip(np.floor(zr).astype(int) + 1, 0, nr)  # primeiro centro depois da travessia
    trocas = np.zeros((na, nb, nr + 1), np.int32)
    np.add.at(trocas, (I, J, kz), 1)
    dentro = (np.cumsum(trocas, axis=2)[:, :, :nr] % 2).astype(bool)
    ordem = [0, 0, 0]
    ordem[a], ordem[b], ordem[eixo] = 0, 1, 2
    return np.transpose(dentro, ordem)


def dentro_da_malha(verts, faces, origem, h: float, forma) -> np.ndarray:
    """Teste de interior por maioria de três direções de raios (x, y e z).

    Em linguagem simples: se a malha anatómica tiver pequenos buracos, um raio que passe por um deles conta
    mal; votar entre as três direções corrige quase todos esses erros.
    """
    votos = sum(dentro_por_raios(verts, faces, origem, h, forma, e).astype(np.int8) for e in range(3))
    return votos >= 2


def maior_componente(ativos: np.ndarray) -> np.ndarray:
    """Fica só com o maior bloco de vóxeis ligados pelas faces.

    Em linguagem simples: pedaços soltos (ou presos só por uma aresta) não têm rigidez para os segurar e
    tornariam o sistema impossível de resolver; por isso retiram-se.
    """
    rot, n = ndimage.label(ativos)
    if n <= 1:
        return ativos.copy()
    tamanhos = np.bincount(rot.ravel())
    tamanhos[0] = 0
    return rot == tamanhos.argmax()


def malha_voxeis(ativos: np.ndarray, origem, h: float):
    """Nós e ligações de uma malha de hexaedros com um cubo por vóxel ativo.

    Em linguagem simples: cada vóxel ativo passa a ser um elemento cúbico; os cantos partilhados por vóxeis
    vizinhos são o mesmo nó (a malha fica contínua). Devolve (pontos (n, 3) em mm, ligações (ne, 8),
    índices (ne, 3) de cada vóxel na grelha), com os cantos pela ordem de rigidez_cubo.
    """
    _, cantos = rigidez_cubo(0.3)
    ijk = np.argwhere(ativos)
    forma_nos = np.array(ativos.shape) + 1
    ids = ((ijk[:, None, :] + cantos[None, :, :]) * np.array([forma_nos[1] * forma_nos[2], forma_nos[2], 1])).sum(-1)
    unicos, ligacoes = np.unique(ids, return_inverse=True)
    ligacoes = ligacoes.reshape(-1, 8)
    i, r = np.divmod(unicos, forma_nos[1] * forma_nos[2])
    j, k = np.divmod(r, forma_nos[2])
    pontos = np.asarray(origem, float) + h * np.column_stack([i, j, k])
    return pontos, ligacoes, ijk


def etiquetas_grossas(fina: np.ndarray, fator: int, prioridade=None) -> np.ndarray:
    """Etiqueta de cada vóxel grosso pela maioria dos vóxeis finos que contém (fator^3 por vóxel grosso).

    Em linguagem simples: a geometria define-se numa grelha fina; cada elemento da malha de cálculo fica com o
    material que ocupa mais do seu volume. Os empates resolvem-se pelo vóxel fino do canto (0, 0, 0) do
    elemento, uma amostra sem preferência por nenhum material (dar sempre a vitória ao osso nos empates
    engrossava a cortical quando o fator é 2); se o canto não estiver entre os empatados, ganha a etiqueta
    com mais prioridade (por defeito, a de número mais alto). A grelha fina tem de ter dimensões múltiplas
    de 'fator'.
    """
    nx, ny, nz = (s // fator for s in fina.shape)
    f = fina[: nx * fator, : ny * fator, : nz * fator].reshape(nx, fator, ny, fator, nz, fator)
    n_et = int(fina.max()) + 1 if prioridade is None else len(prioridade)
    contagens = np.stack([(f == e).sum(axis=(1, 3, 5)) for e in range(n_et)], axis=-1).astype(float)
    canto = f[:, 0, :, 0, :, 0].astype(int)
    np.put_along_axis(contagens, canto[..., None], np.take_along_axis(contagens, canto[..., None], -1) + 0.5, -1)
    pri = np.arange(n_et) if prioridade is None else np.asarray(prioridade, float)
    contagens += 1e-3 * pri / (pri.max() + 1)
    return contagens.argmax(-1).astype(fina.dtype)
