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

"""
Generator for SMD connectors (single row with two mounting pads)

       _X__X__X__X_
    XX| X  X  X  X |XX
    XX|            |XX
      |____________|
"""

from math import sqrt
import os

from kilibs.geom import GeomRectangle, Direction
from kilibs.declarative_defs import evaluable_defs as EDs
from KicadModTree import *
from KicadModTree.util.courtyard_builder import CourtyardBuilder
from generators.tools.footprint.declarative_def_tools.connectors_config import (
    ConnectorsConfiguration,
    ConnectorOrientation,
)
from generators.tools.footprint.drawing_tools import round_to_grid
from generators.tools.footprint.footprint_text_fields import addTextFields
from generators.tools.footprint.save_footprint import write_footprint
from kilibs.config import global_config as GC
from generators.tools.footprint.declarative_def_tools import ast_evaluator, fp_additional_drawing

from generators.tools.spec.base_spec import BaseSpec
from generators.tools.spec.spec_generator import get_spec_dicts
from kilibs.config.global_config import GLOBAL_CONFIG
from generators.tools.cli_args import CLI_ARGS

class SMDSingleRowPlusMPProperties:
    """
    A complete description of a single-row SMD connector series with two mounting pads
    and a row of pads.
    """

    # The original dict
    _series_def: dict

    manufacturer: str
    mpm_format_string: str
    mpn_param_1: list | None
    """List of parameters, indexed by pincount"""
    datasheet: str | None

    pitch: float
    orientation: ConnectorOrientation
    """Orientation of the connector, 'H' or 'V'"""

    pins_toward_bottom: bool
    """Main row of pins is toward the bottom of the footprint"""

    pad_size: Vector2D
    mounting_pad_size: Vector2D

    mount_pad_center_x_to_pin: float
    """Position of the mounting pad in x, relative to the center of end pin
    in the main row"""

    pad_pos_y: float
    """Main pad row position in y, relative to the origin"""
    mounting_pad_pos_y: float
    """Position of the mounting pad in y, relative to the origin"""

    rel_body_edge_y: float
    """Body edge in y, relative to the center of the mouting pad outside edge"""
    rel_body_edge_x: float
    """Body edge in x, relative to the center of the main pad row"""
    body_size_y: float
    """Total body size in y"""

    # Compatibile with addTextFields
    text_inside_pos: str | float

    pin_range: list[int]
    """The list of pin counts that this series supports"""

    pin1_fab_marker_y: EDs.EvaluableScalar | None
    """Manual override for where to place the "root" of the pin1 fab marker"""

    automatic_silk_outline: bool

    additional_drawings: list[fp_additional_drawing.FPAdditionalDrawing]

    def __init__(self, series_def: dict, group_def: dict, id: str):
        self._series_def = series_def

        # We could make the group definition a separate class, but it's literally
        # just one field, so we'll just store it in here.
        self.manufacturer = group_def["manufacturer"]

        self.series = series_def["series"]
        self.datasheet = series_def.get("datasheet", None)
        self.orientation = ConnectorOrientation.from_str(series_def["orientation"])
        self.pitch = series_def["pitch"]

        # We might want to make this a generic YAML def, but maybe the syntax would be better as
        #  pins:            pins:
        #    from: 2          list: [4, 6, 10]
        #    to: 15
        # But that affects many defs and it's "OK" now
        pin_range_def_type, pin_range_def = series_def["pinrange"]
        if pin_range_def_type == "range":
            self.pin_range = range(*pin_range_def)
        elif pin_range_def_type == "list":
            self.pin_range = pin_range_def
        else:
            raise ("Pin range definition error in part {:s}".format(id))

        self.mpn_param_1 = series_def.get("mpn_param_1", None)
        self.mpm_format_string = series_def["mpn_format_string"]

        pad1_pos = series_def["pad1_position"]
        if pad1_pos == "bottom-left":
            self.pins_toward_bottom = True
        elif pad1_pos == "top-left":
            self.pins_toward_bottom = False
        else:
            raise ValueError(
                f"pad1_position must be 'bottom-left' or 'top-left', not '{pad1_pos}'"
            )

        rel_pad_y_outside_edge: float = series_def["rel_pad_y_outside_edge"]
        rel_pad_y_inside_edge: float = series_def["rel_pad_y_inside_edge"]

        pad_size_x = series_def["pad_size_x"]
        pad_size_y = rel_pad_y_outside_edge - rel_pad_y_inside_edge
        self.pad_size = Vector2D(pad_size_x, pad_size_y)

        self.pad_pos_y = -rel_pad_y_outside_edge / 2 + pad_size_y / 2

        self.mounting_pad_size = Vector2D(
            series_def["mounting_pad_size"][0], series_def["mounting_pad_size"][1]
        )

        self.mounting_pad_pos_y = (
            rel_pad_y_outside_edge / 2 - self.mounting_pad_size.y / 2
        )

        if "center_shift_y" in series_def:
            center_shift_y: float = series_def["center_shift_y"]
            self.mounting_pad_pos_y -= center_shift_y
            self.pad_pos_y -= center_shift_y

        # Body sizes
        self.rel_body_edge_y = series_def["rel_body_edge_y"]
        self.rel_body_edge_x = series_def["rel_body_edge_x"]
        self.body_size_y = series_def["body_size_y"]

        self.mount_pad_center_x_to_pin = (
            series_def["center_pad_to_mounting_pad_edge"]
            + self.mounting_pad_size.x / 2.0
        )

        self.text_inside_pos = series_def["text_inside_pos"]

        self.pin1_fab_marker_y = (
            EDs.EvaluableScalar(series_def["pin1_fab_marker_y"])
            if "pin1_fab_marker_y" in series_def
            else None
        )

        self.automatic_silk_outline = series_def.get("automatic_silk_outline", True)

        self.additional_drawings = (
            fp_additional_drawing.FPAdditionalDrawing.from_standard_yaml(
                series_def
            )
        )

    def pin_row_length_c_to_c(self, pincount: int) -> float:
        """
        Center-to-center distance of the main pin row
        """
        return (pincount - 1) * self.pitch

    def get_mpn_param(self, idx: int):
        """If the series has a parameter that varies with pincount, return it for the given pincount"""
        if self.mpn_param_1 is not None:
            return self.mpn_param_1[idx]
        else:
            return None


def generate_one_footprint(
    generator_name: str,
    global_config: GC.GlobalConfig,
    idx: int,
    pincount: int,
    series_props: SMDSingleRowPlusMPProperties,
    conn_config: ConnectorsConfiguration,
):

    # Get the series definition for old dict-based access
    series_definition = series_props._series_def

    mpn_format_params = {"pincount": pincount}
    # Look up index-specific parameters
    if mpn_param := series_props.get_mpn_param(idx):
        mpn_format_params["mpn_param_1"] = mpn_param

    mpn = series_props.mpm_format_string.format(**mpn_format_params)

    pins_toward_bottom = series_props.pins_toward_bottom
    needs_additional_silk_pin1_marker = False

    pad_size = series_props.pad_size
    pad_pos_y = series_props.pad_pos_y

    mounting_pad_size = series_props.mounting_pad_size
    mount_pad_y_pos = series_props.mounting_pad_pos_y

    # center pin 1 to center pin n
    dimension_A = series_props.pin_row_length_c_to_c(pincount)

    body_br = Vector2D(dimension_A / 2 + series_props.rel_body_edge_x, 0)
    body_tl = Vector2D(-body_br.x, 0)

    if pins_toward_bottom:
        pad_pos_y *= -1
        mount_pad_y_pos *= -1
        mount_pad_edge_y_outside = mount_pad_y_pos - mounting_pad_size.y / 2
        body_tl.y = mount_pad_edge_y_outside - series_props.rel_body_edge_y
        body_br.y = body_tl.y + series_props.body_size_y
    else:
        mount_pad_edge_y_outside = mount_pad_y_pos + mounting_pad_size.y / 2
        body_br.y = mount_pad_edge_y_outside + series_props.rel_body_edge_y
        body_tl.y = body_br.y - series_props.body_size_y

    body_rect = GeomRectangle(start=body_tl, end=body_br)

    orientation = conn_config.get_orientation_name(series_props.orientation)
    footprint_name = conn_config.fp_name_format_string.format(
        man=series_props.manufacturer,
        series=series_props.series,
        mpn=mpn,
        num_rows=1,
        pins_per_row=pincount,
        mounting_pad="-1MP",
        pitch=series_props.pitch,
        orientation=orientation,
    )
    footprint_name = footprint_name.replace("__", "_")

    # Symbols that expressions can use
    fp_symbols = {
        "pitch_x": series_props.pitch,
        "pin_count": pincount,
        "body_left_x": body_rect.left,
        "body_right_x": body_rect.right,
        "body_top_y": body_rect.top,
        "body_bottom_y": body_rect.bottom,
        "body_center_x": body_rect.center.x,
        "body_center_y": body_rect.center.y
    }

    fp_evaluator = ast_evaluator.ASTevaluator(symbols=fp_symbols)

    kicad_mod = Footprint(footprint_name, FootprintType.SMD)
    kicad_mod.description = "{:s} {:s} series connector, {:s} ({:s})".format(
        series_props.manufacturer,
        series_props.series,
        mpn,
        series_props.datasheet or "",
    )
    kicad_mod.tags = conn_config.keyword_fp_string.format(
        series=series_props.series,
        orientation=orientation,
        man=series_props.manufacturer,
        entry=conn_config.get_orientation_description(series_props.orientation),
    )

    ############################# Pads ##################################
    optional_pad_params = {
        "round_radius_handler": global_config.roundrect_radius_handler
    }

    pad_shape = Pad.SHAPE_ROUNDRECT

    kicad_mod.append(PadArray(
        center=[0, pad_pos_y], x_spacing=series_props.pitch, pincount=pincount,
        size=pad_size, type=Pad.TYPE_SMT, shape=pad_shape, layers=Pad.LAYERS_SMT,
        **optional_pad_params))

    mount_pad_left_x_pos = -dimension_A/2 - series_props.mount_pad_center_x_to_pin
    mounting_pad_name = global_config.get_pad_name(GC.PadName.MECHANICAL)

    kicad_mod.append(Pad(
        number = mounting_pad_name, type=Pad.TYPE_SMT,
        shape=pad_shape, at=[mount_pad_left_x_pos, mount_pad_y_pos],
        size=mounting_pad_size, layers=Pad.LAYERS_SMT,
        **optional_pad_params))
    kicad_mod.append(Pad(
        number = mounting_pad_name, type=Pad.TYPE_SMT,
        shape=pad_shape, at=[-mount_pad_left_x_pos, mount_pad_y_pos],
        size=mounting_pad_size, layers=Pad.LAYERS_SMT,
        **optional_pad_params))

    ######################### Body outline ###############################
    pad_edge_silk_center_offset = global_config.silk_pad_offset
    pad_1_x_outside_edge = -dimension_A/2 - pad_size.x/2

    if pins_toward_bottom: #Man i wish there where a rotate footprint function available.
        body_edge_pin = body_rect.bottom
        body_edge_mount_pad = body_rect.top
        silk_y_mp_pin_side = mount_pad_y_pos + mounting_pad_size.y / 2 + pad_edge_silk_center_offset
        mp_edge_outside = mount_pad_y_pos - mounting_pad_size.y / 2
        silk_y_mp_outside = mp_edge_outside - pad_edge_silk_center_offset
        pin_edge_outside = pad_pos_y + pad_size.y / 2
        silk_y_offset_pin_side = global_config.silk_fab_offset
    else:
        body_edge_pin = body_rect.top
        body_edge_mount_pad = body_rect.bottom
        silk_y_mp_pin_side = mount_pad_y_pos - mounting_pad_size.y / 2 - pad_edge_silk_center_offset
        mp_edge_outside = mount_pad_y_pos + mounting_pad_size.y / 2
        silk_y_mp_outside = mp_edge_outside + pad_edge_silk_center_offset
        pin_edge_outside = pad_pos_y - pad_size.y / 2
        silk_y_offset_pin_side = -global_config.silk_fab_offset

    # Pin side
    bounding_box_y_pin_side = pad_pos_y + (
        pad_size.y / 2 * (1 if pins_toward_bottom else -1)
    )
    side_line_y_pin_side = body_edge_pin
    mp_inner_edge_x_left_silk = mount_pad_left_x_pos + mounting_pad_size.x / 2 + pad_edge_silk_center_offset
    modified_pinside_x_inner = body_rect.left

    if 'edge_modifier_pin_side' in series_definition:
        modifier = series_definition['edge_modifier_pin_side']
        modified_pinside_x_inner = body_rect.left + modifier['width']

        if pins_toward_bottom:
            side_line_y_pin_side += modifier['length']
            if side_line_y_pin_side > bounding_box_y_pin_side:
                bounding_box_y_pin_side = side_line_y_pin_side
        else:
            side_line_y_pin_side -= modifier['length']
            if side_line_y_pin_side < bounding_box_y_pin_side:
                bounding_box_y_pin_side = side_line_y_pin_side

        poly_fab_pin_side=[
            {'x': body_rect.left, 'y': side_line_y_pin_side},
            {'x': modified_pinside_x_inner, 'y': side_line_y_pin_side},
            {'x': modified_pinside_x_inner, 'y': body_edge_pin},
            {'x': -modified_pinside_x_inner, 'y': body_edge_pin},
            {'x': -modified_pinside_x_inner, 'y': side_line_y_pin_side},
            {'x': body_rect.right, 'y': side_line_y_pin_side}
        ]

        if modifier['length'] < 0:
            silk_x_offset = -global_config.silk_fab_offset
        else:
            silk_x_offset = global_config.silk_fab_offset

        if modified_pinside_x_inner + silk_x_offset > pad_1_x_outside_edge - pad_edge_silk_center_offset:
            poly_silk_edge_left = [
                {'x': body_rect.left - global_config.silk_fab_offset, 'y': silk_y_mp_pin_side},
                {'x': body_rect.left - global_config.silk_fab_offset, 'y': side_line_y_pin_side + silk_y_offset_pin_side},
                {'x': pad_1_x_outside_edge - pad_edge_silk_center_offset, 'y': side_line_y_pin_side + silk_y_offset_pin_side},
                {'x': pad_1_x_outside_edge - pad_edge_silk_center_offset, 'y': pin_edge_outside}
            ]
            if abs(pin_edge_outside) - abs(side_line_y_pin_side + silk_y_offset_pin_side) < global_config.silk_line_length_min:
                needs_additional_silk_pin1_marker = True

            poly_silk_edge_right = [
                {'x': body_rect.right + global_config.silk_fab_offset, 'y': silk_y_mp_pin_side},
                {'x': body_rect.right + global_config.silk_fab_offset, 'y': side_line_y_pin_side + silk_y_offset_pin_side},
                {'x': -pad_1_x_outside_edge + pad_edge_silk_center_offset, 'y': side_line_y_pin_side + silk_y_offset_pin_side}
            ]

        else:
            poly_silk_edge_left = [
                {'x': body_rect.left - global_config.silk_fab_offset, 'y': silk_y_mp_pin_side},
                {'x': body_rect.left - global_config.silk_fab_offset, 'y': side_line_y_pin_side + silk_y_offset_pin_side},
                {'x': modified_pinside_x_inner + silk_x_offset, 'y': side_line_y_pin_side + silk_y_offset_pin_side},
                {'x': modified_pinside_x_inner + silk_x_offset, 'y': body_edge_pin + silk_y_offset_pin_side},
                {'x': pad_1_x_outside_edge - pad_edge_silk_center_offset, 'y': body_edge_pin + silk_y_offset_pin_side},
                {'x': pad_1_x_outside_edge - pad_edge_silk_center_offset, 'y': pin_edge_outside}
            ]
            if abs(pin_edge_outside) - abs(body_edge_pin + silk_y_offset_pin_side) < global_config.silk_line_length_min:
                needs_additional_silk_pin1_marker = True

            poly_silk_edge_right = [
                {'x': body_rect.right + global_config.silk_fab_offset, 'y': silk_y_mp_pin_side},
                {'x': body_rect.right + global_config.silk_fab_offset, 'y': side_line_y_pin_side + silk_y_offset_pin_side},
                {'x': -modified_pinside_x_inner - silk_x_offset, 'y': side_line_y_pin_side + silk_y_offset_pin_side},
                {'x': -modified_pinside_x_inner - silk_x_offset, 'y': body_edge_pin + silk_y_offset_pin_side},
                {'x': -pad_1_x_outside_edge + pad_edge_silk_center_offset, 'y': body_edge_pin + silk_y_offset_pin_side}
            ]
    else:
        poly_fab_pin_side=[
            {'x': body_rect.left, 'y': body_edge_pin},
            {'x': body_rect.right, 'y': body_edge_pin}
        ]
        poly_silk_edge_left = [
            {'x': body_rect.left - global_config.silk_fab_offset, 'y': silk_y_mp_pin_side},
            {'x': body_rect.left - global_config.silk_fab_offset, 'y': side_line_y_pin_side + silk_y_offset_pin_side},
            {'x': pad_1_x_outside_edge - pad_edge_silk_center_offset, 'y': body_edge_pin + silk_y_offset_pin_side},
            {'x': pad_1_x_outside_edge - pad_edge_silk_center_offset, 'y': pin_edge_outside}
        ]
        if abs(pin_edge_outside) - abs(body_edge_pin + silk_y_offset_pin_side) < global_config.silk_line_length_min:
            needs_additional_silk_pin1_marker = True

        poly_silk_edge_right = [
            {'x': body_rect.right + global_config.silk_fab_offset, 'y': silk_y_mp_pin_side},
            {'x': body_rect.right + global_config.silk_fab_offset, 'y': side_line_y_pin_side + silk_y_offset_pin_side},
            {'x': -pad_1_x_outside_edge + pad_edge_silk_center_offset, 'y': body_edge_pin + silk_y_offset_pin_side}
        ]
    kicad_mod.append(PolygonLine(shape=poly_fab_pin_side, layer='F.Fab', width=global_config.fab_line_width))

    if series_props.automatic_silk_outline:
        kicad_mod.append(PolygonLine(shape=poly_silk_edge_left, layer='F.SilkS', width=global_config.silk_line_width))
        kicad_mod.append(PolygonLine(shape=poly_silk_edge_right, layer='F.SilkS', width=global_config.silk_line_width))

    # Mount pad side
    bounding_box_y_mount_pad_side = mount_pad_y_pos + (-mounting_pad_size.y / 2 if pins_toward_bottom else mounting_pad_size.y / 2)
    if abs(bounding_box_y_mount_pad_side) < abs(body_edge_mount_pad):
        bounding_box_y_mount_pad_side = body_edge_mount_pad
    mid_line_y_mount_pad_side = body_edge_mount_pad

    if 'edge_modifier_mount_pad_side' in series_definition:
        modifier = series_definition['edge_modifier_mount_pad_side']

        if 'width_start' in modifier:
            modified_mp_start_x_inner = - modifier['width_start']/2 # We assume centered body!
        if 'start_from_body_side' in modifier:
            modified_mp_start_x_inner = body_rect.left + modifier['start_from_body_side']
        modified_mp_end_x_inner = modified_mp_start_x_inner
        if 'width_end' in modifier:
            modified_mp_end_x_inner = - modifier['width_end']/2 # We assume centered body!
        if 'end_from_body_side' in modifier:
            modified_mp_end_x_inner = body_rect.left + modifier['end_from_body_side']

        if pins_toward_bottom:
            mid_line_y_mount_pad_side += modifier['depth']
            if mid_line_y_mount_pad_side < bounding_box_y_mount_pad_side:
                bounding_box_y_mount_pad_side = mid_line_y_mount_pad_side
        else:
            mid_line_y_mount_pad_side -= modifier['depth']
            if mid_line_y_mount_pad_side > bounding_box_y_mount_pad_side:
                bounding_box_y_mount_pad_side = mid_line_y_mount_pad_side

        if modifier['depth'] < 0:
            silk_x_offset = -global_config.silk_fab_offset
        else:
            silk_x_offset = global_config.silk_fab_offset

        poly_fab_mp_side=[
            {'x': body_rect.left, 'y': body_edge_mount_pad},
            {'x': modified_mp_start_x_inner, 'y': body_edge_mount_pad},
            {'x': modified_mp_end_x_inner, 'y': mid_line_y_mount_pad_side},
            {'x': -modified_mp_end_x_inner, 'y': mid_line_y_mount_pad_side},
            {'x': -modified_mp_start_x_inner, 'y': body_edge_mount_pad},
            {'x': body_rect.right, 'y': body_edge_mount_pad}
        ]

        poly_silk_mp_side=[
            {'x': mp_inner_edge_x_left_silk, 'y': body_edge_mount_pad - silk_y_offset_pin_side},
            {'x': modified_mp_start_x_inner + silk_x_offset, 'y': body_edge_mount_pad - silk_y_offset_pin_side},
            {'x': modified_mp_end_x_inner + silk_x_offset, 'y': mid_line_y_mount_pad_side - silk_y_offset_pin_side},
            {'x': -modified_mp_end_x_inner - silk_x_offset, 'y': mid_line_y_mount_pad_side - silk_y_offset_pin_side},
            {'x': -modified_mp_start_x_inner - silk_x_offset, 'y': body_edge_mount_pad - silk_y_offset_pin_side},
            {'x': -mp_inner_edge_x_left_silk, 'y': body_edge_mount_pad - silk_y_offset_pin_side}
        ]
        if modified_mp_start_x_inner + global_config.silk_fab_offset < mp_inner_edge_x_left_silk:
            poly_silk_mp_side=[
                {'x': mp_inner_edge_x_left_silk, 'y': mid_line_y_mount_pad_side - silk_y_offset_pin_side},
                {'x': -mp_inner_edge_x_left_silk, 'y': mid_line_y_mount_pad_side - silk_y_offset_pin_side}
            ]
    else:
        poly_fab_mp_side=[
            {'x': body_rect.left, 'y': body_edge_mount_pad},
            {'x': body_rect.right, 'y': body_edge_mount_pad}
        ]
        poly_silk_mp_side=[
            {'x': mp_inner_edge_x_left_silk, 'y': body_edge_mount_pad - silk_y_offset_pin_side},
            {'x': -mp_inner_edge_x_left_silk, 'y': body_edge_mount_pad - silk_y_offset_pin_side}
        ]

    if series_props.rel_body_edge_y > pad_edge_silk_center_offset:
        poly_silk_mp_side[0]['x'] = body_rect.left
        poly_silk_mp_side[len(poly_silk_mp_side)-1]['x'] = body_rect.right

    if series_props.rel_body_edge_y > pad_edge_silk_center_offset + global_config.silk_line_length_min:
        poly_silk_mp_side[0]['x'] = body_rect.left - global_config.silk_fab_offset
        poly_silk_mp_side[len(poly_silk_mp_side)-1]['x'] = body_rect.right + global_config.silk_fab_offset

        poly_silk_mp_side.insert(0,{'x': body_rect.left - global_config.silk_fab_offset, 'y': silk_y_mp_outside})
        poly_silk_mp_side.append({'x': body_rect.right + global_config.silk_fab_offset, 'y': silk_y_mp_outside})

    if series_props.automatic_silk_outline:
        kicad_mod.append(PolygonLine(shape=poly_silk_mp_side, layer='F.SilkS', width=global_config.silk_line_width))

    kicad_mod.append(PolygonLine(shape=poly_fab_mp_side, layer='F.Fab', width=global_config.fab_line_width))

    kicad_mod.append(Line(start=[body_rect.left, side_line_y_pin_side], end=[body_rect.left, body_edge_mount_pad],
                            layer='F.Fab', width=global_config.fab_line_width))

    kicad_mod.append(Line(start=[body_rect.right, side_line_y_pin_side], end=[body_rect.right, body_edge_mount_pad],
                            layer='F.Fab', width=global_config.fab_line_width))

    ###################### Additional Drawings ###########################

    dwg_nodes = fp_additional_drawing.create_additional_drawings(
        series_props.additional_drawings, global_config, fp_evaluator
    )
    kicad_mod.extend(dwg_nodes)

    ############################# CrtYd ##################################

    courtyard_offset = global_config.get_courtyard_offset(GC.GlobalConfig.CourtyardType.CONNECTOR)
    cb = CourtyardBuilder.from_node(node=kicad_mod, global_config=global_config, offset_fab=courtyard_offset)
    kicad_mod += cb.node

    ######################### Pin 1 marker ##############################

    marker_len = global_config.fab_pin1_marker_length

    if series_props.pin1_fab_marker_y is not None:
        pin1_fab_marker_y = series_props.pin1_fab_marker_y.evaluate(fp_evaluator)
    else:
        # Auto position
        if series_props.pins_toward_bottom:
            pin1_fab_marker_y = body_rect.bottom
        else:
            pin1_fab_marker_y = body_rect.top

        # And also autosize

        # How far is the pin 1 centre from the nearest kink in the line?
        distance_to_edge = abs(modified_pinside_x_inner - (-dimension_A / 2))
        marker_len = min(distance_to_edge * 2, marker_len)

    if marker_len < 0.5:
        raise ValueError(
            "The automatic pin 1 fab marker is too small. "
            "You should use 'pin1_fab_marker_y' to put it in the right place"
        )

    # Work out which way it points
    if pin1_fab_marker_y > body_rect.center.y:
        pin1_fab_marker_dir = Direction.NORTH
    else:
        pin1_fab_marker_dir = Direction.SOUTH

    # draw_pin1_chevron_on_hline is what we really need but it's a lot of diffs
    # and we should change the silk arrow at the same time.
    pin1_chevron_pts = [
        [-dimension_A / 2 - marker_len / 2, pin1_fab_marker_y],
        # apex: point it the right way
        [
            -dimension_A / 2,
            (
                pin1_fab_marker_y
                + (marker_len / sqrt(2))
                * (1 if (pin1_fab_marker_dir == Direction.SOUTH) else -1)
            ),
        ],
        [-dimension_A / 2 + marker_len / 2, pin1_fab_marker_y],
    ]
    kicad_mod += PolygonLine(
        shape=pin1_chevron_pts, layer="F.Fab", width=global_config.fab_line_width
    )

    if series_props.pins_toward_bottom:
        cy2 = cb.bbox.bottom
        poly_pin1_marker_silk = [
            [-dimension_A/2-marker_len/4, cy2 + marker_len/sqrt(8)],
            [-dimension_A/2, cy2],
            [-dimension_A/2+marker_len/4, cy2 + marker_len/sqrt(8)],
            [-dimension_A/2-marker_len/4, cy2 + marker_len/sqrt(8)],
        ]
    else:
        cy1 = cb.bbox.top
        poly_pin1_marker_silk = [
            [-dimension_A/2-marker_len/4, cy1 - marker_len/sqrt(8)],
            [-dimension_A/2, cy1],
            [-dimension_A/2+marker_len/4, cy1 - marker_len/sqrt(8)],
            [-dimension_A/2-marker_len/4, cy1 - marker_len/sqrt(8)]
        ]

    if needs_additional_silk_pin1_marker:
        kicad_mod.append(PolygonLine(shape=poly_pin1_marker_silk, layer='F.SilkS', width=global_config.silk_line_width))

    ######################### Text Fields ###############################
    addTextFields(kicad_mod=kicad_mod, configuration=global_config, body_edges=body_rect.bbox(),
        courtyard=cb.bbox, fp_name=footprint_name,
        text_y_inside_position=series_props.text_inside_pos)

    ########################### file names ###############################
    lib_name = conn_config.lib_name_format_string.format(
        man=series_props.manufacturer,
        series=series_props.series,
    )
    model_name = '{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}{model3d_path_suffix:s}'.format(
        model3d_path_prefix=global_config.model_3d_prefix, lib_name=lib_name, fp_name=footprint_name,
        model3d_path_suffix=global_config.model_3d_suffix)
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
    configuration = ConnectorsConfiguration.load_from_file(os.path.expandvars(CLI_ARGS.connector_config))
    for _, yaml_file in get_spec_dicts(generator_name):
        series_definitions = yaml_file["device_definition"]
        for series_id, series_definition in series_definitions.items():
            group_definition = yaml_file["group_definitions"]
            series_props = SMDSingleRowPlusMPProperties(
                series_definition, group_definition, series_id
            )
            for idx, pincount in enumerate(series_props.pin_range):
                generate_one_footprint(
                    generator_name, GLOBAL_CONFIG, idx, pincount, series_props, configuration,
                )
                num_fps_generated += 1
    return num_fps_generated