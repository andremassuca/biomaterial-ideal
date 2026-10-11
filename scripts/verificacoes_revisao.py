"""Números pedidos pela revisão por especialistas, gerados a partir dos dados (rastreáveis).

Grava results/verificacoes_revisao.md com:
  R25  conjunto de compromisso do VIKOR (condições C1 e C2 do Anexo A.5, eq. 20), cenários A e B;
  R27  vencedor de cada método com a matriz no ponto médio de cada intervalo (em vez do típico), cenário A;
  R91  sensibilidade do scaffold ao tempo de degradação do compósito PCL/β-TCP com o intervalo do PCL (24-48 meses);
  R46  fração da parede do stent com TAWSS abaixo de vários limiares (fluxo pulsátil), se os VTK existirem.
O Spearman entre métodos (R22) já está em results/spearman.csv.
Uso: python scripts/verificacoes_revisao.py
"""
from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_all import CASOS, RESULTS  # noqa: E402

from biomat_mcdm.io import DATA, DecisionProblem, build_problem  # noqa: E402
from biomat_mcdm.methods.vikor import compromise_set, vikor  # noqa: E402
from biomat_mcdm.pipeline import fmt_pt, rank_all_methods  # noqa: E402

LIMIARES_PA = (0.3, 0.4, 0.5, 0.6, 0.8, 1.0)
COLUNA_POS = {"TOPSIS": "pos_TOPSIS", "WASPAS": "pos_WASPAS", "VIKOR": "pos_VIKOR"}


def compromisso_vikor(p: DecisionProblem) -> dict:
    """Conjunto de compromisso do VIKOR (passo 6, eq. 20) com os números das duas condições.

    Em linguagem simples: o 1.º do VIKOR só se pode dar como vencedor isolado se tiver vantagem
    suficiente sobre o 2.º (C1: P(2) - P(1) ≥ 1/(m - 1)) e se for também o melhor em S ou em R (C2).
    Devolve os materiais por ordem de P, os valores de P, o limiar, se C1 e C2 se cumprem e o conjunto.
    """
    r = vikor(p.X, p.weights, p.types, p.targets)
    S, R, P = r["S"], r["R"], r["P"]
    ordem = list(np.argsort(P, kind="stable"))
    m = len(P)
    limiar = 1 / (m - 1)
    a1, a2 = ordem[0], ordem[1]
    return {"ordem": [p.alternatives[i] for i in ordem], "P": [float(P[i]) for i in ordem],
            "limiar": limiar, "C1": bool(P[a2] - P[a1] >= limiar),
            "C2": bool(S[a1] == S.min() or R[a1] == R.min()),
            "conjunto": [p.alternatives[i] for i in compromise_set(S, R, P)]}


def vencedores_ponto_medio(p: DecisionProblem) -> dict[str, tuple[str, str]]:
    """{método: (vencedor com o típico, vencedor com o ponto médio)}.

    Em linguagem simples: refaz o ranking com o meio de cada intervalo (mín. + máx.)/2 em vez do
    valor típico da base, para ver quanto do resultado depende da escolha do típico.
    """
    tip = rank_all_methods(p)
    med = rank_all_methods(replace(p, X_tipico=None))
    return {m: (tip.loc[tip[c] == 1, "material"].iloc[0], med.loc[med[c] == 1, "material"].iloc[0])
            for m, c in COLUNA_POS.items()}


def sensibilidade_valor(p: DecisionProblem, material: str, criterio: str, valores, intervalo: tuple[float, float]
                        ) -> list[dict]:
    """Vencedor e 2.º de cada método quando o valor típico de um material num critério muda.

    Em linguagem simples: troca o valor de um só material num só critério (e o seu intervalo) por
    cada valor da lista, refaz o ranking com os três métodos e diz quem fica em 1.º e em 2.º, com a
    diferença de C do TOPSIS entre os dois. Os dados da base não mudam.
    """
    i = next(k for k, a in enumerate(p.alternatives) if a.startswith(material))
    j = p.criteria.index(criterio)
    out = []
    for v in valores:
        Xt, Xmn, Xmx = p.X.copy(), p.X_min.copy(), p.X_max.copy()
        Xt[i, j], Xmn[i, j], Xmx[i, j] = v, intervalo[0], intervalo[1]
        r = rank_all_methods(replace(p, X_tipico=Xt, X_min=Xmn, X_max=Xmx))
        linha = {"valor": float(v)}
        for metodo, col in COLUNA_POS.items():
            linha[metodo] = (r.loc[r[col] == 1, "material"].iloc[0], r.loc[r[col] == 2, "material"].iloc[0])
        c = r.sort_values("pos_TOPSIS")["C_TOPSIS"].to_numpy()
        linha["dC_TOPSIS"] = float(c[0] - c[1])
        out.append(linha)
    return out


def fracoes_por_limiar(tau: np.ndarray, area: np.ndarray, limiares=LIMIARES_PA) -> dict[float, float]:
    """{limiar (Pa): fração da área (0 a 1) com tensão de corte abaixo desse limiar}.

    Em linguagem simples: para cada valor de corte, soma a área da parede onde o sangue roça
    mais devagar do que esse valor e divide pela área total.
    """
    tau, area = np.asarray(tau, float), np.asarray(area, float)
    return {float(L): float(area[tau < L].sum() / area.sum()) for L in limiares}


def dados_cfd() -> dict[str, dict] | None:
    """TAWSS e área de cada face da parede na zona do stent (fluxo pulsátil, malha média), ou None sem VTK."""
    import cfd_stent as cs
    from biomat_mcdm.cfd import posproc as pp

    out = {}
    for mat in cs.MATERIAIS:
        nome = f"pulsatil_{mat}_media_{cs.PASSOS}"
        d = cs.vtk_ultimo(nome)
        if d is None:
            return None
        meta = json.loads((cs.TRABALHO / nome / "caso.json").read_text(encoding="utf-8"))
        st = meta["stent"]
        z0, z1 = st["z0_mm"] / 1000, (st["z0_mm"] + st["n_aneis"] * st["altura_anel_mm"]) / 1000
        w = pp.ler(d / "boundary" / "parede.vtp").compute_cell_sizes()
        k = pp.janela_z(np.asarray(w.cell_centers().points), z0, z1)
        tau = cs.RHO * np.asarray(w.cell_data["mag(wallShearStress)Mean"])
        out[mat] = {"tau": tau[k], "area": np.asarray(w.cell_data["Area"])[k], "espessura_um": st["espessura_um"],
                    "tau_tubo": cs.an.tensao_corte_poiseuille(cs.MU, cs.RAIO_MM / 1000, meta["u_media"])}
    return out


def texto(data_dir: Path = DATA, cfd: dict | None = None) -> str:
    """Markdown com as três verificações (R25, R27, R46)."""
    L = ["# Verificações pedidas pela revisão por especialistas", "",
         "Gerado por scripts/verificacoes_revisao.py a partir de data/ (η = 1). O Spearman entre métodos (R22) "
         "está em results/spearman.csv.", "",
         "## R25: conjunto de compromisso do VIKOR (Anexo A.5, eq. 20)", "",
         "C1: P(2) - P(1) ≥ 1/(m - 1); C2: o 1.º por P também é o melhor em S ou em R.", "",
         "| Caso | Cenário | Ordem por P (P) | Limiar 1/(m - 1) | C1 | C2 | Conjunto de compromisso |",
         "|---|---|---|---|---|---|---|"]
    for caso, nome in CASOS.items():
        for cen in ("A", "B"):
            c = compromisso_vikor(build_problem(nome, cen, data_dir))
            ordem = "; ".join(f"{m} ({fmt_pt(v, 3)})" for m, v in zip(c["ordem"], c["P"]))
            L.append(f"| {caso} | {cen} | {ordem} | {fmt_pt(c['limiar'], 3)} | {'sim' if c['C1'] else 'não'} | "
                     f"{'sim' if c['C2'] else 'não'} | {', '.join(c['conjunto'])} |")
    L += ["", "## R27: vencedor com o típico e com o ponto médio de cada intervalo (cenário A)", "",
          "| Caso | Método | Vencedor (típico) | Vencedor (ponto médio) |", "|---|---|---|---|"]
    for caso, nome in CASOS.items():
        for metodo, (t, m) in vencedores_ponto_medio(build_problem(nome, "A", data_dir)).items():
            L.append(f"| {caso} | {metodo} | {t} | {m} |")
    L += ["", "## R91: tempo de degradação do compósito PCL/β-TCP com o intervalo do PCL (24 a 48 meses)", "",
          "Sensibilidade: só o compósito muda (intervalo 24-48 meses, o do PCL na base); a base não muda "
          "(compósito: 26 meses, Zhong 2026, verificado a 11 out). Vencedor (2.º) por método; ΔC do TOPSIS entre o 1.º e o 2.º.", "",
          "| Cenário | Típico do compósito (meses) | TOPSIS | WASPAS | VIKOR | ΔC TOPSIS |", "|---|---|---|---|---|---|"]
    for cen in ("A", "B"):
        for s in sensibilidade_valor(build_problem(CASOS["Scaffold"], cen, data_dir), "Compósito PCL",
                                     "Tempo de degradação", (24, 36, 48), (24, 48)):
            L.append(f"| {cen} | {fmt_pt(s['valor'], 0)} | " + " | ".join(f"{s[m][0]} ({s[m][1]})" for m in COLUNA_POS)
                     + f" | {fmt_pt(s['dC_TOPSIS'], 3)} |")
    L += ["", "## R46: fração da parede do stent com TAWSS abaixo de cada limiar (fluxo pulsátil, malha média)", ""]
    if cfd is None:
        L.append("Sem os VTK do CFD neste computador: secção não gerada.")
    else:
        mats = list(cfd)
        L += ["| Limiar (Pa) | " + " | ".join(f"{m} ({fmt_pt(cfd[m]['espessura_um'], 0)} µm)" for m in mats) + " |",
              "|---|" + "---|" * len(mats)]
        fr = {m: fracoes_por_limiar(cfd[m]["tau"], cfd[m]["area"]) for m in mats}
        for lim in LIMIARES_PA:
            L.append(f"| {fmt_pt(lim, 1)} | " + " | ".join(f"{fmt_pt(100 * fr[m][lim], 0)} %" for m in mats) + " |")
        L += ["", "TAWSS média na zona do stent relativa à tensão de corte do tubo sem stent (Poiseuille com a "
              "velocidade média do ciclo, " + fmt_pt(cfd[mats[0]]["tau_tubo"], 3) + " Pa):", ""]
        for m in mats:
            media = float((cfd[m]["tau"] * cfd[m]["area"]).sum() / cfd[m]["area"].sum())
            L.append(f"- {m}: {fmt_pt(media, 3)} Pa, razão {fmt_pt(media / cfd[m]['tau_tubo'], 2)}")
    return "\n".join(L) + "\n"


def main() -> None:
    try:
        cfd = dados_cfd()
    except (ImportError, OSError, KeyError):
        cfd = None
    md = texto(cfd=cfd)
    (RESULTS / "verificacoes_revisao.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
