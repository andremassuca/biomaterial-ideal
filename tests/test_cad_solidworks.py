"""Testes das funções puras de scripts/cad_solidworks.py (sem SolidWorks; o script carrega-se pelo caminho)."""

import importlib.util
import math
from pathlib import Path

import pytest

CAMINHO = Path(__file__).resolve().parents[1] / "scripts" / "cad_solidworks.py"
spec = importlib.util.spec_from_file_location("cad_solidworks", CAMINHO)
cad = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cad)


@pytest.fixture(scope="module")
def c():
    return cad.ler_cotas()


def test_ler_cotas_le_valores_com_virgula(c):
    assert c["implante_diametro"] == 4.1
    assert c["rosca_passo"] == 0.8
    assert c["haste_ccd"] == 135
    assert c["haste_offset"] == 38.3


def test_ler_cotas_ignora_linhas_sem_chave(tmp_path):
    f = tmp_path / "cotas.md"
    f.write_text("| chave | valor |\n|---|---|\n| a_b | 1,5 |\n| Texto | 2 |\n| c | x |\n", encoding="utf-8")
    assert cad.ler_cotas(f) == {"a_b": 1.5}


def test_eixo_colo_respeita_offset_ccd_e_colo(c):
    e = cad.eixo_colo(c)
    assert e["centro"][0] == pytest.approx(-c["haste_offset"])
    dx, dy = e["direcao"]
    # ângulo entre o colo e o eixo da haste (apontado para a ponta) é o cervicodiafisário
    assert math.degrees(math.acos(-dy)) == pytest.approx(c["haste_ccd"])
    assert math.dist(e["centro"], e["base"]) == pytest.approx(c["haste_colo"])


def test_contorno_haste_fechado_e_dentro_das_larguras(c):
    pts = cad.contorno_haste(c)
    assert pts[0] == pts[-1]
    ys = [y for _, y in pts]
    assert min(ys) == 0 and max(ys) == c["haste_comprimento"]
    assert max(x for x, _ in pts) <= c["haste_largura_ombro"] / 2


def test_perfil_implante_tem_diametros_das_cotas(c):
    p = cad.perfil_implante(c)
    assert max(r for r, _ in p) == pytest.approx(c["implante_diametro"] / 2)
    assert p[1][0] == pytest.approx(c["apice_nucleo"] / 2)
    assert p[2][1] == pytest.approx(c["parte_conica"])
    assert p[-2][0] == pytest.approx(c["plataforma_diametro"] / 2)
    assert p[-1][1] == pytest.approx(c["implante_comprimento"])


def test_perfil_rosca_tem_profundidade_e_cabe_no_passo(c):
    p = cad.perfil_rosca(c)
    assert max(r for r, _ in p) == pytest.approx(c["implante_diametro"] / 2)
    assert max(y for _, y in p) - min(y for _, y in p) < c["rosca_passo"]


def test_perfil_rosca_recusa_filete_maior_do_que_o_passo(c):
    with pytest.raises(ValueError):
        cad.perfil_rosca({**c, "rosca_passo": 0.2})


def test_pilar_e_coroa_ficam_acima_do_implante(c):
    L = c["implante_comprimento"]
    assert min(y for _, y in cad.perfil_pilar(c)) == pytest.approx(L)
    assert max(r for r, _ in cad.perfil_pilar(c)) == pytest.approx(c["pilar_diametro"] / 2)
    coroa = cad.perfil_coroa(c)
    assert min(y for _, y in coroa) == pytest.approx(L + c["pilar_altura_gengival"])
    assert max(r for r, _ in coroa) == pytest.approx(c["coroa_largura"] / 2)
