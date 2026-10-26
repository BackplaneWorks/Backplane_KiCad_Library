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

"""Class definition for a geometric arc."""

from __future__ import annotations

from math import atan2, copysign, degrees, hypot, pi, radians
from typing import Self, cast

from kilibs.geom.bounding_box import BoundingBox
from kilibs.geom.shapes.geom_shape import GeomShapeOpen
from kilibs.geom.tolerances import TOL_MM, tol_deg
from kilibs.geom.vector import Vec2DCompatible, Vector2D


class GeomArc(GeomShapeOpen):
    """A geometric arc."""

    def __init__(
        self,
        shape: GeomArc | None = None,
        center: Vec2DCompatible | None = None,
        start: Vec2DCompatible | None = None,
        mid: Vec2DCompatible | None = None,
        end: Vec2DCompatible | None = None,
        angle: float | None = None,
        long_way: bool = False,
    ) -> None:
        """Create a geometric arc.

        Args:
            shape: Arc from which to derive the parameters. It can be used together with
                `start` or `stop` to define an arc that has either the same starting or
                same end point, same orientation, but different value for `start` or
                `end` - depending on which one of the parameters was provided.
            center: Coordinates (in mm) of the center of the arc.
            start: Coordinates (in mm) of the start point of the arc.
            mid: Coordinates (in mm) of the mid point of the arc.
            end: Coordinates (in mm) of the end point of the arc.
            angle: Angle of the arc in degrees.
            long_way: Used when constructing the arc with the center, start and end
                point to specify if the longer of the 2 possible resulting arcs or the
                shorter one shall be constructed.
        """

        # Instance attributes:
        self.center: Vector2D
        """The center point of the arc."""
        self._start: Vector2D
        """The start point of the arc."""
        self._end: Vector2D | None
        """The end point of the arc."""
        self._angle: float
        """The angle of the arc."""

        if shape is not None:
            self.center = shape.center.copy()
            self._start = shape._start.copy()
            self._angle = shape._angle
            self._end = shape._end.copy() if shape._end else None
            if end is not None:
                self._end = Vector2D(end)
                angle = self.point_to_angle_relative_to_self(self._end)
                if (angle > 0 and self._angle > 0) or (angle < 0 and self._angle < 0):
                    self._init_angle(angle)
                else:
                    self._init_angle(360 - angle)  # not sure if this is correct
            elif start is not None:
                self._start = Vector2D(start)
                angle = self.point_to_angle_relative_to_self(self._start)
                if (angle > 0 and self._angle > 0) or (angle < 0 and self._angle < 0):
                    self._init_angle(self._angle - angle)
                else:
                    self._init_angle(
                        360 - (self._angle - angle)
                    )  # not sure if this is correct
                self._end = None
        elif center is not None:
            if angle is not None:
                self._init_from_center_angle_point(center, angle, start, mid, end)
            elif start is not None and end is not None:
                self._init_from_center_start_end(center, start, end, long_way)
            else:
                raise KeyError(
                    "Arcs defined with center point must define either an angle or endpoint."
                )
        elif start is not None and mid is not None and end is not None:
            self._init_from_3_point_arc(start, mid, end)

    def copy(self) -> Self:
        """Create a deep copy of itself."""
        arc = GeomArc.__new__(GeomArc)
        arc.center = self.center.copy()
        arc._start = self._start.copy()
        arc._angle = self._angle
        arc._end = None if self._end is None else self._end.copy()
        return cast(Self, arc)

    def get_atomic_shapes(self) -> list[GeomArc]:
        """Return a list with itself in it since an arc is an atomic shape."""
        return [self]

    def get_native_shapes(self) -> list[GeomArc]:
        """Return a list with itself in it since an arc is a basic shape."""
        return [self]

    def translate(self, vector: Vector2D) -> Self:
        """Move the arc.

        Args:
            vector: The direction and distance in mm.

        Returns:
            The translated arc.
        """
        self.center += vector
        self._start += vector
        if self._end:
            self._end += vector
        return self

    def rotate(
        self,
        angle: float,
        origin: Vector2D = Vector2D.zero(),
    ) -> Self:
        """Rotate the arc around a given point.

        Args:
            angle: Rotation angle in degrees.
            origin: Coordinates (in mm) of the point around which to rotate.

        Returns:
            The rotated arc.
        """
        self.center.rotate(angle=angle, origin=origin)
        self._start.rotate(angle=angle, origin=origin)
        self._end = None
        return self

    def bbox(self) -> BoundingBox:
        """Return the bounding box of the arc."""
        start = self._start
        end = self.end
        t_pt = self.center - Vector2D.from_floats(0.0, self.radius)
        l_pt = self.center - Vector2D.from_floats(self.radius, 0.0)
        b_pt = self.center + Vector2D.from_floats(0.0, self.radius)
        r_pt = self.center + Vector2D.from_floats(self.radius, 0.0)
        top = t_pt.y if self.is_point_on_self(t_pt) else min(start.y, end.y)
        left = l_pt.x if self.is_point_on_self(l_pt) else min(start.x, end.x)
        bottom = b_pt.y if self.is_point_on_self(b_pt) else max(start.y, end.y)
        right = r_pt.x if self.is_point_on_self(r_pt) else max(start.x, end.x)
        return BoundingBox([left, top], [right, bottom])

    def is_equal(self, other: GeomArc, tol: float = TOL_MM) -> bool:
        """Return wheather two arcs are identical or not.

        Args:
            other: The other arc.
            tol: The maximum deviation in mm that a dimension is allowed to have to be
            still considered to be equal to the same dimension in the other arc.

        Returns:
            `True` if the arcs are equal, `False` otherwise.
        """
        if not self._start.is_equal(point=other._start, tol=tol):
            return False
        if abs(self._angle - other._angle) > tol:
            return False
        if not self.center.is_equal(point=other.center, tol=tol):
            return False
        return True

    def point_to_local_polar_form(
        self, point: Vector2D, tol: float = TOL_MM
    ) -> tuple[float, float]:
        """Transform a point to polar coordinates relative to the center of the arc.

        Args:
            point: Coordinates (in mm) of the point to transform.
            tol: Tolerance in mm used to determine if a point is equal to the start
                point of the arc. If so, the angle returned for such a point is allowed
                to have the opposed sign of the angle of the arc.

        Returns:
            A tuple with (radius in mm, angle in degrees) representing the polar
            coordinates of the point relative to the center of the arc. The returned
            angle is in the range of (-180°, 180°].
        """
        rad_p = (point - self.center).norm()
        tol_d = tol_deg(tol, rad_p)
        ang_p_s = self.point_to_angle_relative_to_self(point)
        # If the angle is slightly negative, keep it that way. This point is identical
        # with the start point and instead of yielding 359.999° it should rather be
        # -0.001°:
        if tol_d is None or abs(ang_p_s) >= tol_d:
            ang_p_s %= 360
            if self._angle < 0 and ang_p_s > 0:
                ang_p_s -= 360

        return (rad_p, ang_p_s)

    def point_to_angle_relative_to_self(self, point: Vector2D) -> float:
        """Get the angle between the arc's starting point and the given point.

        The returned angle is in the range of (-360°, 360°], but always such that the
        returned angle is always less than 180° away from the end point.

        Args:
            point: Coordinates (in mm) of the point.

        Returns:
            The angle between start and the point in degrees. The returned angle is in
            the range of (-360°, 360°].
        """
        ang_s = (self._start - self.center).arg()
        ang_p = (point - self.center).arg()
        ang_p_s = ang_p - ang_s
        ang_e = ang_s + self._angle
        if ang_e - ang_p_s <= -180:
            ang_p_s -= 360
        elif ang_e - ang_p_s > 180:
            ang_p_s += 360
        return ang_p_s

    def is_point_on_self(
        self,
        point: Vector2D,
        exclude_segment_ends: bool = False,
        tol: float = TOL_MM,
    ) -> bool:
        """Check if a point is on the arc outline.

        Args:
            point: The coordinates (in mm) of the point.
            exclude_segment_ends: If `True`, then points within `tol` distance of the
                end points of the segment are not considered to be on the outline.
            tol : Distance in mm that the point is allowed to be away from the outline
                while still being considered to lay on the outline.

        Returns:
            `True` if the point is considered to be on the arc segment within the given
            tolerance, `False` otherwise.
        """
        radius = self.radius
        d_pc = hypot(point.x - self.center.x, point.y - self.center.y)
        if abs(radius - d_pc) > tol:
            return False

        if radius <= tol:  # No need to calculate angles if the arc is just a point:
            return True

        tol_d = degrees(tol / radius)
        # Rotate to local coordinate system (start point is at 0 degree):
        ang_p_s = self.point_to_angle_relative_to_self(point)
        if abs(ang_p_s) >= tol_d:
            ang_p_s %= 360
            if self._angle < 0 and ang_p_s > 0:
                ang_p_s -= 360
        tol_d = degrees(tol / radius)
        if exclude_segment_ends:
            if self._angle < 0:
                if ang_p_s < self._angle + tol_d:
                    return False
            else:
                if ang_p_s > self._angle - tol_d:
                    return False
        else:
            if self._angle < 0:
                if ang_p_s < self._angle - tol_d:
                    return False
            else:
                if ang_p_s > self._angle + tol_d:
                    return False
        return True

    def is_point_on_self_accelerated(
        self,
        point: Vector2D,
        exclude_segment_ends: bool = False,
        tol: float = TOL_MM,
    ) -> bool:
        """Check if a point is on the arc outline while knowing it is a point on a
        circle with equal radius and center as the arc. This allows for accelerated
        testing with respect to the `is_point_on_self()` function.

        Args:
            point: The coordinates (in mm) of the point.
            exclude_segment_ends: If `True`, then points within `tol` distance of the
                end points of the segment are not considered to be on the outline.
            tol : Distance in mm that the point is allowed to be away from the outline
                while still being considered to lay on the outline.

        Returns:
            `True` if the point is considered to be on the arc segment within the given
            tolerance, `False` otherwise.
        """
        point_center = point - self.center
        start_center = self._start - self.center

        angle_point = atan2(point_center.y, point_center.x)  # between -pi and +pi
        angle_start = atan2(start_center.y, start_center.x)  # between -pi and +pi
        angle_end = radians(self._angle)  # between -2pi and +2pi
        radius = self.radius
        if radius > tol:
            tol_rad = tol / radius  # `tol` in mm converted to `tol_rad` in radians
        else:
            return not exclude_segment_ends

        # Because we will use 2*pi a lot:
        pi2 = 2 * pi

        # angle between the point and start
        angle_point_start = (angle_point - angle_start) % pi2  # between 0 and +2pi

        # Check if the point is within `tol` distance from the starting point:
        if abs(angle_point_start) <= tol_rad or abs(angle_point_start - pi2) <= tol_rad:
            return not exclude_segment_ends

        # If the arc angle is negative and the point-to-start angle is positive, express
        # the point-to-start angle as a negative number to facilitate direct comparison:
        if angle_end < 0 and angle_point_start > 0:
            angle_point_start -= pi2

        # Check if the point is within `tol` distance from the end point:
        angle_point_end = (angle_point_start - angle_end) % pi2
        if abs(angle_point_end) <= tol_rad or abs(angle_point_end - pi2) <= tol_rad:
            return not exclude_segment_ends

        if self._angle < 0:
            if angle_point_start < angle_end:
                return False
        else:
            if angle_point_start > angle_end:
                return False
        return True

    def sort_points_relative_to_start(
        self,
        points: list[Vector2D],
        tol: float = TOL_MM,
    ) -> list[tuple[float, float, Vector2D]]:
        """Sort a list of points by angular distance from the start point of the arc.

        Args:
            points: The list of points.
            tol: The distance in mm that two points are allowed to be away from each
                other and still be considered identical.

        Returns:
            The sorted list of the points as a tuple containing in their polar form
            and their cartesian coordinates (`radius`, `angle`, coordinates).
        """
        local_points: list[tuple[float, tuple[float, float, Vector2D]]] = []
        for p in points:
            r, phi = self.point_to_local_polar_form(point=p, tol=tol)
            local_points.append((phi, (r, phi, p)))
        ps: list[tuple[float, float, Vector2D]] = []
        for _, pt in sorted(local_points, reverse=(self._angle < 0)):
            ps.append(pt)
        return ps

    def reverse(self) -> GeomArc:
        """Reverse the arc (start point becomes the end point and vice versa).

        Returns:
            The arc after reversing it.
        """
        temp = self._start
        self._start = self.end
        self._angle = -self._angle
        self._end = temp
        return self

    @property
    def radius(self) -> float:
        """The radius of the arc."""
        return (self._start - self.center).norm()

    @radius.setter
    def radius(self, radius: float) -> None:
        """The radius of the arc."""
        _, ang_s = self._start.to_polar(origin=self.center)
        self._start = Vector2D.from_polar(
            radius=radius, angle=ang_s, origin=self.center
        )
        self._end = None

    @property
    def mid(self) -> Vector2D:
        """The mid point of the arc."""
        return self._start.copy().rotate(self._angle / 2, origin=self.center)

    @property
    def end(self) -> Vector2D:
        """The end point of the arc."""
        if not self._end:
            self._end = self._start.copy().rotate(self._angle, origin=self.center)
        return self._end

    @end.setter
    def end(self, end: Vector2D) -> None:
        """Set the end point while keeping the start point and the direction the
        same.
        """
        self._end = end
        ang_e = (end - self.center).arg()
        ang_s = (self._start - self.center).arg()
        angle = ang_e - ang_s
        if self._angle * angle >= 0:
            self._init_angle(angle)
        else:
            self._init_angle(copysign(1, self._angle) * 360 + angle)

    @property
    def start(self) -> Vector2D:
        """The start point of the arc."""
        return self._start

    @start.setter
    def start(self, start: Vector2D) -> None:
        """Set the start point while keeping the end point and the direction the
        same.
        """
        ang_s = (self._start - self.center).arg()
        ang_p = (start - self.center).arg()
        angle = ang_s - ang_p
        self._init_angle(self._angle + angle)
        self._start = start

    def set_start(self, start: Vector2D) -> None:
        """Set the start point while keeping the angle constant. This rotates the end
        point.
        """
        self._start = start
        self._end = None

    @property
    def angle(self) -> float:
        """The angle of the arc."""
        return self._angle

    @angle.setter
    def angle(self, angle: float) -> None:
        """Set the angle of the arc and invalidate the end point."""
        self._angle = angle
        self._end = None

    @property
    def length(self) -> float:
        """The length of the arc segment."""
        return abs(radians(self._angle)) * self.radius

    @property
    def direction(self) -> int:
        """The direction of the arc segment."""
        if self._angle > 0:
            return 1
        elif self._angle < 0:
            return -1
        return 0

    def _init_angle(self, angle: float) -> float:
        """Convert the angle to a value between -360° and + 360°.

        Args:
            angle: Angle in degrees.

        Returns:
            The converted angle in degrees.
        """
        angle = angle % 720
        if angle > 360:
            angle -= 720
        self._angle = angle
        return self._angle

    def _init_from_center_angle_point(
        self,
        center: Vec2DCompatible,
        angle: float,
        start: Vec2DCompatible | None = None,
        mid: Vec2DCompatible | None = None,
        end: Vec2DCompatible | None = None,
    ) -> None:
        """Create an arc by using the center, the angle and a point.

        Args:
            center: Coordinates (in mm) of the center of the arc.
            angle: Angle of the arc in degrees.
            start: Coordinates (in mm) of the atart point of the arc.
            mid: Coordinates (in mm) of the mid point of the arc.
            end: Coordinates (in mm) of the end point of the arc.
        """
        self.center = Vector2D(center)
        self._init_angle(angle)

        if start is not None:
            self._start = Vector2D(start)
            self._end = None
        elif mid is not None:
            mp_r, mp_a = Vector2D(mid).to_polar(origin=self.center)
            self._start = Vector2D.from_polar(
                radius=mp_r,
                angle=mp_a - self._angle / 2,
                origin=self.center,
            )
            self._end = None
        elif end is not None:
            self._end = Vector2D(end)
            mp_r, mp_a = self._end.to_polar(origin=self.center)
            self._start = Vector2D.from_polar(
                radius=mp_r,
                angle=mp_a - self._angle,
                origin=self.center,
            )
        else:
            raise KeyError(
                "Arcs defined with 'center' and 'angle' must either define the 'start' or 'mid' or 'end' point."
            )

    def _init_from_center_start_end(
        self,
        center: Vec2DCompatible,
        start: Vec2DCompatible,
        end: Vec2DCompatible,
        long_way: bool = False,
    ) -> None:
        """Create an arc by using the center, start and end point.

        Args:
            center: Coordinates (in mm) of the center of the arc.
            start: Coordinates (in mm) of the start point of the arc.
            end: Coordinates (in mm) of the end point of the arc.
            long_way: `True` if the arc angle is > 180°, `False` otherwise.
        """
        if None in [center, start, end]:
            raise KeyError(
                "Arcs defined by 'center', 'start', and 'end' points must define all three."
            )

        self.center = Vector2D(center)
        self._start = Vector2D(start)
        self._end = Vector2D(end)
        sp_r, sp_a = self._start.to_polar(origin=self.center)
        ep_r, ep_a = self._end.to_polar(origin=self.center)

        if abs(sp_r - ep_r) > TOL_MM:
            raise ValueError(
                "Start and end points must be at equal distance from the center point."
            )
        self._init_angle(angle=ep_a - sp_a)

        if long_way:
            if abs(self._angle) < 180:
                self._angle = -copysign((360 - abs(self._angle)), self._angle)
            if self._angle == -180:
                self._angle = 180
        else:
            if abs(self._angle) > 180:
                self._angle = -copysign((abs(self._angle) - 360), self._angle)
            if self._angle == 180:
                self._angle = -180

    def _init_from_3_point_arc(
        self,
        start: Vec2DCompatible,
        mid: Vec2DCompatible,
        end: Vec2DCompatible,
    ) -> None:
        """Create an arc by using the start, mid and end point.

        Args:
            start: Coordinates (in mm) of the start point of the arc.
            mid: Coordinates (in mm) of the mid point of the arc.
            end: Coordinates (in mm) of the end point of the arc.
        """
        if None in (start, mid, end):
            raise KeyError(
                "Cannot construct Arc with just two points and no further parameters."
            )
        self._start = Vector2D(start)
        mid = Vector2D(mid)
        self._end = Vector2D(end)
        p1 = self._start.copy()
        p2 = mid.copy()
        p3 = self._end.copy()

        # prevent divide by zero
        if abs(p2.x - p1.x) < TOL_MM:
            # rotate points
            p1, p2, p3 = p2, p3, p1
        elif abs(p3.x - p2.x) < TOL_MM:
            # rotate point other direction
            p1, p2, p3 = p3, p1, p2

        # all Points are collinear in x or y
        if (
            abs(p2.x - p1.x) < TOL_MM
            and abs(p3.x - p2.x) < TOL_MM
            or abs(p2.y - p1.y) < TOL_MM
            and abs(p3.y - p2.y) < TOL_MM
        ):
            raise ValueError("This is not an arc")

        ma = (p2.y - p1.y) / (p2.x - p1.x)
        mb = (p3.y - p2.y) / (p3.x - p2.x)

        if abs(mb - ma) < TOL_MM:
            raise ValueError("This is not an arc")

        center_x = (
            ma * mb * (p1[1] - p3[1]) + mb * (p1[0] + p2[0]) - ma * (p2[0] + p3[0])
        ) / (2 * (mb - ma))

        # prevent divide by zero
        if abs(ma) < TOL_MM:
            center_y = (-1 / mb) * (center_x - (p2[0] + p3[0]) / 2) + (
                p2[1] + p3[1]
            ) / 2
        else:
            center_y = (-1 / ma) * (center_x - (p1[0] + p2[0]) / 2) + (
                p1[1] + p2[1]
            ) / 2

        center = Vector2D.from_floats(center_x, center_y)

        # Compute start and end angles
        def _angle_from_center(pt: Vector2D) -> float:
            return atan2(pt.y - center.y, pt.x - center.x)

        start_angle = _angle_from_center(self._start)
        end_angle = _angle_from_center(self._end)

        def _midpoint_is_cw_from(
            center: Vector2D, start: Vector2D, mid: Vector2D
        ) -> bool:
            v1 = start - center
            v2 = mid - center
            cross = v1.x * v2.y - v1.y * v2.x
            return cross < 0

        # Determine if the arc is clockwise
        cw = _midpoint_is_cw_from(center, p1, p2)

        # Compute sweep angle
        if cw:
            if end_angle > start_angle:
                end_angle -= 2 * pi
        else:
            if end_angle < start_angle:
                end_angle += 2 * pi

        sweep_angle = end_angle - start_angle

        # Store arc properties
        self.center = center
        self._init_angle(angle=degrees(sweep_angle))

    def __repr__(self) -> str:
        """Return the string representation of the arc."""
        return (
            f"GeomArc(center={self.center}, start={self._start}, angle={self._angle})"
        )
