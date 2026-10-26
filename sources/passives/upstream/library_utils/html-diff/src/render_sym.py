#!/usr/bin/env python3

import re
import sys
from pathlib import Path

try:
    import kicad_sym
except ImportError:
    if (
        common := Path(__file__).parent.parent.with_name("common").absolute()
    ) not in sys.path:
        sys.path.insert(0, str(common))

import kicad_sym  # NOQA: F811
from svg_util import Tag, add_bboxes, bbox, define_arc, guarded, setup_svg


def elem_style(elem):
    if isinstance(elem, (kicad_sym.Property, kicad_sym.Text)):
        return {"class": "l-any-f"}
    else:
        classes = []
        if getattr(elem, "fill_type", None) == "outline":
            classes.append("l-any-f")

        stroke_width = getattr(elem, "stroke_width", 0)

        if stroke_width < 0:
            # An explicit stroke width of < 0 disables the stroke
            stroke_width = 0
        elif stroke_width == 0:
            # Exactly 0 means "use schematic default". The default value
            # for the schematic default is 0.152mm (6 mil), so we use that.
            stroke_width = 0.1524

        if stroke_width > 0:
            classes.append("l-any-s")

        return {
            "class": " ".join(classes),
            "stroke_width": stroke_width,
            "stroke_linecap": "round",
            "stroke_linejoin": "round",
        }


def render_rect(sym, elem, **style):
    x, y = min(elem.startx, elem.endx), min(-elem.starty, -elem.endy)
    w, h = max(elem.startx, elem.endx) - x, max(-elem.starty, -elem.endy) - y
    yield (x, y, x + w, y + h), Tag("rect", **style, x=x, y=y, width=w, height=h)


def render_circle(sym, elem, **style):
    x, y = elem.centerx, -elem.centery
    r = max(0.2, elem.radius)
    yield (x - r, y - r, x + r, y + r), Tag("circle", **style, cx=x, cy=y, r=r)


def render_polyline(sym, elem, **style):
    points = [(pt.x, -pt.y) for pt in elem.points]
    path_data = "M " + " L ".join(f"{x:.6f} {y:.6f}" for x, y in points)
    yield bbox(*points), Tag("path", **style, d=path_data)


def render_arc(sym, arc, **style):
    x1, y1 = arc.startx, -arc.starty
    x2, y2 = arc.midx, -arc.midy
    x3, y3 = arc.endx, -arc.endy

    c, r, collinear, large_arc, sweep, is_circle = define_arc(
        (x1, y1), (x2, y2), (x3, y3)
    )

    if is_circle:
        elem_bbox = bbox((c[0] - r, c[1] - r), (c[0] + r, c[1] + r))
        yield elem_bbox, Tag("circle", **style, cx=c[0], cy=c[1], r=r)
        return

    if collinear:
        # The points are collinear, so we just draw a line
        elem_bbox = bbox((x1, y1), (x2, y2))
        yield elem_bbox, Tag(
            "path", **style, d=f"M {x1:.6f} {y1:.6f} L {x2:.6f} {y2:.6f}"
        )
        return

    d = f"M {x1:.6f} {y1:.6f} A {r:.6f} {r:.6f} 0 {int(large_arc)} {int(sweep)} {x3:.6f} {y3:.6f}"
    # We just approximate the bbox here with that of a circle. Calculating precise arc bboxes is
    # hairy, and unnecessary for our purposes.
    elem_bbox = bbox((c[0] - r, c[1] - r), (c[0] + r, c[1] + r))
    yield elem_bbox, Tag("path", **style, d=d)


def render_bezier(sym, elem, **style):
    # KiCad beziers are cubic segments in groups of 4 points: start, control 1,
    # control 2, end.
    points = [(pt.x, -pt.y) for pt in elem.points]

    if len(points) < 4:
        raise ValueError(
            f"Bezier element has {len(points)} points, but at least 4 are required"
        )

    x0, y0 = points[0]
    x1, y1 = points[1]
    x2, y2 = points[2]
    x3, y3 = points[3]
    d = f"M {x0:.6f} {y0:.6f} C {x1:.6f} {y1:.6f}, {x2:.6f} {y2:.6f}, {x3:.6f} {y3:.6f}"

    # A cubic Bezier lies within the convex hull of its control points, so the
    # control-point bbox is a safe (if conservative) bounding box.
    yield bbox(*points), Tag("path", **style, d=d)


def render_text(sym, elem, **style):

    content = getattr(elem, "text", getattr(elem, "value", None))
    assert content is not None
    x, y = elem.posx, -elem.posy

    yield from text_elem(x, y, elem.rotation, content, elem.effects, style)


def render_property(sym, elem, **style):

    if elem.is_hidden:
        return

    content = getattr(elem, "text", getattr(elem, "value", None))
    assert content is not None
    x, y = elem.posx, -elem.posy

    yield from text_elem(x, y, elem.rotation, content, elem.effects, style)


def text_elem(x, y, rot, content, effects, style):
    if rot in (90, 270):
        xform = {"transform": f"rotate({-rot} {x} {y})"}
    else:
        xform = {}

    size = 1.27
    anchor = "middle"
    style_extra = {}

    if effects is not None:

        size = effects.sizey / 2 or 1.27
        anchor = {"center": "middle", "left": "start", "right": "end"}.get(
            effects.h_justify, "middle"
        )
        baseline = {"top": "text-top", "center": "middle", "bottom": "hangign"}.get(
            effects.v_justify, "middle"
        )

    content = re.sub(
        r"~{([^}]*)}|^~([^{].*)$",
        r'<tspan text-decoration="overline">\1\2</tspan>',
        content,
    )
    content = re.sub(
        r"_{([^}]*)}",
        r'<tspan font-size="70%" baseline-shift="sub">\1</tspan>',
        content,
    )

    yield (x, y, x, y), Tag(
        "text",
        [content],
        font_family="monospace",
        font_size=f"{size*0.7:.3f}mm",
        x=x,
        y=y,
        dominant_baseline=baseline,
        text_anchor=anchor,
        **style,
        **xform,
        **style_extra,
    )


def render_pin(sym, elem, **style):
    if elem.is_hidden:
        return

    l = elem.length  # NOQA: E741
    x1, y1 = elem.posx, -elem.posy
    x2, y2 = x1 + l, y1
    rot = elem.rotation
    xform = {"transform": f"rotate({-rot} {x1} {y1})"}

    yield bbox((x1, y1), (x2, y2)), Tag(
        "path", **xform, **style, d=f"M {x1:.6f} {y1:.6f} L {x2:.6f} {y2:.6f}"
    )

    eps = 1
    for tag in {
        "line": [],
        "inverted": [
            Tag("circle", **xform, **style, cx=x2 - eps / 3 - 0.2, cy=y2, r=eps / 3)
        ],
        "clock": [
            Tag(
                "path",
                **xform,
                **style,
                d=f"M {x2} {y2-eps/2} L {x2+eps/2} {y2} L {x2} {y2+eps/2}",
            )
        ],  # NOQA: E501
        "inverted_clock": [
            Tag("circle", **xform, **style, cx=x2 - eps / 3 - 0.2, cy=y2, r=eps / 3),
            Tag(
                "path",
                **xform,
                **style,
                d=f"M {x2} {y2-eps/2} L {x2+eps/2} {y2} L {x2} {y2+eps/2}",
            ),
        ],  # NOQA: E501
        "input_low": [
            Tag(
                "path",
                **xform,
                **style,
                d=f"M {x2} {y2} L {x2-eps} {y2-eps} L {x2-eps} {y2}",
            )
        ],  # NOQA: E501
        "clock_low": [
            Tag(
                "path",
                **xform,
                **style,
                d=f"M {x2} {y2} L {x2-eps} {y2-eps} L {x2-eps} {y2}",
            ),  # NOQA: E501
            Tag(
                "path",
                **xform,
                **style,
                d=f"M {x2} {y2-eps/2} L {x2+eps/2} {y2} L {x2} {y2+eps/2}",
            ),
        ],  # NOQA: E501
        "output_low": [
            Tag("path", **xform, **style, d=f"M {x2} {y2-eps} L {x2-eps} {y2}")
        ],  # NOQA: E501
        "edge_clock_high": [
            Tag(
                "path",
                **xform,
                **style,
                d=f"M {x2} {y2} L {x2-eps} {y2-eps} L {x2-eps} {y2}",
            ),  # NOQA: E501
            Tag(
                "path",
                **xform,
                **style,
                d=f"M {x2} {y2-eps/2} L {x2+eps/2} {y2} L {x2} {y2+eps/2}",
            ),
        ],  # NOQA: E501
        "non_logic": [
            Tag(
                "path",
                **xform,
                **style,
                d=f"M {x2-eps/2} {y2-eps/2} L {x2+eps/2} {y2+eps/2}",
            ),  # NOQA: E501
            Tag(
                "path",
                **xform,
                **style,
                d=f"M {x2-eps/2} {y2+eps/2} L {x2+eps/2} {y2-eps/2}",
            ),
        ],  # NOQA: E501
        # FIXME...
    }.get(elem.shape, []):
        yield (x1, y1, x1, y1), tag

    if rot in (90, 270):
        t_rot = 90
    else:
        t_rot = 0

    # Use the global symbol property to decide if the text appears at all
    if not sym.hide_pin_names:
        e = l + sym.pin_names_offset
        elem.name_effect.h_justify = "left"
        if rot in (180, 270):
            elem.name_effect.h_justify = {"left": "right", "right": "left"}.get(
                elem.name_effect.h_justify
            )

        nx, ny = {
            0: (x1 + e, y1),
            90: (x1, y1 - e),
            180: (x1 - e, y1),
            270: (x1, y1 + e),
        }[rot]

        yield from text_elem(
            nx, ny, t_rot, elem.name, elem.name_effect, {"class": "l-any-f"}
        )

    if not sym.hide_pin_numbers:
        k = 0.4
        elem.number_effect.v_justify = "top"
        nx, ny = {
            0: (x1 + l / 2, y1 - k),
            90: (x1 - k, y1 - l / 2),
            180: (x1 - l / 2, y1 - k),
            270: (x1 - k, y1 + l / 2),
        }[rot]

        yield from text_elem(
            nx, ny, t_rot, elem.number, elem.number_effect, {"class": "l-any-f"}
        )


def _render_sym_internal(sym, root_sym, unit=1):
    for fun, elems in [
        (render_rect, root_sym.rectangles),
        (render_circle, root_sym.circles),
        (render_polyline, root_sym.polylines),
        (render_arc, root_sym.arcs),
        (render_bezier, root_sym.beziers),
        (render_pin, root_sym.pins),
        (render_text, root_sym.texts),
        # Properties are the only bit that is not in the root symbol
        (render_property, sym.properties),
    ]:
        for elem in elems:
            if hasattr(elem, "unit") and elem.unit not in (0, unit):  # bad API
                continue
            yield from guarded(
                f"element {elem} of symbol {sym.name}",
                fun(root_sym, elem, **elem_style(elem)),
            )


def render_sym(
    sym: kicad_sym.KicadSymbol, lib: kicad_sym.KicadLibrary, default_style=True
):
    # The parent symbol that contributes graphical data
    root_sym = sym.get_root_symbol()

    for unit in range(1, root_sym.unit_count + 1):
        tags, bboxes = [], []

        for bbox, tag in _render_sym_internal(sym, root_sym, unit):  # NOQA: F402
            tags.append(tag)
            bboxes.append(bbox)

        x1, y1, x2, y2 = add_bboxes(bboxes)
        xm, ym = max(abs(x1), abs(x2)), max(abs(y1), abs(y2))
        bounds = ((-xm, -ym), (xm, ym))
        if default_style:
            tags.insert(
                0,
                Tag(
                    "style",
                    ["""
                .l-any-f { fill: black; }
                .l-any-s { stroke: black }
                * { fill: none; stroke: none }
                tspan { fill: black; } """],
                ),
            )
        yield str(setup_svg(tags, bounds, margin=10))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("kicad_sym_file", type=Path)
    args = parser.parse_args()
    _suffix, _, sym_name = args.kicad_sym_file.suffix.partition(":")
    libfile = args.kicad_sym_file.with_suffix(".kicad_sym")
    for i, unit_data in enumerate(render_sym(libfile.read_text(), sym_name)):
        outf = (
            args.kicad_sym_file.parent
            / f"{args.kicad_sym_file.stem}_{sym_name}_{i}.svg"
        )
        print(f"writing unit {i} to {str(outf)}", file=sys.stderr)
        outf.write_text(unit_data)
