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

"""Parameter tools."""

from collections.abc import Sequence
from typing import TypeVar

from kilibs.geom import Vector2D, Vector3D

T = TypeVar("T", int, float)


def toNumberArray(
    value: (
        int
        | float
        | dict[str, float | int | str]
        | Sequence[float | int | str]
        | Vector2D
        | Vector3D
    ),
    length: int = 2,
    min_value: int | None = 1,
    member_type: type[T] = int,
) -> list[T]:
    """Convert value into an array of given type with given length.

    Args:
        value: The value which can be of any of the supported types:

            * `int` or `float`: Returns array filled with copies of value.
            * `dict`: Array created with values for keys 'x', 'y', 'z'. Not that the
              dict is only supported for `length` equal to 2 and 3.
            * list or tuple -> truncated to `length`.
            * `Vector2D` or `Vector3D`: truncated to `length`.

        length: Defines the length of the resulting array.
        min_value: Defines the minimum allowed value (raise a `ValueError` if too low).
            If equal to `None` then no check is performed.
        mamber_type: All members of the array will be converted to this type.

    Raises:
        TypeError: If the `min_value` is too low, or the type or the length is not
            supported.

    Returns:
        The given `value` converted to the given `type` and `length`.
    """
    if isinstance(value, int | float):
        result = [member_type(value) for _ in range(length)]
    elif isinstance(value, dict):
        if length in [2, 3]:
            KEYS = ["x", "y", "z"]
            result = [member_type(value[KEYS[i]]) for i in range(length)]
        else:
            raise TypeError("Dict only supported for length 2 or 3.")
    elif isinstance(value, Sequence):
        if len(value) >= length:
            result = [member_type(v) for v in value[:length]]
        else:
            raise TypeError("Sequence only supported for length 2 or 3.")
    else:
        if len(value) < length:
            raise TypeError(
                "Vector dimensions ({}) are too low. Must be at least {}".format(
                    len(value), length
                )
            )
        result = [member_type(v) for v in value]

    if min_value is not None and isAnyLarger(result, min_value, False):
        raise ValueError(
            "At least one value in ({}) too small. Limit is {}.".format(
                result, min_value
            )
        )
    return result


def toIntArray(
    value: (
        int
        | float
        | dict[str, float | int | str]
        | Sequence[float | int | str]
        | Vector2D
        | Vector3D
    ),
    length: int = 2,
    min_value: int | None = 1,
) -> list[int]:
    """Convert `value` into an array of ints of given `length`.

    Args:
        value: The value which can be of any of the supported types:

            * `int` or `float`: Returns array filled with copies of value.
            * `dict`: Array created with values for keys 'x', 'y', 'z'. Not that the
              dict is only supported for `length` equal to 2 and 3.
            * list or tuple -> truncated to `length`.
            * `Vector2D` or `Vector3D`: truncated to `length`.

        length: Defines the length of the resulting array.
        min_value: Defines the minimum allowed value (raise a `ValueError` if too low).
            If equal to `None` then no check is performed.

    Raises:
        TypeError: If the `min_value` is too low, or the type or the length is not
            supported.

    Returns:
        The given `value` converted to an array of `int`.
    """
    return toNumberArray(value, length, min_value, member_type=int)


def toFloatArray(
    value: (
        int
        | float
        | dict[str, float | int | str]
        | Sequence[float | int | str]
        | Vector2D
        | Vector3D
    ),
    length: int = 2,
    min_value: int | None = 1,
) -> list[float]:
    """Convert value into an array of floats of given length.

    Args:
        value: The value which can be of any of the supported types:

            * `int` or `float`: Returns array filled with copies of value.
            * `dict`: Array created with values for keys 'x', 'y', 'z'. Not that the
              dict is only supported for `length` equal to 2 and 3.
            * list or tuple -> truncated to `length`.
            * `Vector2D` or `Vector3D`: truncated to `length`.

        length: Defines the length of the resulting array.
        min_value: Defines the minimum allowed value (raise a `ValueError` if too low).
            If equal to `None` then no check is performed.
        mamber_type: All members of the array will be converted to this type.

    Raises:
        TypeError: If the `min_value` is too low, or the type or the length is not
            supported.

    Returns:
        The given `value` converted to floats.
    """
    return toNumberArray(value, length, min_value, member_type=float)


def isAnyLarger(
    values: (
        int
        | float
        | dict[str, float | int | str]
        | Sequence[float | int | str]
        | Vector2D
        | Vector3D
    ),
    low_limits: int,
    must_be_larger: bool = False,
) -> bool:
    """Check if any value in the source array is larger than its respective limit.

    Args:
        values: The values to check.
        low_limits: Defines the minimum allowed value (raise a `ValueError` if too low).
            If equal to `None` then no check is performed.
        must_be_larger: Defines if the number must be larger than the limit or if the
            limit is the minimum value.

    Returns:
        `True` if all the values given are larger (or larger/equal if `must_be_larger is
        `False`) than the `low_limits` value, `False` otherwise.
    """
    if isinstance(values, float | int):
        if values < low_limits or (values <= low_limits and must_be_larger):
            return True
    else:
        limits = toFloatArray(low_limits, len(values), min_value=None)
        if isinstance(values, dict):
            val_list: list[float] = []
            for _, val in values.items():
                val_list.append(float(val))
            values = val_list
        for v, l in zip(values, limits):
            if float(v) < float(l) or (float(v) <= float(l) and must_be_larger):
                return True
    return False


def toVectorUseCopyIfNumber(
    value: (
        int
        | float
        | dict[str, float | int | str]
        | Sequence[float | int | str]
        | Vector2D
        | Vector3D
    ),
    length: int = 2,
    low_limit: int | None = None,
    must_be_larger: bool = True,
) -> Vector2D | Vector3D:
    """Convert `value` into a vector of the given dimension.

    Args:
        value: The value to convert.
            Supported types are all types allowed for vector constructor plus `int` and
            `float`. If `int`/`float`, the vector will be initialized with the correct
            number of copies.
        length: Defines the dimension of the resulting vector (either 2 or 3).
        low_limit: Defines the minimum allowed value (raise a value error if too low).
            If `None` is given as argument, then no check is performed.
        must_be_larger: Defines if the number must be larger than the limit or if the
            limit is the minimum value.

    Returns:
        A vector of `value` with the given dimension.
    """
    result: (
        Sequence[float | int | str] | dict[str, float | int | str] | Vector2D | Vector3D
    )
    if isinstance(value, int | float):
        result = [float(value) for _ in range(length)]
    else:
        result = value
    if length == 2 and not isinstance(result, Vector3D):
        result = Vector2D(result)
    elif length == 3:
        result = Vector3D(result)
    else:
        raise ValueError("length must be 2 or 3")
    if low_limit is not None and isAnyLarger(result, low_limit, must_be_larger):
        raise ValueError(
            "One value in ({}) too small. Limit is {}.".format(result, low_limit)
        )
    return result


def getOptionalBoolTypeParam(
    kwargs: dict[str, bool | float | int | str],
    param_name: str,
    default_value: bool | None = None,
) -> bool | None:
    """Get a named parameter from a packed `dict` and converts it to a `bool` if
    possible.

    Args:
        **kwargs: The parameters as packed `dict`.
        param_name: The name of the parameter (=key).
        default_value: The value to be used if the parameter is not in the `dict`.

    Returns:
        The value of the parameter from the given `dict` as `bool`, if possible. If
        the value from the dictionary is not `None` but cannot be converted into a
        `bool`, the default value is returned, otherwise `None` is returned.
    """
    val = kwargs.get(param_name, default_value)
    if val is not None:
        if (
            (isinstance(val, bool) and val)
            or (val == 1)
            or (
                isinstance(val, str)
                and (str(val).lower() == "true" or str(val).lower() == "yes")
            )
        ):
            return True
        elif (
            (isinstance(val, bool) and not val)
            or (val == 0)
            or (
                isinstance(val, str)
                and (str(val).lower() == "false" or str(val).lower() == "no")
            )
        ):
            return False
        return default_value
    return val


def getOptionalNumberTypeParam(
    kwargs: dict[str, float | int | str],
    param_name: str,
    default_value: float | int | None = None,
    low_limit: float | int | None = None,
    high_limit: float | int | None = None,
    allow_equal_limit: bool = True,
) -> float | int | None:
    """Get a named parameter from a packed `dict` and guarantee it is a number (`float`
    or `int`).

    Args:
        **kwargs: The parameters as packed `dict`.
        param_name: The name of the parameter (=key).
        default_value: The value to be used if the parameter is not in the `dict`.
        low_limit: The minimum allowable value.
        high_limit: The maximum allowable value.
        allow_equal_limit: Limits are included in range of allowable values
            (min <= x <= max if true else min < x < max).

    Raises:
        ValueError: When the value is outside of the limits or when the type of the
            value is not a `float` or `int`.

    Returns:
        The value of the parameter from the given `dict` as `float` or `int`.
    """
    val = kwargs.get(param_name, default_value)
    if val is not None:
        if not isinstance(val, float | int):
            raise TypeError("{} needs to be of type int or float".format(param_name))
        if low_limit is not None:
            if val < low_limit or (val == low_limit and not allow_equal_limit):
                raise ValueError(
                    "{} with value {} violates the low limit of {}".format(
                        param_name, val, low_limit
                    )
                )
        if high_limit is not None:
            if val > high_limit or (val == low_limit and not allow_equal_limit):
                raise ValueError(
                    "{} with value {} violates the high limit of {}".format(
                        param_name, val, high_limit
                    )
                )
    return val
