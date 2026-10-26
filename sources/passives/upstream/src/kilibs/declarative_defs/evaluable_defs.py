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
"""Classes for different types that can be evaluated as an expression."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from types import UnionType
from typing import Any, TypeAlias

from kilibs.geom import Vector2D


class Evaluable(ABC):
    """Something that can be evaluated as an expression. This is the basic type that
    most other evaluable types are composed from.

    For example, a vector that you want to be able to evaluate as an expression in x and
    y would have one EvaluableScalar for x and one for y, and itself would be an
    Evaluable that evaluates the two scalars and returns a Vector2D.
    """

    @abstractmethod
    def evaluate(self, expr_evaluator: Callable[[Any], Any]) -> Any:
        """Evaluate the object and return it. Exact return type depends on the
        implementing class.

        Args:
            expr_evaluator: A callable that takes an expression and returns its
                evaluated value.
        """
        raise NotImplementedError("Evaluable.evaluate() must be implemented")


class EvaluableScalar(Evaluable):
    """A value that can be evaluated as an expression, or just be a literal number,
    eventually returning a `float`.
    """

    ExprType: TypeAlias = str | float | int
    """The type of the expression, which can be a `str`, a `float`, or an `int`."""

    def __init__(self, dict_entry: ExprType) -> None:
        """Initialize an `EvaluableScalar`.

        Args:
            dict_entry: The expression, which can be a `str`, a `float`, or an `int`.
        """
        self.value = dict_entry

    def evaluate(self, expr_evaluator: Callable[[ExprType], float]) -> float:
        """Evaluate the expression and return the result as a `float`.

        Args:
            expr_evaluator: A callable that takes an expression and returns its
            evaluated value.

        Returns:
            The evaluated value as a `float`.
        """
        val = expr_evaluator(self.value)
        return float(val)


class EvaluableInt(Evaluable):
    """A value that can be evaluated as an expression, or just be a literal number,
    eventually returning an `int`.
    """

    ExprType: TypeAlias = str | int
    """The type of the expression, which can be a `str` or an `int`."""

    def __init__(self, dict_entry: ExprType):
        """Initialize an `EvaluableInt`.

        Args:
            dict_entry: The expression, which can be a `str` or an `int`.
        """
        self.value = dict_entry

    def evaluate(self, expr_evaluator: Callable[[ExprType], int]) -> int:
        """Evaluate the expression and return the result as an `int`.

        Args:
            expr_evaluator: A callable that takes an expression and returns its
            evaluated value.

        Returns:
            The evaluated value as an `int`.
        """
        val = expr_evaluator(self.value)
        return int(val)


class EvaluableList(list[Any]):
    """Simple wrapper around a list that checks the length and type of the entries."""

    def __init__(
        self,
        dict_entry: list[Any],
        exp_len: int | None,
        exp_type: type[Any] | UnionType | None = None,
    ):
        """Initialize an `EvaluableList`.

        Args:
            dict_entry: The list to wrap.
            exp_len: The expected length of the list, or `None` if any length is
                allowed.
            exp_type: The expected type of the entries, or `None` if any type is allowed
                (strings are always allowed).

        Raises:
            ValueError: If `dict_entry` is not a list, or `exp_len` is not `None` and
                the length of `dict_entry` does notmatch `exp_len`, or if `exp_type` is
                not `None` and an entry in `dict_entry` is not a string and not of type
                `exp_type`.
        """
        if exp_len is not None and len(dict_entry) != exp_len:
            raise ValueError(
                f"EvaluableList must have length {exp_len}, got {len(dict_entry)}"
            )

        if exp_type is not None:
            for i, entry in enumerate(dict_entry):
                # Strs are evaluated as expressions, so we can't check the type now, that will
                if not isinstance(entry, str):
                    if not isinstance(entry, exp_type):
                        raise ValueError(
                            f"EvaluableList entry {i} must be of type {exp_type}, got {type(entry)}"
                        )

        super().__init__(dict_entry)


class EvaluableVector2D:
    """A point with x- and y-coordinates that can be evaluated as expressions, or just
    be literal numbers.

    Example:
        This is usually used like this:

        .. code-block::

            some_key: [x, y]
    """

    x: EvaluableScalar
    """The x-coordinate."""
    y: EvaluableScalar
    """The y-coordinate."""

    def __init__(self, dict_entry: list[EvaluableScalar.ExprType]) -> None:
        """Initialize an `EvaluableVector2D`.

        Args:
            dict_entry: A dictionary or containing the x- and y-values that can be
                extracted.
        """
        el = EvaluableList(dict_entry, exp_len=2, exp_type=EvaluableScalar.ExprType)
        assert len(el) == 2
        self.x = EvaluableScalar(el[0])
        self.y = EvaluableScalar(el[1])

    def evaluate(
        self, expr_evaluator: Callable[[EvaluableScalar.ExprType], float]
    ) -> Vector2D:
        """Evaluate the x- and y-coordinates and return them as a Vector2D.

        Args:
            expr_evaluator: A callable that evaluates an expression to a scalar.

        Returns:
            A Vector2D object with the evaluated x- and y-coordinates.
        """
        return Vector2D(
            self.x.evaluate(expr_evaluator), self.y.evaluate(expr_evaluator)
        )


class EvaluableVector2Int:
    """A point with x- and y-coordinates that can be evaluated as expressions, or just
    be literal numbers.

    Can be used for integer coordinates, e.g. for grid counts, etc.
    """

    x: EvaluableInt
    """The x-coordinate."""
    y: EvaluableInt
    """The y-coordinate."""

    def __init__(self, dict_entry: list[EvaluableInt.ExprType]):
        """Initialize an `EvaluableVector2Int`.

        Args:
            dict_entry: A dictionary or containing the x- and y-values that can be
                extracted.
        """
        el = EvaluableList(dict_entry, exp_len=2, exp_type=EvaluableInt.ExprType)
        assert len(el) == 2
        self.x = EvaluableInt(el[0])
        self.y = EvaluableInt(el[1])

    def evaluate(
        self, expr_evaluator: Callable[[EvaluableInt.ExprType], int]
    ) -> tuple[int, int]:
        """Evaluate the x- and y-coordinates and return them as a Vector2D.

        Args:
            expr_evaluator: A callable that evaluates an expression to an `int`.

        Returns:
            A Vector2D object with the evaluated x- and y-coordinates.
        """
        return (self.x.evaluate(expr_evaluator), self.y.evaluate(expr_evaluator))
