from math import sin

import cadquery as cq


def make_chip(params):
    # dimensions for DirectFET's
    A = params["A"]  # package length
    B = params["B"]  # package width
    C = params["C"]  # wing width
    D = params["D"]  # wing length

    M = params["M"]  # package height
    P = params["P"]  # die and body height over board
    R = params["R"]  # pad height over board

    if params["die"]:
        die_size_x = params["die"][0]
        die_size_y = params["die"][1]
        if len(params["die"]) > 2:
            die_pos_x = params["die"][2]
            die_pos_y = params["die"][3]
        else:
            die_pos_x = 0
            die_pos_y = 0

    pads = params["pads"]  # pads

    # modelName = params.modelName  # Model Name
    # rotation = params.rotation   # rotation

    top_subtract = B - (B * 0.9)
    top_width = B - top_subtract
    top_lenght = (A - 2 * D) - top_subtract

    ec = (B - C) / 2 / 3  # chamfer of edges
    shell_thickness = 0.1

    a = sin(45) * ec
    inner_ec = (a - shell_thickness / 4) / sin(45)
    top_ec = inner_ec

    # Create a 3D box based on the dimension variables above and fillet it
    case = cq.Workplane("XY").box(
        A - 2 * D, B, (M - (P + R)) * 0.5, centered=(True, True, False)
    )
    case = case.edges("|Z").chamfer(ec)
    case = (
        case.edges("|Y").edges(">Z").fillet(((M - (P + R)) * 0.5) + P + R - (M * 0.5))
    )

    subtract = cq.Workplane("XY").box(
        A - 2 * D - shell_thickness * 2,
        B - shell_thickness * 2,
        ((M - (P + R)) * 0.5) - 0.1,
        centered=(True, True, False),
    )
    if inner_ec > 0:
        subtract.edges("|Z").chamfer(inner_ec)
    case.cut(subtract)

    top = cq.Workplane("XY").box(
        top_lenght, top_width, (M - (P + R)) * 0.5, centered=(True, True, False)
    )
    if top_ec > 0:
        top = top.edges("|Z").fillet(top_ec)
    top_fillet = ((M - (P + R)) * 0.5) * 0.9
    top = top.edges(">Z").fillet(top_fillet)
    top = top.translate((0, 0, (M - P - R) * 0.5))
    case = case.union(top)
    case = case.translate((0, 0, P + R))

    wing1 = (
        cq.Workplane("XY")
        .box(D, C, M * 0.5, centered=(True, True, False))
        .translate(((A - D) / 2, 0, 0))
    )
    wing2 = (
        cq.Workplane("XY")
        .box(D, C, M * 0.5, centered=(True, True, False))
        .translate((-(A - D) / 2, 0, 0))
    )
    case = case.union(wing1).union(wing2)
    die = (
        cq.Workplane("XY")
        .box(
            die_size_x,
            die_size_y,
            (M - P) * 0.5 - (P + R),
            centered=(True, True, False),
        )
        .translate((die_pos_x, die_pos_y, P + R))
    )

    for Pad in range(len(pads)):
        if Pad == 0:
            Pads = (
                cq.Workplane("XY")
                .box(
                    pads[Pad][0],
                    pads[Pad][1],
                    (M - (P + R)) * 0.5 + P,
                    centered=(True, True, False),
                )
                .translate((pads[Pad][2], pads[Pad][3], R))
                .edges("<Z")
                .fillet(P * 0.9)
            )
        else:
            Pads = Pads.union(
                cq.Workplane("XY")
                .box(
                    pads[Pad][0],
                    pads[Pad][1],
                    (M - (P + R)) * 0.5 + P,
                    centered=(True, True, False),
                )
                .translate((pads[Pad][2], pads[Pad][3], R))
                .edges("<Z")
                .fillet(P * 0.9)
            )
    case = case.union(Pads)
    return (case, die)
