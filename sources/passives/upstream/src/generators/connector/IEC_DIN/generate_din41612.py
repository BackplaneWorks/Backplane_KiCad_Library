# generators is free software: you can redistribute it and/or modify it under the terms
# of the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# generators is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# generators. If not, see < http://www.gnu.org/licenses/ >.
#
# (C) The KiCad Librarian Team

import os
import string
import sys
from KicadModTree import *
from generators.tools.footprint.drawing_tools import *
from generators.tools.footprint.save_footprint import write_footprint
from kilibs.config import global_config as GC
from math import ceil

# According to IEC 60603-2 §3 and DIN 41612-1 §2 connector names should be like
# this:
# "${STANDARD}${TYPE}${PINCOUNT}${GENDER}${METHOD}-${FURTHER_INFO}"
# with:
# STANDARD: either "IEC 60603-2 " or "DIN 41 612-"
# TYPE: B, C, D, E, F, G, H, M, Q, R, S, T, U, V, W
# PINCOUNT: Number of populated pins, 3 digits
# SEX: M: male, F: female
# METHOD: A: screws, C (DIN) crimp (IEC), D: insulation displacement (IEC),
#         K: clamps (DIN), P: press fit (DIN) S: solder, T: blade receptacle,
#         W: wire wrap
# FURTHER_INFO: Pin length, materials and other things that don't change the
#               footprint.
#
# This library choose to use the prefix "Conn_DIN41612_", because Din 41612 is
# more common term.
# METHOD and further are omitted, because the footprint is suited for
# soldering and press fit.
#
# It includes half and third sized connectors, that are not part of IEC 60603
# or DIN 41612. These connectors are named 2X and 3X, a convention also used by
# Harting.

# These connectors do not place the grid origin on top of the first existing
# pin. The standard is designed such that the a1 pin is always on the same
# position on the board. It is used as grid origin even if a1 is not populated.
# This allows it to change between different connectors while maintaining their
# precise position on the PCB.
# See the discussion in the originial pull request:
# https://github.com/KiCad/kicad-footprints/pull/1076

lib_name = "Connector_DIN"
global_config = GC.GLOBAL_CONFIG

large_holes = {
    "pin_hole_diameter": 1.6,
    "pin_plating_diameter": 2.6,
}


# dimensions based of ERNI, ept and Harting
dimensions = {
    "pin_hole_diameter": 1,
    "pin_plating_diameter": 1.55,
    "mounting_hole_diameter": 2.85,
    "pin_row_offset": 2.54,
    "pin_column_offset": 2.54,
    "silk_reference_offset": 1.0,
    "name_pattern": "{row}{pin}",
    "Horizontal": {
        "a1_mounting": 2.54,
        "a1_edge": 5.3,
        "edge_offset": 0.5,
        "mounting_housing_front": 10.2,  # max set by ERNI
        "mounting_housing_back": -2.54,  # max set by ept
        "gender": "male",
        "full": {
            "housing_width": 94,
            "connector_width": 87.5,
            "mounting_width": 88.9,
            "row_pins": 32,
            "pin_nr_offset": 0
        },
        "half": {
            "housing_width": 53.9,
            "connector_width": 47,
            "mounting_width": 48.26,
            "row_pins": 16,
            "pin_nr_offset": 0
        },
        "third": {
            "housing_width": 38.1,
            "connector_width": 31.7,
            "mounting_width": 33.02,
            "row_pins": 10,
            "pin_nr_offset": 0
        },
        "m1": {
            "housing_width": 94,
            "connector_width": 87.5,
            "mounting_width": 88.9,
            "row_pins": 26,
            "pin_nr_offset": 3 # pin_nr_offset * 2 + row_pins = 32
        },
        "m2": {
            "housing_width": 94,
            "connector_width": 87.5,
            "mounting_width": 88.9,
            "row_pins": 20,
            "pin_nr_offset": 6
        },
        "m3": {
            "housing_width": 94,
            "connector_width": 87.5,
            "mounting_width": 88.9,
            "row_pins": 14,
            "pin_nr_offset": 9
        },
        "m4": { # None standard
            "housing_width": 94,
            "connector_width": 87.5,
            "mounting_width": 88.9,
            "row_pins": 8,
            "pin_nr_offset": 12
        },
        "m5": { # None standard
            "housing_width": 94,
            "connector_width": 87.5,
            "mounting_width": 88.9,
            "row_pins": 2,
            "pin_nr_offset": 15
        },
    },
    "Vertical": {
        "a1_mounting": 2.54 - 0.3,
        "housing_depth": 8.6,
        "connector_depth": 6.2,
        "nodge_width": 1,
        "mounting_hole_diameter": 2.85,
        "pin_hole_diameter": 1,
        "nodge_height": 3,
        "nodge_width": 1,
        "gender": "female",
        "full": {
            "housing_width": 95,
            "connector_width": 85,
            "connector_outer_width": 88,
            "mounting_width": 90,
            "row_pins": 32,
            "pin_nr_offset": 0
        },
        "half": {
            "housing_width": 55,
            "connector_width": 44.4,
            "connector_outer_width": 47.4,
            "mounting_width": 50,
            "row_pins": 16,
            "pin_nr_offset": 0
        },
        "third": {
            "housing_width": 39.76,
            "connector_width": 29.2,
            "connector_outer_width": 32.1,
            "mounting_width": 34.76,
            "row_pins": 10,
            "pin_nr_offset": 0
        },
        "m1": {
            "housing_width": 95,
            "connector_width": 85,
            "connector_outer_width": 88,
            "mounting_width": 90,
            "row_pins": 26,
            "pin_nr_offset": 3 # pin_nr_offset * 2 + row_pins = 32
        },
        "m2": {
            "housing_width": 95,
            "connector_width": 85,
            "connector_outer_width": 88,
            "mounting_width": 90,
            "row_pins": 20,
            "pin_nr_offset": 6
        },
        "m3": {
            "housing_width": 95,
            "connector_width": 85,
            "connector_outer_width": 88,
            "mounting_width": 90,
            "row_pins": 14,
            "pin_nr_offset": 9
        },
        "m4": { # None standard
            "housing_width": 95,
            "connector_width": 85,
            "connector_outer_width": 88,
            "mounting_width": 90,
            "row_pins": 8,
            "pin_nr_offset": 12
        },
        "m5": { # None standard
            "housing_width": 95,
            "connector_width": 85,
            "connector_outer_width": 88,
            "mounting_width": 90,
            "row_pins": 2,
            "pin_nr_offset": 15
        },
    },
    "series": {
        "B": dict(
            series_rows="ab",
            housing_height=8.1,
            connector_height=6,
            directions = {"Horizontal", "Vertical"},
        ),
        "C": dict(
            series_rows="abc",
            housing_height=10.6,
            connector_height=8.5,
            directions = {"Horizontal", "Vertical"},
        ),
        #            'CD': { 'series_rows': 'abcd' },
        "D": dict(
            series_rows="abc",
            housing_height=10.6,
            connector_height=8.5,
            directions = {"Horizontal", "Vertical"}, **large_holes
        ),
        "E": dict(
            series_rows="abcde",
            housing_height=15.7,
            connector_height=13.6,
            directions = {"Horizontal", "Vertical"},
            **large_holes,
        ),
        #            'E160': { 'series_rows': 'abcde', },
        "F": dict(
            series_rows="zbd",
            housing_height=14.8,
            connector_height=12.4,
            Vertical=large_holes,
            directions = {"Horizontal", "Vertical"},
        ),
        #            'F_flat': { 'series_rows': 'zbd', },
        # TODO H11 vertical and horizontal use different rows (e, vs. ac)
        #            'H11': { 'series_rows': 'e',
        #                'name_pattern': '{pin}', **large_holes,
        #                'mounting_housing_front': 14.3,
        #                'a1_mounting': 12.7,
        #                'a1_edge': 12.7 + 2.3,
        #                },
        "M": dict(
            series_rows="abc",
            housing_height=10.6,
            connector_height=8.5,
            directions = {"Horizontal", "Vertical"},
        ),
        "M-flat": dict( # None standard
            series_rows="abc",
            housing_height=10.6,
            connector_height=8.5,
            directions = {"Vertical"},
        ),
        "M-invers": dict( # None standard
            series_rows="abc",
            housing_height=10.6,
            connector_height=8.5,
            gender_reverse=True,
            directions = {"Horizontal", "Vertical"},
        ),
        "Q": dict(
            series_rows="ab",
            mounting_housing_back=10.2 - 12.6,
            housing_height=8.6,
            connector_height=6.2,
            nodge_height=2.5,
            gender_reverse=True,
            directions = {"Horizontal", "Vertical"},
        ),
        "R": dict(
            series_rows="abc",
            housing_height=11.1,
            connector_height=8.7,
            nodge_height=2.5,
            gender_reverse=True,
            directions = {"Horizontal", "Vertical"},
        ),
    },
}

# There is also some info on these parts in: https://www.mouser.com/datasheet/2/625/ERNI-DIN41612-IEC60603-2-e-364520.pdf
datasheets = [
    "https://b2b.harting.com/files/livebooks/en/PRD0200000100063/downloads/livebook.pdf",
]

global_config = GC.GLOBAL_CONFIG

mounting_args = dict(
    type=Pad.TYPE_NPTH,
    shape=Pad.SHAPE_CIRCLE,
    size=dimensions["mounting_hole_diameter"],
    drill=dimensions["mounting_hole_diameter"],
    layers=Pad.LAYERS_NPTH,
)

silk_reference_args = dict(
    type="reference",
    text="REF**",
    layer="F.SilkS",
    thickness=0.15,
    size=(1, 1),
)

fab_reference_args = dict(
    type="user",
    text="${REFERENCE}",
    layer="F.Fab",
    thickness=0.15,
    size=(1, 1),
)


def mirror_x(point, ref):
    shifted = point - ref
    return Vector2D(ref.x - shifted.x, point.y)


def mirror_y(point, ref):
    shifted = point - ref
    return Vector2D(point.x, ref.y - shifted.y)


def round_courtyard(point):
    grid = 0.01
    return Vector2D(ceil(point.x / grid) * grid, ceil(point.y / grid) * grid)


def build_positions(config, pins_per_row, row, row_direction, column_direction):
    if row_direction == Vector2D(0, 1):  # horizontal
        offset = config["series_rows"].lower().index(row) * config["pin_row_offset"]
    else:  # vertical always uses all rows, z is index -1
        rows = "zabcde"
        offset = (rows.index(row) - 1) * config["pin_row_offset"]
    pin_one = Vector2D(row_direction.x * offset, row_direction.y * offset)
    if pins_per_row == config["row_pins"]:
        positions = range(1 + config["pin_nr_offset"], config["row_pins"] + 1 + config["pin_nr_offset"])
    elif pins_per_row == config["row_pins"] // 2:
        positions = range(2 + config["pin_nr_offset"], config["row_pins"] + 1 + config["pin_nr_offset"], 2)
    elif pins_per_row == config["row_pins"] // 4:
        positions = range(2 + config["pin_nr_offset"], config["row_pins"] + 1 + config["pin_nr_offset"], 4)
    elif pins_per_row == 11:
        positions = range(2 + config["pin_nr_offset"], config["row_pins"] + 1 + config["pin_nr_offset"], 3)
    else:
        raise Exception(
            f"weird pins per row: {pins_per_row} (row_pins: "
            f"{config['row_pins']}, {pins}x{rows}"
        )
    return {
        pin: Vector2D(
            pin_one.x + column_direction.x * (pin - 1) * config["pin_column_offset"],
            pin_one.y + column_direction.y * (pin - 1) * config["pin_column_offset"],
        )
        for pin in positions
    }


def build_pins(mod, config, pins, rows, row_direction, column_direction):

    pin_args = dict(
        type=Pad.TYPE_THT,
        size=config["pin_plating_diameter"],
        drill=config["pin_hole_diameter"],
        layers=Pad.LAYERS_THT,
        round_radius_handler=global_config.roundrect_radius_handler,
    )

    first = None
    pins_per_row = pins / len(rows)
    for row in rows.lower():
        positions = build_positions(
            config, pins_per_row, row, row_direction, column_direction
        )

        for pin, pos in positions.items():
            number = config["name_pattern"].format(**locals())
            if first is None:
                # no marked pin yet
                shape = Pad.SHAPE_ROUNDRECT
                first = pos
            else:
                shape = Pad.SHAPE_CIRCLE
            mod.append(Pad(at=pos, number=number, shape=shape, **pin_args))

    # return the position of the first pin to place markers correctly
    return first


def build_din41612_connector_horizontal(generator_name, mod, series, direction, pins, rows, config):

    center = Vector2D(config["pin_column_offset"] * ((config["row_pins"] + config["pin_nr_offset"] * 2) / 2 - 0.5), 0)
    mounting = Vector2D(center.x - config["mounting_width"] / 2, -config["a1_mounting"])
    # place mounting holes
    mod.append(Pad(at=mounting, **mounting_args))
    mod.append(Pad(at=mirror_x(mounting, center), **mounting_args))

    pos1 = build_pins(
        mod,
        config,
        pins,
        rows,
        row_direction=Vector2D(0, 1),
        column_direction=Vector2D(1, 0),
    )

    # silk screen reference
    mod.append(
        Property(
            name=Property.REFERENCE,
            text="REF**",
            at=mounting
            + (0, -config["mounting_housing_back"] + config["silk_reference_offset"]),
            rotation=0,
            layer="F.SilkS",
        )
    )
    mod.append(
        Text(
            at=Vector2D(center.x, mounting.y),
            text=fab_reference_args["text"],
            layer=fab_reference_args["layer"],
            thickness=fab_reference_args["thickness"],
            size=fab_reference_args["size"],
        )
    )
    mod.append(
        Property(
            name=Property.VALUE,
            text=config["footprint_name"],
            at=Vector2D(center.x, config["last_row_pos"] + config["pin_row_offset"]),
            layer="F.Fab",
        )
    )

    config["a1_housing_front"] = (
        config["a1_mounting"] + config["mounting_housing_front"]
    )
    config["a1_housing_back"] = config["a1_mounting"] + config["mounting_housing_back"]

    hole_part_depth = 6
    hole_part_width = 5
    hole_part_inset = 1
    # draw outline
    mod.append(
        PolygonLine(
            shape=[
                Vector2D(
                    center.x - config["connector_width"] / 2,
                    -config["a1_housing_front"],
                ),
                Vector2D(
                    center.x - config["connector_width"] / 2,
                    -config["a1_housing_front"] + hole_part_depth,
                ),
                Vector2D(
                    center.x - config["housing_width"] / 2,
                    -config["a1_housing_front"] + hole_part_depth,
                ),
                Vector2D(
                    center.x - config["housing_width"] / 2, -config["a1_housing_back"]
                ),
                Vector2D(
                    center.x - config["housing_width"] / 2 + hole_part_width,
                    -config["a1_housing_back"],
                ),
                Vector2D(
                    center.x - config["housing_width"] / 2 + hole_part_width,
                    -config["a1_housing_back"] - hole_part_inset,
                ),
                Vector2D(
                    center.x + config["housing_width"] / 2 - hole_part_width,
                    -config["a1_housing_back"] - hole_part_inset,
                ),
                Vector2D(
                    center.x + config["housing_width"] / 2 - hole_part_width,
                    -config["a1_housing_back"],
                ),
                Vector2D(
                    center.x + config["housing_width"] / 2, -config["a1_housing_back"]
                ),
                Vector2D(
                    center.x + config["housing_width"] / 2,
                    -config["a1_housing_front"] + hole_part_depth,
                ),
                Vector2D(
                    center.x + config["connector_width"] / 2,
                    -config["a1_housing_front"] + hole_part_depth,
                ),
                Vector2D(
                    center.x + config["connector_width"] / 2,
                    -config["a1_housing_front"],
                ),
                Vector2D(
                    center.x - config["connector_width"] / 2,
                    -config["a1_housing_front"],
                ),
            ],
            layer="F.Fab",
            width=0.1,
        )
    )

    # add silk screen
    sd = 0.2 + 0.06
    silk_points = [
        Vector2D(
            center.x - config["housing_width"] / 2 - sd,
            -config["a1_edge"] + config["edge_offset"],
        ),
        Vector2D(
            center.x - config["housing_width"] / 2 - sd, -config["a1_housing_back"] + sd
        ),
        Vector2D(
            center.x - config["housing_width"] / 2 + hole_part_width + sd,
            -config["a1_housing_back"] + sd,
        ),
        Vector2D(
            center.x - config["housing_width"] / 2 + hole_part_width + sd,
            -config["a1_housing_back"] - hole_part_inset + sd,
        ),
    ]
    line_point = Vector2D(
        center.x - config["housing_width"] / 2 + hole_part_width + sd,
        -config["a1_housing_back"] - hole_part_inset + sd,
    )

    keepout_radius = config["pin_plating_diameter"] + (0.2 + 0.12) * 2
    positions = list(
        build_positions(
            config,
            pins_per_row=pins / len(rows),
            row=rows[0],
            row_direction=Vector2D(0, 1),
            column_direction=Vector2D(1, 0),
        ).values()
    )
    keepouts = addKeepoutRect(
        positions[0].x, positions[0].y, keepout_radius, keepout_radius
    )
    for pos in positions[1:]:
        keepouts += addKeepoutRound(pos.x, pos.y, keepout_radius, keepout_radius)

    mod.append(PolygonLine(shape=silk_points, layer="F.SilkS", width=0.12))
    mod.append(
        PolygonLine(
            shape=list(map(lambda x: mirror_x(x, center), silk_points)),
            layer="F.SilkS",
            width=0.12,
        )
    )
    addHLineWithKeepout(
        mod,
        line_point.x,
        mirror_x(line_point, center).x,
        line_point.y,
        layer="F.SilkS",
        width=0.12,
        keepouts=keepouts,
    )

    # add arrow pointing at a1
    arrow_points = map(
        lambda x: pos1 + x,
        (
            Vector2D(-0.2 - 0.12 - config["pin_plating_diameter"] / 2, 0),
            Vector2D(-0.8 - 0.12 - config["pin_plating_diameter"] / 2, -0.3),
            Vector2D(-0.8 - 0.12 - config["pin_plating_diameter"] / 2, 0.3),
            Vector2D(-0.2 - 0.12 - config["pin_plating_diameter"] / 2, 0),
        ),
    )
    mod.append(PolygonLine(shape=list(arrow_points), layer="F.SilkS", width=0.12))
    # add a1 marker on fab layer
    marker_points = map(
        lambda x: pos1 + x,
        (
            Vector2D(0, -config["a1_housing_back"] - hole_part_inset - 0.2),
            Vector2D(-0.5, -config["a1_housing_back"] - hole_part_inset - 0.9),
            Vector2D(0.5, -config["a1_housing_back"] - hole_part_inset - 0.9),
            Vector2D(0, -config["a1_housing_back"] - hole_part_inset - 0.2),
        ),
    )
    mod.append(PolygonLine(shape=list(marker_points), layer="F.Fab", width=0.1))

    # add courtyard
    cy = 0.5
    mod.append(
        PolygonLine(
            shape=list(
                map(
                    round_courtyard,
                    [
                        Vector2D(
                            center.x - config["housing_width"] / 2 - cy,
                            -config["a1_housing_front"] - cy,
                        ),
                        Vector2D(
                            center.x - config["housing_width"] / 2 - cy,
                            -config["a1_housing_back"] + cy,
                        ),
                        Vector2D(
                            center.x
                            - (config["row_pins"] - 1) / 2 * config["pin_column_offset"]
                            - config["pin_plating_diameter"] / 2
                            - cy,
                            -config["a1_housing_back"] + cy,
                        ),
                        Vector2D(
                            center.x
                            - (config["row_pins"] - 1) / 2 * config["pin_column_offset"]
                            - config["pin_plating_diameter"] / 2
                            - cy,
                            config["last_row_pos"]
                            + config["pin_plating_diameter"] / 2
                            + cy,
                        ),
                        Vector2D(
                            center.x
                            + (config["row_pins"] - 1) / 2 * config["pin_column_offset"]
                            + config["pin_plating_diameter"] / 2
                            + cy,
                            config["last_row_pos"]
                            + config["pin_plating_diameter"] / 2
                            + cy,
                        ),
                        Vector2D(
                            center.x
                            + (config["row_pins"] - 1) / 2 * config["pin_column_offset"]
                            + config["pin_plating_diameter"] / 2
                            + cy,
                            -config["a1_housing_back"] + cy,
                        ),
                        Vector2D(
                            center.x + config["housing_width"] / 2 + cy,
                            -config["a1_housing_back"] + cy,
                        ),
                        Vector2D(
                            center.x + config["housing_width"] / 2 + cy,
                            -config["a1_housing_front"] - cy,
                        ),
                        Vector2D(
                            center.x - config["housing_width"] / 2 - cy,
                            -config["a1_housing_front"] - cy,
                        ),
                    ],
                )
            ),
            layer="F.CrtYd",
            width=0.05,
        )
    )
    # mark board edge
    mod.append(
        PolygonLine(
            shape=[
                Vector2D(center.x - config["housing_width"] / 2, -config["a1_edge"]),
                Vector2D(center.x + config["housing_width"] / 2, -config["a1_edge"]),
            ],
            layer="Dwgs.User",
            width=0.08,
        )
    )
    mod.append(
        Text(
            text="Board edge",
            at=Vector2D(center.x, -config["a1_edge"] - 2),
            layer="Cmts.User",
            size=(0.7, 0.7),
            thickness=0.1,
        )
    )
    arrow_args = dict(
        width=0.1,
        layer="Cmts.User",
    )
    mod.append(
        PolygonLine(
            shape=[
                Vector2D(center.x - 0.2, -config["a1_edge"] - 0.6),
                Vector2D(center.x, -config["a1_edge"] - 0.1),
                Vector2D(center.x + 0.2, -config["a1_edge"] - 0.6),
            ],
            **arrow_args,
        )
    )
    mod.append(
        PolygonLine(
            shape=[
                Vector2D(center.x, -config["a1_edge"] - 0.1),
                Vector2D(center.x, -config["a1_edge"] - 1.4),
            ],
            **arrow_args,
        )
    )
    # draw line for special contacts marking
    if series in {"M", "M-invers"}:
        special_contacts_nr_half = int(((32 - config["row_pins"]) / 3) / 2)
        for sc in range(special_contacts_nr_half):
            # left
            mod.append(
                PolygonLine(
                    shape=[
                        Vector2D(center.x - 36.83 + 7.62 * sc, 0),
                        Vector2D(center.x - 36.83 + 7.62 * sc, -1),
                    ],
                    **arrow_args,
                )
            )
            # right
            mod.append(
                PolygonLine(
                    shape=[
                        Vector2D(center.x + 36.83 - 7.62 * sc, 0),
                        Vector2D(center.x + 36.83 - 7.62 * sc, -1),
                    ],
                    **arrow_args,
                )
            )


def build_din41612_connector_vertical(generator_name, mod, series, direction, pins, rows, config):
    all_rows = "zabcde"
    min_row_index = all_rows.find(config["series_rows"][0])
    max_row_index = all_rows.find(config["series_rows"][-1])
    total_rows = max_row_index - min_row_index
    rows_width = (total_rows) * config["pin_column_offset"]
    center_x = rows_width / 2
    if "z" in config["series_rows"]:
        center_x -= config["pin_column_offset"]
    center = Vector2D(
        center_x, config["pin_column_offset"] * ((config["row_pins"] + config["pin_nr_offset"] * 2) / 2 - 0.5)
    )
    pos1 = build_pins(
        mod,
        config,
        pins,
        rows,
        row_direction=Vector2D(1, 0),
        column_direction=Vector2D(0, 1),
    )
    mounting = Vector2D(config["a1_mounting"], center.y - config["mounting_width"] / 2)
    mod.append(Pad(at=mounting, **mounting_args))
    mod.append(Pad(at=mirror_y(mounting, center), **mounting_args))

    # references
    mod.append(
        Property(
            name=Property.REFERENCE,
            text="REF**",
            at=center
            - (0, config["housing_width"] / 2 + config["silk_reference_offset"]),
            rotation=0,
            layer="F.SilkS",
        )
    )
    mod.append(
        Text(
            at=center,
            text=fab_reference_args["text"],
            layer=fab_reference_args["layer"],
            thickness=fab_reference_args["thickness"],
            size=fab_reference_args["size"],
        )
    )
    mod.append(
        Property(
            name=Property.VALUE,
            text=config["footprint_name"],
            at=center
            + (0, config["housing_width"] / 2 + config["silk_reference_offset"]),
            layer="F.Fab",
        )
    )

    # connector outline
    conn_left = center.x - config["connector_height"] / 2
    conn_right = center.x + config["connector_height"] / 2
    conn_top = center.y - config["connector_width"] / 2
    conn_bottom = center.y + config["connector_width"] / 2
    conn_outline = [
        Vector2D(conn_left, conn_top),
        Vector2D(conn_right - config["nodge_height"], conn_top),
        Vector2D(conn_right - config["nodge_height"], conn_top + config["nodge_width"]),
        Vector2D(conn_right, conn_top + config["nodge_width"]),
        Vector2D(conn_right, conn_bottom - config["nodge_width"]),
        Vector2D(
            conn_right - config["nodge_height"], conn_bottom - config["nodge_width"]
        ),
        Vector2D(conn_right - config["nodge_height"], conn_bottom),
        Vector2D(conn_left, conn_bottom),
        Vector2D(conn_left, conn_top),
    ]
    mod.append(PolygonLine(shape=conn_outline, layer="F.Fab", width=0.1))
    if config["gender"] == "male":
        for mul in (1, -1):
            height = center.y + mul * config["connector_outer_width"] / 2
            inner_height = center.y + mul * config["connector_width"] / 2
            mod.append(
                PolygonLine(
                    shape=(
                        Vector2D(center.x - config["housing_height"] / 2, height),
                        Vector2D(mounting.x - 3, height),
                        Vector2D(mounting.x - 3, inner_height),
                    ),
                    layer="F.Fab",
                    width=0.1,
                )
            )
            mod.append(
                PolygonLine(
                    shape=(
                        Vector2D(conn_right - config["nodge_height"], inner_height),
                        Vector2D(mounting.x + 3, inner_height),
                        Vector2D(mounting.x + 3, height),
                        Vector2D(center.x + config["housing_height"] / 2, height),
                    ),
                    layer="F.Fab",
                    width=0.1,
                )
            )

    # housing
    def housing(expand):
        return [
            Vector2D(
                center.x - config["housing_height"] / 2 - expand,
                center.y - config["housing_width"] / 2 - expand,
            ),
            Vector2D(
                center.x + config["housing_height"] / 2 + expand,
                center.y - config["housing_width"] / 2 - expand,
            ),
            Vector2D(
                center.x + config["housing_height"] / 2 + expand,
                center.y + config["housing_width"] / 2 + expand,
            ),
            Vector2D(
                center.x - config["housing_height"] / 2 - expand,
                center.y + config["housing_width"] / 2 + expand,
            ),
            Vector2D(
                center.x - config["housing_height"] / 2 - expand,
                center.y - config["housing_width"] / 2 - expand,
            ),
        ]

    mod.append(PolygonLine(shape=housing(0), layer="F.Fab", width=0.1))
    mod.append(PolygonLine(shape=housing(0.11), layer="F.SilkS", width=0.12))
    mod.append(
        PolygonLine(
            shape=list(map(round_courtyard, housing(0.5))),
            layer="F.CrtYd",
            width=0.05,
        )
    )

    # add arrow pointing at a1
    edge_position = Vector2D(center.x - config["housing_height"] / 2, pos1.y)
    arrow_points = map(
        lambda x: edge_position + x,
        (
            Vector2D(-0.3, 0),
            Vector2D(-0.3 - 0.68, -0.3),
            Vector2D(-0.3 - 0.68, 0.3),
            Vector2D(-0.3, 0),
        ),
    )
    mod.append(PolygonLine(shape=list(arrow_points), layer="F.SilkS", width=0.12))
    # do similar on the fab layer
    arrow_points = map(
        lambda x: edge_position + x,
        (
            Vector2D(0, -0.5),
            Vector2D(0.7, 0),
            Vector2D(0, 0.5),
        ),
    )
    mod.append(PolygonLine(shape=list(arrow_points), layer="F.Fab", width=0.1))

    keepout_radius = config["pin_plating_diameter"] + 0.4
    positions = list(
        build_positions(
            config,
            pins_per_row=pins / len(rows),
            row=rows[0],
            row_direction=Vector2D(1, 0),
            column_direction=Vector2D(0, 1),
        ).values()
    )
    keepouts = addKeepoutRect(
        positions[0].x, positions[0].y, keepout_radius, keepout_radius
    )
    for pos in positions[1:]:
        keepouts += addKeepoutRound(pos.x, pos.y, keepout_radius, keepout_radius)
    for row in rows[1:]:
        positions = build_positions(
            config,
            pins_per_row=pins / len(rows),
            row=row,
            row_direction=Vector2D(1, 0),
            column_direction=Vector2D(0, 1),
        )
        for pos in positions.values():
            keepouts += addKeepoutRound(pos.x, pos.y, keepout_radius, keepout_radius)
    # Draw Special contacts hole
    if series in {"M", "M-invers"}:
        special_contacts_nr_half = int(((32 - config["row_pins"]) / 3) / 2)
        for sc in range(special_contacts_nr_half):
            sc_pos = Vector2D(center.x, center.y + 36.83 - 7.62 * sc)
            sc_args = dict(
                type=Pad.TYPE_NPTH,
                shape=Pad.SHAPE_CIRCLE,
                size=6,
                drill=6,
                layers=Pad.LAYERS_NPTH,
            )
            mod.append(Pad(at=sc_pos, **sc_args))
            mod.append(Pad(at=mirror_y(sc_pos, center), **sc_args))
    # Draw Special contacts markings
    if series == "M-flat":
        markingLine_args = dict(
            width=0.1,
            layer="Cmts.User",
        )
        special_contacts_nr_half = int(((32 - config["row_pins"]) / 3) / 2)
        for sc in range(special_contacts_nr_half):
            # ToDo: Makrings

            # top
            mod.append(
                PolygonLine(
                    shape=[
                        Vector2D(center.x + .5, center.y - 36.83 + 7.62 * sc),
                        Vector2D(center.x - .5, center.y - 36.83 + 7.62 * sc),
                    ],
                    **markingLine_args,
                )
            )
            mod.append(
                PolygonLine(
                    shape=[
                        Vector2D(center.x, center.y - 36.83 + 7.62 * sc + .5),
                        Vector2D(center.x, center.y - 36.83 + 7.62 * sc - .5),
                    ],
                    **markingLine_args,
                )
            )
            # bottom
            mod.append(
                PolygonLine(
                    shape=[
                        Vector2D(center.x + .5, center.y + 36.83 - 7.62 * sc),
                        Vector2D(center.x - .5, center.y + 36.83 - 7.62 * sc),
                    ],
                    **markingLine_args,
                )
            )
            mod.append(
                PolygonLine(
                    shape=[
                        Vector2D(center.x, center.y + 36.83 - 7.62 * sc + .5),
                        Vector2D(center.x, center.y + 36.83 - 7.62 * sc - .5),
                    ],
                    **markingLine_args,
                )
            )
    # highlight connector shape on silk
    highlight_expand = 0
    he = highlight_expand
    conn_highlight = GeomPolygon(
        shape=[
            Vector2D(conn_left - he, conn_top - he),
            Vector2D(conn_right - config["nodge_height"] + he, conn_top - he),
            Vector2D(
                conn_right - config["nodge_height"] + he,
                conn_top + config["nodge_width"] - he,
            ),
            Vector2D(conn_right + he, conn_top + config["nodge_width"] - he),
            Vector2D(conn_right + he, conn_bottom - config["nodge_width"] + he),
            Vector2D(
                conn_right - config["nodge_height"] + he,
                conn_bottom - config["nodge_width"] + he,
            ),
            Vector2D(conn_right - config["nodge_height"] + he, conn_bottom + he),
            Vector2D(conn_left - he, conn_bottom + he),
            Vector2D(conn_left - he, conn_top - he),
        ]
    )

    mod += makeNodesWithKeepout(
        conn_highlight, layer="F.SilkS", width=0.12, keepouts=keepouts
    )


def build_din41612_connector(generator_name, series, direction, pins, rows, extra_args={}):
    width = "full"
    try:
        if series in {"M", "M-flat", "M-invers"} and pins == 78:
            width = "m1"
            safe_series = series
        elif series in {"M", "M-flat", "M-invers"} and pins == 60:
            width = "m2"
            safe_series = series
        elif series in {"M", "M-flat", "M-invers"} and pins == 42:
            width = "m3"
            safe_series = series
        elif series in {"M", "M-flat", "M-invers"} and pins == 24:
            width = "m4"
            safe_series = series
        elif series in {"M", "M-flat", "M-invers"} and pins == 6:
            width = "m5"
            safe_series = series
        elif series.split("/")[1] == "2":
            width = "half"
            safe_series = series.split("/")[0] + "2"
        elif series.split("/")[1] == "3":
            width = "third"
            safe_series = series.split("/")[0] + "3"
    except:
        safe_series = series

    config = dimensions.copy()
    config.update(config[direction])
    config.update(config[direction][width])
    series_config = config["series"][series.split("/")[0]]
    config.update(series_config)
    if direction in series_config:
        config.update(series_config[direction])
    config.update(extra_args)

    used_rows = config["series_rows"].find(rows[-1])
    config["last_row_pos"] = used_rows * config["pin_row_offset"]

    # generate base settings
    pins_per_row = pins // len(rows)
    extra_fp_name = ""
    if config.get("extra_desc") == "rows":
        extra_fp_name += f"_Rows{rows.upper()}"
    elif config.get("extra_desc") != None:
        extra_fp_name = config.get("extra_desc")
    if config.get("gender_reverse") == True:
        if config["gender"] == "male":
            config["gender"] = "female"
        elif config["gender"] == "female":
            config["gender"] = "male"
    gender = string.capwords(config["gender"])
    footprint_name = (
        f"DIN41612_{safe_series}_{len(rows)}x{pins_per_row}"
        f"{extra_fp_name}_{gender}_{direction}_THT"
    )
    config["footprint_name"] = footprint_name
    mod = Footprint(footprint_name, FootprintType.THT)
    description_rows = f"{len(rows)} rows" if len(rows) > 1 else "1 row"
    mod.setDescription(
        f"DIN41612 connector, type {series}, {direction}, "
        f"{description_rows} "
        f"{config['row_pins']} pins wide, "
        f"{' '.join(datasheets)}"
    )
    mod.setTags(f"DIN 41612 IEC 60603 {series}")
    model3d_path_prefix = global_config.model_3d_prefix
    model3d_suffix = global_config.model_3d_suffix
    mod.append(
        Model(filename=f"{model3d_path_prefix}{lib_name}.3dshapes/{footprint_name}{model3d_suffix}")
    )

    if direction == "Horizontal":
        build_din41612_connector_horizontal(generator_name, mod, series, direction, pins, rows, config)
    else:
        build_din41612_connector_vertical(generator_name, mod, series, direction, pins, rows, config)

    write_footprint(mod, lib_name, generator_name)
    return mod


connectors = {
    "B": [(64, "ab"), (32, "a"), (32, "ab")],
    "B/2": [(32, "ab"), (16, "ab")],
    "B/3": [(20, "ab"), (10, "ab")],
    "C": [(96, "abc"), (64, "ac"), (32, "ac"), (32, "a"), (48, "abc")],
    "C/2": [(32, "ac"), (48, "abc")],
    "C/3": [(20, "ac"), (30, "abc")],
    #        'CD': [ (128, 'abcd') ],
    "D": [(32, "ac"), (16, "ac")],
    "E": [(32, "ae"), (32, "ac", dict(extra_desc="rows")), (48, "ace")],
    #        'E160': [ (160, 'abcde') ],
    #        'F_flat': [ (32, 'zb') (32, 'zd'), (48, 'zbd') ],
    "F": [(32, "zd", dict(extra_desc="rows")), (32, "zb"), (48, "zbd")],
    # "G": [(64, "?ac")],
    #        'H11': [ (11, 'e') ],
    # "H": [(15, "?ac")],
    "M": [(78, "abc", dict(extra_desc="+2")), (60, "abc", dict(extra_desc="+4")), (42, "abc", dict(extra_desc="+6")), (24, "abc", dict(extra_desc="+8"))],
    "M-flat": [(78, "abc", dict(extra_desc="+2")), (60, "abc", dict(extra_desc="+4")), (42, "abc", dict(extra_desc="+6")), (24, "abc", dict(extra_desc="+8"))],
    "M-invers": [(78, "abc", dict(extra_desc="+2")), (60, "abc", dict(extra_desc="+4")), (42, "abc", dict(extra_desc="+6")), (24, "abc", dict(extra_desc="+8")), (6, "abc", dict(extra_desc="+10"))],
    "Q": [(64, "ab")],
    "Q/2": [(32, "ab")],
    "Q/3": [(20, "ab")],
    "R": [(64, "ac"), (96, "abc"), (48, "abc"), (32, "ac"), (32, "a")],
    "R/2": [(48, "abc"), (32, "ac")],
    "R/3": [(30, "abc"), (20, "ac")],
    # "S": [(32, "?ac")],
    # "T": [(32, "?ac"), (48, "?ac")],
    # "U": [(32, "?ac"), (48, "?ac")],
    # "V": [(64, "?ac")],
    # "W": [(96, "?abc")],
}

# TODO: G RD T TE H11 H15 H7/F24 U V W
# TODO: check all manufacturer special variants
# make fab shape depend on mounting position not on front of connector


def generate_all(generator_name: str) -> int:
    num_fps_generated = 0
    for direction in ("Horizontal", "Vertical"):
        for series, variants in connectors.items():
            if direction in (dimensions["series"])[series.split("/")[0]]["directions"]:
                for v in variants:
                    pins = v[0]
                    rows = v[1]
                    if len(v) > 2:
                        args = v[2]
                    else:
                        args = {}
                    build_din41612_connector(
                        generator_name,
                        series=series,
                        direction=direction,
                        pins=pins,
                        rows=rows,
                        extra_args=args,
                    )
                    num_fps_generated += 1
    return num_fps_generated
