import cadquery as cq

CASE_THT_TYPE = "tht"
CASE_SMD_TYPE = "smd"
CASE_THTSMD_TYPE = "thtsmd"
CASE_THT_N_TYPE = "tht_n"
# _TYPES = [CASE_THT_TYPE, CASE_SMD_TYPE, CASE_THT_N_TYPE ]


CORNER_NONE_TYPE = "none"
CORNER_CHAMFER_TYPE = "chamfer"
CORNER_FILLET_TYPE = "fillet"
_CORNER = [CORNER_NONE_TYPE, CORNER_CHAMFER_TYPE, CORNER_FILLET_TYPE]


def make_case(params):

    L = params["L"]  # package length
    W = params["W"]  # package width
    H = params["H"]  # package height
    A1 = params["A1"]  # Body separation height
    rim = params["rim"]  # Rim underneath
    pin1corner = params["pin1corner"]  # Left upp corner relationsship to pin 1
    pin = params["pin"]  # pin/pad coordinates
    roundbelly = params["roundbelly"]  # If belly of caseing should be round (or flat)
    pintype = params["pintype"]  # pin type , like SMD or THT

    ff = W / 20.0

    if ff > 0.25:
        ff = 0.25

    mvX = 0
    mvY = 0
    # Dummy
    case = (
        cq.Workplane("XY")
        .workplane(offset=A1, centerOption="CenterOfMass")
        .moveTo(0, 0)
        .rect(1, 1, False)
        .extrude(H)
    )

    if pintype == CASE_SMD_TYPE:
        mvX = 0 - (L / 2.0)
        mvY = 0 - (W / 2.0)
        case = (
            cq.Workplane("XY")
            .workplane(offset=A1, centerOption="CenterOfMass")
            .moveTo(mvX, mvY)
            .rect(L, W, False)
            .extrude(H)
        )
    elif (pintype == CASE_THT_TYPE) or (pintype == CASE_THT_N_TYPE):
        p = pin[0]
        mvX = p[0] + pin1corner[0]
        mvY = p[1] - pin1corner[1]
        # FreeCAD.Console.PrintMessage('\r\n')
        # FreeCAD.Console.PrintMessage('CASE_THT_TYPE\r\n')
        case = (
            cq.Workplane("XY")
            .workplane(offset=A1, centerOption="CenterOfMass")
            .moveTo(mvX, mvY)
            .rect(L, -W, False)
            .extrude(H)
        )

    if rim != None:
        if len(rim) == 3:
            rdx = rim[0]
            rdy = rim[1]
            rdh = rim[2]
            if rdx != 0:
                case1 = (
                    cq.Workplane("XY")
                    .workplane(offset=A1, centerOption="CenterOfMass")
                    .moveTo(mvX + rdx, mvY)
                    .rect(L - (2.0 * rdx), 0 - (W + 1.0), False)
                    .extrude(rdh)
                )
                case = case.cut(case1)
            if rdy != 0:
                case1 = (
                    cq.Workplane("XY")
                    .workplane(offset=A1, centerOption="CenterOfMass")
                    .moveTo(mvX, mvY - rdy)
                    .rect(L + 1.0, 0 - (W - (2.0 * rdy)), False)
                    .extrude(rdh)
                )
                case = case.cut(case1)

    case = case.faces("<X").edges("<Y").fillet(ff)
    case = case.faces("<X").edges(">Y").fillet(ff)
    case = case.faces(">X").edges("<Y").fillet(ff)
    case = case.faces(">X").edges(">Y").fillet(ff)
    case = case.faces(">Y").edges(">Z").fillet(ff)

    if roundbelly == 1 and rim == None:
        # Belly is rounded
        case = case.faces(">Y").edges("<Z").fillet(ff / 2.0)

    return case


def make_case_top(params):

    L = params["L"]  # package length
    W = params["W"]  # package width
    H = params["H"]  # package height
    A1 = params["A1"]  # Body separation height
    pin1corner = params["pin1corner"]  # Left upp corner relationsship to pin 1
    pin = params["pin"]  # pin/pad cordinates
    show_top = params["show_top"]  # If top should be visible or not
    pintype = params["pintype"]  # pin type , like SMD or THT

    mvX = 0
    mvY = 0
    # Dummy
    casetop = (
        cq.Workplane("XY")
        .workplane(offset=A1 + H, centerOption="CenterOfMass")
        .moveTo(0, 0)
        .rect(1, 1, False)
        .extrude(0.8)
    )

    ff = W / 20.0
    if ff > 1.0:
        ff = 1.0

    Ldt = ff
    Wdt = ff

    L1 = L - (2.0 * Ldt)
    W1 = W - (2.0 * Wdt)

    if show_top == 1:
        tty = A1 + H - 0.1

        if pintype == CASE_SMD_TYPE:
            mvX = (0 - (L1 / 2.0)) + ((L - L1) / 2.0)
            mvY = (0 - (W1 / 2.0)) - ((W - W1) / 2.0)
            casetop = (
                cq.Workplane("XY")
                .workplane(offset=tty, centerOption="CenterOfMass")
                .moveTo(mvX, mvY)
                .rect(L1, W1, False)
                .extrude(0.2)
            )
        elif pintype == CASE_THT_TYPE or pintype == CASE_THT_N_TYPE:
            p = pin[0]
            mvX = (p[0] + pin1corner[0]) + ((L - L1) / 2.0)
            mvY = (p[1] - pin1corner[1]) - ((W - W1) / 2.0)
            casetop = (
                cq.Workplane("XY")
                .workplane(offset=tty, centerOption="CenterOfMass")
                .moveTo(mvX, mvY)
                .rect(L1, -W1, False)
                .extrude(0.2)
            )

        casetop = casetop.faces("<X").edges("<Y").fillet(ff)
        casetop = casetop.faces("<X").edges(">Y").fillet(ff)
        casetop = casetop.faces(">X").edges("<Y").fillet(ff)
        casetop = casetop.faces(">X").edges(">Y").fillet(ff)
    else:
        # If it is not used, just hide it inside the body
        if pintype == CASE_SMD_TYPE:
            mvX = 0
            mvY = 0
            casetop = (
                cq.Workplane("XY")
                .workplane(offset=A1 + (H / 4.0), centerOption="CenterOfMass")
                .moveTo(mvX, mvY)
                .rect(0.1, 0.1, False)
                .extrude(0.1)
            )
        else:
            p = pin[0]
            mvX = (p[0] + pin1corner[0]) + (L / 2.0)
            mvY = (p[1] - pin1corner[1]) - (W / 2.0)
            casetop = (
                cq.Workplane("XY")
                .workplane(offset=A1 + (H / 4.0), centerOption="CenterOfMass")
                .moveTo(mvX, mvY)
                .rect(0.1, 0.1, False)
                .extrude(0.1)
            )

    return casetop


def make_pins_tht(params):

    L = params["L"]  # package length
    W = params["W"]  # package width
    H = params["H"]  # package height
    A1 = params["A1"]  # Body separation height
    rim = params["rim"]  # Rim underneath
    pinpadsize = params["pinpadsize"]  # pin diameter or pad size
    pinpadh = params["pinpadh"]  # pin length, pad height
    pintype = params["pintype"]  # Casing type
    pin = params["pin"]  # pin/pad cordinates

    pinss = 0.1
    if rim != None:
        if len(rim) == 3:
            rdx = rim[0]
            rdy = rim[1]
            rdh = rim[2]
            pinss = rdh + 0.1

    p = pin[0]
    pins = (
        cq.Workplane("XY")
        .workplane(offset=A1 + pinss, centerOption="CenterOfMass")
        .moveTo(p[0], -p[1])
        .circle(pinpadsize / 2.0, False)
        .extrude(0 - (pinpadh + pinss))
    )
    pins = pins.faces("<Z").fillet(pinpadsize / 5.0)
    if len(p) > 3:
        pt = p[2]
        if pt == "round":
            pd = p[3]
            pins = (
                cq.Workplane("XY")
                .workplane(offset=A1 + pinss, centerOption="CenterOfMass")
                .moveTo(p[0], -p[1])
                .circle(pd / 2.0, False)
                .extrude(0 - (pinpadh + pinss))
            )
            pins = pins.faces("<Z").fillet(pinpadsize / 5.0)
        if pt == "rect" and len(p) > 4:
            pdx = p[3]
            pdy = p[4]
            pd = pdx
            if pdy < pdx:
                pd = pdy
            pins = (
                cq.Workplane("XY")
                .workplane(offset=A1 + pinss, centerOption="CenterOfMass")
                .moveTo(p[0], -p[1])
                .rect(pdx, pdy, centered=True)
                .extrude(0 - (pinpadh + pinss))
            )
            pins = pins.faces("<Z").fillet(pd / 5.0)

    for i in range(1, len(pin)):
        p = pin[i]
        pint = (
            cq.Workplane("XY")
            .workplane(offset=A1 + pinss, centerOption="CenterOfMass")
            .moveTo(p[0], -p[1])
            .circle(pinpadsize / 2.0, False)
            .extrude(0 - (pinpadh + pinss))
        )
        pint = pint.faces("<Z").fillet(pinpadsize / 5.0)
        if len(p) > 3:
            pt = p[2]
            if pt == "round":
                pd = p[3]
                pint = (
                    cq.Workplane("XY")
                    .workplane(offset=A1 + pinss, centerOption="CenterOfMass")
                    .moveTo(p[0], -p[1])
                    .circle(pd / 2.0, False)
                    .extrude(0 - (pinpadh + pinss))
                )
                pint = pint.faces("<Z").fillet(pd / 5.0)
            if pt == "rect" and len(p) > 4:
                pdx = p[3]
                pdy = p[4]
                pd = pdx
                if pdy < pdx:
                    pd = pdy
                pint = (
                    cq.Workplane("XY")
                    .workplane(offset=A1 + pinss, centerOption="CenterOfMass")
                    .moveTo(p[0], -p[1])
                    .rect(pdx, pdy, centered=True)
                    .extrude(0 - (pinpadh + pinss))
                )
                pint = pint.faces("<Z").fillet(pd / 5.0)

        #        pint=cq.Workplane("XY").workplane(offset=A1 + pinss).moveTo(p[0], -p[1]).circle(pinpadsize / 2.0, False).extrude(0 - (pinpadh + pinss))
        #        pint = pint.faces("<Z").fillet(pinpadsize / 5.0)
        pins = pins.union(pint)

    return pins


def make_pins_tht_n(params):

    L = params["L"]  # package length
    W = params["W"]  # package width
    H = params["H"]  # package height
    A1 = params["A1"]  # Body separation height
    pinpadsize = params["pinpadsize"]  # pin diameter or pad size
    pinpadh = params["pinpadh"]  # pin length, pad height
    pintype = params["pintype"]  # Casing type
    pin = params["pin"]  # pin/pad cordinates

    p = pin[0]
    pins = (
        cq.Workplane("XY")
        .workplane(offset=A1 + 2.0, centerOption="CenterOfMass")
        .moveTo(p[0], -p[1])
        .circle(pinpadsize / 2.0, False)
        .extrude(0 - (pinpadh + 2.0))
    )
    pins = pins.faces("<Z").fillet(pinpadsize / 5.0)
    pind = (
        cq.Workplane("XZ")
        .workplane(offset=0 - p[1] + (pinpadsize / 2.0), centerOption="CenterOfMass")
        .moveTo(p[0], A1 + 2.0)
        .circle(pinpadsize / 2.0, False)
        .extrude(0 - (W / 2.0))
    )
    pind = pind.faces("<Y").fillet(pinpadsize / 2.0)
    pins = pins.union(pind)

    for i in range(1, len(pin)):
        p = pin[i]
        pint = (
            cq.Workplane("XY")
            .workplane(offset=A1 + 2.0, centerOption="CenterOfMass")
            .moveTo(p[0], -p[1])
            .circle(pinpadsize / 2.0, False)
            .extrude(0 - (pinpadh + 2.0))
        )
        pint = pint.faces("<Z").fillet(pinpadsize / 5.0)
        pind = (
            cq.Workplane("XZ")
            .workplane(
                offset=0 - p[1] + (pinpadsize / 2.0), centerOption="CenterOfMass"
            )
            .moveTo(p[0], A1 + 2.0)
            .circle(pinpadsize / 2.0, False)
            .extrude(0 - (W / 2.0))
        )
        pind = pind.faces("<Y").fillet(pinpadsize / 2.0)
        pint = pint.union(pind)
        pins = pins.union(pint)

    return pins


def make_pins_smd(params):

    L = params["L"]  # package length
    W = params["W"]  # package width
    H = params["H"]  # package height
    A1 = params["A1"]  # Body separation height
    pinpadsize = params["pinpadsize"]  # pin diameter or pad size
    pinpadh = params["pinpadh"]  # pin length, pad height
    pintype = params["pintype"]  # Casing type
    pin = params["pin"]  # pin/pad cordinates

    #
    # Dummy
    #
    pins = (
        cq.Workplane("XY")
        .workplane(offset=0, centerOption="CenterOfMass")
        .moveTo(0, 0)
        .rect(0.1, 0.1)
        .extrude(0.1)
    )
    #

    for i in range(0, len(pin)):
        p = pin[i]
        myX1 = p[0] - pinpadsize
        myY1 = -p[1]
        xD = myX1
        yD = pinpadsize
        if p[0] < 0 and (p[1] > (0 - (W / 2.0)) and p[1] < ((W / 2.0))):
            # Left side
            if p[0] < (0 - (L / 2.0)):
                # Normal pad
                myX1 = p[0] / 2.0
                myY1 = -p[1]
                xD = p[0]
                yD = pinpadsize
                pint = (
                    cq.Workplane("XY")
                    .workplane(offset=0, centerOption="CenterOfMass")
                    .moveTo(myX1, myY1)
                    .rect(xD, yD)
                    .extrude(pinpadh)
                )
            else:
                # pad cordinate is inside the body
                myZ1 = pinpadsize / 2.0
                myY1 = -p[1]
                xD = pinpadsize
                yD = pinpadsize
                pint = (
                    cq.Workplane("ZY")
                    .workplane(
                        offset=(L / 2.0) - (pinpadh / 2.0), centerOption="CenterOfMass"
                    )
                    .moveTo(myZ1, myY1)
                    .rect(xD, yD)
                    .extrude(pinpadh)
                )

        #
        elif p[0] >= 0 and (p[1] > (0 - (W / 2.0)) and p[1] < ((W / 2.0))):
            # Right side
            if p[0] > (L / 2.0):
                # Normal pad
                myX1 = p[0] / 2.0
                xD = -p[0]
                yD = pinpadsize
                pint = (
                    cq.Workplane("XY")
                    .workplane(offset=0, centerOption="CenterOfMass")
                    .moveTo(myX1, myY1)
                    .rect(xD, yD)
                    .extrude(pinpadh)
                )
            else:
                # pad cordinate is inside the body
                myZ1 = pinpadsize / 2.0
                myY1 = -p[1]
                xD = pinpadsize
                yD = pinpadsize
                pint = (
                    cq.Workplane("ZY")
                    .workplane(
                        offset=0 - ((L / 2.0) + (pinpadh / 2.0)),
                        centerOption="CenterOfMass",
                    )
                    .moveTo(myZ1, myY1)
                    .rect(xD, yD)
                    .extrude(pinpadh)
                )
        elif p[1] < 0:
            # top pad
            if p[1] < (W / 2.0):
                myX1 = p[0] - (pinpadsize / 2.0)
                myY1 = 0 - (p[1] / 2.0)
                yD = 0 - p[1]
                xD = pinpadsize
                pint = (
                    cq.Workplane("XY")
                    .workplane(offset=0, centerOption="CenterOfMass")
                    .moveTo(myX1, myY1)
                    .rect(xD, yD)
                    .extrude(pinpadh)
                )
            else:
                # pad cordinate is inside the body
                myZ1 = pinpadsize / 2.0
                yD = pinpadsize
                xD = pinpadsize
                myX1 = p[0] - (pinpadsize / 2.0)
                pint = (
                    cq.Workplane("ZX")
                    .workplane(
                        offset=((W / 2.0) - (pinpadh / 2.0)),
                        centerOption="CenterOfMass",
                    )
                    .moveTo(myZ1, myX1)
                    .rect(xD, yD)
                    .extrude(pinpadh)
                )
        else:
            # bottom pad
            if p[1] > (W / 2.0):
                myX1 = p[0] - (pinpadsize / 2.0)
                myY1 = 0 - (p[1] / 2.0)
                yD = 0 - p[1]
                xD = pinpadsize
                pint = (
                    cq.Workplane("XY")
                    .workplane(offset=0, centerOption="CenterOfMass")
                    .moveTo(myX1, myY1)
                    .rect(xD, yD)
                    .extrude(pinpadh)
                )
            else:
                # pad cordinate is inside the body
                myX1 = p[0] - (pinpadsize / 2.0)
                myZ1 = pinpadsize / 2.0
                yD = pinpadsize
                xD = pinpadsize
                pint = (
                    cq.Workplane("ZX")
                    .workplane(
                        offset=0 - ((W / 2.0) + (pinpadh / 2.0)),
                        centerOption="CenterOfMass",
                    )
                    .moveTo(myZ1, myX1)
                    .rect(xD, yD)
                    .extrude(pinpadh)
                )

        if i == 0:
            pins = pint
        else:
            pins = pins.union(pint)

    return pins
