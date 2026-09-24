"""Tests for walking colon-separated headers through the command tree."""

import pytest

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


@pytest.mark.parametrize(
    ("start", "header", "expected_landed", "expected_path"),
    [
        (root, ":MEAS:VOLT:AC:NPLC", nplc, ac),
        (root, "VOLT", volt_sense, root),
        (root, ":SENS:VOLT:DC", dc, volt_sense),
        (root, "MEAS:VOLTAGE:AC", ac, volt),
        (root, "meas:volt:ac", ac, volt),
        (volt, "AC:NPLC", nplc, ac),
        (volt, ":MEAS:VOLT:AC:NPLC", nplc, ac),
        (root, "VOLT:DC", dc, volt_sense),
        (ac, "NPLC", nplc, ac),
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
