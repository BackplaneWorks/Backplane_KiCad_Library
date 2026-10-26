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

"""Classes for SMD inductor properties."""

import abc
import logging
from typing import Any, cast

from kilibs.declarative_defs.packages.two_pad_dimensions import TwoPadDimensions
from generators.tools.spec.base_spec import BaseSpec
from generators.tools.spec.spec_registry import register_spec
from kilibs.geom import Vector3D


def _get_key_as_float_or_none(d: dict[str, Any], key: str) -> float | None:
    """Return the key as a `float` or, if the key is not present in the dictionary,
    then `None` is returned.

    Args:
        d: The dictionary.
        key: The key.
    """
    try:
        return float(d[key])
    except KeyError:
        return None


class InductorBodyParameters(abc.ABC):
    """Parameters for the body of an inductor."""

    @abc.abstractmethod
    def get_body_size(self) -> Vector3D:
        """Get the size of the body of the inductor for naming purposes."""
        pass


class TwoPadInductorParameters(InductorBodyParameters):
    """
    Parameters for any simple two-pad inductor model.
    """

    def __init__(self, data: dict[str, Any]):
        self.width_x: float
        """Width of the inductor in mm."""
        self.length_y: float
        """Length of the inductor in mm."""
        self.height: float
        """Overall height of the inductor in mm."""
        self.landing_dims: TwoPadDimensions
        """Dimensions of PCB landing pads in mm."""
        self.device_pad_dims: TwoPadDimensions
        """Dimensions of pads on the inductor in mm."""

        self.width_x = float(data["widthX"])
        self.length_y = float(data["lengthY"])
        self.height = float(data["height"])
        self.landing_dims = self._derive_landing_size(data)
        self.device_pad_dims = self._derive_pad_spacing(data)

    def get_body_size(self) -> Vector3D:
        """Get the size of the body of the inductor for naming purposes.

        Returns:
            The size of the body of the inductor as a `Vector2D`.
        """
        return Vector3D(self.width_x, self.length_y, self.height)

    def _derive_landing_size(self, data: dict[str, Any]) -> TwoPadDimensions:
        """Handle the various methods of providing sufficient dimensions to derive the
        land X dimension.

        Args:
            data: The dictionary containing the PCB landing pad dimensions.

        Returns:
            An instance of `TwoPadDimensions` containing the pad dimensions extracted
            from the given `dict`.
        """
        landing_y = float(data["landingY"])
        xin = _get_key_as_float_or_none(data, "landingX")
        spc_c = _get_key_as_float_or_none(data, "landingSpacingX")
        spc_ix = _get_key_as_float_or_none(data, "landingInsideX")
        spc_ox = _get_key_as_float_or_none(data, "landingOutsideX")
        try:
            return TwoPadDimensions(landing_y, xin, spc_c, spc_ix, spc_ox)
        except ValueError:
            raise RuntimeError(
                "Unhandled combination of landing dimensions, "
                "saw: " + ", ".join(data.keys())
            )

    def _derive_pad_spacing(self, data: dict[str, str]) -> TwoPadDimensions:
        """Handle the various methods of providing sufficient dimensions to derive the
        pad dimensions (this is the pad on the device, not on the PCB - that is the
        landing).

        If the parameters are not given, pads will be constructed from the landing sizes
        (is this an error?).

        Args:
            data: The dictionary from which to extract the pad dimensions of the
                inductor.

        Returns:
            An instance of `TwoPadDimensions` containing the pad dimensions extracted
            from the given `dict`.
        """
        pad_y = _get_key_as_float_or_none(data, "padY")
        if pad_y is None:
            logging.debug(
                "No physical pad dimensions (padY) found - using body and PCB landing "
                "dimensions (lengthY, landingY) as a substitute."
            )
            pad_y = min(self.landing_dims.size_crosswise, self.length_y)

        spc_c = _get_key_as_float_or_none(data, "padSpacingX")
        spc_ix = _get_key_as_float_or_none(data, "padInsideX")
        spc_ox = _get_key_as_float_or_none(data, "padOutsideX")
        pad_x = _get_key_as_float_or_none(data, "padX")
        try:
            pad_dims = TwoPadDimensions(pad_y, pad_x, spc_c, spc_ix, spc_ox)
        except ValueError:
            # We don't have enough info here to construct the pad dimensions
            # So construct a pad width to be getting on with.
            logging.debug(
                "No physical pad dimensions (padX) found - using landing dimensions "
                "as a substitute."
            )
            # limit the outside dim to the overall package size
            pad_ox = min(self.landing_dims.spacing_outside, self.width_x)
            pad_dims = TwoPadDimensions(
                pad_y,
                spacing_inside=self.landing_dims.spacing_inside,
                spacing_outside=pad_ox,
            )
        return pad_dims


class CuboidParameters(TwoPadInductorParameters):
    """
    Parameters for the cuboid inductor model.
    """

    def __init__(self, data: dict[str, Any], bottom_pads: bool):
        super().__init__(data)

        self.corner_radius: float | None
        """Optional corner radius of the inductor in mm."""
        self.top_fillet_radius: float | None
        """Optional top fillet radius of the inductor in mm."""
        self.bottom_pads: bool
        """Whether the inductor has pads on the bottom side of the body."""

        self.corner_radius = _get_key_as_float_or_none(data, "cornerRadius")
        self.top_fillet_radius = _get_key_as_float_or_none(data, "topFilletRadius")

        self.bottom_pads = bottom_pads


class HorizontalAirCoreParameters(TwoPadInductorParameters):
    """
    Parameters for the horizontal air core D-foot inductor model.

    This is a special case of the two-pad inductor, where the pads are on the
    sides of the inductor, and the coil is mounted horizontally.
    """

    def __init__(self, data: dict[str, Any]):
        super().__init__(data)

        # This default comes from what was used for the Coilcraft SQ series
        # Probably would be better to specify this.
        self.wire_size: float = data.get(
            "wireSize", self.landing_dims.size_inline * 0.5
        )
        """The size of the wire used in the coil in mm."""

        self.foot_shape: str = data["footShape"]
        """The shape of the foot of the inductor, e.g. 'd_section'"""

        # Round and rectangular foot shapes may be needed in the future,
        if self.foot_shape not in ["d_section"]:
            raise ValueError(
                f"Unknown foot shape '{self.foot_shape}' for horizontal air core inductor."
            )


class ShieldedDrumRoundedRectBlockParameters(TwoPadInductorParameters):
    """
    Parameters for the shielded drum block inductor model.

    Example series for this type: Coilcraft MSS1246:
    https://www.coilcraft.com/getmedia/960fadbe-0ca0-40e2-ae20-64edb15f3a07/mss1246.pdf
    """

    def __init__(self, data: dict[str, Any]):
        super().__init__(data)

        self.core_diameter: float
        """Diameter of the core of the inductor in mm."""
        self.corner_radius: float
        """Optional corner radius of the inductor in mm."""

        self.core_diameter = float(data["coreDiameter"])
        self.corner_radius = float(data["cornerRadius"])


class ShieldedDrumFlatBaseParameters(TwoPadInductorParameters):
    r"""
    Parameters for the shielded drum flat base inductor model.

    Example series for this type: TDK SLF series:
    https://product.tdk.com/en/system/files/dam/doc/product/inductor/inductor/smd/catalog/inductor_commercial_power_slf6025_en.pdf

        +--------------+
        |              |
        |              |
    ++--+--------------+--++
    ++--------------------++

     +--------------------+
     |  /              \  |
     | /                \ |
    +|/                  \|+
    |||                  |||
    +|\                  /|+
     | \                / |
     |  \              /  |
     +--------------------+
    """

    def __init__(self, data: dict[str, Any]):

        super().__init__(data)
        self.core_diameter: float
        """Diameter of the core of the inductor."""
        self.base_thickness: float
        """Thickness of the base of the inductor."""
        self.base_corner_radius: float
        """Corner radius of the base of the inductor."""
        self.top_cap_z_height: float
        """Height of the top cap of the inductor. 0 for no cap."""
        self.top_cap_diameter: float
        """Diameter of the top cap of the inductor."""
        self.top_edge_chamfer: float
        """Chamfer of the top edge of the inductor (not the cap, the shield)."""
        self.top_cap_ring_color: str | None
        """Color of the top cap ring, if given (else no colored ring)"""
        self.pin1_corner_notch_size: float
        """Size of the notch in the corner of the base for pin 1, if any, 0 for no notch."""
        self.pin1_corner_notch_at_top_y: bool
        """Whether the notch for pin 1 is at the top or bottom of the base (in y)."""
        self.orientation_mark: str | None
        """The type of orientation mark to use, e.g. 'dot'"""
        self.has_visible_coil_ends: bool
        """Whether the coil ends are visible above the base."""

        self.core_diameter = float(data["coreDiameter"])
        self.base_thickness = float(data["baseThickness"])
        self.base_corner_radius = float(data.get("baseCornerRadius", 0.5))
        self.top_cap_z_height = float(data.get("topCapZHeight", 0.0))

        if "topCapDiameterProportion" in data:
            # If the top cap diameter is given as a proportion of the core diameter,
            # then calculate it.
            self.top_cap_diameter = self.core_diameter * float(
                data["topCapDiameterProportion"]
            )
        else:
            # Otherwise, use the given top cap diameter, or turn it off
            self.top_cap_diameter = float(data.get("topCapDiameter", 0.0))

        self.top_cap_ring_color = data.get("topCapRingColor", None)

        self.top_edge_chamfer = float(data.get("topEdgeChamfer", 0.2))

        self.pin1_corner_notch_size = float(data.get("pin1CornerNotchSize", 0.0))
        self.pin1_corner_notch_at_top_y = bool(data.get("pin1CornerNotchAtTopY"))

        self.has_visible_coil_ends = bool(data.get("hasVisibleCoilEnds"))

        self.orientation_mark = data.get("orientationMark", None)


@register_spec
class SmdInductorSpec(BaseSpec):
    """Object that represents the definition of a single inductor part.

    This is a complete defintion of a single inductor, which may be being
    constructed from a merged dictionary of series and part definitions.
    """

    def __init__(
        self,
        id: str = "",
        spec: dict[str, Any] = {},
        file_name: str = "",
    ) -> None:
        """Create an instance of `SmdInductorSpec`.

        Args:
            id: The name/identifier of the spec. This is the name of the key
                of the spec (in the YAML file) or the name of the component.
            spec: The dictionary containing the specification of the component.
            file_name: The name of the YAML file that holds this spec definition.
        """
        # General instance attributes
        self.manufacturer: str
        """The manufacturer of the inductors."""
        self.tags: list[str]
        """The tags."""
        self.has_orientation: bool
        """`True` if the inductors have an orientation and require a pin 1 marker."""
        self.library_name: str
        """The name of the library to store the output in."""
        self.series_description: str | None = None
        """Optional name of the series, used in the footprint description if the part
        number isn't enough."""
        self.additional_description: str | None = None
        """Optional additional description for the series, used in the footprint
        description, after the series. Can be useful when the 'series' def is only
        a subset of the manufacturer-described series."""

        # Instance attributes for the 3D model
        self.has_3d_data: bool
        """`True` if this spec has all information required for the 3D model."""
        self.body_color: str
        """Color of the body, if there is one"""
        self.pad_color: str
        """Color of the pads"""
        self.pad_thickness: float
        """Thickness of the pads"""
        self.coil_color: str | None
        """Color of the coil, if drawn"""

        # Instance attributes for the inductor
        self.part_number: str
        """Part number of the inductor."""
        self.datasheet: str | None
        """Datasheet of the inductor or `None` if the series datasheet is used."""
        self.body: InductorBodyParameters
        """The body parameters of the inductor, which determine both how the
        footprint may be drawn and how the 3D model is generated."""
        self.include_in_qa: bool
        """Whether to include this part in the QA set."""

        super().__init__(id, spec, file_name)

        self.manufacturer = spec["manufacturer"]
        # space delimited list of the tags
        self.tags = spec.get("tags", [])
        self.series_description = spec.get("series_description", None)
        self.additional_description = spec.get("additional_description", None)

        self.has_orientation = spec.get("has_orientation", False)
        self.library_name = spec["library_name"]

        if "3d" in spec:
            self.has_3d_data = True
        else:
            self.has_3d_data = False
        block_3d = spec.get("3d", {})
        self.body_color = block_3d.get("bodyColor", "black body")
        self.coil_color = block_3d.get("wireColor", "metal dark cu")
        self.pad_color = block_3d.get("pinColor", "metal grey pins")
        self.pad_thickness = block_3d.get("padThickness", 0.05)

        self.part_number = spec["PartNumber"]
        self.datasheet = spec.get("datasheet", None)
        self.include_in_qa = spec.get("include_in_qa", False)  # type: ignore

        body_type_key = cast(int | str, spec.get("3d", {}).get("type", 1))  # type: ignore

        # Switch the inductor type based on the 'type' key
        match body_type_key:
            case 1 | 2:  # "cuboid":
                self.body = CuboidParameters(spec, body_type_key == 1)
            case "horizontal_air_core":
                self.body = HorizontalAirCoreParameters(spec)
            case "shielded_drum_rounded_rectangular_base":
                self.body = ShieldedDrumRoundedRectBlockParameters(spec)
            case "shielded_drum_flat_base":
                self.body = ShieldedDrumFlatBaseParameters(spec)
            case _:
                raise ValueError(
                    f"Unknown inductor type '{body_type_key}' for part {self.part_number}"
                )
