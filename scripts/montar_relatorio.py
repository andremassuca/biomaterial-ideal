"""Monta relatorio/RELATORIO.md a partir dos rascunhos, das tabelas geradas e das figuras.

Ordem: primeira página (logótipos, unidade curricular, título, autor, resumo estruturado e palavras-chave),
abstract (página 2), índice, 1 Introdução (com a Tabela 1, resumo dos casos), 2 Métodos, 3 Validação,
4-7 Casos (anca, stent, scaffold, implante dentário), 8 Extensões exploratórias, 9 Discussão, 10 Conclusões,
Referências, Normas e
legislação citadas, Anexos A, B (só a contagem por estado) e C (rubricas das escalas ordinais) e Glossário.
- Os marcadores <!-- incluir: tabelas/x.md --> e <!-- figura: fig_x --> são substituídos pelas tabelas
  de relatorio/tabelas/ e pelas figuras de results/figures/, numeradas pela ordem em que aparecem; as
  legendas saem por cima ("Tabela n." a negrito e o texto em itálico, pelo pacote caption).
- As citações "Apelido (et al.) ano" passam ao formato APA 7: "(Apelido et al., ano)" dentro de parênteses e
  "Apelido et al. (ano)" na frase; a lista de referências sai por ordem alfabética, a partir de
  relatorio/referencias.md.
- As normas ISO e ASTM citadas saem numa lista própria, por ordem alfabética.
- Formato: Times New Roman 11 pt (tabelas a 10 pt), títulos a negrito (14 pt e 12 pt) numerados com ponto,
  margens de 2 cm, texto justificado, números de página.
Correr antes scripts/run_all.py, scripts/figuras.py e scripts/tabelas_relatorio.py.
Uso: python scripts/montar_relatorio.py
"""
from __future__ import annotations

import csv
import json
import importlib.util
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
REL = RAIZ / "relatorio"
FIGURAS = "../results/figures"  # caminho relativo a relatorio/

_spec = importlib.util.spec_from_file_location("verificar_referencias", RAIZ / "scripts" / "verificar_referencias.py")
vr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vr)

CASOS = [("caso_anca_rascunho.md", 4), ("caso_stent_rascunho.md", 5), ("caso_scaffold_rascunho.md", 6),
         ("caso_dentario_rascunho.md", 7)]
NOMES_TABELA = {"haste": "haste femoral", "par": "par articular (semiquantitativo)", "stent": "stent vascular",
                "scaffold": "scaffold ósseo", "dentario": "implante dentário (semiquantitativo)"}
LEGENDAS = {
    "fig_a_rigidez_haste": "Razão entre o módulo de Young de cada liga candidata à haste e o do osso cortical "
                           "(barra: valor típico; traço: mínimo a máximo).",
    "fig_b_posicoes": "Posição de cada material por método (TOPSIS, WASPAS e VIKOR) nos três casos quantitativos, "
                      "cenários A e B (η = 1).",
    "fig_c_monte_carlo": "Monte Carlo das propriedades (10 000 iterações, cenário A): percentagem das iterações em "
                         "que cada material fica em 1.º lugar, por método.",
    "fig_d_vencedor_eta": "Material em 1.º lugar no cenário A, por método, quando η vai de 0 (só pesos objetivos) "
                          "a 1 (só pesos subjetivos).",
    "fig_e_resumo": "Resumo dos três casos quantitativos: vencedor por método, robustez no Monte Carlo das "
                    "propriedades e cenários em que o vencedor muda.",
    "fig_f_semiquantitativos": "Valores por critério nos casos semiquantitativos (par articular e implante "
                               "dentário), cenário A; cor do pior (claro) ao melhor (escuro) em cada critério.",
    "funil": "Funil da triagem: dos compostos do Materials Project aos materiais da base verificada e à "
             "recomendação por dispositivo (números de results/funil.md).",
    "fea/sed_corte_coronal": "Energia de deformação no osso num corte coronal do fémur, no pico da marcha: fémur "
                             "intacto e com as hastes de aço 316L, Co-Cr-Mo, Ti-6Al-4V ELI e Ti-6Al-4V poroso "
                             "(17 GPa) (simulação exploratória, secção 8.3).",
    "cfd/tawss_mapas": "Tensão de corte na parede média no ciclo (TAWSS) na parede da artéria aberta como uma "
                       "folha, com os struts finos (Pt-Cr, 79 µm) e grossos (316L, 135 µm); o sangue corre da "
                       "esquerda para a direita (simulação exploratória, secção 8.4).",
}
# Figuras fora de results/figures (caminho relativo a relatorio/); as outras são results/figures/<nome>.png.
CAMINHOS = {"funil": "../design/graficos/clara/funil.png"}
INCLUIR = re.compile(r"<!-- incluir: tabelas/(?P<nome>[\w]+)\.md -->")
FIGURA = re.compile(r"<!-- figura: ([\w/]+) -->")
BLOCO_FIGURAS = re.compile(r"(?:<!-- figura: [\w/]+ -->\s*)+")
NORMA = re.compile(r"Regulamento \(UE\) 2017/745|\b21 CFR \d+(?:\.\d+)?|\b(?:ISO|ASTM)\s(?:F?\d[\w.\-]*(?::\d{4})?(?:\(\d{4}\))?(?:e\d)?)"
                   r"(?:,\s(?:F\d[\w.\-]*))*")


def ler(nome: str) -> str:
    return (REL / nome).read_text(encoding="utf-8").strip()


def sem_titulo(texto: str) -> str:
    """Tira a primeira linha de título (# ...)."""
    linhas = texto.splitlines()
    return "\n".join(linhas[1:]).strip() if linhas and linhas[0].startswith("# ") else texto


def renumerar_caso(texto: str, n: int) -> str:
    """Título "# Caso k: X" passa a "# n. X"; secções ## numeradas n.1, n.2, ...; questões "### k." passam a "### Qk.".

    Em linguagem simples: põe o caso no número de secção do relatório e deixa as questões do
    enunciado identificadas como Q1 a Q11.
    """
    texto = re.sub(r"^# Caso \d+: (.+)$", lambda m: f"# {n}. {m.group(1)}", texto, count=1, flags=re.M)
    contador = iter(range(1, 100))
    texto = re.sub(r"^## (?!\d)(.+)$", lambda m: f"## {n}.{next(contador)} {m.group(1)}", texto, flags=re.M)
    return re.sub(r"^### (\d+)\. ", r"### Q\1. ", texto, flags=re.M)


class Numerador:
    """Numera figuras e tabelas pela ordem em que aparecem e guarda o número de cada figura."""

    def __init__(self) -> None:
        self.tabela = 0
        self.figuras: dict[str, int] = {}

    def nova_tabela(self) -> int:
        self.tabela += 1
        return self.tabela

    def figura(self, nome: str) -> tuple[int, bool]:
        """Número da figura e se é a primeira vez que aparece."""
        if nome in self.figuras:
            return self.figuras[nome], False
        self.figuras[nome] = len(self.figuras) + 1
        return self.figuras[nome], True


def tabela_gerada(nome: str, num: Numerador) -> str:
    """Conteúdo de relatorio/tabelas/<nome>.md, com legenda e frase de chamada quando é tabela."""
    corpo = "\n".join(l for l in ler(f"tabelas/{nome}.md").splitlines() if not l.startswith("<!--")).strip()
    chave, tipo = nome.rsplit("_", 1)
    if tipo == "robustez":
        return corpo
    if nome == "comparacao_estudos":
        num.nova_tabela()
        # oito colunas de texto: letra mais pequena no PDF (o preâmbulo põe as tabelas longas em \small; aqui o
        # \small passa a \footnotesize só dentro do grupo). O Word ignora os comandos do LaTeX.
        return ("\\begingroup\\renewcommand{\\small}{\\footnotesize}\n\n"
                + com_legenda(corpo, "Comparação com estudos publicados de seleção de materiais para implantes por "
                                     "métodos multicritério (\"não indicado\": informação não encontrada no texto lido).")
                + "\n\n\\endgroup")
    n = num.nova_tabela()
    if tipo == "criterios":
        legenda = f"Critérios, tipo, alvo, peso e justificação: {NOMES_TABELA[chave]}."
        chamada = f"Os critérios e os pesos estão na Tabela {n}."
    else:
        legenda = f"Pontuação e posição nos três métodos e consenso de Borda, cenários A e B: {NOMES_TABELA[chave]}."
        chamada = f"Os resultados estão na Tabela {n}."
    return f"{chamada}\n\n{com_legenda(corpo, legenda)}"


def com_legenda(tabela: str, legenda: str) -> str:
    """Tabela markdown com legenda do pandoc ("Table: ..."); o LaTeX numera-a e põe a legenda por cima.

    Em linguagem simples: a numeração do LaTeX segue a mesma ordem do Numerador, porque só as tabelas
    com legenda contam (as de robustez não têm). A legenda entra logo a seguir à primeira tabela do bloco,
    antes de notas que venham depois dela.
    """
    linhas = tabela.splitlines()
    inicio = next(i for i, l in enumerate(linhas) if l.startswith("|"))
    fim = next((i for i in range(inicio, len(linhas)) if not linhas[i].startswith("|")), len(linhas))
    return "\n".join(linhas[:fim] + ["", f"Table: {legenda}", ""] + linhas[fim:]).strip()


def lista_pt(nums: list[int]) -> str:
    """[1] -> "Figura 1"; [2, 3, 4] -> "Figuras 2, 3 e 4"."""
    if len(nums) == 1:
        return f"Figura {nums[0]}"
    return "Figuras " + ", ".join(map(str, nums[:-1])) + f" e {nums[-1]}"


def bloco_figuras(nomes: list[str], num: Numerador) -> str:
    """Um bloco de marcadores de figura seguidos: uma frase de chamada e as figuras novas, com legenda."""
    novas, vistas = [], []
    for nome in nomes:
        n, primeira = num.figura(nome)
        (novas if primeira else vistas).append((n, nome))
    frases = []
    if novas:
        verbo = "mostra" if len(novas) == 1 else "mostram"
        frases.append(f"A{'s' if len(novas) > 1 else ''} {lista_pt([n for n, _ in novas])} {verbo} estes resultados.")
    if vistas:
        frases.append(f"Ver também a{'s' if len(vistas) > 1 else ''} {lista_pt([n for n, _ in vistas])}.")
    out = [" ".join(frases)]
    for n, nome in novas:
        caminho = CAMINHOS.get(nome, f"{FIGURAS}/{nome}.png")
        out.append(f"![{LEGENDAS[nome]}]({caminho}){{width=100%}}")
    return "\n\n".join(out)


def substituir_marcadores(texto: str, num: Numerador) -> str:
    # "Tabela [n]" no texto refere-se à primeira tabela incluída a seguir no mesmo bloco.
    if "Tabela [n]" in texto:
        texto = texto.replace("Tabela [n]", f"Tabela {num.tabela + 1}")
    # "Tabela [n+1]": a segunda tabela do mesmo bloco (no capítulo 8, a da massa vem depois da da CFD)
    texto = texto.replace("Tabela [n+1]", f"Tabela {num.tabela + 2}")
    texto = INCLUIR.sub(lambda m: tabela_gerada(m["nome"], num), texto)
    # Figuras seguidas no mesmo bloco: uma só frase de chamada no início.
    return BLOCO_FIGURAS.sub(lambda m: bloco_figuras(FIGURA.findall(m.group(0)), num) + "\n\n", texto)


ORDEM_CAPITULOS = ("anca", "stent", "scaffold", "dentário")


def ordem_dos_capitulos(linhas: list[str]) -> list[str]:
    """Linhas da Tabela 1 pela ordem dos capítulos (anca, stent, scaffold, dentário); as outras ficam no fim."""
    def chave(l: str) -> int:
        caso = l.split("|")[1].lower()
        return next((i for i, c in enumerate(ORDEM_CAPITULOS) if c in caso), len(ORDEM_CAPITULOS))
    return sorted(linhas, key=chave)


def percentagem_inquebravel(texto: str) -> str:
    """Espaço inquebrável entre o número e o "%" (no PDF, o "%" não passa sozinho para a linha seguinte)."""
    return re.sub(r"(\d) %", "\\1\u00a0%", texto)


def tabela_resumo(num: Numerador) -> str:
    """Tabela 1: a tabela de 00_resumo_executivo.md (caso, problema, biomateriais e proposta)."""
    linhas = [l for l in ler("00_resumo_executivo.md").splitlines() if l.startswith("|")]
    linhas = linhas[:2] + ordem_dos_capitulos(linhas[2:])
    n = num.nova_tabela()
    return (f"A Tabela {n} resume, para cada caso, o problema do material atual, os biomateriais comparados e a "
            f"proposta.\n\n" + com_legenda("\n".join(linhas), "Resumo dos casos."))


def base_norma(n: str) -> str:
    """Código da norma sem a edição (ASTM F2182-19e2 -> ASTM F2182; ISO 7206-4:2010 -> ISO 7206-4)."""
    if n.startswith("ASTM"):
        return re.sub(r"-\d{2}(?:e\d)?(?:\(\d{4}\))?$", "", n)
    return re.sub(r":\d{4}$", "", n)


def normas(texto: str) -> list[str]:
    """Normas ISO e ASTM citadas, por ordem alfabética, sem repetições (listas "ASTM F1, F2" separadas).

    Quando a mesma norma aparece com e sem edição, fica só a forma com edição.
    """
    out = set()
    for m in NORMA.finditer(texto):
        partes = [p.strip().rstrip(".") for p in m.group(0).split(",")]
        org = partes[0].split()[0]
        out.add(partes[0])
        out.update(f"{org} {p}" for p in partes[1:])
    com_edicao = {base_norma(n) for n in out if base_norma(n) != n}
    final = [n for n in out if base_norma(n) != n or n not in com_edicao]
    return sorted(final, key=lambda s: (s.split()[0], [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]))


# Número de aluno e logótipos da primeira página (relatorio/logos/). Logótipo em falta: caixa com o nome.
NUMERO_ALUNO = "22403378"
LOGOS = {"LUSOFONA": ("logos/lusofona.png", "Universidade Lusófona"), "FE": ("logos/fe.png", "Faculdade de Engenharia")}
ALTURA_LOGO = "2.2cm"

YAML = """---
lang: pt-PT
documentclass: article
papersize: a4
fontsize: 11pt
geometry: margin=2cm
mainfont: "Times New Roman"
mathfont: "Cambria Math"
linestretch: 1.15
colorlinks: true
header-includes: |
  ```{{=latex}}
{preambulo}
  ```
---
"""


YAML_WORD = "---\nlang: pt-PT\n---\n"


def logo(chave: str, word: bool = False) -> str:
    """Imagem do logótipo (markdown) ou, se o ficheiro não existir, uma caixa (no Word, um texto) com o nome."""
    caminho, nome = LOGOS[chave]
    if (REL / caminho).exists():
        return f"![]({caminho}){{height={ALTURA_LOGO}}}"
    if word:
        return f"[Logótipo: {nome}]"
    return (f"`\\fbox{{\\parbox[c][{ALTURA_LOGO}][c]{{4cm}}{{\\centering\\small Logótipo:\\\\ {nome}}}}}`"
            "{=latex}")


def primeira_pagina(resumo: str, abstract: str, word: bool = False) -> str:
    """Primeira página (logótipos, unidade curricular, título, autor e resumo), abstract e índice.

    No Word usa o modelo primeira_pagina_word.md (estilos do Word em vez de comandos LaTeX).
    """
    t = ler("formato/primeira_pagina_word.md" if word else "formato/primeira_pagina.md")
    for marca, valor in (("@@LOGO_LUSOFONA@@", logo("LUSOFONA", word)), ("@@LOGO_FE@@", logo("FE", word)),
                         ("@@NUMERO@@", NUMERO_ALUNO), ("@@RESUMO@@", resumo), ("@@ABSTRACT@@", abstract)):
        t = t.replace(marca, valor)
    return t


def titulos_com_ponto(texto: str) -> str:
    """"## 4.2 Resultados" passa a "## 4.2. Resultados" (os de nível 1 já têm ponto: "# 4. Anca")."""
    return re.sub(r"^(#{2,3}) (\d+(?:\.\d+)+) ", r"\1 \2. ", texto, flags=re.M)


def ordem_alfabetica(texto: str) -> str:
    """Chave de ordenação de uma referência: o texto sem acentos, sem formatação e em minúsculas (Ahlström = Ahlstrom)."""
    import unicodedata
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return "".join(c for c in t if c.isalnum() or c.isspace()).lower().strip()


def lista_referencias(refs: dict[str, str], citadas: list[str], word: bool = False) -> str:
    """Referências citadas por ordem alfabética do texto (apelido do 1.º autor), com indentação suspensa.

    No PDF, a indentação vem de um comando LaTeX em cada entrada; no Word, do estilo "Referencia".
    """
    chaves = sorted((k for k in refs if k in citadas), key=lambda k: ordem_alfabetica(refs[k]))
    if word:
        return '::: {custom-style="Referencia"}\n' + "\n\n".join(refs[k] for k in chaves) + "\n:::"
    recuo = "`\\hangindent=1cm\\hangafter=1`{=latex}"
    return "\n\n".join(f"{recuo}{refs[k]}" for k in chaves)


def legenda_word(rotulo: str, n: int | str, texto: str) -> str:
    """Parágrafo de legenda para o Word: "Tabela n." a negrito e o texto em itálico, no estilo "Legenda"."""
    return f'::: {{custom-style="Legenda"}}\n**{rotulo} {n}.** *{texto}*\n:::'


LEGENDA_ANEXO = re.compile(r"^\*\*Tabela (?P<letra>[A-Z])\.(?P<n>\d+)\.\*\* (?P<texto>.+)$", re.M)
# No PDF, as tabelas de um anexo recomeçam a numeração com a letra do anexo (Tabela B.1, B.2, ...).
NUMERACAO_ANEXO = ("```{{=latex}}\n\\setcounter{{table}}{{0}}\\renewcommand{{\\thetable}}{{{letra}.\\arabic{{table}}}}"
                   "\\renewcommand{{\\theHtable}}{{{letra}.\\arabic{{table}}}}\n```")


def legendas_do_anexo(texto: str, word: bool = False) -> str:
    """Legenda manual "**Tabela B.1.** texto" de um anexo passa ao estilo das outras legendas.

    Em linguagem simples: no PDF vira uma legenda do pandoc ("Table: texto"), numerada pelo LaTeX como B.1;
    no Word vira o parágrafo de legenda (estilo "Legenda"), por cima da tabela, com o mesmo número.
    """
    m = LEGENDA_ANEXO.search(texto)
    if not m:
        return texto
    if word:
        return texto[:m.start()] + legenda_word("Tabela", f"{m['letra']}.{m['n']}", m["texto"]) + texto[m.end():]
    antes, depois = texto[:m.start()], texto[m.end():].lstrip("\n")
    return antes + NUMERACAO_ANEXO.format(letra=m["letra"]) + "\n\n" + com_legenda(depois, m["texto"])


def para_word(texto: str) -> str:
    """Passa as legendas do formato do PDF para o do Word, com o mesmo número.

    Em linguagem simples: no PDF o LaTeX numera e põe as legendas por cima; o Word não o faz com o pandoc,
    por isso aqui cada "Table: legenda" vira um parágrafo "Tabela n. legenda" antes da tabela e cada figura
    "![legenda](...)" fica com o parágrafo "Figura n. legenda" por cima e a imagem sem legenda. A ordem é a
    mesma do LaTeX, por isso os números coincidem com os do texto.
    """
    linhas = texto.split("\n")
    out: list[str] = []
    n_tab = 0
    for linha in linhas:
        if linha.startswith("Table: "):
            n_tab += 1
            while out and out[-1] == "":
                out.pop()
            inicio = len(out)
            while inicio > 0 and out[inicio - 1].startswith("|"):
                inicio -= 1
            out[inicio:inicio] = [legenda_word("Tabela", n_tab, linha[len("Table: "):]), ""]
            out.append("")
            continue
        out.append(linha)
    n_fig = iter(range(1, 1000))
    texto = "\n".join(out)
    return re.sub(r"^!\[([^\]]+)\]\(([^)]+)\)(\{[^}]*\})?$",
                  lambda m: f"{legenda_word('Figura', next(n_fig), m[1])}\n\n![]({m[2]}){m[3] or ''}",
                  texto, flags=re.M)


def contagem_verificados(materiais: Path = RAIZ / "data" / "materiais.csv") -> tuple[int, int]:
    """(valores verificados, total de valores) da base: conta como verificado todo o estado "Verificado..."."""
    with open(materiais, encoding="utf-8", newline="") as f:
        estados = [linha["estado"] for linha in csv.DictReader(f)]
    return sum(e.startswith("Verificado") for e in estados), len(estados)


def substituir_numeros_da_base(texto: str, materiais: Path = RAIZ / "data" / "materiais.csv") -> str:
    """Troca @@N_VERIFICADOS@@ e @@N_TOTAL@@ pelos números atuais da base (data/materiais.csv).

    Em linguagem simples: o número de valores verificados nunca fica escrito à mão no texto; vem sempre
    da base no momento da montagem.
    """
    n, total = contagem_verificados(materiais)
    return texto.replace("@@N_VERIFICADOS@@", str(n)).replace("@@N_TOTAL@@", str(total))


LINHA_PASSO_PENDENTE = "- passo de tempo: a verificação com o dobro dos passos por ciclo está a ser calculada e entra na versão final;"


def substituir_passo_cfd(texto: str, verificacoes: Path = RAIZ / "results" / "cfd_verificacoes.json") -> str:
    """Troca @@CFD_PASSO@@ pela variação da área com corte baixo entre 1000 e 2000 passos por ciclo.

    Em linguagem simples: a verificação do passo de tempo da CFD acaba depois das outras; enquanto não houver
    resultado em results/cfd_verificacoes.json, a linha da lista diz que está a ser calculada (sem número)."""
    if "@@CFD_PASSO@@" not in texto:
        return texto
    v = json.loads(verificacoes.read_text(encoding="utf-8")) if verificacoes.exists() else {}
    if "passo_variacao_area" in v:
        return texto.replace("@@CFD_PASSO@@", f"{100 * v['passo_variacao_area']:.2f}".replace(".", ","))
    linhas = [LINHA_PASSO_PENDENTE if "@@CFD_PASSO@@" in linha else linha for linha in texto.split("\n")]
    return "\n".join(linhas)


def montar(word: bool = False) -> str:
    num = Numerador()
    resumo = sem_titulo(ler("resumo_rascunho.md"))
    abstract = sem_titulo(ler("abstract_rascunho.md"))
    corpo = [ler("introducao_rascunho.md") + "\n\n" + tabela_resumo(num),
             ler("metodos_rascunho.md"), ler("validacao_rascunho.md")]
    corpo += [renumerar_caso(ler(f), n) for f, n in CASOS]
    corpo.append(ler("extensoes_rascunho.md"))
    disc = ler("discussao_rascunho.md")
    disc = disc.replace("\n## 9.2", "\n\n<!-- figura: fig_e_resumo -->\n\n## 9.2", 1)
    corpo += [disc, ler("conclusao_rascunho.md")]
    partes_corpo = []
    for c in corpo:
        partes_corpo.append(substituir_marcadores(c, num))
        if c.startswith("# 8. Extensões"):
            # tabelas escritas à mão no rascunho (legenda "Table: ..."): contam para a numeração das seguintes
            num.tabela += sum(1 for l in c.splitlines() if l.startswith("Table: "))
    texto = "\n\n".join(partes_corpo)
    anexo_a = ler("anexo_a_equacoes.md")
    fim = "\n\n".join([anexo_a, ler("anexo_c_rubricas.md"), ler("glossario.md")])
    refs = vr.ler_referencias()
    citado, citadas = vr.citar_apa(texto + "\n\n" + fim, refs)
    texto, fim = citado.split("\n\n# Anexo A", 1)
    fim = "# Anexo A" + fim
    lista_normas = "\n".join(f"- {n}" for n in normas(texto + fim))
    # Anexo B no relatório: só a contagem por estado; a tabela completa fica em tabelas/anexo_b_dados.md e no .xlsx.
    anexo_b = "\n".join(l for l in ler("tabelas/anexo_b_resumo.md").splitlines() if not l.startswith("<!--"))
    anexo_b = legendas_do_anexo(anexo_b, word)
    anexo_a, resto = fim.split("\n\n# Glossário", 1)
    # Anexo C (rubricas das escalas ordinais) sai depois do anexo B; as citações já foram tratadas com o resto.
    anexo_a, anexo_c = anexo_a.split("\n\n# Anexo C", 1)
    anexo_c = "# Anexo C" + anexo_c
    preambulo = "\n".join("  " + l for l in ler("formato/preambulo.tex").splitlines())
    partes = [YAML_WORD if word else YAML.format(preambulo=preambulo), primeira_pagina(resumo, abstract, word),
              titulos_com_ponto(texto), "# Referências\n\n" + lista_referencias(refs, citadas, word),
              "# Normas e legislação citadas\n\n" + lista_normas, titulos_com_ponto(anexo_a), anexo_b, anexo_c,
              "# Glossário" + resto]
    final = substituir_passo_cfd(substituir_numeros_da_base("\n\n".join(partes) + "\n"))
    return para_word(final) if word else percentagem_inquebravel(final)


def main() -> None:
    for nome, word in (("RELATORIO.md", False), ("RELATORIO_word.md", True)):
        destino = REL / nome
        destino.write_text(montar(word), encoding="utf-8")
        print(destino)


if __name__ == "__main__":
    main()
