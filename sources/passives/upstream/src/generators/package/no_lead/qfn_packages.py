import cadquery as cq

from .spec import NoLeadSpec

def make_qfn(
    nlc: NoLeadSpec,
) -> tuple[cq.Workplane, cq.Workplane, cq.Workplane | None, cq.Workplane | None]:

    marker = nlc.marker

    # Body size parameters
    e = nlc.body_size_x.nominal
    d = nlc.body_size_y.nominal
    a1 = nlc.body_pcb_gap.minimum
    a2 = nlc.body_height.maximum
    body_fillet = nlc.body_fillet

    # Lead parameters
    pitch_x = nlc.pitch_x.nominal
    pitch_y = nlc.pitch_y.nominal
    lead_height = nlc.lead_height.nominal
    lead_width_h = nlc.lead_width_h.nominal
    lead_width_v = nlc.lead_width_v.nominal
    lead_len_h = nlc.lead_len_h.nominal
    lead_len_v = nlc.lead_len_v.nominal
    lead_to_edge = nlc.lead_to_edge.nominal
    lead_shape = nlc.lead_shape
    lead_shape_custom = nlc.lead_shape_custom
    npx = nlc.num_pins_x
    npy = nlc.num_pins_y
    ep_chamfer = nlc.ep_chamfer.nominal

    # Excluded pins:
    excluded_pins = nlc.deleted_pins + nlc.hidden_pins

    # Total height:
    a = a1 + a2

    # Construct the case:
    case = cq.Workplane("XY").box(e, d, a2).translate((0, 0, a2 / 2 + a1))
    if body_fillet != 0.0:
        case.edges("|X").fillet(body_fillet)
        case.edges("|Z").fillet(body_fillet)

    # First pin marker:
    marker_diameter = max(d, e) / 10.0
    if min(d, e) < 5 * marker_diameter:
        marker_edge_clearance = marker_diameter / 4.0
    else:
        marker_edge_clearance = marker_diameter / 2.0
    marker_depth = 0.050
    marker_dx = nlc.marker_dx
    marker_dy = nlc.marker_dy
    if marker_dx is None:
        marker_dx = marker_edge_clearance
    if marker_dy is None:
        marker_dy = marker_edge_clearance
    if lead_shape in ("concave", "cshaped"):
        if npy != 0:
            marker_dx = marker_dx + lead_len_h - a1 / 2
        if npx != 0:
            marker_dy = marker_dy + lead_len_v - a1 / 2
    if marker == "bar":
        pinmark = cq.Workplane(
            "XY", (-e / 2 + marker_diameter / 2 + marker_dx, 0, a - marker_depth / 2)
        ).box(marker_diameter, d - 2 * marker_dy, marker_depth)
        case = case.cut(pinmark)
    elif marker == "circle":
        circle_center_x = -e / 2 + marker_diameter / 2 + marker_dx
        circle_center_y = d / 2 - marker_diameter / 2 - marker_dy
        pinmark = (
            cq.Workplane("XY", (circle_center_x, circle_center_y, a))
            .circle(marker_diameter / 2)
            .extrude(-marker_depth)
        )
        case = case.cut(pinmark)
    else:
        pinmark = None

    # Create a base pin for the x- and y-axis each (this pin is later copied):
    bpin_shape: dict[str, cq.Workplane] = {}
    bpin_cut: dict[str, cq.Workplane] = {}
    for axis, length, width in zip(
        ["x", "y"], [lead_len_h, lead_len_v], [lead_width_h, lead_width_v]
    ):
        # Create pins centered on the x- and y-plane:
        if lead_shape == "square":
            bpin_shape[axis] = cq.Workplane().box(
                width, length, lead_height, centered=(True, True, False)
            )
        elif lead_shape == "rounded":
            radius = width / 2
            bpin = (
                cq.Workplane("XY")
                .moveTo(-radius, -length / 2 + radius)
                .threePointArc(
                    (0, -length / 2),
                    (radius, -length / 2 + radius),
                )
                .lineTo(radius, length / 2)
                .lineTo(-radius, length / 2)
                .close()
                .extrude(lead_height)
            )
            bpin_shape[axis] = bpin
        elif lead_shape == "concave":
            pincut = cq.Workplane().box(
                width, length, a2 + a1 * 2, centered=(True, True, False)
            )
            bpin = (
                cq.Workplane("XY")
                .box(width, length, a2 + a1 * 2, centered=(True, True, False))
                .edges("|X")
                .fillet(a1)
                .faces(">Z")
                .edges(">Y")
                .workplane(centerOption="CenterOfMass")
                .circle(width * 0.3)
                .cutThruAll()
            )
            bpin_shape[axis] = bpin
            bpin_cut[axis] = pincut
        elif lead_shape == "cshaped":
            bpin = (
                cq.Workplane()
                .box(width, length, a2 + a1 * 2, centered=(True, True, False))
                .edges("|X")
                .fillet(a1)
            )
            bpin_shape[axis] = bpin

    # For custom shaped pins, construct and unite them all:
    if lead_shape == "custom":
        merged_pins = cq.Workplane()
        for pin_shape in lead_shape_custom:
            first_point = pin_shape[0]
            pin = cq.Workplane("XY").moveTo(first_point[0], first_point[1])
            for i in range(1, len(pin_shape)):
                point = pin_shape[i]
                pin = pin.lineTo(point[0], point[1])
            pin = pin.close().extrude(lead_height)
            merged_pins = merged_pins.union(pin)
    else:
        # For all other pin shapes first calculate the location and rotation of the
        # pins (later they are created in an efficient way based on that information):
        valid_locs_h: list[cq.Location] = []
        valid_locs_v: list[cq.Location] = []
        pincounter = 1

        # Left row:
        first_pos_y = (npy - 1) * pitch_y / 2
        x = -e / 2 + lead_to_edge + lead_len_v / 2
        for i in range(npy):
            if pincounter not in excluded_pins:
                y = first_pos_y - i * pitch_y
                translation = cq.Vector(x, y, 0)
                valid_locs_v.append(cq.Location(translation, cq.Vector(0, 0, 1), 90))
            pincounter += 1

        # Bottom row:
        y = -d / 2 + lead_to_edge + lead_len_h / 2
        first_pos_x = -(npx - 1) * pitch_x / 2
        for i in range(npx):
            if pincounter not in excluded_pins:
                x = first_pos_x + i * pitch_x
                translation = cq.Vector(x, y, 0)
                valid_locs_h.append(cq.Location(translation, cq.Vector(0, 0, 1), 180))
            pincounter += 1

        # Right row:
        x = e / 2 - lead_to_edge - lead_len_v / 2
        for i in range(npy):
            if pincounter not in excluded_pins:
                y = -first_pos_y + i * pitch_y
                translation = cq.Vector(x, y, 0)
                valid_locs_v.append(cq.Location(translation, cq.Vector(0, 0, 1), 270))
            pincounter += 1

        # Top row:
        y = d / 2 - lead_to_edge - lead_len_h / 2
        for i in range(npx):
            if pincounter not in excluded_pins:
                x = -first_pos_x - i * pitch_x
                translation = cq.Vector(x, y, 0)
                valid_locs_h.append(cq.Location(translation))
            pincounter += 1

        # Create all pins:
        merged_pins = cq.Workplane()
        merged_cuts = cq.Workplane()
        # Create all horizontal pins in a single, efficient operation
        if npx:
            merged_pins = (
                cq.Workplane("XY")
                .pushPoints(valid_locs_h)
                .each(lambda loc: bpin_shape["x"].val().located(loc), combine="a")  # type: ignore
            )
            if lead_shape == "concave":
                merged_cuts = (
                    cq.Workplane("XY")
                    .pushPoints(valid_locs_h)
                    .each(lambda loc: bpin_cut["x"].val().located(loc), combine="a")  # type: ignore
                )

        # Create all vertical pins in a single, efficient operation
        if npy:
            merged_pins_v = (
                cq.Workplane("XY")
                .pushPoints(valid_locs_v)
                .each(lambda loc: bpin_shape["y"].val().located(loc), combine="a")  # type: ignore
            )
            merged_pins = merged_pins.union(merged_pins_v)
            if lead_shape == "concave":
                merged_cuts_v = (
                    cq.Workplane("XY")
                    .pushPoints(valid_locs_v)
                    .each(lambda loc: bpin_cut["y"].val().located(loc), combine="a")  # type: ignore
                )
                merged_cuts = merged_cuts.union(merged_cuts_v)

        # Cut the pins out of the case:
        if lead_shape == "concave":
            case = case.cut(merged_cuts)

    # Cut the pins out of the case:
    if lead_shape != "concave":
        case = case.cut(merged_pins)

    # Create exposed thermal pad if required
    if nlc.has_ep:
        epads: list[cq.Workplane] = []
        ep_size_x = nlc.ep_size_x.nominal
        ep_size_y = nlc.ep_size_y.nominal
        ep_chamfer = nlc.ep_chamfer.nominal
        epad_offset_x = nlc.ep_offset_x.nominal
        epad_offset_y = nlc.ep_offset_y.nominal
        for nx in range(1, nlc.ep_num[0] + 1):
            for ny in range(1, nlc.ep_num[1] + 1):
                offset_x = (
                    -((nlc.ep_num[0] - 1) * nlc.ep_pitch[0]) / 2
                    + (nx - 1) * nlc.ep_pitch[0]
                )
                offset_y = (
                    -((nlc.ep_num[1] - 1) * nlc.ep_pitch[1]) / 2
                    + (ny - 1) * nlc.ep_pitch[1]
                )
                epad: cq.Workplane = (
                    cq.Workplane("XY")
                    .moveTo(-ep_size_x / 2 + ep_chamfer, -ep_size_y / 2)
                    .lineTo(ep_size_x / 2, -ep_size_y / 2)
                    .lineTo(ep_size_x / 2, ep_size_y / 2)
                    .lineTo(-ep_size_x / 2, ep_size_y / 2)
                    .lineTo(-ep_size_x / 2, -ep_size_y / 2 + ep_chamfer)
                    .close()
                    .extrude(lead_height)
                    .translate((epad_offset_x + offset_x, epad_offset_y + offset_y, 0))
                    .rotate((0, 0, 0), (0, 0, 1), nlc.ep_angle)
                )
                epads.append(epad)

        # Merge all exposed pads to a single object:
        merged_epads = epads[0]
        for p in epads[1:]:
            merged_epads = merged_epads.union(p)
    else:
        merged_epads = None

    return case, merged_pins, merged_epads, pinmark
