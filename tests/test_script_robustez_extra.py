"""Testes de scripts/robustez_extra.py (o script carrega-se pelo caminho)."""
import importlib.util
from pathlib import Path

import pandas as pd

CAMINHO = Path(__file__).resolve().parents[1] / "scripts" / "robustez_extra.py"
spec = importlib.util.spec_from_file_location("robustez_extra_script", CAMINHO)
se = importlib.util.module_from_spec(spec)
spec.loader.exec_module(se)


def test_correr_e_relatorio_num_caso(monkeypatch):
    monkeypatch.setattr(se, "CASOS", {"Haste": se.CASOS["Haste"]})
    monkeypatch.setattr(se, "CENARIOS", ("A",))
    t = se.correr(n_iter=50)
    assert set(t) == {"retirar", "dimensoes", "pesos", "valores"}
    assert len(t["retirar"]) == 5 * 3 and len(t["dimensoes"]) == 3
    assert t["valores"]["estado"].notna().all()
    texto = se.relatorio_md(t, 50, 42)
    assert "## Haste, cenário A" in texto and "### a) Retirar uma alternativa" in texto
    assert "—" not in texto and "–" not in texto  # sem travessões


def test_vencedores_base_assinala_empate():
    assert "empate" in se.vencedores_base("Stent", "B")  # ΔC = 0,002
    assert "empate" not in se.vencedores_base("Haste", "A")


def test_com_fontes_marca_valores_sem_linha():
    av = pd.DataFrame({"material": ["Pt-Cr", "Inexistente"], "criterio": ["Módulo de Young", "Módulo de Young"]})
    out = se.com_fontes(av, "Stent vascular")
    assert out.loc[0, "estado"] != "sem linha na base" and out.loc[1, "estado"] == "sem linha na base"
    assert out.loc[1, "ref_curta"] == "sem referência"


def _retirar():
    return pd.DataFrame({
        "retirado": ["X"] * 3 + ["Y"] * 3, "metodo": ["TOPSIS", "WASPAS", "VIKOR"] * 2,
        "alterado": [True, False, True, False, False, False], "so_empates": [True, False, False] + [False] * 3,
        "pares": ["A ↔ B (empate)", "", "A ↔ B", "", "", ""],
        "vencedor_antes": ["A", "A", "A", "A", "A", "A"], "vencedor_depois": ["A", "A", "B", "A", "A", "A"]})


def test_celula_e_tabela_retirar():
    r = _retirar()
    assert se.celula_retirar(r.iloc[[0]]) == "sim (só empates, ΔC < 0,01)"
    assert se.celula_retirar(r.iloc[[1]]) == "não" and se.celula_retirar(r.iloc[[2]]) == "sim"
    t = se.tabela_retirar(r)
    assert t["Retirado"].tolist() == ["X", "Y"]
    assert t.loc[1, "Pares que trocam"] == "nenhum" and "VIKOR: A ↔ B" in t.loc[0, "Pares que trocam"]


def test_frase_vencedor_retirar():
    r = _retirar()
    assert "VIKOR sem X (A → B)" in se.frase_vencedor_retirar(r)
    assert "nunca muda" in se.frase_vencedor_retirar(r.iloc[[0, 1]])


def test_tabela_dimensoes():
    dm = pd.DataFrame({"metodo": ["TOPSIS", "VIKOR"], "vencedor_base": ["A", "A"], "vencedor_iguais": ["A", "B"],
                       "pct_mantem": [90.0, 100.0], "pct_mantem_ou_empate": [95.0, 100.0],
                       "outro_vencedor": ["B", ""], "pct_outro": [10.0, 0.0]})
    t = se.tabela_dimensoes(dm)
    assert t.loc[0, "MC: mantém o 1.º"] == "90,0 % (95,0 % com empates)"
    assert t.loc[1, "Outro 1.º mais frequente"] == "nenhum"


def test_tabelas_de_ajuste_e_frase_de_empate():
    pw = pd.DataFrame({"criterio": ["a", "a", "a", "b", "b", "b"], "metodo": ["TOPSIS", "WASPAS", "VIKOR"] * 2,
                       "peso": [0.6] * 3 + [0.4] * 3, "var": [-0.2, None, -0.3, None, None, None],
                       "novo_vencedor": ["B", None, "B", None, None, None],
                       "var_empate": [-0.15, None, None, None, None, None]})
    t = se.tabela_pesos(pw)
    assert t["Critério"].tolist() == ["a", "b"] and t.loc[0, "TOPSIS"] == "-20,0 % (B)"
    assert t.loc[1, "VIKOR"] == "não troca até ±100 %"
    pv = pd.DataFrame({"material": ["A"] * 3, "criterio": ["c"] * 3, "metodo": ["TOPSIS", "WASPAS", "VIKOR"],
                       "ordinal": [True] * 3, "valor": [5.0] * 3, "var": [-0.2, -0.4, None], "pontos": [-1, -2, None],
                       "novo_vencedor": ["B", "B", None], "var_empate": [-0.2, None, None],
                       "estado": ["A verificar"] * 3, "ref_curta": ["Escala"] * 3})
    v = se.tabela_valores(pv)
    assert v.loc[0, "Variação que troca"] == "-1 ponto (-20,0 %)" and v.loc[0, "Valor"] == "5 (ordinal)"
    assert v.loc[0, "Estado"] == "A verificar"
    f = se.frase_empate_topsis(pw, pv)
    assert "peso: a -15,0 %" in f and "valor: A / c -1 ponto (-20,0 %)" in f
