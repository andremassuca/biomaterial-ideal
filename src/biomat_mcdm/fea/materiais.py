"""Propriedades elásticas (E e nu) dos materiais da haste e do osso usados na FEA.

Os módulos de Young das ligas vêm de data/materiais.csv (coluna "tipico"). A base não tem coeficientes de
Poisson: os valores abaixo são valores de desenho, usuais em FEA de próteses, e ficam "A verificar"
(estão listados em docs/FEA_HASTE.md). A energia de deformação no osso é pouco sensível a nu face a E.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[3]
MATERIAIS_CSV = RAIZ / "data" / "materiais.csv"
TECIDO_CSV = RAIZ / "data" / "tecido.csv"

# nomes na base de dados -> nome curto usado nas tabelas
LIGAS = {"Aço inox 316L": "316L", "Co-Cr-Mo forjado": "Co-Cr-Mo", "Ti-6Al-4V ELI": "Ti-6Al-4V"}

# coeficientes de Poisson: valores de desenho, A verificar (sem fonte na base de dados)
NU = {"Aço inox 316L": 0.30, "Co-Cr-Mo forjado": 0.30, "Ti-6Al-4V ELI": 0.34}
NU_OSSO = 0.30  # usado em FEA do fémur, por exemplo Johnson et al. 2023 (doi:10.1177/11795972231166240)

E_POROSO_GPA = 17.0  # Ti-6Al-4V poroso: valor de desenho (alvo: o osso cortical)

# osso trabecular do colo do fémur: E = 6,850 rho^1,49 GPa (Morgan, Bayraktar e Keaveny 2003, J Biomech
# 36:897-904, doi:10.1016/S0021-9290(03)00071-X; relação citada em Oftadeh et al. 2015, J Biomech Eng
# 137:010802, Tabela 2, doi:10.1115/1.4029176), com densidade aparente de desenho rho = 0,5 g/cm3 (dentro do
# intervalo 0,26-0,75 g/cm3 dos provetes do colo)
RHO_TRABECULAR = 0.5


def modulo_trabecular(rho_aparente: float = RHO_TRABECULAR) -> float:
    """Módulo de Young do osso trabecular do colo do fémur (MPa) pela relação de Morgan et al. 2003.

    Em linguagem simples: o osso esponjoso é tanto mais rígido quanto mais denso; esta lei de potência foi
    medida em provetes do colo do fémur humano (densidade aparente em g/cm3, E em GPa; aqui devolve MPa).
    """
    return 6850.0 * rho_aparente ** 1.49


def modulo_cortical(caminho: Path = TECIDO_CSV) -> float:
    """Módulo de Young do osso cortical (MPa): ponto médio do intervalo de data/tecido.csv.

    Em linguagem simples: lê a linha "Osso cortical, Módulo de Young" (15 a 20 GPa, Li et al. 2014) e usa o
    meio do intervalo, como a coluna "tipico" faz para os materiais.
    """
    t = pd.read_csv(caminho, encoding="utf-8")
    linha = t[(t["tecido"] == "Osso cortical") & (t["propriedade"] == "Módulo de Young")].iloc[0]
    return 1000.0 * (float(linha["min"]) + float(linha["max"])) / 2


def materiais_haste(caminho: Path = MATERIAIS_CSV) -> dict[str, tuple[float, float]]:
    """Os quatro materiais da haste: nome curto -> (E em MPa, nu).

    Em linguagem simples: tira da base de dados o módulo de Young típico do 316L, do Co-Cr-Mo e do
    Ti-6Al-4V (haste femoral) e junta o Ti-6Al-4V poroso com E = 17 GPa (valor de desenho), com o nu do
    Ti-6Al-4V.
    """
    d = pd.read_csv(caminho, encoding="utf-8")
    d = d[(d["componente"] == "Haste femoral") & (d["propriedade"] == "Módulo de Young")]
    saida = {}
    for nome, curto in LIGAS.items():
        E = float(d.loc[d["material"] == nome, "tipico"].iloc[0]) * 1000.0
        saida[curto] = (E, NU[nome])
    saida["Ti-6Al-4V poroso"] = (E_POROSO_GPA * 1000.0, NU["Ti-6Al-4V ELI"])
    return saida


# osso trabecular usado no caso principal: 0,39 GPa (Li et al., Materials 2014, Tabelas 2 e 3), o mesmo do estudo
# de confirmação no SOLIDWORKS e dentro dos 50-500 MPa de data/tecido.csv; a relação de Morgan (modulo_trabecular)
# fica como sensibilidade (com rho = 0,5 g/cm3 dá cerca de 2,4 GPa, valor do colo do fémur, mais denso)
E_TRABECULAR_MPA = 390.0


def materiais_osso(e_trabecular_mpa: float = E_TRABECULAR_MPA) -> dict[str, tuple[float, float]]:
    """Osso cortical e trabecular: nome -> (E em MPa, nu), isotrópicos e lineares (hipótese).

    Em linguagem simples: o cortical vem da base de dados (ponto médio de 15 a 20 GPa) e o trabecular é 0,39 GPa,
    o mesmo valor do modelo do SOLIDWORKS, para as duas ferramentas usarem os mesmos materiais."""
    return {"cortical": (modulo_cortical(), NU_OSSO), "trabecular": (e_trabecular_mpa, NU_OSSO)}
