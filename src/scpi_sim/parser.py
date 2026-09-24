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
