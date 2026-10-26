import cadquery as cq


def make_transformer(params):
    # modelName = params['modelName']
    # serie = params['serie']
    A1 = params["A1"]
    body = params["body"]
    top = params["top"]
    pin = params["pin"]
    npth = params["npth"]
    rotation = params["rotation"]

    # Dummy
    tx = body[0]
    if body[0] < 0:
        tx = tx + 1
    else:
        tx = body[0] - 1
    ty = body[1]
    if body[0] < 0:
        ty = ty + 1
    else:
        ty = body[0] - 1
    case_top = (
        cq.Workplane("XY")
        .workplane(offset=A1 + 1.0, centerOption="CenterOfMass")
        .moveTo(tx, 0 - ty)
        .rect(0.1, 0.1, False)
        .extrude(0.1)
    )

    if top != None:
        case_top = (
            cq.Workplane("XY")
            .workplane(offset=A1 + body[4] - 0.1, centerOption="CenterOfMass")
            .moveTo(top[0], 0 - top[1])
            .rect(top[2], 0 - top[3], False)
            .extrude(top[4] + 0.1)
        )
        case_top = case_top.faces(">Y").edges("<X").fillet(1.0)
        case_top = case_top.faces(">Y").edges(">X").fillet(1.0)
        case_top = case_top.faces("<Y").edges("<X").fillet(1.0)
        case_top = case_top.faces("<Y").edges(">X").fillet(1.0)
        case_top = case_top.faces(">Z").edges(">X").fillet(1.0)
        #
        if rotation != 0:
            case_top = case_top.rotate((0, 0, 0), (0, 0, 1), rotation)

    case = (
        cq.Workplane("XY")
        .workplane(offset=A1, centerOption="CenterOfMass")
        .moveTo(body[0], 0 - body[1])
        .rect(body[2], 0 - body[3], False)
        .extrude(body[4])
    )
    case = case.faces(">Y").edges("<X").fillet(1.0)
    case = case.faces(">Y").edges(">X").fillet(1.0)
    case = case.faces("<Y").edges("<X").fillet(1.0)
    case = case.faces("<Y").edges(">X").fillet(1.0)
    case = case.faces(">Z").edges(">X").fillet(1.0)
    #
    if rotation != 0:
        case = case.rotate((0, 0, 0), (0, 0, 1), rotation)

    p = pin[0]
    pins = (
        cq.Workplane("XY")
        .workplane(offset=A1 + 1.0, centerOption="CenterOfMass")
        .moveTo(p[0], -p[1])
        .circle(p[2] / 2.6, False)
        .extrude(0 - (p[3] + A1 + 1.0))
    )
    pins = pins.faces("<Z").fillet(p[2] / 5.0)
    for i in range(1, len(pin)):
        p = pin[i]
        pint = (
            cq.Workplane("XY")
            .workplane(offset=A1 + 1.0, centerOption="CenterOfMass")
            .moveTo(p[0], -p[1])
            .circle(p[2] / 2.6, False)
            .extrude(0 - (p[3] + A1 + 1.0))
        )
        pint = pint.faces("<Z").fillet(p[2] / 5.0)
        pins = pins.union(pint)

    if rotation != 0:
        pins = pins.rotate((0, 0, 0), (0, 0, 1), rotation)

    return (case_top, case, pins)
