"""Exporta de data/ (e de src/) o que o núcleo Rust da aplicação precisa, um JSON por caso.

Gera app-nativa/dados/caso_<caso>.json com: parâmetros (η, incerteza dos valores únicos,
fator do P-foco, teto do custo), os problemas de decisão dos cenários A e B (materiais,
critérios, tipos, alvos, pesos, mín., máx. e típico), as propriedades que as regras
"critério acrescentado" pedem (ex.: teor de níquel do stent), os critérios do problema
crítico por ligação, as regras de data/perfis_doente.csv e os perfis de referência.
Gera também app-nativa/dados/app.json (nomes simples, fichas, filtros, espectro de confiança, FEA,
massa e textos) e, quando a CFD tiver resultados, cfd_stent.json, para a interface.
Sem números escritos à mão: tudo vem de data/ através das funções de src/.

Uso: python scripts/exportar_app_json.py [--saida app-nativa/dados]
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import pandas as pd

from biomat_mcdm.io import DATA, DecisionProblem, build_problem, criterios_do_problema, load_data, load_parametros
from biomat_mcdm.perfis import CASOS, PERFIS_REFERENCIA, ler_regras
from biomat_mcdm.robustness import e_ordinal

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "app-nativa" / "dados"
CENARIOS = ("A", "B")
LIGACOES = ("direta", "indireta")


def nome_ficheiro(caso: str) -> str:
    """Nome do ficheiro de um caso, sem acentos nem espaços (ex.: "Implante dentário" -> caso_implante_dentario.json)."""
    tabela = str.maketrans("áàâãéêíóôõúçÁÉÍÓÚÇ", "aaaaeeiooouc" + "AEIOUC")
    return "caso_" + re.sub(r"[^a-z0-9]+", "_", caso.translate(tabela).lower()).strip("_") + ".json"


def _num(x) -> float | None:
    """Número ou None (para os NaN do pandas, que o JSON não aceita)."""
    if x is None:
        return None
    x = float(x)
    return None if math.isnan(x) else x


def problema_json(p: DecisionProblem) -> dict:
    """Converte um DecisionProblem num dicionário pronto para JSON.

    Em linguagem simples: escreve as listas de materiais e critérios e as matrizes (uma lista
    por material) dos valores mínimo, máximo e típico; marca os critérios ordinais (1-5), que
    não variam no Monte Carlo.
    """
    return {"alternativas": list(p.alternatives), "criterios": list(p.criteria), "tipos": list(p.types),
            "alvos": [_num(a) for a in p.targets], "pesos": [float(w) for w in p.weights],
            "x_min": p.X_min.tolist(), "x_max": p.X_max.tolist(), "x_tipico": p.X.tolist(),
            "ordinal": [e_ordinal(c) for c in p.criteria]}


def propriedades_extra(caso: str, regras: pd.DataFrame, data_dir: Path = DATA) -> dict:
    """Valores (mín., máx., típico) das propriedades pedidas pelas regras "critério acrescentado".

    Em linguagem simples: o stent com alergia ao níquel precisa do teor de níquel de cada liga,
    que não é critério do caso de base; aqui vai buscar esses valores à base de dados.
    """
    mat, _ = load_data(data_dir)
    out = {}
    for alvo in regras[regras["efeito"] == "critério acrescentado"]["alvo_do_efeito"]:
        prop = re.sub(r"\s*\((custo|benefício)\)\s*$", "", alvo)
        sub = mat[(mat["caso_componente"] == CASOS[caso]) & (mat["propriedade"] == prop)]
        out[prop] = {r.material: {"min": _num(r.min), "max": _num(r.max),
                                  "tipico": _num(r.tipico) if not pd.isna(r.tipico) else (r.min + r.max) / 2}
                     for r in sub.drop_duplicates("material").itertuples()}
    return out


def caso_json(caso: str, data_dir: Path = DATA) -> dict:
    """Tudo o que o núcleo Rust precisa para um caso, como dicionário.

    Em linguagem simples: junta num só objeto os dados do caso, os cenários A e B, as regras
    dos perfis de doente e os perfis de exemplo; a aplicação lê este ficheiro e não precisa
    do Python.
    """
    regras = ler_regras(data_dir)
    regras = regras[regras["dispositivo"] == CASOS[caso]]
    cenarios = {}
    for c in CENARIOS:
        try:
            cenarios[c] = problema_json(build_problem(CASOS[caso], c, data_dir))
        except ValueError:
            continue  # cenário sem problema válido neste caso
    regras_json = [{k: (None if pd.isna(v) else (str(v) if k == "valor" else v)) for k, v in r.items()}
                   for r in regras.to_dict("records")]
    return {
        "caso": caso, "caso_componente": CASOS[caso],
        "parametros": load_parametros(data_dir),
        "cenarios": cenarios,
        "propriedades_extra": propriedades_extra(caso, regras, data_dir),
        "problemas_criticos": {lig: criterios_do_problema(CASOS[caso], (lig,), data_dir) for lig in LIGACOES},
        "regras": regras_json,
        "perfis_referencia": {pid: {"descricao": d, "perfil": perfil}
                              for pid, (c, d, perfil) in PERFIS_REFERENCIA.items() if c == caso},
    }


def exportar(saida: Path = SAIDA, data_dir: Path = DATA) -> list[Path]:
    """Grava um JSON por caso em `saida`; devolve os caminhos gravados."""
    saida.mkdir(parents=True, exist_ok=True)
    caminhos = []
    for caso in CASOS:
        f = saida / nome_ficheiro(caso)
        f.write_text(json.dumps(caso_json(caso, data_dir), ensure_ascii=False, indent=1), encoding="utf-8")
        caminhos.append(f)
    return caminhos


# ------------------------------------------------------------------ dados extra para a interface (app.json)

RESULTS = RAIZ / "results"
DOCS = RAIZ / "docs"
LIMIAR_EMPATE = 0.01  # igual a scripts/figuras.py e scripts/tabelas_relatorio.py (ΔC do TOPSIS abaixo = empate)


def _script(nome: str):
    """Carrega um módulo de scripts/ pelo caminho (scripts/ não é um pacote)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(nome, Path(__file__).resolve().parent / f"{nome}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _registos(df: pd.DataFrame) -> list[dict]:
    """Linhas de uma tabela como dicionários, com os NaN trocados por None (o JSON não aceita NaN)."""
    return [{k: (None if (isinstance(v, float) and math.isnan(v)) else v) for k, v in r.items()}
            for r in df.to_dict("records")]


def nomes_json() -> dict:
    """Nomes simples aprovados (scripts/nomes_simples.py): material -> {nome, codigo}.

    Em linguagem simples: a aplicação mostra sempre o nome em linguagem corrente e o código técnico em letra
    pequena; esta função passa a tabela para JSON."""
    ns = _script("nomes_simples")
    return {m: {"nome": n, "codigo": c} for m, (n, c) in ns.NOMES.items()}


def fichas_json(data_dir: Path = DATA) -> dict:
    """Propriedades de cada material (data/materiais.csv) e do tecido (data/tecido.csv), com fonte e estado.

    Em linguagem simples: são as fichas dos materiais da aplicação; cada valor leva a referência, o DOI, a nota e o
    estado ("Verificado", "A verificar"), tal como estão na base."""
    mat = pd.read_csv(data_dir / "materiais.csv", encoding="utf-8")
    tec = pd.read_csv(data_dir / "tecido.csv", encoding="utf-8")
    return {"materiais": _registos(mat), "tecido": _registos(tec)}


def filtros_json(data_dir: Path = DATA) -> dict:
    """Filtros de RM, ISO 10993-1 e esterilização por material, e o cenário de sensibilidade da esterilização.

    Em linguagem simples: junta a tabela data/filtros_material.csv com o resultado de cada filtro
    (src/biomat_mcdm/filtros.py) e com a lista de vencedores antes e depois de impor um método de esterilização."""
    from biomat_mcdm import filtros as fl
    tabela = fl.ler_filtros_material(data_dir)
    mat, _ = load_data(data_dir)
    estatuto = mat.drop_duplicates("material").set_index("material")["estatuto"].to_dict()
    rm = fl.filtro_rm(list(tabela.index), tabela)
    iso = fl.filtro_iso10993({m: estatuto.get(m, "") for m in tabela.index})
    linhas = []
    for m, r in tabela.iterrows():
        linhas.append({"material": m, **r.to_dict(), "estatuto": estatuto.get(m, ""), "rm": rm[m], "iso10993": iso[m]})
    return {"metodos": dict(fl.METODOS_ESTERILIZACAO), "materiais": linhas,
            "esterilizacao": _registos(fl.esterilizacao_linhas(data_dir=data_dir))}


def espectro_json(results_dir: Path = RESULTS, data_dir: Path = DATA) -> list[dict]:
    """Espectro de confiança: por caso, o vencedor, o segundo, o ΔC do TOPSIS no cenário A e a robustez.

    Em linguagem simples: mede a distância entre o primeiro e o segundo no TOPSIS (quanto maior, mais claro o
    vencedor). Nos casos quantitativos junta a % de repetições do Monte Carlo das propriedades em que o vencedor
    fica em 1.º (mínimo e máximo entre métodos); nos semiquantitativos, quantas versões da análise o mantêm."""
    from biomat_mcdm.pipeline import rank_all_methods
    pts = pd.read_csv(results_dir / "pontuacoes.csv")
    mc = pd.read_csv(results_dir / "monte_carlo.csv")
    mc = mc[mc["analise"] == "MC propriedades"]
    sq = pd.read_csv(results_dir / "semiquantitativos.csv")
    out = []
    for caso in ("Haste", "Stent", "Scaffold"):
        s = pts[(pts["caso"] == caso) & (pts["cenario"] == "A")].sort_values("C_TOPSIS", ascending=False)
        v = s["material"].iloc[0]
        p = mc[(mc["caso"] == caso) & (mc["material"] == v)]["pct_primeiro"]
        out.append({"caso": caso, "vencedor": v, "segundo": s["material"].iloc[1],
                    "delta_c": float(s["C_TOPSIS"].iloc[0] - s["C_TOPSIS"].iloc[1]), "semiquantitativo": False,
                    "pct_primeiro_min": float(p.min()), "pct_primeiro_max": float(p.max()),
                    "n_iter": int(mc[mc["caso"] == caso]["n_iter"].iloc[0])})
    for caso in ("Par articular", "Implante dentário"):
        d = rank_all_methods(build_problem(CASOS[caso], "A", data_dir)).sort_values("C_TOPSIS", ascending=False)
        v = d["material"].iloc[0]
        s = sq[(sq["caso"] == caso) & (sq["posicao"] == 1)]
        out.append({"caso": caso, "vencedor": v, "segundo": d["material"].iloc[1],
                    "delta_c": float(d["C_TOPSIS"].iloc[0] - d["C_TOPSIS"].iloc[1]), "semiquantitativo": True,
                    "versoes_mantem": int((s["material"] == v).sum()),
                    "versoes_total": int(s.groupby(["cenario", "variante", "metodo"]).ngroups)})
    return sorted(out, key=lambda c: -c["delta_c"])


def fea_json(results_dir: Path = RESULTS) -> dict | None:
    """FEA da haste: energia no osso nas zonas de Gruen 1 e 7 (malha mais fina) e comparação das duas ferramentas.

    Em linguagem simples: para cada material diz quanta energia de deformação fica no osso face ao fémur intacto
    (razão) e o stress shielding (1 - razão); junta a comparação Python contra SOLIDWORKS. Devolve None se os
    resultados não existirem."""
    csv = results_dir / "fea_haste.csv"
    if not csv.exists():
        return None
    d = pd.read_csv(csv)
    fc = _script("fea_comparacao")
    fina = d[(d["malha_mm"] == d["malha_mm"].min()) & d["zona"].isin([1, 7])]
    fina = fina.assign(material_base=fina["material"].map(fc.NOMES))
    out = {"malha_mm": float(d["malha_mm"].min()), "malhas_mm": sorted(map(float, d["malha_mm"].unique()), reverse=True),
           "zonas": _registos(fina[["material", "material_base", "E_haste_GPa", "zona", "energia_mJ", "razao", "stress_shielding",
                                    "elementos", "graus_liberdade"]])}
    if (results_dir / "fea_haste_sw.json").exists():
        t = fc.tabela(fc.razoes_python(csv), fc.razoes_solidworks(results_dir / "fea_haste_sw.json"))
        out["comparacao"] = [{"material": m, **{k: float(v) for k, v in r.items()}} for m, r in t.iterrows()]
    return out


def massa_json(results_dir: Path = RESULTS) -> dict | None:
    """Massa da haste por material (results/massa_haste.csv) e o desvio máximo do centro de massa do corpo.

    Em linguagem simples: a forma é a mesma em todos os materiais, por isso o volume sai de massa / densidade; o
    desvio do centro de massa do corpo usa os valores de desenho de scripts/massa_haste.py (massa corporal e
    distância máxima). Devolve None se os resultados não existirem."""
    csv = results_dir / "massa_haste.csv"
    if not csv.exists():
        return None
    from biomat_mcdm.massa import desvio_centro_massa_mm
    mh = _script("massa_haste")
    t = pd.read_csv(csv)
    dm_g = float(t["massa_g"].max() - t["massa_g"].min())
    return {"materiais": _registos(t), "volume_cm3": float(t["massa_g"].iloc[0] / t["densidade_g_cm3"].iloc[0]),
            "diferenca_g": dm_g, "massa_corpo_kg": mh.MASSA_CORPO_KG, "distancia_max_m": mh.DISTANCIA_MAX_M,
            "desvio_max_mm": desvio_centro_massa_mm(dm_g / 1000.0, mh.DISTANCIA_MAX_M, mh.MASSA_CORPO_KG),
            "excursao_vertical_cm": list(mh.EXCURSAO_VERTICAL_CM), "excursao_lateral_cm": list(mh.EXCURSAO_LATERAL_CM)}


def cfd_json(results_dir: Path = RESULTS) -> dict | None:
    """Resultados do fluxo pulsátil da CFD do stent (results/cfd_pulsatil.json), ou None enquanto não existirem."""
    f = results_dir / "cfd_pulsatil.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def app_json(data_dir: Path = DATA, results_dir: Path = RESULTS, docs_dir: Path = DOCS) -> dict:
    """Tudo o que a interface precisa além dos casos: nomes, fichas, filtros, espectro, FEA, massa e textos.

    Em linguagem simples: os números da interface vêm todos daqui ou dos caso_*.json; o limiar de empate é o do
    relatório (scripts/figuras.py) e o texto dos iões vem de docs/IOES_METALICOS.md."""
    ioes = docs_dir / "IOES_METALICOS.md"
    mc = pd.read_csv(results_dir / "monte_carlo.csv")
    return {"nomes": nomes_json(), "fichas": fichas_json(data_dir), "filtros": filtros_json(data_dir),
            "espectro": espectro_json(results_dir, data_dir), "limiar_empate": LIMIAR_EMPATE,
            "monte_carlo_referencia": _registos(mc), "fea": fea_json(results_dir), "massa": massa_json(results_dir),
            "textos": {"ioes": ioes.read_text(encoding="utf-8") if ioes.exists() else None}}


def exportar_extras(saida: Path = SAIDA, data_dir: Path = DATA, results_dir: Path = RESULTS) -> list[Path]:
    """Grava app.json e, se a CFD já tiver resultados, cfd_stent.json; devolve os caminhos gravados."""
    saida.mkdir(parents=True, exist_ok=True)
    caminhos = [saida / "app.json"]
    caminhos[0].write_text(json.dumps(app_json(data_dir, results_dir), ensure_ascii=False, indent=1), encoding="utf-8")
    cfd = cfd_json(results_dir)
    if cfd is not None:
        caminhos.append(saida / "cfd_stent.json")
        caminhos[1].write_text(json.dumps(cfd, ensure_ascii=False, indent=1), encoding="utf-8")
    return caminhos


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--saida", type=Path, default=SAIDA)
    saida = ap.parse_args().saida
    for f in exportar(saida) + exportar_extras(saida):
        print(f.relative_to(RAIZ) if f.is_relative_to(RAIZ) else f)


if __name__ == "__main__":
    main()
