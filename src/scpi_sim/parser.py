"""Walking a colon-separated SCPI header through the command tree."""

from scpi_sim.tree import Node


def walk(root: Node, current: Node, header: str) -> "Node | None":
    """Return the node that `header` resolves to, or `None` if any keyword misses.

    A header with a leading colon starts from `root`; otherwise it starts from
    `current`. Each keyword is resolved one level below the previous one.

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
    for node in result:
        resolve_current = current.resolve(node)
        if resolve_current is None:
            return None
        current = resolve_current
    return current
