"""Preenche os números da CFD no rascunho do capítulo 8 e na Discussão a partir dos resultados gravados.

Uso: python scripts/preencher_cfd_relatorio.py

Lê results/cfd_verificacoes.json (gravado por scripts/cfd_stent.py resumo) e troca as marcas @@CFD_...@@ de
relatorio/extensoes_rascunho.md e relatorio/discussao_rascunho.md pelos valores, com vírgula decimal. Assim os números
do texto vêm sempre dos resultados e não ficam escritos à mão.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
REL = RAIZ / "relatorio"
VERIF = RAIZ / "results" / "cfd_verificacoes.json"


def pt(x: float, casas: int = 1) -> str:
    return f"{x:.{casas}f}".replace(".", ",")


def textos(v: dict) -> dict[str, str]:
    """Marca -> texto, a partir das verificações e dos resultados da CFD."""
    p, a = v["pulsatil"]["Pt-Cr"], v["pulsatil"]["316L"]
    resultados = (
        f"Resultados (Tabela [n]): com os struts finos de Pt-Cr, {pt(100 * p['fracao_baixa'], 0)} % da parede entre "
        f"os struts fica com a tensão de corte média no ciclo (TAWSS) abaixo de 0,4 Pa; com os struts grossos de 316L, "
        f"{pt(100 * a['fracao_baixa'], 0)} %. A TAWSS média na parede é de {pt(p['tau_media'], 2)} Pa com o Pt-Cr e "
        f"{pt(a['tau_media'], 2)} Pa com o 316L (num tubo sem stent seria cerca de 0,87 Pa, a solução de Poiseuille "
        f"com o caudal médio). O índice de corte oscilatório médio é de {pt(p['osi_media'], 3)} com o Pt-Cr e "
        f"{pt(a['osi_media'], 3)} com o 316L. As zonas de corte baixo ficam logo a jusante de cada strut, onde o escoamento "
        f"descola e recircula, e crescem com a altura do strut.\n\n"
        "| Stent | Espessura do strut (µm) | TAWSS média (Pa) | Parede abaixo de 0,4 Pa | OSI médio |\n"
        "|---|---|---|---|---|\n"
        f"| Pt-Cr | {pt(p['espessura_um'], 0)} | {pt(p['tau_media'], 2)} | {pt(100 * p['fracao_baixa'], 0)} % | "
        f"{pt(p['osi_media'], 3)} |\n"
        f"| 316L | {pt(a['espessura_um'], 0)} | {pt(a['tau_media'], 2)} | {pt(100 * a['fracao_baixa'], 0)} % | "
        f"{pt(a['osi_media'], 3)} |\n\n"
        "Table: Resultados da simulação do escoamento no stent (fluxo pulsátil, médias no segundo ciclo, parede da "
        "artéria entre os struts).")
    disc = (f"com os struts finos de Pt-Cr, {pt(100 * p['fracao_baixa'], 0)} % da parede entre os struts fica abaixo "
            f"de 0,4 Pa, contra {pt(100 * a['fracao_baixa'], 0)} % com os struts grossos de 316L.")
    passo = {"@@CFD_PASSO@@": pt(100 * v["passo_variacao_area"], 1)} if "passo_variacao_area" in v else {}
    return passo | {
        "@@CFD_POIS_PERFIL@@": pt(100 * v["poiseuille"]["erro_perfil_max"], 1),
        "@@CFD_POIS_TAU@@": pt(100 * v["poiseuille"]["erro_tau"], 2),
        "@@CFD_POIS_DP@@": pt(100 * v["poiseuille"]["erro_dp"], 2),
        "@@CFD_MALHA@@": pt(100 * v["malha_max_variacao_area"], 1),
        "@@CFD_CICLOS@@": pt(100 * v["ciclos_max"], 1),
        "@@CFD_RESULTADOS@@": resultados,
        "@@CFD_DISC@@": disc,
    }


def preencher(texto: str, marcas: dict[str, str]) -> str:
    for k, v in marcas.items():
        texto = texto.replace(k, v)
    return texto


def main() -> None:
    v = json.loads(VERIF.read_text(encoding="utf-8"))
    marcas = textos(v)
    for nome in ("extensoes_rascunho.md", "discussao_rascunho.md"):
        p = REL / nome
        t = preencher(p.read_text(encoding="utf-8"), marcas)
        p.write_text(t, encoding="utf-8")
        # a marca do passo de tempo pode ficar: o montar_relatorio.py trata dela (verificação que acaba depois)
        if "@@CFD" in t.replace("@@CFD_PASSO@@", ""):
            sys.exit(f"marcas por preencher em {nome}")
    print("ok")


if __name__ == "__main__":
    main()
