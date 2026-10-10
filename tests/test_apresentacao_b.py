"""Testes de scripts/apresentacao_b.py (funções de dados e de imagem; sem PowerPoint)."""
import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from PIL import Image

RAIZ = Path(__file__).resolve().parents[1]


def _carregar(nome):
    spec = importlib.util.spec_from_file_location(nome, RAIZ / "scripts" / f"{nome}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nome] = mod
    spec.loader.exec_module(mod)
    return mod


ab = _carregar("apresentacao_b")


@pytest.fixture(scope="module")
def numeros():
    return ab.ap.ler_numeros()


def test_confianca_classifica_os_cinco_dispositivos(numeros):
    c = {d: nivel for d, _, nivel, _ in ab.confianca(numeros, True, simples=True)}
    assert c == {"Haste femoral": "Sólida", "Stent coronário": "Empate técnico", "Scaffold ósseo": "Depende da leitura",
                 "Par articular": "Indicativo", "Implante dentário": "Indicativo"}


def test_confianca_muda_com_os_numeros(numeros):
    fraca = replace(numeros, mc_haste={"TOPSIS": 9000, "WASPAS": 10000, "VIKOR": 10000},
                    dc_stent={"A": 0.05, "B": 0.03})
    c = {d: nivel for d, _, nivel, _ in ab.confianca(fraca, False)}
    assert c["Haste femoral"] == "Provável" and c["Stent coronário"] == "Provável"
    assert c["Scaffold ósseo"] == "Provável"


def test_funil_le_os_numeros_do_results():
    f = ab.funil()
    assert f["mp"] > f["nivel2"] > f["base"] > f["final"] == 5
    assert f["elementos"] == 118


def test_perfis_exemplo_tem_o_defeito_sem_carga_e_a_alergia_ao_titanio():
    ex = {d: (antes, depois) for d, _, antes, depois in ab.perfis_exemplo()}
    assert ex["Defeito sem carga"] == ("Compósito PCL/β-TCP (impressão 3D)", "β-TCP poroso")
    assert ex["Alergia ao titânio confirmada por teste"] == ("Ti cp grau 4", "Zircónia Y-TZP")


def test_intervalo_e_n_regras():
    lo, hi, u = ab.intervalo("Aço inox 316L", "Módulo de Young")
    assert (lo, hi, u) == (205.0, 210.0, "GPa")
    assert ab.n_regras() == len(pd.read_csv(RAIZ / "data" / "perfis_doente.csv"))


def test_nb_e_mil_nao_partem_os_numeros():
    assert ab.nb("10 000 a 9 999") == "10 000 a 9 999"
    assert " " not in ab.mil(10000)


def test_pasta_renders_escolhe_a_primeira_completa(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir(), b.mkdir()
    for c, _, _ in ab.DISPOSITIVOS:
        (b / f"{c}_transparente.png").write_bytes(b"")
    (a / "anca_transparente.png").write_bytes(b"")
    assert ab.pasta_renders([a, b]) == b
    with pytest.raises(FileNotFoundError):
        ab.pasta_renders([a])


def _render_teste(caminho):
    a = np.zeros((200, 300, 4), np.uint8)
    a[80:120, 120:180] = (200, 50, 50, 255)    # objeto opaco
    a[60:160, 20:290, 3] = np.maximum(a[60:160, 20:290, 3], 90)  # sombra larga e meio transparente
    Image.fromarray(a, "RGBA").save(caminho)


def test_recortar_transparente_segue_o_objeto_e_esbate_a_sombra(tmp_path):
    o = tmp_path / "x_transparente.png"
    _render_teste(o)
    d = ab.recortar_transparente(o, tmp_path / "cache")
    im = np.asarray(Image.open(d))
    assert im.shape[1] < 300 and im.shape[0] < 200      # recortado à volta do objeto
    assert im[..., 3].max() == 255                       # o objeto fica opaco
    assert im[0, :, 3].max() == 0 and im[:, 0, 3].max() == 0  # a sombra chega a zero nas margens


def test_logotipo_branco_mantem_a_transparencia(tmp_path):
    o = tmp_path / "logo.png"
    a = np.zeros((10, 10, 4), np.uint8)
    a[2:5, 2:5] = (10, 20, 30, 255)
    Image.fromarray(a, "RGBA").save(o)
    b = np.asarray(Image.open(ab.logotipo_branco(o, tmp_path)))
    assert (b[3, 3] == (255, 255, 255, 255)).all() and b[0, 0, 3] == 0


def test_imagem_reduzida(tmp_path):
    o = tmp_path / "grande.png"
    Image.new("RGB", (4000, 2000)).save(o)
    d = ab.imagem_reduzida(o, 1000, tmp_path / "c")
    assert Image.open(d).size == (1000, 500)


def test_confianca_sem_nomes_simples_mantem_a_versao_1(numeros):
    c = ab.confianca(numeros, True)
    assert c[0][1] == "Ti-6Al-4V ELI" and c[3][2] == "Indicação"


def test_razoes_fea_e_grafico(tmp_path):
    csv = tmp_path / "fea.csv"
    pd.DataFrame({"malha_mm": [1.0] * 4 + [2.0], "material": ["316L", "316L", "Ti-6Al-4V", "Ti-6Al-4V", "316L"],
                  "zona": [1, 7, 1, 7, 1], "razao": [0.6, 0.1, 0.7, 0.2, 0.9]}).to_csv(csv, index=False)
    r = ab.razoes_fea(csv)
    assert r == {"Ti-6Al-4V": (0.7, 0.2), "316L": (0.6, 0.1)}
    p = ab.grafico_fea(r, tmp_path / "g.png")
    assert Image.open(p).size[0] > 1000


def test_n_verificados_conta_os_estados_verificado(tmp_path):
    pd.DataFrame({"estado": ["Verificado", "Verificado (fornecedor)", "A verificar", "Verificado (derivado)"]}) \
        .to_csv(tmp_path / "materiais.csv", index=False)
    assert ab.n_verificados(tmp_path) == (3, 4)
    v, t = ab.n_verificados()
    assert 0 < v < t


def test_mc_primeiro_le_o_monte_carlo_das_propriedades(tmp_path):
    pd.DataFrame({"caso": ["Stent"] * 3 + ["Haste"], "analise": ["MC propriedades"] * 2 + ["W pesos ±20 %"] * 2,
                  "metodo": ["TOPSIS", "WASPAS", "TOPSIS", "TOPSIS"], "material": ["Pt-Cr"] * 4,
                  "pct_primeiro": [70.0, 56.0, 83.0, 1.0]}).to_csv(tmp_path / "monte_carlo.csv", index=False)
    assert ab.mc_primeiro("Stent", tmp_path) == {"Pt-Cr": {"TOPSIS": 70.0, "WASPAS": 56.0}}
    st = ab.mc_primeiro("Stent")
    assert set(st["Pt-Cr"]) == {"TOPSIS", "WASPAS", "VIKOR"}


def test_graficos_ficam_com_o_tamanho_da_caixa(tmp_path):
    """Os gráficos dos diapositivos têm exatamente as polegadas da caixa (300 ppp): a letra não encolhe."""
    p = ab.grafico_mc_stent({"Pt-Cr": {"TOPSIS": 70, "WASPAS": 56, "VIKOR": 58},
                             "Co-Cr L605": {"TOPSIS": 27, "WASPAS": 41, "VIKOR": 32}}, tmp_path / "m.png")
    assert Image.open(p).size == (round(5.55 * 300), round(4.7 * 300))
    g = ab.grafico_gibson(tmp_path / "g.png")
    assert Image.open(g).size == (round(5.55 * 300), round(4.7 * 300))
    f = ab.grafico_funil(pd.read_csv(RAIZ / "results" / "funil.csv"), tmp_path / "f.png")
    assert Image.open(f).size == (round(7.9 * 300), round(4.9 * 300))
    r = ab.grafico_fea({"316L": (0.5, 0.1)}, tmp_path / "r.png")
    assert Image.open(r).size == (round(5.25 * 300), round(4.3 * 300))


def test_dados_e_grafico_da_cfd(tmp_path):
    import json
    js = tmp_path / "cfd.json"
    js.write_text(json.dumps({"Pt-Cr": {"espessura_um": 79.0, "fracao_baixa": 0.46},
                              "316L": {"espessura_um": 135.0, "fracao_baixa": 0.81}}), encoding="utf-8")
    d = ab.dados_cfd(js)
    assert d["316L"]["fracao_baixa"] == 0.81
    p = ab.grafico_cfd(d, tmp_path / "c.png")
    assert Image.open(p).size[0] > 1000
