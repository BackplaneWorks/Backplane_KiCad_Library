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

from ..footprint_scripts_potentiometers import (
    makePotentiometerVertical,
    makeSpindleTrimmer,
)


def generate_all(generator_name: str) -> int:
    num_generated_fps = 0

    lib_name = "Potentiometer_SMD"

    # 2018 comment: this footprint is not generated on-center due to design limitations of footprint_scripts_potentiometers.py
    # 2025 comment: this seems completely broken and problem isn't worth solving without just rewriting most of the generator anyway.
    # class_name="Bourns PRS11S"; add_description="http://www.bourns.com/docs/Product-Datasheets/PRS11S.pdf"
    # pins = 5; rmx=16.5; rmy=2.5; ddrill=1; wbody=13; hbody=11.7; height3d = 7.2; wscrew=4.3; dscrew=6.8
    # wshaft=20-wbody-wscrew; dshaft=6; pinxoffset=1.75; pinyoffset=(hbody-2*rmy)/2.0; dbody=0; vpinyoffset=(hbody-2*rmy)/2.0; c_offsetx=6.5; c_offsety=hbody/2.0; mh_rmy=11.3
    # makePotentiometerVertical(generator_name, lib_name=lib_name, SMD_pads=True, SMD_padsize=[4,2], mh_ddrill=1.5, mh_count=2, mh_rmx=0, mh_rmy=mh_rmy, mh_xoffset=8.25, mh_yoffset=(mh_rmy-2*rmy)/2.0, mh_nopads=True, shaft_hole=False, class_name=class_name, wbody=wbody, hbody=hbody, d_body=dbody, dshaft=dshaft, dscrew=dscrew, c_ddrill=dscrew+0.5,c_offsetx=c_offsetx, c_offsety=c_offsety, pinxoffset=pinxoffset,pinyoffset=pinyoffset, pins=pins, rmx=rmx, rmy=rmy, ddrill=ddrill, specialtags=[], add_description=add_description, name_additions=[], height3d=height3d)

    class_name="ACP CA6-VSMD"; add_description="http://www.acptechnologies.com/wp-content/uploads/2017/06/01-ACP-CA6.pdf"
    pins = 3; rmx=8.65; rmy=4.3/2.0; ddrill=0.9; wbody=6.5; hbody=6.5; dbody=0; height3d = 4.5+hbody/2.0; screwzpos = 4.5; wscrew=-wbody; dscrew=2
    wshaft=0; dshaft=1.8; pinxoffset=1.075; pinyoffset=(hbody-2*rmy)/2.0; dbody=0; vpinyoffset=(hbody-2*rmy)/2.0; c_offsetx=3.525; c_offsety=hbody/2.0; c_ddrill=2.5
    makePotentiometerVertical(generator_name, lib_name=lib_name, SMD_pads=True, SMD_padsize=[2.5,2], style="trimmer", shaft_hole=False, class_name=class_name, wbody=wbody, hbody=hbody, d_body=dbody, dshaft=dshaft, dscrew=dscrew, c_ddrill=c_ddrill,c_offsetx=c_offsetx, c_offsety=c_offsety, pinxoffset=pinxoffset,pinyoffset=vpinyoffset, pins=pins, rmx=rmx, rmy=rmy, ddrill=ddrill, specialtags=[], add_description=add_description, name_additions=[], height3d=height3d)
    makePotentiometerVertical(generator_name, lib_name=lib_name, SMD_pads=True, SMD_padsize=[2.5,2], style="trimmer", shaft_hole=True, class_name=class_name, wbody=wbody, hbody=hbody, d_body=dbody, dshaft=dshaft, dscrew=dscrew, c_ddrill=c_ddrill,c_offsetx=c_offsetx, c_offsety=c_offsety, pinxoffset=pinxoffset,pinyoffset=vpinyoffset, pins=pins, rmx=rmx, rmy=rmy, ddrill=ddrill, specialtags=[], add_description=add_description, name_additions=[], height3d=height3d)
    num_generated_fps += 2

    class_name="ACP CA9-VSMD"; add_description="http://www.acptechnologies.com/wp-content/uploads/2017/05/02-ACP-CA9-CE9.pdf"
    pins = 3; rmx=9.25; rmy=2.5; ddrill=1.3; hbody=9.8; wbody=10; dbody=0; screwzpos = 7; wscrew=-wbody; dscrew=3
    wshaft=0; dshaft=2.1; pinxoffset=-0.375; pinyoffset=(hbody-2*rmy)/2.0; dbody=0; vpinyoffset=(hbody-2*rmy)/2.0; c_offsetx=5.125; c_offsety=hbody/2.0; c_ddrill=4; height3d=5.5
    makePotentiometerVertical(generator_name, lib_name=lib_name, SMD_pads=True, SMD_padsize=[2.5,2.5], style="trimmer", shaft_hole=False, class_name=class_name, wbody=wbody, hbody=hbody, d_body=dbody, dshaft=dshaft, dscrew=dscrew, c_ddrill=c_ddrill,c_offsetx=c_offsetx, c_offsety=c_offsety, pinxoffset=pinxoffset,pinyoffset=vpinyoffset, pins=pins, rmx=rmx, rmy=rmy, ddrill=ddrill, specialtags=[], add_description=add_description, name_additions=[], height3d=height3d)
    makePotentiometerVertical(generator_name, lib_name=lib_name, SMD_pads=True, SMD_padsize=[2.5,2.5], style="trimmer", shaft_hole=True, class_name=class_name, wbody=wbody, hbody=hbody, d_body=dbody, dshaft=dshaft, dscrew=dscrew, c_ddrill=c_ddrill,c_offsetx=c_offsetx, c_offsety=c_offsety, pinxoffset=pinxoffset,pinyoffset=vpinyoffset, pins=pins, rmx=rmx, rmy=rmy, ddrill=ddrill, specialtags=[], add_description=add_description, name_additions=[], height3d=height3d)
    num_generated_fps += 2

    class_name="ACP CA14-VSMD"; add_description="http://www.acptechnologies.com/wp-content/uploads/2017/10/03-ACP-CA14-CE14.pdf"
    pins = 3; rmx=13; rmy=5; dbody=0; pinxoffset=-0.7; wbody=14; hbody=14; vpinyoffset=(hbody-2*rmy)/2.0; c_offsetx=7; c_offsety=hbody/2.0; c_ddrill=7; height3d=5.8
    makePotentiometerVertical(generator_name, lib_name=lib_name, SMD_pads=True, SMD_padsize=[3,3], style="trimmer", shaft_hole=False, class_name=class_name, wbody=wbody, hbody=hbody, d_body=dbody, dshaft=dshaft, dscrew=dscrew, c_ddrill=c_ddrill,c_offsetx=c_offsetx, c_offsety=c_offsety, pinxoffset=pinxoffset,pinyoffset=vpinyoffset, pins=pins, rmx=rmx, rmy=rmy, ddrill=ddrill, specialtags=[], add_description=add_description, name_additions=[], height3d=height3d)
    makePotentiometerVertical(generator_name, lib_name=lib_name, SMD_pads=True, SMD_padsize=[3,3], style="trimmer", shaft_hole=True, class_name=class_name, wbody=wbody, hbody=hbody, d_body=dbody, dshaft=dshaft, dscrew=dscrew, c_ddrill=c_ddrill,c_offsetx=c_offsetx, c_offsety=c_offsety, pinxoffset=pinxoffset,pinyoffset=vpinyoffset, pins=pins, rmx=rmx, rmy=rmy, ddrill=ddrill, specialtags=[], add_description=add_description, name_additions=[], height3d=height3d)
    num_generated_fps += 2

    class_name="Bourns 3214W"; add_description = "https://www.bourns.com/docs/Product-Datasheets/3214.pdf"
    wbody=4.8; hbody=3.5; pinxoffset=(wbody-2.5)/2.0+2.5; pinyoffset=0.3; height3d = 5.1; rmx2=-1.25; rmy2=2.9; rmx3=-2.5; rmy3=0; ddrill=0.8; dscrew=1.5; wscrew = dscrew; screwxoffset = 1.2; screwyoffset = hbody-1.1
    style = "screwtop"; SMD_pads = True; SMD_padsize = [1.3,1.6,2,1.6,1.3,1.6]
    makeSpindleTrimmer(generator_name, lib_name=lib_name, shaft_hole=False, class_name=class_name, ddrill=ddrill, wbody=wbody, hbody=hbody, pinxoffset=pinxoffset, pinyoffset=pinyoffset, rmx2=rmx2, rmy2=rmy2, rmx3=rmx3, rmy3=rmy3, dscrew=dscrew, wscrew=wscrew, screwxoffset=screwxoffset, screwyoffset=screwyoffset, style=style, SMD_pads=SMD_pads, SMD_padsize=SMD_padsize, specialtags=[], add_description=add_description, name_additions=[], height3d=height3d)
    num_generated_fps += 1

    class_name="Bourns 3214X"
    wbody=4.8; hbody=3.5; pinxoffset=(wbody-2.5)/2.0+2.5; pinyoffset=-(5.1-3.5)/2.0; height3d = 5.3; rmx2=-1.15; rmy2=5.1; rmx3=-2.3; rmy3=0; ddrill=0.8; dscrew=1.5; wscrew = dscrew; screwxoffset = 1.2; screwyoffset = hbody-1.1
    style = "screwtop"; SMD_pads = True; SMD_padsize = [1.3,1.9,2,1.9,1.3,1.9]
    makeSpindleTrimmer(generator_name, lib_name=lib_name, shaft_hole=False, class_name=class_name, ddrill=ddrill, wbody=wbody, hbody=hbody, pinxoffset=pinxoffset, pinyoffset=pinyoffset, rmx2=rmx2, rmy2=rmy2, rmx3=rmx3, rmy3=rmy3, dscrew=dscrew, wscrew=wscrew, screwxoffset=screwxoffset, screwyoffset=screwyoffset, style=style, SMD_pads=SMD_pads, SMD_padsize=SMD_padsize, specialtags=[], add_description=add_description, name_additions=[], height3d=height3d)
    num_generated_fps += 1

    class_name="Bourns 3214G"
    wbody=4.6; hbody=4.8; pinxoffset=(wbody-5.2)/2.0+5.2; pinyoffset=(hbody-2.3)/2.0; height3d = 3.71; rmx2=-5.2; rmy2=1.15; rmx3=0; rmy3=2.3; ddrill=0.8; dscrew=1.78; wscrew = 0; screwxoffset = 0; screwyoffset = 1.27
    style = "screwleft"; SMD_pads = True; SMD_padsize = [1.3,1.3,1.3,2,1.3,1.3]
    makeSpindleTrimmer(generator_name, lib_name=lib_name, shaft_hole=False, class_name=class_name, ddrill=ddrill, wbody=wbody, hbody=hbody, pinxoffset=pinxoffset, pinyoffset=pinyoffset, rmx2=rmx2, rmy2=rmy2, rmx3=rmx3, rmy3=rmy3, dscrew=dscrew, wscrew=wscrew, screwxoffset=screwxoffset, screwyoffset=screwyoffset, style=style, SMD_pads=SMD_pads, SMD_padsize=SMD_padsize, specialtags=[], add_description=add_description, name_additions=[], height3d=height3d)
    num_generated_fps += 1

    class_name="Bourns 3214J"
    wbody=4.6; hbody=4.8; pinxoffset=(wbody-4)/2.0+4; pinyoffset=(hbody-2.3)/2.0; height3d = 3.71; rmx2=-4; rmy2=1.15; rmx3=0; rmy3=2.3; ddrill=0.8; dscrew=1.78; wscrew = 0; screwxoffset = 0; screwyoffset = 1.27
    style = "screwleft"; SMD_pads = True; SMD_padsize = [2,1.3,2,2,2,1.3]
    makeSpindleTrimmer(generator_name, lib_name=lib_name, shaft_hole=False, class_name=class_name, ddrill=ddrill, wbody=wbody, hbody=hbody, pinxoffset=pinxoffset, pinyoffset=pinyoffset, rmx2=rmx2, rmy2=rmy2, rmx3=rmx3, rmy3=rmy3, dscrew=dscrew, wscrew=wscrew, screwxoffset=screwxoffset, screwyoffset=screwyoffset, style=style, SMD_pads=SMD_pads, SMD_padsize=SMD_padsize, specialtags=[], add_description=add_description, name_additions=[], height3d=height3d)
    num_generated_fps += 1

    class_name="Bourns 3314J"; add_description = "http://www.bourns.com/docs/Product-Datasheets/3314.pdf"
    pins = 3; wbody=4.5; hbody=4.5; rmx2=-1.15; rmy2=4.0; rmx3=-2.3; rmy3=0; pinxoffset=(wbody+rmx3)/2.0-rmx3; pinyoffset=(hbody-rmy2)/2.0; height3d = 2.55; ddrill=0.8; dscrew=2.0; wscrew = 0; screwxoffset = wbody/2.0; screwyoffset = hbody/2.0
    style = "screwtop"; SMD_pads = True; SMD_padsize = [1.3,2.0,2.0,2.0,1.3,2.0]
    makeSpindleTrimmer(generator_name, lib_name=lib_name, shaft_hole=False, class_name=class_name, ddrill=ddrill, wbody=wbody, hbody=hbody, pinxoffset=pinxoffset, pinyoffset=pinyoffset, rmx2=rmx2, rmy2=rmy2, rmx3=rmx3, rmy3=rmy3, dscrew=dscrew, wscrew=wscrew, screwxoffset=screwxoffset, screwyoffset=screwyoffset, style=style, SMD_pads=SMD_pads, SMD_padsize=SMD_padsize, specialtags=[], add_description=add_description, name_additions=[], height3d=height3d)
    num_generated_fps += 1

    class_name="Bourns 3314G"
    pinyoffset=-1.25; rmy2 = 5.5; pinxoffset=(wbody+rmx3)/2.0-rmx3; pinyoffset=(hbody-rmy2)/2.0; SMD_padsize = [1.3,1.3,2.0,1.3,1.3,1.3]
    makeSpindleTrimmer(generator_name, lib_name=lib_name, shaft_hole=False, class_name=class_name, ddrill=ddrill, wbody=wbody, hbody=hbody, pinxoffset=pinxoffset, pinyoffset=pinyoffset, rmx2=rmx2, rmy2=rmy2, rmx3=rmx3, rmy3=rmy3, dscrew=dscrew, wscrew=wscrew, screwxoffset=screwxoffset, screwyoffset=screwyoffset, style=style, SMD_pads=SMD_pads, SMD_padsize=SMD_padsize, specialtags=[], add_description=add_description, name_additions=[], height3d=height3d)
    num_generated_fps += 1

    class_name="Bourns 3314R-1"
    wbody=5.0; pinxoffset=(wbody+rmx3)/2.0-rmx3; screwxoffset = wbody/2.0; ddrill = 3.2
    makeSpindleTrimmer(generator_name, lib_name=lib_name, shaft_hole=True, class_name=class_name, ddrill=ddrill, wbody=wbody, hbody=hbody, pinxoffset=pinxoffset, pinyoffset=pinyoffset, rmx2=rmx2, rmy2=rmy2, rmx3=rmx3, rmy3=rmy3, dscrew=dscrew, wscrew=wscrew, screwxoffset=screwxoffset, screwyoffset=screwyoffset, style=style, SMD_pads=SMD_pads, SMD_padsize=SMD_padsize, specialtags=[], add_description=add_description, name_additions=[], height3d=height3d)
    num_generated_fps += 1

    class_name="Bourns 3314R-GM5"
    rmx2=-1.155; rmy2 = 6.25; rmx3=-2.31; pinxoffset=(wbody+rmx3)/2.0-rmx3; pinyoffset=(hbody-rmy2)/2.0; ddrill = 3.2
    makeSpindleTrimmer(generator_name, lib_name=lib_name, shaft_hole=True, class_name=class_name, ddrill=ddrill, wbody=wbody, hbody=hbody, pinxoffset=pinxoffset, pinyoffset=pinyoffset, rmx2=rmx2, rmy2=rmy2, rmx3=rmx3, rmy3=rmy3, dscrew=dscrew, wscrew=wscrew, screwxoffset=screwxoffset, screwyoffset=screwyoffset, style=style, SMD_pads=SMD_pads, SMD_padsize=SMD_padsize, specialtags=["extended leadframe"], add_description=add_description, name_additions=[], height3d=height3d)
    num_generated_fps += 1

    # Disable this, it has a manual orientaion mark added in the output library
    class_name="Bourns 3314S"
    # wbody = 5.01; rmx2=-1.15; rmy2 = 4.05; rmx3=-2.3; pinxoffset=(wbody+rmx3)/2.0-rmx3; pinyoffset=(hbody-rmy2)/2.0;  height3d = 5.61; screwxoffset = wbody/2.0; style = "screwleft"; SMD_padsize = [1.2,1.75,1.6,1.75,1.2,1.75]
    # makeSpindleTrimmer(generator_name, lib_name=lib_name, shaft_hole=False, class_name=class_name, ddrill=ddrill, wbody=wbody, hbody=hbody, pinxoffset=pinxoffset, pinyoffset=pinyoffset, rmx2=rmx2, rmy2=rmy2, rmx3=rmx3, rmy3=rmy3, dscrew=dscrew, wscrew=wscrew, screwxoffset=screwxoffset, screwyoffset=screwyoffset, style=style, SMD_pads=SMD_pads, SMD_padsize=SMD_padsize, specialtags=[], add_description=add_description, name_additions=[], height3d=height3d)

    class_name="Bourns 3224W"; add_description = "https://www.bourns.com/docs/Product-Datasheets/3224.pdf"
    wbody=4.8; hbody=3.5; pinxoffset=(wbody-2.5)/2.0+2.5; pinyoffset=0.3; height3d = 5.1; rmx2=-1.25; rmy2=2.9; rmx3=-2.5; rmy3=0; ddrill=0.8; dscrew=1.5; wscrew = dscrew; screwxoffset = 1.2; screwyoffset = hbody-1.1
    style = "screwtop"; SMD_pads = True; SMD_padsize = [1.3,1.6,2,1.6,1.3,1.6]
    makeSpindleTrimmer(generator_name, lib_name=lib_name, shaft_hole=False, class_name=class_name, ddrill=ddrill, wbody=wbody, hbody=hbody, pinxoffset=pinxoffset, pinyoffset=pinyoffset, rmx2=rmx2, rmy2=rmy2, rmx3=rmx3, rmy3=rmy3, dscrew=dscrew, wscrew=wscrew, screwxoffset=screwxoffset, screwyoffset=screwyoffset, style=style, SMD_pads=SMD_pads, SMD_padsize=SMD_padsize, specialtags=[], add_description=add_description, name_additions=[], height3d=height3d)
    num_generated_fps += 1

    class_name="Bourns 3224X"
    wbody=4.8; hbody=3.5; pinxoffset=(wbody-2.5)/2.0+2.5; pinyoffset=-(5.1-3.5)/2.0; height3d = 5.3; rmx2=-1.15; rmy2=5.1; rmx3=-2.3; rmy3=0; ddrill=0.8; dscrew=1.5; wscrew = dscrew; screwxoffset = 1.2; screwyoffset = hbody-1.1
    style = "screwtop"; SMD_pads = True; SMD_padsize = [1.3,1.9,2,1.9,1.3,1.9]
    makeSpindleTrimmer(generator_name, lib_name=lib_name, shaft_hole=False, class_name=class_name, ddrill=ddrill, wbody=wbody, hbody=hbody, pinxoffset=pinxoffset, pinyoffset=pinyoffset, rmx2=rmx2, rmy2=rmy2, rmx3=rmx3, rmy3=rmy3, dscrew=dscrew, wscrew=wscrew, screwxoffset=screwxoffset, screwyoffset=screwyoffset, style=style, SMD_pads=SMD_pads, SMD_padsize=SMD_padsize, specialtags=[], add_description=add_description, name_additions=[], height3d=height3d)
    num_generated_fps += 1

    class_name="Bourns 3224G"
    wbody=4.6; hbody=4.8; pinxoffset=(wbody-5.2)/2.0+5.2; pinyoffset=(hbody-2.3)/2.0; height3d = 3.71; rmx2=-5.2; rmy2=1.15; rmx3=0; rmy3=2.3; ddrill=0.8; dscrew=1.78; wscrew = 0; screwxoffset = 0; screwyoffset = 1.27
    style = "screwleft"; SMD_pads = True; SMD_padsize = [1.3,1.3,1.3,2,1.3,1.3]
    makeSpindleTrimmer(generator_name, lib_name=lib_name, shaft_hole=False, class_name=class_name, ddrill=ddrill, wbody=wbody, hbody=hbody, pinxoffset=pinxoffset, pinyoffset=pinyoffset, rmx2=rmx2, rmy2=rmy2, rmx3=rmx3, rmy3=rmy3, dscrew=dscrew, wscrew=wscrew, screwxoffset=screwxoffset, screwyoffset=screwyoffset, style=style, SMD_pads=SMD_pads, SMD_padsize=SMD_padsize, specialtags=[], add_description=add_description, name_additions=[], height3d=height3d)
    num_generated_fps += 1

    class_name="Bourns 3224J"
    wbody=4.6; hbody=4.8; pinxoffset=(wbody-4)/2.0+4; pinyoffset=(hbody-2.3)/2.0; height3d = 3.71; rmx2=-4; rmy2=1.15; rmx3=0; rmy3=2.3; ddrill=0.8; dscrew=1.78; wscrew = 0; screwxoffset = 0; screwyoffset = 1.27
    style = "screwleft"; SMD_pads = True; SMD_padsize = [2,1.3,2,2,2,1.3]
    makeSpindleTrimmer(generator_name, lib_name=lib_name, shaft_hole=False, class_name=class_name, ddrill=ddrill, wbody=wbody, hbody=hbody, pinxoffset=pinxoffset, pinyoffset=pinyoffset, rmx2=rmx2, rmy2=rmy2, rmx3=rmx3, rmy3=rmy3, dscrew=dscrew, wscrew=wscrew, screwxoffset=screwxoffset, screwyoffset=screwyoffset, style=style, SMD_pads=SMD_pads, SMD_padsize=SMD_padsize, specialtags=[], add_description=add_description, name_additions=[], height3d=height3d)
    num_generated_fps += 1

    class_name="Bourns 3269W"; add_description = "https://www.bourns.com/docs/Product-Datasheets/3269.pdf"
    wbody=6.35; hbody=4.32; pinxoffset=(wbody-5.08)/2.0+5.08; pinyoffset=-0.25; height3d = 7.44; rmx2=-2.54; rmy2=4.83; rmx3=-5.08; rmy3=0; ddrill=0.8; dscrew=1.78; wscrew = dscrew; screwxoffset = wbody-1.002; screwyoffset = hbody-1.52
    style = "screwtop"; SMD_pads = True; SMD_padsize = [1.19,2.79]
    makeSpindleTrimmer(generator_name, lib_name=lib_name, shaft_hole=False, class_name=class_name, ddrill=ddrill, wbody=wbody, hbody=hbody, pinxoffset=pinxoffset, pinyoffset=pinyoffset, rmx2=rmx2, rmy2=rmy2, rmx3=rmx3, rmy3=rmy3, dscrew=dscrew, wscrew=wscrew, screwxoffset=screwxoffset, screwyoffset=screwyoffset, style=style, SMD_pads=SMD_pads, SMD_padsize=SMD_padsize, specialtags=[], add_description=add_description, name_additions=[], height3d=height3d)
    num_generated_fps += 1

    class_name="Bourns 3269X"
    wbody=6.35; hbody=4.32; pinxoffset=(wbody-5.08)/2.0+5.08; pinyoffset=-0.25; height3d = 7.44; rmx2=-2.54; rmy2=4.83; rmx3=-5.08; rmy3=0; ddrill=0.8; dscrew=1.78; wscrew = 1.52; screwxoffset = 0; screwyoffset = hbody-1.52
    style = "screwleft"; SMD_pads = True; SMD_padsize = [1.19,2.79]
    makeSpindleTrimmer(generator_name, lib_name=lib_name, shaft_hole=False, class_name=class_name, ddrill=ddrill, wbody=wbody, hbody=hbody, pinxoffset=pinxoffset, pinyoffset=pinyoffset, rmx2=rmx2, rmy2=rmy2, rmx3=rmx3, rmy3=rmy3, dscrew=dscrew, wscrew=wscrew, screwxoffset=screwxoffset, screwyoffset=screwyoffset, style=style, SMD_pads=SMD_pads, SMD_padsize=SMD_padsize, specialtags=[], add_description=add_description, name_additions=[], height3d=height3d)
    num_generated_fps += 1

    class_name="Bourns 3269P"
    wbody=6.35; hbody=6.35; pinxoffset=-(wbody-6.4)/2.0+6.4; pinyoffset=(hbody-5.08)/2.0; height3d = 5.21; rmx2=-6.4; rmy2=2.54; rmx3=0; rmy3=5.08; ddrill=0.8; dscrew=1.78; wscrew = 1.52; screwxoffset = 0; screwyoffset = 1.27
    style = "screwleft"; SMD_pads = True; SMD_padsize = [3.3,1.19]
    makeSpindleTrimmer(generator_name, lib_name=lib_name, shaft_hole=False, class_name=class_name, ddrill=ddrill, wbody=wbody, hbody=hbody, pinxoffset=pinxoffset, pinyoffset=pinyoffset, rmx2=rmx2, rmy2=rmy2, rmx3=rmx3, rmy3=rmy3, dscrew=dscrew, wscrew=wscrew, screwxoffset=screwxoffset, screwyoffset=screwyoffset, style=style, SMD_pads=SMD_pads, SMD_padsize=SMD_padsize, specialtags=[], add_description=add_description, name_additions=[], height3d=height3d)
    num_generated_fps += 1

    class_name="Vishay TS53YJ"; add_description = "https://www.vishay.com/docs/51008/ts53.pdf"
    wbody=5; hbody=5; pinxoffset=0.5+4; pinyoffset=(5-2.3)/2.0; height3d = 2.7; rmx2=-4; rmy2=1.15; rmx3=0; rmy3=2.3; ddrill=0.8; dscrew=2.3; wscrew = dscrew; screwxoffset = wbody/2.0; screwyoffset = hbody/2.0
    SMD_pads = True; SMD_padsize = [2,1.3,2,2,2,1.3]
    makeSpindleTrimmer(generator_name, lib_name=lib_name, shaft_hole=False, class_name=class_name, screwstyle="cross", ddrill=ddrill, wbody=wbody, hbody=hbody, pinxoffset=pinxoffset, pinyoffset=pinyoffset, rmx2=rmx2, rmy2=rmy2, rmx3=rmx3, rmy3=rmy3, dscrew=dscrew, wscrew=wscrew, screwxoffset=screwxoffset, screwyoffset=screwyoffset, style="screwtop", SMD_pads=SMD_pads, SMD_padsize=SMD_padsize, specialtags=[], add_description=add_description, name_additions=[], height3d=height3d)
    num_generated_fps += 1

    class_name="Vishay TS53YL"
    wbody=5; hbody=5; pinxoffset=-0.25+5.5; pinyoffset=(5-2.3)/2.0; height3d = 2.7; rmx2=-5.5; rmy2=1.15; rmx3=0; rmy3=2.3; ddrill=0.8; dscrew=2.3; wscrew = dscrew; screwxoffset = wbody/2.0; screwyoffset = hbody/2.0
    SMD_pads = True; SMD_padsize = [1.3,1.3,2,1.3,1.3,1.3]
    makeSpindleTrimmer(generator_name, lib_name=lib_name, shaft_hole=False, class_name=class_name, screwstyle="cross", ddrill=ddrill, wbody=wbody, hbody=hbody, pinxoffset=pinxoffset, pinyoffset=pinyoffset, rmx2=rmx2, rmy2=rmy2, rmx3=rmx3, rmy3=rmy3, dscrew=dscrew, wscrew=wscrew, screwxoffset=screwxoffset, screwyoffset=screwyoffset, style="screwtop", SMD_pads=SMD_pads, SMD_padsize=SMD_padsize, specialtags=[], add_description=add_description, name_additions=[], height3d=height3d)
    num_generated_fps += 1

    return num_generated_fps