from rules_symbol.rule import KLCRule


class Rule(KLCRule):
    """Pins not connected on the footprint may be omitted from the symbol"""

    def checkMissingPins(self) -> bool:
        # builds a map listing all pins under the same prefix
        # i.e {"": [1,2,3], "C": [2,3,6], "AM": [2,3]}
        prefix_pinnr_map = {}
        for pin in self.component.pins:
            try:
                unstacked_pins = pin.unstack() if pin.is_stack() else [pin]
                for p in unstacked_pins:
                    prefix = p.get_pin_number_prefix(p.number)
                    prefixlist = prefix_pinnr_map.setdefault(prefix, [])
                    prefixlist += [int(p.number.removeprefix(prefix))]
            except ValueError:
                pass

        if not prefix_pinnr_map:
            return False

        # check rows for missing pin numbers
        missing_pins = []
        for prefix, pin_number_list in prefix_pinnr_map.items():
            if not pin_number_list:
                # the names of some pins only consist of letters (e.g. "SH");
                # prefix_pinnr_map then stores the whole name as the prefix
                # and maps it to an empty list:
                # {"": [1,2,3], "SH": []}
                # skip over such entries here
                continue
            for pin_number in range(min(pin_number_list), max(pin_number_list) + 1):
                if pin_number not in pin_number_list:
                    missing_pins.append(prefix + str(pin_number))
        if missing_pins:
            self.warning(
                "Pin{s} {n} {v} missing.".format(
                    s="s" if len(missing_pins) > 1 else "",
                    n=", ".join(str(x) for x in missing_pins),
                    v="are" if len(missing_pins) > 1 else "is",
                )
            )
        return False

    def check(self) -> bool:
        # no need to check pins on a derived symbols
        if self.component.extends is not None:
            return False

        return self.checkMissingPins()

    def fix(self) -> None:
        """
        Proceeds the fixing of the rule, if possible.
        """

        self.info("Fix not supported")
