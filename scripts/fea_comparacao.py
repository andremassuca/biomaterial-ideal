"""Comparação lado a lado das duas FEA da haste: Python (caso principal) e SOLIDWORKS Simulation (confirmação).

Uso: python scripts/fea_comparacao.py

Lê results/fea_haste.csv (scripts/fea_haste.py, malha mais fina) e results/fea_haste_sw.json (scripts/fea_solidworks.py,
malha mais fina) e grava results/fea_comparacao.md e results/figures/fea/comparacao_ferramentas.png e .svg.
A grandeza comparada é a razão entre a energia de deformação no osso com a haste e no fémur intacto, nas zonas de
Gruen 1 e 7 (os valores absolutos diferem porque a geometria e a malha são diferentes; a ordem tem de bater).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
RESULTS = RAIZ / "results"
NOMES = {"316L": "Aço inox 316L", "Co-Cr-Mo": "Co-Cr-Mo forjado", "Ti-6Al-4V": "Ti-6Al-4V ELI",
         "Ti-6Al-4V poroso": "Ti-6Al-4V poroso"}


def razoes_python(csv: Path = RESULTS / "fea_haste.csv") -> pd.DataFrame:
    """Razão implantado / intacto por material e zona (1 e 7) na malha mais fina do caso em Python."""
    d = pd.read_csv(csv)
    d = d[(d["malha_mm"] == d["malha_mm"].min()) & d["zona"].isin([1, 7]) & (d["material"] != "Fémur intacto")]
    d = d.assign(material=d["material"].map(NOMES).fillna(d["material"]))
    return d.pivot(index="material", columns="zona", values="razao").rename(columns={1: "G1", 7: "G7"})


def razoes_solidworks(js: Path = RESULTS / "fea_haste_sw.json") -> pd.DataFrame:
    """Razão implantado / intacto por material e zona (1 e 7) na malha mais fina do estudo no SOLIDWORKS."""
    d = json.loads(js.read_text(encoding="utf-8"))
    m = str(min(d["malhas_mm"]))
    intacto = d["casos"]["Intacto"][m]["zonas"]
    linhas = {}
    for caso, v in d["casos"].items():
        if caso == "Intacto":
            continue
        z = v[m]["zonas"]
        linhas[caso] = {"G1": z["1"]["energia_J"] / intacto["1"]["energia_J"],
                        "G7": z["7"]["energia_J"] / intacto["7"]["energia_J"]}
    return pd.DataFrame(linhas).T


def ordem(r: pd.Series) -> list[str]:
    """Materiais da maior para a menor razão (mais energia no osso, menos stress shielding, primeiro)."""
    return list(r.sort_values(ascending=False).index)


def tabela(py: pd.DataFrame, sw: pd.DataFrame) -> pd.DataFrame:
    t = py.join(sw, lsuffix="_python", rsuffix="_solidworks", how="inner")
    return t.loc[ordem(t["G1_python"])]


NOTA_POROSO = ("Haste de Ti-6Al-4V poroso (17 GPa, valor de desenho): com interface colada e rigidez igual à do osso "
               "cortical, a energia no osso fica próxima da do osso intacto (razão perto de 1). Uma razão acima de 1 "
               "quer dizer só que o osso à volta trabalha um pouco mais do que no fémur intacto.")


def md(t: pd.DataFrame) -> str:
    f = lambda x: f"{x:.2f}".replace(".", ",")  # noqa: E731
    linhas = ["# FEA da haste: comparação das duas ferramentas", "",
              "Razão = energia de deformação no osso com a haste / fémur intacto, nas zonas de Gruen 1 e 7 (malha mais "
              "fina de cada ferramenta). Python: fémur anatómico (BodyParts3D), hexaedros de vóxel. SOLIDWORKS "
              "Simulation: fémur simplificado modelado por script, tetraedros. Os mesmos materiais, a mesma carga "
              "(caso de carga da marcha de Heller 2005: contacto da anca e abdutores) e fixação distal.", "",
              "| Material da haste | Gruen 1: Python | Gruen 1: SOLIDWORKS | Gruen 7: Python | Gruen 7: SOLIDWORKS |",
              "|---|---|---|---|---|"]
    linhas += [f"| {m} | {f(r['G1_python'])} | {f(r['G1_solidworks'])} | {f(r['G7_python'])} | "
               f"{f(r['G7_solidworks'])} |" for m, r in t.iterrows()]
    o = {c: ordem(t[c]) for c in t.columns}
    igual = all(o[c] == o["G1_python"] for c in t.columns)
    linhas += ["", "Ordem (mais energia no osso primeiro): " + " > ".join(o["G1_python"]) + ".",
               "A ordem é a mesma nas duas ferramentas e nas duas zonas." if igual else
               "ATENÇÃO: a ordem não é a mesma em todas as colunas.", "",
               "Os valores absolutos diferem (geometria anatómica contra simplificada, espessura da cortical, posição "
               "da fixação, tipo de elemento); a tendência e a ordem são o que se compara.", "",
               NOTA_POROSO]
    return "\n".join(linhas) + "\n"


def figura(t: pd.DataFrame, destino: Path = RESULTS / "figures" / "fea"):
    sys.path.insert(0, str(RAIZ / "scripts"))
    import estilo_graficos as eg
    import matplotlib.pyplot as plt
    import numpy as np
    eg.aplicar("clara")
    fig, axs = plt.subplots(1, 2, figsize=(9, 3.6), sharey=True)
    x = np.arange(len(t))
    for ax, z in zip(axs, ("G1", "G7")):
        ax.bar(x - 0.2, t[f"{z}_python"], 0.38, color="#0072B2", label="Python (fémur anatómico)")
        ax.bar(x + 0.2, t[f"{z}_solidworks"], 0.38, color="#E69F00", label="SOLIDWORKS (fémur simplificado)")
        ax.axhline(1, color="#55595e", lw=0.8, ls="--")
        ax.set_xticks(x, [m.replace(" forjado", "").replace(" ELI", "").replace("Aço inox ", "") for m in t.index],
                      fontsize=9)
        ax.set_title(f"Zona de Gruen {z[1]}", fontsize=11)
    axs[0].set_ylabel("Energia no osso / fémur intacto")
    axs[0].legend(fontsize=8, loc="upper left")
    destino.mkdir(parents=True, exist_ok=True)
    return eg.gravar(fig, "comparacao_ferramentas", destino, formatos=("png", "svg"))


def main() -> None:
    t = tabela(razoes_python(), razoes_solidworks())
    (RESULTS / "fea_comparacao.md").write_text(md(t), encoding="utf-8")
    for p in figura(t):
        print(p.relative_to(RAIZ))
    print(md(t))


if __name__ == "__main__":
    main()
