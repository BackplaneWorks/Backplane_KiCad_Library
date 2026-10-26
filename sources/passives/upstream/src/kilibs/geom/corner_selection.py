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

"""Class definition for handling corner selections."""

from __future__ import annotations

from collections.abc import Generator, Iterable, Mapping
from typing import Self, cast


class CornerSelection:
    """Class for handling corner selection."""

    TOP_LEFT = "tl"
    """The top left corner."""
    TOP_RIGHT = "tr"
    """The top right corner."""
    BOTTOM_RIGHT = "br"
    """The bottom right corner."""
    BOTTOM_LEFT = "bl"
    """The bottom left corner."""

    def __init__(
        self,
        corner_selection: Iterable[bool] | Mapping[str, str | bool | int] | int | None,
    ) -> None:
        """Create a corner selection.

        Args:
            corner_selection: Can be a `list` of 4 `bools`, a `dict` or an `int` with
            the following interpretation:

                * A list of bools do directly set the corners (top left, top right,
                  bottom right, bottom left);
                * A dict with keys (constants see below);
                * The integer 1 means all corners;
                * The integer 0 means no corners.
        """

        # Instance attributes:
        self.top_left: bool
        """Whether the top left corner is selected."""
        self.top_right: bool
        """Whether the top right corner is selected."""
        self.bottom_right: bool
        """Whether the bottom right corner is selected."""
        self.bottom_left: bool
        """Whether the bottom left corner is selected."""

        self.top_left = False
        self.top_right = False
        self.bottom_right = False
        self.bottom_left = False

        if isinstance(corner_selection, int | None):
            if corner_selection == 1:
                self.select_all()
                return
            elif corner_selection == 0 or corner_selection is None:
                return
            else:
                raise ValueError(
                    f"Invalid value {corner_selection} for corner_selection."
                )
        elif isinstance(corner_selection, Mapping):
            corner_selection = cast(Mapping[str, str | bool | int], corner_selection)
            for key, value in corner_selection.items():
                self[key] = bool(value)
        else:
            for i, value in enumerate(corner_selection):
                self[i] = bool(value)

    def select_all(self) -> None:
        """Select all corners."""
        for i in range(len(self)):
            self[i] = True

    def clear_all(self) -> None:
        """Select no corners."""
        for i in range(len(self)):
            self[i] = False

    def set_left(self, value: int | bool = 1) -> None:
        """Select left corners."""
        self.top_left = bool(value)
        self.bottom_left = bool(value)

    def set_top(self, value: int | bool = 1) -> None:
        """Select top corners."""
        self.top_left = bool(value)
        self.top_right = bool(value)

    def set_right(self, value: int | bool = 1) -> None:
        """Select right corners."""
        self.top_right = bool(value)
        self.bottom_right = bool(value)

    def set_bottom(self, value: int | bool = 1) -> None:
        """Select bottom corners."""
        self.bottom_left = bool(value)
        self.bottom_right = bool(value)

    def is_any_selected(self) -> bool:
        """Check if any corner is selected."""
        for v in self:
            if v:
                return True
        return False

    def rotate_clockwise(self) -> Self:
        """Rotate the corner selection clockwise."""
        top_left_old = self.top_left

        self.top_left = self.bottom_left
        self.bottom_left = self.bottom_right
        self.bottom_right = self.top_right
        self.top_right = top_left_old
        return self

    def rotate_counter_clockwise(self) -> Self:
        """Rotate the corner selection counter clockwise."""
        top_left_old = self.top_left

        self.top_left = self.top_right
        self.top_right = self.bottom_right
        self.bottom_right = self.bottom_left
        self.bottom_left = top_left_old
        return self

    def __or__(self, other: Self | Iterable[bool]) -> Self:
        """Apply bitwise logic or operation."""
        return self.__class__([s or o for s, o in zip(self, other)])

    def __ior__(self, other: Self | Iterable[bool]) -> Self:
        """Apply bitwise logic or operation inplace."""
        for i, value in enumerate(other):
            self[i] |= value
        return self

    def __and__(self, other: Self | Iterable[bool]) -> Self:
        """Apply bitwise logic and operation."""
        return self.__class__([s and o for s, o in zip(self, other)])

    def __iand__(self, other: Self | Iterable[bool]) -> Self:
        """Apply bitwise logic and operation inplace."""
        for i, value in enumerate(other):
            self[i] &= value
        return self

    def __len__(self) -> int:
        """Number of items."""
        return 4

    def __iter__(self) -> Generator[bool, None, None]:
        """Return an iterator for all its items."""
        yield self.top_left
        yield self.top_right
        yield self.bottom_right
        yield self.bottom_left

    def __getitem__(self, item: int | str) -> bool:
        """Get the given item."""
        if item in [0, CornerSelection.TOP_LEFT]:
            return self.top_left
        if item in [1, CornerSelection.TOP_RIGHT]:
            return self.top_right
        if item in [2, CornerSelection.BOTTOM_RIGHT]:
            return self.bottom_right
        if item in [3, CornerSelection.BOTTOM_LEFT]:
            return self.bottom_left
        raise IndexError("Index {} is out of range".format(item))

    def __setitem__(self, item: int | str, value: bool | int | str) -> None:
        """Set the given item."""
        if item in [0, CornerSelection.TOP_LEFT]:
            self.top_left = bool(value)
        elif item in [1, CornerSelection.TOP_RIGHT]:
            self.top_right = bool(value)
        elif item in [2, CornerSelection.BOTTOM_RIGHT]:
            self.bottom_right = bool(value)
        elif item in [3, CornerSelection.BOTTOM_LEFT]:
            self.bottom_left = bool(value)
        else:
            raise IndexError("Index {} is out of range".format(item))

    def to_dict(self) -> dict[str, bool]:
        """Convert the corner selection to a dictionary."""
        return {
            CornerSelection.TOP_LEFT: self.top_left,
            CornerSelection.TOP_RIGHT: self.top_right,
            CornerSelection.BOTTOM_RIGHT: self.bottom_right,
            CornerSelection.BOTTOM_LEFT: self.bottom_left,
        }

    def __str__(self) -> str:
        """Return a string representation of the corner selection."""
        return str(self.to_dict())
