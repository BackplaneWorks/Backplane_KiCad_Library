import pytest

from KicadModTree import Polygon, Vector2D
from KicadModTree.nodes.specialized.ChamferedRectangle import (
    ChamferedRectangle,
    ChamferSizeHandler,
    CornerSelection,
)
from KicadModTree.tests.test_utils import custom_assertions as CA


@pytest.mark.parametrize(
    "size, layer, width, chamfer, corners, fill, exp_points",
    [
        (
            (1, 2), "F.SilkS", 0.1, 0.2,
            CornerSelection({CornerSelection.TOP_LEFT: True}),
            False,
            (
                (-0.5, -0.8),   # Top left, bottom left of chamfer
                (-0.5, 1.0),    # Bottom left
                (0.5, 1.0),     # Bottom right
                (0.5, -1),      # Top right
                (-0.3, -1),     # Top left, top right of chamfer
            )
        ),
    ],
)  # fmt: skip
def test_ChamferedRectangle(size, layer, width, chamfer, corners, fill, exp_points):

    size = Vector2D(size)

    chamfer_handler = ChamferSizeHandler(chamfer_exact=chamfer)

    r = ChamferedRectangle(
        center=Vector2D.zero(),
        size=size,
        layer=layer,
        width=width,
        chamfer=chamfer_handler,
        corners=corners,
        fill=fill,
    )

    # Check that the properties are set correctly
    assert r.size == size
    assert r.layer == layer
    assert r.width == width
    assert r.fill == fill

    # Flatten the object and check the output
    #
    # ChamferedRect is a base object, so it should flatten to itself
    serialised = r.flatten()

    # Pull out the Polygon object
    polygons = CA.assert_contains_n_of_type(serialised, 1, Polygon)

    # Check the points are in the expected order
    exp_points = [Vector2D(p) for p in exp_points]
    CA.assert_contains_only_points_cyclic(polygons[0].points, exp_points)
