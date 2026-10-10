"""Filtros de requisito (ISO 10993-1, RM, esterilização) e cenário de sensibilidade da esterilização.

Decisão de 8 out 2026: estes requisitos entram como filtros e no texto, não como critérios com peso, para não mudar
os rankings do relatório. Dados por material em data/filtros_material.csv (com fonte e estado por campo).

- RM (ASTM F2503): um material ferromagnético é "MR Unsafe" e sai; "A verificar" não sai, fica assinalado.
- ISO 10993-1: a avaliação biológica é do dispositivo final, não do material; o filtro não exclui ninguém: assinala
  os materiais com uso clínico (avaliação feita no dispositivo) e os de investigação (avaliação por demonstrar).
- Esterilização: no cenário de sensibilidade com um método imposto (vapor, óxido de etileno ou radiação gama), saem os
  materiais "incompatível" com esse método; "com restrições" e "A verificar" ficam, assinalados.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from biomat_mcdm.io import DATA, build_problem
from biomat_mcdm.perfis import CASOS, excluir
from biomat_mcdm.pipeline import rank_all_methods

METODOS_ESTERILIZACAO = {"vapor": "vapor", "oxido_etileno": "óxido de etileno", "radiacao_gama": "radiação gama"}


def ler_filtros_material(data_dir: Path = DATA) -> pd.DataFrame:
    """Lê data/filtros_material.csv (uma linha por material), indexado pelo nome do material."""
    return pd.read_csv(data_dir / "filtros_material.csv", dtype=str, keep_default_na=False).set_index("material")


def filtro_rm(materiais: list[str], tabela: pd.DataFrame) -> dict[str, str]:
    """Resultado do filtro de RM por material: "exclui" (ferromagnético), "passa" ou "A verificar".

    Em linguagem simples: um material atraído por um íman forte é perigoso numa ressonância magnética (rótulo MR
    Unsafe da ASTM F2503) e sai; os que não têm fonte ficam por verificar, sem sair."""
    saida = {}
    for m in materiais:
        v = tabela.loc[m, "ferromagnetico"].strip().lower() if m in tabela.index else ""
        saida[m] = "exclui" if v == "sim" else "passa" if v == "não" else "A verificar"
    return saida


def filtro_iso10993(estatutos: dict[str, str]) -> dict[str, str]:
    """Situação de cada material face à ISO 10993-1 (não exclui ninguém).

    Em linguagem simples: a norma avalia o dispositivo pronto, não o material; um material já usado em dispositivos
    clínicos teve essa avaliação no dispositivo; um material de investigação ainda a tem de demonstrar."""
    saida = {}
    for m, e in estatutos.items():
        e = str(e)
        if e.startswith("Investigação"):
            saida[m] = "por demonstrar no dispositivo final"
        elif e.startswith(("Clínico", "Descontinuado")):
            saida[m] = "avaliada em dispositivos clínicos"
        else:
            saida[m] = "fora do ranking"
    return saida


def incompativeis(materiais: list[str], tabela: pd.DataFrame, metodo: str) -> list[str]:
    """Materiais incompatíveis com o método de esterilização dado (coluna de data/filtros_material.csv)."""
    if metodo not in METODOS_ESTERILIZACAO:
        raise ValueError(f"método de esterilização desconhecido: {metodo!r}")
    return [m for m in materiais if m in tabela.index and tabela.loc[m, metodo].strip().lower() == "incompatível"]


def cenario_esterilizacao(caso: str, metodo: str, cenario: str = "A", data_dir: Path = DATA) -> dict:
    """Cenário de sensibilidade: impõe um método de esterilização e volta a ordenar sem os incompatíveis.

    Devolve o vencedor de cada método de decisão antes e depois, os materiais que saíram e, se ficarem menos de dois
    candidatos, o motivo de não haver ranking."""
    tabela = ler_filtros_material(data_dir)
    base = build_problem(CASOS[caso], cenario, data_dir)
    rb = rank_all_methods(base)
    saem = incompativeis(list(base.alternatives), tabela, metodo)
    r = {"caso": caso, "cenario": cenario, "metodo": metodo, "saem": saem,
         "antes": {m: rb.sort_values(f"pos_{m}")["material"].iloc[0] for m in ("TOPSIS", "WASPAS", "VIKOR")}}
    if len(base.alternatives) - len(saem) < 2:
        r["depois"] = None
        r["motivo"] = "menos de dois candidatos compatíveis"
        return r
    reduzido, _ = excluir(base, saem)
    rr = rank_all_methods(reduzido)
    r["depois"] = {m: rr.sort_values(f"pos_{m}")["material"].iloc[0] for m in ("TOPSIS", "WASPAS", "VIKOR")}
    return r


def esterilizacao_linhas(cenarios=("A", "B"), data_dir: Path = DATA) -> pd.DataFrame:
    """Cenário de sensibilidade da esterilização em todos os casos, cenários e métodos (uma linha por combinação)."""
    linhas = []
    for caso in CASOS:
        for cen in cenarios:
            for metodo in METODOS_ESTERILIZACAO:
                r = cenario_esterilizacao(caso, metodo, cen, data_dir)
                depois = r["depois"] or {}
                linhas.append({"caso": caso, "cenario": cen, "metodo": METODOS_ESTERILIZACAO[metodo],
                               "saem": "; ".join(r["saem"]), "muda": bool(r["saem"]) and depois != r["antes"],
                               **{f"antes_{m}": r["antes"][m] for m in r["antes"]},
                               **{f"depois_{m}": depois.get(m, r.get("motivo", "")) for m in r["antes"]}})
    return pd.DataFrame(linhas)


def filtros_md(data_dir: Path = DATA) -> str:
    """Resumo legível dos filtros (RM, ISO 10993-1) e do cenário de sensibilidade da esterilização."""
    from biomat_mcdm.io import load_data
    tabela = ler_filtros_material(data_dir)
    mat, _ = load_data(data_dir)
    estatuto = mat.drop_duplicates("material").set_index("material")["estatuto"].to_dict()
    md = ["# Filtros de requisito e cenário da esterilização", "",
          "Gerado por scripts/run_all.py (src/biomat_mcdm/filtros.py; dados em data/filtros_material.csv). Os filtros "
          "não entram como critérios com peso; os rankings do relatório não mudam.", "",
          "## RM (ASTM F2503) e ISO 10993-1", "", "| Material | RM | ISO 10993-1 |", "|---|---|---|"]
    rm = filtro_rm(list(tabela.index), tabela)
    iso = filtro_iso10993({m: estatuto.get(m, "") for m in tabela.index})
    md += [f"| {m} | {rm[m]} | {iso[m]} |" for m in tabela.index]
    md += ["", "Nenhum material é ferromagnético na base; os que estão \"A verificar\" não têm fonte direta.", "",
           "## Esterilização imposta (sensibilidade)", "",
           "Saem os materiais incompatíveis com o método; \"com restrições\" e \"A verificar\" ficam.", "",
           "| Caso | Cenário | Método | Saem | Vencedor antes (T/W/V) | Vencedor depois (T/W/V) |", "|---|---|---|---|---|---|"]
    for _, r in esterilizacao_linhas(data_dir=data_dir).iterrows():
        if not r["saem"]:
            continue
        antes = " / ".join(r[f"antes_{m}"] for m in ("TOPSIS", "WASPAS", "VIKOR"))
        depois = " / ".join(r[f"depois_{m}"] for m in ("TOPSIS", "WASPAS", "VIKOR"))
        md.append(f"| {r['caso']} | {r['cenario']} | {r['metodo']} | {r['saem']} | {antes} | {depois} |")
    md += ["", "Combinações sem linha: nenhum material incompatível (o ranking não muda)."]
    return "\n".join(md) + "\n"
