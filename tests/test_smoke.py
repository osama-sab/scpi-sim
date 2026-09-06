import importlib.metadata

import scpi_sim


def test_version() -> None:
    assert importlib.metadata.version("scpi-sim") == scpi_sim.__version__
