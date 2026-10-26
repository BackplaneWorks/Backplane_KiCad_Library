import cadquery as cq

CASE_THT_TYPE = "tht"
CASE_SMD_TYPE = "smd"
CASE_THTSMD_TYPE = "thtsmd"
CASE_THT_N_TYPE = "tht_n"


CORNER_NONE_TYPE = "none"
CORNER_CHAMFER_TYPE = "chamfer"
CORNER_FILLET_TYPE = "fillet"


def make_case(params):

    L = params["L"]  # package length
    W = params["W"]  # package width
    H = params["H"]  # package height
    A1 = params["A1"]  # Body separation height
    rim = params["rim"]  # Rim underneath
    rotation = params["rotation"]  # rotation if required
    pin1corner = params["pin1corner"]  # Left upp corner relationsship to pin 1
    pin = params["pin"]  # pin/pad cordinates
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
        .workplane(centerOption="CenterOfMass", offset=A1)
        .moveTo(0, 0)
        .rect(1, 1, False)
        .extrude(H)
    )

    if pintype == CASE_SMD_TYPE:
        mvX = 0 - (L / 2.0)
        mvY = 0 - (W / 2.0)
        case = (
            cq.Workplane("XY")
            .workplane(centerOption="CenterOfMass", offset=A1)
            .moveTo(mvX, mvY)
            .rect(L, W, False)
            .extrude(H)
        )
    elif pintype == CASE_THT_TYPE or pintype == CASE_THT_N_TYPE:
        p = pin[0]
        mvX = p[1] + pin1corner[0]
        mvY = p[2] - pin1corner[1]
        case = (
            cq.Workplane("XY")
            .workplane(centerOption="CenterOfMass", offset=A1)
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
                    .workplane(centerOption="CenterOfMass", offset=A1)
                    .moveTo(mvX + rdx, mvY)
                    .rect(L - (2.0 * rdx), 0 - (W + 1.0), False)
                    .extrude(rdh)
                )
                case = case.cut(case1)
            if rdy != 0:
                case1 = (
                    cq.Workplane("XY")
                    .workplane(centerOption="CenterOfMass", offset=A1)
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

    if rotation != 0:
        case = case.rotate((0, 0, 0), (0, 0, 1), rotation)

    return case


def make_case_top(params):

    L = params["L"]  # package length
    W = params["W"]  # package width
    H = params["H"]  # package height
    A1 = params["A1"]  # Body separation height
    rotation = params["rotation"]  # rotation if required
    pin1corner = params["pin1corner"]  # Left upp corner relationsship to pin 1
    pin = params["pin"]  # pin/pad cordinates
    show_top = params["show_top"]  # If top should be visible or not
    pintype = params["pintype"]  # pin type , like SMD or THT

    mvX = 0
    mvY = 0
    # Dummy
    casetop = (
        cq.Workplane("XY")
        .workplane(centerOption="CenterOfMass", offset=A1 + H)
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
                .workplane(centerOption="CenterOfMass", offset=tty)
                .moveTo(mvX, mvY)
                .rect(L1, W1, False)
                .extrude(0.2)
            )
        elif pintype == CASE_THT_TYPE or pintype == CASE_THT_N_TYPE:
            p = pin[0]
            mvX = (p[1] + pin1corner[0]) + ((L - L1) / 2.0)
            mvY = (p[2] - pin1corner[1]) - ((W - W1) / 2.0)
            casetop = (
                cq.Workplane("XY")
                .workplane(centerOption="CenterOfMass", offset=tty)
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
                .workplane(centerOption="CenterOfMass", offset=A1 + (H / 4.0))
                .moveTo(mvX, mvY)
                .rect(0.1, 0.1, False)
                .extrude(0.1)
            )
        else:
            p = pin[0]
            mvX = (p[1] + pin1corner[0]) + (L / 2.0)
            mvY = (p[2] - pin1corner[1]) - (W / 2.0)
            casetop = (
                cq.Workplane("XY")
                .workplane(centerOption="CenterOfMass", offset=A1 + (H / 4.0))
                .moveTo(mvX, mvY)
                .rect(0.1, 0.1, False)
                .extrude(0.1)
            )

    if rotation != 0:
        casetop = casetop.rotate((0, 0, 0), (0, 0, 1), rotation)

    return casetop


def make_pins(params):

    L = params["L"]  # package length
    W = params["W"]  # package width
    H = params["H"]  # package height
    A1 = params["A1"]  # Body separation height
    rotation = params["rotation"]  # rotation if required
    pin = params["pin"]  # pin/pad cordinates
    rim = params["rim"]  # Rim underneath
    pintype = str(params["pintype"])

    pins = None

    pinss = 0.1
    if rim != None:
        if len(rim) == 3:
            rdx = rim[0]
            rdy = rim[1]
            rdh = rim[2]
            pinss = rdh + 0.1
    if pintype == "tht_n":
        pinss = 2.0
    #
    # Dummy
    #
    pins = None  # cq.Workplane("XY").workplane(centerOption="CenterOfMass", offset=0).moveTo(0, 0).rect(0.1, 0.1).extrude(0.1)
    # pint=cq.Workplane("XY").workplane(centerOption="CenterOfMass", offset=0).moveTo(0, 0).rect(0.1, 0.1).extrude(0.1)
    #

    for i in range(0, len(pin)):
        p = pin[i]

        pt = str(p[0])
        px = float(p[1])
        py = float(p[2])

        if pt == "rect":
            pl = float(p[3])
            pw = float(p[4])
            ph = float(p[5])
            # print('make_pins 1.1\r\n')

            pint = (
                cq.Workplane("XY")
                .workplane(centerOption="CenterOfMass", offset=A1 + pinss)
                .moveTo(px, -py)
                .rect(pl, pw)
                .extrude(0 - (ph + pinss))
            )

        elif pt == "round":
            # print('make_pins 1.2 i ' + str(i) + '\r\n')
            # print('make_pins 1.2 pt ' + str(pt) + '\r\n')
            # print('make_pins 1.2 px ' + str(px) + '\r\n')
            # print('make_pins 1.2 py ' + str(py) + '\r\n')
            pd = p[3]
            ph = p[4]
            # print('make_pins 1.2 pd ' + str(pd) + '\r\n')
            # print('make_pins 1.2 ph ' + str(ph) + '\r\n')

            pint = (
                cq.Workplane("XY")
                .workplane(centerOption="CenterOfMass", offset=A1 + pinss)
                .moveTo(px, -py)
                .circle(pd / 2.0, False)
                .extrude(0 - (ph + pinss))
            )
            pint = pint.faces("<Z").fillet(pd / 5.0)
            if pintype == "tht_n":
                pint = pint.faces(">Z").fillet(pd / 15.0)
                pind = (
                    cq.Workplane("XZ")
                    .workplane(centerOption="CenterOfMass", offset=0 - py + (pd / 2.0))
                    .moveTo(px, A1 + pinss)
                    .circle(pd / 2.0, False)
                    .extrude(0 - (W / 2.0))
                )
                pind = pind.faces("<Y").fillet(pd / 2.0)
                pint = pint.union(pind)

        elif pt == "smd":
            pd = p[3]
            ph = p[4]
            myX1 = px - pd
            myY1 = -py
            xD = myX1
            yD = pd
            if px < 0 and (py > (0 - (W / 2.0)) and py < ((W / 2.0))):
                # Left side
                if px < (0 - (L / 2.0)):
                    # print('make_pins smd 1\r\n')
                    # Normal pad
                    myX1 = px / 2.0
                    myY1 = -py
                    xD = px
                    yD = pd
                    pint = (
                        cq.Workplane("XY")
                        .workplane(centerOption="CenterOfMass", offset=0)
                        .moveTo(myX1, myY1)
                        .rect(xD, yD)
                        .extrude(ph)
                    )
                else:
                    # pad cordinate is inside the body
                    # print('make_pins smd 2\r\n')
                    myZ1 = pd / 2.0
                    myY1 = -py
                    xD = pd
                    yD = pd
                    pint = (
                        cq.Workplane("ZY")
                        .workplane(
                            centerOption="CenterOfMass", offset=(L / 2.0) - (ph / 2.0)
                        )
                        .moveTo(myZ1, myY1)
                        .rect(xD, yD)
                        .extrude(ph)
                    )

            elif px >= 0 and (py > (0 - (W / 2.0)) and py < ((W / 2.0))):
                # Right side
                if px > (L / 2.0):
                    # print('make_pins smd 3\r\n')
                    # Normal pad
                    myX1 = px / 2.0
                    xD = -px
                    yD = pd
                    pint = (
                        cq.Workplane("XY")
                        .workplane(centerOption="CenterOfMass", offset=0)
                        .moveTo(myX1, myY1)
                        .rect(xD, yD)
                        .extrude(ph)
                    )
                else:
                    # print('make_pins smd 4\r\n')
                    # pad cordinate is inside the body
                    myZ1 = pd / 2.0
                    myY1 = -py
                    xD = pd
                    yD = pd
                    pint = (
                        cq.Workplane("ZY")
                        .workplane(
                            centerOption="CenterOfMass",
                            offset=0 - ((L / 2.0) + (ph / 2.0)),
                        )
                        .moveTo(myZ1, myY1)
                        .rect(xD, yD)
                        .extrude(ph)
                    )
            elif py < 0:
                # top pad
                if p[1] < (W / 2.0):
                    # print('make_pins smd 5\r\n')
                    myX1 = px - (pd / 2.0)
                    myY1 = 0 - (py / 2.0)
                    yD = 0 - py
                    xD = pd
                    pint = (
                        cq.Workplane("XY")
                        .workplane(centerOption="CenterOfMass", offset=0)
                        .moveTo(myX1, myY1)
                        .rect(xD, yD)
                        .extrude(ph)
                    )
                else:
                    # print('make_pins smd 6\r\n')
                    # pad cordinate is inside the body
                    myZ1 = pd / 2.0
                    yD = pd
                    xD = pd
                    myX1 = px - (pd / 2.0)
                    pint = (
                        cq.Workplane("ZX")
                        .workplane(
                            centerOption="CenterOfMass", offset=((W / 2.0) - (ph / 2.0))
                        )
                        .moveTo(myZ1, myX1)
                        .rect(xD, yD)
                        .extrude(ph)
                    )
            else:
                # bottom pad
                if py > (W / 2.0):
                    # print('make_pins smd 7\r\n')
                    myX1 = px - (pd / 2.0)
                    myY1 = 0 - (py / 2.0)
                    yD = 0 - py
                    xD = pd
                    pint = (
                        cq.Workplane("XY")
                        .workplane(centerOption="CenterOfMass", offset=0)
                        .moveTo(myX1, myY1)
                        .rect(xD, yD)
                        .extrude(ph)
                    )
                else:
                    # print('make_pins smd 8\r\n')
                    # pad cordinate is inside the body
                    myX1 = px - (pd / 2.0)
                    myZ1 = pd / 2.0
                    yD = pd
                    xD = pd
                    pint = (
                        cq.Workplane("ZX")
                        .workplane(
                            centerOption="CenterOfMass",
                            offset=0 - ((W / 2.0) + (ph / 2.0)),
                        )
                        .moveTo(myZ1, myX1)
                        .rect(xD, yD)
                        .extrude(ph)
                    )

        if pins is None:
            pins = pint
        else:
            pins = pins.union(pint)

    if rotation != 0:
        pins = pins.rotate((0, 0, 0), (0, 0, 1), rotation)

    return pins
