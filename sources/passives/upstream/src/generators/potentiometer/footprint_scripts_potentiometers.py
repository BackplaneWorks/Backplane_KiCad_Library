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

import math

from KicadModTree import *  # NOQA
from generators.tools.footprint.drawing_tools import *
from generators.tools.footprint.footprint_global_properties import *
from kilibs.config import global_config as GC
from generators.tools.footprint.save_footprint import write_footprint

global_config = GC.GLOBAL_CONFIG


'''
An external argument interface is provided.
It should be used to make footprints part-by-part as needed.
Only minimal testing and error checking provided!

Separate scripts are provided to make "off the shelf" pots using these functions.
See make_Potentiometer_SMD.py and make_Potentiomter_THT.py

'''

def makePotentiometerHorizontal(generator_name, class_name="", wbody=0, hbody=0, dscrew=0, style="normal", ddrill=0,
                              wscrew=0, wshaft=0, dshaft=0,
                              pinxoffset=0, pinyoffset=0, pins=3, R_POW=0, x_3d=[0, 0, 0], s_3d=[1, 1, 1], r_3d=[0, 0, 0], has3d=1,
                              rmx=5.08, rmy=5.08,
                              specialtags=[], add_description="", lib_name="Potentiometer", name_additions=[],
                              height3d=10, screwzpos=5, mh_ddrill=1.5, mh_count=0, mh_rmx=0, mh_rmy=15, mh_xoffset=0, mh_yoffset=0):
    """
    create potentiometer footprints, horizontally mounted

    style="normal":
            ^   ^      +-----------+
     pinyoffset |      |           |
            v   |   ^  |   O1   O4 +-------+                                              ^
                | rmy  |           |       +-------------------------------+ ^            |
                |   v  |   O2   O5 |       |                               | dshaft       |
                |      |           |       +-------------------------------+ v            dscrew
                hbody  |   O3   O6 +-------+                                              v
                |      |           |
                v      +-----------+       <----------wshaft--------------->
                            <rmx>  <------->wscrew
                       <---wbody--->
                                 <->pinxoffset


    style="trimmer" (only valid for 3-pin!!!):
        O1           ^
                     rmy
                O2   v

        O3
         <-rmx-->

    Parameters:
        class_name: manufacturer and MPN like "Bourns 3214W" (str)
        wbody: body length (float)
        hbody: body height (float)
        wscrew: collar length (float)
        dscrew: collar diameter (float)
        wshaft: shaft length (float)
        dshaft: shaft diameter (float)
        style: type of pot from "normal" or "trimmer" [default = "normal"] (str)
        pinxoffset: distance from face of body to first column of pins [default = 0] (float)
        pinyoffset: distance from top of body to first row of pins [default = 0] (float)
        pins: number of pins; "trimmer" style can only support 3 pins [default = 3] (int)
        rmx: column spacing of pins [default = 5.08] (float)
        rmy: row (or vertical) spacing of pins [default = 5.08] (float)
        ddrill: drill hole diameter [default = 1.5] (float)
        R_POW: power rating of pot with zero being default [default = 0] (float)
        x_3d: 3D model location [default = [0, 0, 0]] (list of floats)
        s_3d: 3D model scaling [default = [1 / 2.54, 1 / 2.54, 1 / 2.54]] (list of floats)
        r_3d: 3D model rotation [default = [0, 0, 0]] (list of floats)
        has3d: presence of 3D model [default = 1] (bool)
        specialtags: keywords that will be comma-delimited [default = []] (list of strs)
        add_description: descriptive text [default = ""] (str)
        lib_name: library name [default = "Potentiometers"] (str)
        name_additions: extra text for footprint name that will be underscore-delimited [default = []] (list of strs)
        height3d: height of 3D model [default = 10] (float)
        screwzpos: height of collar above bottom of body [default = 5] (float)
        mh_ddrill: drill hole diameter of mounting holes [default = 1.5] (float)
        mh_count: number of mounting holes; 1, 2, or 4 are supported [default = 0] (int)
        mh_rmx: column spacing of mounting holes [default = 0] (float)
        mh_rmy: row spacing of mounting holes [default = 15] (float)
        mh_xoffset: distance from face of body to first column of mounting holes [default = 0] (float)
        mh_yoffset: distance from top of body to first row of mounting holes [default = 0] (float)

    Returns:
        None
    """

    padx = 1.8 * ddrill
    pady = padx
    txt_offset = 1
    slk_offset = global_config.silk_fab_offset
    grid_crt = global_config.courtyard_grid

    pad1style = Pad.SHAPE_CIRCLE

    cols = pins / 3
    overpadwidth = rmx * (cols - 1) + padx
    overpadheight = rmy * 2 + pady

    # generate list of pads depending on pin count
    padpos = []
    offset = [0, 0]
    if pins >= 3:
        # for 3 pins, pot could be normal with a vertical column of pins or a trimmer with staggered pins
        if style=="trimmer":
            padpos.append([3, 0, 2 * rmy, ddrill, padx, pady])
            padpos.append([2, rmx, rmy, ddrill, padx, pady])
            padpos.append([1, 0, 0, ddrill, padx, pady])
            offset = [0, 0]
        else:
            padpos.append([3, 0, 0, ddrill, padx, pady])
            padpos.append([2, 0, rmy, ddrill, padx, pady])
            padpos.append([1, 0, 2 * rmy, ddrill, padx, pady])
            offset = [0, -2 * rmy]
    if pins >= 6:
        padpos.append([6, -rmx, 0, ddrill, padx, pady])
        padpos.append([5, -rmx, rmy, ddrill, padx, pady])
        padpos.append([4, -rmx, 2 * rmy, ddrill, padx, pady])
    if pins >= 9:
        padpos.append([9, -2*rmx, 0, ddrill, padx, pady])
        padpos.append([8, -2*rmx, rmy, ddrill, padx, pady])
        padpos.append([7, -2*rmx, 2 * rmy, ddrill, padx, pady])

    mp_name = global_config.get_pad_name(GC.PadName.MECHANICAL)

    # add mounting holes to list of pads
    if mh_count == 1:
        padpos.append([mp_name, mh_xoffset, -mh_yoffset, mh_ddrill, 2 * mh_ddrill, 2 * mh_ddrill])
    if mh_count == 2:
        padpos.append([mp_name, mh_xoffset, -mh_yoffset, mh_ddrill, 2 * mh_ddrill, 2 * mh_ddrill])
        padpos.append([mp_name, mh_xoffset - mh_rmx, -mh_yoffset + mh_rmy, mh_ddrill, 2 * mh_ddrill, 2 * mh_ddrill])
    if mh_count == 4:
        padpos.append([mp_name, mh_xoffset, -mh_yoffset, mh_ddrill, 2 * mh_ddrill, 2 * mh_ddrill])
        padpos.append([mp_name, mh_xoffset - mh_rmx, -mh_yoffset + mh_rmy, mh_ddrill, 2 * mh_ddrill, 2 * mh_ddrill])
        padpos.append([mp_name, mh_xoffset - mh_rmx, -mh_yoffset, mh_ddrill, 2 * mh_ddrill, 2 * mh_ddrill])
        padpos.append([mp_name, mh_xoffset, -mh_yoffset + mh_rmy, mh_ddrill, 2 * mh_ddrill, 2 * mh_ddrill])

    lbody_fab = -(wbody - pinxoffset) # left side of body
    tbody_fab = -pinyoffset # top of body
    wbody_fab = wbody # body length
    hbody_fab = hbody # body height

    wscrew_fab = wscrew # collar length
    hscrew_fab = dscrew # collar height
    lscrew_fab = lbody_fab + wbody_fab # left side of collar
    tscrew_fab = tbody_fab + (hbody_fab - hscrew_fab) / 2.0 # top of collar

    wshaft_fab = wshaft # shaft length
    hshaft_fab = dshaft # shaft diameter
    lshaft_fab = lscrew_fab + wscrew_fab # left side of shaft
    tshaft_fab = tbody_fab + (hbody_fab - hshaft_fab) / 2.0 # top of shaft

    lbody_slk = lbody_fab - math.copysign(slk_offset, wbody_fab)
    tbody_slk = tbody_fab - slk_offset
    wbody_slk = wbody_fab + math.copysign(2 * slk_offset, wbody_fab)
    hbody_slk = hbody_fab + 2 * slk_offset

    lscrew_slk = lbody_slk + wbody_slk
    tscrew_slk = tscrew_fab - slk_offset
    wscrew_slk = wscrew_fab
    hscrew_slk = hscrew_fab + 2 * slk_offset

    lshaft_slk = lscrew_slk + wscrew_slk
    tshaft_slk = tshaft_fab - slk_offset
    wshaft_slk = wshaft_fab
    hshaft_slk = hshaft_fab + 2 * slk_offset

    if wbody_fab < 0:
        wscrew_slk = wscrew_slk + 2 * slk_offset
        wshaft_slk = wshaft_slk + 2 * slk_offset

    minx = miny = 1e99
    maxx = maxy = -1e99
    for p in padpos:
        maxx = max(maxx, p[1] + p[4] / 2)
        minx = min(minx, p[1] - p[4] / 2)
        maxy = max(maxy, p[2] + p[5] / 2)
        miny = min(miny, p[2] - p[5] / 2)

    minx = min(minx, lbody_fab, lbody_fab + wbody_fab + wscrew_fab + wshaft_fab)
    miny = min(miny, tbody_fab, tscrew_fab, tshaft_fab)
    maxx = max(maxx, lbody_fab + wbody_fab + wscrew_fab + wshaft_fab, lbody_fab)
    maxy = max(maxy, tbody_fab + hbody_fab, tscrew_fab + hscrew_fab, tshaft_fab + hshaft_fab)

    h_crt = (maxy - miny) + 2 * crt_offset
    w_crt = (maxx - minx) + 2 * crt_offset
    l_crt = minx - crt_offset
    t_crt = miny - crt_offset

    pow_rat = ""
    if R_POW > 0:
        pow_rat = "{0}W".format(R_POW)
        if (1 / R_POW == int(1 / R_POW)):
            pow_rat = pow_rat + " = 1/{0}W".format(int(1 / R_POW))

    tgs = specialtags
    tgs.append(class_name)
    if len(pow_rat) > 0:
        tgs.append(pow_rat)

    name_prefix = "Potentiometer"
    description = "Potentiometer, horizontal"
    tags = "Potentiometer horizontal"
    for t in tgs:
        description = description + ", " + t
        tags = tags + " " + t
    description = description + ", " + add_description

    footprint_name = ""
    for n in name_additions: footprint_name = footprint_name + "_" + n
    footprint_name = name_prefix + "_" + "_".join(class_name.split()) + "_Horizontal"

    # init kicad footprint
    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    kicad_mod.setDescription(description)
    kicad_mod.setTags(tags)

    kicad_modg = Translation(offset[0], offset[1])
    kicad_mod.append(kicad_modg)

    # set general values
    kicad_modg.append(Property(name=Property.REFERENCE, text='REF**', at=[0, t_crt - txt_offset], layer='F.SilkS'))
    kicad_modg.append(Property(name=Property.VALUE, text=footprint_name, at=[0, t_crt + h_crt + txt_offset], layer='F.Fab'))

    # create FAB-layer
    # horizontal pot: place refdes on F.Fab in center of body and shrink size if body is small
    text_size = min(1, abs(round(wbody_fab / 4.5, 2)))
    kicad_modg.append(Text(text='${REFERENCE}', at=[lbody_fab+wbody_fab/2.0, tbody_fab+hbody_fab/2.0],
                           size=[text_size, text_size], thickness=round(text_size * 0.15, 2),
                           layer='F.Fab'))

    kicad_modg.append(Rectangle(start=[lbody_fab, tbody_fab], end=[lbody_fab + wbody_fab, tbody_fab + hbody_fab], layer='F.Fab',width=lw_fab))
    if wscrew_fab * hscrew_fab != 0:
        kicad_modg.append(
            Rectangle(start=[lscrew_fab, tscrew_fab], end=[lscrew_fab + wscrew_fab, tscrew_fab + hscrew_fab],layer='F.Fab', width=lw_fab))
    if wshaft_fab * hshaft_fab != 0:
        kicad_modg.append(
            Rectangle(start=[lshaft_fab, tshaft_fab], end=[lshaft_fab + wshaft_fab, tshaft_fab + hshaft_fab],layer='F.Fab', width=lw_fab))

    # build keepout for silkscreen
    keepouts = []
    for p in padpos:
        keepouts = keepouts + addKeepoutRound(p[1], p[2], p[4] + 2 * lw_slk + 2 * slk_offset, p[5] + 2 * lw_slk + 2 * slk_offset)

    # create SILKSCREEN-layer
    addRectWithKeepout(kicad_modg, lbody_slk, tbody_slk, wbody_slk, hbody_slk, 'F.SilkS', lw_slk, keepouts, 0.001)
    if wscrew>0 and wscrew_slk * hscrew_slk != 0:
        addRectWithKeepout(kicad_modg, lscrew_slk, tscrew_slk, wscrew_slk, hscrew_slk, 'F.SilkS', lw_slk, keepouts,0.001)
    if wshaft>0 and wshaft_slk * hshaft_slk != 0:
        addRectWithKeepout(kicad_modg, lshaft_slk, tshaft_slk, wshaft_slk, hshaft_slk, 'F.SilkS', lw_slk, keepouts,0.001)

    # create courtyard
    kicad_mod.append(Rectangle(start=[round_to_grid(l_crt + offset[0], grid_crt), round_to_grid(t_crt + offset[1], grid_crt)],
                              end=[round_to_grid(l_crt + w_crt + offset[0], grid_crt), round_to_grid(t_crt + h_crt + offset[1], grid_crt)],layer='F.CrtYd', width=lw_crt))

    # create pads
    for p in padpos:
        ps = Pad.SHAPE_CIRCLE
        if p[0] == 1:
            ps = pad1style
        kicad_modg.append(Pad(number=p[0], type=Pad.TYPE_THT, shape=ps, at=[p[1], p[2]], size=[p[4], p[5]], drill=p[3],
                              layers=Pad.LAYERS_THT))

    # add model
    if (has3d != 0):
        kicad_modg.append(Model(filename=global_config.model_3d_prefix + lib_name + ".3dshapes/" + footprint_name + global_config.model_3d_suffix, at=x_3d, scale=s_3d, rotate=r_3d))

    write_footprint(kicad_mod, lib_name, generator_name)


def makePotentiometerVertical(generator_name, class_name, wbody, hbody, screwstyle="none", style="normal", d_body=0, dshaft=6,
                                dscrew=7, c_ddrill=0, c_offsetx=0, c_offsety=0, pinxoffset=0, pinyoffset=0,
                                pins=3, rmx=5.08, rmy=5.08, ddrill=1.5, shaft_hole=False, SMD_pads=False,
                                SMD_padsize=[], SMD_type="3-5", R_POW=0, x_3d=[0, 0, 0], s_3d=[1, 1, 1], r_3d=[0, 0, 0], has3d=1,
                                specialtags=[], add_description="", lib_name="Potentiometer", name_additions=[],
                                height3d=10, mh_ddrill=1.5, mh_count=0, mh_rmx=0, mh_rmy=15,
                                mh_xoffset=0, mh_yoffset=0, mh_smd=False, mh_padsize=[], mh_nopads=False):
    """
    create potentiometer footprints, vertically mounted

    style=normal
                        <-->pinxoffset
            ^   ^          +---------------+ ^
     pinyoffset |          |               | |
            v   |   ^  O1  |               | cofsety
                | rmy      |     CCCCC     | |
                |   v  O2  |     CCCCC     | v
                |          |     CCCCC     |
                hbody  O3  |               |
                |          |               |
                v          +---------------+
                           <------->coffsetx
                           <-----wbody----->


    style=trimmer (only valid for 3-pin!!!)
        O1           ^
                     rmy
                O2   v

        O3
         <-rmx-->

    Parameters:
        class_name: manufacturer and MPN like "Bourns 3214W" (str)
        wbody: body length (float)
        hbody: body height (float)
        screwstyle: screw style from "none", "slit", or "cross" [default = "none"] (str)
        style: type of pot from "normal" or "trimmer" [default = "normal"] (str)
        d_body: diameter of body for circular pot [default = 0] (float)
        dshaft: shaft diameter [default = 6] (float)
        dscrew: collar diameter [default = 7] (float)
        c_ddrill: drill diameter to fit collar or zero for no hole [default = 0] (float)
        c_offsetx: distance from left side of body to collar center [default = 0] (float)
        c_offsety:: distance from top of body to collar center [default = 0] (float)
        pinxoffset: distance from left side of body to first column of pins [default = 0] (float)
        pinyoffset: distance from top of body to first row of pins [default = 0] (float)
        pins: number of pins; "trimmer" style can only support 3 pins [default = 3] (int)
        rmx: column spacing of pins [default = 5.08] (float)
        rmy: row (or vertical) spacing of pins [default = 5.08] (float)
        ddrill: drill hole diameter [default = 1.5] (float)
        shaft_hole: places hole under pot for shaft through PCB [default = False] (bool)
        SMD_pads: allows using SMD pads [default = False] (bool)
        SMD_padsize: X and Y dimensions of SMD pads in [X, Y] format [default = []] (list of floats)
        SMD_type: allow specifying the SMD pad layout from below options [default = "3-5"] (str)
                "3-5": 5 pin pot with 3 pins on left side and 2 pins on right side with no middle pin
        R_POW: power rating of pot with zero being default [default = 0] (float)
        x_3d: 3D model location [default = [0, 0, 0]] (list of floats)
        s_3d: 3D model scaling [default = [1 / 2.54, 1 / 2.54, 1 / 2.54]] (list of floats)
        r_3d: 3D model rotation [default = [0, 0, 0]] (list of floats)
        has3d: presence of 3D model [default = 1] (bool)
        specialtags: keywords that will be comma-delimited [default = []] (list of strs)
        add_description: descriptive text [default = ""] (str)
        lib_name: library name [default = "Potentiometers"] (str)
        name_additions: extra text for footprint name that will be underscore-delimited [default = []] (list of strs)
        height3d: height of 3D model [default = 10] (float)
        mh_ddrill: drill hole diameter of mounting holes [default = 1.5] (float)
        mh_count: number of mounting holes; 1, 2, or 4 are supported [default = 0] (int)
        mh_rmx: column spacing of mounting holes [default = 0] (float)
        mh_rmy: row spacing of mounting holes [default = 15] (float)
        mh_xoffset: distance from left side of body to first column of mounting holes [default = 0] (float)
        mh_yoffset: distance from top of body to first row of mounting holes [default = 0] (float)
        mh_smd: allows using SMD mounting holes [default = False] (bool)
        mh_padsize: X and Y dimensions of SMD mounting holes in [X, Y] format [default = []] (list of floats)
        mh_nopads: allows selecting the presence of mounting holes [default = False] (bool)

    Returns:
        None
    """

    padx = 1.8 * ddrill
    pady = padx
    if SMD_pads and len(SMD_padsize) >= 2:
        padx = SMD_padsize[0]
        pady = SMD_padsize[1]

    txt_offset = 1
    slk_offset = global_config.silk_fab_offset
    grid_crt = global_config.courtyard_grid

    pad1style = Pad.SHAPE_CIRCLE

    cols = pins / 3
    overpadwidth = rmx * (cols - 1) + padx
    overpadheight = rmy * 2 + pady

    padpos = []
    offset = [0, 0]
    padtype = Pad.TYPE_THT
    padstyle = Pad.SHAPE_CIRCLE
    if SMD_pads:
        padtype = Pad.TYPE_SMT
        padstyle = Pad.SHAPE_ROUNDRECT
    mhtype = Pad.TYPE_THT
    mhstyle = Pad.SHAPE_CIRCLE
    if mh_smd:
        mhtype = Pad.TYPE_SMT
        mhstyle = Pad.SHAPE_ROUNDRECT
    if pins >= 3:
        if style == "trimmer":
            padpos.append([3, 0, 0, ddrill, padx, pady, padtype, padstyle])
            padpos.append([2, rmx, rmy, ddrill, padx, pady, padtype, padstyle])
            padpos.append([1, 0, 2 * rmy, ddrill, padx, pady, padtype, padstyle])
            offset = [0, -2 * rmy]
            if SMD_pads:
                offset = [-rmx/2.0, -rmy]
        else:
            padpos.append([3, 0, 0, ddrill, padx, pady, padtype, padstyle])
            padpos.append([2, 0, rmy, ddrill, padx, pady, padtype, padstyle])
            padpos.append([1, 0, 2 * rmy, ddrill, padx, pady, padtype, padstyle])
            offset = [0, -2 * rmy]
            if SMD_pads:
                offset = [0, -rmy]
    if pins == 4:
        padpos.append([4, 0, -rmy, ddrill, padx, pady, padtype, padstyle])
    if pins == 5 and SMD_pads and SMD_type == "3-5":
        padpos.append([5, -rmx / 2.0 + rmx + pinxoffset, 0, ddrill, padx, pady, padtype, padstyle])
        padpos.append([4, -rmx / 2.0 + rmx + pinxoffset, 2 * rmy, ddrill, padx, pady, padtype, padstyle])
        if SMD_pads:
            offset[0] = -rmx / 2.0
    if pins >= 6:
        padpos.append([6, -rmx, 0, ddrill, padx, pady, padtype, padstyle])
        padpos.append([5, -rmx, rmy, ddrill, padx, pady, padtype, padstyle])
        padpos.append([4, -rmx, 2 * rmy, ddrill, padx, pady, padtype, padstyle])
        if SMD_pads:
            offset[0] = -rmx / 2.0
    if pins >= 9:
        padpos.append([9, -2 * rmx, 0, ddrill, padx, pady, padtype, padstyle])
        padpos.append([8, -2 * rmx, rmy, ddrill, padx, pady, padtype, padstyle])
        padpos.append([7, -2 * rmx, 2 * rmy, ddrill, padx, pady, padtype, padstyle])
        if SMD_pads:
            offset[0] = -rmx

    mhpadsizex = 2 * mh_ddrill
    mhpadsizey = mhpadsizex
    if mh_nopads:
        mhpadsizex = mh_ddrill
        mhpadsizey = mhpadsizex
    if mh_smd and len(mh_padsize) >= 2:
        mhpadsizex = mh_padsize[0]
        mhpadsizey = mh_padsize[1]

    mp_name = global_config.get_pad_name(GC.PadName.MECHANICAL)

    if mh_count == 1:
        padpos.append(["", mh_xoffset, -mh_yoffset, mh_ddrill, mhpadsizex, mhpadsizey, mhtype, mhstyle])
    if mh_count == 2:
        padpos.append([mp_name, mh_xoffset, -mh_yoffset, mh_ddrill, mhpadsizex, mhpadsizey, mhtype, mhstyle])
        padpos.append([mp_name, mh_xoffset - mh_rmx, -mh_yoffset + mh_rmy, mh_ddrill, mhpadsizex, mhpadsizey, mhtype, mhstyle])
    if mh_count == 4:
        padpos.append([mp_name, mh_xoffset, -mh_yoffset, mh_ddrill, mhpadsizex, mhpadsizey, mhtype, mhstyle])
        padpos.append([mp_name, mh_xoffset - mh_rmx, -mh_yoffset + mh_rmy, mh_ddrill, mhpadsizex, mhpadsizey, mhtype, mhstyle])
        padpos.append([mp_name, mh_xoffset - mh_rmx, -mh_yoffset, mh_ddrill, mhpadsizex, mhpadsizey, mhtype, mhstyle])
        padpos.append([mp_name, mh_xoffset, -mh_yoffset + mh_rmy, mh_ddrill, mhpadsizex, mhpadsizey, mhtype, mhstyle])

    lbody_fab = pinxoffset # why does the X offset of the pin set the body's left side location?!?!?!
    tbody_fab = -pinyoffset
    wbody_fab = wbody
    hbody_fab = hbody
    cdbody_fab = d_body
    clbody_fab = lbody_fab + c_offsetx
    ctbody_fab = tbody_fab + c_offsety

    if c_ddrill > 0 and shaft_hole == True:
        padpos.append(['', clbody_fab, ctbody_fab, c_ddrill, c_ddrill, c_ddrill, Pad.TYPE_NPTH, mhstyle])

    lbody_slk = lbody_fab - slk_offset
    tbody_slk = tbody_fab - slk_offset
    wbody_slk = wbody_fab + 2 * slk_offset
    hbody_slk = hbody_fab + 2 * slk_offset
    cdbody_slk = cdbody_fab + 2 * slk_offset
    clbody_slk = clbody_fab
    ctbody_slk = ctbody_fab

    minx = miny = 1e99
    maxx = maxy = -1e99
    for p in padpos:
        maxx = max(maxx, p[1] + p[4] / 2)
        minx = min(minx, p[1] - p[4] / 2)
        maxy = max(maxy, p[2] + p[5] / 2)
        miny = min(miny, p[2] - p[5] / 2)

    minx = min(minx, lbody_fab, clbody_fab - cdbody_fab / 2)
    miny = min(miny, tbody_fab, ctbody_fab - cdbody_fab / 2)
    maxx = max(maxx, lbody_fab + wbody_fab, clbody_fab + cdbody_fab / 2)
    maxy = max(maxy, tbody_fab + hbody_fab, ctbody_fab + cdbody_fab / 2)

    h_crt = (maxy - miny) + 2 * crt_offset
    w_crt = (maxx - minx) + 2 * crt_offset
    l_crt = minx - crt_offset
    t_crt = miny - crt_offset

    pow_rat = ""
    if R_POW > 0:
        pow_rat = "{0}W".format(R_POW)
        if (1 / R_POW == int(1 / R_POW)):
            pow_rat = pow_rat + " = 1/{0}W".format(int(1 / R_POW))

    tgs = specialtags
    tgs.append(class_name)
    if len(pow_rat) > 0:
        tgs.append(pow_rat)

    name_prefix = "Potentiometer"
    description = "Potentiometer, vertical"
    tags = "Potentiometer vertical"
    if shaft_hole:
        description = description + ", shaft hole"
        tags = tags + " hole"
    for t in tgs:
        description = description + ", " + t
        tags = tags + " " + t
    description = description + ", " + add_description

    for n in name_additions: footprint_name = footprint_name + "_" + n
    footprint_name = name_prefix + "_" + "_".join(class_name.split()) + "_Vertical"
    if shaft_hole: footprint_name = footprint_name + "_Hole"

    footprint_type = FootprintType.SMD if SMD_pads else FootprintType.THT

    # init kicad footprint
    kicad_mod = Footprint(footprint_name, footprint_type)
    kicad_mod.setDescription(description)
    kicad_mod.setTags(tags)

    kicad_modg = Translation(offset[0], offset[1])
    kicad_mod.append(kicad_modg)

    # set general values
    kicad_modg.append(Property(name=Property.REFERENCE, text='REF**', at=[l_crt + w_crt / 2, t_crt - txt_offset], layer='F.SilkS'))
    kicad_modg.append(Property(name=Property.VALUE, text=footprint_name, at=[l_crt + w_crt / 2, t_crt + h_crt + txt_offset], layer='F.Fab'))

    # create FAB-layer
    drawbody = wbody > 0
    if cdbody_fab > 0:
        if style == "trimmer":
            dy = hbody_fab / 2.0
            if drawbody and dy <= cdbody_fab / 2:
                dx = math.sqrt(cdbody_fab * cdbody_fab / 4 - dy * dy)
                alpha = 360 - 2 * math.degrees(math.atan(dy / dy))
                kicad_modg.append(PolygonLine(shape=[[clbody_fab - dx, ctbody_fab - dy], [lbody_fab, ctbody_fab - dy],
                                                        [lbody_fab, ctbody_fab + dy], [clbody_fab - dx, ctbody_fab + dy]], layer='F.Fab', width=lw_fab))
                kicad_modg.append(Arc(center=[clbody_fab, ctbody_fab], start=[clbody_fab-dx, ctbody_fab-dy], angle=alpha,layer='F.Fab', width=lw_fab))
            else:
                kicad_modg.append(Circle(center=[clbody_fab, ctbody_fab], radius=cdbody_fab / 2.0, layer='F.Fab', width=lw_fab))

                # vertical trimmer with circular body: place refdes on F.Fab inside
                # calculate text size (also used for offset distance inside outer circle)
                text_size = min(1, round((cdbody_fab - dscrew) / 4.0, 2))
                kicad_modg.append(Text(text='${REFERENCE}', at=[clbody_fab - cdbody_fab / 2.0 + text_size * 1.2, ctbody_fab],
                                 size=[text_size, text_size], thickness=round(text_size * 0.15, 2),
                                 layer='F.Fab', rotation = 90))

                if drawbody:
                    kicad_modg.append(Rectangle(start=[lbody_fab, tbody_fab], end=[lbody_fab + wbody_fab, tbody_fab + hbody_fab],
                                 layer='F.Fab', width=lw_fab))
        else:
            cdradius = cdbody_fab / 2.0
            kicad_modg.append(Circle(center=[clbody_fab, ctbody_fab], radius=cdradius, layer='F.Fab', width=lw_fab))
            dy = hbody_fab / 2.0

            #kicad_modg.append(Text(text='REF**', at=[clbody_fab, ctbody_fab], size=[min(1.0, cdradius), min(1.0, cdradius)], layer='F.Fab'))

            if drawbody and dy <= cdbody_fab / 2.0:
                dx = math.sqrt(cdbody_fab * cdbody_fab / 4 - dy * dy)

                # vertical pot with circular body: place refdes on F.Fab inside left edge of body
                kicad_modg.append(Text(text='${REFERENCE}', at=[lbody_fab + 1, ctbody_fab], layer='F.Fab', rotation = 90))

                kicad_modg.append(PolygonLine(shape=[[clbody_fab - dx, ctbody_fab - dy], [lbody_fab, ctbody_fab - dy],
                                                        [lbody_fab, ctbody_fab + dy], [clbody_fab - dx, ctbody_fab + dy]], layer='F.Fab', width=lw_fab))
            elif drawbody:
                kicad_modg.append(Rectangle(start=[lbody_fab, tbody_fab], end=[lbody_fab + wbody_fab, tbody_fab + hbody_fab],
                             layer='F.Fab', width=lw_fab))
    elif drawbody:
        # vertical pot with square body: place refdes on F.Fab inside left edge of body
        kicad_modg.append(Text(text='${REFERENCE}', at=[lbody_fab + 1, ctbody_fab], layer='F.Fab', rotation = 90))

        kicad_modg.append(Rectangle(start=[lbody_fab, tbody_fab], end=[lbody_fab + wbody_fab, tbody_fab + hbody_fab],
                                   layer='F.Fab', width=lw_fab))

    if dscrew > 0:
        #kicad_modg.append(Circle(center=[clbody_fab, ctbody_fab], radius=dscrew / 2.0, layer='F.Fab', width=lw_fab))
        if screwstyle == "slit":
            addSlitScrew(kicad_modg, [clbody_fab, ctbody_fab], dscrew / 2.0, 'F.Fab', lw_fab)
        elif screwstyle == "cross":
            addCrossScrew(kicad_modg, [clbody_fab, ctbody_fab], dscrew / 2.0, 'F.Fab', lw_fab)

    if dshaft > 0 and shaft_hole == False:
        kicad_modg.append(Circle(center=[clbody_fab, ctbody_fab], radius=dshaft / 2.0, layer='F.Fab', width=lw_fab))

    # build keepout for silkscreen
    keepouts = []
    for p in padpos:
        if p[7] == Pad.SHAPE_CIRCLE:
            keepouts = keepouts + addKeepoutRound(p[1], p[2], p[4] + 2 * lw_slk + 2 * slk_offset, p[5] + 2 * lw_slk + 2 * slk_offset)
        else:
            keepouts = keepouts + addKeepoutRect(p[1], p[2], p[4] + 2 * lw_slk + 2 * slk_offset, p[5] + 2 * lw_slk + 2 * slk_offset)
    # debug_draw_keepouts(kicad_modg,keepouts)

    # create SILKSCREEN-layer
    drawbody = wbody > 0
    if cdbody_fab > 0:
        addCircleWithKeepout(kicad_modg, clbody_slk, ctbody_slk, cdbody_slk / 2.0, 'F.SilkS', lw_slk, keepouts)
        dy = hbody_slk / 2.0
        if drawbody and dy <= cdbody_slk / 2.0:
            dx = math.sqrt(cdbody_slk * cdbody_slk / 4.0 - dy * dy)
            addHLineWithKeepout(kicad_modg, clbody_slk - dx, lbody_slk, ctbody_slk - dy, 'F.SilkS', lw_slk,keepouts)
            addVLineWithKeepout(kicad_modg, lbody_slk, ctbody_slk - dy, ctbody_slk + dy, 'F.SilkS', lw_slk,keepouts)
            addHLineWithKeepout(kicad_modg, clbody_slk - dx, lbody_slk, ctbody_slk + dy, 'F.SilkS', lw_slk,keepouts)
            drawbody = False

    if drawbody:
        addRectWithKeepout(kicad_modg, lbody_slk, tbody_slk, wbody_slk, hbody_slk, 'F.SilkS', lw_slk, keepouts,0.001)

    # create courtyard
    kicad_mod.append(Rectangle(start=[round_to_grid(l_crt + offset[0], grid_crt), round_to_grid(t_crt + offset[1], grid_crt)],
                              end=[round_to_grid(l_crt + w_crt + offset[0], grid_crt), round_to_grid(t_crt + h_crt + offset[1], grid_crt)],
                              layer='F.CrtYd', width=lw_crt))
    # create pads
    for p in padpos:
        if p[6] == Pad.TYPE_SMT:
            kicad_modg.append(Pad(number=p[0], type=p[6], shape=p[7], at=[p[1], p[2]], size=[p[4], p[5]], drill=p[3],
                                  round_radius_handler=global_config.roundrect_radius_handler,
                                  layers=Pad.LAYERS_SMT))
        else:
            kicad_modg.append(Pad(number=p[0], type=p[6], shape=p[7], at=[p[1], p[2]], size=[p[4], p[5]], drill=p[3],
                                  round_radius_handler=global_config.roundrect_radius_handler,
                                  layers=Pad.LAYERS_THT))

    # add model
    if (has3d != 0):
        if SMD_pads:
            kicad_modg.append(Model(filename=global_config.model_3d_prefix + lib_name + ".3dshapes/" + footprint_name + global_config.model_3d_suffix, at=x_3d, scale=s_3d, rotate=r_3d))
        else:
            kicad_modg.append(Model(filename=global_config.model_3d_prefix + lib_name + ".3dshapes/" + footprint_name + global_config.model_3d_suffix, at=x_3d, scale=s_3d, rotate=r_3d))

    write_footprint(kicad_mod, lib_name, generator_name)


def makeSpindleTrimmer(generator_name, class_name, wbody, hbody, pinxoffset, pinyoffset, rmx2, rmy2, rmx3, rmy3, dscrew, ddrill=1,
                            wscrew=0, screwxoffset=0, screwyoffset=0, style = "screwleft", screwstyle="slit",
                            shaft_hole=False, SMD_pads=False, SMD_padsize=[], R_POW=0, x_3d=[0, 0, 0], s_3d=[1, 1, 1], r_3d=[0, 0, 0],
                            has3d=1, specialtags=[], add_description="", lib_name="Potentiometer", name_additions=[],
                            height3d=10):
    """
    create spindle trimmer potentiometer (only valid for 3-pin!!!)
                                                          <-----------rmx2------------->
                      screwxoffset<>      <------------------rmx3---------------------->
       screwyoffset ^              +---------------------------------------------------------------+         ^       ^
                    |     ^   +----|                                                               |         |       |
                    v  dsrew  +--  |                     O2O                                       | ^       |       pinyoffset
                          v   +----|                                                               | rmy2    |       |
                        wscrew<--->|     O3O                                           O1O         | v       hbody   v
                                   |                                                               |         |
                                   +---------------------------------------------------------------+         v
                                   <----------------------------wbody------------------------------>
                                   <------pinxoffset------------------------------------>

    Parameters:
        class_name: manufacturer and MPN like "Bourns 3214W" (str)
        wbody: body length (float)
        hbody: body height (float)
        pinxoffset: distance from left side of body to pin 1 (float)
        pinyoffset: distance from top of body to pin 1 (float)
        rmx2: distance from pin 1 left to pin 2 (float)
        rmy2: distance from pin 1 up to pin 2 (float)
        rmx3: distance from pin 1 left to pin 3 (float)
        rmy3: distance from pin 1 up to pin 3 (float)
        dscrew: screw diameter (float)
        ddrill: drill hole diameter [default = 1] (float)
        wscrew: length of screw for left screw types [default = 0] (float)
        screwxoffset: distance from left side of body to screw for top screw types [default = 0] (float)
        screwyoffset: distance from top of body to center of screw [default = 0] (float)
        style: location of screw from "screwleft" or "screwtop" [default = "screwleft"] (str)
        screwstyle: screw style from "slit" or "cross" [default = "slit"] (str)
        SMD_pads: allows using SMD pads [default = False] (bool)
        SMD_padsize: X and Y dimensions of SMD pads in [X, Y] format [default = []] (list of floats)
        R_POW: power rating of pot with zero being default [default = 0] (float)
        x_3d: 3D model location [default = [0, 0, 0]] (list of floats)
        s_3d: 3D model scaling [default = [1 / 2.54, 1 / 2.54, 1 / 2.54]] (list of floats)
        r_3d: 3D model rotation [default = [0, 0, 0]] (list of floats)
        has3d: presence of 3D model [default = 1] (bool)
        specialtags: keywords that will be comma-delimited [default = []] (list of strs)
        add_description: descriptive text [default = ""] (str)
        lib_name: library name [default = "Potentiometers"] (str)
        name_additions: extra text for footprint name that will be underscore-delimited [default = []] (list of strs)
        height3d: height of 3D model [default = 10] (float)

    Returns:
        None
    """

    padx = 1.8 * ddrill
    pady = padx
    if SMD_pads and len(SMD_padsize) >= 2:
        padx = SMD_padsize[0]
        pady = SMD_padsize[1]

    txt_offset = 1
    slk_offset = global_config.silk_fab_offset
    grid_crt = global_config.courtyard_grid

    padpos = []
    padtype = Pad.TYPE_THT
    padstyle = Pad.SHAPE_CIRCLE
    if SMD_pads:
        padtype = Pad.TYPE_SMT
        padstyle = Pad.SHAPE_ROUNDRECT
    padpos.append([1, pinxoffset, pinyoffset, ddrill, padx, pady, padtype, padstyle])
    if SMD_pads and len(SMD_padsize) >= 4:
        padpos.append([2, pinxoffset+rmx2, pinyoffset+rmy2, ddrill, SMD_padsize[2], SMD_padsize[3], padtype, padstyle])
    else:
        padpos.append([2, pinxoffset + rmx2, pinyoffset + rmy2, ddrill, padx, pady, padtype, padstyle])
    if SMD_pads and len(SMD_padsize) >= 6:
        padpos.append([3, pinxoffset + rmx3, pinyoffset + rmy3, ddrill, SMD_padsize[4], SMD_padsize[5], padtype, padstyle])
    else:
        padpos.append([3, pinxoffset+rmx3, pinyoffset+rmy3, ddrill, padx, pady, padtype, padstyle])
    offset = [-pinxoffset, -pinyoffset]
    if SMD_pads:
        offset = [-(max(padpos[0][1],padpos[1][1],padpos[2][1])+min(padpos[0][1],padpos[1][1],padpos[2][1]))/2, -(max(padpos[0][2],padpos[1][2],padpos[2][2])+min(padpos[0][2],padpos[1][2],padpos[2][2]))/2]
        #offset = [-(pinxoffset+pinxoffset+rmx2+pinxoffset+rmx3)/3.0, -(pinyoffset+pinyoffset+rmy2+pinyoffset+rmy3)/3.0]

    lbody_fab = 0
    tbody_fab = 0
    wbody_fab = wbody
    hbody_fab = hbody

    lbody_slk = lbody_fab - slk_offset
    tbody_slk = tbody_fab - slk_offset
    wbody_slk = wbody_fab + 2 * slk_offset
    hbody_slk = hbody_fab + 2 * slk_offset

    if style == "screwtop" and shaft_hole == True:
        padpos.append(['', screwxoffset, screwyoffset, ddrill, ddrill, ddrill, Pad.TYPE_NPTH, Pad.SHAPE_CIRCLE])

    if style=="screwleft":
        orientation = "horizontal"
        lscrew_fab=lbody_fab+screwxoffset-wscrew
        tscrew_fab = tbody_fab + screwyoffset-dscrew/2.0
        wscrew_fab = wscrew
        hscrew_fab = dscrew
        lscrew_slk=lscrew_fab-slk_offset
        tscrew_slk = tscrew_fab-slk_offset
        wscrew_slk = wscrew_fab
        hscrew_slk = hscrew_fab+slk_offset*2
    elif style=="screwtop":
        orientation = "vertical"
        lscrew_fab=lbody_fab+screwxoffset
        tscrew_fab = tbody_fab + screwyoffset
        wscrew_fab = dscrew
        hscrew_fab = dscrew
        lscrew_slk = lscrew_fab
        tscrew_slk = tscrew_fab
        wscrew_slk = wscrew_fab + 2*slk_offset
        hscrew_slk = hscrew_fab + 2*slk_offset

    minx = miny = 1e99
    maxx = maxy = -1e99
    for p in padpos:
        maxx = max(maxx, p[1] + p[4] / 2)
        minx = min(minx, p[1] - p[4] / 2)
        maxy = max(maxy, p[2] + p[5] / 2)
        miny = min(miny, p[2] - p[5] / 2)

    minx = min(minx, lbody_fab)
    miny = min(miny, tbody_fab)
    maxx = max(maxx, lbody_fab + wbody_fab)
    maxy = max(maxy, tbody_fab + hbody_fab)
    if style == "screwleft":
        minx = min(minx, lscrew_fab)
        miny = min(miny, tscrew_fab)
        maxx = max(maxx, lscrew_fab + wscrew_fab)
        maxy = max(maxy, tscrew_fab + hscrew_fab)

    h_crt = (maxy - miny) + 2 * crt_offset
    w_crt = (maxx - minx) + 2 * crt_offset
    l_crt = minx - crt_offset
    t_crt = miny - crt_offset

    pow_rat = ""
    if R_POW > 0:
        pow_rat = "{0}W".format(R_POW)
        if (1 / R_POW == int(1 / R_POW)):
            pow_rat = pow_rat + " = 1/{0}W".format(int(1 / R_POW))

    tgs = specialtags
    tgs.append(class_name)
    if len(pow_rat) > 0:
        tgs.append(pow_rat)

    name_prefix = "Potentiometer"
    description = "Potentiometer, " + orientation
    tags = "Potentiometer " + orientation
    if shaft_hole:
        description = description + ", shaft hole"
        tags = tags + " hole"
    for t in tgs:
        description = description + ", " + t
        tags = tags + " " + t
    description = description + ", " + add_description

    for n in name_additions: footprint_name = footprint_name + "_" + n
    footprint_name = name_prefix + "_" + "_".join(class_name.split()) + "_" + orientation.capitalize()
    if shaft_hole: footprint_name = footprint_name + "_Hole"

    footprint_type = FootprintType.SMD if SMD_pads else FootprintType.THT

    # init kicad footprint
    kicad_mod = Footprint(footprint_name, footprint_type)
    kicad_mod.setDescription(description)
    kicad_mod.setTags(tags)

    kicad_modg = Translation(offset[0], offset[1])
    kicad_mod.append(kicad_modg)

    # set general values
    kicad_modg.append(Property(name=Property.REFERENCE, text='REF**', at=[l_crt + w_crt / 2.0, t_crt - txt_offset], layer='F.SilkS'))
    kicad_modg.append(Property(name=Property.VALUE, text=footprint_name, at=[l_crt + w_crt / 2.0, t_crt + h_crt + txt_offset], layer='F.Fab'))

    # create FAB-layer
    kicad_modg.append(Rectangle(start=[lbody_fab, tbody_fab], end=[lbody_fab + wbody_fab, tbody_fab + hbody_fab], layer='F.Fab', width=lw_fab))
    if style == "screwleft":
        if wscrew > 0:
            kicad_modg.append(Rectangle(start=[lscrew_fab, tscrew_fab], end=[lscrew_fab + wscrew_fab, tscrew_fab + hscrew_fab], layer='F.Fab',width=lw_fab))
            kicad_modg.append(Line(start=[lscrew_fab, tscrew_fab+hscrew_fab/2.0], end=[lscrew_fab + wscrew_fab/2.0, tscrew_fab + hscrew_fab/2.0], layer='F.Fab', width=lw_fab))

        # trimmer pot with rectangular body: place refdes on F.Fab centered in body
        text_size = round(min(1, lbody_fab + wbody_fab, tbody_fab + hbody_fab), 2)
        kicad_modg.append(Text(text='${REFERENCE}', at=[lbody_fab+wbody_fab/2.0, tbody_fab+hbody_fab/2.0],
                               size=[text_size, text_size], thickness=round(text_size * 0.15, 2),
                               layer='F.Fab'))
    elif style == "screwtop":
        # screw graphics are inside body somewhere, so determine where to place F.Fab ref des text
        if (hbody_fab / 2.0 == tscrew_fab):
            # screw is centered vertically in body, so place at top center of body
            text_x = lbody_fab + wbody_fab / 2.0
            text_y = tscrew_fab - wscrew_fab + 0.3
            text_size = round(min(1, (hbody_fab - wscrew_fab) / 4.0), 2)
        else:
            # determine if screw is closer to left or right side of body, then place centered on other side of body
            text_y = tbody_fab + hbody_fab / 2.0
            if (lscrew_fab <= wbody_fab - lscrew_fab):
                text_x = lscrew_fab + (wbody_fab - lscrew_fab) / 2.0
                text_size = round(min(1, (wbody_fab - lscrew_fab) / 6.0), 2)
            else:
                text_x = lbody_fab + lscrew_fab / 2.0
                text_size = round(min(1, lscrew_fab / 6.0), 2)

        # trimmer pot top-mount with rectangular body: place refdes on F.Fab at location found above
        kicad_modg.append(Text(text='${REFERENCE}', at=[text_x, text_y],
                               size=[text_size, text_size], thickness=round(text_size * 0.15, 2),
                               layer='F.Fab'))

        if shaft_hole == False:
            if screwstyle=="slit":
                addSlitScrew(kicad_modg, [lscrew_fab, tscrew_fab], wscrew_fab / 2.0, 'F.Fab', lw_fab)
            else:
                addCrossScrew(kicad_modg, [lscrew_fab, tscrew_fab], wscrew_fab / 2.0, 'F.Fab', lw_fab)

    # build keepout for silkscreen
    keepouts = []
    for p in padpos:
        if p[7] == Pad.SHAPE_CIRCLE:
            keepouts = keepouts + addKeepoutRound(p[1], p[2], p[4] + 2 * lw_slk + 2 * slk_offset, p[5] + 2 * lw_slk + 2 * slk_offset)
        else:
            keepouts = keepouts + addKeepoutRect(p[1], p[2], p[4] + 2 * lw_slk + 2 * slk_offset, p[5] + 2 * lw_slk + 2 * slk_offset)
    # debug_draw_keepouts(kicad_modg,keepouts)

    # create SILKSCREEN-layer
    addRectWithKeepout(kicad_modg, lbody_slk, tbody_slk, wbody_slk, hbody_slk, 'F.SilkS', lw_slk, keepouts)
    if style == "screwleft" and wscrew > 0:
        addRectWithKeepout(kicad_modg, lscrew_slk, tscrew_slk, wscrew_slk, hscrew_slk, 'F.SilkS', lw_slk, keepouts)
        addHLineWithKeepout(kicad_modg, lscrew_slk, lscrew_slk+wscrew_slk/2.0, tscrew_slk+hscrew_slk/2.0, 'F.SilkS', lw_slk, keepouts)
    '''elif style == "screwtop":
        if screwstyle == "slit":
            addSlitScrewWithKeepouts(kicad_modg, lscrew_slk, tscrew_slk, wscrew_slk / 2.0, 'F.SilkS', lw_slk, keepouts)
        else:
            addCrossScrewWithKeepouts(kicad_modg, lscrew_slk, tscrew_slk, wscrew_slk / 2.0, 'F.SilkS', lw_slk, keepouts)'''

    # create courtyard
    kicad_mod.append(Rectangle(start=[round_to_grid(l_crt + offset[0], grid_crt), round_to_grid(t_crt + offset[1], grid_crt)],
                             end=[round_to_grid(l_crt + w_crt + offset[0], grid_crt), round_to_grid(t_crt + h_crt + offset[1], grid_crt)], layer='F.CrtYd', width=lw_crt))

    # create pads
    for p in padpos:
        if p[6] == Pad.TYPE_SMT:
            kicad_modg.append(Pad(number=p[0], type=p[6], shape=p[7], at=[p[1], p[2]], size=[p[4], p[5]], drill=p[3],
                                  round_radius_handler=global_config.roundrect_radius_handler,
                                  layers=Pad.LAYERS_SMT))
        else:
            kicad_modg.append(Pad(number=p[0], type=p[6], shape=p[7], at=[p[1], p[2]], size=[p[4], p[5]], drill=p[3],
                                  round_radius_handler=global_config.roundrect_radius_handler,
                                  layers=Pad.LAYERS_THT))

    # add model
    if (has3d != 0):
        kicad_modg.append(Model(filename=global_config.model_3d_prefix + lib_name + ".3dshapes/" + footprint_name + global_config.model_3d_suffix, at=x_3d, scale=s_3d, rotate=r_3d))

    write_footprint(kicad_mod, lib_name, generator_name)
