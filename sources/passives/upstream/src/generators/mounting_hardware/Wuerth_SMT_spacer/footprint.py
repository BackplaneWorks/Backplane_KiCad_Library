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

from generators.tools.spec.base_spec import BaseSpec
from KicadModTree import *
from generators.tools.footprint.footprint_text_fields import addTextFields
from generators.tools.footprint.save_footprint import write_footprint
from kilibs.config import global_config as GC
from kilibs.config.global_config import GLOBAL_CONFIG
from generators.tools.spec.spec_generator import get_spec_dicts


def roundToBase(value, base):
    return round(value/base) * base

def generate_footprint(generator_name: str, global_config: GC.GlobalConfig, params, mpn):
    fp_params = params['footprint']
    mech_params = params['mechanical']
    part_params = params['parts'][mpn]

    if 'id' in mech_params:
        size = str(mech_params['id'])
    elif 'ext_thread' in mech_params:
        size = str(mech_params['ext_thread']['od'])

    if 'M' not in size:
        size = "{}mm".format(size)

    td = ""
    size_prefix = ""
    hole_type = "inside through hole"
    if 'thread_depth' in part_params:
        hole_type = "inside blind hole"
        td = "_ThreadDepth{}mm".format(part_params['thread_depth'])
    elif 'ext_thread' in mech_params:
        hole_type = "external"
        size_prefix = 'External'

    h = part_params['h'] if 'h' in part_params else part_params['h1']

    suffix = ''
    if 'suffix' in params:
        suffix = '_{}'.format(params['suffix'])

    fp_name = "Mounting_Wuerth_{series}-{size_prefix}{size}_H{h}mm{td}{suffix}_{mpn}".format(
                    size=size, h=h, mpn=mpn, td=td, size_prefix=size_prefix,
                    series=params['series_prefix'], suffix=suffix)

    kicad_mod = Footprint(fp_name, FootprintType.SMD)

    kicad_mod.setDescription("Mounting Hardware, {hole_type} {size}, height {h}, Wuerth electronics {mpn} ({ds:s})".format(size=size, h=h, mpn=mpn, ds=part_params['datasheet'], hole_type=hole_type))

    kicad_mod.setTags('Mounting {} {}'.format(size, mpn))

    kicad_mod.allow_soldermask_bridges = True

    paste_count = fp_params['ring']['paste'].get('paste_count', 4)

    kicad_mod.append(
        RingPad(
            number='1', at=(0, 0),
            size=fp_params['ring']['od'], inner_diameter=fp_params['ring']['id'],
            num_anchor=4, anchor_to_edge_clearance=0.254,
            num_paste_zones=paste_count,
            paste_round_radius_radio=0.25,
            paste_max_round_radius=0.1,
            paste_to_paste_clearance=fp_params['ring']['paste']['clearance'],
            paste_inner_diameter=fp_params['ring']['paste']['id'],
            paste_outer_diameter=fp_params['ring']['paste']['od']
            ))
    if 'npth' in fp_params:
        kicad_mod.append(
            Pad(at=[0, 0], number="",
                type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE, size=fp_params['npth'],
                drill=fp_params['npth'], layers=Pad.LAYERS_NPTH))

    kicad_mod.append(
        Circle(
            center=[0, 0], radius=mech_params['od']/2,
            layer='F.Fab', width=global_config.fab_line_width
            ))

    ########################### CrtYd #################################
    rc = max(mech_params['od'], fp_params['ring']['od'])/2+global_config.get_courtyard_offset(GC.GlobalConfig.CourtyardType.DEFAULT)
    rc = roundToBase(rc, global_config.courtyard_grid)


    kicad_mod.append(
        Circle(
            center=[0, 0], radius=rc,
            layer='F.CrtYd', width=global_config.courtyard_line_width
            ))

    ########################### SilkS #################################



    ######################### Text Fields ###############################
    rb = mech_params['od']/2
    body_edge={'left':-rb, 'right':rb, 'top':-rb, 'bottom':rb}
    addTextFields(kicad_mod=kicad_mod, configuration=global_config, body_edges=body_edge,
        courtyard={'top':-rc, 'bottom':rc}, fp_name=fp_name, text_y_inside_position='center')

    ##################### Output and 3d model ############################
    model3d_path_prefix = global_config.model_3d_prefix
    model3d_path_suffix = global_config.model_3d_suffix

    lib_name = "Mounting_Wuerth"
    model_name = '{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}{model3d_path_suffix:s}'.format(
        model3d_path_prefix=model3d_path_prefix, lib_name=lib_name, fp_name=fp_name,
        model3d_path_suffix=model3d_path_suffix)
    kicad_mod.append(Model(filename=model_name))

    write_footprint(kicad_mod, lib_name, generator_name)


def create_footprints(spec: BaseSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification (not used by this generator).
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
    num_fps_generated = 0
    yaml_files = get_spec_dicts(generator_name)
    for _, yaml_file in yaml_files:
        for _, series in yaml_file.items():
            for mpn in series['parts']:
                generate_footprint(generator_name, GLOBAL_CONFIG, series, mpn)
                num_fps_generated += 1
    return num_fps_generated
