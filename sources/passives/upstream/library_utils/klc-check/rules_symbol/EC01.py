# -*- coding: utf-8 -*-
import math

import geometry
from kicad_sym import Bezier, Polyline
from rules_symbol.rule import KLCRule


class Rule(KLCRule):
    """Basic geometry checks"""

    # set thresholds for tested angle
    verySmallAngle = math.radians(0.4)

    smallLength = 0.1  # in mm, about 4 thou

    def _check_degenerate_arcs(self) -> None:
        for arc in self.component.arcs:
            d_start_mid = arc.start.distance_to(arc.midpoint)
            d_end_mid = arc.end.distance_to(arc.midpoint)
            d_start_end = arc.start.distance_to(arc.end)

            if d_start_mid < self.smallLength or d_end_mid < self.smallLength:
                self.warning(
                    f"Arc has zero or near-zero size: start {arc.start}, mid {arc.end}, end {arc.end}"
                )
            elif d_start_end < self.smallLength:
                self.warning(
                    f"Arc starts and ends in the same, or nearly the same, place ({arc.start}): is it a circle?"
                )

    def _check_degenerate_polylines(self) -> None:
        for polyline in self.component.polylines:
            n_points = len(polyline.points)
            segment_i = 0
            if n_points == 0:
                self.warning("Polyline contains no points")
            elif n_points == 1:
                self.warning(
                    f"Polyline contains only a single point: {polyline.points[0]}"
                )
            else:
                # do segment-by-segment checks
                for seg in polyline.get_segs():
                    if seg.length < self.smallLength:
                        self.warning(
                            f"Polyline contains a zero or near-zero length segment "
                            f"(segment {segment_i + 1} of {n_points - 1}): "
                            f" {seg}, length {seg.length:04f}"
                        )

                    theta = seg.angle
                    theta_deviation = math.radians(45) - abs(
                        math.radians(45) - (theta % math.radians(90))
                    )

                    if theta_deviation > 0 and theta_deviation < self.verySmallAngle:
                        degrees = math.degrees(theta)
                        self.warning(
                            "Polyline contains a segment that is nearly, but not exactly, horizontal or vertical "
                            f"(segment {segment_i + 1} of {n_points - 1}): "
                            f"segment {seg} is {degrees:04f} degrees"
                        )

                    segment_i += 1

    def _check_nearly_closed_polylines(self):
        for polyline in self.component.polylines:
            n_points = len(polyline.points)
            # can't close a single segment
            if n_points < 3:
                continue

            first_point = polyline.points[0].pt
            last_point = polyline.points[-1].pt

            if (
                self._points_almost_equal(first_point, last_point)
                and first_point != last_point
            ):
                self.warning(
                    f"Polyline with {n_points} points nearly, but not quite, closed: "
                    f"start is {first_point}, end is {last_point}"
                )

    def _check_degenerate_texts(self) -> None:
        for text in self.component.texts:
            if len(text.text) == 0:
                self.warning(f"Text at {text.pos} has no content")

    def _lengths_almost_equal(self, l1, l2) -> bool:
        return abs(l2 - l1) < self.smallLength

    def _points_almost_equal(self, p1, p2) -> bool:
        return p1.distance_to(p2) < self.smallLength

    def _check_duplicate_segments(self) -> None:
        def _segs_almost_equal(s1, s2) -> bool:
            return (
                s1.start.distance_to(s2.start) < self.smallLength
                and s1.end.distance_to(s2.end) < self.smallLength
            )

        def _polylines_comparable_for_overlap(p1: Polyline, p2: Polyline) -> bool:
            """
            Check if two polylines are "comparable" - that is, a segment in one
            overlapping with a segment in the other is a problem.
            """

            # first, if one is filled and one is not, they're not comparable
            # (one could be the border and another the fill)
            if p1.fill_type != p2.fill_type:
                return False

            # If either is in all units, it could be compparable
            either_is_all_units = p1.unit == 0 or p2.unit == 0

            # They're only comparable if they're in the same unit
            if not either_is_all_units and p1.unit != p2.unit:
                return False

            return True

        all_segs = []
        for polyline in self.component.polylines:
            for seg in polyline.get_segs():
                # order all segs the same way (A->B is the same as B->A for this purpose)
                all_segs.append((seg.lexicographically_ordered(), polyline))

        for i in range(len(all_segs)):
            for j in range(i + 1, len(all_segs)):

                if not _polylines_comparable_for_overlap(
                    all_segs[i][1], all_segs[j][1]
                ):
                    continue

                s1 = all_segs[i][0]
                s2 = all_segs[j][0]
                if _segs_almost_equal(s1, s2):
                    if s1 == s2:
                        self.warning(f"The same segment appears multiple times: {s1}")
                    else:
                        self.warning(f"The segment {s1} is very similar to: {s2}")

    def _check_duplicate_circles(self) -> None:
        def _circles_almost_equal(c1, c2) -> bool:
            return c1.center.pt.distance_to(
                c2.center.pt
            ) < self.smallLength and self._lengths_almost_equal(c1.radius, c2.radius)

        for i in range(len(self.component.circles)):
            for j in range(i + 1, len(self.component.circles)):
                c1 = self.component.circles[i]
                c2 = self.component.circles[j]

                if c1.unit == c2.unit and _circles_almost_equal(c1, c2):
                    if c1 == c2:
                        self.warning(
                            "The same circle appears multiple times: "
                            f"center {c1.center}, radius {c1.radius}"
                        )
                    else:
                        self.warning(
                            "The circle geometry"
                            f"(center {c1.center}, radius {c1.radius}) "
                            "is very similar to: "
                            f"(center {c2.center}, radius {c2.radius})"
                        )

    def _check_duplicate_arcs(self) -> None:
        def _arcs_almost_equal(a1, a2) -> bool:
            # arcs can go either way and they're still the same
            a1_s_e_ordered = sorted(
                (a1.start, a1.end), key=geometry.Point.lexicographic_key
            )
            a2_s_e_ordered = sorted(
                (a2.start, a2.end), key=geometry.Point.lexicographic_key
            )

            return (
                self._points_almost_equal(a1_s_e_ordered[0], a2_s_e_ordered[0])
                and self._points_almost_equal(a1_s_e_ordered[1], a2_s_e_ordered[1])
                and self._points_almost_equal(a1.midpoint, a2.midpoint)
            )

        for i in range(len(self.component.arcs)):
            for j in range(i + 1, len(self.component.arcs)):
                a1 = self.component.arcs[i]
                a2 = self.component.arcs[j]

                if a1.unit == a2.unit and _arcs_almost_equal(a1, a2):
                    if a1 == a2:
                        self.warning(
                            "The same arc geometry exists multiple times: "
                            f"{a1.start}, midpoint {a1.midpoint}, end {a1.end}"
                        )
                    else:
                        self.warning(
                            "The arc geometry "
                            f"({a1.start}, midpoint {a1.midpoint}, end {a1.end}) "
                            "is very similar to "
                            f"({a2.start}, midpoint {a2.midpoint}, end {a2.end})"
                        )

    def _check_duplicate_bezier(self) -> None:

        def _beizer_almost_equal(b1: Bezier, b2: Bezier):
            almost_equal = True
            for b1_pt, b2_pt in zip(b1.points, b2.points):
                b1_pt = geometry.Point(b1_pt.x, b1_pt.y)
                b2_pt = geometry.Point(b2_pt.x, b2_pt.y)
                if b1_pt.distance_to(b2_pt) >= self.smallLength:
                    almost_equal = False
            return almost_equal

        for i in range(len(self.component.beziers)):
            for j in range(i + 1, len(self.component.beziers)):
                b1 = self.component.beziers[i]
                b2 = self.component.beziers[j]

                if b1.unit == b2.unit and _beizer_almost_equal(b1, b2):
                    if b1 == b2:
                        self.warning(
                            "The same beizer geometry exists multiple times: "
                            f"{b1.points}"
                        )
                    else:
                        self.warning(
                            "The bezier geometry "
                            f"{b1.points}"
                            "is very similar to "
                            f"{b2.points}"
                        )

    def _check_duplicate_texts(self) -> None:
        def _texts_almost_equal(t1, t2) -> bool:
            # arcs can go either way and they're still the same
            return (
                self._points_almost_equal(t1.pos, t2.pos)
                and t1.text == t2.text
                and t1.effects == t2.effects
            )

        for i in range(len(self.component.texts)):
            for j in range(i + 1, len(self.component.texts)):
                t1 = self.component.texts[i]
                t2 = self.component.texts[j]

                if t1.unit == t2.unit and _texts_almost_equal(t1, t2):
                    if t1 == t2:
                        self.warning(
                            "The same text exists multiple times: "
                            f"'{t1.text}' at {t1.pos}"
                        )
                    else:
                        self.warning(
                            "The text "
                            f"'{t1.text}' at {t1.pos} "
                            "is very similar to "
                            f"({t2.text}' at {t2.pos}"
                        )

    def check(self):
        """
        Proceeds the checking of the rule.
        """
        self._check_degenerate_arcs()
        self._check_degenerate_polylines()
        self._check_nearly_closed_polylines()
        self._check_degenerate_texts()

        # very small circles are just dots
        # and that's probably OK

        self._check_duplicate_segments()
        self._check_duplicate_circles()
        self._check_duplicate_arcs()
        self._check_duplicate_bezier()
        self._check_duplicate_texts()

        return 0  # There is no KLC rule for this so this check only generates warnings

    def fix(self):
        """
        Proceeds the fixing of the rule, if possible.
        """
        return
