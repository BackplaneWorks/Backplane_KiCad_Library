from math import radians, tan

import cadquery as cq

ma_deg = 8


def make_Smx(params):

    L = params["L"]
    W = params["W"]
    H = params["H"]
    F = params["F"]
    S = params["S"]
    T = params["T"]
    G = params["G"]
    pml = params["pml"]
    rot = params["rotation"]
    # dest_dir_pref = params.dest_dir_prefix

    Lb = L - 2.0 * T  # body lenght
    ppH = H * 0.45  # pivot point height

    ma_rad = radians(ma_deg)
    dtop = (H - ppH) * tan(ma_rad)
    dbot = (ppH - T) * tan(ma_rad)
    dbump = ppH * tan(ma_rad)

    body_base = (
        cq.Workplane(cq.Plane.XY())
        .workplane(centerOption="CenterOfMass", offset=0)
        .rect(W - dbump, G)
        .workplane(centerOption="CenterOfMass", offset=T)
        .rect(W - dbot, G)
        .loft(ruled=True)
    )

    body = (
        cq.Workplane(cq.Plane.XY())
        .workplane(centerOption="CenterOfMass", offset=T)
        .rect(W - dbot, Lb - dbot)
        .workplane(centerOption="CenterOfMass", offset=ppH - T)
        .rect(W, Lb)
        .workplane(centerOption="CenterOfMass", offset=H - ppH)
        .rect(W - dtop, Lb - dtop)
        .loft(ruled=True)
    )

    body = body.union(body_base)
    # sleep
    pinmark = (
        cq.Workplane(cq.Plane.XY())
        .workplane(centerOption="CenterOfMass", offset=H)
        .rect(W - dtop - dtop, pml)
        .workplane(centerOption="CenterOfMass", offset=T * 0.01)
        .rect(W - dtop - dtop, pml)
        .loft(ruled=True)
    )

    # translate the object
    pinmark = pinmark.translate(
        (0, Lb / 2.0 - pml / 2.0 - dtop / 2.0 - dtop / 2.0, 0)
    ).rotate((0, 0, 0), (0, 1, 0), 0)
    # Create a pin object at the center of top side.
    # threePointArc((L+K/sqrt(2), b/2-K*(1-1/sqrt(2))),
    #              (L+K, b/2-K)). \
    bpin1 = (
        cq.Workplane("XY")
        .moveTo(0, Lb / 2.0 - S)
        .lineTo(0, Lb / 2.0)
        .lineTo(F, Lb / 2.0)
        .lineTo(F, Lb / 2.0 - S)
        .close()
        .extrude(T + 0.01 * T)
    )
    bpin1 = bpin1.translate((-F / 2.0, 0, 0))
    bpin = bpin1.translate((0, -Lb + S, 0))

    delta = 0.01
    hpin = ppH - delta * ppH
    bpin2 = (
        cq.Workplane("XY")
        .moveTo(0, Lb / 2.0)
        .lineTo(0, Lb / 2.0 + T)
        .lineTo(F, Lb / 2.0 + T)
        .lineTo(F, Lb / 2.0)
        .close()
        .extrude(hpin)
    )
    bpin2 = bpin2.translate((-F / 2.0, 0, 0))
    BS = cq.selectors.BoxSelector
    bpin2 = bpin2.edges(
        BS(
            (0 - delta, L / 2.0 - delta, hpin - delta),
            (0 + delta, L / 2.0 + delta, hpin + delta),
        )
    ).fillet(T * 2.0 / 3.0)
    bpin2 = bpin2.edges(
        BS(
            (0 - delta, L / 2.0 - delta, 0 - delta),
            (0 + delta, L / 2.0 + delta, 0 + delta),
        )
    ).fillet(T * 2.0 / 3.0)
    bpinv = bpin2.rotate((0, 0, 0), (0, 0, 1), 180)  # .translate((0,-T,0))

    merged_pins = bpin
    merged_pins = merged_pins.union(bpin1)
    merged_pins = merged_pins.union(bpin2)
    merged_pins = merged_pins.union(bpinv)
    pins = merged_pins

    return (body, pins, pinmark)
