"""Tests for walking colon-separated headers through the command tree."""

import pytest

from scpi_sim.parser import ParsedUnit, helper_parser, split_unit, walk, walk_message
from scpi_sim.tree import Node

nplc = Node("NPLCycles")
dc = Node("DC", children=[nplc], queryable=False)
volt_sense = Node("VOLTage", children=[dc], queryable=False, settable=False)

clear = Node("CLEar", queryable=False)

sense = Node(
    "SENSe",
    optional=True,
    children=[
        volt_sense,
        clear,
    ],
    settable=False,
    queryable=False,
)

rang_dc = Node("RANGe")
nplc_dc = Node("NPLCycles")

rang_ac = Node("RANGe")
nplc_ac = Node("NPLCycles")

ac_v = Node(
    "AC",
    children=[
        nplc_ac,
        rang_ac,
    ],
    settable=False,
)
dc_v = Node(
    "DC",
    children=[
        nplc_dc,
        rang_dc,
    ],
    settable=False,
)
volt = Node(
    "VOLTage",
    children=[
        ac_v,
        dc_v,
    ],
    settable=False,
    queryable=False,
)
meas = Node(
    "MEASure",
    children=[volt],
    settable=False,
    queryable=False,
)

root = Node(
    "ROOT",
    children=[
        sense,
        meas,
    ],
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
    test_result = walk_message(root, message, {})
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


leaf = Node("LEAF")
inner = Node("INNer", optional=True, children=[leaf])
outer = Node(
    "OUTer",
    optional=True,
    children=[inner],
)
origin = Node("ORIGin", children=[outer])


@pytest.mark.parametrize(
    ("start", "header", "expected_landed", "expected_path"),
    [
        (origin, "OUTER:INNER:LEAF", leaf, inner),
        (origin, "OUTER:LEAF", leaf, outer),
        (origin, "INNER:LEAF", leaf, inner),
        (origin, "LEAF", leaf, origin),
    ],
    ids=[
        "full_header",
        "outer_header",
        "inner_header",
        "both_skipped",
    ],
)
def test_nested_optional_keywords(
    start: Node, header: str, expected_landed: Node, expected_path: Node
) -> None:
    """Either or both of two nested optional nodes may be skipped.

    The path is still the node before the last typed keyword: skipped default
    nodes don't alter it (SCPI-99 section 6.2.4), so ``LEAF`` alone leaves it
    at the start.
    """
    outcome = walk(origin, start, header)
    assert outcome is not None
    current, path = outcome
    assert path is expected_path
    assert current is expected_landed


@pytest.mark.parametrize(
    ("outer_optional", "inner_optional", "header"),
    [
        (True, False, "OUTER:LEAF"),
        (False, True, "INNER:LEAF"),
    ],
    ids=[
        "outer_optional",
        "inner_optional",
    ],
)
def test_nested_optional_negative(
    outer_optional: bool, inner_optional: bool, header: str
) -> None:
    """Skipping a required node in a nested chain fails, at either level.

    Each row is the all-optional tree with exactly one node made required,
    and its header skips that node, so only the optional flag can explain
    the failure. Each row builds its own tree: one tree can't hold both
    flags, and a node can't have two parents.
    """
    leaf = Node("LEAF")
    inner = Node(
        "INNer",
        optional=inner_optional,
        children=[leaf],
    )
    outer = Node(
        "OUTer",
        optional=outer_optional,
        children=[
            inner,
        ],
    )
    origin = Node("ORIGin", children=[outer])
    outcome = walk(origin, origin, header)
    assert outcome is None


cls = Node("CLS", queryable=False)
opc = Node("OPC", queryable=True)
ese = Node("ESE", settable=True)
dc_curr = Node("DC")
ac_curr = Node("AC")
current_src = Node("CURRent", children=[dc_curr, ac_curr])
source = Node("SOURce", children=[current_src])


@pytest.mark.parametrize(
    ("message", "result"),
    [
        (
            "CURR:DC 10;*CLS;AC",
            [
                ParsedUnit(dc_curr, False, "10"),
                ParsedUnit(cls, False, ""),
                ParsedUnit(ac_curr, False, ""),
            ],
        ),
        (
            "*CLS",
            [ParsedUnit(cls, False, "")],
        ),
        (
            "*OPC?",
            [ParsedUnit(opc, True, "")],
        ),
        (
            "*ESE 10",
            [ParsedUnit(ese, False, "10")],
        ),
        ("*CLS?", [None]),
        (
            "CURR:DC;*RST;AC",
            [ParsedUnit(dc_curr, False, ""), None],
        ),
        (
            "*cls",
            [ParsedUnit(cls, False, "")],
        ),
    ],
    ids=[
        "common-command-between-paths",
        "common-command-only",
        "common-command-query",
        "common-command-parameter",
        "non-queryable-query-common-command",
        "non-existing-command",
        "lower-case-common-command",
    ],
)
def test_common_commands(message: str, result: list[ParsedUnit | None]) -> None:
    assert (
        walk_message(source, message, {"*OPC": opc, "*CLS": cls, "*ESE": ese}) == result
    )


def test_path_per_connection_state() -> None:
    message_one = walk_message(root, "MEAS:VOLT:AC:NPLC", {})
    message_two = walk_message(root, "RANGe", {})
    assert message_one == [ParsedUnit(nplc_ac, False, "")]
    assert message_two == [None]
