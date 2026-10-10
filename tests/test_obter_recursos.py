"""Testes de scripts/obter_recursos.py (sem rede; o script carrega-se pelo caminho)."""

import importlib.util
from pathlib import Path

CAMINHO = Path(__file__).resolve().parents[1] / "scripts" / "obter_recursos.py"
spec = importlib.util.spec_from_file_location("obter_recursos", CAMINHO)
rec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rec)


def test_hdri_escolhe_o_hdr_na_resolucao_pedida():
    info = {"hdri": {"2k": {"hdr": {"url": "https://x/HDRIs/hdr/2k/estudio_2k.hdr"}},
                     "4k": {"hdr": {"url": "https://x/HDRIs/hdr/4k/estudio_4k.hdr"}}}}
    assert rec.ficheiros_polyhaven(info, "hdris", []) == [("estudio_2k.hdr", "https://x/HDRIs/hdr/2k/estudio_2k.hdr")]
    assert rec.ficheiros_polyhaven(info, "hdris", [], "4k")[0][0] == "estudio_4k.hdr"


def test_textura_escolhe_cada_mapa_em_jpg():
    info = {m: {"2k": {"jpg": {"url": f"https://x/{m}_2k.jpg"}, "png": {"url": "nao"}}} for m in ("Rough", "nor_gl", "Diffuse")}
    saida = rec.ficheiros_polyhaven(info, "textures", ["Rough", "nor_gl"])
    assert saida == [("Rough_2k.jpg", "https://x/Rough_2k.jpg"), ("nor_gl_2k.jpg", "https://x/nor_gl_2k.jpg")]


def test_malhas_tem_anca_femur_mandibula_e_molar():
    assert {"FJ3152", "FJ3365", "FJ3289", "FJ1268"} <= set(rec.MALHAS)


def test_chaves_s3_le_os_ficheiros_da_listagem():
    xml = ("<ListBucketResult><Contents><Key>collections/summary/version=v/part-0.zstd.parquet</Key>"
           "<Size>10</Size></Contents><Contents><Key>collections/summary/version=v/_SUCCESS</Key></Contents>"
           "</ListBucketResult>")
    assert rec.chaves_s3(xml) == ["collections/summary/version=v/part-0.zstd.parquet",
                                  "collections/summary/version=v/_SUCCESS"]
    assert rec.chaves_s3("<ListBucketResult/>") == []
