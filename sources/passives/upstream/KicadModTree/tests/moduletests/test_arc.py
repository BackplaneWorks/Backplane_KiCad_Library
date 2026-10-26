import math

import pytest

from KicadModTree import *
from KicadModTree.tests.test_utils.fp_file_test import SerialisationTest
from kilibs.geom import GeomArc, GeomCircle, Vector2D
from kilibs.geom.operations.intersection_points import get_intersection_points
from tests.kilibs.geom.is_equal import is_equal_val, is_equal_vectors


def assert_arc_geom(
    arc: GeomArc, start, end, center, mid, radius: float, angle: float
) -> None:
    """
    Assert that the arc has the given geometry
    """
    assert is_equal_vectors(arc.start, start)
    assert is_equal_vectors(arc.end, end)
    assert is_equal_vectors(arc.center, center)
    assert is_equal_vectors(arc.mid, mid)
    assert is_equal_val(arc.radius, radius)
    assert is_equal_val(arc.angle, angle)
    assert arc.angle == pytest.approx(angle)


def test_arcGeometry():

    sqrt2_2 = math.sqrt(2) / 2

    # A semi-circular arc
    semicircle = GeomArc(
        center=Vector2D(0, 0), start=Vector2D(1, 0), angle=180
    )

    assert_arc_geom(
        arc=semicircle,
        start=(1, 0),
        end=(-1, 0),
        center=(0, 0),
        mid=(0, 1),
        radius=1,
        angle=180,
    )

    # A semi-circular arc by endpoint goes in a specific direction
    semicircle_by_endpoint = GeomArc(
        center=Vector2D(0, 0), start=Vector2D(1, 0), end=Vector2D(-1, 0)
    )

    assert_arc_geom(
        arc=semicircle_by_endpoint,
        start=(1, 0),
        end=(-1, 0),
        center=(0, 0),
        mid=(0, -1),
        radius=1,
        angle=-180,  # CW
    )

    # Check that end or angle is required
    with pytest.raises(KeyError):
        GeomArc(center=Vector2D(0, 0), start=Vector2D(1, 0))

    # Test that the negative angle goes the other way
    negative_semicircle = GeomArc(
        center=Vector2D(0, 0), start=Vector2D(1, 0), angle=-180
    )

    assert_arc_geom(
        arc=negative_semicircle,
        start=(1, 0),
        end=(-1, 0),
        center=(0, 0),
        mid=(0, -1),
        radius=1,
        angle=-180,
    )

    arc_90deg_down = GeomArc(
        center=Vector2D(0, 0), start=Vector2D(1, 0), angle=-90
    )

    assert_arc_geom(
        arc=arc_90deg_down,
        start=(1, 0),
        end=(0, -1),
        center=(0, 0),
        mid=(sqrt2_2, -sqrt2_2),
        radius=1,
        angle=-90,
    )

    arc_90deg_down_nonunity_radius = GeomArc(
        center=Vector2D(0, 0), start=Vector2D(0, -1.2), angle=-90
    )

    assert_arc_geom(
        arc=arc_90deg_down_nonunity_radius,
        start=(0, -1.2),
        end=(-1.2, 0),
        center=(0, 0),
        mid=1.2 * Vector2D(-sqrt2_2, -sqrt2_2),
        radius=1.2,
        angle=-90,
    )

    # Arc not centred on the origin
    arc_not_on_origin = GeomArc(
        center=Vector2D(1, 1), start=Vector2D(2, 1), angle=-90
    )

    assert_arc_geom(
        arc=arc_not_on_origin,
        start=(2, 1),
        end=(1, 0),
        center=(1, 1),
        mid=(1 + sqrt2_2, 1 - sqrt2_2),
        radius=1,
        angle=-90,
    )

    # Not a simple angle for the mid
    arc_45_deg = GeomArc(center=Vector2D(0, 0), start=Vector2D(1, 0), angle=45)

    assert_arc_geom(
        arc=arc_45_deg,
        start=(1, 0),
        end=(sqrt2_2, sqrt2_2),
        center=(0, 0),
        mid=(math.cos(math.radians(22.5)), math.sin(math.radians(22.5))),
        radius=1,
        angle=45,
    )

    # Degenerate radius
    a_zero_radius = GeomArc(
        center=Vector2D(0, 0), start=Vector2D(0, 0), angle=42
    )

    assert_arc_geom(
        arc=a_zero_radius,
        start=(0, 0),
        end=(0, 0),
        center=(0, 0),
        mid=(0, 0),
        radius=0,
        angle=42,
    )


def testArcBy3Points():

    a_180_left_cw = GeomArc(
        start=Vector2D(0, -1),
        end=Vector2D(0, 1),
        mid=Vector2D(-1, 0),
    )

    assert_arc_geom(
        arc=a_180_left_cw,
        start=(0, -1),
        end=(0, 1),
        center=(0, 0),
        mid=(-1, 0),
        radius=1,
        angle=-180,  # CW
    )

    # The same thing the other way around, should still work exactly the same
    a_180_left_ccw = GeomArc(
        start=Vector2D(0, 1),
        end=Vector2D(0, -1),
        mid=Vector2D(-1, 0),
    )

    assert_arc_geom(
        arc=a_180_left_ccw,
        start=(0, 1),
        end=(0, -1),
        center=(0, 0),
        mid=(-1, 0),
        radius=1,
        angle=180,  # CCW
    )

    # Now, try an arc thats over 180 degreee
    # this has triggered bugs before
    a_over_180 = GeomArc(
        start=Vector2D(0, -1),
        end=Vector2D(0, 1),
        mid=Vector2D(-2, 0),
    )

    assert_arc_geom(
        arc=a_over_180,
        start=(0, -1),
        end=(0, 1),
        center=(-0.75, 0),
        mid=(-2, 0),
        radius=1.25,
        angle=-253.73979529168804,
    )

    # And one less than 180 degrees
    # and horizontal
    a_less_180 = GeomArc(
        start=Vector2D(-1, 0),
        end=Vector2D(1, 0),
        mid=Vector2D(0, 0.5),
    )

    assert_arc_geom(
        arc=a_less_180,
        start=(-1, 0),
        end=(1, 0),
        center=(0, -0.75),
        mid=(0, 0.5),
        radius=1.25,
        angle=-106.26020470831197,  # CW
    )


@pytest.mark.parametrize("start, mid, end", [
    ((0, -1), (0, 0),  (0,  1)),  # vertical/same x
    ((1,  0), (0, 0), (-1,  0)),  # horizontal/same y
    ((2,  1), (0, 0), (-2, -1)),  # diagonal
])  # fmt: skip
def testArc3PointCollinear(start, mid, end):
    """
    Check that an arc with three collinear points raises an error.
    """

    with pytest.raises(ValueError):
        GeomArc(
            start=Vector2D(start),
            end=Vector2D(mid),
            mid=Vector2D(end),
        )


def testCircleCircleIntersection():
    # check intersection of two circles with identical radii
    c1 = GeomCircle(center=[0, 0], radius=math.sqrt(2))
    c2 = GeomCircle(center=[2, 0], radius=math.sqrt(2))
    ip = get_intersection_points(c1, c2)
    assert len(ip) == 2
    for p in ip:
        assert any((p - Vector2D(1, y)).is_nullvec(tol=1e-7) for y in [1, -1])

    # check intersection of two circles with different radii
    c1 = GeomCircle(center=[0, 0], radius=2)
    c2 = GeomCircle(center=[2 * math.sqrt(3/4), 0], radius=1)
    ip = get_intersection_points(c1, c2)
    assert len(ip) == 2
    for p in ip:
        assert any((p - Vector2D(2 * math.sqrt(3/4), y)).is_nullvec(tol=1e-7) for y in [1, -1])

    # check intersection of two circles with different radii, too far apart
    c1 = GeomCircle(center=[0, 0], radius=2)
    c2 = GeomCircle(center=[4, 0], radius=1)
    ip = get_intersection_points(c1, c2)
    assert len(ip) == 0

    # check intersection of two circles with different radii, contained in each other
    c1 = GeomCircle(center=[0, 0], radius=2)
    c2 = GeomCircle(center=[0.5, 0], radius=1)
    ip = get_intersection_points(c1, c2)
    assert len(ip) == 0

    # check intersection point of circles touching outside
    c1 = GeomCircle(center=[0, 0], radius=1)
    c2 = GeomCircle(center=[2, 0], radius=1)
    ip = get_intersection_points(c1, c2)
    assert len(ip) == 0

    # check intersection point of circles touching inside
    c1 = GeomCircle(center=[0, 0], radius=2)
    c2 = GeomCircle(center=[1, 0], radius=1)
    ip = get_intersection_points(c1, c2)
    assert len(ip) == 0

    # check intersection point of circles touching inside
    # with some tolerance (this can cause a sqrt bounds error,
    # false duplicates or false negatives if not caught)

    # this case is 1.11 and 1.36, as both are numbers that have FP error
    # and this case caused a domain error
    c1 = GeomCircle(center=[0.25, 0], radius=1.11)
    c2 = GeomCircle(center=[0, 0], radius=1.36)
    ip = get_intersection_points(c1, c2)
    assert len(ip) == 0

    # vary position on x and y axis
    c1 = GeomCircle(center=[0, 0], radius=math.sqrt(2))
    c2 = GeomCircle(center=[0, 2], radius=math.sqrt(2))
    ip = get_intersection_points(c1, c2)
    assert len(ip) == 2
    for p in ip:
        assert any((p - Vector2D(x, 1)).is_nullvec(tol=1e-7) for x in [1, -1])
    c2 = GeomCircle(center=[-2, 0], radius=math.sqrt(2))
    ip = get_intersection_points(c1, c2)
    assert len(ip) == 2
    for p in ip:
        assert any((p - Vector2D(-1, y)).is_nullvec(tol=1e-7) for y in [1, -1])
    c2 = GeomCircle(center=[0, -2], radius=math.sqrt(2))
    for p in get_intersection_points(c1, c2):
        assert any((p - Vector2D(x, -1)).is_nullvec(tol=1e-7) for x in [1, -1])

    # circle 2 on the first median
    c1 = GeomCircle(center=[0, 0], radius=1)
    c2 = GeomCircle(center=[1, 1], radius=1)
    ip = get_intersection_points(c1, c2)
    assert len(ip) == 2
    for p in ip:
        assert any((p - Vector2D(x, y)).is_nullvec(tol=1e-7) for x, y in [(1, 0), (0, 1)])

    # circle 2 on the fourth median
    c1 = GeomCircle(center=[0, 0], radius=1)
    c2 = GeomCircle(center=[1, -1], radius=1)
    ip = get_intersection_points(c1, c2)
    assert len(ip) == 2
    for p in ip:
        assert any((p - Vector2D(x, y)).is_nullvec(tol=1e-7) for x, y in [(1, 0), (0, -1)])

    # circles on arbitrary positions
    center = Vector2D(3, -2)
    for angle in [0, 30, -30, 180, -180, 72, 143]:
        offset = Vector2D(math.sin(math.radians(angle)), math.cos(math.radians(angle)))
        c1 = GeomCircle(center=center, radius=math.sqrt(2))
        c2 = GeomCircle(center=center + 2 * offset, radius=math.sqrt(2))
        ip = get_intersection_points(c1, c2)
        assert len(ip) == 2
        for p in ip:
            assert any(
                (p - (center + offset + s * offset.rotated(90, origin=Vector2D(0, 0)))).is_nullvec(tol=1e-7)
                for s in [-1, 1])

    # two degenerated circles with the same center
    center = Vector2D(3, -2)
    c1 = GeomCircle(center=center, radius=0)
    c2 = GeomCircle(center=center, radius=0)
    ip = get_intersection_points(c1, c2)
    assert len(ip) == 0

    # two identical circles with the same center
    center = Vector2D(3, -2)
    c1 = GeomCircle(center=center, radius=1)
    c2 = GeomCircle(center=center, radius=1)
    assert get_intersection_points(c1, c2) == []


class TestArcSerialisation(SerialisationTest):

    def testArcsKx90deg(self):
        """
        Test that the Arc type can be serialised to KiCad format,
        looking at the 90 degree arcs.

        This is mostly a test of the serialisation, not the geometry, since
        while the geometry is tested above, the actual validity of the
        values in the output is not rigourously checked.
        """
        kicad_mod = Footprint("arc_90deg", FootprintType.SMD)

        center = Vector2D(0, 0)
        kicad_mod.append(
            Arc(center=center, start=Vector2D(1, 0), angle=-90))
        kicad_mod.append(
            Arc(center=center, start=Vector2D(0, -1.2), angle=-90))

        kicad_mod.append(
            Arc(center=center, start=Vector2D(-1.4, 0), angle=-90))
        kicad_mod.append(
            Arc(center=center, start=Vector2D(0, 1.6), angle=-90))

        kicad_mod.append(
            Arc(center=center, start=Vector2D(2, 0), angle=90))
        kicad_mod.append(
            Arc(center=center, start=Vector2D(0, 2.2), angle=90))

        kicad_mod.append(
            Arc(center=center, start=Vector2D(-2.4, 0), angle=90))
        kicad_mod.append(
            Arc(center=center, start=Vector2D(0, -2.6), angle=90))

        kicad_mod.append(
            Arc(center=center, start=Vector2D(3, 0), end=Vector2D(0, -3)))
        kicad_mod.append(
            Arc(center=center, start=Vector2D(0, -3.2), end=Vector2D(-3.2, 0)))

        kicad_mod.append(
            Arc(center=center, start=Vector2D(-3.4, 0), end=Vector2D(0, 3.4)))
        kicad_mod.append(
            Arc(center=center, start=Vector2D(0, 3.6), end=Vector2D(3.6, 0)))

        kicad_mod.append(
            Arc(center=center, start=Vector2D(4, 0), end=Vector2D(0, 4)))
        kicad_mod.append(
            Arc(center=center, start=Vector2D(0, 4.2), end=Vector2D(-4.2, 0)))

        kicad_mod.append(
            Arc(center=center, start=Vector2D(-4.4, 0), end=Vector2D(0, -4.4)))
        kicad_mod.append(
            Arc(center=center, start=Vector2D(0, -4.6), end=Vector2D(4.6, 0)))

        kicad_mod.append(
            Arc(center=center, start=Vector2D(5, 0), end=Vector2D(0, -5),
                long_way=True))
        kicad_mod.append(
            Arc(center=center, start=Vector2D(0, -5.2), end=Vector2D(-5.2, 0),
                long_way=True))

        kicad_mod.append(
            Arc(center=center, start=Vector2D(-5.4, 0), end=Vector2D(0, 5.4),
                long_way=True))
        kicad_mod.append(
            Arc(center=center, start=Vector2D(0, 5.6), end=Vector2D(5.6, 0),
                long_way=True))

        kicad_mod.append(
            Arc(center=center, start=Vector2D(6, 0), end=Vector2D(-6, 0)))
        kicad_mod.append(
            Arc(center=center, start=Vector2D(-6.2, 0), end=Vector2D(6.2, 0)))

        kicad_mod.append(
            Arc(center=center, start=Vector2D(6.6, 0), end=Vector2D(-6.6, 0),
                long_way=True))
        kicad_mod.append(
            Arc(center=center, start=Vector2D(-6.8, 0), end=Vector2D(6.8, 0),
                long_way=True))

        kicad_mod.append(
            Arc(center=center, mid=Vector2D(7, 0), angle=90))
        kicad_mod.append(
            Arc(center=center, mid=Vector2D(0, -7.2), angle=90))
        kicad_mod.append(
            Arc(center=center, mid=Vector2D(-7.4, 0), angle=90))
        kicad_mod.append(
            Arc(center=center, mid=Vector2D(0, 7.6), angle=90))

        kicad_mod.append(
            Arc(center=center, mid=Vector2D(8, 0), angle=-90))
        kicad_mod.append(
            Arc(center=center, mid=Vector2D(0, -8.2), angle=-90))
        kicad_mod.append(
            Arc(center=center, mid=Vector2D(-8.4, 0), angle=-90))
        kicad_mod.append(
            Arc(center=center, mid=Vector2D(0, 8.6), angle=-90))

        self.assert_serialises_as(kicad_mod, 'arc_90deg.kicad_mod')

    def testArcsKx90degOffsetRotated(self):
        kicad_mod = Footprint("arc_90deg_45deg", FootprintType.SMD)

        center = Vector2D(-5, 5)
        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(1, 0)+center).rotate(45, origin=center),
                angle=-90
            ))
        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(0, -1.2)+center).rotate(45, origin=center),
                angle=-90
            ))

        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(-1.4, 0)+center).rotate(45, origin=center),
                angle=-90
            ))
        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(0, 1.6)+center).rotate(45, origin=center),
                angle=-90
            ))

        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(2, 0)+center).rotate(45, origin=center),
                angle=90
            ))
        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(0, 2.2)+center).rotate(45, origin=center),
                angle=90
            ))

        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(-2.4, 0)+center).rotate(45, origin=center),
                angle=90
            ))
        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(0, -2.6)+center).rotate(45, origin=center),
                angle=90
            ))

        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(3, 0)+center).rotate(45, origin=center),
                end=(Vector2D(0, -3)+center).rotate(45, origin=center)
            ))
        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(0, -3.2)+center).rotate(45, origin=center),
                end=(Vector2D(-3.2, 0)+center).rotate(45, origin=center)
            ))

        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(-3.4, 0)+center).rotate(45, origin=center),
                end=(Vector2D(0, 3.4)+center).rotate(45, origin=center)
            ))
        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(0, 3.6)+center).rotate(45, origin=center),
                end=(Vector2D(3.6, 0)+center).rotate(45, origin=center)
            ))

        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(4, 0)+center).rotate(45, origin=center),
                end=(Vector2D(0, 4)+center).rotate(45, origin=center)
            ))
        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(0, 4.2)+center).rotate(45, origin=center),
                end=(Vector2D(-4.2, 0)+center).rotate(45, origin=center)
            ))

        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(-4.4, 0)+center).rotate(45, origin=center),
                end=(Vector2D(0, -4.4)+center).rotate(45, origin=center)
            ))
        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(0, -4.6)+center).rotate(45, origin=center),
                end=(Vector2D(4.6, 0)+center).rotate(45, origin=center)
            ))

        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(5, 0)+center).rotate(45, origin=center),
                end=(Vector2D(0, -5)+center).rotate(45, origin=center),
                long_way=True
            ))
        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(0, -5.2)+center).rotate(45, origin=center),
                end=(Vector2D(-5.2, 0)+center).rotate(45, origin=center),
                long_way=True
            ))

        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(-5.4, 0)+center).rotate(45, origin=center),
                end=(Vector2D(0, 5.4)+center).rotate(45, origin=center),
                long_way=True
            ))
        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(0, 5.6)+center).rotate(45, origin=center),
                end=(Vector2D(5.6, 0)+center).rotate(45, origin=center),
                long_way=True
            ))

        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(6, 0)+center).rotate(45, origin=center),
                end=(Vector2D(-6, 0)+center).rotate(45, origin=center)
            ))
        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(-6.2, 0)+center).rotate(45, origin=center),
                end=(Vector2D(6.2, 0)+center).rotate(45, origin=center)
            ))

        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(6.6, 0)+center).rotate(45, origin=center),
                end=(Vector2D(-6.6, 0)+center).rotate(45, origin=center),
                long_way=True
            ))
        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(-6.8, 0)+center).rotate(45, origin=center),
                end=(Vector2D(6.8, 0)+center).rotate(45, origin=center),
                long_way=True
            ))

        kicad_mod.append(
            Arc(
                center=center,
                mid=(Vector2D(7, 0)+center).rotate(45, origin=center),
                angle=90
            ))
        kicad_mod.append(
            Arc(
                center=center,
                mid=(Vector2D(0, -7.2)+center).rotate(45, origin=center),
                angle=90
            ))
        kicad_mod.append(
            Arc(
                center=center,
                mid=(Vector2D(-7.4, 0)+center).rotate(45, origin=center),
                angle=90
            ))
        kicad_mod.append(
            Arc(
                center=center,
                mid=(Vector2D(0, 7.6)+center).rotate(45, origin=center),
                angle=90
            ))

        kicad_mod.append(
            Arc(
                center=center,
                mid=(Vector2D(8, 0)+center).rotate(45, origin=center),
                angle=-90
            ))
        kicad_mod.append(
            Arc(
                center=center,
                mid=(Vector2D(0, -8.2)+center).rotate(45, origin=center),
                angle=-90
            ))
        kicad_mod.append(
            Arc(
                center=center,
                mid=(Vector2D(-8.4, 0)+center).rotate(45, origin=center),
                angle=-90
            ))
        kicad_mod.append(
            Arc(
                center=center,
                mid=(Vector2D(0, 8.6)+center).rotate(45, origin=center),
                angle=-90
            ))

        self.assert_serialises_as(kicad_mod, 'arc_90deg_45deg.kicad_mod')
