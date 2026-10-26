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

from __future__ import annotations

from typing import Any

from kilibs.util.toleranced_size import TolerancedSize

from generators.tools.spec.spec_registry import register_spec
from ..package_spec import PackageSpec


@register_spec
class PlccSpec(PackageSpec):
    """
    A type that represents the configuration of a PLCC footprint
    (probably from a YAML config block).

    Over time, add more type-safe accessors to this class, and replace
    use of the raw dictionary.
    """
    def __init__(
        self,
        id: str = "",
        spec: dict[str, Any] = {},
        file_name: str = "",
    ) -> None:
        """Create an instance of `PlccSpec`.

        Args:
            id: The name/identifier of the spec. This is the name of the key of the spec
                (in the YAML file).
            spec: The dictionary containing the specification of the component.
            file_name: The name of the YAML file that holds this spec definition.
        """
        super().__init__(id, spec, file_name)

        self.device_type = str(spec["device_type"])

        self.num_pins_x = int(spec["num_pins_x"])
        self.num_pins_y = int(spec["num_pins_y"])
        self.pitch = float(spec["pitch"])

        unit = spec.get("units", "mm")

        self.lead_width = TolerancedSize.from_yaml(spec, base_name='lead_width', unit=unit)

        self.pad_length_addition = float(spec.get("pad_length_addition", 0))

        self.overall_x = TolerancedSize.from_yaml(spec, base_name='overall_size_x', unit=unit)
        self.overall_y = TolerancedSize.from_yaml(spec, base_name='overall_size_y', unit=unit)

        self.body_x = TolerancedSize.from_yaml(spec, base_name='body_size_x', unit=unit)
        self.body_y = TolerancedSize.from_yaml(spec, base_name='body_size_y', unit=unit)

        self.lead_inside_x = None
        self.lead_inside_y = None
        self.lead_center_distance_x = None
        self.lead_center_distance_y = None
        self.lead_length = None

        if "lead_inside_x" in spec:
            self.lead_inside_x = TolerancedSize.from_yaml(spec, base_name='lead_inside_x', unit=unit)
            self.lead_inside_y = TolerancedSize.from_yaml(spec, base_name='lead_inside_y', unit=unit)
        elif "lead_center_distance_x" in spec:
            self.lead_center_distance_x = TolerancedSize.from_yaml(spec, base_name='lead_center_distance_x', unit=unit)
            self.lead_center_distance_y = TolerancedSize.from_yaml(spec, base_name='lead_center_distance_y', unit=unit)
        else:
            self.lead_length = TolerancedSize.from_yaml(spec, base_name="lead_len", unit=unit)

        self.body_chamfer = float(spec["body_chamfer"])

        self.suffix = spec.get("suffix", None)
        self.include_suffix_in_3dpath = spec.get("include_suffix_in_3dpath", True)
        self.has_fp_data = True
