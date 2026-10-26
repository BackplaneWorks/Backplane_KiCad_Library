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

"""
Pad number generator functions.

Some ICs have a non-standard pin numbering scheme.
Using the generators an iterable is generated following the scheme.

Available generators:
----------------------
- increment: Generates pin numbers increasing by one and supports skipping pin numbers
            using the deleted_pins kwarg (skipped pins return a bogus value of -1)
- cw_dual: Generates pin numbers counting clockwise from the starting position
- ccw_dual: Generates pin numbers counting counter-clockwise from the starting position

Examples:
---------
To use a generator add the following to the device config:

  pad_numbers:
    generator: 'ccw_dual'
    axis: 'x'

To achieve a non-standard pin numbering of 2, 3, ..., N, 1 (instead of 1, 2, ... N) use:

  pad_numbers:
    generator: 'increment'
    offset: 1
    increment: 1
"""


def increment(pincount, init=1, offset=0, increment=1, **kwargs):
    """Standard increment iterator.

    Args:
        pincount: Total number of pins
        init: Initial starting count (default: 1)
        increment: (default: 1) amount to increment pin-numbers on each step. Can be negative for CCW numbering
        offset: add an offset to the pin numbers to achieve a non-standard pin numbering
            Examples:
                offset=1 results in [2, 3, ..., pincount, 1] instead of [1, 2, ..., pincount]
                offset=-1 results in [pincount, 1, 2, ..., pincount - 1]
        **kwargs: Other keyword arguments

    Returns:
        Iterator
    """
    pad_num = init # pad number

    deleted_pins = kwargs.get("deleted_pins", [])
    num_deleted_pins = len(deleted_pins)

    for i in range(init, pincount + 1):
        if i in deleted_pins:
            yield None
        else:
            yield 1 + (pad_num - 1 + offset) % (pincount - num_deleted_pins)
            pad_num += increment


def _get_pin_cw(pincount, loc):
    """Helper function to locate pin number for cw_dual.

    Args:
        pincount: Total number of pins
        loc: Starting location

    Returns:
        pin_number: Starting pin number
    """
    pins_per_side = pincount // 2
    if loc == "top_left":
        return 0
    elif loc == "bottom_left":
        return pins_per_side * 2 + 1
    elif loc == "bottom_right":
        return pins_per_side
    elif loc == "top_right":
        return pins_per_side + 1
    return 0


def _get_pin_ccw(pincount, loc):
    """Helper function to locate pin number for ccw_dual.

        Args:
            pincount: Total number of pins
            loc: Starting location

        Returns:
            pin_number: Starting pin number
    """
    pins_per_side = pincount // 2
    if loc == "top_left":
        return 0
    elif loc == "bottom_left":
        return pins_per_side + 1
    elif loc == "bottom_right":
        return pins_per_side
    elif loc == "top_right":
        return pins_per_side * 2 + 1
    return 0


def clockwise_dual(pincount, init=1, start="top_left", axis="x", **kwargs):
    """Generator for dual row packages counting clockwise.

    Args:
        pincount: Total number of pins
        init: Initial starting count (default: 1)
        start: The starting corner, top/bottom - left/right
        axis: Pin axis, either x or y. Is depended on num_pins_{x,y}
        **kwargs: Other keyword arguments

    Returns:
        Iterator
    """
    i = _get_pin_cw(pincount, start)

    if axis == "y":
        pins = iter(range(pincount, 0, -1))
    else:
        pins = iter(range(pincount))

    for ind in pins:
        yield ((i + ind) % pincount) + init


def counter_clockwise_dual(pincount, init=1, start="top_left", axis="x", **kwargs):
    """Generator for dual row packages counting counter clockwise.

     Args:
         pincount: Total number of pins
         init: Initial starting count (default: 1)
         start: The starting corner, top/bottom - left/right
         axis: Pin axis, either x or y. Is depended on num_pins_{x,y}
         **kwargs: Other keyword arguments

     Returns:
         Iterator
     """
    i = _get_pin_ccw(pincount, start)

    if axis == "x":
        pins = iter(range(pincount, 0, -1))
    else:
        pins = iter(range(pincount))

    for ind in pins:
        yield ((i + ind) % pincount) + init


# Add available generators to the dictionary
generators = {
    "increment": increment,
    "cw_dual": clockwise_dual,
    "ccw_dual": counter_clockwise_dual,
}


def get_generator(device_params):
    """Returns a pad number iterator based on device_params and selected generator.
    Fallback to plain increment.

    Args:
        device_params: Device parameters dictionary

    Returns:
        Pad number iterator

    Raises:
        KeyError: If generator not available
    """
    # Fallback to plain increment
    pincount = device_params["num_pins_x"] * 2 + device_params["num_pins_y"] * 2
    pad_nums = device_params.get("pad_numbers")

    if not pad_nums:
        return generators["increment"](pincount, **device_params)

    if ("init" not in pad_nums):
        pad_nums["init"] = 1

    pad_generator = pad_nums.get("generator", "increment")
    gen = generators.get(pad_generator)
    if not gen:
        gens = ", ".join(generators.keys())
        raise KeyError("{}: Use one of [{}]".format(pad_generator, gens))

    iterator = gen(pincount, deleted_pins=device_params.get("deleted_pins", []), **pad_nums)
    return iterator
