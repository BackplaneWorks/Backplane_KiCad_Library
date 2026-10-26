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

"""Classes for handling pad corners."""

from kilibs.geom.vector import Vector2D


class RoundRadiusHandler:
    """Handler for the round radius setting of a corner."""

    def __init__(
        self,
        radius_ratio: float,
        maximum_radius: float | None = None,
        round_radius_exact: float | None = None,
    ) -> None:
        """Initializes the RoundRadiusHandler.

        Args:
            radius_ratio: The radius ratio of the rounded rectangle. Must be in the
                range [0, 0.5].
            maximum_radius: The maximum radius for the rounded rectangle. Defaults to
                `None`, meaning no maximum limit.
            round_radius_exact: An exact round radius to set for a pad. Defaults to
                `None`, meaning `radius_ratio` and `maximum_radius` will be used.

        Raises:
            ValueError: If `radius_ratio` is not within the range [0, 0.5].
        """

        # Instance attributes:
        self.radius_ratio: float
        """The ratio between the shorter length of a pad and the rounding radius."""
        self.maximum_radius: float | None
        """Maxiumum radius in mm for the rounded rectangle."""
        self.round_radius_exact: float | None
        """The exact raounding radius in mm."""

        if radius_ratio < 0 or radius_ratio > 0.5:
            raise ValueError("radius_ratio must be in range [0, 0.5]")

        self.radius_ratio = radius_ratio
        self.maximum_radius = maximum_radius
        self.round_radius_exact = round_radius_exact

    def get_radius_ratio(self, shortest_sidelength: float) -> float:
        """Get the resulting round radius ratio.

        Calculates the effective radius ratio to be used for the pad, considering
        `round_radius_exact`, `maximum_radius`, and `radius_ratio` in that order of
        precedence.

        Args:
            shortest_sidelength: The shortest sidelength of a pad.

        Returns:
            The resulting round radius ratio to be used for the pad.

        Raises:
            ValueError: If the `round_radius_exact` is too large for the pad size.
        """
        if self.round_radius_exact is not None:
            if self.round_radius_exact > shortest_sidelength / 2:
                raise ValueError(
                    "requested round radius of {} is too large for pad size of {}".format(
                        self.round_radius_exact, shortest_sidelength
                    )
                )
            if self.maximum_radius is not None:
                return (
                    min(self.round_radius_exact, self.maximum_radius)
                    / shortest_sidelength
                )
            else:
                return self.round_radius_exact / shortest_sidelength

        if self.maximum_radius is not None:
            if self.radius_ratio * shortest_sidelength > self.maximum_radius:
                return self.maximum_radius / shortest_sidelength

        return self.radius_ratio

    def get_round_radius(self, shortest_sidelength: float) -> float:
        """Get the resulting round radius.

        Args:
            shortest_sidelength: The shortest sidelength of a pad.

        Returns:
            The resulting round radius to be used for the pad.
        """
        return self.get_radius_ratio(shortest_sidelength) * shortest_sidelength

    def rounding_requested(self) -> bool:
        """Check if the pad has a rounded corner.

        Returns:
            `True` if rounded corners are required (i.e., radius is non-zero), `False`
            otherwise.
        """
        if self.maximum_radius == 0.0:
            return False
        if self.round_radius_exact == 0.0:
            return False
        if self.radius_ratio == 0.0:
            return False
        return True

    def limit_max_radius(self, limit: float) -> None:
        """Set a new maximum radius limit.

        If rounding is requested and a maximum radius is already set, this method
        updates `maximum_radius` to the minimum of its current value and the given
        `limit`. If no maximum radius was set, it sets `maximum_radius` to the given
        `limit`.

        Args:
            limit: The new maximum radius limit.
        """

        if not self.rounding_requested():
            return
        if self.maximum_radius is not None:
            self.maximum_radius = min(self.maximum_radius, limit)
        else:
            self.maximum_radius = limit

    def __str__(self) -> str:
        """Returns a string representation of the RoundRadiusHandler.

        Returns:
            A string showing the current radius ratio, maximum radius, and exact radius.
        """
        return "ratio {}, max {}, exact {}".format(
            self.radius_ratio, self.maximum_radius, self.round_radius_exact
        )


class ChamferSizeHandler:
    """Handler for the chamfer setting of a corner."""

    def __init__(
        self,
        maximum_chamfer: float | None = None,
        chamfer_ratio: float | None = None,
        chamfer_exact: float | None = None,
        chamfer_size: float | Vector2D | None = None,
        default_chamfer_ratio: float = 0.25,
    ) -> None:
        """Initializes the ChamferSizeHandler.

        Args:
            chamfer_ratio: The chamfer ratio of the chamfered pad. Defaults to
                `default_chamfer_ratio`.
            maximum_chamfer: The maximum chamfer size.
            chamfer_exact: The exact chamfer size for a pad.
            chamfer_size: A single number or a Vector2D specifying the chamfer size. If
                a Vector2D, both x- and y- components must be equal for native pads.
            default_chamfer_ratio: This parameter allows to set the default chamfer
                ratio.

        Raises:
            ValueError: If `chamfer_ratio` or `default_chamfer_ratio` are not within the
            range [0, 0.5], or if `chamfer_size` is a non-square vector.
        """

        # Instance attributes:
        self.maximum_chamfer: float | None
        """The maximum chamfer size."""
        self.chamfer_exact: float | None
        """The exact chamfer size."""
        self.chamfer_ratio: float
        """The ratio between the chamfer size and the shorter length of a pad."""

        def exception_if_not_within_range(name: str, param: float) -> None:
            if param < 0.0:
                raise ValueError(f"{name} must be larger than 0.")
            elif param > 0.5:
                raise ValueError(f"{name} must be smaller than 0.5.")

        exception_if_not_within_range("default_chamfer_ratio", default_chamfer_ratio)
        if chamfer_ratio is None:
            chamfer_ratio = default_chamfer_ratio
        exception_if_not_within_range("chamfer_ratio", chamfer_ratio)
        self.chamfer_ratio = chamfer_ratio
        self.maximum_chamfer = maximum_chamfer
        if chamfer_size is not None:
            # Support the same vector or single number input as ChamferedPad
            # does, but native pads can only have a chamfer_size vector that is the
            # equal.
            chamfer_size = Vector2D(chamfer_size)
            if chamfer_size.x != chamfer_size.y:
                raise ValueError("chamfer_size must be a square vector for native pads")
            chamfer_size = chamfer_size.x
        else:
            chamfer_size = None

        # Override with chamfer_exact if it is set
        if chamfer_exact is None:
            self.chamfer_exact = chamfer_size
        else:
            self.chamfer_exact = chamfer_exact

    def get_chamfer_ratio(self, shortest_sidelength: float) -> float:
        """Get the chamfer ratio.

        Calculates the effective chamfer ratio to be used for the pad, considering
        `chamfer_exact`, `maximum_chamfer`, and `chamfer_ratio` in that order of
        precedence.

        Args:
            shortest_sidelength: The shortest sidelength of a pad.

        Returns:
            The resulting chamfer ratio to be used for the pad.

        Raises:
            ValueError: If the `chamfer_exact` is too large for the pad size.
        """
        if self.chamfer_exact is not None:
            if self.chamfer_exact > shortest_sidelength / 2:
                raise ValueError(
                    "requested chamfer of {} is too large for pad size of {}".format(
                        self.chamfer_exact, shortest_sidelength
                    )
                )
            if self.maximum_chamfer is not None:
                return (
                    min(self.chamfer_exact, self.maximum_chamfer) / shortest_sidelength
                )
            else:
                return self.chamfer_exact / shortest_sidelength

        if self.maximum_chamfer is not None:
            if self.chamfer_ratio * shortest_sidelength > self.maximum_chamfer:
                return self.maximum_chamfer / shortest_sidelength

        return self.chamfer_ratio

    def get_chamfer_size(self, shortest_sidelength: float) -> float:
        """Get the resulting chamfer size.

        Calculates the actual chamfer size based on the chamfer ratio and the shortest
        sidelength of the pad.

        Args:
            shortest_sidelength: The shortest sidelength of a pad.

        Returns:
            The resulting chamfer size to be used for the pad.
        """
        return self.get_chamfer_ratio(shortest_sidelength) * shortest_sidelength

    def chamfer_requested(self) -> bool:
        """Check if the handler indicates a non-zero chamfer.

        Returns:
            `True` if a chamfer is requested (i.e., chamfer size is non-zero), `False`
            otherwise.
        """
        if self.maximum_chamfer == 0:
            return False
        if self.chamfer_exact == 0:
            return False
        if self.chamfer_ratio == 0:
            return False
        return True

    def limit_max_chamfer(self, limit: float) -> None:
        """Set a new maximum chamfer limit.

        If a chamfer is requested and a maximum chamfer is already set, this method
        updates `maximum_chamfer` to the minimum of its current value and the given
        `limit`. If no maximum chamfer was set, it sets `maximum_chamfer` to the given
        `limit`.

        Args:
            limit: The new maximum chamfer limit.
        """
        if not self.chamfer_requested():
            return
        if self.maximum_chamfer is not None:
            self.maximum_chamfer = min(self.maximum_chamfer, limit)
        else:
            self.maximum_chamfer = limit

    def __str__(self) -> str:
        """Returns a string representation of the ChamferSizeHandler.

        Returns:
            A string showing the current chamfer ratio, maximum chamfer, and exact
            chamfer.
        """
        return "ratio {}, max {}, exact {}".format(
            self.chamfer_ratio, self.maximum_chamfer, self.chamfer_exact
        )
