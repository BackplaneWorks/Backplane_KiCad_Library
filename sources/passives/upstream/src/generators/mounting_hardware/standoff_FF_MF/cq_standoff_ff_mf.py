from math import sqrt

import cadquery as cq


def make_standoff(params):
    OD = params["OD"]  # Outer Diameter, Flat side to flatside for HEX
    ID = params["ID"]  # Inner Diameter
    H = params["H"]  # Height of standoff
    shape = params["shape"]  # Shape can be 'Round' or 'Hex'
    rot = params["rotation"]
    # dest_dir_pref = params['dest_dir_prefix']

    if shape == "Hex":
        a = OD / sqrt(3)
        body = cq.Workplane("XY").polygon(6, a * 2).extrude(H)
        body = body.cut(cq.Workplane("XY").circle(ID / 2).extrude(H))
    if shape == "Round":
        body = cq.Workplane("XY").circle(OD / 2).extrude(H)
        body = body.cut(cq.Workplane("XY").circle(ID / 2).extrude(H))
    body = body.edges(">Z").fillet(a / 20)
    body = body.edges("<Z").fillet(a / 20)
    if params["stud_H"] > 0:
        body = body.union(
            cq.Workplane("XY")
            .circle(ID / 2)
            .extrude(-params["stud_H"] - 0.5)
            .translate((0.0, 0.0, 0.5))
        )
        body = body.edges("<Z").fillet(a / 20)

    return body
