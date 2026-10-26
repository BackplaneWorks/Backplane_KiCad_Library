import cadquery as cq


def make_chip(params):
    # dimensions for chip capacitors
    L = params["L"]  # package length
    W = params["W"]  # package width
    T = params["T"]  # package height

    pb = params["pb"]  # pin band
    pt = params["pt"]  # pin thickness
    A1 = params["A1"]  # pin width

    P = params["P"]  # pin pitch
    np = params["np"]  # number of pins on x axis

    ef = params["ef"]  # fillet of edges
    concave = params["concave"]  # pin pitch
    # modelName = params['modelName']  # Model Name
    # rotation = params['rotation']   # rotation
    if params["excluded_pins"]:
        excluded_pins = params["excluded_pins"]
    else:
        excluded_pins = ()  ##no pin excluded

    # Create a 3D box based on the dimension variables above and fillet it
    case = cq.Workplane("XY").box(W - 4 * pt, L, T - 4 * pt)
    # case.edges("|X").fillet(ef)
    # body.edges("|Z").fillet(ef)
    # translate the object
    case = case.translate((0, 0, T / 2)).rotate((0, 0, 0), (0, 0, 1), 0)
    top = cq.Workplane("XY").box(W - 2 * pb, L, 2 * pt)
    # top = top.edges("|X").fillet(ef)
    top = top.translate((0, 0, T - pt)).rotate((0, 0, 0), (0, 0, 1), 0)

    if concave:
        pinblock = (
            cq.Workplane("XY")
            .box(pb, A1, T)
            .edges("|Y")
            .fillet(ef)
            .translate((-W / 2 + pb / 2, 0, T / 2))
            .rotate((0, 0, 0), (0, 0, 1), 0)
        )

        bpin = (
            cq.Workplane("XY")
            .box(pb, A1, T)
            .faces(">Z")
            .edges("<X")
            .workplane(centerOption="CenterOfMass")
            .circle(A1 * 0.3)
            .cutThruAll()
            .edges("|Y")
            .fillet(ef)
            .translate((-W / 2 + pb / 2, 0, T / 2))
            .rotate((0, 0, 0), (0, 0, 1), 0)
        )
    else:
        circle_r = (P - A1) / 2
        pinblock = (
            cq.Workplane("XY")
            .circle(circle_r)
            .extrude(T)
            .translate((-W / 2 - circle_r + pb, 0, 0))
            .rotate((0, 0, 0), (0, 0, 1), 0)
        )
        pincutblock = (
            cq.Workplane("XY")
            .box(pb - circle_r, P - A1, T)
            .translate((-W / 2 + (pb - circle_r) / 2, 0, T / 2))
            .rotate((0, 0, 0), (0, 0, 1), 0)
        )
        pinblock = pinblock.union(pincutblock)
        # pinblock = cq.Workplane("XY").faces(">Z").circle((P-A1)/2).cutThruAll().rotate((0,0,0), (0,0,1), 0)

        bpin = (
            cq.Workplane("XY")
            .box(pb, A1, T)
            .faces(">Z")
            .vertices(">Y")
            .vertices(">X")
            .workplane(centerOption="CenterOfMass")
            .rect((pb - pb * 0.4) * 2, A1 * 0.4)
            .cutThruAll()
            .faces(">Z")
            .vertices("<Y")
            .vertices(">X")
            .workplane(centerOption="CenterOfMass")
            .rect((pb - pb * 0.4) * 2, A1 * 0.4)
            .cutThruAll()
            .edges("|Y")
            .fillet(ef)
            .translate((-W / 2 + pb / 2, 0, T / 2))
            .rotate((0, 0, 0), (0, 0, 1), 0)
        )
        endpinwidth = (L - (np - 1) * P + A1) / 2
        endpin = (
            cq.Workplane("XY")
            .box(pb, endpinwidth, T)
            .faces(">Z")
            .vertices(">Y")
            .vertices(">X")
            .workplane(centerOption="CenterOfMass")
            .rect((pb - pb * 0.4) * 2, endpinwidth * 0.4)
            .cutThruAll()
            .faces(">Z")
            .vertices("<Y")
            .vertices(">X")
            .workplane(centerOption="CenterOfMass")
            .rect((pb - pb * 0.4) * 2, endpinwidth * 0.4)
            .cutThruAll()
            .edges("|Y")
            .fillet(ef)
            .translate((-W / 2 + pb / 2, circle_r / 2, T / 2))
            .rotate((0, 0, 0), (0, 0, 1), 0)
        )
    pins = []
    pincounter = 1
    first_pos_x = (np - 1) * P / 2
    endpincounter = 0
    for i in range(np):
        if pincounter not in excluded_pins:
            if concave:
                pin = bpin.translate((0, first_pos_x - i * P, 0)).rotate(
                    (0, 0, 0), (0, 0, 1), 180
                )
                pinsubtract = pinblock.translate((0, first_pos_x - i * P, 0)).rotate(
                    (0, 0, 0), (0, 0, 1), 180
                )
                case = case.cut(pinsubtract)
            else:
                if pincounter in (1, np, np + 1, np * 2):
                    pin = endpin.translate(
                        (0, first_pos_x - i * P - circle_r * endpincounter, 0)
                    ).rotate((0, 0, 0), (0, 0, 1), 180)
                    endpincounter += 1
                else:
                    pin = bpin.translate((0, first_pos_x - i * P, 0)).rotate(
                        (0, 0, 0), (0, 0, 1), 180
                    )
            pins.append(pin)
        pincounter += 1
    endpincounter = 0
    for i in range(np):
        if pincounter not in excluded_pins:
            if concave:
                pin = bpin.translate((0, first_pos_x - i * P, 0))
                pinsubtract = pinblock.translate((0, first_pos_x - i * P, 0))
                case = case.cut(pinsubtract)
            else:
                if pincounter in (1, np, np + 1, np * 2):
                    pin = endpin.translate(
                        (0, first_pos_x - i * P - circle_r * endpincounter, 0)
                    )
                    endpincounter += 1
                else:
                    pin = bpin.translate((0, first_pos_x - i * P, 0))
            pins.append(pin)
        pincounter += 1

    if not concave:
        first_pos_x_hole = (np - 2) * P / 2
        for i in range(np - 1):
            pinsubtract = pinblock.translate((0, first_pos_x_hole - i * P, 0))
            case = case.cut(pinsubtract)
            pinsubtract = pinsubtract.rotate((0, 0, 0), (0, 0, 1), 180)
            case = case.cut(pinsubtract)

    merged_pins = pins[0]
    for p in pins[1:]:
        merged_pins = merged_pins.union(p)
    pins = merged_pins

    # body_copy.ShapeColor=result.ShapeColor
    # show(case)
    # show(top)
    # show(pins)
    # extract case from pins
    case = case.cut(pins)
    # pins = pins.cut(case, True, True)
    return (case, top, pins)
