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
from kilibs.config import global_config as GC
from generators.tools.footprint.save_footprint import write_footprint
global_config = GC.DefaultGlobalConfig()


def smd_chip(generator_name: str, args):
    # init kicad footprint
    kicad_mod = Footprint(args['name'], FootprintType.SMD)
    kicad_mod.setDescription(args['description'])
    kicad_mod.setTags(args['tags'])

    # set general values
    text_x = 0.
    text_y = max([args['pad_y'] / 2., args['part_y'] / 2.]) + args['courtyard'] + 0.75

    kicad_mod.append(Property(name=Property.REFERENCE, text='REF**', at=[text_x, -text_y], layer='F.SilkS'))
    kicad_mod.append(Text(text='${REFERENCE}', at=[text_x, -text_y], layer='F.Fab'))
    kicad_mod.append(Property(name=Property.VALUE, text=args['name'], at=[text_x, text_y], layer='F.Fab'))

    # create silkscreen
    silk_x = args['part_x'] / 2.
    silk_y = max([args['pad_y'] / 2., args['part_y'] / 2.]) + min(max(0.15, args['courtyard'] - 0.05), 0.2)

    kicad_mod.append(Line(start=[silk_x, silk_y], end=[-silk_x, silk_y], layer='F.SilkS'))
    kicad_mod.append(Line(start=[silk_x, -silk_y], end=[-silk_x, -silk_y], layer='F.SilkS'))

    # create fabrication layer
    kicad_mod.append(Rectangle(start=[args['part_x'] / 2., args['part_y'] / 2.],
                              end=[-args['part_x'] / 2., -args['part_y'] / 2.],
                              layer='F.Fab'))

    # create courtyard
    courtyard_x = args['courtyard'] + max([args['pad_spacing'] / 2. + args['pad_x'], args['part_x'] / 2.])
    courtyard_y = args['courtyard'] + max([args['pad_y'] / 2., args['part_y'] / 2.])

    kicad_mod.append(Rectangle(start=[courtyard_x, courtyard_y],
                              end=[-courtyard_x, -courtyard_y],
                              layer='F.CrtYd'))

    # create pads
    pad_settings = {'type': Pad.TYPE_SMT,
                    'shape': Pad.SHAPE_RECT,
                    'size': [args['pad_x'], args['pad_y']],
                    'layers': Pad.LAYERS_SMT}

    pad_x_center = (args['pad_spacing'] + args['pad_x'])  / 2.

    kicad_mod.append(Pad(number=1, at=[-pad_x_center, 0], **pad_settings))
    kicad_mod.append(Pad(number=2, at=[pad_x_center, 0], **pad_settings))

    if "model_suffix" not in args:
        args['model_suffix']=global_config.model_3d_suffix

    # add model
    kicad_mod.append(Model(filename="{model_dir}.3dshapes/{name}{model_suffix}".format(**args),
                           at=[0, 0, 0], scale=[1, 1, 1], rotate=[0, 0, 0]))

    # write file
    write_footprint(kicad_mod, args["model_dir"], generator_name)
    return 1


@register_generator
class SmdChipFootprintGenerator(FootprintGenerator[BaseSpec]):

def create_footprints(spec: BaseSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification (not used by this generator).
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
        global global_config
        global_config = GLOBAL_CONFIG
        parser = ModArgparser(smd_chip)
        parser.add_parameter("name", type=str, required=True)  # the root node of .yml files is parsed as name
        parser.add_parameter("description", type=str, required=True)
        parser.add_parameter("tags", type=str, required=True)
        parser.add_parameter("model_dir", type=str, required=True)
        parser.add_parameter("courtyard", type=float, required=False, default=0.25)
        parser.add_parameter("part_x", type=float, required=True)
        parser.add_parameter("part_y", type=float, required=True)
        parser.add_parameter("pad_x", type=float, required=True)
        parser.add_parameter("pad_y", type=float, required=True)
        parser.add_parameter("pad_spacing", type=float, required=True)

        return parser.run(get_spec_file_names(self.name, CLI_ARGS, globs = ["*.csv"]))
