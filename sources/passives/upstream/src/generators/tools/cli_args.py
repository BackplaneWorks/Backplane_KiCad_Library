# kilibs is free software: you can redistribute it and/or modify it under the terms of
# the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# kilibs is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with kilibs.
# If not, see < http://www.gnu.org/licenses/ >.
#
# (C) The KiCad Librarian Team
"""
The parsed command line interface (CLI) arguments.

This module is designed to be imported only once, providing direct access to the single,
static Namespace instance containing all command-line configuration.
"""

from argparse import Namespace


def init(cli_args: Namespace) -> None:
    """Initialize the CLI arguments.
    This method needs to be called once for each process.

    Args:
        cli_args: The parsed CLI arguments.
    """
    global CLI_ARGS
    CLI_ARGS = cli_args  # pyright: ignore


CLI_ARGS = Namespace()
"""The CLI arguments singleton."""
