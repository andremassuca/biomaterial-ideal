"""Testes de scripts/fea_haste.py (funções auxiliares; o caso completo só com a malha anatómica presente)."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("skfem")

CAMINHO = Path(__file__).resolve().parents[1] / "scripts" / "fea_haste.py"
spec = importlib.util.spec_from_file_location("fea_haste", CAMINHO)
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)


def test_propriedades_por_etiqueta():
    et = np.array([1, 2, 3, 4, 0])
    osso = {"cortical": (17500.0, 0.3), "trabecular": (2440.0, 0.3)}
    E, nu = F.propriedades(et, 105500.0, 0.34, osso, (225000.0, 0.3))
    assert E.tolist() == [17500.0, 2440.0, 105500.0, 225000.0, 0.0]
    assert nu[2] == 0.34


def _df():
    linhas = []
    for h in (1.0, 0.75):
        for nome, base in (("Fémur intacto", 10.0), ("316L", 5.0), ("Ti-6Al-4V poroso", 9.0)):
            for z in range(1, 8):
                e = base * (1.02 if h == 1.0 else 1.0)
                linhas.append({"malha_mm": h, "material": nome, "E_haste_GPa": np.nan if base == 10 else 1.0,
                               "zona": z, "energia_mJ": e, "energia_por_volume_mJ_mm3": e / 100,
                               "razao": e / 10, "stress_shielding": 1 - e / 10, "elementos": 100,
                               "graus_liberdade": 300})
    return pd.DataFrame(linhas)


def test_tabela_md_tem_tabela_convergencia_e_ordem():
    texto = F.tabela_md(_df(), [1.0, 0.75])
    assert "| 316L |" in texto
    assert "Variação entre as duas malhas mais finas (1 e 0,75 mm)" in texto
    assert "| 316L | 2,0 | 2,0 |" in texto
    assert "- Gruen 1: Ti-6Al-4V poroso > 316L" in texto
    assert chr(0x2014) not in texto and chr(0x2013) not in texto  # sem travessões
    assert "a razão implantado / intacto (e portanto o stress shielding) cumpre" in texto
    assert "a energia absoluta cumpre (máximo 2,0 %)" in texto


def test_num_virgula_decimal_e_sem_menos_zero():
    assert F.num(1.2345) == "1,234" or F.num(1.2345) == "1,235"
    assert F.num(-0.0001) == "0,000"
    assert F.num(0.000612, ".2e") == "6,12e-04"
    assert F.num(0.75, "g") == "0,75"


@pytest.mark.skipif(not F.OBJ_FEMUR.exists(), reason="malha anatómica do BodyParts3D não disponível")
def test_caso_completo_em_malha_grossa():
    g, ff, hv, hf, cotas = F.preparar()
    assert np.allclose(g["H"], g["centro_haste"], atol=0.5)  # haste no sítio dos renders
    linhas = pd.DataFrame(F.correr_malha(4.0, g, ff, hv, hf, cotas, 75.0))
    assert len(linhas) == 5 * 7
    g1 = linhas[linhas["zona"] == 1].set_index("material")["energia_mJ"]
    # física esperada: haste mais rígida, menos energia no osso proximal
    assert g1["Co-Cr-Mo"] < g1["Ti-6Al-4V"] < g1["Ti-6Al-4V poroso"]


def test_tabela_md_diz_proximo_do_osso_intacto():
    texto = F.tabela_md(_df(), [1.0, 0.75])
    assert "próxima da do osso intacto" in texto and "melhor" not in texto


def _campos_sinteticos():
    ijk = np.array([[i, j, 2] for i in range(20) for j in range(40)])
    et = np.where(ijk[:, 0] < 10, 1, 3)
    m = {"h": 5.0, "origem": np.array([-60.0, -20.0, -12.0]), "forma": np.array([20, 40, 5]), "ijk": ijk, "et": et}
    W = np.full(len(ijk), 1e-3 * 125)
    return {k: (m, W) for k in F.PAINEIS_DIAPOSITIVO}


def test_titulos_diapositivo_com_nomes_simples():
    assert F.titulos_diapositivo() == ["Fémur intacto", "Cobalto-crómio (Co-Cr-Mo)", "Liga de titânio porosa (17 GPa)"]


def test_figura_diapositivo_tamanho_e_ficheiros(tmp_path):
    from PIL import Image

    destino = F.figura_diapositivo(_campos_sinteticos(), 118.7, tmp_path / "diap")
    png = destino.with_suffix(".png")
    assert png.exists() and destino.with_suffix(".svg").exists()
    largura, altura = Image.open(png).size
    assert (largura, altura) == (2280, 1380)  # 7,6 x 4,6 polegadas a 300 ppp


def _verificacao_sintetica():
    base = {"aplicada_N": np.array([1.0, -2.0, 3.0]), "reacao_N": np.array([-1.0, 2.0, -3.0]),
            "erro_equilibrio_pct": 1e-9, "residuo_max_N": 1e-8, "desloc_max_mm": 3.21,
            "ponto_max": np.array([-40.0, 150.0, 3.0]), "desloc_cabeca_mm": np.array([-2.0, -0.5, 1.0])}
    intacto = dict(base, eps_max_ue=np.array([400, 1100, 1300, 1600.0]),
                   eps_min_ue=np.array([-400, -1500, -1700, -2000.0]), eps_cortical_todo_ue=(1400.0, -1900.0),
                   axial_lateral_ue=600.0, axial_medial_ue=-900.0)
    return {"Fémur intacto": intacto, "Ti-6Al-4V": base}


def test_texto_verificacoes():
    texto = F.texto_verificacoes(_verificacao_sintetica(), 0.75)
    assert "| Fémur intacto | 1,0; -2,0; 3,0 | -1,0; 2,0; -3,0 |" in texto
    assert "| Máxima (tração) | 400 | 1100 | 1300 | 1600 |" in texto
    assert "lado lateral 600, lado medial -900" in texto


def test_texto_sensibilidade_diz_se_a_ordem_muda():
    base = _df()
    sens = base.copy()
    sens.loc[sens["material"] == "316L", "energia_mJ"] = 20.0  # passa à frente do poroso
    texto = F.texto_sensibilidade(sens, base, 2440.0, 390.0, 0.75)
    assert "| 316L |" in texto and "Razão G1 (0,39 GPa)" in texto and "Razão G1 (2,44 GPa)" in texto
    assert "- Gruen 1: ordem diferente" in texto
    assert "- Gruen 7: ordem diferente" in texto
    assert "ordem igual" in F.texto_sensibilidade(base, base, 2440.0, 390.0, 0.75)
