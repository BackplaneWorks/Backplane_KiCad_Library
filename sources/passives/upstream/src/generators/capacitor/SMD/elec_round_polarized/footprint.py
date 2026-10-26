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

import yaml
import math

from KicadModTree import *  # NOQA

from generators.tools.footprint.save_footprint import write_footprint
from generators.tools.spec.base_spec import BaseSpec
from generators.tools.spec.spec_generator import get_spec_file_names
from kilibs.config.global_config import GLOBAL_CONFIG


def create_footprints(spec: BaseSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification (not used by this generator).
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
    num_fps_generated = 0
    for filepath in get_spec_file_names(generator_name):
        num_fps_generated += parse_and_execute_yml_file(generator_name, filepath)
    return num_fps_generated


def create_footprint(generator_name, name, **kwargs) -> int:
    courtyard_offset = GLOBAL_CONFIG.get_courtyard_offset(GLOBAL_CONFIG.CourtyardType.DEFAULT)

    kicad_mod = Footprint(name, FootprintType.SMD)

    body_width = kwargs['body_width']['nominal']
    body_length = kwargs['body_length']['nominal']
    body_diameter = kwargs['body_diameter']['nominal']
    body_height = kwargs['body_height']['nominal']

    description = "SMD capacitor, aluminum electrolytic"

    if 'extra_description' in kwargs:
        description += ", " + kwargs['extra_description']

    description += ", " + str(body_diameter) + "x" + str(body_height) + "mm"

    if 'datasheet' in kwargs:
        description += ", " + kwargs['datasheet']

    kicad_mod.description = description
    kicad_mod.tags = ['capacitor', 'electrolytic']

    # set general values
    text_offset_y = body_width / 2. + courtyard_offset + 0.8

    # silkscreen REF**
    silk_text_config = GLOBAL_CONFIG.get_text_properties_for_layer("F.SilkS")
    silk_text_size = silk_text_config.size_nom
    silk_text_thickness = silk_text_size * silk_text_config.thickness_ratio
    kicad_mod.append(Property(name=Property.REFERENCE, text='REF**', at=[0, -text_offset_y], layer='F.SilkS', size=[
                    silk_text_size, silk_text_size], thickness=silk_text_thickness))
    # fab value
    fab_text_config = GLOBAL_CONFIG.get_text_properties_for_layer("F.Fab")
    fab_text_size = fab_text_config.size_nom
    fab_text_thickness = fab_text_size * fab_text_config.thickness_ratio
    kicad_mod.append(Property(name=Property.VALUE, text=name, at=[0, text_offset_y], layer='F.Fab', size=[
                    fab_text_size, fab_text_size], thickness=fab_text_thickness))
    # fab REF**
    fab_text_size = body_diameter / 5.0
    fab_text_size = min(fab_text_size, fab_text_config.size_max)
    fab_text_size = max(fab_text_size, fab_text_config.size_min)
    fab_text_thickness = fab_text_size * fab_text_config.thickness_ratio
    kicad_mod.append(Text(text='${REFERENCE}', at=[0, 0], layer='F.Fab', size=[
                    fab_text_size, fab_text_size], thickness=fab_text_thickness))

    # create fabrication layer
    fab_x = body_length / 2.
    fab_y = body_width / 2.

    if kwargs['pin1_chamfer'] == 'auto':
        fab_edge = min(fab_x / 2, fab_y / 2, GLOBAL_CONFIG.fab_pin1_marker_length)
    else:
        fab_edge = kwargs['pin1_chamfer']
    fab_x_edge = fab_x - fab_edge
    fab_y_edge = fab_y - fab_edge
    kicad_mod.append(Line(start=[fab_x, -fab_y], end=[fab_x, fab_y],
                        layer='F.Fab', width=GLOBAL_CONFIG.fab_line_width))
    kicad_mod.append(Line(start=[-fab_x_edge, -fab_y], end=[fab_x, -fab_y],
                        layer='F.Fab', width=GLOBAL_CONFIG.fab_line_width))
    kicad_mod.append(Line(start=[-fab_x_edge, fab_y], end=[fab_x, fab_y],
                        layer='F.Fab', width=GLOBAL_CONFIG.fab_line_width))
    if fab_edge > 0:
        kicad_mod.append(Line(start=[-fab_x, -fab_y_edge], end=[-fab_x, fab_y_edge],
                            layer='F.Fab', width=GLOBAL_CONFIG.fab_line_width))
        kicad_mod.append(Line(start=[-fab_x, -fab_y_edge], end=[-fab_x_edge, -fab_y],
                            layer='F.Fab', width=GLOBAL_CONFIG.fab_line_width))
    kicad_mod.append(Line(start=[-fab_x, fab_y_edge], end=[-fab_x_edge, fab_y],
                        layer='F.Fab', width=GLOBAL_CONFIG.fab_line_width))
    kicad_mod.append(Circle(center=[0, 0], radius=body_diameter / 2.,
                            layer='F.Fab', width=GLOBAL_CONFIG.fab_line_width))

    # fab polarity marker
    fab_pol_size = body_diameter / 10.
    fab_pol_wing = fab_pol_size / 2.
    fab_pol_distance = body_diameter / 2. - fab_pol_wing - GLOBAL_CONFIG.fab_line_width
    fab_pol_pos_y = fab_text_size / 2 + GLOBAL_CONFIG.silk_pad_clearance + fab_pol_size
    fab_pol_pos_x = math.sqrt(fab_pol_distance * fab_pol_distance - fab_pol_pos_y * fab_pol_pos_y)
    fab_pol_pos_x = -fab_pol_pos_x
    fab_pol_pos_y = -fab_pol_pos_y
    kicad_mod.append(Line(start=[fab_pol_pos_x - fab_pol_wing, fab_pol_pos_y], end=[fab_pol_pos_x + fab_pol_wing, fab_pol_pos_y],
                        layer='F.Fab', width=GLOBAL_CONFIG.fab_line_width))
    kicad_mod.append(Line(start=[fab_pol_pos_x, fab_pol_pos_y - fab_pol_wing], end=[fab_pol_pos_x, fab_pol_pos_y + fab_pol_wing],
                        layer='F.Fab', width=GLOBAL_CONFIG.fab_line_width))

    # create silkscreen
    fab_to_silk_offset = GLOBAL_CONFIG.silk_fab_offset
    silk_x = body_length / 2. + fab_to_silk_offset
    silk_y = body_width / 2. + fab_to_silk_offset
    silk_y_start = kwargs['pad_width'] / 2. + \
        GLOBAL_CONFIG.silk_pad_clearance + GLOBAL_CONFIG.silk_line_width / 2.
    silk_45deg_offset = fab_to_silk_offset * math.tan(math.radians(22.5))
    silk_x_edge = fab_x - fab_edge + silk_45deg_offset
    silk_y_edge = fab_y - fab_edge + silk_45deg_offset

    kicad_mod.append(Line(start=[silk_x, silk_y], end=[silk_x, silk_y_start],
                        layer='F.SilkS', width=GLOBAL_CONFIG.silk_line_width))
    kicad_mod.append(Line(start=[silk_x, -silk_y], end=[silk_x, -silk_y_start],
                        layer='F.SilkS', width=GLOBAL_CONFIG.silk_line_width))
    kicad_mod.append(Line(start=[-silk_x_edge, -silk_y], end=[silk_x, -silk_y],
                        layer='F.SilkS', width=GLOBAL_CONFIG.silk_line_width))
    kicad_mod.append(Line(start=[-silk_x_edge, silk_y], end=[silk_x, silk_y],
                        layer='F.SilkS', width=GLOBAL_CONFIG.silk_line_width))

    if silk_y_edge > silk_y_start:
        kicad_mod.append(Line(start=[-silk_x, silk_y_edge], end=[-silk_x, silk_y_start],
                            layer='F.SilkS', width=GLOBAL_CONFIG.silk_line_width))
        kicad_mod.append(Line(start=[-silk_x, -silk_y_edge], end=[-silk_x, -silk_y_start],
                            layer='F.SilkS', width=GLOBAL_CONFIG.silk_line_width))

        kicad_mod.append(Line(start=[-silk_x, -silk_y_edge], end=[-silk_x_edge, -silk_y],
                            layer='F.SilkS', width=GLOBAL_CONFIG.silk_line_width))
        kicad_mod.append(Line(start=[-silk_x, silk_y_edge], end=[-silk_x_edge, silk_y],
                            layer='F.SilkS', width=GLOBAL_CONFIG.silk_line_width))
    else:
        # because of the 45 degree edge we can user a simple apporach
        silk_x_cut = silk_x - (silk_y_start - silk_y_edge)
        silk_y_edge_cut = silk_y_start

        kicad_mod.append(Line(start=[-silk_x_cut, -silk_y_edge_cut], end=[-silk_x_edge,
                                                                        - silk_y], layer='F.SilkS', width=GLOBAL_CONFIG.silk_line_width))
        kicad_mod.append(Line(start=[-silk_x_cut, silk_y_edge_cut], end=[-silk_x_edge,
                                                                        silk_y], layer='F.SilkS', width=GLOBAL_CONFIG.silk_line_width))

    # silk polarity marker
    silk_pol_size = body_diameter / 8.
    silk_pol_wing = silk_pol_size / 2.
    silk_pol_pos_y = silk_y_start + silk_pol_size
    silk_pol_pos_x = silk_x + silk_pol_wing + GLOBAL_CONFIG.silk_line_width * 2
    silk_pol_pos_x = -silk_pol_pos_x
    silk_pol_pos_y = -silk_pol_pos_y
    kicad_mod.append(Line(start=[silk_pol_pos_x - silk_pol_wing, silk_pol_pos_y], end=[silk_pol_pos_x + silk_pol_wing, silk_pol_pos_y],
                        layer='F.SilkS', width=GLOBAL_CONFIG.silk_line_width))
    kicad_mod.append(Line(start=[silk_pol_pos_x, silk_pol_pos_y - silk_pol_wing], end=[silk_pol_pos_x, silk_pol_pos_y + silk_pol_wing],
                        layer='F.SilkS', width=GLOBAL_CONFIG.silk_line_width))

    # create courtyard
    courtyard_x = body_length / 2. + courtyard_offset
    courtyard_y = body_width / 2. + courtyard_offset
    courtyard_pad_x = kwargs['pad_spacing'] / 2. + kwargs['pad_length'] + courtyard_offset
    courtyard_pad_y = kwargs['pad_width'] / 2. + courtyard_offset
    courtyard_45deg_offset = courtyard_offset * math.tan(math.radians(22.5))
    courtyard_x_edge = fab_x - fab_edge + courtyard_45deg_offset
    courtyard_y_edge = fab_y - fab_edge + courtyard_45deg_offset
    courtyard_x_lower_edge = courtyard_x
    if courtyard_y_edge < courtyard_pad_y:
        courtyard_x_lower_edge = courtyard_x_lower_edge - courtyard_pad_y + courtyard_y_edge
        courtyard_y_edge = courtyard_pad_y
    # rounding
    courtyard_x = float(format(courtyard_x, ".2f"))
    courtyard_y = float(format(courtyard_y, ".2f"))
    courtyard_pad_x = float(format(courtyard_pad_x, ".2f"))
    courtyard_pad_y = float(format(courtyard_pad_y, ".2f"))
    courtyard_x_edge = float(format(courtyard_x_edge, ".2f"))
    courtyard_y_edge = float(format(courtyard_y_edge, ".2f"))
    courtyard_x_lower_edge = float(format(courtyard_x_lower_edge, ".2f"))

    # drawing courtyard
    kicad_mod.append(Line(start=[courtyard_x, -courtyard_y], end=[courtyard_x, -courtyard_pad_y],
                        layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width))
    kicad_mod.append(Line(start=[courtyard_x, -courtyard_pad_y], end=[courtyard_pad_x,
                                                                    - courtyard_pad_y], layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width))
    kicad_mod.append(Line(start=[courtyard_pad_x, -courtyard_pad_y], end=[courtyard_pad_x,
                                                                        courtyard_pad_y], layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width))
    kicad_mod.append(Line(start=[courtyard_pad_x, courtyard_pad_y], end=[courtyard_x,
                                                                        courtyard_pad_y], layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width))
    kicad_mod.append(Line(start=[courtyard_x, courtyard_pad_y], end=[courtyard_x, courtyard_y],
                        layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width))

    kicad_mod.append(Line(start=[-courtyard_x_edge, courtyard_y], end=[courtyard_x,
                                                                    courtyard_y], layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width))
    kicad_mod.append(Line(start=[-courtyard_x_edge, -courtyard_y], end=[courtyard_x,
                                                                        - courtyard_y], layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width))
    if fab_edge > 0:
        kicad_mod.append(Line(start=[-courtyard_x_lower_edge, courtyard_y_edge], end=[-courtyard_x_edge,
                                                                                    courtyard_y], layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width))
        kicad_mod.append(Line(start=[-courtyard_x_lower_edge, -courtyard_y_edge], end=[-courtyard_x_edge,
                                                                                    - courtyard_y], layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width))
    if courtyard_y_edge > courtyard_pad_y:
        kicad_mod.append(Line(start=[-courtyard_x, -courtyard_y_edge], end=[-courtyard_x,
                                                                            - courtyard_pad_y], layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width))
        kicad_mod.append(Line(start=[-courtyard_x, courtyard_pad_y], end=[-courtyard_x,
                                                                        courtyard_y_edge], layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width))
    kicad_mod.append(Line(start=[-courtyard_x_lower_edge, -courtyard_pad_y], end=[-courtyard_pad_x,
                                                                                - courtyard_pad_y], layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width))
    kicad_mod.append(Line(start=[-courtyard_pad_x, -courtyard_pad_y], end=[-courtyard_pad_x,
                                                                        courtyard_pad_y], layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width))
    kicad_mod.append(Line(start=[-courtyard_pad_x, courtyard_pad_y], end=[-courtyard_x_lower_edge,
                                                                        courtyard_pad_y], layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width))

    # all pads have this kwargs, so we only write them once
    pad_kwargs = {'type': Pad.TYPE_SMT,
                'shape': Pad.SHAPE_ROUNDRECT,
                'layers': Pad.LAYERS_SMT,
                'round_radius_handler': GLOBAL_CONFIG.roundrect_radius_handler,
    }

    # create pads
    x_pad_spacing = kwargs['pad_spacing'] / 2. + kwargs['pad_length'] / 2.
    kicad_mod.append(Pad(number=1, at=[-x_pad_spacing, 0],
                        size=[kwargs['pad_length'], kwargs['pad_width']], **pad_kwargs))
    kicad_mod.append(Pad(number=2, at=[x_pad_spacing, 0],
                        size=[kwargs['pad_length'], kwargs['pad_width']], **pad_kwargs))

    lib_name = 'Capacitor_SMD'
    # add model
    modelname = name.replace("_HandSoldering", "")
    kicad_mod.append(Model(filename="{model_prefix:s}{lib_name:s}.3dshapes/{name:s}{suffix:s}".format(
                                model_prefix=GLOBAL_CONFIG.model_3d_prefix, lib_name=lib_name, name=modelname, suffix=GLOBAL_CONFIG.model_3d_suffix),
                        at=[0, 0, 0], scale=[1, 1, 1], rotate=[0, 0, 0]))

    # write file
    write_footprint(kicad_mod, lib_name, generator_name)
    return 1


def parse_and_execute_yml_file(generator_name, filepath) -> int:
    num_fps_generated = 0
    with open(filepath, 'r') as stream:
        yaml_parsed = yaml.safe_load(stream)
        for footprint in yaml_parsed:
            num_fps_generated += create_footprint(generator_name, footprint, **yaml_parsed.get(footprint))
    return num_fps_generated
