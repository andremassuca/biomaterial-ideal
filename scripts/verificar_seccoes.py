"""Verifica as referências cruzadas do relatório montado ("secção N.M", "capítulo N", "Anexo X").

Uso: python scripts/verificar_seccoes.py [relatorio/RELATORIO.md]

Para cada referência no texto, procura o título correspondente no relatório e grava em
results/referencias_cruzadas.md a lista (linha, referência, título de destino), para rever à mão que cada uma aponta
para o sítio certo. Sai com erro se alguma referência apontar para uma secção que não existe.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
RELATORIO = RAIZ / "relatorio" / "RELATORIO.md"
SAIDA = RAIZ / "results" / "referencias_cruzadas.md"

TITULO = re.compile(r"^(#{1,3}) (?:(?P<num>\d+(?:\.\d+)*)\.?|Anexo (?P<anexo>[A-Z])(?:\.|\b)|(?P<sub>[A-Z]\.\d+)) ?(?P<texto>.*)$")
# "secção 8.3", "secções 4 a 7", "secções 8.3 e 8.4", "capítulo 8", "Anexo A", "Anexo A.5"
REF = re.compile(r"\b(?P<tipo>[Ss]ecç(?:ão|ões)|[Cc]apítulos?|[Aa]nexo)\s+(?P<alvo>[A-Z]?\d*(?:\.\d+)*[A-Z]?)"
                 r"(?:\s+(?P<lig>a|e)\s+(?P<alvo2>\d+(?:\.\d+)*))?")


def titulos(texto: str) -> dict[str, str]:
    """{"8": "Extensões exploratórias", "8.3": "...", "A": "Equações dos métodos", "A.5": "..."}."""
    out = {}
    for linha in texto.splitlines():
        m = TITULO.match(linha)
        if not m:
            continue
        chave = m["num"] or m["anexo"] or m["sub"]
        if chave:
            out[chave] = m["texto"].strip().lstrip(". ")
    return out


def intervalo(a: str, b: str) -> list[str]:
    """"4" a "7" -> ["4", "5", "6", "7"] (só para números inteiros de capítulo)."""
    if a.isdigit() and b.isdigit():
        return [str(i) for i in range(int(a), int(b) + 1)]
    return [a, b]


def referencias(texto: str) -> list[tuple[int, str, str]]:
    """(linha, texto da referência, chave de destino) de cada referência no corpo (antes das Referências)."""
    corpo = texto.split("\n# Referências", 1)[0]
    out = []
    for n, linha in enumerate(corpo.splitlines(), start=1):
        if linha.startswith("#") or linha.startswith("!["):
            continue
        for m in REF.finditer(linha):
            alvo = m["alvo"].rstrip(".")
            if not alvo:
                continue
            # anexos do relatório: "Anexo" com maiúscula e uma letra (A, B, C) ou "A.5"; "anexo VI" de um
            # regulamento não é uma referência interna
            if m["tipo"].lower() == "anexo" and (m["tipo"][0] == "a" or not re.fullmatch(r"[A-Z](?:\.\d+)?", alvo)):
                continue
            chaves = [alvo]
            if m["alvo2"]:
                chaves = intervalo(alvo, m["alvo2"]) if m["lig"] == "a" else [alvo, m["alvo2"]]
            for c in chaves:
                out.append((n, m.group(0), c))
    return out


def verificar(texto: str) -> tuple[list[tuple[int, str, str, str]], list[tuple[int, str, str]]]:
    """Devolve (referências resolvidas com o título de destino, referências sem destino)."""
    t = titulos(texto)
    ok, falhas = [], []
    for n, ref, c in referencias(texto):
        if c in t:
            ok.append((n, ref, c, t[c]))
        else:
            falhas.append((n, ref, c))
    return ok, falhas


def main() -> None:
    caminho = Path(sys.argv[1]) if len(sys.argv) > 1 else RELATORIO
    texto = caminho.read_text(encoding="utf-8")
    ok, falhas = verificar(texto)
    linhas = ["# Referências cruzadas do relatório", "",
              f"Gerado por scripts/verificar_seccoes.py a partir de {caminho.relative_to(RAIZ).as_posix()}. "
              "Rever que cada referência aponta para o assunto certo.", "",
              "| Linha | Referência | Destino | Título do destino |", "|---|---|---|---|"]
    linhas += [f"| {n} | {r} | {c} | {tit} |" for n, r, c, tit in ok]
    linhas += [f"| {n} | {r} | {c} | SEM DESTINO |" for n, r, c in falhas]
    SAIDA.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print("\n".join(linhas))
    if falhas:
        sys.exit(f"{len(falhas)} referência(s) sem destino")


if __name__ == "__main__":
    main()
