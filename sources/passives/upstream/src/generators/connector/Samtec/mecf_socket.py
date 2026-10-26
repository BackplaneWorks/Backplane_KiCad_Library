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
from KicadModTree import *  # NOQA
from generators.tools.footprint.drawing_tools import round_to_grid
from generators.tools.footprint.footprint_text_fields import addTextFields
from generators.tools.footprint.save_footprint import write_footprint
from kilibs.config import global_config as GC


lib_name_category = 'PCBEdge'

A = {   '05': 8.64,
        '08': 12.45,
        '20': 27.69,
        '30': 40.39,
        '40': 53.09,
        '50': 65.79,
        '60': 78.49,
        '70': 91.19
    }

B = {   '05': 5.08,
        '08': 8.89,
        '20': 24.13,
        '30': 36.83,
        '40': 49.53,
        '50': 62.23,
        '60': 74.93,
        '70': 87.63
    }

C = {   '05': 2.54,
        '08': 3.81,
        '20': 10.16,
        '30': 13.97,
        '40': 20.32,
        '50': 26.67,
        '60': 20.32,
        '70': 34.29
    }

D = {   '08': 1.27,
        '20': 7.62,
        '30': 11.43,
        '40': 17.78,
        '50': 24.13,
        '60': 17.78,
        '70': 31.75
    }


E = {   '05': 12.45,
        '08': 16.26,
        '20': 31.50,
        '30': 44.20,
        '40': 56.90,
        '50': 69.60,
        '60': 82.30,
        '70': 95.00
    }

F = {   '01': 3.81,
        '02': 4.60
    }

G = {   '60': 40.64,
        '70': 73.66
    }

H = {   '60': 38.10,
        '70': 71.12
    }

POL = { '05': [ 3],
        '08': [ 5],
        '20': [15],
        '30': [21],
        '40': [31],
        '50': [41],
        '60': [31, 63],
        '70': [53, 115]
      }

pad_size = [0.66,1.35]

def generate_one_footprint(generator_name: str, global_config: GC.GlobalConfig, weld, pol, pcb_thickness, n, configuration):
    off = configuration['silk_fab_offset']
    CrtYd_offset = configuration['courtyard_offset']['connector']

    fp_name = 'Samtec_MECF-' + n + '-' + pcb_thickness + '-'
    if pol == False:
        fp_name = fp_name + 'NP-'
    fp_name = fp_name + 'L-DV'
    if weld == True:
        fp_name = fp_name + '-WT'

    fp_name += '_{:d}x{:02d}_P{:.2f}mm'.format(2,int(n),1.27)
    if pol:
        fp_name += '_Polarized'

    fp_name = fp_name + '_Socket'
    fp_name = fp_name + '_Horizontal'

    kicad_mod = Footprint(fp_name, FootprintType.SMD)

    description = "Highspeed card edge connector for "
    if pcb_thickness == '01':
        description = description + '1.6mm'
    else:
        description = description + '2.4mm'

    description = description + " PCB's with " + n + " contacts "

    if pol == True:
        description = description + '(polarized)'
    else:
        description = description + '(not polarized)'

    #set the FP description
    kicad_mod.setDescription(description)
    kicad_mod.footprintType = FootprintType.SMD

    tags = "conn samtec card-edge high-speed"

    #set the FP tags
    kicad_mod.setTags(tags)


    top = -(F[pcb_thickness]/2.0 + 0.9)
    bot =  (F[pcb_thickness]/2.0 + 0.9)

    left = 0
    right = 0
    if weld == True:
        left = -(E[n]/2.0 + 0.91)
        right = (E[n]/2.0 + 0.91)
    else:
        left = -(A[n]/2.0 + 0.91)
        right = (A[n]/2.0 + 0.91)

    body_edge={
        'left': left,
        'right': right,
        'top': top,
        'bottom': bot
    }


    top_left =  [left, top]
    bot_right = [ right, bot]

    # create Fab (exact outline)
    kicad_mod.append(Line(start=[left + 1.27, bot], end=[right, bot],
        layer='F.Fab', width=configuration['fab_line_width']))   #bot line
    kicad_mod.append(Line(start=[left, top], end=[ right, top],
        layer='F.Fab', width=configuration['fab_line_width']))   #top line
    kicad_mod.append(Line(start=[left, bot - 1.27], end=[left, top],
        layer='F.Fab', width=configuration['fab_line_width']))   #left line
    kicad_mod.append(Line(start=[right, bot], end=[ right, top],
        layer='F.Fab', width=configuration['fab_line_width']))   #right line
    kicad_mod.append(Line(start=[left, bot - 1.27], end=[left + 1.27, bot],
        layer='F.Fab', width=configuration['fab_line_width']))   #corner

    top = top - off
    bot = bot + off
    left = left - off
    right = right + off

    # create silscreen (exact + 0.11)
    kicad_mod.append(Line(start=[round(left, 2) + 1.27, round(bot, 2)],
                          end=[round(right, 2), round(bot, 2)],
                          layer='F.SilkS', width=configuration['silk_line_width'])) #bot line
    kicad_mod.append(Line(start=[round(left, 2), round(top, 2)],
                          end=[round(right, 2), round(top, 2)],
                          layer='F.SilkS', width=configuration['silk_line_width'])) #top line
    kicad_mod.append(Line(start=[round(left, 2), round(bot, 2) - 1.27],
                          end=[round(left, 2), round(top, 2)],
                          layer='F.SilkS', width=configuration['silk_line_width'])) #left line
    kicad_mod.append(Line(start=[round(right, 2), round( bot, 2)],
                          end=[round(right, 2), round(top, 2)],
                          layer='F.SilkS', width=configuration['silk_line_width'])) #right line
    kicad_mod.append(Line(start=[round(left, 2) + 1.27, round(bot, 2) ],
                          end=[round(left, 2), round(bot, 2) - 1.27],
                          layer='F.SilkS', width=configuration['silk_line_width']))   #corner


    top = round_to_grid(body_edge['top'] - CrtYd_offset, configuration['courtyard_grid'])
    bot = round_to_grid(body_edge['bottom'] + CrtYd_offset, configuration['courtyard_grid'])
    left = round_to_grid(body_edge['left'] - CrtYd_offset, configuration['courtyard_grid'])
    right = round_to_grid(body_edge['right'] + CrtYd_offset, configuration['courtyard_grid'])

    cy1 = top
    cy2 = bot

    # create courtyard (exact + 0.25)
    kicad_mod.append(Rectangle(start=[round(left,2), round(top,2)],
                          end=[round(right,2), round(bot,2)],
                          layer='F.CrtYd', width=configuration['courtyard_line_width']))





    # create pads
    for i in range(0,int(n)):
        start = - B[n]/2.0

        if pol == True:
            if (i*2+1) not in POL[n]:
                kicad_mod.append(Pad(number=i*2 + 1, type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                    at=[start + i*1.27, F[pcb_thickness]/2.0], size=pad_size, layers=Pad.LAYERS_SMT))
                kicad_mod.append(Pad(number=i*2 + 2, type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                    at=[start + i*1.27, - F[pcb_thickness]/2.0], size=pad_size, layers=Pad.LAYERS_SMT))
        else:
            kicad_mod.append(Pad(number=i*2 + 1, type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                at=[start + i*1.27, F[pcb_thickness]/2.0], size=pad_size, layers=Pad.LAYERS_SMT))
            kicad_mod.append(Pad(number=i*2 + 2, type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                at=[start + i*1.27, - F[pcb_thickness]/2.0], size=pad_size, layers=Pad.LAYERS_SMT))



    drill = 1.45
    kicad_mod.append(Pad(number="", type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE,
        at=[-A[n]/2.0, 0], size=drill, drill=drill, layers=Pad.LAYERS_NPTH))
    kicad_mod.append(Pad(number="", type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE,
        at=[A[n]/2.0, 1.0], size=drill, drill=drill, layers=Pad.LAYERS_NPTH))

    if weld == True:
        size = [1.5,1.5]
        drill = 1
        kicad_mod.append(Pad(number="", type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE,
            at=[-E[n]/2.0, 0], size=size, drill=drill, layers=Pad.LAYERS_THT))
        kicad_mod.append(Pad(number="", type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE,
            at=[ E[n]/2.0, 0.0], size=size, drill=drill, layers=Pad.LAYERS_THT))

    # output kicad model
    #print(kicad_mod
    # kicad_mod.append(Property(name=Property.REFERENCE, text='REF**', at=[0,3.81], layer='F.SilkS'))
    # kicad_mod.append(Text(text='${REFERENCE}', at=[0,0], layer='F.Fab'))
    # kicad_mod.append(Property(name=Property.VALUE, text=fp_name, at=[0,-3.81], layer='F.Fab'))
    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
        courtyard={'top':cy1, 'bottom':cy2}, fp_name=fp_name, text_y_inside_position='center')

    ##################### Output and 3d model ############################
    model3d_path_prefix = configuration.get('3d_model_prefix',global_config.model_3d_prefix)
    model3d_path_suffix = configuration.get('3d_model_suffix',global_config.model_3d_suffix)

    #lib_name = configuration['lib_name_format_string'].format(series=series, man=manufacturer)
    lib_name = configuration['lib_name_specific_function_format_string'].format(category=lib_name_category)
    model_name = '{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}{model3d_path_suffix:s}'.format(
        model3d_path_prefix=model3d_path_prefix, lib_name=lib_name, fp_name=fp_name,
        model3d_path_suffix=model3d_path_suffix)
    kicad_mod.append(Model(filename=model_name))

    write_footprint(kicad_mod, lib_name, generator_name)


def generate_all(generator_name: str, global_config: GC.GlobalConfig, configuration: dict[str, Any]) -> int:
    num_fps_generated = 0
    for weld in [True, False]:
        for pol in [True, False]:
            for pcb_thickness in ['01', '02']:
                for n in ['05', '08', '20', '30', '40', '50', '60', '70']:
                    generate_one_footprint(generator_name, global_config, weld, pol, pcb_thickness, n, configuration)
                    num_fps_generated += 1
    return num_fps_generated



