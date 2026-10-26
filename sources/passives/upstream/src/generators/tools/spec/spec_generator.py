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

from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Any, TypeAlias, cast

import yaml

from generators.tools.cli_args import CLI_ARGS
from kilibs.util import dict_tools, list_filter, list_filter_idx

from .base_spec import BaseSpec, TypeSpec

_DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent.parent / "data"
"""The path of the data folder."""

D: TypeAlias = dict[str, Any]
DD: TypeAlias = dict[str, dict[str, Any]]
DDD: TypeAlias = dict[str, dict[Any, dict[str, Any]]]


def get_spec_file_names(
    generator_name: str, globs: list[str] = ["*.yaml"], data_path: Path | None = None
) -> list[str]:
    """Get the list of the names of the YAML files containing the specs for a given
    generator.

    Args:
        globs: The list of the globs the file names need to match with.
        generator_name: The generator name.
        data_path: The path to the "data" folder. If `None`, the path is automatically
            inferred relative to the location of this script.

    Returns:
        The list of the file names.
    """
    if data_path is None:
        data_path = _DATA_PATH
    generator_path = data_path / generator_name
    # Workaround for legacy generators: We ignore "cq_parameters.yaml". Those files are
    # only used by `create_specs()` in `legacy_model_spec.py`:
    cq_file = generator_path / "cq_parameters.yaml"
    file_names = [
        str(f) for glob in globs for f in generator_path.glob(glob) if f != cq_file
    ]
    try:
        if CLI_ARGS.category or CLI_ARGS.category_exclude:
            return list_filter(file_names, CLI_ARGS.category, CLI_ARGS.category_exclude)
    except AttributeError:
        # When CLI_ARGS.category or CLI_ARGS.categorcy_exclude are not defined we don't
        # filter the list:
        pass
    return file_names


def get_spec_dicts(
    generator_name: str | None = None,
    file_name: str | None = None,
    data_path: Path | None = None,
) -> list[tuple[str, DD]]:
    """Get the list of the contents of the YAML files for a given generator.

    Args:
        generator_name: The generator name. If `None`, `file_name` must be provided.
        file_name: Optional name of the file to load the specs from. If `None`, then
            `generator_name` must be provided. In that case all specs of that generator
            are loaded. If `file_name` is a relative path, then `generator_name` must
            be provided.
        data_path: The path to the "data" folder. If `None`, the path is automatically
            inferred relative to the location of this script.

    Returns:
        A list of tuples, where each tuple represents one YAML file
            * YAML file name: str
            * YAML file content: dict[str, dict[str, Any]]).
    """
    specs_raw: list[tuple[str, dict[str, Any]]] = []
    if file_name is None:
        if generator_name is not None:
            file_names = get_spec_file_names(generator_name, data_path=data_path)
        else:
            raise ValueError("Either `file_name` or `generator_name` must be provided.")
    else:
        if generator_name is None or os.path.isabs(file_name):
            file_names = [file_name]
        else:
            if data_path is None:
                data_path = _DATA_PATH
            file_names = [str(data_path / generator_name / file_name)]
    for file_name in file_names:
        try:
            with open(file_name, "r", encoding="utf-8") as stream:
                if yaml.__with_libyaml__:
                    loader = yaml.CSafeLoader
                else:
                    loader = yaml.SafeLoader  # type: ignore
                yaml_dict: DD = yaml.load(stream, Loader=loader)
                series_dict: DD = {}
                del_keys: list[str] = []
                for id, spec in yaml_dict.items():
                    if id.startswith("series"):
                        del_keys.append(id)
                        series_dict.update(get_spec_dict_for_series(spec, file_name))
                for del_key in del_keys:
                    del yaml_dict[del_key]
                yaml_dict.update(series_dict)
                dict_tools.dict_inherit(yaml_dict)
                if "default_parameters" in yaml_dict.keys():
                    default_parameters: D = yaml_dict.pop("default_parameters")
                    for id, spec in yaml_dict.items():
                        dict_tools.dict_merge(default_parameters, spec)
                        yaml_dict[id] = spec
                yaml_dict = {
                    k: v for k, v in yaml_dict.items() if not k.startswith("defaults")
                }
                try:
                    if CLI_ARGS.quality_assurance_set is True:
                        qa_yaml_dict = {}
                        for id, spec in yaml_dict.items():
                            if include_in_qa := spec.get("include_in_qa"):
                                if isinstance(include_in_qa, dict):
                                    spec.update(cast(dict[Any, Any], include_in_qa))
                                qa_yaml_dict[id] = spec
                        yaml_dict = qa_yaml_dict
                except AttributeError:
                    # In case CLI_ARGS.quality_assurance_set is not defined we treat it
                    # as if it as set to False (nothing to do).
                    pass
                specs_raw.append((file_name, yaml_dict))
        except FileNotFoundError:
            specs_raw.append((file_name, {}))
    return specs_raw


def get_file_name_ids_specs(
    generator_name: str | None = None,
    file_name: str | None = None,
    data_path: Path | None = None,
) -> list[tuple[str, list[tuple[str, DD]]]]:
    """Extract the file names, IDs, and specs of all the spec files.

    Args:
        generator_name: The generator name. If `None`, `file_name` must be provided.
        file_name: Optional name of the file to load the specs from. If `None`, then
            `generator_name` must be provided. In that case all specs of that generator
            are loaded.
        data_path: The path to the "data" folder. If `None`, the path is automatically
            inferred relative to the location of this script.

    Returns:
        A list of tuples where each tuple represents one YAML file with:
            * YAML file name: str
            * List of entries with:
                * ID: str
                * entry: dict[str, dict[str, Any]]
    """
    ret: list[tuple[str, list[tuple[str, DD]]]] = []
    for file_name, raw_specs in get_spec_dicts(generator_name, file_name, data_path):
        ids_specs: list[tuple[str, DD]] = []
        for id, spec in raw_specs.items():
            ids_specs.append((id, spec))
        try:
            ids_specs = list_filter_idx(
                ids_specs, 0, CLI_ARGS.part, CLI_ARGS.part_exclude
            )
        except AttributeError:
            # In case CLI_ARGS.part or CLI_ARGS.part_exclude are not defined we don't
            # filter the list of ids and specs.
            pass
        ret.append((file_name, ids_specs))
    return ret


def get_specs(
    generator_name: str | None = None,
    file_name: str | None = None,
    spec_type: type[TypeSpec] = BaseSpec,
) -> list[TypeSpec]:
    """Get the list of the specs for a given generator (from its YAML files).

    Args:
        generator_name: The generator name. If `None`, `file_name` must be provided.
        file_name: Optional name of the file to load the specs from. If `None`, then
            `generator_name` must be provided. In that case all specs of that generator
            are loaded.
        spec_type: The class of the specs that shall be created.

    Returns:
        The unified list of the specs derived from all the generator's YAML files.
    """
    specs: list[TypeSpec] = []
    make_fps = True if CLI_ARGS.output_dir_footprints else False
    make_mods = True if CLI_ARGS.output_dir_models else False
    for file_name, ids_specs in get_file_name_ids_specs(generator_name, file_name):
        for id, spec in ids_specs:
            spec = spec_type(id, spec, file_name)
            if make_fps and spec.has_fp_data or make_mods and spec.has_3d_data:
                specs.append(spec)
    return specs


def create_specs(file_name: str, generator_name: str) -> list[BaseSpec]:
    """Default implementation for `create_specs`.

    Args:
        file_name: The name of the specs file to create the specs from.
        generator_name: The name of the generator to create the specs for.

    Return:
        The created specs.
    """
    from .spec_registry import get_spec_class

    spec_class = get_spec_class(generator_name)

    if spec_class is None:
        raise ModuleNotFoundError(
            f"No class in {generator_name}/spec.py was decorated with `@register_spec`."
        )
    return get_specs(None, file_name, spec_class)


def get_spec_dict_for_series(series_data: D, file_name: str) -> DD:
    """Get spec dictionary from a series definition.

    Args:
        series_data: The data of the series.
        file_name: The name of the YAML file that holds the series.

    Return:
        A list of tuples containing a generated ID and the specs dictionary.
    """

    default_parameters: D = series_data.get("default_parameters", {})
    explicit_definitions: DD = series_data.get("explicit_definitions", {})
    inferred_parameters: DDD = series_data.get("inferred_parameters", {})
    csv_file_names: list[str] | str = series_data.get("csv", [])
    if isinstance(csv_file_names, str):
        csv_file_names = [csv_file_names]
    csv_folder = Path(file_name).parent
    series_dict: DD = {}

    def get_series_part_definition(
        file_name: str,
        row_dict: D,
        default_parameters: D,
        inferred_parameters: DDD,
    ) -> DD:
        part_dict = default_parameters.copy()
        part_dict.update(row_dict)
        for inferred_name, inferred_values in inferred_parameters.items():
            part_value = part_dict[inferred_name]
            for inferred_value, infered_params in inferred_values.items():
                if part_value == inferred_value:
                    part_dict.update(infered_params)
                    break
        part_name = file_name[:-4] + "_" + "_".join(str(v) for v in row_dict.values())
        return {part_name: part_dict}

    def get_part_with_parameter(param_name: str, param_value: Any) -> DD:
        for part_dict in series_dict.values():
            if part_dict.get(param_name) == param_value:
                return part_dict
        raise KeyError(f"No part definition was found with {param_name}={param_value}.")

    def convert_dict_strings_to_int_or_float(dictionary: dict[str, str]) -> None:
        for key, value in line_as_dict.items():
            # Check if the value is non-empty before attempting conversion
            if value is None or value.strip() == "":
                continue
            try:
                if value.strip().isdigit():
                    line_as_dict[key] = int(value)
                    continue
            except ValueError:
                pass
            try:
                line_as_dict[key] = float(value)
            except ValueError:
                continue

    for csv_file_name in csv_file_names:
        with open(csv_folder / csv_file_name, encoding="utf-8-sig") as f:
            reader = csv.DictReader(filter(lambda row: not row.startswith("#"), f))
            for line_as_dict in reader:
                convert_dict_strings_to_int_or_float(line_as_dict)
                series_dict.update(
                    get_series_part_definition(
                        csv_file_name,
                        line_as_dict,
                        default_parameters,
                        inferred_parameters,
                    )
                )

    series_dict_of_inheriting_parts: DD = {}
    for key, part_dict in explicit_definitions.items():
        for param_key, value in part_dict.items():
            if param_key.startswith("inherit_"):
                inherit_param_name = param_key[len("inherit_") :]
                inherit_def = get_part_with_parameter(inherit_param_name, value)
                del part_dict[param_key]
                dict_tools.dict_merge(inherit_def, part_dict)
                series_dict_of_inheriting_parts[key] = part_dict
                break
    series_dict.update(series_dict_of_inheriting_parts)
    return series_dict
