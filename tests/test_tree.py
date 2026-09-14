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
