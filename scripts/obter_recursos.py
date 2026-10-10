"""Descarrega os recursos externos: malhas anatómicas (BodyParts3D), HDRI e texturas (Poly Haven) e o resumo do
Materials Project (dados abertos no AWS, CC BY 4.0, sem chave) para o funil de triagem.

Uso:
    python scripts/obter_recursos.py

Os ficheiros ficam fora do repositório, em recursos (pasta definida em RECURSOS). Fontes, licenças e
linhas de atribuição: design/cad/fontes_anatomicas.md.
"""

from __future__ import annotations

import io
import json
import re
import urllib.request
import zipfile
from pathlib import Path

RECURSOS = Path(r"recursos")
BP3D = "https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/"
# ficheiro de elementos do BodyParts3D (FJ...) e pacote onde está
MALHAS = {
    "FJ3152": ("anca direita (right hip bone, FMA16586)", "partof_BP3D_4.0_obj_99.zip"),
    "FJ3365": ("fémur direito (right femur, FMA24474)", "partof_BP3D_4.0_obj_99.zip"),
    "FJ3289": ("mandíbula (mandible, FMA52748)", "partof_BP3D_4.0_obj_99.zip"),
    "FJ1268": ("1.º molar inferior direito (FMA55705)", "isa_BP3D_4.0_obj_99.zip"),
    "FJ1269": ("1.º pré-molar inferior direito (FMA55694)", "isa_BP3D_4.0_obj_99.zip"),
    "FJ1270": ("2.º molar inferior direito (FMA55706)", "isa_BP3D_4.0_obj_99.zip"),
}
POLYHAVEN = {
    "hdris": {"studio_small_09": ["hdr"]},
    "textures": {"metal_plate": ["Rough", "nor_gl"], "clay_plaster": ["Rough", "nor_gl"]},
}


MP_S3 = "https://materialsproject-build.s3.amazonaws.com/"
MP_VERSAO = "2026-09-28"  # versão dos dados usada no funil (scripts/funil.py)


def chaves_s3(xml: str) -> list[str]:
    """Lê os nomes dos ficheiros (Key) numa listagem de um balde S3 (resposta XML do list-type=2)."""
    return re.findall(r"<Key>([^<]+)</Key>", xml)


def ficheiros_polyhaven(info: dict, tipo: str, mapas: list[str], resolucao: str = "2k") -> list[tuple[str, str]]:
    """Escolhe os ficheiros a descarregar na resposta da API da Poly Haven (api.polyhaven.com/files/<id>).

    Em linguagem simples: para um HDRI fica com o .hdr na resolução pedida; para uma textura fica com cada mapa
    pedido (por exemplo rugosidade e normais) em JPG. Devolve pares (nome do ficheiro, URL).
    """
    saida = []
    if tipo == "hdris":
        f = info["hdri"][resolucao]["hdr"]
        saida.append((Path(f["url"]).name, f["url"]))
    else:
        for mapa in mapas:
            f = info[mapa][resolucao]["jpg"]
            saida.append((Path(f["url"]).name, f["url"]))
    return saida


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "biomat-mcdm/1.0"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read()


def obter_malhas():
    pasta = RECURSOS / "bodyparts3d" / "obj"
    pasta.mkdir(parents=True, exist_ok=True)
    por_pacote: dict[str, list[str]] = {}
    for fj, (_, pacote) in MALHAS.items():
        if not (pasta / f"{fj}.obj").exists():
            por_pacote.setdefault(pacote, []).append(fj)
    for pacote, fjs in por_pacote.items():
        local = RECURSOS / "bodyparts3d" / pacote
        if not local.exists():
            local.write_bytes(_get(BP3D + pacote))
        with zipfile.ZipFile(local) as z:
            for nome in z.namelist():
                if Path(nome).stem in fjs:
                    (pasta / Path(nome).name).write_bytes(z.read(nome))
                    print("malha", Path(nome).name)


def obter_polyhaven():
    for tipo, itens in POLYHAVEN.items():
        for ident, mapas in itens.items():
            pasta = RECURSOS / "polyhaven" / ident
            pasta.mkdir(parents=True, exist_ok=True)
            info = json.load(io.BytesIO(_get(f"https://api.polyhaven.com/files/{ident}")))
            for nome, url in ficheiros_polyhaven(info, tipo, mapas):
                if not (pasta / nome).exists():
                    (pasta / nome).write_bytes(_get(url))
                    print("poly haven", ident, nome)


def obter_materials_project(colecoes=("summary",), versao: str = MP_VERSAO):
    """Descarrega cada coleção do Materials Project (um ficheiro parquet por coleção e versão)."""
    pasta = RECURSOS / "materials_project"
    pasta.mkdir(parents=True, exist_ok=True)
    for c in colecoes:
        local = pasta / f"{c}_{versao}.parquet"
        if local.exists():
            continue
        prefixo = f"collections/{c}/version={versao}/"
        chaves = [k for k in chaves_s3(_get(f"{MP_S3}?list-type=2&prefix={prefixo}").decode()) if k.endswith(".parquet")]
        if len(chaves) != 1:
            raise RuntimeError(f"esperava um parquet em {prefixo}, encontrei {len(chaves)}")
        local.write_bytes(_get(MP_S3 + chaves[0]))
        print("materials project", local.name)


if __name__ == "__main__":
    obter_malhas()
    obter_polyhaven()
    obter_materials_project()
