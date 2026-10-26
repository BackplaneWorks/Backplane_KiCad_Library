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


import pytest

from kilibs.util import dict_tools as DT


def test_dict_inherit_no_inheritance():
    """No inheritance: dict_inherit just returns the input dictionary unchanged."""

    d = {
        "a": 1,
        "b": {"c": 2, "d": 3},
    }

    DT.dict_inherit(d)
    assert d == {
        "a": 1,
        "b": {"c": 2, "d": 3},
    }


def test_dict_inherit_single_level():
    """dict_inherit must correctly resolve a single level of inheritance."""

    d = {
        "1": {
            "a": 1,
            "b": {"c": 2, "d": 3},
        },
        "2": {
            "inherit": "1",
            "b": {"c": 3},
        },
    }

    DT.dict_inherit(d)

    # "2" must have inherited from "1", with own values winning
    assert d["2"] == {
        "a": 1,
        "b": {"c": 3, "d": 3},
    }

    # "inherit" key must be stripped from resolved entry
    assert "inherit" not in d["2"]

    # "1" (root) is unchanged
    assert d["1"] == {
        "a": 1,
        "b": {"c": 2, "d": 3},
    }


def test_dict_inherit_multi_level():
    """dict_inherit must correctly resolve chains deeper than 1 parent."""

    d = {
        "1": {
            "a": 1,
            "b": {"c": 2, "d": 3},
        },
        "2": {"inherit": "1", "b": {"c": 3}, "d": 4},
        "n": {
            "inherit": "2",
            "e": 5,
        },
    }

    DT.dict_inherit(d)

    # "n" must have inherited from both "2" and "1", with own values winning
    assert d["n"] == {
        "a": 1,  # from '1'
        "b": {"c": 3, "d": 3},  # from '2', then replaced with from '1'
        "d": 4,  # from '2'
        "e": 5,  # own value
    }

    # "inherit" keys must be stripped from all resolved entries
    assert "inherit" not in d["n"]
    assert "inherit" not in d["2"]

    # "1" (root) is unchanged
    assert d["1"] == {
        "a": 1,
        "b": {"c": 2, "d": 3},
    }


def test_dict_inherit_multi_level_reverse_order():
    """dict_inherit must correctly resolve chains deeper than 1 parent.

    The keys are inserted so that the deepest child ("n") comes first.
    """

    # deepest child first
    d = {
        "n": {
            "inherit": "2",
            "d": 4,
        },
        # intermediate
        "2": {
            "inherit": "1",
            "b": {"c": 3},
        },
        # root (no inherit)
        "1": {
            "a": 1,
            "b": {"c": 2, "d": 3},
        },
    }

    DT.dict_inherit(d)

    # "n" must have inherited from both "2" and "1", with own values winning
    assert d["n"] == {
        "a": 1,
        "b": {"c": 3, "d": 3},
        "d": 4,
    }


def test_dict_inherit_recursion_error():
    """Cyclic inheritance must raise RecursionError."""
    d = {
        "a": {"inherit": "b"},
        "b": {"inherit": "a"},
    }
    with pytest.raises(RecursionError):
        DT.dict_inherit(d)


def test_dict_inherit_deep_recursion_error():
    """Deep cyclic inheritance must raise RecursionError."""
    d = {
        "a": {"inherit": "b"},
        "b": {"inherit": "c"},
        "c": {"inherit": "a"},
    }
    with pytest.raises(RecursionError):
        DT.dict_inherit(d)


def test_dict_inherit_self_inheritance():
    """Self-inheritance must raise RecursionError."""
    d = {
        "a": {"inherit": "a"},
    }
    with pytest.raises(RecursionError):
        DT.dict_inherit(d)


def test_dict_inherit_invalid_parent():
    """If a parent is not found, KeyError must be raised."""
    d = {
        "a": {"inherit": "b"},
    }
    with pytest.raises(KeyError):
        DT.dict_inherit(d)
