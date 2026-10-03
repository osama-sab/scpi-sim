"""Parsing SCPI program messages: splitting units and walking headers."""

from dataclasses import dataclass

from scpi_sim.tree import Node


def walk(root: Node, current: Node, header: str) -> "tuple[Node, Node] | None":
    """Resolve `header` and return ``(landed, path)``, or `None` if a keyword misses.

    A header with a leading colon starts from `root`; otherwise it starts from
    `current`. Each keyword is resolved one level below the previous one.

    ``landed`` is the node the header resolves to. ``path`` is the node the walk
    stood on just before the last keyword: the header minus its last keyword,
    which is where the next relative unit in the same message starts. SCPI-99
    section 6.2.4 requires this "route" rather than the parent of ``landed``,
    because default (optional) nodes must not alter the header path.

    Parameters
    ----------
    root
        The top of the command tree.
    current
        Where a relative header (no leading colon) starts resolving from.
    header
        Colon-separated keywords only, e.g. ``"SENS:VOLT:DC"``, with no
        parameters and no trailing ``?``.
    """
    result = header.split(":")
    if header == "":
        return None
    if result[0] == "":
        current = root
        result = result[1:]
    path = current
    for node in result:
        resolve_current = current.resolve(node)
        if resolve_current is None:
            return None
        path = current
        current = resolve_current
    return current, path


def split_unit(unit: str) -> tuple[str, bool, str] | None:
    """Split one message unit into ``(header, is_query, parameter_text)``.

    The header ends at the first whitespace; everything after that gap is the
    parameter text, with whitespace trimmed from its ends only, so spaces
    inside it (``'"Hello, world!"'``) are kept. A ``?`` at the end of the
    header marks a query and is removed from the returned header.

    The header itself isn't checked here: ``"MEAS:"`` is returned as it is, and
    `walk` rejects it later. Parameter text is not parsed.

    Returns `None` for an empty or whitespace-only unit, and for a ``?``
    anywhere in the header except at its end (``"VOLT?:DC"``).
    """
    list_unit = unit.split(maxsplit=1)  # split once
    if not list_unit:
        return None
    header = list_unit[0]
    is_query = False
    # Check: list_unit consists of one or two elements
    if len(list_unit) == 2:
        parameter_text = list_unit[1]
        parameter_text = parameter_text.rstrip()
    else:
        parameter_text = ""
    # Check: header is a query
    if "?" in header:
        if header[-1] == "?":
            is_query = True
            header = header[:-1]
        else:
            return None
    result = (header, is_query, parameter_text)
    return result


def helper_parser(node: Node, is_query: bool) -> bool:
    """Return whether `node` accepts a unit in this form: query or command.

    The query flag picks which of the node's flags decides: a query needs
    ``queryable``, a command needs ``settable``. SCPI-99 section 6.2.3 makes
    both forms the default and marks exceptions as ``[query only]`` or
    ``[no query]``; a path node such as a bare ``SENSe`` allows neither.
    """
    return (node.settable and not is_query) or (node.queryable and is_query)


@dataclass(frozen=True)
class ParsedUnit:
    """One message unit whose header resolved to a node in the command tree.

    Attributes
    ----------
    node
        The node the header landed on. Compare it with ``is``: two nodes with
        the same mnemonic in different branches (``AC:RANGe``, ``DC:RANGe``)
        compare equal with ``==``.
    is_query
        True if the header ended in ``?``.
    parameters
        Everything after the header, trimmed at its ends but not parsed, e.g.
        ``"10,0.001"``; ``""`` if the unit had no parameters.
    """

    node: Node
    is_query: bool
    parameters: str


def walk_message(root: Node, message: str) -> list[ParsedUnit | None]:
    """Parse every ``;``-separated unit of `message`, one `ParsedUnit` per unit.

    Each unit is split by `split_unit` into header, query flag and parameter
    text, and only the header is walked. The current path starts at `root` for
    every message and, after each unit, becomes that unit's route: the node
    before its last keyword (see `walk`). Whitespace around each unit is
    ignored; whitespace inside a header is not, so ``"MEAS: VOLT"`` fails.

    Provisional, pending IEEE 488.2:

    - A unit that can't be split, doesn't resolve, or uses a form its node
      doesn't allow (see `helper_parser`) adds ``None`` and ends the message;
      later units are not parsed, so the list stops at the failure.
    - An empty unit counts as a failure: a trailing ``;``, or ``;;``.

    Known limitation: the message is split on every ``;``, including one
    inside a quoted string parameter (``DISP:TEXT "a;b"``), which cuts that
    unit in two.

    Parameters
    ----------
    root
        The top of the command tree.
    message
        One program message: units separated by ``;``, each a header with an
        optional trailing ``?`` and optional parameter text.
    """
    result = message.split(";")
    current_path = root
    result_list: list[ParsedUnit | None] = []
    for res in result:
        value = split_unit(res)
        if value is None:
            result_list.append(None)
            return result_list
        header, query, parameter = value
        outcome = walk(root, current_path, header)
        if outcome is None:
            result_list.append(None)
            return result_list
        landed, current_path = outcome
        if helper_parser(landed, query):
            result_unit = ParsedUnit(node=landed, is_query=query, parameters=parameter)
            result_list.append(result_unit)
        else:
            result_list.append(None)
            return result_list
    return result_list
