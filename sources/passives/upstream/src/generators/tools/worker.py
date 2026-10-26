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

import importlib
import logging
import time
from argparse import Namespace
from collections.abc import Callable, Sequence
from typing import Any, cast

from generators.tools.spec.base_spec import BaseSpec

from .definitions import FUNC_NAMES, GEN_IDX_SPEC, MODULE_NAMES

_keyboard_interrupt_received = False
"""Store whether a keyboard interrupt has been received."""

_function_cache: dict[tuple[str, int], Callable[[Any, str], list[Any] | int]] = {}
"""Cache for the generator functions that have already been imported."""


def _get_function(
    generator_name: str, gen_idx: int
) -> Callable[[Any, str], list[Any] | int]:
    """
    Retrieve a function from the cache or load it dynamically if not cached.

    Args:
        generator_name: The name of the generator.
        gen_idx: The index of the generator type (0=spec, 1=footprint, 2=model).

    Return:
        The generator function.
    """
    cache_key = (generator_name, gen_idx)
    if cache_key in _function_cache:
        return _function_cache[cache_key]
    name = f"generators.{generator_name.replace('/', '.')}.{MODULE_NAMES[gen_idx]}"
    try:
        module = importlib.import_module(name)
        func = getattr(module, FUNC_NAMES[gen_idx])
        _function_cache[cache_key] = func
        return func
    except AttributeError:
        if gen_idx == GEN_IDX_SPEC:
            import generators.tools.spec.spec_generator as spec_generator

            # When no create_specs() function is implemented use the default
            # implementation.
            _function_cache[cache_key] = spec_generator.create_specs
            return spec_generator.create_specs
        else:
            raise AttributeError(
                f"Function '{FUNC_NAMES[gen_idx]}' not found in module '{name}'."
            )


def init_worker(args: Namespace) -> None:
    """Initializes the persistent variables of a process. This method should be called
    only once for each process.

    Args:
        args: The CLI arguments.
    """
    import colorlog

    from generators.tools import cli_args
    from kilibs.config import global_config, ipc_rules

    LOG_FORMAT = "%(log_color)s%(message)s%(reset)s"
    LOG_COLORS = {
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
    }

    cli_args.init(args)
    ipc_rules.init(args.ipc_rules)
    global_config.init(args.global_config)

    # Configure the debug level:
    if args.verbose == 0:
        log_level = logging.WARNING
    elif args.verbose == 1:
        log_level = logging.INFO
    else:  # elif verbose_level > 1:
        log_level = logging.DEBUG
    colorlog.basicConfig(  # type: ignore
        level=log_level,
        format=LOG_FORMAT,
        log_colors=LOG_COLORS,
    )


def run_worker(
    generator_name: str, gen_idx: int, work_package: Sequence[str | BaseSpec]
) -> tuple[list[BaseSpec] | int, float]:
    """Execute the generator function of the given generator and measure the execution
    time.

    Args:
        generator_name: The name of the generator.
        gen_idx: Index of the generator to call (0=spec, 1=footprint, 2=model).
        work_package: The work package to run the generator on.

    Returns:
        A tuple containing the result of the run in the first and the time in seconds in
        the second argument.
    """
    # Since the keyboard interrupt (CTRL + C) is not handled correctly by the
    # ProcessPoolExecutor, if a keyboard interrupt is detected, this process and all
    # remaining processes in the pool are terminated by raising a KeyboardInterrupt:
    global _keyboard_interrupt_received
    if _keyboard_interrupt_received:
        raise KeyboardInterrupt
    try:
        start_time = time.perf_counter()
        return_val: list[BaseSpec] | int
        if isinstance(work_package[0], str):
            return_val = []
        else:
            return_val = 0
        func = _get_function(generator_name, gen_idx)
        for data in work_package:
            return_val += cast(Any, func(data, generator_name))
        elapsed_time = time.perf_counter() - start_time
        return return_val, elapsed_time
    except KeyboardInterrupt:
        _keyboard_interrupt_received = True
        raise
