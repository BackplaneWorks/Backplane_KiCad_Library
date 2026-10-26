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

from typing import Any

from KicadModTree import (
    Footprint,
    FootprintType,
)

from ...package_spec import PackageSpec
from generators.tools.spec.spec_generator import get_spec_dicts

class CommonToSpec(PackageSpec):
    """Class for properties common to both types of TO packages"""

    def __init__(
        self,
        id: str = "",
        spec: dict[str, Any] = {},
        file_name: str = "",
    ) -> None:
        """Create an instance of `CommonToSpec`.

        Args:
            id: The name/identifier of the spec. Typically, this is the name of the key
                of the spec (in the YAML file) or the name of the component.
            spec: The dictionary containing the specification of the component.
            file_name: The name of the YAML file that holds this spec definition.
        """
        super().__init__(id, spec, file_name)

        try:
            self.pins: int = spec["number_of_pins"]
            self.pad_dimensions: list[float] = spec["pad_dimensions_xy"]
            self.drill: float = spec["pad_hole_diameter"]
        except KeyError as e:
            msg = f"Error in '{id}': Parameter '{e.args[0]}' must be provided!"
            print("\n" + msg + "\n")
            raise KeyError(msg)

        self.name_base: str = ""
        self.fpnametags = []
        self.additional_package_names: list[str] = spec.get(
            "additional_package_names", []
        )
        self.device_type = spec.get("device_type", "")

        if "device_type" in spec:
            self.name_base = spec["device_type"] + "-" + f"{self.pins}"
        else:
            self.name_base = id
        self.has_fp_data = True

    def init_footprint(self, description: str, tags: list[str], name: str):
        fp = Footprint(name, FootprintType.THT)
        fp.description = description
        fp.tags = tags
        return fp


class RectangularToSpec(CommonToSpec):
    """Class for properties of rectangular shaped TO packages"""

    def __init__(
        self,
        id: str = "",
        spec: dict[str, Any] = {},
        file_name: str = "",
    ) -> None:
        """Create an instance of `RectangularToSpec`.

        Args:
            id: The name/identifier of the spec. Typically, this is the name of the key
                of the spec (in the YAML file) or the name of the component.
            spec: The dictionary containing the specification of the component.
            file_name: The name of the YAML file that holds this spec definition.
        """
        super().__init__(id, spec, file_name)
        try:
            self.plastic_dimensions: list[float] = spec["plastic_dimensions_xyz"]  # fmt: skip
            self.pitch: float = spec["pitch"]
        except KeyError as e:
            msg = f"Error in '{id}': Parameter '{e.args[0]}' must be provided!"
            print("\n" + msg + "\n")
            raise KeyError(msg)

        self.metal_dimensions: list[float] = spec.get(
            "metal_dimensions_xyz", [0, 0, 0]
        )
        self.metal_offset_x: float = spec.get(
            "metal_offset_x", 0
        )  # offset of metal from left
        self.mounting_hole_position: list[int] = spec.get(
            "mounting_hole_position", [0, 0]
        )
        self.mounting_hole_diameter: float = spec.get(
            "mounting_hole_diameter_on_package", 0
        )
        self.mounting_hole_drill: float = spec.get(
            "mounting_hole_diameter_on_pcb", 0
        )
        self.pin_min_length_before_90deg_bend: float = spec.get(
            "pin_min_length_before_90deg_bend", 0
        )
        self.pin_width_height: list[float] = spec.get(
            "pin_width_height", [0, 0]
        )
        self.pin_offset_x: float = 0
        self.pin_offset_z: float = spec.get("pin_offset_z", 0)
        self.additional_pin_pad_size: list[float] = spec.get(
            "additional_pin_pad_size", []
        )
        self.plastic_angled: list[float] = spec.get("plastic_angled", [])
        self.metal_angled: list[float] = spec.get("metal_angled", [])

        self.generate_footprint_type: int = spec.get("generate_footprint_type")
        self.staggered_pitch: list[float] = spec.get("staggered_pitch")
        self.pitch_list: list[float] = spec.get("pitch_list", [])

        if self.pitch_list:
            self.pin_spread = sum(self.pitch_list)
        else:
            self.pin_spread = (self.pins - 1) * self.pitch
        self.pin_offset_x = (self.plastic_dimensions[0] - self.pin_spread) / 2

        # If pads are too wide, make them narrower for non-staggered devices
        if "staggered_pitch" not in spec:
            self.pad_dimensions[0] = min(self.pad_dimensions[0], 0.75 * self.pitch)

    def init_footprint(
        self, orientation: str, modifier: str, staggered_type: int, config: dict, generator_name: str
    ):
        description, tags, name = self._get_descr_tags_fpname(
            orientation, modifier, staggered_type, config, generator_name
        )
        return super().init_footprint(description, tags, name)

    def _get_descr_tags_fpname(
        self, orientation: str, modifier: str, staggered_type: int, config: dict, generator_name: str
    ):
        # Tags
        tags = [
            self.name_base,
            orientation,
            f"RM {self.pitch}mm",
        ] + self.metadata.additional_tags
        fpnametags = self.fpnametags
        if staggered_type == 1:
            tags.append("staggered type-1")
            fpnametags = ["StaggeredType1"] + fpnametags
        elif staggered_type == 2:
            tags.append("staggered type-2")
            fpnametags = ["StaggeredType2"] + fpnametags

        # Description
        description = self.name_base
        for tag in tags[1:]:
            description += ", " + tag
        if self.metadata.datasheet:
            description += ", see " + self.metadata.datasheet

        # Footprint name
        if staggered_type > 0:
            name_format = config[
                "fp_name_to_tht_staggered_format_string_no_trailing_zero"
            ]
            if orientation == "Vertical":
                pitch_y = self.staggered_pitch[0]
                lead = pitch_y - self.plastic_dimensions[2] + self.pin_offset_z
            else:
                pitch_y = self.staggered_pitch[1]
                lead = pitch_y + self.pin_min_length_before_90deg_bend
            footprint_name = (
                name_format.format(
                    man=self.metadata.manufacturer or "",
                    mpn=self.metadata.part_number or "",
                    pkg=self.device_type,
                    pincount=self.pins,
                    pitch_x=2 * self.pitch,
                    pitch_y=pitch_y,
                    parity="Odd" if staggered_type == 1 else "Even",
                    lead=lead,
                    orientation=orientation if orientation == "Vertical" else modifier,
                )
                .replace("__", "_")
                .lstrip("_")
            )
        else:
            footprint_name = self.name_base
            if orientation == "Horizontal" and self.additional_pin_pad_size:
                footprint_name += "-1EP"
            for t in self.additional_package_names:
                footprint_name += "_" + t
            footprint_name += "_" + orientation
            if modifier:
                footprint_name += "_" + modifier
            for t in fpnametags:
                footprint_name += "_" + t
        return description, tags, footprint_name


class RoundToSpec(CommonToSpec):
    """Class for properties of round shaped TO packages"""

    def __init__(
        self,
        id: str = "",
        spec: dict[str, Any] = {},
        file_name: str = "",
    ) -> None:
        """Create an instance of `RoundToSpec`.

        Args:
            id: The name/identifier of the spec. Typically, this is the name of the key
                of the spec (in the YAML file) or the name of the component.
            spec: The dictionary containing the specification of the component.
            file_name: The name of the YAML file that holds this spec definition.
        """
        super().__init__(id, spec, file_name)
        try:
            self.pin_circle_diameter: float = spec["pin_circle_diameter"]
            self.diameter_inner: float = spec[
                "diameter_inner"
            ]  # diameter of top can
            self.diameter_outer: float = spec[
                "diameter_outer"
            ]  # diameter of bottom can
        except KeyError as e:
            msg = f"Error in '{id}': Parameter '{e.args[0]}' must be provided!"
            print("\n" + msg + "\n")
            raise KeyError(msg)

        self.mark_width: float = spec.get("mark_width", 0)
        self.mark_length: float = spec.get("mark_length", 0)
        self.pin1_angle: float = spec.get("pin1_angle", 180)
        self.angle_between_pins: float = spec.get(
            "angle_between_pins", -90 if self.pins == 3 else -360 / self.pins
        )
        self.mark_angle: float = spec.get("mark_angle", self.pin1_angle + 45)
        self.window_diameter: float = spec.get("window_diameter", 0)
        self.deleted_pins: list[int] = spec.get("deleted_pins", [])

    def init_footprint(self, footprint_type: str, generator_name: str):
        description, tags, name = self._get_descr_tags_fpname(footprint_type, generator_name)
        return super().init_footprint(description, tags, name)

    def _get_descr_tags_fpname(self, footprint_type: str, generator_name: str):
        # Tags
        name = self.name_base
        tags = []
        if footprint_type == "window" or footprint_type == "lens":
            name += "_" + footprint_type.capitalize()
            tags.append(footprint_type.capitalize())

        # Footprint name
        for t in self.additional_package_names:
            name += "_" + t
        for t in self.fpnametags:
            name += "_" + t

        # Description
        tags = [self.name_base] + tags + self.metadata.additional_tags
        description = self.name_base
        for t in tags[1:]:
            description += ", " + t
        if self.metadata.datasheet:
            description += ", see " + self.metadata.datasheet

        return description, tags, name


def create_specs(file_name: str, generator_name: str) -> list[CommonToSpec]:
    """Create specs for the TO packages.

    Args:
        file_name: The name of the specs file to create the specs from.
        generator_name: The name of this generator.

    Returns:
        A list containing the specs of all the TO packages.
    """
    specs: list[Any] = []
    for file_name, yaml_content in get_spec_dicts(None, file_name):
        for id, spec in yaml_content.items():
            if "plastic_dimensions_xyz" in spec:
                specs.append(RectangularToSpec(id, spec, file_name))
            elif  "diameter_inner" in spec:
                specs.append(RoundToSpec(id, spec, file_name))
    return specs
