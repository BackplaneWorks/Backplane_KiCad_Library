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

import yaml
import os

from generators.tools.cli_args import CLI_ARGS

def _load_package_config() -> dict[str, Any]:
    """Load the package config."""
    path = os.path.expandvars(CLI_ARGS.package_config)
    with open(path, "r") as config_stream:
        if yaml.__with_libyaml__:
            loader = yaml.CSafeLoader
        else:
            loader = yaml.SafeLoader  # type: ignore
        return yaml.load(config_stream, Loader=loader)

PACKAGE_CONFIG: dict[str, Any] = _load_package_config()
"""The package config."""
