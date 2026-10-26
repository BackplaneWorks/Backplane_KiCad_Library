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

from typing import Any, cast

from kilibs.geom import (
    BoundingBox,
    GeomArc,
    GeomCircle,
    GeomCompoundPolygon,
    GeomCross,
    GeomCruciform,
    GeomLine,
    GeomPolygon,
    GeomRectangle,
    GeomRoundRectangle,
    GeomShape,
    GeomStadium,
    GeomTrapezoid,
    Vector2D,
)
from kilibs.geom.tolerances import TOL_MM
from kilibs.geom.vector import Vec2DCompatible


def are_equal(
    objects1: list[Any],
    objects2: list[Any],
    may_permutate: bool = True,
    rel: float = TOL_MM,
) -> bool:
    """Check if two list of objects are approximately equal.
    The objects may be permutated.
    """
    if len(objects1) != len(objects2):
        return False
    if may_permutate == False:
        for i in range(len(objects1)):
            if not is_equal(a=objects1[i], b=objects2[i], rel=rel):
                return False
    else:
        for object1 in objects1:
            equal = False
            for object2 in objects2:
                if is_equal(a=object1, b=object2, rel=rel):
                    equal = True
                    break
            if equal == False:
                return False
    return True


def is_equal(a: Any, b: Any, rel: float = TOL_MM) -> bool:
    """Check if two objects are approximately equal."""
    if isinstance(a, float | int) and isinstance(b, float | int):
        return is_equal_val(a, b, rel)
    elif isinstance(a, Vector2D | list | tuple) and isinstance(
        b, Vector2D | list | tuple
    ):
        if isinstance(a, list | tuple):
            a = cast(list[int], a)
            a = [float(x) for x in a]
        if isinstance(b, list | tuple):
            b = cast(list[int], b)
            b = [float(x) for x in b]
        return is_equal_vectors(a, b, rel)
    elif isinstance(a, GeomShape) and isinstance(b, GeomShape):
        return is_equal_geom_shapes(a, b, rel)
    elif isinstance(a, BoundingBox) and isinstance(b, BoundingBox):
        return is_equal_bboxes(a, b, rel)
    else:
        return False


def is_equal_val(a: float | int, b: float | int, rel: float = TOL_MM) -> bool:
    """Check if two values are approximately equal."""
    return abs(a - b) <= rel


def is_equal_vector(vec: Vector2D, x: float, y: float, rel: float = TOL_MM) -> bool:
    """Check if a vector's properties is approximately equal to the parameters
    given.
    """
    return abs(vec.x - x) <= rel and abs(vec.y - y) <= rel


def is_equal_vectors(
    a: Vec2DCompatible, b: Vec2DCompatible, rel: float = TOL_MM
) -> bool:
    """Check if two vectors are approximately equal."""
    a = Vector2D(a)
    b = Vector2D(b)
    return is_equal_vector(vec=a, x=b.x, y=b.y, rel=rel)


def is_equal_geom_shapes(a: GeomShape, b: GeomShape, rel: float = TOL_MM) -> bool:
    """Check if two GeomShapes are approximately equal."""
    if isinstance(a, GeomArc) and isinstance(b, GeomArc):
        return is_equal_geom_arcs(a, b, rel=rel)
    elif isinstance(a, GeomLine) and isinstance(b, GeomLine):
        return is_equal_geom_lines(a, b, rel=rel)
    elif isinstance(a, GeomCross) and isinstance(b, GeomCross):
        return is_equal_geom_crosses(a, b, rel=rel)
    elif isinstance(a, GeomCircle) and isinstance(b, GeomCircle):
        return is_equal_geom_circles(a, b, rel=rel)
    elif isinstance(a, GeomRectangle) and isinstance(b, GeomRectangle):
        return is_equal_geom_rectangles(a, b, rel=rel)
    elif isinstance(a, GeomPolygon) and isinstance(b, GeomPolygon):
        return is_equal_geom_polygons(a, b, rel=rel)
    elif isinstance(a, GeomCompoundPolygon) and isinstance(b, GeomCompoundPolygon):
        return is_equal_geom_compound_polygons(a, b, rel=rel)
    elif isinstance(a, GeomStadium) and isinstance(b, GeomStadium):
        return is_equal_geom_stadiums(a, b, rel=rel)
    elif isinstance(a, GeomCruciform) and isinstance(b, GeomCruciform):
        return is_equal_geom_cruciforms(a, b, rel=rel)
    elif isinstance(a, GeomRoundRectangle) and isinstance(b, GeomRoundRectangle):
        return is_equal_geom_round_rectangles(a, b, rel=rel)
    elif isinstance(a, GeomTrapezoid) and isinstance(b, GeomTrapezoid):
        return is_equal_geom_trapezoids(a, b, rel=rel)
    else:
        return False


def is_equal_geom_arc(
    arc: GeomArc,
    angle: float,
    radius: float,
    center: Vec2DCompatible,
    start: Vec2DCompatible,
    mid: Vec2DCompatible,
    end: Vec2DCompatible,
    rel: float = TOL_MM,
) -> bool:
    """Check if an arc's properties is approximately equal to the parameters given."""
    if not is_equal_val(arc.angle, angle, rel=rel):
        return False
    if not is_equal_val(arc.radius, radius, rel=rel):
        return False
    if not is_equal_vectors(arc.center, center, rel=rel):
        return False
    if not is_equal_vectors(arc.start, start, rel=rel):
        return False
    if not is_equal_vectors(arc.mid, mid, rel=rel):
        return False
    if not is_equal_vectors(arc.end, end, rel=rel):
        return False
    return True


def is_equal_geom_arcs(a: GeomArc, b: GeomArc, rel: float = TOL_MM) -> bool:
    """Check if two arcs are approximately equal."""
    return is_equal_geom_arc(
        arc=a,
        angle=b.angle,
        radius=b.radius,
        center=b.center,
        start=b.start,
        mid=b.mid,
        end=b.end,
        rel=rel,
    )


def is_equal_geom_line(
    line: GeomLine,
    start: Vec2DCompatible,
    end: Vec2DCompatible,
    mid: Vector2D,
    direction: Vector2D,
    length: float,
    ordered: bool = True,
    rel: float = TOL_MM,
) -> bool:
    """Check if a line's properties is approximately equal to the parameters given."""
    if not is_equal_val(line.length, length, rel=rel):
        return False
    if not is_equal_vectors(line.mid, mid, rel=rel):
        return False
    if ordered:
        if not is_equal_vectors(line.direction, direction, rel=rel):
            return False
        if not is_equal_vectors(line.start, start, rel=rel):
            return False
        if not is_equal_vectors(line.end, end, rel=rel):
            return False
    else:
        if not is_equal_vectors(line.direction, -direction, rel=rel):
            return False
        if not is_equal_vectors(line.start, end, rel=rel):
            return False
        if not is_equal_vectors(line.end, start, rel=rel):
            return False
    return True


def is_equal_geom_lines(
    a: GeomLine, b: GeomLine, ordered: bool = True, rel: float = TOL_MM
) -> bool:
    """Check if two lines are approximately equal."""
    return is_equal_geom_line(
        line=a,
        start=b.start,
        end=b.end,
        mid=b.mid,
        direction=b.direction,
        length=b.length,
        ordered=ordered,
        rel=rel,
    )


def is_equal_geom_cross(
    cross: GeomCross,
    center: Vec2DCompatible,
    size: Vec2DCompatible,
    angle: float,
    rel: float = TOL_MM,
) -> bool:
    """Check if two crosses are approximately equal."""
    if not is_equal_val(cross.angle, angle, rel=rel):
        return False
    if not is_equal_vectors(cross.center, center, rel=rel):
        return False
    if not is_equal_vectors(cross.size, size, rel=rel):
        return False
    return True


def is_equal_geom_crosses(a: GeomCross, b: GeomCross, rel: float = TOL_MM) -> bool:
    """Check if two crosses are approximately equal."""
    return is_equal_geom_cross(
        cross=a,
        center=b.center,
        size=b.size,
        angle=b.angle,
        rel=rel,
    )


def is_equal_geom_circle(
    circle: GeomCircle,
    radius: float,
    center: Vec2DCompatible,
    mid: Vec2DCompatible,
    rel: float = TOL_MM,
) -> bool:
    """Check if a circle's properties is approximately equal to the parameters
    given.
    """
    if not is_equal_val(circle.radius, radius, rel=rel):
        return False
    if not is_equal_vectors(circle.center, center, rel=rel):
        return False
    if not is_equal_vectors(circle.mid, mid, rel=rel):
        return False
    return True


def is_equal_geom_circles(a: GeomCircle, b: GeomCircle, rel: float = TOL_MM) -> bool:
    """Check if two circles are approximately equal."""
    return is_equal_geom_circle(
        circle=a, radius=b.radius, center=b.center, mid=b.mid, rel=rel
    )


def is_equal_geom_polygon(
    polygon: GeomPolygon,
    points: list[Vector2D],
    segments: list[GeomLine],
    rel: float = TOL_MM,
) -> bool:
    """Check if a polygon's properties is approximately equal to the parameters
    given.
    """
    # for backward compatibility some polygons have the first point repeated
    # (closed explicitely) wihle others don't. We allow a difference of 1 point
    # in the length if the last point is equal to the first point.
    if len(polygon.points) == len(points) + 1:
        if not is_equal_vectors(polygon.points[0], polygon.points[-1]):
            return False
    elif len(polygon.points) + 1 == len(points):
        if not is_equal_vectors(points[0], points[-1]):
            return False
    else:
        if len(polygon.points) != len(points):
            return False
    for i in range(len(polygon.points)):
        if not is_equal_vectors(polygon.points[i], points[i], rel=rel):
            return False
    for i in range(len(polygon.segments)):
        if not is_equal_geom_lines(polygon.segments[i], segments[i], rel=rel):
            return False
    return True


def is_equal_geom_polygons(a: GeomPolygon, b: GeomPolygon, rel: float = TOL_MM) -> bool:
    """Check if two polygons are approximately equal."""
    return is_equal_geom_polygon(
        polygon=a, points=b.points, segments=b.segments, rel=rel
    )


def is_equal_geom_rectangle(
    rectangle: GeomRectangle,
    angle: float,
    center: Vec2DCompatible,
    size: Vec2DCompatible,
    points: list[Vector2D],
    min_dimension: float,
    max_dimension: float,
    left: float,
    right: float,
    top: float,
    bottom: float,
    top_left: Vec2DCompatible,
    top_right: Vec2DCompatible,
    bottom_left: Vec2DCompatible,
    bottom_right: Vec2DCompatible,
    right_midpoint: Vec2DCompatible,
    left_midpoint: Vec2DCompatible,
    top_midpoint: Vec2DCompatible,
    bottom_midpoint: Vec2DCompatible,
    rel: float = TOL_MM,
) -> bool:
    """Check if a rectangle's properties is approximately equal to the parameters given."""
    if not is_equal_val(rectangle.angle, angle, rel=rel):
        return False
    if not is_equal_vectors(rectangle.center, center, rel=rel):
        return False
    if not is_equal_vectors(rectangle.size, size, rel=rel):
        return False
    for i in range(len(rectangle.points)):
        if not is_equal_vectors(rectangle.points[i], points[i], rel=rel):
            return False
    if not is_equal_val(rectangle.min_dimension, min_dimension, rel=rel):
        return False
    if not is_equal_val(rectangle.max_dimension, max_dimension, rel=rel):
        return False
    if not is_equal_val(rectangle.left, left, rel=rel):
        return False
    if not is_equal_val(rectangle.right, right, rel=rel):
        return False
    if not is_equal_val(rectangle.top, top, rel=rel):
        return False
    if not is_equal_val(rectangle.bottom, bottom, rel=rel):
        return False
    if not is_equal_vectors(rectangle.top_left, top_left, rel=rel):
        return False
    if not is_equal_vectors(rectangle.top_right, top_right, rel=rel):
        return False
    if not is_equal_vectors(rectangle.bottom_left, bottom_left, rel=rel):
        return False
    if not is_equal_vectors(rectangle.bottom_right, bottom_right, rel=rel):
        return False
    if not is_equal_vectors(rectangle.right_midpoint, right_midpoint, rel=rel):
        return False
    if not is_equal_vectors(rectangle.left_midpoint, left_midpoint, rel=rel):
        return False
    if not is_equal_vectors(rectangle.top_midpoint, top_midpoint, rel=rel):
        return False
    if not is_equal_vectors(rectangle.bottom_midpoint, bottom_midpoint, rel=rel):
        return False
    return True


def is_equal_geom_rectangles(
    a: GeomRectangle, b: GeomRectangle, rel: float = TOL_MM
) -> bool:
    """Check if two rectangles are approximately equal."""
    return is_equal_geom_rectangle(
        rectangle=a,
        angle=b.angle,
        center=b.center,
        size=b.size,
        points=b.points,
        min_dimension=b.min_dimension,
        max_dimension=b.max_dimension,
        left=b.left,
        right=b.right,
        top=b.top,
        bottom=b.bottom,
        top_left=b.top_left,
        top_right=b.top_right,
        bottom_left=b.bottom_left,
        bottom_right=b.bottom_right,
        right_midpoint=b.right_midpoint,
        left_midpoint=b.left_midpoint,
        top_midpoint=b.top_midpoint,
        bottom_midpoint=b.bottom_midpoint,
        rel=rel,
    )


def is_equal_geom_compound_polygon(
    compound_polygon: GeomCompoundPolygon,
    close: bool,
    segments: list[GeomArc | GeomLine],
    rel: float = TOL_MM,
) -> bool:
    if compound_polygon.close != close:
        return False
    if len(segments) != len(compound_polygon.get_atomic_shapes()):
        return False
    for i, segment in enumerate(compound_polygon.get_atomic_shapes()):
        if not is_equal_geom_shapes(segments[i], segment, rel=rel):
            return False
    return True


def is_equal_geom_compound_polygons(
    a: GeomCompoundPolygon, b: GeomCompoundPolygon, rel: float = TOL_MM
) -> bool:
    return is_equal_geom_compound_polygon(
        compound_polygon=a,
        close=b.close,
        segments=b.get_atomic_shapes(),
        rel=rel,
    )


def is_equal_geom_stadium(
    stadium: GeomStadium,
    centers: list[Vector2D],
    radius: float,
    rel: float = TOL_MM,
) -> bool:
    if not is_equal_vectors(stadium.centers[0], centers[0], rel):
        return False
    if not is_equal_vectors(stadium.centers[1], centers[1], rel):
        return False
    if not is_equal_val(stadium.radius, radius, rel):
        return False
    return True


def is_equal_geom_stadiums(a: GeomStadium, b: GeomStadium, rel: float = TOL_MM) -> bool:
    return is_equal_geom_stadium(
        stadium=a,
        centers=b.centers,
        radius=b.radius,
        rel=rel,
    )


def is_equal_geom_cruciform(
    cruciform: GeomCruciform,
    center: Vector2D,
    overall_h: float,
    overall_w: float,
    tail_h: float,
    tail_w: float,
    rel: float = TOL_MM,
) -> bool:
    if not is_equal_vectors(cruciform.center, center, rel):
        return False
    if not is_equal_val(cruciform.overall_h, overall_h, rel):
        return False
    if not is_equal_val(cruciform.overall_w, overall_w, rel):
        return False
    if not is_equal_val(cruciform.tail_h, tail_h, rel):
        return False
    if not is_equal_val(cruciform.tail_w, tail_w, rel):
        return False
    return True


def is_equal_geom_cruciforms(
    a: GeomCruciform, b: GeomCruciform, rel: float = TOL_MM
) -> bool:
    return is_equal_geom_cruciform(
        cruciform=a,
        center=b.center,
        overall_h=b.overall_h,
        overall_w=b.overall_w,
        tail_h=b.tail_h,
        tail_w=b.tail_w,
        rel=rel,
    )


def is_equal_geom_round_rectangle(
    round_rectangle: GeomRoundRectangle,
    center: Vec2DCompatible,
    size: Vec2DCompatible,
    corner_radius: float,
    angle: float,
    rel: float = TOL_MM,
) -> bool:
    if not is_equal_vectors(round_rectangle.center, center, rel):
        return False
    if not is_equal_vectors(round_rectangle.size, size, rel):
        return False
    if not is_equal_val(round_rectangle.corner_radius, corner_radius, rel):
        return False
    if not is_equal_val(round_rectangle.angle, angle, rel):
        return False
    return True


def is_equal_geom_round_rectangles(
    a: GeomRoundRectangle, b: GeomRoundRectangle, rel: float = TOL_MM
) -> bool:
    return is_equal_geom_round_rectangle(
        round_rectangle=a,
        center=b.center,
        size=b.size,
        corner_radius=b.corner_radius,
        angle=b.angle,
        rel=rel,
    )


def is_equal_geom_trapezoid(
    trapezoid: GeomTrapezoid,
    center: Vec2DCompatible,
    size: Vec2DCompatible,
    corner_radius: float,
    side_angle: float,
    rotation_angle: float,
    rel: float = TOL_MM,
) -> bool:
    if not is_equal_vectors(trapezoid.center, center, rel):
        return False
    if not is_equal_vectors(trapezoid.size, size, rel):
        return False
    if not is_equal_val(trapezoid.corner_radius, corner_radius, rel):
        return False
    if not is_equal_val(trapezoid.side_angle, side_angle, rel):
        return False
    if not is_equal_val(trapezoid.rotation_angle, rotation_angle, rel):
        return False
    return True


def is_equal_geom_trapezoids(
    a: GeomTrapezoid, b: GeomTrapezoid, rel: float = TOL_MM
) -> bool:
    return is_equal_geom_trapezoid(
        trapezoid=a,
        center=b.center,
        size=b.size,
        corner_radius=b.corner_radius,
        side_angle=b.side_angle,
        rotation_angle=b.rotation_angle,
        rel=rel,
    )


def is_equal_bbox(
    bbox: BoundingBox,
    center: Vec2DCompatible,
    size: Vec2DCompatible,
    min_dimension: Vector2D | None,
    max_dimension: Vector2D | None,
    left: float,
    right: float,
    top: float,
    bottom: float,
    top_left: Vec2DCompatible,
    top_right: Vec2DCompatible,
    bottom_left: Vec2DCompatible,
    bottom_right: Vec2DCompatible,
    right_midpoint: Vec2DCompatible,
    left_midpoint: Vec2DCompatible,
    top_midpoint: Vec2DCompatible,
    bottom_midpoint: Vec2DCompatible,
    rel: float = TOL_MM,
) -> bool:
    """Check if a rectangle's properties is approximately equal to the parameters given."""
    if bbox.min is not None and min_dimension is not None:
        if not is_equal_vectors(bbox.min, min_dimension, rel=rel):
            return False
    elif type(bbox.min) != type(min_dimension):
        return False
    if bbox.max is not None and max_dimension is not None:
        if not is_equal_vectors(bbox.max, max_dimension, rel=rel):
            return False
    elif type(bbox.max) != type(max_dimension):
        return False
    if not is_equal_val(bbox.left, left, rel=rel):
        return False
    if not is_equal_val(bbox.right, right, rel=rel):
        return False
    if not is_equal_val(bbox.top, top, rel=rel):
        return False
    if not is_equal_val(bbox.bottom, bottom, rel=rel):
        return False
    if not is_equal_vectors(bbox.top_left, top_left, rel=rel):
        return False
    if not is_equal_vectors(bbox.top_right, top_right, rel=rel):
        return False
    if not is_equal_vectors(bbox.bottom_left, bottom_left, rel=rel):
        return False
    if not is_equal_vectors(bbox.bottom_right, bottom_right, rel=rel):
        return False
    if not is_equal_vectors(bbox.right_midpoint, right_midpoint, rel=rel):
        return False
    if not is_equal_vectors(bbox.left_midpoint, left_midpoint, rel=rel):
        return False
    if not is_equal_vectors(bbox.top_midpoint, top_midpoint, rel=rel):
        return False
    if not is_equal_vectors(bbox.bottom_midpoint, bottom_midpoint, rel=rel):
        return False
    if not is_equal_vectors(bbox.center, center, rel=rel):
        return False
    if not is_equal_vectors(bbox.size, size, rel=rel):
        return False
    return True


def is_equal_bboxes(a: BoundingBox, b: BoundingBox, rel: float = TOL_MM) -> bool:
    """Check if two bounding boxes are approximately equal."""
    return is_equal_bbox(
        bbox=a,
        center=b.center,
        size=b.size,
        min_dimension=b.min,
        max_dimension=b.max,
        left=b.left,
        right=b.right,
        top=b.top,
        bottom=b.bottom,
        top_left=b.top_left,
        top_right=b.top_right,
        bottom_left=b.bottom_left,
        bottom_right=b.bottom_right,
        right_midpoint=b.right_midpoint,
        left_midpoint=b.left_midpoint,
        top_midpoint=b.top_midpoint,
        bottom_midpoint=b.bottom_midpoint,
        rel=rel,
    )
