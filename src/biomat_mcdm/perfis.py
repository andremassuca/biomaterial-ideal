"""Perfis de doente: aplica as regras de data/perfis_doente.csv a um caso e ordena os materiais.

Regras de aplicação (data/leia_me.md, secção "Perfis de doente"):
  - condicao_codigo: condições separadas por "; ", todas têm de se verificar
    (ex.: "idade<60; atividade=alta"). Uma condição sobre um dado que o perfil não tem
    não se verifica.
  - "peso multiplicado": o peso do critério é multiplicado pelo valor e os pesos voltam a somar 1.
  - "leitura do problema" (scaffold): P-foco com a leitura indicada ("leitura literal" = só
    ligações diretas; "leitura ampla" = diretas + indiretas, data/problemas_criticos.csv) e o
    fator da coluna valor (igual a fator_foco_problema, data/parametros.csv).
  - "critério acrescentado": o critério entra com o peso do valor e os restantes ficam com
    1 menos esse peso, na mesma proporção.
  - "exclusão": os materiais listados (separados por "; ") saem do ranking.
  - "nota": não altera o ranking; devolve o texto do alvo_do_efeito.
  - Várias regras que sobem o mesmo critério: usa-se o maior fator, não o produto.
  - Sem regra para o sexo: o sexo pode vir no perfil, mas nenhuma regra o usa.

Ordem de aplicação (leitura literal das regras, escolhida aqui):
  1. exclusões; 2. fatores de peso (o maior por critério; "peso multiplicado" e "leitura do
  problema" juntam-se nesta regra), seguidos de uma única renormalização; 3. critério
  acrescentado, por último, para que fique exatamente com o peso da tabela (0,20 no níquel).
  Dúvida registada: se o critério acrescentado entrasse antes dos fatores, o seu peso final
  deixaria de ser 0,20 quando outra regra do mesmo doente se aplica (ex.: S-NI com S-VASO).

Funções puras: leem os CSV de data/ e devolvem tabelas; não escrevem ficheiros.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, replace
from pathlib import Path

import numpy as np
import pandas as pd

from biomat_mcdm.io import DATA, DecisionProblem, build_problem, criterios_do_problema, load_data
from biomat_mcdm.pipeline import consenso_borda, rank_all_methods

# Nome curto do caso (como em scripts/run_all.py) → valor de "dispositivo" em perfis_doente.csv
# (igual a caso_componente em criterios.csv).
CASOS = {"Haste": "Prótese da anca | Haste femoral", "Stent": "Stent vascular",
         "Scaffold": "Scaffold (regeneração óssea)", "Par articular": "Prótese da anca | Par articular",
         "Implante dentário": "Implante dentário"}

# Leituras do problema crítico (coluna alvo_do_efeito das regras "leitura do problema").
LEITURAS = {"leitura literal": ("direta",), "leitura ampla": ("direta", "indireta")}

# Sufixo do alvo_do_efeito de um "critério acrescentado" → tipo do critério.
_TIPO_ACRESCENTADO = {"custo": "cost", "benefício": "benefit"}

# Casos de referência (docs/ESPECIFICACAO_APP.md). As entradas são exemplos de desenho que
# ativam as regras da tabela; não são dados de doentes reais.
PERFIS_REFERENCIA = {
    "H1": ("Haste", "Jovem ativo", {"idade": 40, "sexo": "M", "atividade": "alta"}),
    "H2": ("Haste", "Idosa com osteoporose", {"idade": 78, "sexo": "F", "atividade": "baixa",
                                              "osteoporose": "sim"}),
    "H3": ("Haste", "IMC 38", {"idade": 65, "imc": 38}),
    "S1": ("Stent", "Alergia ao níquel", {"alergia_niquel": "sim"}),
    "S2": ("Stent", "Vaso de 2,5 mm com alergia ao níquel", {"vaso_mm": 2.5, "alergia_niquel": "sim"}),
    "C1": ("Scaffold", "Defeito com carga", {"defeito": "com_carga"}),
    "C2": ("Scaffold", "Defeito sem carga", {"defeito": "sem_carga"}),
    "D1": ("Implante dentário", "Gengiva fina", {"gengiva_mm": 1.5}),
    "D2": ("Implante dentário", "Bruxismo", {"bruxismo": "sim"}),
    "D3": ("Implante dentário", "Alergia ao titânio confirmada por teste",
           {"alergia_titanio_confirmada": "sim"}),
}


@dataclass
class ResultadoPerfil:
    """Resultado de um perfil: problema ajustado, ranking e o que mudou face ao caso de base."""
    problema: DecisionProblem          # pesos, critérios e candidatos já ajustados
    ranking: pd.DataFrame              # rank_all_methods + consenso de Borda
    regras: pd.DataFrame               # linhas de perfis_doente.csv que se aplicaram
    excluidos: list[str] = field(default_factory=list)
    notas: list[str] = field(default_factory=list)


def ler_regras(data_dir: Path = DATA) -> pd.DataFrame:
    """Lê data/perfis_doente.csv (uma linha por regra).

    Em linguagem simples: carrega a tabela das regras aprovadas, com a fonte e o estado de cada uma.
    """
    return pd.read_csv(data_dir / "perfis_doente.csv", dtype={"valor": str})


_COND = re.compile(r"^\s*([\w]+)\s*(<=|>=|<|>|=)\s*(.+?)\s*$")


def _num(x) -> float | None:
    """Converte para número (aceita vírgula decimal); None se não for número."""
    try:
        return float(str(x).replace(",", "."))
    except ValueError:
        return None


def condicao_cumprida(codigo: str, perfil: dict) -> bool:
    """Diz se o perfil cumpre o condicao_codigo de uma regra.

    Em linguagem simples: lê condições como "idade<60; atividade=alta" e verifica cada uma com
    os dados do doente; só dá verdadeiro se todas se verificarem. Um dado que falta no perfil
    conta como "não se verifica" (ex.: sem IMC, a regra do IMC não se aplica).
    """
    for parte in str(codigo).split(";"):
        if not parte.strip():
            continue
        m = _COND.match(parte)
        if not m:
            raise ValueError(f"condição ilegível: {parte!r}")
        chave, op, esperado = m.groups()
        if chave not in perfil or perfil[chave] is None:
            return False
        dado = perfil[chave]
        if op == "=":
            a, b = _num(dado), _num(esperado)
            iguais = (a == b) if a is not None and b is not None else \
                str(dado).strip().lower() == esperado.strip().lower()
            if not iguais:
                return False
            continue
        a, b = _num(dado), _num(esperado)
        if a is None or b is None:
            raise ValueError(f"comparação numérica com valor não numérico: {parte!r} ({dado!r})")
        if not {"<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b}[op]:
            return False
    return True


def regras_ativas(caso: str, perfil: dict, data_dir: Path = DATA) -> pd.DataFrame:
    """Regras da tabela que se aplicam a este caso e a este doente.

    Em linguagem simples: das 17 regras, fica só com as do dispositivo escolhido cujas
    condições o doente cumpre.
    """
    regras = ler_regras(data_dir)
    regras = regras[regras["dispositivo"] == CASOS[caso]]
    return regras[[condicao_cumprida(c, perfil) for c in regras["condicao_codigo"]]].reset_index(drop=True)


def _criterio_acrescentado(alvo: str) -> tuple[str, str]:
    """Separa "Teor de níquel (custo)" em ("Teor de níquel", "cost")."""
    m = re.match(r"^(.*?)\s*\((custo|benefício)\)\s*$", alvo)
    if not m:
        raise ValueError(f"critério acrescentado sem tipo (custo ou benefício): {alvo!r}")
    return m.group(1), _TIPO_ACRESCENTADO[m.group(2)]


def _leitura(alvo: str) -> tuple[str, ...]:
    """Ligações do problema crítico pedidas por uma regra "leitura do problema"."""
    for chave, lig in LEITURAS.items():
        if chave in alvo:
            return lig
    raise ValueError(f"leitura do problema desconhecida: {alvo!r}")


def excluir(problem: DecisionProblem, materiais: list[str]) -> tuple[DecisionProblem, list[str]]:
    """Tira materiais do problema; devolve o problema reduzido e os que saíram de facto.

    Em linguagem simples: os materiais da lista deixam de ser candidatos; os que não estavam
    no problema são ignorados. Se ficarem menos de dois, não há ranking e dá erro.
    """
    alvo = set(materiais)
    ficam = [i for i, a in enumerate(problem.alternatives) if a not in alvo]
    sai = [a for a in problem.alternatives if a in alvo]
    if len(ficam) < 2:
        raise ValueError("a exclusão deixa menos de dois materiais")
    return replace(problem, alternatives=[problem.alternatives[i] for i in ficam],
                   X_min=problem.X_min[ficam], X_max=problem.X_max[ficam],
                   X_tipico=None if problem.X_tipico is None else problem.X_tipico[ficam]), sai


def multiplicar_pesos(problem: DecisionProblem, fatores: dict[str, float]) -> DecisionProblem:
    """Multiplica o peso de cada critério pelo seu fator e renormaliza (soma 1).

    Em linguagem simples: os critérios indicados ganham importância (fator 2 = o dobro) e os
    outros perdem peso na mesma proporção, para que o total continue a ser 1.
    """
    w = problem.weights.astype(float).copy()
    for crit, f in fatores.items():
        if f <= 0:
            raise ValueError("o fator tem de ser positivo")
        if crit not in problem.criteria:
            raise ValueError(f"critério da regra não existe no problema: {crit!r}")
        w[problem.criteria.index(crit)] *= f
    return replace(problem, weights=w / w.sum())


def acrescentar_criterio(problem: DecisionProblem, caso: str, propriedade: str, tipo: str, peso: float,
                         data_dir: Path = DATA) -> DecisionProblem:
    """Acrescenta um critério (propriedade de data/materiais.csv) com o peso dado.

    Em linguagem simples: junta uma coluna nova à matriz (ex.: o teor de níquel, critério de
    custo) com o peso pedido; os outros critérios ficam com 1 menos esse peso, repartido na
    mesma proporção que antes. Os valores mínimo, máximo e típico vêm da base de dados.
    """
    if not 0 < peso < 1:
        raise ValueError("o peso do critério acrescentado tem de estar em ]0, 1[")
    mat, _ = load_data(data_dir)
    sub = mat[(mat["caso_componente"] == CASOS[caso]) & (mat["propriedade"] == propriedade)]
    sub = sub.drop_duplicates("material").set_index("material")
    falta = [a for a in problem.alternatives if a not in sub.index or pd.isna(sub.loc[a, "min"])]
    if falta:
        raise ValueError(f"{propriedade!r} sem valor para: {falta}")
    sub = sub.loc[problem.alternatives]
    lo, hi = sub["min"].to_numpy(float), sub["max"].to_numpy(float)
    tip = sub["tipico"].astype(float).fillna(pd.Series((lo + hi) / 2, index=sub.index)).to_numpy(float)
    if tipo == "cost" and np.any(lo < 0):
        # um valor 0 é aceite (o WASPAS usa a eq. 11 com T = 0); um valor negativo não tem sentido num teor
        raise ValueError(f"{propriedade!r} tem valores negativos num critério de custo")
    X_tip = problem.X if problem.X_tipico is None else problem.X_tipico
    return replace(problem, criteria=[*problem.criteria, propriedade],
                   X_min=np.column_stack([problem.X_min, lo]), X_max=np.column_stack([problem.X_max, hi]),
                   X_tipico=np.column_stack([X_tip, tip]),
                   types=[*problem.types, tipo], targets=[*problem.targets, None],
                   weights=np.append(problem.weights * (1 - peso), peso))


def aplicar_regras(problem: DecisionProblem, caso: str, regras: pd.DataFrame,
                   data_dir: Path = DATA) -> tuple[DecisionProblem, list[str], list[str]]:
    """Aplica as regras ativas a um problema; devolve (problema ajustado, excluídos, notas).

    Em linguagem simples: primeiro tira os materiais excluídos, depois sobe o peso dos
    critérios (o maior fator quando várias regras mexem no mesmo critério), e por fim
    acrescenta critérios novos com o peso da tabela. As notas só se devolvem, não mudam nada.
    """
    excluidos, notas, fatores, acrescentar = [], [], {}, []
    for r in regras.itertuples():
        if r.efeito == "exclusão":
            problem, sai = excluir(problem, [s.strip() for s in r.alvo_do_efeito.split(";")])
            excluidos += sai
        elif r.efeito == "nota":
            notas.append(r.alvo_do_efeito)
        elif r.efeito == "peso multiplicado":
            fatores[r.alvo_do_efeito] = max(fatores.get(r.alvo_do_efeito, 0.0), float(r.valor))
        elif r.efeito == "leitura do problema":
            for crit in criterios_do_problema(CASOS[caso], _leitura(r.alvo_do_efeito), data_dir):
                if crit in problem.criteria:  # como em com_foco: critérios só do cenário B ignoram-se
                    fatores[crit] = max(fatores.get(crit, 0.0), float(r.valor))
        elif r.efeito == "critério acrescentado":
            acrescentar.append(r)
        else:
            raise ValueError(f"efeito desconhecido: {r.efeito!r}")
    if fatores:
        problem = multiplicar_pesos(problem, fatores)
    for r in acrescentar:
        prop, tipo = _criterio_acrescentado(r.alvo_do_efeito)
        problem = acrescentar_criterio(problem, caso, prop, tipo, float(r.valor), data_dir)
    return problem, excluidos, notas


def avaliar_perfil(caso: str, perfil: dict, cenario: str = "A", data_dir: Path = DATA) -> ResultadoPerfil:
    """Ponto de entrada: ranking de um caso para um doente (serve run_all.py e a app).

    Em linguagem simples: constrói o problema do caso (cenário A por omissão), escolhe as
    regras que o doente ativa, ajusta candidatos, pesos e critérios, e corre os três métodos
    e o consenso de Borda. Um perfil vazio dá o ranking de referência.
    """
    if caso not in CASOS:
        raise ValueError(f"caso desconhecido: {caso!r} (use um de {list(CASOS)})")
    base = build_problem(CASOS[caso], cenario, data_dir)
    regras = regras_ativas(caso, perfil, data_dir)
    problem, excluidos, notas = aplicar_regras(base, caso, regras, data_dir)
    ranking = consenso_borda(rank_all_methods(problem))
    return ResultadoPerfil(problem, ranking, regras, excluidos, notas)


def tabela_referencia(cenario: str = "A", data_dir: Path = DATA) -> pd.DataFrame:
    """Tabela dos casos de referência (PERFIS_REFERENCIA) com a comparação com o caso de base.

    Em linguagem simples: para cada perfil de exemplo guarda, por material, as pontuações e
    posições dos três métodos e do consenso, as posições no caso de base (pos_ref_*), as
    regras aplicadas e os materiais excluídos. É o ficheiro results/perfis_referencia.csv,
    contra o qual a aplicação é testada.
    """
    partes = []
    for pid, (caso, descricao, perfil) in PERFIS_REFERENCIA.items():
        res = avaliar_perfil(caso, perfil, cenario, data_dir)
        ref = avaliar_perfil(caso, {}, cenario, data_dir).ranking.set_index("material")
        df = res.ranking.copy()
        for k in ("TOPSIS", "WASPAS", "VIKOR", "Borda"):
            df[f"pos_ref_{k}"] = df["material"].map(ref[f"pos_{k}"]).astype(int)
        pesos = dict(zip(res.problema.criteria, res.problema.weights))
        partes.append(df.assign(
            perfil=pid, descricao=descricao, caso=caso, cenario=cenario,
            entradas="; ".join(f"{k}={v}" for k, v in perfil.items()),
            regras="; ".join(res.regras["id"]), excluidos="; ".join(res.excluidos),
            notas="; ".join(res.notas),
            pesos=json.dumps({c: round(float(w), 10) for c, w in pesos.items()}, ensure_ascii=False)))
    out = pd.concat(partes, ignore_index=True)
    primeiras = ["perfil", "descricao", "caso", "cenario", "entradas", "regras", "excluidos", "notas", "material"]
    return out[primeiras + [c for c in out.columns if c not in primeiras]]
