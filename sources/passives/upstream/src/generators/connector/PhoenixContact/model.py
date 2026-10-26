#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This is derived from a cadquery script for generating PDIP models in X3D format
#
# from https://bitbucket.org/hyOzd/freecad-macros
# author hyOzd
#
# Dimensions are from Microchips Packaging Specification document:
# DS00000049BY. Body drawing is the same as QFP generator#
#
## Requirements
## CadQuery 2.1 commit e00ac83f98354b9d55e6c57b9bb471cdf73d0e96 or newer
## https://github.com/CadQuery/cadquery
#
## To run the script just do: ./generator.py --output_dir [output_directory]
## e.g. ./generator.py --output_dir /tmp
#
# * These are cadquery tools to export                                       *
# * generated models in STEP & VRML format.                                  *
# *                                                                          *
# * cadquery script for generating QFP/SOIC/SSOP/TSSOP models in STEP AP214  *
# * Copyright (c) 2015                                                       *
# *     Maurice https://launchpad.net/~easyw                                 *
# * Copyright (c) 2022                                                       *
# *     Update 2022                                                          *
# *     jmwright (https://github.com/jmwright)                               *
# *     Work sponsored by KiCAD Services Corporation                         *
# *          (https://www.kipro-pcb.com/)                                    *
# *                                                                          *
# * All trademarks within this guide belong to their legitimate owners.      *
# *                                                                          *
# *   This program is free software; you can redistribute it and/or modify   *
# *   it under the terms of the GNU General Public License (GPL)             *
# *   as published by the Free Software Foundation; either version 2 of      *
# *   the License, or (at your option) any later version.                    *
# *   for detail see the LICENCE text file.                                  *
# *                                                                          *
# *   This program is distributed in the hope that it will be useful,        *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of         *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          *
# *   GNU Library General Public License for more details.                   *
# *                                                                          *
# *   You should have received a copy of the GNU Library General Public      *
# *   License along with this program; if not, write to the Free Software    *
# *   Foundation, Inc.,                                                      *
# *   51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA           *
# *                                                                          *
# ****************************************************************************

__title__ = "make Altech connector 3D models exported to STEP and VRML"
__author__ = "scripts: Stefan; models: see cq_model files; update: jmwright"
__Comment__ = """This generator loads cadquery model scripts and generates step/wrl files for the official kicad library."""

___ver___ = "2.0.0"

from generators.tools.model import export_tools
from generators.tools.spec.legacy_model_spec import LegacyModelSpec

from .cq_models.conn_phoenix_mc import generate_part as generate_part_mc
from .cq_models.conn_phoenix_mc import seriesParams as series_params_mc
from .cq_models.conn_phoenix_mkds import (
    make_case_MKDS_1_5_10_5_08,
    make_pins_MKDS_1_5_10_5_08,
)
from .cq_models.conn_phoenix_mstb import generate_part as generate_part_mstb
from .cq_models.conn_phoenix_mstb import seriesParams as series_params_mstb


def create_models(spec: LegacyModelSpec, generator_name: str) -> int:
    """Create the 3D models.

    Args:
        spec: The spec of the part(s) to generate.
        generator_name: The name of the generator.

    Returns:
        The number of models generated.
    """
    # Convert the number of pins to an array of one if there is only one pin
    num_pins_list = (
        [spec.spec["num_pins"]]
        if type(spec.spec["num_pins"]).__name__ == "int"
        else spec.spec["num_pins"]
    )
    for num_pins in num_pins_list:
        insert = None
        mount_screw = None

        if spec.id == "AK300" or spec.id == "MKDS_1_5":
            # Make the parts of the model
            body = make_case_MKDS_1_5_10_5_08(spec.spec, num_pins)
            pins = make_pins_MKDS_1_5_10_5_08(spec.spec, num_pins)
            body = body.rotate((0, 0, 0), (0, 0, 1), spec.spec["rotation"])
            pins = pins.rotate((0, 0, 0), (0, 0, 1), spec.spec["rotation"])

        elif spec.id.startswith("MC"):

            (pins, body, insert, mount_screw, _, _) = generate_part_mc(
                spec.spec, num_pins
            )

            body = body.rotate((0, 0, 0), (0, 0, 1), spec.spec["rotation"]).translate(
                (0, -3.0, 3.0)
            )
            pins = pins.rotate((0, 0, 0), (0, 0, 1), spec.spec["rotation"])
            if not spec.spec["angled"]:
                pins = pins.translate((0, 0, 3.0))
            if insert != None:
                insert = insert.rotate(
                    (0, 0, 0), (0, 0, 1), spec.spec["rotation"]
                ).translate((0, -3.0, 3.0))
            if mount_screw != None:
                if spec.spec["angled"]:
                    mount_screw = mount_screw.rotate(
                        (0, 0, 0), (1, 0, 0), -90
                    ).translate(
                        (
                            0,
                            -series_params_mc.mount_screw_head_height
                            - series_params_mc.body_height / 2.0,
                            series_params_mc.thread_insert_r,
                        )
                    )
                else:
                    mount_screw = mount_screw.rotate(
                        (1, 0, 0), (0, 0, 0), 180
                    ).translate(
                        (
                            0,
                            series_params_mc.mount_screw_head_height
                            - series_params_mc.body_height / 2.0,
                            series_params_mc.body_height
                            + series_params_mc.mount_screw_head_height,
                        )
                    )

        elif spec.id.startswith("MSTB") or spec.id.startswith("GMSTB"):

            (pins, body, insert, mount_screw, plug, plug_screws) = generate_part_mstb(
                spec.spec, num_pins
            )
            # print(pins)
            # Rotate and translate parts so they end up in the correct location/orientation
            body = body.rotate((0, 0, 0), (0, 0, 1), spec.spec["rotation"])
            if (
                spec.id.startswith("MSTB") or spec.id.startswith("GMSTB")
            ) and spec.spec["angled"]:
                body = body.translate((0, -3.0, 3.0))
            pins = pins.rotate((0, 0, 0), (0, 0, 1), spec.spec["rotation"])
            if insert != None and spec.spec["angled"]:
                insert = insert.rotate(
                    (0, 0, 0), (0, 0, 1), spec.spec["rotation"]
                ).translate((0, -3.0, 3.0))
            if mount_screw != None:
                if spec.spec["angled"]:
                    mount_screw = mount_screw.rotate(
                        (1, 0, 0), (0, 0, 0), 90
                    ).translate(
                        (
                            0,
                            -series_params_mstb.mount_screw_head_height
                            - series_params_mstb.body_height / 2.0,
                            series_params_mstb.thread_r / 2.0,
                        )
                    )
                else:
                    mount_screw = mount_screw.rotate(
                        (1, 0, 0), (0, 0, 0), 180
                    ).translate(
                        (
                            0,
                            0,
                            series_params_mstb.body_height
                            - series_params_mstb.mount_screw_head_height,
                        )
                    )

        # Assemble the filename
        file_name = spec.spec["file_name"].format(
            pin_num=num_pins,
            pad_pin_num="0" + str(num_pins) if num_pins < 10 else str(num_pins),
            row_num=1,
            pitch=spec.spec["pin_pitch"],
            comma_pitch=str(spec.spec["pin_pitch"]).replace(".", ","),
            pad_pitch=(
                spec.spec["pin_pitch"]
                if len(str(spec.spec["pin_pitch"]).split(".")[1]) == 2
                else str(spec.spec["pin_pitch"]) + "0"
            ),
            prefix=spec.spec["series_name"].split("-")[0],
            midfix=spec.spec["series_name"].split("-")[1],
            orientation=(
                "Horizontal"
                if "angled" in spec.spec and spec.spec["angled"] == True
                else "Vertical"
            ),
            flanged=(
                "_ThreadedFlange"
                if "flanged" in spec.spec and spec.spec["flanged"] == True
                else ""
            ),
            mount_hole=(
                "_MountHole"
                if "mount_hole" in spec.spec and spec.spec["mount_hole"] == True
                else ""
            ),
        )

        parts = export_tools.AssemblyParts(
            [
                (body, spec.spec["body_color_key"]),
                (pins, spec.spec["pin_color_key"]),
            ]
        )

        if insert is not None:
            parts.append(insert, spec.spec["insert_color_key"])
        if mount_screw is not None:
            parts.append(mount_screw, spec.spec["screw_color_key"])

        export_tools.export(
            generator_name=generator_name,
            lib_name=spec.spec["destination_dir"],
            model_name=file_name,
            parts=parts,
        )
    return len(num_pins_list)
