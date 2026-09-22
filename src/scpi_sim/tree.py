"""A single node of the SCPI command tree, with its short and long spellings."""

from dataclasses import dataclass, field


class InvalidMnemonicError(ValueError):
    """Raised when a Node's mnemonic doesn't follow SCPI naming rules."""


class DuplicateParentError(ValueError):
    """Raised when a child Node has more than one parent."""


@dataclass
class Node:
    """One keyword in the SCPI command tree."""

    mnemonic: str
    settable: bool = False
    queryable: bool = False
    optional: bool = False
    children: dict[str, "Node"] = field(default_factory=dict)
    parent: "Node | None" = field(default=None, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Validate the mnemonic, then make this node the parent of its children.

        Every child is checked before any is changed, so a failure leaves
        all children exactly as they were.

        Raises
        ------
        InvalidMnemonicError
            If the abbreviation prefix isn't uppercase, the remainder
            isn't lowercase, or the mnemonic is longer than 12 characters.
        DuplicateParentError
            If any child already belongs to a different parent node.
        """
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

        for node in self.children.values():
            if node.parent is not None and node.parent is not self:
                raise DuplicateParentError("No duplicate parents")

        for node in self.children.values():
            node.parent = self

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
        node_key = Node("")
        values_children = self.children.values()
        for node in values_children:
            if keyword.upper() == node.long():
                node_key = node
            if keyword.upper() == node.short():
                node_key = node
        if node_key in values_children:
            return node_key
        for word in values_children:
            if word.optional:
                if word.resolve(keyword):
                    node_key_2 = word.resolve(keyword)
                    return node_key_2
        return None
