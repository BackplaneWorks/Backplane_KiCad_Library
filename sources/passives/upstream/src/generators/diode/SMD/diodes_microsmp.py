import cadquery as cq

from generators.tools.model import cq_color_correct, parameters, shaderColors

# these sizes are without the pins (see *_OVERHANG)
BOTTOM_BODY_WIDTH = 2.2
BOTTOM_BODY_DEPTH = 1.3
UPPER_BODY_HEIGHT = 0.485
TOP_OFFSET = 0.04

LARGE_PIN_WIDTH = 1.3
LARGE_PIN_DEPTH = 0.88
LARGE_PIN_HEIGHT = 0.195
LARGE_PIN_OVERHANG = 0.15
SMALL_PIN_WIDTH = 0.65
SMALL_PIN_DEPTH = 0.65
SMALL_PIN_HEIGHT = LARGE_PIN_HEIGHT
SMALL_PIN_OVERHANG = LARGE_PIN_OVERHANG

CATHODE_BAND_OFFSET = 0.155
CATHODE_BAND_WIDTH = 0.166
CATHODE_BAND_THICKNESS = 0.01

BODY_COLOR_NAME = "black body"
MARK_COLOR_NAME = "light brown label"
PINS_COLOR_NAME = "metal grey pins"


def make_microsmp(parameters):
    # specified dimensions
    full_length = parameters["L"]  # includes pins
    full_width = parameters["W"]
    full_height = parameters["H"]  # top cap + pin zone
    large_pin_length = parameters["SL"]
    large_pin_width = parameters["FL"]
    large_pin_height = parameters["TL"]
    large_pin_overhang = parameters["DL"]
    small_pin_length = parameters["SS"]
    small_pin_width = parameters["FS"]
    small_pin_height = parameters["TS"]
    small_pin_overhang = parameters["DS"]
    cathode_band_offset = parameters["KO"]
    cathode_band_width = parameters["KW"]
    cathode_band_thickness = parameters["KT"]
    top_chamfer = parameters["C"]
    large_pin_is_anode = parameters.get("large_pin_is_anode", False)

    # additional dimensions
    lower_body_length = full_length - (small_pin_overhang + large_pin_overhang)
    lower_body_height = max(large_pin_height, small_pin_height)
    upper_body_height = full_height - lower_body_height

    # connectors
    small_pin_x_offset = (
        lower_body_length - small_pin_length
    ) / 2.0 + small_pin_overhang
    small_pin = (
        cq.Workplane("XY")
        .workplane(offset=lower_body_height / 2)
        .move(
            -small_pin_x_offset if large_pin_is_anode else small_pin_x_offset,
            0,
        )
        .box(small_pin_length, small_pin_width, small_pin_height)
    )
    large_pin_x_offset = (
        lower_body_length - large_pin_length
    ) / 2.0 + large_pin_overhang
    large_pin = (
        cq.Workplane("XY")
        .workplane(offset=lower_body_height / 2)
        .move(
            large_pin_x_offset if large_pin_is_anode else -large_pin_x_offset,
            0,
        )
        .box(large_pin_length, large_pin_width, large_pin_height)
    )
    pins = small_pin.union(large_pin)

    # body
    bottom_body = (
        cq.Workplane("XY")
        .workplane(offset=lower_body_height / 2)
        .box(lower_body_length, full_width, lower_body_height)
        .cut(small_pin)
        .cut(large_pin)
    )
    top_body = (
        cq.Workplane("XY")
        .workplane(offset=lower_body_height)
        .rect(lower_body_length, full_width)
        .workplane(offset=upper_body_height)
        .rect(lower_body_length - 2 * top_chamfer, full_width - 2 * top_chamfer)
        .loft()
    )
    full_body = bottom_body.union(top_body)

    # cathode band (always on the left)
    cathode_band = (
        cq.Workplane("XY")
        .workplane(offset=lower_body_height + upper_body_height)
        .move(
            -(lower_body_length - cathode_band_width) / 2
            + top_chamfer
            + cathode_band_offset
        )
        .box(
            cathode_band_width,
            full_width - 2 * top_chamfer,
            cathode_band_thickness,
        )
    )

    # return parts of assembly
    return (
        full_body,
        pins,
        cathode_band,
    )
