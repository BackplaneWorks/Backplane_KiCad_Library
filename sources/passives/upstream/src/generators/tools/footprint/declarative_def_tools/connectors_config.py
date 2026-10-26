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

import enum
import yaml
from pathlib import Path


class ConnectorOrientation(enum.Enum):
    """
    An enumeration of the possible orientations of a connector footprint.
    """

    HORZ = "H"
    VERT = "V"

    @classmethod
    def from_str(cls, string: str):
        if string == "H":
            return cls.HORZ
        elif string == "V":
            return cls.VERT
        else:
            raise ValueError(f"Unknown orientation string: {string}")


class ConnectorsConfiguration:
    """
    An object that holds the policy configuration for a connector footprint generator,
    probably read from a file like conn_config_KLCv3.yaml.
    """

    def __init__(self, config: dict):
        self.fp_name_format_string = config["fp_name_format_string"]
        self.fp_name_format_string_shielded = config["fp_name_format_string_shielded"]
        self.fp_name_no_series_format_string = config["fp_name_no_series_format_string"]
        self.fp_name_dual_pitch_format_string = config[
            "fp_name_dual_pitch_format_string"
        ]
        self.fp_name_unequal_row_format_string = config[
            "fp_name_unequal_row_format_string"
        ]

        self.keyword_fp_string = config["keyword_fp_string"]
        self.lib_name_format_string_full = config["lib_name_format_string_full"]
        self.lib_name_format_string = config["lib_name_format_string"]
        self.lib_name_specific_function_format_string = config[
            "lib_name_specific_function_format_string"
        ]

        self.entry_direction = config["entry_direction"]

        self._orientation_options: dict[ConnectorOrientation, str] = {}
        for key, value in config["orientation_options"].items():
            self._orientation_options[ConnectorOrientation(key)] = value

        self._entry_direction: dict[ConnectorOrientation, str] = {}
        for key, value in config["entry_direction"].items():
            self._entry_direction[ConnectorOrientation(key)] = value

    def get_orientation_name(self, orientation: ConnectorOrientation) -> str:
        """
        Get the name of the orientation of the connector, for use in the footprint name string.
        """
        return self._orientation_options[orientation]

    def get_orientation_description(self, orientation: ConnectorOrientation) -> str:
        """
        Get the description of the orientation of the connector, for use in the footprint description
        or keywords.
        """
        return self._entry_direction[orientation]

    @classmethod
    def load_from_file(cls, filepath: Path):
        with open(filepath, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
        return cls(config)
