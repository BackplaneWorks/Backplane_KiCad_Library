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

# Kicad currently does not support adding keepout zones directly to footprints
# For this reason the library maintenance team decided to communicate keepouts as follows:
#  - A polygon outlining the keepout area (on layer Dwgs.User)
#  - Hatching of this area on the same layer
#  - Text on Cmts.User: KEEPOUT (with additional information if necessary)

from math import sqrt

from KicadModTree import *  # NOQA


KEEPOUT_DEFAULT_CONFIG={
    'graphical_layer':'Dwgs.User',
    'line_width': 0.1,
    'hatching_spacing': 2,
    'text':{
        'size':[1,1],
        'fontwidth':0.15,
        'position':'center',
        'layer':'Cmts.User'
    }
}
def addRectangularKeepout(kicad_mod, center, size, text='KEEPOUT', config=KEEPOUT_DEFAULT_CONFIG):
    keepout_edges={
        'left': center[0] - (size[0] / 2),
        'top': center[1] - (size[1] / 2)
    }
    keepout_edges['right'] = keepout_edges['left'] + size[0]
    keepout_edges['bottom'] = keepout_edges['top'] + size[1]
    kicad_mod.append(Rectangle(
        start=[keepout_edges['left'], keepout_edges['top']],
        end=[keepout_edges['right'], keepout_edges['bottom']],
        layer=config['graphical_layer'], width=config['line_width']))

    if size[0] >= size[1]:
        rot = 0
        longer_size = size[0]
    else:
        longer_size = size[1]
        rot = 90

    fs = round(longer_size/len(text), 2)
    if fs > config['text']['size'][0]:
        size = config['text']['size']
        thickness = config['text']['fontwidth']
    else:
        size = [fs, fs]
        thickness = config['text']['fontwidth'] * fs


    kicad_mod.append(Text(text=text,
        at=center, rotation=rot,
        layer=config['text']['layer'], size=size,
        thickness=thickness))


    p1 = {'x':keepout_edges['left'], 'y':keepout_edges['top']}
    p2 = {'x':keepout_edges['left'], 'y':keepout_edges['top']}
    # 45° hatching
    step = config['hatching_spacing']
    step_x = step/sqrt(2)
    step_y = step_x

    p1_direction = 'move_right'
    p2_direction = 'move_down'

    while (1):
        if p1_direction == 'move_right':
            p1['x'] += step_x
            if p1['x'] > keepout_edges['right']:
                p1_direction = 'move_down'
                dx = keepout_edges['right'] - (p1['x'] - step_x)
                dy = step_y - dx
                p1['x'] = keepout_edges['right']
                p1['y'] += dy
        else:
            p1['y'] += step_y


        if p2_direction == 'move_down':
            p2['y'] += step_y
            if p2['y'] > keepout_edges['bottom']:
                p2_direction = 'move_right'
                dy = keepout_edges['bottom'] - (p2['y'] - step_y)
                dx = step_x - dy
                p2['x'] += dx
                p2['y'] = keepout_edges['bottom']
        else:
            p2['x'] += step_x

        if p1['y'] > keepout_edges['bottom']:
            return

        kicad_mod.append(Line(start=p1, end=p2,
            layer=config['graphical_layer'], width=config['line_width']))
