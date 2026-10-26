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

from KicadModTree import *
from generators.tools.footprint.drawing_tools import round_to_grid
from generators.tools.footprint.footprint_text_fields import addTextFields
from generators.tools.footprint.save_footprint import write_footprint
from kilibs.config import global_config as GC
from typing import Any

def make_module(generator_name: str, global_config: GC.GlobalConfig, pin_count, configuration):

    series = ""
    series_long = ('Molex 1.00mm Pitch Easy-On BackFlip, ' +
                'Right-Angle, Bottom Contact FFC/FPC')
    manufacturer = 'Molex'
    orientation = 'H'
    number_of_rows = 1

    conn_category = "FFC-FPC"

    lib_by_conn_category = True

    part_code = "200528-0{:02d}0"

    pitch = 1.0
    pad_size = (0.4, 1.0)
    mp_size = (2.0, 1.3)
    foot_y = 3.95
    toe_size = (0.55, 0.35)
    lead_size = (0.15, pad_size[1] - 0.6)
    mpn = part_code.format(pin_count)
    datasheet='https://www.molex.com/pdm_docs/sd/2005280{:02d}0_sd.pdf'.format(pin_count)

    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_format_string'].format(
        man = manufacturer,
        series = series,
        mpn = mpn,
        num_rows = number_of_rows,
        pins = pin_count,
	pins_per_row = pin_count,
        mounting_pad = "-1MP",
        pitch = pitch,
        orientation = orientation_str)

    footprint_name = footprint_name.replace("__",'_')

    kicad_mod = Footprint(footprint_name, FootprintType.SMD)
    kicad_mod.setDescription(
        ("Molex {:s}, {:s}, {:d} Circuits ({:s})").format(
        series_long, mpn, pin_count, datasheet))
    kicad_mod.setTags(configuration['keyword_fp_string'].format(
        man=manufacturer,
        series=series,
        orientation=orientation_str,
        entry=configuration['entry_direction'][orientation]))

    A = pin_count + 5.2
    B = pin_span = pin_count - 1
    C = pin_count + 3.6
    pin_y = -(0.4 - (lead_size[1] / 2)) - 0.71
    lever_size = (C, 4)
    toe_ins_corner = ((A / 2) - toe_size[0], pin_y + (0.4 - (lead_size[1] / 2)))
    lever_out_corner = (C / 2,
        (toe_ins_corner[1] - toe_size[1]) + 5.25)
    pad_silk_off = (configuration['silk_pad_clearance'] +
                    (configuration['silk_line_width'] / 2))
    fab_silk_off = configuration['silk_fab_offset']

    ## Mounting Pads ##

    mp_pos = ((pin_span / 2) + 1.8 + (mp_size[0] / 2),
        pin_y + (pad_size[1] / 2) + 1.55 + (mp_size[1] / 2))

    def make_anchor_pad(x_direction):
        mounting_pad_name = global_config.get_pad_name(GC.PadName.MECHANICAL)
        kicad_mod.append(
            Pad(number = mounting_pad_name,
                type = Pad.TYPE_SMT,
                shape = Pad.SHAPE_RECT,
                at = [x_direction * mp_pos[0], mp_pos[1]],
                size = mp_size,
                layers = Pad.LAYERS_SMT))
    make_anchor_pad(-1)
    make_anchor_pad(1)

    ## Pads ##

    kicad_mod.append(
        PadArray(center = [0, pin_y],
            pincount = pin_count,
            x_spacing = pitch,
            type = Pad.TYPE_SMT,
            shape = Pad.SHAPE_RECT,
            size = pad_size,
            layers = Pad.LAYERS_SMT))

    ## Fab ##

    fab_body_outline = [
        {'x': toe_ins_corner[0], 'y': toe_ins_corner[1] - toe_size[1]},
        {'x': toe_ins_corner[0], 'y': toe_ins_corner[1]},
        {'x': -toe_ins_corner[0], 'y': toe_ins_corner[1]},
        {'x': -toe_ins_corner[0], 'y': toe_ins_corner[1] - toe_size[1]},
        {'x': -(A / 2), 'y': toe_ins_corner[1] - toe_size[1]},
        {'x': -(A / 2), 'y': (toe_ins_corner[1] - toe_size[1]) + foot_y},
        {'x': (A / 2), 'y': (toe_ins_corner[1] - toe_size[1]) + foot_y},
        {'x': (A / 2), 'y': toe_ins_corner[1] - toe_size[1]},
        {'x': toe_ins_corner[0], 'y': toe_ins_corner[1] - toe_size[1]}
    ]

    kicad_mod.append(PolygonLine(
        shape=fab_body_outline,
        layer = 'F.Fab',
        width = configuration['fab_line_width']))

    fab_pin1_mark = [
        {'x': -(pin_span / 2) - 0.5, 'y': toe_ins_corner[1]},
        {'x': -(pin_span / 2), 'y': toe_ins_corner[1] + 0.75},
        {'x': -(pin_span / 2) + 0.5, 'y': toe_ins_corner[1]}
    ]

    kicad_mod.append(PolygonLine(
        shape=fab_pin1_mark,
        layer = 'F.Fab',
        width = configuration['fab_line_width']))

    fab_lever_outline = [
        {'x': lever_out_corner[0], 'y': lever_out_corner[1] - lever_size[1]},
        {'x': -lever_out_corner[0], 'y': lever_out_corner[1] - lever_size[1]},
        {'x': -lever_out_corner[0], 'y': lever_out_corner[1]},
        {'x': lever_out_corner[0], 'y': lever_out_corner[1]},
        {'x': lever_out_corner[0], 'y': lever_out_corner[1] - lever_size[1]}
    ]

    kicad_mod.append(PolygonLine(
        shape=fab_lever_outline,
        layer = 'F.Fab',
        width = configuration['fab_line_width']))

    ## SilkS ##

    silk_outline1 = [
        {'x': (-(pin_span / 2) - (pad_size[0] / 2)) - pad_silk_off, 'y': pin_y - (pad_size[1] / 2)},
        {'x': (-(pin_span / 2) - (pad_size[0] / 2)) - pad_silk_off, 'y': toe_ins_corner[1] - fab_silk_off},
        {'x': -toe_ins_corner[0] + fab_silk_off, 'y': toe_ins_corner[1] - fab_silk_off},
        {'x': -toe_ins_corner[0] + fab_silk_off, 'y': (toe_ins_corner[1] - toe_size[1]) - fab_silk_off},
        {'x': -(A / 2) - fab_silk_off, 'y': (toe_ins_corner[1] - toe_size[1]) - fab_silk_off},
        {'x': -(A / 2) - fab_silk_off, 'y': (mp_pos[1] - (mp_size[1] / 2)) - pad_silk_off},
    ]


    silk_outline2 = [
        {'x': -(A / 2) - fab_silk_off, 'y': (mp_pos[1] + (mp_size[1] / 2)) + pad_silk_off},
        {'x': -(A / 2) - fab_silk_off, 'y': ((toe_ins_corner[1] - toe_size[1]) + foot_y) + fab_silk_off},
        {'x': -lever_out_corner[0] - fab_silk_off, 'y': ((toe_ins_corner[1] - toe_size[1]) + foot_y) + fab_silk_off},
        {'x': -lever_out_corner[0] - fab_silk_off, 'y': lever_out_corner[1] + fab_silk_off},
        {'x': lever_out_corner[0] + fab_silk_off, 'y': lever_out_corner[1] + fab_silk_off},
        {'x': lever_out_corner[0] + fab_silk_off, 'y': ((toe_ins_corner[1] - toe_size[1]) + foot_y) + fab_silk_off},
        {'x': (A / 2) + fab_silk_off, 'y': ((toe_ins_corner[1] - toe_size[1]) + foot_y) + fab_silk_off},
        {'x': (A / 2) + fab_silk_off, 'y': (mp_pos[1] + (mp_size[1] / 2)) + pad_silk_off},
    ]

    silk_outline3 = [
        {'x': (A / 2) + fab_silk_off, 'y': (mp_pos[1] - (mp_size[1] / 2)) - pad_silk_off},
        {'x': (A / 2) + fab_silk_off, 'y': (toe_ins_corner[1] - toe_size[1]) - fab_silk_off},
        {'x': toe_ins_corner[0] - fab_silk_off, 'y': (toe_ins_corner[1] - toe_size[1]) - fab_silk_off},
        {'x': toe_ins_corner[0] - fab_silk_off, 'y': toe_ins_corner[1] - fab_silk_off},
        {'x': ((pin_span / 2) + (pad_size[0] / 2)) + pad_silk_off, 'y': toe_ins_corner[1] - fab_silk_off}
    ]

    kicad_mod.append(PolygonLine(
        shape=silk_outline1,
        layer = 'F.SilkS',
        width = configuration['silk_line_width']))

    kicad_mod.append(PolygonLine(
        shape=silk_outline2,
        layer = 'F.SilkS',
        width = configuration['silk_line_width']))

    kicad_mod.append(PolygonLine(
        shape=silk_outline3,
        layer = 'F.SilkS',
        width = configuration['silk_line_width']))

    ## CrtYd ##

    bounding_box = {
        'top': pin_y - (pad_size[1] / 2),
        'left': (-mp_pos[0] - (mp_size[0] / 2)),
        'bottom': lever_out_corner[1],
        'right': (mp_pos[0] + (mp_size[0] / 2))}

    cx1 = round_to_grid(bounding_box['left']-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    cy1 = round_to_grid(bounding_box['top']-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

    cx2 = round_to_grid(bounding_box['right']+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    cy2 = round_to_grid(bounding_box['bottom']+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

    kicad_mod.append(Rectangle(
        start=[cx1, cy1], end=[cx2, cy2],
        layer='F.CrtYd', width=configuration['courtyard_line_width']))

    ## Text ##

    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=bounding_box, courtyard={'top':cy1, 'bottom':cy2}, fp_name=footprint_name, text_y_inside_position='center')




    ##################### Output and 3d model ############################
    if lib_by_conn_category:
        lib_name = configuration['lib_name_specific_function_format_string'].format(category=conn_category)
    else:
        lib_name = configuration['lib_name_format_string'].format(series=series, man=manufacturer)

    model_name = '{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}{model3d_path_suffix:s}'.format(
        model3d_path_prefix=global_config.model_3d_prefix, lib_name=lib_name, fp_name=footprint_name,
        model3d_path_suffix=global_config.model_3d_suffix)
    kicad_mod.append(Model(filename=model_name))

    write_footprint(kicad_mod, lib_name, generator_name)


def generate_all(generator_name: str, global_config: GC.GlobalConfig, configuration: dict[str, Any]) -> int:
    num_fps_generated = 0
    # with pincount(s) and partnumber(s) to be generated, build them all in a nested loop
    pinrange = range(4, 31) # 4-30 circuits
    for pincount in pinrange:
        make_module(generator_name, global_config, pincount, configuration)
        num_fps_generated += 1
    return num_fps_generated
