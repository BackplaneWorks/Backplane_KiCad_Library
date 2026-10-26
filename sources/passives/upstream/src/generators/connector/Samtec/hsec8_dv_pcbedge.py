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
# This file is heavily inspired from the MECF card edge generator by @poeschlr
# (C) Original author: Armin Schoisswohl @armin.sch
# (C) The KiCad Librarian Team

# PCB card edge footprint generator for Samtec's HSEC8 0.8mm pitch edge card connector family.
#
# Sources:
#   https://suddendocs.samtec.com/prints/hsec8-1xxx-xx-xx-dv-x-xx-x-xx-mkt.pdf
#   https://suddendocs.samtec.com/prints/hsec8-1xxx-xx-xx-dv-x-xx-footprint.pdf

from typing import Any
from KicadModTree import Footprint, FootprintType, Line, Text, Arc, Pad, Rectangle
from generators.tools.footprint.drawing_tools import round_to_grid
from generators.tools.footprint.footprint_text_fields import addTextFields
from generators.tools.footprint.save_footprint import write_footprint
from kilibs.config import global_config as GC


lib_name_category = 'Samtec_HSEC8'

pad_pitch = 0.8

# Table 1: A/B for options -10, -20, -30 are equal to E/J in Table 3 below, *-13 is not generated
# Table 2
C = { '01': 4.6, '02': 5.03, '03': 5.39 }
D = { k: c + 2.4 for k, c in C.items() } # equals T in package drawing
# Table 3: A/B for options -10, -20, -30 are equal to E/J below, *-13 is not generated
F = {
    9: 3,
    10: None,
    13: 5,
    20: None,
    25: 5,
    30: None,
    37: 20,
    40: 21,
    49: 26,
    50: 26,
    60: 31,
    70: 31,
    80: 31,
    90: 31,
    100: 31,
}
E = { n: pad_pitch * (n - 1) + (3.2 if f else 0.0) for n, f in F.items() }
G = { n: pad_pitch * f if f else None for n, f in F.items() }
H = { n: (n - f - 2) if f else (n - 1) for n, f in F.items() }
I = { n: pad_pitch * h for n, h in H.items() }
J = { n: e + 3.0 for n, e in E.items() }
# Table 4 & 5: K equals L for -10, -20, -30
L = { n: e + 7.7 for n, e in E.items() }
# Tables 6 & 9: option -L not generated
# Table 7: option -PE not generated
# Table 8: option -L2 not generated
# Table 10 & 11: S/T equal K/L of tables 4 & 5
# Table 12: option -L2 not generated

# Table 13:
W = { n: f for n, f in F.items() } # W equals F
V = {n: pad_pitch * (n - 1) + ((4.0 - pad_pitch) if w else 0.0) for n, w in W.items()}
X = {n: (pad_pitch * w) if w else None for n, w in W.items()}
Y = {n: v + 2.05 for n, v in V.items()}
Z = {n: (x + 2.0) if x else None for n, x in X.items()}
AA = {n: y + 9.0 for n, y in Y.items()}
AB = {n: y + 5.0 for n, y in Y.items()}
# Table 14: PCB thickness
AC = { k: ac - 3.03 for k, ac in C.items() }
# Table 15 & 16: option -PE not generated

__tables__ = {
    2: ['C', 'D'],
    3: ['E', 'F', 'G', 'H', 'I', 'J'],
    5: ['L'],
    13: ['V', 'W', 'X', 'Y', 'Z', 'AA', 'AB'],
    14: ['AC'],
}

pad_size = [0.55,2.80]

pinrange = sorted(V.keys())


def generate_one_footprint(generator_name: str, global_config: GC.GlobalConfig, positions: int, variant: str, configuration):
    CrtYd_offset = configuration['courtyard_offset']['default']
    option = '-BL' if (variant == 'lock') else ''
    fp_name = 'Samtec_HSEC8-1%02d-X-X-DV%s_2x%02d_P0.8mm' % (positions, option, positions)
    if (variant == 'wing'):
        fp_name += "_Wing"
    fp_name += "_Edge"

    kicad_mod = Footprint(fp_name, FootprintType.UNSPECIFIED)

    kicad_mod.excludeFromBOM = True
    kicad_mod.excludeFromPositionFiles = True

    description = "Highspeed card edge for PCB's with 2x%d contacts%s" % (positions, {'': '', 'wing': ' (with horizontal Edge.Cuts ends)', 'lock':' (with board lock option)'}[variant])
    #set the FP description
    kicad_mod.setDescription(description)

    tags = "conn samtec card-edge high-speed"

    #set the FP tags
    kicad_mod.setTags(tags)


    # set general values
    top = -6.4
    bot = 0.0

    left = -(Y[positions] / 2.0)
    right = (Y[positions] / 2.0)
    body_edge={
        'left': left,
        'right': right,
        'top': top,
        'bottom': bot
    }

    # create Fab & Silk (exact outline)
    for layer in [ 'F.Fab', 'B.Fab', 'F.SilkS', 'B.SilkS' ]:
        props = {'layer': layer, 'width': configuration['silk_line_width' if layer.endswith('.SilkS') else 'fab_line_width']}
        chamfer = 1.27 if layer.startswith('F.') else 0.0
        kicad_mod.append(Line(start=[left, top + chamfer], end=[left + chamfer, top], **props))   # pin 1 corner
        kicad_mod.append(Line(start=[left + chamfer, top], end=[right, top], **props))   #top line
        if layer.endswith('.Fab'):
            kicad_mod.append(Line(start=[left, bot], end=[ right, bot], **props))   #bot line
            kicad_mod.append(Line(start=[left, top + chamfer], end=[left, bot], **props))   #left line
            kicad_mod.append(Line(start=[right, top], end=[ right, bot], **props))   #right line
            kicad_mod.append(Line(start=[left, bot - 0.88], end=[right, bot - 0.88], **props))   #PCBedge chamfer line

    top = round_to_grid(body_edge['top'] - CrtYd_offset, configuration['courtyard_grid'])
    bot = round_to_grid(body_edge['bottom'] + CrtYd_offset, configuration['courtyard_grid'])
    left = round_to_grid(body_edge['left'] - CrtYd_offset, configuration['courtyard_grid'])
    right = round_to_grid(body_edge['right'] + CrtYd_offset, configuration['courtyard_grid'])

    cy1 = top
    cy2 = bot

    # create courtyards
    for layer in ['F.CrtYd', 'B.CrtYd']:
        kicad_mod.append(Rectangle(start=[left, top], end=[right, bot], layer=layer, width=configuration['courtyard_line_width']))

    top = body_edge['top']
    bot = body_edge['bottom']

    ## create cutout
    props = {'layer': 'Edge.Cuts', 'width': configuration['edge_cuts_line_width']}
    kicad_mod.append(Line(start=[-Y[positions] / 2, bot - 5.0], end=[-Y[positions] / 2, bot], **props)) # left edge
    if (X[positions] is None): # no notch
        kicad_mod.append(Line(start=[-Y[positions] / 2, bot], end=[Y[positions] / 2, bot], **props)) # top edge
    else: # notch
        notch_center = -Y[positions] / 2 + 1.03 + Z[positions]
        notch_left = notch_center - 1.2
        notch_right = notch_center + 1.2
        kicad_mod.append(Line(start=[-Y[positions] / 2, bot], end=[notch_left, bot], **props)) # top edge to start of notch
        kicad_mod.append(Line(start=[notch_left , bot], end=[notch_left, bot - 5.2], **props)) # left edge of notch
        kicad_mod.append(Arc(center=[notch_center, bot - 5.2], start=[notch_left, bot - 5.2], angle=180, **props)) # rounded part of notch
        kicad_mod.append(Line(start=[notch_right , bot - 5.2], end=[notch_right, bot], **props)) # right edge of notch
        kicad_mod.append(Line(start=[notch_right , bot], end=[Y[positions] / 2, bot], **props)) # top edge from notch to right
    kicad_mod.append(Line(start=[Y[positions] / 2, bot], end=[Y[positions] / 2, bot - 5.0], **props)) # right edge
    if (variant in ['wing', 'lock']):
        for sign in [1, -1]:
            kicad_mod.append(Arc(center=[sign * (Y[positions] / 2 + 1.0), bot - 5.0], start=[sign * Y[positions] / 2, bot - 5.0], angle=90 * sign, **props)) # rounded part of notch
    if (variant == 'lock'):
        for sign in [1, -1]:
            kicad_mod.append(Line(start=[sign * (Y[positions] / 2 + 1.0), bot - 6.0], end=[sign * AA[positions] / 2, bot - 6.0], **props)) # rounded part of notch
            kicad_mod.append(Line(start=[sign * AA[positions] / 2, bot - 6.0], end=[sign * AA[positions] / 2, bot - 7.38], **props)) # rounded part of notch
            kicad_mod.append(Arc(center=[sign * (AA[positions] / 2 - 0.4), bot - 7.38], start=[sign * AA[positions] / 2, bot - 7.38], angle=-90 * sign, **props)) # rounded part of notch
            kicad_mod.append(Line(start=[sign * (AA[positions] / 2 - 0.4), bot - 7.78], end=[sign * (AB[positions] / 2 - 1.0), bot - 7.78], **props)) # rounded part of notch
            kicad_mod.append(Arc(center=[sign * (AB[positions] / 2 - 1.0), bot - 8.78], start=[sign * (AB[positions] / 2 - 1.0), bot - 7.78], angle=90 * sign, **props)) # rounded part of notch

    ## create pads (and some numbers on silk for orientation)
    fontsize = 0.75
    start = -V[positions] / 2
    for i in range(0, positions):
        off = 4.0 - pad_pitch if W[positions] and i > W[positions] else 0.0
        for idx, layer in enumerate([Pad.LAYERS_CONNECT_FRONT, Pad.LAYERS_CONNECT_BACK]):
            kicad_mod.append(Pad(number=2 * i + idx + 1, type=Pad.TYPE_CONNECT, shape=Pad.SHAPE_RECT,
                                 at=[start + i * pad_pitch + off, bot - 3.8 + pad_size[1]/2], size=pad_size, layers=layer))
        if (i in [0, positions - 1]) or (W[positions] and (i - W[positions]) in [0, 1]):
            align = 0 if (i == 0 or i - 1 == W[positions]) else 1
            for idx, layer in enumerate(['F.SilkS', 'B.SilkS']):
                lbl = '%d' % (2 * i + idx + 1)
                kicad_mod.append(Text(text=lbl, at=[start + i * pad_pitch + off + (-1)**align * fontsize * (len(lbl) - 1) / 2, bot - 3.8 - fontsize], layer=layer, mirror=idx, size=[fontsize, fontsize]))

    ## create some useful additional information on User.Comments layer
    kicad_mod.append(Text(text="Chamfer 30 degree 0.45 mm", at=[0, bot - 0.44], layer='Cmts.User', size=[fontsize, fontsize]))
    if ('-BL' in option):
        mate_distance = zip([1.8], ['ref'])
    else:
        mate_distance = zip([2.05, 3.69], ['min', 'max'])
    for dist, name in mate_distance: # see https://suddendocs.samtec.com/prints/hsec8%20mated%20document-mkt.pdf Table 1
        kicad_mod.append(Line(start=[body_edge['left'], body_edge['bottom'] + dist], end=[body_edge['left'] + 2.5, body_edge['bottom'] + dist], width=configuration['fab_line_width'], layer='Cmts.User'))
        kicad_mod.append(Text(text="mated PCB distance: %.2f mm (%s)" % (dist, name), at=[left + 3, bot + dist], layer='Cmts.User', size=[fontsize, fontsize], justify='left'))

    # TODO: add keepout area on inner layers near chamfered edges
    # this requires to create a new Zone node in the KicadModTree to add something like:
    #
    #  kicad_mod.append(Zone(nodes=[[-Y[positions] / 2, bot - 1.0], [Y[positions] / 2, bot - 1.0], [Y[positions] / 2, bot], [-Y[positions] / 2, bot]], layer='Inner Layers', etc etc))
    #

    ######################### Text Fields ###############################
    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
                  courtyard={'top':cy1, 'bottom':cy2}, fp_name=fp_name, text_y_inside_position=-2.54)

    lib_name = configuration['lib_name_specific_function_format_string'].format(category=lib_name_category)


    write_footprint(kicad_mod, lib_name, generator_name)


def print_table(table_num: int = None):

    v2s = lambda v: "%.2f" % v if isinstance(v, float) else "%d" % v if isinstance(v, int) else "n/a" if v is None else str(v)
    k2s = lambda v: "-%02d" % v if isinstance(v, int) else str(v)

    fmts = []
    values = []
    hdr = []
    for col in __tables__[table_num]:
        values.append(globals().get(col))
        for v in values[-1].values():
            if isinstance(v, int):
                fmts.append('%3s')
                hdr.append(" %-2s" % col)
            elif isinstance(v, float):
                fmts.append('%5s')
                hdr.append("  %-3s" % col)
            else:
                continue
            break
    fmt = "| %-4s | " + (" | ".join(fmts)) + " |"

    print("Table %d: https://suddendocs.samtec.com/prints/hsec8-1xxx-xx-xx-dv-x-xx-footprint.pdf" % table_num)
    print("|      | " + (" | ".join(hdr)) + " |")
    print("|------|" + ("|".join("-" * (len(h) + 2) for h in hdr)) + "|")
    for k in sorted(values[0].keys()):
        print(fmt % ((k2s(k),) + tuple(v2s(v[k]) for v in values)))
    print("")


def generate_all(generator_name: str, global_config: GC.GlobalConfig, configuration: dict[str, Any]) -> int:
    num_fps_generated = 0
    for variant in ['', 'wing', 'lock']:
        for positions in pinrange:
            generate_one_footprint(generator_name, global_config, positions, variant, configuration)
            num_fps_generated += 1
    return num_fps_generated
