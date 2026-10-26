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

"""Dictionary tools."""

import copy
from typing import Any


def dict_merge(defaults: dict[Any, Any], dictionary: dict[Any, Any]) -> None:
    """
    Recursively updates `dictionary` in-place with a deep copy of key-value pairs from
    `defaults` that `dictionary` does not yet contain.

    If both `defaults` and `dictionary` contain the same key:

    * If the values are both dictionaries, they are merged recursively (`dictionary`
      is completed with a deep copy of the key-value pairs from `default`).
    * Otherwise, the value in `dictionary` is kept (`dictionary` takes precedence).

    Example:
        >>> defaults = {"a": 1, "b": {"b1": 2, "b2": 3}}
        >>> dictionary = {"a": 2, "b": {"b2": 4}}
        >>> dict_merge(defaults, dictionary)
        >>> print(dictionary)
            {"a": 2, "b": {"b1": 2, "b2": 4}}

    Args:
        defaults: Dictionary providing default/fall-back values.
        dictionary: Dictionary to be updated in-place (the resulting dictionary).
    """
    for key, value in defaults.items():
        if key not in dictionary:
            dictionary[key] = copy.deepcopy(value)
        elif isinstance(value, dict) and isinstance(dictionary[key], dict):
            dict_merge(value, dictionary[key])  # pyright: ignore


def dict_inherit(d: dict[Any, Any]) -> None:
    """Merge recursively dictionaries within a hierarchy using 'inherit' entries.

    The top-level dictionary (`d`) can be thought of as a type of "namespace"
    containing a collection of objects (sub-dictionaries). Objects within the
    namespace may contain an 'inherit' entry, which stores the key for another
    object within the namespace.

    Inheritance is done recursively, so it is possible to have multiple levels
    of inheritance (object c can inherit b, which itself inherits from a). When
    this function is executed, it iterates through every entry in `d` and runs
    dictMerge() until all of the 'inherit' entries have been resolved. The
    result is applied to `d` in-place.

    Args:
        d: Top-level "namespace" dictionary containing other dictionaries, each of
            which may contain an 'inherit' key to be resolved; edited in-place.

    Raises:
        RecursionError: If two dictionaries attempt to inherit each other.
        KeyError: If a dictionary tries to inherit from a key that is not in `d`.

    Examples:
        Typical JSON/YAML file structure that can be processed by this function:

        .. code-block::

            {
                "1": {
                    "a": 1,
                    "b": {"c": 2, "d": 3, ...}
                },
                "2": {
                    "inherit": "1",
                    "b": {"c": 3}
                },
                ...
                "n": {
                    "inherit": "2",
                    "d": 4
                }
            }

        The result will look something like this:

        .. code-block::

            {
                "1": {
                    "a": 1,
                    "b": {"c": 2, "d": 3, ...}
                },
                "2": {
                    "a": 1,
                    "b": {"c": 3, "d": 3, ...}
                },
                ...
                "n": {
                    "a": 1,
                    "b": {"c": 3, "d": 3, ...},
                    "d": 4
                }
            }
    """

    def dict_inherit(
        d: dict[Any, Any], child: dict[Any, Any], parent: dict[Any, Any]
    ) -> None:
        if "inherit" in parent:
            if d[parent["inherit"]] is child:
                raise RecursionError
            else:
                dict_inherit(d, parent, d[parent["inherit"]])

        del child["inherit"]
        dict_merge(parent, child)

    for v in d.values():
        if isinstance(v, dict) and "inherit" in v:
            dict_inherit(d, v, d[v["inherit"]])  # pyright: ignore
        else:
            continue
