from collections.abc import Iterable
from typing import Any

from kilibs.geom import GeomLine, Vector2D
from kilibs.geom.tolerances import TOL_MM

"""
Collection of useful testing predicates for the KicadModTree library.
"""


def _default_cmp(a, b):
    return a == b


def assert_contains_only(to_check: list, should_contain: list, cmp=_default_cmp):
    """
    Predicate to check if a list contains only the elements of another list,
    with no regard to ordering.
    """

    for p in should_contain:
        found = False
        for c in to_check:
            if cmp(c, p):
                found = True
                break

        assert found, f"Element {p} not found in list: {to_check}"


def assert_contains_only_cyclic(to_check: list, should_contain: list, cmp=_default_cmp):
    """
    Predicate to check if a list contains only the elements of another list,
    and possibly wrapping around and possibly reversed.

    So the following are all equivalent:

    * [1, 2, 3, 4]
    * [2, 3, 4, 1]
    * [4, 3, 2, 1]
    * [3, 2, 1, 4]
    """

    assert len(to_check) == len(
        should_contain
    ), f"Length mismatch: {to_check} vs {should_contain}"

    found_indexes = []

    # First check that all needed points are in the list in the first place
    # and record their indexes
    for p in should_contain:
        found_at_index = -1
        for ic, c in enumerate(to_check):
            if cmp(c, p):
                found_at_index = ic
                break

        assert found_at_index >= 0, f"Element {p} not found in list: {to_check}"
        found_indexes.append(found_at_index)

    # Check that the points are in order
    is_forward = found_indexes[1] == (found_indexes[0] + 1) % len(to_check)

    if not is_forward:
        for i in range(len(found_indexes) - 1):
            assert (found_indexes[i] - 1) % len(to_check) == found_indexes[
                i + 1
            ], f"Element {i} not in order (reversed): {found_indexes[i]} -> {found_indexes[i + 1]}"
    else:
        for i in range(len(found_indexes) - 1):
            assert (found_indexes[i] + 1) % len(to_check) == found_indexes[
                i + 1
            ], f"Element {i} not in order: {found_indexes[i]} -> {found_indexes[i + 1]}"

    return True


def assert_contains_only_points_cyclic(
    to_check: list[Vector2D], expected: list[Vector2D], tol: float = TOL_MM
):
    """
    Predicate to check if all points in a list are in another list, and
    no others, and occur in the same order, but possibly wrapped around.

    This is a wrapper around assert_contains_only_cyclic, with a toleranced
    comparison function.
    """

    def cmp(a, b):
        return a.is_equal(b, tol)

    return assert_contains_only_cyclic(to_check, expected, cmp)


def assert_contains_lines(
    to_check: list[GeomLine], expected: list[GeomLine], tol: float = TOL_MM
):
    """
    Predicate to check if all lines in a list are in another list, and
    no others, in any order, with a tolerance. They can each be in either direction
    """

    def cmp(a: GeomLine, b: GeomLine):
        if a.is_equal(other=b, tol=tol):
            return True
        elif a.copy().reverse().is_equal(other=b, tol=tol):
            return True
        return False

    assert_contains_only(to_check, expected, cmp)


def assert_contains_n_of_type(to_check: Iterable[Any], n: int, type_: type) -> list:
    """
    Predicate to check if a list contains exactly n elements of a given type.

    : return: The list of elements of the given type.
    """

    matches = [el for el in to_check if isinstance(el, type_)]
    count = len(matches)

    assert count == n, f"Found {count} elements of type {type_}, expected {n}"

    return matches
