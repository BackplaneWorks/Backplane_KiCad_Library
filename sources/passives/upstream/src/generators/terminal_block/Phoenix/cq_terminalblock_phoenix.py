import cadquery as cq

from generators.tools.model.parameters import load_aux_parameters

screw_clearance = 0.10
screw_t = 0.70
screw_down = 0.20


def make_pin(i, bs):

    # make pin
    px = 1.0
    py = 1.0
    if "pin_size" in bs:
        px = bs["pin_size"]
        py = bs["pin_size"]
    if "pin_sizex" in bs:
        px = bs["pin_sizex"]
    if "pin_sizey" in bs:
        py = bs["pin_sizey"]
    pinl = bs["pin_l"]
    h = bs["height"]
    # print('  Making pin...\n')
    if bs["pin_shape"] == "rect":
        pin = (
            cq.Workplane("XY", origin=(0, 0, bs["opening_z"]))
            .workplane(centerOption="CenterOfMass")
            .rect(px, py)
            .extrude(-1 * (pinl + bs["opening_z"]))
        )
    else:
        pin = (
            cq.Workplane("XY", origin=(0, 0, bs["opening_z"]))
            .workplane(centerOption="CenterOfMass")
            .circle(px / 2)
            .extrude(-1 * (pinl + bs["opening_z"]))
        )

    # make terminal
    # print('  Making terminal...\n')
    pin = pin.union(
        cq.Workplane("XY", origin=(0, 0, bs["opening_z"]))
        .rect(bs["opening_w"], bs["terminal_d"])
        .extrude(bs["opening_h"])
    )

    # screw model
    # print('  Making screw...\n')
    pin = pin.union(
        cq.Workplane("XY", origin=(0, bs["screw_y"], bs["opening_z"] + bs["opening_h"]))
        .circle(bs["screw_dia"] / 2 - screw_clearance)
        .extrude(h - bs["opening_h"] - bs["opening_z"] - screw_down)
    )
    pin = pin.cut(
        cq.Workplane("XY", origin=(0, bs["screw_y"], h - screw_down))
        .rect(screw_t, bs["screw_dia"])
        .extrude(-1 * screw_t)
    )
    if bs["screw_cross"]:
        pin = pin.cut(
            cq.Workplane("XY", origin=(0, bs["screw_y"], h - screw_down))
            .rect(bs["screw_dia"] / 2, screw_t)
            .extrude(-1 * screw_t)
        )

    # make terminal hole
    # print('  Making terminal hole...\n')
    if bs["terminal_hole"] == "rect":
        hole = (
            cq.Workplane("XZ", origin=(0, bs["terminal_d"] / 2, bs["terminal_hole_z"]))
            .rect(bs["terminal_hole_w"], bs["terminal_hole_h"])
            .extrude(bs["terminal_d"])
        )
        if bs["terminal_hole_r"] > 0:
            hole = hole.edges("|Y").fillet(bs["terminal_hole_r"])
        pin = pin.cut(hole)
    else:
        pin = pin.cut(
            cq.Workplane("XZ", origin=(0, bs["terminal_d"] / 2, bs["terminal_hole_z"]))
            .circle(bs["terminal_hole_d"])
            .extrude(bs["terminal_d"])
        )

    # move into position
    # print('  Moving pin...\n')
    pin = pin.translate((bs["pitch"] * i, 0, 0))

    return pin


def get_bodystyle(series_params):
    body_style_params = load_aux_parameters(__file__, "bodystyles.yaml")

    # See if there is a match to the body style for the current model
    if series_params["bodystyle"] in body_style_params["bodystyles"]:
        bs = body_style_params["bodystyles"][series_params["bodystyle"]]
        # allow overrides in model def
        for k in bs.keys():
            if k in series_params:
                bs[k] = series_params[k]
        return bs

    # not defined - pitch required to defined other values
    if "pitch" in series_params:
        p = series_params["pitch"]
    else:
        p = 5.0

    bsdefault = {
        "pitch": p,
        "height": 12,
        "width": 8,
        "chf": False,
        "chb": False,
        "opening_w": p * 0.8,
        "opening_h": p * 0.8,
        "opening_z": 1.0,
        "terminal_d": p * 0.8,
        "terminal_hole": "circle",
        "terminal_hole_d": p * 0.6,
        "screw_dia": p * 0.8,
        "screw_t": 0,
        "screw_cross": False,
        "pin_shape": "circle",
        "pin_size": 1.0,
        "pin_l": 3.5,
        "key": "none",
        "pinslot": 0,
    }
    # allow overrides again
    for k in bsdefault.keys():
        if k in series_params:
            bsdefault[k] = series_params[k]
    return bsdefault


def make_dovetail(body, bs):
    dt_w = bs["key_w"]
    dt_l = bs["key_l"]
    dt_h = bs["key_h"]
    return (
        body.moveTo(0, dt_w / 4)
        .lineTo(dt_l, dt_w / 2)
        .lineTo(dt_l, -0.5 * dt_w)
        .lineTo(0, -0.25 * dt_w)
        .close()
        .extrude(dt_h)
    )


def make_part(series_params):

    # bodystyle defines series features/dimensions
    bs = get_bodystyle(series_params)

    # get often-used params
    p = bs["pitch"]
    w = bs["width"]
    n = series_params["n"]
    h = bs["height"]
    bo = bs["backoffset"]

    # calculate helper dimensions
    l = p * n

    # make base body (rectangle)
    if "endpadding" in bs:
        ep = bs["endpadding"]
    else:
        ep = 0
    body = (
        cq.Workplane("YZ", origin=(-1 * ep, 0, 0)).rect(w, h, False).extrude(l + 2 * ep)
    )

    # add front nub for pt (has to happen first)
    if "phoenix_pt" in series_params["bodystyle"]:
        # print('Making nubs...\n')
        if series_params["bodystyle"] == "phoenix_pt_5":
            nub_h = 3.5
            nub_w = 0.75
        else:  # _35
            nub_h = 2.85
            nub_w = 0.55
        body = body.union(
            cq.Workplane("YZ", origin=(0, -1 * nub_w, h - bs["chf_z"] - nub_h))
            .rect(nub_w, nub_h, False)
            .extrude(l)
            .edges("<Y")
            .edges("|X")
            .fillet(nub_w * 0.8)
        )

    # common style features
    for i in range(0, n):  # per opening
        xcl = p * (i + 0.5)
        # print('Making body pinwise features for pin ' + str(i+1) + ' @ x=' + str(xcl) + '...\n')
        # print('  Making cutout...\n')
        body = body.cut(
            cq.Workplane(
                "XZ", origin=(xcl, -100, bs["opening_z"] + bs["opening_h"] / 2)
            )
            .rect(bs["opening_w"], bs["opening_h"])
            .extrude(-1 * (100 + w - bo + (bs["terminal_d"] / 2)))
        )  # opening
        body = body.cut(
            cq.Workplane("XY", origin=(xcl, w - bo + bs["screw_y"], h))
            .circle(bs["screw_dia"] / 2)
            .extrude(-1 * (h - bs["opening_z"]))
        )  # screw hole
        pinco_w = 2.2
        if "pinslot" in bs and bs["pinslot"] > 0:
            # print('  Making pinslot...\n')
            body = body.cut(
                cq.Workplane("XZ", origin=(xcl, 0, bs["opening_z"] / 2))
                .rect(bs["pinslot"], bs["opening_z"])
                .extrude(-1 * (w - bo + bs["pinslot"] / 2))
                .edges(">Y")
                .edges("|Z")
                .fillet(bs["pinslot"] * 0.45)
            )  # slot for pin
        if "phoenix_pt" in series_params["bodystyle"]:
            # print('  Cleaning nub...\n')
            body = body.cut(
                cq.Workplane("XY", origin=(xcl, -50, 0))
                .rect(bs["opening_w"], 100)
                .extrude(h)
            )  # clear out nub (anything forward of front face)
        if series_params["bodystyle"] == "phoenix_pt_5":
            backhole_d = 2.2
            backhole_h = 5.35
            # print('  Adding backhole...\n')
            body = body.cut(
                cq.Workplane("XZ", origin=(xcl, w, backhole_h))
                .circle(backhole_d / 2)
                .extrude(w)
            )
        if "phoenix_m" in series_params["bodystyle"]:
            # print('  Lofting entry...\n')
            if "mkds_3" in series_params["bodystyle"]:
                loft_w = 4.00
                loft_zu = 3.15
                loft_zd = 2.35
                loft_d = 2.20
            elif "mpt_05" in series_params["bodystyle"]:
                loft_w = 2.15
                loft_zu = 2.40
                loft_zd = 2.05
                loft_d = 1.15
            else:  # mkds_15
                loft_w = 3.60
                loft_zu = 3.05
                loft_zd = 2.15
                loft_d = 0.80
            body = body.cut(
                cq.Workplane(
                    "XZ", origin=(xcl, loft_d, bs["opening_z"] + bs["opening_h"] / 2)
                )
                .rect(bs["opening_w"], bs["opening_h"])
                .workplane(offset=loft_d, centerOption="CenterOfMass")
                .moveTo(-0.5 * loft_w, -1 * loft_zd)
                .lineTo(-0.5 * loft_w, loft_zu)
                .lineTo(0.5 * loft_w, loft_zu)
                .lineTo(0.5 * loft_w, -1 * loft_zd)
                .close()
                .loft()
            )
        if series_params["bodystyle"] == "phoenix_mpt_05_254" and n < 4:
            # print('  Adding locator pin...\n')
            body = body.union(
                cq.Workplane("XY", origin=(xcl, w - bo - p, 0))
                .circle(0.55)
                .extrude(-1.50)
            )

    if bs["chf"]:  # front chamfer
        # print('Making front chamfer...\n')
        if bs["chf_ins"] > 0:
            body = body.cut(
                cq.Workplane("YZ", origin=(-1 * ep, 0, 0))
                .moveTo(0, h)
                .lineTo(bs["chf_y"] + bs["chf_ins"], h)
                .lineTo(bs["chf_ins"], h - bs["chf_z"])
                .lineTo(0, h - bs["chf_z"])
                .close()
                .extrude(l + 2 * ep)
            )
        else:
            body = body.cut(
                cq.Workplane("YZ", origin=(-1 * ep, 0, 0))
                .moveTo(0, h)
                .lineTo(bs["chf_y"], h)
                .lineTo(0, h - bs["chf_z"])
                .close()
                .extrude(l + 2 * ep)
            )
    if bs["chb"]:  # front chamfer
        # print('Making back chamfer...\n')
        if bs["chb_ins"] > 0:
            body = body.cut(
                cq.Workplane("YZ", origin=(-1 * ep, 0, 0))
                .moveTo(w, h)
                .lineTo(w - bs["chb_y"] - bs["chb_ins"], h)
                .lineTo(w - bs["chb_ins"], h - bs["chb_z"])
                .lineTo(w, h - bs["chb_z"])
                .close()
                .extrude(l + 2 * ep)
            )
        else:
            body = body.cut(
                cq.Workplane("YZ", origin=(-1 * ep, 0, 0))
                .moveTo(w, h)
                .lineTo(w - bs["chb_y"], h)
                .lineTo(w, h - bs["chb_z"])
                .close()
                .extrude(l + 2 * ep)
            )

    if series_params["bodystyle"] == "phoenix_pt_5":
        # print('Making back ribs...\n')
        rib_w = 0.80
        rib_h = 9.36
        for i in range(1, n):
            xcl = p * i
            body = body.union(
                cq.Workplane("XZ", origin=(xcl, w, rib_h / 2))
                .rect(rib_w, rib_h)
                .extrude(bs["chb_y"])
            )

    # add keys
    if "key" in bs and not bs["key"] == "none":
        k = 0
        if bs["key_l"] < 0:
            k = l
        key_z = 0
        klat = bs["key_lat"]
        if bs["key_vert"] == "top":
            key_z = h - bs["key_h"]
        key_y = bs["key_off"]
        if bs["key"] == "dovetail":
            if klat == "front" or klat == "both":
                # print('Making front dovetails...\n')
                body = body.cut(
                    make_dovetail(
                        cq.Workplane("XY", origin=(0 + k, (w - bo) - key_y, key_z)), bs
                    )
                )
                body = body.union(
                    make_dovetail(
                        cq.Workplane("XY", origin=(l - k, (w - bo) - key_y, key_z)), bs
                    )
                )
            if klat == "back" or klat == "both":
                # print('Making back dovetails...\n')
                body = body.cut(
                    make_dovetail(
                        cq.Workplane("XY", origin=(0 + k, (w - bo) + key_y, key_z)), bs
                    )
                )
                body = body.union(
                    make_dovetail(
                        cq.Workplane("XY", origin=(l - k, (w - bo) + key_y, key_z)), bs
                    )
                )
        elif bs["key"] == "rect":
            kl = bs["key_l"]
            kw = bs["key_w"]
            kh = bs["key_h"]
            if klat == "front" or klat == "both":
                # print('Making front keys...\n')
                body = body.cut(
                    cq.Workplane(
                        "XY", origin=((-0.5 * kl) + k, (w - bo) - key_y, key_z)
                    )
                    .rect(kl, kw)
                    .extrude(bs["key_h"])
                )
                body = body.extrude(
                    cq.Workplane(
                        "XY", origin=((0.5 * kl) + l - k, (w - bo) - key_y, key_z)
                    )
                    .rect(kl, kw)
                    .extrude(bs["key_h"])
                )
            if klat == "back" or klat == "both":
                # print('Making back keys...\n')
                body = body.cut(
                    cq.Workplane(
                        "XY", origin=((-0.5 * kl) + k, (w - bo) + key_y, key_z)
                    )
                    .rect(kl, kw)
                    .extrude(bs["key_h"])
                )
                body = body.extrude(
                    cq.Workplane(
                        "XY", origin=((0.5 * kl) + l - k, (w - bo) + key_y, key_z)
                    )
                    .rect(kl, kw)
                    .extrude(bs["key_h"])
                )

    # position body
    body = body.translate((-0.5 * p, -1 * (w - bo), 0))

    # make pins

    # print('Making pin 1...\n')
    pins = make_pin(0, bs)
    for i in range(1, n):
        # print('Making pin ' + str(i+1) + '...\n')
        pins = pins.union(make_pin(i, bs))

    return (body, pins)
