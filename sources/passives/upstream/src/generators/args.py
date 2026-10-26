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
from pathlib import Path


def add_argparse_arguments(parser: ArgumentParser) -> None:
    """Add arguments to an argument parser.

    Args:
        parser: The parser to add the arguments to.
    """
    # Arguments for the runner:
    parser.add_argument(
        "-g",
        "--generator",
        type=str,
        nargs="*",
        default=[],
        help="Names (or globs) of the generators to run. Default: all.",
    )
    parser.add_argument(
        "-G",
        "--generator-exclude",
        type=str,
        nargs="*",
        default=[],
        help="Names (or globs) or the generators to exclude. Default: none.",
    )
    parser.add_argument(
        "-c",
        "--category",
        type=str,
        nargs="*",
        default=[],
        help="Names (or globs) of the catetories to generate. Default: all.",
    )
    parser.add_argument(
        "-C",
        "--category-exclude",
        type=str,
        nargs="*",
        default=[],
        help="Names (or globs) of the categories to exclude. Default: none.",
    )
    parser.add_argument(
        "-p",
        "--part",
        type=str,
        nargs="*",
        default=[],
        help="Names (or globs) of the parts to generate. Default: all.",
    )
    parser.add_argument(
        "-P",
        "--part-exclude",
        type=str,
        nargs="*",
        default=[],
        help="Names (or globs) of the parts to exclude. Default: none.",
    )
    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="List available generators and exit. Filter with --generator. Use in "
        "combination with '-f' and '-m' to see only relevant generators.",
    )
    parser.add_argument(
        "-f",
        "--output-dir-footprints",
        type=Path,
        default=None,
        help="Output directory for footprints. Default: no footprint generation.",
    )
    parser.add_argument(
        "-m",
        "--output-dir-models",
        type=Path,
        default=None,
        help="Output directory for models. Default: no model generation.",
    )
    parser.add_argument(
        "-s",
        "--separate-outputs",
        action="store_true",
        help="Place each generator's output in a separate directory.",
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=0,
        help="Number of jobs to run in parallel.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity level. Default: only errors and warnings.",
    )
    parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        help="Show this help message. If you specify a generator (with the -g "
        "argument) the help message is extended by the help of the generator-"
        "specific CLI agruments.",
    )
    parser.add_argument(
        "-u",
        "--update-sorted-generators-list",
        action="store_true",
        help=f"Update the files that contains the list of the generators sorted by the "
        "execution time of their slowest work package. Executing the generators in "
        "that order reduces wall time. This option only works when either all "
        "footprints or all models (or both) are generated.",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Run without creating any outputs. Use in combination with '--verbose' to"
        "display the names of the generated footprints (if used '-f DUMMY_PATH' is "
        "used) or models (if '-m DUMMY_PATH' is used).",
    )
    parser.add_argument(
        "-q",
        "--quality-assurance-set",
        action="store_true",
        help="Generate only the subset of parts that are marked for quality assurance.",
    )

    # Arugments for the footprint generators:
    parser_fp_group = parser.add_argument_group("Footprint generator arguments")
    parser_fp_group.add_argument(
        "--global-config",
        type=str,
        nargs="?",
        help="The config file defining how the footprint will look like (KLC). Default:"
        " 'config_KLCv3.0'.",
        default="config_KLCv3.0",
    )
    parser_fp_group.add_argument(
        "--ipc-rules",
        type=str,
        nargs="?",
        help="The IPC rules document. Default: 'ipc_7351b'.",
        default="ipc_7351b",
    )
    parser_fp_group.add_argument(
        "--ipc-density",
        type=str,
        nargs="?",
        help="The IPC density level ('least', 'nominal', 'most'). Default: 'nominal'",
        default="nominal",
    )
    parser_fp_group.add_argument(
        "--force-rectangular-pads",
        action="store_true",
        help="Use rectangular pads instead of rounded rectangular ones.",
    )

    # Arugments for the model generators:
    parser_mod_group = parser.add_argument_group("3D model generator arguments")
    parser_mod_group.add_argument(
        "--export-vrml",
        # deprecated=True, # needs minimum Python 3.13
        action="store_true",
        help="Export also VRML files in addition to the STEP files. Deprecated and may be removed in the future.",
    )
    parser_mod_group.add_argument(
        "--quick",
        action="store_true",
        help="Do not fuse and merge 3D models (is quicker but only for test purpose).",
    )
