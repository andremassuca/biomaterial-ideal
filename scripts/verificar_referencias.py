"""Verifica as citações do relatório contra a lista única de referências (relatorio/referencias.md).

Uma citação no texto tem a forma "Apelido [et al.|e Apelido|& Apelido] AAAA" (ex.: "Higuchi et al. 2019",
"Hu e Yoon 2018", "NJR 2026"); a chave correspondente é "Apelido AAAA" (apelido do primeiro autor ou
entidade). Mostra as citações sem referência e as referências que nenhum texto cita.
Também converte as citações para autor-ano no estilo APA 7, para a montagem do relatório
(scripts/montar_relatorio.py): "(Petković et al., 2025)" dentro de parênteses e "Petković et al. (2025)" na frase.
Uso: python scripts/verificar_referencias.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
REFERENCIAS = RAIZ / "relatorio" / "referencias.md"
# Textos do relatório, pela ordem em que entram no RELATORIO.md.
TEXTOS = ["resumo_rascunho.md", "introducao_rascunho.md", "metodos_rascunho.md", "validacao_rascunho.md",
          "caso_anca_rascunho.md", "caso_stent_rascunho.md", "caso_scaffold_rascunho.md",
          "caso_dentario_rascunho.md", "extensoes_rascunho.md", "discussao_rascunho.md", "conclusao_rascunho.md",
          "anexo_a_equacoes.md", "glossario.md", "tabelas/comparacao_estudos.md"]

_NOME = r"(?:(?:Le|De|Van) )?[A-ZÁÉÍÓÚÂÊÔÃÕÇÅÖÜ][\w'’\-]+"
# O ano pode vir solto ("Higuchi et al. 2019") ou entre parênteses ("Higuchi et al. (2019)").
CITACAO = re.compile(rf"\b(?P<nome>{_NOME})(?P<meio> et al\.,?| e {_NOME}| & {_NOME})?,? "
                     rf"(?:\((?P<anop>(?:19|20)\d\d)\)|(?P<ano>(?:19|20)\d\d)\b)")


def _ano(m: re.Match) -> str:
    return m["ano"] or m["anop"]


ENTRADA = re.compile(r"^- \[(?P<chave>[^\]]+)\] (?P<texto>.+)$")


def ler_referencias(caminho: Path = REFERENCIAS) -> dict[str, str]:
    """Entradas da lista única: {chave: texto da referência}."""
    out = {}
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        m = ENTRADA.match(linha)
        if m:
            out[m["chave"]] = m["texto"]
    return out


def citacoes(texto: str, chaves: set[str] | None = None) -> list[str]:
    """Chaves citadas num texto, pela ordem da primeira ocorrência e sem repetições.

    Em linguagem simples: procura "Apelido (et al.) ano" e devolve "Apelido ano". Com `chaves`,
    só conta as que estão na lista ou que têm "et al." ou um segundo autor (para não confundir
    nomes próprios seguidos de um ano, como "Absorb 2017", com citações).
    """
    vistas = []
    for m in CITACAO.finditer(texto):
        k = f"{m['nome']} {_ano(m)}"
        if chaves is not None and k not in chaves and not m["meio"]:
            continue
        if k not in vistas:
            vistas.append(k)
    return vistas


def verificar(pasta: Path = RAIZ / "relatorio", referencias: Path = REFERENCIAS) -> tuple[list[str], list[str]]:
    """Devolve (citações sem referência, referências não citadas)."""
    refs = ler_referencias(referencias)
    citadas = []
    for nome in TEXTOS:
        p = pasta / nome
        if p.exists():
            for k in citacoes(p.read_text(encoding="utf-8"), set(refs)):
                if k not in citadas:
                    citadas.append(k)
    sem_ref = [k for k in citadas if k not in refs]
    nao_citadas = sorted(k for k in refs if k not in citadas)
    return sem_ref, nao_citadas


def rotulo(entrada: str) -> str:
    """Nome do autor a usar no texto, a partir da entrada APA da lista.

    Em linguagem simples: 1 autor dá "Apelido"; 2 autores, "Apelido e Apelido"; 3 ou mais, "Apelido et al.";
    uma entidade com sigla entre parênteses retos ("National Joint Registry [NJR]") dá a sigla.
    """
    sigla = re.match(r"^[^(]*?\[(?P<s>[^\]]+)\]\. \(", entrada)
    if sigla:
        return sigla["s"]
    autores = entrada.split(" (", 1)[0]
    apelidos = re.findall(r"(?:^|(?<=\.), (?:e )?)([^,(]+?), [A-ZÁÉÍÓÚÅÖÜ]\.", autores)
    if len(apelidos) == 1 and not re.search(r"\., e ", autores):
        return apelidos[0]
    if len(apelidos) == 2 and autores.count(", e ") == 1 and autores.count(".,") == 1:
        return f"{apelidos[0]} e {apelidos[1]}"
    return f"{apelidos[0]} et al."


def entre_parenteses(texto: str, pos: int) -> bool:
    """True se a posição está dentro de parênteses abertos na mesma linha (ou na mesma célula de tabela)."""
    inicio = max(texto.rfind(chr(10), 0, pos), texto.rfind("|", 0, pos)) + 1
    trecho = texto[inicio:pos]
    return trecho.count("(") > trecho.count(")")


def citar_apa(texto: str, refs: dict[str, str]) -> tuple[str, list[str]]:
    """Reescreve as citações da lista no formato APA e devolve o texto e as chaves citadas.

    Ex.: "(Higuchi et al. 2019; Hu e Yoon 2018)" passa a "(Higuchi et al., 2019; Hu e Yoon, 2018)" e
    "segundo Petković et al. 2025" passa a "segundo Petković et al. (2025)". O nome vem da lista (rotulo),
    por isso fica certo mesmo que o rascunho use "et al." com dois autores. Citações fora da lista ficam como estão.
    """
    citadas: list[str] = []

    def troca(m: re.Match) -> str:
        k = f"{m['nome']} {_ano(m)}"
        if k not in refs:
            return m.group(0)
        if k not in citadas:
            citadas.append(k)
        nome = rotulo(refs[k])
        return f"{nome}, {_ano(m)}" if entre_parenteses(texto, m.start()) else f"{nome} ({_ano(m)})"

    return CITACAO.sub(troca, texto), citadas


def main() -> int:
    sem_ref, nao_citadas = verificar()
    print(f"Citações sem referência ({len(sem_ref)}):")
    print("\n".join(f"  - {k}" for k in sem_ref) or "  nenhuma")
    print(f"Referências não citadas ({len(nao_citadas)}):")
    print("\n".join(f"  - {k}" for k in nao_citadas) or "  nenhuma")
    return 1 if sem_ref else 0


if __name__ == "__main__":
    sys.exit(main())
