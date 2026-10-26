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
"""IPC rules."""

from __future__ import annotations

import dataclasses
import enum
from importlib import resources
from pathlib import Path
from typing import Any

import yaml


class IpcDensity(enum.Enum):
    """An `enum` for IPC densities."""

    # The values are the values used in ipc_defintions.yaml
    # as the keys for the density values in the IPC tables.
    LOW_DENSITY_MOST_MATERIAL = "most"
    """Setting for low density (largest pads)."""
    NOMINAL = "nominal"
    """Setting for nominal density (medium pads)."""
    HIGH_DENSITY_LEAST_MATERIAL = "least"
    """Setting for high density (smallest pads)."""

    @classmethod
    def from_str(cls, string: str) -> IpcDensity:
        """Convert a string "least/nominal/most" to an IPC density specifier.

        Args:
            string: The string ("least/nominal/most").

        Returns:
            An `IpcDensity` enum.
        """
        if string == "least":
            return cls.HIGH_DENSITY_LEAST_MATERIAL
        elif string == "nominal":
            return cls.NOMINAL
        elif string == "most":
            return cls.LOW_DENSITY_MOST_MATERIAL

        raise ValueError("Unknown IPC density specifier: {}".format(string))


@dataclasses.dataclass
class Roundoff:
    """Toe/heel/fillet roundoff values for an IPC class."""

    toe: float
    """The multiple of mm to which the toe is rounded off."""
    heel: float
    """The multiple of mm to which the heel is rounded off."""
    side: float
    """The multiple of mm to which the side is rounded off."""


@dataclasses.dataclass
class Offsets:
    """Fillet and courtyard values for an IPC class."""

    toe: float
    """Offset of the toe in mm."""
    heel: float
    """Offset of the heel in mm."""
    side: float
    """Offset of the side in mm."""
    courtyard: float
    """Offset of the courtyard in mm."""


@dataclasses.dataclass
class DeviceClass:
    """Class representing a device class (e.g. ipc_spec_smaller_0603)."""

    offsets: dict[IpcDensity, Offsets]
    """Offset values for the different IPC densities."""
    roundoff: Roundoff
    """Roundoff."""

    def get_offsets(self, density: IpcDensity) -> Offsets:
        """Get the offsets for the given IPC density.

        Args:
            density: The IPC density.

        Returns: The offset of the given IPC density.
        """
        return self.offsets[density]


class IpcRules:
    """A class for IPC rules.

    Applies to parts with toe/heel/side offsets and roundoff values for different IPC densities.
    """

    classes: dict[str, DeviceClass]
    _data: dict[str, Any]

    def __init__(self, data: dict[str, Any]) -> None:
        """Initialize the IpcRules class with the given data.

        Args:
            data: Dictionary containing IPC rules. Probalby this comes from the YAML
                file in the package, but you can provide your own.
        """
        self._data = data

        # This def doesn't specify a value for min_ep_to_pad_clearance
        # (is this really an IPC figure, not global config?)
        self.min_ep_to_pad_clearance = None

        generic_rules = data.get("ipc_generic_rules", None)

        if generic_rules is not None:
            if "min_ep_to_pad_clearance" in generic_rules:
                self.min_ep_to_pad_clearance = float(
                    generic_rules["min_ep_to_pad_clearance"]
                )

        self.classes = {}
        for key, class_data in data.items():
            # We did these already
            if key in ["ipc_generic_rules"]:
                continue

            self.classes[key] = self._construct_class(class_data)

    @classmethod
    def from_file(cls, file_name: str = "ipc_7351b") -> IpcRules:
        """Load the rules from the package data.

        Args:
            file_name: The file name.

        If the filename is a path (with a YAML extension), use it directly,
        otherwise use the package data with that name.
        """

        def get_data(path: Path | str) -> IpcRules:
            with open(path, "r") as file:
                data = yaml.safe_load(file)
                return cls(data)

        if file_name.endswith(".yaml"):
            return get_data(file_name)
        else:
            resource = resources.files("kilibs.config.ipc_configs").joinpath(
                file_name + ".yaml"
            )
            with resources.as_file(resource) as res_path:
                return get_data(res_path)

    @staticmethod
    def _roundoff_from_dict(data: dict[str, float]) -> Roundoff:
        """Create a Roundoff instance from a dictionary.

        Args:
            data: The dictionary.

        Returns:
            The `Roundoff` from the dictionary.
        """
        return Roundoff(
            toe=float(data["toe"]),
            heel=float(data["heel"]),
            side=float(data["side"]),
        )

    @staticmethod
    def _offsets_from_dict(data: dict[str, float]) -> Offsets:
        """Create an Offsets instance from a dictionary.

        Args:
            data: The dictionary.

        Returns:
            The `Offsets` from the dictionary.
        """
        return Offsets(
            toe=float(data["toe"]),
            heel=float(data["heel"]),
            side=float(data["side"]),
            courtyard=float(data["courtyard"]),
        )

    @staticmethod
    def _construct_class(data: dict[str, dict[str, float]]) -> DeviceClass:
        """Create a `DeviceClass` instance from a dictionary.

        Args:
            data: Dictionary containing the class data.

        Returns:
            The `DeviceClass` instance.
        """
        offsets: dict[IpcDensity, Offsets] = {}
        for key in ["most", "nominal", "least"]:
            fillet_data = data[key]
            density = IpcDensity.from_str(key)
            offsets[density] = IpcRules._offsets_from_dict(fillet_data)

        roundoff = IpcRules._roundoff_from_dict(data["round_base"])

        return DeviceClass(
            offsets=offsets,
            roundoff=roundoff,
        )

    def get_class(self, class_name: str) -> DeviceClass:
        """Get the `DeviceClass` instance for the given class name.

        Args:
            class_name: The class name.

        Returns:
            The `DeviceClass` instance.
        """
        return self.classes[class_name]

    @property
    def raw_data(self) -> dict[str, Any]:
        """Legacy accessor for dict-based data.

        Over time, reduce the use of this property in favour of typed
        members.
        """
        return self._data


class BallType(enum.Enum):
    """The type of a BGA ball for the purpose of calculating the pad size
    by automatic calculation."""

    COLLAPSIBLE = "collapsible"
    """Ball that collapses on reflow (e.g. a BGA solder ball)."""
    NON_COLLAPSIBLE = "non-collapsible"
    """Ball that does not collapse on reflow (e.g. a column or LGA land)."""


@dataclasses.dataclass
class IpcBallPadData:
    """Class representing a single ball-pad size definition, which is
    probably representing a given density level (e.g. Median)."""

    collapsible_ratio: float
    """Ratio of the ball diameter to the pad diameter for collapsible balls."""
    non_collapsible_ratio: float
    """Ratio of the ball diameter to the pad diameter for non-collapsible balls."""
    roundoff: float
    """Roundoff value for the pad size"""


class IpcBallRules:
    """A class for IPC ball-pad rules, indexed by IPC density."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Initialize the IpcBallRules class with the given data.

        Args:
            data: Dictionary containing IPC ball-pad rules. Probably this comes from
                the YAML file in the package, but you can provide your own.
        """

        self._pad_data: dict[IpcDensity, IpcBallPadData] = {}
        """The pad data for the different IPC densities."""
        self._data: dict[str, Any] = data
        """The raw data from the YAML file."""

        for key in ["most", "nominal", "least"]:
            ball_data = data[key]
            density = IpcDensity.from_str(key)
            self._pad_data[density] = IpcBallPadData(
                collapsible_ratio=ball_data["collapsible_ratio"],
                non_collapsible_ratio=ball_data["non_collapsible_ratio"],
                roundoff=ball_data["round_base"],
            )

    def get_pad_data(self, density: IpcDensity) -> IpcBallPadData:
        """Get the pad data for the given IPC density.

        Args:
            density: The IPC density.

        Returns:
            The `IpcBallPadData` of the given IPC density.
        """
        return self._pad_data[density]

    @classmethod
    def from_file(cls, file_name: str = "ipc7352_ball") -> IpcBallRules:
        """Load the rules from the package data.

        Args:
            file_name: The file name.

        If the filename is a path (with a YAML extension), use it directly,
        otherwise use the package data with that name.
        """

        def get_data(path: Path | str) -> IpcBallRules:
            with open(path, "r") as file:
                data = yaml.safe_load(file)
                # The ball rules YAML holds the densities under a single class key
                # (e.g. "ipc_spec_ball_7352").
                return cls(data["ball_size_data"])

        if file_name.endswith(".yaml"):
            return get_data(file_name)
        else:
            resource = resources.files("kilibs.config.ipc_configs").joinpath(
                file_name + ".yaml"
            )
            with resources.as_file(resource) as res_path:
                return get_data(res_path)


@dataclasses.dataclass
class ManufacturingTolerance:
    """Manufacturing tolerance for IPC rules (F and P)."""

    manufacturing_tolerance: float
    """Manufacturing tolerance in mm. This is the F value in IPC rules."""
    placement_tolerance: float
    """Placement tolerance in mm. This is the P value in IPC rules."""


def init(rules_file: str = "ipc_7351b") -> None:
    """Initialize the default IPC rules singleton."""
    global DEFAULT_IPC_RULES
    DEFAULT_IPC_RULES = IpcRules.from_file(rules_file)  # pyright: ignore


DEFAULT_IPC_RULES = IpcRules.from_file()
"""The default IPC rules singleton."""

DEFAULT_IPC_BALL_RULES = IpcBallRules.from_file()
"""The default IPC ball-pad rules singleton."""
