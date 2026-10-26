from typing import Any

from generators.tools.footprint.declarative_def_tools import common_metadata
from generators.tools.spec.base_spec import BaseSpec
from generators.tools.spec.spec_registry import register_spec
from kilibs.geom import Vector2D, Vector3D


@register_spec
class TerminalBlockBarrierProperties(BaseSpec):

    lib_description = "Barrier terminal block"

    def __init__(
        self,
        id: str = "",
        spec: dict[str, Any] = {},
        file_name: str = "",
    ) -> None:
        """Create an instance of `PackageSpec`.

        Args:
            id: The name/identifier of the spec. Typically, this is the name of the key
                of the spec (in the YAML file) or the name of the component.
            spec: The dictionary containing the specification of the component.
            file_name: The name of the YAML file that holds this spec definition.
        """
        super().__init__(id, spec, file_name)

        self.name: str = id

        self.name_template: str = spec["name_template"]
        """ the name of module (template) """

        self.pitch: float = spec["pitch"]
        """ 'pitch' is the distance between 2 pins """

        # Parse pins specification string into a list n_pins
        pins = spec.get("pins", "")
        self.n_pin_variants: list[int] = []
        """ 'pins' is the number of pin spec ( '2-10' or '2-5,20-12' or ''2,10,20' ) """
        pin_specs = str(pins).strip().split(",")
        for pin_spec in pin_specs:
            range_spec = pin_spec.strip().split("-")
            if len(range_spec) == 2:
                start = int(range_spec[0])
                end = int(range_spec[1])
                self.n_pin_variants.extend(list(range(start, end + 1)))
            else:
                self.n_pin_variants.append(int(range_spec[0]))

        self.width: float = spec["width"]
        """ 'width' is the package width (length is pitch*nPin + border ) """
        self.height: float = spec["height"]
        """ 'height' is the package height (not including cover) """

        self.separator: float = spec.get("separator")
        """ 'separator' is the separator thickness """
        self.side_border: float = spec.get("side_border", self.separator)
        """ 'sides_border' is the thickness of the sides (default = separator) """
        self.back_border: float = spec.get("back_border", 0)  # defaut: no back-border
        """ 'top_border' is the width of the top border (default 0) """

        self.pad_size = Vector2D(spec["pad_size"][0], spec["pad_size"][1])
        """ 'pad_size' is the size [x,y] of the pads (first is rectangle, others oval) """
        self.drill_diameter: float = spec["drill"]
        """ 'drill' is the diameter of the pad hole """
        self.pad_to_back: float = spec.get(
            "pad_to_back", self.width / 2
        )  # cosmetic: default is the middle
        """ 'pad_to_back' is the distance of pads from the top of the package     """

        self.metadata = common_metadata.CommonMetadata(spec)
        """ Datasheet URL / Manufacturer name """

        self.screw_offset: float = spec.get(
            "screw_offset", 0
        )  # cosmetic: default center of the terminal "cell"
        """ 'screw_offset' is used to move up/down default screw position (default 0) """

        self.cell_size = Vector3D(
            self.pitch - self.separator,
            self.width - self.back_border,
            spec.get(
                "depth", self.height * 0.6
            ),  # cosmetic: default more than half height
        )
        self.screw_base_size = Vector3D(
            self.cell_size.x * 0.95,
            self.cell_size.x * 0.95,  # square base: same as x
            spec.get("base_height", 1.2),  # cosmetic: usually 1.2mm
        )
        self.screw_diameter: float = self.screw_base_size.x * 0.9

        self.fillet: float = spec.get("fillet", 0.0)
        """ 'fillet' is round of the package """

        clearance = spec.get("clearance", {})  # cosmetic: default no clearance (flat)
        self.clr_bottom: float = clearance.get("bottom", 0)
        """ 'clearance.bottom' is the clearance for each pin (bottom) """
        self.clr_back: float = clearance.get("back", 0)
        """ 'clearance.back' is the clearance for each pin (back) """
        self.clr_front: float = clearance.get("front", 0)
        """ 'clearance.front' is the clearance for each pin (front) """

        cover = spec.get("cover", {})
        self.cover_width: float = cover.get("width", self.width)
        """ 'cover.width' is the cover width """
        self.cover_thickness: float = cover.get("thickness", 0)
        """ 'cover.thickness' is the cover thickness (condition for cover) """
        self.cover_hinge: float = max(
            cover.get("hinge", self.side_border / 2), self.side_border
        )
        """ 'cover.cover_hinge' is the cover hinge thickness """

        pin = spec.get("pin", {})
        self.pin_size = Vector3D(
            pin.get("width"), pin.get("thickness"), pin.get("length")
        )
        """ 'pin: width, thinkness, length' is the pin length (under pcb surface) """

        self.ref_y_position: str | float = spec.get("ref_y_position", "center")

        self.body_color_key: str = spec.get("body_color_key", "black body")
        self.pins_color_key: str = spec.get("pins_color_key", "metal grey pins")
        self.cover_color_key: str = spec.get("cover_color_key", "glass_grey")

    def getFootprintName(self, n_pin: int) -> str:
        return self.name_template.format(
            lib_name=self.lib_name, n_pin=f"{n_pin:02d}", pitch=f"{self.pitch:g}"
        )

    @property
    def lib_name(self):
        return f"TerminalBlock_{self.metadata.manufacturer}"
