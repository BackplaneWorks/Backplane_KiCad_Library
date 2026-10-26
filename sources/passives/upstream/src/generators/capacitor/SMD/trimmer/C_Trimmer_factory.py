# generators is free software: you can redistribute it and/or modify it under the terms
# of the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# generators is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# generators. If not, see < http://www.gnu.org/licenses/ >.
#
# (C) The KiCad Librarian Team

import yaml

from generators.tools.footprint.save_footprint import write_footprint
from generators.tools.footprint.drawing_tools import round_to_grid
from kilibs.config import global_config as GC
from kilibs.config.global_config import GLOBAL_CONFIG

from KicadModTree import *  # NOQA
from .bump import *
from .corners import *
from .chamfers import *


class Dimensions(object):

    def __init__(self, base, variant, cut_pin=False, tab_linked=False):

        footprint = variant['footprint']
        device = variant['device']

        # FROM KLC
        self.fab_line_width_mm = 0.1
        self.fab_text_size = [1.0, 1.0]
        self.fab_text_thickness = 0.15
        self.fab_reference_text_size = [0.5, 0.5]
        self.fab_reference_text_thickness = 0.05
        self.silk_line_width_mm = 0.12
        self.silk_text_size = [1.0, 1.0]
        self.silk_text_thickness = 0.15
        self.courtyard_line_width_mm = 0.05
        self.courtyard_clearance_mm = 0.25
        self.courtyard_precision_mm = 0.01

        # NAME
        self.name = self._footprint_name(variant['manufacturer'], variant['series'])

        # PADS
        self.pad_offset_x_mm = (footprint['pad']['x_mm'] - footprint['x_mm']) / 2.0

        # FAB OUTLINE
        self.device_offset_x_mm = device['body']['x_mm'] / 2.0  # x coordinate of RHS of device
        self.body_x_mm = device['body']['x_mm']
        self.body_offset_y_mm = device['body']['y_mm'] / 2.0  # y coordinate of bottom of body

        # COURTYARD
        self.biggest_x_mm = footprint['x_mm']
        self.biggest_y_mm = device['body']['y_mm']
        if 'top' in device['projection']['sides'] or 'bottom' in device['projection']['sides']:
             self.biggest_y_mm += 2.0 * device['projection']['offset_mm']
        self.courtyard_offset_x_mm = round_to_grid(self.courtyard_clearance_mm + self.biggest_x_mm / 2.0,
                                                   self.courtyard_precision_mm)
        self.courtyard_offset_y_mm = round_to_grid(self.courtyard_clearance_mm + self.biggest_y_mm / 2.0,
                                                   self.courtyard_precision_mm)
        # SILKSCREEN
        self.label_centre_x_mm = 0
        self.label_centre_y_mm = self.courtyard_offset_y_mm + 1
        self.silk_offset_mm = (0.2, 0.2)  #  amount to shift silkscreen in X and Y directions to avoid overlapping fab lines

    def _footprint_name(self, manufacturer, series):
        name = 'C_Trimmer_{m:s}_{s:s}'.format(m=manufacturer, s=series)
        return name


class CapacitorTrimmer:

    global_config: GC.GlobalConfig

    def __init__(self, config_file):
        self.FAMILY = None
        self.config = None

    def _load_config(self, config_file):
        # This will come from FootprintGenerator one day
        self.global_config = GLOBAL_CONFIG
        devices = yaml.safe_load_all(open(config_file))
        config = None
        for dev in devices:
            if dev['base']['family'] == self.FAMILY:
                config = dev
                break
        return config

    def _add_properties(self, m, variant):
        m.setDescription('{bd:s}, {vd:s}'.format(bd=self.config['base']['description'], vd=variant['datasheet']))
        m.setTags('{bk:s} {vk:s}'.format(bk=self.config['base']['keywords'], vk=variant['keywords']))
        return m

    def _add_labels(self, m, variant, dim):
        m.append(Property(name=Property.REFERENCE, text='REF**', size=dim.silk_text_size, thickness=dim.silk_text_thickness, at=[dim.label_centre_x_mm, -dim.label_centre_y_mm],
                      layer='F.SilkS'))
        m.append(Text(text='${REFERENCE}', size=dim.fab_reference_text_size, thickness=dim.fab_reference_text_thickness, at=[0, 0], layer='F.Fab'))
        m.append(Property(name=Property.VALUE, text=dim.name, size=dim.fab_text_size, thickness=dim.fab_text_thickness, at=[dim.label_centre_x_mm, dim.label_centre_y_mm], layer='F.Fab'))
        return m

    def _draw_pads(self, m, variant, dim):
        m.append(Pad(number=1, type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                             at=[dim.pad_offset_x_mm, 0],
                             size=[variant['footprint']['pad']['x_mm'], variant['footprint']['pad']['y_mm']],
                             layers=Pad.LAYERS_SMT))
        m.append(Pad(number=2, type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                             at=[-dim.pad_offset_x_mm, 0],
                             size=[variant['footprint']['pad']['x_mm'], variant['footprint']['pad']['y_mm']],
                             layers=Pad.LAYERS_SMT))
        return m

    def _draw_fab_outline(self, m, variant, dim, width, offset):
        # draw body
        right_x = dim.device_offset_x_mm
        left_x = right_x - dim.body_x_mm
        top_y = -dim.body_offset_y_mm
        bottom_y = -top_y
        if 'left' in variant['device']['chamfer']['sides']:
            chamfers = [{'corner': 'topleft', 'size': variant['device']['chamfer']['size_mm']},
                        {'corner': 'bottomleft', 'size': variant['device']['chamfer']['size_mm']}]
        elif 'right' in variant['device']['chamfer']['sides']:
            chamfers = [{'corner': 'topright', 'size': variant['device']['chamfer']['size_mm']},
                        {'corner': 'bottomright', 'size': variant['device']['chamfer']['size_mm']}]
        else:
            chamfers = []
        m = add_rect_chamfer(m, [left_x, top_y], [right_x, bottom_y], 'F.Fab', width, offset, chamfers)
        m.append(Circle(center=[0, 0], radius=dim.body_offset_y_mm, layer='F.Fab', width=width))
        # add frame extensions
        p = variant['device']['projection']
        if 'top' in p['sides']:
            m = add_bump(m, [0, top_y], p['x_side_mm'], p['offset_mm'], 'up', 'F.Fab', width, offset)
        if 'bottom' in p['sides']:
            m = add_bump(m, [0, bottom_y], p['x_side_mm'], p['offset_mm'], 'down', 'F.Fab', width, offset)
        if 'right' in p['sides']:
            m = add_bump(m, [right_x, 0], p['y_side_mm'], p['offset_mm'], 'right', 'F.Fab', width, offset)
        if 'left' in p['sides']:
            m = add_bump(m, [left_x, 0], p['y_side_mm'], p['offset_mm'], 'left', 'F.Fab', width, offset)
        return m

    def _draw_silk_outline(self, m, variant, dim, width, offset):
        right_x = dim.device_offset_x_mm
        left_x = right_x - dim.body_x_mm
        top_y = -dim.body_offset_y_mm
        bottom_y = -top_y
        if 'left' in variant['device']['chamfer']['sides']:
            chamfers = ['topleft', 'bottomleft']
        elif 'right' in variant['device']['chamfer']['sides']:
            chamfers = ['topright', 'bottomright']
        else:
            chamfers = []
        m = add_corners(m, [left_x, top_y], [right_x, bottom_y], 0.5, 0.5, 'F.SilkS', width, offset, chamfers)
        return m

    def _draw_courtyard(self, m ,dim):
        m.append(Rectangle(start=[-dim.courtyard_offset_x_mm, -dim.courtyard_offset_y_mm],
                                  end=[dim.courtyard_offset_x_mm, dim.courtyard_offset_y_mm], layer='F.CrtYd',
                                  width=dim.courtyard_line_width_mm))
        return m

    def _add_3D_model(self, m, base, dim):
        model_filename = (
            self.global_config.model_3d_prefix
            + base["3d_libname"]
            + ".3dshapes/"
            + dim.name
            + self.global_config.model_3d_suffix
        )
        m.append(
            Model(filename=model_filename, at=[0, 0, 0], scale=[1, 1, 1],
                  rotate=[0, 0, 0]))
        return m

    def _build_footprint(self, generator_name: str, base, variant, cut_pin=False, tab_linked=False, verbose=False):

        # calculate dimensions and other attributes specific to this variant
        dim = Dimensions(base, variant, cut_pin, tab_linked)

        # initialise footprint
        kicad_mod = Footprint(dim.name, FootprintType.SMD)
        kicad_mod = self._add_properties(kicad_mod, variant)
        kicad_mod = self._add_labels(kicad_mod, variant, dim)

        # create pads
        kicad_mod = self._draw_pads(kicad_mod, variant, dim)

        # create fab outline
        kicad_mod = self._draw_fab_outline(kicad_mod, variant, dim, dim.fab_line_width_mm, (0, 0))

        # create silkscreen outline
        kicad_mod = self._draw_silk_outline(kicad_mod, variant, dim, dim.silk_line_width_mm, dim.silk_offset_mm)

        # create courtyard
        kicad_mod = self._draw_courtyard(kicad_mod, dim)

        # add 3D model
        kicad_mod = self._add_3D_model(kicad_mod, base, dim)

        # write file
        lib_name = "Capacitor_SMD"
        write_footprint(kicad_mod, lib_name, generator_name)

    def build_series(self, generator_name: str, verbose=False) -> int:
        base = self.config['base']
        for variant in self.config['variants']:
            self._build_footprint(generator_name, base, variant, verbose=verbose)
        return len(self.config['variants'])


class StyleA(CapacitorTrimmer):

    def __init__(self, config_file):
        self.FAMILY = 'STYLE-A'
        self.config = self._load_config(config_file)


class StyleB(CapacitorTrimmer):

    def __init__(self, config_file):
        self.FAMILY = 'STYLE-B'
        self.config = self._load_config(config_file)


class StyleC(CapacitorTrimmer):

    def __init__(self, config_file):
        self.FAMILY = 'STYLE-C'
        self.config = self._load_config(config_file)


class StyleD(CapacitorTrimmer):

    def __init__(self, config_file):
        self.FAMILY = 'STYLE-D'
        self.config = self._load_config(config_file)


class Factory(object):

    def __init__(self, config_file):
        self._config_file = config_file
        self.build_list = [StyleA(self._config_file), StyleB(self._config_file), StyleC(self._config_file), StyleD(self._config_file)]

        