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
from generators.tools.footprint.drawing_tools import *
from .footprint_scripts_LEDs import *
from generators.tools.spec.base_spec import BaseSpec


def create_footprints(spec: BaseSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification (not used by this generator).
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
    num_fps_generated = 0
    led_type = "round"

    d2 = 0
    R_POW = 0
    clname = "LED"
    lbname = "LED_THT"
    ddrill = 0.9

    # LED_D3.0mm
    led_type = "round"
    pins = 2
    pitch = 2.54
    diameter = 3
    w = 3.8
    h = w
    height3d = 4.3
    height3d_bottom = 1
    name_additions = None
    desc_extras_start = None
    desc_extras_end = None
    makeLEDRadial(
        generator_name,
        pins=pins,
        pitch=pitch,
        w=w,
        h=h,
        ddrill=ddrill,
        diameter=diameter,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=desc_extras_end,
        base_filename=clname,
        lib_name=lbname,
        name_additions=name_additions,
        height3d=height3d,
        height3d_bottom=height3d_bottom,
    )
    num_fps_generated += 1

    # LED_D3.0mm_Clear
    led_type = "round"
    pins = 2
    pitch = 2.54
    diameter = 3
    w = 3.8
    h = w
    height3d = 4.3
    height3d_bottom = 1
    name_additions = None
    desc_extras_start = None
    desc_extras_end = None
    makeLEDRadial(
        generator_name,
        pitch=pitch,
        w=w,
        h=h,
        ddrill=ddrill,
        diameter=diameter,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=["clear"],
        base_filename=clname,
        lib_name=lbname,
        name_additions=["Clear"],
        height3d=height3d,
        height3d_bottom=height3d_bottom,
    )
    num_fps_generated += 1

    # LED_D3.0mm_IRBlack
    led_type = "round"
    pins = 2
    pitch = 2.54
    diameter = 3
    w = 3.8
    h = w
    height3d = 4.3
    height3d_bottom = 1
    name_additions = None
    desc_extras_start = None
    desc_extras_end = None
    makeLEDRadial(
        generator_name,
        pins=pins,
        pitch=pitch,
        w=w,
        h=h,
        ddrill=ddrill,
        diameter=diameter,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=["infrared", "black"],
        tag_extras=["IR"],
        base_filename=clname,
        lib_name=lbname,
        name_additions=["IRBlack"],
        height3d=height3d,
        height3d_bottom=height3d_bottom,
    )
    num_fps_generated += 1

    # LED_D3.0mm_IRGrey
    led_type = "round"
    pins = 2
    pitch = 2.54
    diameter = 3
    w = 3.8
    h = w
    height3d = 4.3
    height3d_bottom = 1
    name_additions = None
    desc_extras_start = None
    desc_extras_end = None
    makeLEDRadial(
        generator_name,
        pins=pins,
        pitch=pitch,
        w=w,
        h=h,
        ddrill=ddrill,
        diameter=diameter,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=["infrared", "grey"],
        tag_extras=["IR"],
        base_filename=clname,
        lib_name=lbname,
        name_additions=["IRGrey"],
        height3d=height3d,
        height3d_bottom=height3d_bottom,
    )
    num_fps_generated += 1

    # LED_D3.0mm-3
    pins = 3
    desc_extras_end = [
        "https://www.kingbright.com/attachments/file/psearch/000/00/00/L-3VSURKCGKC(Ver.12A).pdf"
    ]
    makeLEDRadial(
        generator_name,
        pins=pins,
        pitch=pitch,
        w=w,
        h=h,
        ddrill=ddrill,
        diameter=diameter,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=desc_extras_end,
        base_filename=clname,
        lib_name=lbname,
        name_additions=name_additions,
        height3d=height3d,
        height3d_bottom=height3d_bottom,
    )
    num_fps_generated += 1

    # LED_D5.0mm
    pins = 2
    pitch = 2.54
    diameter = 5
    w = 5.8
    h = w
    height3d = 7.6
    height3d_bottom = 1
    name_additions = None
    desc_extras_start = None
    desc_extras_end = [
        "http://cdn-reichelt.de/documents/datenblatt/A500/LL-504BC2E-009.pdf"
    ]
    makeLEDRadial(
        generator_name,
        pins=pins,
        pitch=pitch,
        w=w,
        h=h,
        ddrill=ddrill,
        diameter=diameter,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=desc_extras_end,
        base_filename=clname,
        lib_name=lbname,
        name_additions=name_additions,
        height3d=height3d,
        height3d_bottom=height3d_bottom,
    )
    num_fps_generated += 1

    # LED_D5.0mm_Clear
    pins = 2
    pitch = 2.54
    diameter = 5
    w = 5.8
    h = w
    height3d = 7.6
    height3d_bottom = 1
    name_additions = None
    desc_extras_start = None
    desc_extras_end = [
        "clear",
        "http://cdn-reichelt.de/documents/datenblatt/A500/LL-504BC2E-009.pdf",
    ]
    makeLEDRadial(
        generator_name,
        pins=pins,
        pitch=pitch,
        w=w,
        h=h,
        ddrill=ddrill,
        diameter=diameter,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=desc_extras_end,
        base_filename=clname,
        lib_name=lbname,
        name_additions=["Clear"],
        height3d=height3d,
        height3d_bottom=height3d_bottom,
    )
    num_fps_generated += 1

    # LED_D5.0mm_IRBlack
    pins = 2
    pitch = 2.54
    diameter = 5
    w = 5.8
    h = w
    height3d = 7.6
    height3d_bottom = 1
    name_additions = None
    desc_extras_start = None
    desc_extras_end = [
        "infrared",
        "black",
        "http://cdn-reichelt.de/documents/datenblatt/A500/LL-504BC2E-009.pdf",
    ]
    makeLEDRadial(
        generator_name,
        pins=pins,
        pitch=pitch,
        w=w,
        h=h,
        ddrill=ddrill,
        diameter=diameter,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=desc_extras_end,
        tag_extras=["IR"],
        base_filename=clname,
        lib_name=lbname,
        name_additions=["IRBlack"],
        height3d=height3d,
        height3d_bottom=height3d_bottom,
    )
    num_fps_generated += 1

    # LED_D5.0mm_IRGrey
    pins = 2
    pitch = 2.54
    diameter = 5
    w = 5.8
    h = w
    height3d = 7.6
    height3d_bottom = 1
    name_additions = None
    desc_extras_start = None
    desc_extras_end = [
        "infrared",
        "grey",
        "http://cdn-reichelt.de/documents/datenblatt/A500/LL-504BC2E-009.pdf",
    ]
    makeLEDRadial(
        generator_name,
        pins=pins,
        pitch=pitch,
        w=w,
        h=h,
        ddrill=ddrill,
        diameter=diameter,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=desc_extras_end,
        tag_extras=["IR"],
        base_filename=clname,
        lib_name=lbname,
        name_additions=["IRGrey"],
        height3d=height3d,
        height3d_bottom=height3d_bottom,
    )
    num_fps_generated += 1

    # LED_D5.0mm-3
    pins = 3
    desc_extras_end = [
        "https://www.kingbright.com/attachments/file/psearch/000/00/00/L-59EGC(Ver.20A).pdf"
    ]
    makeLEDRadial(
        generator_name,
        pins=pins,
        pitch=pitch,
        w=w,
        h=h,
        ddrill=ddrill,
        diameter=diameter,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=desc_extras_end,
        base_filename=clname,
        lib_name=lbname,
        name_additions=name_additions,
        height3d=height3d,
        height3d_bottom=height3d_bottom,
    )
    num_fps_generated += 1

    # LED_D5.0mm-4_RGB, which would normally be called LED_D5.0mm-4
    pins = 4
    pitch = 1.27
    desc_extras_end = [
        "https://www.kingbright.com/attachments/file/psearch/000/00/00/L-154A4SUREQBFZGEW(Ver.13A).pdf"
    ]
    makeLEDRadial(
        generator_name,
        pins=pins,
        pitch=pitch,
        w=w,
        h=h,
        ddrill=ddrill,
        diameter=diameter,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=["RGB"],
        desc_extras_end=desc_extras_end,
        base_filename=clname,
        lib_name=lbname,
        name_additions=["RGB"],
        height3d=height3d,
        height3d_bottom=height3d_bottom,
    )
    num_fps_generated += 1

    # LED_D4.0mm
    pins = 2
    pitch = 2.54
    diameter = 4
    w = 4.8
    h = w
    height3d = 6
    height3d_bottom = 1
    name_additions = None
    desc_extras_start = None
    desc_extras_end = [
        "https://www.kingbright.com/attachments/file/psearch/000/00/00/L-43GD(Ver.17B).pdf"
    ]
    makeLEDRadial(
        generator_name,
        pins=pins,
        pitch=pitch,
        w=w,
        h=h,
        ddrill=ddrill,
        diameter=diameter,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=desc_extras_end,
        base_filename=clname,
        lib_name=lbname,
        name_additions=name_additions,
        height3d=height3d,
        height3d_bottom=height3d_bottom,
    )
    num_fps_generated += 1

    # LED_D8.0mm
    pins = 2
    pitch = 2.54
    diameter = 8
    w = 9
    h = w
    height3d = 9
    height3d_bottom = 2
    name_additions = None
    desc_extras_start = None
    desc_extras_end = [
        "http://cdn-reichelt.de/documents/datenblatt/A500/LED8MMGE_LED8MMGN_LED8MMRT%23KIN.pdf"
    ]
    makeLEDRadial(
        generator_name,
        pins=pins,
        pitch=pitch,
        w=w,
        h=h,
        ddrill=ddrill,
        diameter=diameter,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=desc_extras_end,
        base_filename=clname,
        lib_name=lbname,
        name_additions=name_additions,
        height3d=height3d,
        height3d_bottom=height3d_bottom,
    )
    num_fps_generated += 1

    # LED_D8.0mm-3
    pins = 3
    desc_extras_end = None
    makeLEDRadial(
        generator_name,
        pins=pins,
        pitch=pitch,
        w=w,
        h=h,
        ddrill=ddrill,
        diameter=diameter,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=desc_extras_end,
        base_filename=clname,
        lib_name=lbname,
        name_additions=name_additions,
        height3d=height3d,
        height3d_bottom=height3d_bottom,
    )
    num_fps_generated += 1

    # LED_D10.0mm
    pins = 2
    pitch = 2.54
    diameter = 10
    w = 11
    h = w
    height3d = 11.5
    height3d_bottom = 2
    name_additions = None
    desc_extras_start = None
    desc_extras_end = [
        "http://cdn-reichelt.de/documents/datenblatt/A500/LED10-4500RT%23KIN.pdf"
    ]
    makeLEDRadial(
        generator_name,
        pins=pins,
        pitch=pitch,
        w=w,
        h=h,
        ddrill=ddrill,
        diameter=diameter,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=desc_extras_end,
        base_filename=clname,
        lib_name=lbname,
        name_additions=name_additions,
        height3d=height3d,
        height3d_bottom=height3d_bottom,
    )
    num_fps_generated += 1

    # LED_D10.0mm-3
    pins = 3
    desc_extras_end = [
        "http://www.kingbright.com/attachments/file/psearch/000/00/20131112/L-819EGW(Ver.13A).pdf"
    ]
    makeLEDRadial(
        generator_name,
        pins=pins,
        pitch=pitch,
        w=w,
        h=h,
        ddrill=ddrill,
        diameter=diameter,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=desc_extras_end,
        base_filename=clname,
        lib_name=lbname,
        name_additions=name_additions,
        height3d=height3d,
        height3d_bottom=height3d_bottom,
    )
    num_fps_generated += 1

    # LED_D20.0mm
    pins = 2
    pitch = 2.54
    diameter = 20
    w = 23
    h = w
    height3d = 10
    height3d_bottom = 3.5
    name_additions = None
    desc_extras_start = None
    desc_extras_end = [
        "http://cdn-reichelt.de/documents/datenblatt/A500/DLC2-6GD%28V6%29.pdf"
    ]
    makeLEDRadial(
        generator_name,
        pins=pins,
        pitch=pitch,
        w=w,
        h=h,
        ddrill=ddrill,
        diameter=diameter,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=desc_extras_end,
        base_filename=clname,
        lib_name=lbname,
        name_additions=name_additions,
        height3d=height3d,
        height3d_bottom=height3d_bottom,
    )
    num_fps_generated += 1

    # LED_Oval_W5.2mm_H3.8mm
    led_type = "oval"
    pins = 2
    pitch = 2.54
    diameter = 0
    w = 5.2
    h = 3.8
    height3d = 7
    height3d_bottom = 0
    name_additions = None
    desc_extras_start = None
    desc_extras_end = [
        "https://www.kingbright.com/attachments/file/psearch/000/00/00/L-5603QBC-D(Ver.17B).pdf"
    ]
    makeLEDRadial(
        generator_name,
        pins=pins,
        pitch=pitch,
        w=w,
        h=h,
        ddrill=ddrill,
        diameter=diameter,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=desc_extras_end,
        base_filename=clname + "_Oval",
        lib_name=lbname,
        name_additions=name_additions,
        height3d=height3d,
        height3d_bottom=height3d_bottom,
    )
    num_fps_generated += 1

    # LED_D2.0mm_W4.8mm_H2.5mm_FlatTop
    led_type = "box"
    pins = 2
    pitch = 2.54
    diameter = 2
    w = 4.8
    h = 2.5
    height3d = 4.5
    height3d_bottom = 3.5
    name_additions = ["FlatTop"]
    desc_extras_start = ["Round", "Flat Top"]
    desc_extras_end = [
        "http://www.kingbright.com/attachments/file/psearch/000/00/20160808bak/L-13GD(Ver.9B).pdf"
    ]
    makeLEDRadial(
        generator_name,
        pins=pins,
        pitch=pitch,
        w=w,
        h=h,
        ddrill=ddrill,
        diameter=diameter,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=desc_extras_end,
        base_filename=clname + "",
        lib_name=lbname,
        name_additions=name_additions,
        height3d=height3d,
        height3d_bottom=height3d_bottom,
    )
    num_fps_generated += 1

    # LED_D1.8mm_W3.3mm_H2.4mm
    led_type = "box"
    pins = 2
    pitch = 2.54
    diameter = 1.8
    w = 3.3
    h = 2.4
    height3d = 1.4
    height3d_bottom = 1.6
    name_additions = None
    desc_extras_start = ["Round"]
    desc_extras_end = None
    makeLEDRadial(
        generator_name,
        pins=pins,
        pitch=pitch,
        w=w,
        h=h,
        ddrill=ddrill,
        diameter=diameter,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=desc_extras_end,
        base_filename=clname + "",
        lib_name=lbname,
        name_additions=name_additions,
        height3d=height3d,
        height3d_bottom=height3d_bottom,
    )
    num_fps_generated += 1

    # LED_D3.0mm_FlatTop
    led_type = "round"
    pins = 2
    pitch = 2.54
    diameter = 3
    w = 3.8
    h = w
    height3d = 4.8
    height3d_bottom = 6 - 4.8
    name_additions = ["FlatTop"]
    desc_extras_start = ["Round", "Flat Top"]
    desc_extras_end = [
        "https://www.kingbright.com/attachments/file/psearch/000/00/00/L-47XEC(Ver.14A).pdf"
    ]
    makeLEDRadial(
        generator_name,
        pins=pins,
        pitch=pitch,
        w=w,
        h=h,
        ddrill=ddrill,
        diameter=diameter,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=desc_extras_end,
        base_filename=clname + "",
        lib_name=lbname,
        name_additions=name_additions,
        height3d=height3d,
        height3d_bottom=height3d_bottom,
    )
    num_fps_generated += 1

    # LED_D5.0mm_FlatTop
    led_type = "round"
    pins = 2
    pitch = 2.54
    diameter = 5
    w = 5.9
    h = w
    height3d = 8.6
    height3d_bottom = 1
    name_additions = ["FlatTop"]
    desc_extras_start = ["Round", "Flat Top"]
    desc_extras_end = [
        "https://www.kingbright.com/attachments/file/psearch/000/00/watermark00/L-483GDT(Ver.12B).pdf"
    ]
    makeLEDRadial(
        generator_name,
        pins=pins,
        pitch=pitch,
        w=w,
        h=h,
        ddrill=ddrill,
        diameter=diameter,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=desc_extras_end,
        base_filename=clname + "",
        lib_name=lbname,
        name_additions=name_additions,
        height3d=height3d,
        height3d_bottom=height3d_bottom,
    )
    num_fps_generated += 1

    # LED_D2.0mm_W4.0mm_H2.8mm_FlatTop
    led_type = "box"
    pins = 2
    pitch = 2.54
    diameter = 2
    w = 4
    h = 2.8
    height3d = 1.95
    height3d_bottom = 5 - 1.95
    name_additions = ["FlatTop"]
    desc_extras_start = ["Round", "Flat Top"]
    desc_extras_end = [
        "https://www.kingbright.com/attachments/file/psearch/000/00/00/L-1034IDT(Ver.14A).pdf"
    ]
    makeLEDRadial(
        generator_name,
        pins=pins,
        pitch=pitch,
        w=w,
        h=h,
        ddrill=ddrill,
        diameter=diameter,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=desc_extras_end,
        base_filename=clname + "",
        lib_name=lbname,
        name_additions=name_additions,
        height3d=height3d,
        height3d_bottom=height3d_bottom,
    )
    num_fps_generated += 1

    # LED_Rectangular_W3.9mm_H1.8mm
    led_type = "box"
    pins = 2
    pitch = 2.54
    diameter = 0
    w = 3.9
    h = 1.75
    height3d = 7
    height3d_bottom = 0
    name_additions = None
    desc_extras_start = None
    desc_extras_end = [
        "http://www.kingbright.com/attachments/file/psearch/000/00/20160808bak/L-2774GD(Ver.7B).pdf"
    ]
    makeLEDRadial(
        generator_name,
        pins=pins,
        pitch=pitch,
        w=w,
        h=h,
        ddrill=ddrill,
        diameter=diameter,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=desc_extras_end,
        base_filename=clname + "_Rectangular",
        lib_name=lbname,
        name_additions=name_additions,
        height3d=height3d,
        height3d_bottom=height3d_bottom,
    )
    num_fps_generated += 1

    # LED_Rectangular_W3.9mm_H1.9mm
    led_type = "box"
    pins = 2
    pitch = 2.54
    diameter = 0
    w = 3.9
    h = 1.9
    height3d = 7
    height3d_bottom = 0
    name_additions = None
    desc_extras_start = None
    desc_extras_end = [
        "https://www.kingbright.com/attachments/file/psearch/000/00/watermark00/L-144GDT(Ver.11B).pdf"
    ]
    makeLEDRadial(
        generator_name,
        pins=pins,
        pitch=pitch,
        w=w,
        h=h,
        ddrill=ddrill,
        diameter=diameter,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=desc_extras_end,
        base_filename=clname + "_Rectangular",
        lib_name=lbname,
        name_additions=name_additions,
        height3d=height3d,
        height3d_bottom=height3d_bottom,
    )
    num_fps_generated += 1

    # LED_Rectangular_W3.0mm_H2.0mm
    led_type = "box"
    pins = 2
    pitch = 2.54
    diameter = 0
    w = 3
    h = 2
    height3d = 7
    height3d_bottom = 0
    name_additions = None
    desc_extras_start = None
    desc_extras_end = [
        "http://www.kingbright.com/attachments/file/psearch/000/00/20160808bak/L-169XCGDK(Ver.8B).pdf"
    ]
    makeLEDRadial(
        generator_name,
        pins=pins,
        pitch=pitch,
        w=w,
        h=h,
        ddrill=ddrill,
        diameter=diameter,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=desc_extras_end,
        base_filename=clname + "_Rectangular",
        lib_name=lbname,
        name_additions=name_additions,
        height3d=height3d,
        height3d_bottom=height3d_bottom,
    )
    num_fps_generated += 1

    # LED_Rectangular_W5.0mm_H2.0mm
    led_type = "box"
    pins = 2
    pitch = 2.54
    diameter = 0
    w = 5
    h = 2
    height3d = 9.7
    height3d_bottom = 0
    name_additions = None
    desc_extras_start = None
    desc_extras_end = [
        "http://www.kingbright.com/attachments/file/psearch/000/00/00/L-169XCGDK(Ver.9B).pdf"
    ]
    makeLEDRadial(
        generator_name,
        pins=pins,
        pitch=pitch,
        w=w,
        h=h,
        ddrill=ddrill,
        diameter=diameter,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=desc_extras_end,
        base_filename=clname + "_Rectangular",
        lib_name=lbname,
        name_additions=name_additions,
        height3d=height3d,
        height3d_bottom=height3d_bottom,
    )
    num_fps_generated += 1

    # LED_Rectangular_W5.0mm_H2.0mm-3Pins
    led_type = "box"
    pins = 3
    pitch = 2.54
    diameter = 0
    w = 5
    h = 2
    height3d = 9.7
    height3d_bottom = 0
    name_additions = None
    desc_extras_start = None
    desc_extras_end = [
        "http://www.kingbright.com/attachments/file/psearch/000/00/20160808bak/L-169XCGDK(Ver.8B).pdf"
    ]
    makeLEDRadial(
        generator_name,
        pins=pins,
        pitch=pitch,
        w=w,
        h=h,
        ddrill=ddrill,
        diameter=diameter,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=desc_extras_end,
        base_filename=clname + "_Rectangular",
        lib_name=lbname,
        name_additions=name_additions,
        height3d=height3d,
        height3d_bottom=height3d_bottom,
    )
    num_fps_generated += 1

    # LED_Rectangular_W5.0mm_H5.0mm
    led_type = "box"
    pins = 2
    pitch = 2.54
    diameter = 0
    w = 5
    h = 5
    height3d = 9.7
    height3d_bottom = 0
    name_additions = None
    desc_extras_start = None
    desc_extras_end = [
        "http://www.kingbright.com/attachments/file/psearch/000/00/20160808bak/L-169XCGDK(Ver.8B).pdf"
    ]
    makeLEDRadial(
        generator_name,
        pins=pins,
        pitch=pitch,
        w=w,
        h=h,
        ddrill=ddrill,
        diameter=diameter,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=desc_extras_end,
        base_filename=clname + "_Rectangular",
        lib_name=lbname,
        name_additions=name_additions,
        height3d=height3d,
        height3d_bottom=height3d_bottom,
    )
    num_fps_generated += 1

    # LED_SideEmitter_Rectangular_W4.5mm_H1.6mm
    led_type = "box"
    pins = 2
    pitch = 2.54
    diameter = 0
    w = 4.5
    h = 1.6
    height3d = 5.7
    height3d_bottom = 0
    name_additions = None
    desc_extras_start = ["Side Emitter"]
    desc_extras_end = [
        "http://cdn-reichelt.de/documents/datenblatt/A500/LED15MMGE_LED15MMGN%23KIN.pdf"
    ]
    makeLEDRadial(
        generator_name,
        pins=pins,
        pitch=pitch,
        w=w,
        h=h,
        ddrill=ddrill,
        diameter=diameter,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=desc_extras_end,
        base_filename=clname + "_SideEmitter_Rectangular",
        lib_name=lbname,
        name_additions=name_additions,
        height3d=height3d,
        height3d_bottom=height3d_bottom,
    )
    num_fps_generated += 1

    # LED_D3.0mm_Horizontal_O-.--mm_Z-.--mm
    led_type = "round"
    pins = 2
    pitch = 2.54
    dled = 3
    dledout = 3.8
    offset = 2.54
    wled = 5.3
    height3d = 3
    name_additions = None
    desc_extras_start = None
    desc_extras_end = None

    offsets = [1.27, 3.81, 6.35]
    for ledypos in [2, 6, 10]:
        for offset in offsets:
            makeLEDHorizontal(
                generator_name,
                ledypos=ledypos,
                pins=pins,
                pitch=pitch,
                ddrill=ddrill,
                dled=dled,
                dledout=dledout,
                offsetled=offset,
                wled=wled,
                led_type=led_type,
                has3d=1,
                fpname_override="",
                desc_extras_start=desc_extras_start,
                desc_extras_end=desc_extras_end,
                base_filename=clname,
                lib_name=lbname,
                name_additions=name_additions,
                height3d=height3d,
            )
            num_fps_generated += 1

    # LED_D3.0mm_Horizontal_O1.27mm_Z2.0mm_Clear
    offset = 1.27
    ledypos = 2.0
    makeLEDHorizontal(
        generator_name,
        ledypos=ledypos,
        pins=pins,
        pitch=pitch,
        ddrill=ddrill,
        dled=dled,
        dledout=dledout,
        offsetled=offset,
        wled=wled,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=["clear"],
        base_filename=clname,
        lib_name=lbname,
        name_additions=["Clear"],
        height3d=height3d,
    )
    num_fps_generated += 1

    # LED_D3.0mm_Horizontal_O1.27mm_Z2.0mm_IRBlack
    makeLEDHorizontal(
        generator_name,
        ledypos=ledypos,
        pins=pins,
        pitch=pitch,
        ddrill=ddrill,
        dled=dled,
        dledout=dledout,
        offsetled=offset,
        wled=wled,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=["infrared", "black"],
        tag_extras=["IR"],
        base_filename=clname,
        lib_name=lbname,
        name_additions=["IRBlack"],
        height3d=height3d,
    )
    num_fps_generated += 1

    # LED_D3.0mm_Horizontal_O1.27mm_Z2.0mm_IRGrey
    makeLEDHorizontal(
        generator_name,
        ledypos=ledypos,
        pins=pins,
        pitch=pitch,
        ddrill=ddrill,
        dled=dled,
        dledout=dledout,
        offsetled=offset,
        wled=wled,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=["infrared", "grey"],
        tag_extras=["IR"],
        base_filename=clname,
        lib_name=lbname,
        name_additions=["IRGrey"],
        height3d=height3d,
    )
    num_fps_generated += 1

    # LED_D5.0mm_Horizontal_O-.--mm_Z-.--mm
    led_type = "round"
    pins = 2
    pitch = 2.54
    dled = 5
    dledout = 5.8
    offset = 2.54
    wled = 8.6
    height3d = 5
    name_additions = None
    desc_extras_start = None
    desc_extras_end = None
    for ledypos in [3, 9, 15]:
        for offset in offsets:
            makeLEDHorizontal(
                generator_name,
                ledypos=ledypos,
                pins=pins,
                pitch=pitch,
                ddrill=ddrill,
                dled=dled,
                dledout=dledout,
                offsetled=offset,
                wled=wled,
                led_type=led_type,
                has3d=1,
                fpname_override="",
                desc_extras_start=desc_extras_start,
                desc_extras_end=desc_extras_end,
                base_filename=clname,
                lib_name=lbname,
                name_additions=name_additions,
                height3d=height3d,
            )
            num_fps_generated += 1

    # LED_D5.0mm_Horizontal_O1.27mm_Z3.0mm_Clear
    offset = 1.27
    ledypos = 3.0
    makeLEDHorizontal(
        generator_name,
        ledypos=ledypos,
        pins=pins,
        pitch=pitch,
        ddrill=ddrill,
        dled=dled,
        dledout=dledout,
        offsetled=offset,
        wled=wled,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=["clear"],
        base_filename=clname,
        lib_name=lbname,
        name_additions=["Clear"],
        height3d=height3d,
    )
    num_fps_generated += 1

    # LED_D5.0mm_Horizontal_O1.27mm_Z3.0mm_IRBlack
    makeLEDHorizontal(
        generator_name,
        ledypos=ledypos,
        pins=pins,
        pitch=pitch,
        ddrill=ddrill,
        dled=dled,
        dledout=dledout,
        offsetled=offset,
        wled=wled,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=["infrared", "black"],
        tag_extras=["IR"],
        base_filename=clname,
        lib_name=lbname,
        name_additions=["IRBlack"],
        height3d=height3d,
    )
    num_fps_generated += 1

    # LED_D5.0mm_Horizontal_O1.27mm_Z3.0mm_IRGrey
    makeLEDHorizontal(
        generator_name,
        ledypos=ledypos,
        pins=pins,
        pitch=pitch,
        ddrill=ddrill,
        dled=dled,
        dledout=dledout,
        offsetled=offset,
        wled=wled,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=["infrared", "grey"],
        tag_extras=["IR"],
        base_filename=clname,
        lib_name=lbname,
        name_additions=["IRGrey"],
        height3d=height3d,
    )
    num_fps_generated += 1

    # LED_D5.0mm-3_Horizontal_O3.81mm_Z3.0mm
    offset = 3.81
    ledypos = 3.0
    makeLEDHorizontal(
        generator_name,
        ledypos=ledypos,
        pins=3,
        pitch=pitch,
        ddrill=ddrill,
        dled=dled,
        dledout=dledout,
        offsetled=offset,
        wled=wled,
        led_type=led_type,
        has3d=1,
        fpname_override="",
        desc_extras_start=desc_extras_start,
        desc_extras_end=desc_extras_end,
        base_filename=clname,
        lib_name=lbname,
        name_additions=name_additions,
        height3d=height3d,
    )
    num_fps_generated += 1

    # LED_D1.8mm_W1.8mm_H2.4mm_Horizontal_O-.--mm_Z-.-mm
    led_type = "box"
    pins = 2
    pitch = 2.54
    dled = 1.8
    dledout = 3.3
    wled = 3
    wledback = 1.6
    height3d = 2.4
    height3d_bottom = 1.6
    name_additions = None
    desc_extras_start = None
    desc_extras_end = None
    for ledypos in [1.65, 1.65 + 3.3, 1.65 + 3.3 * 2]:
        for offset in offsets:
            makeLEDHorizontal(
                generator_name,
                ledypos=ledypos,
                pins=pins,
                pitch=pitch,
                ddrill=ddrill,
                dled=dled,
                dledout=dledout,
                wledback=wledback,
                offsetled=offset,
                wled=wled,
                led_type=led_type,
                has3d=1,
                fpname_override="",
                desc_extras_start=desc_extras_start,
                desc_extras_end=desc_extras_end,
                base_filename=clname + "",
                lib_name=lbname,
                name_additions=name_additions,
                height3d=height3d,
            )
            num_fps_generated += 1

    # LED_Rectangular_W5.0mm_H2.0mm_Horizontal_O-.--mm_Z-.-mm
    led_type = "box"
    pins = 2
    pitch = 2.54
    dled = 5
    dledout = 5
    wled = 9.7
    wledback = 0
    height3d = 2
    height3d_bottom = 1.6
    name_additions = None
    desc_extras_start = None
    desc_extras_end = None
    for ledypos in [1, 3, 5]:
        for offset in offsets:
            makeLEDHorizontal(
                generator_name,
                ledypos=ledypos,
                pins=pins,
                pitch=pitch,
                ddrill=ddrill,
                dled=dled,
                dledout=dledout,
                wledback=wledback,
                offsetled=offset,
                wled=wled,
                led_type=led_type,
                has3d=1,
                fpname_override="",
                desc_extras_start=desc_extras_start,
                desc_extras_end=desc_extras_end,
                base_filename=clname + "_Rectangular",
                lib_name=lbname,
                name_additions=name_additions,
                height3d=height3d,
            )
            num_fps_generated += 1
    return num_fps_generated
