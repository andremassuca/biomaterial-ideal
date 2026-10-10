"""Massa e centro de massa da haste com cada material e efeito no centro de massa do corpo.

Uso: python scripts/massa_haste.py

Lê a haste (design/cad/stl/haste_femoral_haste.STL, Corail tamanho 8 modelada no SOLIDWORKS, em mm) e as
densidades da haste em data/materiais.csv (coluna "tipico"); grava results/massa_haste.md e results/massa_haste.csv.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from biomat_mcdm.massa import desvio_centro_massa_mm, massas_g, volume_e_centroide  # noqa: E402

STL = RAIZ / "design" / "cad" / "stl" / "haste_femoral_haste.STL"
MASSA_CORPO_KG = 75.0  # valor de desenho, o mesmo da FEA da haste
DISTANCIA_MAX_M = 0.5  # majorante de desenho: maior do que a distância de qualquer ponto da anca ao centro de massa
FRACAO_COXA = 0.1416  # coxa, homens: de Leva 1996 (via Healthcare 2022;10:2054, Tabela 5); fonte secundária
EXCURSAO_VERTICAL_CM = (2.74, 4.83)  # centro de massa na marcha, 0,7 a 1,6 m/s: Orendurff 2004 (resumo)
EXCURSAO_LATERAL_CM = (3.85, 6.99)


def ler_stl(caminho: Path):
    import pyvista as pv
    m = pv.read(str(caminho)).clean().triangulate()
    f = np.asarray(m.faces).reshape(-1, 4)[:, 1:]
    return np.asarray(m.points, dtype=float), f


def densidades_haste() -> dict[str, float]:
    d = pd.read_csv(RAIZ / "data" / "materiais.csv")
    s = d[(d["caso"] == "Prótese da anca") & (d["componente"] == "Haste femoral") & (d["propriedade"] == "Densidade")]
    return {r.material: float(r.tipico) for r in s.itertuples()}


def fmt(x: float, casas: int = 0) -> str:
    return f"{x:,.{casas}f}".replace(",", " ").replace(".", ",")


def main() -> None:
    v, f = ler_stl(STL)
    vol_mm3, centro = volume_e_centroide(v, f)
    vol = vol_mm3 / 1000.0
    rho = densidades_haste()
    m = massas_g(vol, rho)
    t = pd.DataFrame({"material": list(m), "densidade_g_cm3": [rho[k] for k in m], "massa_g": list(m.values())})
    t = t.sort_values("massa_g", ascending=False)
    t.to_csv(RAIZ / "results" / "massa_haste.csv", index=False)
    dm = (t["massa_g"].max() - t["massa_g"].min()) / 1000.0
    desvio = desvio_centro_massa_mm(dm, DISTANCIA_MAX_M, MASSA_CORPO_KG)
    coxa = FRACAO_COXA * MASSA_CORPO_KG
    linhas = [
        "# Massa e centro de massa da haste femoral", "",
        "Gerado por scripts/massa_haste.py. Haste Corail tamanho 8 (design/cad/stl/haste_femoral_haste.STL), "
        "densidades típicas de data/materiais.csv. A forma é a mesma em todos os materiais.", "",
        f"Volume: {fmt(vol, 1)} cm³. Centro de massa da haste (referencial do STL, mm): "
        f"({fmt(centro[0], 1)}; {fmt(centro[1], 1)}; {fmt(centro[2], 1)}). Como a densidade é uniforme, o centro "
        "de massa da haste é o mesmo com qualquer material (é o centroide da forma).", "",
        "| Material | Densidade (g/cm³) | Massa da haste (g) |", "|---|---|---|"]
    linhas += [f"| {r.material} | {fmt(r.densidade_g_cm3, 2)} | {fmt(r.massa_g)} |" for r in t.itertuples()]
    linhas += [
        "", f"Diferença entre a haste mais pesada e a mais leve: {fmt(dm * 1000)} g.", "",
        "## Efeito no centro de massa do corpo", "",
        f"Com {fmt(MASSA_CORPO_KG)} kg de massa corporal (valor de desenho, o da FEA) e a haste a menos de "
        f"{fmt(DISTANCIA_MAX_M, 1)} m do centro de massa do corpo (majorante de desenho), trocar a haste mais leve "
        f"pela mais pesada desloca o centro de massa do corpo, no máximo, {fmt(desvio, 2)} mm "
        "(dm x d / M).", "",
        f"Comparação: na marcha normal, o centro de massa sobe e desce {fmt(EXCURSAO_VERTICAL_CM[0], 1)} a "
        f"{fmt(EXCURSAO_VERTICAL_CM[1], 1)} cm e oscila {fmt(EXCURSAO_LATERAL_CM[0], 1)} a "
        f"{fmt(EXCURSAO_LATERAL_CM[1], 1)} cm para os lados a cada passo (Orendurff MS et al. J Rehabil Res Dev "
        "2004;41:829-834, doi:10.1682/jrrd.2003.10.0150; só resumo). A coxa pesa cerca de "
        f"{fmt(coxa, 1)} kg ({fmt(100 * FRACAO_COXA, 1)} % da massa corporal; de Leva P. J Biomech 1996;29:1223-1230, "
        "valores lidos numa reprodução da tabela, Healthcare 2022;10:2054, Tabela 5 [confirmar no original]); a "
        f"diferença entre materiais é {fmt(100 * dm / coxa, 1)} % da massa da coxa.", "",
        f"Conclusão: o efeito no centro de massa do corpo é desprezável (menos de {fmt(np.ceil(desvio * 10) / 10, 1)} "
        f"mm, pelo menos {int(EXCURSAO_VERTICAL_CM[0] * 10 // desvio)} vezes menos do que a subida e descida do "
        "próprio centro de massa a cada passo). O material da haste "
        "não muda o equilíbrio nem a marcha por causa da massa; o que muda é a rigidez (FEA, results/fea_haste.md).",
        "", "Nota: a massa da haste não é toda massa acrescentada, porque substitui osso e medula retirados. Num "
        "estudo que pesou o que se retira e o que se coloca, o ganho mediano com a prótese total não cimentada foi "
        "de 145 g (Marmor S et al. Orthop Traumatol Surg Res 2023, doi:10.1016/j.otsr.2022.103298; só resumo).", ""]
    (RAIZ / "results" / "massa_haste.md").write_text("\n".join(linhas), encoding="utf-8")
    print("\n".join(linhas))


if __name__ == "__main__":
    main()
