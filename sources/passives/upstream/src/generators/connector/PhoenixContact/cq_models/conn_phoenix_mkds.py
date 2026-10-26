import cadquery as cq

from generators.tools.model.cq_helpers import union_all


def make_case_MKDS_1_5_10_5_08(params, pinnumber):
    W = params["W"]  # package width
    H = params["H"]  # package height
    WD = params["WD"]  # > Y distance form pin center to package edge
    A1 = params["A1"]  # Body seperation height
    PE = params["PE"]  # Distance from edge to pin
    PS = params["pin_pitch"]  # Pin distance
    PD = params["PD"]  # Pin diameter
    PL = params["PL"]  # Pin diameter
    PF = params["PF"]  # Pin form
    SW = params["SW"]  # Blender width
    rotation = params["rotation"]  # rotation if required

    lw = (2.0 * PE) + ((pinnumber - 1) * PS)

    #
    # Create a polygon of the shape and extrude it along the Y axis
    #
    pts = []
    #    pts.append((0.0, 0.0))
    #
    pts.append((0.0 - WD, 0.0))
    #
    pts.append((0.0 - WD, 0.0 + (H * 0.5)))
    #
    pts.append((0.0 - WD + 0.2, 0.0 + (H * 0.5)))
    #
    pts.append((0.0 - (WD * 0.5), 0.0 + H))
    #
    pts.append(((W - WD) * 0.4, 0.0 + H))
    #
    pts.append(((W - WD), 0.0 + (H * 0.3)))
    #
    pts.append((W - WD, 0.0))
    #
    case = (
        cq.Workplane("YZ")
        .workplane(offset=0 - PE, centerOption="CenterOfMass")
        .polyline(pts, includeCurrent=True)
        .close()
        .extrude(lw)
    )
    case = case.translate((0.0, 0.0, A1))
    #
    #
    A1A = A1 + 0.2
    bb = WD - 0.4
    SL = SW / 1.1  # Screw diameter

    px = 0.0
    pins = None

    #
    # Cut out the hole for the cable
    #
    for i in range(0, pinnumber):
        pp = (
            cq.Workplane("XZ")
            .workplane(offset=0.0, centerOption="CenterOfMass")
            .moveTo(px, A1 + 0.5 * PS)
            .rect(0.6 * PS, 0.8 * PS)
            .extrude(0.5 * W)
        )
        case = case.cut(pp)
        px = px + PS

    px = 0.0
    #
    # Cut out the hole for the screw
    #
    dd = WD * 0.4
    ofx = 0.0
    for i in range(0, pinnumber):
        pp = (
            cq.Workplane("XY")
            .workplane(offset=A1 + (H / 2.0), centerOption="CenterOfMass")
            .moveTo(px, 0.0 - ofx)
            .circle(dd, False)
            .extrude(H)
        )
        case = case.cut(pp)
        px = px + PS

        #    case = case.faces("<Y").edges(">X").fillet(0.1)
    case = case.faces("<X").fillet(0.05)
    case = case.faces(">X").fillet(0.05)
    # case = case.faces(">Z").fillet(0.05)
    #    case = case.faces("<Y").edges(">Z").fillet(0.05)

    if rotation > 0.01:
        case = case.rotate((0, 0, 0), (0, 0, 1), rotation)

    return case


def make_pins_MKDS_1_5_10_5_08(params, pinnumber):
    W = params["W"]  # package width
    H = params["H"]  # package height
    WD = params["WD"]  # > Y distance form pin center to package edge
    A1 = params["A1"]  # Body seperation height
    PE = params["PE"]  # Distance from edge to pin
    PS = params["pin_pitch"]  # Pin distance
    PD = params["PD"]  # Pin diameter
    PL = params["PL"]  # Pin diameter
    PF = params["PF"]  # Pin form
    SW = params["SW"]  # Blender width
    rotation = params["rotation"]  # rotation if required

    px = 0.0
    pins = []

    for i in range(0, pinnumber):
        if PF == "round":
            pint = (
                cq.Workplane("XY")
                .workplane(offset=A1, centerOption="CenterOfMass")
                .moveTo(px, 0.0)
                .circle(PD[0] / 2.0, False)
                .extrude(0 - (A1 + PL))
            )
            pint = pint.faces("<Z").fillet(PD[0] / 2.2)
        else:
            pint = (
                cq.Workplane("XY")
                .workplane(offset=A1, centerOption="CenterOfMass")
                .moveTo(px, 0.0)
                .rect(PD[0], PD[1])
                .extrude(0 - (A1 + PL))
            )
            if PD[0] < PD[1]:
                pint = pint.faces("<Z").fillet(PD[0] / 2.2)
            else:
                pint = pint.faces("<Z").fillet(PD[1] / 2.2)

        pins.append(pint)

        px = px + PS

    #
    # Ad screws
    #
    px = 0.0
    dd = WD * 0.4
    ofx = 0.0
    for i in range(0, pinnumber):
        pint = (
            cq.Workplane("XY")
            .workplane(offset=A1 + H - 0.5, centerOption="CenterOfMass")
            .moveTo(px, 0.0 - ofx)
            .circle(dd, False)
            .extrude(0.0 - (H / 2.0))
        )
        pint = pint.faces(">Z").fillet(dd / 2.2)
        pint2 = (
            cq.Workplane("XY")
            .workplane(offset=A1 + H, centerOption="CenterOfMass")
            .moveTo(px, 0.0 - ofx)
            .rect(2.0 * dd, 0.5)
            .extrude(0.0 - 1.0)
        )
        pint = pint.cut(pint2)
        pins.append(pint)

        px = px + PS

    #
    # Ad metal hole
    #
    px = 0.0
    dd = WD * 0.4
    ofx = 0.0
    for i in range(0, pinnumber):
        pint = (
            cq.Workplane("XZ")
            .workplane(offset=WD * 0.9, centerOption="CenterOfMass")
            .moveTo(px, A1 + 0.5 * PS)
            .rect(0.6 * PS, 0.8 * PS)
            .extrude(0.0 - 2.0)
        )
        pint2 = (
            cq.Workplane("XZ")
            .workplane(offset=WD * 0.9, centerOption="CenterOfMass")
            .moveTo(px, A1 + 0.5 * PS)
            .rect(0.4 * PS, 0.6 * PS)
            .extrude(0.0 - 2.0)
        )
        pint = pint.cut(pint2)
        pint = pint.faces("<Y").fillet(0.1)
        pins.append(pint)
        px = px + PS

    merged_pins = union_all(pins)

    if rotation > 0.01:
        merged_pins = merged_pins.rotate((0, 0, 0), (0, 0, 1), rotation)

    return merged_pins
