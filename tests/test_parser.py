"""Tests for walking colon-separated headers through the command tree."""

from scpi_sim.parser import walk
from scpi_sim.tree import Node

dc = Node("DC")
volt_sense = Node("VOLTage", children={dc.short(): dc, dc.long(): dc})
sense = Node(
    "SENSe",
    optional=True,
    children={volt_sense.short(): volt_sense, volt_sense.long(): volt_sense},
)

nplc = Node("NPLCycles")
ac = Node("AC", children={nplc.short(): nplc, nplc.long(): nplc})
volt = Node("VOLTage", children={ac.short(): ac, ac.long(): ac})
meas = Node("MEASure", children={volt.short(): volt, volt.long(): volt})

root = Node(
    "ROOT",
    children={
        sense.short(): sense,
        sense.long(): sense,
        meas.short(): meas,
        meas.long(): meas,
    },
)


def test_full_header_lands_on_node() -> None:
    """A complete header resolves keyword by keyword to the right node."""
    assert walk(root, meas, ":MEAS:VOLT:AC:NPLC") is nplc
    assert walk(root, root, ":SENS:VOLT:DC") is dc


def test_short_and_long_spellings_mix() -> None:
    """Short and long forms can be mixed within one header."""
    assert walk(root, root, "MEAS:VOLTAGE:AC") is ac


def test_keywords_are_case_insensitive() -> None:
    """Lowercase keywords resolve the same as uppercase ones."""
    assert walk(root, root, "meas:volt:ac") is ac


def test_relative_header_starts_from_current() -> None:
    """Without a leading colon, the walk starts from `current`, not `root`."""
    assert walk(root, volt, "AC:NPLC") is nplc


def test_leading_colon_resets_to_root() -> None:
    """A leading colon ignores `current`; the same header without one fails."""
    assert walk(root, volt, ":MEAS:VOLT:AC:NPLC") is nplc
    assert walk(root, volt, "MEAS:VOLT:AC:NPLC") is None


def test_optional_keyword_can_be_skipped() -> None:
    """An optional keyword (SENSe) can be left out of the header."""
    assert walk(root, root, "VOLT:DC") is dc


def test_required_keyword_cannot_be_skipped() -> None:
    """A required keyword (MEASure) can't be left out of the header."""
    assert walk(root, root, "VOLT:AC") is None


def test_missing_keyword_returns_none() -> None:
    """A keyword that doesn't exist, first or later, gives None."""
    assert walk(root, root, "MEASu:VOLT:AC") is None
    assert walk(root, root, "MEAS:VOLT:ACurrent") is None


def test_malformed_headers_return_none() -> None:
    """Empty keywords, an empty header, and a bare colon all give None."""
    assert walk(root, root, "MEAS::VOLT") is None
    assert walk(root, root, "MEAS:VOLT:") is None
    assert walk(root, root, "") is None
    assert walk(root, root, ":") is None
