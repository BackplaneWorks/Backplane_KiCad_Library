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


class TwoPadDimensions:
    """Defines two pads spaced like this (doesn't have to be in the x-direction, or even
    parallel to any axis).

    Generally this is used to capture dimesions of pads defined in some other way
    (e.g. a declarative definition), but itself if just a simple container for values.

    .. aafig::

                    spacing outside
        |<------------------------------------->|
        |                                       |
        |           spacing centre              |
        |     |<------------------------->|     |
        |     |                           |     |
        +-----+-----+               +-----+-----+ ---
        |     |     |               |     |     |  ^
        |     o     |               |     o     |  | size crosswise
        |           |               |           |  v
        +-----------+               +-----------+ ---
        |           |               |
        |<--------->|<------------->|
         size inline  spacing inside

    The offset_crosswise is an optional offset in the crosswise direction, which
    defaults to 0:

    .. aafig::

        +---------+
        |    o    | ------
        +---------+     ^
                        | offset_crosswise
                        v                       +---------+
                    --------------------------- |    o    |
                                                +---------+
    """

    size_crosswise: float
    """Width of the pads in mm."""
    size_inline: float
    """Height of the pads in mm."""
    spacing_inside: float
    """Distance in mm between the two inner edges of the pads."""
    offset_crosswise: float = 0.0
    """Offset between pads in mm in the crosswise direction, defaults to 0."""

    def __init__(
        self,
        size_crosswise: float,
        size_inline: float | None = None,
        spacing_centre: float | None = None,
        spacing_inside: float | None = None,
        spacing_outside: float | None = None,
    ) -> None:
        """Handle the various methods of providing sufficient dimensions to derive a
        size, and the inside edge to edge distance that this script works with
        internally.

        Exactly two of the size_inline and spacing parameters are needed.

        Args:
            size_crosswise: The size perpendicular to the spacing dimensions in mm.
            size_inline: The size parallel to the spacing dimensions in mm.
            spacing_centre: The spacing between pad centres in mm.
        """
        if size_inline and spacing_inside:
            # Already have what we need
            pass
        elif size_inline and spacing_outside:
            spacing_inside = spacing_outside - (size_inline * 2)
        elif size_inline and spacing_centre:
            spacing_inside = spacing_centre - size_inline
        elif spacing_inside and spacing_outside:
            size_inline = (spacing_outside - spacing_inside) / 2

        if size_inline is None or spacing_inside is None:
            raise ValueError(
                "Could not derive the two-pad size from the given parameters"
            )
        self.size_inline = size_inline
        self.spacing_inside = spacing_inside
        self.size_crosswise = size_crosswise

    @property
    def spacing_outside(self) -> float:
        """Distance in mm between the two outer edges of the pads."""
        return self.spacing_inside + (self.size_inline * 2)

    @spacing_outside.setter
    def spacing_outside(self, value: float) -> None:
        """Set the spacing outside and derive the size_inline."""
        if value < self.spacing_inside:
            raise ValueError("Spacing outside cannot be less than spacing inside")
        self.spacing_inside = value - (self.size_inline * 2)

    @property
    def spacing_centre(self) -> float:
        """Distance in mm between the two centers of the pads."""
        return self.spacing_inside + self.size_inline
