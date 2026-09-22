import pytest

from scpi_sim.tree import DuplicateParentError, InvalidMnemonicError, Node


def test_short() -> None:
    """short() returns the documented abbreviation, or the whole word if ≤ 4 chars."""
    list_long = ["VOLTage", "CURRent", "MEASure", "DO", "TAXI", "AUTO", "POWer"]

    expected_shorts = ["VOLT", "CURR", "MEAS", "DO", "TAXI", "AUTO", "POW"]

    actual_shorts = []
    for word in list_long:
        node = Node(word)
        actual_shorts.append(node.short())

    assert actual_shorts == expected_shorts


def test_long() -> None:
    """long() returns the fully spelled-out mnemonic, upper-cased."""
    list_long = ["VOLTage", "CURRent", "MEASure", "DO", "TAXI", "AUTO", "POWer"]

    expected_long = ["VOLTAGE", "CURRENT", "MEASURE", "DO", "TAXI", "AUTO", "POWER"]

    actual_long = []
    for word in list_long:
        node = Node(word)
        actual_long.append(node.long())

    assert actual_long == expected_long


def test_matches() -> None:
    """matches() accepts short/long spelling in any case, rejects near-misses."""
    list_long = ["VOLT", "VOLTAGE", "volt", "VoLtAgE", "VOLTAG", "VOL", "VOLTAGES"]
    expected_bool_list = [True, True, True, True, False, False, False]

    node = Node("VOLTage")

    # Just pass the entire list directly to the function!
    match_long = node.matches(list_long)

    assert match_long == expected_bool_list


def test_mnemonic() -> None:
    """A malformed mnemonic raises InvalidMnemonicError; a well-formed one doesn't."""
    with pytest.raises(InvalidMnemonicError):
        Node("voltage")
    with pytest.raises(InvalidMnemonicError):
        Node("VOLTAGe")
    with pytest.raises(InvalidMnemonicError):
        Node("Differentiate")
    Node("VOLTage")


def test_resolve() -> None:
    """resolve() matches directly, misses cleanly, and only skips optional children."""
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

    key_word_short = "NPLC"

    key_word_long = "VOLTAGE"

    key_word_miss = "NPLCycles"

    keyword_match = "VOLTage"

    keyword_block = "AC"

    list_test = [
        ac.resolve(key_word_short),
        meas.resolve(key_word_long),
        meas.resolve(key_word_miss),
        root.resolve(keyword_match),
        root.resolve(keyword_block),
    ]

    expected_list = [nplc, volt, None, volt_sense, None]

    assert list_test == expected_list


def test_parent() -> None:
    """A child claimed by a second parent is rejected and keeps its first parent."""
    nplc = Node("NPLCycles")
    ac = Node("AC", children={nplc.short(): nplc, nplc.long(): nplc})
    volt = Node("VOLTage", children={ac.short(): ac, ac.long(): ac})

    with pytest.raises(DuplicateParentError):
        Node("VOLTage", children={ac.short(): ac, ac.long(): ac})
    with pytest.raises(TypeError):
        Node("DC", parent=volt)  # type: ignore[call-arg]
    with pytest.raises(DuplicateParentError):
        a = Node("AC")
        b = Node("DC")
        Node("SENSe", children={"AC": a})
        Node("VOLTage", children={"DC": b, "AC": a})

    b = Node("DC")
    c = Node("MEASure", children={"DC": b})
    assert b.parent is c

    assert volt is ac.parent
    assert None is volt.parent

    volt_resolve = volt.resolve("ac")
    assert volt_resolve is not None
    assert volt is volt_resolve.parent

    ac_result = ac.resolve("NPLCycles")
    assert ac_result is not None
    assert ac is ac_result.parent
