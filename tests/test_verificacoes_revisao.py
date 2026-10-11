import importlib.util
from pathlib import Path

import numpy as np

from biomat_mcdm.io import DecisionProblem

CAMINHO = Path(__file__).resolve().parents[1] / "scripts" / "verificacoes_revisao.py"
spec = importlib.util.spec_from_file_location("verificacoes_revisao", CAMINHO)
vr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vr)


def problema(tipico=None):
    X_min = np.array([[1.0, 1.0], [2.0, 2.0], [3.0, 3.0]])
    X_max = np.array([[1.0, 5.0], [2.0, 2.0], [3.0, 3.0]])
    return DecisionProblem(["a", "b", "c"], ["c1", "c2"], X_min, X_max, ["benefit", "benefit"], [None, None],
                           np.array([0.5, 0.5]), tipico)


def test_fracoes_por_limiar_soma_areas_abaixo():
    fr = vr.fracoes_por_limiar(np.array([0.2, 0.5, 0.9]), np.array([1.0, 1.0, 2.0]), (0.3, 0.6, 1.0))
    assert fr == {0.3: 0.25, 0.6: 0.5, 1.0: 1.0}


def test_compromisso_vikor_com_vencedor_claro():
    c = vr.compromisso_vikor(problema())  # típico = ponto médio: c domina
    assert c["ordem"][0] == "c" and c["P"][0] == 0.0
    assert c["limiar"] == 0.5 and c["C1"] and c["C2"] and c["conjunto"] == ["c"]


def test_vencedores_ponto_medio_compara_tipico_e_meio():
    # típico de "a" no c2 = 5 (máximo): com o típico ganha "a"; com o ponto médio (3) ganha "c"
    tip = np.array([[1.0, 5.0], [2.0, 2.0], [3.0, 3.0]])
    v = vr.vencedores_ponto_medio(problema(tip))
    assert set(v) == {"TOPSIS", "WASPAS", "VIKOR"}
    assert all(m == "c" for _, m in v.values())


def test_texto_tem_as_tres_seccoes_sem_cfd():
    md = vr.texto(cfd=None)
    assert "R25" in md and "R27" in md and "R46" in md and "Sem os VTK" in md
    assert "| Stent | A |" in md


def test_sensibilidade_valor_troca_o_vencedor_quando_o_valor_piora():
    # "a" ganha com c2 = 5; com c2 = 1 (intervalo 1-5) passa a ganhar "c"
    tip = np.array([[1.0, 5.0], [2.0, 2.0], [3.0, 3.0]])
    s = vr.sensibilidade_valor(problema(tip), "a", "c2", (5, 1), (1, 5))
    assert [x["valor"] for x in s] == [5.0, 1.0]
    assert s[1]["TOPSIS"][0] == "c" and s[1]["dC_TOPSIS"] > 0
    assert set(s[0]) == {"valor", "TOPSIS", "WASPAS", "VIKOR", "dC_TOPSIS"}


def test_texto_tem_a_sensibilidade_da_degradacao():
    md = vr.texto(cfd=None)
    assert "R91" in md and "| A | 36 |" in md and "| B | 48 |" in md
