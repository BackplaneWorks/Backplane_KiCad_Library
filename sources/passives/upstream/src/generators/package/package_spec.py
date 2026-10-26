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

from generators.tools.spec.base_spec import BaseSpec
from generators.tools.footprint.declarative_def_tools import common_metadata

class PackageSpec(BaseSpec):
    """
    A type that represents the spec of a package.
    """

    def __init__(
        self,
        id: str = "",
        spec: dict[str, Any] = {},
        file_name: str = "",
    ) -> None:
        """Create an instance of `PackageSpec`.

        Args:
            id: The name/identifier of the spec. Typically, this is the name of the key
                of the spec (in the YAML file) or the name of the component.
            spec: The dictionary containing the specification of the component.
            file_name: The name of the YAML file that holds this spec definition.
        """
        # Instance attributes:
        self.spec: dict[str, Any]
        """The dictionary containing the specification of the device."""
        self.metadata: common_metadata.CommonMetadata
        """The common meta data."""

        super().__init__(id, spec, file_name)

        self.spec = copy.deepcopy(spec)
        self.metadata = common_metadata.CommonMetadata(self.spec)
        self.has_fp_data = False
        self.has_3d_data = False
