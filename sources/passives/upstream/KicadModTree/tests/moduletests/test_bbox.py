from KicadModTree import Circle, Line, Rectangle, Translation
from kilibs.geom import Vector2D


def test_bounding_box():
    # for line
    p1 = Vector2D(3, 1)
    p2 = Vector2D(-2, 4)
    line = Line(start=p1, end=p2, layer=None)
    bbox = line.bbox()
    assert bbox.left == min(p1.x, p2.x)
    assert bbox.top == min(p1.y, p2.y)
    assert bbox.right == max(p1.x, p2.x)
    assert bbox.bottom == max(p1.y, p2.y)

    rect = Rectangle(start=(p1.x, p2.y), end=(p2.x, p1.y), layer=None)
    bbox = rect.bbox()
    assert bbox.left == min(p1.x, p2.x)
    assert bbox.top == min(p1.y, p2.y)
    assert bbox.right == max(p1.x, p2.x)
    assert bbox.bottom == max(p1.y, p2.y)

    circle = Circle(center=(3, 1), radius=2)
    bbox = circle.bbox()
    assert bbox.left == 1
    assert bbox.top == -1
    assert bbox.right == 5
    assert bbox.bottom == 3


def test_translation():

    line = Line(start=(0, 0), end=(1, 1), layer=None)
    translation = Translation(42, 43)

    translation += line

    t_bbox = translation.bbox()
    assert t_bbox.left == 42
    assert t_bbox.top == 43
    assert t_bbox.right == 43
    assert t_bbox.bottom == 44
