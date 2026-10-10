"""Planeamento da haste femoral no fémur anatómico (como num planeamento pré-operatório em radiografia AP).

Uso:
    python scripts/planeamento_haste.py

Para cada tamanho do catálogo da Corail (offset standard e high offset, sem colar), coloca a haste com o centro
da cabeça no centro anatómico e a ponta no eixo do canal (geometria_3d.colocar_haste), corta o fémur pelo plano
coronal que contém a cabeça e o eixo do canal e mede, nesse plano, se o contorno da haste fica dentro do osso e a
que distância da superfície. Escolhe o maior tamanho que fica todo dentro com folga mínima de 2 mm (para a
cortical). Resultado em design/cad/planeamento_haste.csv; o tamanho escolhido vai para design/cad/cotas.md à mão.

Fonte do catálogo: DePuy Synthes, "Sistema de cadera CORAIL, Justificación del producto y Técnica Quirúrgica",
p. 28 (offset estándar, sin collar; high offset, sin collar). Medidas com cabeça de 28 mm +5,0.
"""

from __future__ import annotations

import csv
import importlib.util
import math
import sys
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
import geometria_3d as geo  # noqa: E402

_spec = importlib.util.spec_from_file_location("cad_solidworks", RAIZ / "scripts" / "cad_solidworks.py")
cad = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cad)

FEMUR = Path(r"recursos\bodyparts3d\obj\FJ3365.obj")
SAIDA = RAIZ / "design" / "cad" / "planeamento_haste.csv"
MARGEM = 2.0  # mm de folga mínima à superfície do osso no plano coronal (espaço para a cortical)

# (variante, tamanho, comprimento A, comprimento B, offset C, comprimento do colo D), em mm
CATALOGO = [
    ("standard", 8, 115, 93, 38.3, 39), ("standard", 9, 130, 108, 38.8, 39), ("standard", 10, 140, 118, 39.5, 39),
    ("standard", 11, 145, 123, 40.3, 39), ("standard", 12, 150, 128, 41.0, 39),
    ("high", 9, 130, 108, 45.7, 43), ("high", 10, 140, 118, 46.4, 43), ("high", 11, 145, 123, 47.2, 43),
]


def cabeca_e_eixo(vf):
    """Centro e raio da cabeça do fémur e eixo do canal na diáfise proximal (como em renders_blender.py)."""
    topo = vf[:, 2].max()
    cand = vf[(vf[:, 2] > topo - 50) & (vf[:, 0] > np.percentile(vf[:, 0], 70))]
    H, r = geo.ajustar_esfera(cand)
    for _ in range(4):
        H, r = geo.ajustar_esfera(vf[np.abs(np.linalg.norm(vf - H, axis=1) - r) < 3])
    C0, a = geo.eixo_principal(vf[(vf[:, 2] > H[2] - 230) & (vf[:, 2] < H[2] - 70)])
    return H, r, C0, a


def contorno_denso(pts, passo=1.0):
    """Pontos ao longo de uma polilinha, com espaçamento de cerca de 'passo' mm."""
    saida = []
    for p, q in zip(pts[:-1], pts[1:]):
        n = max(1, int(math.dist(p, q) / passo))
        saida += [(p[0] + (q[0] - p[0]) * k / n, p[1] + (q[1] - p[1]) * k / n) for k in range(n)]
    return np.array(saida)


LARGURAS = ("haste_largura_ombro", "haste_largura_ponta", "haste_espessura", "haste_espessura_ponta")


def cotas_do_tamanho(base, A, B, C, D, A_ref=150):
    """Cotas de um tamanho do catálogo: A, B, offset e colo do catálogo; larguras e espessuras proporcionais a A.

    Em linguagem simples: o catálogo só dá comprimentos, offset e colo; as larguras e espessuras do corpo são
    valores de desenho pensados para o tamanho 12 (A = 150 mm) e encolhem na mesma proporção do comprimento.
    """
    c = dict(base, haste_comprimento=A, haste_comprimento_b=B, haste_offset=C, haste_colo=D)
    for k in LARGURAS:
        c[k] = round(base[k] * A / A_ref, 1)
    return c


def escolher_tamanho(resultados, margem=MARGEM):
    """O maior tamanho (comprimento) com o contorno todo dentro do osso e folga mínima >= margem.

    Em linguagem simples: entre os tamanhos que cabem com espaço para a cortical, fica o maior, porque uma haste
    não cimentada deve encher o canal; se nenhum cabe, fica o que tem maior folga mínima.
    """
    cabem = [r for r in resultados if r["fracao_dentro"] == 1.0 and r["folga_minima"] >= margem]
    if cabem:
        return max(cabem, key=lambda r: (r["A"], r["folga_minima"]))
    return max(resultados, key=lambda r: (r["fracao_dentro"], r["folga_minima"]))


def avaliar():
    verts, faces = geo.ler_obj(FEMUR)
    H, _, C0, a = cabeca_e_eixo(verts)
    n = np.cross(H - C0, a)
    n /= np.linalg.norm(n)
    ez = np.array([0, 0, 1.0]) - (np.array([0, 0, 1.0]) @ n) * n
    ez /= np.linalg.norm(ez)
    ex = np.cross(n, ez)
    segs = geo.cortar_malha(verts, faces, n, H)
    seg2 = np.stack([(segs - H) @ ex, (segs - H) @ ez], axis=-1)
    base = cad.ler_cotas()
    resultados = []
    for variante, tam, A, B, C, D in CATALOGO:
        c = cotas_do_tamanho(base, A, B, C, D)
        altura = cad.eixo_colo(c)["centro"][1]
        T, s, med = geo.colocar_haste(H, C0, a, altura=altura, offset=C)
        corpo = contorno_denso(cad.contorno_haste(c))
        mundo = T + corpo[:, 1:2] * s - corpo[:, 0:1] * med
        p2 = np.stack([(mundo - H) @ ex, (mundo - H) @ ez], axis=-1)
        conta = corpo[:, 1] < A - 4  # os pontos do topo ficam no plano da osteotomia (osso ressecado)
        p2 = p2[conta]
        dentro = geo.dentro_da_seccao(p2, seg2)
        dist = geo.distancia_aos_segmentos(p2, seg2)
        folga = float(np.where(dentro, dist, -dist).min())
        varo = math.degrees(math.acos(np.clip(s @ (a / np.linalg.norm(a)), -1, 1)))
        resultados.append({"variante": variante, "tamanho": tam, "A": A, "B": B, "offset": C, "colo": D,
                           "fracao_dentro": float(dentro.mean()), "folga_minima": round(folga, 2),
                           "angulo_haste_canal": round(varo, 1)})
    return resultados


def main():
    res = avaliar()
    escolhido = escolher_tamanho(res)
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with SAIDA.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(res[0]) + ["escolhido"])
        w.writeheader()
        for r in res:
            w.writerow({**r, "escolhido": "sim" if r is escolhido else ""})
    for r in res:
        print(r, "<- escolhido" if r is escolhido else "")


if __name__ == "__main__":
    main()
