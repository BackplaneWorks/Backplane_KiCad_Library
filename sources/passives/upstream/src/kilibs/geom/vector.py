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
# (C) The KiCad Librarian Team

"""Classes for 2D and 3D vectors."""

from __future__ import annotations, division

from builtins import round
from collections.abc import Generator, Sequence
from math import atan2, cos, degrees, hypot, radians, sin

from kilibs.geom.tolerances import TOL_MM


class Vector2D:
    """A 2D vector."""

    def __init__(
        self,
        coordinates: Vec2DCompatible | float | int,
        y: float | int | None = None,
    ):
        """Representation of a 2D Vector in space.

        Args:
            coordinates: Either x- and y-coordinates of the point, if the second
                parameter is also used, just the x-coordinate. If x is a float and y is
                `None`, then the vector is constructed with y equal to x.
            y: y-coordinate of the point.

        Example:
            >>> from KicadModTree import *
            >>> Vector2D(0, 0)
            >>> Vector2D([0, 0])
            >>> Vector2D((0, 0))
            >>> Vector2D({'x': 0, 'y':0})
            >>> Vector2D(Vector2D(0, 0))
        """

        # Instance attributes:
        self.x: float
        """The x-coordinate."""
        self.y: float
        """The y-coordinate."""

        # parse constructor
        if isinstance(coordinates, float | int):
            self.x = float(coordinates)
            if y is not None:
                self.y = float(y)
            else:
                self.y = self.x
        elif isinstance(coordinates, Vector2D):
            self.x = coordinates.x
            self.y = coordinates.y
        elif isinstance(coordinates, Sequence):
            self.x = float(coordinates[0])
            self.y = float(coordinates[1])
        else:  # isinstance(coordinates, dict):
            # parse vectors with format: Vector2D({'x':0, 'y':0})
            self.x = float(coordinates.get("x", 0.0))
            self.y = float(coordinates.get("y", 0.0))

    @classmethod
    def from_floats(cls, x: float, y: float) -> Vector2D:
        """Create a vector from two floats without type checks. This initialization
        method is significantly faster than the one using the generic constructor.

        Args:
            x: x-coordinate of the point.
            y: y-coordinate of the point.

        Example:
            >>> from KicadModTree import *
            >>> vector = Vector2D.from_floats(0.0, 0.0)
        """
        vec = Vector2D.__new__(Vector2D)
        vec.x = x
        vec.y = y
        return vec

    @classmethod
    def zero(cls) -> Vector2D:
        """Create a zero-vector."""
        vec = Vector2D.__new__(Vector2D)
        vec.x = 0.0
        vec.y = 0.0
        return vec

    @classmethod
    def from_homogeneous(cls, source: Vector3D) -> Vector2D:
        r"""Return a 2D vector from its homogeneous representation.

        $\textrm{homogeneous}^{-1}(\mathbf{v})=(x/z, y/z)$

        :params:
            source: 3D homogeneous representation.
        """
        return Vector2D.from_floats(source.x / source.z, source.y / source.z)

    @classmethod
    def from_polar(
        cls,
        radius: float,
        angle: float,
        origin: Vec2DCompatible = (0, 0),
    ) -> Vector2D:
        """Generate a vector from a polar representation.

        Args:
            radius: The length of the vector.
            angle: The angle of the vector in degrees.
            origin: The origin point for the polar conversion.
        """
        angle = radians(angle)
        x = radius * cos(angle)
        y = radius * sin(angle)
        return Vector2D.from_floats(x, y) + Vector2D(origin)

    def copy(self) -> Vector2D:
        """Create a copy of the vector."""
        vec = Vector2D.__new__(Vector2D)
        vec.x = self.x
        vec.y = self.y
        return vec

    def round_to(self, base: float) -> Vector2D:
        """Round to a specific base (like it's required for a grid).

        Args:
            base: The base we want to round to (e.g. 0.05).

        Returns:
            A new instance of the vector that is rounded to the grid.
        """
        if not base:
            return self.__copy__()

        return self.__class__([round(v / base) * base for v in self])

    def distance_to(self, point: Vec2DCompatible) -> float:
        """Distance between this and another point.

        Args:
            point: The other point.

        Returns:
            The distance between self and the other point.
        """
        point = Vector2D(point)
        return hypot(point.x - self.x, point.y - self.y)

    def is_equal(self, point: Vector2D, tol: float = TOL_MM) -> bool:
        """Check if two points are close to each other.

        Args:
            point: The other point.
            tol: The maximum distance between the points that is tolerated to still
                qualify them as being close to each other.

        Returns:
            `True` if the points are close, `False` otherwise.
        """
        if abs(self.x - point.x) > tol or abs(self.y - point.y) > tol:
            return False
        return True

    def positive(self) -> Vector2D:
        """Return the vector with x=abs(x) and y=abs(y)."""
        self.x = abs(self.x)
        self.y = abs(self.y)
        return self

    def min(self, other: Vector2D) -> Vector2D:
        """Return the value of the smallest coordinate."""
        return Vector2D(*[min(*v) for v in zip(self, other)])

    def max(self, other: Vector2D) -> Vector2D:
        """Return the value of the largest coordinate."""
        return Vector2D(*[max(*v) for v in zip(self, other)])

    def to_dict(self) -> dict[str, float]:
        """Return a dictionary containing the coordinates."""
        return {"x": self.x, "y": self.y}

    def translate(
        self,
        vector: Vec2DCompatible | None = None,
        x: float | None = None,
        y: float | None = None,
    ) -> Vector2D:
        """Move the vector.

        Args:
            vector: The direction and distance in mm.
            x: The distance in mm in the x-direction.
            y: The distance in mm in the y-direction.

        Returns:
            The translated line.
        """
        if vector is not None:
            vector = Vector2D(vector)
        elif x is not None or y is not None:
            vector = Vector2D(x if x else 0, y if y else 0)
        else:
            raise KeyError("Either 'x', 'y', or 'vector' must be provided.")
        self.x += vector.x
        self.y += vector.y
        return self

    def rotate(
        self,
        angle: float,
        origin: Vector2D,
    ) -> Vector2D:
        """Rotate the point around a given point.

        Args:
            angle: Rotation angle in degrees.
            origin: Coordinates (in mm) of the point around which to rotate.

        Returns:
            The rotated point.
        """
        angle = radians(angle)
        cosa = cos(angle)
        sina = sin(angle)
        xo = self.x - origin.x
        yo = self.y - origin.y
        self.x = origin.x + cosa * xo - sina * yo
        self.y = origin.y + sina * xo + cosa * yo
        return self

    def rotated(
        self,
        angle: float,
        origin: Vector2D,
    ) -> Vector2D:
        """Create a copy of itself and rotate it.

        Args:
            angle: Rotation angle in degrees.
            origin: Coordinates (in mm) of the point around which to rotate.

        Returns:
            The rotated copy of the vector.
        """
        new_vec = self.copy()
        new_vec.rotate(angle, origin)
        return new_vec

    def to_polar(
        self,
        origin: Vec2DCompatible = (0, 0),
    ) -> tuple[float, float]:
        """Get polar representation of the vector.

        Args:
            origin: The origin point for the polar conversion.

        Returns:
            A tuple containing (radius, angle) with the polar representation. The angle
            is in the range of (-180°, 180°].
        """
        op = Vector2D(origin)
        diff = self - op
        radius = diff.norm()
        angle = diff.arg()
        return (radius, angle)

    def norm(self) -> float:
        """Calculate the length (cartesian norm) of the vector."""
        return hypot(*self)

    def arg(self) -> float:
        """Calculate the angle of the vector with respect to the origin (0, 0).

        Returns:
            The Angle of the vector in degrees in the range of (-180°, 180°].
        """
        return degrees(atan2(self.y, self.x))

    def dot_product(self, other: Vector2D) -> float:
        r"""Calculate the inner product of this vector with another vector:

        $\mathbf{a}\cdot\mathbf{b}=\|\mathbf{a}\|\cdot\|\mathbf{b}\|\cdot\cos{\theta}$

        Args:
            other: The other vector.

        Returns:
            The dot product.
        """
        return self.x * other.x + self.y * other.y

    def cross_product(self, other: Vector2D) -> Vector3D:
        r"""Calculate the cross product of this vector with another vector:

        $\mathbf{a}\times\mathbf{b}=\|\mathbf{a}\|\cdot\|\mathbf{b}\|\cdot\sin\theta\cdot\mathbf{n}$

        Args:
            other: The other vector.

        Returns:
            The cross product.
        """
        return Vector3D(0, 0, self.x * other.y - self.y * other.x)

    def orthogonal(self) -> Vector2D:
        """Return the vector orthogonal to itself. In the left-handed coordinate system
        (the one used for layouts) this corresponds to a clockwise rotation by 90°.
        """
        return Vector2D.from_floats(-self.y, self.x)

    def is_nullvec(self, tol: float = TOL_MM) -> bool:
        """Check if the vector is equal to the null-vector.

        Args:
            tol: Manhattan distance that the vector is allowed to be away from (0, 0)
                and still be considered equal to (0, 0).

        Returns:
            `True` if the vector is a null-vector, `False` otherwise.
        """
        if abs(self.x) > tol or abs(self.y) > tol:
            return False
        return True

    def normalize(self, tol: float = TOL_MM) -> Vector2D:
        """Normalize the vector (scale it to unit length).

        Args:
            tol: To prevent a division by zero, if the vector is shorter than `tol`,
                then a `ZeroDivisionError` is raised.

        Returns:
            The normalized vector.

        Raises:
            `ZeroDivisionError`: If the length of the vector is shorter than `tol`.
        """
        norm = self.norm()
        if norm > tol:
            self.x /= norm
            self.y /= norm
        else:
            raise ZeroDivisionError("Cannot normalize vector.")
        return self

    def resize(self, new_len: float, tol: float = TOL_MM) -> Vector2D:
        """Resize the vector to a new length in the same direction.

        Args:
            tol: To prevent a division by zero, if the vector is shorter than `tol`,
                then the vector is not resized.

        Returns:
            The resized vector.

        Raises:
            `ZeroDivisionError`: If the length of the vector is shorter than `tol`.
        """
        norm = hypot(*self)
        if norm < tol:
            raise ZeroDivisionError("Cannot resize null vector.")
        ratio = new_len / norm
        self *= ratio
        return self

    def to_homogeneous(self) -> Vector3D:
        r"""Get homogeneous representation of the vector.

        $\textrm{homogeneous}(\mathbf{v})=(x, y, 1)$
        """
        return Vector3D(self.x, self.y, 1)

    @property
    def min_val(self) -> float:
        """Get the value of the smallest coordinate."""
        return min(self.x, self.y)

    @property
    def max_val(self) -> float:
        """Get the value of the largest coordinate."""
        return max(self.x, self.y)

    @property
    def x_y_equal(self, tol: float = TOL_MM) -> bool:
        """Check if the x- and y-coordinates are equal within a tolerance.

        Args:
            tol: The maximum distance between the coordinates that is tolerated to still
                qualify them as being equal.

        Returns:
            `True` if the coordinates are equal, `False` otherwise.
        """
        return abs(self.x - self.y) <= tol

    @staticmethod
    def __arithmetic_parse(
        value: Vec2DCompatible | float | int,
    ) -> Vector2D:
        """Return a vector from different types."""
        if isinstance(value, Vector2D):
            return value
        elif isinstance(value, int | float):
            return Vector2D.from_floats(float(value), float(value))
        else:
            return Vector2D(value)

    def __eq__(self, other: object) -> bool:
        """Test whether two vectors are equal."""
        if not isinstance(other, Vector2D):
            return False
        return self.x == other.x and self.y == other.y

    def __ne__(self, other: object) -> bool:
        """Test whether two vectors are not equal."""
        return not self.__eq__(other)

    def __add__(
        self, value: Vector2D | tuple[float, float] | list[float] | float | int
    ) -> Vector2D:
        """Return a new vector that is the sum of itself with another vector or
        scalar.
        """
        other = Vector2D.__arithmetic_parse(value)
        return Vector2D.from_floats(self.x + other.x, self.y + other.y)

    def __iadd__(
        self, value: Vector2D | tuple[float, float] | list[float] | float | int
    ) -> Vector2D:
        """Add another vector or scalar to this vector."""
        other = Vector2D.__arithmetic_parse(value)
        self.x += other.x
        self.y += other.y
        return self

    def __neg__(self) -> Vector2D:
        """Create a copy of this vector and negate it."""
        return Vector2D.from_floats(-self.x, -self.y)

    def __sub__(
        self, value: Vector2D | tuple[float, float] | list[float] | float | int
    ) -> Vector2D:
        """Return a new vector that is the equal to itself minus the another vector or
        scalar.
        """
        other = Vector2D.__arithmetic_parse(value)
        return Vector2D.from_floats(self.x - other.x, self.y - other.y)

    def __isub__(
        self, value: Vector2D | tuple[float, float] | list[float] | float | int
    ) -> Vector2D:
        """Subtract another vector or scalar from this."""
        other = Vector2D.__arithmetic_parse(value)
        self.x -= other.x
        self.y -= other.y
        return self

    def __mul__(
        self, value: Vector2D | tuple[float, float] | list[float] | float | int
    ) -> Vector2D:
        """Multiply a vector with another vector or scalar."""
        other = Vector2D.__arithmetic_parse(value)
        return Vector2D.from_floats(self.x * other.x, self.y * other.y)

    def __rmul__(
        self, other: Vector2D | tuple[float, float] | list[float] | float | int
    ) -> Vector2D:
        """Multiply a vector with another vector or scalar."""
        return Vector2D.__mul__(self, other)

    def __div__(
        self, value: Vector2D | tuple[float, float] | list[float] | float | int
    ) -> Vector2D:
        """Divide this vector by another vector or scalar."""
        other = Vector2D.__arithmetic_parse(value)
        return Vector2D.from_floats(self.x / other.x, self.y / other.y)

    def __truediv__(
        self, obj: Vector2D | tuple[float, float] | list[float] | float | int
    ) -> Vector2D:
        """Divide this vector by another vector or scalar."""
        return self.__div__(obj)

    def __abs__(self) -> float:
        """Gets the length of the vector (same as `norm()`)."""
        return hypot(*self)

    def __lt__(self, other: Vector2D) -> float:
        """Returns if a vector is smaller than another one (required for sorting)."""
        return self.norm() < other.norm()

    def __repr__(self) -> str:
        """Return a string representation of the vector."""
        return f"Vector2D(x={self.x}, y={self.y})"

    def __str__(self) -> str:
        """Return a string representation of the vector."""
        return f"({self.x}, {self.y})"

    def __getitem__(self, key: str | int) -> float:
        """Get the value of the given coordinate."""
        if key == 0 or key == "x":
            return self.x
        if key == 1 or key == "y":
            return self.y
        raise IndexError("Index {} is out of range".format(key))

    def __setitem__(self, key: str | int, item: float | int) -> None:
        """Set the value of the given coordinate."""
        if key == 0 or key == "x":
            self.x = float(item)
        elif key == 1 or key == "y":
            self.y = float(item)
        else:
            raise IndexError("Index {} is out of range".format(key))

    def __len__(self) -> int:
        """Return the number of elements of this vector."""
        return 2

    def __iter__(self) -> Generator[float, None, None]:
        """Create an iterable list of the coordinates of this vector."""
        yield self.x
        yield self.y

    def __copy__(self) -> Vector2D:
        """Create a deep copy instead of a shallow one."""
        return self.copy()


class Vector3D:
    """A 3D vector."""

    def __init__(
        self,
        coordinates: Vec3DCompatible | float | int | None = None,
        y: int | float | None = None,
        z: int | float | None = None,
    ):
        """Representation of a 3D Vector in space.

        Args:
            coordinates: Either x- and y-coordinates of the point, if the second
                parameter is also used, just the x-coordinate.
            y: y-coordinate of the point.
            z: z-coordinate of the point.

        Example:
            >>> from KicadModTree import *
            >>> Vector3D(0, 0, 0)
            >>> Vector3D([0, 0, 0])
            >>> Vector3D((0, 0, 0))
            >>> Vector3D({'x': 0, 'y':0, 'z':0})
            >>> Vector3D(Vector2D(0, 0))
            >>> Vector3D(Vector3D(0, 0, 0))
        """

        self.x: float
        """The x-coordinate."""
        self.y: float
        """The y-coordinate."""
        self.z: float
        """The z-coordinate."""

        self.z = 0.0
        if isinstance(coordinates, float | int):
            self.x = float(coordinates)
            if y is not None:
                self.y = float(y)
            else:
                raise TypeError("You have to give at least x and y-coordinates.")
            if z is not None:
                self.z = float(z)
        elif isinstance(coordinates, Vector2D | Vector3D):
            self.x = coordinates.x
            self.y = coordinates.y
            if isinstance(coordinates, Vector3D):
                self.z = coordinates.z
        elif isinstance(coordinates, list | tuple):
            if len(coordinates) < 2:
                raise TypeError("Invalid list size (to small).")
            elif len(coordinates) > 3:
                raise TypeError("Invalid list size (to big).")
            else:
                self.x = float(coordinates[0])
                self.y = float(coordinates[1])
                if len(coordinates) == 3:
                    self.z = float(coordinates[2])
        elif isinstance(coordinates, dict):
            self.x = float(coordinates.get("x", 0.0))
            self.y = float(coordinates.get("y", 0.0))
            self.z = float(coordinates.get("z", 0.0))
        elif coordinates is None:
            self.x = 0.0
            self.y = 0.0
        else:
            raise TypeError("Invalid type for `coordinates`.")

    def cross_product(self, other: Vec3DCompatible | float | int) -> Vector3D:
        r"""Calculate the cross product of this vector with another vector:

        $\mathbf{a}\times\mathbf{b}=\|\mathbf{a}\|\cdot\|\mathbf{b}\|\cdot\sin\theta\cdot\mathbf{n}$

        Args:
            other: The other vector.

        Returns:
            The cross product.
        """
        other = Vector3D.__arithmetic_parse(other)
        return Vector3D(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def dot_product(self, other: Vec3DCompatible | float | int) -> float:
        r"""Calculate the inner product of this vector with another vector:

        $\mathbf{a}\cdot\mathbf{b}=\|\mathbf{a}\|\cdot\|\mathbf{b}\|\cdot\cos{\theta}$

        Args:
            other: The other vector.

        Returns:
            The dot product.
        """
        other = Vector3D.__arithmetic_parse(other)
        return self.x * other.x + self.y * other.y + self.z * other.z

    def is_nullvec(self, tol: float = TOL_MM) -> bool:
        """Check if the vector is equal to the null-vector.

        Args:
            tol: Manhattan distance that the vector is allowed to be away from (0, 0, 0)
                in any axis and still be considered equal to (0, 0).

        Returns:
            `True` if the vector is a null-vector, `False` otherwise.
        """
        if abs(self.x) > tol or abs(self.y) > tol or abs(self.z) > tol:
            return False
        return True

    def round_to(self, base: float) -> Vector3D:
        """Round to a specific base (like it's required for a grid).

        Args:
            base: The base we want to round to (e.g. 0.05).

        Returns:
            A new instance of the vector that is rounded to the grid.
        """
        if not base:
            return self.__copy__()

        return self.__class__([round(v / base) * base for v in self])

    def to_dict(self) -> dict[str, float]:
        """Return a dictionary containing the coordinates."""
        return {"x": self.x, "y": self.y, "z": self.z}

    def to_tuple(self) -> tuple[float, float, float]:
        """Return a tuple of (x, y, z)"""
        return (self.x, self.y, self.z)

    @staticmethod
    def __arithmetic_parse(
        value: Vec3DCompatible | int | float,
    ) -> Vector3D:
        if isinstance(value, Vector3D):
            return value
        elif isinstance(value, int | float):
            return Vector3D(value, value, value)
        else:
            return Vector3D(value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector3D):
            return False
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __add__(self, value: Vec3DCompatible | int | float) -> Vector3D:
        other = Vector3D.__arithmetic_parse(value)
        return Vector3D(self.x + other.x, self.y + other.y, self.z + other.z)

    def __iadd__(self, value: Vec3DCompatible | int | float) -> Vector3D:
        other = Vector3D.__arithmetic_parse(value)
        self.x += other.x
        self.y += other.y
        self.z += other.z
        return self

    def __neg__(self) -> Vector3D:
        return Vector3D(-self.x, -self.y, -self.z)

    def __sub__(self, value: Vec3DCompatible | int | float) -> Vector3D:
        other = Vector3D.__arithmetic_parse(value)
        return Vector3D(self.x - other.x, self.y - other.y, self.z - other.z)

    def __isub__(self, value: Vec3DCompatible | int | float) -> Vector3D:
        other = Vector3D.__arithmetic_parse(value)
        self.x -= other.x
        self.y -= other.y
        self.z -= other.z
        return self

    def __mul__(self, value: Vec3DCompatible | int | float) -> Vector3D:
        other = Vector3D.__arithmetic_parse(value)
        return Vector3D(self.x * other.x, self.y * other.y, self.z * other.z)

    def __div__(self, value: Vec3DCompatible | int | float) -> Vector3D:
        other = Vector3D.__arithmetic_parse(value)
        return Vector3D(self.x / other.x, self.y / other.y, self.z / other.z)

    def __truediv__(self, obj: Vec3DCompatible | int | float) -> Vector3D:
        return self.__div__(obj)

    def __repr__(self) -> str:
        return "Vector3D (x={x}, y={y}, z={z})".format(**self.to_dict())

    def __str__(self) -> str:
        return "(x={x}, y={y}, z={z})".format(**self.to_dict())

    def __getitem__(self, key: str | int) -> float:
        if key == 0 or key == "x":
            return self.x
        if key == 1 or key == "y":
            return self.y
        if key == 2 or key == "z":
            return self.z
        else:
            raise IndexError("Index {} is out of range".format(key))

    def __setitem__(self, key: str | int, item: int | float) -> None:
        if key == 0 or key == "x":
            self.x = float(item)
        elif key == 1 or key == "y":
            self.y = float(item)
        elif key == 2 or key == "z":
            self.z = float(item)
        else:
            raise IndexError("Index {} is out of range".format(key))

    def __len__(self) -> int:
        return 3

    def __iter__(self) -> Generator[float, None, None]:
        yield self.x
        yield self.y
        yield self.z

    def __copy__(self) -> Vector3D:
        return Vector3D(self.x, self.y, self.z)


Vec2DCompatible = Vector2D | Sequence[float | int | str] | dict[str, float | int | str]
"""Union for types compatible with a :class:`.Vector2D`."""

Vec3DCompatible = (
    Vector3D | Vector2D | Sequence[float | int | str] | dict[str, float | int | str]
)
"""Union for types compatible with a :class:`.Vector3D`."""
