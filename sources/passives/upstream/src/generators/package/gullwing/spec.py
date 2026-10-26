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

from typing import Any, Literal, cast

from kilibs.config import ipc_rules
from kilibs.util.toleranced_size import TolerancedSize
from generators.tools.footprint.declarative_def_tools import (
    common_metadata,
    fp_additional_drawing,
    pad_overrides,
    rule_area_properties,
)
from generators.tools.spec.spec_registry import register_spec

from ..package_spec import PackageSpec
from ..config import PACKAGE_CONFIG


class TopSlugConfiguration:
    """
    A type that represents the configuration of a "top slug"
    (top heat sink pad), probably from a YAML config block.
    """

    shape: str
    x: TolerancedSize
    y: TolerancedSize
    # Optional tail_x for rectangular slugs with vertical "tails" to the
    # package edge.
    tail_x: TolerancedSize | None

    def __init__(self, spec: dict[str, Any]) -> None:

        self.shape = spec["shape"]

        if self.shape not in ["rectangle", "cruciform"]:
            raise ValueError(f"Unsupported top slug shape: {self.shape}")

        self.x = TolerancedSize.from_yaml(spec, base_name="x")
        self.y = TolerancedSize.from_yaml(spec, base_name="y")

        self.tail_x = None

        if self.shape == "cruciform":
            self.tail_x = TolerancedSize.from_yaml(spec, base_name="tail_x")

    def get_name_suffix(self) -> str:

        # See https://github.com/KiCad/kicad-footprints/issues/955 for discussion
        s = "TopEP"

        if self.shape == "rectangle" or self.shape == "cruciform":
            s += f"{self.x.nominal:.2f}x{self.y.nominal:.2f}mm"
        else:
            raise ValueError(f"Unsupported top slug shape: {self.shape}")

        return s


@register_spec
class GullwingSpec(PackageSpec):
    """
    A type that represents the configuration of a gullwing footprint
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
        """Create an instance of `GullwingSpec`.

        Args:
            id: The name/identifier of the spec. This is the name of the key of the spec
                (in the YAML file).
            spec: The dictionary containing the specification of the component.
            file_name: The name of the YAML file that holds this spec definition.
        """
        # Instance attributes for generator independent data:
        self.top_slug: TopSlugConfiguration | None
        """The optional top slug configuration."""
        self.additional_drawings: list[fp_additional_drawing.FPAdditionalDrawing]
        """The list containing additional drawings."""
        self.pad_overrides: pad_overrides.PadOverrides
        """Definitions to overwrite properties of some pads"""
        self.rule_areas: list[rule_area_properties.RuleAreaProperties] = []
        """The rule areas (zones)."""

        # Instance attributes for general data:
        self.device_type: str
        """The device type."""
        self.lead_type: Literal["gullwing", "flat_lead"]
        """The lead type."""
        self.force_small_pitch_ipc_definition: bool
        """Whether the small pitch IPC definition shall be applied to this device."""
        self.ipc_density: ipc_rules.IpcDensity
        """The IPC density rules."""

        # Instance attributes for dimensions:
        self.body_size_x: TolerancedSize
        """The body size in x direction."""
        self.body_size_y: TolerancedSize
        """The body size in y direction."""
        self.lead_width: TolerancedSize
        """The lead width."""
        self.lead_len: TolerancedSize | None
        """The lead length."""
        self.has_ep: bool
        """Whether the device has an exposed pad"""
        self.ep_size_x: TolerancedSize
        """The size of the exposed pad in x direction."""
        self.ep_size_y: TolerancedSize
        """The size of the exposed pad in y direction."""
        self.ep_mask_x: TolerancedSize
        """The size of the mask of the exposed pad in x direction."""
        self.ep_mask_y: TolerancedSize
        """The size of the mask of the exposed pad in y direction."""
        self.heel_reduction: float
        """The heel reduction."""
        self.overall_size_x: TolerancedSize
        """The overall size of the package (incl. pins) in x direction."""
        self.overall_size_y: TolerancedSize
        """The overall size of the package (incl. pins) in y direction."""

        # Instance attributes related to the pinning:
        self.pitch: float
        """The pitch."""
        self.num_pins_x: int
        """Number of pins of the package in x direction."""
        self.num_pins_y: int
        """Number of pins of the package in y direction."""
        self.pincount_full: int
        """The full pin count (also counting deleted and hidden pins, but not EPs)."""
        self.pincount_real: int
        """The real pin count (not counting deleted or hidden pins or EPs)."""
        self.deleted_pins: list[int]
        """The list of deleted pins."""
        self.hidden_pins: list[int]
        """The list of hidden pins."""

        # Instance attributes related to the 3D data:
        self.has_3d_data: bool
        """True if the gullwing configuration has a full data set for the 3D model."""
        self.marker: Literal["circle", "bar"]
        """The kind of pin-1 marker that is used."""
        self.lead_top_flat_part_length: float | None
        """The optional length of the top flat part of a pin."""
        self.lead_height: float
        """The height of a lead."""
        self.lead_radius_top: float
        """The radius of the top pin bending."""
        self.lead_radius_bottom: float
        """The radius of the bottom pin bending."""
        self.lead_angle: float | None
        """The angle of the lead's inclined part"""
        self.body_fillet: float
        """The dimension of the optional fillet of the body's edges."""
        self.body_size_top_delta: float
        """The top part of the body is that much smaller than the bottom part."""
        self.corners_chamfer: float
        """The size of the chamfer of the corners."""
        self.body_angle: float
        """The angle of the body."""
        self.body_pcb_gap: float
        """The maximum gap between the PCB and the component body."""
        self.body_height: float
        """The maximum body height."""
        self.overall_height: float
        """The maximum overall height."""

        # Instance attributes related to the names:
        self.fp_name_without_vias: str
        """Name of the footprint if it is created without vias."""
        self.fp_name_with_vias: str
        """Name of the footprint if it is created with vias."""
        self.model_name: str
        """Name of the 3D model."""
        self.lib_name: str
        """Name of the library."""

        super().__init__(id, spec, file_name)

        if file_name.endswith("cq_parameters_obsolete.yaml"):
            self.has_fp_data = False
        else:
            self.has_fp_data = True

        self._extract_generator_independent_data()
        self._extract_general_data()
        self._extract_dimensions()
        self._extract_pinning()
        self._extract_3d_data()
        self._compose_device_names()
        self._compose_lib_name()

    def _extract_generator_independent_data(self) -> None:
        self.metadata = common_metadata.CommonMetadata(self.spec)
        if "top_slug" in self.spec:
            self.top_slug = TopSlugConfiguration(self.spec["top_slug"])
        else:
            self.top_slug = None
        self.additional_drawings = (
            fp_additional_drawing.FPAdditionalDrawing.from_standard_yaml(self.spec)  # type: ignore
        )
        self.rule_areas = rule_area_properties.RuleAreaProperties.from_standard_yaml(  # pyright: ignore
            self.spec
        )
        self.pad_overrides = pad_overrides.PadOverrides(
            self.spec.get(pad_overrides.PAD_OVERRIDES_KEY, [])
        )

    def _extract_general_data(self) -> None:
        self.device_type = self.spec.get("device_type", "")
        self.lead_type = self.spec.get("lead_type", "gullwing")
        # only gullwing and flat are supported by this generator
        if self.lead_type not in ["gullwing", "flat_lead"]:
            raise ValueError(f"Unsupported lead type: {self.lead_type}")

        self.force_small_pitch_ipc_definition = self.spec.get(
            "force_small_pitch_ipc_definition", False
        )
        if self.force_small_pitch_ipc_definition and self.lead_type != "gullwing":
            raise ValueError(
                f"force_small_pitch_ipc_definition is not supported for lead type: {self.lead_type}"
            )
        self.ipc_density = ipc_rules.IpcDensity.from_str(
            self.spec.get("ipc_density", "nominal")
        )

    def _extract_dimensions(self) -> None:
        spec = self.spec

        self.body_size_x = TolerancedSize.from_yaml(spec, base_name="body_size_x")
        self.body_size_y = TolerancedSize.from_yaml(spec, base_name="body_size_y")
        self.lead_width = TolerancedSize.from_yaml(spec, base_name="lead_width")
        if "lead_len" in spec:
            self.lead_len = TolerancedSize.from_yaml(spec, base_name="lead_len")
        else:
            self.lead_len = None
            self.has_fp_data = False
        if "EP_size_x_min" in spec and "EP_size_x_max" in spec or "EP_size_x" in spec:
            self.ep_size_x = TolerancedSize.from_yaml(spec, base_name="EP_size_x")
            self.ep_size_y = TolerancedSize.from_yaml(spec, base_name="EP_size_y")
            self.has_ep = True
        else:
            self.ep_size_x = TolerancedSize.from_string("0")
            self.ep_size_y = TolerancedSize.from_string("0")
            self.has_ep = False

        if "EP_mask_x" in spec and "EP_mask_y" in spec:
            self.ep_mask_x = TolerancedSize.from_yaml(spec, base_name="EP_mask_x")
            self.ep_mask_y = TolerancedSize.from_yaml(spec, base_name="EP_mask_y")
        else:
            self.ep_mask_x = TolerancedSize.from_string("0")
            self.ep_mask_y = TolerancedSize.from_string("0")

        self.heel_reduction = spec.get("heel_reduction", 0.0)

        if "overall_size_x" not in spec and "overall_size_y" not in spec:
            raise KeyError(
                "Either overall size x or overall size y must be given "
                "(Outside to outside lead dimensions)"
            )
        if "overall_size_x" in spec:
            self.overall_size_x = TolerancedSize.from_yaml(
                spec, base_name="overall_size_x"
            )
        else:
            self.overall_size_x = TolerancedSize.from_yaml(
                spec, base_name="overall_size_y"
            )
        if "overall_size_y" in spec:
            self.overall_size_y = TolerancedSize.from_yaml(
                spec, base_name="overall_size_y"
            )
        else:
            self.overall_size_y = TolerancedSize.from_yaml(
                spec, base_name="overall_size_x"
            )

    def _extract_pinning(self) -> None:
        self.pitch = self.spec["pitch"]
        if self.pitch <= 0:
            raise ValueError(f"Pitch must be positive, got {self.pitch}")
        self.num_pins_x = self.spec["num_pins_x"]
        self.num_pins_y = self.spec["num_pins_y"]

        if "deleted_pins" in self.spec:
            if type(self.spec["deleted_pins"]) is int:
                self.spec["deleted_pins"] = [self.spec["deleted_pins"]]
            self.deleted_pins = self.spec["deleted_pins"]
        else:
            self.deleted_pins = []
        if "hidden_pins" in self.spec:
            if type(self.spec["hidden_pins"]) is int:
                self.spec["hidden_pins"] = [self.spec["hidden_pins"]]
            self.hidden_pins = self.spec["hidden_pins"]
        else:
            self.hidden_pins = []
        if "deleted_pins" in self.spec and "hidden_pins" in self.spec:
            raise ValueError("A footprint may not have deleted pins and hidden pins.")

        self.pincount_full = self.num_pins_x * 2 + self.num_pins_y * 2
        self.pincount_real = (
            self.pincount_full - len(self.hidden_pins) - len(self.deleted_pins)
        )
        if "pin_count" in self.spec:
            # If the pin count is explicitly given, we use that and don't adjust for hidden/deleted pins
            self.pincount_full = cast(int, self.spec["pin_count"])

    def _extract_3d_data(self) -> None:
        self.has_3d_data = True
        self.marker = self.spec.get("marker", "circle")

        # Lead parameters
        self.lead_top_flat_part_length = cast(
            float | None, self.spec.get("lead_top_flat_part_length")
        )
        if "lead_height" in self.spec:
            self.lead_height = TolerancedSize.from_yaml(self.spec, "lead_height").nominal
        else:
            self.lead_height = 0.0
            self.has_3d_data = False
        if "lead_radius_bottom" in self.spec:
            self.lead_radius_bottom = TolerancedSize.from_yaml(
                self.spec, "lead_radius_bottom"
            ).nominal
        else:
            self.lead_radius_bottom = 0.75 * self.lead_height
            if isinstance(self.lead_len, TolerancedSize):
                self.lead_radius_bottom = min(
                    self.lead_radius_bottom, self.lead_len.nominal - self.lead_height - 0.01
                )
            if self.lead_radius_bottom < 0.0:
                raise ValueError("Given parameters result in negative bending radius.")
        if "lead_radius_top" in self.spec:
            self.lead_radius_top = TolerancedSize.from_yaml(
                self.spec, "lead_radius_top"
            ).nominal
        else:
            self.lead_radius_top = min(0.75 * self.lead_height, self.lead_radius_bottom)
            if self.lead_radius_top < 0.0:
                raise ValueError("Given parameters result in negative bending radius.")
        self.lead_angle = cast(float | None, self.spec.get("lead_angle"))

        # Body parameters (except from height)
        self.body_fillet = cast(float, self.spec.get("body_fillet", 0.0))
        self.body_size_top_delta = max(
            cast(float, self.spec.get("body_size_top_delta", 0.1)), 0.001
        )
        self.corners_chamfer = cast(float, self.spec.get("corners_chamfer", 0.25))
        self.body_angle = cast(float, self.spec.get("body_angle", 10.0))

        # Body height parameters
        if "body_pcb_gap" in self.spec and "body_height" in self.spec:
            self.body_pcb_gap = TolerancedSize.from_yaml(
                self.spec, "body_pcb_gap"
            ).maximum
            self.body_height = TolerancedSize.from_yaml(self.spec, "body_height").maximum
            self.overall_height = self.body_pcb_gap + self.body_height
            if "overall_height" in self.spec:
                overall_height_explicit = TolerancedSize.from_yaml(
                    self.spec, "overall_height"
                ).maximum
                if abs(self.overall_height - overall_height_explicit) > 0.01:
                    raise KeyError(
                        f"Body height is over constrained and maximum dimensions "
                        f"do not match:\n"
                        f"body_pcb_gap: {self.body_pcb_gap}, "
                        f"body_height: {self.body_height}, "
                        f"overall_height: {overall_height_explicit}"
                    )
        elif "body_pcb_gap" in self.spec and "overall_height" in self.spec:
            self.body_pcb_gap = TolerancedSize.from_yaml(
                self.spec, "body_pcb_gap"
            ).maximum
            self.overall_height = TolerancedSize.from_yaml(
                self.spec, "overall_height"
            ).maximum
            self.body_height = self.overall_height - self.body_pcb_gap
        elif "body_height" in self.spec and "overall_height" in self.spec:
            self.body_height = TolerancedSize.from_yaml(self.spec, "body_height").maximum
            self.overall_height = TolerancedSize.from_yaml(
                self.spec, "overall_height"
            ).maximum
            self.body_pcb_gap = self.overall_height - self.body_height
        else:
            self.body_height = 0.0
            self.overall_height = 0.0
            self.body_pcb_gap = 0.0
            self.has_3d_data = False

    def _compose_device_names(self) -> None:
        spec = self.spec

        size_x = self.body_size_x.nominal
        size_y = self.body_size_y.nominal

        if "pin_count" in spec:
            # If the pin count is explicitly given, we use that and don't adjust for hidden/deleted pins
            pincount_text = "{}".format(self.pincount_full)
        elif self.hidden_pins:
            pincount_text = "{}-{}".format(
                self.pincount_full - len(self.hidden_pins), self.pincount_full
            )
        elif self.deleted_pins:
            pincount_text = "{}-{}".format(
                self.pincount_full, self.pincount_full - len(self.deleted_pins)
            )
        else:
            pincount_text = "{}".format(self.pincount_full)

        ep_size_x = self.ep_size_x.nominal
        ep_size_y = self.ep_size_y.nominal
        if self.has_ep:
            name_format = PACKAGE_CONFIG[
                "fp_name_EP_format_string_no_trailing_zero_pincount_text"
            ]
            if "EP_size_x_overwrite" in spec:
                ep_size_x = cast(float, spec["EP_size_x_overwrite"])
                ep_size_y = cast(float, spec["EP_size_y_overwrite"])
            if "EP_mask_x" in self.spec:
                name_format = PACKAGE_CONFIG[
                    "fp_name_EP_custom_mask_format_string_no_trailing_zero_pincount_text"
                ]
        else:
            name_format = PACKAGE_CONFIG[
                "fp_name_format_string_no_trailing_zero_pincount_text"
            ]

        if self.metadata.custom_name_format:
            name_format = self.metadata.custom_name_format

        # This suffix is always added to the footprint name, as it is important for the 3D model
        always_suffix = ""

        if self.top_slug:
            always_suffix = "_" + self.top_slug.get_name_suffix()

        suffix = spec.get("suffix", "")

        if always_suffix:
            suffix = always_suffix + suffix

        self.fp_name_without_vias = (
            name_format.format(
                man=self.metadata.manufacturer or "",
                mpn=self.metadata.part_number or "",
                pkg=self.device_type,
                pincount=pincount_text,
                size_y=size_y,
                size_x=size_x,
                pitch=spec["pitch"],
                ep_size_x=ep_size_x,
                ep_size_y=ep_size_y,
                mask_size_x=self.ep_mask_x.nominal,
                mask_size_y=self.ep_mask_y.nominal,
                suffix=suffix,
                suffix2="",
                vias="",
            )
            .replace("__", "_")
            .lstrip("_")
        )

        self.fp_name_with_vias = (
            name_format.format(
                man=self.metadata.manufacturer or "",
                mpn=self.metadata.part_number or "",
                pkg=self.device_type,
                pincount=pincount_text,
                size_y=size_y,
                size_x=size_x,
                pitch=spec["pitch"],
                ep_size_x=ep_size_x,
                ep_size_y=ep_size_y,
                mask_size_x=self.ep_mask_x.nominal,
                mask_size_y=self.ep_mask_y.nominal,
                suffix=suffix,
                suffix2="",
                vias=self.spec.get("thermal_via_suffix", "_ThermalVias"),
            )
            .replace("__", "_")
            .lstrip("_")
        )

        if self.device_type:
            suffix_3d = (
                suffix
                if spec.get("include_suffix_in_3dpath", "True") == "True"
                else always_suffix
            )
            self.model_name = (
                name_format.format(
                    man=self.metadata.manufacturer or "",
                    mpn=self.metadata.part_number or "",
                    pkg=self.device_type,
                    pincount=pincount_text,
                    size_y=size_y,
                    size_x=size_x,
                    pitch=spec["pitch"],
                    ep_size_x=ep_size_x,
                    ep_size_y=ep_size_y,
                    mask_size_x=self.ep_mask_x.nominal,
                    mask_size_y=self.ep_mask_y.nominal,
                    suffix=suffix_3d,
                    suffix2="",
                    vias="",
                )
                .replace("__", "_")
                .lstrip("_")
            )
        else:
            self.model_name = self.id

    def _compose_lib_name(self) -> None:
        if "override_lib_name" in self.spec:
            self.lib_name = self.spec["override_lib_name"]
        else:
            self.lib_name = PACKAGE_CONFIG["lib_name_format_string"].format(
                category=self.spec["library_Suffix"]
            )

    @property
    def spec_dictionary(self) -> dict[str, Any]:
        """
        Get the raw spec dictionary.

        This is only temporary, and can be piecewise replaced by
        type-safe declarative definitions, but that requires deep changes
        """
        return self.spec

    @property
    def has_top_slug(self) -> bool:
        return self.top_slug is not None
