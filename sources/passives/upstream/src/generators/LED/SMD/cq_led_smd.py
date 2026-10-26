from math import sqrt

import cadquery as cq


def make_chip(all_params):
    # dimensions for LED's
    package_found = True

    package_type = all_params["package_type"]
    length = all_params["length"]  # package length
    width = all_params["width"]  # package width
    height = all_params["height"]  # package height
    pin_band = all_params["pin_band"]  # pin band
    pin_thickness = all_params["pin_thickness"]  # pin thickness
    if pin_thickness == "auto":
        pin_thickness = pin_band / 10.0
    base_height = all_params["base_height"]  # pin thickness
    edge_fillet = all_params["edge_fillet"]  # fillet of edges
    place_pinmark = all_params["pinmark"]
    pinmark = 0
    if edge_fillet == "auto":
        edge_fillet = pin_thickness

    if package_type == "chip_lga":
        pin_distance_edge = all_params["pin_distance_edge"]
        if pin_thickness == "auto":
            pin_thickness = 0.01
        # creating base
        base = (
            cq.Workplane("XY")
            .workplane(offset=pin_thickness, centerOption="CenterOfMass")
            .box(length, width, base_height, centered=(True, True, False))
        )
        # creating top
        top = (
            cq.Workplane("XZ")
            .workplane(offset=-width / 2.0, centerOption="CenterOfMass")
            .moveTo(-(length / 2.0), base_height + pin_thickness)
            .lineTo((-(length / 2)) * 0.9, height)
            .lineTo((length / 2.0) * 0.9, height)
            .lineTo(length / 2.0, base_height + pin_thickness)
            .close()
            .extrude(width)
        )
        # creating pins
        pin_center = length / 2.0 - pin_distance_edge - pin_band / 2.0
        pins = (
            cq.Workplane("XY")
            .moveTo(-pin_center, 0)
            .box(
                pin_band,
                width - 2 * pin_distance_edge,
                pin_thickness,
                centered=(True, True, False),
            )
            .moveTo(pin_center, 0)
            .box(
                pin_band,
                width - 2 * pin_distance_edge,
                pin_thickness,
                centered=(True, True, False),
            )
        )
        if place_pinmark == True:
            pinmark_side = (length - pin_distance_edge * 2.0 - pin_band * 2.0) * 0.8
            pinmark_length = sqrt(
                pinmark_side * pinmark_side - pinmark_side / 2 * pinmark_side / 2
            )
            pinmark = (
                cq.Workplane("XY")
                .workplane(offset=pin_thickness / 2, centerOption="CenterOfMass")
                .moveTo(-pinmark_length / 2, 0)
                .lineTo(pinmark_length / 2, pinmark_side / 2)
                .lineTo(pinmark_length / 2, -pinmark_side / 2)
                .close()
                .extrude(pin_thickness / 2)
            )
    elif package_type == "chip_convex":
        # creating base
        base = (
            cq.Workplane("XY")
            .workplane(offset=pin_thickness, centerOption="CenterOfMass")
            .box(
                length - 2 * pin_thickness,
                width,
                base_height - 2 * pin_thickness,
                centered=(True, True, False),
            )
        )
        # creating top
        top = (
            cq.Workplane("XZ")
            .workplane(offset=-width / 2, centerOption="CenterOfMass")
            .moveTo(-(length / 2 - pin_band), base_height - pin_thickness)
            .lineTo((-(length / 2 - pin_band)) * 0.9, height)
            .lineTo((length / 2 - pin_band) * 0.9, height)
            .lineTo(length / 2 - pin_band, base_height - pin_thickness)
            .close()
            .extrude(width)
        )
        # creating pins
        pins = (
            cq.Workplane("XY")
            .moveTo((length - pin_band) / 2.0, 0)
            .box(pin_band, width, base_height, centered=(True, True, False))
            .moveTo(-(length - pin_band) / 2.0, 0)
            .box(pin_band, width, base_height, centered=(True, True, False))
            .edges("|Y")
            .fillet(edge_fillet)
        )
        pins = (
            pins.workplane(offset=base_height, centerOption="CenterOfMass")
            .moveTo(0, width / 2)
            .rect(length - pin_band / 2, width / 4, centered=True)
            .cutThruAll()
            .moveTo(0, -width / 2)
            .rect(length - pin_band / 2, width / 4, centered=True)
            .cutThruAll()
        )
        pins = pins.cut(base)
        # creating pinmark
        if place_pinmark == True:
            pinmark_side = width * 0.8
            pinmark_length = sqrt(
                pinmark_side * pinmark_side - pinmark_side / 2 * pinmark_side / 2
            )
            pinmark = (
                cq.Workplane("XY")
                .workplane(offset=pin_thickness / 2, centerOption="CenterOfMass")
                .moveTo(-pinmark_length / 2, 0)
                .lineTo(pinmark_length / 2, pinmark_side / 2)
                .lineTo(pinmark_length / 2, -pinmark_side / 2)
                .close()
                .extrude(pin_thickness / 2)
            )

    elif package_type == "chip_concave":
        base = (
            cq.Workplane("XY")
            .workplane(offset=pin_thickness, centerOption="CenterOfMass")
            .box(
                length - 2 * pin_thickness,
                width,
                base_height - 2 * pin_thickness,
                centered=(True, True, False),
            )
        )
        base = (
            base.workplane(offset=base_height, centerOption="CenterOfMass")
            .moveTo(-length / 2, -width / 4 - 0.1)
            .threePointArc(
                (-length / 2 + pin_band / 2 + 0.1, 0),
                (-length / 2, width / 4 + 0.1),
                forConstruction=False,
            )
            .close()
            .moveTo(length / 2, -width / 4 - 0.1)
            .threePointArc(
                (length / 2 - pin_band / 2 - 0.1, 0),
                (length / 2, width / 4 + 0.1),
                forConstruction=False,
            )
            .close()
            .cutThruAll()
        )
        # creating top
        top = (
            cq.Workplane("XZ")
            .workplane(offset=-width / 2, centerOption="CenterOfMass")
            .moveTo(-(length / 2 - pin_band), base_height - pin_thickness)
            .lineTo((-(length / 2 - pin_band)) * 0.9, height)
            .lineTo((length / 2 - pin_band) * 0.9, height)
            .lineTo(length / 2 - pin_band, base_height - pin_thickness)
            .close()
            .extrude(width)
        )
        # creating pins
        pins = (
            cq.Workplane("XY")
            .moveTo((length - pin_band) / 2.0, 0)
            .box(pin_band, width, base_height, centered=(True, True, False))
            .moveTo(-(length - pin_band) / 2.0, 0)
            .box(pin_band, width, base_height, centered=(True, True, False))
            .edges("|Y")
            .fillet(edge_fillet)
        )
        pins = (
            pins.workplane(offset=base_height, centerOption="CenterOfMass")
            .moveTo(-length / 2, -width / 4)
            .threePointArc(
                (-length / 2 + pin_band / 2, 0),
                (-length / 2, width / 4),
                forConstruction=False,
            )
            .close()
            .moveTo(length / 2, -width / 4)
            .threePointArc(
                (length / 2 - pin_band / 2, 0),
                (length / 2, width / 4),
                forConstruction=False,
            )
            .close()
            .cutThruAll()
        )
        pins = pins.cut(base)
        # creating pinmark
        if place_pinmark == True:
            pinmark_side = width * 0.8
            pinmark_length = sqrt(
                pinmark_side * pinmark_side - pinmark_side / 2 * pinmark_side / 2
            )
            pinmark = (
                cq.Workplane("XY")
                .workplane(offset=pin_thickness / 2, centerOption="CenterOfMass")
                .moveTo(-pinmark_length / 2, 0)
                .lineTo(pinmark_length / 2, pinmark_side / 2)
                .lineTo(pinmark_length / 2, -pinmark_side / 2)
                .close()
                .extrude(pin_thickness / 2)
            )

    elif package_type == "chip_concave_4":

        top_length = all_params["top_length"]
        top_width = all_params["top_width"]
        top_height = all_params["top_height"]

        pincnt = all_params["pincnt"]

        # creating base
        base = (
            cq.Workplane("XY")
            .workplane(offset=pin_thickness, centerOption="CenterOfMass")
            .moveTo(0.0, 0.0)
            .rect(length, width, True)
            .extrude(height)
        )

        # creating top
        top = (
            cq.Workplane("XY")
            .workplane(
                offset=pin_thickness + (height - 0.0001), centerOption="CenterOfMass"
            )
            .moveTo(0.0, 0.0)
            .rect(top_length, top_width, True)
            .extrude(top_height)
        )
        top = top.faces("<X").edges(">Z").chamfer(top_height - 0.002, top_height / 4.0)
        top = top.faces(">X").edges(">Z").chamfer(top_height / 4.0, top_height - 0.002)
        top = top.faces(">Z").edges(">X").fillet(top_height / 10.0)
        top = top.faces(">Z").edges("<X").fillet(top_height / 10.0)

        # creating pins
        pins = None
        for i in range(0, len(pincnt)):
            p = pincnt[i]
            px = p[0]
            py = p[1]
            pw = p[2]
            pl = p[3]
            ph = p[4]

            p2 = (
                cq.Workplane("XY")
                .workplane(offset=0.0, centerOption="CenterOfMass")
                .moveTo(px, py)
                .rect(pl, pw, True)
                .extrude(ph)
            )

            pcx = 0.0
            if px > 0:
                pcx = px + (pl / 2.0)
            else:
                pcx = px - (pl / 2.0)

            pc0 = (
                cq.Workplane("XY")
                .workplane(offset=0.0, centerOption="CenterOfMass")
                .moveTo(pcx, py)
                .circle(pw / 4.0, False)
                .extrude(2 * base_height)
            )
            p2 = p2.cut(pc0)
            base = base.cut(pc0)

            if i == 0:
                pins = p2
            else:
                pins = pins.union(p2)

        # creating pinmark
        if place_pinmark == True:
            pinmark_side = width * 0.4
            pinmark_length = sqrt(
                pinmark_side * pinmark_side - pinmark_side / 2 * pinmark_side / 2
            )
            pinmark = (
                cq.Workplane("XY")
                .workplane(offset=pin_thickness / 2, centerOption="CenterOfMass")
                .moveTo(-pinmark_length / 2, 0)
                .lineTo(pinmark_length / 2, pinmark_side / 2)
                .lineTo(pinmark_length / 2, -pinmark_side / 2)
                .close()
                .extrude(pin_thickness / 2)
            )
        else:
            pinmark = (
                cq.Workplane("XY")
                .workplane(offset=pin_thickness + 0.05, centerOption="CenterOfMass")
                .moveTo(0.0, 0.0)
                .rect(0.05, 0.05, True)
                .extrude(0.05)
            )

    elif package_type == "plcc_a":
        pincnt = all_params["pincnt"]
        #
        # Make the main block
        base = (
            cq.Workplane("XY")
            .workplane(offset=base_height, centerOption="CenterOfMass")
            .moveTo(0.0, 0.0)
            .rect(length, width, True)
            .extrude(height)
        )
        #
        # Cut out the edge of the corner
        p2 = (
            cq.Workplane("XY")
            .workplane(offset=base_height + (height * 0.8), centerOption="CenterOfMass")
            .moveTo(0.0, 0.0)
            .rect(length, width, True)
            .extrude(height)
        )
        p2 = p2.rotate((0, 0, 0), (0, 0, 1), 45.0)
        p2 = p2.translate((0.0 - (length * 0.75), (width * 0.75), 0.0))
        base = base.cut(p2)
        #
        # Make rounded top
        base = base.faces(">Z").fillet(height / 20.0)
        #
        # Cut out the circular hole ontop
        tp = (
            cq.Workplane("XY")
            .workplane(offset=base_height + (height / 2.0), centerOption="CenterOfMass")
            .moveTo(0.0, 0.0)
            .circle(width / 3.0, False)
            .extrude(2 * height)
        )
        base = base.cut(tp)
        base = base.faces(">Z[3]").chamfer(height / 5.0)
        #
        # Create the glass top
        top = (
            cq.Workplane("XY")
            .workplane(offset=base_height + (height / 2.0), centerOption="CenterOfMass")
            .moveTo(0.0, 0.0)
            .circle(width / 3.0, False)
            .extrude(height / 4.0)
        )

        pins = None
        for i in range(0, len(pincnt)):
            p = pincnt[i]
            px = p[0]
            py = p[1]
            pw = p[2]
            pl = p[3]
            ph = p[4]

            p2 = (
                cq.Workplane("XY")
                .workplane(offset=0.0, centerOption="CenterOfMass")
                .moveTo(px, py)
                .rect(pl, pw, True)
                .extrude(ph)
            )
            p3 = (
                cq.Workplane("XY")
                .workplane(offset=pin_thickness, centerOption="CenterOfMass")
                .moveTo(px, py)
                .rect(pl - (2.0 * pin_thickness), pw + (2.0 * pin_thickness), True)
                .extrude(ph - (2.0 * pin_thickness))
            )
            p3 = p3.faces("<X").fillet(pin_thickness / 2.0)
            p3 = p3.faces(">X").fillet(pin_thickness / 2.0)
            p2 = p2.cut(p3)
            if px < 0:
                p2 = p2.faces("<X").edges(">Z").fillet(pin_thickness / 2.0)
                p2 = p2.faces("<X").edges("<Z").fillet(pin_thickness / 2.0)
            else:
                p2 = p2.faces(">X").edges(">Z").fillet(pin_thickness / 2.0)
                p2 = p2.faces(">X").edges("<Z").fillet(pin_thickness / 2.0)

            if i == 0:
                pins = p2
            else:
                pins = pins.union(p2)

        pinmark = (
            cq.Workplane("XY")
            .workplane(
                offset=pin_thickness + (height / 2.0), centerOption="CenterOfMass"
            )
            .moveTo(0.0, 0.0)
            .circle(width / 3.0, False)
            .extrude(height / 8.0)
        )

    else:
        package_found = False
        base = 0
        top = 0
        pins = 0
        pinmark = 0

    return (base, top, pins, pinmark, package_found)
