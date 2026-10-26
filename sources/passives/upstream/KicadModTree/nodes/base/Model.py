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

"""Class definition a 3D model."""

from __future__ import annotations

from KicadModTree.nodes.Node import Node
from kilibs.geom import Vec3DCompatible, Vector3D


class Model(Node):
    """A model."""

    filename: str
    """The filename of the model."""
    at: Vector3D
    """The coordinates of the center of the model in mm."""
    scale: Vector3D
    """The scale of the model in x-, y-, and z-direction."""
    rotation: Vector3D
    """The rotation of the model around the x-, y-, and z-axis in degrees."""

    def __init__(
        self,
        filename: str,
        at: Vec3DCompatible = [0, 0, 0],
        scale: Vec3DCompatible = [1, 1, 1],
        rotate: Vec3DCompatible = [0, 0, 0],
    ) -> None:
        """Create a 3D model node.

        Args:
            filename: Name of the 3D model file (including path).
            at: Offset position of the model in mm.
            scale: Scale of the model.
            rotate: Rotation of the model in degrees.

        Example:
            >>> from KicadModTree import *
            >>> Model(filename="example.3dshapes/example_footprint.wrl",
            ...       at=[0, 0, 0], scale=[1, 1, 1], rotate=[0, 0, 0])
        """
        Node.__init__(self)
        self.filename = filename
        self.at = Vector3D(at)
        self.scale = Vector3D(scale)
        self.rotation = Vector3D(rotate)

    def __repr__(self) -> str:
        return (
            f'Model(filename: "{self.filename}"'
            f"at={self.at}, "
            f"scale={self.scale}, "
            f"rotate={self.rotation}, "
        )
