"""Geometria da CFD: setor da artéria coronária e struts do stent em losangos.

O stent tem n_losangos células à volta da artéria. O padrão é simétrico em relação aos planos radiais que passam
pelos vértices dos losangos, por isso a CFD usa só um setor de 180/n_losangos graus com planos de simetria nos
lados. Dentro do setor, os struts formam uma linha em zigue-zague de um plano de simetria ao outro.

Coordenadas: eixo da artéria em z; s é o comprimento de arco na parede (s = R theta), o "plano desenrolado".
As funções trabalham em mm; o STL sai em metros (unidades do OpenFOAM).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Stent:
    """Parâmetros do stent e da artéria (mm e µm).

    raio_mm: raio do lúmen (a superfície exterior dos struts encosta à parede);
    n_losangos: células à volta da artéria; altura_anel_mm: avanço axial de cada strut (meia célula);
    n_aneis: número de struts ao longo do eixo no setor; z0_mm: onde começa o stent;
    espessura_um: espessura radial do strut (o que se compara); largura_um: largura do strut na parede.
    """

    raio_mm: float
    n_losangos: int
    altura_anel_mm: float
    n_aneis: int
    z0_mm: float
    espessura_um: float
    largura_um: float

    @property
    def setor_rad(self) -> float:
        return np.pi / self.n_losangos

    @property
    def arco_mm(self) -> float:
        """Largura do setor na parede (comprimento de arco de um plano de simetria ao outro)."""
        return self.raio_mm * self.setor_rad

    @property
    def comprimento_mm(self) -> float:
        return self.n_aneis * self.altura_anel_mm

    @property
    def angulo_strut_graus(self) -> float:
        """Ângulo de cada strut com o eixo da artéria (90° = strut à volta da artéria)."""
        return float(np.degrees(np.arctan2(self.arco_mm, self.altura_anel_mm)))


def linha_struts(st: Stent) -> np.ndarray:
    """Vértices (s, z) em mm da linha central dos struts no setor: zigue-zague entre s = 0 e s = arco.

    Em linguagem simples: cada strut vai de um plano de simetria ao outro enquanto avança uma altura de anel;
    o seguinte volta para trás. Espelhado nos dois planos, isto dá losangos fechados.
    """
    i = np.arange(st.n_aneis + 1)
    s = np.where(i % 2 == 0, 0.0, st.arco_mm)
    return np.column_stack([s, st.z0_mm + i * st.altura_anel_mm])


def poligono_struts(st: Stent, tamanho_mm: float):
    """Malha de triângulos (no plano desenrolado) da área ocupada pelos struts, feita pelo gmsh.

    Cada strut é um retângulo com a largura do strut, prolongado meia largura em cada ponta para fechar os
    vértices; os retângulos são unidos (operação booleana) e a área é dividida em triângulos de lado
    tamanho_mm. Devolve (nos (k, 2) em mm, triângulos (m, 3) orientados no sentido direto).
    """
    import gmsh

    w = st.largura_um / 1000.0
    v = linha_struts(st)
    iniciado = gmsh.isInitialized()
    if not iniciado:
        gmsh.initialize(interruptible=False)
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add("struts")
        occ = gmsh.model.occ
        partes = []
        for a, b in zip(v[:-1], v[1:]):
            d = b - a
            comp = float(np.hypot(*d)) + w
            tag = occ.addRectangle(-comp / 2, -w / 2, 0, comp, w)
            occ.rotate([(2, tag)], 0, 0, 0, 0, 0, 1, float(np.arctan2(d[1], d[0])))
            m = (a + b) / 2
            occ.translate([(2, tag)], float(m[0]), float(m[1]), 0)
            partes.append((2, tag))
        if len(partes) > 1:
            occ.fuse(partes[:1], partes[1:])
        occ.synchronize()
        gmsh.option.setNumber("Mesh.MeshSizeMin", tamanho_mm)
        gmsh.option.setNumber("Mesh.MeshSizeMax", tamanho_mm)
        gmsh.model.mesh.generate(2)
        tags, coords, _ = gmsh.model.mesh.getNodes()
        p = coords.reshape(-1, 3)[:, :2]
        indice = np.full(int(tags.max()) + 1, -1)
        indice[tags.astype(int)] = np.arange(len(tags))
        _, nos = gmsh.model.mesh.getElementsByType(2)  # 2 = triângulo de 3 nós
        t = indice[nos.astype(int).reshape(-1, 3)]
        gmsh.model.remove()
    finally:
        if not iniciado:
            gmsh.finalize()
    usados = np.unique(t)
    novo = np.full(len(p), -1)
    novo[usados] = np.arange(len(usados))
    p, t = p[usados], novo[t]
    return p, orientar(p, t)


def orientar(p: np.ndarray, t: np.ndarray) -> np.ndarray:
    """Põe todos os triângulos no sentido direto (área com sinal positivo)."""
    a = area_com_sinal(p, t)
    t = t.copy()
    t[a < 0] = t[a < 0][:, [0, 2, 1]]
    return t


def area_com_sinal(p: np.ndarray, t: np.ndarray) -> np.ndarray:
    e1 = p[t[:, 1]] - p[t[:, 0]]
    e2 = p[t[:, 2]] - p[t[:, 0]]
    return 0.5 * (e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0])


def arestas_fronteira(t: np.ndarray) -> np.ndarray:
    """Arestas que pertencem a um só triângulo (o contorno), com o interior à esquerda."""
    e = np.vstack([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]])
    chave = np.sort(e, axis=1)
    _, inv, cont = np.unique(chave, axis=0, return_inverse=True, return_counts=True)
    return e[cont[inv.ravel()] == 1]


def para_3d(s_mm, z_mm, r_mm, raio_mm: float) -> np.ndarray:
    """Passa do plano desenrolado (s, z) ao espaço, no raio r: x = r cos(s/R), y = r sin(s/R)."""
    th = np.asarray(s_mm) / raio_mm
    return np.column_stack([r_mm * np.cos(th), r_mm * np.sin(th), np.asarray(z_mm, dtype=float)])


def solido_struts(st: Stent, tamanho_mm: float, saliencia_mm: float = 0.05):
    """Sólido fechado dos struts: o polígono do plano desenrolado entre r = R - espessura e r = R + saliência.

    Em linguagem simples: os struts encostam à parede por dentro e entram no lúmen com a sua espessura; o sólido
    passa um pouco para lá da parede (saliência) para o corte da malha ficar limpo. As tampas acompanham a
    curvatura da artéria e os lados são radiais. Devolve (vértices (n, 3) em mm, triângulos (m, 3)) com as
    normais para fora.
    """
    p, t = poligono_struts(st, tamanho_mm)
    r_in = st.raio_mm - st.espessura_um / 1000.0
    r_out = st.raio_mm + saliencia_mm
    n = len(p)
    v = np.vstack([para_3d(p[:, 0], p[:, 1], r_in, st.raio_mm), para_3d(p[:, 0], p[:, 1], r_out, st.raio_mm)])
    tampa_dentro = t[:, [0, 2, 1]]  # normal para o eixo
    tampa_fora = t + n  # normal para fora (e_theta x e_z = e_r)
    ar = arestas_fronteira(t)
    lados = np.vstack([np.column_stack([ar[:, 0], ar[:, 1], ar[:, 1] + n]),
                       np.column_stack([ar[:, 0], ar[:, 1] + n, ar[:, 0] + n])])
    return v, np.vstack([tampa_dentro, tampa_fora, lados])


def volume_triangulado(v: np.ndarray, f: np.ndarray) -> float:
    """Volume de uma superfície fechada (teorema da divergência); positivo se as normais apontam para fora."""
    a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)


def volume_esperado(st: Stent, area_mm2: float, saliencia_mm: float = 0.05) -> float:
    """Volume do sólido a partir da área no plano desenrolado: V = (A / R) (r_fora² - r_dentro²) / 2."""
    r_in = st.raio_mm - st.espessura_um / 1000.0
    r_out = st.raio_mm + saliencia_mm
    return area_mm2 / st.raio_mm * (r_out ** 2 - r_in ** 2) / 2.0


def escrever_stl(caminho, v_mm: np.ndarray, f: np.ndarray, nome: str = "struts") -> None:
    """Grava um STL de texto em metros (unidades do OpenFOAM)."""
    v = v_mm / 1000.0
    a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    nrm = np.cross(b - a, c - a)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    linhas = [f"solid {nome}"]
    for k in range(len(f)):
        linhas += [f"  facet normal {nrm[k, 0]:.6e} {nrm[k, 1]:.6e} {nrm[k, 2]:.6e}", "    outer loop",
                   *(f"      vertex {q[0]:.9e} {q[1]:.9e} {q[2]:.9e}" for q in (a[k], b[k], c[k])),
                   "    endloop", "  endfacet"]
    linhas.append(f"endsolid {nome}")
    with open(caminho, "w", encoding="ascii", newline="\n") as fh:
        fh.write("\n".join(linhas) + "\n")
