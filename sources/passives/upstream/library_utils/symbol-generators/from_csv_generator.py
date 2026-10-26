#!/usr/bin/env python3

# Generator that creates a symbol from a pinout CSV.
# See ./template.csv and ./BQ24004-example.csv for reference.

# add directory (common) that contains the kicad_sym lib to the path
# you can also use a relative module path instead
import os
import sys

# workaround to import the kicad_sym library
common = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.path.pardir, "common")
)
if common not in sys.path:
    sys.path.insert(0, common)

import argparse
import csv
import logging
import math
import re
import textwrap
import traceback
from collections import OrderedDict, defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Dict, List, Tuple

from kicad_sym import AltFunction, KicadLibrary, KicadSymbol, Pin, Rectangle, mil_to_mm

# logger to use to print errors/warnings etc.
logger = logging.getLogger("kicad_utils.from_csv_generator")

# Parser wide constants
CHAR_WIDTH_GUESSTIMATE = 50
PIN_NAME_LIMIT = 32


# Parser specific type definitions
@dataclass
class Metadata:
    reference: str
    name: str
    footprint: str | None = None
    footprint_filter: str | None = None
    datasheet: str | None = None
    description: str | None = None
    keywords: str | None = None
    generator_split_pin_names: int | None = True
    generator_min_aspect_ratio: float | None = None

    def __str__(self):
        out = textwrap.dedent("""
        {self.reference} '{self.name}':
            footprint: {self.footprint}
            footprint_filter: {self.footprint_filter}
            datasheet: {self.datasheet}
            description: {self.description}
            keywords: {self.keywords}
            generator_split_pin_names: {self.generator_split_pin_names}
        """)

        if self.generator_min_aspect_ratio is not None:
            out += (
                f"    generator_min_aspect_ratio: {self.generator_min_aspect_ratio}\n"
            )
        return out

    def __repr__(self):
        return f"{self.reference} '{self.name}'"


class PinData:
    """
    The data for one symbol pin to generate.
    """

    class Side(StrEnum):
        """
        All valid sides a pin can have.
        """

        TOP = "top"
        BOTTOM = "bottom"
        LEFT = "left"
        RIGHT = "right"

    pin_number: str | None
    name: str
    alt_names: List[str]
    type: str
    side: Side
    unit: str | None

    def __init__(self, data: dict, split_pin_names: bool = True):
        if type(data) is not dict:
            raise TypeError("Parameter data must be of type dict.")

        self.type = data.get("type", "").lower().replace(" ", "_")

        if self.type != "space" and "pin" not in data:
            raise ValueError("Missing pin number in data")
        if self.type != "space" and "name" not in data:
            raise ValueError("Missing pin name in data")

        if "pin" in data and len(data["pin"].strip()) > 0:
            self.pin_number = data["pin"]
        else:
            self.pin_number = None

        if split_pin_names:
            self.name, *self.alt_names = data.get("name", "").split(";")
        else:
            self.name, self.alt_names = data.get("name", ""), []

        if len(self.name) > PIN_NAME_LIMIT:
            logger.warning(
                f"pin name '{self.name}' is longer than {PIN_NAME_LIMIT} characters"
            )

        self.side = PinData.Side(data["side"].lower().replace(" ", "_"))
        if not self.side:
            self.side = PinData.Side.RIGHT

        self.unit = data.get("unit", "").strip()

    def __str__(self):
        return (
            f"<({self.pin_number or ''}) '{self.name}':"
            + f" side: {self.side.value}, type: {self.type}, unit: {self.unit}>"
        )

    def __repr__(self):
        return self.__str__()


# disable flake8 error here as CIs flake8 version is to old to properly handle PEP 613 – Explicit Type Aliases
type PinStack = List[PinData]  # noqa: E999


# Handle both numeric pin ranges, and alphanumeric BGA pin ranges
bga_letters = "ABCDEFGHJKLMNPRTUVWY"
bga_rows = [*bga_letters, *[a + b for a in bga_letters for b in bga_letters]]


def pin_range(start, end):
    if start_m := re.fullmatch(r"([A-Z]+)([0-9]+)", start):
        end_m = re.fullmatch(r"([A-Z]+)([0-9]+)", start)
        start_row, start_col = start_m.groups()
        end_row, end_col = end_m.groups()

        start_col, end_col = int(start_col), int(end_col)
        start_row, end_row = bga_rows.index(start_row), bga_rows.index(end_row)

        rows = [bga_rows[i] for i in range(start_row, end_row + 1)]
        cols = list(range(start_col, end_col + 1))

        return [f"{row}{col}" for row in rows for col in cols]
    else:
        return list(map(str, range(int(start), int(end) + 1)))


def parse_csv(
    filename: str, split_pin_names: bool | None = None
) -> Tuple[Metadata, List[PinData]]:
    """Parses the given CSV file into a list of pins and metadata.

    Parameters:
        filename (str): The path to the CSV file to parse.
        split_pin_names (bool | None): Whether to split pin names into alt names by ';'.

    Returns:
        tuple: A tuple with the symbol metadata as a dict as the first element
               and a list of pin data as the second element.
    """
    metadata_dict: Dict[str, str] = {}
    metadata: Metadata | None = None
    in_metadata_section: bool = True

    pin_headers: List[str] | None = None
    pin_data: List[PinData] = []

    with open(filename, newline="") as csvfile:
        reader = csv.reader(
            filter(lambda row: not row.startswith("# "), csvfile)
        )  # filter out lines with comments
        for row in reader:
            if in_metadata_section:  # parse metadata
                if not row or not row[0].strip():
                    # skip from metadata to pin data on first empty line
                    in_metadata_section = False

                    try:
                        metadata = Metadata(**metadata_dict)
                    except (ValueError, TypeError) as e:
                        raise ValueError("Error parsing metadata section") from e

                    # fallback to split pin names from metadata section
                    if split_pin_names is None:
                        split_pin_names = metadata.generator_split_pin_names

                    continue

                else:  # add row to metadata
                    metadata_dict[row[0].lower()] = row[1]

            else:  # parse pin data
                if len(row) == 0 or all(
                    map(lambda cell: cell == "", row)
                ):  # skip empty rows
                    continue
                elif (
                    pin_headers is None
                ):  # treat first pin data row as header names/order
                    pin_headers = list(
                        map(lambda h: h.lower(), filter(lambda h: len(h) > 0, row))
                    )

                    required_key_missing = False
                    if "pin" not in pin_headers:
                        logger.error('key "pin" is missing in the header row')
                        required_key_missing = True
                    if "name" not in pin_headers:
                        logger.error('key "name" is missing in the header row')
                        required_key_missing = True
                    if "type" not in pin_headers:
                        logger.error('key "type" is missing in the header row')
                        required_key_missing = True
                    if "side" not in pin_headers:
                        logger.warning('key "side" is missing in the header row')
                    if required_key_missing:
                        raise ValueError(
                            "A required key is missing in the CSV pin header row."
                        )
                else:
                    parsed_pin_data = {}

                    for column, header in enumerate(pin_headers):
                        if column >= len(row):
                            break
                        parsed_pin_data[header] = row[column]

                    if "unit" in pin_headers and parsed_pin_data["unit"].strip() == "":
                        logger.warning(
                            f'no unit set for pin {parsed_pin_data["pin"]} "{parsed_pin_data["name"]}"'
                        )

                    # if there are multiple pins with the same name (e.g. GND pins) one can specify
                    # them all in a single line like separated by comma like this: "1,2,5,7-11"
                    # This loop parses and splits that format.
                    if parsed_pin_data["pin"].strip() == "":
                        pin_data.append(PinData(parsed_pin_data, split_pin_names))
                    else:
                        for pin_num_str in parsed_pin_data["pin"].split(","):
                            pin_range_start, _, pin_range_end = pin_num_str.partition(
                                "-"
                            )
                            if not pin_range_end:
                                pin_range_end = pin_range_start

                            for pin_num in pin_range(pin_range_start, pin_range_end):
                                new_pin = parsed_pin_data.copy()
                                new_pin["pin"] = pin_num
                                pin_data.append(PinData(new_pin, split_pin_names))

    if metadata is None:
        raise ValueError("Failed to parse metadata from CSV.")
    return (metadata, pin_data)


# group pins by unit name
def group_pins_by_unit(pin_data: List[PinData]) -> Dict[str, List[PinData]]:
    """Groups together the given pins by their unit.

    Parameters:
        pin_data (list): A list of pin data.

    Returns:
        dict: A dict mapping for each unit the name of the unit to list of pins on in this unit.
    """
    symbol_units = defaultdict(list)
    for pin in pin_data:
        symbol_units[pin.unit].append(pin)
    return dict(symbol_units)


# group pins according to side
def group_pins_by_side(pins: List[PinData]) -> Dict[PinData.Side, List[PinData]]:
    """Groups together the given pins by their side.

    Parameters:
        pins (list): A list of pin data.

    Returns:
        dict: A dict mapping for each side the name of the side to list of pins on this side.
    """
    side_dict = {}
    for side in PinData.Side:
        side_dict[side] = []
    for pin in pins:
        side_dict[pin.side].append(pin)
    return side_dict


def create_pin_stacks(pins: List[PinData]) -> List[PinStack]:
    """Groups together the given pins by their name to create stacks of same pins.

    Parameters:
        pins (list): A list of pin data.

    Returns:
        list: A list of lists each containing a group of pins with the same name.
    """
    # mapping of pin names to pin pin_stacks
    pin_stacks: Dict[str, List[PinData]] = OrderedDict()
    # go through all pins and sort them into pin_stacks
    for index, pin in enumerate(pins):
        # do not group spaces and no_connects
        if pin.type == "space" or pin.type == "no_connect":
            pin_stacks[f"do_not_group_{index}"] = [pin]
        # add pins to existing pin_stacks
        elif pin.name in pin_stacks:
            existing_pin = pin_stacks[pin.name][0]
            if pin.type == existing_pin.type:
                pin_stacks[pin.name].append(pin)
            else:
                logger.warning(
                    f"Tried to add pin with number {pin.pin_number} and type {pin.type}"
                    + f" to stack with name {pin.name} and conflicting type {existing_pin.type}!"
                )
        # create new pin_stacks for new pin names
        else:
            pin_stacks[pin.name] = [pin]
    # return list of pin stacks where the pins in each stack are sorted by pin number
    return list(
        map(lambda g: sorted(g, key=lambda p: p.pin_number), pin_stacks.values())
    )


def pos_for_pin(pin_count: int, index: int, direction: bool = True) -> int:
    """Calculates the position for the pin at the given index.

    Parameters:
        pin_count (int): The total number of pins on the axis to calculate the position for.
        index (int): The index of the pin to calculate the position for.
        direction (bool): Whether the highest pin is on the positive (True) or negative side (False) of the axis.

    Returns:
        int: The position of the pin at the given index.
    """
    dir_int = 1 if direction else -1
    return (-dir_int * (pin_count // 2) * 100) + (dir_int * index * 100)


def pin_label_width(pin: PinData) -> int:
    """Calculates the estimated width of the label of the given pin.

    Parameters:
        pin (PinData): The pin data to calculate the label width for.

    Returns:
        int: The estimated width of the pin's label.
    """
    return (len(pin.name) + 1) * CHAR_WIDTH_GUESSTIMATE


def calculate_base_bounding_box_size(
    pin_stacks: Dict[PinData.Side, List[PinStack]],
) -> Tuple[int, int]:
    """Calculates the base bounding box containing the given pin stacks for each side.

    Parameters:
        pin_stacks (dict): The pin stacks for each side to calculate the base bounding box for.

    Returns:
        tuple: The base bounding box as a tuple of width, height.
    """

    pin_count_horizontal = max(
        len(pin_stacks[PinData.Side.TOP]), len(pin_stacks[PinData.Side.BOTTOM])
    )
    pin_count_vertical = max(
        len(pin_stacks[PinData.Side.LEFT]), len(pin_stacks[PinData.Side.RIGHT])
    )

    total_horizontal_pin_width = (pin_count_horizontal + 1) * 100
    max_pin_name_length_left = max(
        (pin_label_width(pin) for pin, *others in pin_stacks[PinData.Side.LEFT]),
        default=0,
    )
    max_pin_name_length_right = max(
        (pin_label_width(pin) for pin, *others in pin_stacks[PinData.Side.RIGHT]),
        default=0,
    )

    bounding_box_width = (
        max(
            total_horizontal_pin_width,
            max_pin_name_length_left,
            max_pin_name_length_right,
            200,
        )
        // 200
        + 1
    ) * 200

    total_vertical_pin_width = (pin_count_vertical + 1) * 100
    max_pin_name_length_top = max(
        (pin_label_width(pin) for pin, *others in pin_stacks[PinData.Side.TOP]),
        default=0,
    )
    max_pin_name_length_bottom = max(
        (pin_label_width(pin) for pin, *others in pin_stacks[PinData.Side.BOTTOM]),
        default=0,
    )

    bounding_box_height = (
        max(
            total_vertical_pin_width,
            max_pin_name_length_top,
            max_pin_name_length_bottom,
            200,
        )
        // 200
        + 1
    ) * 200

    return (bounding_box_width, bounding_box_height)


def check_label_intersection(
    pin_stacks: List[PinStack],
    pin_stacks_opposite: List[PinStack],
    current_bounding_box: Tuple[int, int],
) -> bool:
    """Checks if the labels of the given pin_stacks intersect with the labels of the opposite side.

    Parameters:
        pin_stacks (list): A list of pin stacks to check the intersection of labels for.
        pin_stacks_opposite (list): The list of pin stacks on the opposite side.
        current_bounding_box (tuple): The width and height of the current bounding box.

    Returns:
        bool: Whether the labels of pin_stacks intersect with the labels of the opposite side or not.
    """
    b_width, b_height = current_bounding_box
    # Check intersection for all given pin stacks
    for i, pin_stack in enumerate(pin_stacks):
        pin = pin_stack[
            0
        ]  # Use first pin in stack as pin stacks are grouped by label/name
        length = pin_label_width(pin)
        x_pos = pos_for_pin(len(pin_stacks), i, True)
        y_pos = -b_height / 2

        # Check intersection with each pin stack on the opposite side
        for j, pin_stack_opposite in enumerate(pin_stacks_opposite):
            pin_opposite = pin_stack_opposite[0]
            length_opposite = pin_label_width(pin_opposite)
            x_pos_opposite = pos_for_pin(len(pin_stacks_opposite), j, True)
            y_pos_opposite = b_height / 2

            # Check intersection of the two labels
            if (
                x_pos_opposite < x_pos + 100
                and x_pos_opposite + 100 > x_pos
                and y_pos + length > y_pos_opposite - length_opposite - 200
            ):
                return True  # Return if one pair of labels intersect

    return False


def check_adjacent_label_intersections(
    pin_stacks: Dict[PinData.Side, List[PinStack]],
    bounding_box: Tuple[int, int],
) -> bool:
    """Checks if labels from perpendicular sides overlap at symbol corners.

    A top/bottom pin's vertical label can overlap with a left/right pin's
    horizontal label near a corner when both labels extend deep enough into
    the body.

    Parameters:
        pin_stacks (dict): The pin stacks for each side.
        bounding_box (tuple): The width and height of the current bounding box.

    Returns:
        bool: Whether any adjacent-side labels overlap.
    """

    # This function was generated using claude opus, an LLM. Proceed with caution.
    # I (jaseg) tested it on many symbols from the new xilinx symbol generator, and
    # it worked well in these cases where previously, we'd get problematic overlap.
    bbox_w, bbox_h = bounding_box

    for tb_side in [PinData.Side.TOP, PinData.Side.BOTTOM]:
        for lr_side in [PinData.Side.LEFT, PinData.Side.RIGHT]:
            tb_stacks = pin_stacks[tb_side]
            lr_stacks = pin_stacks[lr_side]

            if not tb_stacks or not lr_stacks:
                continue

            for i, tb_stack in enumerate(tb_stacks):
                if tb_stack[0].type in ("space", "no_connect"):
                    continue
                tb_label = pin_label_width(tb_stack[0])
                tb_x = pos_for_pin(len(tb_stacks), i, True)

                for j, lr_stack in enumerate(lr_stacks):
                    if lr_stack[0].type in ("space", "no_connect"):
                        continue
                    lr_label = pin_label_width(lr_stack[0])
                    lr_y = pos_for_pin(len(lr_stacks), j, False)

                    # Check x: is the tb pin within the lr label's horizontal extent?
                    if lr_side == PinData.Side.RIGHT:
                        x_overlaps = tb_x > bbox_w / 2 - lr_label - 200
                    else:
                        x_overlaps = tb_x < -bbox_w / 2 + lr_label + 200

                    # Check y: is the lr pin within the tb label's vertical extent?
                    if tb_side == PinData.Side.TOP:
                        y_overlaps = lr_y > bbox_h / 2 - tb_label - 200
                    else:
                        y_overlaps = lr_y < -bbox_h / 2 + tb_label + 200

                    if x_overlaps and y_overlaps:
                        return True

    return False


def extend_bounding_box(
    pin_stacks: Dict[PinData.Side, List[PinStack]],
    bounding_box: Tuple[int, int],
    min_aspect_ratio: float | None = None,
) -> Tuple[int, int]:
    """Extends a given bounding box until no pin stack labels overlap anymore.

    Parameters:
        pin_stacks (list): The list of pin stacks to check and remove intersections for.
        bounding_box (tuple): A tuple of the bounding box width and height.
        min_aspect_ratio (float): The min aspect ratio to enforce while calculating.

    Returns:
        tuple: The extended bounding box as a tuple of width and height.
    """
    bounding_box_width, bounding_box_height = bounding_box

    # Extend bounding box size until no pin labels intersect
    intersect_top = True
    intersect_bottom = True
    intersect_left = True
    intersect_right = True

    while intersect_top or intersect_bottom or intersect_left or intersect_right:

        intersect_top = check_label_intersection(
            pin_stacks[PinData.Side.TOP],
            pin_stacks[PinData.Side.BOTTOM],
            (bounding_box_width, bounding_box_height),
        )

        intersect_bottom = check_label_intersection(
            pin_stacks[PinData.Side.BOTTOM],
            pin_stacks[PinData.Side.TOP],
            (bounding_box_width, bounding_box_height),
        )

        if intersect_top or intersect_bottom:
            bounding_box_height += 200

        intersect_left = check_label_intersection(
            pin_stacks[PinData.Side.LEFT],
            pin_stacks[PinData.Side.RIGHT],
            (bounding_box_height, bounding_box_width),
        )

        intersect_right = check_label_intersection(
            pin_stacks[PinData.Side.RIGHT],
            pin_stacks[PinData.Side.LEFT],
            (bounding_box_height, bounding_box_width),
        )

        if intersect_left or intersect_right:
            bounding_box_width += 200

    # Grow bbox to prevent adjacent-side (90-degree) label overlaps at corners
    while check_adjacent_label_intersections(
        pin_stacks, (bounding_box_width, bounding_box_height)
    ):
        bounding_box_width += 200

    if min_aspect_ratio is not None:
        if bounding_box_width / bounding_box_height < min_aspect_ratio:
            bounding_box_width = (
                math.ceil(bounding_box_height * min_aspect_ratio / 200) * 200
            )

    return (bounding_box_width, bounding_box_height)


def generate_pins(
    new_symbol: KicadSymbol,
    pin_stacks: List[PinStack],
    posx_func: Callable[[int], int],
    posy_func: Callable[[int], int],
    rotation: int,
    pin_length: int,
    unit_index: int,
) -> None:
    """Adds the given pin stacks to the new symbol using the given functions and rotation to determine pin positions.

    Parameters:
        new_symbol (KicadSymbol): The symbol to generate pins for.
        pin_stacks (list): The list of pin stacks to place where each is a list of pins.
        posx_func (func): Function returning the x position of a pin (stack) for a given index.
        posy_func (func): Function returning the y position of a pin (stack) for a given index.
        rotation (int): The rotation/orientation of the pins.
        pin_length (int): The pin length according to KLC S4.1
        unit_index (int): The index of the unit inside of the symbol to generate the pins in.
    """
    # Add all given pin stacks to the symbol
    for index, pin_stack in enumerate(pin_stacks):
        # Calculate pos for pin stack
        posy = posy_func(index)
        posx = posx_func(index)
        # Add each pin of the stack
        for pos_in_stack, pin in enumerate(pin_stack):
            # Skip placing pins for spaces
            if pin.type == "space":
                continue
            # Move in no_connect pins to meet KLC S4.6
            if pin.type == "no_connect":
                if rotation % 180 == 0:
                    posx += -pin_length if posx > 0 else pin_length
                else:
                    posy += -pin_length if posy > 0 else pin_length
            etype = pin.type
            # Set type passive according to KLC S4.3 7,8
            if pos_in_stack != 0 and pin.type in ["power_in", "power_out", "output"]:
                etype = "passive"
            # Add the pin to the symbol
            new_symbol.pins.append(
                Pin(
                    number=pin.pin_number,
                    name=pin.name,
                    etype=etype,
                    posx=mil_to_mm(posx),
                    posy=mil_to_mm(posy),
                    is_hidden=(pos_in_stack != 0 or pin.type == "no_connect"),
                    rotation=rotation,
                    length=mil_to_mm(pin_length),
                    altfuncs=list(
                        map(lambda n: AltFunction(name=n, etype=etype), pin.alt_names)
                    ),
                    unit=unit_index,
                )
            )


def output_symbol(input_csv_file: str, cli_args: Any) -> None:
    # parse csv and get units
    try:
        metadata, pin_data = parse_csv(input_csv_file, cli_args.split)
    except ValueError as parser_error:
        logger.error(
            f"Can not parse input CSV {input_csv_file}. Is it properly formatted?"
        )
        logger.error(str(parser_error))
        logger.error(traceback.format_exc())
        raise parser_error

    # load generator default CLI args from CSV
    min_aspect_ratio = cliArgs.min_aspect_ratio or metadata.generator_min_aspect_ratio

    symbol_units_dict = group_pins_by_unit(pin_data)
    unit_names_list = sorted(symbol_units_dict.keys())
    unit_names_dict = {(i + 1): name for i, name in enumerate(unit_names_list)}

    # generate kicad symbol

    output_base_path = cli_args.output or cli_args.input

    if cli_args.folder_mode:
        input_file_parts = Path(input_csv_file).parts[len(Path(cli_args.input).parts) :]
        output_path = Path(output_base_path, *input_file_parts)
        output_path = Path(
            output_path.parents[1],
            output_path.parent.with_suffix(".kicad_symdir").name,
            output_path.with_suffix(".kicad_sym").name,
        )
        libname = output_path.stem
        filename = str(output_path)
    else:
        libname = Path(output_base_path).stem
        filename = str(Path(output_base_path).with_suffix(".kicad_sym"))

    new_symbol = KicadSymbol.new(
        metadata.name,
        libname,
        reference=metadata.reference,
        footprint=metadata.footprint or "",
        datasheet=metadata.datasheet or "",
        keywords=metadata.keywords or "",
        description=metadata.description or "",
        fp_filters=metadata.footprint_filter or "",
        unit_names=unit_names_dict,
    )

    new_symbol.add_default_properties()

    # Even if we don't have any unit data, all symbols must have at least one unit
    new_symbol.unit_count = max(1, len(symbol_units_dict.keys()))

    max_bounding_box_width = 0
    max_bounding_box_height = 0
    max_x_offset = 0
    max_y_offset = 0

    # for each unit add pins and bounding box rectangle
    for unit_index, unit_name in unit_names_dict.items():
        pins: List[PinData] = symbol_units_dict[unit_name]
        # group pins into stacks
        pin_stacks: Dict[PinData.Side, List[PinStack]] = {
            side: create_pin_stacks(pins)
            for side, pins in group_pins_by_side(pins).items()
        }

        # get base bounding box
        base_bounding_box = calculate_base_bounding_box_size(pin_stacks)

        # Calculate pin length according to KLC S4.1
        max_pin_number_length = max(
            list(
                map(
                    lambda p: len(p.pin_number if p.pin_number is not None else ""),
                    pins,
                )
            )
        )
        pin_length = min(max(100, max_pin_number_length * 50), 300)

        # extend bounding box to prevent pin label intersections
        bounding_box = extend_bounding_box(
            pin_stacks, base_bounding_box, min_aspect_ratio
        )
        bounding_box_width, bounding_box_height = bounding_box

        # pos_for_pin centers pins at +/-50 for even pin counts due to
        # integer division (pin_count // 2). Shift the rectangle to match
        # the dominant side's pin center so pins are visually centered.
        left_count = len(pin_stacks[PinData.Side.LEFT])
        right_count = len(pin_stacks[PinData.Side.RIGHT])
        top_count = len(pin_stacks[PinData.Side.TOP])
        bottom_count = len(pin_stacks[PinData.Side.BOTTOM])

        dominant_v = max(left_count, right_count)
        dominant_h = max(top_count, bottom_count)
        y_offset = 50 if dominant_v > 0 and dominant_v % 2 == 0 else 0
        x_offset = -50 if dominant_h > 0 and dominant_h % 2 == 0 else 0

        # Adjust bbox dimensions so perpendicular pin endpoints land on 100 mil grid.
        # Required: (dim/2 + offset + pin_length) % 100 == 0
        if (bounding_box_height // 2 + y_offset + pin_length) % 100 != 0:
            bounding_box_height += 100
        if (bounding_box_width // 2 + x_offset + pin_length) % 100 != 0:
            bounding_box_width += 100

        if bounding_box_width > max_bounding_box_width:
            max_bounding_box_width = bounding_box_width
            max_x_offset = x_offset
        if bounding_box_height > max_bounding_box_height:
            max_bounding_box_height = bounding_box_height
            max_y_offset = y_offset

        # generate pins for each side
        generate_pins(
            new_symbol,
            pin_stacks[PinData.Side.LEFT],
            lambda i: -bounding_box_width / 2 + x_offset - pin_length,
            lambda i: pos_for_pin(len(pin_stacks[PinData.Side.LEFT]), i, False),
            0,
            pin_length,
            unit_index,
        )

        generate_pins(
            new_symbol,
            pin_stacks[PinData.Side.RIGHT],
            lambda i: bounding_box_width / 2 + x_offset + pin_length,
            lambda i: pos_for_pin(len(pin_stacks[PinData.Side.RIGHT]), i, False),
            180,
            pin_length,
            unit_index,
        )

        generate_pins(
            new_symbol,
            pin_stacks[PinData.Side.TOP],
            lambda i: pos_for_pin(len(pin_stacks[PinData.Side.TOP]), i, True),
            lambda i: bounding_box_height / 2 + y_offset + pin_length,
            270,
            pin_length,
            unit_index,
        )

        generate_pins(
            new_symbol,
            pin_stacks[PinData.Side.BOTTOM],
            lambda i: pos_for_pin(len(pin_stacks[PinData.Side.BOTTOM]), i, True),
            lambda i: -bounding_box_height / 2 + y_offset - pin_length,
            90,
            pin_length,
            unit_index,
        )

        # add bounding box rectangle
        new_symbol.rectangles.append(
            Rectangle(
                mil_to_mm(bounding_box_width / 2 + x_offset),
                mil_to_mm(bounding_box_height / 2 + y_offset),
                mil_to_mm(-bounding_box_width / 2 + x_offset),
                mil_to_mm(-bounding_box_height / 2 + y_offset),
                stroke_width=mil_to_mm(10),
                unit=unit_index,
            )
        )

    # add symbol metadata
    label_reference = new_symbol.get_property("Reference")
    label_reference.posx = mil_to_mm(-max_bounding_box_width / 2 + max_x_offset)
    label_reference.posy = mil_to_mm(max_bounding_box_height / 2 + max_y_offset + 100)

    label_value = new_symbol.get_property("Value")
    label_value.posx = mil_to_mm(max_bounding_box_width / 2 + max_x_offset)
    label_value.posy = mil_to_mm(max_bounding_box_height / 2 + max_y_offset + 100)

    label_datasheet = new_symbol.get_property("Datasheet")
    label_datasheet.posx = mil_to_mm(max_x_offset)
    label_datasheet.posy = mil_to_mm(-max_bounding_box_height / 2 + max_y_offset - 600)

    label_description = new_symbol.get_property("Description")
    label_description.posx = mil_to_mm(max_x_offset)
    label_description.posy = mil_to_mm(
        -max_bounding_box_height / 2 + max_y_offset - 800
    )
    label_description.effects.v_justify = "top"

    # save library with symbol
    lib = KicadLibrary(filename)
    lib.symbols.append(new_symbol)

    Path(filename).parent.mkdir(parents=True, exist_ok=True)

    lib.write()

    print(f"Written generated symbol to {filename}")


# the actual main function of the parser when invoked as a script:
if __name__ == "__main__":
    # parse cmdline parameters
    parser = argparse.ArgumentParser(
        prog="from_csv_generator.py", description="Generates KiCad Symbols from CSVs."
    )
    parser.add_argument(
        "input", help="The CSV file or folder of CSV files to generate a symbol for."
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Where to output the generated symbol(s) to. If not given the path of the"
        + " input CSV(s) with the extension .kicad_sym is used.",
    )
    parser.add_argument(
        "--dont-split-altfuncs",
        action="store_false",
        default=None,  # default to info from csv metadata section; if that's not there default to True
        dest="split",
        help='Disable splitting pin names into alternate functions on ";".',
    )
    parser.add_argument(
        "--min-aspect-ratio",
        type=float,
        dest="min_aspect_ratio",
        help="The minimum aspect ratio to enforce for the generated symbol as width / height.",
    )
    parser.add_argument(
        "--folder",
        dest="folder_mode",
        action="store_true",
        default=False,
        help="Process a folder of CSVs and output a directory structure of KiCad Symbols.",
    )

    cliArgs = parser.parse_args()

    # configure logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if cliArgs.folder_mode:
        if not Path(cliArgs.input).is_dir():
            logger.error("No folder given as input!")
        else:
            csv_files = [
                Path(r, f)
                for r, d, files in os.walk(cliArgs.input)
                for f in files
                if f.endswith(".csv")
            ]
            for csv_file in csv_files:
                try:
                    output_symbol(str(csv_file), cliArgs)
                except BaseException:
                    logger.error(f"Error generating output for {csv_file}!")
                    continue
    else:
        if Path(cliArgs.input).is_dir():
            logger.error("Folder given as input! Did you mean to use --folder?")
        else:
            output_symbol(cliArgs.input, cliArgs)
