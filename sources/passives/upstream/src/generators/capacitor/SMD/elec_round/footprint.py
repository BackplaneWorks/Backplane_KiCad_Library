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
import os

from kilibs.config import ipc_rules
from kilibs.util.toleranced_size import TolerancedSize
from KicadModTree import *  # NOQA
from generators.tools.footprint.ipc_pad_size_calculators import ipc_gull_wing

from generators.tools.footprint.save_footprint import write_footprint
from generators.tools.spec.base_spec import BaseSpec
from generators.tools.spec.spec_generator import get_spec_file_names
from generators.tools.cli_args import CLI_ARGS
from kilibs.config.global_config import GLOBAL_CONFIG


def create_footprints(spec: BaseSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification (not used by this generator).
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
    series_path = os.path.expandvars(str(CLI_ARGS.capacitor_config))
    with open(series_path, 'r') as config_stream:
        configuration = yaml.safe_load(config_stream)

    ipc_defs = ipc_rules.IpcRules.from_file(CLI_ARGS.capacitor_ipc_rules)

    configuration['ipc_density'] = ipc_rules.IpcDensity(CLI_ARGS.ipc_density)
    configuration['force_rectangular_pads'] = CLI_ARGS.force_rectangular_pads
    
    num_fps_generated = 0
    for filepath in get_spec_file_names(generator_name):
        with open(filepath, 'r') as stream:
            yaml_parsed = yaml.safe_load(stream)
            for footprint in yaml_parsed:
                num_fps_generated += create_footprint(generator_name, footprint, configuration, ipc_defs, **yaml_parsed.get(footprint))
    return num_fps_generated


def create_footprint(generator_name, name, configuration, ipc_definitions, **kwargs) -> int:
    courtyard_offset = GLOBAL_CONFIG.get_courtyard_offset(GLOBAL_CONFIG.CourtyardType.DEFAULT)
    kicad_mod = Footprint(name, FootprintType.SMD)

    # init kicad footprint
    datasheet = ", " + kwargs['datasheet'] if 'datasheet' in kwargs else ""
    description = "SMD capacitor, aluminum electrolytic"
    tags = 'capacitor electrolytic'
    if name[:2] == "C_":
        description += " nonpolar"
        tags += " nonpolar"
    if 'extra_description' in kwargs:
        description += ", " + kwargs['extra_description']

    # ensure all provided dimensions are fully toleranced
    device_dimensions = {
        'body_length': TolerancedSize.from_yaml(kwargs, base_name='body_length'),
        'body_width': TolerancedSize.from_yaml(kwargs, base_name='body_width'),
        'body_height': TolerancedSize.from_yaml(kwargs, base_name='body_height'),
        'body_diameter': TolerancedSize.from_yaml(kwargs, base_name='body_diameter')
    }

    # for ease of use, capture nominal body and pad sizes
    body_size = {
        'length': device_dimensions['body_length'].nominal,
        'width': device_dimensions['body_width'].nominal,
        'height': device_dimensions['body_height'].nominal,
        'diameter': device_dimensions['body_diameter'].nominal
    }

    description += ", " + str(body_size['diameter']) + "x" + str(body_size['height']) + "mm"
    kicad_mod.setDescription(description + datasheet)
    kicad_mod.setTags(tags)

    # set general values
    text_offset_y = body_size['width'] / 2.0 + courtyard_offset + 0.8

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
    fab_text_size = device_dimensions["body_diameter"].nominal / 5.0
    fab_text_size = min(fab_text_size, fab_text_config.size_max)
    fab_text_size = max(fab_text_size, fab_text_config.size_min)
    fab_text_thickness = fab_text_size * fab_text_config.thickness_ratio
    kicad_mod.append(Text(text='${REFERENCE}', at=[0, 0], layer='F.Fab', size=[
                    fab_text_size, fab_text_size], thickness=fab_text_thickness))

    # create pads
    # all pads have these properties
    pad_params = {
        "type": Pad.TYPE_SMT,
        "layers": Pad.LAYERS_SMT,
        "shape": Pad.SHAPE_RECT,
    }

    # prefer IPC-7351C compliant rounded rectangle pads
    if not configuration['force_rectangular_pads']:
        pad_params['shape'] = Pad.SHAPE_ROUNDRECT
        pad_params['round_radius_handler'] = GLOBAL_CONFIG.roundrect_radius_handler

    # prefer calculating pads from lead dimensions per IPC
    # fall back to using pad sizes directly if necessary
    if ('lead_length' in kwargs) and ('lead_width' in kwargs) and ('lead_spacing' in kwargs):
        # gather IPC data (unique parameters for >= 10mm tall caps)
        ipc_density_suffix = '' if body_size['height'] < 10 else '_ge_10mm'
        ipc_device_class = 'ipc_spec_capae_crystal' + ipc_density_suffix
        ipc_offsets = ipc_definitions.get_class(ipc_device_class).get_offsets(configuration['ipc_density'])
        ipc_round_base = ipc_definitions.get_class(ipc_device_class).roundoff

        manf_tol = ipc_rules.ManufacturingTolerance(
            manufacturing_tolerance=configuration.get("manufacturing_tolerance", 0.1),
            placement_tolerance=configuration.get("placement_tolerance", 0.05),
        )

        # # fully tolerance lead dimensions; leads are dimensioned like SOIC so use gullwing calculator
        device_dimensions['lead_width'] = TolerancedSize.from_yaml(kwargs, base_name='lead_width')
        device_dimensions['lead_spacing'] = TolerancedSize.from_yaml(kwargs, base_name='lead_spacing')
        device_dimensions['lead_length'] = TolerancedSize.from_yaml(kwargs, base_name='lead_length')
        device_dimensions['lead_outside'] = TolerancedSize(maximum =
            device_dimensions['lead_spacing'].maximum +
            device_dimensions.get('lead_length').maximum * 2,
            minimum = device_dimensions['lead_spacing'].minimum +
            device_dimensions.get('lead_length').minimum * 2)

        Gmin, Zmax, Xmax = ipc_gull_wing(ipc_offsets, ipc_round_base, manf_tol,
                device_dimensions['lead_width'], device_dimensions['lead_outside'],
                lead_len=device_dimensions.get('lead_length'))

        pad_params['size'] = [(Zmax - Gmin) / 2.0, Xmax]

        x_pad_spacing = (Zmax + Gmin) / 4.0
    elif ('pad_length' in kwargs) and ('pad_width' in kwargs) and ('pad_spacing' in kwargs):
        x_pad_spacing = kwargs['pad_spacing'] / 2.0 + kwargs['pad_length'] / 2.0
        pad_params['size'] = [kwargs['pad_length'], kwargs['pad_width']]
    else:
        raise KeyError("Provide all three 'pad' or 'lead' properties ('_spacing', '_length', and '_width')")

    kicad_mod.append(Pad(number=1, at=[-x_pad_spacing, 0], **pad_params))
    kicad_mod.append(Pad(number=2, at=[x_pad_spacing, 0], **pad_params))

    # create fabrication layer
    fab_x = body_size['length'] / 2.0
    fab_y = body_size['width'] / 2.0

    if kwargs['pin1_chamfer'] == 'auto':
        fab_edge = min(fab_x/2.0, fab_y/2.0, GLOBAL_CONFIG.fab_pin1_marker_length)
    else:
        fab_edge = kwargs['pin1_chamfer']
    fab_x_edge = fab_x - fab_edge
    fab_y_edge = fab_y - fab_edge
    kicad_mod.append(Line(start=[fab_x, -fab_y], end=[fab_x, fab_y], layer='F.Fab', width=GLOBAL_CONFIG.fab_line_width))
    kicad_mod.append(Line(start=[-fab_x_edge, -fab_y], end=[fab_x, -fab_y], layer='F.Fab', width=GLOBAL_CONFIG.fab_line_width))
    kicad_mod.append(Line(start=[-fab_x_edge, fab_y], end=[fab_x, fab_y], layer='F.Fab', width=GLOBAL_CONFIG.fab_line_width))
    if fab_edge > 0:
        kicad_mod.append(Line(start=[-fab_x, -fab_y_edge], end=[-fab_x, fab_y_edge], layer='F.Fab', width=GLOBAL_CONFIG.fab_line_width))
        kicad_mod.append(Line(start=[-fab_x, -fab_y_edge], end=[-fab_x_edge, -fab_y], layer='F.Fab', width=GLOBAL_CONFIG.fab_line_width))
    kicad_mod.append(Line(start=[-fab_x, fab_y_edge], end=[-fab_x_edge, fab_y], layer='F.Fab', width=GLOBAL_CONFIG.fab_line_width))
    kicad_mod.append(Circle(center=[0, 0], radius=body_size['diameter']/2.0, layer='F.Fab', width=GLOBAL_CONFIG.fab_line_width))

    # create silkscreen
    fab_to_silk_offset = GLOBAL_CONFIG.silk_fab_offset
    silk_x = body_size['length'] / 2.0 + fab_to_silk_offset
    silk_y = body_size['width'] / 2.0 + fab_to_silk_offset
    silk_y_start = pad_params['size'][1] / 2.0 + GLOBAL_CONFIG.silk_pad_clearance + GLOBAL_CONFIG.silk_line_width/2.0
    silk_45deg_offset = fab_to_silk_offset*math.tan(math.radians(22.5))
    silk_x_edge = fab_x - fab_edge + silk_45deg_offset
    silk_y_edge = fab_y - fab_edge + silk_45deg_offset

    kicad_mod.append(Line(start=[silk_x, silk_y], end=[silk_x, silk_y_start], layer='F.SilkS', width=GLOBAL_CONFIG.silk_line_width))
    kicad_mod.append(Line(start=[silk_x, -silk_y], end=[silk_x, -silk_y_start], layer='F.SilkS', width=GLOBAL_CONFIG.silk_line_width))
    kicad_mod.append(Line(start=[-silk_x_edge, -silk_y], end=[silk_x, -silk_y], layer='F.SilkS', width=GLOBAL_CONFIG.silk_line_width))
    kicad_mod.append(Line(start=[-silk_x_edge, silk_y], end=[silk_x, silk_y], layer='F.SilkS', width=GLOBAL_CONFIG.silk_line_width))

    if silk_y_edge > silk_y_start:
        kicad_mod.append(Line(start=[-silk_x, silk_y_edge], end=[-silk_x, silk_y_start], layer='F.SilkS', width=GLOBAL_CONFIG.silk_line_width))
        kicad_mod.append(Line(start=[-silk_x, -silk_y_edge], end=[-silk_x, -silk_y_start], layer='F.SilkS', width=GLOBAL_CONFIG.silk_line_width))

        kicad_mod.append(Line(start=[-silk_x, -silk_y_edge], end=[-silk_x_edge, -silk_y], layer='F.SilkS', width=GLOBAL_CONFIG.silk_line_width))
        kicad_mod.append(Line(start=[-silk_x, silk_y_edge], end=[-silk_x_edge, silk_y], layer='F.SilkS', width=GLOBAL_CONFIG.silk_line_width))
    else:
        silk_x_cut = silk_x - (silk_y_start - silk_y_edge) # because of the 45 degree edge we can user a simple apporach
        silk_y_edge_cut = silk_y_start

        kicad_mod.append(Line(start=[-silk_x_cut, -silk_y_edge_cut], end=[-silk_x_edge, -silk_y], layer='F.SilkS', width=GLOBAL_CONFIG.silk_line_width))
        kicad_mod.append(Line(start=[-silk_x_cut, silk_y_edge_cut], end=[-silk_x_edge, silk_y], layer='F.SilkS', width=GLOBAL_CONFIG.silk_line_width))

    # create courtyard
    courtyard_x = body_size['length'] / 2.0 + courtyard_offset
    courtyard_y = body_size['width'] / 2.0 + courtyard_offset
    courtyard_pad_x = x_pad_spacing + pad_params['size'][0] / 2.0 + courtyard_offset
    courtyard_pad_y = pad_params['size'][1] / 2.0 + courtyard_offset
    courtyard_45deg_offset = courtyard_offset*math.tan(math.radians(22.5))
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
    kicad_mod.append(Line(start=[courtyard_x, -courtyard_y], end=[courtyard_x, -courtyard_pad_y], layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width))
    kicad_mod.append(Line(start=[courtyard_x, -courtyard_pad_y], end=[courtyard_pad_x, -courtyard_pad_y], layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width))
    kicad_mod.append(Line(start=[courtyard_pad_x, -courtyard_pad_y], end=[courtyard_pad_x, courtyard_pad_y], layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width))
    kicad_mod.append(Line(start=[courtyard_pad_x, courtyard_pad_y], end=[courtyard_x, courtyard_pad_y], layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width))
    kicad_mod.append(Line(start=[courtyard_x, courtyard_pad_y], end=[courtyard_x, courtyard_y], layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width))

    kicad_mod.append(Line(start=[-courtyard_x_edge, courtyard_y], end=[courtyard_x, courtyard_y], layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width))
    kicad_mod.append(Line(start=[-courtyard_x_edge, -courtyard_y], end=[courtyard_x, -courtyard_y], layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width))
    if fab_edge > 0:
        kicad_mod.append(Line(start=[-courtyard_x_lower_edge, courtyard_y_edge], end=[-courtyard_x_edge, courtyard_y], layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width))
        kicad_mod.append(Line(start=[-courtyard_x_lower_edge, -courtyard_y_edge], end=[-courtyard_x_edge, -courtyard_y], layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width))
    if courtyard_y_edge > courtyard_pad_y:
        kicad_mod.append(Line(start=[-courtyard_x, -courtyard_y_edge], end=[-courtyard_x, -courtyard_pad_y], layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width))
        kicad_mod.append(Line(start=[-courtyard_x, courtyard_pad_y], end=[-courtyard_x, courtyard_y_edge], layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width))
    kicad_mod.append(Line(start=[-courtyard_x_lower_edge, -courtyard_pad_y], end=[-courtyard_pad_x, -courtyard_pad_y], layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width))
    kicad_mod.append(Line(start=[-courtyard_pad_x, -courtyard_pad_y], end=[-courtyard_pad_x, courtyard_pad_y], layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width))
    kicad_mod.append(Line(start=[-courtyard_pad_x, courtyard_pad_y], end=[-courtyard_x_lower_edge, courtyard_pad_y], layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width))

    lib_name ='Capacitor_SMD'
    # add model
    modelname = name.replace("_HandSoldering", "")
    kicad_mod.append(Model(filename="{model_prefix:s}{lib_name:s}.3dshapes/{name:s}{suffix:s}".format(model_prefix=GLOBAL_CONFIG.model_3d_prefix, lib_name=lib_name, name=modelname, suffix=GLOBAL_CONFIG.model_3d_suffix),
                            at=[0, 0, 0], scale=[1, 1, 1], rotate=[0, 0, 0]))

    # write file
    write_footprint(kicad_mod, lib_name, generator_name)
    return 1
