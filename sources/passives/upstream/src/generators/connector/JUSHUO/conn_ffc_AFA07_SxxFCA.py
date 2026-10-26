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
# (C) 2016 by Thomas Pointhuber, <thomas.pointhuber@gmx.at> (TE connectivity)
# (C) 2024 by Uli Köhler <kicad@techoverflow.net> (JUSHUO)
# (C) The KiCad Librarian Team

"""

Family of 1.0mm pitch FFC connectors
https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_JUSHUO-AFA07-S04FCA-00_C262710.pdf

"""
from typing import Any
from KicadModTree import (
    Footprint,
    FootprintType,
    Model,
    Pad,
    PadArray,
    PolygonLine,
    Line,
    Rectangle,
)
from generators.tools.footprint.footprint_text_fields import addTextFields
from kilibs.config import global_config as GC

from generators.tools.footprint import drawing_tools
from generators.tools.footprint.nodes import pin1_arrow
from generators.tools.footprint.save_footprint import write_footprint
from kilibs.geom import Direction, Vector2D


manufacturer = "JUSHUO"
conn_category = "FFC-FPC"

datasheet = "https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_JUSHUO-AFA07-S04FCA-00_C262710.pdf"

lib_by_conn_category = True



def generate_one_footprint(generator_name: str, global_config: GC.GlobalConfig, pincount, configuration):

    footprint_name = f'JUSHUO_AFA07-S{pincount:02g}FCA-00_1x{pincount}-1MP_P1.0mm_Horizontal'

    # "Global" Y offset, so the part is centered for pick & place
    pad_y = -6.75/2 # Total Y dimension of part with retracted actuator,
    # see graphic below "Section A-A" in the datasheet

    pitch = 1 # Attribute of part family

    # Pin pad (1..n) properties
    pad_width = 0.6 # Datasheet, suggested pad layout
    pad_height = 1.8 # Datasheet, suggested pad layout
    pad_x_span = pitch * (pincount - 1)
    pad1_x = pad_x_span / 2.0

    marker_y = 0.8*pad_height # How long the pin 1 marker is in vertical direction

    # How much further than the body do the pins extend in Y direction?
    pin_protrusion_from_body = 1.45 # Below "Section A-A" in datasheet

    # Mounting pad properties
    mounting_pad_width = 2.6
    mounting_pad_height = 3.0
    tab_x = pad_x_span / 2.0 + 1.05 + mounting_pad_width / 2.0
    # 0.23 Determined by measuring footprint against datasheet recommendation (4.57mm)
    tab_y = pad_y + pad_height / 2.0 + mounting_pad_height / 2.0 - 0.23

    # Compute position of top left corner of body (?)
    body_y1 = pad_y + pad_height / 2.0

    # Compute body width
    body_width =  5.05+(pitch*pincount) # Dim "C" in datasheet
    half_body_width = body_width / 2.0

    # Compute width of the actuator (in X direction)
    actuator_width = 7+(pitch*pincount) # Dim "D" in datasheet
    half_actuator_width = actuator_width / 2.0

    # Actuator position in extended and retracted state
    actuator_y1 = body_y1 + 6.75 - pin_protrusion_from_body # "Section A-A" in datasheet
    actuator_y2 = body_y1 + 8.4 - pin_protrusion_from_body # Below "Section A-A" in datasheet

    acutator_height = 1.0 # Extent of actuator part in Y direction. Measured from EasyEDA model.

    body_edge = {
        'left': -half_body_width,
        'right': half_body_width,
        'top': body_y1,
        'bottom': actuator_y1
    }

    silk_clearance = configuration['silk_pad_clearance'] + configuration['silk_line_width']/2
    nudge = configuration['silk_fab_offset']

    courtyard_precision = configuration['courtyard_grid']
    courtyard_clearance = configuration['courtyard_offset']['connector']
    courtyard_x = drawing_tools.round_to_grid(
        half_actuator_width + courtyard_clearance, courtyard_precision
    )
    courtyard_y1 = drawing_tools.round_to_grid(
        pad_y - pad_height / 2.0 - courtyard_clearance, courtyard_precision
    )
    courtyard_y2 = drawing_tools.round_to_grid(
        actuator_y2 + courtyard_clearance, courtyard_precision
    )

    # initialise footprint
    kicad_mod = Footprint(footprint_name, FootprintType.SMD)
    kicad_mod.setDescription(f'JUSHUO FPC connector, {pincount:02g} bottom-side contacts, 1.0mm pitch, 2.5mm height, SMT, {datasheet}')
    kicad_mod.setTags('jushuo fpc')

    # Create pads (1..n)
    kicad_mod.append(PadArray(pincount=pincount, x_spacing=pitch, center=[0,pad_y],
        type=Pad.TYPE_SMT, shape=Pad.SHAPE_ROUNDRECT,
        size=[pad_width, pad_height], layers=Pad.LAYERS_SMT,
        round_radius_handler=global_config.roundrect_radius_handler))

    # Create tab (smt mounting) pads
    mounting_pad_name = global_config.get_pad_name(GC.PadName.MECHANICAL)
    kicad_mod.append(Pad(number=mounting_pad_name,
        at=[-tab_x, tab_y], type=Pad.TYPE_SMT, shape=Pad.SHAPE_ROUNDRECT,
        size=[mounting_pad_width, mounting_pad_height], layers=Pad.LAYERS_SMT,
        round_radius_handler=global_config.roundrect_radius_handler))
    kicad_mod.append(Pad(number=mounting_pad_name,
        at=[tab_x, tab_y], type=Pad.TYPE_SMT, shape=Pad.SHAPE_ROUNDRECT,
        size=[mounting_pad_width, mounting_pad_height], layers=Pad.LAYERS_SMT,
        round_radius_handler=global_config.roundrect_radius_handler))

    # Start of the angled side section of the actuator
    actuator_angle_start_y = actuator_y1-acutator_height - 1.5 # 1.5mm measured from EasyEDA model
    # Where the rectangular (slightly wider) section of the actuator starts
    actuator_rectangular_section_start_y = actuator_angle_start_y - 1 # 1mm measured from EasyEDA model
    actuator_rectangular_section_half_width = half_actuator_width - 0.35 # 0.35: EasyEDA

    # create fab outline and pin 1 marker
    kicad_mod.append(PolygonLine(
        shape=[
            # Left upper corner
            [-half_body_width, body_y1],
            # Right upper corner
            [half_body_width, body_y1],

            # Rectangular section of actuator
            [half_body_width, actuator_rectangular_section_start_y], # Start
            [actuator_rectangular_section_half_width, actuator_rectangular_section_start_y],
            [actuator_rectangular_section_half_width, actuator_angle_start_y], # Down

            # Actuator angled section
            [half_actuator_width, actuator_y1-acutator_height],

            # Front (cable-facing) section of actuator
            [half_actuator_width, actuator_y1],

            # Line from lower right to lower left corner
            [-half_actuator_width, actuator_y1],
            # Actuator angled section
            [-half_actuator_width, actuator_y1-acutator_height],

            # Rectangular section of actuator
            [-actuator_rectangular_section_half_width, actuator_angle_start_y], # Up
            [-actuator_rectangular_section_half_width, actuator_rectangular_section_start_y],
            [-half_body_width, actuator_rectangular_section_start_y], # Start

            # End
            [-half_body_width, body_y1]
        ],
        layer='F.Fab', width=configuration['fab_line_width']))

    kicad_mod.append(PolygonLine(
        shape=[
            [-pad1_x-0.5, body_y1],
            [-pad1_x, body_y1+1],
            [-pad1_x+0.5, body_y1]],
        layer='F.Fab', width=configuration['fab_line_width']))

    # create open actuator outline, only on F.Fab
    kicad_mod.append(PolygonLine(
        shape=[
            [half_body_width, actuator_y1],
            [half_body_width, actuator_y2-acutator_height],
            [half_actuator_width, actuator_y2-acutator_height],
            [half_actuator_width, actuator_y2],
            [-half_actuator_width, actuator_y2],
            [-half_actuator_width, actuator_y2-acutator_height],
            [-half_body_width, actuator_y2-acutator_height],
            [-half_body_width, actuator_y1]],
        layer='F.Fab', width=configuration['fab_line_width']))

    #
    # create silkscreen outline and pin 1 marker
    #

    # Silkscreen outline
    kicad_mod.append(PolygonLine(
        shape=[
            # This line was disabled due to copper/silkscreen clearance
            #[actuator_rectangular_section_half_width+nudge,actuator_rectangular_section_start_y-nudge],
            [actuator_rectangular_section_half_width+nudge, actuator_angle_start_y],

            [half_actuator_width+nudge, actuator_y1-acutator_height],
            [half_actuator_width+nudge, actuator_y1+nudge],
            [-half_actuator_width-nudge, actuator_y1+nudge],
            [-half_actuator_width-nudge, actuator_y1-acutator_height],

            [-actuator_rectangular_section_half_width-nudge, actuator_angle_start_y],
            # This line was disabled due to copper/silkscreen clearance
            # [-actuator_rectangular_section_half_width-nudge,actuator_rectangular_section_start_y-nudge],
        ],
        layer='F.SilkS', width=configuration['silk_line_width']))

    # Pin 1 marker
    # kicad_mod.append(PolygonLine(
    #     shape=[
    #         [-tab_x+mounting_pad_width/2.0+silk_clearance, body_y1-nudge],
    #         [-pad1_x-pad_width/2.0-silk_clearance, body_y1-nudge],
    #         [-pad1_x-pad_width/2.0-silk_clearance, body_y1-nudge-marker_y]],
    #     layer='F.SilkS', width=configuration['silk_line_width']))

    arrow_size_enum = drawing_tools.SilkArrowSize.MEDIUM
    arrow_size, arrow_length = drawing_tools.getStandardSilkArrowSize(
        arrow_size_enum, configuration['silk_line_width'])
    arrow_apex = Vector2D(-tab_x+mounting_pad_width/2.0+silk_clearance+0.1, (body_y1-nudge + body_y1-nudge-marker_y)/2-0.1)

    kicad_mod.append(
        pin1_arrow.Pin1SilkscreenArrow(
            apex_position=arrow_apex,
            angle=Direction.EAST,
            size=arrow_size,
            length=arrow_length,
            layer="F.SilkS",
            line_width_mm=configuration["silk_line_width"],
        )
    )

    # Small line to the right of the pins
    kicad_mod.append(Line(
        start=[pad1_x+pad_width/2.0+silk_clearance, body_y1-nudge],
        end=[tab_x-mounting_pad_width/2.0-silk_clearance, body_y1-nudge],
        layer='F.SilkS', width=configuration['silk_line_width']))

    # create courtyard
    kicad_mod.append(Rectangle(start=[-courtyard_x, courtyard_y1], end=[courtyard_x, courtyard_y2],
        layer='F.CrtYd', width=configuration['courtyard_line_width']))
    # kicad_mod.append(Text(type='reference', text='REF**', size=[1,1], at=[0, courtyard_y1 - label_y_offset], layer='F.SilkS'))
    # kicad_mod.append(Text(type='user', text='${REFERENCE}', size=[1,1], at=[0, tab_y], layer='F.Fab'))
    # kicad_mod.append(Text(type='value', text=footprint_name, at=[0, courtyard_y2 + label_y_offset], layer='F.Fab'))

    ######################### Text Fields ###############################
    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
        courtyard={'top':courtyard_y1, 'bottom':courtyard_y2}, fp_name=footprint_name, text_y_inside_position=[0, tab_y])

    ##################### Output and 3d model ############################
    if lib_by_conn_category:
        lib_name = configuration['lib_name_specific_function_format_string'].format(category=conn_category)
    else:
        lib_name = configuration['lib_name_format_string'].format(man=manufacturer)

    model_name = '{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}{model3d_path_suffix:s}'.format(
        model3d_path_prefix=global_config.model_3d_prefix, lib_name=lib_name, fp_name=footprint_name,
        model3d_path_suffix=global_config.model_3d_suffix)
    kicad_mod.append(Model(filename=model_name))

    write_footprint(kicad_mod, lib_name, generator_name)


def generate_all(generator_name: str, global_config: GC.GlobalConfig, configuration: dict[str, Any]) -> int:
    num_fps_generated = 0
    pincounts = range(4, 30)
    for pincount in pincounts:
        generate_one_footprint(generator_name, global_config, pincount, configuration)
        num_fps_generated += 1
    return num_fps_generated
