#!/usr/bin/env python3
"""Derive sizes from the delivered vector contours; preserve original 35 mm files.

uv run --no-project --with shapely==2.1.2 --with pillow==12.1.1 \
  --with numpy==2.3.5 --with fonttools==4.66.0 --with cairosvg==2.8.2 \
  scripts/build_shoggoth.py
Requires system libpotrace for importing the original writer (no retracing here).
"""
from pathlib import Path
import sys, re, json, shutil, hashlib, math
import shapely
from shapely.geometry import Polygon, GeometryCollection
from shapely.ops import unary_union
from shapely.affinity import scale

ROOT = Path(__file__).resolve().parents[1]
ORIG = ROOT / 'sources/shoggoth/original'
sys.path.insert(0, str(ORIG / 'source'))
import generate_badge as gen

OUT = ROOT / 'libraries/Backplane_Shoggoth.pretty'
V = ROOT / 'verification/shoggoth'

def quantized_polys(g, layer):
    """Repair nanometre-grid pinches before emitting simple KiCad contours."""
    out=[]
    for piece in gen.pieces(g):
        rounded=Polygon([(round(x,6),round(y,6)) for x,y in list(piece.exterior.coords)])
        fixed=gen.clean(rounded)
        assert abs(fixed.area-piece.area)<.00001
        for p in gen.polygons(fixed):
            if p.is_empty or p.area<1e-12:
                continue
            simple=list(shapely.constrained_delaunay_triangles(p).geoms) if p.interiors else [p]
            for q in simple:
                assert q.is_valid and not q.interiors
                xy=' '.join(f'(xy {gen.fmt(x)} {gen.fmt(y)})' for x,y in list(q.exterior.coords)[:-1])
                out.append(f'  (fp_poly (pts {xy}) (stroke (width 0) (type solid)) (fill solid) (layer "{layer}"))')
    return out

gen.kicad_polys=quantized_polys

def read_layers(path):
    layers = {}
    # Original writer emits each polygon on one line. No regex parsing of nesting.
    for line in path.read_text().splitlines():
        if not line.strip().startswith('(fp_poly '):
            continue
        layer = re.search(r'\(layer "([^"]+)"\)', line)[1]
        points = [(float(x), float(y)) for x,y in re.findall(r'\(xy ([-\d.]+) ([-\d.]+)\)', line)]
        layers.setdefault(layer, []).append(Polygon(points))
    return {k: unary_union(v) for k,v in layers.items()}

def small_variant(ink, face35):
    """Only subtract ink: do not put ink into previously untouched source colours.

    A 0.15 mm diameter opening removes thin positive features. Enclosed negative
    features smaller than 0.15 mm are enlarged. Rounded tapered boundaries still
    need process review; a morphology screen is not a stroke-width certificate.
    Rebuild the copper from the original face with fixed physical silk clearance.
    """
    ink0 = scale(ink, xfact=25/35, yfact=25/35, origin=(0,0))
    ink = gen.clean(ink0.buffer(-.075, quad_segs=16).buffer(.075, quad_segs=16).intersection(ink0))
    removed_holes = []
    for p in gen.polygons(ink):
        for ring in p.interiors:
            hole = Polygon(ring)
            corners = list(hole.minimum_rotated_rectangle.exterior.coords)
            width = min(math.dist(a,b) for a,b in zip(corners,corners[1:]))
            if width < .15:
                removed_holes.append(hole.buffer((.15-width)/2+.001, quad_segs=16))
    if removed_holes:
        ink = gen.clean(ink.difference(unary_union(removed_holes)))
    # 35 mm copper was already inset by >=0.10 mm; scaling followed by another
    # inward offset retains that edge inset and restores >=0.11 mm to scaled silk.
    face = scale(face35, xfact=25/35, yfact=25/35, origin=(0,0))
    face = gen.clean(face.buffer(-.10*(1-25/35),quad_segs=16).difference(ink.buffer(.111,quad_segs=16)))
    assert ink.difference(ink0).area < 1e-10
    return ink, face, {'removed_silk_area_mm2':ink0.difference(ink).area,
                       'removed_silk_percent':100*ink0.difference(ink).area/ink0.area,
                       'enlarged_negative_features':len(removed_holes),
                       'adaptation':'0.15 mm positive feature opening; enlarge enclosed negative detail to >=0.15 mm; restore 0.11 mm mask/silk gap'}

def main():
    for p in [OUT,V,ROOT/'previews/shoggoth',ROOT/'sources/shoggoth/vectors']:
        p.mkdir(parents=True,exist_ok=True)
    report={}
    for kind in ['Mascot','Badge']:
        original=ORIG/'ShoggothBadge.pretty'/f'Shoggoth_{kind}_35mm.kicad_mod'
        layers=read_layers(original)
        ink35,face35=layers['F.SilkS'],layers['F.Cu']
        assert face35.equals(layers['F.Mask'])
        for size in [25,35,50]:
            name=f'Shoggoth_{kind}_{size}mm'
            note={}
            if size==25:
                ink,face,note=small_variant(ink35,face35)
            else:
                ink=scale(ink35,xfact=size/35,yfact=size/35,origin=(0,0))
                face=scale(face35,xfact=size/35,yfact=size/35,origin=(0,0))
            total=unary_union([ink,face]); bounds=total.bounds
            if size==35:
                shutil.copy2(original,OUT/original.name)
                mod=original.read_text()
            else:
                mod=gen.module(name,ink,face).replace('35 mm decorative',f'{size} mm decorative')
                if size==25:
                    mod=mod.replace('raster-traced shoggoth;', 'raster-traced shoggoth, detail-adapted for 0.15 mm screening;')
                (OUT/f'{name}.kicad_mod').write_text(mod)
            (ROOT/'sources/shoggoth/vectors'/f'{name}.svg').write_text(gen.source_svg(name,ink,face,bounds))
            preview=gen.source_svg(name,ink,face,bounds,layout=True)
            (ROOT/'previews/shoggoth'/f'{name}.svg').write_text(preview)
            gen.cairosvg.svg2png(bytestring=preview.encode(),write_to=str(ROOT/'previews/shoggoth'/f'{name}.png'),output_width=1000)
            # New, explicitly disposable validation boards. Production board edits use IPC.
            (V/f'{name}.kicad_pcb').write_text(gen.demo_board(name,mod,bounds))
            (V/f'{name}.kicad_pro').write_text(json.dumps({'meta':{'filename':name+'.kicad_pro','version':1},'board':{'design_settings':{'rules':{'min_silk_clearance':.1,'min_copper_edge_clearance':.3}}}},indent=2)+'\n')
            gap=ink.distance(face)
            assert gap>=.109
            assert face.intersection(ink).area<1e-9
            assert sum(len(p.interiors) for p in gen.polygons(face))==3
            # Record smallest enclosed negative detail of the final ink.
            neg=[]
            for p in gen.polygons(ink):
                for ring in p.interiors:
                    corners=list(Polygon(ring).minimum_rotated_rectangle.exterior.coords)
                    neg.append(min(math.dist(a,b) for a,b in zip(corners,corners[1:])))
            if size==25: assert min(neg)>=.15-1e-6
            report[name]={'nominal_width_mm':size,'actual_width_mm':bounds[2]-bounds[0],
                          'height_mm':bounds[3]-bounds[1],'silk_to_opening_mm':gap,
                          'smallest_enclosed_negative_short_caliper_mm':min(neg),
                          'face_mask_holes':3,'copper_equals_mask':True,'paste_geometry':0,
                          'original_35mm_byte_identical':size==35,
                          'sha256':hashlib.sha256((OUT/f'{name}.kicad_mod').read_bytes()).hexdigest(),**note}
    (V/'geometry-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
