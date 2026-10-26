from rules_footprint.rule import KLCRule


class Rule(KLCRule):
    """All text should use the default KiCad stroke font."""

    def check(self) -> bool:
        for text in self.module.userText:
            if text["font"]["face"] is not None:
                self.error(f"Text uses non kicad font {text['font']['face']}")
                self.errorExtra(
                    f"Text item \"{text['user']}\" on layer {text['layer']} at ({text['pos']['x']}, {text['pos']['y']})"
                )

        if self.module.reference["font"]["face"] is not None:
            self.error(
                f"Reference field uses non kicad font {self.module.reference['font']['face']}"
            )
        if self.module.value["font"]["face"] is not None:
            self.error(
                f"Value field uses non kicad font {self.module.value['font']['face']}"
            )

        return False

    def fix(self) -> None:
        """
        Proceeds the fixing of the rule, if possible.
        """

        self.info("Fixing not supported")
