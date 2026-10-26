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

from copy import deepcopy
from typing import Union

from kilibs.geom import Vector2D
from kilibs.config.global_config import GLOBAL_CONFIG
from generators.tools.cli_args import CLI_ARGS
from generators.tools.footprint.declarative_def_tools import common_metadata
from generators.tools.spec.base_spec import BaseSpec
from generators.tools.spec.spec_generator import get_file_name_ids_specs
from generators.tools.footprint.footprint_scripts_DIP import makeDIP


class DIPConfiguration:
    """
    Type-safe representation of a DIP footprint configuration
    """
    pins: int
    pitch_x: float
    pitch_y: float
    body_size: Vector2D
    drill: float
    pad_size: Vector2D
    package_type: str
    package_tags: list
    standard: Union[str, None]
    metadata: common_metadata.CommonMetadata
    socket_size_outset: Union[Vector2D, None]

    def __init__(self, spec):
        self.pins = spec['pins']
        self.pitch_x = spec['pitch_x']
        self.pitch_y = spec['pitch_y']
        self.body_size = Vector2D(spec['body_size_x'], spec['body_size_y'])

        # Eventually, the pad size should be a parameter of a 'policy'
        # based on pin sizes
        self.pad_size = Vector2D(spec['pad_size'])
        self.drill = spec['drill']

        self.package_type = spec['package_type']
        self.package_tags = spec['package_tags']
        self.standard = spec.get('standard', None)
        self.metadata = common_metadata.CommonMetadata(spec)

        self.socket_size_outset = self._get_socket_size_outset(spec)

        assert self.pins % 2 == 0
        assert self.drill > 0

    def _get_socket_size_outset(self, spec) -> Union[Vector2D, None]:
        outset = spec.get('socket_size_outset', None)
        return None if outset is None else Vector2D(outset)


def adjust_config_for_longpads(config: DIPConfiguration) -> None:
    """
    Amend a DIP configuration to make the pads longer

    Args:
        base_spec (dict): footprint spec of the "base" footprint
    """
    # "standard" value for larger pads -> 1.6mm to 2.4mm
    # Eventually would be good to make this a parameter of a 'policy'
    # that drives the footprint generation (along with, say, IPA densities)
    # on top of the base spec values
    longpad_size_delta = Vector2D(0.8, 0)

    config.pad_size += longpad_size_delta
    config.metadata.additional_tags.append('LongPads')


def adjust_config_for_socket(config: DIPConfiguration) -> None:
    """
    Amend a DIP configuration to add space for a socket

    Args:
        base_spec (dict): footprint spec of the "base" footprint
        socket_size_outset (Vector2D): how much bigger the socket is than the base footprint
    """
    # Again, would be good to make this a parameter of a 'policy'
    socket_size_outset = Vector2D(2.54, 2.54)

    config.socket_size_outset = socket_size_outset
    config.metadata.additional_tags.append('Socket')


def make_from_config(generator_name: str, config: DIPConfiguration):
    """
    Construct a footprint from a DIPConfiguration object
    """

    # Munge the geometry into what makeDIP wants

    pin_row_length = (config.pins / 2 - 1) * config.pitch_y
    overlen_total = config.body_size.y - pin_row_length

    if config.socket_size_outset is None:
        socket_width = 0
        socket_height = 0
    else:
        socket_width = config.pitch_x + config.socket_size_outset.x
        socket_height = (config.pins / 2 - 1) * config.pitch_y + config.socket_size_outset.y

    args = {
        'pins': config.pins,
        'rm': config.pitch_y,
        'pinrow_distance_in': config.pitch_x,  # not actuall in inches!
        'package_width': config.body_size.x,
        'overlen_top': overlen_total / 2,
        'overlen_bottom': overlen_total / 2,
        'ddrill': config.drill,
        'pad': config.pad_size,
        'smd_pads': False,
        'socket_width': socket_width,
        'socket_height': socket_height,
        'socket_pinrow_distance_offset': 0,
        'datasheet': config.metadata.datasheet,
        'tags_additional': config.metadata.additional_tags,
        'DIPName': config.package_type,
        'DIPTags': ' '.join(config.package_tags),
        'global_config': GLOBAL_CONFIG,
    }

    desc = [config.metadata.description]

    if config.standard:
        desc.append(config.standard)

    args['DIPDescription'] = ', '.join(desc)

    makeDIP(generator_name,**args, outdir=CLI_ARGS.output_dir_footprints)

def make_all_variants_from_device_params(generator_name: str, device_params: dict):

    dip_config = DIPConfiguration(device_params)

    def longpad_mutator(config: DIPConfiguration):
        adjust_config_for_longpads(config)

    def socket_mutator(config: DIPConfiguration):
        adjust_config_for_socket(config)

    # lists of config-mutators to apply in order
    variants = [
        [],
        [longpad_mutator],
        [socket_mutator],
        [longpad_mutator, socket_mutator],
    ]

    for variant in variants:
        # Create a fresh copy of the base config for each variant
        variant_config = deepcopy(dip_config)

        # Then mutate it according to the variant
        for mutator in variant:
            mutator(variant_config)

        make_from_config(generator_name, variant_config)
    return len(variants)


def create_footprints(spec: BaseSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification (not used by this generator).
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
    num_fps_generated = 0
    for _, ids_specs in get_file_name_ids_specs(generator_name):
        for _, spec_dict in ids_specs:
            num_fps_generated += make_all_variants_from_device_params(generator_name, spec_dict)
    return num_fps_generated
