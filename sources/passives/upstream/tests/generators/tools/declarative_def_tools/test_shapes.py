import pytest

from generators.tools.footprint.declarative_def_tools import shape_properties as SP


def test_no_shape_type_key():

    # This should fail because there's no type
    spec = {
        "corners": [[1, 2], [3, 4]],
    }
    with pytest.raises(ValueError):
        SP.construct_shape(spec)


def test_rect():

    spec = {
        "type": "rect",
        "corners": [["a", "b"], ["c", "d"]],
    }
    rp = SP.RectProperties(spec)

    assert rp.exprs.corner1.x.value == "a"
    assert rp.exprs.corner1.y.value == "b"
    assert rp.exprs.corner2.x.value == "c"
    assert rp.exprs.corner2.y.value == "d"


def test_rect_center_size():

    spec = {
        "type": "rect",
        "center": ["a", "b"],
        "size": ["c", "d"],
    }
    rp = SP.RectProperties(spec)

    assert rp.exprs.center.x.value == "a"
    assert rp.exprs.center.y.value == "b"
    assert rp.exprs.size.x.value == "c"
    assert rp.exprs.size.y.value == "d"


def test_circle_rad():

    spec = {
        "type": "circle",
        "center": ["a", "b"],
        "radius": 1,
    }
    kp = SP.CircleProperties(spec)

    assert kp.exprs.center.x.value == "a"
    assert kp.exprs.center.y.value == "b"
    assert kp.exprs.rad_diam.value == 1
    assert kp.exprs.is_diam is False


def test_circle_radius_and_diameter():
    # Cannot have both radius and diameter
    with pytest.raises(ValueError):
        spec = {
            "type": "circle",
            "center": [1, 2],
            "radius": 1,
            "diameter": 2,
        }
        SP.CircleProperties(spec)


def test_polygon():

    spec = {
        "type": "poly",
        "points": [[1, 2], [3, 4], [5, 6]],
        "offset": [7, 8],
    }

    pp = SP.PolyProperties(spec)

    assert pp.pts[0].x.value == 1
    assert pp.pts[0].y.value == 2
