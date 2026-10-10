import importlib.util
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]


def _carregar(nome):
    spec = importlib.util.spec_from_file_location(nome, RAIZ / "scripts" / f"{nome}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nome] = mod
    spec.loader.exec_module(mod)
    return mod


ap = _carregar("apresentacao")
po = _carregar("poster")


@pytest.fixture(scope="module")
def numeros():
    return ap.ler_numeros()


def test_ler_numeros_reproduz_os_valores_do_relatorio(numeros):
    # 111 verificados: 109 desde as correções de fontes de 8 out (bloco 2) e mais 2 com a tração do 316L e do Ti grau 4
    # da haste (Okazaki 2012, aprovada a 9 out); o relatório v9 tem 95
    assert numeros.n_valores == 300 and numeros.n_verificados == 111
    assert round(numeros.c_haste, 3) == 0.752
    assert numeros.mc_haste == {"TOPSIS": 9999, "WASPAS": 10000, "VIKOR": 10000}
    assert round(numeros.dc_stent["A"], 3) == 0.022 and round(numeros.dc_stent["B"], 3) == 0.002
    assert round(numeros.dc_scaffold["A"], 3) == 0.051 and round(numeros.dc_scaffold["B"], 3) == 0.085
    assert (round(numeros.mc_stent_ptcr[0]), round(numeros.mc_stent_ptcr[1])) == (56, 70)
    assert numeros.vencedor_dentario == "Ti cp grau 4"
    assert round(100 * numeros.extra["p_alvo"], 1) == 59.9
    assert round(numeros.extra["troca_waspas"], 2) == 0.52


def test_xml_timing_tem_entradas_video_automatico_e_nos_de_media():
    xml = ap.xml_timing([5, 6], [(9, 13000, True), (10, 12000, False)], {5})
    s = ap.etree.tostring(xml).decode()
    assert s.count('presetClass="entr"') == 2
    assert s.count('presetClass="mediacall"') == 1 and 'cmd="playFrom(0.0)"' in s
    assert s.count("<p:video>") == 2
    assert '<p:bldP spid="5"' in s and '<p:bldP spid="6"' not in s
    ids = [int(x.split('"')[1]) for x in s.split('cTn id=')[1:]]
    assert len(ids) == len(set(ids))


def test_xml_transicao_morph_tem_alternativa_fade():
    s = ap.etree.tostring(ap.xml_transicao(True)).decode()
    assert "morph" in s and "<p:fade/>" in s
    assert "morph" not in ap.etree.tostring(ap.xml_transicao(False)).decode()


def test_formatos_portugueses():
    assert ap.pt(0.7519, 3) == "0,752"
    assert ap.milhares(10000) == "10 000"


def test_frases_dos_casos_sem_travessoes(numeros):
    frases = po.frases_casos(numeros)
    assert [c for c, _ in frases] == ["Haste femoral", "Stent coronário", "Scaffold ósseo", "Par articular",
                                      "Implante dentário"]
    texto = " ".join(f for _, f in frases) + " ".join(po.REFERENCIAS)
    assert "9 999 / 10 000 / 10 000" in texto
    assert chr(0x2014) not in texto and chr(0x2013) not in texto


def test_tamanhos_do_poster():
    assert po.A2[0] / po.A2[1] == pytest.approx(420 / 594)
    # A3 por redução direta: mesma proporção
    assert (297 / 420) == pytest.approx(420 / 594, rel=0.002)


def test_figuras_do_poster_no_tamanho_de_impressao_e_com_letra_legivel_em_a3(numeros, tmp_path):
    from PIL import Image
    assert po.LETRA_MIN_A2 * 297 / 420 >= 12
    figs = po.figuras_poster(numeros, tmp_path)
    assert [f.name for f in figs] == ["poster_haste.png", "poster_stent.png", "poster_scaffold.png",
                                      "poster_par.png", "poster_dentario.png"]
    for f in figs:
        w, h = Image.open(f).size
        assert abs(w - po.TAM_FIG[0] * 300) <= 1 and abs(h - po.TAM_FIG[1] * 300) <= 1


def test_dados_das_figuras_do_poster_vem_dos_resultados(numeros):
    d = po.dados_figuras(numeros)
    assert round(float(d["stent"]["TOPSIS"]["Pt-Cr"]), 1) == 69.7
    assert d["par"].iloc[0]["material"] == numeros.vencedor_par
    assert d["dentario"].iloc[0]["material"] == numeros.vencedor_dentario
