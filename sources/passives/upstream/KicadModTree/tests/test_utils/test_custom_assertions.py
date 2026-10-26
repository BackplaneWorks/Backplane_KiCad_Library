import pytest

from KicadModTree.tests.test_utils import custom_assertions as CA

"""
Simple tests on the predicates in fp_predicates.

These don't need to be exhaustive, as the predicates are used in other tests
which gives coverage, but this is more about documenting the behaviour of the
predicates.
"""


@pytest.mark.parametrize(
    "list_to_check, should_contain, exp_match",
    (
        ([1, 2, 3, 4], [1, 2, 3, 4], True),     # Straight order match
        ([1, 2, 3, 4], [2, 3, 4, 1], True),
        ([1, 2, 3, 4], [4, 3, 2, 1], True),
        ([1, 2, 3, 4], [3, 2, 1, 4], True),
        ([1, 2, 3],    [1, 2, 3, 4], False),    # List to check doesn't contain 4
        ([1, 2, 3, 4], [1, 2, 3],    False),    # List to check has too many elements
    ),
)  # fmt: skip
def test_contains_only_points_cyclic(list_to_check, should_contain, exp_match):

    if exp_match:
        assert CA.assert_contains_only_cyclic(list_to_check, should_contain)
    else:
        with pytest.raises(AssertionError):
            CA.assert_contains_only_cyclic(list_to_check, should_contain)
