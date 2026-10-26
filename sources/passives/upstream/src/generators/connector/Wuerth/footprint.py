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
from ..config import CONNECTOR_CONFIG


def create_footprints(spec: BaseSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification (not used by this generator).
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
    num_fps_generated = 0
    
    import generators.connector.Wuerth.wuerth_6480xx11622 as con1
    num_fps_generated += con1.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)
    
    import generators.connector.Wuerth.wuerth_wr_phd_bottom_entry as con2
    d = get_spec_file_names(generator_name=generator_name, globs=["wuerth_wr_phd_bottom_entry.yaml"])[0]
    num_fps_generated += con2.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG, d)

    return num_fps_generated

