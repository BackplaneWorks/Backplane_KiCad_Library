#!/usr/bin/env python3
"""Generate Backplane logo footprints from the outlined brand SVGs.

Reads only paths (no fonts, no text items) from sources/backplane_logo/ and
writes libraries/Backplane_Logo.pretty/. Add sizes to SIZES and rerun.

Per size the scaled art is made printable at MIN_FEATURE (the fab's silkscreen
minimum line width): strokes thinner than it are thickened, gaps narrower than
it are filled (that detail merges), and any sliver left is removed. A variant
is skipped at a size where that would close a letter counter, merge separate
parts (letters, slabs) or move an edge further than MAX_DRIFT; the skip is
recorded in the report.
"""
from pathlib import Path
import json, math, re, hashlib, sys
import numpy as np
import shapely
from shapely.geometry import Polygon, MultiPolygon, LineString, box
from shapely.ops import unary_union, polygonize
from shapely import affinity

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'sources/backplane_logo'
LIB = ROOT / 'libraries/Backplane_Logo.pretty'
REPORT = ROOT / 'verification/logo/build-report.json'

# Silkscreen legend minimum line width, free tier of the project's fab
# (fab_profile silk_line_min, published 0.15 mm, read 2026-11-13). Copper and
# mask variants use the same value: it is above the fab's 0.10 mm track/space
# and 0.10 mm mask bridge, so every layer gets identical art.
MIN_FEATURE = 0.15
SIZES = {                              # overall ink width, mm (--sizes 16,25 to try others)
    'Mark': [3, 5, 8, 12, 20, 30],
    'Text': [12, 20, 30],              # 12 is recorded as skipped: see the build report
}
MAX_DRIFT = 3 * 0.15                   # mm; how far any edge may move
ART = {
    'Mark': ('backplane-mark.svg', 'Backplane mark'),
    'Text': ('backplane-lockup-horizontal.svg', 'Backplane mark with backplane wordmark, horizontal'),
}
LAYERS = {   # suffix: (layers, mirrored, description)
    'SilkS': (['F.SilkS'], False, 'front silkscreen'),
    'SilkS_Back': (['B.SilkS'], True, 'back silkscreen, mirrored to read from the back'),
    'Cu': (['F.Cu', 'F.Mask'], False, 'front copper with matching mask opening (exposed finish, e.g. ENIG gold); floating, no net'),
}

# ---------------------------------------------------------------- SVG paths
NUM = r'[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?'

def _flatten(path_d, steps_per_unit):
    """Path data -> list of closed rings (lists of points). Supports M L H V Q C Z."""
    toks = re.findall(r'[MLHVQCZmlhvqcz]|' + NUM, path_d)
    rings, cur, pos, start, cmd, i = [], [], (0.0, 0.0), (0.0, 0.0), None, 0
    def nums(n):
        nonlocal i
        v = [float(t) for t in toks[i:i + n]]; i += n; return v
    def curve(pts, n):
        p = np.array(pts)
        length = np.sum(np.linalg.norm(np.diff(p, axis=0), axis=1))
        k = max(4, math.ceil(length * steps_per_unit))
        t = np.linspace(0, 1, k + 1)[1:, None]
        if n == 2:
            q = (1 - t) ** 2 * p[0] + 2 * (1 - t) * t * p[1] + t ** 2 * p[2]
        else:
            q = (1 - t) ** 3 * p[0] + 3 * (1 - t) ** 2 * t * p[1] + 3 * (1 - t) * t ** 2 * p[2] + t ** 3 * p[3]
        return [tuple(x) for x in q]
    while i < len(toks):
        if re.fullmatch('[A-Za-z]', toks[i]):
            cmd = toks[i]; i += 1
            if cmd in 'Zz':
                if len(cur) > 2: rings.append(cur)
                cur, pos = [], start
                continue
        rel = cmd.islower(); c = cmd.upper()
        ox, oy = pos if rel else (0.0, 0.0)
        if c == 'M':
            if len(cur) > 2: rings.append(cur)
            x, y = nums(2); pos = start = (x + ox, y + oy); cur = [pos]
            cmd = 'l' if rel else 'L'
        elif c == 'L':
            x, y = nums(2); pos = (x + ox, y + oy); cur.append(pos)
        elif c == 'H':
            x, = nums(1); pos = (x + ox, pos[1]); cur.append(pos)
        elif c == 'V':
            y, = nums(1); pos = (pos[0], y + oy); cur.append(pos)
        elif c == 'Q':
            a = nums(4); p1, p2 = (a[0] + ox, a[1] + oy), (a[2] + ox, a[3] + oy)
            cur += curve([pos, p1, p2], 2); pos = p2
        elif c == 'C':
            a = nums(6); p1, p2, p3 = (a[0] + ox, a[1] + oy), (a[2] + ox, a[3] + oy), (a[4] + ox, a[5] + oy)
            cur += curve([pos, p1, p2, p3], 3); pos = p3
        else:
            raise ValueError('unsupported path command ' + cmd)
    if len(cur) > 2: rings.append(cur)
    return rings

def _winding(pt, rings):
    x, y = pt; w = 0
    for r in rings:
        a = np.asarray(r); b = np.roll(a, -1, axis=0)
        up = (a[:, 1] <= y) & (b[:, 1] > y); dn = (a[:, 1] > y) & (b[:, 1] <= y)
        cross = (b[:, 0] - a[:, 0]) * (y - a[:, 1]) - (x - a[:, 0]) * (b[:, 1] - a[:, 1])
        w += int(np.sum(up & (cross > 0))) - int(np.sum(dn & (cross < 0)))
    return w

def _fill(rings, rule):
    """Filled region of a path under its SVG fill-rule (exact for overlapping contours)."""
    lines = unary_union([LineString(r + [r[0]]) for r in rings])
    faces = [f for f in polygonize(lines) if f.area > 0]
    keep = []
    for f in faces:
        w = _winding(f.representative_point().coords[0], rings)
        if (w % 2 == 1) if rule == 'evenodd' else (w != 0):
            keep.append(f)
    return unary_union(keep)

def read_svg(path):
    """Filled region of the SVG's paths, in SVG user units (y down), grouped:
    the path with id "mark" is the mark, every other path is the wordmark."""
    text = path.read_text()
    assert '<text' not in text and '<tspan' not in text, f'{path} has live text: outline it first'
    groups = {}
    for m in re.finditer(r'<path\b([^>]*)/?>', text):
        attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', m.group(1)))
        rule = attrs.get('fill-rule', 'nonzero')
        s = 1.0
        if 'transform' in attrs:
            t = re.fullmatch(r'scale\((' + NUM + r')\)', attrs['transform'].strip())
            assert t, 'only scale() transforms are supported: ' + attrs['transform']
            s = float(t.group(1))
        g = _fill(_flatten(attrs['d'], steps_per_unit=1.5), rule)
        group = 'mark' if attrs.get('id', 'mark') == 'mark' else 'wordmark'
        groups.setdefault(group, []).append(affinity.scale(g, s, s, origin=(0, 0)))
    out = {k: unary_union(v) for k, v in groups.items()}
    assert all(g.is_valid and not g.is_empty for g in out.values())
    return out

# ---------------------------------------------------------------- printability
MITRE = dict(join_style='mitre', mitre_limit=5.0)

def polys(g):
    if g.is_empty: return []
    return list(g.geoms) if hasattr(g, 'geoms') else [g]

def clean(g):
    g = shapely.make_valid(g).buffer(0)
    return unary_union([p for p in polys(g) if isinstance(p, Polygon) and p.area > 1e-6])

def opening(g, r): return clean(g.buffer(-r, **MITRE).buffer(r, **MITRE))
def closing(g, r): return clean(g.buffer(r, **MITRE).buffer(-r, **MITRE))

def holes(g): return sum(len(p.interiors) for p in polys(g))

def _parts(region, noise):
    return [p for p in polys(clean(region)) if p.area > noise]

def _width(p):
    """Widest point of a region: twice its largest inscribed circle radius."""
    return 2 * shapely.maximum_inscribed_circle(p, 1e-4).length

def _same_topology(a, b):
    return len(polys(a)) == len(polys(b)) and holes(a) == holes(b)

def _narrow_gaps(g, r):
    return closing(g, r).difference(g)

def printable(art, m=MIN_FEATURE):
    """Make art printable at feature size m. Returns (geometry, notes).

    Ink narrower than m is a "strip"; background narrower than m is a "gap".
    1. A strip that runs along a gap for much of its length is a highlight
       line (the mark's slab edges): the gap is filled, so the strip merges
       back into its body and the silhouette is kept.
    2. Other strips (the mark's frame, letter strokes) are thickened to m.
    3. Gaps whose filling would join no parts and close no hole (ink traps,
       notches) are filled. The rest (the occlusion gaps that separate slabs,
       letter apertures) are opened to m by insetting the solid parts beside
       them uniformly, by the least amount that works.
    4. Whatever is still under m is filled or removed.
    """
    r = m / 2
    noise = (m * m) * 0.05
    notes = {'merged_highlights': 0, 'thickened_strokes': 0, 'filled_notches': 0, 'inset_mm': 0.0, 'inset_parts': 0}
    strips = _parts(art.difference(opening(art, r)), noise)
    g, merged = art, set()
    # Finest detail first, so a hairline slot is told apart from a wider
    # occlusion gap it runs into at small sizes.
    for rho in (r / 4, r / 2, 3 * r / 4, r * 1.001):
        for q in _parts(_narrow_gaps(g, rho), noise):
            edge = q.buffer(m * 0.05)
            for i, s in enumerate(strips):
                if i in merged: continue
                if s.boundary.intersection(edge).length > 0.4 * s.length / 2:
                    filled = clean(g.union(q.buffer(1e-4)))
                    if _same_topology(filled, g):
                        g = filled; merged.add(i)
                        notes['merged_highlights'] += 1
                    break
    for i, s in enumerate(strips):
        if i in merged: continue
        d = max(0.0, (m - 2 * s.area / s.length) / 2) + 0.002   # from mean width
        for _ in range(6):             # grow until the whole strip is >= m wide
            grown = s.buffer(d, **MITRE)
            if grown.difference(opening(grown, r * 0.999)).area < noise: break
            d += m * 0.05
        g = g.union(grown)
        notes['thickened_strokes'] += 1
    g = clean(g)
    for q in _parts(_narrow_gaps(g, r * 1.001), noise):
        filled = clean(g.union(q.buffer(1e-4)))
        if _same_topology(filled, g):
            g = filled; notes['filled_notches'] += 1         # ink trap / notch
    # Gaps that must stay open: inset the solid parts beside them uniformly
    # (mitred, so slabs stay clean parallelograms), by the least amount that
    # opens every such gap to m. Thin strokes (the frame) are not inset.
    gaps = _parts(_narrow_gaps(g, r * 1.001), noise)
    if gaps:
        near = unary_union(gaps).buffer(m * 0.05)
        solid = [P for P in polys(g) if P.intersects(near)
                 and opening(P, m).area > 0.8 * P.area]      # >= 2 m wide bodies
        rest = [P for P in polys(g) if not any(P.equals(S) for S in solid)]
        for k in range(1, 21):
            e = m * k / 20
            trial = clean(unary_union(rest + [S.buffer(-e, **MITRE) for S in solid]))
            if (_same_topology(trial, g)
                    and not _parts(_narrow_gaps(trial, r * 0.999), noise)
                    and trial.difference(opening(trial, r * 0.999)).area < noise):
                g = trial
                notes['inset_mm'] = round(e, 4)
                notes['inset_parts'] = len(solid)
                break
    g = clean(g)
    for q in _parts(closing(g, r * 1.001).difference(g), 0):   # leftover wedges
        filled = clean(g.union(q.buffer(1e-5)))
        if _same_topology(filled, g): g = filled
    g = opening(g, r * 0.999)
    return g, notes

def thin_area(g, m=MIN_FEATURE):
    """Ink narrower than m, and gap narrower than m, in mm^2 (both ~0 when printable)."""
    return (g.difference(opening(g, m / 2 * 0.98)).area,
            closing(g, m / 2 * 0.98).difference(g).area)

# ---------------------------------------------------------------- KiCad output
def simple_pieces(p):
    """Split a polygon with holes into hole-free simple polygons (exact union)."""
    if not p.interiors: return [p]
    x0, y0, x1, y1 = p.bounds
    cuts = sorted({Polygon(r).representative_point().y for r in p.interiors})
    edges = [y0 - 1, *cuts, y1 + 1]
    out = []
    for a, b in zip(edges, edges[1:]):
        for q in polys(clean(p.intersection(box(x0 - 1, a, x1 + 1, b)))):
            out += simple_pieces(q) if q.interiors else [q]
    assert unary_union(out).symmetric_difference(p).area < 1e-8
    return out

def fp_polys(g, layer):
    out = []
    for p in polys(g):
        for q in simple_pieces(shapely.orient_polygons(p) if hasattr(shapely, 'orient_polygons') else p):
            q = shapely.set_precision(q, 1e-6)          # KiCad's 1 nm grid
            for piece in polys(clean(q)):
                assert piece.is_valid and not piece.interiors and piece.area > 0
                xy = ' '.join(f'(xy {x:.6f} {y:.6f})' for x, y in list(piece.exterior.coords)[:-1])
                out.append(f'  (fp_poly (pts {xy}) (stroke (width 0) (type solid)) (fill solid) (layer "{layer}"))')
    return out

def footprint(name, descr, tags, g, layers, mirrored):
    if mirrored: g = affinity.scale(g, -1, 1, origin=(0, 0))
    fab = 'B.Fab' if mirrored else 'F.Fab'
    just = ' (justify mirror)' if mirrored else ''
    lines = [f'(footprint "{name}"', '  (version 20240108)', '  (generator "backplane_logo_svg")',
             '  (layer "F.Cu")', f'  (descr "{descr.replace(chr(34), chr(39))}")', f'  (tags "{tags}")',
             '  (attr board_only exclude_from_pos_files exclude_from_bom)',
             f'  (fp_text reference "REF**" (at 0 0) (layer "{fab}") hide (effects (font (size 1 1) (thickness 0.15)){just}))',
             f'  (fp_text value "{name}" (at 0 0) (layer "{fab}") hide (effects (font (size 1 1) (thickness 0.15)){just}))']
    for layer in layers: lines += fp_polys(g, layer)
    return '\n'.join(lines) + '\n)\n'

# ---------------------------------------------------------------- build
def main():
    global SIZES
    if '--sizes' in sys.argv:                     # try sizes without writing the library
        trial = [float(v) for v in sys.argv[sys.argv.index('--sizes') + 1].split(',')]
        SIZES = {k: trial for k in SIZES}
        global LIB, REPORT
        LIB = Path('/tmp/backplane_logo_trial.pretty'); REPORT = LIB / 'build-report.json'
    LIB.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    for old in LIB.glob('Backplane_Logo_*.kicad_mod'): old.unlink()
    report = {'min_feature_mm': MIN_FEATURE, 'min_feature_source': 'fab_profile silk_line_min (free): https://jlcpcb.com/capabilities/pcb-capabilities, read 2026-11-13',
              'max_drift': MAX_DRIFT, 'sources': {}, 'footprints': {}, 'skipped': {}}
    for kind, (svg, label) in ART.items():
        groups = read_svg(SRC / svg)
        report['sources'][svg] = hashlib.sha256((SRC / svg).read_bytes()).hexdigest()
        x0, y0, x1, y1 = unary_union(list(groups.values())).bounds
        for size in SIZES[kind]:
            k = size / (x1 - x0)
            scaled = {n: affinity.scale(affinity.translate(g, -(x0 + x1) / 2, -(y0 + y1) / 2), k, k, origin=(0, 0))
                      for n, g in groups.items()}
            # Mark and wordmark are made printable separately, so the lockup's
            # mark gets exactly the treatment the standalone mark gets.
            done = {n: printable(g) for n, g in scaled.items()}
            art = unary_union(list(scaled.values()))
            g = unary_union([d[0] for d in done.values()])
            notes = {n: d[1] for n, d in done.items()}
            drift = art.hausdorff_distance(g)
            thin_ink, thin_gap = thin_area(g)
            ok = (_same_topology(g, art) and drift <= MAX_DRIFT
                  and thin_ink < MIN_FEATURE ** 2 * 0.05 and thin_gap < MIN_FEATURE ** 2 * 0.05)
            info = {'width_mm': round(g.bounds[2] - g.bounds[0], 4), 'height_mm': round(g.bounds[3] - g.bounds[1], 4),
                    'holes_source': holes(art), 'holes_out': holes(g), 'parts_source': len(polys(art)), 'parts_out': len(polys(g)), 'drift_mm': round(drift, 4),
                    'area_change_pct': round(100 * (g.area - art.area) / art.area, 2),
                    'under_min_ink_mm2': round(thin_ink, 6), 'under_min_gap_mm2': round(thin_gap, 6), 'steps': notes}
            if not ok:
                report['skipped'][f'{kind}_{size}mm'] = info
                print(f'skip {kind} {size} mm: {info}')
                continue
            for suffix, (layers, mirrored, ldesc) in LAYERS.items():
                name = f'Backplane_Logo_{kind}_{size}mm_{suffix}'
                descr = (f'{label}, {info["width_mm"]:g} x {info["height_mm"]:g} mm, {ldesc}; '
                         f'outlined from the brand SVG, features >= {MIN_FEATURE} mm; no pads')
                text = footprint(name, descr, 'logo backplane art graphic', g, layers, mirrored)
                (LIB / f'{name}.kicad_mod').write_text(text)
                report['footprints'][name] = {**info, 'layers': layers, 'mirrored': mirrored,
                                              'sha256': hashlib.sha256(text.encode()).hexdigest()}
            print(f'{kind} {size} mm: {info}')
    REPORT.write_text(json.dumps(report, indent=2) + '\n')
    print(f'{len(report["footprints"])} footprints, {len(report["skipped"])} skipped size/variant pairs')

if __name__ == '__main__':
    main()
