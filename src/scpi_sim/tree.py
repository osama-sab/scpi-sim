"""A single node of the SCPI command tree, with its short and long spellings."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Node:
    """One keyword in the SCPI command tree."""

    mnemonic: str
    settable: bool = False
    queryable: bool = False
    optional: bool = False

    def short(self) -> str:
        """Return the standard SCPI short form of the mnemonic."""
        clean_name = self.mnemonic.lower()
        if len(clean_name) <= 4:
            return Node.long(self)
        elif clean_name[3] in ["a", "e", "i", "o", "u"]:
            short3 = clean_name[:3]
            return short3.upper()
        else:
            short4 = clean_name[:4]
            return short4.upper()

    def long(self) -> str:
        """Return the mnemonic's long form, upper-cased."""
        clean_name = self.mnemonic.lower()
        return clean_name.upper()

    def matches(self, text: list[str]) -> list[bool]:
        """Return whether each keyword in `text` matches this mnemonic.

        A keyword matches if it equals the node's short or long form,
        case-insensitively.
        """
        match_list = [self.short(), self.long()]
        return [t.upper() in match_list for t in text]
