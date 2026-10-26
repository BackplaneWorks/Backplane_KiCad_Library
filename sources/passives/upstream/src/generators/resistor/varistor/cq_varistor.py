import math

import cadquery as cq


def make_varistor(params):
    case = make_case_RV_Disc(params)
    pins = make_pins_RV_Disc(params)

    return (case, pins)


def make_case_RV_Disc(params):
    D = params["D"]  # package length
    E = params["E"]  # body overall width
    A1 = params["A1"]  # package height
    pin = params["pin"]  # Pins
    rotation = params["rotation"]  # Rotation if required
    pintype = params["pintype"]  # pin type , like SMD or THT

    # FreeCAD.Console.PrintMessage('make_case_RV_Disc\r\n')
    #
    #
    #
    p0 = pin[0]
    p1 = pin[1]
    x0 = p0[0]
    y0 = p0[1]
    dx = math.fabs((p0[0] - p1[0]) / 2.0)
    dy = math.fabs((p0[1] - p1[1]) / 2.0)
    cx = x0 + dx
    cy = y0 + dy

    ff = E / 2.05

    case = (
        cq.Workplane("XZ")
        .workplane(offset=cy - (E / 2.0), centerOption="CenterOfMass")
        .moveTo(cx, A1 + (D / 2.0))
        .circle(D / 2.0, False)
        .extrude(E)
    )

    case = case.faces("<X").edges("<Y").fillet(ff)
    case = case.faces(">X").edges(">Y").fillet(ff)

    if rotation != 0:
        case = case.rotate((0, 0, 0), (0, 0, 1), rotation)

    return case


def make_pins_RV_Disc(params):
    A1 = params["A1"]  # Body seperation height
    b = params["b"]  # pin diameter or pad size
    ph = params["ph"]  # pin length
    rotation = params["rotation"]  # rotation if required
    pin = params["pin"]  # pin/pad cordinates
    D = params["D"]  # package length

    # FreeCAD.Console.PrintMessage('make_pins_RV_Disc \r\n')

    p = pin[0]
    pins = (
        cq.Workplane("XY")
        .workplane(offset=A1 + (D / 2.0), centerOption="CenterOfMass")
        .moveTo(p[0], -p[1])
        .circle(b / 2.0, False)
        .extrude(0 - (ph + A1 + (D / 2.0)))
    )
    pins = pins.faces("<Z").fillet(b / 5.0)

    for i in range(1, len(pin)):
        p = pin[i]
        pint = (
            cq.Workplane("XY")
            .workplane(offset=A1 + (D / 2.0), centerOption="CenterOfMass")
            .moveTo(p[0], -p[1])
            .circle(b / 2.0, False)
            .extrude(0 - (ph + A1 + (D / 2.0)))
        )
        pint = pint.faces("<Z").fillet(b / 5.0)
        pins = pins.union(pint)

    if rotation != 0:
        pins = pins.rotate((0, 0, 0), (0, 0, 1), rotation)

    return pins
