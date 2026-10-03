"""Tests for walking colon-separated headers through the command tree."""

import pytest

from scpi_sim.parser import ParsedUnit, helper_parser, split_unit, walk, walk_message
from scpi_sim.tree import Node

nplc = Node("NPLCycles")
dc = Node("DC", children={nplc.short(): nplc, nplc.long(): nplc}, queryable=False)
volt_sense = Node(
    "VOLTage", children={dc.short(): dc, dc.long(): dc}, queryable=False, settable=False
)

clear = Node("CLEar", queryable=False)

sense = Node(
    "SENSe",
    optional=True,
    children={
        volt_sense.short(): volt_sense,
        volt_sense.long(): volt_sense,
        clear.short(): clear,
        clear.long(): clear,
    },
    settable=False,
    queryable=False,
)

rang_dc = Node("RANGe")
nplc_dc = Node("NPLCycles")

rang_ac = Node("RANGe")
nplc_ac = Node("NPLCycles")

ac_v = Node(
    "AC",
    children={
        nplc_ac.short(): nplc_ac,
        nplc_ac.long(): nplc_ac,
        rang_ac.short(): rang_ac,
        rang_ac.long(): rang_ac,
    },
    settable=False,
)
dc_v = Node(
    "DC",
    children={
        nplc_dc.short(): nplc_dc,
        nplc_dc.long(): nplc_dc,
        rang_dc.short(): rang_dc,
        rang_dc.long(): rang_dc,
    },
    settable=False,
)
volt = Node(
    "VOLTage",
    children={
        ac_v.short(): ac_v,
        ac_v.long(): ac_v,
        dc_v.short(): dc_v,
        dc_v.long(): dc_v,
    },
    settable=False,
    queryable=False,
)
meas = Node(
    "MEASure",
    children={volt.short(): volt, volt.long(): volt},
    settable=False,
    queryable=False,
)

root = Node(
    "ROOT",
    children={
        sense.short(): sense,
        sense.long(): sense,
        meas.short(): meas,
        meas.long(): meas,
    },
    settable=False,
    queryable=False,
)


@pytest.mark.parametrize(
    ("start", "header", "expected_landed", "expected_path"),
    [
        (root, ":MEAS:VOLT:AC:NPLC", nplc_ac, ac_v),
        (root, "VOLT", volt_sense, root),
        (root, ":SENS:VOLT:DC", dc, volt_sense),
        (root, "MEAS:VOLTAGE:AC", ac_v, volt),
        (root, "meas:volt:ac", ac_v, volt),
        (volt, "AC:NPLC", nplc_ac, ac_v),
        (volt, ":MEAS:VOLT:AC:NPLC", nplc_ac, ac_v),
        (root, "VOLT:DC", dc, volt_sense),
        (ac_v, "NPLC", nplc_ac, ac_v),
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
        (
            "MEAS:VOLT:AC:RANG;NPLC",
            [ParsedUnit(rang_ac, False, ""), ParsedUnit(nplc_ac, False, "")],
        ),
        (
            "MEAS:VOLT:AC:RANG;:MEAS:VOLT:DC:NPLC",
            [ParsedUnit(rang_ac, False, ""), ParsedUnit(nplc_dc, False, "")],
        ),
        ("MEAS:VOLT:AC?;NPLC", [ParsedUnit(ac_v, True, ""), None]),
        (
            "CLE;MEAS:VOLT:AC?",
            [ParsedUnit(clear, False, ""), ParsedUnit(ac_v, True, "")],
        ),
        ("VOLT:DC;XYZ;NPLC", [ParsedUnit(dc, False, ""), None]),
        ("XYZ;MEAS", [None]),
        ("MEAS:VOLT:AC:RANG", [ParsedUnit(rang_ac, False, "")]),
        ("MEAS:VOLT:AC:RANG;", [ParsedUnit(rang_ac, False, ""), None]),
        (
            "MEAS:VOLT:AC:RANG; NPLC",
            [ParsedUnit(rang_ac, False, ""), ParsedUnit(nplc_ac, False, "")],
        ),
        ("MEAS: VOLT:AC", [None]),
        (
            "MEAS:VOLT:AC:RANG;\tNPLC",
            [ParsedUnit(rang_ac, False, ""), ParsedUnit(nplc_ac, False, "")],
        ),
        ("MEAS:VOLT:AC:RANG\n", [ParsedUnit(rang_ac, False, "")]),
        ("MEAS:VOLT:DC? 10,0.001", [ParsedUnit(dc_v, True, "10,0.001")]),
        (
            "MEAS:VOLT:AC:RANG 10;NPLC?",
            [ParsedUnit(rang_ac, False, "10"), ParsedUnit(nplc_ac, True, "")],
        ),
        ("MEAS:VOLT:AC:RANG;VOLT?:DC;NPLC", [ParsedUnit(rang_ac, False, ""), None]),
        ("CLE?", [None]),
        ("SENS", [None]),
        ("SENS:VOLT:DC:NPLC;:CLE?", [ParsedUnit(nplc, False, ""), None]),
        (";;", [None]),
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
        "standard_message_query",
        "path_parameter_query",
        "bad_query",
        "query_on_command_only",
        "bare_sense",
        "bad_form",
        "semicolon_error",
        "empty_message",
    ],
)
def test_walk_message(message: str, expected: list[ParsedUnit | None]) -> None:
    """Each unit gives its node (by identity), query flag and parameter text.

    A failed unit appears as None and ends the list; lengths must match exactly.
    """
    test_result = walk_message(root, message)
    for x, y in zip(test_result, expected, strict=True):
        if y is None:
            assert x is None
        else:
            assert x is not None
            assert x.node is y.node
            assert x.is_query == y.is_query
            assert x.parameters == y.parameters


@pytest.mark.parametrize(
    ("entry", "expectation"),
    [
        ("NPLC", ("NPLC", False, "")),
        ("NPLC 10", ("NPLC", False, "10")),
        ("NPLC?", ("NPLC", True, "")),
        ("MEAS:VOLT:DC? 10,0.001", ("MEAS:VOLT:DC", True, "10,0.001")),
        (" MEAS:VOLT:DC? 10,0.001 ", ("MEAS:VOLT:DC", True, "10,0.001")),
        ("MEAS:VOLT:DC?\t10,0.001", ("MEAS:VOLT:DC", True, "10,0.001")),
        ("VOLT?:DC", None),
        ("MEAS: VOLT", ("MEAS:", False, "VOLT")),
        ("MEAS:", ("MEAS:", False, "")),
        ("  ", None),
        ("NPLC\t10", ("NPLC", False, "10")),
        ('DISP:DATA "Hello, world!"', ("DISP:DATA", False, '"Hello, world!"')),
        ('DISP:TEXT "Ready?"', ("DISP:TEXT", False, '"Ready?"')),
        ("NPLC 10 ", ("NPLC", False, "10")),
    ],
    ids=[
        "only-header",
        "header-and-parameter",
        "header-and-query",
        "header-query-parameter",
        "multiple-whitespaces",
        "tab-query",
        "query-wrong-place",
        "split-in-header",
        "broken-header",
        "empty-str",
        "tab-no-query",
        "spaces-inside-parameter",
        "?-inside-parameter",
        "trailing-whitespace",
    ],
)
def test_split_unit(entry: str, expectation: tuple[str, bool, str] | None) -> None:
    test_output = split_unit(entry)
    assert test_output == expectation


@pytest.mark.parametrize(
    ("settable", "queryable", "is_query", "expected"),
    [
        (True, True, False, True),
        (True, True, True, True),
        (True, False, False, True),
        (True, False, True, False),
        (False, True, False, False),
        (False, True, True, True),
        (False, False, False, False),
        (False, False, True, False),
    ],
    ids=[
        "command-on-both",
        "query-on-both",
        "command-on-command-only",
        "query-on-command-only",
        "command-on-query-only",
        "query-on-query-only",
        "command-on-path",
        "query-on-path",
    ],
)
def test_helper(
    settable: bool, queryable: bool, is_query: bool, expected: bool
) -> None:
    """Every flag combination in both forms: query needs queryable, command settable.

    Each row builds its own node, so the flags tested are exactly the row's flags.
    """
    node = Node("NPLCycles", settable=settable, queryable=queryable)
    result_bool = helper_parser(node, is_query)
    assert result_bool == expected
