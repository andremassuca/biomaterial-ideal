"""Resume a repetição do fluxo pulsátil do stent com sangue de Carreau (results/cfd_pulsatil_carreau.json).

Lê os casos já corridos (pulsatil_<material>_media_1000 e pulsatil_<material>_media_1000_carreau, em
trabalho_cfd) com as mesmas funções da CFD principal (scripts/cfd_stent.py: TAWSS média e fração da
área da parede abaixo de 0,4 Pa na zona do stent, segundo ciclo). Só muda a viscosidade; o resultado é uma verificação
adicional, não uma previsão clínica. Os parâmetros do modelo de Carreau vêm de results/cfd_carreau.json.

Uso: python scripts/resumo_cfd_carreau_pulsatil.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
RESULTS = RAIZ / "results"
DESTINO = RESULTS / "cfd_pulsatil_carreau.json"
MATERIAIS = ("Pt-Cr", "316L")
PASSOS = 1000


def comparar(newt: dict, carr: dict) -> dict:
    """Junta o caso newtoniano e o de Carreau de um material, com as diferenças.

    Em linguagem simples: recebe as métricas dos dois casos (TAWSS média e fração da parede abaixo do limiar) e
    devolve as duas medidas lado a lado, a diferença em pontos percentuais e a variação relativa da TAWSS."""
    return {
        "espessura_um": newt["espessura_um"],
        "newtoniano": {"tau_media": newt["tau_media"], "fracao_baixa": newt["fracao_baixa"]},
        "carreau": {"tau_media": carr["tau_media"], "fracao_baixa": carr["fracao_baixa"]},
        "dif_fracao_pp": 100.0 * (carr["fracao_baixa"] - newt["fracao_baixa"]),
        "dif_tau_rel": carr["tau_media"] / newt["tau_media"] - 1.0,
    }


def ordem_mantida(casos: dict, medida: str, modelo: str) -> bool:
    """Diz se a ordem entre o strut fino (Pt-Cr) e o grosso (316L) é a mesma nos dois modelos de sangue.

    Em linguagem simples: o strut grosso deve ter mais parede com corte baixo (fração maior) e menos TAWSS; devolve
    True se isso se mantém com o modelo pedido ('newtoniano' ou 'carreau')."""
    fino, grosso = casos["Pt-Cr"][modelo][medida], casos["316L"][modelo][medida]
    return grosso > fino if medida == "fracao_baixa" else grosso < fino


def resumir() -> dict:
    """Calcula as métricas dos quatro casos e devolve o dicionário que se grava em results/."""
    sys.path.insert(0, str(RAIZ / "scripts"))
    import cfd_stent as cs  # noqa: PLC0415  (só aqui, porque precisa do VTK e da pasta de trabalho)

    casos = {}
    for mat in MATERIAIS:
        base = f"pulsatil_{mat}_media_{PASSOS}"
        casos[mat] = comparar(cs.metricas_parede(base, "TAWSS"), cs.metricas_parede(f"{base}_carreau", "TAWSS"))
    carreau = json.loads((RESULTS / "cfd_carreau.json").read_text(encoding="utf-8"))["carreau"]
    return {"limiar_pa": cs.LIMIAR_PA, "carreau": carreau, "casos": casos,
            "ordem_mantida": all(ordem_mantida(casos, m, mod) for m in ("fracao_baixa", "tau_media")
                                 for mod in ("newtoniano", "carreau"))}


def main() -> None:
    DESTINO.write_text(json.dumps(resumir(), ensure_ascii=False, indent=1), encoding="utf-8")
    print(DESTINO.relative_to(RAIZ))


if __name__ == "__main__":
    main()
