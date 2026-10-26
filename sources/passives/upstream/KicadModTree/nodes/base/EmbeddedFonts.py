# kilibs is free software: you can redistribute it and/or modify it under the terms of
# the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# kilibs is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with kilibs.
# If not, see < http://www.gnu.org/licenses/ >.
#
# (C) The KiCad Librarian Team

"""Class definition for embedded fonts."""

from __future__ import annotations

from KicadModTree.nodes.Node import Node


class EmbeddedFonts(Node):
    """An embedded font.

    This is a class that represents an embedded font node in a Kicad footprint.

    For the time being there is no embedded font support in KiCad generated footprints,
    but if it were added, it would go here.

    We still use this node, because the format expects one (since v9) and omitting
    it causes diffs when saved in KiCad.
    """

    def __init__(self) -> None:
        """Create an embedded fonts node."""
        super().__init__()

    @property
    def enabled(self) -> bool:
        """Return whether the embedded font is enabled or not."""
        return False

    def __repr__(self) -> str:
        """The string representation of the embedded fonts."""
        return f"EmbeddedFonts(enabled={self.enabled})"
