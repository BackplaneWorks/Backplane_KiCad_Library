from rules_footprint.rule import KLCRule


class Rule(KLCRule):
    """There are no embedded files"""

    def check(self) -> bool:
        if self.module.embedded_fonts != "no":
            self.error("The checkbox 'embedded fonts' must be unchecked.")
            return True

        if len(self.module.files):
            self.error("No files should be embedded in symbols")
            for fi in self.module.files:
                self.errorExtra(f'Found file "{fi["name"]}" of type "{fi["type"]}"')
            return True

        return False

    def fix(self) -> None:
        """
        Proceeds the fixing of the rule, if possible.
        """

        self.info("Fixing not supported")
