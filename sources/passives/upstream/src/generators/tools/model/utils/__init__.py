#!/usr/bin/env python3

# CadQuery Helper Functions
#
# Copyright (C) 2025 Martin Sotirov <martin@libtec.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import math

import cadquery as cq


def as_list(v):
    if type(v) is list:
        return v
    else:
        return [v]


class V2:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __getitem__(self, i):
        return [self.x, self.y][i]

    def __repr__(self):
        return f"V({self.x}, {self.y})"

    def __add__(self, v):
        if type(v) is V2:
            return V2(self.x + v.x, self.y + v.y)
        else:
            return V2(self.x + v, self.y + v)

    def __sub__(self, v):
        if type(v) is V2:
            return V2(self.x - v.x, self.y - v.y)
        else:
            return V2(self.x - v, self.y - v)

    def __mul__(self, v):
        if type(v) is V2:
            return V2(self.x * v.x, self.y * v.y)
        else:
            return V2(self.x * v, self.y * v)

    def dist(self, v):
        return math.sqrt((self.x - v.x) ** 2 + (self.y - v.y) ** 2)

    def normalized(self):
        d = self.dist(V2(0, 0))
        return V2(self.x / d, self.y / d)

    @staticmethod
    def from_angle(a):
        return V2(math.cos(a), math.sin(a))


class Line:
    def __init__(self, m, b):
        self.m = m  # slope
        self.b = b  # intercept

    def get_line_intersection(self, l):
        x = (l.b - self.b) / (self.m - l.m)

        if abs(self.m) < 10000:
            y = self.m * x + self.b
        else:
            y = l.m * x + l.b

        return V2(x, y)


def get_side_to_tip_corner(side, tip, pt, ccw):
    w = side.x - tip.x
    h = side.y - tip.y
    a = math.atan2(h, w)

    tri_c = math.sqrt(w * w + h * h)
    tri_a = pt / 2
    tri_b = math.sqrt(tri_c**2 - tri_a**2)

    tri_B = math.asin(tri_b / tri_c)

    if ccw:
        tip_a = a + tri_B
    else:
        tip_a = a - tri_B

    corner = tip + V2(math.cos(tip_a), math.sin(tip_a)) * (pt / 2)

    return corner


def get_back_side(p0, p1, p2, th):
    # Get angles
    a0 = math.atan2(p0.y - p1.y, p0.x - p1.x)
    a1 = math.atan2(p2.y - p1.y, p2.x - p1.x)
    if a0 < 0:
        a0 += math.pi * 2
    if a1 < 0:
        a1 += math.pi * 2

    # Get perpendiculars
    pa0 = a0 + math.pi / 2
    pa1 = a1 - math.pi / 2

    # Get back points
    p0_b = p1 + V2(math.cos(pa0), math.sin(pa0)) * th
    p1_b = p1 + V2(math.cos(pa1), math.sin(pa1)) * th

    # Get back lines
    m0 = math.tan(a0)
    m1 = math.tan(a1)
    l0 = Line(m0, p0_b.y - p0_b.x * m0)
    l1 = Line(m1, p1_b.y - p1_b.x * m1)

    # Get back corner
    c = l0.get_line_intersection(l1)

    return c


def make_rounded_corner(body, p0, p1, p2, r):
    # Make a sharp corner if the corner radius is too small:
    if r <= 0:
        body = body.lineTo(p1.x, p1.y)
        return body, p1

    # Get side angles:
    a0 = math.atan2(p0.y - p1.y, p0.x - p1.x)
    a1 = math.atan2(p2.y - p1.y, p2.x - p1.x)
    m0 = math.tan(a0)
    m1 = math.tan(a1)

    # Get corner angle:
    ca = a0 - a1
    if ca < 0:
        ca += math.pi * 2

    # Get side perpendicular angles depending on the corner direction:
    if ca < math.pi:
        pa0 = a0 - math.pi / 2
        pa1 = a1 + math.pi / 2
    else:
        pa0 = a0 + math.pi / 2
        pa1 = a1 - math.pi / 2

    # Get side perpendiculars:
    pp0 = V2.from_angle(pa0) * r
    pp1 = V2.from_angle(pa1) * r
    pb0 = p1 + pp0
    pb1 = p1 + pp1

    # Get corner arc center:
    l0 = Line(m0, pb0.y - pb0.x * m0)
    l1 = Line(m1, pb1.y - pb1.x * m1)
    c = l0.get_line_intersection(l1)

    # Get arc start and end points:
    s = c - pp0
    e = c - pp1

    # Reverse the arc direction depending on the corner direction:
    if ca < math.pi:
        r = -r

    # Draw a line to arc start if necessary:
    if p0.dist(s) > 0.00001:
        body = body.lineTo(*s)

    # Draw the rounded corner:
    body = body.radiusArc(tuple(e), r)

    return body, e


def make_rounded_corner_th(body, p0, p1, p2, r, th):
    # Get side angles:
    a0 = math.atan2(p0.y - p1.y, p0.x - p1.x)
    a1 = math.atan2(p2.y - p1.y, p2.x - p1.x)

    # Get angle between sides:
    ca = a0 - a1
    if ca < 0:
        ca += math.pi * 2

    # Reduce corner radius by the thickness if it's an inner corner:
    if ca < math.pi:
        r -= th

    return make_rounded_corner(body, p0, p1, p2, r)


def make_rounded_corner_shape(workplane, p, r):
    p = p.copy()
    r = r.copy()

    r += [r[-1]] * (len(p) - len(r))

    p.insert(0, V2(0, p[0].y))
    p.append(V2(0, p[-1].y))
    p.append(p[0])
    r.append(0)

    body = workplane.moveTo(*p[0])
    prev = p[0]
    for i in range(1, len(p) - 1):
        if p[i].dist(prev) < 0.00001:
            p[i] = prev
            continue

        body, prev = make_rounded_corner(body, prev, p[i], p[i + 1], r[i - 1])

    body = body.close()

    return body


def _make_operation(body, edges, val, func_name):
    if not val:
        return body

    body = body.edges(edges)
    body = getattr(body, func_name)(val)

    return body


def make_chamfer(body, edges, val):
    return _make_operation(body, edges, val, "chamfer")


def make_fillet(body, edges, val):
    return _make_operation(body, edges, val, "fillet")


def make_asymmetric_chamfer(body, chamfer, w, d, pos, a):
    if not chamfer:
        return

    w0 = w / 2 - chamfer[0]
    w1 = w / 2
    y0 = 0
    y1 = chamfer[1]

    if w0 < 0:
        raise ValueError(f"Chamfer is too big")

    cut = cq.Workplane("YX")
    cut = cut.moveTo(-w0, y0)
    cut = cut.lineTo(-w1, y0)
    cut = cut.lineTo(-w1, y1)
    cut = cut.close()
    cut = cut.moveTo(w0, y0)
    cut = cut.lineTo(w1, y0)
    cut = cut.lineTo(w1, y1)
    cut = cut.close()
    cut = cut.extrude(d / 2, both=True)
    cut = cut.rotate((0, 0, 0), (0, -1, 0), a)
    cut = cut.translate(tuple(pos))

    body = body.cut(cut)

    return body


def _make_z_edges_action(body, values, action):
    if values is None:
        return body

    if type(values) is not list:
        values = [values] * 4

    if len(values) != 4:
        raise ValueError("Either on number or 4 numbers must be provided")

    edges = [
        "|Z and >X and >Y",
        "|Z and >X and <Y",
        "|Z and <X and <Y",
        "|Z and <X and >Y",
    ]

    for edge, value in zip(edges, values):
        if not value:
            continue

        body = body.edges(edge)
        body = getattr(body, action)(value)

    return body


def make_z_chamfers(body, chamfers):
    return _make_z_edges_action(body, chamfers, "chamfer")


def make_z_fillets(body, fillets):
    return _make_z_edges_action(body, fillets, "fillet")
