"""Funil de triagem em três níveis: do universo de partida até à base verificada onde se faz o MCDM.

Nível 1 (universo de partida):
  - Materials Project (dados abertos, CC BY 4.0): compostos inorgânicos cristalinos com propriedades
    calculadas (DFT). Servem só para filtrar; nenhum valor do Materials Project entra no MCDM;
  - os 118 elementos, com a classificação de toxicidade de fontes oficiais (data/funil/elementos.csv);
  - as normas ASTM de materiais para implantes cirúrgicos (data/funil/normas.csv), com a norma como fonte.
Nível 2 (filtros automáticos sobre o Materials Project, valores em data/funil/filtros.csv):
  elementos excluídos, estabilidade termodinâmica, densidade e módulo de Young.
Nível 3: a base verificada (data/materiais.csv), com propriedades de fontes publicadas, onde se faz o MCDM.

Entre o nível 2 e o nível 3 não há um filtro automático: a base verificada junta os materiais com norma ou
uso clínico e propriedades confirmadas em fontes (as ligas, por exemplo, não existem no Materials Project,
que só tem fases ordenadas). O funil mostra a escala da triagem, não um caminho único de dados.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from biomat_mcdm.io import DATA

FUNIL = DATA / "funil"
COLUNAS_MP = ["material_id", "formula", "elementos", "e_hull", "densidade", "k_vrh", "g_vrh"]


def modulo_young(k, g):
    """Módulo de Young (GPa) a partir dos módulos de compressibilidade K e de corte G (GPa).

    Em linguagem simples: para um material isotrópico, E = 9KG / (3K + G). Devolve NaN quando falta um
    dos valores ou quando algum não é positivo (dados elásticos ausentes ou instáveis)."""
    k = np.asarray(k, dtype=float)
    g = np.asarray(g, dtype=float)
    with np.errstate(invalid="ignore", divide="ignore"):
        e = 9 * k * g / (3 * k + g)
    return np.where((k > 0) & (g > 0), e, np.nan)


def ler_filtros(caminho: Path = FUNIL / "filtros.csv") -> dict[str, float]:
    """Lê os limites dos filtros automáticos (parametro -> valor numérico)."""
    f = pd.read_csv(caminho)
    return {p: float(str(v).replace(",", ".")) for p, v in zip(f["parametro"], f["valor"])}


def elementos_excluidos(elementos: pd.DataFrame) -> dict[str, str]:
    """Elementos que eliminam um composto, com o motivo (símbolo -> motivo).

    Em linguagem simples: sai um elemento radioativo (sem isótopos estáveis), um elemento da classe 1 da
    ICH Q3D (os mais tóxicos por via parentérica) ou um elemento que a IARC classifica no grupo 1 como
    elemento (não só alguns compostos dele: o níquel metálico e o crómio metálico ficam)."""
    motivos = {}
    for _, r in elementos.iterrows():
        m = []
        if str(r.get("radioativo", "")).strip().lower() == "sim":
            m.append("radioativo")
        if str(r.get("classe_ich_q3d", "")).strip() == "1":
            m.append("ICH Q3D classe 1")
        if str(r.get("iarc_elemento", "")).strip() == "1":
            m.append("IARC grupo 1")
        if m:
            motivos[str(r["simbolo"]).strip()] = "; ".join(m)
    return motivos


def aplicar_filtros(mp: pd.DataFrame, excluidos, filtros: dict[str, float]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aplica os filtros do nível 2, por ordem; devolve (compostos que passam, contagem por etapa).

    Em linguagem simples: parte de todos os compostos e, em cada etapa, fica só com os que cumprem a regra:
    (1) nenhum elemento excluído; (2) estáveis (energia acima do casco convexo até e_hull_max eV/átomo);
    (3) densidade até densidade_max g/cm³; (4) com dados elásticos calculados; (5) módulo de Young entre
    modulo_min e modulo_max GPa. A contagem diz quantos restam depois de cada etapa."""
    excl = set(excluidos)
    d = mp.copy()
    etapas = [("Materials Project (todos os compostos)", len(d))]
    d = d[[excl.isdisjoint(e) for e in d["elementos"]]]
    etapas.append(("Sem elementos excluídos", len(d)))
    d = d[d["e_hull"] <= filtros["e_hull_max"]]
    etapas.append(("Estáveis", len(d)))
    d = d[d["densidade"] <= filtros["densidade_max"]]
    etapas.append(("Densidade dentro do limite", len(d)))
    d = d.assign(modulo=modulo_young(d["k_vrh"], d["g_vrh"]))
    d = d[d["modulo"].notna()]
    etapas.append(("Com dados elásticos calculados", len(d)))
    d = d[(d["modulo"] >= filtros["modulo_min"]) & (d["modulo"] <= filtros["modulo_max"])]
    etapas.append(("Módulo de Young dentro do intervalo", len(d)))
    contagem = pd.DataFrame(etapas, columns=["etapa", "n"]).assign(nivel=2)
    contagem.loc[0, "nivel"] = 1
    return d, contagem[["nivel", "etapa", "n"]]


def base_verificada(materiais: pd.DataFrame) -> pd.DataFrame:
    """Nível 3: número de materiais distintos por caso e componente na base verificada."""
    return (materiais.groupby(["caso", "componente"])["material"].nunique()
            .rename("n").reset_index())
