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

from typing import Any
from dataclasses import dataclass, fields, asdict
import enum
from math import sqrt, isclose

from KicadModTree import (
    Footprint,
    FootprintType,
    Line,
    Model,
    Pad,
    PadArray,
    PolygonLine,
    Property,
    Rectangle,
    Text,
    Translation,
)
from kilibs.geom import Vec2DCompatible, Vector2D
import generators.tools.footprint.misc_tools as MT
from kilibs.config import global_config as GC
from generators.tools.footprint.drawing_tools import roundCrt
from kilibs.config import global_config as GC
from generators.tools.spec.base_spec import BaseSpec
from generators.tools.spec.spec_registry import register_spec
from generators.tools.footprint.save_footprint import write_footprint
from pathlib import Path

class ClassName(enum.Enum):
    PH = "PinHeader"
    PS = "PinSocket"
    IDC = "IDC-Header"

class Orientation(enum.Enum):
    VERTICAL = "Vertical"
    HORIZONTAL = "Horizontal"

class MountType(enum.Enum):
    THT = "THT"
    SMD = "SMD"
    Edge = "Edge"

@register_spec
@dataclass
class FPconfiguration(BaseSpec):
    lib_format: str = ""
    class_name: str = "" # Base behavior, checked against class ClassName(enum.Enum)
    class_descr: str = ""
    footpr_format: str = ""
    descr_format: str = ""
    tags_base: str = ""
    orientation: str = "" # checked against class Orientation(enum.Enum)
    mount_type: str = "" # checked against class MountType(enum.Enum)
    mount_text: str = ""
    footpr_type: FootprintType = FootprintType.THT # filled by init
    datasheet: str | None = None
    # should be filled by builder function:
    lib_name: str = ""
    footpr_name: str = ""

    pin_pitch: float = 0.0
    row_range: range = range(0, 0) # yaml optional input for generator
    row_count: int = 0
    row_pitch: float | None = None
    pos_range: range = range(0, 0) # yaml input for generator
    pos_count: int = 0  # filled by generator.
    pin_count: int | None = None  # filled by init: row_count * pos_count
    pin1_left: bool = True
    isStaggered: bool | None = None # filled by init if missing: True if mount_type == "SMD" and row_count == 1
    isSocket: bool = False # filled by init depending on class_name

    body_width: float = 0.0 # X plane
    body_height: float = 0.0 # Z plane usually
    body_overlength: float = 0.0 # Y plane: extra lenght from top/bottom pins -/+ pin_pitch/2.
    body_offset: float = 0.0
    body_wall_thick: float = 0.0 # IDC only?
    body_notch_width: float = 0.0 # IDC only? length?

    pins_length: float = 0.0 # The Vertical or horizontal pin part of pinheader
    pins_width: float = 0.0
    #pins_thick: float = 0.0 # for flat pins on the underside of sockets
    pins_drill: float = 0.0
    pins_offset: float = 0.0
    pins_smd_length: float = 0.0 # The curved smd part of the pinheader/pinsocket.

    pads_width: float = 0.0
    pads_length: float = 0.0
    pads_offset: float | None = None # preferred over pads_pp_width, but otherwise can be derived from that.
    pads_pp: float | None = None # pad-pad outside width, sometimes referred to as E+1 or W+1 where E/W is the pin-pin width

    # IDC specific: mounting pad/hole, latches
    mhole_drill: float = 0.0
    mhole_length: float = 0.0
    mhole_width: float = 0.0
    mhole_overlength: float = 0.0
    mhole_offset: float = 0.0
    latch_enable: bool = False
    # latch length & width should be switched after refactor since overlength and other params are referring to Y plane
    latch_length: float = 0.0
    latch_length_range = None # builder function should fill latch_length
    latch_width: float = 0.0
    mating_overlen: float = 0.0

    # these text fields have different value depending on destination. See updateTexts()
    row_text: str = ""
    pin1_text: str = ""
    mhole_text: str = ""
    latch_text: str = ""

    def isSubLevelAndParsed(self, key, value):
        if not isinstance(value, dict):
            return False

        for sub_key, sub_value in value.items():
            if sub_key == "range" or sub_key == "list":
                if hasattr(self, f'{key}_range'):
                    match sub_key:
                        case "range": setattr(self, f'{key}_range', range(value["range"][0], value["range"][1] + 1))
                        case "list":  setattr(self, f'{key}_range', list(value["list"]))
                elif hasattr(self, key):
                    match sub_key:
                        case "range": setattr(self, key, range(value["range"][0], value["range"][1] + 1))
                        case "list":  setattr(self, key, list(value["list"]))
                else:
                    raise ValueError(f'Property {key}.{sub_key} could not be mapped to FPconfiguration ({key} or {key}_range): {sub_key}')

            elif self.isSubLevelAndParsed(f'{key}_{sub_key}', sub_value): #dict in a dict?
                pass
            elif  not hasattr(self, f'{key}_{sub_key}'):
                raise ValueError(f'Property {key}.{sub_key} could not be mapped to FPconfiguration: {value}')
            else:
                setattr(self, f'{key}_{sub_key}', sub_value)
        return True


    def __init__(
        self,
        id: str = "",
        spec: dict[str, Any] = {},
        file_name: str = "",
    ) -> None:
        """Create an instance of `BaseSpec`.

        Args:
            id: The name/identifier of the spec. Typically, this is the name of the key
                of the spec (in the YAML file) or the name of the component.
            spec: The dictionary containing the specification of the component.
            file_name: The name of the YAML file that holds this spec definition.
        """
        super().__init__(id, spec, file_name)

        for key, value in spec.items():
            if key == "class_name":
                if value not in [member.value for member in ClassName]:
                    raise ValueError(f"Invalid class_name: {spec['class_name']}")
                else:
                    self.class_name = value
            elif key == "orientation":
                if value not in [member.value for member in Orientation]:
                    raise ValueError(f"Invalid orientation: {spec['orientation']}")
                else:
                    self.orientation = value
            elif key == "mount_type":
                match value:
                    case "THT":
                        self.footpr_type = FootprintType.THT
                    case "SMD" | "Edge":
                        self.footpr_type = FootprintType.SMD
                    case _:
                        raise ValueError(f"Invalid mount type: {spec['mount']}")
                self.mount_type = value
            elif self.isSubLevelAndParsed(key, value):
                pass
            elif  not hasattr(self, key):
                raise ValueError(f'Property {key} could not be mapped to FPconfiguration: {value}')
            else:
                setattr(self, key, value)
        # end of parameter parsing

        # setting defaults for optional parameters:
        if self.class_name == "PinSocket":
            self.isSocket = True
        if self.isStaggered == None:
            self.isStaggered = (True if
                self.mount_type == "SMD" and 
				self.orientation == "Vertical" and 
				self.row_count == 1
                else False)
        if self.row_pitch == None:
            self.row_pitch = self.pin_pitch
        if self.pin_count == None:
            self.pin_count = self.row_count * self.pos_count
        if self.pads_offset == None and self.pads_pp != None:
            self.pads_offset = (self.pads_pp - (self.row_count-1)*self.row_pitch - self.pads_length)/2

        self.updateTexts("Description")


    def updateTexts(self, dest, include_prefixes=True):
        valid_dests = ["FootprintName", "Description", "Tags"]
        if dest not in valid_dests:
            raise ValueError(f"updateTexts: invalid destination: {dest} not in {valid_dests}")
        if include_prefixes:
            pre_fpr = '_'
            pre_dsc = ', '
            pre_tag = ' '
        else:
            pre_fpr = ''
            pre_dsc = ''
            pre_tag = ''

        match self.row_count:
            case 1: 
                if dest == "Description":   self.row_text = pre_dsc + "single row"
                elif dest == "Tags":        self.row_text = pre_tag + "single row"
            case 2:
                if dest == "Description":   self.row_text = pre_dsc + "double rows"
                elif dest == "Tags":        self.row_text = pre_tag + "double row"
            case 3:
                if dest == "Description":   self.row_text = pre_dsc + "triple rows"
                elif dest == "Tags":        self.row_text = pre_tag + "triple row"
            case 4:
                if dest == "Description":   self.row_text = pre_dsc + "quadruple rows"
                elif dest == "Tags":        self.row_text = pre_tag + "quadruple row"
            case _: 
                raise ValueError(f"Invalid row_count: {spec['row_count']}")

        if self.pin1_left:
            if dest == "FootprintName": self.pin1_text = pre_fpr + "Pin1Left"
            elif dest == "Description": self.pin1_text = pre_dsc + "style 1 (pin 1 left)"
            elif dest == "Tags":        self.pin1_text = pre_tag + "style1 pin1 left"
        else:
            if dest == "FootprintName": self.pin1_text = pre_fpr + "Pin1Right"
            elif dest == "Description": self.pin1_text = pre_dsc + "style 2 (pin 1 right)"
            elif dest == "Tags":        self.pin1_text = pre_tag + "style2 pin1 right"

        if self.mhole_drill > 0:
            if dest == "FootprintName": self.mhole_text = "-1MP"
            elif dest == "Description": self.mhole_text = pre_dsc + "mounting holes"
            elif dest == "Tags":        self.mhole_text = pre_tag + "MountHole"

        if self.latch_enable and isclose(self.latch_length, 0, rel_tol=1e-05):
            if dest == "FootprintName": self.latch_text = pre_fpr + "Latch"
            elif dest == "Description": self.latch_text = " " + "latches"
            elif dest == "Tags":        self.latch_text = pre_tag + "latching"
        elif self.latch_enable:
            if dest == "FootprintName": self.latch_text = f"{pre_fpr}Latch{self.latch_length:03.1f}mm"
            elif dest == "Description": self.latch_text = f"{pre_dsc}{self.latch_length:03.1f}mm latches"
            elif dest == "Tags":        self.latch_text = f"{pre_tag}latch{self.latch_length:03.1f}mm"
        else:
            self.latch_text = ""

    def formatString(self, s: str) -> str:
        return MT.formatString(self, s)
        # return s.format(**asdict(self))

    def getLibraryName(self) -> str:
        return self.formatString(self.lib_format)
        # same as return self.lib_format.format(**asdict(self))

    def getFootprintName(self) -> str:
        self.updateTexts("FootprintName")
        return self.formatString(self.footpr_format)
        # same as return self.footpr_format.format(**asdict(self))

    def getDescription(self) -> str:
        self.updateTexts("Description")
        return self.formatString(self.descr_format)
        # same as return self.descr_format.format(**asdict(self))

    def getBaseTags(self) -> str:
        self.updateTexts("Tags")
        return self.formatString(self.tags_base)
        # same as return self.tags_base.format(**asdict(self))

