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

from typing import Any

from kilibs.config.global_config import GLOBAL_CONFIG


def _load_connector_config() -> dict[str, Any]:
    """Create an instance of a connector footprint generator.

    Args:
        args: The global CLI arguments in form of a namespace.
    """
    import yaml
    import os
    from copy import deepcopy
    from generators.tools.cli_args import CLI_ARGS

    configuration = deepcopy(GLOBAL_CONFIG.raw_data)
    series_config_path = os.path.expandvars(CLI_ARGS.connector_config)
    with open(series_config_path, 'r') as config_stream:
        configuration.update(yaml.safe_load(config_stream))
    return configuration


CONNECTOR_CONFIG = _load_connector_config()
