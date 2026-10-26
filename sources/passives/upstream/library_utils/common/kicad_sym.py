"""
Library for processing KiCad's symbol files.
"""

import hashlib
import json
import math
import re
import shutil
import sys
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import geometry
import sexpr


class KicadFileFormatError(ValueError):
    """any kind of problem discovered while parsing a KiCad file"""


# KiCad can only handle multiples of 90 degrees
VALID_ROTATIONS = frozenset({0, 90, 180, 270})


def mil_to_mm(mil: float) -> float:
    return round(mil * 0.0254, 6)


def mm_to_mil(mm: float) -> float:
    return round(mm / 0.0254)


def _parse_at(i):
    sexpr_at = _get_array(i, "at")[0]
    posx = sexpr_at[1]
    posy = sexpr_at[2]
    if len(sexpr_at) == 4:
        rot = sexpr_at[3]
    else:
        rot = None
    return (posx, posy, rot)


def _get_array(
    data,
    value,
    result: Optional[List[Any]] = None,
    level: int = 0,
    max_level: Optional[int] = None,
):
    """return the array which has value as first element"""
    if result is None:
        result = []

    if max_level is not None and max_level <= level:
        return result

    level += 1

    for index, i in enumerate(data):
        if isinstance(i, list):
            _get_array(i, value, result, level, max_level)
        else:
            # also check for the index here, if we don't do that, we might return a list
            # that looks like [0, 1, 2, 'value', 4], but we only want to return a list
            # where 'value' is the first element, like ['value', 2, 3, 4]
            if i == value and index == 0:
                result.append(data)
    return result


def _get_array2(data, value):
    ret = []
    for i in data:
        if isinstance(i, list) and i[0] == value:
            ret.append(i)
    return ret


def _get_color(sexpr) -> Optional["Color"]:
    col = None
    for i in sexpr:
        if isinstance(i, list) and i[0] == "color":
            col = Color(i[1], i[2], i[3], i[4])
    return col


def _get_stroke(sexpr) -> Tuple[Optional[int], Optional["Color"]]:
    width = None
    line_style = "default"
    col = None
    for i in sexpr:
        if isinstance(i, list) and i[0] == "stroke":
            width = _get_value_of(i, "width")
            line_style = _get_value_of(i, "type")
            col = _get_color(i)
            break
    return (width, line_style, col)


def _get_fill(sexpr) -> Tuple[Optional[Any], Optional["Color"]]:
    fill = None
    col = None
    for i in sexpr:
        if isinstance(i, list) and i[0] == "fill":
            fill = _get_value_of(i, "type")
            col = _get_color(i)
            break
    return (fill, col)


def _get_xy(sexpr, lookup) -> Tuple[float, float]:
    for i in sexpr:
        if isinstance(i, list) and i[0] == lookup:
            return (i[1], i[2])
    return (0.0, 0.0)


def _get_value_ofRecursively(data, path, item_to_get=False):
    """return the array which has value as first element, but recursively

    if item_to_get is != 0, return the array element with that index
    """
    # if we walked the whole path we are done. return the data
    if not path:
        # in some cases it is useful to only get the 2nd item, for
        # example ['lenght', 42] should just return 42
        if item_to_get != 0:
            return data[item_to_get]
        return data

    for i in data:
        # look at sub-arrays, if their first element matches the path-spec,
        # strip the front item from the path list and do this recursively
        if isinstance(i, list) and i[0] == path[0]:
            return _get_value_ofRecursively(i, path[1:], item_to_get)


def _get_value_of(data, lookup, default=None):
    """find the array which has lookup as first element, return its 2nd element"""
    for i in data:
        if isinstance(i, list) and i[0] == lookup:
            return i[1]
    return default


def _get_yesno_value_of(data, lookup, default=False):
    """find the array which has lookup as first element, return its 2nd element as boolean"""
    for i in data:
        if isinstance(i, list) and i[0] == lookup:
            return i[1].lower() == "yes"
    return default


def _has_value(data, lookup) -> bool:
    """return true if the lookup item exists"""
    for i in data:
        if isinstance(i, list) and i[0] == lookup:
            return True
    return False


class KicadSymbolBase:
    def as_json(self):
        return json.dumps(self, default=lambda x: x.__dict__, indent=2)

    def compare_pos(self, x, y):
        if hasattr(self, "posx") and hasattr(self, "posy"):
            return round(self.posx, 6) == round(x, 6) and round(self.posy, 6) == round(
                y, 6
            )
        return False

    def is_unit(self, unit, body_style_idx):
        if hasattr(self, "unit") and hasattr(self, "body_style_idx"):
            return self.unit == unit and self.body_style_idx == body_style_idx
        return False

    @classmethod
    def quoted_string(cls, s: str) -> str:
        s = re.sub("\\n", "\\\\n", s)
        s = re.sub('"', '\\"', s)
        return f'"{s}"'

    @classmethod
    def dir_to_rotation(cls, d: str) -> int:
        if d == "R":
            return 0
        elif d == "U":
            return 90
        elif d == "L":
            return 180
        elif d == "D":
            return 270
        else:
            raise ValueError(
                f"Invalid direction requested: {d} (should be one of: R / U / L / D"
            )


@dataclass
class Color(KicadSymbolBase):
    """Encode the color of an entity. Currently not used in the kicad_sym format"""

    r: int
    g: int
    b: int
    a: int

    def get_sexpr(self):
        return ["color", self.r, self.g, self.b, self.a]


@dataclass
class TextEffect(KicadSymbolBase):
    """Encode the text effect of an entity"""

    sizex: float
    sizey: float
    is_italic: bool = False
    is_bold: bool = False
    is_mirrored: bool = False
    h_justify: str = "center"
    v_justify: str = "center"
    color: Optional[Color] = None
    face: Optional[str] = None

    @classmethod
    def new_mil(cls, size: float) -> "TextEffect":
        return cls(mil_to_mm(size), mil_to_mm(size))

    def get_sexpr(self):
        fnt = ["font", ["size", self.sizex, self.sizey]]
        if self.face:
            fnt.append(["face", self.face])
        if self.is_italic:
            fnt.append(["italic", "yes"])
        if self.is_bold:
            fnt.append(["bold", "yes"])
        sx = ["effects", fnt]
        if self.is_mirrored:
            sx.append("mirror")
        if self.color:
            sx.append(self.color.get_sexpr())

        justify = ["justify"]
        if self.h_justify and self.h_justify != "center":
            justify.append(self.h_justify)
        if self.v_justify and self.v_justify != "center":
            justify.append(self.v_justify)

        if len(justify) > 1:
            sx.append(justify)

        return sx

    @classmethod
    def from_sexpr(cls, sexpr):
        if sexpr.pop(0) != "effects":
            return None
        font_info = _get_array(sexpr, "font")[0]
        face = _get_value_of(font_info, "face", None)
        sizex, sizey = _get_xy(font_info, "size")
        is_italic = "italic" in font_info
        is_bold = "bold" in font_info
        is_mirrored = "mirror" in sexpr
        justify = _get_array2(sexpr, "justify")
        h_justify = "center"
        v_justify = "center"
        if justify:
            if "top" in justify[0]:
                v_justify = "top"
            if "bottom" in justify[0]:
                v_justify = "bottom"
            if "left" in justify[0]:
                h_justify = "left"
            if "right" in justify[0]:
                h_justify = "right"
        return cls(
            sizex,
            sizey,
            is_italic,
            is_bold,
            is_mirrored,
            h_justify,
            v_justify,
            face=face,
        )


@dataclass
class AltFunction(KicadSymbolBase):
    name: str
    etype: str
    shape: str = "line"

    def get_sexpr(self) -> List[str]:
        return ["alternate", self.quoted_string(self.name), self.etype, self.shape]

    @classmethod
    def from_sexpr(cls, sexpr) -> "AltFunction":
        identifier, name, etype, shape = sexpr
        return AltFunction(name, etype, shape)


@dataclass
class Pin(KicadSymbolBase):
    name: str
    number: str
    etype: str
    posx: float = 0.0
    posy: float = 0.0
    rotation: int = 0
    shape: str = "line"
    length: float = 2.54
    is_global: bool = False
    is_hidden: bool = False
    number_int: Optional[int] = None
    name_effect: Optional[TextEffect] = None
    number_effect: Optional[TextEffect] = None
    altfuncs: List[AltFunction] = field(default_factory=list)
    unit: int = 0
    body_style_idx: int = 0

    def __post_init__(self):
        # try to parse the pin_number into an integer if possible
        if self.number_int is None and re.match(r"^\d+$", self.number):
            self.number_int = int(self.number)
        # There is some weird thing going on with the instance creation of name_effect and
        # number_effect.
        # when creating lots of pins from scratch, the id() of their name_effect member is the same
        # that is most likely the result of some optimization
        # to circumvent that, we create instances explicitly
        if self.name_effect is None:
            self.name_effect = TextEffect(1.27, 1.27)
        if self.number_effect is None:
            self.number_effect = TextEffect(1.27, 1.27)

    @classmethod
    def _parse_name_or_number(cls, i, typ="name"):
        """Convert a sexpr pin-name or pin-number into a python dict"""
        sexpr_n = _get_array(i, typ)[0]
        name = sexpr_n[1]
        effects = TextEffect.from_sexpr(_get_array(sexpr_n, "effects")[0])
        return (name, effects)

    def get_sexpr(self):
        sx = [
            "pin",
            self.etype,
            self.shape,
            ["at", self.posx, self.posy, self.rotation],
        ]
        if self.is_global:
            sx.append("global")
        sx.append(["length", self.length])

        # hide is default no
        if self.is_hidden:
            sx.append(["hide", "yes"])

        name_sx: list[Any] = ["name", self.quoted_string(self.name)]
        if self.name_effect:
            name_sx.append(self.name_effect.get_sexpr())
        sx.append(name_sx)
        number_sx: list[Any] = ["number", self.quoted_string(self.number)]
        if self.number_effect:
            number_sx.append(self.number_effect.get_sexpr())
        sx.append(number_sx)

        # alternates are sorted by name in KiCad
        alt_funcs = sorted(self.altfuncs, key=lambda af: af.name)

        for altfn in alt_funcs:
            sx.append(altfn.get_sexpr())

        return sx

    def get_direction(self) -> str:
        if self.rotation == 0:
            return "R"
        elif self.rotation == 90:
            return "U"
        elif self.rotation == 180:
            return "L"
        elif self.rotation == 270:
            return "D"
        else:
            raise NotImplementedError(f"Invalid 'rotation' of Pin: {self.rotation}")

    """
    Since KiCad10 Pins can be natively stacked. They format just puts a list of pin numbers
    into the normal pin_number field like so: [23, 45, 74]
    This function splits 'unstacks' those pins and returns a list of the pins that are
    part of the pinstack.
    """

    def unstack(self) -> List["Pin"]:
        if stack_list := re.match(r"^\[(.*?)\]$", self.number):
            pin_list = []
            pins_in_stack = stack_list.group(1).split(",")
            for pin_number in pins_in_stack:
                # if the current 'pin-number' is a range, we need to unpack that
                if "-" in pin_number and len(pin_number.split("-")) == 2:
                    pin_prefix = Pin.get_pin_number_prefix(pin_number)
                    pin_num_start, pin_num_end = [
                        p.removeprefix(pin_prefix) for p in pin_number.split("-")
                    ]
                    for i in range(int(pin_num_start), int(pin_num_end) + 1):
                        pinstack_pin = deepcopy(self)
                        pinstack_pin.number = pin_prefix + str(i)
                        pin_list.append(pinstack_pin)
                else:
                    # make a copy of the pin, then overwrite its
                    # number with the unstacked number
                    pinstack_pin = deepcopy(self)
                    pinstack_pin.number = pin_number
                    pin_list.append(pinstack_pin)
            return pin_list
        else:
            return [self]

    """
    Returns true when this pin is a native pin stack
    """

    def is_stack(self) -> bool:
        return True if re.match(r"^\[(.*?)\]$", self.number) else False

    """
    Returns the pin native stack number or range alpha-char prefix
    Like A4 -> "A", AM6 -> "AM", AD12-AD22 -> "AD" or non on simple numbers 4 -> ""
    """

    @staticmethod
    def get_pin_number_prefix(pin_name) -> str:
        # return everything up to the first digit...
        for i in range(len(pin_name)):
            if pin_name[i].isdigit():
                return pin_name[:i]
        # ...or the whole name
        return pin_name

    @classmethod
    def from_sexpr(cls, sexpr, unit: int, body_style_idx: int) -> "Pin":
        is_hidden = False
        is_global = False
        # The first 3 items are pin, type and shape
        if sexpr.pop(0) != "pin":
            return None
        etype = sexpr.pop(0)
        shape = sexpr.pop(0)
        # the 4th item (global) is optional
        if sexpr[0] == "global":
            sexpr.pop(0)
            is_global = True
        # fetch more properties
        hidearray = _get_array2(sexpr, "hide")
        if len(hidearray) and "yes" in hidearray[0]:
            is_hidden = True
        length = _get_value_of(sexpr, "length")
        posx, posy, rotation = _parse_at(sexpr)
        name, name_effect = cls._parse_name_or_number(sexpr)
        number, number_effect = cls._parse_name_or_number(sexpr, typ="number")

        if rotation not in VALID_ROTATIONS:
            raise ValueError(
                f"Invalid 'rotation' attribute value for pin: {rotation}"
                f" (must be one of {set(VALID_ROTATIONS)})"
            )
        altfuncs = []
        alt_n = _get_array(sexpr, "alternate")
        for alt_sexpr in alt_n:
            altfuncs.append(AltFunction.from_sexpr(alt_sexpr))
        # we also need the pin-number as integer, try to convert it.
        # Some pins won't work since they are called 'MP' or similar
        number_int = None
        try:
            number_int = int(number)
        except ValueError:
            pass
        # create and return a pin with the extracted values
        return Pin(
            name,
            number,
            etype,
            posx,
            posy,
            rotation,
            shape,
            length,
            is_global,
            is_hidden,
            number_int,
            name_effect,
            number_effect,
            altfuncs=altfuncs,
            unit=unit,
            body_style_idx=body_style_idx,
        )


@dataclass
class Circle(KicadSymbolBase):
    centerx: float
    centery: float
    radius: float
    stroke_width: float = 0.254
    stroke_line_style: str = "default"
    stroke_color: Optional[Color] = None
    fill_type: str = "none"
    fill_color: Optional[Color] = None
    unit: int = 0
    body_style_idx: int = 0

    def get_sexpr(self) -> List[Any]:
        stroke_sx = ["stroke", ["width", self.stroke_width]]
        if self.stroke_color:
            stroke_sx.append(self.stroke_color.get_sexpr())
        fill_sx = ["fill", ["type", self.fill_type]]
        if self.fill_color:
            fill_sx.append(self.fill_color.get_sexpr())
        sx = [
            "circle",
            ["center", self.centerx, self.centery],
            ["radius", self.radius],
            stroke_sx,
            fill_sx,
        ]
        return sx

    @classmethod
    def from_sexpr(cls, sexpr, unit: int, body_style_idx: int):
        # The first 3 items are pin, type and shape
        if sexpr.pop(0) != "circle":
            return None
        # the 1st element
        centerx, centery = _get_xy(sexpr, "center")
        radius = _get_value_of(sexpr, "radius")
        stroke, sline, scolor = _get_stroke(sexpr)
        fill, fcolor = _get_fill(sexpr)
        return Circle(
            centerx,
            centery,
            radius,
            stroke,
            sline,
            scolor,
            fill,
            fcolor,
            unit=unit,
            body_style_idx=body_style_idx,
        )

    @property
    def center(self) -> geometry.Point:
        return Point(self.centerx, self.centery)


@dataclass
class Arc(KicadSymbolBase):
    #  (arc (start -3.302 3.175) (mid -3.937 2.54) (end -3.302 1.905)
    #    (stroke (width 0.254) (type default) (color 0 0 0 0))
    #    (fill (type none))
    #  )
    startx: float
    starty: float
    endx: float
    endy: float
    midx: float
    midy: float
    stroke_width: float = 0.254
    stroke_line_style: str = "default"
    stroke_color: Optional[Color] = None
    fill_type: str = "none"
    fill_color: Optional[Color] = None
    unit: int = 0
    body_style_idx: int = 0

    def get_sexpr(self) -> List[Any]:
        stroke_sx = [
            "stroke",
            ["width", self.stroke_width],
            ["type", self.stroke_line_style],
        ]
        if self.stroke_color:
            stroke_sx.append(self.stroke_color.get_sexpr())
        fill_sx = ["fill", ["type", self.fill_type]]
        if self.fill_color:
            fill_sx.append(self.fill_color.get_sexpr())
        sx = [
            "arc",
            ["start", self.startx, self.starty],
            ["mid", self.midx, self.midy],
            ["end", self.endx, self.endy],
            stroke_sx,
            fill_sx,
        ]
        return sx

    @classmethod
    def from_sexpr(cls, sexpr, unit: int, body_style_idx: int) -> Optional["Arc"]:
        if sexpr.pop(0) != "arc":
            return None
        startx, starty = _get_xy(sexpr, "start")
        endx, endy = _get_xy(sexpr, "end")
        midx, midy = _get_xy(sexpr, "mid")
        stroke, sline, scolor = _get_stroke(sexpr)
        fill, fcolor = _get_fill(sexpr)
        return Arc(
            startx,
            starty,
            endx,
            endy,
            midx,
            midy,
            stroke,
            sline,
            scolor,
            fill,
            fcolor,
            unit=unit,
            body_style_idx=body_style_idx,
        )

    @property
    def start(self) -> geometry.Point:
        return geometry.Point(self.startx, self.starty)

    @property
    def end(self) -> geometry.Point:
        return geometry.Point(self.endx, self.endy)

    @property
    def midpoint(self) -> geometry.Point:
        return geometry.Point(self.midx, self.midy)


@dataclass
class Point(KicadSymbolBase):
    """
    A point in a KiCad symbol
    """

    _pt: geometry.Point

    def __init__(self, x, y):
        self._pt = geometry.Point(x, y)

    @property
    def pt(self) -> geometry.Point:
        """
        Get the geometric point underlying this object
        """
        return self._pt

    @property
    def x(self) -> float:
        return self._pt.x

    @property
    def y(self) -> float:
        return self._pt.y

    @classmethod
    def new_mil(cls, x: float, y: float) -> "Point":
        return cls(mil_to_mm(x), mil_to_mm(y))

    def get_sexpr(self):
        return ["xy", self._pt.x, self._pt.y]


@dataclass
class Polyline(KicadSymbolBase):
    points: List[Point]
    stroke_width: float = 0.254
    stroke_line_style: str = "default"
    stroke_color: Optional[Color] = None
    fill_type: str = "none"
    fill_color: Optional[Color] = None
    unit: int = 0
    body_style_idx: int = 0

    def get_sexpr(self):
        pts_list: list[Any] = [x.get_sexpr() for x in self.points]
        pts_list.insert(0, "pts")
        stroke_sx = [
            "stroke",
            ["width", self.stroke_width],
            ["type", self.stroke_line_style],
        ]
        if self.stroke_color:
            stroke_sx.append(self.stroke_color.get_sexpr())
        fill_sx = ["fill", ["type", self.fill_type]]
        if self.fill_color:
            fill_sx.append(self.fill_color.get_sexpr())
        sx = [
            "polyline",
            pts_list,
            stroke_sx,
            fill_sx,
        ]
        return sx

    def is_closed(self) -> bool:
        # if the last and first point are the same, we consider the polyline closed
        # a closed triangle will have 4 points (A-B-C-A) stored in the list of points
        return (len(self.points) > 3) and (self.points[0] == self.points[-1])

    def get_boundingbox(self) -> Tuple[float, float, float, float]:
        if self.points:
            minx = min(p.x for p in self.points)
            maxx = max(p.x for p in self.points)
            miny = min(p.y for p in self.points)
            maxy = max(p.y for p in self.points)
            return (maxx, maxy, minx, miny)
        else:
            return (0, 0, 0, 0)

    def as_rectangle(self) -> "Rectangle":
        maxx, maxy, minx, miny = self.get_boundingbox()
        return Rectangle(
            minx,
            maxy,
            maxx,
            miny,
            self.stroke_width,
            self.stroke_color,
            self.fill_type,
            self.fill_color,
            unit=self.unit,
            body_style_idx=self.body_style_idx,
        )

    def get_center_of_boundingbox(self) -> Tuple[float, float]:
        maxx, maxy, minx, miny = self.get_boundingbox()
        return ((minx + maxx) / 2, ((miny + maxy) / 2))

    def is_rectangle(self) -> bool:
        # a rectangle has 5 points and is closed
        if len(self.points) != 5 or not self.is_closed():
            return False

        # construct lines between the points
        p0 = self.points[0]
        for p1_idx in range(1, len(self.points)):
            p1 = self.points[p1_idx]
            dx = p1.x - p0.x
            dy = p1.y - p0.y
            if dx != 0 and dy != 0:
                # if a line is neither horizontal or vertical its not
                # part of a rectangle
                return False
            # select next point
            p0 = p1

        return True

    @classmethod
    def from_sexpr(cls, sexpr, unit: int, body_style_idx: int) -> Optional["Polyline"]:
        pts = []
        if sexpr.pop(0) != "polyline":
            return None
        for p in _get_array(sexpr, "pts")[0]:
            if "xy" in p:
                pts.append(Point(p[1], p[2]))

        stroke, sline, scolor = _get_stroke(sexpr)
        fill, fcolor = _get_fill(sexpr)
        return Polyline(
            pts,
            stroke,
            sline,
            scolor,
            fill,
            fcolor,
            unit=unit,
            body_style_idx=body_style_idx,
        )

    def get_segs(self):
        """
        Generate the geometric segments of this polyline
        """
        for i in range(len(self.points) - 1):
            yield (geometry.Seg2D(self.points[i].pt, self.points[i + 1].pt))


@dataclass
class Bezier(KicadSymbolBase):
    # (bezier
    # 	(pts
    # 		(xy 0.508 -26.67) (xy 0.508 -26.8102) (xy 0.7354 -26.924) (xy 1.016 -26.924)
    # 	)
    # 	(stroke
    # 		(width 0.0254)
    # 		(type solid)
    # 		(color 204 185 134 1)
    # 	)
    # 	(fill
    # 		(type none)
    # 	)
    # )
    points: List[float]
    stroke_width: float = 0
    stroke_type: str = "default"
    stroke_color: Optional[Color] = None
    fill_type: str = "none"
    fill_color: Optional[Color] = None
    unit: int = 0
    body_style_idx: int = 0

    def get_sexpr(self):
        pts_list: list[Any] = [x.get_sexpr() for x in self.points]
        pts_list.insert(0, "pts")
        stroke_sx = [
            "stroke",
            ["width", self.stroke_width],
            ["type", self.stroke_type],
        ]
        if self.stroke_color:
            stroke_sx.append(self.stroke_color.get_sexpr())
        fill_sx = ["fill", ["type", self.fill_type]]
        if self.fill_color:
            fill_sx.append(self.fill_color.get_sexpr())
        sx = [
            "bezier",
            pts_list,
            stroke_sx,
            fill_sx,
        ]
        return sx

    @classmethod
    def from_sexpr(cls, sexpr, unit: int, body_style_idx: int) -> Optional["Bezier"]:
        if sexpr.pop(0) != "bezier":
            return None
        points = []
        for p in _get_array(sexpr, "pts")[0]:
            if "xy" in p:
                points.append(Point(p[1], p[2]))
        stroke_width, stroke_type, stroke_color = _get_stroke(sexpr)
        fill_type, fill_color = _get_fill(sexpr)
        return Bezier(
            points,
            stroke_width,
            stroke_type,
            stroke_color,
            fill_type,
            fill_color,
            unit,
            body_style_idx,
        )


@dataclass
class Text(KicadSymbolBase):
    text: str
    posx: float
    posy: float
    rotation: float
    effects: TextEffect
    unit: int = 0
    body_style_idx: int = 0

    def get_sexpr(self) -> List[Any]:
        sx = [
            "text",
            self.quoted_string(self.text),
            ["at", self.posx, self.posy, self.rotation],
            self.effects.get_sexpr(),
        ]
        return sx

    @classmethod
    def from_sexpr(cls, sexpr, unit: int, body_style_idx: int) -> Optional["Text"]:
        if sexpr.pop(0) != "text":
            return None
        text = sexpr.pop(0)
        posx, posy, rotation = _parse_at(sexpr)
        effects = TextEffect.from_sexpr(_get_array(sexpr, "effects")[0])

        return Text(
            text,
            posx,
            posy,
            rotation,
            effects,
            unit=unit,
            body_style_idx=body_style_idx,
        )

    @property
    def pos(self):
        return geometry.Point(self.posx, self.posy)


@dataclass
class Rectangle(KicadSymbolBase):
    """
    Some v6 symbols use rectangles, newer ones encode them as polylines.
    At some point in time we can most likely remove this class since its not used anymore
    """

    startx: float
    starty: float
    endx: float
    endy: float
    stroke_width: float = 0.254
    stroke_line_style: str = "default"
    stroke_color: Optional[Color] = None
    fill_type: str = "background"
    fill_color: Optional[Color] = None
    unit: int = 0
    body_style_idx: int = 0

    @property
    def area(self) -> float:
        return abs(self.startx - self.endx) * abs(self.starty - self.endy)

    @classmethod
    def new_mil(
        cls, sx: float, sy: float, ex: float, ey: float, fill: str = "background"
    ) -> "Rectangle":
        r = cls(mil_to_mm(sx), mil_to_mm(sy), mil_to_mm(ex), mil_to_mm(ey))
        if fill in ["none", "outline", "background"]:
            r.fill_type = fill
        return r

    def get_sexpr(self) -> List[Any]:
        stroke_sx = [
            "stroke",
            ["width", self.stroke_width],
            ["type", self.stroke_line_style],
        ]
        if self.stroke_color:
            stroke_sx.append(self.stroke_color.get_sexpr())
        fill_sx = ["fill", ["type", self.fill_type]]
        if self.fill_color:
            fill_sx.append(self.fill_color.get_sexpr())
        sx = [
            "rectangle",
            ["start", self.startx, self.starty],
            ["end", self.endx, self.endy],
            stroke_sx,
            fill_sx,
        ]
        return sx

    def as_polyline(self) -> Polyline:
        pts = [
            Point(self.startx, self.starty),
            Point(self.endx, self.starty),
            Point(self.endx, self.endy),
            Point(self.startx, self.endy),
            Point(self.startx, self.starty),
        ]
        return Polyline(
            pts,
            self.stroke_width,
            self.stroke_line_style,
            self.stroke_color,
            self.fill_type,
            self.fill_color,
            unit=self.unit,
            body_style_idx=self.body_style_idx,
        )

    def get_center(self) -> Tuple[float, float]:
        x = (self.endx + self.startx) / 2.0
        y = (self.endy + self.starty) / 2.0
        return (x, y)

    @classmethod
    def from_sexpr(cls, sexpr, unit: int, body_style_idx: int) -> Optional["Rectangle"]:
        if sexpr.pop(0) != "rectangle":
            return None
        # the 1st element
        startx, starty = _get_xy(sexpr, "start")
        endx, endy = _get_xy(sexpr, "end")
        stroke, sline, scolor = _get_stroke(sexpr)
        fill, fcolor = _get_fill(sexpr)
        return Rectangle(
            startx,
            starty,
            endx,
            endy,
            stroke,
            sline,
            scolor,
            fill,
            fcolor,
            unit=unit,
            body_style_idx=body_style_idx,
        )


@dataclass
class Property(KicadSymbolBase):
    name: str
    value: str
    posx: float = 0.0
    posy: float = 0.0
    rotation: float = 0.0
    is_hidden: bool = False
    show_name: bool = False
    effects: Optional[TextEffect] = None
    private: bool = False
    do_not_autoplace: bool = False

    def __post_init__(self):
        # There is some weird thing going on with the instance creation of effect.
        # Do the same trick as we do with Pin().
        if self.effects is None:
            self.effects = TextEffect(1.27, 1.27)

    def get_sexpr(self) -> List[Any]:
        sx = ["property"]
        if self.private:
            sx.append("private")
        sx.append(self.quoted_string(self.name))
        sx.append(self.quoted_string(self.value))
        sx.append(["at", self.posx, self.posy, self.rotation])

        sx.append(["show_name", "yes" if self.show_name else "no"])

        sx.append(["do_not_autoplace", "yes" if self.do_not_autoplace else "no"])

        # KiCad 10 only output when hidden
        if self.is_hidden:
            sx.append(["hide", "yes" if self.is_hidden else "no"])

        if self.effects:
            sx.append(self.effects.get_sexpr())
        return sx

    def set_pos_mil(self, x: float, y: float, rot: int = 0) -> None:
        self.posx = mil_to_mm(x)
        self.posy = mil_to_mm(y)
        # TODO: verify whether we should really (silently) restrict the rotation of all properties
        if rot in VALID_ROTATIONS:
            self.rotation = rot

    def is_private(self):
        return self.private

    @classmethod
    def from_sexpr(cls, sexpr, unit: int = 0) -> Optional["Property"]:
        if sexpr.pop(0) != "property":
            return None
        # the first item in this list could be 'private', so if it is, we need to pop the 'name' again
        # example:  (property private "KLC_S4.2" "VDD33_{LDO} is a internal LDO"
        # vs.       (property "KLC_S4.2" "VDD33_{LDO} is a internal LDO"
        private = False
        name = sexpr.pop(0)
        if name == "private":
            private = True
            name = sexpr.pop(0)
        value = sexpr.pop(0)
        posx, posy, rotation = _parse_at(sexpr)

        do_not_autoplace = _get_yesno_value_of(sexpr, "do_not_autoplace")
        effects = TextEffect.from_sexpr(_get_array(sexpr, "effects")[0])

        is_hidden = False
        hidearray = _get_array2(sexpr, "hide")
        if len(hidearray) and "yes" in hidearray[0]:
            is_hidden = True

        show_name = _get_yesno_value_of(sexpr, "show_name")

        return Property(
            name,
            value,
            posx,
            posy,
            rotation,
            is_hidden,
            show_name,
            effects,
            private,
            do_not_autoplace,
        )


@dataclass
class KicadEmbeddedFile(KicadSymbolBase):
    name: str
    ftype: str
    compressed_data_base64: str
    checksum: str

    def get_sexpr(self) -> List[Any]:
        sx = [
            "file",
            ["name", self.quoted_string(self.name)],
            ["type", self.ftype],
            ["data", "".join(self.compressed_data_base64)],
            ["checksum", self.quoted_string(self.checksum)],
        ]
        return sx

    @classmethod
    def from_file(cls, filename: str | Path) -> Optional["KicadEmbeddedFile"]:
        filename = Path(filename)

        # needs implementing :)
        return None

    @classmethod
    def from_sexpr(cls, sexpr) -> Optional["KicadEmbeddedFile"]:
        if sexpr.pop(0) != "file":
            return None
        name = _get_value_of(sexpr, "name")
        ftype = _get_value_of(sexpr, "type")
        compressed_data_lines = _get_array(sexpr, "data")[0][1:]
        checksum = _get_value_of(sexpr, "checksum")
        return KicadEmbeddedFile(name, ftype, compressed_data_lines, checksum)


@dataclass
class KicadSymbol(KicadSymbolBase):
    name: str
    libname: str
    filename: Path = field(compare=False)
    properties: List[Property] = field(default_factory=list)
    pins: List[Pin] = field(default_factory=list)
    rectangles: List[Rectangle] = field(default_factory=list)
    circles: List[Circle] = field(default_factory=list)
    arcs: List[Arc] = field(default_factory=list)
    polylines: List[Polyline] = field(default_factory=list)
    beziers: List[Bezier] = field(default_factory=list)
    texts: List[Text] = field(default_factory=list)
    pin_names_offset: float = 0.508
    hide_pin_names: bool = False
    hide_pin_numbers: bool = False
    is_power: bool = False
    exclude_from_sim: bool = False
    in_bom: bool = True
    on_board: bool = True
    extends: Optional[str] = None
    unit_count: int = 1
    body_style_count: int = 1
    embedded_fonts = False
    files: List[KicadEmbeddedFile] = field(default_factory=list)
    """
    A dictionary mapping unit numbers (int, 1-indexed) to unit names (str).
    None values indicate that the unit has no specific name.
    """
    unit_names: dict[int, str | None] = field(default_factory=dict)
    body_styles: list[str] = field(default_factory=list)
    digest: str = ""

    # List of parent symbols, the first element is the direct parent,
    # the last element is the root symbol
    _inheritance: list["KicadSymbol"] = field(default_factory=list)

    def __post_init__(self):
        if self.filename == Path(""):
            raise ValueError("Filename can not be empty")
        self.libname = self.filename.stem

    def get_sexpr(self) -> List[str]:
        # add header
        full_name = self.quoted_string("{}".format(self.name))
        sx: list[Any] = ["symbol", full_name]
        if self.extends:
            sx.append(["extends", self.quoted_string(self.extends)])

        if not self.extends:
            # the body_styles field is only written when there is at least a second style
            if len(self.body_styles) > 1:
                bs = ["body_styles"]
                if self.body_styles[1] == "demorgan":
                    bs.append(self.quoted_string("demorgan"))
                else:
                    bs.extend([self.quoted_string(s) for s in self.body_styles])
                sx.append(bs)

            pn: list[Any] = ["pin_names"]
            if self.pin_names_offset != 0.508:
                pn.append(["offset", self.pin_names_offset])
            if self.hide_pin_names:
                pn.append(["hide", "yes"])
            if len(pn) > 1:
                sx.append(pn)

            sx.append(["exclude_from_sim", "yes" if self.exclude_from_sim else "no"])
            sx.append(["in_bom", "yes" if self.in_bom else "no"])
            sx.append(["on_board", "yes" if self.on_board else "no"])
            if self.is_power:
                sx.append(["power"])
            if self.hide_pin_numbers:
                sx.append(["pin_numbers", ["hide", "yes"]])

        # add properties
        for prop in self.properties:
            sx.append(prop.get_sexpr())

        if not self.extends:
            # if the symbol extends another one, we do not add any graphical elements
            # or pins, those are all inherited from the parent symbol

            # add embedded files
            file_expression = []
            for file in self.files:
                file_expression.append(file.get_sexpr())
            if len(file_expression) > 0:
                sx.append(["embedded_files", *file_expression])

            def pin_sort_key(pin: Pin) -> tuple:
                # This is a bit fiddly, and the comments in KiCad seems wrong
                # Pins are sorted by:
                #   pin position (y first, then x) in SCH_ITEM::compare
                # then by pin-specific values:
                #   pin number (as integer if possible, otherwise as string)
                #   ...
                return (
                    pin.posx,
                    -pin.posy,
                    pin.number,
                    pin.length,
                    pin.rotation,
                    pin.shape,
                    pin.etype,
                    pin.is_hidden,
                )

            # add units
            for d in range(0, self.body_style_count + 1):
                for u in range(0, self.unit_count + 1):
                    unit_elements = []
                    for pin in (
                        self.arcs
                        + self.circles
                        + self.texts
                        + self.rectangles
                        + self.beziers
                        + self.polylines
                        + sorted(self.pins, key=pin_sort_key)
                    ):
                        if pin.is_unit(u, d):
                            unit_elements.append(pin.get_sexpr())

                    if unit_elements:
                        subsym_name = self.quoted_string(
                            "{}_{}_{}".format(self.name, u, d)
                        )
                        unit = ["symbol", subsym_name, *unit_elements]

                        if n := self.unit_names.get(u):
                            unit.append(["unit_name", n])

                        sx.append(unit)

        sx.append(["embedded_fonts", "yes" if self.embedded_fonts else "no"])
        return sx

    def get_center_rectangle(
        self, units: Optional[List[int]] = None
    ) -> Optional[Polyline]:
        # return a polyline for the requested unit that is a rectangle
        # and is closest to the center
        candidates = {}
        # building a dict with floats as keys.. there needs to be a rule against that^^
        pl_rects = [i.as_polyline() for i in self.rectangles]
        pl_rects.extend(pl for pl in self.polylines if pl.is_rectangle())
        for pl in pl_rects:
            if (units is None) or (pl.unit in units):
                # extract the center, calculate the distance to origin
                x, y = pl.get_center_of_boundingbox()
                dist = math.sqrt(x * x + y * y)
                candidates[dist] = pl

        if candidates:
            # sort the list return the first (smallest) item
            return candidates[sorted(candidates.keys())[0]]
        return None

    def get_largest_area_rectangle(
        self, units: Optional[List[int]] = None
    ) -> Optional[Polyline]:
        """
        From all the rectangles in the requested units,
        select the one rectangle with the largest area.

        If [units] is None, all units are considered.
        """
        largest_area = 0.0
        largest_rect = None
        for pl in self.rectangles:
            if (units is None) or (pl.unit in units):
                if pl.area > largest_area:
                    largest_area = pl.area
                    largest_rect = pl

        return largest_rect

    def get_pinstacks(self) -> Dict[str, List[Pin]]:
        stacks = {}
        for pin in self.pins:
            # if the unit is 0 that means this pin is common to all units
            unit_list = [pin.unit]
            if pin.unit == 0:
                unit_list = list(range(1, self.unit_count + 1))

            # if the unit is 0 that means this pin is common to all units
            style_list = [pin.body_style_idx]
            if pin.body_style_idx == 0:
                style_list = list(range(1, self.body_style_count + 1))

            # add the pin to the correct stack
            for style in style_list:
                for unit in unit_list:
                    loc = "x{0}_y{1}_u{2}_d{3}".format(pin.posx, pin.posy, unit, style)
                    # add this location to the dict if it does not exist
                    stacks.setdefault(loc, [])
                    stacks[loc].append(pin)
        return stacks

    def get_parent_symbol(self) -> "KicadSymbol":
        if self._inheritance:
            return self._inheritance[0]
        return self

    def get_root_symbol(self) -> "KicadSymbol":
        if self._inheritance:
            return self._inheritance[-1]
        return self

    def get_property(self, pname: str) -> Optional[Property]:
        for p in self.properties:
            if p.name == pname:
                return p

        return None

    def add_default_properties(self) -> None:
        defaults = [
            {"n": "Reference", "v": "U", "h": False},
            {"n": "Value", "v": self.name, "h": False},
            {"n": "Footprint", "v": "", "h": True},
            {"n": "Datasheet", "v": "", "h": True},
            {"n": "Description", "v": "", "h": True},
            {"n": "ki_keywords", "v": "", "h": True},
            {"n": "ki_fp_filters", "v": "", "h": True},
        ]

        for prop in defaults:
            if self.get_property(prop["n"]) is None:
                p = Property(prop["n"], prop["v"])
                p.is_hidden = prop["h"]
                self.properties.append(p)

    @classmethod
    def new(
        cls,
        name: str,
        libname: str,
        reference: str = "U",
        footprint: str = "",
        datasheet: str = "",
        keywords: str = "",
        description: str = "",
        fp_filters: str = "",
        unit_names: dict = None,
    ):
        unit_names = unit_names or {}
        sym = cls(name, libname, Path(f"{libname}.kicad_sym"), unit_names=unit_names)
        sym.add_default_properties()
        sym.get_property("Reference").value = reference
        sym.get_property("Footprint").value = footprint
        sym.get_property("Datasheet").value = datasheet
        sym.get_property("ki_keywords").value = keywords
        sym.get_property("Description").value = description
        if isinstance(fp_filters, list):
            fp_filters = " ".join(fp_filters)
        sym.get_property("ki_fp_filters").value = fp_filters
        return sym

    def get_fp_filters(self) -> List[str]:
        filters = self.get_property("ki_fp_filters")
        if filters:
            return filters.value.split(" ")
        else:
            return []

    def is_graphic_symbol(self) -> bool:
        return self.extends is None and (
            not self.pins or self.get_property("Reference").value == "#SYM"
        )

    def is_power_symbol(self) -> bool:
        return self.is_power

    def is_locked(self) -> bool:
        return self.get_property("ki_locked") is not None

    def get_pins_by_name(self, name: str) -> List[Pin]:
        pins = []
        for pin in self.pins:
            if pin.name == name:
                pins += [pin]
        return pins

    def get_pins_by_number(self, num) -> Optional[Pin]:
        for pin in self.pins:
            if pin.number == str(num):
                return pin
        return None

    # by default return pins in style 1
    def get_pins_by_unit(self, unit_num: int, body_style: int | str = 1) -> List[Pin]:
        """
        Returns all the pins of a specified unit number unit_num. The method uses by default
        body style with index 1 (first style) which is always available. It is possible to ask for
        a different style with parameter body_style which can be a numerical index or the name.

        The available names for a body_style depends on how a symbol is defined. When only one
        style is implemented for a symbol, by default it is not explicitly named and we use
        the conventional name "standard". Legacy symbols before kicad 10, with an optional body style,
        were calling the second body style as "demorgan". Since kicady 10 it is possible to have a
        custom number of body style and the names are defined locally in the symbol itself, in this
        case "standard" or "demorgan" may not work. You can use the method get_unit_body_styles()
        to discover the available names.
        """
        if isinstance(body_style, str):
            if body_style not in self.body_styles:
                raise ValueError(f"{body_style} is not a valid body style")
            body_style_idx = self.body_styles.index(body_style) + 1
        else:
            body_style_idx = body_style

        if unit_num > self.unit_count:
            raise ValueError(f"unit id {unit_num} is out of possible values")
        if body_style_idx > self.body_style_count:
            raise ValueError(f"style id {body_style_idx} is out of possible values")

        pins = []
        if unit_num > 0 and body_style_idx > 0:
            for pin in self.pins:
                # unit 0 means pin shared among all units, style 0 means pin shared among all styles
                if (pin.unit == unit_num or pin.unit == 0) and (
                    pin.body_style_idx == body_style_idx or pin.body_style_idx == 0
                ):
                    pins += [pin]
        return pins

    def filter_pins(
        self,
        name: Optional[str] = None,
        direction: Optional[str] = None,
        electrical_type: Optional[str] = None,
    ) -> List[Pin]:
        pins = []
        for pin in self.pins:
            if (
                (name and pin.name == name)
                or (direction and pin.rotation == self.dir_to_rotation(direction))
                or (electrical_type and pin.etype == electrical_type)
            ):
                pins.append(pin)
        return pins

    # Heuristics, which tries to determine whether this is a "small" component (resistor,
    # capacitor, LED, diode, transistor, ...).
    def is_small_component_heuristics(self) -> bool:
        if len(self.pins) <= 2:
            return True

        filled_rect = self.get_center_rectangle(list(range(self.unit_count)))

        # if there is no filled rectangle as symbol outline and we have 3 or 4 pins, we assume this
        # is a small symbol
        if (3 <= len(self.pins) <= 4) and (filled_rect is None):
            return True

        return False

    def get_unit_body_styles(self, unit_num: int = 0) -> list[tuple[int, int, str]]:
        """
        Returns the available body styles of a specific or all units. The result is a list
        of three-elements tuples where the first item is the unit number, the second is the
        body style index number, and the third element is the body style name.
        """
        result = []

        if unit_num > 0:
            unit_list = [unit_num]
        else:
            unit_list = range(1, self.unit_count + 1)
        for u in unit_list:
            for style_idx, style in enumerate(self.body_styles):
                if self.get_pins_by_unit(u, style):
                    result.append((u, style_idx + 1, style))

        return result

    def derive(self, name: str, new_prop_values: dict = {}) -> "KicadSymbol":
        """
        Create a new symbol deriving from an existing one.

        A derived symbol inherits all the properties, standard and custom, from the base symbol.
        Here, by default, the property Value is set to the new symbol name while Reference is set
        equal to the base symbol value. All the other standard properties of the derived symbol are
        instead reset. It is also possible to specify custom initial values by passing a dictionary
        new_prop_values where the keys are the property names.
        """
        newsym = deepcopy(self)
        newsym._inheritance = [self]

        # remove graphical part
        newsym.pins = []
        newsym.rectangles = []
        newsym.circles = []
        newsym.arcs = []
        newsym.polylines = []
        newsym.beziers = []
        newsym.texts = []

        # reset members related to graphical part
        newsym.unit_names = {}
        newsym.unit_count = 1
        newsym.body_styles = ["standard"]
        newsym.body_style_count = 1

        newsym.name = name
        newsym.extends = self.name
        if self.filename.parent.suffix == ".kicad_symdir":
            newsym.filename = newsym.filename.with_name(f"{name}.kicad_sym")
        elif self.filename.suffix == ".kicad_sym":
            pass  # same filename
        else:
            raise Exception(f"unsupported library name {self.filename}")

        # standard properties
        prop_list = [
            "Reference",
            "Value",
            "Footprint",
            "Datasheet",
            "Description",
            "ki_keywords",
            "ki_fp_filters",
        ]

        for p in prop_list:
            if p in new_prop_values:
                newsym.get_property(p).value = new_prop_values[p]
            else:
                # default values
                if p == "Value":
                    # Value is update with new symbol name
                    newsym.get_property(p).value = name
                elif p == "Reference":
                    # Reference is likely the same (same library) -> preserved
                    pass
                else:
                    newsym.get_property(p).value = ""

        return newsym

    def _calculate_hash(self) -> str:
        """
        Calculate sha256 hash of the symbol sexpr. It is for internal use.
        """
        return hashlib.sha256(str(self.get_sexpr()).encode("utf-8")).hexdigest()


@dataclass
class KicadLibrary(KicadSymbolBase):
    """
    A class to parse kicad_sym files format of the KiCad
    """

    filename: str | Path
    symbols: list[KicadSymbol] = field(default_factory=list)
    generator: str = "kicad-library-utils"
    version: str = "20251024"

    imported_generator: str = ""
    imported_generator_version: str = ""

    def __post_init__(self):
        self.filename = Path(self.filename)

        if self.filename.suffix not in [".kicad_sym", ".kicad_symdir"]:
            raise ValueError(
                "library filename should end with .kicad_sym or .kicad_symdir"
            )

    def write(self, write_modified_only: bool = True):
        """
        Write a library to disk as a single file .kicad_sym or .kicad_symdir format. This function is
        meant to blindly overwrite the library.

        By default a library is written only when symbols are changed. If the format is .kicad_sym, a change in
        a single symbol causes the full rewrite of the library. With the .kicad_symdir format, symbols are
        selectively saved only when changed since loading time. This is useful when modifying a symbol of an
        .kicad_symdir library to reduce amount of git changes. It is possible to force writing of all symbols by
        setting write_modified_only to False.
        """
        if self.filename.suffix == ".kicad_sym":
            if write_modified_only:
                is_modified = False
                for s in self.symbols:
                    if s.digest != s._calculate_hash():
                        is_modified = True
                        break
            else:
                is_modified = True

            if is_modified:
                for s in self.symbols:
                    s.digest = s._calculate_hash()

                with open(
                    self.filename, "w", encoding="utf-8", newline="\n"
                ) as lib_file:
                    lib_file.write(self.get_sexpr() + "\n")
        elif self.filename.suffix == ".kicad_symdir":
            if not self.filename.exists():
                self.filename.mkdir(parents=True)

            for s in self.symbols:
                # write only when modified or explicitly asked for
                h = s._calculate_hash()
                if not write_modified_only or s.digest != h:
                    s.digest = h
                    with open(
                        s.filename, "w", encoding="utf-8", newline="\n"
                    ) as lib_file:
                        lib_file.write(self.get_sexpr(s.name) + "\n")
        else:
            raise Exception(f"unsupported library name {self.filename}")

    def write_as_file(self, libfile: str | Path, overwrite: bool = False):
        """
        Write a library to disk using single file format .kicad_sym, this method is meant
        to be used to save to a different libfile than the one used to load the library.

        It is an helper function on top of write() and is useful to convert format from a directory.
        The symbols are updated accordingly to reflect the new layout.
        """

        libfile = Path(libfile)

        if libfile == self.filename:
            raise Exception("Please use write() to write to the same libfile")

        if not libfile.suffix == ".kicad_sym":
            raise Exception(
                f"Trying to save library as a single file but filename {libfile} doesn't end with .kicad_sym"
            )

        if libfile.exists():
            if libfile.is_dir():
                # this should never happen
                raise Exception(
                    f"Trying to save library as a single file but filename {libfile} is already present as a dir"
                )
            elif libfile.is_file():
                if not overwrite:
                    raise Exception(
                        f"Trying to save library {libfile} but found an old file with the same name, overwrite if you are sure"
                    )

        self.filename = libfile
        for s in self.symbols:
            s.libname = libfile.stem
            s.filename = libfile

        self.write(write_modified_only=False)

    def write_as_dir(self, libdir: str | Path, overwrite: bool = False):
        """
        Write a library to disk using directory format .kicad_symdir, this method is meant
        to be used to save to a different libdir than the one used to load the library.

        It is an helper function on top of write() and is useful to convert format from a single library file.
        The symbols are updated accordingly to reflect the new layout.
        """
        libdir = Path(libdir)

        if libdir == self.filename:
            raise Exception("Please use write() to write to the same libdir")

        if not libdir.suffix == ".kicad_symdir":
            raise Exception(
                f"Trying to save library as dir format but filename {libdir} doesn't end with .kicad_symdir"
            )

        if libdir.exists():
            if libdir.is_file():
                # this should never happen
                raise Exception(
                    f"Trying to save library as dir format but filename {libdir} is already present as a file"
                )
            elif libdir.is_dir():
                if not overwrite:
                    raise Exception(
                        f"Trying to save library {libdir} but found an old folder with the same name, overwrite if you are sure"
                    )

                # delete to avoid mixing of symbols from two libraries
                shutil.rmtree(libdir)
        libdir.mkdir(parents=True)

        self.filename = libdir
        for s in self.symbols:
            s.libname = libdir.stem
            s.filename = libdir / Path(f"{s.name}.kicad_sym")

        self.write(write_modified_only=False)

    def get_sexpr(self, sym_name: str = "") -> str:
        sx = [
            "kicad_symbol_lib",
            ["version", self.version],
            ["generator", self.quoted_string(self.generator)],
            ["generator_version", self.quoted_string(self.version)],
        ]

        if sym_name:
            sym_list = [self.get_symbol(sym_name)]
            if not sym_list[0]:
                raise Exception(
                    f"Asked sexpr of the symbol {sym_name} which doesn't exist"
                )
        else:
            sym_list = self.symbols

        for sym in sym_list:
            sx.append(sym.get_sexpr())
        return sexpr.build_sexp(sx)

    def check_extends_order(self):
        """
        Check if every parent symbol exists & appears before every
        child symbol that extends it.

        Raises:
            KicadFileFormatError: If a parent symbol does not exist
                or appears after a child symbol that extends it.
        """
        already_seen = set()
        for symbol in self.symbols:
            name = symbol.name
            parent = symbol.extends
            if parent and parent not in already_seen:
                raise KicadFileFormatError(
                    f"Parent symbol {parent} of {name} not found"
                )
            already_seen.add(symbol.name)

    @classmethod
    def from_path(cls, filename: str | Path, data=None) -> "KicadLibrary":
        filename = Path(filename)
        if filename.is_dir():
            return KicadLibrary.from_dir(filename)
        else:
            return KicadLibrary.from_file(filename)

    @classmethod
    def from_dir(cls, dirname: str | Path, data=None) -> "KicadLibrary":
        """
        Parse a symbol library from a kicad_symdir directory

        raises KicadFileFormatError in case of problems
        """

        dirname = Path(dirname)
        if not dirname.is_dir():
            raise NotADirectoryError(f'The library "{dirname}" is not a directory')

        # create a empty library
        # we kinda would need to set version and generator, but that is
        # not simple, because they could differ in the sub-files in that kicad_symdir
        library = KicadLibrary(dirname)

        # for tracking derived symbols we need another dict
        # (this is code-duplication from the from_file method)
        symbol_names = {}

        # iterate over all .kicad_sym files in the directory
        for sub_lib_filename in sorted(dirname.glob("*.kicad_sym")):
            # read the sub library
            sub_library = KicadLibrary.from_file(
                sub_lib_filename, check_inheritance=False
            )
            if len(sub_library.symbols) > 1:
                raise KicadFileFormatError(
                    f"Found more than one symbols in: {sub_lib_filename}"
                )

            # fetch the first symbol from the sub-library
            # overwrite the libname with the name from the directory
            symbol = sub_library.symbols[0]
            symbol.libname = dirname.stem

            # fill the symbol_names dict we need for inheritance checking laters
            if symbol.name in symbol_names:
                raise KicadFileFormatError(f"Duplicate symbols: {symbol.name}")
            symbol_names[symbol.name] = symbol

            # add this single symbol to our library
            library.symbols.append(symbol)

        # do some inheritance sanity checks (duplicated from from_file function)
        for symbol in library.symbols:
            cursor = symbol
            while cursor.extends:
                if symbol.name == symbol.extends:
                    raise KicadFileFormatError(f"Symbol {symbol.name} extends itself")

                if symbol.extends in symbol._inheritance:
                    raise KicadFileFormatError(
                        f"Symbol {symbol.name} has a circular inheritance"
                    )

                parent_sym = symbol_names.get(cursor.extends)
                if parent_sym is None:
                    raise KicadFileFormatError(
                        f"Symbol {symbol.name} is extended to a part not in the library"
                    )

                symbol._inheritance.append(parent_sym)
                cursor = parent_sym

        return library

    @classmethod
    def from_file(
        cls, filename: str | Path, data=None, check_inheritance=True
    ) -> "KicadLibrary":
        """
        Parse a symbol library from a file.

        raises KicadFileFormatError in case of problems
        """

        filename = Path(filename)

        # Check if library exists and set the empty library if not
        if not filename.is_file():
            raise FileNotFoundError(f'The library "{filename}" is not a file')

        library = KicadLibrary(filename)

        # read the s-expression data
        try:
            if data:
                sexpr_data = sexpr.parse_sexp(data)
            else:
                with open(filename, encoding="utf8") as f:
                    # parse s-expr
                    sexpr_data = sexpr.parse_sexp(f.read())
        except ValueError as exc:
            if data:
                raise KicadFileFormatError(
                    f"Problem while parsing the s-expr from data {data}: {exc}"
                ) from None
            else:
                raise KicadFileFormatError(
                    f"Problem while parsing the s-expr in file {filename}: {exc}"
                ) from None

        # Because of the various file format changes in the development of kicad v6 and v7, we want
        # to ensure that this parser is only used with v6 files. Any other version will most likely
        # not work as expected. So just don't load them at all.
        version = _get_value_of(sexpr_data, "version")
        if str(version) != KicadLibrary.version:
            raise KicadFileFormatError(
                f'Version of symbol file is "{version}", not "{KicadLibrary.version}"'
            )
        library.imported_generator = _get_value_of(sexpr_data, "generator")
        library.imported_generator_version = _get_value_of(
            sexpr_data, "generator_version"
        )

        # for tracking derived symbols we need another dict
        symbol_names = {}

        # itertate over symbols
        sym_list = _get_array(sexpr_data, "symbol", max_level=2)
        for item in sym_list:
            item_type = item.pop(0)
            if item_type != "symbol":
                raise KicadFileFormatError(f"Unexpected token found: {item_type}")
            # retrieving the `partname`, even if formatted as `libname:partname` (legacy format)
            partname = str(item.pop(0).split(":")[-1])

            # we found a new part, extract the symbol name
            symbol = KicadSymbol(partname, libname=str(filename), filename=filename)

            # build a dict of symbolname -> symbol
            if partname in symbol_names:
                raise KicadFileFormatError(f"Duplicate symbols: {partname}")
            symbol_names[partname] = symbol

            # extract extends field
            extends = _get_array2(item, "extends")
            if extends:
                symbol.extends = extends[0][1]
            else:
                # Extract body_styles field, it is not always present and contains a list of style names.
                # After parsing, the body_styles member will be a list that always contains:
                # - a "standard" element as first and only entry if 1 style is present,
                #   in datafile: body_styles not present
                # - "standard" and "demorgan" elements for 2 styles where the second is DeMorgan style,
                #   in datafile: (body_styles demorgan)
                # - the style names saved in the datafile (generic case since kicad 10),
                #   in datafile: (body_styles "name1" "name2" ...)
                bs = _get_array2(item, "body_styles")
                if bs:
                    if bs[0][1] == "demorgan":
                        symbol.body_styles = ["standard", "demorgan"]
                    else:
                        symbol.body_styles.extend(bs[0][1:])
                else:
                    symbol.body_styles = ["standard"]
                symbol.body_style_count = len(symbol.body_styles)

            # extract properties
            for prop in _get_array(item, "property"):
                try:
                    # TODO: do not append the new property, if it is None
                    symbol.properties.append(Property.from_sexpr(prop))
                except ValueError as exc:
                    raise KicadFileFormatError(
                        f"Failed to import '{partname}': {exc}"
                    ) from exc

            # get embedded files
            files_array = _get_array(item, "embedded_files")
            if files_array:
                for file in _get_array(files_array[0], "file"):
                    symbol.files.append(KicadEmbeddedFile.from_sexpr(file))

            # get flags
            symbol.exclude_from_sim = (
                _get_value_of(item, "exclude_from_sim", "no") == "yes"
            )
            symbol.in_bom = _get_value_of(item, "in_bom", "no") == "yes"
            symbol.on_board = _get_value_of(item, "on_board", "no") == "yes"
            if _has_value(item, "power"):
                symbol.is_power = True
            symbol.embedded_fonts = _get_value_of(item, "embedded_fonts", "no") == "yes"

            # get pin-numbers properties
            pin_numbers_info = _get_array2(item, "pin_numbers")
            if pin_numbers_info:
                symbol.hide_pin_numbers = (
                    _get_value_of(pin_numbers_info[0], "hide", "no") == "yes"
                )

            # get pin-name properties
            pin_names_info = _get_array2(item, "pin_names")
            if pin_names_info:
                symbol.hide_pin_names = (
                    _get_value_of(pin_names_info[0], "hide", "no") == "yes"
                )
                # sometimes the pin_name_offset value does not exist, then use 20mil as default
                symbol.pin_names_offset = _get_value_of(
                    pin_names_info[0], "offset", 0.508
                )

            # get the actual geometry information
            # it is split over units
            subsymbols = _get_array2(item, "symbol")
            for unit_data in subsymbols:
                # we found a new 'subpart' (no clue how to call it properly)
                subpart_type = unit_data.pop(0)
                if subpart_type != "symbol":
                    raise KicadFileFormatError(
                        f"Unexpected token found as 'subsymbol' of {item_type}: {subpart_type}"
                    )
                name = unit_data.pop(0)

                # split the name
                m1 = re.match(r"^" + re.escape(partname) + r"_(\d+?)_(\d+?)$", name)
                if not m1:
                    raise KicadFileFormatError(
                        f"Failed to parse subsymbol due to invalid name: {name}"
                    )

                unit_idx, body_style_idx = (m1.group(1), m1.group(2))
                unit_idx = int(unit_idx)
                body_style_idx = int(body_style_idx)

                # update the amount of units, alternative-styles
                # kicad 10 introduced support for multi style units, previously demorgan was
                # the only admitted second style name
                symbol.unit_count = max(unit_idx, symbol.unit_count)
                symbol.body_style_count = max(body_style_idx, symbol.body_style_count)

                unit_name = _get_array2(unit_data, "unit_name")
                if unit_name:
                    symbol.unit_names[unit_idx] = unit_name[0][1]

                # extract pins and graphical items
                for pin in _get_array(unit_data, "pin"):
                    try:
                        symbol.pins.append(
                            Pin.from_sexpr(pin, unit_idx, body_style_idx)
                        )
                    except ValueError as valexc:
                        raise KicadFileFormatError(
                            f"Failed to parse symbol {partname}: {valexc}"
                        ) from None
                for circle in _get_array(unit_data, "circle"):
                    symbol.circles.append(
                        Circle.from_sexpr(circle, unit_idx, body_style_idx)
                    )
                for arc in _get_array(unit_data, "arc"):
                    symbol.arcs.append(Arc.from_sexpr(arc, unit_idx, body_style_idx))
                for rect in _get_array(unit_data, "rectangle"):
                    # symbol.polylines.append(
                    #     Rectangle.from_sexpr(rect, unit, demorgan).as_polyline()
                    # )
                    symbol.rectangles.append(
                        Rectangle.from_sexpr(rect, unit_idx, body_style_idx)
                    )
                for poly in _get_array(unit_data, "polyline"):
                    symbol.polylines.append(
                        Polyline.from_sexpr(poly, unit_idx, body_style_idx)
                    )
                for bezier in _get_array(unit_data, "bezier"):
                    symbol.beziers.append(
                        Bezier.from_sexpr(bezier, unit_idx, body_style_idx)
                    )
                for text in _get_array(unit_data, "text"):
                    symbol.texts.append(Text.from_sexpr(text, unit_idx, body_style_idx))

            # integrity check, only for base not derived symbols
            if subsymbols and len(symbol.body_styles) != symbol.body_style_count:
                raise KicadFileFormatError(
                    f"The amount of body styles found for symbol {symbol.name} does not match the metadata: there are {symbol.body_style_count} different styles, but the list of body styles has {len(symbol.body_styles)} entries."
                )

            symbol.digest = symbol._calculate_hash()

            # add it to the list of symbols
            library.symbols.append(symbol)

        # do some inheritance sanity checks
        if check_inheritance:
            for symbol in library.symbols[:]:
                cursor = symbol
                while cursor.extends:
                    if symbol.name == symbol.extends:
                        raise KicadFileFormatError(
                            f"Symbol {symbol.name} extends itself"
                        )

                    if symbol.extends in symbol._inheritance:
                        raise KicadFileFormatError(
                            f"Symbol {symbol.name} has a circular inheritance"
                        )

                    # If a single file from a `kicad_symdir` is loaded, that means that we don't load the parent of a
                    # derived symbol. So we need to guess its filename based on the parent name and load it as well.
                    if cursor.extends not in symbol_names:
                        parent_filename = (
                            library.filename.parent / f"{cursor.extends}.kicad_sym"
                        )
                        try:
                            parent_lib = KicadLibrary.from_file(parent_filename)
                        except FileNotFoundError:
                            raise KicadFileFormatError(
                                f"Could not open parent-library {parent_filename} while trying to load {symbol.name}"
                            )
                        for extra_sym in parent_lib.symbols:
                            if (
                                symbol_names.setdefault(extra_sym.name, extra_sym)
                                is not extra_sym
                            ):
                                raise KicadFileFormatError(
                                    f"Duplicate symbol while trying to load parent symbol: {extra_sym.name}"
                                )
                            if extra_sym.name == cursor.extends:
                                library.symbols.append(extra_sym)

                    parent_sym = symbol_names.get(cursor.extends)
                    if not parent_sym:
                        raise KicadFileFormatError(
                            f"Parent {cursor.extends} of symbol {symbol.name} not found"
                        )

                    symbol._inheritance.append(parent_sym)
                    cursor = parent_sym

        return library

    def get_symbol(self, name: str) -> KicadSymbol | None:
        """
        Get the symbol with the given name in the library, or None if not found.
        """
        for symbol in self.symbols:
            if symbol.name == name:
                return symbol
        return None

    def add_derived_symbol(
        self,
        base_name: str,
        derived_name: str,
        overwrite: bool = False,
        allow_recursive_inheritance: bool = False,
    ):
        """
        Add a new derived symbol derived_name starting from base_name.

        It is possible to overwrite an already present symbol or allow recursive derivation
        (inheritance).
        """
        basesym = None
        idx_to_remove = None
        for idx in range(0, len(self.symbols)):
            s = self.symbols[idx]
            if derived_name == s.name:
                if not overwrite:
                    raise ValueError(
                        f"a symbol {derived_name} already exists, overwrite if sure"
                    )
                else:
                    idx_to_remove = idx
            if base_name == s.name:
                basesym = s
        if not basesym:
            raise ValueError(
                f"a symbol {base_name} doesn't exist, cannot use it as base symbol"
            )
        if basesym.extends and not allow_recursive_inheritance:
            raise Exception(
                "derivation of a derived symbol is technically feasible but discouraged"
            )
        # overwrite symbol
        if idx_to_remove:
            self.symbols.pop(idx_to_remove)

        newsym = basesym.derive(derived_name)

        parent = self.get_symbol(newsym.extends)
        while parent.extends:
            parent = self.get_symbol(parent.extends)
            newsym._inheritance.append(parent)

        self.symbols.append(newsym)


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        a = KicadLibrary.from_file(sys.argv[1])
        a.generator = "kicad_symbol_editor"
        print(a.get_sexpr())
    else:
        print("pass a .kicad_sym file please")
