from OCP.Quantity import Quantity_Color, Quantity_TOC_sRGB

"""
This modules exists because there is a mismatch in the handling of colors
between versions of OpenCasCade. CadQuery uses version 7.5+, which expects
sRGB to be used for export and import of STEP files. Earlier versions used
linear RGB, so when the STEP file is exchanged between versions the gamma
shift is applied incorrectly. Once the versions of OCCT between KiCAD and
CadQuery sync up, there will be no need for this extra code anymore, and a
find-replace can be done on the codebase to convert "cq_color_correct.Color"
to simply "cq.Color".
"""


class Color(object):
    """
    Wrapper for the OCCT color object Quantity_Color.
    """

    wrapped: Quantity_Color

    def __init__(self, *args, **kwargs):
        """
        Construct a Color from RGB(A) values. Alpha is ignored here.

        :param r: red value, 0-1
        :param g: green value, 0-1
        :param b: blue value, 0-1
        :param a: alpha value, 0-1 (default: 0)
        """

        if len(args) == 3:
            r, g, b = args
            self.wrapped = Quantity_Color(r, g, b, Quantity_TOC_sRGB)
        elif len(args) == 4:
            r, g, b, a = args
            self.wrapped = Quantity_Color(r, g, b, Quantity_TOC_sRGB)
        else:
            raise ValueError(f"Unsupported arguments: {args}, {kwargs}")

    def toTuple(self):
        """
        Convert Color to RGB tuple.
        """
        a = 1

        return (self.wrapped.Red(), self.wrapped.Green(), self.wrapped.Blue(), a)
