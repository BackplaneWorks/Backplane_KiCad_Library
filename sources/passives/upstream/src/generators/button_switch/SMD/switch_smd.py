import cadquery as cq

CASE_THT_TYPE = "tht"
CASE_SMD_TYPE = "smd"
CASE_THTSMD_TYPE = "thtsmd"

CORNER_NONE_TYPE = "none"
CORNER_CHAMFER_TYPE = "chamfer"
CORNER_FILLET_TYPE = "fillet"


def make_case(params):

    L = params["L"]  # package length
    W = params["W"]  # package width
    H = params["H"]  # package height
    pitch = params["pitch"]  # pin pitch
    PH = params["PH"]  # pin height above package height
    npins = params["npins"]  # total number of pins
    rotation = params["rotation"]  # rotation if required
    corner = params["corner"]  # Chamfer or corner
    A1 = params["A1"]  # Body seperation height

    # FreeCAD.Console.PrintMessage('make_case\r\n')

    xd = H / 4.0
    tpins = npins / 2
    mvX = L / 2.0
    mvY = W / 2.0
    case = (
        cq.Workplane("XY")
        .workplane(offset=A1, centerOption="CenterOfMass")
        .moveTo(-mvX, -mvY)
        .rect(L, W, False)
        .extrude(H)
    )

    if npins < 3:
        xd = L / 4.0
        yd = W / 3.0
        myXD = xd * 2.0
        myYD = yd
        myX = 0 - (xd / 2.0)
        myY = 0 - (yd / 2)
        pighole = (
            cq.Workplane("XY")
            .workplane(offset=A1 + H, centerOption="CenterOfMass")
            .moveTo(myX, myY)
            .rect(myXD, myYD, False)
            .extrude(-(H / 4))
        )
        case = case.cut(pighole)
    else:
        xd = L / 4.0
        yd = pitch / 3.0

        myX = 0 - (xd / 2.0)
        myY = 0 - ((tpins / 2) * (pitch / 2.0) + (yd / 2.0))
        myXD = xd * 2.0
        myYD = yd

        if tpins % 2 == 0:
            myY = (pitch / 2.0) + (((tpins / 2) - 1) * pitch)
        else:
            myY = (((tpins / 2) - 1) * pitch) + pitch

        myY = myY - (myYD / 2)
        for i in range(0, int(tpins)):
            pighole = (
                cq.Workplane("XY")
                .workplane(offset=A1 + H, centerOption="CenterOfMass")
                .moveTo(myX, myY)
                .rect(myXD, myYD, False)
                .extrude(-(H / 4))
            )
            case = case.cut(pighole)
            myY = myY - pitch

    xd = H / 4.0
    if corner == CORNER_CHAMFER_TYPE:
        case = case.faces("<X").edges(">Z").chamfer(xd, xd)

    if corner == CORNER_FILLET_TYPE:
        case = case.faces("<X").edges(">Z").fillet(xd)

    if rotation != 0:
        case = case.rotate((0, 0, 0), (0, 0, 1), rotation)

    return case


def make_pigs(params):

    L = params["L"]  # package length
    W = params["W"]  # package width
    H = params["H"]  # package height
    pitch = params["pitch"]  # pin pitch
    PH = params["PH"]  # pin height above package height
    npins = params["npins"]  # total number of pins
    rotation = params["rotation"]  # rotation if required
    corner = params["corner"]  # Chamfer or corner
    A1 = params["A1"]  # Body seperation height

    # FreeCAD.Console.PrintMessage('make_pigs\r\n')

    tpins = npins / 2
    xd = L / 4.0
    yd = W / 3.0
    myXD = xd / 2.0
    myYD = yd
    myX = 0 - (xd / 2.0)
    myY = 0 - (yd / 2.0)
    pigs = (
        cq.Workplane("XY")
        .workplane(offset=A1 + H + PH, centerOption="CenterOfMass")
        .moveTo(myX, myY)
        .rect(myXD, myYD, False)
        .extrude(-(PH + (H / 4)))
    )

    if npins > 2:
        xd = L / 4.0
        yd = pitch / 3.0
        myX = 0 - (xd / 2.0)
        myXD = xd / 2.0
        myYD = yd

        if tpins % 2 == 0:
            myY = (pitch / 2.0) + (((tpins / 2) - 1) * pitch)
        else:
            myY = (((tpins / 2) - 1) * pitch) + pitch

        myY = myY - (myYD / 2)
        pigs = (
            cq.Workplane("XY")
            .workplane(offset=A1 + H + PH, centerOption="CenterOfMass")
            .moveTo(myX, myY)
            .rect(myXD, myYD, False)
            .extrude(-(PH + (H / 4)))
        )
        for i in range(0, int(tpins)):
            pig = (
                cq.Workplane("XY")
                .workplane(offset=A1 + H + PH, centerOption="CenterOfMass")
                .moveTo(myX, myY)
                .rect(myXD, myYD, False)
                .extrude(-(PH + (H / 4)))
            )
            pigs = pigs.union(pig)
            myY = myY - pitch

    if rotation != 0:
        pigs = pigs.rotate((0, 0, 0), (0, 0, 1), rotation)

    return pigs


def make_pins_smd(params):
    L = params["L"]  # package length
    W = params["W"]  # package width
    H = params["H"]  # package height
    pitch = params["pitch"]  # pitch
    paddist = params["paddist"]  # pad distance
    PH = params["PH"]  # pin height above package height
    npins = params["npins"]  # total number of pins
    rotation = params["rotation"]  # rotation if required
    corner = params["corner"]  # Chamfer or corner
    A1 = params["A1"]  # Body seperation height
    pinshape = params["pinshape"]  # If pin is L shape
    padsh = params["padsh"]  # pads height
    padsw = params["padsw"]  # pads width

    # FreeCAD.Console.PrintMessage("make_pins_smd, npins: %f\r\n" % npins)

    # pinshape 0 type - just a metallic surface on to the side of the block
    # pinshape 1 type - an S shape leg
    # pinshape 2 type - a leg comming along the board under the block

    tpins = npins / 2

    xd = padsw
    yd = padsw
    myXD = xd / 2.0
    myYD = yd
    myX = 0.0 - ((paddist) + (padsh / 2.0))
    myY = 0.0 - (padsw / 2.0)

    if pinshape == 0:
        myX = 0.0 - ((L / 2.0) + (padsh / 2.0))

    if pinshape == 1:
        myX = 0.0 - (paddist - (padsw / 2.0))

    if pinshape == 2:
        myX = 0.0 - paddist

    # Dummy creation to create pins and pin1 otside the 'if' scopes
    pins = (
        cq.Workplane("ZY")
        .workplane(offset=-myX - padsw - (padsh / 2.0), centerOption="CenterOfMass")
        .moveTo(0, myY)
        .rect(padsw, padsw, False)
        .extrude(padsh)
    )
    pin1 = (
        cq.Workplane("ZY")
        .workplane(offset=-myX - padsw - (padsh / 2.0), centerOption="CenterOfMass")
        .moveTo(0, myY)
        .rect(padsw, padsw, False)
        .extrude(padsh)
    )

    if pinshape == 0:
        pin1 = (
            cq.Workplane("ZY")
            .workplane(offset=myX, centerOption="CenterOfMass")
            .moveTo(0, 0 - (padsw / 2))
            .rect(padsw, padsw, False)
            .extrude(padsh)
        )

    elif pinshape == 1:
        pin1 = (
            cq.Workplane("ZY")
            .workplane(offset=-myX, centerOption="CenterOfMass")
            .moveTo(0, myY)
            .rect(padsw, padsw, False)
            .extrude(padsh)
        )
        pint = (
            cq.Workplane("XY")
            .workplane(offset=padsw - padsh, centerOption="CenterOfMass")
            .moveTo(myX, myY)
            .rect(-myX, padsw, False)
            .extrude(padsh)
        )
        pin1 = pin1.union(pint)
        pin1 = pin1.faces("<X").edges(">Z").fillet(padsh / 2)
        pint = (
            cq.Workplane("XY")
            .workplane(offset=0, centerOption="CenterOfMass")
            .moveTo(myX, myY)
            .rect(-padsw, padsw, False)
            .extrude(padsh)
        )
        pin1 = pin1.union(pint)
        pin1 = pin1.faces("<Z").edges(">X").fillet(padsh / 2)

    elif pinshape == 2:
        pin1 = (
            cq.Workplane("XY")
            .workplane(offset=0, centerOption="CenterOfMass")
            .moveTo(myX, myY)
            .rect(myX, padsw, False)
            .extrude(padsh)
        )

    pin2 = pin1.rotate((0, 0, 0), (0, 0, 1), 180)
    pin1 = pin1.union(pin2)
    pins = pin1

    if npins > 2:
        if tpins % 2 == 0:
            myY = (pitch / 2.0) + (((tpins / 2) - 1) * pitch)
        else:
            myY = (((tpins / 2) - 1) * pitch) + pitch

        pint = pin1.translate((0, myY, 0))
        pins = pint
        myY = myY - pitch

        for i in range(1, int(tpins)):
            pint = pin1.translate((0, myY, 0))
            pins = pins.union(pint)
            myY = myY - pitch

    if rotation != 0:
        pins = pins.rotate((0, 0, 0), (0, 0, 1), rotation)

    return pins
