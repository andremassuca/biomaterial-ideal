"""Testes do verificador de referências cruzadas do relatório."""
import importlib.util
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("verificar_seccoes", RAIZ / "scripts" / "verificar_seccoes.py")
vs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vs)

TEXTO = """# 1. Introdução

As secções 2 a 3 tratam dos métodos; a secção 8.3 tem a FEA e o Anexo A.5 o VIKOR (ver também o capítulo 9).

# 2. Métodos
# 3. Validação
# 8. Extensões exploratórias
## 8.3. Simulação da haste
# 9. Discussão
# Anexo A. Equações dos métodos
## A.5 VIKOR com critérios-alvo

# Referências

Na secção 99 das referências nada se verifica.
"""


def test_titulos_e_referencias_resolvidas():
    t = vs.titulos(TEXTO)
    assert t["8"] == "Extensões exploratórias" and t["8.3"] == "Simulação da haste" and t["A.5"].startswith("VIKOR")
    ok, falhas = vs.verificar(TEXTO)
    assert not falhas
    assert {c for _, _, c, _ in ok} == {"2", "3", "8.3", "A.5", "9"}


def test_referencia_sem_destino_e_apanhada():
    ok, falhas = vs.verificar(TEXTO.replace("secção 8.3", "secção 8.7"))
    assert [c for _, _, c in falhas] == ["8.7"]


def test_relatorio_montado_nao_tem_referencias_perdidas():
    import sys
    sys.path.insert(0, str(RAIZ / "scripts"))
    import montar_relatorio as mr
    _, falhas = vs.verificar(mr.montar())
    assert not falhas, falhas
