"""Títulos dos mapas da CFD do stent: pela espessura do strut, não pela liga."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import cfd_stent as cs  # noqa: E402


def test_rotulo_espessura_fala_da_espessura_e_nao_da_liga():
    assert cs.rotulo_espessura("Pt-Cr", 79.0) == "Strut fino, 79 µm (DES atual)"
    assert cs.rotulo_espessura("316L", 135.0) == "Strut grosso, 135 µm (1.ª geração)"
    for t in (cs.rotulo_espessura("Pt-Cr", 79.0), cs.rotulo_espessura("316L", 135.0)):
        assert "Pt-Cr" not in t and "316L" not in t
