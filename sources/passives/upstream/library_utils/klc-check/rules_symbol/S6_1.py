from rules_symbol.rule import KLCRule

RD_Map = [
    ("Y", ["Oscillator"]),
    ("U", ["CI_Test_S6.x"]),
]
AllowedDesignators = [
    "A",
    "AE",
    "BT",
    "C",
    "D",
    "DS",
    "F",
    "FB",
    "FB",
    "FD",
    "FL",
    "H",
    "J",
    "JP",
    "K",
    "L",
    "LS",
    "M",
    "MK",
    "P",
    "Q",
    "R",
    "RN",
    "RT",
    "RV",
    "SW",
    "T",
    "TC",
    "TJ",
    "TP",
    "U",
    "Y",
    "Z",
]


class Rule(KLCRule):
    """Correct reference designators should be used"""

    def checkRD(self) -> bool:
        fail = False
        ref = self.component.get_property("Reference")
        if not ref:
            self.error("Component is missing Reference field")
            # can not do other checks, return
            return True

        for entry in RD_Map:
            if self.component.libname in entry[1]:
                if not ref.value.startswith(entry[0]):
                    self.error(
                        f"Library {self.component.libname} should have {entry[0]} as RD prefix"
                    )
                    fail = True

        return fail

    def checkReferenceValue(self) -> bool:
        ref = self.component.get_property("Reference")
        if ref.value not in AllowedDesignators:
            self.error(
                "Component Reference designator not in list of allowed designators"
            )
            return True
        return False

    def check(self) -> bool:

        return any([self.checkRD(), self.checkReferenceValue()])

    def fix(self) -> None:
        """
        Proceeds the fixing of the rule, if possible.
        """
        self.info("not supported")
        self.recheck()
