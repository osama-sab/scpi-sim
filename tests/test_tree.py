import re

import pytest

from scpi_sim.tree import (
    AmbiguousPathError,
    DuplicateChildError,
    DuplicateParentError,
    InvalidMnemonicError,
    Node,
)


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
    volt_sense = Node("VOLTage", children=[dc])
    sense = Node(
        "SENSe",
        optional=True,
        children=[volt_sense],
    )

    nplc = Node("NPLCycles")
    ac = Node("AC", children=[nplc])
    volt = Node("VOLTage", children=[ac])
    meas = Node("MEASure", children=[volt])

    root = Node(
        "ROOT",
        children=[
            sense,
            meas,
        ],
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
    ac = Node("AC", children=[nplc])
    volt = Node("VOLTage", children=[ac])

    with pytest.raises(DuplicateParentError):
        Node("VOLTage", children=[ac])
    with pytest.raises(TypeError):
        Node("DC", parent=volt)  # type: ignore[call-arg]
    ac_sense = Node("AC")
    dc = Node("DC")
    sense = Node("SENSe", children=[ac_sense])
    assert sense is ac_sense.parent

    with pytest.raises(DuplicateParentError):
        Node("VOLTage", children=[dc, ac_sense])
    assert dc.parent is None
    assert ac_sense.parent is sense

    curr = Node("CURRent")
    meas = Node("MEASure", children=[curr])
    assert curr.parent is meas

    assert volt is ac.parent
    assert None is volt.parent

    volt_resolve = volt.resolve("ac")
    assert volt_resolve is not None
    assert volt is volt_resolve.parent

    ac_result = ac.resolve("NPLCycles")
    assert ac_result is not None
    assert ac is ac_result.parent


@pytest.mark.parametrize(
    ("mnemonic", "children_mnemonics"),
    [
        ("ROOT", ["JSTart", "JSTop"]),
        ("CURRent", ["AMPerage", "AMPere"]),
        ("ORIGin", ["VOLT", "VOLTage"]),
    ],
    ids=[
        "JST-short-collision",
        "AMP-short-collision",
        "long-equals-short",
    ],
)
def test_same_level_collision_raises(
    mnemonic: str, children_mnemonics: list[str]
) -> None:
    """Siblings that share a spelling are rejected (SCPI-99 p. 25, JSTart/JSTop).

    Rows hold only mnemonics; each run builds fresh nodes from them.
    """
    children_list: list[Node] = []
    for child in children_mnemonics:
        children_list.append(Node(child))
    with pytest.raises(AmbiguousPathError):
        Node(mnemonic, children=children_list)
    for child_node in children_list:
        assert child_node.parent is None


@pytest.mark.parametrize(
    ("mnemonic", "children_mnemonics"),
    [
        ("CLOCk", ["TIMer", "TIME"]),
    ],
    ids=[
        "different-spellings",
    ],
)
def test_same_level_distinct_spellings_allowed(
    mnemonic: str, children_mnemonics: list[str]
) -> None:
    """Siblings whose spellings all differ coexist (SCPI-99 p. 25, TIME/TIMer)."""
    children_list: list[Node] = []
    for child in children_mnemonics:
        children_list.append(Node(child))
    node = Node(mnemonic, children=children_list)
    for child_node in children_list:
        assert child_node.parent is node


def test_collision_through_optional_child() -> None:
    """A direct child collides with one promoted through an optional sibling.

    Children of a default node count one level up (SCPI-99 p. 26), so LEAF
    and [TREE]:LEAF are both typeable as LEAF at ORIGin. The failed build
    leaves both children unadopted.
    """
    second_leaf = Node("LEAF")
    tree = Node("TREE", optional=True, children=[second_leaf])
    leaf = Node("LEAF")
    with pytest.raises(AmbiguousPathError):
        Node("ORIGin", children=[tree, leaf])
    assert tree.parent is None
    assert leaf.parent is None


def test_two_optional_siblings_with_same_child() -> None:
    """Two optional siblings that both promote a LEAF collide at their parent."""
    second_leaf = Node("LEAF")
    tree = Node("TREE", optional=True, children=[second_leaf])
    leaf = Node("LEAF")
    plant = Node("PLANt", optional=True, children=[leaf])
    with pytest.raises(AmbiguousPathError):
        Node("ORIGin", children=[tree, plant])
    assert tree.parent is None
    assert plant.parent is None


def test_promotion_stops_at_required_node() -> None:
    """Promotion stops at a required node, so a LEAF below it doesn't collide.

    [OUTer]:INNer:LEAF needs INNer typed, so only OUTer and INNer are typeable
    at ORIGin, next to the direct LEAF.
    """
    second_leaf = Node("LEAF")
    inner = Node("INNer", children=[second_leaf])
    outer = Node("OUTer", optional=True, children=[inner])
    leaf = Node("LEAF")
    Node("ORIGin", children=[leaf, outer])
    assert second_leaf.parent is inner


def test_collision_through_two_optional_children() -> None:
    """Promotion repeats through nested defaults: [OUTer][INNer]LEAF hits LEAF."""
    second_leaf = Node("LEAF")
    inner = Node("INNer", optional=True, children=[second_leaf])
    outer = Node("OUTer", optional=True, children=[inner])
    leaf = Node("LEAF")
    with pytest.raises(AmbiguousPathError):
        Node("ORIGin", children=[leaf, outer])
    assert outer.parent is None
    assert leaf.parent is None


def test_jstart_with_optional_node_containing_jstop() -> None:
    """A short-form collision (JST) is caught through a default node too."""
    jstop = Node("JSTop")
    tree = Node("TREE", optional=True, children=[jstop])
    jstart = Node("JSTart")
    with pytest.raises(AmbiguousPathError):
        Node("ORIGin", children=[jstart, tree])
    assert jstart.parent is None
    assert tree.parent is None


def test_parent_child_same_name() -> None:
    """A node may have a child with its own name: different levels, no default."""
    child = Node("VOLTage")
    parent = Node("VOLTage", children=[child])
    assert parent is child.parent


def test_optional_node_and_child_node_same_mnemonic() -> None:
    """An optional node and its same-named child collide one level up.

    [TREE]:TREE is valid on its own; at ORIGin both are typeable as TREE. This
    also pins the order: the optional node is recorded before its children.
    """
    child_tree = Node("TREE")
    tree = Node("TREE", optional=True, children=[child_tree])
    with pytest.raises(AmbiguousPathError):
        Node("ORIGin", children=[tree])
    assert tree.parent is None


def test_same_name_different_positions() -> None:
    """The same mnemonic under two required siblings is fine (AC:RANGe, DC:RANGe)."""
    range_ac = Node("RANGe")
    ac = Node("AC", children=[range_ac])
    range_dc = Node("RANGe")
    dc = Node("DC", children=[range_dc])
    origin = Node("ORIGin", children=[ac, dc])
    assert dc.parent is origin
    assert ac.parent is origin


def test_duplicate_child_error() -> None:
    """The same node object listed twice is a DuplicateChildError, not ambiguity.

    Checked with identity: two different but equal nodes are an ambiguity.
    """
    a = Node("A")
    with pytest.raises(DuplicateChildError):
        Node("ORIGin", children=[a, a])
    assert a.parent is None


@pytest.mark.parametrize(
    ("chain", "expected"),
    [
        ((("ROOT", False), ("VOLTage", False), ("DC", False)), "ROOT:VOLTage:DC"),
        ((("ROOT", False), ("VOLTage", True), ("DC", False)), "ROOT[:VOLTage]:DC"),
        ((("ROOT", True), ("VOLTage", True), ("DC", False)), "[ROOT:][VOLTage:]DC"),
        (
            (("ROOT", False), ("VOLTage", True), ("DC", False), ("NPLCycles", True)),
            "ROOT[:VOLTage]:DC[:NPLCycles]",
        ),
        ((("ROOT", True), ("VOLTage", False), ("DC", True)), "[ROOT:]VOLTage[:DC]"),
        (
            (("ROOT", True), ("VOLTage", False), ("DC", False), ("NPLCycles", True)),
            "[ROOT:]VOLTage:DC[:NPLCycles]",
        ),
        ((("ROOT", False), ("VOLTage", True), ("DC", True)), "ROOT[:VOLTage][:DC]"),
        (
            (("ROOT", False), ("VOLTage", True), ("DC", True), ("NPLCycles", False)),
            "ROOT[:VOLTage][:DC]:NPLCycles",
        ),
        ((("VOLTage", False),), "VOLTage"),
        ((("VOLTage", True),), "[VOLTage]"),
    ],
    ids=[
        "all-required",
        "optional-between-two-required",
        "two-optional-parents",
        "required-optional-required-optional",
        "required-between-two-optionals",
        "optional-last",
        "two-optional-children",
        "two-optionals-in-the-middle",
        "single-required",
        "single-optional",
    ],
)
def test_path(chain: tuple[tuple[str, bool], ...], expected: str) -> None:
    """path() writes SCPI notation for every position of an optional node.

    Each row is a straight chain, top-down, as (mnemonic, optional) pairs; the
    test builds it bottom-up and checks the bottom node's path. Before the first
    required node an optional one takes the colon after it, afterwards the one
    before it; a lone optional node has no colon at all.
    """
    bottom_up = chain[::-1]
    list_nodes: list[Node] = []
    (child_mnemonic, child_is_optional) = bottom_up[0]
    child_node = Node(child_mnemonic, optional=child_is_optional)
    list_nodes.append(child_node)
    for pair in bottom_up[1:]:
        (mnemonic, is_optional) = pair
        last_node = list_nodes[-1]
        node = Node(mnemonic, optional=is_optional, children=[last_node])
        list_nodes.append(node)
    assert child_node.path() == expected


def test_equal_nodes_different_paths() -> None:
    """Two equal RANGe nodes get different paths: what == can't tell apart, path can."""
    range_ac = Node("RANGe")
    ac = Node("AC", children=[range_ac])
    range_dc = Node("RANGe")
    dc = Node("DC", children=[range_dc])
    Node("ORIGin", children=[ac, dc])
    assert range_ac.path() == "ORIGin:AC:RANGe"
    assert range_dc.path() == "ORIGin:DC:RANGe"


@pytest.mark.parametrize(
    ("first", "second"),
    [
        ("leaf", "outer"),
        ("outer", "leaf"),
    ],
    ids=["leaf-first", "outer-first"],
)
def test_reversed_child_order_path(first: str, second: str) -> None:
    """The ambiguity message names the promoted path whichever child comes first.

    Order decides which node is the first claimant and which the second, so
    both must be printed with path(). Rows name the order; nodes are built here.
    """
    second_leaf = Node("LEAF")
    inner = Node("INNer", optional=True, children=[second_leaf])
    outer = Node("OUTer", optional=True, children=[inner])
    leaf = Node("LEAF")
    children_list = [leaf, outer]
    if first == "outer":
        children_list = children_list[::-1]
    with pytest.raises(AmbiguousPathError, match=re.escape("[OUTer:][INNer:]LEAF")):
        Node("ORIGin", children=children_list)
    assert outer.parent is None
    assert leaf.parent is None
