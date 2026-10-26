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
# (C) 2017 by @SchrodingersGat
# (C) 2017 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>
# (C) The KiCad Librarian Team

"""Class definition for a (1D) pad array."""

from collections.abc import Callable, Generator, Iterable
from typing import NamedTuple, cast

from KicadModTree.nodes.base.Pad import Pad, ReferencedPad
from KicadModTree.nodes.Container import Container
from KicadModTree.nodes.specialized.ChamferedPad import ChamferedPad
from KicadModTree.util.corner_handling import RoundRadiusHandler
from kilibs.geom import (
    GeomRectangle,
    GeomShapesClosed,
    Vec2DCompatible,
    Vector2D,
)
from generators.tools.footprint.declarative_def_tools.pad_overrides import PadOverrides


class _ApplyOverrideResult(NamedTuple):
    """A named tuple containing the result of the pad override."""

    number: int | str
    """The number of the pad."""
    position: Vector2D
    """The position of the pad."""
    size: Vector2D
    """The size of the pad."""


class PadArray(Container[Pad | ReferencedPad]):
    """Add a row (1D array) of pads.

    Simplifies the handling of pads which are rendered in a specific form.

    Args:
        type: Type of the pad (e.g., Pad.TYPE_THT, Pad.TYPE_SMT, Pad.TYPE_CONNECT,
            Pad.TYPE_NPTH).
        shape: Shape of the pad (e.g., Pad.SHAPE_CIRCLE, Pad.SHAPE_OVAL, Pad.SHAPE_RECT,
            Pad.SHAPE_TRAPEZE, ...).
        layers: Layers which are used for the pad (e.g., [Pad.LAYERS_SMT,
            Pad.LAYERS_THT, Pad.LAYERS_NPTH]).
        pincount: Number of pads to create.
        size: Size of each pad.
        start: Start point of the pad array.
        center: Center point of the pad array.
        drill: Drill-size of the pad.
        tht_pad1_shape: Shape for marking pad 1 for through hole components.
        fab_property: Fabrication property of the pad (e.g. FabProperty.BGA).
        hidden_pins: Pin number(s) to be skipped; a footprint with hidden pins has
            missing pads and matching pin numbers.
        deleted_pins: Pin locations(s) to be skipped; a footprint with deleted pins has
            pads missing but no missing pin numbers.
        increment: Declare how the name of the follow up is calculated.
        initial: Name of the first pad.
        tht_pad1_id: Pad number used for "pin 1".
        spacing: Distance in mm between the centers of the pads in the array.
        x_spacing: Distance in mm along the x-axis between the centers of the pads.
        y_spacing: Distance in mm along the y-axis between the centers of the pads
        round_radius_handler: Handler for the rounded radius of the pad corners.
        radius_ratio: ratio between the minimum pad dimension and the radius of the
            rounded radius.
        maximum_radius: Maximum value for the corner radius in mm.
        chamfer_size: Size in mm for the chamfer used for the end pads.
        chamfer_corner_selection_first: Select which corners should be chamfered on the
            first pad of the array.
        chamfer_corner_selection_last: Select which corners should be chamfered on the
            last pad  of the array.
        pad_overrides: An optional dict defining the pad overrides.
        end_pads_size_reduction: Size is reduced on the given side (size reduced plus
            center moved).

    Example:
        >>> from KicadModTree import *
        >>> PadArray(pincount=10, spacing=[1,-1], center=[0,0], initial=5, increment=2,
        ...          type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, size=[1,2],
        ...          layers=Pad.LAYERS_SMT)
    """

    def __init__(
        self,
        type: str,
        shape: str,
        layers: list[str],
        pincount: int,
        size: Vec2DCompatible | float,
        start: Vec2DCompatible | None = None,
        center: Vec2DCompatible | None = None,
        drill: float | Vec2DCompatible | None = None,
        tht_pad1_shape: str = Pad.SHAPE_ROUNDRECT,
        fab_property: Pad.FabProperty | None = None,
        hidden_pins: Iterable[int] = [],
        deleted_pins: Iterable[int] = [],
        increment: (
            int
            | Callable[[int | str | None], int | str | None]
            | Generator[int | str | None, None, None]
        ) = 1,
        initial: int | str = 1,
        tht_pad1_id: int = 1,
        spacing: Vec2DCompatible | None = None,
        x_spacing: float | None = None,
        y_spacing: float | None = None,
        round_radius_handler: RoundRadiusHandler | None = None,
        # radius_ratio: float = 0.25,
        # maximum_radius: float = 0.25,
        chamfer_size: float = 0.0,
        chamfer_corner_selection_first: Iterable[bool] | None = None,
        chamfer_corner_selection_last: Iterable[bool] | None = None,
        pad_overrides: PadOverrides | None = None,
        end_pads_size_reduction: dict[str, float] | None = None,
    ) -> None:

        # Instance attributes:
        self.starting_position: Vector2D
        """Coordinates of the first pad of the array in mm."""
        self.spacing: Vector2D
        """Distance between two adjacent pads."""
        self.size: Vector2D
        """Size of the pads."""
        self.pincount: int
        """Number of pads in the array."""
        self.initial_pin: int | str
        """Number of the first pin of the array."""
        self.increment: (
            int
            | Callable[[int | str | None], int | str | None]
            | Generator[int | str | None, None, None]
        )
        """Pad number increment."""
        self.exclude_pin_list: list[int]
        """List of pins to exclude."""
        self.hidden_pins: Iterable[int]
        """List of pins that are hidden."""
        self.modified: bool
        """True if pad_overrides, hidden_pins or deleted_pins are used."""

        super().__init__()
        self.increment = increment
        self._init_pincount(pincount, hidden_pins, deleted_pins)
        self._init_initial_number(initial)
        self._init_spacing(spacing, x_spacing, y_spacing)
        self._init_starting_position(start, center)
        self.modified = True if pad_overrides else False

        # Create pads:
        self.size = Vector2D(size)
        end_pad_size = None
        if end_pads_size_reduction:
            size_reduction = end_pads_size_reduction
            end_pad_size = self.size.copy()

            delta_size = Vector2D.from_floats(
                size_reduction.get("x+", 0.0) + size_reduction.get("x-", 0.0),
                size_reduction.get("y+", 0.0) + size_reduction.get("y-", 0.0),
            )

            end_pad_size -= delta_size

            delta_pos = Vector2D.from_floats(
                (size_reduction.get("x-", 0.0) - size_reduction.get("x+", 0.0)) / 2.0,
                (size_reduction.get("y-", 0.0) - size_reduction.get("y+", 0.0)) / 2.0,
            )
        else:
            delta_pos = Vector2D.zero()

        pad_numbers: list[str | int | None] | list[str | int] | range
        # Special case, increment = 0
        # This can be used for creating an array with all the same pad number:
        if self.increment == 0:
            pad_numbers = [self.initial_pin] * self.pincount
        elif isinstance(self.increment, int):
            pad_numbers = range(
                cast(int, self.initial_pin),
                cast(int, self.initial_pin) + (self.pincount * self.increment),
                self.increment,
            )
        elif callable(self.increment):
            pad_numbers = cast(list[str | int | None], [self.initial_pin])
            for _ in range(1, self.pincount):
                pad_numbers.append(self.increment(pad_numbers[-1]))
        else:  # if isinstance(self.increment, Generator):
            pad_numbers = [next(self.increment) for _ in range(self.pincount)]

        reference_pad: Pad | None = None

        for i, number in enumerate(pad_numbers):
            # deleted pins are filtered by pad/pin position (they are 'None' in pad_numbers list)
            # hidden pins are filtered out by pad number (index of pad_numbers list)
            if number is not None and not (
                self.hidden_pins and number in self.exclude_pin_list
            ):
                current_pad_pos = Vector2D(
                    self.starting_position.x + i * self.spacing.x,
                    self.starting_position.y + i * self.spacing.y,
                )

                current_pad_size = self.size
                current_shape = shape
                if i == 0 or i == len(pad_numbers) - 1:
                    current_pad_pos += delta_pos
                    if end_pad_size:
                        current_pad_size = end_pad_size
                if type == Pad.TYPE_THT and number == tht_pad1_id:
                    current_shape = tht_pad1_shape

                pad_params_with_override = self._apply_overrides(
                    number, current_pad_pos, current_pad_size, pad_overrides
                )

                if chamfer_size:
                    chamfer_corner_selection = None
                    if i == 0 and chamfer_corner_selection_first:
                        chamfer_corner_selection = chamfer_corner_selection_first
                    elif i == len(pad_numbers) - 1 and chamfer_corner_selection_last:
                        chamfer_corner_selection = chamfer_corner_selection_last
                    if chamfer_corner_selection and round_radius_handler:
                        self.append(
                            ChamferedPad(
                                number=pad_params_with_override.number,
                                at=pad_params_with_override.position,
                                size=pad_params_with_override.size,
                                corner_selection=chamfer_corner_selection,
                                chamfer_size=chamfer_size,
                                layers=layers,
                                round_radius_handler=round_radius_handler,
                                type=type,
                                fab_property=fab_property,
                                drill=drill,
                            )
                        )
                        continue

                # Copying a pad and changing a few properties is faster than creating
                # a new one.
                if (
                    isinstance(reference_pad, Pad)
                    and pad_params_with_override.size == reference_pad.size
                    and reference_pad.shape == current_shape
                ):
                    referenced_pad = ReferencedPad(
                        reference_pad=reference_pad,
                        number=pad_params_with_override.number,
                        at=pad_params_with_override.position,
                    )
                    self.append(referenced_pad)
                else:
                    reference_pad = Pad(
                        number=pad_params_with_override.number,
                        at=pad_params_with_override.position,
                        size=pad_params_with_override.size,
                        shape=current_shape,
                        layers=layers,
                        round_radius_handler=round_radius_handler,
                        type=type,
                        fab_property=fab_property,
                        drill=drill,
                    )
                    self.append(reference_pad)
            else:
                self.modified = True

    def _init_pincount(
        self, pincount: int, hidden_pins: Iterable[int], deleted_pins: Iterable[int]
    ) -> None:
        """Initialize the pin count.

        Args:
            pincount: The number of pins in the array.
            hidden_pins: The list of pins to hide.
            delted_pins: The list of pins to delete.
        """
        self.pincount = pincount
        self.hidden_pins = hidden_pins
        if pincount <= 0:
            raise ValueError(f"{pincount} is an invalid value for pincount.")
        self.exclude_pin_list = []
        if hidden_pins:
            if deleted_pins:
                raise KeyError("hidden pins and deleted pins cannot be used together")
            # exclude_pin_list is for pads being removed based on pad number
            # deleted pins are filtered out later by pad location (not number)
            self.exclude_pin_list = list(hidden_pins)
            if type(self.exclude_pin_list) not in [list, tuple]:
                raise TypeError(
                    'hidden pin list must be specified like "hidden_pins=[0,1]"'
                )
            elif any([type(i) not in [int] for i in self.exclude_pin_list]):
                raise ValueError("hidden pin list must contain integer values")

    # Where to start the array
    def _init_starting_position(
        self,
        start: Vec2DCompatible | None = None,
        center: Vec2DCompatible | None = None,
    ) -> None:
        """Initialize the starting position of the pad array.

        Args:
            start: The optional starting position of the pad array.
            center: The optional center position of the pad array.

        Note:
            Either `start` or `center` have to be defined.
        """
        self.starting_position = Vector2D.from_floats(0.0, 0.0)

        # Start takes priority
        if start:
            self.starting_position = Vector2D(start)
        elif center:
            # Now calculate the desired starting position of the array
            center = Vector2D(center)
            self.starting_position.x = (
                center.x - (self.pincount - 1) * self.spacing.x / 2.0
            )
            self.starting_position.y = (
                center.y - (self.pincount - 1) * self.spacing.y / 2.0
            )

    def _init_initial_number(self, initial: int | str = 1) -> None:
        """Initialize the number of the first pad.

        Args:
            initial: The number of the first pad.
        """
        self.initial_pin = initial
        if self.initial_pin == "":
            self.increment = 0
        elif not isinstance(self.initial_pin, int) or self.initial_pin < 1:
            if not callable(self.increment):
                raise ValueError(
                    "{pn} is not a valid starting pin number if increment is not a function".format(
                        pn=self.initial_pin
                    )
                )

    def _init_spacing(
        self,
        spacing: Vec2DCompatible | None,
        x_spacing: float | None = None,
        y_spacing: float | None = None,
    ) -> None:
        """Initialize the pad spacing.

        Note:
            Spacing can be given as:
            spacing = Vector2D(1,2) # high priority
            x_spacing = 1
            y_spacing = 2

        Args:
            spacing: Optional spacing in both x- and y-direction.
            x_spacing: Optional parameter for the spacing on the x-axis.
            y_spacing: Optional parameter for the spacing on the y-axis.
        """
        if spacing:
            self.spacing = Vector2D(spacing)
        else:
            self.spacing = Vector2D(0, 0)
            if x_spacing:
                self.spacing.x = x_spacing
            if y_spacing:
                self.spacing.y = y_spacing
        if self.spacing.x == 0 and self.spacing.y == 0:
            raise ValueError("pad spacing ({self.spacing}) must be non-zero")

    def _apply_overrides(
        self,
        pad_number: int | str,
        pad_position: Vector2D,
        pad_size: Vector2D,
        pad_overrides: PadOverrides | None,
    ) -> _ApplyOverrideResult:
        """Apply pad overrides to the current pad position and parameters.

        Args:
            pad_number: The original number of the pad (before potential override).
            pad_position: The original position of the pad (before potential override).
            pad_size: The original size of the pad (before potential override).
            pad_overrides: The pad overrides.

        Returns:
            A named tuple containing the number, position and size of the pad after the
            override.
        """
        # No overrides? Just return input
        if pad_overrides is None:
            return _ApplyOverrideResult(pad_number, pad_position, pad_size)

        # Check if pad number is in dictionary
        this_pad_override = pad_overrides.overrides.get(pad_number)

        # No overrides for this pad? Just return input
        if this_pad_override is None:
            return _ApplyOverrideResult(pad_number, pad_position, pad_size)

        # Copy input variables (to avoid changing the outer state)
        pad_position = pad_position.copy()
        pad_size = pad_size.copy()

        # Apply relative move:
        # {'pad_override': {1: {"move": [0.1, 0.0]}}}
        if this_pad_override.move:
            if this_pad_override.move[0] is not None:
                pad_position[0] += this_pad_override.move[0]
            if this_pad_override.move[1] is not None:
                pad_position[1] += this_pad_override.move[1]

        # Apply "absolute" position transformation ("set position")
        # {'pad_override': {1: {"at": [0.1, 0.0]}}}
        # Any of the coordinates can be set to None to ignore that coordinate.
        if this_pad_override.at:
            if this_pad_override.at[0] is not None:
                pad_position[0] = this_pad_override.at[0]
            if this_pad_override.at[1] is not None:
                pad_position[1] = this_pad_override.at[1]

        # Apply "size_increase" relative size change
        # {'pad_override': {1: {"size_increase": [0.1, -0.5]}}}
        if this_pad_override.size_increase:
            if this_pad_override.size_increase[0] is not None:
                pad_size[0] += this_pad_override.size_increase[0]
            if this_pad_override.size_increase[1] is not None:
                pad_size[1] += this_pad_override.size_increase[1]

        # Apply "size" absolute override
        # {'pad_override': {1: {"size": [1.5, 0.7]}}}
        # Any of the coordinates can be set to None to ignore that coordinate.
        if this_pad_override.size:
            if this_pad_override.size[0] is not None:
                pad_size[0] = this_pad_override.size[0]
            if this_pad_override.size[1] is not None:
                pad_size[1] = this_pad_override.size[1]

        # Apply "number" override
        # {'pad_override': {1: {"override_numbers": "B6"}}}
        # Pleeease use this only as a way of last resort :-)
        pad_number = this_pad_override.override_number or pad_number

        return _ApplyOverrideResult(pad_number, pad_position, pad_size)

    def flatten(self) -> list[Pad | ReferencedPad]:
        """Return the leaf nodes to serialize."""
        return self._children

    def get_pad_with_name(self, number: str | int) -> Pad | ReferencedPad | None:
        """Return the pad with the given name.

        Args:
            number: The number or name of the pad.

        Returns:
            The pad with the given name, or `None` if no pad with such a name could be
            found."""
        for pad in self._children:
            if pad.number == number:
                return pad
        return None

    def as_geom_shape(self, inflation: float = 0.0) -> GeomRectangle | None:
        """Return the geometric rectangle that encloses all pads in the pad array.

        Args:
            inflation: Amount in mm that the returned shape is inflated.

        Returns:
            The inflated contour of the pad array.
        """
        if not self._children:
            return None
        bbox = self._children[0].bbox().include_bbox(self._children[-1].bbox())
        return GeomRectangle(
            start=bbox.top_left - inflation, end=bbox.bottom_right + inflation
        )

    def as_geom_shapes(self, inflation: float = 0.0) -> list[GeomShapesClosed]:
        """Return a list of geometric rectangles that enclose all pads of the pad array.
        If there are no deleted or hidden pins this correponds to a list containing the
        bounding box of the pad array. If there are gaps in the pad array (caused by
        hidden or deleted pins) the list contains the contours of the individual pads.

        Args:
            inflation: Amount in mm that the returned shape is inflated.

        Returns:
            The inflated contours of the pads in the array.
        """
        # If no pad is deleted or hidden return a list with a single item:
        if self.pincount == len(self._children):
            geom_shape = self.as_geom_shape(inflation)
            if geom_shape is None:
                return []
            else:
                return [geom_shape]
        # Otherwise return a list of the individual pad contours:
        else:
            shapes: list[GeomShapesClosed] = []
            for pad in self._children:
                shapes.append(pad.as_geom_shape(inflation))
            return shapes

    def __repr__(self) -> str:
        """The string representation of the pad array."""
        return (
            f"PadArray("
            f'initial_pin="{self.initial_pin}", '
            f"pincount={self.pincount}, "
            f"size={self.size}, "
            f"spacing={self.spacing}, "
            f"starting_position={self.starting_position})"
        )


def get_pad_radius_from_arrays(pad_arrays: list[PadArray]) -> float:
    """Return the radius of the pads in the array.

    Note: As soon as the first pad with a radius different from zero is found, that
        radius is returned.
    """
    pad_radius = 0.0
    for pad_array in pad_arrays:
        if pad_radius == 0.0:
            pads = pad_array.children
            if len(pads):
                pad_radius = pads[0].get_round_radius()
    return pad_radius


def find_lowest_numbered_pad(
    pad_arrays: list[PadArray],
) -> tuple[int, int]:
    """From a list of pad arrays, find the lowest-integer-numbered pad.

    Returns:
        A tuple containing [the index of the pad array] [the index of the pad] of the
        lowest-integer-numbered-pad.
    """

    index_array = 0
    index_pad = 0
    pad_number = None

    for idx_array, pad_array in enumerate(pad_arrays):
        for idx_pad, pad in enumerate(pad_array):
            try:
                int_num = int(pad.number)
            except ValueError:
                # If the pad number is not an int, skip it
                continue

            if pad_number is None or int_num < pad_number:
                pad_number = int_num
                index_array = idx_array
                index_pad = idx_pad

    return (index_array, index_pad)
