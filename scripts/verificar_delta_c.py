"""Confere os ΔC escritos à mão nos rascunhos do relatório contra results/pontuacoes.csv.

ΔC é a diferença de C (TOPSIS) entre o 1.º e o 2.º lugar de um caso num cenário. Para cada "ΔC = x" dos
rascunhos, o caso vem do nome do ficheiro (caso_stent_rascunho.md) ou do marcador da linha ("**Stent:**"), e o
cenário vem de "em A"/"em B" logo a seguir ao número ou, se não houver, da última menção a "cenário A/B" antes
dele na mesma linha. Compara-se com o valor dos resultados arredondado a 3 casas.
Uso: python scripts/verificar_delta_c.py
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
REL = RAIZ / "relatorio"
RESULTS = RAIZ / "results"
CASOS = {"anca": "Haste", "stent": "Stent", "scaffold": "Scaffold"}
MARCADORES = {"Haste": "Haste", "Stent": "Stent", "Scaffold": "Scaffold"}
NUM = r"(\d+,\d+)"
DELTA = re.compile(rf"ΔC = {NUM}(?: em ([AB]))?(?: e {NUM} em ([AB]))?")


@dataclass
class Ocorrencia:
    ficheiro: str
    linha: int
    caso: str | None
    cenario: str | None
    valor: float
    excerto: str


def caso_da_linha(ficheiro: str, linha: str) -> str | None:
    """Caso pelo nome do ficheiro (caso_x_rascunho.md) ou pelo marcador "**Caso" no início da linha."""
    m = re.match(r"caso_(\w+?)_rascunho\.md", ficheiro)
    if m and m.group(1) in CASOS:
        return CASOS[m.group(1)]
    m = re.match(r"\s*- \*\*(\w+)", linha)
    return MARCADORES.get(m.group(1)) if m else None


def ocorrencias(texto: str, ficheiro: str) -> list[Ocorrencia]:
    """Todos os ΔC de um texto, com o caso e o cenário a que se referem."""
    out = []
    for n, linha in enumerate(texto.splitlines(), 1):
        caso = caso_da_linha(ficheiro, linha)
        for m in DELTA.finditer(linha):
            antes = re.findall(r"cenário ([AB])", linha[:m.start()])
            pares = [(m.group(1), m.group(2) or (antes[-1] if antes else None))]
            if m.group(3):
                pares.append((m.group(3), m.group(4)))
            for v, cen in pares:
                out.append(Ocorrencia(ficheiro, n, caso, cen, float(v.replace(",", ".")),
                                      linha[max(0, m.start() - 60):m.end() + 5].strip()))
    return out


def delta_resultados(pontuacoes: pd.DataFrame, caso: str, cenario: str) -> float:
    c = pontuacoes[(pontuacoes["caso"] == caso) & (pontuacoes["cenario"] == cenario)]["C_TOPSIS"]
    c = c.sort_values(ascending=False).to_numpy()
    return float(c[0] - c[1])


def conferir(rel: Path = REL, results: Path = RESULTS) -> list[tuple[Ocorrencia, float | None, bool]]:
    """(ocorrência, ΔC dos resultados, coincide a 3 casas) para todos os rascunhos."""
    pts = pd.read_csv(results / "pontuacoes.csv")
    out = []
    for f in sorted(rel.glob("*_rascunho.md")) + [rel / "00_resumo_executivo.md"]:
        for o in ocorrencias(f.read_text(encoding="utf-8"), f.name):
            if o.caso is None or o.cenario is None:
                out.append((o, None, False))
                continue
            d = delta_resultados(pts, o.caso, o.cenario)
            out.append((o, d, round(d, 3) == round(o.valor, 3)))
    return out


def main() -> None:
    print("| Onde | Texto | Caso, cenário | Resultado (pontuacoes.csv) | Confere |")
    print("|---|---|---|---|---|")
    for o, d, ok in conferir():
        res = "sem caso ou cenário" if d is None else f"{d:.4f}".replace(".", ",")
        print(f"| {o.ficheiro}:{o.linha} | ΔC = {o.valor:.3f} | {o.caso}, {o.cenario} | {res} | "
              f"{'sim' if ok else 'NÃO'} |".replace("ΔC = 0.", "ΔC = 0,"))


if __name__ == "__main__":
    main()
