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
from ..footprint_scripts_terminal_blocks import *


def generate_all(generator_name: str) -> int:
    num_fps_generated = 0

    classname="TerminalBlock_MetzConnect"

    block_size=[4,4]
    block_offset=[0,0]
    pins=[[1.5,0],[-1.5,0]]
    ddrill=1.5
    pad=[3,3]
    screw_diameter=3
    screw_offset=[0,0]
    slit_screw=True
    name="360272"
    webpage="https://media.metz-connect.com/files/171/Data_sheet_360272.PDF "
    footprint_name="TerminalBlock_MetzConnect_{0}_1x01_Horizontal_ScrewM2.6".format(name)
    classname_description="single screw terminal block Metz Connect {0}".format(name)
    makeScrewTerminalSingleStd(generator_name, footprint_name, block_size=block_size, block_offset=block_offset, pins=pins, ddrill=ddrill, pad=pad, screw_diameter=screw_diameter, screw_offset=screw_offset, slit_screw=slit_screw,
                        tags_additional=[], lib_name=classname, classname=classname, classname_description=classname_description, webpage=webpage)
    num_fps_generated += 1

    block_size=[5,4]
    block_offset=[0.5,0]
    name="360273"
    webpage="https://media.metz-connect.com/files/171/Data_sheet_360273.PDF "
    footprint_name="TerminalBlock_MetzConnect_{0}_1x01_Horizontal_ScrewM2.6_WireProtection".format(name)
    classname_description="single screw terminal block Metz Connect {0}".format(name)
    makeScrewTerminalSingleStd(generator_name, footprint_name, block_size=block_size, block_offset=block_offset, pins=pins, ddrill=ddrill, pad=pad, screw_diameter=screw_diameter, screw_offset=screw_offset, slit_screw=slit_screw,
                        tags_additional=[], lib_name=classname, classname=classname, classname_description=classname_description, webpage=webpage)
    num_fps_generated += 1

    block_size=[5,5]
    block_offset=[0,0]
    pins=[[2,0],[-2,0]]
    ddrill=1.5
    pad=[3,3]
    screw_diameter=4
    screw_offset=[0,0]
    slit_screw=True
    name="360410"
    webpage="https://media.metz-connect.com/files/171/Data_sheet_360410.PDF "
    footprint_name="TerminalBlock_MetzConnect_{0}_1x01_Horizontal_ScrewM3.0".format(name)
    classname_description="single screw terminal block Metz Connect {0}".format(name)
    makeScrewTerminalSingleStd(generator_name, footprint_name, block_size=block_size, block_offset=block_offset, pins=pins, ddrill=ddrill, pad=pad, screw_diameter=screw_diameter, screw_offset=screw_offset, slit_screw=slit_screw,
                        tags_additional=[], lib_name=classname, classname=classname, classname_description=classname_description, webpage=webpage)
    num_fps_generated += 1

    name="360381"
    webpage="https://media.metz-connect.com/files/171/Data_sheet_360381.PDF "
    footprint_name="TerminalBlock_MetzConnect_{0}_1x01_Horizontal_ScrewM3.0".format(name)
    classname_description="single screw terminal block Metz Connect {0}".format(name)
    makeScrewTerminalSingleStd(generator_name, footprint_name, block_size=block_size, block_offset=block_offset, pins=pins, ddrill=ddrill, pad=pad, screw_diameter=screw_diameter, screw_offset=screw_offset, slit_screw=slit_screw,
                        tags_additional=[], lib_name=classname, classname=classname, classname_description=classname_description, webpage=webpage)
    num_fps_generated += 1

    block_size=[6,4]
    block_offset=[1,0]
    name="360322"
    webpage="https://media.metz-connect.com/files/171/Data_sheet_360322.PDF "
    footprint_name="TerminalBlock_MetzConnect_{0}_1x01_Horizontal_ScrewM3.0_WireProtection".format(name)
    classname_description="single screw terminal block Metz Connect {0}".format(name)
    makeScrewTerminalSingleStd(generator_name, footprint_name, block_size=block_size, block_offset=block_offset, pins=pins, ddrill=ddrill, pad=pad, screw_diameter=screw_diameter, screw_offset=screw_offset, slit_screw=slit_screw,
                        tags_additional=[], lib_name=classname, classname=classname, classname_description=classname_description, webpage=webpage)
    num_fps_generated += 1

    block_size=[9, 7.3]
    block_offset=[0,0]
    pins=[[2,0],[-2,0]]
    ddrill=1.5
    pad=[3,3]
    screw_diameter=4
    screw_offset=[0,0]
    slit_screw=True
    name="360291"
    webpage="https://media.metz-connect.com/files/171/Data_sheet_360291.PDF "
    footprint_name="TerminalBlock_MetzConnect_{0}_1x01_Horizontal_ScrewM3.0_Boxed".format(name)
    classname_description="single screw terminal block Metz Connect {0}".format(name)
    makeScrewTerminalSingleStd(generator_name, footprint_name, block_size=block_size, block_offset=block_offset, pins=pins, ddrill=ddrill, pad=pad, screw_diameter=screw_diameter, screw_offset=screw_offset, slit_screw=slit_screw,
                        tags_additional=[], lib_name=classname, classname=classname, classname_description=classname_description, webpage=webpage)
    num_fps_generated += 1

    block_size=[9, 7.3]
    block_offset=[0,0]
    pins=[[0,0]]
    ddrill=1.5
    pad=[3,3]
    screw_diameter=4
    screw_offset=[0,0]
    slit_screw=True
    name="360271"
    webpage="https://www.metz-connect.com/media/file/8a8a80ea6e17c2e6016e3b8ef7cd2d65.de.0/product_summary_u_contact_de_en_fr.pdf "
    footprint_name="TerminalBlock_MetzConnect_{0}_1x01_Horizontal_ScrewM3.0_Boxed".format(name)
    classname_description="single screw terminal block Metz Connect {0}".format(name)
    makeScrewTerminalSingleStd(generator_name, footprint_name, block_size=block_size, block_offset=block_offset, pins=pins, ddrill=ddrill, pad=pad, screw_diameter=screw_diameter, screw_offset=screw_offset, slit_screw=slit_screw,
                        tags_additional=[], lib_name=classname, classname=classname, classname_description=classname_description, webpage=webpage)
    num_fps_generated += 1

    block_size=[9,9]
    block_offset=[0,0]
    pins=[[4,4],[-4,4],[4,-4],[-4,-4]]
    ddrill=1.6
    pad=[3.2,3.2]
    screw_diameter=7
    screw_offset=[0,0]
    slit_screw=True
    name="360425"
    webpage="https://www.metz-connect.com/media/file/8a8a80ea6e17c2e6016e3b8ef7cd2d65.de.0/product_summary_u_contact_de_en_fr.pdf "
    footprint_name="TerminalBlock_MetzConnect_{0}_1x01_Horizontal_ScrewM4.0_Boxed".format(name)
    classname_description="single screw terminal block Metz Connect {0}".format(name)
    makeScrewTerminalSingleStd(generator_name, footprint_name, block_size=block_size, block_offset=block_offset, pins=pins, ddrill=ddrill, pad=pad, screw_diameter=screw_diameter, screw_offset=screw_offset, slit_screw=slit_screw,
                        tags_additional=[], lib_name=classname, classname=classname, classname_description=classname_description, webpage=webpage)
    num_fps_generated += 1

    return num_fps_generated
