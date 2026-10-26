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

from typing import Any, TypeVar

TypeSpec = TypeVar("TypeSpec", bound="BaseSpec")
"""A TypeVar bound to the a `BaseSpec`."""


class BaseSpec:
    """
    Base class for all generator specifications.

    All specific generator configuration classes (Specs) must inherit from this
    base class to ensure compatibility with the unified generator runner.
    """

    def __init__(
        self,
        id: str = "",
        spec: dict[str, Any] = {},
        file_name: str = "",
    ) -> None:
        """Create an instance of `BaseSpec`.

        Args:
            id: The name/identifier of the spec. Typically, this is the name of the key
                of the spec (in the YAML file) or the name of the component.
            spec: The dictionary containing the specification of the component.
            file_name: The name of the YAML file that holds this spec definition.
        """

        # Instance attributes:
        self.has_fp_data: bool
        """True if this spec contains all the data needed to create a footprint."""
        self.has_3d_data: bool
        """True if this spec contains all the data needed to create a 3D model."""
        self.id: str
        """The identifier (name) of the spec. Typically this is equal to the name of the
        key holding the spec if the spec comes from a YAML file."""

        self.has_fp_data = True
        self.has_3d_data = True
        self.id = id
