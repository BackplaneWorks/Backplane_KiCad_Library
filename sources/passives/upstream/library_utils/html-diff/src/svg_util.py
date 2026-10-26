import logging
import math
import textwrap


def guarded(item_label: str, gen):
    """Yield everything from the gen function. On an exception, log and skip the item."""
    try:
        yield from gen
    except Exception as e:
        logging.error(f"Error rendering {item_label}:\n\t{e}")


class Tag:
    """Helper class to ease creation of SVG. All API functions that create SVG allow you to
    substitute this with your own implementation by passing a ``tag`` parameter."""

    def __init__(self, name, children=None, root=False, **attrs):
        self.name, self.attrs = name, attrs
        self.children = children or []
        self.root = root

    def __str__(self):
        prefix = '<?xml version="1.0" encoding="utf-8"?>\n' if self.root else ""
        opening = " ".join(
            [self.name]
            + [
                f'{key.replace("__", ":").replace("_", "-")}="{value}"'
                for key, value in self.attrs.items()
            ]
        )
        if self.children:
            children = "\n".join(textwrap.indent(str(c), "  ") for c in self.children)
            return f"{prefix}<{opening}>\n{children}\n</{self.name}>"
        else:
            return f"{prefix}<{opening}/>"


def point_line_distance(l1, l2, p):
    """Calculate distance between infinite line through l1 and l2, and point p."""
    # https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line
    x1, y1 = l1
    x2, y2 = l2
    x0, y0 = p
    length = math.dist(l1, l2)
    if math.isclose(length, 0):
        return math.dist(l1, p)
    return ((x2 - x1) * (y1 - y0) - (x1 - x0) * (y2 - y1)) / length


def distance_between(p1, p2):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return math.sqrt(dx * dx + dy * dy)


def define_arc(p1, p2, p3):
    """
    Returns the center radius, collinearity and side (large/small) of the circle
    passing the given 3 points.
    """
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3

    # If the end points are the same, the circle is at the midpoint
    if distance_between(p1, p3) < 1.0e-6:
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        r = distance_between((cx, cy), (x1, y1))
        return (cx, cy), r, False, False, False, True

    # Compute temporary values to help with calculations
    denom = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))

    if math.isclose(denom, 0):
        return (x1, y1), 0, True, False, False, False

    # Compute intermediate values
    cx = (
        (x1**2 + y1**2) * (y2 - y3)
        + (x2**2 + y2**2) * (y3 - y1)
        + (x3**2 + y3**2) * (y1 - y2)
    ) / denom

    cy = (
        (x1**2 + y1**2) * (x3 - x2)
        + (x2**2 + y2**2) * (x1 - x3)
        + (x3**2 + y3**2) * (x2 - x1)
    ) / denom

    r = distance_between((cx, cy), (x1, y1))
    dc = point_line_distance((x1, y1), (x3, y3), (cx, cy))
    d2 = point_line_distance((x1, y1), (x3, y3), (x2, y2))

    collinear = abs(d2) < 1.0e-6

    # If center and point 2 lie on the same side of line through point 1 and 3,
    # we need to draw the large arc, else the small one
    large_arc = dc * d2 >= 0

    # Location of point 2 relative to that line determins CW/CCW direction
    sweep = d2 > 0

    return (cx, cy), r, collinear, large_arc, sweep, False


def bbox(*args):
    xs, ys = [x for x, _ in args], [y for _, y in args]
    return min(xs), min(ys), max(xs), max(ys)


def add_bboxes(bboxes):
    # format: [(min_x, min_y, max_x, max_Y), ...]
    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")

    for x1, y1, x2, y2 in bboxes:
        assert x1 <= x2 and y1 <= y2
        if x1 < min_x:
            min_x = x1
        if y1 < min_y:
            min_y = y1
        if x2 > max_x:
            max_x = x2
        if y2 > max_y:
            max_y = y2

    return min_x, min_y, max_x, max_y


def svg_rotation(angle_rad, cx=0, cy=0):
    return f"rotate({float(math.degrees(angle_rad)):.4} {float(cx):.6} {float(cy):.6})"


def setup_svg(tags, bounds, margin=0, pagecolor="white", tag=Tag, inkscape=False):
    (min_x, min_y), (max_x, max_y) = bounds

    if margin:
        min_x -= margin
        min_y -= margin
        max_x += margin
        max_y += margin

    w, h = max_x - min_x, max_y - min_y
    w = 1.0 if math.isclose(w, 0.0) else w
    h = 1.0 if math.isclose(h, 0.0) else h

    if inkscape:
        tags.insert(
            0,
            tag(
                "sodipodi:namedview",
                [],
                id="namedview1",
                pagecolor=pagecolor,
                inkscape__document_units="mm",
            ),
        )
        namespaces = dict(
            xmlns="http://www.w3.org/2000/svg",
            xmlns__xlink="http://www.w3.org/1999/xlink",
            xmlns__sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd",
            xmlns__inkscape="http://www.inkscape.org/namespaces/inkscape",
        )

    else:
        namespaces = dict(
            xmlns="http://www.w3.org/2000/svg",
            xmlns__xlink="http://www.w3.org/1999/xlink",
        )

    # TODO export apertures as <uses> where reasonable.
    return tag(
        "svg",
        tags,
        width=f"{w}mm",
        height=f"{h}mm",
        viewBox=f"{min_x} {min_y} {w} {h}",
        **namespaces,
        root=True,
    )
