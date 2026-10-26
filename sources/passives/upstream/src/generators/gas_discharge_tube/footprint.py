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

import abc

from KicadModTree import Footprint, FootprintType, Pad
from kilibs.declarative_defs import SpecDict
from generators.tools.spec.base_spec import BaseSpec
from kilibs.config.global_config import GLOBAL_CONFIG
from generators.tools.spec.spec_generator import get_file_name_ids_specs
from kilibs.geom import Vector2D
from kilibs.util.toleranced_size import TolerancedSize
from generators.tools.footprint.declarative_def_tools import common_metadata
from generators.tools.footprint.save_footprint import write_footprint
from generators.tools.footprint.nodes.layouts.cross_body_pad_layout import CrossBodyPadLayout
from generators.tools.footprint.nodes.layouts.tht_axial_layout import ThtAxialLayout


class GDTBodyProperties(abc.ABC):
    """
    Properties for the body of a GDT (Gas Discharge Tube).
    This class is used to define the physical characteristics of the GDT body.
    """

    num_pads: int


class GDTBodyPropertiesSMDCylinder(GDTBodyProperties):
    """
    Properties for a "cylinder" style GDT (i.e. for an SMD cylinder with 2 or 3 terminals).
    """

    body_length: TolerancedSize
    body_diameter: TolerancedSize

    def __init__(self, spec: SpecDict):
        self.body_length = TolerancedSize.from_string(spec["body_length"])
        self.body_diameter = TolerancedSize.from_string(spec["body_diameter"])
        self.num_pads = int(spec["num_pads"])


class GDTBodyPropertiesTHTCylinder(GDTBodyProperties):
    """
    Properties for a "cylinder" style GDT (i.e. for a THT cylinder with 2 or 3 terminals).
    """

    body_length: TolerancedSize
    body_diameter: TolerancedSize
    lead_spacing: TolerancedSize
    lead_diameter: TolerancedSize

    def __init__(self, spec: SpecDict):
        self.body_length = TolerancedSize.from_string(spec["body_length"])
        self.body_diameter = TolerancedSize.from_string(spec["body_diameter"])
        self.lead_spacing = TolerancedSize.from_string(spec["lead_spacing"])
        self.lead_diameter = TolerancedSize.from_string(spec["lead_diameter"])
        self.total_length = TolerancedSize.from_string(spec["total_length"])

        self.num_pads = int(spec["num_pads"])


class GDTLayoutProperties(abc.ABC):
    """
    Properties for the layout (footprint-specific parameters) of a GDT (Gas Discharge Tube).
    """

    @property
    @abc.abstractmethod
    def is_tht(self) -> bool:
        """Returns True if this GDT is a through-hole type."""
        return False

    @property
    @abc.abstractmethod
    def body_size_description(self) -> str:
        """Returns a description of the body size for use in the description."""
        return ""


class GDTCrossBodyLayoutProperties(GDTLayoutProperties):
    """
    Properties for a "cross-body-pad" style GDT. This probably is mostly used for
    SMD cyclinder GDTs with 2 or 3 terminals.
    """

    center_pad_size: Vector2D | None
    end_pad_size: Vector2D
    end_pad_center_spacing: float | None
    end_pad_inner_spacing: float | None
    end_pad_outer_spacing: float | None
    body_properties: GDTBodyPropertiesSMDCylinder

    """
    If True, the end pad size is specified directly, rather than derived from the physical terminal sizes
    """

    def __init__(self, body_props: GDTBodyPropertiesSMDCylinder, spec: SpecDict):

        self.body_properties = body_props

        if self.body_properties.num_pads not in (2, 3):
            raise ValueError("GDTs only support 2 or 3 pads")

        if self.body_properties.num_pads == 3:
            # We need the center pad size
            if "center_pad_size" not in spec:
                raise ValueError("3-pad GDTs require a center pad size")
            self.center_pad_size = Vector2D(spec["center_pad_size"])
        else:
            self.center_pad_size = None

        self.end_pad_size = Vector2D(spec["end_pad_size"])

        self.end_pad_center_spacing = None
        self.end_pad_inner_spacing = None
        self.end_pad_outer_spacing = None

        if "end_pad_center_spacing" in spec:
            self.end_pad_center_spacing = float(spec["end_pad_center_spacing"])
        elif "end_pad_inner_spacing" in spec:
            self.end_pad_inner_spacing = float(spec["end_pad_inner_spacing"])
        elif "end_pad_outer_spacing" in spec:
            self.end_pad_outer_spacing = float(spec["end_pad_outer_spacing"])
        else:
            raise ValueError("GDTs require an end pad center spacing or inner spacing")

    @property
    def is_tht(self) -> bool:
        return False

    @property
    def body_size_description(self) -> str:
        """Returns a description of the body size."""
        body_size = self.body_size
        return f"{body_size.x}x{body_size.y}mm"

    @property
    def body_size(self) -> Vector2D:
        # Just defer to the body properties for the body size.
        return Vector2D(
            self.body_properties.body_length.nominal,
            self.body_properties.body_diameter.nominal,
        )


class GDTLayoutPropertiesTHTInline(GDTLayoutProperties):
    """
    Properties for a "inline" style THT GDT. This is used for THT cylinder GDTs with 2 or 3 terminals.
    """

    def __init__(self, body_props: GDTBodyPropertiesTHTCylinder, spec: SpecDict):
        self.body_properties = body_props

        pad_props = spec["pad"]
        self.pad_size = Vector2D(pad_props["size"])
        self.pad_drill = pad_props["drill"]

    @property
    def is_tht(self) -> bool:
        return True

    @property
    def body_size_description(self) -> str:
        """Returns a description of the body size."""
        body_size = self.body_size
        return f"{body_size.x}x{body_size.y}mm"

    @property
    def body_size(self) -> Vector2D:
        # Just defer to the body properties for the body size.
        return Vector2D(
            self.body_properties.body_length.nominal,
            self.body_properties.body_diameter.nominal,
        )


class GDTProperties:
    """Configuration properties for the GDT footprint generator.

    This mostly consists of:

        * metadata
        * body_properties - describe the "real" physical properties of the device
        * layout_properties - describe parameters used to draw the footprint
    """

    metadata: common_metadata.CommonMetadata
    body_properties: GDTBodyProperties
    layout_properties: GDTLayoutProperties
    fp_name: str

    def __init__(self, spec: SpecDict):
        self.fp_name = spec["fp_name"]

        self.metadata = common_metadata.CommonMetadata(spec)

        if spec["body_type"] == "smd_cylinder":
            self.body_properties = GDTBodyPropertiesSMDCylinder(spec["body_params"])
        elif spec["body_type"] == "tht_cylinder":
            self.body_properties = GDTBodyPropertiesTHTCylinder(spec["body_params"])
        else:
            raise ValueError(f"Unsupported body type: {spec['body_type']}")

        # Based on the layout type, we create the appropriate body properties
        if spec["layout_type"] == "smd_cross_body":
            if not isinstance(self.body_properties, GDTBodyPropertiesSMDCylinder):
                raise ValueError(
                    "Cross-body layout is only supported for SMD cylinder GDTs"
                )

            self.layout_properties = GDTCrossBodyLayoutProperties(
                self.body_properties, spec["layout_params"]
            )
        elif spec["layout_type"] == "tht_inline":
            if not isinstance(self.body_properties, GDTBodyPropertiesTHTCylinder):
                raise ValueError(
                    "Inline layout is only supported for THT cylinder GDTs"
                )

            # For THT inline, we don't have a specific layout properties class yet
            self.layout_properties = GDTLayoutPropertiesTHTInline(
                self.body_properties, spec["layout_params"]
            )
        else:
            raise ValueError(f"Unsupported layout type: {spec['layout_type']}")


def create_footprints(spec: BaseSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification (not used by this generator).
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
    num_fps_generated = 0
    for _, ids_specs in get_file_name_ids_specs(generator_name):
        for id, spec in ids_specs:
            generateFootprint(spec, id, generator_name)
            num_fps_generated += 1
    return num_fps_generated


def generateFootprint(spec: SpecDict, pkg_id: str, generator_name: str) -> None:
    fp_config = GDTProperties(spec)

    lib_name = spec["library"]

    fp_type = FootprintType.SMD

    if fp_config.layout_properties.is_tht:
        fp_type = FootprintType.THT

    # create the footprint
    kicad_mod = Footprint(fp_config.fp_name, fp_type)

    desc = [
        "Gas discharge tube",
        f"{fp_config.body_properties.num_pads}-electrode",
        "THT" if fp_config.layout_properties.is_tht else "SMD",
        fp_config.layout_properties.body_size_description,
    ]

    if fp_config.metadata.datasheet:
        desc.append(fp_config.metadata.datasheet)

    kicad_mod.description = ", ".join(desc)

    tags = ["GDT"] + fp_config.metadata.additional_tags
    kicad_mod.tags = tags

    if isinstance(fp_config.layout_properties, GDTCrossBodyLayoutProperties):
        layout_props = fp_config.layout_properties

        pad_sizes: list[Vector2D] = []

        pad_sizes.append(layout_props.end_pad_size)

        if layout_props.center_pad_size is not None:
            pad_sizes.append(layout_props.center_pad_size)

        pad_sizes.append(
            pad_sizes[0]
        )  # For all GDTs, the end pads are the same size

        num_pads = fp_config.body_properties.num_pads

        if layout_props.end_pad_center_spacing is not None:
            pad_pitch = layout_props.end_pad_center_spacing / (num_pads - 1)
        elif layout_props.end_pad_inner_spacing is not None:
            pad_pitch = (layout_props.end_pad_inner_spacing + pad_sizes[0].x) / (
                num_pads - 1
            )
        elif layout_props.end_pad_outer_spacing is not None:
            pad_pitch = (layout_props.end_pad_outer_spacing - pad_sizes[0].x) / (
                num_pads - 1
            )
        else:
            raise ValueError(
                "GDTs require an end pad center spacing or inner/outer spacing"
            )

        # Create the layout for the cross-body pads
        layout = CrossBodyPadLayout(
            global_config=GLOBAL_CONFIG,
            pad_size=pad_sizes,
            pitch=pad_pitch,
            pad_count=fp_config.body_properties.num_pads,
            body_size=layout_props.body_size,
            footprint_name=kicad_mod.name,
        )

        kicad_mod += layout
    elif isinstance(fp_config.layout_properties, GDTLayoutPropertiesTHTInline):
        layout_props = fp_config.layout_properties

        pad_proto = Pad(
            at=Vector2D(0, 0),
            type=Pad.TYPE_THT,
            shape=Pad.SHAPE_OVAL,
            size=layout_props.pad_size,
            drill=layout_props.pad_drill,
            round_radius_handler=GLOBAL_CONFIG.roundrect_radius_handler,
            layers=Pad.LAYERS_THT,
        )

        layout = ThtAxialLayout(
            global_config=GLOBAL_CONFIG,
            pad_prototype=pad_proto,
            num_pads=fp_config.body_properties.num_pads,
            pitch=layout_props.body_properties.lead_spacing.nominal,
            body_size=layout_props.body_size,
            has_pin1_arrow=False,
            total_length=layout_props.body_properties.total_length.nominal,
            lead_diameter=layout_props.body_properties.lead_diameter.nominal,
            shrink_fit_lead_courtyard=False,
            footprint_name=kicad_mod.name,
        )
        kicad_mod += layout
    else:
        raise NotImplementedError(
            f"Unsupported layout type: {type(fp_config.layout_properties)}"
        )

    kicad_mod.add_standard_3d_model_to_footprint(lib_name, kicad_mod.name)

    write_footprint(kicad_mod, lib_name, generator_name)
