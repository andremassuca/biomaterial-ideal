import importlib.util
import sys
from pathlib import Path

CAMINHO = Path(__file__).resolve().parents[1] / "scripts" / "verificar_delta_c.py"
spec = importlib.util.spec_from_file_location("verificar_delta_c", CAMINHO)
vd = importlib.util.module_from_spec(spec)
sys.modules["verificar_delta_c"] = vd
spec.loader.exec_module(vd)


def test_ocorrencias_identifica_caso_e_cenario():
    t = ("- **Stent:** no cenário A blá; no cenário B, empatado (ΔC = 0,002).\n"
         "- **Scaffold:** nos dois cenários (ΔC = 0,051 em A e 0,085 em B).")
    o = vd.ocorrencias(t, "discussao_rascunho.md")
    assert [(x.caso, x.cenario, x.valor) for x in o] == [("Stent", "B", 0.002), ("Scaffold", "A", 0.051),
                                                         ("Scaffold", "B", 0.085)]
    assert vd.ocorrencias("No cenário A (ΔC = 0,022).", "caso_stent_rascunho.md")[0].caso == "Stent"


def test_todos_os_delta_c_do_relatorio_batem_com_os_resultados():
    res = vd.conferir()
    assert res, "não se encontrou nenhum ΔC nos rascunhos"
    falhas = [(o.ficheiro, o.linha, o.valor, d) for o, d, ok in res if not ok]
    assert not falhas, f"ΔC escritos à mão que não batem com results/pontuacoes.csv: {falhas}"
