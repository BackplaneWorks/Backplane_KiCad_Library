from math import sqrt

import cadquery as cq


# Make marking (only applies to array at this point)
def make_marking(params, n=1):
    if params["shape"] == "array":
        mr = 0.5  # radius of dot
        mt = 0.01  # thickness of marking
        moff = 2.0  # offset of marking from edge of body
        c = 0.3  # height of body off board
        marking = (
            cq.Workplane("XZ")
            .circle(mr)
            .extrude(mt)
            .translate(
                (moff - params["px"] / 2, -params["w"] / 2, c + params["d"] - moff)
            )
        )
    else:
        marking = None
    return marking

    # make a resistor body based on input parameters


def make_body(params, n=1):

    if params["shape"] == "array":
        # resistor array body: rectangle with rounded corners
        c = 0.3  # height off board
        l = params["px"] * n  # length of body
        body = cq.Workplane("YZ").rect(params["w"], params["d"]).extrude(l)
        body = body.translate((-params["px"] / 2, 0, c + params["d"] / 2))
        body = body.edges().fillet(params["w"] / 3)
    elif params["shape"] == "bare":
        # bare metal element - note that pins below board level are done in the MakePins routine
        c = 1.0  # height off board
        t = 1.0  # element thickness
        r = t * 1.5  # radius of bend
        arco = (1 - sqrt(2) / 2) * r  # helper value sets a mid point in the radius arcs
        h = (
            params["d"] - t / 2 - c
        )  # height of centerline of element - model gets moved up by c later.
        # construct path for element
        path = (
            cq.Workplane("XZ")
            .lineTo(0, h - r)
            .threePointArc((arco, h - arco), (r, h))
            .lineTo(params["px"] - r, h)
            .threePointArc((params["px"] - arco, h - arco), (params["px"], h - r))
            .lineTo(params["px"], 0)
        )
        body = cq.Workplane("XY").rect(t, params["w"]).sweep(path).translate((0, 0, c))
        # make wee circular feet
        body = body.union(cq.Workplane("XY").circle(1.6).extrude(c * 2))
        body = body.union(
            cq.Workplane("XY")
            .circle(1.6)
            .extrude(c * 2)
            .translate((params["px"], 0, 0))
        )
    else:
        if params["orient"] == "v":
            if params["shape"] == "din":
                # vertical cylindrical resistor body
                body = (
                    cq.Workplane("XY")
                    .circle(params["d"] / 2 * 0.9)
                    .extrude(params["l"])
                )
                body = body.union(
                    cq.Workplane("XY").circle(params["d"] / 2).extrude(params["l"] / 4)
                )
                body = body.union(
                    cq.Workplane("XY")
                    .workplane(offset=params["l"] * 3 / 4)
                    .circle(params["d"] / 2)
                    .extrude(params["l"] / 4)
                )
                body = body.edges(">Z or <Z").fillet(params["d"] / 4)
            else:  # (params['shape == 'power'):
                # all vertical types that are not din will make a box!
                body = (
                    cq.Workplane("XY")
                    .rect(params["d"], params["w"])
                    .extrude(params["l"])
                )
            # sits off the board by 1mm
            body = body.translate((0, 0, 1.0))
        else:
            if params["shape"] == "din":
                # horizontal cylindrical resistor
                body = (
                    cq.Workplane("YZ")
                    .circle(params["d"] / 2 * 0.9)
                    .extrude(params["l"])
                )
                body = body.union(
                    cq.Workplane("YZ").circle(params["d"] / 2).extrude(params["l"] / 4)
                )
                body = body.union(
                    cq.Workplane("YZ")
                    .workplane(offset=params["l"] * 3 / 4)
                    .circle(params["d"] / 2)
                    .extrude(params["l"] / 4)
                )
                body = body.edges(">X or <X").fillet(params["d"] / 4)
            else:  # elif (params['shape == 'power') or (params['shape == 'box') or (params['shape == 'radial') or (params['shape == 'shunt'):
                # otherwise it's a box
                body = (
                    cq.Workplane("YZ")
                    .rect(params["w"], params["d"])
                    .extrude(params["l"])
                )
            if (params["shape"] == "radial") and (params["py"] == 0.0):
                # for the vishay series of radial resistors
                # add the cool undercut from the datasheet http://www.vishay.com/docs/30218/cpcx.pdf
                # doesn't apply to the centered-pin vitrohm types (with py>0) - see below
                flat = 1.0  # length of flat part at edges
                cut_h = 3.0  # height of cutout
                # generate a trapezoidal body to cut out of main body
                cutbody = (
                    cq.Workplane("XZ")
                    .workplane(offset=-params["w"] / 2)
                    .center(flat, -params["d"] / 2)
                    .lineTo(cut_h, cut_h)
                    .lineTo(params["l"] - 2 * flat - cut_h, cut_h)
                    .lineTo(params["l"] - 2 * flat, 0)
                    .close()
                    .extrude(params["w"])
                )
                body = body.cut(cutbody)  # cut!
            if (params["shape"] == "radial") and (params["py"] != 0.0):
                # center on pin 1 http://www.vitrohm.com/content/files/vitrohm_series_kvs_-_201702.pdf
                body = body.translate((-params["l"] / 2, 0, params["d"] / 2))
            else:
                # sit on board, and center between pads
                body = body.translate(
                    ((params["px"] - params["l"]) / 2, 0, params["d"] / 2)
                )
    return body


# makes a simple rectangular array pin, including the larger section above board
# c is height above board
# zbelow is negative value, length of pin below board level
def MakeSingleArrayPin(c, zbelow):
    pin = (
        cq.Workplane("XY").rect(0.5, 0.3).extrude(c - zbelow).translate((0, 0, zbelow))
    )
    pin = pin.union(cq.Workplane("XY").rect(1.14, 0.5).extrude(c))
    return pin


# make a bent resistor pin - suitable for din and power resistors, horiz or vert
def make_pins(params, n=1):

    zbelow = -3.0  # negative value, length of pins below board level
    minimumstraight = 1.0  # short straight section of pins next to bends, body

    # bent pin - upside down u shape
    if (
        (params["shape"] == "din")
        or (params["shape"] == "power")
        or (params["shape"] == "shunt")
    ):
        r = params["pd"] * 1.5  # radius of pin bends
        arco = (
            1 - sqrt(2) / 2
        ) * r  # helper factor to create midpoints of profile radii
        if params["orient"] == "v":
            # vertical
            h = params["l"] + 2 * minimumstraight + r
        else:
            # horizontal
            h = params["d"] / 2
        # create the path and pin
        path = (
            cq.Workplane("XZ")
            .lineTo(0, h - r - zbelow)
            .threePointArc((arco, h - arco - zbelow), (r, h - zbelow))
            .lineTo(params["px"] - r, h - zbelow)
            .threePointArc(
                (params["px"] - arco, h - arco - zbelow), (params["px"], h - r - zbelow)
            )
            .lineTo(params["px"], 0)
        )
        pin = (
            cq.Workplane("XY")
            .circle(params["pd"] / 2)
            .sweep(path)
            .translate((0, 0, zbelow))
        )
    # simple pins using px/py - just two cylinders at appropriate locations
    elif (
        (params["shape"] == "box")
        or (params["shape"] == "radial")
        or (params["shape"] == "bare")
    ):
        # extends somewhat above the board to allow for more complex body shapes, e.g. radial
        aboveboardfactor = 0.5
        if params["shape"] == "bare":
            aboveboardfactor = 0  # don't extend up if making a bare resistor
        pin = (
            cq.Workplane("XY")
            .circle(params["pd"] / 2)
            .extrude(params["d"] * aboveboardfactor - zbelow)
            .translate((0, 0, zbelow))
        )
        pin = pin.union(
            pin.translate((params["px"], params["py"], 0))
        )  # add second pin
    elif params["shape"] == "array":
        # resistor array has rectangular pins
        c = 0.8  # height off board - from datasheet
        pin = MakeSingleArrayPin(c, zbelow)
        for i in range(1, n):
            pin = pin.union(
                MakeSingleArrayPin(c, zbelow).translate((i * params["px"], 0, 0))
            )

    # add extra pins for shunt package using py as pitch
    if params["shape"] == "shunt":
        pin = pin.union(
            cq.Workplane("XY")
            .circle(params["pd"] / 2)
            .extrude(zbelow)
            .translate(((params["px"] - params["py"]) / 2, 0, 0))
        )
        pin = pin.union(
            cq.Workplane("XY")
            .circle(params["pd"] / 2)
            .extrude(zbelow)
            .translate(((params["px"] + params["py"]) / 2, 0, 0))
        )

    return pin
