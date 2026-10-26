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

"""Functions to obtain the intersection points between atomic shapes."""

import math

from kilibs.geom.shapes.geom_arc import GeomArc
from kilibs.geom.shapes.geom_circle import GeomCircle
from kilibs.geom.shapes.geom_line import GeomLine
from kilibs.geom.shapes.geom_shape_alias import GeomShapesAtomic
from kilibs.geom.tolerances import TOL_MM
from kilibs.geom.vector import Vector2D


def get_intersection_points_of_atomic_shapes(
    shape1: GeomShapesAtomic,
    shape2: GeomShapesAtomic,
    exclude_tangents: bool = False,
    exclude_segment_ends_shape1: bool = False,
    exclude_segment_ends_shape2: bool = False,
    infinite_line: bool = False,
    tol: float = TOL_MM,
) -> list[Vector2D]:
    """Intersect two atomic geometric shapes.

    Args:
        shape1: One of the two shapes to intersect with each other.
        shape2: The other shape to intersect with.
        exclude_tangents: If `True` tangent points (single intersections) are
            removed from the results.
        exclude_segment_ends_shape1: `True` if intersections coinciding with one of
            the ends of the `shape1` shall be removed from the results.
        exclude_segment_ends_shape2: `True` if intersections coinciding with one of
            the ends of the `shape2` shall be removed from the results.
        infinite_line: `True` if the lines shall be considered to be infinitely
            long (the intersection points can lie outside of the segments).
        tol: Tolerance in mm used to determine if two points are identical.

    Returns:
        List of intersection points.
    """
    if isinstance(shape1, GeomLine):
        return get_intersection_points_of_line_with_atomic_shape(
            line=shape1,
            shape=shape2,
            exclude_tangents=exclude_tangents,
            exclude_segment_ends_line=exclude_segment_ends_shape1,
            exclude_segment_ends_shape=exclude_segment_ends_shape2,
            infinite_line=infinite_line,
            tol=tol,
        )
    elif isinstance(shape1, GeomArc):
        return get_intersection_points_of_arc_with_atomic_shape(
            arc=shape1,
            shape=shape2,
            exclude_tangents=exclude_tangents,
            exclude_segment_ends_arc=exclude_segment_ends_shape1,
            exclude_segment_ends_shape=exclude_segment_ends_shape2,
            infinite_line=infinite_line,
            tol=tol,
        )
    else:  # isinstance(shape1, GeomCircle):
        return get_intersection_points_of_circle_with_atomic_shape(
            circle=shape1,
            shape=shape2,
            exclude_tangents=exclude_tangents,
            exclude_segment_ends_shape=exclude_segment_ends_shape2,
            infinite_line=infinite_line,
            tol=tol,
        )


def get_intersection_points_of_arc_with_atomic_shape(
    arc: GeomArc,
    shape: GeomShapesAtomic,
    exclude_tangents: bool = False,
    exclude_segment_ends_arc: bool = False,
    exclude_segment_ends_shape: bool = False,
    infinite_line: bool = False,
    tol: float = TOL_MM,
) -> list[Vector2D]:
    """Intersect an arc with an atomic geometric shape.

    Args:
        arc: The arc.
        shape: The other shape.
        exclude_tangents: If `True` tangent points (single intersections) are
            removed from the results.
        exclude_segment_ends_arc: `True` if intersections coinciding with one of
            the ends of the `arc` shall be removed from the results.
        exclude_segment_ends_shape: `True` if intersections coinciding with one of
            the ends of the `shape` shall be removed from the results.
        infinite_line: `True` if the lines shall be considered to be infinitely
            long (the intersection points can lie outside of the segments).
        tol: Tolerance in mm used to determine if two points are identical.

    Returns:
        List of intersection points.
    """
    if isinstance(shape, GeomLine):
        return get_intersection_points_of_arc_with_line(
            arc=arc,
            line=shape,
            exclude_tangents=exclude_tangents,
            exclude_segment_ends_arc=exclude_segment_ends_arc,
            exclude_segment_ends_line=exclude_segment_ends_shape,
            infinite_line=infinite_line,
            tol=tol,
        )
    elif isinstance(shape, GeomArc):
        return get_intersection_points_of_arcs(
            arc1=arc,
            arc2=shape,
            exclude_tangents=exclude_tangents,
            exclude_segment_ends_arc1=exclude_segment_ends_arc,
            exclude_segment_ends_arc2=exclude_segment_ends_shape,
            infinite_line=infinite_line,
            tol=tol,
        )
    else:  # isinstance(shape, GeomCircle):
        return get_intersection_points_of_arc_with_circle(
            arc=arc,
            circle=shape,
            exclude_tangents=exclude_tangents,
            exclude_segment_ends=exclude_segment_ends_arc,
            infinite_line=infinite_line,
            tol=tol,
        )


def get_intersection_points_of_circle_with_atomic_shape(
    circle: GeomCircle,
    shape: GeomShapesAtomic,
    exclude_tangents: bool = False,
    exclude_segment_ends_shape: bool = False,
    infinite_line: bool = False,
    tol: float = TOL_MM,
) -> list[Vector2D]:
    """Intersect a circle with an atomic geometric shape.

    Args:
        circle: The circle.
        shape: The other shape.
        exclude_tangents: If `True` tangent points (single intersections) are
            removed from the results.
        exclude_segment_ends_shape: `True` if intersections coinciding with one of
            the ends of the `shape` shall be removed from the results.
        infinite_line: `True` if the lines shall be considered to be infinitely
            long (the intersection points can lie outside of the segments).
        tol: Tolerance in mm used to determine if two points are identical.

    Returns:
        List of intersection points.
    """
    if isinstance(shape, GeomLine):
        return get_intersection_points_of_circle_with_line(
            circle=circle,
            line=shape,
            exclude_tangents=exclude_tangents,
            exclude_segment_ends=exclude_segment_ends_shape,
            infinite_line=infinite_line,
            tol=tol,
        )
    elif isinstance(shape, GeomArc):
        return get_intersection_points_of_arc_with_circle(
            arc=shape,
            circle=circle,
            exclude_tangents=exclude_tangents,
            exclude_segment_ends=exclude_segment_ends_shape,
            infinite_line=infinite_line,
            tol=tol,
        )
    else:  # isinstance(shape, GeomCircle):
        return get_intersection_points_of_circles(
            circle1=circle,
            circle2=shape,
            exclude_tangents=exclude_tangents,
            tol=tol,
        )


def get_intersection_points_of_line_with_atomic_shape(
    line: GeomLine,
    shape: GeomShapesAtomic,
    exclude_tangents: bool = False,
    exclude_segment_ends_line: bool = False,
    exclude_segment_ends_shape: bool = False,
    infinite_line: bool = False,
    tol: float = TOL_MM,
) -> list[Vector2D]:
    """Intersect a line with an atomic geometric shape.

    Args:
        line: The line.
        shape: The other shape.
        exclude_tangents: If `True` tangent points (single intersections) are
            removed from the results.
        exclude_segment_ends_line: `True` if intersections coinciding with one of
            the ends of the `line` shall be removed from the results.
        exclude_segment_ends_shape: `True` if intersections coinciding with one of
            the ends of the `shape` shall be removed from the results.
        infinite_line: `True` if the lines shall be considered to be infinitely
            long (the intersection points can lie outside of the segments).
        tol: Tolerance in mm used to determine if two points are identical.

    Returns:
        List of intersection points.
    """
    if isinstance(shape, GeomLine):
        return get_intersection_points_of_lines(
            line1=line,
            line2=shape,
            exclude_segment_ends_line1=exclude_segment_ends_line,
            exclude_segment_ends_line2=exclude_segment_ends_shape,
            infinite_line=infinite_line,
            tol=tol,
        )
    elif isinstance(shape, GeomArc):
        return get_intersection_points_of_arc_with_line(
            arc=shape,
            line=line,
            exclude_tangents=exclude_tangents,
            exclude_segment_ends_arc=exclude_segment_ends_shape,
            exclude_segment_ends_line=exclude_segment_ends_line,
            infinite_line=infinite_line,
            tol=tol,
        )
    else:  # isinstance(shape, GeomCircle):
        return get_intersection_points_of_circle_with_line(
            circle=shape,
            line=line,
            exclude_tangents=exclude_tangents,
            exclude_segment_ends=exclude_segment_ends_line,
            infinite_line=infinite_line,
            tol=tol,
        )


def get_intersection_points_of_arcs(
    arc1: GeomArc,
    arc2: GeomArc,
    exclude_tangents: bool = False,
    exclude_segment_ends_arc1: bool = False,
    exclude_segment_ends_arc2: bool = False,
    infinite_line: bool = False,
    tol: float = TOL_MM,
) -> list[Vector2D]:
    """Intersect two arcs.

    Args:
        arc1: One of the two arcs to intersect with each other.
        arc2: The other arc to intersect with.
        exclude_tangents: If `True` tangent points (single intersections) are
            removed from the results.
        exclude_segment_ends_arc1: `True` if intersections coinciding with one of
            the ends of the `arc1` shall be ignored.
        exclude_segment_ends_arc2: `True` if intersections coinciding with one of
            the ends of the `arc2` shall be ignored.
        tol: Tolerance in mm used to determine if two points are identical.

    Returns:
        List of intersection points.
    """
    arc1_circle = GeomCircle(center=arc1.center, radius=arc1.radius)
    pts = get_intersection_points_of_arc_with_circle(
        arc=arc2,
        circle=arc1_circle,
        exclude_tangents=exclude_tangents,
        exclude_segment_ends=exclude_segment_ends_arc2,
        infinite_line=infinite_line,
        tol=tol,
    )
    # Discard points that are not on the arc itself
    if infinite_line:
        return pts
    pts = [
        pt
        for pt in pts
        if arc1.is_point_on_self_accelerated(
            point=pt, exclude_segment_ends=exclude_segment_ends_arc1, tol=tol
        )
    ]
    return pts


def get_intersection_points_of_arc_with_circle(
    arc: GeomArc,
    circle: GeomCircle,
    exclude_tangents: bool = False,
    exclude_segment_ends: bool = False,
    infinite_line: bool = False,
    tol: float = TOL_MM,
) -> list[Vector2D]:
    """Intersect an arc with an circle.

    Args:
        arc: The arc.
        circle: The circle.
        exclude_tangents: If `True` tangent points (single intersections) are
            removed from the results.
        exclude_segment_ends: `True` if intersections coinciding with one of
            the ends of the `arc` shall be ignored.
        tol: Tolerance in mm used to determine if two points are identical.

    Returns:
        List of intersection points.
    """
    arc_circle = GeomCircle(center=arc.center, radius=arc.radius)
    pts = get_intersection_points_of_circles(
        circle1=circle,
        circle2=arc_circle,
        exclude_tangents=exclude_tangents,
        tol=tol,
    )
    # Discard points that are not on the arc itself
    if not infinite_line:
        pts = [
            pt
            for pt in pts
            if arc.is_point_on_self_accelerated(
                point=pt, exclude_segment_ends=exclude_segment_ends, tol=tol
            )
        ]
    return pts


def get_intersection_points_of_arc_with_line(
    arc: GeomArc,
    line: GeomLine,
    exclude_tangents: bool = False,
    exclude_segment_ends_arc: bool = False,
    exclude_segment_ends_line: bool = False,
    infinite_line: bool = False,
    tol: float = TOL_MM,
) -> list[Vector2D]:
    """Intersect an arc with an line.

    Args:
        arc: The arc.
        line: The line.
        exclude_tangents: If `True` tangent points (single intersections) are
            removed from the results.
        exclude_segment_ends_arc: `True` if intersections coinciding with one of
            the ends of the `arc` shall be ignored.
        exclude_segment_ends_line: `True` if intersections coinciding with one of
            the ends of the `line` shall be ignored.
        infinite_line: `True` if the line shall be considered to be infinitely
            long (the intersection points can lie outside of the segments).
        tol: Tolerance in mm used to determine if two points are identical.

    Returns:
        List of intersection points.
    """
    arc_circle = GeomCircle(arc)
    pts = get_intersection_points_of_circle_with_line(
        circle=arc_circle,
        line=line,
        exclude_tangents=exclude_tangents,
        exclude_segment_ends=exclude_segment_ends_line,
        infinite_line=infinite_line,
        tol=tol,
    )
    # Remove the points that are not on the arc segment:
    pts = [
        pt
        for pt in pts
        if arc.is_point_on_self_accelerated(
            point=pt, exclude_segment_ends=exclude_segment_ends_arc, tol=tol
        )
    ]
    return pts


def get_intersection_points_of_circles(
    circle1: GeomCircle,
    circle2: GeomCircle,
    exclude_tangents: bool = False,
    tol: float = TOL_MM,
) -> list[Vector2D]:
    """Intersect two circle.

    Args:
        circle1: One of the two arcs to intersect with each other.
        circle2: The other arc to intersect with.
        exclude_tangents: If `True` tangent points (single intersections) are
            removed from the results.
        tol: Tolerance in mm used to determine if two points are identical.

    Returns:
        List of intersection points.
    """
    # from https://mathworld.wolfram.com/Circle-CircleIntersection.html
    # Equations are for circle1 center on (0, 0) and circle2 center on (d, 0)
    # so we translate the results back accordingly
    r1, r2 = circle1.radius, circle2.radius
    d, phi = (circle2.center - circle1.center).to_polar()

    # Circles are too far away to touch
    if r1 + r2 + tol < d:
        return []

    # One circle is inside the other
    if d + tol < abs(r1 - r2):
        return []

    if abs(d) < tol:
        # circles have the same center
        if abs(r2) < tol and abs(r1) < tol:
            # circles have both radius zero --> return common center
            x = y = 0.0
        else:
            return []  # the two circles are identical
    else:
        x = (d**2 - r2**2 + r1**2) / (2 * d)

        # The circles are tangent - the point lies r1 from the center of circle1
        # This defends against sqrt(negative), as well as returning two almost identical
        # points when the circles are tangent.
        if abs(abs(x) - r1) < tol:
            y = 0
        else:
            numerator = 4 * d**2 * r1**2 - (d**2 - r2**2 + r1**2) ** 2
            y = math.sqrt(numerator) / d

    signs = [0.0] if (y < tol) else [0.5, -0.5]
    origin = Vector2D.from_floats(0.0, 0.0)
    pts = [
        Vector2D(x, s * y).rotate(angle=phi, origin=origin) + circle1.center
        for s in signs
    ]
    if len(pts) == 1 and exclude_tangents:
        return []
    else:
        return pts


def get_intersection_points_of_circle_with_line(
    circle: GeomCircle,
    line: GeomLine,
    exclude_segment_ends: bool = False,
    exclude_tangents: bool = False,
    infinite_line: bool = False,
    tol: float = TOL_MM,
) -> list[Vector2D]:
    """Intersect an circle with a line.

    Args:
        circle: The circle.
        line: The line.
        exclude_segment_ends_line: `True` if intersections coinciding with one of
            the ends of the `line` shall be ignored.
        exclude_tangents: If `True` tangent points (single intersections) are
            removed from the results.
        infinite_line: `True` if the line shall be considered to be infinitely
            long (the intersection points can lie outside of the segments).
        tol: Tolerance in mm used to determine if two points are identical.

    Returns:
        List of intersection points.
    """
    # from http://mathworld.wolfram.com/Circle-LineIntersection.html
    # Equations are for circle center on (0, 0) so we translate everything
    # to the origin (well the line anyways as we do only need the radius of the circle)
    lt = line.translated(-circle.center)
    d = lt.end - lt.start
    dr = d.norm()
    if dr < tol:  # line has length zero
        if circle.is_point_on_self(point=lt.mid, tol=tol):
            return [lt.start]
        else:
            return []
    D = lt.start.x * lt.end.y - lt.end.x * lt.start.y
    discriminant = circle.radius**2 * dr**2 - D**2
    pts: list[Vector2D] = []
    if discriminant < 0:
        if abs(discriminant) < tol:
            discriminant = 0
        else:
            return []
    dr2 = dr**2
    sqrt_discriminant_div_r2 = math.sqrt(discriminant) / dr2

    def calc_point(sign: int) -> Vector2D:
        return (
            Vector2D.from_floats(
                (
                    D * d.y / dr2
                    + sign * math.copysign(1, d.y) * d.x * sqrt_discriminant_div_r2
                ),
                (-D * d.x / dr2 + sign * abs(d.y) * sqrt_discriminant_div_r2),
            )
            + circle.center
        )

    pt1 = calc_point(1)
    pt2 = calc_point(-1)
    # Test if the two points can be considered to be a single point. We test if the
    # distance between the center of these two points and the border of the circle is
    # smaller than `tol`.
    pt_mid = (pt1 + pt2) / 2
    dist_mid_pt_border_of_circle = abs((pt_mid - circle.center).norm() - circle.radius)
    if dist_mid_pt_border_of_circle <= tol:
        pts = [pt_mid]
    else:
        pts = [pt1, pt2]

    # Test if the point is tangent (only one intersection point) and needs to be removed
    if exclude_tangents and len(pts) == 1:
        return []

    # Discard points that are not on the line segment itself
    if not infinite_line:
        pts = [
            pt
            for pt in pts
            if line.is_point_on_self_accelerated(
                point=pt, exclude_segment_ends=exclude_segment_ends, tol=tol
            )
        ]
    return pts


def get_intersection_points_of_lines(
    line1: GeomLine,
    line2: GeomLine,
    exclude_segment_ends_line1: bool = False,
    exclude_segment_ends_line2: bool = False,
    infinite_line: bool = False,
    tol: float = TOL_MM,
) -> list[Vector2D]:
    """Intersect two lines.

    Args:
        line1: One of the two lines to intersect with each other.
        line2: The other line to intersect with.
        exclude_segment_ends_line1: `True` if intersections coinciding with one of
            the ends of `line1` shall be ignored.
        exclude_segment_ends_line2: `True` if intersections coinciding with one of
            the ends of `line2` shall be ignored.
        infinite_line: `True` if the lines shall be considered to be infinitely
            long (the intersection points can lie outside of the segments).
        tol: Tolerance in mm used to determine if two segments are parallel.

    Returns:
        List of intersection points.
    """
    # Note: The code is optimized for speed and thus uses "manual" implementations
    # of the various functions.

    # Most of the times the lines are either horizontal or vertical - hence we can
    # accelerate the calculations:
    # We use homogeneous coordinates here:
    l1_x, l1_y, l1_z = line1.to_homogeneous()
    l2_x, l2_y, l2_z = line2.to_homogeneous()

    # Cross product:
    ip_x, ip_y, ip_z = (
        l1_y * l2_z - l1_z * l2_y,
        l1_z * l2_x - l1_x * l2_z,
        l1_x * l2_y - l1_y * l2_x,
    )
    if abs(ip_z) <= tol:
        return []  # The lines are parallel

    # Back to homogenous presentation:
    pt = Vector2D.from_floats(ip_x / ip_z, ip_y / ip_z)

    if infinite_line:
        return [pt]

    # Test that the point is on both line segments
    if line1.is_point_on_self_accelerated(
        point=pt, exclude_segment_ends=exclude_segment_ends_line1, tol=tol
    ) and line2.is_point_on_self_accelerated(
        point=pt, exclude_segment_ends=exclude_segment_ends_line2, tol=tol
    ):
        return [pt]

    # The lines are not parallel, but the intersection point is not on neither line
    return []


def get_intersection_points_of_upwards_ray_with_line(
    ray_start: Vector2D,
    line: GeomLine,
    tol: float = TOL_MM,
) -> list[Vector2D]:
    """Intersect a line segment with a vertical ray, i.e. another line segment that is
    vertical and infinitly long in direction of the y-axis.

    Args:
        ray_start: The start point of the ray.
        line: The line segment to intersect with.
        tol: Tolerance in mm used to determine if two segments are parallel.

    Returns:
        List of intersection points.
    """
    # Note: The code is optimized for speed and thus uses "manual" implementations
    # of the various functions.
    d2 = line.direction
    if abs(d2.x) <= tol:
        return []  # The lines are parallel
    elif abs(d2.y) <= tol:
        pt = Vector2D.from_floats(ray_start.x, line.start.y)
    else:
        l2_x, l2_y, l2_z = line.to_homogeneous()
        pt = Vector2D.from_floats(ray_start.x, -(ray_start.x * l2_x + l2_z) / l2_y)
    # Test that the point is on the line segment and on the ray
    if ray_start.y <= (pt.y + tol) and line.is_point_on_self_accelerated(
        point=pt, exclude_segment_ends=False, tol=tol
    ):
        # If the intersection happens to be on the start of the segment, it means that
        # it is also on the end of the previous segment. We don't want to count
        # the same intersectino twice, so we ignore it in that case:
        if pt.is_equal(line.start, tol=tol):
            return []
        else:
            return [pt]
    # The lines are not parallel, but the intersection point is not on neither line
    return []


def get_intersection_points_of_upwards_ray_with_circle(
    ray_start: Vector2D,
    circle: GeomCircle,
    exclude_tangents: bool = False,
    tol: float = TOL_MM,
) -> list[Vector2D]:
    """Intersect a circle with a vertical ray, i.e. a line segment that is vertical and
    infinitly long in direction of the y-axis.

    Args:
        ray_start: The start point of the ray.
        circle: The circle to intersect with.
        exclude_tangents: Whether to exclucde tangent points form the solution.
        tol: Tolerance in mm used to determine if two segments are parallel.

    Returns:
        List of intersection points.
    """
    ips: list[Vector2D] = []
    x = ray_start.x
    cx, cy = circle.center.x, circle.center.y

    # Calculate the horizontal distance between the line and the circle's center
    dx = abs(x - cx)

    if dx >= circle.radius + tol:
        return []
    elif dx >= circle.radius - tol:
        if exclude_tangents:
            return []
        else:  # Tangent: one intersection point
            ips.append(Vector2D.from_floats(x, cy))
    else:
        y_offset_sq = circle.radius**2 - dx**2
        y_offset = math.sqrt(y_offset_sq)
        y = cy + y_offset
        if ray_start.y <= y:
            ips.append(Vector2D.from_floats(x, y))
            y = cy - y_offset
            if ray_start.y <= y:
                ips.append(Vector2D.from_floats(x, y))
    return ips


def get_intersection_points_of_upwards_ray_with_arc(
    ray_start: Vector2D,
    arc: GeomArc,
    exclude_tangents: bool = False,
    tol: float = TOL_MM,
) -> list[Vector2D]:
    """Intersect an arc with a vertical ray, i.e. a line segment that is vertical and
    infinitly long in direction of the y-axis.

    Args:
        ray_start: The start point of the ray.
        arc: The arc segment to intersect with.
        exclude_tangents: Whether to exclucde tangent points form the solution.
        tol: Tolerance in mm used to determine if two segments are parallel.

    Returns:
        List of intersection points.
    """
    circle = GeomCircle(shape=arc)
    ips = get_intersection_points_of_upwards_ray_with_circle(
        ray_start=ray_start, circle=circle, exclude_tangents=exclude_tangents, tol=tol
    )
    intersections: list[Vector2D] = []
    for pt in ips:
        if arc.is_point_on_self_accelerated(
            point=pt, exclude_segment_ends=False, tol=tol
        ):
            # If the intersection happens to be on the start of the segment, it means that
            # it is also on the end of the previous segment. We don't want to count
            # the same intersectino twice, so we ignore it in that case:
            if not pt.is_equal(arc.start, tol=tol):
                intersections.append(pt)
    return intersections
