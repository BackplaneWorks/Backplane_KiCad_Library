#!/usr/bin/env python3
"""Build passives through the pinned, unmodified KiCad two-terminal generator."""
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import argparse
import copy
import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace
import yaml
sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
UPSTREAM = HERE / 'upstream'
sys.path[:0] = [str(UPSTREAM / 'src'), str(UPSTREAM)]
from generators.tools import cli_args
from kilibs.config import global_config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'libraries')
    args = parser.parse_args()
    cli_args.init(SimpleNamespace(dry_run=False, separate_outputs=False, output_dir_footprints=args.output.resolve()))
    global_config.init(str(HERE / 'configs/global.yaml'))
    # Import after initialization: upstream modules capture CLI/config singletons.
    from generators.SMD_2terminal_chip_molded.footprint import TwoTerminalSMD
    from kilibs.config.ipc_rules import IpcRules
    gc = global_config.GLOBAL_CONFIG
    ipc = IpcRules.from_file(str(HERE / 'configs/ipc7351B_2terminal.yaml'))
    inventory = []
    for density in ('least', 'nominal', 'most'):
        config = copy.deepcopy(gc.raw_data)
        config.update(yaml.safe_load((HERE / 'configs/package.yaml').read_text()))
        # Names remain identical across distinct density libraries.
        config['ipc_density'] = [density, '']
        groups_file = HERE / 'configs' / f'{density}.yaml'
        generator = TwoTerminalSMD(gc, ipc, groups_file, config)
        count = generator.generateFootprints('SMD_2terminal_chip_molded', HERE / 'configs/sizes')
        library = args.output / f'Backplane_Passives_{density.title()}.pretty'
        for path in sorted(library.glob('*.kicad_mod')):
            text = path.read_text()
            prefix = path.stem[0]
            family = {'R': 'Resistor_SMD', 'C': 'Capacitor_SMD', 'L': 'Inductor_SMD'}[prefix]
            model = f'${{BACKPLANE_KICAD_LIBRARY}}/3dmodels/{family}.3dshapes/{path.stem}.step'
            if not (ROOT / '3dmodels' / f'{family}.3dshapes' / (path.stem + '.step')).is_file():
                text, n = re.subn(r'\n\t\(model "[^"]+".*?\n\t\)', '', text, flags=re.S)
                assert n == 1, path
                path.write_text(text)
                inventory.append({'id': f'{library.stem}:{path.stem}', 'density': density, 'model': None})
                continue
            text, n = re.subn(r'\(model "[^"]+"', lambda _: f'(model "{model}"', text)
            assert n == 1, path
            path.write_text(text)
            inventory.append({'id': f'{library.stem}:{path.stem}', 'file': str(path.resolve().relative_to(ROOT)) if path.resolve().is_relative_to(ROOT) else str(path), 'density': density, 'model': model})
        assert count == len([p for p in library.glob('*.kicad_mod') if not p.stem.endswith('_LegacyLocal')]), (density, count)
        print(f'{library.name}: {count} footprints')
    # Preserve the additional historical local pattern without inventing other densities.
    legacy = (HERE / 'configs/legacy-local.yaml')
    data = yaml.safe_load(legacy.read_text())
    text = (HERE / data['source']).read_text().replace(data['original_name'], data['name'])
    text, n = re.subn(r'\(model "[^"]+"', lambda _: f'(model "{data["model"]}"', text)
    assert n == 1
    target = args.output / 'Backplane_Passives_Least.pretty' / (data['name'] + '.kicad_mod')
    target.write_text(text)
    print('Preserved original local 0806 geometry in Least only (45/44/44 total)')
    return inventory

if __name__ == '__main__':
    main()
