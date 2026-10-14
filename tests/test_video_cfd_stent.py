"""Funções puras do vídeo da CFD do stent (formatação, tempos, séries e percentagem abaixo do limiar)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import video_cfd_stent as v  # noqa: E402


def test_fmt_pt_usa_virgula_e_sinal_menos():
    assert v.fmt_pt(0.508, 3) == "0,508"
    assert v.fmt_pt(-1.5, 1) == "−1,5"


def test_velocidade_ignora_o_sinal_do_caudal():
    assert np.isclose(v.velocidade_cm_s(-4.4e-8, 4.4e-7), 10.0)
    assert np.allclose(v.velocidade_cm_s(np.array([-1.0, 1.0]), 2.0), [50.0, 50.0])


def test_fase_do_ciclo_vai_de_0_a_100_e_nao_sai_do_intervalo():
    assert v.fase_do_ciclo(v.T_INICIO) == 0.0
    assert np.isclose(v.fase_do_ciclo(v.T_INICIO + v.PERIODO / 2), 50.0)
    assert v.fase_do_ciclo(v.T_FIM + 1) == 100.0
    assert v.fase_do_ciclo(0.0) == 0.0


def test_tempo_do_quadro_espera_varre_e_espera():
    assert v.tempo_do_quadro(0) == v.T_INICIO
    assert v.tempo_do_quadro(int(v.S_INICIO * v.FPS)) == v.T_INICIO
    meio = int((v.S_INICIO + v.S_VARRIMENTO / 2) * v.FPS)
    assert np.isclose(v.tempo_do_quadro(meio), v.T_INICIO + v.PERIODO / 2)
    assert v.tempo_do_quadro(v.n_quadros() - 1) == v.T_FIM
    assert 10 * v.FPS <= v.n_quadros() <= 20 * v.FPS  # duração entre 10 e 20 s


def test_recortar_e_valor_em():
    t = np.linspace(0, 3, 301)
    y = 2 * t
    tr, yr = v.recortar(t, y, 1.0, 2.0)
    assert tr[0] == 1.0 and tr[-1] == 2.0 and len(tr) == 101
    assert np.isclose(v.valor_em(tr, yr, 1.505), 3.01)
    assert np.isclose(v.valor_em(tr, yr, 5.0), yr[-1])  # fora da série fica no extremo, não extrapola


def test_percentagem_abaixo_pesa_pela_area():
    tau = np.array([0.1, 0.3, 0.5, 0.9])
    area = np.array([1.0, 1.0, 2.0, 4.0])
    assert np.isclose(v.percentagem_abaixo(tau, area, 0.4), 25.0)  # 2 de 8
    assert v.percentagem_abaixo(tau, area, 0.0) == 0.0
    assert np.isclose(v.media_ponderada(tau, area), (0.1 + 0.3 + 1.0 + 3.6) / 8)


def test_texto_do_instante_tem_tempo_e_fase():
    assert v.texto_instante(v.T_INICIO + v.PERIODO / 2) == "t = 1,59 s (fase 50 % do 2.º ciclo)"
