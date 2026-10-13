import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

RAIZ = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("mapas_vm", RAIZ / "scripts" / "mapas_von_mises_mapdl.py")
mv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mv)

RST_316L = mv.RST_DIR_PADRAO / "Aco316L" / "haste.rst"
JSON = mv.JSON_PADRAO


def test_vm_tracao_uniaxial_e_corte_puro():
    assert mv.vm_de_tensor([100, 0, 0, 0, 0, 0]) == pytest.approx(100.0)
    # corte puro: vm = sqrt(3) * tau
    assert mv.vm_de_tensor([0, 0, 0, 50, 0, 0]) == pytest.approx(50 * np.sqrt(3))
    # pressão hidrostática não produz von Mises
    assert mv.vm_de_tensor([-80, -80, -80, 0, 0, 0]) == pytest.approx(0.0)
    assert mv.vm_de_tensor(np.zeros((4, 6))).shape == (4,)


def test_media_nodal_por_corpo_nao_mistura_materiais():
    # dois elementos a partilhar o nó 0 (interface): corpo 1 com sx=100, corpo 3 com sx=300
    conn = np.array([[0, 1], [0, 2]])
    tens = np.zeros((2, 2, 6))
    tens[0, :, 0] = 100.0
    tens[1, :, 0] = 300.0
    corpo = np.array([1, 3])
    m = mv.media_nodal_por_corpo(conn, tens, corpo, 4)
    assert m[1][0] == pytest.approx(100.0) and m[3][0] == pytest.approx(300.0)
    assert np.isnan(m[1][2]) and np.isnan(m[3][1])      # nós que o corpo não toca
    assert np.isnan(m[2]).all()                          # corpo sem elementos
    # a média sobre todos misturaria: 200 no nó 0
    glob = mv.media_nodal_por_corpo(conn, tens, np.array([1, 1]), 4)
    assert glob[1][0] == pytest.approx(200.0)


def test_maximos_por_corpo():
    mx = mv.maximos_por_corpo({1: np.array([1.0, np.nan, 5.0]), 2: np.array([2.0, 3.0, np.nan]),
                               3: np.full(3, np.nan)})
    assert mx["Osso cortical"] == 5.0 and mx["Osso trabecular"] == 3.0 and mx["Haste"] is None
    assert mx["Global"] == 5.0


def test_escala_comum_arredonda_para_cima():
    e = mv.escala_comum([73.6, 124.6, 88.1])
    assert e == {"min": 0.0, "max": 130.0, "saturacao": 130.0}
    assert mv.escala_comum([120.0])["max"] == 120.0
    with pytest.raises(ValueError):
        mv.escala_comum([])


def test_formatacao_e_ticks():
    assert mv.fmt_pt(171.89) == "171,9" and mv.fmt_pt(None) == "n.d."
    pos, rot = mv.ticks_da_escala({"min": 0.0, "max": 130.0, "saturacao": 130.0})
    assert pos[0] == 0.0 and pos[-1] == 130.0 and rot[-1] == "130+" and len(pos) == len(rot)
    assert mv.nome_ficheiro("CoCrMo", "frente") == "CoCrMo_von_mises_frente.png"
    assert mv.dentro_da_tolerancia(171.9, 171.8) and not mv.dentro_da_tolerancia(160.6, 171.9)


def test_caixa_comum_cobre_todas_as_imagens():
    a = np.full((50, 60, 3), 255, dtype=np.uint8)
    b = a.copy()
    a[10:20, 10:20] = 0
    b[30:40, 40:50] = 0
    l0, l1, c0, c1 = mv.caixa_comum([a, b], margem=2)
    assert (l0, l1, c0, c1) == (8, 42, 8, 52)


@pytest.mark.skipif(not JSON.exists(), reason="JSON dos mapas ainda não gerado")
def test_json_coerente_com_os_png():
    d = json.loads(JSON.read_text(encoding="utf-8"))
    assert "malha" in d["nota"] and set(d["casos"]) == set(mv.CASOS)
    pasta = mv.SAIDA_PADRAO
    for k, c in d["casos"].items():
        for chave in ("material", "E_haste_GPa", "vm_max_MPa", "malha_mm", "elementos", "nos", "escala_MPa",
                      "ficheiros"):
            assert chave in c
        assert c["malha_mm"] == 3.0 and c["escala_MPa"]["max"] == d["escala_MPa"]["max"]
        assert dentro_ou_igual(c["vm_max_MPa"]["Global"], mv.PUBLICADO_MPA[k])
        for f in c["ficheiros"].values():
            assert (pasta / f).exists()
    assert (pasta / d["ficheiro_comparacao"]).exists()


def dentro_ou_igual(obtido, esperado):
    return mv.dentro_da_tolerancia(obtido, esperado)


@pytest.mark.skipif(not RST_316L.exists(), reason="ficheiros .rst do MAPDL não existem nesta máquina")
def test_integracao_pico_316l():
    c = mv.ler_caso(RST_316L)
    medias = mv.media_nodal_por_corpo(c["conn"], c["tens"], c["corpo"], len(c["pontos"]))
    mx = mv.maximos_por_corpo(medias)
    assert mv.dentro_da_tolerancia(mx["Haste"], 171.9)
    assert c["E_haste_GPa"] == pytest.approx(207.5)
