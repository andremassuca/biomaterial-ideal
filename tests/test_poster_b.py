"""Testes de scripts/poster_b.py (sem Chrome: dados, HTML e redução do PDF)."""
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


pb = _carregar("poster_b")


def test_render_prefere_a_primeira_pasta(tmp_path):
    a, b = tmp_path / "final", tmp_path / "rapida"
    a.mkdir(), b.mkdir()
    (b / "anca_transparente.png").write_bytes(b"x")
    assert pb.render("anca", [a, b]) == b / "anca_transparente.png"
    (a / "anca_transparente.png").write_bytes(b"x")
    assert pb.render("anca", [a, b]) == a / "anca_transparente.png"
    with pytest.raises(FileNotFoundError):
        pb.render("stent", [a, b])


def test_larguras_funil_decrescem_com_minimo():
    w = pb.larguras_funil([271325, 6479, 31, 5])
    assert w[0] == pytest.approx(1.0)
    assert all(x > y for x, y in zip(w, w[1:])) and min(w) >= 0.18


def test_degraus_e_numero():
    d = pb.degraus_funil({"mp": 271325, "nivel2": 6479, "base": 31, "final": 5})
    assert [n for n, _ in d] == [271325, 6479, 31, 5]
    assert pb.numero(271325) == "271 325" and pb.numero(5) == "5"


def test_html_poster_tem_os_tres_passos_numeros_e_aviso():
    h = pb.html_poster()
    fu = pb.ab.funil()
    for s in ("Que material pôr dentro do corpo?", "Como decidimos", "O que descobrimos", pb.ab.AVISO,
              f"Orientador: {pb.ab.ORIENTADOR}", pb.numero(fu["mp"]), "Empate técnico", "@page { size: 420mm 594mm;"):
        assert s in h, s
    assert "—" not in h and "–" not in h  # sem travessões
    assert "Código QR do repositório público (a criar)" in h  # sem URL fica o marcador


def test_reduzir_e_paginas(tmp_path):
    import pymupdf
    a2 = tmp_path / "a2.pdf"
    d = pymupdf.open()
    d.new_page(width=420 * 72 / 25.4, height=594 * 72 / 25.4).insert_text((100, 100), "teste")
    d.save(a2)
    a3 = pb.reduzir(a2, tmp_path / "a3.pdf")
    r = pymupdf.open(a3)[0].rect
    assert round(r.width / 72 * 25.4) == 297 and round(r.height / 72 * 25.4) == 420
    assert pb.paginas(a3) == 1
