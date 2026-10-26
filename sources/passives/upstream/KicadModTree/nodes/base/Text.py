# kilibs is free software: you can redistribute it and/or modify it under the terms of
# the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# kilibs is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with kilibs.
# If not, see < http://www.gnu.org/licenses/ >.
#
# (C) 2016 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>
# (C) The KiCad Librarian Team

"""Class definition for Text nodes."""

from __future__ import annotations

from typing import Self

from KicadModTree.nodes.Node import Node
from kilibs.geom import BoundingBox, Vec2DCompatible, Vector2D


class _TextBase(Node):
    """The base node of Text and Property."""

    def __init__(
        self,
        text: str,
        at: Vec2DCompatible,
        rotation: float = 0.0,
        mirror: bool = False,
        layer: str = "F.SilkS",
        size: Vec2DCompatible = [1, 1],
        thickness: float = 0.15,
        justify: str | None = None,
        hide: bool = False,
        unlocked: bool = False,
    ) -> None:
        """Initialize a text base node.

        Args:
            text: Content that is shown.
            at: Coordinates of the text.
            rotation: Rotation in degrees of the text field.
            mirror: Whether the text is mirrored or not.
            layer: On which layer the text is drawn.
            size: Size of the text.
            thickness: Thickness of the text.
            justify: Justification of the text (default: 'center').
            hide: `True` if the text shall be hidden.
            unlocked: `True` to disable keeping the text upright.

        Example:
            >>> from KicadModTree import *
            >>> Text(text='REF**', at=[0, -3], layer='F.SilkS')
            >>> Property(name='Value', text="footprint name", at=[0, 3], layer='F.Fab')
            >>> Text(text='test', at=[0, 0], layer='Cmts.User')
        """

        # Instance attributes:
        self.text: str
        """Content that is shown."""
        self.at: Vector2D
        """Coordinates of the text."""
        self.rotation: float
        """Rotation in degrees of the text field."""
        self.mirror: bool
        """Whether the text is mirrored or not."""
        self.layer: str
        """On which layer the text is drawn."""
        self.size: Vector2D
        """Size of the text."""
        self.thickness: float
        """Thickness of the text."""
        self.justify: str | None
        """Justification of the text (default: 'center')."""
        self.hide: bool
        """`True` if the text shall be hidden."""
        self.unlocked: bool
        """`True` to disable keeping the text upright."""

        Node.__init__(self)
        self.text = text
        self.at = Vector2D(at)
        self.rotation = rotation
        self.mirror = mirror
        self.layer = layer
        self.size = Vector2D(size)
        self.thickness = thickness
        self.justify = justify
        self.hide = hide
        self.unlocked = unlocked

    def rotate(
        self,
        angle: float,
        origin: Vector2D = Vector2D.zero(),
    ) -> Self:
        """Rotate text around a given origin.

        Args:
            angle: The rotation angle.
            origin: The origin point for the rotation.
        """
        self.at.rotate(angle=angle, origin=origin)
        # subtraction because kicad text field rotation is the wrong way round
        self.rotation -= angle
        return self

    def translate(self, vector: Vector2D) -> Self:
        """Move the text base.

        Args:
            vector: The direction and distance in mm.

        Returns:
            The translated text base.
        """
        self.at += vector
        return self

    def bbox(self) -> BoundingBox:
        """Return the bounding box of the text base."""
        width = len(self.text) * self.size.x
        height = self.size.x

        min_x = self.at.x - width / 2.0
        min_y = self.at.y - height / 2.0
        max_x = self.at.x + width / 2.0
        max_y = self.at.y + height / 2.0

        return BoundingBox.from_vector2d(
            min=Vector2D(min_x, min_y),
            max=Vector2D(max_x, max_y),
        )

    def __repr__(self) -> str:
        """A string representation of the text base node."""
        if self.justify:
            justify = f"justify={self.justify}"
        else:
            justify = ""
        return (
            f'text="{self.text}", '
            f"at={self.at}, "
            f"layer={self.layer}, "
            f"size={self.size}, "
            f"thickness={self.thickness}, "
            f"{justify}"
        )


class Text(_TextBase):
    """A text node.

    A non-field PCB_TEXT in the KiCad code, or gr_text etc in the s-exp."""

    def __init__(
        self,
        text: str,
        at: Vec2DCompatible,
        rotation: float = 0.0,
        mirror: bool = False,
        layer: str = "F.SilkS",
        size: Vec2DCompatible = [1, 1],
        thickness: float = 0.15,
        justify: str | None = None,
        hide: bool = False,
        unlocked: bool = False,
    ) -> None:
        """Initialize a text node.

        Args:
            text: Content that is shown.
            at: Coordinates of the text.
            rotation: Rotation in degrees of the text field.
            mirror: Whether the text is mirrored or not.
            layer: On which layer the text is drawn.
            size: Size of the text.
            thickness: Thickness of the text.
            justify: Justification of the text (default: 'center').
            hide: `True` if the text shall be hidden.
            unlocked: `True` to disable keeping the text upright.
        """
        super().__init__(
            text=text,
            at=at,
            rotation=rotation,
            mirror=mirror,
            layer=layer,
            size=size,
            thickness=thickness,
            justify=justify,
            hide=hide,
            unlocked=unlocked,
        )
        # Other gr_text/fp_text-specific members here
        # locked (as in can't be selected status) could go here, except
        # that it applies only to gr_text, not fp_text so we don't need it now.

    def __repr__(self) -> str:
        """A string representation of the text."""
        return f"Text({_TextBase.__repr__(self)})"


class Property(_TextBase):
    """A property node.

    A PCB_FIELD in the KiCad code, which is a subclass of PCB_TEXT. 'property' in the
    s-expr format.

    Note: this is not a derived class of Text, as Text could have members
    that don't apply to Property instances.
    """

    REFERENCE = "Reference"
    """Standard designator for references."""
    VALUE = "Value"
    """Standard designator for values."""
    DATASHEET = "Datasheet"
    """Standard designator for datasheets."""
    DESCRIPTION = "Description"
    """Standard designator for descriptions."""
    FOOTPRINT = "Footprint"
    """Standard designator for footprints."""

    def __init__(
        self,
        name: str,
        text: str,
        at: Vec2DCompatible,
        rotation: float = 0.0,
        mirror: bool = False,
        layer: str = "F.SilkS",
        size: Vec2DCompatible = [1, 1],
        thickness: float = 0.15,
        justify: str | None = None,
        hide: bool = False,
        unlocked: bool = False,
    ) -> None:
        """Initialize a property node.

        Args:
            text: Content that is shown.
            at: Coordinates of the text.
            rotation: Rotation in degrees of the text field.
            mirror: Whether the text is mirrored or not.
            layer: On which layer the text is drawn.
            size: Size of the text.
            thickness: Thickness of the text.
            justify: Justification of the text (default: 'center').
            hide: `True` if the text shall be hidden.
            unlocked: `True` to disable keeping the text upright.
        """

        # Instance attributes:
        self._name: str
        """The name of the property."""

        super().__init__(
            text=text,
            at=at,
            rotation=rotation,
            mirror=mirror,
            layer=layer,
            size=size,
            thickness=thickness,
            justify=justify,
            hide=hide,
            unlocked=unlocked,
        )
        # fields have canonical names
        self._name = name

    @property
    def name(self) -> str:
        """The name of the property."""
        return self._name

    def __repr__(self) -> str:
        """A string representation of the property."""
        return f"Property({_TextBase.__repr__(self)})"
