import pytest

from KicadModTree import Rectangle, Vector2D
from KicadModTree.tests.test_utils import custom_assertions as CA


@pytest.mark.parametrize(
    "start, end, layer, width",
    [
        ((0, 0), (1, 1), "F.SilkS", 0.1),
        ((1, 1), (0, 0), "B.SilkS", 0.2),
    ],
)
def test_Rect(start, end, layer, width):

    s = Vector2D(start)
    e = Vector2D(end)

    r = Rectangle(start=s, end=e, layer=layer, width=width)

    # Check that the properties are set correctly
    assert r.center == (s + e)/2
    assert r.size == (e - s).positive()
    assert r.layer == layer
    assert r.width == width

    # Flatten the object and check the output
    #
    # Rectangle is a base object, so it should flatten to itself
    nodes = r.flatten()

    rects = CA.assert_contains_n_of_type(nodes, 1, Rectangle)
    assert rects[0] == r
