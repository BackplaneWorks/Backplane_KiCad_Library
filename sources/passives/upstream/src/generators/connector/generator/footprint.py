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
# Original authors:
#   - Armin Schoisswohl (@armin.sch), <armin.schoisswohl@myotis.at>
#   - Carlos Nieves Ónega (@cnieves1)
#   - John Beard (@johnbeard)
#   - ... (not complete)
# (C) The KiCad Librarian Team

import abc
import copy
import enum
import warnings
import re

import argparse
import yaml
import math
from fnmatch import fnmatch
from typing import Any, Iterable, Callable
from dataclasses import dataclass, asdict
from KicadModTree import (
    Pad,
    RoundRadiusHandler,
    Footprint,
    FootprintType,
    Translation,
    PolygonLine,
    Circle,
    Rectangle,
    Model,
)
from kilibs.util import dict_tools
from kilibs.geom import BoundingBox, Vector2D
from generators.tools.footprint.footprint_text_fields import addTextFields
from generators.tools.footprint.declarative_def_tools import utils, rule_area_properties, fp_additional_drawing
from generators.tools.footprint.declarative_def_tools.utils import DotDict
from generators.tools.footprint.declarative_def_tools.ast_evaluator import ASTevaluator, ASTexprEvaluator
from generators.tools.footprint.drawing_tools import point_is_on_segment
from generators.tools.footprint.save_footprint import write_footprint
from kilibs.config import global_config as GC

from generators.tools.spec.base_spec import BaseSpec
from .spec import ConnectorSpec
from kilibs.config.global_config import GLOBAL_CONFIG
from ..config import CONNECTOR_CONFIG


DEFAULT_SMT_PAD_SHAPE = 'roundrect'
DEFAULT_THT_PAD_SHAPE = 'oval'
DEFAULT_THT_PIN1_PAD_SHAPE = 'roundrect'


def _get_dims(name: str, spec: dict, base: Vector2D = None, mult: float=1):
    if (base is None):
        base = Vector2D(0, 0)
    vals = spec.get(name, {})
    if isinstance(vals, dict):
        return Vector2D(*[_get_dim(name, spec, dim="xy"[n], mult=mult,
                                   base=base[n]) for n in range(2)])
    elif isinstance(vals, list):
        return Vector2D(*[v for v in vals])
    elif isinstance(vals, (float, int, str)):
        return base + vals
    else:
        return base


def _get_dim(name: str, spec: dict, dim: str, base: float=0.0, mult: float=1):
    if (name not in spec):
        return base
    dim_spec = spec[name]
    if (dim in dim_spec):
        if ("%s_offset" % dim in dim_spec):
            warnings.warn(f"\nboth, {dim} and {dim}_offset are specified; {dim}_offset is overridden by {dim}", Warning)
        return dim_spec[dim]
    elif (base != 0.0 and "%s_offset" % dim in dim_spec):
        value = dim_spec["%s_offset" % dim]
        if isinstance(value, (int, float, str)):
            return base + mult * value
        else:
            return [base + mult * v for v in value]
    else:
        raise LookupError("one of '%s', '%s_offset' has to be specified for '%s'" % (dim, dim, name))


def _round_to(val, base, direction: str=None):
    if (isinstance(val, Iterable)):
        return [_round_to(v, base, direction) for v in val]
    if (direction in ['+', 1]):
        return math.ceil(val / base) * base
    elif (direction in ['-', -1]):
        return math.floor(val / base) * base
    else:
        return round(val / base) * base


class PadLayout(abc.ABC):

    @abc.abstractmethod
    def get_pad_pos(self, index) -> Vector2D:
        """
        Returns the position of the pad with the given index
        """
        pass

    @abc.abstractmethod
    def get_pad_name(self, index) -> str:
        """
        Returns the name of the pad with the given index
        """
        pass

class PadGridLayout(PadLayout):
    """
    Pad layout for a grid of pads
    """

    class NumberingAxis(enum.Enum):
        ROW_FIRST = 0
        COL_FIRST = 1


    def __init__(self, pad_pitch: float, row_pitch: float, pads_per_row: int, num_rows: int, pin1_at_top: bool,
                 y_stagger_length: int, y_stagger_offset: float,
                 numbering_axis: NumberingAxis, gap_pos: int, gap_size: int):
        self.pad_pitch = pad_pitch
        self.row_pitch = row_pitch
        self.pads_per_row = pads_per_row
        self.num_rows = num_rows
        self.pin1_at_top = pin1_at_top

        self.y_stagger_length = y_stagger_length
        self.y_stagger_offset = y_stagger_offset

        # how far does y-stagger move in a complete cycle
        self._y_stagger_span = (self.y_stagger_length - 1) * self.y_stagger_offset

        self.numbering_axis = numbering_axis

        self.gap_pos = gap_pos
        self.gap_size = gap_size

        # The span of the nominal rows - pad pos
        self.y_span = self.row_pitch * (self.num_rows - 1)
        self.x_span = self.pad_pitch * (self.pads_per_row + self.gap_size - 1)

    def _row_col(self, index) -> tuple[int, int]:
        """
        Returns the row and column of the pad with the given index
        """
        row = index // self.pads_per_row
        col = index % self.pads_per_row
        return row, col

    def get_pad_pos(self, index) -> Vector2D:
        """"
        Get the pad position relative to the center of the grid
        """
        row, col = self._row_col(index)

        # Step over the gap
        if self.gap_size and col >= self.gap_pos:
            col += self.gap_size

        # # reverse row position if pin1 is at the bottom
        if not self.pin1_at_top:
            row = self.num_rows - 1 - row

        if self.y_stagger_length == 1:
            y_off = 0
        else:
            y_off = (col % self.y_stagger_length) * -self.y_stagger_offset + (
                self._y_stagger_span / 2
            )

        pos = Vector2D(col * self.pad_pitch, row * self.row_pitch + y_off)

        return pos + Vector2D(
            -0.5 * self.x_span,
            -0.5 * self.y_span,
        )

    def get_pad_name(self, index) -> str:
        row, col = self._row_col(index)

        if self.numbering_axis == self.NumberingAxis.COL_FIRST:
            number = col * self.num_rows + row + 1
        else:
            number = row * self.pads_per_row + col + 1

        return str(number)

@dataclass
class PadProperties():
    size: Vector2D
    shape: str
    round_radius_handler: RoundRadiusHandler
    drill: float
    paste: bool
    type: str
    layers: list
    rotation: float

    def __init__(self, pad_spec: dict, global_config: GC.GlobalConfig, default_paste: bool = None):
        self.size = self._get_pad_size(pad_spec)
        self.shape = self._get_pad_shape(pad_spec)
        self.round_radius_handler = self._get_radius_handler(pad_spec, global_config)
        self.drill = self._get_pad_drill(pad_spec)
        self.paste = self._get_pad_paste(pad_spec, default_paste)
        self.type = self._get_pad_type(pad_spec)
        self.layers = self._get_pad_layers(pad_spec, default_paste)
        self.rotation = self._get_pad_rotation(pad_spec)

        if (not self.size or self.size.is_nullvec()):
            self.size = Vector2D(self.drill, self.drill)

        if (self.paste and self.type != Pad.TYPE_NPTH and 'F.Paste' not in self.layers):
            self.layers.append('F.Paste')

    def as_args(self):
        return {k: v for k, v in asdict(self).items() if v is not None}

    def _get_pad_size(self, pad_spec):
        return _get_dims("size", spec=pad_spec)

    def _get_pad_shape(self, pad_spec):
        shape = pad_spec.get("shape", None)
        if (shape is None):
            shape = DEFAULT_THT_PAD_SHAPE if self._get_pad_drill(pad_spec) else DEFAULT_SMT_PAD_SHAPE
        return {"rect": Pad.SHAPE_RECT,
                "roundrect": Pad.SHAPE_ROUNDRECT,
                "circ": Pad.SHAPE_CIRCLE,
                "oval": Pad.SHAPE_OVAL,
                }[shape]

    def _get_radius_handler(self, pad_spec, global_config: GC.GlobalConfig):
        ratio = pad_spec.get("radius_ratio", global_config.round_rect_default_radius)
        rmax = pad_spec.get("max_radius", global_config.round_rect_max_radius)
        return RoundRadiusHandler(radius_ratio=ratio, maximum_radius=rmax)

    def _get_pad_drill(self, pad_spec):
        return pad_spec.get("drill", None)

    def _get_pad_paste(self, pad_spec, default_paste: bool = None):
        if (default_paste is None):
            return pad_spec.get("paste", False if self._get_pad_drill(pad_spec) else True)
        else:
            return pad_spec.get("paste", default_paste)

    def _get_pad_copper(self, pad_spec):
        return pad_spec.get("copper", True)

    def _get_pad_type(self, pad_spec):
        if (self._get_pad_drill(pad_spec)):
            if (self._get_pad_copper(pad_spec) and self._get_pad_drill(pad_spec) < max(self._get_pad_size(pad_spec))):
                return Pad.TYPE_THT
            else:
                return Pad.TYPE_NPTH
        else:
            return Pad.TYPE_SMT

    def _get_pad_layers(self, pad_spec, default_paste: bool = None):
        copper = self._get_pad_copper(pad_spec)
        paste = self._get_pad_paste(pad_spec, default_paste)
        pad_type = self._get_pad_type(pad_spec)
        if (pad_type == Pad.TYPE_NPTH):
            return Pad.LAYERS_NPTH
        elif (pad_type == Pad.TYPE_THT):
            return Pad.LAYERS_THT + ['F.Paste'] if (paste is True) else Pad.LAYERS_THT
        elif (pad_type == Pad.TYPE_SMT):
            if (copper is False):
                return [] if (paste is False) else ['F.Paste']
            else:
                return Pad.LAYERS_CONNECT_FRONT if (paste is False) else Pad.LAYERS_SMT

    def _get_pad_rotation(self, pad_spec):
        return pad_spec.get("rotation", 0)

@dataclass
class FPconfiguration():
    library_name: str
    type: FootprintType
    pad_pitch: float
    num_pos: int
    pad_size: Vector2D
    pad_pos_range: Vector2D
    pad_center_offset: Vector2D
    row_pitch: float = 0.0
    row_x_offset: float = 0.0
    num_rows: int = 1
    gap_pos: int = 0
    gap_size: int = 0
    pad_properties: PadProperties = None
    pad1_properties: PadProperties = None
    skipped_positions: list = None
    num_mount_pads: int = 0
    body_edges: dict = None
    rule_areas: list = None
    silk_fab_offset : float = 0.0
    silk_line_width : float = 0.0
    text_inside_pos: float | str = "center"
    clean_silk: bool = True
    pin1_pos: str = 'top'
    pin1_body_chamfer: float = 0.0
    pin1_marker_shape: str = None
    pin1_marker_size: float = 0.0
    pin1_marker_pos: Vector2D = None
    pin1_on_fab: bool = True
    pin1_fab_y_inset: float = 0.0
    parameters: dict = None
    expr_eval: Callable = None

    def __init__(
        self,
        spec: dict,
        global_config: GC.GlobalConfig,
        positions: int,
        idx: int,
    ):
        self.library_name = spec["library"]
        self.num_pos = positions
        # create the evaluator
        self.asteval = ASTevaluator(protected=True)
        # parse parameters first
        params: dict[str, Any] = spec.get('parameters', {})
        params.update(num_pos=positions, idx=idx)
        self.parameters = self.asteval.eval(params, allow_self_ref=True, symbols=spec, allow_nested=True) # TODO: allow_nested should allow arbitrary eorder evaluations
        # parse spec but skip back the following sections as they may need t, b, l, r, etc.
        self.spec = self.asteval.eval(spec, allow_self_ref=True, raise_errors=True, symbols=self.parameters, allow_nested=True)

        self.pad_pitch = self.spec["pad_pitch"]
        ## row pitch defines if it is a single or dual row connector
        self.row_pitch = self.spec.get("row_pitch", None)

        if (self.row_pitch is None):
            self.row_pitch = 0.0

        if "num_rows" in self.spec:
            self.num_rows = self.spec["num_rows"]
        else:
            self.num_rows = 2 if self.row_pitch else 1

        if self.num_rows > 1 and not self.row_pitch:
            raise ValueError("num_rows > 1 but row_pitch not specified")

        self.numbering_axis = self.spec.get("numbering_axis", "col_first")

        # We will need 'grid' for SEARAYs
        if self.numbering_axis not in ["row_first", "col_first"]:
            raise ValueError("numbering must be 'row_first' or 'col_first'")

        # Stagger of pins in y along a single row
        pin_y_stagger_cycle = self.spec.get("pin_y_stagger_cycle", 1)
        pin_y_stagger_offset = self.spec.get("pin_y_stagger_offset", 0.0)

        ## row_x_offset defines if it has staggered pins or not
        self.row_x_offset = self.spec.get("row_x_offset", 0.0)

        # Get information about 1st pin.
        # This is required even if num_rows is 1, becasue we still need to know
        # which side the pin 1 marker goes on.
        try:
            first_pin_spec = self.spec["first_pin"]
            self.pin1_pos = first_pin_spec["position"]
        except KeyError:
            raise ValueError(
                "Missing mandatory field 'first_pin.position' in footprint specification"
            )

        if self.pin1_pos not in ["top", "bottom"]:
            raise ValueError("'first_pin.position' must be one of 'top', 'bottom'")

        ## collection information about an eventual gap in the pin layout
        gap = self.spec.get("gap", {}).get(positions, [0, 0])

        if (isinstance(gap, dict)):
            gap = [ gap.get("position", 0), gap.get("size", 1) ]
        elif (isinstance(gap, int)):
            gap = [gap, 1]

        self.gap_pos, self.gap_size = gap

        if (self.gap_pos and self.gap_size):
            self.skipped_positions = [self.gap_pos + n for n in range(self.gap_size)]
        else:
            self.skipped_positions = []

        self.pad_layout = PadGridLayout(
            self.pad_pitch,
            self.row_pitch,
            self.num_pos,
            self.num_rows,
            y_stagger_length=pin_y_stagger_cycle,
            y_stagger_offset=pin_y_stagger_offset,
            pin1_at_top=self.pin1_pos == "top",
            numbering_axis=(
                PadGridLayout.NumberingAxis.COL_FIRST
                if self.numbering_axis == "col_first"
                else PadGridLayout.NumberingAxis.ROW_FIRST
            ),
            gap_pos = self.gap_pos,
            gap_size = self.gap_size,
        )

        ## check if there are mount pads
        self.num_mount_pads = len({ep["name"] for ep in self.spec.get("mount_pads", {}).values() if "name" in ep})

        ## get pad positions and size
        pad_spec = self.spec.get("pads")
        self.pad_properties = PadProperties(pad_spec, global_config)
        self.pad_size = self.pad_properties.size

        self.pad_center_offset = _get_dims("pads", spec=self.spec.get("offset", {}))
        self.pad_pos_range = Vector2D(
            (positions + self.gap_size - 1) * self.pad_pitch,
            self.row_pitch * (self.num_rows - 1),
        )

        ## calculate body size
        body_size = _get_dims("body_size", spec=self.spec, base=self.pad_pos_range, mult=2)
        body_center_offset = _get_dims("body", spec=self.spec.get("offset", {}))
        self.body_edges = DotDict({
            "left": -0.5 * body_size.x + body_center_offset.x,
            "right": 0.5 * body_size.x + body_center_offset.x,
            "top": -0.5 * body_size.y + body_center_offset.y,
            "bottom": 0.5 * body_size.y + body_center_offset.y,
        })

        # assemble the dimensions
        self.parameters.update({k[0]: v for k, v in self.body_edges.items()})
        self.parameters.pl = -0.5 * self.pad_pos_range.x + self.pad_center_offset.x
        self.parameters.pr = 0.5 * self.pad_pos_range.x + self.pad_center_offset.x
        self.parameters.pt = -0.5 * self.pad_pos_range.y + self.pad_center_offset.y
        self.parameters.pb = 0.5 * self.pad_pos_range.y + self.pad_center_offset.y

        self.parameters.body_center = body_center_offset

        self.expr_eval = ASTexprEvaluator(symbols=self.parameters)

        ## Get rule areas
        self.rule_areas = rule_area_properties.RuleAreaProperties.from_standard_yaml(self.spec)

        self.text_inside_pos = self.spec.get("text_inside_pos", "center")

        self.clean_silk = self.spec.get('clean_silk', True)

        pad1_defaults = {}

        # Apply defaults based on the basic pad type
        if self.pad_properties.type == Pad.TYPE_THT:
            pad1_defaults["shape"] = DEFAULT_THT_PIN1_PAD_SHAPE

        pad1_spec = first_pin_spec.get("pad", {})

        # The pad1 spec is the normal pad spec, updated with the pin 1 defaults, then the pin 1 spec
        dict_tools.dict_merge(pad_spec, pad1_defaults)
        dict_tools.dict_merge(pad1_defaults, pad1_spec)

        self.pad1_properties = PadProperties(pad1_spec, global_config)

        ## body chamfer at pin1 corner
        self.pin1_body_chamfer = first_pin_spec.get("body_chamfer", 0.0)
        # on some locations scale_y will do the magic to be on the correct side relative to the pin 1 side
        self.scale_y = { "top": -1, "bottom": 1 }[self.pin1_pos]

        ## pin 1 marker properties
        self.pin1_marker_shape = first_pin_spec.get("marker", {}).get("shape", None)
        self.pin1_marker_size = first_pin_spec.get("marker", {}).get("size", self.pad_size.x) / 2
        pin1_offset = first_pin_spec.get("marker", { }).get("offset", 0)
        if (isinstance(pin1_offset, (int, float))):
            pin1_offset = Vector2D(0, pin1_offset)
        elif (isinstance(pin1_offset, dict)):
            pin1_offset = Vector2D(**pin1_offset)
        else:
            pin1_offset = Vector2D(*pin1_offset)
        pin1_offset.y += self.pin1_marker_size

        self.pin1_marker_pos = Vector2D(-0.5 * (self.pad_pos_range.x + self.row_x_offset) + self.pad_center_offset.x,
                                        self.body_edges[self.pin1_pos]) + pin1_offset * Vector2D(1, self.scale_y)
        self.draw_pin1_marker_on_fab = first_pin_spec.get("marker", { }).get("fab", True)

        # Sometimes, the fab marker needs to be set manually
        self.pin1_fab_y_inset = first_pin_spec.get("marker", {}).get("fab_y_inset", 0.0)

        self.exclude_from_bom = self.spec.get("exclude_from_bom", False)
        self.exclude_from_pos = self.spec.get("exclude_from_pos", False)

        if "footprint_type" in self.spec:
            match self.spec["footprint_type"]:
                case "SMD":
                    self.type = FootprintType.SMD
                case "THT":
                    self.type = FootprintType.THT
                case "unspecified":
                    self.type = FootprintType.UNSPECIFIED
                case _:
                    raise ValueError(
                        "Footprint type must be either 'SMD', 'THT' or 'unspecified'."
                    )
        elif self.pad_properties.type == Pad.TYPE_SMT:
            self.type = FootprintType.SMD
        else:
            self.type = FootprintType.THT

        self.additional_drawings = (
            fp_additional_drawing.FPAdditionalDrawing.from_standard_yaml(self.spec)
        )

    def eval_coordinate(self, coord):
        return self.asteval.parse_float(coord, symbols=self.parameters)


def parse_body_shape(spec, *, side: str, eval_expr: Callable):
    shape_spec = spec.get(side, {})
    sign = Vector2D(1,1)
    if (shape_spec == "mirror"):
        shape_spec = spec.get({"left": "right", "right": "left", "top": "bottom", "bottom": "top"}[side], {})
        if (side in ["left", "right"]):
            sign.x = -1
        else:
            sign.y = -1

    nodes = []
    if shape_spec:
        for shape in shape_spec.keys():
            if shape == "polyline":
                for node in shape_spec[shape]:
                    try:
                        xy = Vector2D(*[eval_expr(coord) for coord in node])
                        nodes.append(sign * xy)
                    except KeyboardInterrupt:
                        raise
                    except Exception:
                        raise ValueError("failed to parse polyline node '%s'" % node)
            else:
                raise ValueError("only polyline shapes are implemented, not '%s'" % shape)
    # eventuelly revert the node list to make sure we are running clockwise (in the KiCad coordinate system)
    reverse = False
    if (len(nodes) > 1):
        if (side == "left" and nodes[0].y < nodes[-1].y):
            reverse = True
        if (side == "right" and nodes[0].y > nodes[-1].y):
            reverse = True
        if (side == "top" and nodes[0].x > nodes[-1].x):
            reverse = True
        if (side == "bottom" and nodes[0].x < nodes[-1].x):
            reverse = True
    return [_ for _ in reversed(nodes)] if reverse else nodes


def generate_one_footprint(
    generator_name: str,
    global_config: GC.GlobalConfig,
    positions: int,
    spec: dict,
    configuration: dict,
    idx=0,
):
    for f in ["description", "tags", "fp_name", ]:
        if (f not in spec):
            raise ValueError(f"missing mandatory field '{f}' in footprint specification")

    fp_config = FPconfiguration(
        spec,
        global_config=global_config,
        positions=positions,
        idx=idx,
    )

    # for format strings both, all fields of the spec and all fields of spec.parameters are accessible
    format_dict = DotDict(**fp_config.spec, **fp_config.parameters)

    ## assemble footprint name
    fp_name = fp_config.spec.fp_name.format(**format_dict)

    rows = fp_config.spec.get('fp_name_rows', fp_config.num_rows)
    pins_per_row = fp_config.spec.get('fp_name_pins_per_row', fp_config.num_pos)
    fp_name += "_%dx%02d"  % (rows, pins_per_row)

    if (fp_config.num_mount_pads):
        fp_name += "-%dMP" % fp_config.num_mount_pads

    pitch = fp_config.spec.get('fp_name_pitch', fp_config.pad_pitch)
    fp_name += "_P%smm" %  pitch

    if (fp_config.gap_pos and fp_config.gap_size):
        fp_name += "_Pol%02d" % fp_config.gap_pos

    fp_name += fp_config.spec.get("fp_suffix", "").format(**format_dict)

    ## create the footprint
    kicad_mod = Footprint(fp_name, fp_config.type)

    kicad_mod.excludeFromBOM = fp_config.exclude_from_bom
    kicad_mod.excludeFromPositionFiles = fp_config.exclude_from_pos

    ## set the FP description
    description = fp_config.spec.description.format(**format_dict)
    if (src := fp_config.spec.get("source", None)):
        description += " (source: " + src + ")"
    kicad_mod.description = description

    ## set the FP tags
    tags = fp_config.spec.tags.format(**format_dict)
    kicad_mod.tags = tags

    ## create extra pads/drills
    for mp_name, pad_spec in fp_config.spec.get("mount_pads", DotDict()).items():
        add_mount_pad(kicad_mod,
                      global_config=global_config,
                      pad_pos_range=fp_config.pad_pos_range,
                      pad_spec=pad_spec,
                      pad_center_offset=fp_config.pad_center_offset,
                      default_paste=fp_config.pad_properties.paste,
                      row_x_offset=fp_config.row_x_offset)

    ## collect information from body_shape spec
    body_spec = fp_config.spec.get("body_shape", DotDict())
    body_shape_nodes = build_body_shape(body_spec, fp_config=fp_config)

    ## draw body outline on F.Fab
    fab_outline = PolygonLine(shape=body_shape_nodes,
                              layer="F.Fab",
                              width=global_config.fab_line_width)
    kicad_mod.append(fab_outline)

    ## Any additional drawings?
    kicad_mod += fp_additional_drawing.create_additional_drawings(
        fp_config.additional_drawings, global_config, fp_config.expr_eval
    )

    ## create Pads
    for pad_index in range(fp_config.num_rows * positions):

        pad_pos = fp_config.pad_layout.get_pad_pos(pad_index)
        pad_name = fp_config.pad_layout.get_pad_name(pad_index)

        pad_props = (
            fp_config.pad1_properties
            if (pad_index == 0 and fp_config.pad1_properties)
            else fp_config.pad_properties
        )

        kicad_mod.append(
            Pad(
                number=pad_name,
                at=pad_pos + fp_config.pad_center_offset,
                **pad_props.as_args(),
            )
        )

    ## Create rule areas (keepouts)
    rule_area_zones = rule_area_properties.create_rule_area_zones(fp_config.rule_areas,
                                                                  expr_evaluator=fp_config.expr_eval)
    for rule_area_zone in rule_area_zones:
        kicad_mod.append(rule_area_zone)

    ## calculate the bounding box of the whole footprint (excluding silk)
    bbox = kicad_mod.bbox()

    ## draw silk
    ## duplicate the body shape contour onto F.SilkS with the silk_fab_offset
    silk_outline = fab_outline.copy_with(layer="F.SilkS",
                                         offset=global_config.silk_fab_offset,
                                         width=global_config.silk_line_width)
    kicad_mod.append(silk_outline)

    ## pin 1 indicator on Silk
    pin1_silk = make_pin1_marker(pos=fp_config.pin1_marker_pos,
                                 radius=fp_config.pin1_marker_size,
                                 shape=fp_config.pin1_marker_shape,
                                 flip_marker=fp_config.scale_y < 0,
                                 width=global_config.silk_line_width,
                                 offset=global_config.silk_fab_offset + 2 * global_config.silk_line_width)
    if (pin1_silk is not None):
        kicad_mod.append(pin1_silk)

    if (fp_config.draw_pin1_marker_on_fab):
        pin1_fab_pnts = make_pin1_fab_marker_points(fp_config, global_config)
        # close polygon only if the closing line is not contained in the F.Fab outline
        if (not check_if_points_on_lines(kicad_mod, [pin1_fab_pnts[n] for n in [0, -1]], layer='F.Fab')):
            pin1_fab_pnts.append(pin1_fab_pnts[0])
        pin1_fab = PolygonLine(shape=pin1_fab_pnts, layer='F.Fab', width=global_config.fab_line_width)
        kicad_mod.append(pin1_fab)

    # calculate CourtYard
    cy_offset = global_config.get_courtyard_offset(GC.GlobalConfig.CourtyardType.CONNECTOR)
    courtyard = calculate_courtyard(bbox, offsets= cy_offset, global_config=global_config)
    # append CourtYard rectangle
    kicad_mod.append(Rectangle(**courtyard, layer='F.CrtYd', width=global_config.courtyard_line_width))

    ## clean silk
    if fp_config.clean_silk:
        kicad_mod.clean_silk_mask_overlap(
            side="F",
            silk_pad_clearance=global_config.silk_pad_clearance,
            silk_line_width=global_config.silk_line_width,
        )

    ######################### Text Fields ###############################
    courtyard_box = BoundingBox(courtyard["start"], courtyard["end"])
    body_box = BoundingBox(
        Vector2D(fp_config.body_edges["left"], fp_config.body_edges["top"]),
        Vector2D(fp_config.body_edges["right"], fp_config.body_edges["bottom"]),
    )
    addTextFields(kicad_mod=kicad_mod, configuration=global_config, body_edges=body_box,
                  courtyard=courtyard_box, fp_name=fp_name, text_y_inside_position=fp_config.text_inside_pos)

    lib_name = configuration['lib_name_specific_function_format_string'].format(category=fp_config.library_name)

    ## 3D model
    kicad_mod.append(Model(filename=f"{global_config.model_3d_prefix}{lib_name}.3dshapes/{fp_name}{global_config.model_3d_suffix}",
                            at=[0, 0, 0], scale=[1, 1, 1], rotate=[0, 0, 0]))

    write_footprint(kicad_mod, lib_name, generator_name)


def calculate_courtyard(bbox: BoundingBox, offsets, global_config: GC.GlobalConfig):

    offset = global_config.get_courtyard_offset(GC.GlobalConfig.CourtyardType.CONNECTOR)
    grid = global_config.courtyard_grid

    # TODO: calculate courtyard from all nodes on specific layers
    courtyard = {"start": bbox.min, "end": bbox.max}
    ## get CourtYard offset specification
    if (isinstance(offsets, (int, float))):
        cy_off = { k: Vector2D(offsets, offsets) for k in ["start", "end"] }
    elif isinstance(offsets, dict):
        cy_off = { k: Vector2D(0, 0) for k in ["start", "end"] }
        for e in ["start", "end"]:
            cy_off[e].x = offsets.get('x', offset)
            cy_off[e].y = offsets.get('y', offset)
        cy_off["start"].x = offsets.get("left", cy_off["start"].x)
        cy_off["start"].y = offsets.get("top", cy_off["start"].y)
        cy_off["end"].x = offsets.get("right", cy_off["end"].x)
        cy_off["end"].y = offsets.get("bottom", cy_off["end"].y)
    else:
        raise ValueError("invalid courtyard specification, must be a float or a dictionary")
    courtyard["start"] = Vector2D(*[_round_to(v - off, grid, '-')
                                    for v, off in zip(courtyard["start"], cy_off["start"])])
    courtyard["end"] = Vector2D(*[_round_to(v + off, grid, '+')
                                  for v, off in zip(courtyard["end"], cy_off["end"])])
    return courtyard


def make_pin1_marker(*, pos, radius, shape, flip_marker, width, offset):
    offset_vec = Vector2D(0, offset * (1 if flip_marker else -1))
    if (shape == "circle"):
        pin1_silk = Circle(center=pos - offset_vec, radius=radius, layer='F.SilkS', width=width)
    elif (shape == 'line'):
        line_midlength = Vector2D(radius, 0)
        pnts = [pos-offset_vec-line_midlength, pos-offset_vec+line_midlength]
        pin1_silk = PolygonLine(shape=pnts, layer='F.SilkS', width=width)
    elif (shape == "triangle"):
        pnts = []
        for n in range(3):
            vertex = Vector2D(
                math.sin(2 * n * math.pi / 3),
                math.cos(2 * n * math.pi / 3) * (1 if flip_marker else -1)
            )
            pnts.append(pos - offset_vec + radius * vertex)
        pin1_silk = PolygonLine(shape=pnts + pnts[:1], layer='F.SilkS', width=width)
    elif (shape):
        raise ValueError("invalid pin 1 marker shape '%s'" % shape)
    else:
        pin1_silk = None
    return pin1_silk


def check_if_points_on_lines(kicad_mod, points, layer):
    for node in kicad_mod:
        if (isinstance(node, PolygonLine) and node.layer == layer):
            for l in node.lineItems():
                if all(l.is_point_on_self(p) for p in points):
                    return True
    return False


def make_pin1_fab_marker_points(fp_config: FPconfiguration, global_config: GC.GlobalConfig) -> list:
    # pin 1 on Fab is a triangle

    # location of the tip in x
    tip_x = -0.5 * (fp_config.pad_pos_range.x + fp_config.row_x_offset) + fp_config.pad_center_offset.x

    # width and height of the triangle
    dx = min(fp_config.pad_pitch, global_config.fab_pin1_marker_length)
    dy = 0.8 * fp_config.scale_y * dx

    base_y = fp_config.body_edges[fp_config.pin1_pos] - fp_config.pin1_fab_y_inset * fp_config.scale_y

    pnts = [
        Vector2D(tip_x - 0.5 * dx, base_y),
        Vector2D(tip_x, base_y - dy),
        Vector2D(tip_x + 0.5 * dx, base_y),
    ]
    return pnts


def clean_body_shape(body_shape_nodes):
    # Check if there are 3 points in the same line, and remove the center point
    max_index = len(body_shape_nodes)-3
    i = -1
    while i <= max_index and i+2 <=max_index:
        node_a = body_shape_nodes[i]
        node_b = body_shape_nodes[i+1]
        node_c = body_shape_nodes[i+2]
        node_changed = False
        # Check first if some points are the same, otherwise, point_is_on_segment wouldn't work properly.
        if node_a == node_b:
                del body_shape_nodes[i]
                i = i-1 # Reevaluate from the index before to remove duplicates
                node_changed = True
        elif node_b == node_c:
                del body_shape_nodes[i+1]
                i = i-1 # Reevaluate from the index before to remove duplicates
                node_changed = True
        elif node_a == node_c:
                warnings.warn(f"\nPiece of shape with zero thickness is removed: {body_shape_nodes[i]}, {body_shape_nodes[i+1]}, {body_shape_nodes[i+2]}.", Warning)
                del body_shape_nodes[i+1]
                i = i-1 # Reevaluate from the index before to remove duplicates
                node_changed = True
        elif point_is_on_segment(node_b, node_c, node_a):
                # If A between B and C
                del body_shape_nodes[i]
                node_changed = True
        elif point_is_on_segment(node_a, node_c, node_b):
                # If B between A and C
                del body_shape_nodes[i+1]
                node_changed = True
        elif point_is_on_segment(node_a, node_b, node_c):
                # If C between A and B
                del body_shape_nodes[i+2]
                node_changed = True
        if node_changed:
                i = i-1
                max_index = max_index-1
        i = i+1


def build_body_shape(body_spec: dict, *, fp_config: FPconfiguration):

    body_shapes = { }
    for side in ["left", "top", "right", "bottom"]:
        body_shapes[side] = parse_body_shape(body_spec, side=side, eval_expr=fp_config.expr_eval)
    ## create body shape as a polygon
    left = fp_config.body_edges['left']
    right = fp_config.body_edges['right']
    top = fp_config.body_edges['top']
    bot = fp_config.body_edges['bottom']
    body_shape_nodes = []
    # top left corner (eventually with pin 1 chamfer)
    if (fp_config.pin1_pos == "top" and fp_config.pin1_body_chamfer):
        body_shape_nodes.append(Vector2D(left, top + fp_config.pin1_body_chamfer))
        body_shape_nodes.append(Vector2D(left + fp_config.pin1_body_chamfer, top))
    else:
        body_shape_nodes.append(Vector2D(left, top))
    # top shape (eventually empty)
    body_shape_nodes += body_shapes["top"]
    # top right corner
    body_shape_nodes.append(Vector2D(right, top))
    # right shape (eventually empty)
    body_shape_nodes += body_shapes["right"]
    # bottom right corner
    body_shape_nodes.append(Vector2D(right, bot))
    # bottom shape (eventually empty)
    body_shape_nodes += body_shapes["bottom"]
    # bottom left corner (eventually with pin 1 chamfer)
    if (fp_config.pin1_pos == "bottom" and fp_config.pin1_body_chamfer):
        body_shape_nodes.append(Vector2D(left + fp_config.pin1_body_chamfer, bot))
        body_shape_nodes.append(Vector2D(left, bot - fp_config.pin1_body_chamfer))
    else:
        body_shape_nodes.append(Vector2D(left, bot))
    # left shape (eventually empty)
    body_shape_nodes += body_shapes["left"]

    clean_body_shape(body_shape_nodes)

    # close shape
    body_shape_nodes.append(body_shape_nodes[0])
    return body_shape_nodes


def add_mount_pad(kicad_mod, global_config, pad_pos_range, pad_spec, pad_center_offset, default_paste, row_x_offset):
    center_to_center = _get_dim("center", spec=pad_spec, dim="x", base=pad_pos_range.x, mult=2) + row_x_offset
    pad_pos_y = utils.as_list(_get_dim("center", spec=pad_spec, dim="y"))
    pad_props = PadProperties(pad_spec, global_config, default_paste=default_paste)
    pad_nums = utils.as_list(pad_spec.get('name', [""]))
    if isinstance(pad_nums, (str, int)):
        pad_nums = [pad_nums]
    if len(pad_nums) == 1:
        pad_nums = pad_nums * len(pad_pos_y)
    ends = pad_spec.get('ends', 'both')
    for end in ('left', 'right'):
        if (ends not in [end, 'both']):
            continue
        for num, y in zip(pad_nums, pad_pos_y):
            pad_pos = [{ 'left': -1, 'right': 1 }[end] * 0.5 * center_to_center + pad_center_offset.x, y + pad_center_offset.y]
            kicad_mod.append(Pad(at=pad_pos, number=num, **pad_props.as_args()))


def create_footprints(spec: ConnectorSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification.
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
    num_fps_generated = 0
    list_of_positions = spec.spec["positions"]
    if (isinstance(list_of_positions, str) and (match := re.match(r"^\s*\$\((.+)\)\s*$", list_of_positions))):
        list_of_positions = ASTexprEvaluator().eval(match[1])
    for idx, positions in enumerate(utils.as_list(list_of_positions)):
        generate_one_footprint(generator_name, GLOBAL_CONFIG, positions, idx=idx, spec=spec.spec, configuration=CONNECTOR_CONFIG)
        num_fps_generated += 1
    return num_fps_generated
