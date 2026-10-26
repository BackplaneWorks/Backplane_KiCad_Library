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

def add_argparse_arguments(parser: ArgumentParser) -> None:
    """Add arguments to an argument parser.

    Args:
        parser: The parser to add the arguments to.
    """
    parser.add_argument(
        '--phoenix-contact-config',
        type=str,
        nargs='?',
        help='the config file defining series parameters.',
        default='${GENERATORS}/connector/PhoenixContact/config_phoenix_KLCv3.0.yaml'
    )
