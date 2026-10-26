#!/usr/bin/env python3

import math
import os
import sys

common = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.path.pardir, "common")
)
if common not in sys.path:
    sys.path.insert(0, common)

common = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir, "common")
)
if common not in sys.path:
    sys.path.insert(0, common)

import kicad_sym
from DrawingElements import (
    Drawing,
    DrawingCircle,
    DrawingPin,
    DrawingPolyline,
    DrawingRectangle,
    ElementFill,
)
from Point import Point

libname = "SW_DIP"
library = kicad_sym.KicadLibrary(libname + ".kicad_sym")


def generateDIPSwitch(count):
    name = "SW_DIP_x{:02d}".format(count)
    refdes = "SW"
    footprintFilter = "SW?DIP?x{0}*".format(count)
    description = (
        "{0}x DIP Switch, Single Pole Single Throw (SPST) switch, small symbol".format(
            count
        )
    )
    keywords = "dip switch"
    datasheet = "~"

    grid_size = 100
    circle_radius = 20
    pin_length = 200
    switch_length = 200
    body_width = 300
    lever_angle = 15
    lever_length = switch_length - circle_radius
    width = switch_length + 2 * pin_length
    left = -width / 2
    body_x = -body_width / 2
    top = -round(count / 2) * grid_size
    height = count * grid_size
    body_height = height + grid_size
    body_y = top - grid_size

    symbol = kicad_sym.KicadSymbol.new(
        name, libname, refdes, "", datasheet, keywords, description, footprintFilter
    )
    library.symbols.append(symbol)

    symbol.hide_pin_names = True

    symbol.get_property("Reference").set_pos_mil(0, -(body_y - 50), 0)
    symbol.get_property("Value").set_pos_mil(0, -(body_y + body_height + 50), 0)

    drawing = Drawing()

    # Symbol body
    drawing.append(
        DrawingRectangle(
            end=Point(body_x + body_width, -(body_y + body_height)),
            fill=ElementFill.FILL_BACKGROUND,
            start=Point(body_x, -body_y),
            unit_idx=0,
        )
    )

    pin_left = 1
    pin_right = 2 * count
    pin_y = top

    for s in range(1, count + 1):
        # Left pins
        drawing.append(
            DrawingPin(
                at=Point(left, -pin_y),
                name="~",
                number=pin_left,
                orientation=DrawingPin.PinOrientation.RIGHT,
                pin_length=pin_length,
            )
        )
        # Right pins
        drawing.append(
            DrawingPin(
                at=Point(left + width, -pin_y),
                name="~",
                number=pin_right,
                orientation=DrawingPin.PinOrientation.LEFT,
                pin_length=pin_length,
            )
        )
        # Left circles
        drawing.append(
            DrawingCircle(
                at=Point(-(switch_length / 2 - circle_radius), -pin_y),
                line_width=0,
                radius=circle_radius,
                unit_idx=0,
            )
        )
        # Right circles
        drawing.append(
            DrawingCircle(
                at=Point(switch_length / 2 - circle_radius, -pin_y),
                line_width=0,
                radius=circle_radius,
                unit_idx=0,
            )
        )
        # Levers
        drawing.append(
            DrawingPolyline(
                line_width=0,
                points=[
                    Point(
                        -(switch_length / 2 - circle_radius)
                        + circle_radius * math.cos(lever_angle / 180 * math.pi),
                        -(
                            pin_y
                            - circle_radius * math.sin(lever_angle / 180 * math.pi)
                        ),
                    ),
                    Point(
                        -(switch_length / 2 - circle_radius)
                        + lever_length * math.cos(lever_angle / 180 * math.pi),
                        -(pin_y - lever_length * math.sin(lever_angle / 180 * math.pi)),
                    ),
                ],
                unit_idx=0,
            )
        )

        pin_left = pin_left + 1
        pin_right = pin_right - 1
        pin_y = pin_y + grid_size

    drawing.appendToSymbol(symbol)


if __name__ == "__main__":
    for i in range(1, 13):
        generateDIPSwitch(i)

    library.write()
