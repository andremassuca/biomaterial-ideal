import importlib.util
import os
import sys
import time
from pathlib import Path

import pandas as pd
import pytest

CAMINHO = Path(__file__).resolve().parents[1] / "scripts" / "auditoria_relatorio.py"
spec = importlib.util.spec_from_file_location("auditoria_relatorio", CAMINHO)
ar = importlib.util.module_from_spec(spec)
sys.modules["auditoria_relatorio"] = ar
spec.loader.exec_module(ar)


def _pts():
    """Pontuações de brincar: um caso com dois cenários e três materiais, coerentes."""
    linhas = []
    for cen in ("A", "B"):
        for mat, c, q, p, pos in (("Ti-6Al-4V ELI", 0.8, 0.9, 0.0, 1), ("Aço inox 316L", 0.5, 0.6, 0.5, 2),
                                  ("Ti cp grau 4", 0.2, 0.3, 1.0, 3)):
            linhas.append({"material": mat, "C_TOPSIS": c, "Q_WASPAS": q, "P_VIKOR": p, "pos_TOPSIS": pos,
                           "pos_WASPAS": pos, "pos_VIKOR": pos, "pontos_Borda": 3 * (3 - pos), "pos_Borda": pos,
                           "caso": "Haste", "cenario": cen})
    return pd.DataFrame(linhas)


def _mc():
    linhas = []
    for analise in ("MC propriedades", "W pesos ±20 %"):
        for metodo in ar.METODOS:
            for mat, p1, p2, p3 in (("Ti-6Al-4V ELI", 99.99, 0.01, 0.0), ("Aço inox 316L", 0.01, 60.0, 39.99),
                                    ("Ti cp grau 4", 0.0, 39.99, 60.01)):
                linhas.append({"caso": "Haste", "analise": analise, "metodo": metodo, "material": mat,
                               "pct_primeiro": p1, "pct_segundo": p2, "pct_terceiro": p3, "n_iter": 10000,
                               "seed": 42})
    return pd.DataFrame(linhas)


def _semi():
    return pd.DataFrame([{"caso": "Implante dentário", "cenario": "A", "variante": "A", "metodo": m,
                          "material": mat, "posicao": pos}
                         for m in ar.METODOS for mat, pos in (("Ti cp grau 4", 1), ("Zircónia Y-TZP", 2))])


def test_ler_numero_e_casas_decimais():
    assert ar.ler_numero("9 999") == 9999 and ar.ler_numero("66,9") == 66.9
    assert ar.ler_numero("9,999", ingles=True) == 9999 and ar.ler_numero("66.9", ingles=True) == 66.9
    assert ar.casas_decimais("66,9") == 1 and ar.casas_decimais("100") == 0
    assert ar.mil(10000) == "10 000"


def test_caso_e_material_no_texto():
    assert ar.caso_no_texto("No stent, blá; no scaffold, o") == "Scaffold"
    assert ar.caso_no_texto("sem dispositivo") is None
    mats = ["β-TCP poroso", "Compósito PCL/β-TCP (impressão 3D)"]
    achados = ar.materiais_no_texto("o compósito PCL/β-TCP impresso e o β-TCP", mats)
    assert [m for _, m in achados] == ["Compósito PCL/β-TCP (impressão 3D)", "β-TCP poroso"]
    assert ar.material_antes("o Pt-Cr e o L605", ["Pt-Cr", "Co-Cr L605"]) == "Co-Cr L605"


def test_frase_e_oracao():
    linha = "Primeira frase com 1.º lugar. Segunda, com 66,9 %; terceira."
    assert ar.frase_em(linha, linha.index("66,9")) == "Segunda, com 66,9 %;"
    assert ar.oracao_seguinte("x ficou com os três métodos, mas o VIKOR", 0) == "x ficou com os três métodos"


def test_contagens_e_lider_mc():
    mc = _mc()
    cont = ar.contagens_mc(mc, "Haste", "Ti-6Al-4V ELI")
    assert min(cont.values()) == 9999 and len(cont) == 6
    assert ar.lider_mc(mc, "Haste", "MC propriedades", "TOPSIS") == "Ti-6Al-4V ELI"


def test_percentagens_resultados_junta_a_triangular():
    tri = pd.DataFrame([{"caso": "Haste", "metodo": "TOPSIS", "distribuicao": "triangular",
                         "material": "Ti cp grau 4", "pct_primeiro": 12.3, "n_iter": 10000, "seed": 42}])
    p = ar.percentagens_resultados(_mc(), tri)
    assert "MC triangular" in set(p["analise"]) and len(p) == len(_mc()) + 1


def test_numeros_do_resumo_confirma_e_apanha_erros():
    texto = ("Na haste, o Ti-6Al-4V ELI ficou em 1.º lugar com os três métodos, nos dois cenários e em pelo "
             "menos 9 999 das 10 000 repetições do Monte Carlo (99,99 %).\n"
             "Na haste, o Ti-6Al-4V ELI ficou em 1.º em 5 das 6 combinações de método e cenário.\n"
             "Na haste, o Aço inox 316L ficou mais vezes em 1.º no Monte Carlo com os três métodos.\n"
             "Na haste, ΔC = 0,300 em A e o resto (ΔC = 0,999 (B)).\n"
             "No NJR, 42,5 % das primárias.\n"
             "No implante dentário, o titânio comercialmente puro de grau 4 obteve a melhor pontuação.")
    a = ar.numeros_do_resumo(texto, "resumo_rascunho.md", _pts(), _mc(), _semi())
    por_linha = {(x.onde.split(":")[1], x.nivel) for x in a}
    assert ("1", "erro") not in por_linha and ("1", "ok") in por_linha
    assert ("2", "erro") in por_linha  # é 1.º em 6 de 6, não em 5
    assert ("3", "erro") in por_linha  # o aço não lidera
    assert [x.nivel for x in a if x.onde.endswith(":4")] == ["ok", "erro"]  # ΔC A = 0,3 certo; B = 0,999 errado
    assert [x.nivel for x in a if x.onde.endswith(":5")] == ["nota"]
    assert [x.nivel for x in a if x.onde.endswith(":6")] == ["ok"]


def test_numeros_do_resumo_em_ingles_e_total_errado():
    t = "For the femoral stem, Ti-6Al-4V ELI ranked first in at least 9,999 of the 10,000 Monte Carlo repetitions."
    assert [x.nivel for x in ar.numeros_do_resumo(t, "abstract_rascunho.md", _pts(), _mc(), _semi())] == ["ok"]
    t = "Na haste, o Ti-6Al-4V ELI ficou em 1.º em 9 999 das 5 000 repetições."
    assert ar.numeros_do_resumo(t, "resumo_rascunho.md", _pts(), _mc(), _semi())[0].nivel == "erro"


def test_somas_monte_carlo():
    mc = _mc()
    assert all(a.nivel == "ok" for a in ar.somas_monte_carlo(mc))
    mc.loc[0, "pct_primeiro"] = 90.0
    assert sum(a.nivel == "erro" for a in ar.somas_monte_carlo(mc)) == 1


def test_ler_tabela_resultados():
    t = ("| Cenário | Material | C | Pos. T | Q | Pos. W | P | Pos. V | Consenso |\n|---|---|---|---|---|---|---|---|---|\n"
         "| A | Pt-Cr | 0,653 | 1 | 0,848 | 2 | 0,000 | 1 | 1 (8 pts) |\n")
    df = ar.ler_tabela_resultados(t)
    assert df.iloc[0].to_dict() == {"cenario": "A", "material": "Pt-Cr", "C_TOPSIS": 0.653, "pos_TOPSIS": 1,
                                    "Q_WASPAS": 0.848, "pos_WASPAS": 2, "P_VIKOR": 0.0, "pos_VIKOR": 1,
                                    "pos_Borda": 1, "pontos_Borda": 8}


def test_presenca_reporta_faltas_e_sobras():
    pts = _pts()
    esperados = {("Haste", "A"): ["Ti-6Al-4V ELI", "Aço inox 316L", "Ti cp grau 4"],
                 ("Haste", "B"): ["Ti-6Al-4V ELI", "Aço inox 316L", "TNZT"]}
    a = ar.presenca(esperados, pts, {"Haste": pts})
    assert [x.nivel for x in a] == ["ok", "ok", "erro", "erro"]
    assert "TNZT" in a[2].mensagem and "Ti cp grau 4" in a[2].mensagem


def test_coerencia_rankings_e_tabela_igual():
    pts = _pts()
    assert all(a.nivel == "ok" for a in ar.coerencia_rankings(pts, "x"))
    mau = pts.copy()
    mau.loc[0, "P_VIKOR"] = 0.9  # o 1.º do VIKOR passa a ter P maior do que o 2.º
    mau.loc[0, "pontos_Borda"] = 1
    erros = [a for a in ar.coerencia_rankings(mau, "x") if a.nivel == "erro"]
    assert len(erros) == 1 and "VIKOR" in erros[0].mensagem and "Borda" in erros[0].mensagem
    assert [a.nivel for a in ar.tabela_igual_resultados(pts.round(3), pts)] == ["ok"]
    tab = pts.copy()
    tab.loc[1, "C_TOPSIS"] = 0.4
    assert [a.nivel for a in ar.tabela_igual_resultados(tab, pts)] == ["erro"]


def test_marcadores_e_figuras(tmp_path):
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["svg.hashsalt"] = "teste"  # identificadores fixos, como no scripts/figuras.py
    import matplotlib.pyplot as plt
    rel = tmp_path / "relatorio"
    rel.mkdir()
    (rel / "a_rascunho.md").write_text("<!-- figura: fig_x -->\n<!-- figura: outra -->\n", encoding="utf-8")
    (rel / "RELATORIO.md").write_text("<!-- figura: ignorada -->", encoding="utf-8")
    assert ar.marcadores_figuras(rel) == {"fig_x": ["a_rascunho.md"], "outra": ["a_rascunho.md"]}

    def figura():
        f, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        return f

    pasta = tmp_path / "figs"
    pasta.mkdir()
    svg = pasta / "fig_x.svg"
    f1 = figura()
    f1.savefig(svg, format="svg", dpi=300, metadata={"Date": None})
    plt.close(f1)
    assert ar.svg_igual(figura(), svg)
    png = pasta / "outra.png"
    png.write_bytes(b"x")
    fonte = tmp_path / "dados.csv"
    fonte.write_text("a", encoding="utf-8")
    antigo = time.time() - 100
    os.utime(png, (antigo, antigo))
    caminhos = {"fig_x": str(pasta / "fig_x.png"), "outra": str(png)}
    a = ar.figuras_atualizadas({"fig_x": ["r.md"], "outra": ["r.md"]}, {"fig_x": figura()}, [fonte], caminhos)
    assert [x.nivel for x in a] == ["ok", "aviso"]
    f2, ax = plt.subplots()
    ax.plot([0, 1], [1, 0])
    assert ar.figuras_atualizadas({"fig_x": ["r.md"]}, {"fig_x": f2}, [], caminhos)[0].nivel == "erro"


def test_versoes_ferramentas_e_frase(tmp_path):
    (tmp_path / "results").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "results" / "cfd_stent.md").write_text("Resolvido com o OpenFOAM v2406.", encoding="utf-8")
    (tmp_path / "docs" / "FEA_HASTE_SW.md").write_text("usa-se o SOLIDWORKS 2025 SP2 Premium", encoding="utf-8")
    (tmp_path / "results" / "validacao_matlab.md").write_text("(25.2 (R2025b) Update 2)", encoding="utf-8")
    ansys = tmp_path / "ANSYS Inc"
    (ansys / "ANSYS Student" / "v261").mkdir(parents=True)
    f = ar.versoes_ferramentas(tmp_path, ansys)
    assert f == {"OpenFOAM": "v2406", "SOLIDWORKS": "2025 SP2", "MATLAB": "R2025b", "Ansys": "2026 R1 (v261 Student)"}
    v = {"python": "3.12.10", "numpy": "2.0", "pandas": "2.1", "scipy": "1.1", "matplotlib": None, "gmsh": None,
         "scikit-fem": None, "pyamg": None}
    frase = ar.frase_versoes(42, 10000, v, f, "OpenFOAM e Ansys Fluent")
    assert frase == ("Os cálculos foram feitos em Python 3.12.10, com NumPy 2.0, pandas 2.1 e SciPy 1.1, e o Monte "
                     "Carlo usou 10 000 iterações com a semente 42; a CFD o OpenFOAM v2406 e o Ansys Fluent 2026 R1.")
    assert chr(0x2014) not in frase and chr(0x2013) not in frase  # sem travessões


def test_declaracoes():
    v = {"python": "3.12.10", "numpy": "2.0", "pandas": "2.1", "scipy": "1.1", "matplotlib": "3.0", "gmsh": "4",
         "scikit-fem": "1", "pyamg": "5"}
    texto = "10 000 repetições (semente 42). Python 3.12, NumPy 2.0, pandas 2.1, SciPy 1.1. OpenFOAM sem versão."
    a = {x.onde: x.nivel for x in ar.declaracoes(texto, 42, 10000, v, {})}
    assert a["semente (42)"] == "ok" and a["iterações (10 000)"] == "ok" and a["versão de NumPy"] == "ok"
    assert a["versão do OpenFOAM"] == "erro"
    assert "versão de gmsh" not in a and "versão do MATLAB" not in a  # não citados, não se exigem
    a = {x.onde: x.nivel for x in ar.declaracoes("nada", 42, 10000, v, {})}
    assert a["semente (42)"] == "erro" and a["versão do Python"] == "erro"


def test_relatorio_md_mostra_frase_so_com_erros_de_versoes():
    a = [ar.Achado(6, "erro", "versão do Python", "em falta no relatório"), ar.Achado(2, "ok", "x", "soma")]
    md = ar.relatorio_md(a, "Frase pronta.")
    assert "Frase pronta." in md and "| 6. Semente e versões | 1 | 0 | 0 | 0 |" in md
    assert "Frase pronta." not in ar.relatorio_md(a[1:], "Frase pronta.")


def test_resultados_reais_coerentes():
    """No repositório: as somas do Monte Carlo, a presença das alternativas e os rankings não têm erros."""
    pts = pd.read_csv(ar.RESULTS / "pontuacoes.csv")
    mc = pd.read_csv(ar.RESULTS / "monte_carlo.csv")
    tabelas = ar.ler_tabelas()
    achados = ar.somas_monte_carlo(mc) + ar.presenca(ar.materiais_esperados(), pts, tabelas)
    achados += ar.coerencia_rankings(pts, "pontuacoes")
    for tab in tabelas.values():
        achados += ar.coerencia_rankings(tab, "tabela") + ar.tabela_igual_resultados(tab, pts)
    erros = [(a.verificacao, a.onde, a.mensagem) for a in achados if a.nivel == "erro"]
    assert not erros, erros


@pytest.mark.parametrize("nome", ["resumo_rascunho.md", "abstract_rascunho.md", "00_resumo_executivo.md"])
def test_numeros_dos_resumos_reais_sem_erros(nome):
    f = ar.REL / nome
    if not f.exists():
        pytest.skip(f"{nome} não existe")
    pts = pd.read_csv(ar.RESULTS / "pontuacoes.csv")
    mc = pd.read_csv(ar.RESULTS / "monte_carlo.csv")
    semi = pd.read_csv(ar.RESULTS / "semiquantitativos.csv")
    a = ar.numeros_do_resumo(f.read_text(encoding="utf-8"), nome, pts, mc, semi)
    erros = [(x.onde, x.mensagem) for x in a if x.nivel == "erro"]
    assert not erros, erros
