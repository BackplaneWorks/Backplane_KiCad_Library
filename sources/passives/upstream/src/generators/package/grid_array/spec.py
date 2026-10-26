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

import csv
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, NamedTuple

from kilibs.config import ipc_rules
from kilibs.geom import Vector2D
from kilibs.util.toleranced_size import TolerancedSize
from generators.tools.footprint.declarative_def_tools import (
    common_metadata,
    fp_additional_drawing,
    rule_area_properties,
)

from generators.tools.spec.spec_registry import register_spec
from ..package_spec import PackageSpec

from ..config import PACKAGE_CONFIG
from .config import ROW_NAMES, GridStagger
from .pad_factory import count_balls_in_layouts


@dataclass(frozen=True)
class GridLayout:
    """A single grid layout of a grid-array (BGA) part.

    The spec layer builds these from the raw layout dictionaries of the spec
    YAML (the main layout and any secondary layouts). The pad factories operate
    on this type-safe view, which is independent of the spec file schema.
    """

    layout_x: int
    """Number of balls in x direction."""
    layout_y: int
    """Number of balls in y direction."""
    row_names: list[str]
    """The base row names (already resolved against the part default)."""
    pitch: float | None = None
    """The ball pitch, or `None` if `pitch_x`/`pitch_y` are given."""
    pitch_x: float | None = None
    """The x pitch, or `None` if `pitch` is given."""
    pitch_y: float | None = None
    """The y pitch, or `None` if `pitch` is given."""
    staggered: GridStagger = GridStagger.NONE
    """The stagger direction."""
    row_name_prefix: str | None = None
    """An optional prefix applied to every row name."""
    first_row: str | None = None
    """The first row name, or `None` to start at the first base row."""
    first_column: int = 1
    """The number of the first column."""
    pad_skips: frozenset[str] = frozenset()
    """The names of the pads that are skipped explicitly."""
    row_skips: list[Any] = field(default_factory=list)
    """The per-row list of columns to skip."""
    area_skips: list[tuple[Any, ...]] = field(default_factory=list)
    """The rectangular areas of pads to skip."""
    first_ball: str | None = None
    """The first ball (staggered layouts only), or `None` for `A1`."""
    offset_x: float = 0.0
    """The x offset of the layout."""
    offset_y: float = 0.0
    """The y offset of the layout."""
    pad_size: Vector2D | None = None
    """An explicit pad size override, or `None` for the part default."""
    pad_shape: str | None = None
    """A pad shape override, or `None` for the part default."""
    paste_shape: str | None = None
    """A paste opening shape override, or `None` for the part default."""
    paste_margin: float | None = None
    """A paste margin override, or `None` for the part default."""

    @classmethod
    def from_dict(
        cls, layout: dict[str, Any], default_row_names: list[str]
    ) -> "GridLayout":
        """Build a `GridLayout` from a raw layout dictionary of the spec.

        Every grid-specced part has a main layout, and may have additional
        (secondary) layouts.

        Args:
            layout: The raw layout definition (the part dict for the main
                layout, or one entry of `secondary_layouts`).
            default_row_names: The part-level default row names.

        Returns:
            The type-safe grid layout.
        """
        raw_staggered = (layout.get("staggered") or "").lower()
        if raw_staggered == "x":
            staggered = GridStagger.X
        elif raw_staggered == "y":
            staggered = GridStagger.Y
        elif raw_staggered:
            raise ValueError('staggered must be either "x" or "y"')
        else:
            staggered = GridStagger.NONE

        return cls(
            layout_x=layout["layout_x"],
            layout_y=layout["layout_y"],
            pitch=layout.get("pitch"),
            pitch_x=layout.get("pitch_x"),
            pitch_y=layout.get("pitch_y"),
            staggered=staggered,
            row_names=list(layout.get("row_names") or default_row_names),
            row_name_prefix=layout.get("row_name_prefix"),
            first_row=layout.get("first_row"),
            first_column=layout.get("first_column", 1),
            pad_skips=frozenset(skip.upper() for skip in layout.get("pad_skips", [])),
            row_skips=list(layout.get("row_skips", [])),
            area_skips=[tuple(skip) for skip in layout.get("area_skips", [])],
            first_ball=layout.get("first_ball"),
            offset_x=layout.get("offset_x", 0.0),
            offset_y=layout.get("offset_y", 0.0),
            pad_size=Vector2D(layout["pad_size"]) if "pad_size" in layout else None,
            pad_shape=layout.get("pad_shape"),
            paste_shape=layout.get("paste_shape"),
            paste_margin=layout.get("paste_margin"),
        )


class PinTableEntry(NamedTuple):
    """A single pad of an explicit pin table (e.g. loaded from a CSV).

    In contrast to grid-based layouts, a pin table carries the full pad
    geometry per pad: position, size and solder-mask aperture.
    """

    name: str
    position: Vector2D
    size: Vector2D
    mask_size: Vector2D


@register_spec
class GridArraySpec(PackageSpec):
    """
    A type that represents the configuration of a grid array footprint
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
        """Create an instance of `PackageSpec`.

        Args:
            id: The name/identifier of the spec. Typically, this is the name of the key
                of the spec (in the YAML file) or the name of the component.
            spec: The dictionary containing the specification of the component.
            file_name: The name of the YAML file that holds this spec definition.
        """
        # Instance attributes for generator independent data:
        self.additional_drawings: list[fp_additional_drawing.FPAdditionalDrawing]
        """The list containing additional drawings."""
        self.rule_areas: list[rule_area_properties.RuleAreaProperties] = []
        """The rule areas (zones)."""

        # Instance attributes for genreator specific data:
        self.marker: str | None
        """The pad above which the first pin marker is placed"""

        # Instance attributes for pad details:
        self.ipc_density: ipc_rules.IpcDensity
        """The IPC density rules."""
        self.pad_shape: str
        """The default pad shape."""
        self.paste_shape: str | None
        """The default solder-paste opening shape, or `None`."""
        self.paste_margin: float
        """The default solder-paste margin in mm."""
        self.pad_diameter: float | None
        """The explicit PCB-side pad diameter, or `None` for IPC calculation."""

        self.ball_type: ipc_rules.BallType
        """The ball type."""
        self.ball_diameter: float
        """The ball diameter."""

        # Instance attributes related to the dimensions of the package:
        self.body_size_x: float
        """Size of the package body in x direction."""
        self.body_size_y: float
        """Size of the package body in y direction."""

        # Instance attributes for the pinning data:
        self.num_balls: int
        """Number of balls in the package."""
        self.pitch: Vector2D | None
        """The pad pitch, or `None` for pin-table parts."""
        self.layout_x: int | None
        """Number of balls in x direction, or `None` for pin-table parts."""
        self.layout_y: int | None
        """Number of balls in y direction, or `None` for pin-table parts."""
        self.layouts: list[GridLayout]
        """The type-safe grid layouts (main and any secondary layouts)."""

        self.pin_table: list[PinTableEntry] | None
        """The explicit pin table (e.g. from a CSV), or `None` for grid parts."""

        self.pin_position_flip_x: bool
        """Whether the pin positions are flipped in x direction when reading the pin table."""
        self.pin_position_flip_y: bool
        """Whether the pin positions are flipped in y direction when reading the pin table."""

        # Instance attributes for the 3D model:
        self.body_pcb_gap: float
        """Size of the gap between the PCB and the package body."""
        self.body_height: float
        """Size of the package body in z direction."""
        self.overall_height: float
        """Overall height of the package (sum of `body_pcb_gap` and `body_height`)."""
        self.body_fillet: float
        """Size of the body fillet in mm."""
        self.first_corner_chamfer: float
        """Size of the chamfer of the first pin corner."""
        self.corner_chamfer: float
        """Size of the chamfer of the other corners."""
        self.molded: bool
        """Whether the package has an overmolded part."""
        self.mold_size_x: float
        """Size of the over molded part in x direction."""
        self.mold_size_y: float
        """Size of the over molded part in y direction."""
        self.mold_size_z_bottom: float
        """Size of the bottom part of the package in z direction."""
        self.ball_diameter: float | None
        """Ball diameter."""
        self.seating_plane: float
        """Height of the seating plane."""

        # Instance attributes related to the names:
        self.device_type: str
        """Device type (WLCSP, dsBGA, ...)"""
        self.package_type: str
        """Package type (BGA, CSP, LGA, ...)."""
        self.name: str
        """Name of the FP and 3D model."""
        self.lib_name: str
        """Name of the library."""

        super().__init__(id, spec, file_name)
        self.file_name = file_name

        if file_name.endswith("cq_parameters_obsolete.yaml"):
            self.has_fp_data = False
        else:
            self.has_fp_data = True

        self.marker = spec.get("marker")

        self._extract_generator_independent_data()
        self._extract_dimension_data()
        self._extract_pinning_data()
        self._extract_pad_style_data()
        self._extract_3d_data()
        self._compose_device_name()
        self._compose_lib_name()

    def _extract_generator_independent_data(self) -> None:
        self.metadata = common_metadata.CommonMetadata(self.spec)

        self.additional_drawings = (
            fp_additional_drawing.FPAdditionalDrawing.from_standard_yaml(self.spec)  # type: ignore
        )
        self.rule_areas = rule_area_properties.RuleAreaProperties.from_standard_yaml(  # pyright: ignore
            self.spec
        )

    def _extract_dimension_data(self) -> None:
        self.body_size_x = self.spec["body_size_x"]
        self.body_size_y = self.spec["body_size_y"]

    def _extract_pinning_data(self) -> None:
        self.ipc_density = ipc_rules.IpcDensity.from_str(
            self.spec.get("ipc_density", "nominal")
        )

        if "pin_table" in self.spec:
            # The pads are defined explicitly by a pin table (e.g. from a CSV),
            # not by a grid layout, so there is no pitch or layout to derive.

            self.pin_table = self._load_pin_table()
            self.num_balls = len(self.pin_table)

            # These parameters can be used for name construction, but they don't affect the pad positions.
            self.pitch = self.spec.get("pitch", None)
            self.layout_x = self.spec.get("layout_x", None)
            self.layout_y = self.spec.get("layout_y", None)

            self.pin_position_flip_x = self.spec.get("pin_position_flip_x", False)
            self.pin_position_flip_y = self.spec.get("pin_position_flip_y", False)
            return

        self.pin_table = None

        if "pitch" in self.spec:
            self.pitch = Vector2D(self.spec["pitch"], self.spec["pitch"])
        elif "pitch_x" in self.spec and "pitch_y" in self.spec:
            self.pitch = Vector2D(self.spec["pitch_x"], self.spec["pitch_y"])
        else:
            raise KeyError("Either pitch or both pitch_x and pitch_y must be given.")

        # These don't make sense for non-table parts
        if "pin_position_flip_x" in self.spec or "pin_position_flip_y" in self.spec:
            raise KeyError(
                "pin_position_flip_x and pin_position_flip_y are only valid for "
                "parts with an explicit pin table."
            )
        self.pin_position_flip_x = False
        self.pin_position_flip_y = False

        self.layout_x = self.spec["layout_x"]
        self.layout_y = self.spec["layout_y"]

        # Build the type-safe grid layouts and count the balls of the main and
        # any secondary layouts.
        default_row_names = self.spec.get("row_names", ROW_NAMES)
        self.layouts = [
            GridLayout.from_dict(layout, default_row_names)
            for layout in [self.spec] + self.spec.get("secondary_layouts", [])
        ]
        self.num_balls = count_balls_in_layouts(self.layouts)

    def _extract_pad_style_data(self) -> None:
        self.pad_shape = self.spec.get("pad_shape", "circle")
        self.paste_shape = self.spec.get("paste_shape")
        self.paste_margin = self.spec.get("paste_margin", 0.0)
        self.pad_diameter = self.spec.get("pad_diameter")

        # This is a default to support legacy specs that don't have a ball type (e.g. 3D model-only
        # defs in cq_parameters_obsolete.yaml). We should migrate those to fully-defined specs.
        self.ball_type = self._ball_type_from_str(
            self.spec.get("ball_type", "collapsible")
        )

        self.ball_diameter = self.spec.get("ball_diameter")

    def _load_pin_table(self) -> list[PinTableEntry]:
        """Load the explicit pin table from the CSV referenced by the spec.

        The table is resolved relative to the directory of the spec's YAML file.

        Returns:
            The parsed pin table.
        """
        pin_table_file = Path(self.file_name).parent / str(self.spec["pin_table"])
        entries: list[PinTableEntry] = []
        with open(pin_table_file, newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            for row in reader:
                diameter = float(row["fp_pad_diameter"])
                mask_diameter = float(row["mask_diameter"])
                entries.append(
                    PinTableEntry(
                        name=row["pin_number"],
                        position=Vector2D.from_floats(
                            float(row["position_x"]), float(row["position_y"])
                        ),
                        size=Vector2D.from_floats(diameter, diameter),
                        mask_size=Vector2D.from_floats(mask_diameter, mask_diameter),
                    )
                )
        return entries

    def _ball_type_from_str(self, string: str) -> ipc_rules.BallType:
        """Convert a ball type string from the device YAML to a `BallType`.
        """
        if string == "collapsible":
            return ipc_rules.BallType.COLLAPSIBLE
        elif string == "non-collapsible":
            return ipc_rules.BallType.NON_COLLAPSIBLE

        raise KeyError(
            f"'{string}' qis an invalid ball type."
        )

    def _read_dimension(self, name: str) -> float:
        """Read a body dimension from the spec, tolerances included.

        The YAML may give a plain number or a tolerance string such as
        ``0.286 +/- 0.05``. the nominal value is used for the 3D model.
        """
        return TolerancedSize.from_yaml(self.spec, base_name=name).nominal

    def _extract_3d_data(self) -> None:
        self.has_3d_data = True
        if "body_pcb_gap" in self.spec and "overall_height" in self.spec:
            self.body_pcb_gap = self._read_dimension("body_pcb_gap")
            self.overall_height = self._read_dimension("overall_height")
            self.body_height = self.overall_height - self.body_pcb_gap
        elif "body_height" in self.spec and "overall_height" in self.spec:
            self.body_height = self._read_dimension("body_height")
            self.overall_height = self._read_dimension("overall_height")
            self.body_pcb_gap = self.overall_height - self.body_height
        elif "body_height" in self.spec and "body_pcb_gap" in self.spec:
            self.body_height = self._read_dimension("body_height")
            self.body_pcb_gap = self._read_dimension("body_pcb_gap")
            self.overall_height = self.body_pcb_gap + self.body_height
        else:
            self.has_3d_data = False
            self.body_pcb_gap = self.spec.get("body_pcb_gap", 0.0)
            self.body_height = self.spec.get("body_height", 0.0)
            self.overall_height = self.spec.get("overall_height", 0.0)

        self.body_fillet = self.spec.get("body_fillet", 0.0)
        self.first_corner_chamfer = self.spec.get("first_corner_chamfer", 0.25)
        self.corner_chamfer = self.spec.get("corner_chamfer", 0.25)
        self.molded = self.spec.get("molded", False)
        self.mold_size_x = self.spec.get("mold_size_x", self.body_size_x * (1 - 0.065))
        self.mold_size_y = self.spec.get("mold_size_y", self.body_size_y * (1 - 0.065))
        self.mold_size_z_bottom = self.spec.get("mold_size_z_bottom", 0.0)
        self.ball_diameter = self.spec.get("ball_diameter")
        self.seating_plane = self.spec.get("seating_plane", 0.0)

    def _compose_device_name(self) -> None:
        self.package_type = self.spec.get("package_type", "BGA")
        self.device_type = self.spec.get("device_type", self.spec.get("package_type", ""))

        if not self.has_fp_data:  # for 3d models defined in cq_parameters.yaml
            self.name = self.id
            return
        if "name" in self.spec:
            self.name = self.spec["name"]
            return
        elif self.spec.get("name_equal_to_key"):
            self.name = self.id
            return

        # Compute number of balls + diverse suffix strings
        pitch_text = ""
        stagger_text = ""
        offcenter_text = ""
        for layout in self.layouts:
            if layout.pitch:
                new_pitch_text = f"P{layout.pitch}mm"
            else:
                pitch_x = layout.pitch_x
                pitch_y = layout.pitch_y
                if not (pitch_x and pitch_y):
                    raise KeyError(
                        "Either pitch or both pitch_x and pitch_y must " "be given."
                    )
                new_pitch_text = f"P{pitch_x}x{pitch_y}mm"
            if not pitch_text.endswith(new_pitch_text):
                pitch_text += new_pitch_text
            if layout.staggered is not GridStagger.NONE:
                stagger_text = "_Stagger"
            if layout.offset_x or layout.offset_y:
                offcenter_text = "_Offcenter"

        if self.metadata.custom_name_format:
            name_format = self.metadata.custom_name_format
        else:
            name_format = PACKAGE_CONFIG["fp_name_bga_format_string_no_trailing_zero"]

        pad_suffix = ""
        if (
            self.spec.get("include_pad_diameter_in_name")
            and "pad_diameter" in self.spec
        ):
            pad_diameter = self.spec["pad_diameter"]
            pad_suffix = f"_Pad{pad_diameter}mm"

        ball_suffix = ""
        if (
            self.spec.get("include_ball_diameter_in_name")
            and "ball_diameter" in self.spec
        ):
            ball_diameter = self.spec["ball_diameter"]
            ball_suffix = f"_Ball{ball_diameter}mm"

        suffix = self.spec.get("suffix", "")

        self.name = (
            name_format.format(
                man=self.metadata.manufacturer or "",
                mpn=self.metadata.part_number or "",
                pkg=self.device_type,
                pincount=self.num_balls,
                size_x=self.body_size_x,
                size_y=self.body_size_y,
                nx=self.layout_x,
                ny=self.layout_y,
                pitch=pitch_text,
                ball_d=ball_suffix,
                pad_d=pad_suffix,
                stagger=stagger_text,
                offcenter=offcenter_text,
                suffix=suffix,
                suffix2="",
            )
            .replace("__", "_")
            .lstrip("_")
        )

    def _compose_lib_name(self) -> None:
        self.lib_name = f"Package_{self.package_type}"
