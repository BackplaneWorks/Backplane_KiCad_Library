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

import sys

from collections.abc import Iterable, Iterator, Sequence
from typing import Any

from KicadModTree import Footprint, FootprintType, ModArgparser, Pad, Model, Node, Text
from kilibs.geom import Direction, Vector2D
from generators.tools.footprint.drawing_tools_silk import SilkArrowSize
from kilibs.config import global_config
from generators.tools.footprint.declarative_def_tools import common_metadata
from generators.tools.footprint.save_footprint import write_footprint
from generators.tools.pad_factory import DevicePadType, PadFactory, PadInfo

from generators.tools.footprint.nodes.layouts.n_pad_box_layout import NPadBoxLayout
from generators.tools.footprint.nodes.layouts.footprint_layout import SilkStyle


class TablePadFactory(PadFactory):
    """A pad factory that takes its pads from a data table.

    Each row describes one pad as:

        [pad_type, number, x, y, size_x, size_y, drill]

    where `pad_type` is one of "smd", "tht", "thtr" or "npth". `drill` is only
    used for through-hole pads.
    """

    def __init__(self, rows: Iterable[Sequence[str | float]]) -> None:
        self._rows = list(rows)

    def _pad_size_from_row(self, row: Sequence[str | float]) -> Vector2D:
        """Extract the pad size from a table row.

        A zero `size_y` means a square/round pad, so `size_x` is used for both
        directions.
        """
        size_x = float(row[4])
        size_y = float(row[5])
        if size_y == 0.0:
            return Vector2D.from_floats(size_x, size_x)
        return Vector2D.from_floats(size_x, size_y)

    def _pad_info_from_row(self, row: Sequence[str | float]) -> PadInfo:
        """Convert one table row into a `PadInfo`."""
        pad_type = str(row[0])
        number = str(row[1])
        position = Vector2D.from_floats(float(row[2]), -float(row[3]))
        size = self._pad_size_from_row(row)

        if pad_type == "smd":
            fp_pad_type = Pad.TYPE_SMT
            device_pad_type = DevicePadType.SMD_LAND
            shape = Pad.SHAPE_ROUNDRECT
            drill = None
        elif pad_type in ("tht", "thtr"):
            fp_pad_type = Pad.TYPE_THT
            device_pad_type = DevicePadType.THT_PIN
            shape = Pad.SHAPE_ROUNDRECT if pad_type == "thtr" else Pad.SHAPE_OVAL
            drill = float(row[6])
        elif pad_type == "npth":
            fp_pad_type = Pad.TYPE_NPTH
            device_pad_type = DevicePadType.MECH_PIN
            shape = Pad.SHAPE_OVAL
            drill = float(row[6])
        else:
            raise ValueError(f"Unknown pad type: {pad_type}")

        return PadInfo(
            name=number,
            position=position,
            size=size,
            shape=shape,
            fp_pad_type=fp_pad_type,
            device_pad_type=device_pad_type,
            drill=drill,
        )

    def pads(self) -> Iterator[PadInfo]:
        for row in self._rows:
            yield self._pad_info_from_row(row)


def build_extra_texts(text_data: list[list[str | float]]) -> list[Node]:
    """
    Convert a list of text data into a list of Nodes (probably, but not
    necessarily, Text nodes).

    Data format: [x, y, text, layer, size_x, size_y]
    """

    nodes: list[Node] = []

    for n in text_data:
        at = Vector2D.from_floats(float(n[0]), -float(n[1]))
        stss = str(n[2])

        if len(n) > 3:
            layer = str(n[3])
        else:
            layer = "F.SilkS"

        if len(n) > 5:
            size = Vector2D.from_floats(float(n[4]), float(n[5]))
        else:
            size = Vector2D.from_floats(1.0, 1.0)

        new_node = Text(text=stss, at=at, layer=layer, size=size)

        nodes.append(new_node)

    return nodes


def arrow_nesw_from_str(s: str | None) -> Direction | None:
    """
    Convert a string representing an arrow direction to a cardinal direction.
    """

    if not s:  # None or empty string
        return None

    match s.upper():
        case "NORTH":
            return Direction.NORTH
        case "SOUTH":
            return Direction.SOUTH
        case "EAST":
            return Direction.EAST
        case "WEST":
            return Direction.WEST
        case _:
            pass

    raise ValueError(f"Invalid arrow direction: {s}. Expected one of: NORTH, SOUTH, EAST, WEST.")


def converter(generator_name: str, args: dict[str, Any]) -> int:

    metadata = common_metadata.CommonMetadata(args)
    footprint_name = args["name"]
    fptag = args["tags"]
    SmdTht = str(args["smd_tht"])
    at = Vector2D(args["at"])
    size = Vector2D(args["size"])
    pins = args["pins"]
    extratexts = args["extratexts"]
    body_position_tolerance = Vector2D(args["body_position_tolerance"])
    body_size_tolerance = Vector2D(args["body_size_tolerance"])
    courtyard = float(args["courtyard"])
    automatic_pin1_mark = bool(args["automatic_pin1_mark"])

    arrow_points = arrow_nesw_from_str(args["arrow_points"])

    # Until this can be passed in properly, use the default global config
    global_cfg = global_config.GLOBAL_CONFIG

    # This a very naive way of calculating the total tolerance referenced to the
    # origin, but it's a start
    total_body_tolerance = body_position_tolerance + body_size_tolerance

    # Clearance from the _nominal_ body to the courtyard _centreline_
    courtyard_clearance = total_body_tolerance + Vector2D(courtyard, courtyard)
    # Clearance from the _nominal_ body to the _inside_ of the silk line
    fab_to_silk_clearance = total_body_tolerance

    if not metadata.library_name:
        raise ValueError("Library name is required in the metadata.")

    if not metadata.description:
        raise ValueError("Description is required in the metadata.")

    dir3D = metadata.library_name + '.3dshapes'

    footprint_type = FootprintType.SMD if SmdTht == "smd" else FootprintType.THT
    f = Footprint(footprint_name, footprint_type)

    model_filename = global_cfg.model_3d_prefix + dir3D + "/" + footprint_name + global_cfg.model_3d_suffix

    words = footprint_name.split("_")

    if words[-1].lower().startswith('handsolder'):
        words[-1] = ''
        ff = '_'.join(words)
        model_filename = global_cfg.model_3d_prefix + dir3D + "/" + ff + global_cfg.model_3d_suffix

    descr: list[str] = [
        metadata.description,
    ]
    if metadata.datasheet:
        descr.append(metadata.datasheet)

    f.description = ", ".join(descr)

    f.tags = fptag.split() + metadata.compatible_mpns

    table_factory = TablePadFactory(pins)

    offset = size / 2 + Vector2D(at.x, -at.y)

    min_body_size = size.min_val

    # Basic heuristic to determine the silk arrow size based on the body size
    if min_body_size < 4:
        silk_arrow_size = SilkArrowSize.MEDIUM
    elif min_body_size < 10:
        silk_arrow_size = SilkArrowSize.LARGE
    else:
        silk_arrow_size = SilkArrowSize.HUGE

    layout = NPadBoxLayout(
        global_config=global_cfg,
        body_size=size,
        body_offset=offset,
        pad_factory=table_factory,
        silk_style=SilkStyle.TIGHT,
        is_polarized=automatic_pin1_mark,
        footprint_name=f.name,
        body_to_courtyard_clearance=courtyard_clearance,
        additional_silk_clearance=fab_to_silk_clearance,
        silk_arrow_direction_if_inside=arrow_points,
        silk_arrow_size=silk_arrow_size,
    )

    f += layout

    f += build_extra_texts(extratexts)

    f += Model(filename=model_filename)

    write_footprint(f, metadata.library_name, generator_name)
    return 1


def main(generator_name: str, args: list[str] | None = None) -> int:
    ipc_default_courtyard_clearance = 0.25

    # parse arguments using optparse or argparse or what have you
    parser = ModArgparser(converter)
    # the root node of .yml files is parsed as name
    parser.add_parameter("library_name", type=str, required=True)
    parser.add_parameter("name", type=str, required=True)
    parser.add_parameter("description", type=str, required=True)
    parser.add_parameter("datasheet", type=str, required=True)
    parser.add_parameter("tags", type=str, required=True)
    parser.add_parameter("compatible_mpns", type=list, required=False)
    parser.add_parameter("smd_tht", type=str, required=False, default='tht')
    parser.add_parameter("at", type=list, required=True)
    parser.add_parameter("size", type=list, required=False)
    parser.add_parameter("pins", type=list, required=True)
    # Maximum body position deviation in each axis
    parser.add_parameter("body_position_tolerance", type=list, required=False, default=[0, 0])
    # Maximum body size deviation in each axis from the given nominal size
    parser.add_parameter("body_size_tolerance", type=list, required=False, default=[0, 0])
    # Courtyard outside the maximum body extent (i.e. not including the body tolerance)
    parser.add_parameter("courtyard", type=float, required=False, default=ipc_default_courtyard_clearance)
    parser.add_parameter("extratexts", type=list, required=False, default=[])
    parser.add_parameter("automatic_pin1_mark", type=bool, required=False, default=True)
    parser.add_parameter("arrow_points", type=str, required=False)

    # now run our script which handles the whole part of parsing the files
    return parser.run(generator_name, args)


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
