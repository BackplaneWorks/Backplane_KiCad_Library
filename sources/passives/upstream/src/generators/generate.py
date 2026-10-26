#!/usr/bin/env python3

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

import time

_START_TIME = time.perf_counter()
"""The time at which the script was started. Used to calculate wall time (including the
time of all imports).
"""

import logging
import os
import sys
import traceback
from argparse import ArgumentParser, Namespace
from collections.abc import Generator
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from generators.tools.definitions import (
    GEN_IDX_FP,
    GEN_IDX_MOD,
    GEN_IDX_SPEC,
    GEN_NUM_TYPES,
    MODULE_NAME_ARGS,
    MODULE_NAMES,
)

if TYPE_CHECKING:
    # Imports in this block are executed only by type checkers (e.g., mypy) and IDEs.
    # This avoids loading expensive or unnecessary modules at runtime, thus reducing
    # startup time for fast operations (like '--help' or '--list').
    from concurrent.futures import Future, ProcessPoolExecutor

    from generators.tools.spec.base_spec import BaseSpec


FILE_NAMES_SORTED_GEN_LIST = ["", ".sorted_fp_gen_list", ".sorted_mod_gen_list"]
"""The file names of the lists of the generators sorted by their execution priority (to
minimize wall time)."""


GENERATORS_PATH = Path(__file__).parent
"""The path of the generators folder."""


@dataclass(frozen=True)
class _GeneratorImplementation:
    """A class to hold the information of which generator type is implemented for a
    given generator."""

    name: str
    """Name of the generator."""
    implemented_gens: list[bool]
    """Whether the generator has implemented a spec, footprint or model generator. The
    list is indexed according to the `GEN_IDX` constants."""

    def __eq__(self, other: Any) -> bool:
        """Implementation of the '==' operator. Needed by `set()` to remove duplicates."""
        if isinstance(other, _GeneratorImplementation):
            return self.name == other.name
        return False

    def __hash__(self) -> int:
        """Implementation of the hash method for this class. Needed by `set()` to remove
        duplicates.
        """
        return hash(self.name)


@dataclass(frozen=True)
class _GeneratorStats(_GeneratorImplementation):
    """
    A helper structure to aggregate implementation details, statistics, and outputs
    for a single generator across all stages.
    """

    total_runtime: list[float] = field(default_factory=lambda: [0.0] * GEN_NUM_TYPES)
    """The total CPU processing time recorded for each generator type. The list is
    indexed corresponding to the `GEN_IDX` constants.
    """
    max_work_package_runtime: list[float] = field(
        default_factory=lambda: [0.0] * GEN_NUM_TYPES
    )
    """The maximum time spent on a single work package for each generator type. The list
    is indexed corresponding to the `GEN_IDX` constants. This information is used to
    create a list of all generator names sorted by their maximum work package time to
    minimize wall time.
    """
    success: list[bool] = field(default_factory=lambda: [True] * GEN_NUM_TYPES)
    """The success of each generator type. If during execution of the worker processes a
    worker raised an exception, this flag is set to `False`. The list is indexed
    corresponding to the `GEN_IDX` constants.
    """
    outputs: list[list[BaseSpec] | int] = field(default_factory=lambda: [[], 0, 0])
    """Stores the aggregated return values from all workers for each generator type.
    While a worker of the spec generator returns a list of specs, a worker of the
    footprint and model generators return the number of generated parts for each work
    package."""


def run(default_args: list[str] = []) -> None:
    """Main entry point of the prgram.

    Process the parameters that were passed to this script from the CLI, execute the
    runner and exit the program.

    Args:
        default_args: An optional list of default arguments that are merged with the
            arguments of the CLI in such a way that the arguments of the CLI take
            precedence over the `default_args`.
    """
    implemented_generators, args_files = _scan_for_generators()
    argparser = _create_arg_parser(args_files)
    args = argparser.parse_args(sys.argv[1:] + default_args)

    if args.export_vrml:
        logging.warning("VRML export is deprecated and may be removed in the future.")

    if len(sys.argv) == 1:
        # Print the usage and exit:
        argparser.print_usage()
        sys.exit(0)
    elif args.help or not (
        args.output_dir_footprints or args.output_dir_models or args.list
    ):
        # Print the help and exit:
        argparser.print_help()
        sys.exit(0)
    elif args.list:
        # Display all generator names and exit:
        import tabulate

        implemented_generators = _filter_generators(
            generator_implementations=implemented_generators,
            include_fp_gens=args.output_dir_footprints is not None,
            include_mod_gens=args.output_dir_models is not None,
            include_globs=[],
            exclude_globs=[],
        )
        implemented_generators.sort(key=lambda ig: ig.name.lower())

        headers = ["Generator", "Spec", "FP", "3D"]
        rows: list[tuple[str, str, str, str]] = []
        for ig in implemented_generators:
            has_spec = "Yes" if ig.implemented_gens[GEN_IDX_SPEC] else "No"
            has_fp = "Yes" if ig.implemented_gens[GEN_IDX_FP] else "No"
            has_mod = "Yes" if ig.implemented_gens[GEN_IDX_MOD] else "No"
            rows.append((ig.name, has_spec, has_fp, has_mod))
        rows.sort(key=lambda x: x[0].lower())  # sort by name
        print("")
        print(tabulate.tabulate(rows, headers=headers, floatfmt=".2f"))
        print("")
        sys.exit(0)
    else:
        # Make paths absolute to prevent surprises from happening when using relative
        # paths:
        if args.output_dir_footprints:
            args.output_dir_footprints = args.output_dir_footprints.resolve()
        if args.output_dir_models:
            args.output_dir_models = args.output_dir_models.resolve()
        os.environ.update({"GENERATORS": GENERATORS_PATH.as_posix()})

        # Run the selected generators:
        implemented_generators = _filter_generators(
            generator_implementations=implemented_generators,
            include_fp_gens=args.output_dir_footprints is not None,
            include_mod_gens=args.output_dir_models is not None,
            include_globs=args.generator,
            exclude_globs=args.generator_exclude,
        )

        if not implemented_generators:
            print("No generators selected after filtering. Exiting.")
            sys.exit(2)

        success = _run_generators(implemented_generators, args)

        if success:
            print("Generation successful!")
            sys.exit(0)
        else:
            print("Generation failed!")
            sys.exit(2)


def _create_arg_parser(args_files: list[str]) -> ArgumentParser:
    """Create the argument parser by collecting the arguments from all the generators
    have an `args.py` file.

    Args:
        args_files: The list of the paths of the `args.py` files to load the arguments
            from.

    Returns:
        The argument parser of all the modules that implement
        `add_argparse_arguments()` in their `args.py` file.
    """
    import importlib

    EPILOG = (
        "example: python generate.py -f ../../../FOOTPRINTS_FOLDER "
        "-m ../../../3DMODELS_FOLDER -g package/gullwing -p SOT-23"
    )
    argparser = ArgumentParser(
        description="Generate KiCad footprints and models.",
        add_help=False,
        epilog=EPILOG,
    )
    # Root-level args.py
    import generators.args as root_args

    root_args.add_argparse_arguments(argparser)

    # Generator-level args.py
    parser_gen_group = argparser.add_argument_group("Generator-specific arguments")
    for args_file in args_files:
        module_path = "generators." + args_file.replace("/", ".")
        mod = importlib.import_module(module_path)
        if args_file != MODULE_NAME_ARGS:  # Skip root-level args.py
            mod.add_argparse_arguments(parser_gen_group)
    return argparser


def _scan_for_generators() -> tuple[list[_GeneratorImplementation], list[str]]:
    """Recursively scans subdirectories for generator modules and CLI argument files.

    Returns:
        A tuple containing:
        1. A list with the information of the implemented generators.
        2. A list of the `args.py` files found in the subdirectories.
    """
    # This implementation is a bit cumbersome, but significantly faster than an
    # implementation using Path.rglob():
    GEN_FILE_NAMES: list[str] = [name + ".py" for name in MODULE_NAMES]
    ARGS_FILE_NAME = MODULE_NAME_ARGS + ".py"
    args_files: list[str] = []
    generators_data: dict[str, list[bool]] = {}
    root_folder = os.path.abspath(GENERATORS_PATH)
    len_stem = len(root_folder) + 1
    folders_to_scan = [root_folder]
    while folders_to_scan:
        current_dir = folders_to_scan.pop()
        try:
            with os.scandir(current_dir) as entries:
                for entry in entries:
                    if entry.is_dir(follow_symlinks=False):
                        folders_to_scan.append(entry.path)
                    elif entry.is_file():
                        if entry.name == ARGS_FILE_NAME:
                            folder = Path(os.path.dirname(entry.path)[len_stem:])
                            file = (folder / MODULE_NAME_ARGS).as_posix()
                            args_files.append(file)
                        elif entry.name in GEN_FILE_NAMES:
                            generator_name = Path(
                                os.path.dirname(entry.path)[len_stem:]
                            ).as_posix()
                            if generator_name not in generators_data:
                                generators_data[generator_name] = [False, False, False]
                            idx = GEN_FILE_NAMES.index(entry.name)
                            generators_data[generator_name][idx] = True
        except PermissionError:
            continue
        except FileNotFoundError:
            continue
    igs = [
        _GeneratorImplementation(key, value) for key, value in generators_data.items()
    ]
    igs = sorted(igs, key=lambda i: i.name.lower())
    return igs, args_files


def _filter_generators(
    generator_implementations: list[_GeneratorImplementation],
    include_fp_gens: bool,
    include_mod_gens: bool,
    include_globs: list[str],
    exclude_globs: list[str],
) -> list[_GeneratorImplementation]:
    """Return a list that contains only the requested generator type (footprint or model
    generator).

    Args:
        generator_implementations: The list of generator implementation.
        args: The CLI arguments.
    """
    if not include_fp_gens and not include_mod_gens:
        return generator_implementations

    from kilibs.util import list_filter_attr

    generator_implementations = [
        g
        for g in generator_implementations
        if (include_fp_gens and g.implemented_gens[GEN_IDX_FP])
        or (include_mod_gens and g.implemented_gens[GEN_IDX_MOD])
    ]
    include_globs = [Path(g).as_posix() for g in include_globs]
    exclude_globs = [Path(g).as_posix() for g in exclude_globs]
    return list_filter_attr(
        generator_implementations, "name", include_globs, exclude_globs
    )


def _create_generator_stats(
    implemented_generators: list[_GeneratorImplementation],
) -> list[_GeneratorStats]:
    """Creates the worker stats.

    Args:
        implemented_generators: The list of implemented generators.

    Returns:
        The worker stat with all required attributes initialized.
    """
    generator_stats_list: list[_GeneratorStats] = []
    for ig in implemented_generators:
        generator_stat = _GeneratorStats(ig.name, ig.implemented_gens)
        generator_stats_list.append(generator_stat)
    return generator_stats_list


def _run_generators(
    implemented_generators: list[_GeneratorImplementation], args: Namespace
) -> bool:
    """Execute the main code of the runner.

    First the specs are collected from the selected generators and then run as jobs
    in individual workers (currently processes, but with Python 3.14+ these should
    be threads with minimal overhead).

    Args:
        implemented_generators: The list of implemented generators.
        args: The namespace containing all the parsed CLI arguments.

    Returns:
        On successs `True` is returned, `False` otherwise.
    """
    from concurrent.futures import ProcessPoolExecutor

    from generators.tools.worker import init_worker

    init_worker(args)  # Set log level and persistent variables of the main process.
    success = True  # Variable to keep track of generator errors.
    generator_stats = _create_generator_stats(implemented_generators)
    cpu_count = os.cpu_count()
    max_jobs = cpu_count if cpu_count is not None else 1
    max_jobs = max_jobs - 1 if max_jobs > 1 else max_jobs
    num_workers = args.jobs if args.jobs else max_jobs
    # For easier debugging (because debugging multiprocessing can be a pain) don't use
    # additional processes when the number of workers is set to 1:
    if num_workers == 1:
        executor = None
    else:
        executor = ProcessPoolExecutor(
            num_workers, initializer=init_worker, initargs=(args,)
        )
    wall_times: list[float] = [0.0, 0.0, 0.0]

    gen_types_to_run = [GEN_IDX_SPEC]
    if args.output_dir_footprints is not None:
        gen_types_to_run.append(GEN_IDX_FP)
    if args.output_dir_models is not None:
        gen_types_to_run.append(GEN_IDX_MOD)

    for i in gen_types_to_run:
        start_time = time.perf_counter()
        sort_generator_stats_for_minimum_wall_time(i, generator_stats, args)
        success &= _run_all_generators_of_same_type(
            i, executor, num_workers, generator_stats, args
        )
        if args.update_sorted_generators_list:
            _save_sorted_generator_list(i, generator_stats, args)
        wall_times[i] = time.perf_counter() - start_time
    if executor is not None:
        executor.shutdown()
    _print_stats(generator_stats, wall_times)

    return success


def _run_all_generators_of_same_type(
    gen_idx: int,
    executor: ProcessPoolExecutor | None,
    num_workers: int,
    generator_stats_list: list[_GeneratorStats],
    args: Namespace,
) -> bool:
    """Run all the generators of a given type.

    Args:
        gen_idx: The generator index (following `GEN_IDX`).
        executor: The proces pool executor (or `None` if single threaded).
        generator_stats_list: the list of generator stats.
        args: The namespace.

    Returns:
        True if no spec generator encountered a problem, False otherwise.
    """
    from concurrent.futures import as_completed

    from generators.tools.worker import run_worker

    success = True
    futures: list[Future[tuple[list[Any] | int, float]]] = []
    future_to_stats: dict[Future[tuple[list[Any] | int, float]], _GeneratorStats] = {}
    # Set up the workers:
    for generator_stats in generator_stats_list:
        if generator_stats.implemented_gens[gen_idx]:
            for wp in _get_work_package_chunks(
                generator_stats, gen_idx, num_workers, args
            ):
                if executor is not None:
                    future = executor.submit(
                        run_worker, generator_stats.name, gen_idx, wp
                    )
                    futures.append(future)
                    future_to_stats[future] = generator_stats
                else:
                    output, runtime = run_worker(generator_stats.name, gen_idx, wp)
                    generator_stats.total_runtime[gen_idx] += runtime
                    generator_stats.max_work_package_runtime[gen_idx] = max(
                        runtime, generator_stats.max_work_package_runtime[gen_idx]
                    )
                    generator_stats.outputs[gen_idx] += cast(Any, output)
    # Extract the success and the runtime of the workers of the footprint jobs:
    if executor is not None:
        for future in as_completed(futures):
            generator_stats = future_to_stats[future]
            try:
                output, runtime = future.result()
                generator_stats.total_runtime[gen_idx] += runtime
                generator_stats.max_work_package_runtime[gen_idx] = max(
                    runtime, generator_stats.max_work_package_runtime[gen_idx]
                )
                generator_stats.outputs[gen_idx] += cast(Any, output)
            # Catch every error except for the keyboard interrupt (re-raise that one):
            except KeyboardInterrupt:
                executor.shutdown(wait=False, cancel_futures=True)
                raise
            except Exception as exc:
                logging.error(
                    f"Generator '{generator_stats.name}' produced an exception: {exc}"
                )
                traceback.print_exc()
                generator_stats.success[gen_idx] = False
                success = False
    return success


def _get_work_package_chunks(
    generator_stats: _GeneratorStats,
    gen_idx: int,
    num_workers: int,
    args: Namespace,
) -> Generator[list[Any], None, None]:
    """Split the list of work packages into several chunks of work packages for more
    efficient loading of the worker processes (reduce inter process communication).
    Also filters out the specs that are not relevant (no fp or 3d data) for the given
    generator.

    Args:
        generator_name: The name of the generator.
        gen_idx: The number of the generator (0=spec, 1=footprint, 2=model).
        num_workers: Number of workers that are available.
        args: CLI arguments.
    """
    import generators.tools.spec.spec_generator as spec_generator
    from generators.tools.spec.base_spec import BaseSpec

    # Prepare the arguments passed to the generators depending on their type:
    # - Spec generators: The list of YAML files.
    # - Downstream generators (footprint/model): Use spec generator outputs as input.
    if gen_idx == GEN_IDX_SPEC:
        wps = spec_generator.get_spec_file_names(generator_stats.name)
    else:
        wps = cast(list[BaseSpec], generator_stats.outputs[GEN_IDX_SPEC])
        if gen_idx == GEN_IDX_FP:
            wps = [wp for wp in wps if wp.has_fp_data]
            # Simple workaround for legacy footprint generators that don't have a spec
            # generator - we create a dummy spec for those:
            if not wps and not args.quality_assurance_set:
                base_spec = BaseSpec()
                base_spec.has_3d_data = False
                base_spec.has_fp_data = True
                yield [base_spec]
                return
        else:  # if gen_idx == GEN_IDX_MOD:
            wps = [wp for wp in wps if wp.has_3d_data]
            # Simple workaround for legacy model generators that don't have a spec
            # generator - we create a list of LegacyModelSpec from "cq_parameters.yaml":
            if not generator_stats.implemented_gens[GEN_IDX_SPEC]:
                from generators.tools.spec import legacy_model_spec

                wps = legacy_model_spec.create_specs(generator_stats.name)
            # 3D model gens are so slow that the IPC overhead is negligible. We
            # therefore return chunks of size 1 to maximize the occupancy of all cores:
            for wp in wps:
                yield [wp]
            return

    # Create smaller chunk sizes. It's a compromise between IPC overhead and maximizing
    # occupancy of all the cores. In average we split the work package into
    # 2 * num_workers chunks:
    len_wps = len(wps)
    chunk_size = max(1, len_wps // (num_workers * 2))
    for chunk_start_idx in range(0, len_wps, chunk_size):
        chunk_end_idx = min(chunk_start_idx + chunk_size, len_wps)
        yield wps[chunk_start_idx:chunk_end_idx]


def _print_stats(
    generator_stats_list: list[_GeneratorStats], wall_times: list[float]
) -> None:
    """Print the runner's statistics.

    Args:
        generaor_stats_list: The list containing all the generator statistics to print.
        wall_times: The wall times for each generator type. List is indexed following
            `GEN_IDX`. This parameter is currently unused.
    """
    import tabulate

    headers = [
        "Generator",
        "Result",
        "Time Spec [s]",
        "Time FP [s]",
        "Time 3D [s]",
        "Footprints [1]",
        "Models [1]",
    ]
    rows: list[tuple[str, str, float, float, float, int | str, int | str] | str] = []
    total_success = 0
    total_generators = 0
    total_fps = 0
    total_mods = 0
    total_time_specs = 0.0
    total_time_fps = 0.0
    total_time_mods = 0.0
    for generator_stats in generator_stats_list:
        # Generator entries that have generated neither footprints nor 3D models are
        # skipped:
        success = all(generator_stats.success)
        if (
            generator_stats.outputs[GEN_IDX_FP] == 0
            and generator_stats.outputs[GEN_IDX_MOD] == 0
            and success
        ):
            continue
        spec_gen_runtime = generator_stats.total_runtime[GEN_IDX_SPEC]
        fp_gen_runtime = generator_stats.total_runtime[GEN_IDX_FP]
        mod_gen_runtime = generator_stats.total_runtime[GEN_IDX_MOD]
        num_fps = cast(int, generator_stats.outputs[GEN_IDX_FP])
        num_mods = cast(int, generator_stats.outputs[GEN_IDX_MOD])
        rows.append(
            (
                generator_stats.name,
                "Success" if success else "Failure",
                spec_gen_runtime,
                fp_gen_runtime,
                mod_gen_runtime,
                num_fps if num_fps else "-",
                num_mods if num_mods else "-",
            )
        )
        total_generators += 1
        if success:
            total_success += 1
        total_fps += num_fps
        total_mods += num_mods
        total_time_specs += spec_gen_runtime
        total_time_fps += fp_gen_runtime
        total_time_mods += mod_gen_runtime
    rows.sort(key=lambda x: x[0].lower())  # sort by name
    rows.append(tabulate.SEPARATING_LINE)
    rows.append(
        (
            "TOTAL",
            f"{total_success}/{total_generators}",
            total_time_specs,
            total_time_fps,
            total_time_mods,
            total_fps if total_fps else "-",
            total_mods if total_mods else "-",
        )
    )
    print("")
    print(tabulate.tabulate(rows, headers=headers, floatfmt=".2f"))

    # Output the wall time in a useful format:
    minutes, seconds = divmod(time.perf_counter() - _START_TIME, 60)
    hours, minutes = divmod(minutes, 60)
    str_hours = f"{int(hours)}h " if hours else ""
    str_minutes = f"{int(minutes)}m " if minutes else ""

    print("")
    print(f"Wall time: {str_hours}{str_minutes}{seconds:.2f}s")
    print("")


def _save_sorted_generator_list(
    gen_idx: int,
    generator_stats_list: list[_GeneratorStats],
    args: Namespace,
) -> None:
    """Save the list of the generators sorted by the highest maximum work package
    execution time. This list is then used to prioritize the generators that take long
    to run (for atomic work package sizes) in order to minimize wall time.

    Args:
        gen_idx: The index corresponding to the type of generator for which the list
            shall be saved. This corresponds to one of the `GEN_IDX` constants.
        generator_stats_list: The list of the generator stats.
        args: The CLI arguments.
    """
    if gen_idx == GEN_IDX_SPEC:
        return  # We do not keep a file for the specs generators.
    if args.generator_exclude or args.category_exclude or args.part_exclude:
        return  # Only save when all outputs for a given generator type are generated.
    if args.generator or args.category or args.part:
        return  # Only save when all outputs for a given generator type are generated.
    if gen_idx == GEN_IDX_FP and not args.output_dir_footprints:
        return  # Only save the fp gen list if the footprints are generated.
    if gen_idx == GEN_IDX_MOD and not args.output_dir_models:
        return  # Only save the mod gen list if the modules are generated.

    sorted_generator_stats_list = sorted(
        generator_stats_list,
        key=lambda stats: stats.max_work_package_runtime[gen_idx],
        reverse=True,
    )
    path = GENERATORS_PATH / FILE_NAMES_SORTED_GEN_LIST[gen_idx]
    with open(path, "w") as f:
        f.write(
            "# This file defines the execution order for the generators. Generators\n"
            "# are prioritized in descending order of runtime (slowest first).\n"
            "# This list is automatically updated by the generator runner when\n"
            "# executed with the `-u` option and a full generator run is performed.\n"
        )
        for generator_stats in sorted_generator_stats_list:
            if generator_stats.implemented_gens[gen_idx]:
                f.write(generator_stats.name + "\n")


def sort_generator_stats_for_minimum_wall_time(
    gen_idx: int,
    generator_stats_list: list[_GeneratorStats],
    args: Namespace,
) -> None:
    """Sort the list of generators to minimize wall time for the given generator type.

    Args:
        gen_idx: The index corresponding to the type of generator for which the list
            shall be optimized (one of the `GEN_IDX` constants).
        generator_stats_list: The list of the generator stats that is reordered
            (in-situ).
        args: The CLI arguments.
    """
    if gen_idx == GEN_IDX_SPEC:
        return  # We do not sort the specs generators
    if gen_idx == GEN_IDX_FP and not args.output_dir_footprints:
        return  # Only sort the fp gen list if the footprints are generated.
    if gen_idx == GEN_IDX_MOD and not args.output_dir_models:
        return  # Only sort the mod gen list if the modules are generated.
    sorted_names_list: list[str] = []
    try:
        path = GENERATORS_PATH / FILE_NAMES_SORTED_GEN_LIST[gen_idx]
        with open(path, "r") as f:
            for line in f:
                if not line.startswith("#"):
                    sorted_names_list.append(line.strip())
        name_to_rank = {name: index for index, name in enumerate(sorted_names_list)}
        generator_stats_list.sort(
            key=lambda stats_item: (
                0 if stats_item.name not in name_to_rank else 1,
                name_to_rank.get(stats_item.name, 0),
            )
        )
        # Check if the file FILE_NAMES_SORTED_GEN_LIST needs to be updated (because it
        # does not contain all currently generated names):
        unmatched_names: list[str] = []
        for stats_item in generator_stats_list:
            if stats_item.name not in name_to_rank:
                unmatched_names.append(stats_item.name)
        if unmatched_names:
            logging.warning(
                f"The following generator names were not found in the file "
                f"'{FILE_NAMES_SORTED_GEN_LIST[gen_idx]}':"
            )
            for unmatched_name in unmatched_names:
                logging.warning(f"- {unmatched_name}")
            logging.warning(
                "To remove this warning run the generator with the option '-u'."
            )

    except FileNotFoundError:
        logging.warning(
            f"File '{FILE_NAMES_SORTED_GEN_LIST[gen_idx]}' not found. The generators "
            "will run unsorted. This might affect the wall time negatively."
        )


if __name__ == "__main__":
    run()
