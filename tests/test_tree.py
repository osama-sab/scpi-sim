from scpi_sim.tree import Node


def test_short() -> None:
    list_long = ["VOLTage", "CURRent", "MEASure", "DO", "TAXI", "AUTO", "POWer"]

    expected_shorts = ["VOLT", "CURR", "MEAS", "DO", "TAXI", "AUTO", "POW"]

    actual_shorts = []
    for word in list_long:
        node = Node(word)
        actual_shorts.append(node.short())

    assert actual_shorts == expected_shorts


def test_long() -> None:
    list_long = ["VOLTage", "CURRent", "MEASure", "DO", "TAXI", "AUTO", "POWer"]

    expected_long = ["VOLTAGE", "CURRENT", "MEASURE", "DO", "TAXI", "AUTO", "POWER"]

    actual_long = []
    for word in list_long:
        node = Node(word)
        actual_long.append(node.long())

    assert actual_long == expected_long


def test_matches() -> None:
    list_long = ["VOLT", "VOLTAGE", "volt", "VoLtAgE", "VOLTAG", "VOL", "VOLTAGES"]
    expected_bool_list = [True, True, True, True, False, False, False]

    node = Node("VOLTage")

    # Just pass the entire list directly to the function!
    match_long = node.matches(list_long)

    assert match_long == expected_bool_list


def test_resolve() -> None:
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
