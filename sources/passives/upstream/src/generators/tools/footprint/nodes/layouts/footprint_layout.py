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

from collections.abc import Sequence
from enum import Enum
from typing import Generic, TypeVar, cast

from generators.tools.footprint import drawing_tools as DT
from generators.tools.footprint import footprint_text_fields
from KicadModTree import (
    ChamferedRectangle,
    ExposedPad,
    Pad,
    PadArray,
    Rectangle,
    ReferencedPad,
    RingPad,
    Shape,
    Translation,
)
from KicadModTree.util import courtyard_builder, shape_to_node
from kilibs.config import global_config as GC
from kilibs.geom import (
    BoundingBox,
    CornerSelection,
    GeomRectangle,
    GeomShapesClosed,
    Vector2D,
)
from kilibs.geom.operations import unite

Pads = Pad | ReferencedPad | PadArray | ExposedPad | RingPad
"""A union for all pad types."""
ShapeType = TypeVar("ShapeType", bound=GeomShapesClosed)
"""Type variable for the body shape of the FootprintLayout."""
PadType = TypeVar("PadType", bound=Pads)
"""Type variable for the pads of the FootprintLayout."""


class FabStyle(Enum):
    NONE = 0
    """Don't draw the fab outline."""
    BODY_SHAPE = 1
    """Draw the fab outline in the exact shape of the body."""
    CHAMFER_RECT = 2
    """Draw the fab outline in the shape of a chamfered rectangle."""


class SilkStyle(Enum):
    NONE = 0
    """No silkscreen is drawn."""
    TIGHT = 1
    """Silk is tight to the body but cut away by pad clearance rules."""
    TIGHT_IGNORE_KEEPOUTS = 2
    """Draws the silk outline tight to the body, completely ignoring pad clearance rules
    (fastest but potentially unsafe).
    """
    TIGHT_ENCAPSULATE_PADS = 3
    """Silk outlines both the component body and the pads, effectively encapsulating the
    entire footprint area.
    """
    RECTANGLE_KEEP_TOP_BOTTOM = 4
    """Rectangular silk that is generally tight, but ensures horizontal edges (top /
    bottom) are not trimmed by pads.
    """
    RECTANGLE_KEEP_ALL_SIDES = 5
    """Rectangular silk that is generally tight, but ensures all four edges are not
    trimmed by pads.
    """


class CourtyardStyle(Enum):
    NONE = 0
    """Don't draw the courtyard around the component."""
    TIGHT = 1
    """Draw the courtyard around the component outset from the body outline and pads."""
    RECTANGLE = 2
    """Independent of the body shape, draw the courtyard as a rectangle."""


class FootprintLayout(Translation, Generic[ShapeType, PadType]):
    """
    A FootprintLayoutNode is a node that draws the (main) layout of a footprint
    of a certain type. It is mainly used for devices which have "common"
    layouts, but can be used for any footprint. The main use is allowing many
    generators to share the geometry of the footprint, but drive them with
    different parameters as they need.

    They are usually driven in fairly generic terms (e.g. device 2x3mm, 4pins,
    pitch) etc, and detailed metadata is appended to the parent FP as siblings
    to this node.  In particular, layouts do not care what kind of device it is,
    they only care about the geometry of the footprint (so they are a graphical
    abstraction).

    If geometry needs to be derived from a complex calculation such as IPC
    formulae using various input parameters, it may be better to add a factory
    fuction that does this. For example, instead of the layout node taking "pin
    size" and "global config", the factory function distills it into "pad size"
    and "drill size", and the layout node doesn't need to know about IPC rules,
    it just takes pure geometry. The means it can be driven directly if needed,
    or by another factory function.

    On the other hand, driving silk/fab/courtyard line properties with global
    config is probably a good idea, as it saves a lot of repetition.

    This is distinct from Footprint, which is also a Node, but represents the
    entire footprint, including all other nodes and metadata.

    E.g.:

    - Footprint
       - FootprintLayoutNode (some subclass of)
          - Pad (created by the layout)
          - Line ....
          - Text
       - Model
       - Additional drawings
    """

    def __init__(
        self,
        global_config: GC.GlobalConfig,
        body_shape: ShapeType,
        pads: Sequence[PadType],
        translation_offset: Vector2D = Vector2D.zero(),
    ) -> None:
        """Create an instance of the FootprintLayout.

        Args:
            global_config: The global config.
            body_shape: The shape of the body.
            pads: The pads of the footprint.
            footprint_name: The name of the footprint. Used for automatic label
                placement.
            translation_offset: The translation offset by which all nodes inside the
                layout are translated. Defaults to zero = no translation.
        """

        # Instance attributes:
        self.global_config: GC.GlobalConfig
        """The global config."""
        self.body_shape: ShapeType
        """The body shape."""
        self.pads: Sequence[PadType]
        """The pads."""
        self.courtyard: Shape | None
        """The courtyard."""
        self.additional_silk_keepouts: list[GeomShapesClosed]
        """The silkscreen keepouts in addition to the keepouts of the pads. They are
        used for creating the automatic silk."""
        self._silk_keepouts_around_pads: list[GeomShapesClosed] | None
        """The cached silkscreen keepouts around the pads."""
        self._pads_bounding_box: BoundingBox | None
        """The cached bounding box of all pads."""
        self._uncut_silk_shape: ShapeType | GeomRectangle | None
        """The cached bounding box of the silk. Used only for silk styles
        `RECTANGLE_KEEP_TOP_BOTTOM` and `RECTANGLE_KEEP_ALL_SIDES`.
        """

        super().__init__(translation_offset)
        self.global_config = global_config
        self.body_shape = body_shape
        self.pads = pads
        self.courtyard = None
        self.additional_silk_keepouts = []
        self._silk_keepouts_around_pads = None
        self._pads_bounding_box = None
        self._uncut_silk_shape = None
        self.extend(self.pads)

    def _get_fab_bevel_corner(self, style: FabStyle) -> CornerSelection:
        """
        Get the corner selection for the fab bevel. This is used to draw the chamfered
        rectangle as component outline - if the fab style `CHAMFER_RECT` is selected.

        Normal Rotation A parts have this in the top left.
        """
        return CornerSelection({CornerSelection.TOP_LEFT: True})

    def _get_silk_clearance(self) -> float | Vector2D:
        """
        Get the additional silk clearance. Only in combination with the silk styles
        `RECT_KEEP_TOP_BOTTOM` and `FULL_RECT` the values for x- and y- may differ.
        """
        return 0.0

    def _get_fab_ref_y_pos(self) -> float | str:
        """
        Get the y position of the reference designator. This is used to place
        the reference designator in the footprint.

        Returns:
            "top", "bottom", "center", or an explicit position.
        """
        return "center"

    def _get_courtyard_offset_pads(self) -> float | GC.GlobalConfig.CourtyardType:
        """
        Get the courtyard offset for the pads. This is used to generate the
        courtyard rect.
        """
        return GC.GlobalConfig.CourtyardType.DEFAULT

    def _get_courtyard_offset_body(self) -> float | GC.GlobalConfig.CourtyardType:
        """
        Get the courtyard offset from the body. This is used to generate the
        courtyard rect.
        """
        return GC.GlobalConfig.CourtyardType.DEFAULT

    def _get_silk_keepouts_around_pads(self) -> list[GeomShapesClosed]:
        """Get the silk screen keepouts around the pads."""
        if self._silk_keepouts_around_pads is None:
            self._silk_keepouts_around_pads = []
            inflation = self.global_config.silk_pad_offset
            for pad in self.pads:
                if (shape := pad.as_geom_shape(inflation)) is not None:
                    self._silk_keepouts_around_pads.append(shape)
        return self._silk_keepouts_around_pads

    def _get_pads_bounding_box(self) -> BoundingBox:
        """Get the bounding box encompassing all pads."""
        if self._pads_bounding_box is None:
            self._pads_bounding_box = BoundingBox()
            for pad in self.pads:
                self._pads_bounding_box.include_bbox(pad.bbox())
        return self._pads_bounding_box

    def _get_uncut_silk_shape(self, silk_style: SilkStyle) -> ShapeType | GeomRectangle:
        """Get the silk shape before it is cut by the keepouts."""
        if self._uncut_silk_shape is None:
            if silk_style in (
                SilkStyle.RECTANGLE_KEEP_ALL_SIDES,
                SilkStyle.RECTANGLE_KEEP_TOP_BOTTOM,
            ):
                clearance = (
                    self._get_silk_clearance() + self.global_config.silk_fab_offset
                )
                silk_bbox = self.body_shape.bbox().copy().inflate_anisotropic(clearance)
                pad_bbox = BoundingBox()
                for silk_keepout in self._get_silk_keepouts_around_pads():
                    pad_bbox.include_bbox(silk_keepout.bbox())
                if silk_style is SilkStyle.RECTANGLE_KEEP_ALL_SIDES:
                    silk_bbox.include_bbox(pad_bbox)
                else:
                    assert silk_bbox.min is not None and silk_bbox.max is not None
                    silk_bbox.min.y = min(pad_bbox.top, silk_bbox.top)
                    silk_bbox.max.y = max(pad_bbox.bottom, silk_bbox.bottom)
                self._uncut_silk_shape = GeomRectangle(shape=silk_bbox)

            else:  # silk_style in (TIGHT, TIGHT_IGNORE_KEEPOUTS, TIGHT_ENCAPSULATE_PADS):
                clearance = (
                    self._get_silk_clearance() + self.global_config.silk_fab_offset
                )
                if isinstance(clearance, Vector2D):
                    if not clearance.x_y_equal:
                        if not isinstance(self.body_shape, GeomRectangle):
                            raise ValueError(
                                "If silk clearance is anisotropic the body must be of "
                                "rectangular shape!"
                            )
                        else:
                            self._uncut_silk_shape = self.body_shape.copy()
                            self._uncut_silk_shape.size += 2 * clearance
                    else:
                        self._uncut_silk_shape = cast(
                            ShapeType | GeomRectangle,
                            self.body_shape.inflated(clearance.x),
                        )
                else:
                    self._uncut_silk_shape = cast(
                        ShapeType | GeomRectangle, self.body_shape.inflated(clearance)
                    )
        return self._uncut_silk_shape

    def _courtyard_to_mm(self, offset: float | GC.GlobalConfig.CourtyardType) -> float:
        """Resolve the courtyard offset as an absolute value in mm."""
        if isinstance(offset, GC.GlobalConfig.CourtyardType):
            return self.global_config.get_courtyard_offset(offset)
        return offset

    def _add_automatic_fab_outline(self, style: FabStyle) -> None:
        """Add the fab outline in the given style to the layout."""
        match style:
            case FabStyle.NONE:
                pass

            case FabStyle.BODY_SHAPE:
                self += shape_to_node(
                    shape=cast(GeomShapesClosed, self.body_shape),
                    layer="F.Fab",
                    width=self.global_config.fab_line_width,
                )

            case FabStyle.CHAMFER_RECT:
                # whatever the body shape is, we are asked to draw a chamfered rectangle
                body_bbox = self.body_shape.bbox()
                self += ChamferedRectangle(
                    center=body_bbox.center,
                    size=body_bbox.size,
                    chamfer=self.global_config.fab_bevel,
                    corners=self._get_fab_bevel_corner(style),
                    layer="F.Fab",
                    width=self.global_config.fab_line_width,
                )

    def _add_automatic_silk_outline(self, style: SilkStyle) -> None:
        """Add the silk outline in the given style to the layout."""
        if style is SilkStyle.NONE:
            return

        silk_shapes: list[GeomShapesClosed] = [self._get_uncut_silk_shape(style)]

        if style in (SilkStyle.TIGHT, SilkStyle.RECTANGLE_KEEP_TOP_BOTTOM):
            kos = self._get_silk_keepouts_around_pads() + self.additional_silk_keepouts

        elif style is SilkStyle.TIGHT_ENCAPSULATE_PADS:
            silk_shape = silk_shapes[0]
            silk_shapes = []
            kos = self.additional_silk_keepouts
            for ko in self._get_silk_keepouts_around_pads():
                united_shapes = unite(silk_shape, ko)
                if len(united_shapes) == 1:
                    silk_shape = united_shapes[0]
                else:
                    silk_shapes.append(ko)
            silk_shapes.append(silk_shape)

        else:  # if style in (TIGHT_IGNORE_KEEPOUTS, RECTANGLE_KEEP_ALL_SIDES):
            kos = []

        silk_nodes = DT.makeNodesWithKeepout(
            geom_items=silk_shapes,
            layer="F.SilkS",
            keepouts=kos,
            width=self.global_config.silk_line_width,
        )
        self += silk_nodes

    def _add_automatic_courtyard(self, style: CourtyardStyle) -> None:
        """Add the courtyard in the given style to the layout.

        This method stores the courtyard in the instance attribute `courtyard` (so it
        can be used by other methods like `_add_automatic_labels()`) and adds it to the
        layout.

        Args:
            style: The courtyard style.
        """
        if style is CourtyardStyle.NONE:
            return

        offset_fab = self._courtyard_to_mm(self._get_courtyard_offset_body())
        offset_pads = self._courtyard_to_mm(self._get_courtyard_offset_pads())
        if style is CourtyardStyle.TIGHT:
            courtyard = courtyard_builder.CourtyardBuilder.from_node(
                node=self.pads,
                global_config=self.global_config,
                offset_fab=offset_fab,
                offset_pads=offset_pads,
                outline=self.body_shape,
            ).node

        else:  # if style is CourtyardStyle.RECTANGLE:
            bbox_courtyard = self._get_pads_bounding_box().copy().inflate(offset_pads)
            bbox_courtyard.include_bbox(self.body_shape.bbox().inflate(offset_fab))
            courtyard = Rectangle(layer="F.CrtYd", shape=bbox_courtyard)
            courtyard.round_to_grid(self.global_config.courtyard_grid, outwards=True)

        self.courtyard = courtyard
        self.append(self.courtyard)

    def _add_automatic_labels(self, footprint_name: str) -> None:
        """Add the default labels to the layout.

        Args:
            footprint_name: The name of the footprint.

        Note:
            Before calling this method the instance attribute `courtyard` must be
            created (either via `add_automatic_courtyard()` or manually with
            `self.courtyard = ...`).
        """
        assert self.courtyard, "Create the courtyard first."
        footprint_text_fields.addTextFields(  # pyright: ignore
            self,
            configuration=self.global_config,
            body_edges=self.body_shape.bbox(),
            courtyard=self.courtyard.bbox(),
            fp_name=footprint_name,
            text_y_inside_position=self._get_fab_ref_y_pos(),
            allow_rotation=True,
        )
