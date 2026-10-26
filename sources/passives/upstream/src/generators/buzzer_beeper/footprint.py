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
from generators.tools.footprint.save_footprint import write_footprint
from KicadModTree.nodes.base.Pad import Pad
from generators.tools.spec.base_spec import BaseSpec
from generators.tools.spec.spec_generator import get_spec_file_names
from kilibs.config.global_config import GLOBAL_CONFIG


def create_footprints(spec: BaseSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification (not used by this generator).
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
    parser = ModArgparser(buzzer_round_tht)
    parser.add_parameter("name", type=str, required=True)  # the root node of .yml files is parsed as name
    parser.add_parameter("datasheet", type=str, required=False)
    parser.add_parameter("courtyard", type=float, required=False, default=0.25)
    parser.add_parameter("diameter", type=float, required=True)
    parser.add_parameter("hole_size", type=float, required=True)
    parser.add_parameter("pad_size", type=float, required=True)
    parser.add_parameter("pad_spacing", type=float, required=True)

    return parser.run(generator_name, get_spec_file_names(generator_name, globs=["*.csv"]))

def buzzer_round_tht(generator_name: str, args):
    lib_name = "Buzzer_Beeper"

    # some variables
    buzzer_center = args['pad_spacing'] / 2.
    buzzer_radius = args['diameter'] / 2.

    # init kicad footprint
    kicad_mod = Footprint(args['name'], FootprintType.THT)
    kicad_mod.setDescription(args['datasheet'])
    kicad_mod.setTags("buzzer round tht")

    # set general values
    kicad_mod.append(Property(name=Property.REFERENCE, text='REF**', at=[buzzer_center, -buzzer_radius - 1], layer='F.SilkS'))
    kicad_mod.append(Text(text='${REFERENCE}', at=[buzzer_center, -buzzer_radius - 1], layer='F.Fab'))
    kicad_mod.append(Property(name=Property.VALUE, text=args['name'], at=[buzzer_center, buzzer_radius + 1], layer='F.Fab'))

    # create silkscreen
    kicad_mod.append(Circle(center=[buzzer_center, 0], radius=buzzer_radius + 0.1, layer='F.SilkS'))

    kicad_mod.append(Text(text='+', at=[0, -args['pad_size'] / 2 - 1], layer='F.SilkS'))
    kicad_mod.append(Text(text='+', at=[0, -args['pad_size']/2 - 1], layer='F.Fab'))

    # create fabrication layer
    kicad_mod.append(Circle(center=[buzzer_center, 0], radius=buzzer_radius, layer='F.Fab'))

    # create courtyard
    kicad_mod.append(Circle(center=[buzzer_center, 0], radius=buzzer_radius + args['courtyard'], layer='F.CrtYd'))

    # create pads
    kicad_mod.append(Pad(number=1, type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT,
                        at=[0, 0], size=args['pad_size'], drill=args['hole_size'], layers=Pad.LAYERS_THT))
    kicad_mod.append(Pad(number=2, type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE,
                        at=[args['pad_spacing'], 0], size=args['pad_size'], drill=args['hole_size'], layers=Pad.LAYERS_THT))

    # add model
    kicad_mod.append(Model(
        filename="{prefix}{lib_name}.3dshapes/{fp_name}{suffix}".format(prefix = GLOBAL_CONFIG.model_3d_prefix, suffix=GLOBAL_CONFIG.model_3d_suffix, lib_name=lib_name, fp_name=args["name"]),
        at=[0, 0, 0], scale=[1, 1, 1], rotate=[0, 0, 0]))

    # write file
    write_footprint(kicad_mod, lib_name, generator_name)
    return 1

