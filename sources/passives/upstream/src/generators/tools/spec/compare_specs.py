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


from dataclasses import dataclass
from pathlib import Path

from generators.tools.spec.spec_generator import DD, get_spec_dicts


@dataclass
class SpecIdsDiff:
    """A dataclass containing the result of a spec diff."""

    new_ids: list[str]
    """The list of IDs of the specs that are new."""
    deleted_ids: list[str]
    """The list of IDs of the specs that are deleted."""
    modified_ids: list[str]
    """The list of IDs of the specs that are modified."""
    identical_ids: list[str]
    """The list of IDs of the specs that are identical."""


def compare_specs(
    file_names_specs_new: list[tuple[str, DD]],
    file_names_specs_old: list[tuple[str, DD]],
) -> SpecIdsDiff:
    """Compare two lists of ID-spec pairs.

    Args:
        file_names_specs_new: The new list of file names and specs.
        file_names_specs_old: The old list of file names and specs.

    Returns:
        A `SpecIdsDiff` that contains the IDs of the new, deleted, modified and
        identical specs.
    """
    specs_new = {k: v for _, d in file_names_specs_new for k, v in d.items()}
    specs_old = {k: v for _, d in file_names_specs_old for k, v in d.items()}

    new_ids: list[str] = []
    deleted_ids: list[str] = []
    modified_ids: list[str] = []
    identical_ids: list[str] = []
    for id_new, spec_new in specs_new.items():
        try:
            spec_old = specs_old[id_new]
            if spec_new == spec_old:
                identical_ids.append(id_new)
            else:
                modified_ids.append(id_new)
            del specs_old[id_new]
        except KeyError:
            new_ids.append(id_new)
    deleted_ids = [id for id in specs_old.keys()]
    return SpecIdsDiff(new_ids, deleted_ids, modified_ids, identical_ids)


def compare_specs_of_generator(
    generator_name: str, folder_new: Path, folder_old: Path
) -> SpecIdsDiff:
    """Compare the specs of two files.

    Args:
        generator_name: The name of the generator.
        folder_new: The root folder containing the specs of the new generator.
        folder_old: The root folder containing the specs of the old generator.

    Returns:
        A `SpecIdsDiff` that contains the IDs of the new, deleted, modified and
        identical specs.
    """
    file_names_specs_old = get_spec_dicts(
        generator_name=generator_name, data_path=folder_old
    )
    file_names_specs_new = get_spec_dicts(
        generator_name=generator_name, data_path=folder_new
    )
    # Add manually the "cq_parameter.yaml" as it is otherwise ignored (for backward
    # compatibility with legacy 3D generators):
    file_names_specs_old += get_spec_dicts(
        generator_name=generator_name, file_name="cq_parameters.yaml", data_path=folder_old
    )
    file_names_specs_new += get_spec_dicts(
        generator_name=generator_name, file_name="cq_parameters.yaml", data_path=folder_new
    )
    return compare_specs(file_names_specs_new, file_names_specs_old)
