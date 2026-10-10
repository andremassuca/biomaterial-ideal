import matplotlib as _mpl
import pytest as _pytest


@_pytest.fixture(autouse=True)
def repor_rcparams():
    """Repõe as definições do matplotlib depois de cada teste (o estilo dos gráficos muda-as globalmente)."""
    guardado = _mpl.rcParams.copy()
    yield
    _mpl.rcParams.update(guardado)
