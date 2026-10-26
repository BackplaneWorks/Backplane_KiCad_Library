# Generated with CadQuery2

import cadquery as cq


def generate_connector(dims):
    x = -3.5 / 2
    while x < 0:
        dims["pins"]["centers"].append((x, 0))
        x = dims["pins"]["centers"][-1][0] + 0.5

    for i in range(8):
        dims["pins"]["centers"].append((dims["pins"]["centers"][i][0] * -1, 0))

    body = (
        cq.Workplane("XZ")
        .box(
            dims["body"]["width"],
            dims["body"]["height"],
            dims["body"]["depth"],
            centered=(True, False, True),
        )
        .edges("|Y")
        .fillet(dims["body"]["radius"])
        .faces("<Y")
        .shell(-dims["body"]["wall_thickness"])
        .translate(dims["body"]["offset"])
    )

    body_back = (
        body.faces(">Y")
        .workplane(
            offset=-(
                dims["body"]["depth"]
                - dims["body"]["cavity_depth"]
                - dims["body"]["wall_thickness"]
            )
        )
        .box(
            dims["body"]["width"],
            dims["body"]["height"],
            dims["body"]["depth"]
            - dims["body"]["cavity_depth"]
            - dims["body"]["wall_thickness"],
            centered=(True, False, False),
            combine=False,
        )
        .edges("|Y")
        .fillet(dims["body"]["radius"])
    )

    body = body.union(body_back)

    tounge = (
        body.faces(">Y[-2]")
        .box(
            dims["tounge"]["width"],
            dims["tounge"]["height"],
            dims["tounge"]["depth"],
            centered=(True, True, False),
            combine=False,
        )
        .edges("|Z and <Y")
        .chamfer(dims["tounge"]["tip_chamfer"])
    )

    pegs = (
        body.faces("<Z")
        .workplane()
        .pushPoints(dims["pegs"]["centers"])
        .circle(dims["pegs"]["diameter"] / 2)
        .extrude(dims["pegs"]["length"], combine=False)
        .edges("<Z")
        .chamfer(dims["pegs"]["tip_chamfer"])
    )

    shield_pins_front = (
        body.faces("<Z")
        .workplane(offset=-dims["body"]["height"] / 2)
        .pushPoints(dims["shield"]["centers_front"])
        .box(
            dims["shield"]["thickness"],
            dims["shield"]["width"][0],
            dims["shield"]["length"] + dims["body"]["height"] / 2,
            centered=(True, True, False),
            combine=True,
        )
    )
    body = (
        body.union(shield_pins_front)
        .edges("|X and <Z")
        .fillet(dims["shield"]["width"][0] / 2 - 0.01)
    )

    shield_pins_back = (
        body.faces("<Z[-2]")
        .workplane(offset=-dims["body"]["height"] / 2)
        .pushPoints(dims["shield"]["centers_back"])
        .box(
            dims["shield"]["thickness"],
            dims["shield"]["width"][1],
            dims["shield"]["length"] + dims["body"]["height"] / 2,
            centered=(True, True, False),
            combine=True,
        )
    )
    body = (
        body.union(shield_pins_back)
        .edges("|X and <Z")
        .fillet(dims["shield"]["width"][1] / 2 - 0.01)
    )

    del shield_pins_back
    del shield_pins_front
    del body_back

    pins = (
        cq.Workplane("XZ")
        .workplane(
            offset=-dims["body"]["depth"] / 2
            - dims["body"]["offset"][1]
            - dims["pins"]["length"]
        )
        .pushPoints(dims["pins"]["centers"])
        .box(
            dims["pins"]["width"],
            dims["pins"]["height"],
            dims["pins"]["length"],
            centered=(True, False, False),
            combine=True,
        )
    )
    return (body, tounge, pegs, pins)
