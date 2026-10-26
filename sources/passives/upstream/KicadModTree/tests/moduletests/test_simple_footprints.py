# KicadModTree is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# KicadModTree is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kicad-footprint-generator. If not, see < http://www.gnu.org/licenses/ >.
#
# (C) 2018 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>

from KicadModTree import *
from KicadModTree.tests.test_utils.fp_file_test import SerialisationTest


class TestSimpleFootprints(SerialisationTest):

    def testMinimum(self):
        kicad_mod = Footprint("test", FootprintType.SMD)

        self.assert_serialises_as(kicad_mod, 'footprint_minimal.kicad_mod')

    def testBasicTags(self):
        kicad_mod = Footprint("test", FootprintType.SMD)

        kicad_mod.setDescription("A example footprint")
        kicad_mod.tags = "example"
        kicad_mod.tags += ["example2", "example3"]
        kicad_mod.tags.append("example4")

        self.assert_serialises_as(kicad_mod, 'footprint_basic_tags.kicad_mod')

    def testSampleFootprint(self):
        kicad_mod = Footprint("test", FootprintType.SMD)

        kicad_mod.setDescription("A example footprint")
        kicad_mod.tags = "example"

        kicad_mod.append(Property(name=Property.REFERENCE, text='REF**', at=[0, -3], layer='F.SilkS'))
        kicad_mod.append(Property(name=Property.VALUE, text="test", at=[1.5, 3], layer='F.Fab'))
        kicad_mod.append(Rectangle(start=[-2, -2], end=[5, 2], layer='F.SilkS', fill=False, width=0.12))
        kicad_mod.append(Rectangle(start=[-2.25, -2.25], end=[5.25, 2.25], layer='F.CrtYd', fill=False, width=0.12))
        kicad_mod.append(Pad(number=1, type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT,
                             at=[0, 0], size=[2, 2], drill=1.2, layers=Pad.LAYERS_THT))
        kicad_mod.append(Pad(number=2, type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE,
                             at=[3, 0], size=[2, 2], drill=1.2, layers=Pad.LAYERS_THT))
        kicad_mod.append(Model(filename="example.3dshapes/example_footprint.wrl",
                               at=[0, 0, 0], scale=[1, 1, 1], rotate=[0, 0, 0]))

        self.assert_serialises_as(kicad_mod, 'footprint_simple.kicad_mod')

    def testBasicNodes(self):
        kicad_mod = Footprint("test", FootprintType.SMD)

        kicad_mod.append(Property(name=Property.REFERENCE, text='REF**', at=[0, -3], layer='F.SilkS'))
        kicad_mod.append(Property(name=Property.VALUE, text="footprint name", at=[0, 3], layer='F.Fab'))

        kicad_mod.append(Arc(center=[0, 0], start=[-1, 0], angle=180, layer='F.SilkS'))
        kicad_mod.append(Circle(center=[0, 0], radius=1.5, layer='F.SilkS'))
        kicad_mod.append(Line(start=[1, 0], end=[-1, 0], layer='F.SilkS'))
        kicad_mod.append(Model(filename="example.3dshapes/example_footprint.wrl",
                               at=[0, 0, 0], scale=[1, 1, 1], rotate=[0, 0, 0]))
        kicad_mod.append(Pad(number=1, type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT,
                             at=[0, 0], size=[2, 2], drill=1.2, layers=Pad.LAYERS_THT))

        self.assert_serialises_as(kicad_mod, 'footprint_basic_nodes.kicad_mod')
