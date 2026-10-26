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

GEN_IDX_SPEC = 0
"""The index of the spec generator."""
GEN_IDX_FP = 1
"""The index of the footprint generator."""
GEN_IDX_MOD = 2
"""The index of the model generator."""
GEN_NUM_TYPES = 3
"""The total number of generator types."""

FUNC_NAMES = ("create_specs", "create_footprints", "create_models")
"""The names of the generator functions."""
MODULE_NAMES = ("spec", "footprint", "model")
"""The names of the generator modules."""
MODULE_NAME_ARGS = "args"
"""The module name of the argparse modifiers."""
