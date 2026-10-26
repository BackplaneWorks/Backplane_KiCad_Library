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

import math

from kilibs.geom import Vector2D, GeomRectangle
from kilibs.util.toleranced_size import TolerancedSize
from KicadModTree import Footprint, FootprintType, \
    PolygonLine, Pad
from KicadModTree.nodes.specialized.PadArray import PadArray
from generators.tools.footprint.footprint_text_fields import addTextFields
from generators.tools.footprint.save_footprint import write_footprint

from .spec import PlccSpec
from kilibs.config.ipc_rules import DEFAULT_IPC_RULES
from ..config import PACKAGE_CONFIG
from kilibs.config.global_config import GLOBAL_CONFIG

ipc_density = 'nominal'
category = 'LCC'


def roundToBase(value, base):
    return round(value/base) * base


def params_inch_to_metric(device_params):
    for key in device_params:
        if type(device_params[key]) in [int, float] and 'num_' not in key:
            device_params[key] = device_params[key]*25.4


def calcPadDetails(device_config: PlccSpec, ipc_data, ipc_round_base):
    # Zmax = Lmin + 2JT + √(CL^2 + F^2 + P^2)
    # Gmin = Smax − 2JH − √(CS^2 + F^2 + P^2)
    # Xmax = Wmin + 2JS + √(CW^2 + F^2 + P^2)

    # Some manufacturers do not list the terminal spacing (S) in their datasheet but list the terminal length (T)
    # Then one can calculate
    # Stol(RMS) = √(Ltol^2 + 2*^2)
    # Smin = Lmin - 2*Tmax
    # Smax(RMS) = Smin + Stol(RMS)

    F = PACKAGE_CONFIG.get('manufacturing_tolerance', 0.1)
    P = PACKAGE_CONFIG.get('placement_tolerance', 0.05)

    lead_width_tol = device_config.lead_width.ipc_tol

    def calcPadLength(
        overall: TolerancedSize,
        body: TolerancedSize,
        lead_inside: TolerancedSize | None = None,
        lead_center: TolerancedSize | None = None,
    ):
        overall_tol = overall.ipc_tol
        if lead_inside:
            Tmin = (overall.maximum - lead_inside.maximum)/2
            Stol_RMS = math.sqrt(overall_tol**2+lead_inside.ipc_tol**2)
            Smax_RMS = lead_inside.minimum + Stol_RMS
        elif lead_center:
            Tmin = (body.maximum - lead_center.maximum)
            Stol_RMS = math.sqrt(body.ipc_tol**2+lead_center.ipc_tol**2)
            Smax_RMS = body.maximum - 2*Tmin + Stol_RMS
        else:
            lead_len_tol = device_config.lead_length.ipc_tol
            Stol_RMS = math.sqrt(overall_tol**2+2*(lead_len_tol**2))
            Smin = overall.minimum - 2 * device_config.lead_length.maximum
            Smax_RMS = Smin + Stol_RMS

        Gmin = Smax_RMS - 2*ipc_data['heel'] - math.sqrt(Stol_RMS**2 + F**2 + P**2)

        Zmax = overall.minimum + 2*ipc_data['toe'] + math.sqrt(overall_tol**2 + F**2 + P**2)

        Zmax = roundToBase(Zmax, ipc_round_base['toe'])
        Gmin = roundToBase(Gmin, ipc_round_base['heel'])

        Zmax += device_config.pad_length_addition

        return Gmin, Zmax

    if device_config.lead_inside_x:
        Gmin_x, Zmax_x = calcPadLength(
            overall=device_config.overall_x,
            body=device_config.body_x,
            lead_inside=device_config.lead_inside_x,
        )
        Gmin_y, Zmax_y = calcPadLength(
            overall=device_config.overall_y,
            body=device_config.body_y,
            lead_inside=device_config.lead_inside_y,
        )
    elif device_config.lead_center_distance_x:
        Gmin_x, Zmax_x = calcPadLength(
            overall=device_config.overall_x,
            body=device_config.body_x,
            lead_center=device_config.lead_center_distance_x,
        )
        Gmin_y, Zmax_y = calcPadLength(
            overall=device_config.overall_y,
            body=device_config.body_y,
            lead_center=device_config.lead_center_distance_y,
        )
    else:
        Gmin_x, Zmax_x = calcPadLength(
            overall=device_config.overall_x,
            body=device_config.body_x
        )

        Gmin_y, Zmax_y = calcPadLength(
            overall=device_config.overall_y,
            body=device_config.body_y
        )

    Xmax = device_config.lead_width.minimum + 2*ipc_data['side'] + math.sqrt(lead_width_tol**2 + F**2 + P**2)
    Xmax = roundToBase(Xmax, ipc_round_base['side'])

    Pad = {}
    Pad['first'] = {'start': [-((device_config.num_pins_x-1) % 2)/2 *
                                device_config.pitch, -(Zmax_y+Gmin_y)/4], 'size': [Xmax, (Zmax_y-Gmin_y)/2]}

    Pad['left'] = {'center': [-(Zmax_x+Gmin_x)/4, 0], 'size': [(Zmax_x-Gmin_x)/2, Xmax]}
    Pad['right'] = {'center': [(Zmax_x+Gmin_x)/4, 0], 'size': [(Zmax_x-Gmin_x)/2, Xmax]}
    Pad['top'] = {'start': [(device_config.num_pins_x-1)/2*device_config.pitch, -
                            (Zmax_y+Gmin_y)/4], 'size': [Xmax, (Zmax_y-Gmin_y)/2]}
    Pad['bottom'] = {'center': [0, (Zmax_y+Gmin_y)/4], 'size': [Xmax, (Zmax_y-Gmin_y)/2]}

    return Pad


def create_footprints(spec: PlccSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification.
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
    if spec.spec.get('units', 'mm') == 'inch':
        params_inch_to_metric(spec.spec)
    # We recreate a spec because the values might have changed if they were given in inch.
    # The correct implementation would be to use TolerancedSize with units.
    device_config = PlccSpec(spec.id, spec.spec)

    fab_line_width = GLOBAL_CONFIG.fab_line_width
    silk_line_width = GLOBAL_CONFIG.silk_line_width

    lib_name = PACKAGE_CONFIG['lib_name_format_string'].format(category=category)

    size_y = device_config.body_y.nominal
    size_x = device_config.body_x.nominal

    pincount = device_config.num_pins_x*2 + device_config.num_pins_y*2

    ipc_reference = 'ipc_spec_j_lead'

    ipc_data_set = DEFAULT_IPC_RULES.raw_data[ipc_reference][ipc_density]
    ipc_round_base = DEFAULT_IPC_RULES.raw_data[ipc_reference]['round_base']

    pad_details = calcPadDetails(device_config, ipc_data_set, ipc_round_base)

    suffix = (device_config.suffix or "").format(pad_x=pad_details['left']['size'][0],
                                                    pad_y=pad_details['left']['size'][1])
    suffix_3d = suffix if device_config.include_suffix_in_3dpath else ""

    name_format = PACKAGE_CONFIG['fp_name_format_string']

    fp_name = name_format.format(
        man=device_config.metadata.manufacturer or "",
        mpn=device_config.metadata.part_number or "",
        pkg=device_config.device_type,
        pincount=pincount,
        size_y=size_y,
        size_x=size_x,
        pitch=device_config.pitch,
        suffix=suffix
    ).replace('__', '_').lstrip('_')

    fp_name_2 = name_format.format(
        man=device_config.metadata.manufacturer or "",
        mpn=device_config.metadata.part_number or "",
        pkg=device_config.device_type,
        pincount=pincount,
        size_y=size_y,
        size_x=size_x,
        pitch=device_config.pitch,
        suffix=suffix_3d
    ).replace('__', '_').lstrip('_')

    model_name = fp_name_2

    kicad_mod = Footprint(fp_name, FootprintType.SMD)

    description = "{manufacturer} {mpn} {package}, {pincount} Pin".format(
        manufacturer=device_config.metadata.manufacturer or "",
        package=device_config.device_type,
        mpn=device_config.metadata.part_number or "",
        pincount=pincount,
    ).lstrip()

    if device_config.metadata.datasheet:
        description += f" ({device_config.metadata.datasheet})"

    kicad_mod.description = description

    kicad_mod.tags = (
        PACKAGE_CONFIG["keyword_fp_string"]
        .format(
            man=device_config.metadata.manufacturer or "",
            package=device_config.device_type,
            category=category,
        )
        .lstrip()
    )

    pad_shape_details = {}
    pad_shape_details['shape'] = Pad.SHAPE_ROUNDRECT
    pad_shape_details['round_radius_handler'] = GLOBAL_CONFIG.roundrect_radius_handler

    init = 1
    kicad_mod.append(PadArray(
        initial=init,
        type=Pad.TYPE_SMT,
        layers=Pad.LAYERS_SMT,
        pincount=int(math.ceil(device_config.num_pins_x/2)),
        x_spacing=-device_config.pitch, y_spacing=0,
        **pad_details['first'], **pad_shape_details))

    init += int(math.ceil(device_config.num_pins_x/2))
    kicad_mod.append(PadArray(
        initial=init,
        type=Pad.TYPE_SMT,
        layers=Pad.LAYERS_SMT,
        pincount=device_config.num_pins_y,
        x_spacing=0, y_spacing=device_config.pitch,
        **pad_details['left'], **pad_shape_details))

    init += device_config.num_pins_y
    kicad_mod.append(PadArray(
        initial=init,
        type=Pad.TYPE_SMT,
        layers=Pad.LAYERS_SMT,
        pincount=device_config.num_pins_x,
        y_spacing=0, x_spacing=device_config.pitch,
        **pad_details['bottom'], **pad_shape_details))

    init += device_config.num_pins_x
    kicad_mod.append(PadArray(
        initial=init,
        type=Pad.TYPE_SMT,
        layers=Pad.LAYERS_SMT,
        pincount=device_config.num_pins_y,
        x_spacing=0, y_spacing=-device_config.pitch,
        **pad_details['right'], **pad_shape_details))

    init += device_config.num_pins_y
    kicad_mod.append(PadArray(
        initial=init,
        type=Pad.TYPE_SMT,
        layers=Pad.LAYERS_SMT,
        pincount=int(math.floor(device_config.num_pins_x/2)),
        y_spacing=0, x_spacing=-device_config.pitch,
        **pad_details['top'], **pad_shape_details))

    body_rect = GeomRectangle(center=Vector2D(0,0), size=Vector2D(size_x, size_y))

    bounding_box = {
        'left': pad_details['left']['center'][0] - pad_details['left']['size'][0]/2,
        'right': pad_details['right']['center'][0] + pad_details['right']['size'][0]/2,
        'top': pad_details['top']['start'][1] - pad_details['top']['size'][1]/2,
        'bottom': pad_details['bottom']['center'][1] + pad_details['bottom']['size'][1]/2
    }

    pad_width = pad_details['top']['size'][0]
    p1_x = pad_details['first']['start'][0]

    # ############################ SilkS ##################################

    silk_offset = GLOBAL_CONFIG.silk_fab_offset

    sx1 = -(device_config.pitch*(device_config.num_pins_x-1)/2.0
            + pad_width/2.0 + GLOBAL_CONFIG.silk_pad_offset)

    sy1 = -(device_config.pitch*(device_config.num_pins_y-1)/2.0
            + pad_width/2.0 + GLOBAL_CONFIG.silk_pad_offset)

    poly_silk = [
        [sx1, body_rect.top-silk_offset],
        [body_rect.left-silk_offset, body_rect.top-silk_offset],
        [body_rect.left-silk_offset, sy1]
    ]
    kicad_mod.append(PolygonLine(
        shape=poly_silk,
        width=silk_line_width,
        layer="F.SilkS", x_mirror=0))
    kicad_mod.append(PolygonLine(
        shape=poly_silk,
        width=silk_line_width,
        layer="F.SilkS", y_mirror=0))
    kicad_mod.append(PolygonLine(
        shape=poly_silk,
        width=silk_line_width,
        layer="F.SilkS", x_mirror=0, y_mirror=0))

    silk_off_45 = silk_offset / math.sqrt(2)
    poly_silk_tl = [
        [sx1, body_rect.top-silk_offset],
        [body_rect.left+device_config.body_chamfer-silk_off_45, body_rect.top-silk_offset],
        [body_rect.left-silk_offset, body_rect.top+device_config.body_chamfer-silk_off_45],
        [body_rect.left-silk_offset, sy1]
    ]

    kicad_mod.append(PolygonLine(
        shape=poly_silk_tl,
        width=silk_line_width,
        layer="F.SilkS"))

    # # ######################## Fabrication Layer ###########################

    fab_bevel_size = GLOBAL_CONFIG.fab_bevel.get_chamfer_size(
        min(size_x, size_y)
    )
    fab_bevel_y = fab_bevel_size / math.sqrt(2)
    poly_fab = [
        [p1_x, body_rect.top+fab_bevel_y],
        [p1_x+fab_bevel_size/2, body_rect.top],
        [body_rect.right, body_rect.top],
        [body_rect.right, body_rect.bottom],
        [body_rect.left, body_rect.bottom],
        [body_rect.left, body_rect.top+device_config.body_chamfer],
        [body_rect.left+device_config.body_chamfer, body_rect.top],
        [p1_x-fab_bevel_size/2, body_rect.top],
        [p1_x, body_rect.top+fab_bevel_y]
    ]

    kicad_mod.append(PolygonLine(
        shape=poly_fab,
        width=fab_line_width,
        layer="F.Fab")
    )

    # # ############################ CrtYd ##################################

    off = ipc_data_set['courtyard']
    grid = GLOBAL_CONFIG.courtyard_grid
    off_45 = off*math.tan(math.radians(45.0/2))

    cy1 = roundToBase(bounding_box['top']-off, grid)
    cy2 = roundToBase(body_rect.top-off, grid)
    cy3 = -roundToBase(
        device_config.pitch*(device_config.num_pins_y-1)/2.0
        + pad_width/2.0 + off, grid)
    cy4 = roundToBase(body_rect.top+device_config.body_chamfer-off_45, grid)

    cx1 = -roundToBase(
        device_config.pitch*(device_config.num_pins_x-1)/2.0
        + pad_width/2.0 + off, grid)
    cx2 = roundToBase(body_rect.left-off, grid)
    cx3 = roundToBase(bounding_box['left']-off, grid)
    cx4 = roundToBase(body_rect.left+device_config.body_chamfer-off_45, grid)

    crty_poly_tl = [
        [0, cy1],
        [cx1, cy1],
        [cx1, cy2],
        [cx2, cy2],
        [cx2, cy3],
        [cx3, cy3],
        [cx3, 0]
    ]

    kicad_mod.append(PolygonLine(shape=crty_poly_tl,
                                    layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width,
                                    x_mirror=0))
    kicad_mod.append(PolygonLine(shape=crty_poly_tl,
                                    layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width,
                                    y_mirror=0))
    kicad_mod.append(PolygonLine(shape=crty_poly_tl,
                                    layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width,
                                    x_mirror=0, y_mirror=0))

    crty_poly_tl_ch = [
        [0, cy1],
        [cx1, cy1],
        [cx1, cy2],
        [cx4, cy2],
        [cx2, cy4],
        [cx2, cy3],
        [cx3, cy3],
        [cx3, 0]
    ]
    kicad_mod.append(PolygonLine(shape=crty_poly_tl_ch,
                                    layer='F.CrtYd', width=GLOBAL_CONFIG.courtyard_line_width))

    # ######################### Text Fields ###############################

    cy_bbox = GeomRectangle(center=Vector2D(0, 0), size=Vector2D(cx3 * 2, cy1 * 2))

    addTextFields(kicad_mod=kicad_mod, configuration=GLOBAL_CONFIG, body_edges=body_rect,
                    courtyard=cy_bbox, fp_name=fp_name, text_y_inside_position='center')

    # #################### Output and 3d model ############################
    kicad_mod.add_standard_3d_model_to_footprint(lib_name, model_name)
    write_footprint(kicad_mod, lib_name, generator_name)

    return 1
