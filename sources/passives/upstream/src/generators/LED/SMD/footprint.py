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

from generators.tools.spec.base_spec import BaseSpec
from generators.tools.spec.spec_generator import get_spec_file_names
from kilibs.config.global_config import GLOBAL_CONFIG


def create_footprints(spec: BaseSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification (not used by this generator).
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
    num_fps_generated = 0

    import generators.LED.SMD.plcc4 as plcc4

    file_path = get_spec_file_names(generator_name=generator_name, globs=["plcc4.yml"])[
        0
    ]
    num_fps_generated += plcc4.generate_all(GLOBAL_CONFIG, file_path, generator_name)

    import generators.LED.SMD.smlvn6 as smlvn6

    num_fps_generated += smlvn6.generate_all(GLOBAL_CONFIG, generator_name)

    return num_fps_generated
