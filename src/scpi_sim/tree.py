"""A single node of the SCPI command tree, with its short and long spellings."""

from dataclasses import dataclass, field


class InvalidMnemonicError(ValueError):
    """Raised when a Node's mnemonic doesn't follow SCPI naming rules."""


class DuplicateParentError(ValueError):
    """Raised when a child Node has more than one parent."""


class AmbiguousPathError(ValueError):
    """Raised when two of a Node's children could be reached by the same keyword.

    Children of an optional node count as one level up (SCPI-99 section 6.2.2),
    so this covers same-level collisions and ones through default nodes.
    """


class DuplicateChildError(ValueError):
    """Raised when the same Node object is listed twice among one node's children."""


@dataclass
class Node:
    """One keyword in the SCPI command tree."""

    mnemonic: str
    settable: bool = True
    queryable: bool = True
    optional: bool = False
    children: list["Node"] = field(default_factory=list)
    _lookup: dict[str, "Node"] = field(
        default_factory=dict, init=False, repr=False, compare=False
    )
    parent: "Node | None" = field(default=None, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Validate the mnemonic and the children, then adopt and index them.

        Pass 1 only checks: each child's parent, and every spelling typeable at
        this level (each child plus what `typeable_from_parent` promotes through
        it) for a clash. Pass 2 only changes: each child gets this node as its
        parent and goes into the lookup under both spellings, which is what
        `resolve` reads; promoted nodes are not indexed here. A failure in pass
        1 leaves all children exactly as they were.

        Raises
        ------
        InvalidMnemonicError
            If the abbreviation prefix isn't uppercase, the remainder
            isn't lowercase, or the mnemonic is longer than 12 characters.
        DuplicateParentError
            If any child already belongs to a different parent node.
        DuplicateChildError
            If the same node object appears more than once in `children`.
        AmbiguousPathError
            If two different nodes typeable at this level share a spelling, so
            one keyword would match both; children of optional nodes count as
            typeable here.
        """
        seen: dict[str, Node] = {}
        n = len(self.short())

        if self.mnemonic[:n] != self.short():
            raise InvalidMnemonicError("Mnemonic's prefix should be capitalized")

        if self.mnemonic[n:] != self.long():
            for char in self.mnemonic[n:]:
                if char.isupper():
                    raise InvalidMnemonicError(
                        "Mnemonic's remainder should be lowercase"
                    )

        if len(self.mnemonic) > 12:
            raise InvalidMnemonicError("Max. 12 Characters for a mnemonic")

        for node in self.children:
            if node.parent is not None and node.parent is not self:
                raise DuplicateParentError("No duplicate parent nodes")
            for candidate in node.typeable_from_parent():
                claimed_by = seen.get(candidate.short())
                if claimed_by is candidate:
                    raise DuplicateChildError("Children contains duplicate child node")
                if claimed_by is not None:
                    raise AmbiguousPathError(
                        f"{candidate.short()!r} under {self.mnemonic} would match "
                        f"both {claimed_by.mnemonic} and {candidate.mnemonic}"
                    )

                seen.update(
                    {
                        candidate.short(): candidate,
                        candidate.long(): candidate,
                    }
                )

        for node in self.children:
            node.parent = self
            self._lookup.update(
                {
                    node.short(): node,
                    node.long(): node,
                }
            )

    def typeable_from_parent(self) -> list["Node"]:
        """Return this node, plus everything promoted up through it if it's optional.

        These are the nodes a parent can reach by typing one keyword because of
        this child: the child itself and, through each optional (default) node,
        that node's children too (SCPI-99 p. 26). Promotion stops at a required
        node. The node itself comes first, so a parent checks it before anything
        promoted through it.
        """
        list_nodes: list[Node] = [self]
        if self.optional:
            for child in self.children:
                list_nodes.extend(child.typeable_from_parent())
        return list_nodes

    def short(self) -> str:
        """Return the standard SCPI short form of the mnemonic."""
        clean_name = self.mnemonic.lower()
        if len(clean_name) <= 4:
            return clean_name.upper()
        elif clean_name[3] in ["a", "e", "i", "o", "u"]:
            short3 = clean_name[:3]
            return short3.upper()
        else:
            short4 = clean_name[:4]
            return short4.upper()

    def long(self) -> str:
        """Return the mnemonic's long form, upper-cased."""
        return self.mnemonic.upper()

    def matches(self, text: list[str]) -> list[bool]:
        """Return whether each keyword in `text` matches this mnemonic.

        A keyword matches if it equals the node's short or long form,
        case-insensitively.
        """
        match_list = [self.short(), self.long()]
        return [t.upper() in match_list for t in text]

    def resolve(self, keyword: str) -> "Node | None":
        """Return the child matching `keyword`, or `None` if nothing matches."""
        found = self._lookup.get(keyword.upper())
        if found is not None:
            return found
        for word in self.children:
            if word.optional:
                found_below = word.resolve(keyword)
                if found_below is not None:
                    return found_below
        return None
