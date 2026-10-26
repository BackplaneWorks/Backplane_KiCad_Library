#!/usr/bin/env python3

import math
import os
import sys

common = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir, "common")
)
if common not in sys.path:
    sys.path.insert(0, common)

from kicad_sym import (
    Circle,
    KicadLibrary,
    KicadSymbol,
    Pin,
    Point,
    Polyline,
    Rectangle,
    mil_to_mm,
)


def roundToGrid(x, g):
    if x > 0:
        return math.ceil(x / g) * g
    else:
        return math.floor(x / g) * g


libname = "R_Network"
library = KicadLibrary(libname + ".kicad_sym")


def generateResistorNetwork(count):
    name = "R_Network{:02d}".format(count)
    refdes = "RN"
    footprint = "Resistor_THT:R_Array_SIP{0}".format(count + 1)
    footprint_filter = "R?Array?SIP*"
    description = (
        "{0} resistor network, star topology, bussed resistors, small symbol".format(
            count
        )
    )
    keywords = "R network star-topology"
    datasheet = "http://www.vishay.com/docs/31509/csc.pdf"

    grid_size = 100
    junction_diameter = 20
    pin_length = 100
    resistor_length = 160
    resistor_width = 60
    resistor_top_lead_length = 30
    body_left_offset = 50
    left = -math.floor(count / 2) * grid_size
    body_x = left - body_left_offset
    body_y = -125
    body_height = 250
    body_width = (count - 1) * grid_size + 2 * body_left_offset
    top = -200
    bottom = 200

    symbol = KicadSymbol.new(
        name,
        libname,
        refdes,
        footprint,
        datasheet,
        keywords,
        description,
        footprint_filter,
    )
    library.symbols.append(symbol)

    symbol.hide_pin_names = True
    symbol.pin_names_offset = 0
    symbol.get_property("Reference").set_pos_mil(body_x - 50, 0, 90)
    symbol.get_property("Value").set_pos_mil(body_x + body_width + 50, 0, 90)
    symbol.get_property("Footprint").set_pos_mil(body_x + body_width + 50 + 75, 0, 90)

    # Symbol body
    symbol.rectangles.append(
        Rectangle.new_mil(body_x, body_y, body_x + body_width, body_y + body_height)
    )

    pin_left = left

    # Common pin
    symbol.pins.append(
        Pin(
            "common",
            str(1),
            "passive",
            mil_to_mm(pin_left),
            mil_to_mm(-top),
            rotation=270,
        )
    )

    # First top resistor lead
    symbol.polylines.append(
        Polyline(
            points=[
                Point.new_mil(pin_left, -(top + pin_length)),
                Point.new_mil(pin_left, -(bottom - pin_length - resistor_length)),
            ]
        )
    )

    # print(symbol.properties)

    for s in range(1, count + 1):
        # Resistor pins
        symbol.pins.append(
            Pin(
                name="R{0}".format(s),
                number=str(s + 1),
                etype="passive",
                posx=mil_to_mm(pin_left),
                posy=mil_to_mm(top),
                rotation=90,
                length=mil_to_mm(pin_length),
            )
        )
        # Resistor bodies
        symbol.rectangles.append(
            Rectangle.new_mil(
                pin_left + resistor_width / 2,
                -(bottom - pin_length),
                pin_left - resistor_width / 2,
                -(bottom - pin_length - resistor_length),
            )
        )

        if s < count:
            # Top resistor leads
            symbol.polylines.append(
                Polyline(
                    points=[
                        Point.new_mil(
                            pin_left, -(bottom - pin_length - resistor_length)
                        ),
                        Point.new_mil(
                            pin_left,
                            -(
                                bottom
                                - pin_length
                                - resistor_length
                                - resistor_top_lead_length
                            ),
                        ),
                        Point.new_mil(
                            pin_left + grid_size,
                            -(
                                bottom
                                - pin_length
                                - resistor_length
                                - resistor_top_lead_length
                            ),
                        ),
                        Point.new_mil(
                            pin_left + grid_size,
                            -(bottom - pin_length - resistor_length),
                        ),
                    ],
                    stroke_width=0,
                )
            )
            # Junctions
            symbol.circles.append(
                Circle(
                    centerx=mil_to_mm(pin_left),
                    centery=mil_to_mm(
                        -(
                            bottom
                            - pin_length
                            - resistor_length
                            - resistor_top_lead_length
                        )
                    ),
                    radius=mil_to_mm(junction_diameter / 2),
                    fill_type="outline",
                    stroke_width=0,
                )
            )

        pin_left = pin_left + grid_size


def generateSIPNetworkDividers(count):
    name = "R_Network_Dividers_x{:02d}_SIP".format(count)
    refdes = "RN"
    footprint = "Resistor_THT:R_Array_SIP{0}".format(count + 2)
    footprint_filter = "R?Array?SIP*"
    description = "{0} voltage divider network, dual terminator, SIP package".format(
        count
    )
    keywords = "R network divider topology"
    datasheet = "http://www.vishay.com/docs/31509/csc.pdf"

    grid_size = 200
    junction_diameter = 20
    pin_length = 100
    resistor_length = 100
    resistor_width = 40
    body_left_offset = 50
    left = -math.floor(count / 2) * grid_size
    top = -300
    bottom = 300
    body_x = left - body_left_offset
    body_y = top + pin_length
    body_height = abs(bottom - pin_length - body_y)
    body_width = (count - 1) * grid_size + grid_size / 2 + 2 * body_left_offset
    resistor_vertical_spacing = (body_height - 2 * resistor_length) / 3

    symbol = KicadSymbol.new(
        name,
        libname,
        refdes,
        footprint,
        datasheet,
        keywords,
        description,
        footprint_filter,
    )
    library.symbols.append(symbol)

    symbol.hide_pin_names = True
    symbol.pin_names_offset = 0
    symbol.get_property("Reference").set_pos_mil(body_x - 50, 0, 90)
    symbol.get_property("Value").set_pos_mil(body_x + body_width + 50, 0, 90)
    symbol.get_property("Footprint").set_pos_mil(body_x + body_width + 50 + 75, 0, 90)

    # Symbol body
    symbol.rectangles.append(
        Rectangle.new_mil(body_x, body_y, body_x + body_width, body_y + body_height)
    )

    pin_left = left

    # Common 1 pin
    symbol.pins.append(
        Pin(
            "COM1",
            str(1),
            "passive",
            mil_to_mm(pin_left),
            mil_to_mm(-top),
            rotation=270,
            length=mil_to_mm(pin_length),
        )
    )
    # Common 2 pin
    symbol.pins.append(
        Pin(
            "COM2",
            str(count + 2),
            "passive",
            mil_to_mm(left + (count - 1) * grid_size + grid_size / 2),
            mil_to_mm(-top),
            rotation=270,
            length=mil_to_mm(pin_length),
        )
    )

    # Vertical COM2 lead
    symbol.polylines.append(
        Polyline(
            points=[
                Point.new_mil(
                    left + (count - 1) * grid_size + grid_size / 2,
                    -(bottom - pin_length - resistor_vertical_spacing / 2),
                ),
                Point.new_mil(
                    left + (count - 1) * grid_size + grid_size / 2, -(top + pin_length)
                ),
            ],
            stroke_width=0,
        )
    )

    for s in range(1, count + 1):
        # Voltage divider center pins
        symbol.pins.append(
            Pin(
                name="R{0}".format(s),
                number=str(s + 1),
                etype="passive",
                posx=mil_to_mm(pin_left),
                posy=mil_to_mm(-bottom),
                rotation=90,
                length=mil_to_mm(pin_length),
            )
        )
        # Top resistor bodies
        symbol.rectangles.append(
            Rectangle.new_mil(
                pin_left + resistor_width / 2,
                -(top + pin_length + resistor_vertical_spacing + resistor_length),
                pin_left - resistor_width / 2,
                -(top + pin_length + resistor_vertical_spacing),
            )
        )
        # Bottom resistor bodies
        symbol.rectangles.append(
            Rectangle.new_mil(
                pin_left + 3 * resistor_width / 2 + resistor_width / 2,
                -(bottom - pin_length - resistor_vertical_spacing - resistor_length),
                pin_left + 3 * resistor_width / 2 - resistor_width / 2,
                -(bottom - pin_length - resistor_vertical_spacing),
            )
        )
        # Horizontal COM2 leads
        symbol.polylines.append(
            Polyline(
                points=[
                    Point.new_mil(
                        pin_left + 3 * resistor_width / 2,
                        -(bottom - pin_length - resistor_vertical_spacing),
                    ),
                    Point.new_mil(
                        pin_left + 3 * resistor_width / 2,
                        -(bottom - pin_length - resistor_vertical_spacing / 2),
                    ),
                    Point.new_mil(
                        left + (count - 1) * grid_size + grid_size / 2,
                        -(bottom - pin_length - resistor_vertical_spacing / 2),
                    ),
                ],
                stroke_width=0,
            )
        )

        if s == 1:
            # First resistor top lead
            symbol.polylines.append(
                Polyline(
                    points=[
                        Point.new_mil(pin_left, -(top + pin_length)),
                        Point.new_mil(
                            pin_left, -(top + pin_length + resistor_vertical_spacing)
                        ),
                    ],
                    stroke_width=0,
                )
            )

        if s > 1:
            # Top resistor top leads
            symbol.polylines.append(
                Polyline(
                    points=[
                        Point.new_mil(
                            pin_left - grid_size,
                            -(top + pin_length + resistor_vertical_spacing / 2),
                        ),
                        Point.new_mil(
                            pin_left,
                            -(top + pin_length + resistor_vertical_spacing / 2),
                        ),
                        Point.new_mil(
                            pin_left, -(top + pin_length + resistor_vertical_spacing)
                        ),
                    ],
                    stroke_width=0,
                )
            )

        # Top resistor bottom leads
        symbol.polylines.append(
            Polyline(
                points=[
                    Point.new_mil(pin_left, -(bottom - pin_length)),
                    Point.new_mil(
                        pin_left,
                        -(
                            top
                            + pin_length
                            + resistor_vertical_spacing
                            + resistor_length
                        ),
                    ),
                ],
                stroke_width=0,
            )
        )
        # Bottom resistor top leads
        symbol.polylines.append(
            Polyline(
                points=[
                    Point.new_mil(
                        pin_left,
                        -(
                            top
                            + pin_length
                            + resistor_vertical_spacing
                            + resistor_length
                            + resistor_vertical_spacing / 2
                        ),
                    ),
                    Point.new_mil(
                        pin_left + 3 * resistor_width / 2,
                        -(
                            top
                            + pin_length
                            + resistor_vertical_spacing
                            + resistor_length
                            + resistor_vertical_spacing / 2
                        ),
                    ),
                    Point.new_mil(
                        pin_left + 3 * resistor_width / 2,
                        -(
                            bottom
                            - pin_length
                            - resistor_vertical_spacing
                            - resistor_length
                        ),
                    ),
                ],
                stroke_width=0,
            )
        )
        # Center junctions
        symbol.circles.append(
            Circle(
                centerx=mil_to_mm(pin_left),
                centery=mil_to_mm(0),
                radius=mil_to_mm(junction_diameter / 2),
                fill_type="outline",
                stroke_width=0,
            )
        )

        if s > 1:
            # Bottom junctions
            symbol.circles.append(
                Circle(
                    centerx=mil_to_mm(pin_left + 3 * resistor_width / 2),
                    centery=mil_to_mm(
                        -(bottom - pin_length - resistor_vertical_spacing / 2)
                    ),
                    radius=mil_to_mm(junction_diameter / 2),
                    fill_type="outline",
                    stroke_width=0,
                )
            )

        if s < count:
            # Top junctions
            symbol.circles.append(
                Circle(
                    centerx=mil_to_mm(pin_left),
                    centery=mil_to_mm(
                        -(top + pin_length + resistor_vertical_spacing / 2)
                    ),
                    radius=mil_to_mm(junction_diameter / 2),
                    fill_type="outline",
                    stroke_width=0,
                )
            )

        pin_left = pin_left + grid_size


def generateResistorPack(count):
    name = "R_Pack{:02d}".format(count)
    refdes = "RN"
    footprint = ""
    footprint_filter = ["DIP*", "SOIC*"]
    description = "{0} resistor network, parallel topology, DIP package".format(count)
    keywords = "R network parallel topology isolated"
    datasheet = "~"

    grid_size = 100
    pin_length = 100
    resistor_length = 150
    resistor_width = 50
    body_left_offset = 50
    body_top_offset = 20
    left = -roundToGrid(((count - 1) * grid_size) / 2, 100)
    body_x = left - body_left_offset
    body_height = resistor_length + 2 * body_top_offset
    body_y = -body_height / 2
    body_width = ((count - 1) * grid_size) + 2 * body_left_offset
    top = -200
    bottom = 200

    symbol = KicadSymbol.new(
        name,
        libname,
        refdes,
        footprint,
        datasheet,
        keywords,
        description,
        footprint_filter,
    )
    library.symbols.append(symbol)

    symbol.hide_pin_names = True
    symbol.pin_names_offset = 0
    symbol.get_property("Reference").set_pos_mil(body_x - 50, 0, 90)
    symbol.get_property("Value").set_pos_mil(body_x + body_width + 50, 0, 90)
    symbol.get_property("Footprint").set_pos_mil(body_x + body_width + 50 + 75, 0, 90)

    # Symbol body
    symbol.rectangles.append(
        Rectangle.new_mil(body_x, body_y, body_x + body_width, body_y + body_height)
    )

    pin_left = left

    for s in range(1, count + 1):
        # Resistor bottom pins
        symbol.pins.append(
            Pin(
                name="R{0}.1".format(s),
                number=str(s),
                etype="passive",
                posx=mil_to_mm(pin_left),
                posy=mil_to_mm(-bottom),
                rotation=90,
                length=mil_to_mm(pin_length),
            )
        )
        # Resistor top pins
        symbol.pins.append(
            Pin(
                name="R{0}.2".format(s),
                number=str(2 * count - s + 1),
                etype="passive",
                posx=mil_to_mm(pin_left),
                posy=mil_to_mm(-top),
                rotation=270,
                length=mil_to_mm(pin_length),
            )
        )
        # Resistor bodies
        symbol.rectangles.append(
            Rectangle.new_mil(
                pin_left + resistor_width / 2,
                -(resistor_length / 2),
                pin_left - resistor_width / 2,
                -(-resistor_length / 2),
            )
        )
        # Resistor bottom leads
        symbol.polylines.append(
            Polyline(
                points=[
                    Point.new_mil(pin_left, -(bottom - pin_length)),
                    Point.new_mil(pin_left, -(resistor_length / 2)),
                ],
                stroke_width=0,
            )
        )
        # Resistor top leads
        symbol.polylines.append(
            Polyline(
                [
                    Point.new_mil(pin_left, -(-resistor_length / 2)),
                    Point.new_mil(pin_left, -(top + pin_length)),
                ],
                stroke_width=0,
            )
        )

        pin_left = pin_left + grid_size


def generateSIPResistorPack(count):
    name = "R_Pack{:02d}_SIP".format(count)
    refdes = "RN"
    footprint = "Resistor_THT:R_Array_SIP{0}".format(count * 2)
    footprint_filter = "R?Array?SIP*"
    description = "{0} resistor network, parallel topology, SIP package".format(count)
    keywords = "R network parallel topology isolated"
    datasheet = "http://www.vishay.com/docs/31509/csc.pdf"

    grid_size = 100
    resistor_horizontal_spacing = 300
    pin_length = 150
    resistor_length = 160
    resistor_width = 60
    resistor_long_lead_length = 30
    body_left_offset = 50
    left = -roundToGrid(((count - 1) * resistor_horizontal_spacing) / 2, 100)
    body_x = left - body_left_offset
    body_y = -75
    body_height = 250
    body_width = (
        (count - 1) * resistor_horizontal_spacing + grid_size
    ) + 2 * body_left_offset
    bottom = 200

    symbol = KicadSymbol.new(
        name,
        libname,
        refdes,
        footprint,
        datasheet,
        keywords,
        description,
        footprint_filter,
    )
    library.symbols.append(symbol)

    symbol.hide_pin_names = True
    symbol.pin_names_offset = 0
    symbol.get_property("Reference").set_pos_mil(body_x - 50, 0, 90)
    symbol.get_property("Value").set_pos_mil(body_x + body_width + 50, 0, 90)
    symbol.get_property("Footprint").set_pos_mil(body_x + body_width + 50 + 75, 0, 90)

    # Symbol body
    symbol.rectangles.append(
        Rectangle.new_mil(body_x, body_y, body_x + body_width, body_y + body_height)
    )

    pin_left = left

    for s in range(1, count + 1):
        # Resistor short pins
        symbol.pins.append(
            Pin(
                name="R{0}.1".format(s),
                number=str(2 * s - 1),
                etype="passive",
                posx=mil_to_mm(pin_left),
                posy=mil_to_mm(-bottom),
                rotation=90,
                length=mil_to_mm(pin_length),
            )
        )
        # Resistor long pins
        symbol.pins.append(
            Pin(
                name="R{0}.2".format(s),
                number=str(2 * s),
                etype="passive",
                posx=mil_to_mm(pin_left + grid_size),
                posy=mil_to_mm(-bottom),
                rotation=90,
                length=mil_to_mm(pin_length),
            )
        )
        # Resistor bodies
        symbol.rectangles.append(
            Rectangle.new_mil(
                pin_left + resistor_width / 2,
                -(bottom - pin_length),
                pin_left - resistor_width / 2,
                -(bottom - pin_length - resistor_length),
            )
        )
        # Resistor long leads
        symbol.polylines.append(
            Polyline(
                points=[
                    Point.new_mil(pin_left, -(bottom - pin_length - resistor_length)),
                    Point.new_mil(
                        pin_left,
                        -(
                            bottom
                            - pin_length
                            - resistor_length
                            - resistor_long_lead_length
                        ),
                    ),
                    Point.new_mil(
                        pin_left + grid_size,
                        -(
                            bottom
                            - pin_length
                            - resistor_length
                            - resistor_long_lead_length
                        ),
                    ),
                    Point.new_mil(pin_left + grid_size, -(bottom - pin_length)),
                ],
                stroke_width=0,
            )
        )

        pin_left = pin_left + resistor_horizontal_spacing


if __name__ == "__main__":
    for i in range(3, 14):
        generateResistorNetwork(i)

    for i in range(2, 12):
        generateSIPNetworkDividers(i)

    for i in range(2, 8):
        generateResistorPack(i)
        generateSIPResistorPack(i)

    for i in range(8, 12):
        generateResistorPack(i)

    library.write()
