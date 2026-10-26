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
# modifications 2022 by Armin Schoisswohl (@armin.sch)
# (C) The KiCad Librarian Team

"""Class definition for the base node."""

from __future__ import annotations

import copy
import uuid
from abc import ABC
from collections.abc import Sequence
from enum import Enum
from hashlib import sha1
from traceback import print_stack
from typing import TYPE_CHECKING, Any, Protocol, Self, runtime_checkable

from _hashlib import HASH

from kilibs.geom import BoundingBox, Vector2D, Vector3D

if TYPE_CHECKING:
    from .Container import Container


@runtime_checkable
class _HasCallableHashDict(Protocol):
    def hashdict(self) -> str: ...


class TStamp(object):
    """A timestamp."""

    def __init__(
        self,
        tstamp: uuid.UUID | str | None = None,
        tstamp_seed: uuid.UUID | None = None,
        parent: Node | None = None,
        unique_id: str | None = None,
    ) -> None:
        """Create a timestamp.

        Args:
            tstamp: The optional value of the timestamp.
            tstamp_seed: The optional seed of the timestamp.
            parent: The optional parent Node of the timestamp.
            unique_id: The optinoal UUID.
        """

        # Instance attributes:
        self._tstamp: uuid.UUID | str | None
        """The timestamp."""
        self._tstamp_seed: uuid.UUID | None
        """The timestamp seed."""
        self._unique_id: str | None
        """The unique ID."""
        self._isTStampManualFixed: bool
        """`True` if the timestamp is manually fixed."""
        self._parentNode: Node | None
        """The parent node."""

        if tstamp is not None:
            tstamp = self.parse_as_uuid(tstamp)
        self._tstamp = tstamp

        if tstamp_seed is not None:
            tstamp_seed = self.parse_as_uuid(tstamp_seed)
        self._tstamp_seed = tstamp_seed

        fixed = (tstamp is not None) and (tstamp_seed is None)
        self._isTStampManualFixed = fixed

        if unique_id is not None:
            unique_id = str(unique_id)
        self._unique_id = unique_id

        self._parentNode = parent

    @staticmethod
    def parse_as_uuid(tstamp_uuid: str | uuid.UUID) -> uuid.UUID:
        """Convert the argument to a UUID.

        Args:
            tstamp_uuid: The argument to convert.

        Returns:
            The UUID.
        """
        if isinstance(tstamp_uuid, uuid.UUID):
            return tstamp_uuid
        else:
            return uuid.UUID(str(tstamp_uuid))

    @staticmethod
    def parse_timestamp(tstamp: TStamp | str) -> TStamp:
        """Convert the argument to a timestamp.

        Args:
            tstamp_uuid: The argument to convert.

        Returns:
            The timestamp.
        """
        if isinstance(tstamp, TStamp):
            return tstamp
        else:
            return TStamp(tstamp=TStamp.parse_as_uuid(tstamp))

    def set_unique_id(self, unique_id: uuid.UUID) -> None:
        """Set the UUID.

        Args:
            unique_id: The UUID.
        """
        self._unique_id = str(unique_id)
        self.update_timestamp_conditionally()

    def unset_timestamp(self) -> None:
        """Unset the timestamp."""
        self._tstamp = None
        self._tstamp_seed = None
        self._unique_id = None
        self._isTStampManualFixed = False

    def set_parent_node(self, node: Node) -> None:
        """Set the parent node.

        Args:
            node: The parent node.
        """
        self._parentNode = node

    def get_parent_node(self) -> Node | None:
        """Return the parent node."""
        return self._parentNode

    def is_timestamp_valid(self) -> bool:
        """Return if the timestamp is valid or not."""
        return (self._tstamp is not None) and (self._tstamp != "")

    def is_timestamp_seed_valid(self) -> bool:
        """Return if the timestamp seed is valid or not."""
        return (self._tstamp_seed is not None) and (self._tstamp_seed != "")

    def get_unique_id(self) -> str | None:
        """Return the UUID."""
        return self._unique_id

    def get_timestamp(self) -> uuid.UUID | str | None:
        """Return the timestamp."""
        return self._tstamp

    def set_timestamp(self, tstamp: uuid.UUID | str, tstamp_fixed: bool = True) -> None:
        """ "Set the timestamp.

        Args:
            tsamp: The timestamp.
            tsamp_fixed: `True` if the timestamp shall be considered to be manually
                fixed, i.e. it will not be changed when updating the timestamp."""
        self._tstamp = uuid.UUID(str(tstamp))
        self._isTStampManualFixed = tstamp_fixed

    def return_derived_timestamp(
        self,
        unique_id: str | None = None,
        obj: object | None = None,
        seed: uuid.UUID | None = None,
        use_obj_hash: bool = True,
        hash_using_dict: bool = True,
    ) -> uuid.UUID:
        """Derive a timestamp from one of the given arguments.

        Args:
            unique_id: Optional UUID that is used hashed and used as seed to generate
                a new UUID.
            obj: An optional object whose class name is used as seed to generate a new
                UUID. If `use_obj_hash` is `True` its object dictionary is also used as
                seed.
            seed: An optional UUID that is used as a seed to generate a new UUID.
            use_obj_hash: See description of `hash_using_dict`.
            hash_using_dict: If `use_obj_hash` is `True` and an object is passed as
                argument `obj`, the UUID is derived from the SHA-1 hash of the string
                representation of the object (__repr__(obj)) if `has_using_dict` is
                `True`, otherwise it is derived from the hash value of the object
                itself.
        """
        if use_obj_hash:
            if obj is not None:
                d: str | dict[str, Any]
                if isinstance(obj, _HasCallableHashDict):
                    d = obj.hashdict()
                else:
                    # consider using hash_str = sha1( str(obj.__hash__()).encode('utf-8') ).hexdigest()
                    d = Node.cleanup_to_hash_dict(obj.__dict__)
                hash_str = (
                    sha1(repr(d).encode("utf-8")).hexdigest()
                    if hash_using_dict
                    else hash(obj)
                )
            else:
                hash_str = "None"
        else:
            hash_str = "*"
        if seed is None:
            seed = self._tstamp_seed
        if seed is not None:
            return uuid.uuid5(
                namespace=seed,
                name=f"KicadModTree.Node.{str(obj.__class__.__name__)}.{str(unique_id)}.{str(hash_str)}",
            )
        else:
            raise RuntimeError(
                f"Timestamp of node {repr(self._parentNode)} was not initialized before requesting it."
            )

    def recalculate_timestamp(self) -> uuid.UUID | str | None:
        """If the timestamp is not manually fixed, update the timestamp by using the
        parent node as object to derive the timestamp from (see:
        `returnDerivedTStamp()`)."""
        if not self._isTStampManualFixed:
            self._tstamp = self.return_derived_timestamp(
                unique_id=self.get_unique_id(),
                obj=self._parentNode,
                seed=self.get_timestamp_seed(),
                use_obj_hash=True,
            )
        else:
            print("WARNING: TStamp is fixed at:")
            print_stack()
        return self.get_timestamp()

    def get_timestamp_seed(self) -> uuid.UUID | None:
        """Return the timestamp seed."""
        return self._tstamp_seed

    def initialize_timestamp_seed(self) -> uuid.UUID | None:
        """Initialize the timestamp seed and return it."""
        self.set_timestamp_seed(
            uuid.uuid5(
                namespace=uuid.uuid1(),
                name=f"KicadModTree.Node.{str(self.__class__.__name__)}.{str(self._unique_id)}",
            )
        )
        return self.get_timestamp_seed()

    def update_timestamp_conditionally(self) -> uuid.UUID | str | None:
        """Update the timestamp if it is not manually fixed and return it."""
        if (self._tstamp is None) or (not self._isTStampManualFixed):
            return self.recalculate_timestamp()
        else:
            return self.get_timestamp()

    def set_timestamp_seed(self, tstamp_seed: uuid.UUID | str | None) -> None:
        """Set the timestamp seed."""
        self._tstamp_seed = uuid.UUID(str(tstamp_seed))
        if tstamp_seed is not None:
            self.update_timestamp_conditionally()

    def __str__(self) -> str:
        """Return the timestamp as a string."""
        return str(self.get_timestamp())

    def __repr__(self) -> str:
        """Return the string representation of the timestamp."""
        return (
            f"TStamp(tstamp='{str(self.get_timestamp())}', "
            + f"tstamp_seed='{self.get_timestamp_seed()}', unique_id='{self.get_unique_id()}')"
        )


class Node(ABC):
    """The abstract base node."""

    def __init__(self) -> None:
        """Create a node."""

        # Instance attributes:
        self._parent: Container[Node] | None
        """The parent node."""
        self._tstamp: TStamp
        """The timestamp."""

        self._parent = None
        self._tstamp = TStamp(parent=self)

    def has_valid_timestamp(self) -> bool:
        """Return whether the node has a valid timestamp or not."""
        return self._tstamp.is_timestamp_valid()

    def has_valid_seed_for_timestamp(self) -> bool:
        """Return whether the node has a valid timestamp seed or not."""
        return self._tstamp.is_timestamp_seed_valid()

    def set_timestamp_seed_from_node(self, node: Node) -> None:
        """Sets the timestamp by using the nodes' timestamps' seed."""
        if node.get_timestamp_class().get_timestamp_seed() is not None:
            return self._tstamp.set_timestamp_seed(
                node.get_timestamp_class().get_timestamp_seed()
            )
        else:
            return None

    def get_timestamp_class(self) -> TStamp:
        """Return the timestamp object (class) of the node."""
        return self._tstamp

    def set_timestamp(self, tstamp: uuid.UUID | str | TStamp) -> None:
        """Return the timestamp UUID of the node."""
        if isinstance(tstamp, TStamp):
            self._tstamp = tstamp
        else:
            self._tstamp.set_timestamp(tstamp)

    def get_timestamp(self) -> uuid.UUID | str | None:
        """Return the timestamp of the node."""
        return self._tstamp.get_timestamp()

    @staticmethod
    def cleanup_to_hash_dict(obj_dict: dict[str, Any]) -> dict[str, Any]:
        """Clean up the object dictionary passed as argument for the purpose of hashing
        it and using it to derive a UUID or timestamp from.

        Args:
            obj_dict: The object dictionary.

        Returns:
            The cleaned up object dictionary.
        """
        hash_dict: dict[str, Any] = {}
        if "polygon_nodes_raw" in obj_dict.keys():
            pass
        for k, v in obj_dict.items():
            if k in ["_parent", "_tstamp"]:
                continue
            if hasattr(v, "_deterministic_hash"):
                v = v._deterministic_hash()
            elif isinstance(v, _HasCallableHashDict):
                v = v.hashdict()
            elif (
                isinstance(v, str)
                or isinstance(v, int)
                or isinstance(v, float)
                or isinstance(v, Vector2D)
                or isinstance(v, Vector3D)
                or isinstance(v, TStamp)
                or isinstance(v, Enum)
            ):
                v = str(v)
            else:
                # complex types may contain objects that would return hashes based
                # on run-time memory locations, which are unstable, skip
                v = "[...]"
            hash_dict[k] = v
        return hash_dict

    def hashdict(self) -> dict[str, Any]:
        """Clean up this node's dictionary for the purpose of hashing it and return it."""
        hash_dict = self.cleanup_to_hash_dict(self.__dict__)
        return hash_dict

    def _deterministic_hash(self) -> HASH:
        """Return a deterministic SHA1 hash of this object."""
        return sha1(repr(self.hashdict()).encode("utf-8"))

    def __hash__(self) -> int:
        """Return this object's SHA1 hash as an integer."""
        return int.from_bytes(self._deterministic_hash().digest(), byteorder="little")

    def copy(self) -> Self:
        """Create a copy of itself."""
        copied_node = copy.copy(self)
        copied_node._parent = None
        return copied_node

    def translate(self, vector: Vector2D) -> Self:
        """Move the node.

        Args:
            vector: The distance in mm in the x- and y-direction.

        Returns:
            The translated node.
        """
        # Note: nodes that need this functionality need to implement this method.
        return self

    def translated(self, vector: Vector2D) -> Self:
        """Create a copy of the node and move it.

        Args:
            vector: The distance in mm in the x- and y-direction.

        Returns:
            The translated copy of the node.
        """
        return self.copy().translate(vector)

    def rotate(
        self,
        angle: float,
        origin: Vector2D = Vector2D.zero(),
    ) -> Self:
        """Rotate the node around a given point.

        Args:
            angle: Rotation angle in degrees.
            origin: Coordinates (in mm) of the point around which to rotate.

        Returns:
            The rotated node.
        """
        # Note: nodes that need this functionality need to implement this method.
        return self

    def rotated(
        self,
        angle: float,
        origin: Vector2D = Vector2D.zero(),
    ) -> Self:
        """Create a copy of the node and rotate it around a given point.

        Args:
            angle: Rotation angle in degrees.
            origin: Coordinates (in mm) of the point around which to rotate.

        Returns:
            The rotated copy of the node.
        """
        return self.copy().rotate(angle=angle, origin=origin)

    @property  # Read-only via getter-only.
    def root(self) -> Node:
        """Return the root node of this node."""

        # TODO: recursion detection
        if not self._parent:
            return self
        else:
            return self._parent.root

    @property  # Read-only via getter-only.
    def parent(self) -> Container[Node] | None:
        """Return the parent node of this node."""
        return self._parent

    def flatten(self) -> Sequence[Node]:
        """Recursively retrieve a flat sequence of resolved, transform-applied
        primitives.

        This method traverses the node hierarchy to:

        1. Collect all leaf nodes (or self, if atomic).
        2. Decompose composite nodes into their primitive components.
        3. Apply any active transformations (e.g., :py:class:`Translation`) to the
           geometry.

        Returns:
            A flat list of atomic nodes ready for serialization.
            Note: Transformed nodes are returned as new instances (copies).
        """
        return [self]

    def bbox(self) -> BoundingBox:
        """
        Get the bounding box of the node. This is in its own context, so it is
        independent of the parent nodes' transformation, but does incldue any
        transformation it applies itself.

        Example:
            >>> translation_node = Translation(-10, 0)
            >>> line = Line(start=(0, 0), end=(1, 1))
            >>> translation.append(line)
            >>> bbox = line.bbox()
            >>> print(bbox.min, bbox.max)
                Vector2D(0, 0), Vector2D(1, 1)
            >>> line.translate(Vector2D(10, 0))
            >>> bbox = line.bbox()
            >>> print(bbox.min, bbox.max)
                Vector2D(10, 0), Vector2D(11, 1)
        """
        return BoundingBox()

    def __repr__(self) -> str:
        """The string representation of the Node."""
        class_name = self.__class__.__name__
        return f"{class_name}(parent={self._parent})"
