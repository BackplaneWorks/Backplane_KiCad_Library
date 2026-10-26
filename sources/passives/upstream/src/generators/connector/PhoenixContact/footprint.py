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

from generators.tools.spec.base_spec import BaseSpec
from kilibs.config.global_config import GLOBAL_CONFIG
from generators.tools.cli_args import CLI_ARGS
import copy
import os
import yaml


def create_footprints(spec: BaseSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification (not used by this generator).
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
    CONNECTOR_CONFIG = copy.deepcopy(GLOBAL_CONFIG.raw_data)
    series_config_path = os.path.expandvars(CLI_ARGS.phoenix_contact_config)
    with open(series_config_path, 'r') as config_stream:
        CONNECTOR_CONFIG.update(yaml.safe_load(config_stream))

    num_fps_generated = 0
    import generators.connector.PhoenixContact.mc as mc
    num_fps_generated += mc.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)
    import generators.connector.PhoenixContact.mstb as mstb
    num_fps_generated += mstb.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)
    return num_fps_generated
