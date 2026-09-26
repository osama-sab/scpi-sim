"""Walking a colon-separated SCPI header through the command tree."""

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


def walk_message(root: Node, message: str) -> list[Node | None]:
    """Walk every ``;``-separated unit of `message` and return where each landed.

    The current path starts at `root` for every message and, after each unit,
    becomes that unit's route: the node before its last keyword (see `walk`).
    Whitespace around each unit is removed; whitespace inside a header is not,
    so ``"MEAS: VOLT"`` still fails.

    Provisional, pending IEEE 488.2:

    - A unit that doesn't resolve adds ``None`` and ends the message; later
      units are not walked, so the list stops at the failure.
    - A trailing ``;`` leaves an empty last unit, which counts as a failure.

    Parameters
    ----------
    root
        The top of the command tree.
    message
        One program message: units separated by ``;``, headers only, with no
        parameters and no ``?``.
    """
    result = message.split(";")
    current_path = root
    result_list: list[Node | None] = []
    for res in result:
        res = res.strip()
        outcome = walk(root, current_path, res)
        if outcome is None:
            result_list.append(None)
            return result_list
        landed, current_path = outcome
        result_list.append(landed)
    return result_list
