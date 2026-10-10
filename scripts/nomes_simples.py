"""Nomes simples dos materiais para quem não é da área (apresentação e gráficos dos diapositivos).

Cada material fica com um nome em linguagem corrente e o código técnico ao lado, em letra pequena. Os cinco nomes
das escolhas finais foram definidos pelo André a 8 out 2026; os restantes seguem o mesmo critério.
"""
from __future__ import annotations

NOMES = {
    # haste femoral
    "Ti-6Al-4V ELI": ("Liga de titânio", "Ti-6Al-4V"),
    "Ti cp grau 4": ("Titânio puro", "grau 4"),
    "Ti-13Nb-13Zr": ("Liga de titânio-nióbio", "Ti-13Nb-13Zr"),
    "Ti-35Nb-7Zr-5Ta (TNZT)": ("Liga de titânio em investigação", "TNZT"),
    "Co-Cr-Mo forjado": ("Cobalto-crómio", "Co-Cr-Mo"),
    "Aço inox 316L": ("Aço inoxidável", "316L"),
    # stent
    "Pt-Cr": ("Platina-crómio", "Pt-Cr"),
    "Co-Cr L605": ("Cobalto-crómio", "L605"),
    "Co-Ni-Cr-Mo MP35N": ("Cobalto-níquel", "MP35N"),
    "Liga de Mg WE43 (bioabsorvível)": ("Magnésio reabsorvível", "WE43"),
    "PLLA (bioabsorvível)": ("Polímero reabsorvível", "PLLA"),
    "Nitinol (autoexpansível)": ("Níquel-titânio", "Nitinol"),
    # scaffold
    "Compósito PCL/β-TCP (impressão 3D)": ("Polímero com cerâmica", "PCL/β-TCP"),
    "β-TCP poroso": ("Cerâmica porosa", "β-TCP"),
    "Hidroxiapatite (HA) porosa": ("Hidroxiapatite", "HA"),
    "Vidro bioativo 45S5 poroso": ("Vidro bioativo", "45S5"),
    "PCL": ("Polímero", "PCL"),
    "PLLA": ("Polímero", "PLLA"),
    "PLGA 50:50": ("Polímero", "PLGA"),
    "Quitosano/HA (liofilizado)": ("Quitosano com hidroxiapatite", "quitosano/HA"),
    # par articular
    "ZTA / ZTA (CoC)": ("Cerâmica contra cerâmica", "ZTA"),
    "ZTA / HXLPE (CoXLPE)": ("Cerâmica contra polietileno", "ZTA/HXLPE"),
    "CoCrMo / HXLPE (MoXLPE)": ("Metal contra polietileno", "CoCrMo/HXLPE"),
    "CoCrMo / UHMWPE convencional (MoP)": ("Metal contra polietileno convencional", "CoCrMo/UHMWPE"),
    "CoCrMo / CoCrMo (MoM)": ("Metal contra metal", "CoCrMo"),
    # implante dentário
    "Zircónia Y-TZP": ("Zircónia", "Y-TZP"),
    "Ti-Zr (~15% Zr)": ("Liga de titânio-zircónio", "Ti-Zr"),
    "PEEK": ("Polímero de alto desempenho", "PEEK"),
}


def nome(material: str) -> str:
    """Nome simples de um material (o próprio nome, se não estiver na tabela)."""
    return NOMES.get(material, (material, ""))[0]


def codigo(material: str) -> str:
    """Código técnico de um material (vazio, se não estiver na tabela)."""
    return NOMES.get(material, (material, ""))[1]


def com_codigo(material: str) -> str:
    """Nome simples com o código entre parênteses, por exemplo "Liga de titânio (Ti-6Al-4V)"."""
    n, c = NOMES.get(material, (material, ""))
    return f"{n} ({c})" if c else n
