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

from KicadModTree import *  # NOQA

def add_corners(m, start_pos, end_pos, size_x, size_y, layer, width, offset=(0, 0), chamfers=[]):

    # If specified, an 'offset' can be applied to the corners.
    # For example, creating corners around a given Rectangle of a specified size
    # offset for the rect line

    # For the offset to work properly, start-pos must be top-left, and end-pos must be bottom-right
    x1 = min(start_pos[0], end_pos[0])
    x2 = max(start_pos[0], end_pos[0])
    y1 = min(start_pos[1], end_pos[1])
    y2 = max(start_pos[1], end_pos[1])

    # Put the offset (if any) back in
    start_pos[0] = x1 - offset[0]
    start_pos[1] = y1 - offset[1]
    end_pos[0] = x2 + offset[0]
    end_pos[1] = y2 + offset[1]

    if 'topleft' in chamfers:
        m.append(Line(start=[start_pos[0], start_pos[1] + size_y], end=[start_pos[0] + size_x, start_pos[1]], layer=layer, width=width))
    else:
        m.append(Line(start=[start_pos[0], start_pos[1]], end=[start_pos[0] + size_x, start_pos[1]], layer=layer, width=width))
        m.append(Line(start=[start_pos[0], start_pos[1]], end=[start_pos[0], start_pos[1] + size_y], layer=layer, width=width))

    if 'bottomleft' in chamfers:
        m.append(Line(start=[start_pos[0], end_pos[1] - size_y], end=[start_pos[0] + size_x, end_pos[1]], layer=layer, width=width))
    else:
        m.append(Line(start=[start_pos[0], end_pos[1]], end=[start_pos[0] + size_x, end_pos[1]], layer=layer, width=width))
        m.append(Line(start=[start_pos[0], end_pos[1]], end=[start_pos[0], end_pos[1] - size_y], layer=layer, width=width))

    if 'topright' in chamfers:
        m.append(Line(start=[end_pos[0], start_pos[1] + size_y], end=[end_pos[0] - size_x, start_pos[1]], layer=layer, width=width))
    else:
        m.append(Line(start=[end_pos[0], start_pos[1]], end=[end_pos[0] - size_x, start_pos[1]], layer=layer, width=width))
        m.append(Line(start=[end_pos[0], start_pos[1]], end=[end_pos[0], start_pos[1] + size_y], layer=layer, width=width))

    if 'bottomright' in chamfers:
        m.append(Line(start=[end_pos[0], end_pos[1] - size_y], end=[end_pos[0] - size_x, end_pos[1]], layer=layer, width=width))
    else:
        m.append(Line(start=[end_pos[0], end_pos[1]], end=[end_pos[0] - size_x, end_pos[1]], layer=layer, width=width))
        m.append(Line(start=[end_pos[0], end_pos[1]], end=[end_pos[0], end_pos[1] - size_y], layer=layer, width=width))

    return m

