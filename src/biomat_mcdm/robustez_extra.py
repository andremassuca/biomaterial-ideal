"""Análises de robustez complementares: retirar uma alternativa, dupla contagem por dimensões
e menor ajuste (de um peso ou de um valor) que troca o vencedor.

Funções puras sobre um DecisionProblem (não escrevem ficheiros); scripts/robustez_extra.py
junta-as para os três casos quantitativos e grava results/robustez_extra.md.

Regra de empate do trabalho (LIMIAR_EMPATE): no TOPSIS, dois materiais com diferença de C
inferior a 0,01 contam como empatados. Aqui:
  - uma "troca" do vencedor é sempre estrita (outro material passa a ter melhor pontuação);
  - no TOPSIS regista-se também a variação a partir da qual o vencedor deixa de ter folga
    de 0,01 sobre o 2.º (passa a "empate"), que chega sempre antes da troca estrita;
  - na reversão de ranking, os pares do TOPSIS que trocam com ΔC < 0,01 (antes ou depois)
    ficam assinalados como empates.
"""
from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from biomat_mcdm.io import DATA, DecisionProblem, load_data
from biomat_mcdm.robustness import com_peso, e_ordinal, pontuacoes

METODOS = ["TOPSIS", "WASPAS", "VIKOR"]
LIMIAR_EMPATE = 0.01  # igual a scripts/tabelas_relatorio.py e scripts/figuras.py (ΔC do TOPSIS)
SUFIXO_B = " (só cenário B)"


# ---------- utilitários ----------

def merito(problem: DecisionProblem, metodo: str, w: np.ndarray | None = None,
           X: np.ndarray | None = None) -> np.ndarray:
    """Pontuação de cada material em que maior é sempre melhor.

    Em linguagem simples: o TOPSIS (C) e o WASPAS (Q) já são "maior = melhor"; no VIKOR
    (P, menor = melhor) troca-se o sinal, para todas as comparações se fazerem da mesma forma.
    """
    w = problem.weights if w is None else w
    X = problem.X if X is None else X
    s = pontuacoes(X, w, problem.types, problem.targets, metodo)
    return -s if metodo == "VIKOR" else s


def folga(m: np.ndarray, i: int) -> float:
    """Diferença entre a pontuação do material i e a do melhor dos outros (positiva = i à frente)."""
    outros = np.delete(np.asarray(m, float), i)
    return float(m[i] - outros.max())


# ---------- a) retirar uma alternativa (reversão de ranking) ----------

def retirar_alternativa(problem: DecisionProblem, material: str) -> DecisionProblem:
    """O mesmo problema sem um material (critérios, pesos e alvos iguais).

    Em linguagem simples: tira uma linha da matriz de decisão; tudo o resto fica igual.
    """
    i = problem.alternatives.index(material)
    ficam = [k for k in range(len(problem.alternatives)) if k != i]
    return replace(problem, alternatives=[problem.alternatives[k] for k in ficam],
                   X_min=problem.X_min[ficam], X_max=problem.X_max[ficam],
                   X_tipico=None if problem.X_tipico is None else problem.X_tipico[ficam])


def pares_trocados(alts: list[str], antes: dict[str, float], depois: dict[str, float]) -> list[tuple[str, str]]:
    """Pares de materiais cuja ordem relativa se inverte entre duas pontuações (maior = melhor).

    Em linguagem simples: para cada par (a, b), se a estava estritamente à frente de b e passa
    a estar estritamente atrás, o par trocou. Devolve (a, b) com a = o que estava à frente.
    """
    out = []
    for k, a in enumerate(alts):
        for b in alts[k + 1:]:
            if antes[a] > antes[b] and depois[b] > depois[a]:
                out.append((a, b))
            elif antes[b] > antes[a] and depois[a] > depois[b]:
                out.append((b, a))
    return out


def reversao_ranking(problem: DecisionProblem, metodos: list[str] = METODOS) -> pd.DataFrame:
    """Retira cada material à vez e vê se a ordem dos restantes muda, em cada método.

    Em linguagem simples: é o teste clássico de "reversão de ranking". Se tirar um material
    fraco mudar a ordem entre os outros, o método depende do conjunto de candidatos (porque
    a normalização usa o máximo e o mínimo de cada coluna). No TOPSIS, um par que troca com
    diferença de C inferior a LIMIAR_EMPATE (antes ou depois) fica marcado como empate.
    Colunas: retirado, metodo, alterado, so_empates, pares, vencedor_antes, vencedor_depois.
    """
    base = {m: dict(zip(problem.alternatives, merito(problem, m))) for m in metodos}
    linhas = []
    for mat in problem.alternatives:
        p = retirar_alternativa(problem, mat)
        for m in metodos:
            antes = {a: base[m][a] for a in p.alternatives}
            depois = dict(zip(p.alternatives, merito(p, m)))
            pares = pares_trocados(p.alternatives, antes, depois)
            empate = [m == "TOPSIS" and (abs(antes[a] - antes[b]) < LIMIAR_EMPATE
                                         or abs(depois[a] - depois[b]) < LIMIAR_EMPATE) for a, b in pares]
            linhas.append({"retirado": mat, "metodo": m, "alterado": bool(pares),
                           "so_empates": bool(pares) and all(empate),
                           "pares": "; ".join(f"{a} ↔ {b}" + (" (empate)" if e else "")
                                              for (a, b), e in zip(pares, empate)),
                           "vencedor_antes": max(antes, key=antes.get),
                           "vencedor_depois": max(depois, key=depois.get)})
    return pd.DataFrame(linhas)


# ---------- b) dupla contagem: pesos redistribuídos dentro de cada dimensão ----------

def carregar_dimensoes(caso: str, data_dir: Path = DATA) -> dict[str, str]:
    """Mapa critério → dimensão de um caso (data/dimensoes_criterios.csv).

    Em linguagem simples: diz em que "família" (mecânica, biológica, clínica, económica) fica
    cada critério. Os nomes saem sem "(só cenário B)", como em DecisionProblem.criteria.
    """
    d = pd.read_csv(data_dir / "dimensoes_criterios.csv")
    d = d[d["caso"] == caso]
    return {c.replace(SUFIXO_B, ""): dim for c, dim in zip(d["criterio"], d["dimensao"])}


def grupos_dimensao(criteria: list[str], dims: dict[str, str]) -> dict[str, list[int]]:
    """Índices dos critérios do problema agrupados por dimensão (pela ordem em que aparecem).

    Em linguagem simples: transforma o mapa critério → dimensão numa lista de colunas por
    dimensão. Um critério sem dimensão é um erro (o ficheiro de dimensões está incompleto).
    """
    falta = [c for c in criteria if c not in dims]
    if falta:
        raise ValueError(f"critérios sem dimensão: {falta}")
    out: dict[str, list[int]] = {}
    for j, c in enumerate(criteria):
        out.setdefault(dims[c], []).append(j)
    return out


def pesos_iguais_na_dimensao(weights: np.ndarray, grupos: dict[str, list[int]]) -> np.ndarray:
    """Mantém o peso total de cada dimensão e reparte-o em partes iguais pelos seus critérios.

    Em linguagem simples: se a dimensão mecânica pesa 0,60 e tem 4 critérios, cada um passa a
    pesar 0,15. Assim, ter vários critérios parecidos não dá mais nem menos peso à dimensão.
    """
    w = np.asarray(weights, float)
    out = np.empty_like(w)
    for idx in grupos.values():
        out[idx] = w[idx].sum() / len(idx)
    return out


def sortear_na_dimensao(weights: np.ndarray, grupos: dict[str, list[int]],
                        rng: np.random.Generator, alpha: float = 1.0) -> np.ndarray:
    """Uma redistribuição ao acaso dos pesos dentro de cada dimensão (Dirichlet).

    Em linguagem simples: o peso total de cada dimensão fica fixo; a forma como se reparte
    pelos seus critérios é sorteada. Com alpha = 1 todas as repartições são igualmente
    prováveis (distribuição uniforme no simplex). Dimensões com um só critério não mudam.
    """
    w = np.asarray(weights, float)
    out = w.copy()
    for idx in grupos.values():
        if len(idx) > 1:
            out[idx] = w[idx].sum() * rng.dirichlet(np.full(len(idx), alpha))
    return out


def dupla_contagem(problem: DecisionProblem, dims: dict[str, str], n_iter: int = 10_000,
                   seed: int = 42, metodos: list[str] = METODOS) -> pd.DataFrame:
    """Vencedores com pesos iguais dentro de cada dimensão e % de manutenção no Monte Carlo.

    Em linguagem simples: testa se o resultado depende de como o peso de cada dimensão foi
    repartido pelos seus critérios (por exemplo, três critérios mecânicos parecidos a contar
    três vezes). Os sorteios são os mesmos para os três métodos (mesma seed).
    Colunas: metodo, vencedor_base, vencedor_iguais, pct_mantem (troca estrita) e
    pct_mantem_ou_empate (no TOPSIS conta também o vencedor a menos de LIMIAR_EMPATE do 1.º),
    outro_vencedor e pct_outro (o material que mais vezes fica em 1.º no lugar do vencedor).
    """
    if n_iter < 1:
        raise ValueError("n_iter tem de ser ≥ 1")
    grupos = grupos_dimensao(problem.criteria, dims)
    alts = problem.alternatives
    venc = {m: int(np.argmax(merito(problem, m))) for m in metodos}
    w_ig = pesos_iguais_na_dimensao(problem.weights, grupos)
    rng = np.random.default_rng(seed)
    mantem = {m: 0 for m in metodos}
    mantem_emp = {m: 0 for m in metodos}
    primeiros = {m: np.zeros(len(alts), int) for m in metodos}
    for _ in range(n_iter):
        w = sortear_na_dimensao(problem.weights, grupos, rng)
        for m in metodos:
            s = merito(problem, m, w)
            f = folga(s, venc[m])
            mantem[m] += f > 0
            mantem_emp[m] += f > 0 or (m == "TOPSIS" and f > -LIMIAR_EMPATE)
            primeiros[m][int(np.argmax(s))] += 1
    linhas = []
    for m in metodos:
        outros = primeiros[m].copy()
        outros[venc[m]] = -1
        k = int(np.argmax(outros))
        linhas.append({"metodo": m, "vencedor_base": alts[venc[m]],
                       "vencedor_iguais": alts[int(np.argmax(merito(problem, m, w_ig)))],
                       "pct_mantem": 100 * mantem[m] / n_iter,
                       "pct_mantem_ou_empate": 100 * mantem_emp[m] / n_iter,
                       "outro_vencedor": alts[k] if outros[k] > 0 else "",
                       "pct_outro": 100 * max(outros[k], 0) / n_iter,
                       "n_iter": n_iter, "seed": seed})
    return pd.DataFrame(linhas)


def pesos_por_dimensao(problem: DecisionProblem, dims: dict[str, str]) -> dict[str, float]:
    """Peso total de cada dimensão no problema (soma 1)."""
    return {d: float(problem.weights[idx].sum()) for d, idx in grupos_dimensao(problem.criteria, dims).items()}


# ---------- c) menor ajuste que troca o vencedor ----------

def menor_variacao(muda: Callable[[float], bool], limite: float, passo: float = 0.005,
                   tol: float = 1e-4) -> float | None:
    """Menor variação d (com o sinal de `limite`) para a qual muda(d) é verdadeiro.

    Em linguagem simples: anda em passos pequenos a partir de 0 até ao limite; no primeiro
    passo em que o resultado muda, afina por bisseção entre esse passo e o anterior. Devolve
    None se não mudar até ao limite. (Encontra a primeira mudança a partir de 0, mesmo que a
    resposta não seja monótona.)
    """
    sinal = 1.0 if limite > 0 else -1.0
    n = int(np.ceil(abs(limite) / passo - 1e-9))
    anterior = 0.0
    for k in range(1, n + 1):
        d = sinal * min(k * passo, abs(limite))
        if muda(d):
            lo, hi = anterior, d
            while abs(hi - lo) > tol:
                meio = (lo + hi) / 2
                if muda(meio):
                    hi = meio
                else:
                    lo = meio
            return hi
        anterior = d
    return None


def _menor_abs(a: float | None, b: float | None) -> float | None:
    """A variação de menor valor absoluto entre duas (None = não troca)."""
    vals = [v for v in (a, b) if v is not None]
    return min(vals, key=abs) if vals else None


def ajuste_minimo_pesos(problem: DecisionProblem, limite: float = 1.0, passo: float = 0.005,
                        metodos: list[str] = METODOS) -> pd.DataFrame:
    """Para cada critério e método, a menor variação relativa do peso que troca o 1.º lugar.

    Em linguagem simples: muda só o peso de um critério (de -100 %, peso zero, até +limite),
    os outros encolhem ou crescem na mesma proporção para a soma continuar a ser 1, e procura
    a variação mais pequena (para menos ou para mais) que põe outro material em 1.º.
    var = variação relativa (ex.: -0,30 = peso 30 % mais baixo); None = não troca até ao limite.
    No TOPSIS, var_empate é a variação a partir da qual a folga do vencedor fica abaixo de
    LIMIAR_EMPATE (0 se já está em empate no caso de base).
    """
    linhas = []
    for j, c in enumerate(problem.criteria):
        w0 = float(problem.weights[j])

        def pesos(d: float) -> np.ndarray:
            return com_peso(problem, c, min(w0 * (1 + d), 0.999)).weights

        for m in metodos:
            v0 = int(np.argmax(merito(problem, m)))
            troca = lambda d: int(np.argmax(merito(problem, m, pesos(d)))) != v0  # noqa: E731
            var = _menor_abs(menor_variacao(troca, -1.0, passo), menor_variacao(troca, limite, passo))
            novo = None if var is None else problem.alternatives[int(np.argmax(merito(problem, m, pesos(var))))]
            emp = None
            if m == "TOPSIS":
                if folga(merito(problem, m), v0) < LIMIAR_EMPATE:
                    emp = 0.0
                else:
                    empata = lambda d: folga(merito(problem, m, pesos(d)), v0) < LIMIAR_EMPATE  # noqa: E731
                    emp = _menor_abs(menor_variacao(empata, -1.0, passo), menor_variacao(empata, limite, passo))
            linhas.append({"criterio": c, "metodo": m, "peso": w0, "vencedor": problem.alternatives[v0],
                           "var": var, "peso_novo": None if var is None else w0 * (1 + var),
                           "novo_vencedor": novo, "var_empate": emp})
    return pd.DataFrame(linhas)


def ajuste_minimo_valores(problem: DecisionProblem, limite: float = 0.5, passo: float = 0.005,
                          metodos: list[str] = METODOS) -> pd.DataFrame:
    """Para cada valor típico (material, critério) e método, a menor variação que troca o 1.º.

    Em linguagem simples: muda um só número da matriz de decisão e procura a variação mais
    pequena que põe outro material em 1.º lugar.
      - critérios quantitativos: variação relativa contínua até ±limite (ex.: ±50 %);
      - critérios ordinais (1-5): passos inteiros (±1, ±2, ...) sem sair da escala 1-5; a
        coluna "pontos" guarda o passo e "var" a variação relativa equivalente.
    var = None quando não troca dentro do limite. No TOPSIS, var_empate como em
    ajuste_minimo_pesos (variação a partir da qual a folga do vencedor fica abaixo de 0,01).
    """
    X0 = problem.X
    linhas = []
    for j, c in enumerate(problem.criteria):
        ordinal = e_ordinal(c)
        for i, mat in enumerate(problem.alternatives):
            x0 = float(X0[i, j])

            def matriz(d: float) -> np.ndarray:
                X = X0.copy()
                X[i, j] = x0 + d if ordinal else x0 * (1 + d)
                return X

            for m in metodos:
                v0 = int(np.argmax(merito(problem, m)))
                troca = lambda d: int(np.argmax(merito(problem, m, X=matriz(d)))) != v0  # noqa: E731
                ja_empate = m == "TOPSIS" and folga(merito(problem, m), v0) < LIMIAR_EMPATE
                empata = lambda d: folga(merito(problem, m, X=matriz(d)), v0) < LIMIAR_EMPATE  # noqa: E731
                if ordinal:
                    passos = sorted((k for k in range(-4, 5) if k and 1 <= x0 + k <= 5), key=lambda k: (abs(k), k))
                    pts = next((k for k in passos if troca(k)), None)
                    var = None if pts is None else pts / x0
                    emp = None
                    if m == "TOPSIS":
                        e = 0 if ja_empate else next((k for k in passos if empata(k)), None)
                        emp = None if e is None else e / x0
                    novo_d = pts
                else:
                    pts = None
                    var = _menor_abs(menor_variacao(troca, -limite, passo), menor_variacao(troca, limite, passo))
                    emp = None
                    if m == "TOPSIS":
                        emp = 0.0 if ja_empate else _menor_abs(menor_variacao(empata, -limite, passo),
                                                                menor_variacao(empata, limite, passo))
                    novo_d = var
                novo = None if novo_d is None else problem.alternatives[int(np.argmax(merito(problem, m, X=matriz(novo_d))))]
                linhas.append({"material": mat, "criterio": c, "metodo": m, "ordinal": ordinal, "valor": x0,
                               "vencedor": problem.alternatives[v0], "var": var, "pontos": pts,
                               "valor_novo": None if novo_d is None else float(matriz(novo_d)[i, j]),
                               "novo_vencedor": novo, "var_empate": emp})
    return pd.DataFrame(linhas)


def mais_sensiveis(aj: pd.DataFrame, chaves: list[str]) -> pd.DataFrame:
    """Junta os três métodos e ordena pela menor variação que troca algum vencedor.

    Em linguagem simples: para cada peso (ou valor), fica a variação mais pequena entre os
    três métodos e a lista dos métodos que trocam com ela; os que não trocam em nenhum método
    vão para o fim. Serve para dizer o que mais importa verificar.
    """
    linhas = []
    for k, g in aj.groupby(chaves, sort=False):
        k = k if isinstance(k, tuple) else (k,)
        g2 = g[g["var"].notna()]
        linha = dict(zip(chaves, k))
        for col in ("peso", "valor", "ordinal"):
            if col in g:
                linha[col] = g[col].iloc[0]
        if g2.empty:
            linha.update({"var_min": None, "metodos": "", "novo_vencedor": "", "pontos": None})
        else:
            r = g2.loc[g2["var"].abs().idxmin()]
            iguais = g2[np.isclose(g2["var"].abs(), abs(r["var"]), atol=1e-3)]
            linha.update({"var_min": float(r["var"]), "metodos": ", ".join(iguais["metodo"]),
                          "novo_vencedor": r["novo_vencedor"], "pontos": r.get("pontos")})
        linha["abs"] = np.inf if linha["var_min"] is None else abs(linha["var_min"])
        linhas.append(linha)
    return pd.DataFrame(linhas).sort_values("abs", kind="stable").drop(columns="abs").reset_index(drop=True)


def fmt_var(var: float | None, limite: float, pontos: float | None = None) -> str:
    """Variação para as tabelas: "+12,3 %", "-1 ponto (-20 %)" ou "não troca até ±50 %".

    Em linguagem simples: escreve a variação relativa em percentagem com vírgula decimal; nos
    ordinais mostra primeiro o passo inteiro na escala 1-5. Sem troca, diz até onde se procurou.
    """
    if var is None or (isinstance(var, float) and np.isnan(var)):
        return f"não troca até ±{round(100 * limite)} %"
    p = f"{100 * var:+.1f} %".replace(".", ",")
    if pontos is not None and not (isinstance(pontos, float) and np.isnan(pontos)):
        k = int(round(pontos))
        return f"{k:+d} ponto{'s' if abs(k) > 1 else ''} ({p})"
    return p


# ---------- fontes dos valores ----------

def fontes_celulas(caso: str, data_dir: Path = DATA) -> pd.DataFrame:
    """Estado e referência de cada (material, propriedade) de um caso, de data/materiais.csv.

    Em linguagem simples: para dizer de onde vem cada número e se já foi verificado. Inclui os
    índices derivados (σy/E do stent), cujo estado depende das propriedades de origem.
    """
    mat, _ = load_data(data_dir)
    m = mat[mat["caso_componente"] == caso]
    return (m[["material", "propriedade", "estado", "referencia"]]
            .drop_duplicates(["material", "propriedade"]).reset_index(drop=True))


def referencia_curta(ref: str | float) -> str:
    """Referência resumida a "Apelido et al. ano" (ou "Apelido ano") a partir do texto da base.

    Em linguagem simples: a coluna referencia tem a citação completa; nas tabelas curtas basta
    o primeiro autor e o ano. Se o texto não começar por um autor reconhecível (fichas de
    fornecedor, escalas do trabalho), devolve o texto até à primeira vírgula, ponto e vírgula
    ou parêntese aberto depois de um espaço (até 40 caracteres).
    """
    if not isinstance(ref, str) or not ref.strip():
        return "sem referência"
    ref = ref.strip()
    ano = re.search(r"\b(19|20)\d{2}\b", ref)
    autor = re.match(r"([A-ZÀ-Ý][\w'À-ÿ-]+)\s+[A-Z]{1,3}\b(,)?", ref)
    if autor and ano:
        outros = autor.group(2) is not None
        return f"{autor.group(1)}{' et al.' if outros else ''} {ano.group(0)}"
    inicio = re.split(r"[,;]| \(", ref, maxsplit=1)[0].strip()
    return inicio[:40] + ("..." if len(inicio) > 40 else "")
