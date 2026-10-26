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

from argparse import ArgumentParser

DEFAULT_MIN_PAD_DRILL_INC = 0.2
DEFAULT_PAD_DRILL_INC_FACTOR = 1.25
DEFAULT_RELIEF_DRILL_INC = 0.5


def add_argparse_arguments(parser: ArgumentParser) -> None:
    """Add arguments to an argument parser.

    Args:
        parser: The parser to add the arguments to.
    """
    parser.add_argument(
        '--wire-connector-minimum-pad-drill-oversize', type=float, default=DEFAULT_MIN_PAD_DRILL_INC,
        help='Determines the minimum for how much the pads PTH drill is increased compared to conductor diameter.'
        )
    parser.add_argument(
        '--wire-connector-pad-drill-factor', type=float, default=DEFAULT_PAD_DRILL_INC_FACTOR,
        help='Determines the multiplicator for pad drill size compared to conductor diameter'
        )
    parser.add_argument(
        '--wire-connector-relief-drill-oversize', type=float, default=DEFAULT_RELIEF_DRILL_INC,
        help='Determines how much the relief NPTH drill is increased compared to outer diameter.'
        )
