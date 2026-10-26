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


import copy
import yaml
import os

from pathlib import Path

from kilibs.config import ipc_rules
from kilibs.util.toleranced_size import TolerancedSize
from KicadModTree import *  # NOQA
from KicadModTree.nodes.base.Pad import Pad  # NOQA
from generators.tools.footprint.drawing_tools import (
    nearestSilkPointOnOrthogonalLineSmallClerance,
    round_to_grid_up,
)
from generators.tools.footprint.footprint_text_fields import addTextFields
from kilibs.config import global_config as GC
from generators.tools.footprint.ipc_pad_size_calculators import ipc_body_edge_inside
from generators.tools.footprint.save_footprint import write_footprint

from generators.tools.spec.base_spec import BaseSpec
from generators.tools.spec.spec_generator import get_spec_file_names
from generators.tools.cli_args import CLI_ARGS
from kilibs.config.global_config import GLOBAL_CONFIG


def merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


class TwoTerminalSMD:

    def __init__(
        self,
        global_config: GC.GlobalConfig,
        ipc_defs: ipc_rules.IpcRules,
        command_file,
        configuration,
    ):
        self.global_config = global_config
        self.configuration = configuration
        with open(command_file, "r") as command_stream:
            self.footprint_group_definitions = yaml.safe_load(command_stream)

        self.ipc_definitions = ipc_defs

    def calcPadDetails(
        self,
        device_dimensions,
        ipc_offsets: ipc_rules.Offsets,
        ipc_round_base: ipc_rules.Offsets,
        footprint_group_data,
    ):
        # Zmax = Lmin + 2JT + √(CL^2 + F^2 + P^2)
        # Gmin = Smax − 2JH − √(CS^2 + F^2 + P^2)
        # Xmax = Wmin + 2JS + √(CW^2 + F^2 + P^2)

        # Some manufacturers do not list the terminal spacing (S) in their datasheet but list the terminal length (T)
        # Then one can calculate
        # Stol(RMS) = √(Ltol^2 + 2*^2)
        # Smin = Lmin - 2*Tmax
        # Smax(RMS) = Smin + Stol(RMS)

        manf_tol = ipc_rules.ManufacturingTolerance(
            manufacturing_tolerance=self.configuration.get(
                "manufacturing_tolerance", 0.1
            ),
            placement_tolerance=self.configuration.get("placement_tolerance", 0.05),
        )

        if "terminal_width" in device_dimensions:
            lead_width = device_dimensions["terminal_width"]
        else:
            lead_width = device_dimensions["body_width"]

        Gmin, Zmax, Xmax = ipc_body_edge_inside(
            ipc_offsets,
            ipc_round_base,
            manf_tol,
            device_dimensions["body_length"],
            lead_width,
            lead_len=device_dimensions.get("terminal_length"),
            lead_inside=device_dimensions.get("terminator_spacing"),
        )

        Zmax += footprint_group_data.get("pad_length_addition", 0)
        Pad = {"at": [-(Zmax + Gmin) / 4, 0], "size": [(Zmax - Gmin) / 2, Xmax]}
        Paste = None

        if "paste_pad" in footprint_group_data:
            rel_reduction_factor = footprint_group_data["paste_pad"].get(
                "all_sides_rel", 0.9
            )
            x_abs_reduction = (1 - rel_reduction_factor) * Pad["size"][0]
            Zmax -= 2 * x_abs_reduction
            Gmin += 2 * x_abs_reduction - 2 * footprint_group_data["paste_pad"].get(
                "heel_abs", 0
            )
            Xmax *= rel_reduction_factor
            Paste = {"at": [-(Zmax + Gmin) / 4, 0], "size": [(Zmax - Gmin) / 2, Xmax]}

        return Pad, Paste

    @staticmethod
    def deviceDimensions(device_size_data):
        dimensions = {
            "body_length": TolerancedSize.from_yaml(
                device_size_data, base_name="body_length"
            ),
            "body_width": TolerancedSize.from_yaml(
                device_size_data, base_name="body_width"
            ),
        }
        if (
            "terminator_spacing_max" in device_size_data
            and "terminator_spacing_min" in device_size_data
            or "terminator_spacing" in device_size_data
        ):
            dimensions["terminator_spacing"] = TolerancedSize.from_yaml(
                device_size_data, base_name="terminator_spacing"
            )
        elif (
            "terminal_length_max" in device_size_data
            and "terminal_length_min" in device_size_data
            or "terminal_length" in device_size_data
        ):
            dimensions["terminal_length"] = TolerancedSize.from_yaml(
                device_size_data, base_name="terminal_length"
            )
        else:
            raise KeyError(
                "Either terminator spacing or terminal length must be included in the size definition."
            )

        if (
            "terminal_width_min" in device_size_data
            and "terminal_width_max" in device_size_data
            or "terminal_width" in device_size_data
        ):
            dimensions["terminal_width"] = TolerancedSize.from_yaml(
                device_size_data, base_name="terminal_width"
            )

        return dimensions

    def generateFootprints(self, generator_name, size_definition_path) -> int:
        num_fps_generated = 0
        
        for group_name in self.footprint_group_definitions:
            footprint_group_data = self.footprint_group_definitions[group_name]

            device_size_docs = footprint_group_data["size_definitions"]
            package_size_defintions = {}
            
            for device_size_doc in device_size_docs:
                with open(size_definition_path / device_size_doc, "r") as size_stream:
                    package_size_defintions.update(yaml.safe_load(size_stream))

            for size_name in package_size_defintions:
                device_size_data = package_size_defintions[size_name]
                self.generateFootprint(device_size_data, footprint_group_data, generator_name)
                num_fps_generated += 1
        return num_fps_generated

    def generateFootprint(self, device_size_data, footprint_group_data, generator_name):
        device_dimensions = TwoTerminalSMD.deviceDimensions(device_size_data)

        if "ipc_reference" in device_size_data:
            ipc_reference = device_size_data["ipc_reference"]
        else:
            ipc_reference = footprint_group_data["ipc_reference"]
        ipc_density = self.configuration.get("ipc_density")[0]
        density_suffix = self.configuration.get("ipc_density")[1]

        used_density = ipc_rules.IpcDensity(self.configuration.get('ipc_density', ipc_density)[0])
        ipc_offsets = self.ipc_definitions.get_class(ipc_reference).get_offsets(used_density)
        ipc_round_base = self.ipc_definitions.get_class(ipc_reference).roundoff

        if "ipc_string" in device_size_data:
            ipc_string = device_size_data["ipc_string"]
        elif "ipc_string" in footprint_group_data:
            ipc_string = footprint_group_data["ipc_string"]
        else:
            ipc_string = "IPC-7351"

        pad_details, paste_details = self.calcPadDetails(
            device_dimensions, ipc_offsets, ipc_round_base, footprint_group_data
        )

        suffix = footprint_group_data.get("suffix", "").format(
            pad_x=pad_details["size"][0], pad_y=pad_details["size"][1]
        )
        prefix = footprint_group_data["prefix"]

        model3d_path_prefix = self.configuration.get(
            "3d_model_prefix", self.global_config.model_3d_prefix
        )
        model3d_path_suffix = self.configuration.get(
            "3d_model_suffix", self.global_config.model_3d_suffix
        )
        suffix_3d = (
            suffix
            if footprint_group_data.get("include_suffix_in_3dpath", "True") == "True"
            else ""
        )

        if (
            density_suffix != ""
            and "handsolder" not in footprint_group_data["keywords"]
        ):
            density_description = f", {ipc_string} {ipc_density}"
            suffix = suffix + density_suffix
            suffix_3d = suffix_3d + density_suffix
        else:
            density_description = f", {ipc_string} nominal"

        code_metric = device_size_data.get("code_metric")
        code_letter = device_size_data.get("code_letter")
        code_imperial = device_size_data.get("code_imperial")

        if "code_letter" in device_size_data:
            name_format = self.configuration["fp_name_tantal_format_string"]
        else:
            if "code_metric" in device_size_data:
                name_format = self.configuration["fp_name_format_string"]
            else:
                name_format = self.configuration["fp_name_non_metric_format_string"]

        if "custom_name" in device_size_data:
            fp_name = device_size_data["custom_name"]
            fp_name_2 = device_size_data["custom_name"]
        else:
            fp_name = name_format.format(
                prefix=prefix,
                code_imperial=code_imperial,
                code_metric=code_metric,
                code_letter=code_letter,
                suffix=suffix,
            )
            fp_name_2 = name_format.format(
                prefix=prefix,
                code_imperial=code_imperial,
                code_letter=code_letter,
                code_metric=code_metric,
                suffix=suffix_3d,
            )

        model_name = f"{model3d_path_prefix}{footprint_group_data['fp_lib_name']}.3dshapes/{fp_name_2}{model3d_path_suffix}"

        kicad_mod = Footprint(fp_name, FootprintType.SMD)

        # init kicad footprint
        if "custom_name" in device_size_data:
            kicad_mod.setDescription(device_size_data["description"])
        else:
            kicad_mod.setDescription(
                footprint_group_data["description"].format(
                    code_imperial=code_imperial,
                    code_metric=code_metric,
                    code_letter=code_letter,
                    density=density_description,
                    size_info=device_size_data.get("size_info"),
                )
            )
        kicad_mod.setTags(footprint_group_data["keywords"])

        pad_shape_details = {}
        pad_shape_details["shape"] = Pad.SHAPE_ROUNDRECT
        pad_shape_details["round_radius_handler"] = (
            self.global_config.roundrect_radius_handler
        )

        if paste_details is not None:
            layers_main = ["F.Cu", "F.Mask"]

            kicad_mod.append(
                Pad(
                    number="",
                    type=Pad.TYPE_SMT,
                    layers=["F.Paste"],
                    **merge_dicts(paste_details, pad_shape_details),
                )
            )
            paste_details["at"][0] *= -1
            kicad_mod.append(
                Pad(
                    number="",
                    type=Pad.TYPE_SMT,
                    layers=["F.Paste"],
                    **merge_dicts(paste_details, pad_shape_details),
                )
            )
        else:
            layers_main = Pad.LAYERS_SMT

        P1 = Pad(
            number=1,
            type=Pad.TYPE_SMT,
            layers=layers_main,
            **merge_dicts(pad_details, pad_shape_details),
        )
        pad_radius = P1.get_round_radius()

        kicad_mod.append(P1)
        pad_details["at"][0] *= -1
        kicad_mod.append(
            Pad(
                number=2,
                type=Pad.TYPE_SMT,
                layers=layers_main,
                **merge_dicts(pad_details, pad_shape_details),
            )
        )

        fab_outline = self.configuration.get("fab_outline", "typical")
        if fab_outline == "max":
            outline_size = [
                device_dimensions["body_length"].maximum,
                device_dimensions["body_width"].maximum,
            ]
        elif fab_outline == "min":
            outline_size = [
                device_dimensions["body_length"].minimum,
                device_dimensions["body_width"].minimum,
            ]
        else:
            outline_size = [
                device_dimensions["body_length"].nominal,
                device_dimensions["body_width"].nominal,
            ]

        if footprint_group_data.get("polarization_mark", "False") == "True":
            polararity_marker_size = self.configuration.get("fab_polarity_factor", 0.25)
            polararity_marker_size *= (
                outline_size[1]
                if outline_size[1] < outline_size[0]
                else outline_size[0]
            )

            polarity_marker_thick_line = False

            polarity_max_size = self.configuration.get("fab_polarity_max_size", 1)
            if polararity_marker_size > polarity_max_size:
                polararity_marker_size = polarity_max_size
            polarity_min_size = self.configuration.get("fab_polarity_min_size", 0.25)
            if polararity_marker_size < polarity_min_size:
                if polararity_marker_size < polarity_min_size * 0.6:
                    polarity_marker_thick_line = True
                polararity_marker_size = polarity_min_size

            silk_x_left = (
                -abs(pad_details["at"][0])
                - pad_details["size"][0] / 2
                - self.global_config.silk_pad_offset
            )

            silk_y_bottom = max(
                self.global_config.silk_pad_offset + pad_details["size"][1] / 2,
                outline_size[1] / 2 + self.global_config.silk_fab_offset,
            )

            if polarity_marker_thick_line:
                kicad_mod.append(
                    Rectangle(
                        start=[-outline_size[0] / 2, outline_size[1] / 2],
                        end=[outline_size[0] / 2, -outline_size[1] / 2],
                        layer="F.Fab",
                        width=self.global_config.fab_line_width,
                    )
                )
                x = -outline_size[0] / 2 + self.global_config.fab_line_width
                kicad_mod.append(
                    Line(
                        start=[x, outline_size[1] / 2],
                        end=[x, -outline_size[1] / 2],
                        layer="F.Fab",
                        width=self.global_config.fab_line_width,
                    )
                )
                x += self.global_config.fab_line_width
                if x < -self.global_config.fab_line_width / 2:
                    kicad_mod.append(
                        Line(
                            start=[x, outline_size[1] / 2],
                            end=[x, -outline_size[1] / 2],
                            layer="F.Fab",
                            width=self.global_config.fab_line_width,
                        )
                    )

                kicad_mod.append(
                    Circle(
                        center=[silk_x_left - 0.05, 0],
                        radius=0.05,
                        layer="F.SilkS",
                        width=0.1,
                    )
                )
            else:
                poly_fab = [
                    {"x": outline_size[0] / 2, "y": -outline_size[1] / 2},
                    {
                        "x": polararity_marker_size - outline_size[0] / 2,
                        "y": -outline_size[1] / 2,
                    },
                    {
                        "x": -outline_size[0] / 2,
                        "y": polararity_marker_size - outline_size[1] / 2,
                    },
                    {"x": -outline_size[0] / 2, "y": outline_size[1] / 2},
                    {"x": outline_size[0] / 2, "y": outline_size[1] / 2},
                    {"x": outline_size[0] / 2, "y": -outline_size[1] / 2},
                ]
                kicad_mod.append(
                    PolygonLine(
                        shape=poly_fab,
                        layer="F.Fab",
                        width=self.global_config.fab_line_width,
                    )
                )

                poly_silk = [
                    {"x": outline_size[0] / 2, "y": -silk_y_bottom},
                    {"x": silk_x_left, "y": -silk_y_bottom},
                    {"x": silk_x_left, "y": silk_y_bottom},
                    {"x": outline_size[0] / 2, "y": silk_y_bottom},
                ]
                kicad_mod.append(
                    PolygonLine(
                        shape=poly_silk,
                        layer="F.SilkS",
                        width=self.global_config.silk_line_width,
                    )
                )
        else:
            kicad_mod.append(
                Rectangle(
                    start=[-outline_size[0] / 2, outline_size[1] / 2],
                    end=[outline_size[0] / 2, -outline_size[1] / 2],
                    layer="F.Fab",
                    width=self.global_config.fab_line_width,
                )
            )

            silk_outline_y = outline_size[1] / 2 + self.global_config.silk_fab_offset
            default_clearance = self.global_config.silk_pad_clearance
            silk_point_top_right = nearestSilkPointOnOrthogonalLineSmallClerance(
                pad_size=pad_details["size"],
                pad_position=pad_details["at"],
                pad_radius=pad_radius,
                fixed_point=Vector2D(0, silk_outline_y),
                moving_point=Vector2D(outline_size[0] / 2, silk_outline_y),
                silk_pad_offset_default=(
                    self.global_config.silk_line_width / 2 + default_clearance
                ),
                silk_pad_offset_reduced=(
                    self.global_config.silk_line_width / 2
                    + self.configuration.get(
                        "silk_clearance_small_parts", default_clearance
                    )
                ),
                min_length=self.configuration.get("silk_line_length_min", 0) / 2,
            )

            if silk_point_top_right:
                kicad_mod.append(
                    Line(
                        start=[-silk_point_top_right.x, -silk_point_top_right.y],
                        end=[silk_point_top_right.x, -silk_point_top_right.y],
                        layer="F.SilkS",
                        width=self.global_config.silk_line_width,
                    )
                )
                kicad_mod.append(
                    Line(
                        start=[-silk_point_top_right.x, silk_point_top_right.y],
                        end=silk_point_top_right,
                        layer="F.SilkS",
                        width=self.global_config.silk_line_width,
                    )
                )

        CrtYd_rect = [None, None]
        # Half width of the courtyard
        CrtYd_rect[0] = round_to_grid_up(
            abs(pad_details["at"][0])
            + pad_details["size"][0] / 2
            + ipc_offsets.courtyard,
            self.global_config.courtyard_grid,
            1e-7,
        )
        # Half height of the courtyard
        CrtYd_rect[1] = round_to_grid_up(
            max(pad_details["size"][1], outline_size[1]) / 2
            + ipc_offsets.courtyard,
            self.global_config.courtyard_grid,
            1e-7,
        )
        kicad_mod.append(
            Rectangle(
                start=[-CrtYd_rect[0], CrtYd_rect[1]],
                end=[CrtYd_rect[0], -CrtYd_rect[1]],
                layer="F.CrtYd",
                width=self.global_config.courtyard_line_width,
            )
        )

        ######################### Text Fields ###############################

        addTextFields(
            kicad_mod=kicad_mod,
            configuration=self.configuration,
            body_edges={
                "left": -outline_size[0] / 2,
                "right": outline_size[0] / 2,
                "top": -outline_size[1] / 2,
                "bottom": outline_size[1] / 2,
            },
            courtyard={"top": -CrtYd_rect[1], "bottom": CrtYd_rect[1]},
            fp_name=fp_name,
            text_y_inside_position="center",
        )

        kicad_mod.append(Model(filename=model_name))
        write_footprint(kicad_mod, footprint_group_data["fp_lib_name"], generator_name)


def create_footprints(spec: BaseSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification (not used by this generator).
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
    series_config = copy.deepcopy(GLOBAL_CONFIG.raw_data)

    series_config_path = os.path.expandvars(str(CLI_ARGS.smd_2_terminal_config))
    with open(series_config_path, "r") as config_stream:
        series_config.update(yaml.safe_load(config_stream))

    ipc_defs = ipc_rules.IpcRules.from_file(CLI_ARGS.smd_2_terminal_ipc_rules)

    ipc_density = CLI_ARGS.ipc_density
    postfix = "_" + ipc_density.upper()[0] if ipc_density.upper()[0] != "N" else ""
    series_config["ipc_density"] = [ipc_density, postfix]

    part_definitions_path = Path(__file__).parent / "part_definitions.yaml"
    size_definitions_path = Path(get_spec_file_names(generator_name)[0]).parent
    two_terminal_smd = TwoTerminalSMD(
        GLOBAL_CONFIG, ipc_defs, part_definitions_path, series_config
    )
    return two_terminal_smd.generateFootprints(generator_name, size_definitions_path)
