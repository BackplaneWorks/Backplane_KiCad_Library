# Molex 5569
# Mini-Fit Jr. Header, Dual Row, Right Angle, with Snap-in Plastic Peg PCB Lock

import cadquery as cq


def NextCavity():
    global cavity_index
    cavity_index = cavity_index + 1
    if cavity_index > 3:
        cavity_index = 0
    return cavity_index


def MakeBody(series_params, n):
    by = series_params["dia"] / 2 + (n - 1) * series_params["pitch"] / 2
    bz = -series_params["pitch"] + (
        series_params["body_height"] / 2 + series_params["pitch"] / 2
    )
    body = (
        cq.Workplane("XY")
        .box(
            series_params["body_width"],
            series_params["body_length"][n - 1],
            series_params["body_height"],
        )
        .translate((series_params["bx"], by, bz))
    )

    # Lock
    ls = 3.40
    lock_h = 1.4
    ly = -series_params["dia"] / 2 + series_params["body_height"] / 2 - ls / 2
    ly = by
    lz = series_params["body_height"] - series_params["pitch"] / 2

    body = body.union(
        cq.Workplane("XZ")
        .lineTo(ls, 0)
        .lineTo(ls, lock_h)
        .close()
        .extrude(ls)
        .translate(
            (-series_params["body_width"] - series_params["dia"] / 2, ly + ls / 2, lz)
        )
    )

    # Add peg
    # body = body.union(cq.Workplane("XY").makeCylinder(peg_dia/2, peg_height))
    px = -series_params["peg_to_pin"] + series_params["dia"] / 2
    py = by
    pz = -series_params["body_height"] / 2

    if n > 2:
        py = series_params["dia"] / 2

    peg = (
        cq.Workplane("XY")
        .circle(series_params["peg_dia"] / 2)
        .extrude(series_params["peg_height"])
        .faces("<Z")
        .chamfer(1)
        .translate((px, py, pz))
    )

    # Add second peg if circuit number is greater than 4 (2 pairs)
    if n > 2:
        py = series_params["dia"] / 2 + (n - 1) * series_params["pitch"]
        peg = peg.union(
            cq.Workplane("XY")
            .circle(series_params["peg_dia"] / 2)
            .extrude(series_params["peg_height"])
            .faces("<Z")
            .chamfer(1)
            .translate((px, py, pz))
        )

    body = body.union(peg)

    global cavity_index
    cavity_index = 0
    # Pin cavities
    for i in range(1, n + 1):
        offset = series_params["dia"] / 2 + series_params["pitch"] * (i - 1)
        cavity = cq.Workplane("XY").box(
            series_params["body_width"],
            series_params["cavity_width"],
            series_params["cavity_width"],
        )
        if series_params["cavity_pattern"][cavity_index] < 1:
            cavity = (
                cavity.edges("|X")
                .edges("<Z")
                .chamfer(series_params["cavity_width"] / 4)
            )

        cavity = cavity.translate(
            (
                series_params["bx"] - 1,
                offset,
                series_params["dia"] / 2 + series_params["pitch"],
            )
        )

        body = body.cut(cavity)

        # Bottom row
        cavity = cq.Workplane("XY").box(
            series_params["body_width"],
            series_params["cavity_width"],
            series_params["cavity_width"],
        )
        if series_params["cavity_pattern"][cavity_index] > 0:
            cavity = (
                cavity.edges("|X")
                .edges("<Z")
                .chamfer(series_params["cavity_width"] / 4)
            )

        cavity = cavity.translate(
            (series_params["bx"] - 1, offset, series_params["dia"] / 2)
        )

        body = body.cut(cavity)

        NextCavity()

    # Side rib
    body = body.union(
        cq.Workplane("ZY")
        .circle(0.4)
        .extrude(series_params["body_width"])
        .translate(
            (
                series_params["bx"] + series_params["body_width"] / 2,
                by - (series_params["body_length"][n - 1]) / 2,
                bz - series_params["body_height"] / 2 + 2.5,
            )
        )
    )

    return body


def MakePin(series_params, k):

    h = -series_params["pin_height"] + series_params["pitch"] * k
    l = -series_params["pin_length"] + series_params["step"] * k

    # Begin pin
    pin = (
        cq.Workplane("XY")
        .rect(series_params["dia"], series_params["dia"], False)
        .extrude(h)
        .faces("<Z")
        .chamfer(series_params["ch"])
    )

    # Bending
    pin = pin.union(
        cq.Workplane("ZY")
        .rect(series_params["dia"], series_params["dia"], False)
        .revolve(90)
    )

    # End pin
    pin = pin.union(
        cq.Workplane("YZ")
        .rect(series_params["dia"], series_params["dia"], False)
        .extrude(l)
        .faces("<X")
        .chamfer(series_params["ch"])
    )
    return pin


def MakePinPair(series_params):
    pin = MakePin(series_params, 1)
    # Make a copy of pin for second row
    pair = pin.union(
        MakePin(series_params, 0).translate(
            (series_params["step"], 0, series_params["pitch"])
        )
    )
    return pair


def MakePinPairs(series_params, n):
    result = MakePinPair(series_params)

    for i in range(1, n):
        result = result.union(
            MakePinPair(series_params).translate((0, i * series_params["pitch"], 0))
        )
    return result


def MakePart(series_params):
    n = int(series_params["N"] / 2)
    pins = MakePinPairs(series_params, n)
    body = MakeBody(series_params, n)
    return (body, pins)
