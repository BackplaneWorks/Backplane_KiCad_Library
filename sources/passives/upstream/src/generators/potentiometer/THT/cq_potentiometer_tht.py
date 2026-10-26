import cadquery as cq


def make_chip(series_params):
    # dimensions for LED's
    package_found = True

    package_type = series_params["package_type"]
    length = series_params["length"]  # package length
    width = series_params["width"]  # package width
    height = series_params["height"]  # package height
    pin1corner = series_params["pin1corner"]
    pincnt = series_params["pincnt"]
    base_height = series_params["base_height"]
    screw = series_params["screw"]
    rotation = series_params["rotation"]
    pinmark = series_params["pinmark"]
    source = series_params["source"]

    top = None
    base = None
    pins = None
    pinmark = None

    if package_type == "Bourns_3005":
        #
        p0 = pincnt[0]
        p1 = pincnt[1]
        p2 = pincnt[2]

        # Create base
        base = (
            cq.Workplane("XY")
            .workplane(offset=0.0, centerOption="CenterOfMass")
            .moveTo(0.0, 0.0)
            .rect(length, width, True)
            .extrude(height)
        )
        base0 = (
            cq.Workplane("XY")
            .workplane(offset=0.0, centerOption="CenterOfMass")
            .moveTo(0.0, 0.0)
            .rect(length - (2 * 0.76), width + 0.2, True)
            .extrude(0.89)
        )
        base = base.cut(base0)
        base = base.faces(">X").edges(">Y").fillet(height / 60.0)
        base = base.faces(">X").edges("<Y").fillet(height / 60.0)
        base = base.faces("<X").edges(">Y").fillet(height / 60.0)
        base = base.faces("<X").edges("<Y").fillet(height / 60.0)
        base = base.faces(">Z").fillet(height / 60.0)
        base = base.translate(
            (0.0 - ((length / 2.0) - pin1corner[0]), (p1[2] / 2.0), 0.0)
        )

        # Create top (screw)
        st = screw[0]
        sl = screw[1]
        sd = screw[2]
        sc = screw[3]
        sh = screw[4]

        if st == "lefttop":
            sx = length / 2.0
            top = (
                cq.Workplane("ZY")
                .workplane(offset=(length / 2.0) - 0.1, centerOption="CenterOfMass")
                .moveTo(sh, 0.0)
                .circle(sd / 2.0, False)
                .extrude(sl + 0.1)
            )
            top = top.faces("<X").fillet(sl / 5.0)
            top0 = (
                cq.Workplane("ZY")
                .workplane(
                    offset=((length / 2.0)) + sl + 0.1, centerOption="CenterOfMass"
                )
                .moveTo(sh, 0.0)
                .rect(sd + 1.0, sd / 5.0, True)
                .extrude(0.0 - (sc + 0.1))
            )
            top = top.cut(top0)
            top = top.translate(
                (0.0 - ((length / 2.0) - pin1corner[0]), (p1[2] / 2.0), 0.0)
            )

    if (
        package_type == "Bourns_3299P"
        or package_type == "Bourns_3299W"
        or package_type == "Bourns_3299X"
        or package_type == "Bourns_3299Y"
        or package_type == "Bourns_3299Z"
    ):
        #
        p0 = pincnt[0]
        p1 = pincnt[1]
        p2 = pincnt[2]

        # Create base
        base = (
            cq.Workplane("XY")
            .workplane(offset=0.0, centerOption="CenterOfMass")
            .moveTo(0.0, 0.0)
            .rect(length, width, True)
            .extrude(height)
        )
        base0 = (
            cq.Workplane("XY")
            .workplane(offset=0.0, centerOption="CenterOfMass")
            .moveTo(0.0, 0.0)
            .rect(length - (2 * 0.38), width + 0.2, True)
            .extrude(0.38)
        )
        base = base.cut(base0)
        base0 = (
            cq.Workplane("XY")
            .workplane(offset=0.0, centerOption="CenterOfMass")
            .moveTo(0.0, 0.0)
            .rect(length + 0.2, width - (2 * 0.38), True)
            .extrude(0.38)
        )
        base = base.cut(base0)
        base0 = (
            cq.Workplane("XY")
            .workplane(offset=0.0, centerOption="CenterOfMass")
            .moveTo((length / 2.0) - (0.38 / 2.0), 0.0)
            .rect(0.38, width - (2 * 0.38), True)
            .extrude(height)
        )
        base = base.cut(base0)

        base = base.faces(">X").edges(">Y").fillet(height / 60.0)
        base = base.faces(">X").edges("<Y").fillet(height / 60.0)
        base = base.faces("<X").edges(">Y").fillet(height / 60.0)
        base = base.faces("<X").edges("<Y").fillet(height / 60.0)
        base = base.faces(">Z").fillet(height / 60.0)

        if package_type == "Bourns_3299P":
            base = base.translate(
                (
                    ((length / 2.0) - pin1corner[0]),
                    0.0 - ((width / 2.0) - (pin1corner[1])),
                    0.0,
                )
            )

        if (
            package_type == "Bourns_3299W"
            or package_type == "Bourns_3299X"
            or package_type == "Bourns_3299Y"
            or package_type == "Bourns_3299Z"
        ):
            base = base.rotate((0, 0, 0), (1, 0, 0), 90.0)
            base = base.rotate((0, 0, 0), (0, 1, 0), 90.0)
            base = base.translate((0.0, height / 2.0, length / 2.0))
            base = base.translate(
                (
                    0.0 - ((width / 2.0) - pin1corner[0]),
                    0.0 - ((height / 2.0) - (pin1corner[1])),
                    0.0,
                )
            )

        # Create top (screw)
        st = screw[0]
        sl = screw[1]
        sd = screw[2]
        sc = screw[3]
        sz = screw[4]
        sy = screw[5]

        if st == "lefttop":
            sx = length / 2.0
            top = (
                cq.Workplane("ZY")
                .workplane(offset=0.0 - 0.1, centerOption="CenterOfMass")
                .moveTo(0.0, 0.0)
                .circle(sd / 2.0, False)
                .extrude(sl + 0.1)
            )
            top = top.faces("<X").fillet(sl / 5.0)
            top0 = (
                cq.Workplane("ZY")
                .workplane(offset=sl + 0.1, centerOption="CenterOfMass")
                .moveTo(0.0, 0.0)
                .rect(sd + 1.0, sd / 5.0, True)
                .extrude(0.0 - (sc + 0.1))
            )
            top = top.cut(top0)

            if package_type == "Bourns_3299P":
                top = top.translate((0.0 - (length / 2.0), sy, sz))
                top = top.translate(
                    (
                        ((length / 2.0) - pin1corner[0]),
                        0.0 - ((width / 2.0) - (pin1corner[1])),
                        0.0,
                    )
                )

            if package_type == "Bourns_3299W" or package_type == "Bourns_3299Y":
                top = top.rotate((0, 0, 0), (1, 0, 0), 90.0)
                top = top.rotate((0, 0, 0), (0, 1, 0), 90.0)
                top = top.translate((0.0, 0.0, length))
                top = top.translate(((pin1corner[0] - sy), pin1corner[1] - sz, 0.0))

            if package_type == "Bourns_3299X" or package_type == "Bourns_3299Z":
                top = top.rotate((0, 0, 0), (1, 0, 0), 90.0)
                top = top.translate((0.0 - width, 0.0, 0.0))
                top = top.translate(((pin1corner[0]), pin1corner[1] - sz, length - sy))

    # creating pins
    for i in range(0, len(pincnt)):
        p = pincnt[i]
        pt = p[0]
        px = p[1]
        py = p[2]

        if pt == "tht":
            pl = p[3]
            pw = p[4]
            ph = p[5]
            p2 = (
                cq.Workplane("XY")
                .workplane(offset=1.0, centerOption="CenterOfMass")
                .moveTo(px, py)
                .rect(pl, pw, True)
                .extrude((0.0 - ph) - 1.0)
            )
            if pl > pw:
                p2 = p2.faces("<Z").edges("<X").fillet(pl / 2.5)
                p2 = p2.faces("<Z").edges(">X").fillet(pl / 2.5)
            else:
                p2 = p2.faces("<Z").edges("<Y").fillet(pw / 2.5)
                p2 = p2.faces("<Z").edges(">Y").fillet(pw / 2.5)

            p3 = None
            if py > 0.002:
                p3 = (
                    cq.Workplane("XY")
                    .workplane(offset=1.0, centerOption="CenterOfMass")
                    .moveTo(px - (pl / 2.0), py + (pw / 2.0))
                    .rect(pl, 0.0 - (width / 2.0), False)
                    .extrude(pw)
                )
                p2 = p2.union(p3)
                p2 = p2.faces(">Z").edges(">Y").fillet(pw / 1.5)
            else:
                p3 = (
                    cq.Workplane("XY")
                    .workplane(offset=1.0, centerOption="CenterOfMass")
                    .moveTo(px - (pl / 2.0), py - (pw / 2.0))
                    .rect(pl, width / 2.0, False)
                    .extrude(pw)
                )
                p2 = p2.union(p3)
                p2 = p2.faces(">Z").edges("<Y").fillet(pw / 1.5)

        if pt == "round":
            pd = p[3]
            ph = p[4]
            p2 = (
                cq.Workplane("XY")
                .workplane(offset=1.0, centerOption="CenterOfMass")
                .moveTo(px, py)
                .circle(pd / 2.0, False)
                .extrude((0.0 - ph) - 1.0)
            )
            p2 = p2.faces("<Z").fillet(pd / 5.0)

        if i == 0:
            pins = p2
        else:
            pins = pins.union(p2)

    # Pin marker, dummy
    pinmark = (
        cq.Workplane("XY")
        .workplane(offset=height / 2.0, centerOption="CenterOfMass")
        .moveTo(0.0, 0.0)
        .rect(0.1, 0.1, True)
        .extrude(0.1)
    )
    pinmark = pinmark.translate(
        (0.0 - ((length / 2.0) - pin1corner[0]), (p1[2] / 2.0), 0.0)
    )

    base = base.translate((0.0, 0.0, base_height))
    top = top.translate((0.0, 0.0, base_height))
    pins = pins.translate((0.0, 0.0, base_height))
    pinmark = pinmark.translate((0.0, 0.0, base_height))

    if base == None:
        package_found = False
        base = 0
        top = 0
        pins = 0
        pinmark = 0

    return (base, top, pins, pinmark, package_found)
