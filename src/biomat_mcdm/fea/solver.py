"""Rigidez, resolução e energia de deformação (elasticidade linear, pequenas deformações).

Duas vias:
- malhas gerais (por exemplo, tetraedros do gmsh) com o scikit-fem (resolver_skfem);
- malhas de vóxeis (cubos iguais), em que a matriz de rigidez de cada elemento é a do cubo de referência
  multiplicada pelo módulo de Young do elemento; a do cubo calcula-se uma vez com o scikit-fem
  (rigidez_cubo) e a montagem faz-se com índices (montar_voxeis), o que poupa tempo e memória.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla


def lame(E: float, nu: float) -> tuple[float, float]:
    """Constantes de Lamé (lambda, mu) a partir de E e nu.

    Em linguagem simples: são outra forma de escrever a rigidez de um material isotrópico; mu é o módulo de
    corte (resistência a mudar de forma) e lambda junta o efeito de mudar de volume.
    """
    return E * nu / ((1 + nu) * (1 - 2 * nu)), E / (2 * (1 + nu))


@lru_cache(maxsize=16)
def _rigidez_cubo_cache(nu: float) -> tuple:
    import skfem
    from skfem.models.elasticity import linear_elasticity

    m = skfem.MeshHex.init_tensor(np.array([0.0, 1.0]), np.array([0.0, 1.0]), np.array([0.0, 1.0]))
    b = skfem.Basis(m, skfem.ElementVector(skfem.ElementHex1()), intorder=3)
    lam, mu = lame(1.0, nu)
    K = skfem.asm(linear_elasticity(lam, mu), b).toarray()
    return tuple(map(tuple, K)), tuple(map(tuple, m.p.T.astype(int)))


def rigidez_cubo(nu: float, h: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    """Matriz de rigidez (24 x 24) de um cubo de lado h com E = 1 e cantos do cubo.

    Em linguagem simples: um cubo de material com 8 cantos, cada um com 3 deslocamentos; a matriz diz que
    forças aparecem nos cantos quando estes se deslocam. Num hexaedro trilinear a rigidez escala com h
    (E h), por isso basta calculá-la uma vez para o cubo unitário. Devolve (K, cantos), com cantos (8, 3) em
    0/1 pela ordem dos graus de liberdade (grau = 3 x canto + componente).
    """
    K, cantos = _rigidez_cubo_cache(round(float(nu), 6))
    return np.array(K) * h, np.array(cantos)


def montar_voxeis(ligacoes: np.ndarray, E: np.ndarray, nu: np.ndarray, h: float, n_nos: int) -> sp.csr_matrix:
    """Monta a matriz de rigidez global de uma malha de vóxeis (cubos de lado h).

    Em linguagem simples: cada cubo contribui com a sua matriz (a do cubo de referência vezes o seu E) para os
    graus de liberdade dos seus 8 nós; somam-se todas as contribuições numa matriz esparsa. 'ligacoes' é
    (n_elem, 8) com os nós de cada cubo pela ordem dos cantos de rigidez_cubo.
    """
    ligacoes = np.asarray(ligacoes)
    graus = (3 * ligacoes[:, :, None] + np.arange(3)[None, None, :]).reshape(len(ligacoes), 24)
    linhas, colunas, valores = [], [], []
    for v in np.unique(nu):
        sel = np.flatnonzero(nu == v)
        K0, _ = rigidez_cubo(v, h)
        g = graus[sel]
        linhas.append(np.repeat(g, 24, axis=1).ravel())
        colunas.append(np.tile(g, (1, 24)).ravel())
        valores.append((E[sel, None] * K0.ravel()[None, :]).ravel())
    n = 3 * n_nos
    return sp.coo_matrix((np.concatenate(valores), (np.concatenate(linhas), np.concatenate(colunas))),
                         shape=(n, n)).tocsr()


def montar_voxeis_blocos(ligacoes: np.ndarray, E: np.ndarray, nu: np.ndarray, h: float, n_nos: int,
                         nos_fixos=None, bloco: int = 100000) -> tuple[sp.bsr_matrix, np.ndarray]:
    """Monta a rigidez em blocos 3 x 3 (um por par de nós), já sem os nós presos, poupando memória.

    Em linguagem simples: faz o mesmo que montar_voxeis, mas guarda a matriz como blocos de 3 x 3 por par de
    nós (formato BSR) e trata os elementos aos bocados, para as malhas finas caberem em memória. Os nós
    presos (deslocamento zero) ficam de fora. Devolve (K, nós livres), em que a linha de blocos i corresponde
    ao nó livres[i].
    """
    ligacoes = np.asarray(ligacoes)
    livres = np.ones(n_nos, bool)
    if nos_fixos is not None:
        livres[np.asarray(nos_fixos, int)] = False
    novo = np.full(n_nos, -1, np.int64)
    novo[livres] = np.arange(livres.sum())
    nl = int(livres.sum())
    L = novo[ligacoes]  # (ne, 8), -1 nos nós presos
    # padrão: chaves (linha, coluna) dos pares de nós livres, ordenadas e únicas
    chaves = []
    for i0 in range(0, len(L), bloco):
        Lc = L[i0:i0 + bloco]
        r = np.repeat(Lc, 8, axis=1).ravel()
        c = np.tile(Lc, (1, 8)).ravel()
        ok = (r >= 0) & (c >= 0)
        chaves.append(np.unique(r[ok] * nl + c[ok]))
    chaves = np.unique(np.concatenate(chaves))
    linhas_b = chaves // nl
    indices = (chaves % nl).astype(np.int32)
    indptr = np.zeros(nl + 1, np.int64)
    np.cumsum(np.bincount(linhas_b, minlength=nl), out=indptr[1:])
    dados = np.zeros((len(chaves), 3, 3))
    plano = dados.reshape(len(chaves), 9)
    for v in np.unique(nu):
        K0, _ = rigidez_cubo(v, h)
        B0 = K0.reshape(8, 3, 8, 3).transpose(0, 2, 1, 3).reshape(64, 9)  # blocos (a, b) de 3 x 3
        sel_v = np.flatnonzero(nu == v)
        for i0 in range(0, len(sel_v), bloco):
            sel = sel_v[i0:i0 + bloco]
            Lc = L[sel]
            r = np.repeat(Lc, 8, axis=1).ravel()
            c = np.tile(Lc, (1, 8)).ravel()
            ok = (r >= 0) & (c >= 0)
            pos = np.searchsorted(chaves, r[ok] * nl + c[ok])
            val = (E[sel, None, None] * B0[None, :, :]).reshape(-1, 9)[ok]
            for k in range(9):
                plano[:, k] += np.bincount(pos, weights=val[:, k], minlength=len(chaves))
    K = sp.bsr_matrix((dados, indices, indptr), shape=(3 * nl, 3 * nl))
    return K, np.flatnonzero(livres)


def resolver_voxeis(ligacoes, E, nu, h: float, pontos, forcas, nos_fixos, tol: float = 1e-9) -> np.ndarray:
    """Monta e resolve uma malha de vóxeis grande com gradientes conjugados e multigrelha (pyamg).

    Em linguagem simples: junta montar_voxeis_blocos e o resolvedor iterativo; os nós presos ficam com
    deslocamento zero. Devolve o vetor de deslocamentos de todos os nós (3 por nó).
    """
    import pyamg

    pontos = np.asarray(pontos, float)
    K, livres = montar_voxeis_blocos(ligacoes, E, nu, h, len(pontos), nos_fixos)
    graus = (3 * livres[:, None] + np.arange(3)).ravel()
    B = modos_rigidos(pontos[livres])
    ml = pyamg.smoothed_aggregation_solver(K, B=B, max_coarse=500, smooth="jacobi")
    x, info = spla.cg(K, forcas[graus], rtol=tol, maxiter=3000, M=ml.aspreconditioner(cycle="V"))
    if info != 0:
        raise RuntimeError(f"o gradiente conjugado não convergiu ({info})")
    u = np.zeros(3 * len(pontos))
    u[graus] = x
    return u


def modos_rigidos(pontos: np.ndarray) -> np.ndarray:
    """Os 6 movimentos de corpo rígido (3 translações e 3 rotações) como vetores de deslocamento.

    Em linguagem simples: servem ao pré-condicionador multigrelha (pyamg) para saber que deslocamentos não
    deformam o material; isso acelera muito a resolução em 3D.
    """
    p = np.asarray(pontos, float)
    c = p - p.mean(0)
    B = np.zeros((3 * len(p), 6))
    for i in range(3):
        B[i::3, i] = 1.0
    B[0::3, 3], B[1::3, 3] = -c[:, 1], c[:, 0]
    B[1::3, 4], B[2::3, 4] = -c[:, 2], c[:, 1]
    B[0::3, 5], B[2::3, 5] = c[:, 2], -c[:, 0]
    return B


def resolver(K: sp.csr_matrix, f: np.ndarray, fixos: np.ndarray, pontos: np.ndarray | None = None,
             tol: float = 1e-9, direto_ate: int = 60000) -> np.ndarray:
    """Resolve K u = f com os graus de liberdade 'fixos' a zero.

    Em linguagem simples: tira as linhas e colunas dos graus presos e resolve o resto. Sistemas pequenos vão
    para o método direto; os grandes usam gradientes conjugados com multigrelha algébrica (pyamg), que gasta
    pouca memória. Devolve o vetor de deslocamentos completo.
    """
    n = K.shape[0]
    livre = np.ones(n, bool)
    livre[np.asarray(fixos, int)] = False
    Kl = K[livre][:, livre].tocsr()
    fl = f[livre]
    u = np.zeros(n)
    if Kl.shape[0] <= direto_ate:
        u[livre] = spla.spsolve(Kl.tocsc(), fl)
        return u
    import pyamg

    B = modos_rigidos(pontos)[livre] if pontos is not None else None
    if Kl.shape[0] % 3 == 0 and B is not None:  # graus agrupados por nó (presos nó a nó): blocos 3 x 3
        Kb = sp.bsr_matrix(Kl, blocksize=(3, 3))
    else:
        Kb = Kl
    ml = pyamg.smoothed_aggregation_solver(Kb, B=B, max_coarse=500, smooth="jacobi")
    M = ml.aspreconditioner(cycle="V")
    res = []
    x, info = spla.cg(Kl, fl, rtol=tol, maxiter=3000, M=M, callback=lambda xk: res.append(1))
    if info != 0:
        raise RuntimeError(f"o gradiente conjugado não convergiu ({info}, {len(res)} iterações)")
    u[livre] = x
    return u


def energia_voxeis(ligacoes: np.ndarray, E: np.ndarray, nu: np.ndarray, h: float, u: np.ndarray) -> np.ndarray:
    """Energia de deformação de cada cubo (mJ se as unidades forem N e mm): 1/2 u_e^T K_e u_e.

    Em linguagem simples: a energia que o material de cada elemento guarda ao deformar-se, como uma mola
    comprimida; é a grandeza que o osso "sente" e que o stress shielding faz baixar.
    """
    ligacoes = np.asarray(ligacoes)
    graus = (3 * ligacoes[:, :, None] + np.arange(3)[None, None, :]).reshape(len(ligacoes), 24)
    ue = u[graus]
    W = np.zeros(len(ligacoes))
    for v in np.unique(nu):
        sel = np.flatnonzero(nu == v)
        K0, _ = rigidez_cubo(v, h)
        W[sel] = 0.5 * E[sel] * np.einsum("ei,ij,ej->e", ue[sel], K0, ue[sel])
    return W


def forcas_internas(ligacoes: np.ndarray, E: np.ndarray, nu: np.ndarray, h: float, u: np.ndarray,
                    n_nos: int) -> np.ndarray:
    """Forças internas nodais K u (N), montadas elemento a elemento, sem guardar a matriz global.

    Em linguagem simples: em cada nó, a força que o material à volta faz quando a malha se deforma. Nos nós
    presos, esta força é a reação do apoio; nos nós livres é igual à carga aplicada (equilíbrio).
    """
    ligacoes = np.asarray(ligacoes)
    graus = (3 * ligacoes[:, :, None] + np.arange(3)[None, None, :]).reshape(len(ligacoes), 24)
    f = np.zeros(3 * n_nos)
    for v in np.unique(nu):
        sel = np.flatnonzero(nu == v)
        K0, _ = rigidez_cubo(v, h)
        fe = E[sel, None] * (u[graus[sel]] @ K0.T)
        np.add.at(f, graus[sel].ravel(), fe.ravel())
    return f


def deformacoes_centro(ligacoes: np.ndarray, h: float, u: np.ndarray) -> np.ndarray:
    """Tensor das deformações (3 x 3, adimensional) no centro de cada cubo.

    Em linguagem simples: no centro de um hexaedro trilinear de lado h, a derivada da função de forma do
    canto c na direção j é (2 c_j - 1) / (4 h); o gradiente dos deslocamentos sai da soma pelos 8 cantos e a
    deformação é a sua parte simétrica.
    """
    _, cantos = rigidez_cubo(0.3)
    dN = (2 * cantos - 1) / (4.0 * h)  # (8, 3)
    ue = u.reshape(-1, 3)[np.asarray(ligacoes)]  # (ne, 8, 3)
    G = np.einsum("eai,aj->eij", ue, dN)
    return 0.5 * (G + G.transpose(0, 2, 1))


def deformacoes_principais(eps: np.ndarray) -> np.ndarray:
    """Deformações principais de cada elemento, por ordem crescente (mínima, intermédia, máxima).

    Em linguagem simples: as deformações nas três direções em que o material só estica ou encolhe, sem
    distorção; a máxima é a maior tração e a mínima a maior compressão.
    """
    return np.linalg.eigvalsh(eps)


def resolver_skfem(malha, elemento, E: float, nu: float, fixos: np.ndarray, forcas: np.ndarray):
    """Resolve um problema elástico homogéneo numa malha do scikit-fem (usado na verificação analítica).

    Em linguagem simples: monta a rigidez com o scikit-fem para o elemento dado (por exemplo, tetraedros
    quadráticos), aplica as forças nodais e prende os graus 'fixos'. Devolve (base, deslocamentos).
    """
    import skfem
    from skfem.models.elasticity import linear_elasticity

    base = skfem.Basis(malha, skfem.ElementVector(elemento))
    lam, mu = lame(E, nu)
    K = skfem.asm(linear_elasticity(lam, mu), base)
    u = skfem.solve(*skfem.condense(K, forcas, D=np.asarray(fixos, int)))
    return base, u
