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
import yaml
from typing import Optional

from KicadModTree import *  # NOQA
from kilibs.geom import Direction
from generators.tools.footprint.drawing_tools import SilkArrowSize
from generators.tools.footprint.drawing_tools_silk import draw_silk_triangle_for_pad
from generators.tools.footprint.save_footprint import write_footprint
from kilibs.config import global_config as GC


class Dimensions(object):

    def __init__(self, global_config: GC.GlobalConfig, base, variant, cut_pin=False, tab_linked=False):
        # FROM KLC
        self.fab_line_width_mm = global_config.fab_line_width
        self.silk_line_width_mm = global_config.silk_line_width
        self.courtyard_line_width_mm = global_config.courtyard_line_width
        self.courtyard_clearance_mm = global_config.get_courtyard_offset(GC.GlobalConfig.CourtyardType.DEFAULT)
        self.courtyard_precision_mm = global_config.courtyard_grid
        self.roundrect_radius_handler = global_config.roundrect_radius_handler

        # PIN NUMBERING
        self.centre_pin = 1 + variant["pins"] // 2
        self.tab_pin_number = (
            self.centre_pin if (tab_linked or cut_pin) else variant["pins"] + 1
        )

        # NAME
        self.name = self.footprint_name(
            base["series"],
            (variant["pins"] - 1) if cut_pin else variant["pins"],
            not cut_pin,
            self.tab_pin_number,
        )
        # PADS
        self.pad_1_centre_x_mm = (variant["pad"]["x_mm"] / 2.0) - (
            base["footprint"]["x_mm"] / 2.0
        )
        self.pad_1_centre_y_mm = -variant["pitch_mm"] * (variant["pins"] - 1) / 2.0
        self.tab_centre_x_mm = (
            base["footprint"]["x_mm"] - base["footprint"]["tab"]["x_mm"]
        ) / 2.0
        self.tab_centre_y_mm = 0.0
        self.split_paste = base["footprint"]["split_paste"] == "on"
        self.tab_size_x_mm = base["footprint"]["tab"]["x_mm"]
        self.tab_size_y_mm = base["footprint"]["tab"]["y_mm"]

        # FAB OUTLINE
        self.device_offset_x_mm = (
            base["device"]["x_mm"] / 2.0
        )  # x coordinate of RHS of device
        self.tab_project_x_mm = base["device"]["tab"]["project_x_mm"]
        self.tab_offset_y_mm = (
            base["device"]["tab"]["y_mm"] / 2.0
        )  # y coordinate of bottom of tab
        self.body_x_mm = base["device"]["body"]["x_mm"]
        self.body_offset_y_mm = (
            base["device"]["body"]["y_mm"] / 2.0
        )  # y coordinate of bottom of body
        self.corner_mm = (
            1.0  #  x and y size of chamfered corner on top left of body -- from KLC
        )
        self.tab_x_mm = base["device"]["tab"]["x_mm"]

        if self.tab_project_x_mm >= 0:
            # If the tab extends beyond the body, the device smaller than the footprint and
            # the F.Fab drawing is placed centered onto the footprint.
            self.device_shift_x_mm = 0
        else:
            # If the tab is not extending beyond the body the F.Fab drawing and CourtYard is
            # shifted such that the tab sits centered on it's pad
            tab_right_x_mm = self.device_offset_x_mm + min(0, self.tab_project_x_mm)
            tab_center_x_mm = tab_right_x_mm - self.tab_x_mm / 2
            self.device_shift_x_mm = self.tab_centre_x_mm - tab_center_x_mm

        # Calculate footprint center as body center (excluding pins and tab)
        body_right_x = (
            self.device_offset_x_mm
            - max(0, self.tab_project_x_mm)
            + self.device_shift_x_mm
        )
        self.footprint_origin_x_mm = body_right_x - self.body_x_mm / 2

        # COURTYARD
        left_x_mm = min(
            -base["device"]["x_mm"] / 2.0 + self.device_shift_x_mm,
            -base["footprint"]["x_mm"] / 2.0,
        )
        right_x_mm = max(
            base["device"]["x_mm"] / 2.0 + self.device_shift_x_mm,
            base["footprint"]["x_mm"] / 2.0,
        )
        biggest_y_mm = max(
            base["footprint"]["tab"]["y_mm"],
            base["device"]["body"]["y_mm"],
            2.0 * self.pad_1_centre_y_mm + variant["pad"]["y_mm"],
        )

        self.courtyard_left_x_mm = left_x_mm - self.courtyard_clearance_mm
        self.courtyard_right_x_mm = right_x_mm + self.courtyard_clearance_mm
        self.courtyard_offset_y_mm = self.courtyard_clearance_mm + biggest_y_mm / 2.0

        # SILKSCREEN
        self.label_centre_x_mm = 0
        self.label_centre_y_mm = self.courtyard_offset_y_mm + 1
        self.silk_line_nudge_mm = (
            0.20  #  amount to shift to stop silkscreen lines overlapping fab lines
        )
        self.silk_pad_clearance_mm = global_config.silk_pad_clearance

    @staticmethod
    def round_to(n, precision, direction: str = None):
        if direction == "+":
            return math.ceil(n / precision) * precision
        elif direction == "-":
            return math.floor(n / precision) * precision
        else:
            correction = 0.5 if n >= 0 else -0.5
            return int(n / precision + correction) * precision

    def footprint_name(self, series, num_pins, add_tab, tab_number):
        tab_suffix = "_TabPin" if add_tab else ""
        pins = str(num_pins)
        tab = str(tab_number) if add_tab else ""
        name = "{p:s}-{ps:s}{ts:s}{tn:s}".format(
            p=series, ps=pins, ts=tab_suffix, tn=tab
        )
        return name


class DPAK(object):

    base: dict
    variant: dict
    cut_pin: bool
    dim: Dimensions
    m: Footprint

    first_pad: Optional[Pad]
    tab_pad: Optional[Pad]

    global_config: GC.GlobalConfig

    def __init__(self, base: dict, variant: dict, cut_pin: bool, tab_linked: bool):
        """
        :param base: The base configuration for the DPAK series
        :param variant: The variant configuration for this specific DPAK
        :param cut_pin: Whether to remove the centre pin
        :param tab_linked: Whether the tab is linked to the centre pin, or has its own number
        """

        self.global_config = GC.GLOBAL_CONFIG

        self.base = base
        self.variant = variant
        self.cut_pin = cut_pin

        # Drawing state:
        # The first pad (usually pin 1)
        self.first_pad = None
        # The tab pad
        self.tab_pad = None

        # calculate self.dimensions and other attributes specific to this variant
        self.dim = Dimensions(self.global_config, self.base, self.variant, self.cut_pin, tab_linked)

        # initialise footprint
        self.m = Footprint(self.dim.name, FootprintType.SMD)

    def add_properties(self):
        self.m.setDescription(
            "{bd:s}, {vd:s}".format(
                bd=self.base["description"], vd=self.variant["datasheet"]
            )
        )
        self.m.setTags(
            "{bk:s} {vk:s}".format(
                bk=self.base["keywords"], vk=self.variant["keywords"]
            )
        )

    def add_labels(self):
        self.m.append(
            Property(
                name=Property.REFERENCE,
                text="REF**",
                size=[1, 1],
                at=[self.dim.label_centre_x_mm, -self.dim.label_centre_y_mm],
                layer="F.SilkS",
            )
        )
        self.m.append(Text(text="${REFERENCE}", size=[1, 1], at=[0, 0], layer="F.Fab"))
        self.m.append(
            Property(
                name=Property.VALUE,
                text=self.dim.name,
                at=[self.dim.label_centre_x_mm, self.dim.label_centre_y_mm],
                layer="F.Fab",
            )
        )

    def draw_tab(self, draw_hidden_part=False):
        if self.dim.tab_project_x_mm > 0 or draw_hidden_part:
            right_x = (
                self.dim.device_offset_x_mm
                + min(0, self.dim.tab_project_x_mm)
                + self.dim.device_shift_x_mm
                - self.dim.footprint_origin_x_mm
            )
            left_x = right_x - (
                self.dim.tab_x_mm if draw_hidden_part else self.dim.tab_project_x_mm
            )
            top_y = -self.dim.tab_offset_y_mm
            bottom_y = -top_y
            tab_outline = [
                [left_x, top_y],
                [right_x, top_y],
                [right_x, bottom_y],
                [left_x, bottom_y],
            ]
            if draw_hidden_part:  # close polygon
                tab_outline += tab_outline[:1]
            self.m.append(
                PolygonLine(
                    shape=tab_outline, layer="F.Fab", width=self.dim.fab_line_width_mm
                )
            )

    def draw_body(self):
        right_x = (
            self.dim.device_offset_x_mm
            - max(0, self.dim.tab_project_x_mm)
            + self.dim.device_shift_x_mm
            - self.dim.footprint_origin_x_mm
        )
        left_x = right_x - self.dim.body_x_mm
        top_y = -self.dim.body_offset_y_mm
        bottom_y = -top_y
        body_outline = [
            [right_x, top_y],
            [right_x, bottom_y],
            [left_x, bottom_y],
            [left_x, top_y + self.dim.corner_mm],
            [left_x + self.dim.corner_mm, top_y],
            [right_x, top_y],
        ]
        self.m.append(
            Polygon(
                shape=body_outline,
                layer="F.Fab",
                width=self.dim.fab_line_width_mm,
                fill=False,
            )
        )

    def draw_pins(self):
        right_x = (
            self.dim.device_offset_x_mm
            - max(0, self.dim.tab_project_x_mm)
            - self.dim.body_x_mm
            + self.dim.device_shift_x_mm
            - self.dim.footprint_origin_x_mm
        )
        left_x = right_x - self.variant["pin"]["x_mm"]
        pin_1_top_y = self.dim.pad_1_centre_y_mm - (self.variant["pin"]["y_mm"] / 2.0)
        body_corner_bottom_y = -self.dim.body_offset_y_mm + self.dim.corner_mm
        pin_1_extend = (
            (body_corner_bottom_y - pin_1_top_y)
            if (pin_1_top_y < body_corner_bottom_y)
            else 0.0
        )
        for pin in range(1, self.variant["pins"] + 1):
            if not (pin == self.dim.centre_pin and self.cut_pin):
                top_y = (
                    self.dim.pad_1_centre_y_mm
                    + ((pin - 1) * self.variant["pitch_mm"])
                    - (self.variant["pin"]["y_mm"] / 2.0)
                )
                bottom_y = (
                    self.dim.pad_1_centre_y_mm
                    + ((pin - 1) * self.variant["pitch_mm"])
                    + (self.variant["pin"]["y_mm"] / 2.0)
                )
                pin_outline = [
                    [right_x + (pin_1_extend if pin == 1 else 0), top_y],
                    [left_x, top_y],
                    [left_x, bottom_y],
                    [right_x, bottom_y],
                ]
                self.m.append(
                    PolygonLine(
                        shape=pin_outline,
                        layer="F.Fab",
                        width=self.dim.fab_line_width_mm,
                    )
                )

    def draw_outline(self, show_hidden_tab=False):
        self.draw_tab(draw_hidden_part=show_hidden_tab)
        self.draw_body()
        self.draw_pins()

    def draw_silk(self):

        other_magic_number = 1.5  #  TODO needs better name

        if self.dim.body_offset_y_mm < self.dim.tab_size_y_mm / 2:
            # The silk must end before the pad
            assert self.tab_pad is not None
            right_x = (
                self.tab_pad.at.x
                - self.tab_pad.size.x / 2
                - self.dim.silk_pad_clearance_mm
                - self.dim.silk_line_width_mm / 2
            )
        else:
            right_x = (
                self.dim.device_offset_x_mm
                - max(0, self.dim.tab_project_x_mm)
                + self.dim.device_shift_x_mm
                - self.dim.footprint_origin_x_mm
            )
        middle_x = (
            self.dim.device_offset_x_mm
            + self.dim.device_shift_x_mm
            - max(0, self.dim.tab_project_x_mm)
            - self.dim.body_x_mm
            - self.dim.silk_line_nudge_mm
            - self.dim.footprint_origin_x_mm
        )
        top_y = -self.dim.body_offset_y_mm - self.dim.silk_line_nudge_mm
        bottom_y = (
            self.dim.pad_1_centre_y_mm
            - self.variant["pad"]["y_mm"] / 2.0
            - other_magic_number * self.dim.silk_line_nudge_mm
        )
        top_marker = [
            [right_x, top_y],
            [middle_x, top_y],
            [middle_x, bottom_y],
        ]
        self.m.append(
            PolygonLine(
                shape=top_marker, layer="F.SilkS", width=self.dim.silk_line_width_mm
            )
        )

        # Top line
        top_y = -top_y
        bottom_y = -bottom_y
        bottom_marker = [
            [right_x, top_y],
            [middle_x, top_y],
            [middle_x, bottom_y],
        ]
        self.m.append(
            PolygonLine(
                shape=bottom_marker,
                layer="F.SilkS",
                width=self.dim.silk_line_width_mm,
            )
        )

        # Pin 1 (or first pin if pin 1 cut):
        assert self.first_pad is not None  # should have done this first
        self.m.append(
            draw_silk_triangle_for_pad(
                self.first_pad, SilkArrowSize.LARGE,
                Direction.SOUTH,
                self.dim.silk_line_width_mm,
                self.dim.silk_pad_clearance_mm
            )
        )

    def draw_pads(self):

        for pin in range(1, self.variant["pins"] + 1):
            if not (pin == self.dim.centre_pin and self.cut_pin):
                pad = Pad(
                    number=pin,
                    type=Pad.TYPE_SMT,
                    shape=Pad.SHAPE_ROUNDRECT,
                    at=[
                        self.dim.pad_1_centre_x_mm - self.dim.footprint_origin_x_mm,
                        self.dim.pad_1_centre_y_mm
                        + (pin - 1) * self.variant["pitch_mm"],
                    ],
                    size=[
                        self.variant["pad"]["x_mm"],
                        self.variant["pad"]["y_mm"]
                    ],
                    round_radius_handler=self.dim.roundrect_radius_handler,
                    layers=Pad.LAYERS_SMT
                )

                # Remember this pad so we can draw silk near it
                if self.first_pad is None:
                    self.first_pad = pad

                self.m.append(pad)

        tab_layers = Pad.LAYERS_SMT[:]
        if self.dim.split_paste:
            tab_layers.remove("F.Paste")
        paste_layers = ["F.Paste"]

        tab_pad = Pad(
            number=self.dim.tab_pin_number,
            type=Pad.TYPE_SMT,
            shape=Pad.SHAPE_ROUNDRECT,
            at=[
                self.dim.tab_centre_x_mm - self.dim.footprint_origin_x_mm,
                self.dim.tab_centre_y_mm,
            ],
            size=[
                self.base["footprint"]["tab"]["x_mm"],
                self.base["footprint"]["tab"]["y_mm"],
            ],
            round_radius_handler=self.dim.roundrect_radius_handler,
            layers=tab_layers,
        )
        self.m.append(tab_pad)
        self.tab_pad = tab_pad

        if self.dim.split_paste:
            gutter = self.base["footprint"]["paste_gutter_mm"]
            paste_x_mm = (self.base["footprint"]["tab"]["x_mm"] - gutter) / 2.0
            paste_y_mm = (self.base["footprint"]["tab"]["y_mm"] - gutter) / 2.0
            paste_offset_x = (paste_x_mm + gutter) / 2.0
            paste_offset_y = (paste_y_mm + gutter) / 2.0
            left_x = (
                self.dim.tab_centre_x_mm
                - paste_offset_x
                - self.dim.footprint_origin_x_mm
            )
            right_x = (
                self.dim.tab_centre_x_mm
                + paste_offset_x
                - self.dim.footprint_origin_x_mm
            )
            top_y = self.dim.tab_centre_y_mm - paste_offset_y
            bottom_y = self.dim.tab_centre_y_mm + paste_offset_y
            for pad_xy in [
                [right_x, bottom_y],
                [left_x, top_y],
                [right_x, top_y],
                [left_x, bottom_y],
            ]:
                self.m.append(
                    Pad(
                        number="",
                        type=Pad.TYPE_SMT,
                        shape=Pad.SHAPE_ROUNDRECT,
                        at=pad_xy,
                        size=[paste_x_mm, paste_y_mm],
                        round_radius_handler=self.dim.roundrect_radius_handler,
                        layers=paste_layers,
                    )
                )

    def add_3D_model(self):
        model_filename = (
            self.global_config.model_3d_prefix
            + self.base["libname"]
            + ".3dshapes/"
            + self.dim.name
            + self.global_config.model_3d_suffix
        )
        self.m.append(
            Model(
                filename=model_filename,
                at=[0, 0, 0],
                scale=[1, 1, 1],
                rotate=[0, 0, 0],
            )
        )

    def draw_courtyard(self):
        left = Dimensions.round_to(
            self.dim.courtyard_left_x_mm - self.dim.footprint_origin_x_mm,
            self.dim.courtyard_precision_mm,
            "-",
        )
        right = Dimensions.round_to(
            self.dim.courtyard_right_x_mm - self.dim.footprint_origin_x_mm,
            self.dim.courtyard_precision_mm,
            "+",
        )
        top = Dimensions.round_to(
            -self.dim.courtyard_offset_y_mm, self.dim.courtyard_precision_mm, "-"
        )
        bottom = Dimensions.round_to(
            self.dim.courtyard_offset_y_mm, self.dim.courtyard_precision_mm, "+"
        )
        self.m.append(
            Rectangle(
                start=[left, top],
                end=[right, bottom],
                layer="F.CrtYd",
                width=self.dim.courtyard_line_width_mm,
            )
        )

    def build_footprint(self, generator_name, verbose=False):
        self.add_properties()
        self.add_labels()

        # create pads
        self.draw_pads()

        # create fab outline
        self.draw_outline()

        # create silkscreen marks and pin 1 marker
        self.draw_silk()

        # create courtyard
        self.draw_courtyard()

        # add 3D model
        self.add_3D_model()

        # write file
        lib_name = self.base["libname"]
        write_footprint(self.m, lib_name, generator_name)


class DPAKSeries:

    def __init__(self):
        self.SERIES = None
        self.config = None

    def load_config(self, config_file):
        devices = yaml.safe_load_all(open(config_file))
        config = None
        for dev in devices:
            if dev["base"]["series"] == self.SERIES:
                config = dev
                break
        return config

    def build_series(self, generator_name: str, verbose: bool) -> int:
        base = self.config["base"]
        num_fps_generated = 0
        for variant in self.config["variants"]:

            if "uncut" in variant["centre_pin"]:
                dpak = DPAK(base, variant, cut_pin=False, tab_linked=False)
                dpak.build_footprint(generator_name, verbose=verbose)
                dpak = DPAK(base, variant, cut_pin=False, tab_linked=True)
                dpak.build_footprint(generator_name, verbose=verbose)
                num_fps_generated += 2
            if "cut" in variant["centre_pin"]:
                dpak = DPAK(base, variant, cut_pin=True, tab_linked=False)
                dpak.build_footprint(generator_name, verbose=verbose)
                num_fps_generated += 1
        return num_fps_generated


class TO252(DPAKSeries):

    def __init__(self, config_file):
        super().__init__()
        self.SERIES = "TO-252"
        self.config = self.load_config(config_file)


class TO263(DPAKSeries):

    def __init__(self, config_file):
        super().__init__()
        self.SERIES = "TO-263"
        self.config = self.load_config(config_file)


class TO268(DPAKSeries):

    def __init__(self, config_file):
        super().__init__()
        self.SERIES = "TO-268"
        self.config = self.load_config(config_file)


class ATPAK(DPAKSeries):

    def __init__(self, config_file):
        super().__init__()
        self.SERIES = "ATPAK"
        self.config = self.load_config(config_file)


class Texas_NDW(DPAKSeries):

    def __init__(self, config_file):
        super().__init__()
        self.SERIES = "Texas_NDW"
        self.config = self.load_config(config_file)
