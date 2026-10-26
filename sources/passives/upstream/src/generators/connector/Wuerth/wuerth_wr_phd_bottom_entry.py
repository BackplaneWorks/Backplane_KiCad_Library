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

from typing import Any
from KicadModTree import *
from generators.tools.footprint.footprint_text_fields import addTextFields
from generators.tools.footprint.save_footprint import write_footprint
from kilibs.config import global_config as GC
from KicadModTree.util.courtyard_builder import CourtyardBuilder
from pathlib import Path
import yaml


# Function used to generate footprint
def generate_footprint(generator_name: str, global_config: GC.GlobalConfig, params, part_params, mpn, configuration):

    # Build footprint name
    fp_name = "Wuerth_{series_prefix}_{mpn}_{type}_{rows}x{pins:02d}_P{pitch}mm_{orientation}".format(
        series_prefix=params['series_prefix'], mpn=mpn, type=params['type'], rows=part_params['rows'], pins=part_params['pins']//2, pitch=params['pitch'], orientation=params['orientation'])

    # Create footprint
    if params['type'] == 'SMD':
        kicad_mod = Footprint(fp_name, FootprintType.SMD)
    else:
        kicad_mod = Footprint(fp_name, FootprintType.THT)

    # Description
    kicad_mod.setDescription("Connector Wuerth, WR-PHD {pitch}mm Dual Socket Header Bottom Entry {type}, Wuerth electronics {mpn} ({datasheet})".format(
        pitch=params['pitch'], type=params['type'], mpn=mpn, datasheet=part_params['datasheet']))

    # Keywords
    kicad_mod.setTags("Connector Wuerth WR-PHD {pitch}mm {mpn}".format(
        pitch=params['pitch'], mpn=mpn))

    # Pads
    if params['type'] == 'SMD':
        kicad_mod.append(PadArray(initial=1, start=[-params['pitch']/2-params['holes']['offset'], -params['pitch']*(part_params['pins']//2-1)/2], y_spacing=params['pitch'], pincount=part_params['pins']//2, increment=2,
            size=[params['pads']['x'], params['pads']['y']], type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, layers=['F.Cu', 'F.Paste', 'F.Mask']))
        kicad_mod.append(PadArray(initial=2, start=[params['pitch']/2+params['holes']['offset'], -params['pitch']*(part_params['pins']//2-1)/2], y_spacing=params['pitch'], pincount=part_params['pins']//2, increment=2,
            size=[params['pads']['x'], params['pads']['y']], type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, layers=['F.Cu', 'F.Paste', 'F.Mask']))
    else:
        kicad_mod.append(PadArray(initial=1, start=[0, 0], y_spacing=params['pitch'], pincount=part_params['pins']//2, increment=2,
            size=[params['pads']['diameter'], params['pads']['diameter']], drill=params['pads']['drill'], type=Pad.TYPE_THT, tht_pad1_shape=Pad.SHAPE_RECT, shape=Pad.SHAPE_OVAL, layers=['*.Cu', '*.Mask']))
        kicad_mod.append(PadArray(initial=2, start=[params['pitch']+2*params['holes']['offset'], 0], y_spacing=params['pitch'], pincount=part_params['pins']//2, increment=2,
            size=[params['pads']['diameter'], params['pads']['diameter']], drill=params['pads']['drill'], type=Pad.TYPE_THT, tht_pad1_shape=Pad.SHAPE_RECT, shape=Pad.SHAPE_OVAL, layers=['*.Cu', '*.Mask']))

    # Bottom entry holes
    if params['type'] == 'SMD':
        kicad_mod.append(PadArray(initial="", start=[params['pitch']/2, -params['pitch']*(part_params['pins']//2-1)/2], y_spacing=params['pitch'], pincount=part_params['pins']//2, increment="",
            size=params['holes']['drill'], drill=params['holes']['drill'], type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE, layers=Pad.LAYERS_NPTH))
        kicad_mod.append(PadArray(initial="", start=[-params['pitch']/2, -params['pitch']*(part_params['pins']//2-1)/2], y_spacing=params['pitch'], pincount=part_params['pins']//2, increment="",
            size=params['holes']['drill'], drill=params['holes']['drill'], type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE, layers=Pad.LAYERS_NPTH))
    else:
        kicad_mod.append(PadArray(initial="", start=[params['holes']['offset'], 0], y_spacing=params['pitch'], pincount=part_params['pins']//2, increment="",
            size=params['holes']['drill'], drill=params['holes']['drill'], type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE, layers=Pad.LAYERS_NPTH))
        kicad_mod.append(PadArray(initial="", start=[params['pitch']+params['holes']['offset'], 0], y_spacing=params['pitch'], pincount=part_params['pins']//2, increment="",
            size=params['holes']['drill'], drill=params['holes']['drill'], type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE, layers=Pad.LAYERS_NPTH))

    # Add fab layer
    if params['type'] == 'SMD':
        body_top_left = [-params['width']/2, -params['top']-params['pitch']*(part_params['pins']//2-1)/2]
        body_bottom_right = [params['width']/2, params['top']+params['pitch']*(part_params['pins']//2-1)/2]
    else:
        body_top_left = [(-params['width']+params['pitch'])/2+params['holes']['offset'], -params['top']]
        body_bottom_right = [(-params['width']+params['pitch'])/2+params['width']+params['holes']['offset'], params['top']+params['pitch']*(part_params['pins']//2-1)]
    kicad_mod.append(Rectangle(start=body_top_left, end=body_bottom_right, layer='F.Fab', width=configuration['fab_line_width']))

    # Add silkscreen layer
    silk_top_left = [body_top_left[0] - configuration['silk_fab_offset'], body_top_left[1] - configuration['silk_fab_offset']]
    silk_bottom_right = [body_bottom_right[0] + configuration['silk_fab_offset'], body_bottom_right[1] + configuration['silk_fab_offset']]
    # -> Top part
    kicad_mod.append(Line(start=[silk_top_left[0], silk_top_left[1]], end=[silk_bottom_right[0], silk_top_left[1]], layer='F.SilkS', width=configuration['silk_line_width']))
    kicad_mod.append(Line(start=[silk_top_left[0], silk_top_left[1]], end=[silk_top_left[0], silk_top_left[1] + 1.27/2], layer='F.SilkS', width=configuration['silk_line_width']))
    kicad_mod.append(Line(start=[silk_bottom_right[0], silk_top_left[1]], end=[silk_bottom_right[0], silk_top_left[1] + 1.27/2], layer='F.SilkS', width=configuration['silk_line_width']))
    kicad_mod.append(Line(start=[silk_top_left[0], silk_top_left[1] + 1.27/2], end=[silk_top_left[0] - 1.27/2, silk_top_left[1] + 1.27/2], layer='F.SilkS', width=configuration['silk_line_width']))
    # -> Dashes between the pads
    for x in range(0, part_params['pins']//2-1):
        if params['type'] == 'SMD':
            kicad_mod.append(Line(start=[silk_bottom_right[0], -params['pitch']*(part_params['pins']//2-1)/2 + 3*params['pitch']/8 + x * params['pitch']], end=[silk_bottom_right[0], -params['pitch']*(part_params['pins']//2-1)/2 + 3*params['pitch']/8 + params['pitch']/4 + x * params['pitch']], layer='F.SilkS', width=configuration['silk_line_width']))
            kicad_mod.append(Line(start=[silk_top_left[0], -params['pitch']*(part_params['pins']//2-1)/2 + 3*params['pitch']/8 + x * params['pitch']], end=[silk_top_left[0], -params['pitch']*(part_params['pins']//2-1)/2 + 3*params['pitch']/8 + params['pitch']/4 + x * params['pitch']], layer='F.SilkS', width=configuration['silk_line_width']))
        else:
            kicad_mod.append(Line(start=[silk_bottom_right[0], 3*params['pitch']/8 + x * params['pitch']], end=[silk_bottom_right[0], 3*params['pitch']/8 + params['pitch']/4 + x * params['pitch']], layer='F.SilkS', width=configuration['silk_line_width']))
            kicad_mod.append(Line(start=[silk_top_left[0], 3*params['pitch']/8 + x * params['pitch']], end=[silk_top_left[0], 3*params['pitch']/8 + params['pitch']/4 + x * params['pitch']], layer='F.SilkS', width=configuration['silk_line_width']))
    # -> Bottom part
    kicad_mod.append(Line(start=[silk_bottom_right[0], silk_bottom_right[1]], end=[silk_bottom_right[0], silk_bottom_right[1] - 1.27/2], layer='F.SilkS', width=configuration['silk_line_width']))
    kicad_mod.append(Line(start=[silk_top_left[0], silk_bottom_right[1]], end=[silk_top_left[0], silk_bottom_right[1] - 1.27/2], layer='F.SilkS', width=configuration['silk_line_width']))
    kicad_mod.append(Line(start=[silk_top_left[0], silk_bottom_right[1]], end=[silk_bottom_right[0], silk_bottom_right[1]], layer='F.SilkS', width=configuration['silk_line_width']))

    # Add courtyard layer
    crt_offset = global_config.get_courtyard_offset(GC.GlobalConfig.CourtyardType.CONNECTOR)
    cb = CourtyardBuilder.from_node(
        node=kicad_mod,
        global_config=global_config,
        offset_fab=crt_offset
        )
    kicad_mod += cb.node

    # Add texts
    body_edge={'left': body_top_left[0], 'right': body_bottom_right[0], 'top': body_top_left[1], 'bottom': body_bottom_right[1]}
    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge, fp_name=fp_name, text_y_inside_position='top',
        courtyard={'top': body_edge['top'] - crt_offset, 'bottom': body_edge['bottom'] + crt_offset + 0.2})

    # 3D model definition
    lib_name = "Connector_Wuerth"
    model3d_path_prefix = configuration.get('3d_model_prefix', global_config.model_3d_prefix)
    model3d_path_suffix = configuration.get('3d_model_suffix', global_config.model_3d_suffix)
    model_name = "{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}{model3d_path_suffix:s}".format(
        model3d_path_prefix=model3d_path_prefix, fp_name=fp_name, lib_name=lib_name,
        model3d_path_suffix=model3d_path_suffix)
    kicad_mod.append(Model(filename=model_name))

    # Create output directory

    write_footprint(kicad_mod, lib_name, generator_name)


def generate_all(generator_name: str, global_config: GC.GlobalConfig, configuration: dict[str, Any], data_path: str) -> int:
    with open(data_path, 'r') as params_stream:
        try:
            params = yaml.safe_load(params_stream)
        except yaml.YAMLError as exc:
            print(exc)

    num_fps_generated = 0
    for series in params:
        for mpn in params[series]['parts']:
            generate_footprint(generator_name, global_config, params[series], params[series]['parts'][mpn], mpn, configuration)
            num_fps_generated += 1
    return num_fps_generated
