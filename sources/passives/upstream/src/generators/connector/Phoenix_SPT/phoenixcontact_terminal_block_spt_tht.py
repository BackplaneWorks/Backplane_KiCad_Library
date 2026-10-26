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
import argparse
import yaml

from KicadModTree import *
from generators.tools.footprint.footprint_text_fields import addTextFields
from generators.tools.footprint.save_footprint import write_footprint
from kilibs.config import global_config as GC


# Function used to generate footprint
def generate_footprint(generator_name: str, global_config: GC.GlobalConfig, params, part_params, mpn, configuration):

    # Build footprint name
    fp_name = "PhoenixContact_{series_prefix}{pins}-{orientation_short}-{pitch}{series_sufix}_{rows}x{pins:02d}_P{pitch}mm_{orientation}".format(
        series_prefix=params['series_prefix'].replace(' ', '_').replace('/', '_'), series_sufix=(params['series_sufix'] if params['series_sufix'] is not None else ''), rows=part_params['rows'], pins=part_params['pins'], pitch=params['pitch']['x'], orientation=params['orientation'], orientation_short=params['orientation'][:1])

    # Create footprint
    kicad_mod = Footprint(fp_name, FootprintType.THT)

    # Description
    kicad_mod.setDescription("Connector Phoenix Contact, {series_prefix}{pins}-{orientation_short}-{pitch}{series_sufix} Terminal Block, {mpn} (https://www.phoenixcontact.com/online/portal/gb/?uri=pxc-oc-itemdetail:pid={mpn})".format(
        series_prefix=params['series_prefix'], series_sufix=(params['series_sufix'] if params['series_sufix'] is not None else ''), pins=part_params['pins'], pitch=params['pitch']['x'], orientation_short=params['orientation'][:1], mpn=mpn))

    # Keywords
    kicad_mod.setTags("Connector Phoenix Contact {series_prefix}{pins}-{orientation_short}-{pitch}{series_sufix} {mpn}".format(
        series_prefix=params['series_prefix'], series_sufix=(params['series_sufix'] if params['series_sufix'] is not None else ''), pins=part_params['pins'], pitch=params['pitch']['x'], orientation_short=params['orientation'][:1], mpn=mpn))

    # Pads
    kicad_mod.append(PadArray(initial=1, start=[0, 0], x_spacing=params['pitch']['x']*params['pads']['increment'], pincount=(part_params['pins']+params['pads']['increment']-1)//params['pads']['increment'], increment=params['pads']['increment'],
        size=[params['pads']['size']['x'], params['pads']['size']['y']], drill=params['pads']['drill'], type=Pad.TYPE_THT, tht_pad1_shape=Pad.SHAPE_ROUNDRECT, shape=Pad.SHAPE_OVAL, layers=Pad.LAYERS_THT,
        round_radius_handler=global_config.roundrect_radius_handler))
    kicad_mod.append(PadArray(initial=params['pads']['increment'], start=[(params['pads']['increment']-1)*params['pitch']['x'], params['pitch']['y']], x_spacing=params['pitch']['x']*params['pads']['increment'], pincount=part_params['pins']//params['pads']['increment'], increment=params['pads']['increment'],
        size=[params['pads']['size']['x'], params['pads']['size']['y']], drill=params['pads']['drill'], type=Pad.TYPE_THT, tht_pad1_shape=Pad.SHAPE_ROUNDRECT, shape=Pad.SHAPE_OVAL, layers=Pad.LAYERS_THT,
        round_radius_handler=global_config.roundrect_radius_handler))

    # Add fab layer
    body_top_left = [params['fab']['left'], params['fab']['top']]
    body_bottom_right = [params['fab']['left']+params['pitch']['x']*part_params['pins']+params['fab']['right'], params['fab']['bottom']]
    # -> GeomRectangle
    kicad_mod.append(Rectangle(start=body_top_left, end=body_bottom_right, layer='F.Fab', width=configuration['fab_line_width']))
    # -> Marker of pin 1
    kicad_mod.append(Line(start=[-0.95, params['fab']['top']],
        end=[0, params['fab']['top'] + 1.5], layer='F.Fab', width=configuration['fab_line_width']))
    kicad_mod.append(Line(start=[0.95, params['fab']['top']],
        end=[0, params['fab']['top'] + 1.5], layer='F.Fab', width=configuration['fab_line_width']))

    # Add silkscreen layer
    silk_top_left = [body_top_left[0] - configuration['silk_fab_offset'], body_top_left[1] - configuration['silk_fab_offset']]
    silk_bottom_right = [body_bottom_right[0] + configuration['silk_fab_offset'], body_bottom_right[1] + configuration['silk_fab_offset']]
    # -> GeomRectangle
    if silk_top_left[1] > -params['pads']['size']['y']/2 - configuration['silk_pad_clearance']:
        # Handle case with large pin which overlap the silkscreen
        kicad_mod.append(Line(start=[silk_top_left[0], silk_top_left[1]],
            end=[-params['pads']['size']['x']/2 - configuration['silk_pad_clearance'], silk_top_left[1]], layer='F.SilkS', width=configuration['silk_line_width']))
        for x in range(0, part_params['pins'] - 1):
            kicad_mod.append(Line(start=[params['pads']['size']['x']/2 + configuration['silk_pad_clearance'] + params['pitch']['x'] * x, silk_top_left[1]],
                end=[params['pitch']['x'] - params['pads']['size']['x']/2 - configuration['silk_pad_clearance'] + params['pitch']['x'] * x, silk_top_left[1]], layer='F.SilkS', width=configuration['silk_line_width']))
        kicad_mod.append(Line(start=[params['pads']['size']['x']/2 + configuration['silk_pad_clearance'] + params['pitch']['x'] * (part_params['pins'] - 1), silk_top_left[1]],
            end=[silk_bottom_right[0], silk_top_left[1]], layer='F.SilkS', width=configuration['silk_line_width']))
    else:
        # Case with small pin which do not overlap the silkscreen
        kicad_mod.append(Line(start=[silk_top_left[0], silk_top_left[1]], end=[silk_bottom_right[0], silk_top_left[1]], layer='F.SilkS', width=configuration['silk_line_width']))
    if silk_bottom_right[1] < params['pitch']['y'] + params['pads']['size']['y']/2 + configuration['silk_pad_clearance']:
        # Handle case with large pin which overlap the silkscreen
        kicad_mod.append(Line(start=[silk_top_left[0], silk_bottom_right[1]],
            end=[-params['pads']['size']['x']/2 - configuration['silk_pad_clearance'], silk_bottom_right[1]], layer='F.SilkS', width=configuration['silk_line_width']))
        for x in range(0, part_params['pins'] - 1):
            kicad_mod.append(Line(start=[params['pads']['size']['x']/2 + configuration['silk_pad_clearance'] + params['pitch']['x'] * x, silk_bottom_right[1]],
                end=[params['pitch']['x'] - params['pads']['size']['x']/2 - configuration['silk_pad_clearance'] + params['pitch']['x'] * x, silk_bottom_right[1]], layer='F.SilkS', width=configuration['silk_line_width']))
        kicad_mod.append(Line(start=[params['pads']['size']['x']/2 + configuration['silk_pad_clearance'] + params['pitch']['x'] * (part_params['pins'] - 1), silk_bottom_right[1]],
            end=[silk_bottom_right[0], silk_bottom_right[1]], layer='F.SilkS', width=configuration['silk_line_width']))
    else:
        # Case with small pin which do not overlap the silkscreen
        kicad_mod.append(Line(start=[silk_bottom_right[0], silk_bottom_right[1]], end=[silk_top_left[0], silk_bottom_right[1]], layer='F.SilkS', width=configuration['silk_line_width']))
    kicad_mod.append(Line(start=[silk_bottom_right[0], silk_top_left[1]], end=[silk_bottom_right[0], silk_bottom_right[1]], layer='F.SilkS', width=configuration['silk_line_width']))
    kicad_mod.append(Line(start=[silk_top_left[0], silk_bottom_right[1]], end=[silk_top_left[0], silk_top_left[1]], layer='F.SilkS', width=configuration['silk_line_width']))
    # -> Lines in front of the wiring
    if params['orientation'] == 'Horizontal':
        for x in range(0, part_params['pins']):
            kicad_mod.append(Line(start=[params['fab']['left'] + 0.5 + params['pitch']['x'] * x, params['fab']['bottom'] + configuration['silk_fab_offset']],
                end=[params['fab']['left'] + 0.75 + params['pitch']['x'] * x, params['fab']['bottom'] + configuration['silk_fab_offset'] - 1.5], layer='F.SilkS', width=configuration['silk_line_width']))
            kicad_mod.append(Line(start=[params['fab']['left'] + 0.75 + params['pitch']['x'] * x, params['fab']['bottom'] + configuration['silk_fab_offset'] - 1.5],
                end=[params['fab']['left'] + 0.75 + params['pitch']['x'] * x + params['pitch']['x'] - 1.5, params['fab']['bottom'] + configuration['silk_fab_offset'] - 1.5], layer='F.SilkS', width=configuration['silk_line_width']))
            kicad_mod.append(Line(start=[params['fab']['left'] + 0.75 + params['pitch']['x'] * x + params['pitch']['x'] - 1.25, params['fab']['bottom'] + configuration['silk_fab_offset']],
                end=[params['fab']['left'] + 0.75 + params['pitch']['x'] * x + params['pitch']['x'] - 1.5, params['fab']['bottom'] + configuration['silk_fab_offset'] - 1.5], layer='F.SilkS', width=configuration['silk_line_width']))
    # -> Lines on top of the connector
    if params['orientation'] == 'Vertical':
        for x in range(0, part_params['pins']):
            kicad_mod.append(Rectangle(start=[params['fab']['left'] + 0.75 + params['pitch']['x'] * x, params['pitch']['y'] - 1.25 - (params['pitch']['x'] - 1.5) / 2 - 2.0],
                end=[params['fab']['left'] + 0.75 + params['pitch']['x'] * x + params['pitch']['x'] - 1.5, params['pitch']['y'] - 1.25 - (params['pitch']['x'] - 1.5) / 2 - 0.5], layer='F.SilkS', width=configuration['silk_line_width']))
            kicad_mod.append(Arc(center=[params['fab']['left'] + params['pitch']['x']/2 + params['pitch']['x'] * x, params['pitch']['y'] - 1.0],
                mid=[params['fab']['left'] + params['pitch']['x']/2 + params['pitch']['x'] * x, params['pitch']['y'] - 1.0 - (params['pitch']['x'] - 1.5) / 2],
                angle=90, layer='F.SilkS', width=configuration['silk_line_width']))
    # -> Marker of pin 1
    if silk_top_left[1] > -params['pads']['size']['y']/2 - configuration['silk_pad_clearance']:
        # Handle case with large pin which overlap the silkscreen
        kicad_mod.append(Line(start=[-0.3, -params['pads']['size']['y']/2 - configuration['silk_pad_clearance'] - 0.8],
            end=[0.3, -params['pads']['size']['y']/2 - configuration['silk_pad_clearance'] - 0.8], layer='F.SilkS', width=configuration['silk_line_width']))
        kicad_mod.append(Line(start=[-0.3, -params['pads']['size']['y']/2 - configuration['silk_pad_clearance'] - 0.8],
            end=[0, -params['pads']['size']['y']/2 - configuration['silk_pad_clearance'] - 0.2], layer='F.SilkS', width=configuration['silk_line_width']))
        kicad_mod.append(Line(start=[0.3, -params['pads']['size']['y']/2 - configuration['silk_pad_clearance'] - 0.8],
            end=[0, -params['pads']['size']['y']/2 - configuration['silk_pad_clearance'] - 0.2], layer='F.SilkS', width=configuration['silk_line_width']))
    else:
        # Case with small pin which do not overlap the silkscreen
        kicad_mod.append(Line(start=[-0.3, params['fab']['top'] - configuration['silk_fab_offset'] - 0.8],
            end=[0.3, params['fab']['top'] - configuration['silk_fab_offset'] - 0.8], layer='F.SilkS', width=configuration['silk_line_width']))
        kicad_mod.append(Line(start=[-0.3, params['fab']['top'] - configuration['silk_fab_offset'] - 0.8],
            end=[0, params['fab']['top'] - configuration['silk_fab_offset'] - 0.2], layer='F.SilkS', width=configuration['silk_line_width']))
        kicad_mod.append(Line(start=[0.3, params['fab']['top'] - configuration['silk_fab_offset'] - 0.8],
            end=[0, params['fab']['top'] - configuration['silk_fab_offset'] - 0.2], layer='F.SilkS', width=configuration['silk_line_width']))

    # Add courtyard layer
    courtyard_top_left = [body_top_left[0] - configuration['courtyard_offset']['connector'], body_top_left[1] - configuration['courtyard_offset']['connector']]
    courtyard_bottom_right = [body_bottom_right[0] + configuration['courtyard_offset']['connector'], body_bottom_right[1] + configuration['courtyard_offset']['connector']]
    kicad_mod.append(Rectangle(start=courtyard_top_left, end=courtyard_bottom_right, layer='F.CrtYd', width=configuration['courtyard_line_width']))

    # Add texts
    body_edge={'left': body_top_left[0], 'right': body_bottom_right[0], 'top': body_top_left[1], 'bottom': body_bottom_right[1]}
    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge, fp_name=fp_name, text_y_inside_position='top',
        courtyard={'top': body_edge['top'] - configuration['courtyard_offset']['connector'], 'bottom': body_edge['bottom'] + configuration['courtyard_offset']['connector'] + 0.2})

    # 3D model definition
    lib_name = 'Connector_Phoenix_SPT'
    model3d_path_prefix = configuration.get('3d_model_prefix', global_config.model_3d_prefix)
    model3d_path_suffix = configuration.get('3d_model_suffix', global_config.model_3d_suffix)
    model_name = "{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}{model3d_path_suffix:s}".format(
        model3d_path_prefix=model3d_path_prefix, fp_name=fp_name, lib_name=lib_name,
        model3d_path_suffix=model3d_path_suffix)
    kicad_mod.append(Model(filename=model_name))

    # Create output directory
    write_footprint(kicad_mod, lib_name, generator_name)

