"""Pós-processamento da CFD: perfil de velocidade, tensão de corte na parede (TAWSS), OSI e área com corte baixo.

O OpenFOAM incompressível dá a tensão de corte "cinemática" (dividida pela densidade, m²/s²); aqui multiplica-se
pela densidade para ter Pa.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np


def ler(caminho: Path):
    """Lê um ficheiro VTK do foamToVTK (vtu ou vtp) com o pyvista."""
    import pyvista as pv

    return pv.read(str(caminho))


def raio_e_angulo(centros: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return np.hypot(centros[:, 0], centros[:, 1]), np.arctan2(centros[:, 1], centros[:, 0])


def erro_perfil(r: np.ndarray, uz: np.ndarray, raio: float, u_media: float) -> dict:
    """Compara a velocidade axial nas células com a parábola de Poiseuille.

    Devolve o erro máximo e o erro quadrático médio, ambos em fração da velocidade máxima teórica (2 U).
    """
    from .analitico import perfil_poiseuille

    teo = perfil_poiseuille(r, raio, u_media)
    e = (uz - teo) / (2 * u_media)
    return {"erro_max": float(np.abs(e).max()), "erro_rms": float(np.sqrt(np.mean(e ** 2)))}


def magnitude_tensao(wss_cinematica: np.ndarray, rho: float) -> np.ndarray:
    """Magnitude da tensão de corte em Pa a partir do vetor cinemático do OpenFOAM."""
    return rho * np.linalg.norm(np.atleast_2d(wss_cinematica), axis=1)


def osi(media_vetor: np.ndarray, media_magnitude: np.ndarray) -> np.ndarray:
    """Índice de corte oscilatório: OSI = 0,5 (1 - |média do vetor| / média da magnitude).

    Em linguagem simples: 0 quando o atrito na parede aponta sempre para o mesmo lado; 0,5 quando muda de
    sentido metade do tempo.
    """
    num = np.linalg.norm(np.atleast_2d(media_vetor), axis=1)
    den = np.asarray(media_magnitude, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(den > 0, 0.5 * (1 - num / den), 0.0)


def fracao_abaixo(valores: np.ndarray, areas: np.ndarray, limiar: float) -> float:
    """Fração da área (0 a 1) onde o valor fica abaixo do limiar."""
    areas = np.asarray(areas, dtype=float)
    return float(areas[np.asarray(valores) < limiar].sum() / areas.sum())


def desenrolar(pontos: np.ndarray, raio: float) -> np.ndarray:
    """Passa pontos da parede para o plano desenrolado (s = R theta, z), nas mesmas unidades."""
    _, th = raio_e_angulo(pontos)
    return np.column_stack([raio * th, pontos[:, 2]])


def indice_convergencia(f1: float, f2: float, f3: float, razao: float, fs: float = 1.25) -> dict:
    """Índice de convergência da malha (GCI, Roache) com três malhas: f1 a mais fina, razão de refinamento r.

    Em linguagem simples: com três malhas cada vez mais finas, estima-se a ordem com que o resultado converge e
    quanto ainda pode mudar se a malha fosse infinitamente fina (GCI da malha fina, em fração). Se as
    diferenças mudam de sinal ou não diminuem, a ordem não se calcula e devolve-se só a variação.
    """
    e21, e32 = f2 - f1, f3 - f2
    out = {"variacao_fina": abs(e21 / f1) if f1 else float("nan")}
    # sem convergência monótona e assintótica (diferenças que mudam de sinal ou não diminuem), a ordem não tem
    # sentido: devolve-se só a variação
    if e21 == 0 or e32 == 0 or np.sign(e21) != np.sign(e32) or abs(e32) <= abs(e21):
        out.update(ordem=float("nan"), gci_fina=float("nan"), extrapolado=float("nan"))
        return out
    p = np.log(abs(e32 / e21)) / np.log(razao)
    out.update(ordem=float(p), gci_fina=float(fs * abs(e21 / f1) / (razao ** p - 1)),
               extrapolado=float(f1 + (f1 - f2) / (razao ** p - 1)))
    return out


def janela_z(centros: np.ndarray, z0: float, z1: float) -> np.ndarray:
    """Máscara das faces com o centro entre z0 e z1 (zona do stent)."""
    return (centros[:, 2] >= z0) & (centros[:, 2] <= z1)


def juntar_series(pasta: Path, ficheiro: str = "surfaceFieldValue.dat") -> np.ndarray | None:
    """Junta as séries temporais de um functionObject quando o caso foi retomado a meio.

    Ao retomar, o OpenFOAM escreve numa subpasta nova com o nome do instante de arranque (por exemplo 0/ e
    1.06/). Ordenam-se as subpastas por esse instante; de cada uma guardam-se só as linhas até ao
    arranque da seguinte, porque a corrida retomada substitui o que a anterior tinha escrito depois desse
    instante. Devolve as linhas (tempo na 1.ª coluna) ou None se não houver séries."""
    partes = []
    for sub in Path(pasta).iterdir() if Path(pasta).is_dir() else []:
        try:
            inicio = float(sub.name)
        except ValueError:
            continue
        if (sub / ficheiro).exists():
            partes.append((inicio, np.atleast_2d(np.loadtxt(sub / ficheiro, comments="#"))))
    if not partes:
        return None
    partes.sort(key=lambda p: p[0])
    blocos = [d[d[:, 0] <= partes[i + 1][0]] if i + 1 < len(partes) else d for i, (_, d) in enumerate(partes)]
    return np.vstack(blocos)
