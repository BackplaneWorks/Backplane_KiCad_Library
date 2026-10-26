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
from KicadModTree.nodes.base.Pad import Pad  # NOQA
from generators.tools.footprint.save_footprint import write_footprint


def create_shielding(name, outer_size, size,
                     attachment_drill, attachment_diameter, attachment_positions):

    attachment_positions = sorted(attachment_positions)

    lib_name = "RF_Shielding"
    kicad_mod = Footprint(name, FootprintType.THT)

    # init kicad footprint
    kicad_mod.setDescription('WE-SHC Shielding Cabinet THT {size}x{size}mm'.format(size=size))
    kicad_mod.setTags('Shielding Cabinet')

    courtjard_size = outer_size / 2. + attachment_diameter / 2. + 0.25

    # set general values
    kicad_mod.append(Property(name=Property.REFERENCE, text='REF**', at=[0, -courtjard_size - 1], layer='F.SilkS'))
    kicad_mod.append(Property(name=Property.VALUE, text=name, at=[0, courtjard_size + 1], layer='F.Fab'))

    # create courtyard
    kicad_mod.append(Rectangle(start=[-courtjard_size, -courtjard_size],
                              end=[courtjard_size, courtjard_size],
                              layer='F.CrtYd'))

    # create Fabriaction Layer
    kicad_mod.append(Rectangle(start=[-size / 2., -size / 2.],
                              end=[size / 2., size / 2.],
                              layer='F.Fab'))

    general_kwargs = {'number': 1,
                      'type': Pad.TYPE_THT,
                      'shape': Pad.SHAPE_CIRCLE,
                      'size': [attachment_diameter, attachment_diameter],
                      'drill': attachment_drill,
                      'layers': Pad.LAYERS_THT}

    # create pads
    for position in attachment_positions:
        kicad_mod.append(Pad(at=[outer_size / 2., position / 2.], **general_kwargs))
        kicad_mod.append(Pad(at=[-outer_size / 2., position / 2.], **general_kwargs))
        kicad_mod.append(Pad(at=[position / 2., outer_size / 2.], **general_kwargs))
        kicad_mod.append(Pad(at=[position / 2., -outer_size / 2.], **general_kwargs))

        if position != 0. or 2*outer_size == 2*position:
            kicad_mod.append(Pad(at=[outer_size / 2., -position / 2.], **general_kwargs))
            kicad_mod.append(Pad(at=[-outer_size / 2., -position / 2.], **general_kwargs))
            kicad_mod.append(Pad(at=[-position / 2., outer_size / 2.], **general_kwargs))
            kicad_mod.append(Pad(at=[-position / 2., -outer_size / 2.], **general_kwargs))

    # create silk screen
    silk_padding = 0.2
    silk_outline = size / 2. + silk_padding

    pad_padding = 0.4

    if attachment_positions[0] != 0.:
        line_end = attachment_positions[0] / 2. - attachment_diameter / 2. - pad_padding
        kicad_mod.append(Line(start=[silk_outline, line_end], end=[silk_outline, -line_end], layer='F.SilkS'))
        kicad_mod.append(Line(start=[-silk_outline, -line_end], end=[-silk_outline, line_end], layer='F.SilkS'))
        kicad_mod.append(Line(start=[line_end, silk_outline], end=[-line_end, silk_outline], layer='F.SilkS'))
        kicad_mod.append(Line(start=[line_end, -silk_outline], end=[-line_end, -silk_outline], layer='F.SilkS'))

    for begin, end in zip(attachment_positions, attachment_positions[1:]):
        line_begin = begin / 2. + attachment_diameter / 2. + pad_padding
        line_end = end / 2. - attachment_diameter / 2. - pad_padding
        kicad_mod.append(Line(start=[silk_outline, line_begin], end=[silk_outline, line_end], layer='F.SilkS'))
        kicad_mod.append(Line(start=[silk_outline, -line_begin], end=[silk_outline, -line_end], layer='F.SilkS'))
        kicad_mod.append(Line(start=[-silk_outline, line_begin], end=[-silk_outline, line_end], layer='F.SilkS'))
        kicad_mod.append(Line(start=[-silk_outline, -line_begin], end=[-silk_outline, -line_end], layer='F.SilkS'))
        kicad_mod.append(Line(start=[line_begin, silk_outline], end=[line_end, silk_outline], layer='F.SilkS'))
        kicad_mod.append(Line(start=[line_begin, -silk_outline], end=[line_end, -silk_outline], layer='F.SilkS'))
        kicad_mod.append(Line(start=[-line_begin, silk_outline], end=[-line_end, silk_outline], layer='F.SilkS'))
        kicad_mod.append(Line(start=[-line_begin, -silk_outline], end=[-line_end, -silk_outline], layer='F.SilkS'))

    if attachment_positions[-1] != outer_size:
        line_begin = attachment_positions[-1] / 2. + attachment_diameter / 2. + pad_padding
        line_end = outer_size / 2. + silk_padding
        kicad_mod.append(Line(start=[silk_outline, line_begin], end=[silk_outline, line_end], layer='F.SilkS'))
        kicad_mod.append(Line(start=[silk_outline, -line_begin], end=[silk_outline, -line_end], layer='F.SilkS'))
        kicad_mod.append(Line(start=[-silk_outline, line_begin], end=[-silk_outline, line_end], layer='F.SilkS'))
        kicad_mod.append(Line(start=[-silk_outline, -line_begin], end=[-silk_outline, -line_end], layer='F.SilkS'))
        kicad_mod.append(Line(start=[line_begin, silk_outline], end=[line_end, silk_outline], layer='F.SilkS'))
        kicad_mod.append(Line(start=[line_begin, -silk_outline], end=[line_end, -silk_outline], layer='F.SilkS'))
        kicad_mod.append(Line(start=[-line_begin, silk_outline], end=[-line_end, silk_outline], layer='F.SilkS'))
        kicad_mod.append(Line(start=[-line_begin, -silk_outline], end=[-line_end, -silk_outline], layer='F.SilkS'))

    # fix KLC issue 6.3
    # kicad_mod.insert(Translation(outer_size / 2., attachment_positions[-1] / 2.))

    # write file
    write_footprint(kicad_mod, lib_name, generator_name)


def generate_all(global_config) -> int:
    # http://katalog.we-online.de/pbs/datasheet/36503205.pdf
    create_shielding('Würth_36503205_20x20mm', 20.5, 20.5, 1.1, 1.7, [5.08, 15.24])

    # http://katalog.we-online.de/pbs/datasheet/36503255.pdf
    create_shielding('Würth_36503255_25x25mm', 25.5, 25.5, 1.1, 1.7, [0, 10.16, 20.32])

    # http://katalog.we-online.de/pbs/datasheet/36503305.pdf
    create_shielding('Würth_36503305_30x30mm', 30.5, 30.5, 1.1, 1.7, [5.08, 15.24, 25.40])

    # http://katalog.we-online.de/pbs/datasheet/36503505.pdf
    create_shielding('Würth_36503505_50x50mm', 50.5, 50.5, 1.1, 1.7, [5.08, 15.24, 25.40, 35.56, 45.72])

    # http://katalog.we-online.de/pbs/datasheet/36503605.pdf
    create_shielding('Würth_36503605_60x60mm', 60.5, 60.5, 1.1, 1.7, [5.08, 15.24, 25.40, 35.56, 45.72, 55.88])
    
    return 5