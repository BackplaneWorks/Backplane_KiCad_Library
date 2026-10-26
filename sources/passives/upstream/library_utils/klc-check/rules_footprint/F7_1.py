from kicad_mod import KicadMod
from rules_footprint.rule import KLCRule


class Rule(KLCRule):
    """For through-hole devices, placement type must be set to "Through Hole" """

    def __init__(self, component: KicadMod, args):
        super().__init__(component, args)

        self.pth_count: int = 0
        self.smd_count: int = 0

    def check(self) -> bool:
        """
        Proceeds the checking of the rule.
        The following variables will be accessible after checking:
            * pth_count
            * smd_count
        """

        module = self.module

        self.pth_count = len(module.filterPads("thru_hole"))
        self.smd_count = len(module.filterPads("smd"))

        error = False

        # If the part is a THT part, it should have THT pads
        # and should not be excluded from the BOM or position files
        if module.footprint_type == "through_hole":
            if self.pth_count == 0:
                self.error("Through hole footprint type is set, but no THT pads found")
                error = True

            if module.exclude_from_bom:
                self.error("Through hole footprints should not be excluded from BOM")
                self.errorExtra(
                    "If this part isn't physically fitted, perhaps this"
                    ' footprint should be of "unspecified" type.'
                )
                error = True

            if module.exclude_from_pos_files:
                self.error(
                    "Through hole footprints should not be excluded from"
                    " position files"
                )
                self.errorExtra(
                    "If this part isn't physically fitted, perhaps this"
                    ' footprint should be of "unspecified" type.'
                )
                error = True

        if self.pth_count > 0 and module.footprint_type != "through_hole":
            if module.exclude_from_bom or module.exclude_from_pos_files:
                # This is a warning for THT (but an error for the SMD counterpart)
                # because we don't have a paste layer to check for greater confidence.
                self.warning(
                    "Footprint is excluded from BOM or position files, "
                    " but has plated THT pads"
                )
                self.warningExtra("Ensure this is correct.")

            # Non-virtual and only THT pads
            elif self.smd_count == 0:
                self.error("Through Hole attribute not set")
                self.errorExtra(
                    "For THT footprints, 'Placement type' must be set to 'Through hole'"
                )
                error = True
            # A mix of THT and SMD pads - probably a SMD footprint (e.g. hybrid)

        return error

    def fix(self) -> None:
        """
        Proceeds the fixing of the rule, if possible.
        """

        module = self.module
        if self.check():
            self.info("Setting placement type to 'Through hole'")
            module.footprint_type = "through_hole"
