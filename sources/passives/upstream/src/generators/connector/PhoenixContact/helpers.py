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

def v_add(p1,p2):
    return [p1[0]+p2[0],p1[1]+p2[1]]

def offset_dir(coordinate, offset, center=0):
    if coordinate > center:
        return coordinate + offset
    elif coordinate< center:
        return coordinate - offset
    else:
        return coordinate

def v_offset(point, offset, center = (0,0)):
    if type(center) is dict:
        center_x = float(center.get('x', 0.))
        center_y = float(center.get('y', 0.))
    else:
        center_x=center[0]
        center_y=center[1]

    if type(point) is dict:
        result={}
        result['x']=offset_dir(float(point.get('x', 0.)), offset, center_x)
        result['y']=offset_dir(float(point.get('y', 0.)), offset, center_y)
        return result

    return [
        point[0] + (offset if point[0] >=center_x else -offset),
        point[1] + (offset if point[1] >=center_y else -offset)
    ]

def offset_polyline(polyline_points, offset, center=(0,0)):
    resulting_points = []
    for point in polyline_points:
        resulting_points.append(v_offset(point,offset,center))

    return resulting_points

def create_pin1_marker_triangle(bottom_y, center_x = 0, dimensions = [0.6,0.6], with_top_line = True):
    marker_width = dimensions[0]
    marker_height = dimensions[1]

    marker_top=bottom_y-marker_height
    marker_poly=[
        {'x':center_x+marker_width/2, 'y':marker_top},
        {'x':center_x, 'y':bottom_y},
        {'x':center_x-marker_width/2, 'y':marker_top}
    ]
    if with_top_line:
        marker_poly.append({'x':center_x+marker_width/2, 'y':marker_top})
    return marker_poly

def create_pin1_marker_corner(top_y, left_x, sidelength = [1,1]):
    marker_poly=[
        {'x':left_x, 'y':top_y + sidelength[1]},
        {'x':left_x, 'y':top_y},
        {'x':left_x + sidelength[0], 'y':top_y}
    ]

    return marker_poly
