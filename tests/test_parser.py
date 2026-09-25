"""Tests for walking colon-separated headers through the command tree."""

import pytest

from scpi_sim.parser import walk, walk_message
from scpi_sim.tree import Node

dc = Node("DC")
volt_sense = Node("VOLTage", children={dc.short(): dc, dc.long(): dc})
sense = Node(
    "SENSe",
    optional=True,
    children={volt_sense.short(): volt_sense, volt_sense.long(): volt_sense},
)

rang_dc = Node("RANGe")
nplc_dc = Node("NPLCycles")

rang_ac = Node("RANGe")
nplc_ac = Node("NPLCycles")

ac = Node(
    "AC",
    children={
        nplc_ac.short(): nplc_ac,
        nplc_ac.long(): nplc_ac,
        rang_ac.short(): rang_ac,
        rang_ac.long(): rang_ac,
    },
)
dc_v = Node(
    "DC",
    children={
        nplc_dc.short(): nplc_dc,
        nplc_dc.long(): nplc_dc,
        rang_dc.short(): rang_dc,
        rang_dc.long(): rang_dc,
    },
)
volt = Node(
    "VOLTage",
    children={ac.short(): ac, ac.long(): ac, dc_v.short(): dc_v, dc_v.long(): dc_v},
)
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


@pytest.mark.parametrize(
    ("start", "header", "expected_landed", "expected_path"),
    [
        (root, ":MEAS:VOLT:AC:NPLC", nplc_ac, ac),
        (root, "VOLT", volt_sense, root),
        (root, ":SENS:VOLT:DC", dc, volt_sense),
        (root, "MEAS:VOLTAGE:AC", ac, volt),
        (root, "meas:volt:ac", ac, volt),
        (volt, "AC:NPLC", nplc_ac, ac),
        (volt, ":MEAS:VOLT:AC:NPLC", nplc_ac, ac),
        (root, "VOLT:DC", dc, volt_sense),
        (ac, "NPLC", nplc_ac, ac),
        (root, ":SENS", sense, root),
    ],
    ids=[
        "full-header",
        "optional-skip",
        "full-header-through-optional",
        "short-and-long-mixed",
        "case-insensitive",
        "relative-from-current",
        "leading-colon-ignores-current",
        "optional-keyword-skipped",
        "single-relative",
        "single-leading-colon",
    ],
)
def test_walk_lands_and_keeps_route(
    start: Node, header: str, expected_landed: Node, expected_path: Node
) -> None:
    """A header lands on its node; the path is the node before its last keyword."""
    outcome = walk(root, start, header)
    assert outcome is not None
    landed, path = outcome
    assert landed is expected_landed
    assert path is expected_path


@pytest.mark.parametrize(
    ("start", "header"),
    [
        (volt, "MEAS:VOLT:AC:NPLC"),
        (root, "VOLT:AC"),
        (root, "MEASu:VOLT:AC"),
        (root, "MEAS:VOLT:ACurrent"),
        (root, "MEAS::VOLT"),
        (root, "MEAS:VOLT:"),
        (root, ""),
        (root, ":"),
        (root, "MEAS:XYZ"),
    ],
    ids=[
        "no-leading-colon-from-wrong-node",
        "required-keyword-skipped",
        "first-keyword-missing",
        "later-keyword-missing",
        "empty-keyword-double-colon",
        "empty-keyword-trailing-colon",
        "empty-header",
        "bare-colon",
        "non-existing-node",
    ],
)
def test_walk_fails_with_none(start: Node, header: str) -> None:
    """A header that can't be resolved gives None, never a partial result."""
    assert walk(root, start, header) is None


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("MEAS:VOLT:AC:RANG;NPLC", [rang_ac, nplc_ac]),
        ("MEAS:VOLT:AC:RANG;:MEAS:VOLT:DC:NPLC", [rang_ac, nplc_dc]),
        ("MEAS:VOLT:AC;NPLC", [ac, None]),
        ("VOLT;MEAS:VOLT:AC", [volt_sense, ac]),
        ("MEAS:VOLT:AC:RANG;XYZ;NPLC", [rang_ac, None]),
        ("XYZ;MEAS", [None]),
        ("MEAS:VOLT:AC:RANG", [rang_ac]),
        ("MEAS:VOLT:AC:RANG;", [rang_ac, None]),
        ("MEAS:VOLT:AC:RANG; NPLC", [rang_ac, nplc_ac]),
        ("MEAS: VOLT:AC", [None]),
        ("MEAS:VOLT:AC:RANG;\tNPLC", [rang_ac, nplc_ac]),
        ("MEAS:VOLT:AC:RANG\n", [rang_ac]),
        ("", [None]),
    ],
    ids=[
        "path-carries-across-units",
        "leading-colon-middle",
        "gotcha_one",
        "route_at_message_level",
        "first_failure",
        "first_unit_fail",
        "no_semicolon",
        "trailing_semicolon",
        "spaced_semicolon",
        "no_whitespace_inside_header",
        "whitespace_after_semicolon",
        "newline_terminator",
        "empty_message",
    ],
)
def test_walk_message_is_none(message: str, expected: list[Node | None]) -> None:
    test_result = walk_message(root, message)
    assert all(x is y for x, y in zip(test_result, expected, strict=True))
