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

from kilibs.geom import GeomRectangle
from KicadModTree import *  # NOQA
from KicadModTree.nodes.base.Pad import Pad  # NOQA
from generators.tools.footprint.declarative_def_tools import common_metadata
from kilibs.config import global_config as GC
from generators.tools.footprint.footprint_text_fields import addTextFields
from generators.tools.footprint.save_footprint import write_footprint
import yaml


class SmdShieldProperties:
    """
    Class that represents a consistent view of the properties of a SMD shielding
    can. Probably initialized from a YAML file.
    """

    name: str
    metadata: common_metadata.CommonMetadata
    part_size: Vector2D
    pad_width: float

    x_pad_positions: list[float]
    """List of x coordinates of the pads edges"""
    y_pad_positions: list[float]
    """List of y coordinates of the pads edges"""

    def __init__(self, name: str, spec: dict):
        self.name = name
        self.metadata = common_metadata.CommonMetadata(spec)

        self.part_size = Vector2D(
            spec['x_part_size'],
            spec['y_part_size']
        )

        self.pad_width = spec['pads_width']

        # do some pre calculations
        # TODO: when mirror=False, array has to have even number of array elements
        self.x_pad_positions = self._calculate_pad_spacer(
            spec["x_pad_spacer"], spec.get("x_pad_mirror", True)
        )
        self.y_pad_positions = self._calculate_pad_spacer(
            spec["y_pad_spacer"], spec.get("y_pad_mirror", True)
        )


    def _calculate_pad_spacer(self, pad_spacer: list[float], mirror_spacer: bool):
        """
        The pad spaces are the coordinates of the pads edges in
        the x or y direction. The mirror_spacer parameter is used
        to mirror the pad spacers to the other side of the part.

        E.g. everything on the left is from the mirroring:

        |  |      |  |     |   o   |     |  |      |  |
        XXXX      XXXX     XXXXXXXXX     XXXX      XXXX
        X                                             X
        """
        pad_spacer_pos = []

        if mirror_spacer:
            for spacer in reversed(pad_spacer):
                pad_spacer_pos.append(spacer * -1)

        pad_spacer_pos += pad_spacer

        return pad_spacer_pos


def create_smd_shielding(generator_name: str, global_config: GC.GlobalConfig, shield_properties: SmdShieldProperties, **kwargs):
    lib_name = "RF_Shielding"
    kicad_mod = Footprint(shield_properties.name, FootprintType.SMD)

    description = shield_properties.metadata.description
    if shield_properties.metadata.datasheet:
        description += ", " + shield_properties.metadata.datasheet

    kicad_mod.description = description
    kicad_mod.tags = 'Shielding Cabinet'

    # The outer edges of the pads
    pad_outer_rect = GeomRectangle(
        start=Vector2D(min(shield_properties.x_pad_positions), min(shield_properties.y_pad_positions)),
        end=Vector2D(max(shield_properties.x_pad_positions), max(shield_properties.y_pad_positions)),
    )

    # Centerline of the pads
    pad_center_rect = pad_outer_rect.inflated(-shield_properties.pad_width / 2.0)

    courtyard_offset = global_config.get_courtyard_offset(
        GC.GlobalConfig.CourtyardType.DEFAULT
    )

    body_rect = GeomRectangle(center=Vector2D(0, 0), size=shield_properties.part_size)

    courtyard_rect = pad_outer_rect.inflated(courtyard_offset).round_to_grid(
        grid=global_config.courtyard_grid, outwards=True
    )

    # set general values
    addTextFields(
        kicad_mod,
        global_config,
        body_rect.bbox(),
        courtyard_rect.bbox(),
        kicad_mod.name,
        text_y_inside_position="center",
    )

    kicad_mod.append(
        Rectangle(
            start=courtyard_rect.top_left,
            end=courtyard_rect.bottom_right,
            layer="F.CrtYd",
            width=global_config.courtyard_line_width,
        )
    )

    # create inner courtyard
    pad_width = kwargs['pads_width']

    inner_courtyard = pad_outer_rect.inflated(-pad_width - courtyard_offset).round_to_grid(
        grid=global_config.courtyard_grid, outwards=False
    )

    kicad_mod.append(
        Rectangle(
            start=inner_courtyard.top_left,
            end=inner_courtyard.bottom_right,
            layer="F.CrtYd",
            width=global_config.courtyard_line_width,
        )
    )

    # create Fabrication Layer
    kicad_mod.append(
        Rectangle(
            start=body_rect.top_left,
            end=body_rect.bottom_right,
            layer="F.Fab",
            width=global_config.fab_line_width,
        )
    )

    # all pads have this kwargs, so we only write them one
    general_kwargs = {'number': 1,
                      'type': Pad.TYPE_SMT,
                      'shape': Pad.SHAPE_RECT,
                      'layers': Pad.LAYERS_SMT,
    }
    pad_width = shield_properties.pad_width

    # create edge pads
    corner_pad_size = Vector2D(pad_width, pad_width)
    kicad_mod.append(Pad(at=pad_center_rect.top_left,
                         size=corner_pad_size, **general_kwargs))
    kicad_mod.append(Pad(at=pad_center_rect.top_right,
                         size=corner_pad_size, **general_kwargs))
    kicad_mod.append(Pad(at=pad_center_rect.bottom_left,
                         size=corner_pad_size, **general_kwargs))
    kicad_mod.append(Pad(at=pad_center_rect.bottom_right,
                         size=corner_pad_size, **general_kwargs))

    # iterate pairwise over pads
    for pad_start, pad_end in zip(shield_properties.x_pad_positions[0::2], shield_properties.x_pad_positions[1::2]):
        if pad_start == pad_outer_rect.left:
            pad_start += pad_width
        if pad_end == pad_outer_rect.right:
            pad_end -= pad_width

        kicad_mod.append(Pad(at=[(pad_start+pad_end)/2., pad_center_rect.top],
                         size=[abs(pad_start-pad_end), pad_width], **general_kwargs))
        kicad_mod.append(Pad(at=[(pad_start+pad_end)/2., pad_center_rect.bottom],
                         size=[abs(pad_start-pad_end), pad_width], **general_kwargs))

    for pad_start, pad_end in zip(shield_properties.y_pad_positions[0::2], shield_properties.y_pad_positions[1::2]):
        if pad_start == pad_outer_rect.top:
            pad_start += pad_width
        if pad_end == pad_outer_rect.bottom:
            pad_end -= pad_width

        kicad_mod.append(Pad(at=[pad_center_rect.left, (pad_start+pad_end)/2.],
                         size=[pad_width, abs(pad_start-pad_end)], **general_kwargs))
        kicad_mod.append(Pad(at=[pad_center_rect.right, (pad_start+pad_end)/2.],
                         size=[pad_width, abs(pad_start-pad_end)], **general_kwargs))

    fab_silk_offset = global_config.silk_fab_offset
    pad_silk_offset = global_config.silk_pad_offset

    # iterate pairwise over pads for silk screen
    for pad_start, pad_end in zip(shield_properties.x_pad_positions[1::2], shield_properties.x_pad_positions[2::2]):
        pad_start += pad_silk_offset
        pad_end -= pad_silk_offset

        kicad_mod.append(Line(start=[pad_start, body_rect.top - fab_silk_offset],
                                  end=[pad_end, body_rect.top - fab_silk_offset],
                                  layer='F.SilkS',
                                  width=global_config.silk_line_width))
        kicad_mod.append(Line(start=[pad_start, body_rect.bottom + fab_silk_offset],
                                  end=[pad_end, body_rect.bottom + fab_silk_offset],
                                  layer='F.SilkS',
                                  width=global_config.silk_line_width))

    for pad_start, pad_end in zip(shield_properties.y_pad_positions[1::2], shield_properties.y_pad_positions[2::2]):
        pad_start += pad_silk_offset
        pad_end -= pad_silk_offset

        # check if line has relevant length
        if pad_end - pad_start < 0.5:
            continue

        kicad_mod.append(Line(start=[body_rect.left - fab_silk_offset, pad_start],
                                  end=[body_rect.left - fab_silk_offset, pad_end],
                                  layer='F.SilkS',
                                  width=global_config.silk_line_width))
        kicad_mod.append(Line(start=[body_rect.right + fab_silk_offset, pad_start],
                                  end=[body_rect.right + fab_silk_offset, pad_end],
                                  layer='F.SilkS',
                                  width=global_config.silk_line_width))

    kicad_mod.append(Model(
        filename=global_config.model_3d_prefix
                + lib_name
                + ".3dshapes/"
                + shield_properties.name
                + global_config.model_3d_suffix))

    # write file
    write_footprint(kicad_mod, lib_name, generator_name)


def generate_for_file(generator_name, global_config, filepath) -> int:
    num_fps_generated = 0
    with open(filepath, 'r') as stream:
        yaml_parsed = yaml.safe_load(stream)
        for footprint_name, spec_data in yaml_parsed.items():
            part_props = SmdShieldProperties(footprint_name, spec_data)
            create_smd_shielding(generator_name, global_config, part_props, **spec_data)
            num_fps_generated += 1
    return num_fps_generated
