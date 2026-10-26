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

def add_bump(m, anchor_pos, bump_length, bump_width, direction, layer, width, offset=(0, 0)):

    if direction == 'up':
        delta_x = bump_length
        delta_y = -bump_width
        start_x = anchor_pos[0]
        start_y = anchor_pos[1] - offset[1]
    elif direction == 'down':
        delta_x = bump_length
        delta_y = bump_width
        start_x = anchor_pos[0]
        start_y = anchor_pos[1] + offset[1]
    elif direction == 'left':
        delta_x = -bump_width
        delta_y = bump_length
        start_x = anchor_pos[0] - offset[0]
        start_y = anchor_pos[1]
    elif direction == 'right':
        delta_x = bump_width
        delta_y = bump_length
        start_x = anchor_pos[0] + offset[0]
        start_y = anchor_pos[1]
    else:
        return m

    if direction in ['up', 'down']:
        polygon_line = [
                         {'x': start_x - delta_x / 2.0, 'y': start_y },
                         {'x': start_x - delta_x / 2.0, 'y': start_y + delta_y},
                         {'x': start_x + delta_x / 2.0, 'y': start_y + delta_y},
                         {'x': start_x + delta_x / 2.0, 'y': start_y} ]
    else:
        polygon_line = [
                         {'x': start_x, 'y': start_y - delta_y / 2.0 },
                         {'x': start_x + delta_x, 'y': start_y - delta_y / 2.0},
                         {'x': start_x + delta_x, 'y': start_y + delta_y / 2.0},
                         {'x': start_x, 'y': start_y + delta_y / 2.0} ]
    m.append(PolygonLine(shape=polygon_line, layer=layer, width=width))

    return m
