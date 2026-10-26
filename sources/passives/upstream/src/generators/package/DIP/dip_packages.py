from math import radians, tan

import cadquery as cq

from generators.tools.model.cq_helpers import union_all

CASE_THT_TYPE = "tht"
CASE_SMD_TYPE = "smd"
CASE_THTSMD_TYPE = "thtsmd"

CORNER_CHAMFER_TYPE = "chamfer"
CORNER_FILLET_TYPE = "fillet"


def make_case(params):

    D = params["D"]  # package length
    E1 = params["E1"]  # package width
    E = params["E"]  # package shoulder-to-shoulder width
    A1 = params["A1"]  # package board seperation
    A2 = params["A2"]  # package height

    b1 = params["b1"]  # pin width
    b = params["b"]  # pin width
    e = params["e"]  # pin center to center distance (pitch)

    npins = params["npins"]  # number of pins

    corner = params["corner"]
    excludepins = params["excludepins"]

    # common dimensions
    L = 3.3  # tip to seating plane
    c = 0.254  # lead thickness

    fp_r = 0.8  # first pin indicator radius
    fp_d = 0.2  # first pin indicator depth
    fp_t = 0.4  # first pin indicator distance from edge
    ef = 0.0  # 0.05,      # fillet of edges  Note: bigger bytes model with fillet and possible geometry errorsy TBD

    ti_r = 0.75  # top indicator radius
    ti_d = 0.5  # top indicator depth

    the = 12.0  # body angle in degrees
    tb_s = 0.15  # top part of body is that much smaller

    # calculated dimensions
    A = A1 + A2

    A2_t = (A2 - c) / 2.0  # body top part height
    A2_b = A2_t  # body bottom part height
    D_b = D - 2 * tan(radians(the)) * A2_b  # bottom length
    E1_b = E1 - 2 * tan(radians(the)) * A2_b  # bottom width
    D_t1 = D - tb_s  # top part bottom length
    E1_t1 = E1 - tb_s  # top part bottom width
    D_t2 = D_t1 - 2 * tan(radians(the)) * A2_t  # top part upper length
    E1_t2 = E1_t1 - 2 * tan(radians(the)) * A2_t  # top part upper width

    case = (
        cq.Workplane(cq.Plane.XY())
        .workplane(centerOption="CenterOfMass", offset=A1)
        .rect(D_b, E1_b)
        .workplane(centerOption="CenterOfMass", offset=A2_b)
        .rect(D, E1)
        .workplane(centerOption="CenterOfMass", offset=c)
        .rect(D, E1)
        .rect(D_t1, E1_t1)
        .workplane(centerOption="CenterOfMass", offset=A2_t)
        .rect(D_t2, E1_t2)
        .loft(ruled=True)
    )

    # draw top indicator
    case = case.faces(">Z").center(D_b / 2.0, 0).hole(ti_r * 2, ti_d)

    # finishing touches
    BS = cq.selectors.BoxSelector
    if ef != 0:
        case = case.edges(
            BS((D_t2 / 2.0 + 0.1, E1_t2 / 2.0, 0), (D / 2.0 + 0.1, E1 / 2.0 + 0.1, A2))
        ).fillet(ef)
        case = case.edges(
            BS((-D_t2 / 2.0, E1_t2 / 2.0, 0), (-D / 2.0 - 0.1, E1 / 2.0 + 0.1, A2))
        ).fillet(ef)
        case = case.edges(
            BS((-D_t2 / 2.0, -E1_t2 / 2.0, 0), (-D / 2.0 - 0.1, -E1 / 2.0 - 0.1, A2))
        ).fillet(ef)
        case = case.edges(
            BS((D_t2 / 2.0, -E1_t2 / 2.0, 0), (D / 2.0 + 0.1, -E1 / 2.0 - 0.1, A2))
        ).fillet(ef)
        case = case.edges(
            BS((D / 2.0, E1 / 2.0, A - ti_d - 0.001), (-D / 2.0, -E1 / 2.0, A + 0.1))
        ).fillet(ef)
    ## else:
    ##     case = case.edges(BS((D_t2/2.+0.1, E1_t2/2., 0), (D/2.+0.1, E1/2.+0.1, A2)))
    ##     case = case.edges(BS((-D_t2/2., E1_t2/2., 0), (-D/2.-0.1, E1/2.+0.1, A2)))
    ##     case = case.edges(BS((-D_t2/2., -E1_t2/2., 0), (-D/2.-0.1, -E1/2.-0.1, A2)))
    ##     case = case.edges(BS((D_t2/2., -E1_t2/2., 0), (D/2.+0.1, -E1/2.-0.1, A2)))
    ##     case = case.edges(BS((D/2.,E1/2.,A-ti_d-0.001), (-D/2.,-E1/2.,A+0.1)))

    # add first pin indicator
    ## maui case = case.faces(">Z").workplane().center(D_t2/2.-fp_r-fp_t,E1_t2/2.-fp_r-fp_t).\
    ## maui        hole(fp_r*2, fp_d)

    if params["type"] == CASE_SMD_TYPE:
        mvX = npins * e / 4 + e / 2
        mvX = (((npins / 2.0) - 1.0) / 2) * e
        mvY = (E - c) / 2
        case = case.translate((mvX, mvY, 0))

    return case


def make_pins_tht(params):

    D = params["D"]  # package length
    E1 = params["E1"]  # package width
    E = params["E"]  # package shoulder-to-shoulder width
    A1 = params["A1"]  # package board seperation
    A2 = params["A2"]  # package height

    b1 = params["b1"]  # pin width
    b = params["b"]  # pin width
    e = params["e"]  # pin center to center distance (pitch)

    npins = params["npins"]  # number of pins

    corner = params["corner"]
    excludepins = params["excludepins"]

    # common dimensions
    L = 3.3  # tip to seating plane
    c = 0.254  # lead thickness

    # draw 1st pin (side pin shape)
    x = e * (npins / 4.0 - 0.5)  # center x position of first pin
    ty = (A2 + c) / 2.0 + A1  # top point (max z) of pin

    # draw the side part of the pin
    pin = (
        cq.Workplane("XZ", (x, E / 2.0, 0))
        .moveTo(+b / 2.0, ty)
        .line(0, -(L + ty - b))
        .line(-b / 4.0, -b)
        .line(-b / 2.0, 0)
        .line(-b / 4.0, b)
        .line(0, L - b)
        .line(-(b1 - b) / 2.0, 0)
        .line(0, ty)
        .close()
        .extrude(c)
    )

    # draw the top part of the pin
    pin = (
        pin.faces(">Z")
        .workplane(centerOption="CenterOfMass")
        .center(-(b1 + b) / 4.0, c / 2.0)
        .rect((b1 + b) / 2.0, -E / 2.0, centered=False)
        .extrude(-c)
    )

    # fillet the corners
    def fillet_corner(pina):
        BS = cq.selectors.BoxSelector
        return (
            pina.edges(
                BS(
                    (1000, E / 2.0 - c - 0.001, ty - c - 0.001),
                    (-1000, E / 2.0 - c + 0.001, ty - c + 0.001),
                )
            )
            .fillet(c / 2.0)
            .edges(
                BS(
                    (1000, E / 2.0 - 0.001, ty - 0.001),
                    (-1000, E / 2.0 + 0.001, ty + 0.001),
                )
            )
            .fillet(1.5 * c)
        )

    def chamfer_corner(pina):
        BS = cq.selectors.BoxSelector
        return (
            pina.edges(
                BS(
                    (1000, E / 2.0 - c - 0.001, ty - c - 0.001),
                    (-1000, E / 2.0 - c + 0.001, ty - c + 0.001),
                )
            )
            .chamfer(c / 0.18)
            .edges(
                BS(
                    (1000, E / 2.0 - 0.001, ty - 0.001),
                    (-1000, E / 2.0 + 0.001, ty + 0.001),
                )
            )
            .chamfer(6.0 * c)
        )

    if corner == CORNER_CHAMFER_TYPE:
        pin = chamfer_corner(pin)
    else:
        pin = fillet_corner(pin)

    pinsL = [pin]
    pinsR = [pin.translate((0, 0, 0))]

    if npins / 2 > 2:
        # draw the 2nd pin (regular pin shape)
        x = e * (npins / 4.0 - 0.5 - 1)  # center x position of 2nd pin
        pin2 = (
            cq.Workplane("XZ", (x, E / 2.0, 0))
            .moveTo(b1 / 2.0, ty)
            .line(0, -ty)
            .line(-(b1 - b) / 2.0, 0)
            .line(0, -L + b)
            .line(-b / 4.0, -b)
            .line(-b / 2.0, 0)
            .line(-b / 4.0, b)
            .line(0, L - b)
            .line(-(b1 - b) / 2.0, 0)
            .line(0, ty)
            .close()
            .extrude(c)
        )

        # draw the top part of the pin
        pin2 = (
            pin2.faces(">Z")
            .workplane(centerOption="CenterOfMass")
            .center(0, -E / 4.0)
            .rect(b1, -E / 2.0)
            .extrude(-c)
        )
        if corner == CORNER_CHAMFER_TYPE:
            pin2 = chamfer_corner(pin2)
        else:
            pin2 = fillet_corner(pin2)

        # create other pins (except last one)
        pinsL.append(pin2)
        pinsR.append(pin2.translate((0, 0, 0)))
        for i in range(2, npins // 2 - 1):
            pin_i = pin2.translate((-e * (i - 1), 0, 0))
            pinsL.append(pin_i)
            pinsR.append(pin_i.translate((0, 0, 0)))

    # create last pin (mirrored 1st pin)
    x = -e * (npins / 4.0 - 0.5)
    pinl = (
        cq.Workplane("XZ", (x, E / 2.0, 0))
        .moveTo(-b / 2.0, ty)
        .line(0, -(L + ty - b))
        .line(b / 4.0, -b)
        .line(b / 2.0, 0)
        .line(b / 4.0, b)
        .line(0, L - b)
        .line((b1 - b) / 2.0, 0)
        .line(0, ty)
        .close()
        .extrude(c)
        .faces(">Z")
        .workplane(centerOption="CenterOfMass")
        .center(-(b1 + b) / 4.0, c / 2.0)
        .rect((b1 + b) / 2.0, -E / 2.0, centered=False)
        .extrude(-c)
    )
    # pinl = fillet_corner(pinl)
    if corner == CORNER_CHAMFER_TYPE:
        pinl = chamfer_corner(pinl)
    else:
        pinl = fillet_corner(pinl)

    pinsL.append(pinl)
    pinsR.append(pinl.translate((0, 0, 0)))

    # print('\r\n')
    pinsLNew = []
    pinsRNew = []
    AddPinLeft = True
    AddPinRight = True
    # tts = "len(pinsL) " + str(len(pinsL)) + "\r\n"
    # print(tts)
    # tts = "len(pinsR) " + str(len(pinsR)) + "\r\n"
    # print(tts)
    # for ei in excludepins:
    # tts = "excludepins " + str(ei) + "\r\n"
    # print(tts)
    for i in range(0, npins // 2):
        AddPinLeft = True
        for ei in excludepins:
            if (i + 1) == ei:
                AddPinLeft = False
        if AddPinLeft:
            # tts = "Adding to pinsLNew " + str(i) + "\r\n"
            # print(tts)
            pinsLNew.append(pinsL[i])

    for i in range(npins // 2, npins):
        AddPinRight = True
        for ei in excludepins:
            if (i + 1) == ei:
                AddPinRight = False
        if AddPinRight:
            # tts = "Adding to pinsRNew " + str(i - (npins/2)) + "\r\n"
            # print(tts)
            pinsRNew.append(pinsR[i - (npins // 2)])

    # union all pins
    pinsLT = union_all(pinsLNew)
    pinsRT = union_all(pinsRNew)

    # create other side of the pins (mirror would be better but there
    # is no solid mirror API)
    pinsT = pinsLT.union(pinsRT.rotate((0, 0, 0), (0, 0, 1), 180))

    # mvX = (npins*e/4+e/2)
    # mvY = (E-c)/2
    # pins = pins.translate ((-mvX,-mvY,0))

    return pinsT


def make_pins_smd(params):

    D = params["D"]  # package length
    E1 = params["E1"]  # package width
    E = params["E"]  # package shoulder-to-shoulder width
    A1 = params["A1"]  # package board seperation
    A2 = params["A2"]  # package height

    b1 = params["b1"]  # pin width
    b = params["b"]  # pin width
    e = params["e"]  # pin center to center distance (pitch)

    npins = params["npins"]  # number of pins

    corner = params["corner"]
    excludepins = params["excludepins"]

    # common dimensions
    L = 3.3  # tip to seating plane
    c = 0.254  # lead thickness

    # fillet the corners
    def fillet_corner(pina):
        BS = cq.selectors.BoxSelector
        return (
            pina.edges(
                BS(
                    (1000, E / 2.0 - c - 0.001, ty - c - 0.001),
                    (-1000, E / 2.0 - c + 0.001, ty - c + 0.001),
                )
            )
            .fillet(c / 2.0)
            .edges(
                BS(
                    (1000, E / 2.0 - c - 0.001, -0.001),
                    (-1000, E / 2.0 - c + 0.001, +0.001),
                )
            )
            .fillet(1.5 * c)
            .edges(
                BS(
                    (1000, E / 2.0 - 0.001, ty - 0.001),
                    (-1000, E / 2.0 + 0.001, ty + 0.001),
                )
            )
            .fillet(1.5 * c)
            .edges(
                BS(
                    (1000, E / 2.0 - 0.001, c - 0.001),
                    (-1000, E / 2.0 + 0.001, c + 0.001),
                )
            )
            .fillet(c / 2.0)
        )

    def chamfer_corner(pina):
        BS = cq.selectors.BoxSelector
        return (
            pina.edges(
                BS(
                    (1000, E / 2.0 - c - 0.001, ty - c - 0.001),
                    (-1000, E / 2.0 - c + 0.001, ty - c + 0.001),
                )
            )
            .chamfer(c / 0.18)
            .edges(
                BS(
                    (1000, E / 2.0 - 0.001, ty - 0.001),
                    (-1000, E / 2.0 + 0.001, ty + 0.001),
                )
            )
            .chamfer(6.0 * c)
        )

    # draw 1st pin
    x = e * (npins / 4.0 - 0.5)  # center x position of first pin
    ty = (A2 + c) / 2.0 + A1  # top point (max z) of pin

    # draw the side part of the pin
    pin = (
        cq.Workplane("XZ", (x, E / 2.0, 0))
        .moveTo(-b, 0)
        .lineTo(-b, ty)
        .lineTo(b, ty)
        .lineTo(b, 0)
        .close()
        .extrude(c)
    )

    # draw the top part of the pin
    pin = (
        pin.faces(">Z")
        .workplane(centerOption="CenterOfMass")
        .moveTo(-b, 0)
        .lineTo(-b, -E / 2.0)
        .lineTo(b, -E / 2.0)
        .lineTo(b, 0)
        .close()
        .extrude(-c)
    )

    # Draw the bottom part of the pin
    pin = (
        pin.faces("<Z")
        .workplane(centerOption="CenterOfMass")
        .center(0, -b + c / 2.0)
        .rect(2 * b, 2 * b)
        .extrude(-c)
    )

    if corner == CORNER_CHAMFER_TYPE:
        pin = chamfer_corner(pin)
    else:
        pin = fillet_corner(pin)

    pinsL = [pin]
    pinsR = [pin.translate((0, 0, 0))]
    #
    #
    #
    if npins / 2 > 2:
        # draw the 2nd pin (regular pin shape)
        x = e * (npins / 4.0 - 0.5 - 1)  # center x position of 2nd pin
        pin2 = (
            cq.Workplane("XZ", (x, E / 2.0, 0))
            .moveTo(-b, 0)
            .lineTo(-b, ty)
            .lineTo(b, ty)
            .lineTo(b, 0)
            .close()
            .extrude(c)
        )

        # draw the top part of the pin
        pin2 = (
            pin2.faces(">Z")
            .workplane(centerOption="CenterOfMass")
            .center(0, -(4.0 * b) + c / 2.0)
            .rect(2 * b, 8 * b)
            .extrude(-c)
        )

        # Draw the bottom part of the pin
        pin2 = (
            pin2.faces("<Z")
            .workplane(centerOption="CenterOfMass")
            .center(0, -b + c / 2.0)
            .rect(2 * b, 2 * b)
            .extrude(-c)
        )

        if corner == CORNER_CHAMFER_TYPE:
            pin2 = chamfer_corner(pin2)
        else:
            pin2 = fillet_corner(pin2)

        # create other pins (except last one)
        pinsL.append(pin2)
        pinsR.append(pin2.translate((0, 0, 0)))
        for i in range(2, npins // 2 - 1):
            pin_i = pin2.translate((-e * (i - 1), 0, 0))
            pinsL.append(pin_i)
            pinsR.append(pin_i.translate((0, 0, 0)))

    # create last pin (mirrored 1st pin)
    x = -e * (npins / 4.0 - 0.5)
    pinl = (
        cq.Workplane("XZ", (x, E / 2.0, 0))
        .moveTo(-b, 0)
        .lineTo(-b, ty)
        .lineTo(b, ty)
        .lineTo(b, 0)
        .close()
        .extrude(c)
    )
    # draw the top part of the pin
    pinl = (
        pinl.faces(">Z")
        .workplane(centerOption="CenterOfMass")
        .center(0, -(4.0 * b) + c / 2.0)
        .rect(2 * b, 8 * b)
        .extrude(-c)
    )

    # Draw the bottom part of the pin
    pinl = (
        pinl.faces("<Z")
        .workplane(centerOption="CenterOfMass")
        .center(0, -b + c / 2.0)
        .rect(2 * b, 2 * b)
        .extrude(-c)
    )
    if corner == CORNER_CHAMFER_TYPE:
        pinl = chamfer_corner(pinl)
    else:
        pinl = fillet_corner(pinl)

    pinsL.append(pinl)
    pinsR.append(pinl.translate((0, 0, 0)))

    # print('\r\n')
    pinsLNew = []
    pinsRNew = []
    AddPinLeft = True
    AddPinRight = True
    # tts = "len(pinsL) " + str(len(pinsL)) + "\r\n"
    # print(tts)
    # tts = "len(pinsR) " + str(len(pinsR)) + "\r\n"
    # print(tts)
    # for ei in excludepins:
    #     tts = "excludepins " + str(ei) + "\r\n"
    #     print(tts)
    for i in range(0, npins // 2):
        AddPinLeft = True
        for ei in excludepins:
            if (i + 1) == ei:
                AddPinLeft = False
        if AddPinLeft:
            # tts = "Adding to pinsLNew " + str(i) + "\r\n"
            # print(tts)
            pinsLNew.append(pinsL[i])

    for i in range(npins // 2, npins):
        AddPinRight = True
        for ei in excludepins:
            if (i + 1) == ei:
                AddPinRight = False
        if AddPinRight:
            # tts = "Adding to pinsRNew " + str(i - (npins/2)) + "\r\n"
            # print(tts)
            pinsRNew.append(pinsR[i - (npins // 2)])

    # union all pins
    pinsLT = union_all(pinsLNew)
    pinsRT = union_all(pinsRNew)

    # create other side of the pins (mirror would be better but there
    # is no solid mirror API)
    pinsT = pinsLT.union(pinsRT.rotate((0, 0, 0), (0, 0, 1), 180))

    mvX = (((npins / 2.0) - 1.0) / 2) * e
    mvY = (E - c) / 2
    pinsT = pinsT.translate((mvX, mvY, 0))

    return pinsT
