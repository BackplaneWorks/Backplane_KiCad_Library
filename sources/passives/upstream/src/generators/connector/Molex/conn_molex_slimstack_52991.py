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
from math import sqrt
from KicadModTree import *
from generators.tools.footprint.drawing_tools import round_to_grid
from generators.tools.footprint.footprint_text_fields import addTextFields
from generators.tools.footprint.save_footprint import write_footprint
from kilibs.config import global_config as GC

series = "SlimStack"
series_long = 'SlimStack Fine-Pitch SMT Board-to-Board Connectors'
manufacturer = 'Molex'
orientation = 'V'
number_of_rows = 2
datasheet = 'http://www.molex.com/pdm_docs/sd/529910308_sd.pdf'

#pins_per_row per row
pins_range = [20,30,40,50,60,70,80]

#Molex part number
#n = number of circuits per row
part_code = "52991-0{n:02}8"

pitch = 0.5

def generate_one_footprint(generator_name: str, global_config: GC.GlobalConfig, pincount, configuration):
    mpn = part_code.format(n=pincount)

    CrtYd_off = configuration['courtyard_offset']['connector']
    CrtYd_grid = configuration['courtyard_grid']
    body_edge = {}
    bounding_box = {}

    # handle arguments
    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_format_string'].format(man=manufacturer,
        series=series,
        mpn=mpn, num_rows=number_of_rows, pins_per_row=pincount//2, mounting_pad = "",
        pitch=pitch, orientation=orientation_str)

    kicad_mod = Footprint(footprint_name, FootprintType.SMD)
    kicad_mod.setDescription("Molex {:s}, {:s}, {:d} Pins ({:s})".format(series_long, mpn, pincount, datasheet))
    kicad_mod.setTags(configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry=configuration['entry_direction'][orientation]))

    # calculate working values
    pad_x_spacing = pitch
    pad_y_spacing = 2.2 + 1.8
    pad_width = 0.3
    pad_height = 1.8
    pad_x_span = (pad_x_spacing * ((pincount / 2) - 1))

    h_body_width = 4.3 / 2.0
    h_body_length = (pad_x_span / 2.0) + 2.15

    tab_width = 1.3
    tab_height = 0.5

    fab_width = configuration['fab_line_width']

    outline_x = h_body_length - (pad_x_span / 2.0) - pad_width/2 - (configuration['silk_pad_clearance'] + configuration['silk_line_width']/2)
    marker_y = 0.8
    silk_width = configuration['silk_line_width']
    nudge = configuration['silk_fab_offset']

    courtyard_width = configuration['courtyard_line_width']
    courtyard_precision = configuration['courtyard_grid']
    courtyard_clearance = configuration['courtyard_offset']['connector']
    courtyard_x = round_to_grid(h_body_length + courtyard_clearance, courtyard_precision)
    courtyard_y = round_to_grid((pad_y_spacing + pad_height) / 2.0 + courtyard_clearance, courtyard_precision)

    # create pads
    kicad_mod.append(PadArray(pincount=pincount//2, x_spacing=pad_x_spacing, y_spacing=0,\
        center=[0,-pad_y_spacing/2.0], initial=1, increment=2, type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, size=[pad_width, pad_height],\
        layers=Pad.LAYERS_SMT))
    kicad_mod.append(PadArray(pincount=pincount//2, x_spacing=pad_x_spacing, y_spacing=0,\
        center=[0,pad_y_spacing/2.0], initial=2, increment=2, type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, size=[pad_width, pad_height],\
        layers=Pad.LAYERS_SMT))

    # create fab outline and pin 1 marker
    kicad_mod.append(Rectangle(start=[-h_body_length, -h_body_width], end=[h_body_length, h_body_width], layer='F.Fab', width=fab_width))
    body_edge={
        'left':-h_body_length,
        'top':-h_body_width
    }
    body_edge['right'] = -body_edge['left']
    body_edge['bottom'] = -body_edge['top']
    kicad_mod.append(Line(start=[-h_body_length+outline_x, -h_body_width-nudge], end=[-h_body_length+outline_x, -h_body_width-marker_y], layer='F.Fab', width=fab_width))

    # create silkscreen outline and pin 1 marker
    left_outline = [[-h_body_length+outline_x, h_body_width+nudge], [-h_body_length-nudge, h_body_width+nudge], [-h_body_length-nudge, -h_body_width-nudge],\
                    [-h_body_length+outline_x, -h_body_width-nudge], [-h_body_length+outline_x, -h_body_width-marker_y]]
    right_outline = [[h_body_length-outline_x, h_body_width+nudge], [h_body_length+nudge, h_body_width+nudge], [h_body_length+nudge, -h_body_width-nudge],\
                     [h_body_length-outline_x, -h_body_width-nudge]]
    top_left_tab = [[-h_body_length-nudge, -h_body_width-nudge], [-h_body_length-nudge, -h_body_width-nudge-tab_height],\
                    [-h_body_length-nudge+tab_width, -h_body_width-nudge-tab_height], [-h_body_length-nudge+tab_width, -h_body_width-nudge]]
    bottom_left_tab = [[-h_body_length-nudge, h_body_width+nudge], [-h_body_length-nudge+tab_width/3, h_body_width+nudge+tab_height],\
                       [-h_body_length-nudge+tab_width, h_body_width+nudge+tab_height], [-h_body_length-nudge+tab_width, h_body_width+nudge]]
    top_right_tab = [[h_body_length+nudge, -h_body_width-nudge], [h_body_length+nudge, -h_body_width-nudge-tab_height],\
                     [h_body_length+nudge-tab_width, -h_body_width-nudge-tab_height], [h_body_length+nudge-tab_width, -h_body_width-nudge]]
    bottom_right_tab = [[h_body_length+nudge, h_body_width+nudge], [h_body_length+nudge, h_body_width+nudge+tab_height],\
                       [h_body_length+nudge-tab_width, h_body_width+nudge+tab_height], [h_body_length+nudge-tab_width, h_body_width+nudge]]
    kicad_mod.append(PolygonLine(shape=left_outline, layer='F.SilkS', width=silk_width))
    kicad_mod.append(PolygonLine(shape=right_outline, layer='F.SilkS', width=silk_width))
    kicad_mod.append(PolygonLine(shape=top_left_tab, layer='F.SilkS', width=silk_width))
    kicad_mod.append(PolygonLine(shape=bottom_left_tab, layer='F.SilkS', width=silk_width))
    kicad_mod.append(PolygonLine(shape=top_right_tab, layer='F.SilkS', width=silk_width))
    kicad_mod.append(PolygonLine(shape=bottom_right_tab, layer='F.SilkS', width=silk_width))

    # create courtyard
    kicad_mod.append(Rectangle(start=[-courtyard_x, -courtyard_y], end=[courtyard_x, courtyard_y], layer='F.CrtYd', width=courtyard_width))

    ######################### Text Fields ###############################

    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
        courtyard={'top':-courtyard_y, 'bottom':+courtyard_y},
        fp_name=footprint_name, text_y_inside_position='center')

    ##################### Output and 3d model ############################
    model3d_path_prefix = configuration.get('3d_model_prefix',global_config.model_3d_prefix)
    model3d_path_suffix = configuration.get('3d_model_suffix',global_config.model_3d_suffix)

    lib_name = configuration['lib_name_format_string'].format(series=series, man=manufacturer)
    model_name = '{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}{model3d_path_suffix:s}'.format(
        model3d_path_prefix=model3d_path_prefix, lib_name=lib_name, fp_name=footprint_name,
        model3d_path_suffix=model3d_path_suffix)
    kicad_mod.append(Model(filename=model_name))

    write_footprint(kicad_mod, lib_name, generator_name)


def generate_all(generator_name: str, global_config: GC.GlobalConfig, configuration: dict[str, Any]) -> int:
    num_fps_generated = 0
    for pins in pins_range:
        generate_one_footprint(generator_name, global_config, pins, configuration)
        num_fps_generated += 1
    return num_fps_generated
