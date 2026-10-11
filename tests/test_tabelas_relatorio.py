"""Testes de scripts/tabelas_relatorio.py (o script carrega-se pelo caminho)."""
import importlib.util
from pathlib import Path

import pandas as pd
import pytest

CAMINHO = Path(__file__).resolve().parents[1] / "scripts" / "tabelas_relatorio.py"
spec = importlib.util.spec_from_file_location("tabelas_relatorio", CAMINHO)
tr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tr)


def test_tabela_criterios_tem_todos_os_criterios_do_caso():
    crit = pd.read_csv(tr.DATA / "criterios.csv")
    for caso, _, _ in tr.CASOS.values():
        t = tr.tabela_criterios(caso)
        assert len(t) == (crit["caso_componente"] == caso).sum()
        assert set(t["Tipo"]) <= set(tr.TIPOS.values())
    t = tr.tabela_criterios("Prótese da anca | Haste femoral")
    assert t.loc[t["Critério"] == "Módulo de Young", "Alvo"].item() == "17 GPa"
    assert t.loc[t["Critério"] == "Módulo de Young", "Peso"].item() == "0,20"


def test_resultados_quantitativos_batem_com_results(tmp_path):
    pt = tr.pontuacoes("stent")
    assert set(pt["cenario"]) == {"A", "B"}
    assert tr.delta_c(pt, "A") == pytest.approx(0.022, abs=5e-4)
    assert "empate" in tr.frase_delta(pt)  # cenário B: ΔC = 0,002
    t = tr.tabela_resultados(pt)
    assert len(t) == len(pt) and t.iloc[0]["Pos. T"] == 1


def test_semiquantitativo_calcula_pontuacoes():
    pt = tr.pontuacoes("dentario")
    a = pt[pt["cenario"] == "A"].sort_values("pos_TOPSIS")
    assert a.iloc[0]["material"] == "Ti cp grau 4"


def test_contagem_converte_percentagem_em_iteracoes():
    assert tr.contagem(99.99, 10_000) == "9 999"
    assert tr.contagem(100.0, 10_000) == "10 000"
    assert tr.contagem(50.0, 200) == "100"


def test_pct_nao_arredonda_para_100_nem_para_0():
    assert tr.pct(99.99) == "99,99 %"
    assert tr.pct(100.0) == "100,0 %"
    assert tr.pct(0.01) == "0,01 %"
    assert tr.pct(56.64) == "56,6 %"


def test_gama_eta_compacta():
    eta = pd.DataFrame({"variante": ["η = 0,0", "η = 0,1", "η = 0,2", "η = 0,3"],
                        "material": ["X", "X", "Y", "Y"], "posicao": [1, 1, 1, 1]})
    assert tr.gama_eta(eta, "Y") == "η de 0 a 0,1"
    assert tr.gama_eta(eta, "X") == "η = 0,2, η = 0,3"
    assert tr.gama_eta(eta[eta["material"] == "Y"], "Y") == "nunca"


def test_nota_pesos_so_quando_nao_somam_1():
    assert "0,85" in tr.nota_pesos("Stent vascular")
    assert tr.nota_pesos("Prótese da anca | Haste femoral") == ""


def test_gerar_escreve_quatro_ficheiros_por_caso(tmp_path):
    feitos = tr.gerar(tmp_path)
    # critérios, resultados, robustez e propriedades por caso; retirar, dimensões e ajuste mínimo nos 3 quantitativos;
    # mais os dois anexos B, a comparação com estudos e o Spearman
    assert len(feitos) == 4 * len(tr.CASOS) + 3 * 3 + 4
    for nome in ("haste_retirar", "stent_dimensoes", "scaffold_ajuste_minimo"):
        assert (tmp_path / f"{nome}.md").read_text(encoding="utf-8").startswith("<!-- gerado")
    texto = (tmp_path / "par_resultados.md").read_text(encoding="utf-8")
    assert "Semiquantitativo" in texto and texto.startswith("<!-- gerado")


def test_anexo_b_tem_todas_as_linhas_da_base():
    m = pd.read_csv(tr.DATA / "materiais.csv")
    total = sum(len(tr.tabela_dados(c)) for c in m["caso"].drop_duplicates())
    assert total == len(m)
    t = tr.tabela_dados("Stent vascular")
    l605 = t[(t["Material"] == "Co-Cr L605") & (t["Propriedade"] == "Módulo de Young")].iloc[0]
    assert l605["Valor"] == "225" and l605["Estado"] == "Verificado (fornecedor)"
    assert "Contagem por estado" in tr.anexo_b()


def test_anexo_b_resumo_conta_por_caso_e_no_total():
    m = pd.read_csv(tr.DATA / "materiais.csv")
    t = tr.contagem_estados()
    assert t.loc["Total", "Total"] == len(m)
    assert t.loc["Stent vascular", "Total"] == (m["caso"] == "Stent vascular").sum()
    texto = tr.anexo_b_resumo()
    assert "anexo digital (base_dados_biomateriais.xlsx); a Tabela B.1" in texto and f"{len(m)} linhas" in texto


def test_larguras_cobrem_a_palavra_mais_comprida():
    df = pd.DataFrame({"Material": ["Hidroxiapatite", "PCL"], "C": ["0,436", "0,511"]})
    w = tr.larguras(df)
    assert w[0] >= len("Hidroxiapatite") and w[1] >= 5
    assert tr.md(df).splitlines()[1] == "|" + "-" * w[0] + "|" + "-" * w[1] + "|"


def test_justificacao_do_relatorio_sem_marcas_da_base():
    assert tr.justificacao_relatorio("SEMIQUANTITATIVO (ordinais > 50 %). Osso ~10-20 GPa") == "Osso ~10-20 GPa"
    j = tr.justificacao_relatorio("Osso trabecular ~2-12 MPa: CENÁRIO de referência, ver folha Cenarios")
    assert j.endswith("valor de referência, testado nos cenários T (secção 6.4)") and "Cenarios" not in j


def test_linha_monte_carlo_percentagens_e_contagem():
    mc = pd.DataFrame({"material": ["A", "B", "C"] * 3, "metodo": [m for m in tr.METODOS for _ in range(3)],
                       "pct_primeiro": [70, 29.5, 0.5, 60, 40, 0, 100, 0, 0], "n_iter": 10000})
    linha = tr.linha_monte_carlo(mc, "Monte Carlo X")
    assert linha.startswith("- Monte Carlo X (10 000 iterações")
    assert "A 70,0 % / 60,0 % / 100,0 %" in linha and "C" not in linha.split(":", 1)[1]  # C fica abaixo de 1 %
    sempre = mc.assign(pct_primeiro=[100, 0, 0, 100, 0, 0, 99.99, 0.01, 0])
    assert "A 10 000 / 10 000 / 9 999 das 10 000" in tr.linha_monte_carlo(sempre, "Y")


def test_linhas_cenarios_junta_variantes_com_os_mesmos_vencedores():
    linhas = []
    for var, venc in (("alvo 14", "X"), ("alvo 20", "X"), ("alvo 2", "Y")):
        for m in tr.METODOS:
            linhas += [{"cenario": "T-haste", "variante": var, "metodo": m, "material": venc, "posicao": 1},
                       {"cenario": "T-haste", "variante": var, "metodo": m, "material": "Z", "posicao": 2}]
    for m in tr.METODOS:
        linhas.append({"cenario": "Q", "variante": "sem ordinais", "metodo": m, "material": "X", "posicao": 1})
    out = tr.linhas_cenarios(pd.DataFrame(linhas))
    assert out[0] == "- Sem critérios ordinais (Q): TOPSIS X; WASPAS X; VIKOR X."
    assert out[1] == "- Valores-alvo (T), alvo 14; alvo 20: TOPSIS X; WASPAS X; VIKOR X."
    assert out[2].startswith("- Valores-alvo (T), alvo 2: TOPSIS Y")


def test_robustez_do_stent_inclui_monte_carlo_dos_pesos():
    linhas = tr.robustez_linhas("stent")
    pesos = next(l for l in linhas if "pesos, ±20 %" in l)
    assert "Pt-Cr 83,2 %" in pesos
    assert any(l.startswith("- Sem critérios ordinais (Q)") for l in linhas)
    assert any("R-sentinela" in l for l in linhas)


def test_tabela_spearman_tres_casos_tres_cenarios():
    t = tr.tabela_spearman()
    assert len(t) == 9 and list(t["Caso"].unique()) == ["Haste", "Stent", "Scaffold"]
    haste_a = t[(t["Caso"] == "Haste") & (t["Cenário"] == "A")].iloc[0]
    assert haste_a["TOPSIS / WASPAS"] == "0,30" and haste_a["TOPSIS / VIKOR"] == "0,90"


def test_tabela_propriedades_e_a_matriz_dos_metodos():
    t = tr.tabela_propriedades("haste")
    p = tr.build_problem("Prótese da anca | Haste femoral", "B")
    assert list(t["Propriedade"].str.split(" (", regex=False).str[0]) == [c.split(" (")[0] for c in p.criteria]
    assert list(t.columns[1:]) == p.alternatives
    modulo = t[t["Propriedade"] == "Módulo de Young (GPa)"].iloc[0]
    assert modulo["Ti-6Al-4V ELI"] == "105,5"  # verificado: sem asterisco
    assert t[t["Propriedade"].str.startswith("Densidade")].iloc[0]["Ti-6Al-4V ELI"].endswith("*")


def test_valores_de_modelacao_levam_cruz_e_nao_asterisco():
    stent = tr.tabela_propriedades("stent")
    reab = stent[stent["Propriedade"].str.startswith("Tempo de reabsorção")].iloc[0]
    for liga in ("Aço inox 316L", "Co-Cr L605", "Co-Ni-Cr-Mo MP35N", "Pt-Cr"):
        assert reab[liga].endswith("†") and "*" not in reab[liga]
    scaf = tr.tabela_propriedades("scaffold")
    deg = scaf[scaf["Propriedade"].str.startswith("Tempo de degradação")].iloc[0]
    assert deg["Hidroxiapatite (HA) porosa"].endswith("†")


def test_nota_propriedades_acrescenta_a_nota_do_caso():
    assert tr.nota_propriedades("haste").startswith(tr.NOTA_PROPRIEDADES)
    assert "R = 0,1" in tr.nota_propriedades("haste")
    assert "48 meses" in tr.nota_propriedades("stent")
    assert tr.nota_propriedades("dentario") == tr.NOTA_PROPRIEDADES


def test_ler_robustez_extra_so_do_caso_e_cenario():
    t = tr.ler_robustez_extra("Stent", "A")
    assert set(t) == {"retirar", "dimensoes", "pesos", "valores"}
    assert set(t["retirar"]["retirado"]) == {"Aço inox 316L", "Co-Cr L605", "Co-Ni-Cr-Mo MP35N", "Pt-Cr"}
    assert (t["valores"]["cenario"] == "A").all()


def test_textos_da_robustez_complementar():
    r = tr.texto_retirar("Stent")
    assert "Pt-Cr ↔ Co-Cr L605" in r and "Cenário A" in r
    d = tr.texto_dimensoes("Haste")
    assert "mecânica 0,60" in d and "10 000 repartições" in d
    a = tr.texto_ajuste("Scaffold")
    tabela = [l for l in a.splitlines() if l.startswith("| ") and not l.startswith(("| Material |", "| Critério | Peso |"))]
    assert len(tabela) <= tr.N_VALORES_AJUSTE + tr.N_PESOS_AJUSTE
    assert "ΔC < 0,01" in a
    for texto in (r, d, a):
        assert "—" not in texto and "–" not in texto
