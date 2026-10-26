# math and comments from Michal script
# https://github.com/michal777/KiCad_Lib_Check

from typing import Any, Dict, List

from geometry import Point, Seg2D
from kicad_mod import KicadMod
from rules_footprint.rule import KLCRule, graphItemString


class Rule(KLCRule):
    """Elements on the graphic layer should not overlap"""

    def __init__(self, component: KicadMod, args):
        super().__init__(component, args)

        self.overlaps: Dict[str, List[Any]] = {}
        self.errcnt: int = 0

    def getCirclesOverlap(self, circles) -> List[Any]:
        def is_same(c1, c2) -> bool:
            if c1["end"] == c2["end"] and c1["center"] == c2["center"]:
                return True
            return False

        overlap = []
        for c in circles:
            for c2 in circles:
                if c is c2:
                    continue
                if is_same(c, c2):
                    if c not in overlap:
                        overlap.append((c, c2))

        return overlap

    def getLinesOverlap(self, lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        overlap = []
        directions = {}

        # sort lines by colinearity
        for line in lines:
            seg = Seg2D(
                Point(line["start"]["x"], line["start"]["y"]),
                Point(line["end"]["x"], line["end"]["y"]),
            )

            dx = seg.start.x - seg.end.x
            dy = seg.start.y - seg.end.y

            if dx == 0:
                d = "h"
            elif dy == 0:
                d = "v"
            else:
                d = round(dx / dy, 3)

            if d not in directions:
                directions[d] = []
            directions[d].append((seg, line))

        for d, segs in directions.items():

            for ii in range(len(segs)):
                for jj in range(ii + 1, len(segs)):
                    seg, orig_line = segs[ii]
                    seg2, orig_line2 = segs[jj]

                    if seg.overlaps(seg2):
                        if orig_line not in overlap:
                            overlap.append((orig_line, orig_line2))

        return overlap

    def check(self) -> bool:
        """
        Proceeds the checking of the rule.
        The following variables will be accessible after checking:
            * overlaps
            * errcnt
        """

        module = self.module
        layers_to_check = ["F.Fab", "B.Fab", "F.SilkS", "B.SilkS", "F.CrtYd", "B.CrtYd"]

        self.overlaps = {}
        self.errcnt = 0
        for layer in layers_to_check:
            self.overlaps[layer] = []
            self.overlaps[layer].extend(self.getLinesOverlap(module.filterLines(layer)))
            self.overlaps[layer].extend(
                self.getCirclesOverlap(module.filterCircles(layer))
            )

            # Display message if silkscreen has overlapping lines
            if self.overlaps[layer]:
                self.errcnt += 1
                self.error("%s graphic elements should not overlap." % layer)
                self.errorExtra(
                    "The following elements overlap at least one other graphic"
                    " element on layer %s:" % layer
                )
                for bad, bad2 in self.overlaps[layer]:
                    self.errorExtra(
                        graphItemString(bad, layer=False, width=False)
                        + " with "
                        + graphItemString(bad2, layer=False, width=False)
                    )

        return self.errcnt > 0

    def fix(self) -> None:
        """
        Proceeds the fixing of the rule, if possible.
        """

        return
