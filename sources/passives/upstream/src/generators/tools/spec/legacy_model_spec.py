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

import copy
from typing import Any

from .base_spec import BaseSpec
from .spec_generator import get_file_name_ids_specs


class LegacyModelSpec(BaseSpec):
    """
    A type that represents the spec for legacy model generators.
    """

    def __init__(
        self,
        id: str = "",
        spec: dict[str, Any] = {},
        file_name: str = "",
    ) -> None:
        """Create an instance of `LegacyModelSpec`.

        Args:
            id: The name/identifier of the spec. This is the name of the key of the spec
                (in the YAML file).
            spec: The dictionary containing the specification of the component.
            file_name: The name of the YAML file that holds this spec definition.
        """
        # Instance attributes:
        self.spec: dict[str, Any]
        """The dictionary containing the specification of the device."""

        super().__init__(id, spec, file_name)

        self.spec = copy.deepcopy(spec)
        self.has_fp_data = False
        self.has_3d_data = True


def create_specs(generator_name: str) -> list[LegacyModelSpec]:
    """Default implementation for `create_specs`.

    Args:
        generator_name: The name of the generator to create the specs for.

    Return:
        The created specs.
    """
    CQ_FILE = "cq_parameters.yaml"
    specs: list[LegacyModelSpec] = []
    file_name, ids_specs = get_file_name_ids_specs(generator_name, CQ_FILE)[0]
    for id, spec in ids_specs:
        specs.append(LegacyModelSpec(id, spec, file_name))
    return specs
