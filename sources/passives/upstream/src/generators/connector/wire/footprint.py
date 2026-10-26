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

from copy import deepcopy

from KicadModTree import *  # NOQA
from kilibs.geom import GeomLine, GeomCircle
from kilibs.geom.operations import split
from generators.tools.footprint.drawing_tools import round_to_grid_up
from generators.tools.footprint.footprint_text_fields import addTextFields
from kilibs.config import global_config as GC

from generators.tools.spec.base_spec import BaseSpec
from generators.tools.spec.spec_generator import get_spec_file_names
from generators.tools.footprint.save_footprint import write_footprint
from kilibs.config.global_config import GLOBAL_CONFIG
from generators.tools.cli_args import CLI_ARGS
from ..config import CONNECTOR_CONFIG


FOOTPRINT_TYPES = {
    'plain':{
        'name': '',
        'description': '',
        'tag': '',
        'relief_count': 0
    },
    'relief':{
        'name': '_Relief',
        'description': ' with feed through strain relief',
        'tag': ' strain-relief',
        'relief_count': 1
    },
    'relief2x':{
        'name': '_Relief2x',
        'description': ' with double feed through strain relief',
        'tag': ' double-strain-relief',
        'relief_count': 2
    }
}

def bend_radius(wire_def):
    return wire_def['outer_diameter'] * 3

def fp_name_gen(wire_def, fp_type, pincount, pitch):
    if 'area' in wire_def:
        size_code = '{:g}sqmm'.format(wire_def['area'])

    return 'SolderWire-{}_1x{:02d}{}_D{:g}mm_OD{:g}mm{}'.format(
                    size_code, pincount,
                    '' if pincount == 1 else '_P{:g}mm'.format(pitch),
                    wire_def['diameter'], wire_def['outer_diameter'], fp_type
                )

def description_gen(wire_def, fp_type, pincount, pitch):
    if 'area' in wire_def:
        size_code = '{:g} mm²'.format(wire_def['area'])

    d1 = 'for a single {size:s} wire' if pincount == 1 else 'for {count:d} times {size:s} wires'

    return (
        'Soldered wire connection{}, {}, '
        '{} insulation, '
        'conductor diameter {:g}mm, outer diameter {:g}mm, '
        'size source {}, '
        'bend radius 3 times outer diameter'
        .format(
                fp_type, d1.format(count=pincount, size=size_code),
                wire_def['insulation'],
                wire_def['diameter'], wire_def['outer_diameter'],
                wire_def['source']
            )
    )

def tag_gen(wire_def, fp_type, pincount, pitch):
    if 'area' in wire_def:
        size_code = '{:g}sqmm'.format(wire_def['area'])

    return 'connector wire {}{}'.format(size_code, fp_type)


def make_fp(generator_name:str, global_config: GC.GlobalConfig, wire_def, fp_type, pincount, configuration):
    crtyd_off= configuration['courtyard_offset']['connector']
    silk_pad_off = configuration['silk_pad_clearance'] + configuration['silk_line_width']/2

    pad_drill = max(wire_def['diameter'] + configuration['min_pad_drill_inc'],
                    wire_def['diameter'] * configuration['pad_drill_factor'])
    pad_drill = round_to_grid_up(pad_drill, 0.05, epsilon=1e-7)
    pad_size = max(pad_drill + 1, wire_def['outer_diameter'])

    npth_drill = wire_def['outer_diameter'] + configuration['relief_drill_inc']
    npth_offset = bend_radius(wire_def)*2

    pitch = max(2*wire_def['outer_diameter'], pad_size+2, npth_drill+2)

    fp_name = fp_name_gen(wire_def, fp_type['name'], pincount, pitch)

    kicad_mod = Footprint(fp_name, FootprintType.UNSPECIFIED)
    kicad_mod.setDescription(description_gen(wire_def, fp_type['description'], pincount, pitch))

    kicad_mod.setTags(tag_gen(wire_def, fp_type['tag'], pincount, pitch))

    kicad_mod.excludeFromBOM = True
    kicad_mod.excludeFromPositionFiles = True

    prototype = Translation(0, 0)
    kicad_mod.append(PadArray(
            initial=1, increment=1, pincount=pincount,
            type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE,
            start=(0, 0), spacing=(pitch, 0),
            drill=pad_drill, size=pad_size,
            round_radius_handler=global_config.roundrect_radius_handler,
            layers=Pad.LAYERS_THT
        ))

    for i in range(fp_type['relief_count']):
        prototype.append(Pad(
                number='', type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE,
                at=(0, (i+1)*npth_offset), drill=npth_drill, size=npth_drill,
                layers=Pad.LAYERS_NPTH
            ))

    ######################### Fab Graphic ###############################
    for i in range(fp_type['relief_count']+1):
        prototype.append(Circle(
                center=(0, i*npth_offset), radius=wire_def['outer_diameter']/2,
                layer='F.Fab', width=configuration['fab_line_width']
            ))

    # wire on top side
    if fp_type['relief_count']>0:
        for i in range((fp_type['relief_count']+1)//2):
            sy = 2*i * npth_offset
            ey = (2*i+1) * npth_offset
            prototype.append(Line(
                    start=(-wire_def['outer_diameter']/2, sy),
                    end=(-wire_def['outer_diameter']/2, ey),
                    layer='F.Fab', width=configuration['fab_line_width']
                ))
            prototype.append(Line(
                    start=(wire_def['outer_diameter']/2, sy),
                    end=(wire_def['outer_diameter']/2, ey),
                    layer='F.Fab', width=configuration['fab_line_width']
                ))

    if fp_type['relief_count']>1:
        for i in range(fp_type['relief_count']):
            prototype.append(Circle(
                    center=(0, (i+1)*npth_offset), radius=wire_def['outer_diameter']/2,
                    layer='B.Fab', width=configuration['fab_line_width']
                ))
        for i in range((fp_type['relief_count'])//2):
            sy = (2*i+1) * npth_offset
            ey = (2*i+2) * npth_offset
            prototype.append(Line(
                    start=(-wire_def['outer_diameter']/2, sy),
                    end=(-wire_def['outer_diameter']/2, ey),
                    layer='B.Fab', width=configuration['fab_line_width']
                ))
            prototype.append(Line(
                    start=(wire_def['outer_diameter']/2, sy),
                    end=(wire_def['outer_diameter']/2, ey),
                    layer='B.Fab', width=configuration['fab_line_width']
                ))

    ######################### Silk Graphic ##############################

    silk_x = wire_def['outer_diameter']/2 + configuration['silk_fab_offset']

    splitting_circle = GeomCircle(center=(0,0), radius=(npth_drill/2 + silk_pad_off))
    silk_helper_line = GeomLine(start=(silk_x, 0), end=(silk_x, npth_offset))
    silk_helper_line = split(shape_to_split=silk_helper_line, splitting_shape=splitting_circle)[1]

    silk_y_rel_npth = silk_helper_line.start['x']

    if fp_type['relief_count']>0:
        if silk_x > pad_size/2 + silk_pad_off:
            top = 0
        else:
            top = pad_size/2 + silk_pad_off

        bottom = npth_offset - silk_y_rel_npth
        prototype.append(Line(
                start=(silk_x, top), end=(silk_x, bottom),
                layer='F.SilkS', width=configuration['silk_line_width']
            ))
        prototype.append(Line(
                start=(-silk_x, top), end=(-silk_x, bottom),
                layer='F.SilkS', width=configuration['silk_line_width']
            ))

    if fp_type['relief_count']>1:
        for i in range(fp_type['relief_count']-1):
            layer = 'F.SilkS' if i%2 == 1 else 'B.SilkS'

            top = (i+1)*npth_offset + silk_y_rel_npth
            bottom = (i+2)*npth_offset - silk_y_rel_npth

            prototype.append(Line(
                    start=(silk_x, top), end=(silk_x, bottom),
                    layer=layer, width=configuration['silk_line_width']
                ))
            prototype.append(Line(
                    start=(-silk_x, top), end=(-silk_x, bottom),
                    layer=layer, width=configuration['silk_line_width']
                ))

    ########################## Courtyard ################################

    crtyd_x = max(pad_size, npth_drill)/2 + crtyd_off
    crtyd_top = -max(pad_size, wire_def['outer_diameter'])/2 - crtyd_off
    crtyd_top_main = crtyd_top
    if fp_type['relief_count'] == 0:
        crtyd_bottom = -crtyd_top
        crtyd_bottom_main = crtyd_bottom
    else:
        crtyd_bottom = npth_offset + npth_drill/2 + crtyd_off
        crtyd_bottom_main = npth_offset*fp_type['relief_count'] + npth_drill/2 + crtyd_off

    layer = 'F.CrtYd'
    prototype.append(Rectangle(
            start=Vector2D(-crtyd_x, crtyd_top).round_to(configuration['courtyard_grid']),
            end=Vector2D(crtyd_x, crtyd_bottom).round_to(configuration['courtyard_grid']),
            layer=layer, width=configuration['courtyard_line_width']
        ))

    if fp_type['relief_count']>0:
        i = fp_type['relief_count']
        layer = 'B.CrtYd' if i%2 == 1 else 'F.CrtYd'

        crtyd_top = (i)*npth_offset - (npth_drill/2 + crtyd_off)
        crtyd_bottom = (i)*npth_offset + npth_drill/2 + crtyd_off

        prototype.append(Rectangle(
                start=Vector2D(-crtyd_x, crtyd_top).round_to(configuration['courtyard_grid']),
                end=Vector2D(crtyd_x, crtyd_bottom).round_to(configuration['courtyard_grid']),
                layer=layer, width=configuration['courtyard_line_width']
            ))

    if fp_type['relief_count']>1:
        for i in range(fp_type['relief_count']-1):
            layer = 'F.CrtYd' if i%2 == 1 else 'B.CrtYd'

            crtyd_top = (i+1)*npth_offset - (npth_drill/2 + crtyd_off)
            crtyd_bottom = (i+2)*npth_offset + npth_drill/2 + crtyd_off

            prototype.append(Rectangle(
                    start=Vector2D(-crtyd_x, crtyd_top).round_to(configuration['courtyard_grid']),
                    end=Vector2D(crtyd_x, crtyd_bottom).round_to(configuration['courtyard_grid']),
                    layer=layer, width=configuration['courtyard_line_width']
                ))

    ######################### Text Fields ###############################
    center_x = (pincount-1)*pitch/2

    y1 = -wire_def['outer_diameter']/2
    y2 = wire_def['outer_diameter']/2 + (npth_offset if fp_type['relief_count'] > 0 else 0)

    if pincount%2 == 0 and fp_type['relief_count'] == 0:
        y1 = crtyd_top_main
        y2 = crtyd_bottom_main

    addTextFields(
        kicad_mod=kicad_mod, configuration=configuration,
        body_edges={
            'left':center_x - wire_def['outer_diameter']/2,
            'right':center_x + wire_def['outer_diameter']/2,
            'top':y1,
            'bottom':y2
            },
        courtyard={'top':crtyd_top_main, 'bottom':crtyd_bottom_main},
        fp_name=fp_name, text_y_inside_position='center',
        allow_rotation=True
        )

    ##################### Output and 3d model ############################
    for i in range(pincount):
        prototype.offset.x = i*pitch
        kicad_mod.append(deepcopy(prototype))

    model3d_path_prefix = configuration.get('3d_model_prefix',global_config.model_3d_prefix)
    model3d_path_suffix = configuration.get('3d_model_suffix',global_config.model_3d_suffix)

    lib_name = 'Connector_Wire'
    model_name = '{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}{model3d_path_suffix:s}'.format(
        model3d_path_prefix=model3d_path_prefix, lib_name=lib_name, fp_name=fp_name,
        model3d_path_suffix=model3d_path_suffix)
    kicad_mod.append(Model(filename=model_name))

    write_footprint(kicad_mod, lib_name, generator_name)


def make_for_wire(generator_name:str, global_config, wire_def, configuration):
    for fp_type in FOOTPRINT_TYPES:
        for i in range(6):
            make_fp(generator_name, global_config, wire_def, FOOTPRINT_TYPES[fp_type], i+1, configuration)

def make_for_file(generator_name:str, global_config, filepath, configuration) -> int:
    with open(filepath, 'r') as wire_definition:
        wires = yaml.safe_load(wire_definition)
        for w in wires:
            make_for_wire(generator_name, global_config, wires[w], configuration)
    return len(wires) * len(FOOTPRINT_TYPES) * 6


def create_footprints(spec: BaseSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification (not used by this generator).
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
    num_fps_generated = 0
    connector_config = CONNECTOR_CONFIG.copy()
    connector_config['pad_drill_factor'] = CLI_ARGS.wire_connector_pad_drill_factor
    connector_config['min_pad_drill_inc'] = CLI_ARGS.wire_connector_minimum_pad_drill_oversize
    connector_config['relief_drill_inc'] = CLI_ARGS.wire_connector_relief_drill_oversize

    for filepath in get_spec_file_names(generator_name):
        num_fps_generated += make_for_file(generator_name, GLOBAL_CONFIG, filepath, connector_config)
    return num_fps_generated
