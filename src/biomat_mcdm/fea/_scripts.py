"""Acesso às funções de geometria dos scripts dos renders (scripts/geometria_3d.py e scripts/cad_solidworks.py).

Em linguagem simples: os renders já sabem pôr a haste no fémur; para a FEA usar exatamente a mesma posição,
carregam-se esses dois scripts pelo caminho (não fazem parte do pacote) em vez de copiar o código.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"


def _carregar(nome: str):
    spec = importlib.util.spec_from_file_location(f"_fea_{nome}", SCRIPTS / f"{nome}.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


geo = _carregar("geometria_3d")
cad = _carregar("cad_solidworks")
