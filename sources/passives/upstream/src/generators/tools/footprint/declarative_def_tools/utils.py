# generators is free software: you can redistribute it and/or modify it under the terms
# of the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# generators is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# generators. If not, see < http://www.gnu.org/licenses/ >.
#
# (C) The KiCad Librarian Team

from typing import Iterable, Any, Dict
import copy
import re


def as_list(value) -> list:
    """
    Convert a value to a list, if it isn't already.
    """
    if (isinstance(value, str) or not isinstance(value, Iterable)):
        return [value]
    return [v for v in value]


class DotDict(dict):
    """
    A dictionary that supports dot notation as well as dictionary access notation.

    Converting a dict to a DotDict always creates a copy of the original.

    Inspired by https://stackoverflow.com/questions/13520421/recursive-dotdict
    """
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __init__(self, *args, **kwargs):
        super(DotDict, self).__init__(*args, **kwargs)
        for key, value in self.items():
            if hasattr(value, 'items'):
                self[key] = DotDict(value)
            elif hasattr(value, 'copy'):
                self[key] = value.copy()

    def copy(self):
        return DotDict(super(DotDict, self).copy())

    def update(self, *args, **kwargs):
        for arg in args:
            self.update(**arg)
        for key, value in kwargs.items():
            if hasattr(value, 'items'):
                self[key] = DotDict(value)
            elif hasattr(value, 'copy'):
                self[key] = value.copy()
            else:
                self[key] = value

    def __deepcopy__(self, memo):
        return DotDict(copy.deepcopy(dict(self), memo))

    def dump(self, prefix: str = ""):
        for key, value in self.items():
            if isinstance(value, DotDict):
                value.dump(prefix=prefix + f"{key}.")
            else:
                print(f"{prefix}{key} = {value.__repr__()}")

    def assign(self, *args, **kwargs):
        DotDict.assign_in(self, *args, **kwargs)
        return self


    @staticmethod
    def assign_in(table: Dict, sym_string: str, value: Any, *, create: bool = True, assign: bool = True) -> Dict:

        path = sym_string
        key = None

        while (path):

            if (match := re.match(r"^(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)(?P<tail>.*)$", path)):
                # symbol name
                assert key is None
                key = match["name"]

            elif (match := re.match(r"^\[(?P<idx>.+?)\](?P<tail>.*)$", path)):
                # [num] or ['name'] or ["name"]...
                if (idx := match["idx"]):
                    if (re.match(r"^\d+$", idx)):
                        idx = int(idx)
                    elif (idx.startswith('"') and idx.endswith('"')):
                        idx = idx.strip('"')
                    elif (idx.startswith("'") and idx.endswith("'")):
                        idx = idx.strip("'")
                    else:
                        raise KeyError(f"Unrecognized key type '{idx}' in '{sym_string}'")

                assert idx is not None

                new_obj = DotDict if isinstance(idx, str) else list

                if (create):
                    if (isinstance(table, dict) and key not in table):
                        table[key] = new_obj()
                    elif (table[key] is None):
                        table[key] = new_obj()
                table = table[key]
                key = idx
                if (create and not isinstance(table, dict)):
                    while not (idx < len(table)):
                        table.append(None)

            elif (match := re.match(r"^(?P<dot>\.)(?P<tail>.*)$", path)):
                # dot (separator)
                if (create):
                    if (isinstance(table, dict) and key not in table):
                        table[key] = DotDict()
                    elif (table[key] is None):
                        table[key] = DotDict()
                table = table[key]
                key = None

            else:
                raise NameError(f"{sym_string} is not a valid symbol name")

            path = match["tail"]

        if (key is None):
            raise NameError(f"{sym_string} can not be created")

        if (assign):
            table[key] = value
