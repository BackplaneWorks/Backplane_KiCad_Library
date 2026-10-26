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

from .base_spec import BaseSpec, TypeSpec

_spec_register: dict[str, type[BaseSpec]] = {}
"""The mapping containing all registered spec classes mapped to the generator name."""


def register_spec(cls: type[TypeSpec]) -> type[TypeSpec]:
    """Class decorator to register a class in the generator_register."""
    name = _get_generator_name_from_class(cls)
    _spec_register[name] = cls
    return cls


def get_spec_class(generator_name: str) -> type[BaseSpec] | None:
    """Get the spec class of the generator with the given name.

    Args:
        generator_name: The name of the generator.

    Returns:
        The registered spec class, or `None` if there is no spec registered for that
        generator.
    """
    if generator_name in _spec_register:
        return _spec_register[generator_name]
    else:
        return None


def _get_generator_name_from_class(cls: type[BaseSpec]) -> str:
    """Return the generator name from the class.

    Args:
        cls: The class.

    Returns: The generator name extracted from the module name of the class.
    """
    # Get the generator's name:
    name = cls.__module__  # Results in something like: "generators.pkgs.gw.spec"
    name = name.rsplit(".", 1)[0]  # Results in something like: "generators.pkgs.gw"
    name = name.split(".", 1)[-1]  # Results in something like: "pkgs.gw"
    name = name.replace(".", "/")  # Results in something like: "pkgs/gw"
    return name
