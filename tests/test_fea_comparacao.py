"""Testes de scripts/fea_comparacao.py (com dados pequenos, sem os resultados reais)."""
import importlib.util
import json
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fea_comparacao", RAIZ / "scripts" / "fea_comparacao.py")
fc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fc)


def test_razoes_e_ordem(tmp_path):
    csv = tmp_path / "py.csv"
    pd.DataFrame({"malha_mm": [1.0] * 4 + [2.0], "material": ["316L", "316L", "Ti-6Al-4V", "Ti-6Al-4V", "316L"],
                  "zona": [1, 7, 1, 7, 1], "razao": [0.6, 0.1, 0.7, 0.2, 0.9]}).to_csv(csv, index=False)
    js = tmp_path / "sw.json"
    js.write_text(json.dumps({"malhas_mm": [5.0, 3.5], "casos": {
        "Intacto": {"3.5": {"zonas": {"1": {"energia_J": 2.0}, "7": {"energia_J": 4.0}}}},
        "Aço inox 316L": {"3.5": {"zonas": {"1": {"energia_J": 1.0}, "7": {"energia_J": 1.0}}}},
        "Ti-6Al-4V ELI": {"3.5": {"zonas": {"1": {"energia_J": 1.4}, "7": {"energia_J": 2.0}}}}}}), encoding="utf-8")
    py, sw = fc.razoes_python(csv), fc.razoes_solidworks(js)
    assert py.loc["Aço inox 316L", "G1"] == 0.6  # só a malha mais fina
    assert sw.loc["Ti-6Al-4V ELI", "G7"] == 0.5
    t = fc.tabela(py, sw)
    assert list(t.index) == ["Ti-6Al-4V ELI", "Aço inox 316L"]
    texto = fc.md(t)
    assert "A ordem é a mesma nas duas ferramentas" in texto and "—" not in texto
