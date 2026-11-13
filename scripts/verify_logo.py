#!/usr/bin/env python3
"""Verify Backplane_Logo.pretty: KiCad load, native upgrade roundtrip, polygon
checks, printability at the fab minimum, DRC on a board holding every logo,
native layer plots and the preview sheet."""
from pathlib import Path
import io, json, os, re, shutil, subprocess, sys, hashlib
import shapely
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely import affinity
import cairosvg
from PIL import Image, ImageDraw, ImageFont, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_logo as B

ROOT = B.ROOT
LIB = B.LIB
V = ROOT / 'verification/logo'
PREVIEW = ROOT / 'previews/logo/logo-sheet.png'
CLI = os.environ.get('BACKPLANE_KICAD_CLI') or shutil.which('kicad-cli')
LOG = []
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

def cli(*args):
    p = subprocess.run([CLI, *map(str, args)], text=True, capture_output=True, timeout=300)
    LOG.append({'argv': list(map(str, args)), 'code': p.returncode, 'stdout': p.stdout[-4000:], 'stderr': p.stderr[-4000:]})
    if p.returncode: raise RuntimeError(p.stdout + p.stderr)
    return p.stdout

def fp_items(text):
    """(layer, ring points) per fp_poly, for both our writer and KiCad's own."""
    out = []
    for m in re.finditer(r'\(fp_poly\s*\(pts(.*?)\)\s*\(stroke.*?\(layer "([^"]+)"\)', text, re.S):
        pts = [(float(x), float(y)) for x, y in re.findall(r'\(xy ([-\d.e]+) ([-\d.e]+)\)', m.group(1))]
        out.append((m.group(2), pts))
    return out

def layers(text):
    d = {}
    for layer, pts in fp_items(text):
        d.setdefault(layer, []).append(Polygon(pts))
    return d

def main():
    V.mkdir(parents=True, exist_ok=True)
    for sub in ('footprint-load', 'layers'):
        if (V / sub).exists(): shutil.rmtree(V / sub)
        (V / sub).mkdir()
    build = json.loads((V / 'build-report.json').read_text())
    files = sorted(LIB.glob('*.kicad_mod'))
    assert len(files) == len(build['footprints']) > 0
    version = cli('--version').strip()

    # 1. KiCad loads every footprint and plots it.
    cli('fp', 'export', 'svg', '--output', V / 'footprint-load', '--layers', 'F.Cu,F.Mask,F.SilkS,B.SilkS', LIB)
    assert len(list((V / 'footprint-load').glob('*.svg'))) == len(files)

    # 2. Native roundtrip: KiCad rewrites them in its current format.
    rt = Path('/tmp/backplane_logo_roundtrip.pretty')
    if rt.exists(): shutil.rmtree(rt)
    cli('fp', 'upgrade', '--force', '--output', rt, LIB)

    report = {}
    m = B.MIN_FEATURE
    for p in files:
        name, text = p.stem, p.read_text()
        info = build['footprints'][name]
        assert '(pad ' not in text and 'Paste' not in text and '(fp_text ' in text
        assert '(attr board_only exclude_from_pos_files exclude_from_bom)' in text
        assert '(layer "F.Cu")\n  (descr' in text                 # library footprints are front-side
        items = fp_items(text)
        for layer, pts in items:                                  # every polygon simple, no holes
            poly = Polygon(pts)
            assert poly.is_valid and poly.exterior.is_simple and not poly.interiors and poly.area > 0, (name, layer)
            assert all(abs(v * 1e6 - round(v * 1e6)) < 1e-3 for xy in pts for v in xy)  # 1 nm grid
        L = {k: unary_union(v) for k, v in layers(text).items()}
        assert set(L) == set(info['layers']), (name, set(L))
        art = L[info['layers'][0]]
        if info['mirrored']: art = affinity.scale(art, -1, 1, origin=(0, 0))
        if len(L) == 2: assert L['F.Cu'].symmetric_difference(L['F.Mask']).area < 1e-9
        thin_ink, thin_gap = B.thin_area(art)
        noise = m * m * 0.05
        assert thin_ink < noise and thin_gap < noise, (name, thin_ink, thin_gap)
        assert B.holes(art) == info['holes_source'] and len(B.polys(art)) == info['parts_source']
        # Same art in every layer variant of a size.
        front = unary_union(layers((LIB / (name.rsplit('_', 2)[0] + '_SilkS.kicad_mod' if name.endswith('SilkS_Back')
                                              else name.rsplit('_', 1)[0] + '_SilkS.kicad_mod')).read_text())['F.SilkS'])
        assert front.symmetric_difference(art).area < 1e-9, name
        R = {k: unary_union(v) for k, v in layers((rt / p.name).read_text()).items()}
        delta = {k: L[k].symmetric_difference(R[k]).area for k in L}
        assert max(delta.values()) < 1e-9, (name, delta)
        report[name] = {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'layers': sorted(L),
                        'polygons': len(items), 'width_mm': info['width_mm'], 'height_mm': info['height_mm'],
                        'holes': B.holes(art), 'parts': len(B.polys(art)),
                        'under_min_ink_mm2': round(thin_ink, 7), 'under_min_gap_mm2': round(thin_gap, 7),
                        'roundtrip_difference_mm2': max(delta.values()), 'back_is_mirror_of_front': True}
    shutil.rmtree(rt)

    # 3. One board with every logo at true scale: DRC and native layer plots.
    board, cells = make_board(files, build)
    drc = V / 'logo_test-drc.json'
    cli('pcb', 'drc', '--format', 'json', '--output', drc, '--severity-all', board)
    d = json.loads(drc.read_text())
    assert not d['violations'] and not d['unconnected_items'], d['violations'][:5]
    cli('pcb', 'export', 'svg', '--output', V / 'layers', '--layers', 'F.Cu,F.Mask,F.SilkS,B.SilkS,Edge.Cuts',
        '--mode-multi', '--page-size-mode', '2', '--exclude-drawing-sheet', '--black-and-white', board)
    cli('pcb', 'export', 'svg', '--output', V / 'layers' / 'mirrored', '--layers', 'B.SilkS,Edge.Cuts',
        '--mode-multi', '--mirror', '--page-size-mode', '2', '--exclude-drawing-sheet', '--black-and-white', board)
    sheet(cells)

    (V / 'cli-log.json').write_text(json.dumps(LOG, indent=2) + '\n')
    (V / 'verification-report.json').write_text(json.dumps(
        {'kicad': version, 'cli': CLI, 'footprints': report,
         'board': str(board.relative_to(ROOT)), 'drc_violations': 0, 'unconnected_items': 0,
         'preview': str(PREVIEW.relative_to(ROOT))}, indent=2) + '\n')
    print(f'All {len(files)} logo footprints passed ({version}).')

# ------------------------------------------------------------------ test board
HEADER = '''(kicad_pcb (version 20240108) (generator "backplane_logo_svg")
  (general (thickness 1.6)) (paper "A3")
  (layers (0 "F.Cu" signal) (31 "B.Cu" signal) (32 "B.Adhes" user "B.Adhesive") (33 "F.Adhes" user "F.Adhesive") (34 "B.Paste" user) (35 "F.Paste" user) (36 "B.SilkS" user "B.Silkscreen") (37 "F.SilkS" user "F.Silkscreen") (38 "B.Mask" user) (39 "F.Mask" user) (44 "Edge.Cuts" user) (46 "B.CrtYd" user "B.Courtyard") (47 "F.CrtYd" user "F.Courtyard") (48 "B.Fab" user) (49 "F.Fab" user))
  (setup (pad_to_mask_clearance 0))
  (net 0 "")
'''

def make_board(files, build):
    """Rows: one per variant and size; columns: SilkS, SilkS_Back, Cu."""
    rows = sorted({n.rsplit('_', 1)[0].replace('_SilkS', '') for n in (f.stem for f in files)},
                  key=lambda s: (s.split('_')[2], float(s.split('_')[3][:-2])))
    cols = ['SilkS', 'SilkS_Back', 'Cu']
    colw = max(build['footprints'][f.stem]['width_mm'] for f in files) + 8
    margin, label = 6, 4
    y, body, cells = margin, [], []
    for base in rows:
        h = max(build['footprints'][f'{base}_{c}']['height_mm'] for c in cols)
        y += label
        for i, c in enumerate(cols):
            name = f'{base}_{c}'
            x = margin + colw * (i + 0.5); cy = y + h / 2
            text = (LIB / f'{name}.kicad_mod').read_text().rstrip()
            text = text.replace('  (layer "F.Cu")\n', f'  (layer "F.Cu")\n  (at {x:.4f} {cy:.4f})\n', 1)
            body.append(text)
            cells.append((name, x, y - label, h))
        y += h + 3
    W, H = margin * 2 + colw * len(cols), y + margin
    edge = ''.join(f'  (gr_line (start {a}) (end {b}) (stroke (width 0.05) (type default)) (layer "Edge.Cuts"))\n'
                   for a, b in (('0 0', f'{W} 0'), (f'{W} 0', f'{W} {H}'), (f'{W} {H}', f'0 {H}'), (f'0 {H}', '0 0')))
    board = V / 'logo_test.kicad_pcb'
    board.write_text(HEADER + '\n'.join(body) + '\n' + edge + ')\n')
    return board, (cells, W, H, cols)

# ------------------------------------------------------------------ preview
def raster(svg, width, color):
    data = svg.read_text().replace('#000000', color)
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=data.encode(), output_width=width))).convert('RGBA')

def sheet(spec):
    (cells, W, H, cols) = spec
    px = 1800; s = px / W
    plots = {f.stem.split('-', 1)[-1]: f for f in (V / 'layers').glob('*.svg')}
    mirrored = {f.stem.split('-', 1)[-1]: f for f in (V / 'layers' / 'mirrored').glob('*.svg')}
    def view(parts):
        img = Image.new('RGBA', raster(plots['Edge_Cuts'], px, '#000000').size, '#1f4a3a')
        for f, colour in parts: img.alpha_composite(raster(f, px, colour))
        return img
    front = view([(plots['F_Mask'], '#c9a64e'), (plots['F_Cu'], '#d8b25a'), (plots['F_Silkscreen'], '#f4f1e4')])
    back = view([(mirrored['B_Silkscreen'], '#f4f1e4')])
    f, fb = ImageFont.truetype(FONT, 17), ImageFont.truetype(BOLD, 30)
    head = 120
    out = Image.new('RGB', (front.width * 2 + 60, front.height + head + 20), '#eeeee5')
    d = ImageDraw.Draw(out)
    d.text((20, 18), 'BACKPLANE_LOGO · ALL FOOTPRINTS AT TRUE RELATIVE SCALE', font=fb, fill='#17271d')
    d.text((20, 62), 'Native kicad-cli plots of one test board. Left: top view (silk white, Cu + mask opening gold). '
           'Right: the same board seen from the back (B.SilkS plotted mirrored).', font=f, fill='#17271d')
    out.paste(front, (20, head)); out.paste(back, (front.width + 40, head))
    for name, x, y, h in cells:
        short = name.replace('Backplane_Logo_', '')
        tx = (x - (W / len(cols)) / 2 + 2) * s
        if name.endswith('_SilkS_Back'):
            d.text((front.width + 40 + (W - x - (W / len(cols)) / 2 + 2) * s, head + y * s), short + ' (from back)', font=f, fill='#f4f1e4')
        d.text((20 + tx, head + y * s), short, font=f, fill='#f4f1e4')
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    out.save(PREVIEW)

if __name__ == '__main__':
    main()
