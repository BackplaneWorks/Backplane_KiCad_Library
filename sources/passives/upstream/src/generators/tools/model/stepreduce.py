"""
This module provides functionality to reduce the size of STEP files by removing duplicate entries.
Based on C++ source code from https://gitlab.com/sethhillbrand/stepreduce
"""

"""
This program source code file is part of KICAD, a free EDA CAD application.

Copyright (C) 2018-2019 Kicad Services Corporation

@author Seth Hillbrand

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 3
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, you may find one here:
http://www.gnu.org/licenses/old-licenses/gpl-3.0.html
or you may search the http://www.gnu.org website for the version 3 license,
or you may write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
"""

import re
import sys


def emplace(d, key, val):
    """
    Inserts a key-value pair into the dictionary if the key does not already exist.

    Args:
        d (dict): The dictionary to insert the key-value pair into.
        key: The key to insert into the dictionary.
        val: The value to associate with the key.

    Returns:
        tuple: A tuple containing the key-value pair and a boolean indicating whether the insertion was successful.
               If the key already exists, returns the existing key-value pair and False.
               If the key does not exist, inserts the key-value pair and returns it with True.
    """
    if key in d:
        return ((key, d[key]), False)
    else:
        d[key] = val
        return ((key, val), True)


def split(s, delim):
    parts = s.split(delim, 1)
    return parts if len(parts) == 2 else parts + [""]


def stepreduce(input_file, output_file, verbose=False):
    with open(input_file, "r") as f:
        lines = f.read().splitlines()

    n_lines = len(lines)
    in_lines = []
    out_lines = []
    footer = []
    header = []
    past_header = False
    past_data = False
    continuing = False

    for line in lines:
        if past_header:
            if past_data or "ENDSEC;" in line:
                past_data = True
                footer.append(line)
            else:
                line = line.strip()
                if continuing:
                    if line[0].isalpha():
                        out_lines[-1] += " "
                    out_lines[-1] += line
                else:
                    out_lines.append(line)
                continuing = line[-1] != ";"
        else:
            if "DATA;" in line:
                past_header = True
            header.append(line)

    uniques = {}
    lookup = {}
    pattern = re.compile(r"#(\d+)")

    while True:
        in_lines = out_lines[:]
        out_lines.clear()
        uniques.clear()
        lookup.clear()

        for line in in_lines:
            elems = split(line, "=")
            elems[0] = elems[0][1:]
            oldnum = int(elems[0])
            elems[1] = elems[1].strip()

            (pair, was_inserted) = emplace(uniques, elems[1], len(out_lines) + 1)

            while (
                elems[1].startswith("PRODUCT_DEFINITION")
                or elems[1].startswith("SHAPE_REPRESENTATION")
            ) and not was_inserted:
                elems[1] += " "
                (pair, was_inserted) = emplace(uniques, elems[1], len(out_lines) + 1)

            if not was_inserted:
                if elems[1] != pair[0]:
                    print(f"Warning! {elems[1]} is not the same as {pair[0]}")

                # didn't insert!
                lookup[oldnum] = pair[1]
            else:
                lookup[oldnum] = len(out_lines) + 1
                out_lines.append(f"#{len(out_lines) + 1}={elems[1]}")

        for i in range(len(out_lines)):
            elems = split(out_lines[i], "=")
            line = elems[0] + "="
            while True:
                match = pattern.search(elems[1])
                if not match:
                    break
                oldval = int(match.group(1))
                newval = lookup.get(oldval, oldval)
                line += elems[1][: match.start()] + f"#{newval}"
                elems[1] = elems[1][match.end() :]
            line += elems[1]
            out_lines[i] = line

        if len(in_lines) <= len(out_lines):
            break

    with open(output_file, "w", newline="\n") as f:
        for line in header:
            f.write(line + "\n")
        for line in out_lines:
            f.write(line + "\n")
        for line in footer:
            f.write(line + "\n")

    if verbose:
        print(
            f"stepreduce: {input_file} {n_lines} shrunk to {len(out_lines) + len(header) + len(footer)}"
        )


if __name__ == "__main__":
    stepreduce(sys.argv[1], sys.argv[2])
