#!/usr/bin/env python3

# CadQuery script for generating rotary switch 3D models
#
# Copyright (c) 2015 Maurice https://launchpad.net/~easyw
# Copyright (c) 2022 jmwright (https://github.com/jmwright)
# Work sponsored by KiCAD Services Corporation
#      (https://www.kipro-pcb.com/)
#
# Copyright (c) 2024 Martin Sotirov <martin@libtec.org>
#
# All trademarks within this guide belong to their legitimate owners.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation; either version 2 of
# the License, or (at your option) any later version.
# For detail see the LICENCE text file.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

import logging

import cadquery as cq

from generators.tools.model import export_tools
from generators.tools.spec.legacy_model_spec import LegacyModelSpec


def create_models(spec: LegacyModelSpec, generator_name: str) -> int:
    """Create the 3D models.

    Args:
        spec: The spec of the part(s) to generate.
        generator_name: The name of the generator.

    Returns:
        The number of models generated.
    """
    # Select the model script
    if spec.spec["model_class"] == "rotary":
        from .cq_models import cq_rotary as cqm
    else:
        logging.error("No match found for the model_class")
        return 0

    # Make the parts of the model
    body = cqm.make_body(spec.spec)
    dial = cqm.make_dial(spec.spec)
    shell = cqm.make_shell(spec.spec)
    pins = cqm.make_pins(spec.spec)
    labels = cqm.make_labels(spec.spec)

    parts = export_tools.AssemblyParts(
        [
            (body, spec.spec["body_color_key"]),
            (dial, spec.spec["dial_color_key"]),
            (shell, spec.spec["shell_color_key"]),
            (pins, spec.spec["pin_color_key"]),
            (labels, spec.spec["labels_color_key"]),
        ]
    )
    parts.rotate(spec.spec.get("rotation", 0))
    parts.translate(spec.spec.get("translation", (0, 0, 0)))

    export_tools.export(
        generator_name=generator_name,
        lib_name=spec.spec["destination_dir"],
        model_name=spec.id,
        parts=parts,
    )
    return 1
