from kicad_mod import KicadMod
from rules_footprint.rule import KLCRule


class Rule(KLCRule):
    """For surface-mount devices, placement type must be set to "Surface Mount" """

    def __init__(self, component: KicadMod, args):
        super().__init__(component, args)

        self.pth_count: int = 0
        self.smd_count: int = 0
        self.smd_paste_pad_count: int = 0

    def check(self) -> bool:
        """
        Proceeds the checking of the rule.
        The following variables will be accessible after checking:
            * pth_count
            * smd_count
            * paste_pad_count
        """
        module = self.module

        self.pth_count = len(module.filterPads("thru_hole"))

        smd_pads = module.filterPads("smd")
        self.smd_count = len(smd_pads)

        self.smd_paste_pad_count = 0
        for smd_pad in smd_pads:
            if "F.Paste" in smd_pad["layers"] or "B.Paste" in smd_pad["layers"]:
                self.smd_paste_pad_count += 1

        error = False

        # If the part is a SMD part, it should have soldered SMD pads
        # and should not be excluded from the BOM or position files
        if module.footprint_type == "smd":
            if self.smd_paste_pad_count == 0:
                self.error("SMD footprint type is set, but no soldered SMD pads found")
                error = True

            if module.exclude_from_bom:
                self.error("SMD footprints should not be excluded from BOM")
                self.errorExtra(
                    "If this part isn't physically fitted, perhaps this"
                    ' footprint should be of "unspecified" type.'
                )
                error = True

            if module.exclude_from_pos_files:
                self.error("SMD footprints should not be excluded from position files")
                self.errorExtra(
                    "If this part isn't physically fitted, perhaps this"
                    ' footprint should be of "unspecified" type.'
                )
                error = True

        # Check if there are SMD pads with paste - in some cases, this could be
        # a footprint that should have the 'SMD' type set.
        if module.footprint_type != "smd" and self.smd_paste_pad_count > 0:

            # If the footprint has soldered SMD pads, it should probably not be
            # excluded from the BOM or position files
            if module.exclude_from_bom or module.exclude_from_pos_files:
                self.error(
                    "Footprint is excluded from BOM or position files, "
                    f" but has soldered SMD pads and is of type {module.footprint_type}"
                )
                self.errorExtra(
                    "This indicates a fitted part, in which case"
                    " the type should be 'SMD'"
                )
                error = True

            if self.pth_count == 0:
                self.error("SMD footprint type not set")
                self.errorExtra(
                    "For SMD footprints, footprint type must be set to 'SMD'"
                )
                self.errorExtra(
                    f"There are {self.smd_paste_pad_count} soldered SMD pads"
                )
                error = True
            else:
                self.warning("'SMD' footprint type not set")
                self.warningExtra(
                    "Both THT and soldered SMD pads were found, which might be"
                    " a hybrid (a.k.a. pin-in-paste) footprint"
                )
                self.warningExtra(
                    "Suggest setting footprint type to 'SMD' rather than "
                    f" '{module.footprint_type}'"
                )

        return error

    def fix(self) -> None:
        """
        Proceeds the fixing of the rule, if possible.
        """
        module = self.module
        if self.check():
            self.info("Set 'surface mount' attribute")
            module.footprint_type = "smd"
