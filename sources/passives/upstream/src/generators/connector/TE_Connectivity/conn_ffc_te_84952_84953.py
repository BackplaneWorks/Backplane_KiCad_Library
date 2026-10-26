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
# (C) 2016 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>
# (C) The KiCad Librarian Team

"""

This family of parts is spread over 2 datasheets, depending on the contact side:

Bottom contact:
http://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=84952&DocType=Customer+Drawing&DocLang=English&DocFormat=pdf&PartCntxt=1-84952-5

Top contact:
http://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=84953&DocType=Customer+Drawing&DocLang=English&DocFormat=pdf&PartCntxt=1-84953-5

"""

from math import sqrt
import argparse
import yaml
from typing import Any

from KicadModTree import *
from generators.tools.footprint.drawing_tools import round_to_grid
from generators.tools.footprint.footprint_text_fields import addTextFields
from generators.tools.footprint.save_footprint import write_footprint
from kilibs.config import global_config as GC


manufacturer = "TE-Connectivity"
conn_category = "FFC-FPC"

lib_by_conn_category = True

partnumbers = ["84952","84953"]
pincounts = range(4, 31)

def generate_one_footprint(generator_name: str, global_config: GC.GlobalConfig,
                           partnumber, pincount, configuration):
    # only double digit pincount parts have leading chars on the PN
    if pincount >= 10:
        pn_prefix = str(pincount)[0] + "-"
    else:
        pn_prefix = ""

    footprint_name = 'TE_{pnp}{pn:s}-{pns}_1x{pc:02g}-1MP_P1.0mm_Horizontal'\
        .format(pnp=pn_prefix, pn=partnumber, pns=str(pincount)[-1], pc=pincount)

    # calculate working values
    pitch = 1
    pad_y = -1.8
    pad_width = 0.61
    pad_height = 2
    pad_x_span = pitch * (pincount - 1)
    pad1_x = pad_x_span / 2.0

    tab_width = 4.33 - 1.65
    tab_height = 3.6
    tab_x = pad_x_span / 2.0 + 1.65 + tab_width / 2.0
    tab_y = pad_y + pad_height / 2.0 + tab_height / 2.0

    body_y1 = pad_y + pad_height / 2.0
    half_body_width = pad_x_span / 2.0 + 3.435
    actuator_y1 = body_y1 + 5.4
    actuator_y2 = body_y1 + 7.3
    half_actuator_width = pad_x_span / 2.0 + 4.46
    ear_height = 0.89

    body_edge = {
        'left': -half_body_width,
        'right': half_body_width,
        'top': body_y1,
        'bottom': actuator_y1
    }

    silk_clearance = configuration['silk_pad_clearance'] + configuration['silk_line_width']/2
    marker_y = 1.8
    nudge = configuration['silk_fab_offset']

    courtyard_precision = configuration['courtyard_grid']
    courtyard_clearance = configuration['courtyard_offset']['connector']
    courtyard_x = round_to_grid(half_actuator_width + courtyard_clearance, courtyard_precision)
    courtyard_y1 = round_to_grid(pad_y - pad_height / 2.0 - courtyard_clearance, courtyard_precision)
    courtyard_y2 = round_to_grid(actuator_y2 + courtyard_clearance, courtyard_precision)

    label_y_offset = 0.7

    # select correct datasheet URL depending on part number
    if partnumber == "84952":
        datasheet = "http://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=84952&DocType=Customer+Drawing&DocLang=English&DocFormat=pdf&PartCntxt=84952-4"
        side = "bottom"
    elif partnumber == "84953":
        datasheet = "http://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=84953&DocType=Customer+Drawing&DocLang=English&DocFormat=pdf&PartCntxt=84953-4"
        side = "top"

    # initialise footprint
    kicad_mod = Footprint(footprint_name, FootprintType.SMD)
    kicad_mod.setDescription('TE FPC connector, {pc:02g} {side}-side contacts, 1.0mm pitch, 1.0mm height, SMT, {ds}'.format(pc=pincount, side=side, ds=datasheet))
    kicad_mod.setTags('te fpc {:s}'.format(partnumber))

    # create pads
    kicad_mod.append(PadArray(pincount=pincount, x_spacing=pitch, center=[0,pad_y],
        type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
        size=[pad_width, pad_height], layers=Pad.LAYERS_SMT))

    # create tab (smt mounting) pads
    mounting_pad_name = global_config.get_pad_name(GC.PadName.MECHANICAL)
    kicad_mod.append(Pad(number=mounting_pad_name,
        at=[-tab_x, tab_y], type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
        size=[tab_width, tab_height], layers=Pad.LAYERS_SMT))
    kicad_mod.append(Pad(number=mounting_pad_name,
        at=[tab_x, tab_y], type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
        size=[tab_width, tab_height], layers=Pad.LAYERS_SMT))

    # create fab outline and pin 1 marker
    kicad_mod.append(PolygonLine(
        shape=[
            [-half_body_width, body_y1],
            [half_body_width, body_y1],
            [half_body_width, actuator_y1-ear_height],
            [half_actuator_width, actuator_y1-ear_height],
            [half_actuator_width, actuator_y1],
            [-half_actuator_width, actuator_y1],
            [-half_actuator_width, actuator_y1-ear_height],
            [-half_body_width, actuator_y1-ear_height],
            [-half_body_width, body_y1]],
        layer='F.Fab', width=configuration['fab_line_width']))

    kicad_mod.append(PolygonLine(
        shape=[
            [-pad1_x-0.5, body_y1],
            [-pad1_x, body_y1+1],
            [-pad1_x+0.5, body_y1]],
        layer='F.Fab', width=configuration['fab_line_width']))

    # create open actuator outline
    kicad_mod.append(PolygonLine(
        shape=[
            [half_body_width, actuator_y1],
            [half_body_width, actuator_y2-ear_height],
            [half_actuator_width, actuator_y2-ear_height],
            [half_actuator_width, actuator_y2],
            [-half_actuator_width, actuator_y2],
            [-half_actuator_width, actuator_y2-ear_height],
            [-half_body_width, actuator_y2-ear_height],
            [-half_body_width, actuator_y1]],
        layer='F.Fab', width=configuration['fab_line_width']))

    # create silkscreen outline and pin 1 marker
    kicad_mod.append(PolygonLine(
        shape=[
            [half_body_width+nudge, tab_y+tab_height/2.0+silk_clearance],
            [half_body_width+nudge, actuator_y1-ear_height-nudge],
            [half_actuator_width+nudge, actuator_y1-ear_height-nudge],
            [half_actuator_width+nudge, actuator_y1+nudge],
            [-half_actuator_width-nudge, actuator_y1+nudge],
            [-half_actuator_width-nudge, actuator_y1-ear_height-nudge],
            [-half_body_width-nudge, actuator_y1-ear_height-nudge],
            [-half_body_width-nudge, tab_y+tab_height/2.0+silk_clearance]],
        layer='F.SilkS', width=configuration['silk_line_width']))

    kicad_mod.append(PolygonLine(
        shape=[
            [-tab_x+tab_width/2.0+silk_clearance, body_y1-nudge],
            [-pad1_x-pad_width/2.0-silk_clearance, body_y1-nudge],
            [-pad1_x-pad_width/2.0-silk_clearance, body_y1-nudge-marker_y]],
        layer='F.SilkS', width=configuration['silk_line_width']))

    kicad_mod.append(Line(
        start=[pad1_x+pad_width/2.0+silk_clearance, body_y1-nudge],
        end=[tab_x-tab_width/2.0-silk_clearance, body_y1-nudge],
        layer='F.SilkS', width=configuration['silk_line_width']))

    # create courtyard
    kicad_mod.append(Rectangle(start=[-courtyard_x, courtyard_y1], end=[courtyard_x, courtyard_y2],
        layer='F.CrtYd', width=configuration['courtyard_line_width']))
    # kicad_mod.append(Property(name=Property.REFERENCE, text='REF**', size=[1,1], at=[0, courtyard_y1 - label_y_offset], layer='F.SilkS'))
    # kicad_mod.append(Text(text='${REFERENCE}', size=[1,1], at=[0, tab_y], layer='F.Fab'))
    # kicad_mod.append(Property(name=Property.VALUE, text=footprint_name, at=[0, courtyard_y2 + label_y_offset], layer='F.Fab'))

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
    # with pincount(s) and partnumber(s) to be generated, build them all in a nested loop
    for partnumber in partnumbers:
        for pincount in pincounts:
            generate_one_footprint(generator_name, global_config, partnumber, pincount, configuration)
        num_fps_generated += len(pincounts)
    return num_fps_generated


