from rules_symbol.rule import KLCRule


class Rule(KLCRule):
    """Symbols don't contain embedded files"""

    def check(self) -> bool:
        if self.component.embedded_fonts:
            self.error("The checkbox 'embed fonts' must be unchecked.")
            return True

        if len(self.component.files):
            self.error("No files should be embedded in symbols")
            for fi in self.component.files:
                self.errorExtra(f'Found file "{fi.name}" of type "{fi.ftype}"')
            return True

        return False

    def fix(self) -> None:
        """
        Proceeds the fixing of the rule, if possible.
        """

        self.info("Fixing not supported")
