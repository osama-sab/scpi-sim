import scpi_driver
import scpi_sim

def test_check():
    assert scpi_sim, "scpi_sim not imported"
    assert scpi_driver, "scpi_driver not imported"
