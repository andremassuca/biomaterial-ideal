"""Testes de scripts/montar_relatorio.py (o script carrega-se pelo caminho)."""
import importlib.util
import re
from pathlib import Path

CAMINHO = Path(__file__).resolve().parents[1] / "scripts" / "montar_relatorio.py"
spec = importlib.util.spec_from_file_location("montar_relatorio", CAMINHO)
mr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mr)


def test_renumerar_caso():
    t = "# Caso 3: Stent\n\n## Problema\n\ntexto\n\n## Resultados\n\n### 1. Função do dispositivo\n"
    r = mr.renumerar_caso(t, 5)
    assert r.startswith("# 5. Stent")
    assert "## 5.1 Problema" in r and "## 5.2 Resultados" in r and "### Q1. Função do dispositivo" in r


def test_normas_alfabeticas_e_sem_duplicados():
    t = "ASTM F2182 e ASTM F2182-19e2; ISO 7206-4:2010; ASTM F2052-21, F2213-25; ISO 14801."
    assert mr.normas(t) == ["ASTM F2052-21", "ASTM F2182-19e2", "ASTM F2213-25", "ISO 7206-4:2010", "ISO 14801"]


def test_bloco_de_figuras_numera_uma_vez_e_remete_depois():
    num = mr.Numerador()
    a = mr.bloco_figuras(["fig_b_posicoes", "fig_c_monte_carlo"], num)
    assert a.startswith("As Figuras 1 e 2 mostram") and a.count("![") == 2
    assert f"![{mr.LEGENDAS['fig_c_monte_carlo']}]" in a
    b = mr.bloco_figuras(["fig_c_monte_carlo"], num)
    assert b == "Ver também a Figura 2."


def test_legenda_logo_a_seguir_a_tabela_e_antes_da_nota():
    t = mr.com_legenda("| a | b |\n|---|---|\n| 1 | 2 |\n\nNota: escala ordinal.", "Resultados.")
    assert t == "| a | b |\n|---|---|\n| 1 | 2 |\n\nTable: Resultados.\n\n\nNota: escala ordinal."


def test_titulos_com_ponto():
    t = "# 4. Anca\n\n## 4.2 Resultados\n\n### Q1. Função\n\nver secção 8.8 e 2.4 abaixo"
    assert mr.titulos_com_ponto(t) == "# 4. Anca\n\n## 4.2. Resultados\n\n### Q1. Função\n\nver secção 8.8 e 2.4 abaixo"


def test_primeira_pagina_tem_titulo_autor_resumo_e_abstract():
    p = mr.primeira_pagina("RESUMO", "ABSTRACT")
    assert "Qual é o biomaterial ideal? Seleção multicritério" in p and "André Oliveira Massuça" in p
    assert "Unidade Curricular: Próteses e Órgãos Artificiais" in p
    assert p.index("RESUMO") < p.index("ABSTRACT") < p.index("tableofcontents")
    assert "@@" not in p


def test_logo_em_falta_da_uma_caixa(monkeypatch):
    monkeypatch.setitem(mr.LOGOS, "FE", ("logos/nao_existe.png", "Faculdade de Engenharia"))
    assert "fbox" in mr.logo("FE") and "Faculdade de Engenharia" in mr.logo("FE")


def test_relatorio_montado_sem_marcadores_e_com_referencias_apa():
    texto = mr.montar()
    assert "<!--" not in texto
    corpo, resto = texto.split("\n# Referências\n", 1)
    lista = resto.split("\n# Normas e legislação citadas")[0]
    entradas = re.findall(r"^`\\hangindent", lista, flags=re.M)
    assert len(entradas) == len(mr.vr.ler_referencias())  # todas citadas, nenhuma a mais
    assert not re.search(r"\[\d+\]", corpo)  # já não há citações numeradas
    for sec in ("# 1. Introdução", "# 4. Prótese total da anca", "# 7. Implante dentário", "# 8. Extensões exploratórias",
                "# 9. Discussão", "# 10. Conclusões",
                "# Anexo A.", "# Anexo B.", "# Anexo C.", "# Glossário", "# Resumo", "# Abstract"):
        assert sec in texto
    assert texto.index("# Anexo B.") < texto.index("# Anexo C.") < texto.index("\n# Glossário")
    figs = re.findall(r"!\[[^\]]+\]\(\.\./(?:results/figures|design/graficos/clara)/([\w/]+)\.png", texto)
    assert len(figs) == len(set(figs)) == len(mr.LEGENDAS)
    n_tabelas = corpo.count("\nTable: ")
    assert max(int(n) for n in re.findall(r"Tabela (\d+)", corpo)) == n_tabelas


def test_relatorio_sem_travessoes():
    texto = mr.montar()
    assert chr(0x2014) not in texto and chr(0x2013) not in texto  # travessão e meia-risca


def test_citacoes_no_formato_apa():
    texto = mr.montar()
    corpo = texto.split("\n# Referências\n", 1)[0]
    refs = mr.vr.ler_referencias()
    fora = []
    for m in mr.vr.CITACAO.finditer(corpo):
        k = f"{m['nome']} {mr.vr._ano(m)}"
        if k in refs:
            nome, ano = mr.vr.rotulo(refs[k]), mr.vr._ano(m)
            if m.group(0) not in (f"{nome}, {ano}", f"{nome} ({ano})"):
                fora.append(m.group(0))
    assert fora == []


def test_para_word_legendas_por_cima_com_o_mesmo_numero():
    t = ("texto\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\nTable: Primeira.\n\nNota.\n\n"
         "![Uma figura.](../results/figures/x.png){width=100%}\n\n| c |\n|---|\n| 3 |\n\nTable: Segunda.")
    w = mr.para_word(t)
    assert "Table:" not in w
    assert w.index("**Tabela 1.** *Primeira.*") < w.index("| a | b |") < w.index("Nota.")
    assert w.index("**Figura 1.** *Uma figura.*") < w.index("![](../results/figures/x.png){width=100%}")
    assert w.index("**Tabela 2.** *Segunda.*") < w.index("| c |")


def test_variante_word_sem_latex_e_com_estilos():
    w = mr.montar(word=True)
    assert "{=latex}" not in w and "Table: " not in w
    assert 'custom-style="Referencia"' in w and r"TOC \o" in w
    assert len(re.findall(r"\*\*Figura \d+\.\*\*", w)) == len(mr.LEGENDAS)
    pdf = mr.montar()
    assert len(re.findall(r"\*\*Tabela \d+\.\*\*", w)) == pdf.split("\n# Referências\n")[0].count("\nTable: ")
    assert "**Tabela B.1.** *Número de valores" in w


def test_legenda_do_anexo_no_pdf_e_no_word():
    t = "Texto.\n\n**Tabela B.1.** Contagem.\n\n| a |\n|---|\n| 1 |"
    pdf = mr.legendas_do_anexo(t)
    assert "**Tabela B.1.**" not in pdf and r"{B.\arabic{table}}" in pdf
    assert pdf.index("| 1 |") < pdf.index("Table: Contagem.")
    word = mr.legendas_do_anexo(t, word=True)
    assert "**Tabela B.1.** *Contagem.*" in word and 'custom-style="Legenda"' in word
    assert word.index("Legenda") < word.index("| a |")
    assert mr.legendas_do_anexo("sem legenda") == "sem legenda"


def test_substituir_numeros_da_base(tmp_path):
    csv = tmp_path / "m.csv"
    csv.write_text("caso,estado\nA,Verificado\nA,A verificar\nB,Verificado (fornecedor)\n", encoding="utf-8")
    assert mr.contagem_verificados(csv) == (2, 3)
    assert mr.substituir_numeros_da_base("@@N_VERIFICADOS@@ dos @@N_TOTAL@@", csv) == "2 dos 3"


def test_numero_de_verificados_no_texto_bate_com_a_base():
    import pandas as pd
    estados = pd.read_csv(mr.RAIZ / "data" / "materiais.csv")["estado"]
    n, total = int(estados.str.startswith("Verificado").sum()), len(estados)
    for word in (False, True):
        texto = mr.montar(word)
        assert "@@" not in texto
        assert f"{n} das {total} linhas da base estão verificadas" in texto
        assert f"{n} dos {total} valores verificados em fontes primárias" in texto
        # nenhum outro "x das/dos y linhas/valores" escrito à mão com números diferentes dos da base
        for a, b in re.findall(r"\b(\d+) d[ao]s (\d+) (?:linhas|valores)\b", texto):
            assert (int(a), int(b)) == (n, total)


def test_logo_em_falta_no_word_e_texto(monkeypatch):
    monkeypatch.setitem(mr.LOGOS, "FE", ("logos/nao_existe.png", "Faculdade de Engenharia"))
    assert mr.logo("FE", word=True) == "[Logótipo: Faculdade de Engenharia]"


def test_substituir_passo_cfd_com_e_sem_resultado(tmp_path):
    texto = "- passo de tempo: muda @@CFD_PASSO@@ pontos percentuais;\n- outra linha"
    sem = mr.substituir_passo_cfd(texto, tmp_path / "nao_existe.json")
    assert "@@" not in sem and sem.splitlines()[0] == mr.LINHA_PASSO_PENDENTE and sem.endswith("outra linha")
    f = tmp_path / "v.json"
    f.write_text('{"passo_variacao_area": 0.0123}', encoding="utf-8")
    assert mr.substituir_passo_cfd(texto, f).startswith("- passo de tempo: muda 1,23 pontos percentuais")


def test_referencias_por_ordem_alfabetica_sem_acentos():
    refs = {"b": "Ahlström H. Título.", "a": "Jain A. Título.", "c": "*Gruen* TA. Título.", "d": "Zeta Z. Não citada."}
    texto = mr.lista_referencias(refs, ["a", "b", "c"], word=True)
    assert texto.index("Ahlström") < texto.index("Gruen") < texto.index("Jain") and "Zeta" not in texto


def test_normas_incluem_o_codigo_federal_dos_eua():
    assert "21 CFR 872.3640" in mr.normas("Nos EUA (21 CFR 872.3640) e na ISO 14801.")


def test_tabela_1_pela_ordem_dos_capitulos():
    linhas = ["| **Prótese da anca** | a |", "| **Implante dentário** | b |", "| **Stent vascular** | c |",
              "| **Scaffold ósseo** | d |"]
    assert [l.split("|")[2].strip() for l in mr.ordem_dos_capitulos(linhas)] == ["a", "c", "d", "b"]


def test_percentagem_inquebravel():
    assert mr.percentagem_inquebravel("46,3 % e 82 %; 100%") == "46,3 % e 82 %; 100%"


def test_linha_em_branco_antes_das_listas():
    t = "Texto:\n- um\n- dois\n\nOutro:\n1. a\n2. b\n| x |\n|---|\n```\nc:\n- d\n```"
    r = mr.linha_em_branco_antes_das_listas(t)
    assert "Texto:\n\n- um\n- dois" in r and "Outro:\n\n1. a\n2. b" in r
    assert "c:\n- d" in r  # dentro de um bloco de código fica igual
    assert mr.linha_em_branco_antes_das_listas(r) == r


def test_relatorio_montado_tem_listas_separadas_do_paragrafo():
    texto = mr.montar()
    corpo = texto.split("\n---\n", 2)[-1]
    linhas = corpo.split("\n")
    em_codigo = False
    for i, l in enumerate(linhas[1:], 1):
        if l.lstrip().startswith("```"):
            em_codigo = not em_codigo
        if not em_codigo and mr.ITEM_LISTA.match(l) and not l.startswith(" "):
            ant = linhas[i - 1]
            assert not ant.strip() or mr.ITEM_LISTA.match(ant) or ant.startswith((" ", "|")), (ant, l)


def test_numero_das_tabelas_no_texto_bate_com_a_ordem_das_legendas():
    """Cada "Tabela n" de uma frase de chamada refere-se à legenda que vem a seguir, que é a n-ésima do corpo."""
    texto = mr.montar().split("# Referências", 1)[0]
    for m in re.finditer(r"(?:A Tabela|estão na Tabela) (\d+)", texto):
        antes = texto[:m.start()].count("\nTable: ")
        assert antes + 1 == int(m.group(1)), m.group(0)


def test_largura_figura_estreita_as_figuras_3_e_4():
    assert mr.largura_figura("fig_c_monte_carlo") == "70%"
    assert mr.largura_figura("fig_d_vencedor_eta") == "75%"
    assert mr.largura_figura("fig_b_posicoes") == "100%"
