from typing import Any, Literal, cast

from kilibs.config import ipc_rules  # type: ignore
from kilibs.util.toleranced_size import (  # type: ignore
    TolerancedSize,
    TolerancedSizeHandler,
)
from generators.tools.footprint.declarative_def_tools import (  # type: ignore
    common_metadata,
    fp_additional_drawing,
    pad_overrides,
    rule_area_properties,
)

from ..package_spec import PackageSpec
from ..config import PACKAGE_CONFIG
from generators.tools.spec.spec_registry import register_spec

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
class NoLeadSpec(PackageSpec):
    """
    A type that represents the spec of a no lead package.
    """


    def __init__(
        self,
        id: str = "",
        spec: dict[str, Any] = {},
        file_name: str = "",
    ) -> None:
        """Create an instance of `PackageSpec`.

        Args:
            id: The name/identifier of the spec. Typically, this is the name of the key
                of the spec (in the YAML file) or the name of the component.
            spec: The dictionary containing the specification of the component.
            file_name: The name of the YAML file that holds this spec definition.
        """

        # Instance attributes for generator independent data:
        self.metadata: common_metadata.CommonMetadata
        """The common meta data."""
        self.top_slug: TopSlugConfiguration | None
        """The optional top slug configuration."""
        self.additional_drawings: list[fp_additional_drawing.FPAdditionalDrawing]
        """The list containing additional drawings."""
        self.rule_areas: list[rule_area_properties.RuleAreaProperties] = []
        """The rule areas (zones)."""
        self.pad_overrides: pad_overrides.PadOverrides
        """Definitions to overwrite properties of some pads"""
        self.toleranced_size_handler: TolerancedSizeHandler
        """Handler for toleranced sizes."""

        # Instance attributes for general data:
        self.device_type: str
        """The device type."""
        self.ipc_density: ipc_rules.IpcDensity
        """The IPC density rules."""

        # Instance attributes related to the body:
        self.body_size_x: TolerancedSize
        """The body size in x direction."""
        self.body_size_y: TolerancedSize
        """The body size in y direction."""
        self.body_pcb_gap: TolerancedSize
        """The maximum gap between the PCB and the component body."""
        self.body_height: TolerancedSize
        """The maximum body height."""
        self.overall_height: TolerancedSize
        """The maximum overall height."""
        self.body_fillet: float
        """The size of the fillet of the component body."""

        # Instance attributes related to the pinning:
        self.pitch_x: TolerancedSize
        """The pitch along the x-axis."""
        self.pitch_y: TolerancedSize
        """The pitch along the y-axis."""
        self.lead_center_pos_x: TolerancedSize
        """The distance between the pins on the y-axis and the center."""
        self.lead_center_pos_y: TolerancedSize
        """The distance between the pins on the x-axis and the center."""
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

        # Instance attributes related to the pin shapes:
        self.lead_width: TolerancedSize
        """The lead length."""
        self.lead_len_h: TolerancedSize
        """The lead length of the pins on the x-axis."""
        self.lead_len_v: TolerancedSize
        """The lead length of the pins on the y-axis."""
        self.lead_height: TolerancedSize
        """The height of a lead."""
        self.lead_to_edge: TolerancedSize
        """The distance between the lead edge and the body edge."""
        self.lead_shape: str
        """The shape of the pins."""
        self.lead_shape_custom: list[list[list[float]]]
        """The polygon definition in case of `lead_shape = custom`."""

        # Instance attributes related to the exposed pad:
        self.has_ep: bool
        """Whether the device has an exposed pad"""
        self.ep_size_x: TolerancedSize
        """The size of the exposed pad(s) in x direction."""
        self.ep_size_y: TolerancedSize
        """The size of the exposed pad(s) in y direction."""
        self.ep_angle: float
        """The rotation angle of the exposed pad(s)."""
        self.ep_mask_x: TolerancedSize
        """The size of the mask of the exposed pad in x direction."""
        self.ep_mask_y: TolerancedSize
        """The size of the mask of the exposed pad in y direction."""
        self.ep_chamfer: TolerancedSize
        """The size of the chamfer on the exposed pad on the top left corner."""
        self.ep_num: list[int]
        """Number of exposed pads in x- and y-direction (creates a pad array)."""
        self.ep_pitch: list[float]
        """The pitch of the exposed pads in x- and y-direction."""
        self.ep_offset_x: TolerancedSize
        """The offset of the exposed pad(s) in the x direction."""
        self.ep_offset_y: TolerancedSize
        """The offset of the exposed pad(s) in the y direction."""

        # Instance attributes related to the marker:
        self.marker: Literal["circle", "bar", "none"]
        """Type of marker for the first pin."""
        self.marker_dx: float | None
        """Distance along the x-axis between the marker and the border."""
        self.marker_dy: float | None
        """Distance along the y-axis between the marker and the border."""

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

        self._extract_generator_independent_data()
        self._extract_general_data()
        self._extract_body_data()
        self._extract_pinning_data()
        self._extract_pin_shape_data()
        self._extract_exposed_pad_data()
        self._extract_marker_data()
        self._compose_device_names()
        self._compose_lib_name()
        self._has_3D_and_FP_data(file_name)

    def _extract_generator_independent_data(self) -> None:
        self.metadata = common_metadata.CommonMetadata(self.spec)
        if "top_slug" in self.spec:
            self.top_slug = TopSlugConfiguration(self.spec["top_slug"])
        else:
            self.top_slug = None
        self.additional_drawings = (
            fp_additional_drawing.FPAdditionalDrawing.from_standard_yaml(self.spec)
        )  # type: ignore
        self.rule_areas = rule_area_properties.RuleAreaProperties.from_standard_yaml(  # type: ignore
            self.spec
        )
        self.pad_overrides = pad_overrides.PadOverrides(
            self.spec.get(pad_overrides.PAD_OVERRIDES_KEY, [])
        )
        self.toleranced_size_handler = TolerancedSizeHandler(
            self.spec, self.spec.get("unit")
        )

    def _extract_general_data(self) -> None:
        self.device_type = self.spec.get("device_type", "")
        self.ipc_density = ipc_rules.IpcDensity.from_str(
            self.spec.get("ipc_density", "nominal")
        )

    def _extract_body_data(self) -> None:
        tsh = self.toleranced_size_handler
        body_height = tsh.get_or_none("body_height")
        overall_height = tsh.get_or_none("overall_height")
        body_pcb_gap = tsh.get_or_none("body_pcb_gap")
        if not body_pcb_gap:
            if body_height and overall_height:
                body_pcb_gap = overall_height - body_height
            else:
                body_pcb_gap = TolerancedSize(nominal=0.0)
        else:
            if body_pcb_gap.maximum < 0:
                # Workaround: until the generator supports negative seating planes
                # we just set the value to zero:
                body_pcb_gap = TolerancedSize(nominal=0.0)

        if not body_height:
            if overall_height:
                body_height = overall_height - body_pcb_gap
            else:
                body_height = TolerancedSize(nominal=0.0)
        if not overall_height:
            overall_height = body_pcb_gap + body_height
        diff = overall_height.maximum - body_height.maximum - body_pcb_gap.minimum
        if abs(diff) > 0.01:
            raise KeyError(
                f"{self.id}: "
                f"Body height is over constrained and dimensions do not match:\n"
                f"min(body_pcb_gap)={body_pcb_gap.minimum}, "
                f"max(body_height)={body_height.maximum}, "
                f"max(overall_height)={overall_height.maximum}"
            )
        self.body_height = body_height
        self.overall_height = overall_height
        self.body_pcb_gap = body_pcb_gap
        self.body_size_x = tsh.get("body_size_x")
        self.body_size_y = tsh.get("body_size_y")
        self.body_fillet = self.spec.get("body_fillet", 0.0)

    def _extract_pinning_data(self) -> None:
        s = self.spec
        tsh = self.toleranced_size_handler
        self.pitch_x = tsh.get(["pitch", "pitch_x"])
        self.pitch_y = tsh.get(["pitch", "pitch_y"])
        self.lead_center_pos_x = (
            tsh.get_or_none("lead_center_pos_x")
            or tsh.get("lead_center_to_center_x", 0.0) / 2
        )
        self.lead_center_pos_y = (
            tsh.get_or_none("lead_center_pos_y")
            or tsh.get("lead_center_to_center_y", 0.0) / 2
        )
        self.num_pins_x = s["num_pins_x"]
        self.num_pins_y = s["num_pins_y"]

        if "deleted_pins" in s:
            if type(s["deleted_pins"]) is int:
                s["deleted_pins"] = [s["deleted_pins"]]
            self.deleted_pins = s["deleted_pins"]
        else:
            self.deleted_pins = []
        if "hidden_pins" in s:
            if type(s["hidden_pins"]) is int:
                s["hidden_pins"] = [s["hidden_pins"]]
            self.hidden_pins = s["hidden_pins"]
        else:
            self.hidden_pins = []
        if "deleted_pins" in s and "hidden_pins" in s:
            raise ValueError("A footprint may not have deleted pins and hidden pins.")

        self.pincount_full = self.num_pins_x * 2 + self.num_pins_y * 2
        self.pincount_real = (
            self.pincount_full - len(self.hidden_pins) - len(self.deleted_pins)
        )
        if "pin_count" in s:
            # If the pin count is explicitly given, we use that and don't adjust for hidden/deleted pins
            self.pincount_full = cast(int, s["pin_count"])

    def _extract_pin_shape_data(self) -> None:
        tsh = self.toleranced_size_handler
        self.lead_width_h = tsh.get(["lead_width_H", "lead_width"])
        self.lead_width_v = tsh.get(["lead_width_V", "lead_width"])
        self.lead_to_edge = tsh.get("lead_to_edge", 0.0)
        lead_len_h = tsh.get_or_none(["lead_len_H", "lead_len"])
        lead_len_v = tsh.get_or_none(["lead_len_V", "lead_len"])
        body_to_inside_lead_edge = tsh.get_or_none("body_to_inside_lead_edge")
        if body_to_inside_lead_edge:
            self.lead_len_h = body_to_inside_lead_edge - self.lead_to_edge
            self.lead_len_v = body_to_inside_lead_edge - self.lead_to_edge
        else:
            if not lead_len_h or not lead_len_v:
                raise KeyError(
                    "Either 'lead_len' or 'body_to_inside_lead_edge' must be provided!"
                )
            self.lead_len_h = lead_len_h
            self.lead_len_v = lead_len_v
        lead_height = tsh.get_or_none("lead_height")
        if lead_height is None:
            if self.lead_to_edge.nominal > 0.0:
                # For LGAs the height does not matter -> we set it to a fix value:
                self.lead_height = TolerancedSize(
                    nominal=max(0.1, self.body_pcb_gap.maximum)
                )
            else:
                # For QFN/DFN, etc. the typical lead height is about 1/4 total height:
                self.lead_height = TolerancedSize(
                    minimum=self.overall_height.minimum / 5,
                    nominal=self.overall_height.nominal / 5,
                    maximum=self.overall_height.maximum / 5,
                )
        else:
            self.lead_height = lead_height
        self.lead_shape = self.spec.get("lead_shape", "rounded")
        self.lead_shape_custom = self.spec.get("lead_shape_custom", [])

    def _extract_exposed_pad_data(self) -> None:
        tsh = self.toleranced_size_handler
        self.ep_size_x = tsh.get("EP_size_x", 0.0)
        self.ep_size_y = tsh.get("EP_size_y", 0.0)
        self.ep_offset_x = tsh.get("EP_center_x", 0.0)
        self.ep_offset_y = tsh.get("EP_center_y", 0.0)
        self.ep_angle = self.spec.get("EP_angle", 0.0)
        self.ep_mask_x = tsh.get("EP_mask_x", 0.0)
        self.ep_mask_y = tsh.get("EP_mask_y", 0.0)
        self.ep_chamfer = tsh.get("EP_chamfer", 0.0)
        self.ep_num = self.spec.get("EP_num_pads", [1, 1])
        self.ep_pitch = self.spec.get("EP_pitch", [0, 0])
        if self.ep_size_x.nominal and self.ep_size_y.nominal:
            self.has_ep = True
        else:
            self.has_ep = False

    def _extract_marker_data(self) -> None:
        self.marker = self.spec.get("marker", "circle")
        self.marker_dx = self.spec.get("marker_d", self.spec.get("marker_dx"))
        self.marker_dy = self.spec.get("marker_d", self.spec.get("marker_dy"))

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

        if "EP_size_x_overwrite" in spec:
            ep_size_x = cast(float, spec["EP_size_x_overwrite"])
            ep_size_y = cast(float, spec["EP_size_y_overwrite"])
        else:
            ep_size_x = self.ep_size_x.nominal
            ep_size_y = self.ep_size_y.nominal

        layout = ""
        if self.has_ep:
            name_format = PACKAGE_CONFIG[
                "fp_name_EP_format_string_no_trailing_zero_pincount_text"
            ]
        else:
            name_format = PACKAGE_CONFIG[
                "fp_name_format_string_no_trailing_zero_pincount_text"
            ]
            if spec.get("use_name_format", "QFN") == "LGA":
                name_format = PACKAGE_CONFIG[
                    "fp_name_lga_format_string_no_trailing_zero_pincount_text"
                ]

                if self.num_pins_x > 0 and self.num_pins_y > 0:
                    layout = PACKAGE_CONFIG["lga_layout_border"].format(
                        nx=spec["num_pins_x"], ny=spec["num_pins_y"]
                    )

        if self.metadata.custom_name_format:
            name_format = self.metadata.custom_name_format

        suffix = spec.get("suffix", "")

        self.fp_name_without_vias = (
            name_format.format(
                man=self.metadata.manufacturer or "",
                mpn=self.metadata.part_number or "",
                pkg=self.device_type,
                pincount=pincount_text,
                size_x=size_x,
                size_y=size_y,
                pitch=self.pitch_x.nominal,
                layout=layout,
                ep_size_x=ep_size_x,
                ep_size_y=ep_size_y,
                mask_size_x=self.ep_mask_x.nominal,
                mask_size_y=self.ep_mask_y.nominal,
                suffix="",
                suffix2=suffix,
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
                size_x=size_x,
                size_y=size_y,
                pitch=self.pitch_x.nominal,
                layout=layout,
                ep_size_x=ep_size_x,
                ep_size_y=ep_size_y,
                mask_size_x=self.ep_mask_x.nominal,
                mask_size_y=self.ep_mask_y.nominal,
                suffix="",
                suffix2=suffix,
                vias=self.spec.get("thermal_via_suffix", "_ThermalVias"),
            )
            .replace("__", "_")
            .lstrip("_")
        )

        if self.device_type:
            suffix_3d = suffix if spec.get("include_suffix_in_3dpath", True) else ""
            self.model_name = (
                name_format.format(
                    man=self.metadata.manufacturer or "",
                    mpn=self.metadata.part_number or "",
                    pkg=self.device_type,
                    pincount=pincount_text,
                    size_x=size_x,
                    size_y=size_y,
                    pitch=self.pitch_x.nominal,
                    layout=layout,
                    ep_size_x=ep_size_x,
                    ep_size_y=ep_size_y,
                    mask_size_x=self.ep_mask_x.nominal,
                    mask_size_y=self.ep_mask_y.nominal,
                    suffix="",
                    suffix2=suffix_3d,
                    vias="",
                )
                .replace("__", "_")
                .lstrip("_")
            )
        else:
            self.model_name = self.id

        if "fp_name_prefix" in spec:
            prefix = spec["fp_name_prefix"]
            if not prefix.endswith("_"):
                prefix += "_"
            self.model_name = prefix + self.model_name
            self.fp_name_with_vias = prefix + self.fp_name_with_vias
            self.fp_name_without_vias = prefix + self.fp_name_without_vias

    def _compose_lib_name(self) -> None:
        self.lib_name = self.spec.get("library", "Package_DFN_QFN")

    def _has_3D_and_FP_data(self, file_name: str) -> None:
        if self.overall_height.nominal == 0.0:
            self.has_3d_data = False
        else:
            self.has_3d_data = True
        if file_name.endswith("cq_parameters_obsolete.yaml"):
            self.has_fp_data = False
        else:
            self.has_fp_data = True
