from rules_symbol.rule import KLCRule


class Rule(KLCRule):
    """All text should use the default KiCad stroke font."""

    def check(self) -> bool:
        # Font is set in the TextEffects.font property
        # Those exist in the following elements
        # Property.effects
        # Pin.name_effects, Pin.number_effect -> currently KiCad9 has no option to set fonts for those

        for pin in self.component.pins:
            # no need to check them, we cannot
            # pin.name_effect
            # pin.number_effect
            pass

        for prop in self.component.properties:
            if prop.effects.face is not None:
                self.error(f"Property uses font {prop.effects.face}")
                self.errorExtra(
                    f'Text item "{prop.name}" with value "{prop.value}" at ({prop.posx}, {prop.posy})'
                )

        for text_item in self.component.texts:
            if text_item.effects.face is not None:
                self.error(f"Text uses font {text_item.effects.face}")
                self.errorExtra(
                    f'Text item "{text_item.text}" at ({text_item.posx}, {text_item.posy})'
                )

        return self.hasErrors

    def fix(self) -> None:
        self.recheck()
