#!/usr/bin/env python3
"""Deterministic raster-to-vector artwork. All geometry coordinates are millimetres.

Uses the host's libpotrace (the same tracer used by Inkscape), Pillow,
Shapely >=2.1, fontTools and CairoSVG. No image generation or pcbnew.
Run: uv run --no-project --python /usr/bin/python3 source/generate_badge.py
"""
from pathlib import Path
import ctypes as C
import ctypes.util
import json
import math
import shutil
import hashlib
from xml.sax.saxutils import escape
import numpy as np

from PIL import Image
import shapely
from shapely.geometry import Polygon, MultiPolygon, GeometryCollection, box
from shapely.ops import unary_union
from shapely.affinity import scale, translate
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
import cairosvg

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'source'
WIDTH_MM = 35.0
MASK_SILK_CLEARANCE_MM = 0.10
CAPTION_GAP_MM = 0.90
CAPTION_LINE_GAP_MM = 0.55
CAPTION_HEIGHT_MM = 1.85
CAPTION_LINES = ['THIS PCB WAS DESIGNED', 'BY AN EVIL SHOGGOTH']
CAPTION = 'THIS PCB WAS DESIGNED BY AN EVIL SHOGGOTH'
INPUT = Path('/home/h/.backplane-bend/attachments/t1790292962-8017/6826d1ca-image.png')
REFERENCE = Path('/home/h/.backplane-bend/attachments/t1790292962-8017/70b7a666-image.png')
FONT = Path('/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf')

class Point(C.Structure):
    _fields_ = [('x', C.c_double), ('y', C.c_double)]
class Curve(C.Structure):
    _fields_ = [('n', C.c_int), ('tag', C.POINTER(C.c_int)), ('c', C.POINTER(Point * 3))]
class TracePath(C.Structure):
    pass
TracePath._fields_ = [('area', C.c_int), ('sign', C.c_int), ('curve', Curve),
                     ('next', C.POINTER(TracePath)), ('childlist', C.POINTER(TracePath)),
                     ('sibling', C.POINTER(TracePath)), ('priv', C.c_void_p)]
class Bitmap(C.Structure):
    _fields_ = [('w', C.c_int), ('h', C.c_int), ('dy', C.c_int), ('map', C.POINTER(C.c_ulong))]
class State(C.Structure):
    _fields_ = [('status', C.c_int), ('plist', C.POINTER(TracePath)), ('priv', C.c_void_p)]
class Params(C.Structure):
    _fields_ = [('turdsize', C.c_int), ('turnpolicy', C.c_int), ('alphamax', C.c_double),
                ('opticurve', C.c_int), ('opttolerance', C.c_double)]
lib = C.CDLL(ctypes.util.find_library('potrace'))
lib.potrace_param_default.restype = C.POINTER(Params)
lib.potrace_trace.argtypes = [C.POINTER(Params), C.POINTER(Bitmap)]
lib.potrace_trace.restype = C.POINTER(State)
lib.potrace_state_free.argtypes = [C.POINTER(State)]
lib.potrace_param_free.argtypes = [C.POINTER(Params)]

def clean(g):
    g = shapely.make_valid(g)
    if isinstance(g, (Polygon, MultiPolygon)):
        return g
    return unary_union([p for p in shapely.get_parts(g) if isinstance(p, Polygon)])

def polygons(g):
    return [g] if isinstance(g, Polygon) else list(g.geoms)

def pixel_support(mask):
    """Exact union of foreground pixel cells, for conservative colour boundaries.

    Potrace gives smooth curves but may overshoot a few pixel edges. Clipping
    to these cells prevents any ink entering a green, white or yellow pixel.
    Most of each smooth curve is retained; only overshooting fringes are cut.
    """
    runs=[]
    for y,row in enumerate(np.asarray(mask,dtype=bool)):
        edges=np.flatnonzero(np.diff(np.r_[False,row,False].astype(np.int8)))
        runs.extend(box(int(a),y,int(b),y+1) for a,b in edges.reshape(-1,2))
    return clean(unary_union(runs))

def flatten_cubic(p0, p1, p2, p3, tol):
    # Conservative recursive flatness bound: distance of both controls to chord.
    dx, dy = p3[0]-p0[0], p3[1]-p0[1]
    norm = math.hypot(dx, dy)
    d = max(abs(dx*(q[1]-p0[1])-dy*(q[0]-p0[0])) / norm
            if norm else math.dist(p0, q) for q in (p1,p2))
    if d <= tol:
        return [p3]
    mid = lambda a,b: ((a[0]+b[0])/2, (a[1]+b[1])/2)
    a,b,c=mid(p0,p1),mid(p1,p2),mid(p2,p3)
    d,e=mid(a,b),mid(b,c)
    f=mid(d,e)
    return flatten_cubic(p0,a,d,f,tol)+flatten_cubic(f,e,c,p3,tol)

def trace(mask, tolerance_pixels=0.08):
    w,h = mask.size
    bits = C.sizeof(C.c_ulong)*8
    dy = (w+bits-1)//bits
    words = (C.c_ulong * (dy*h))()
    pix = mask.load()
    for y in range(h):
        for x in range(w):
            if pix[x,y]:
                words[y*dy+x//bits] |= 1 << (bits-1-x%bits)
    param = lib.potrace_param_default()
    param.contents.turdsize = 3
    param.contents.opttolerance = 0.15
    bm = Bitmap(w,h,dy,words)
    state = lib.potrace_trace(param, C.byref(bm))
    if not state or state.contents.status != 0:
        raise RuntimeError('Potrace failed')
    result = GeometryCollection()
    paths = []
    p = state.contents.plist
    while p:
        cv = p.contents.curve
        coords=[]
        last=(cv.c[cv.n-1][2].x, cv.c[cv.n-1][2].y)
        coords.append(last)
        for i in range(cv.n):
            controls=[(cv.c[i][j].x,cv.c[i][j].y) for j in range(3)]
            if cv.tag[i] == 2: # POTRACE_CORNER (CURVETO is 1)
                coords.extend(controls[1:])
            else:
                coords.extend(flatten_cubic(last,*controls,tolerance_pixels))
            last=controls[2]
        shape = clean(Polygon(coords))
        if not shape.is_empty:
            result = result.symmetric_difference(shape)
            paths.append({'sign': chr(p.contents.sign), 'pixel_area': p.contents.area,
                          'vertices': len(coords)})
        p=p.contents.next
    lib.potrace_state_free(state)
    lib.potrace_param_free(param)
    return clean(result), paths

class GlyphPen(BasePen):
    def __init__(self, glyphset):
        super().__init__(glyphset)
        self.rings=[]
    def _moveTo(self,p):
        self.points=[p]
    def _lineTo(self,p):
        self.points.append(p)
    def _curveToOne(self,a,b,c):
        self.points.extend(flatten_cubic(self.points[-1],a,b,c,0.7))
    def _qCurveToOne(self,a,b):
        p=self.points[-1]
        c1=(p[0]+2*(a[0]-p[0])/3,p[1]+2*(a[1]-p[1])/3)
        c2=(b[0]+2*(a[0]-b[0])/3,b[1]+2*(a[1]-b[1])/3)
        self._curveToOne(c1,c2,b)
    def _closePath(self):
        self.rings.append(self.points)
    def _endPath(self):
        self._closePath()

def text_geometry(text, font):
    cmap=font.getBestCmap()
    glyphs=font.getGlyphSet()
    advance=0
    result=[]
    for ch in text:
        name=cmap[ord(ch)]
        pen=GlyphPen(glyphs)
        glyphs[name].draw(pen)
        g=GeometryCollection()
        for ring in pen.rings:
            if len(ring)>2:
                g=g.symmetric_difference(clean(Polygon(ring)))
        if not g.is_empty:
            result.append(translate(g, xoff=advance))
        advance+=font['hmtx'].metrics[name][0]
    return unary_union(result)

def fmt(v):
    return f'{v:.6f}'.rstrip('0').rstrip('.') if abs(v)>0.0000005 else '0'

def svg_path(g):
    paths=[]
    for p in polygons(g):
        for ring in [p.exterior,*p.interiors]:
            pts=list(ring.coords)
            paths.append('M'+' L'.join(f'{fmt(x)},{fmt(y)}' for x,y in pts[:-1])+' Z')
    return ' '.join(paths)

def pieces(g):
    """Split holes into simple contours, rather than emitting unsupported rings.

    Horizontal cuts through every hole open the holes at the piece boundaries.
    Constrained triangulation is a fallback for degenerate/remaining holes.
    All pieces are checked to reproduce the original geometry exactly.
    """
    out=[]
    for p in polygons(g):
        if p.interiors:
            x0,y0,x1,y1=p.bounds
            cuts=sorted(set([y0-1,y1+1]+[Polygon(r).representative_point().y for r in p.interiors]))
            split=[]
            for a,b in zip(cuts,cuts[1:]):
                clipped=clean(p.intersection(box(x0-1,a,x1+1,b)))
                for q in polygons(clipped):
                    if q.is_empty:
                        continue
                    if q.interiors:
                        split.extend(shapely.constrained_delaunay_triangles(q).geoms)
                    else:
                        split.append(q)
            assert unary_union(split).symmetric_difference(p).area<1e-8
            out.extend(split)
        else:
            out.append(p)
    return out

def kicad_polys(g, layer):
    out=[]
    for p in pieces(g):
        coords=list(p.exterior.coords)[:-1]
        xy=' '.join(f'(xy {fmt(x)} {fmt(y)})' for x,y in coords)
        out.append(f'  (fp_poly (pts {xy}) (stroke (width 0) (type solid)) (fill solid) (layer "{layer}"))')
    return out

def module(name, silk, copper):
    header=[f'(footprint "{name}"', '  (version 20240108)',
        '  (generator "shoggoth_raster_trace")', '  (layer "F.Cu")',
        f'  (descr "35 mm decorative raster-traced shoggoth; {CAPTION if "Badge" in name else "mascot only"}; no electrical pads; floating face copper")',
        '  (tags "art logo shoggoth decorative")',
        '  (attr board_only exclude_from_pos_files exclude_from_bom)',
        '  (fp_text reference "REF**" (at 0 0) (layer "F.Fab") hide (effects (font (size 1 1) (thickness 0.15))))',
        f'  (fp_text value "{name}" (at 0 0) (layer "F.Fab") hide (effects (font (size 1 1) (thickness 0.15))))']
    return '\n'.join(header+kicad_polys(silk,'F.SilkS')+kicad_polys(copper,'F.Cu')+kicad_polys(copper,'F.Mask')+[')'])+'\n'

def source_svg(name, silk, copper, bounds, layout=False):
    x0,y0,x1,y1=bounds
    layers=[]
    if layout:
        layers.append(f'<rect x="{x0-1.6}" y="{y0-1.6}" width="{x1-x0+3.2}" height="{y1-y0+3.2}" rx="1.4" fill="#244d3f"/>')
    layers.append(f'<g id="front-copper" inkscape:groupmode="layer" inkscape:label="F.Cu — face only"><path fill="{ "#d8af52" if layout else "#d7bd3e"}" fill-rule="evenodd" d="{svg_path(copper)}"/></g>')
    if not layout:
        layers.append(f'<g id="front-mask-opening" inkscape:groupmode="layer" inkscape:label="F.Mask — same face, hidden for editing" style="display:none"><path fill="#a000a0" fill-rule="evenodd" d="{svg_path(copper)}"/></g>')
    layers.append(f'<g id="front-silkscreen" inkscape:groupmode="layer" inkscape:label="F.SilkS — traced black and caption"><path fill="{ "#f5f3de" if layout else "#151b16"}" fill-rule="evenodd" d="{svg_path(silk)}"/></g>')
    pad=1.7 if layout else 0.25
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" width="{fmt(x1-x0+2*pad)}mm" height="{fmt(y1-y0+2*pad)}mm" viewBox="{fmt(x0-pad)} {fmt(y0-pad)} {fmt(x1-x0+2*pad)} {fmt(y1-y0+2*pad)}">
<title>{escape(name)}</title><desc>{CAPTION}. All coordinates in mm. Green and white source pixels have no artwork. {'Illustrative PCB preview, not physical qualification.' if layout else 'Editable separated layer paths; text converted to outlines.'}</desc>
{''.join(layers)}
</svg>'''

def demo_board(name, mod, bounds):
    x0,y0,x1,y1=bounds
    x0-=2; y0-=2; x1+=2; y1+=2
    mod=mod.replace('(layer "F.Cu")','(layer "F.Cu")\n  (at 60 60)',1)
    edges=[]
    for a,b in [((x0,y0),(x1,y0)),((x1,y0),(x1,y1)),((x1,y1),(x0,y1)),((x0,y1),(x0,y0))]:
        edges.append(f'(gr_line (start {fmt(a[0]+60)} {fmt(a[1]+60)}) (end {fmt(b[0]+60)} {fmt(b[1]+60)}) (stroke (width 0.05) (type default)) (layer "Edge.Cuts"))')
    return f'''(kicad_pcb (version 20240108) (generator "shoggoth_raster_trace")
  (general (thickness 1.6)) (paper "A4")
  (layers (0 "F.Cu" signal) (31 "B.Cu" signal) (32 "B.Adhes" user "B.Adhesive") (33 "F.Adhes" user "F.Adhesive") (34 "B.Paste" user) (35 "F.Paste" user) (36 "B.SilkS" user "B.Silkscreen") (37 "F.SilkS" user "F.Silkscreen") (38 "B.Mask" user) (39 "F.Mask" user) (44 "Edge.Cuts" user) (46 "B.CrtYd" user "B.Courtyard") (47 "F.CrtYd" user "F.Courtyard") (48 "B.Fab" user) (49 "F.Fab" user))
  (setup (pad_to_mask_clearance 0))
{mod}
{chr(10).join(edges)}
)\n'''

def main():
    for d in ['source','ShoggothBadge.pretty','verification','previews']:
        (ROOT/d).mkdir(exist_ok=True)
    for origin,dest in [(INPUT,'mascot-original.png'),(REFERENCE,'style-reference.png')]:
        if origin.exists():
            shutil.copy2(origin,SOURCE/dest)
    im=Image.open(SOURCE/'mascot-original.png').convert('RGB')
    black=Image.new('1', im.size)
    yellow=Image.new('1', im.size)
    # Classify only dark ink and saturated yellow; neither green nor white is drawn.
    black.putdata([max(p)<108 for p in im.getdata()])
    yellow.putdata([p[0]>150 and p[1]>145 and p[2]<130 and p[0]-p[2]>70 and p[1]-p[2]>55 for p in im.getdata()])
    black.save(SOURCE/'classified-black.png')
    yellow.save(SOURCE/'classified-yellow.png')
    ink, inkpaths=trace(black)
    face, facepaths=trace(yellow)
    ink=clean(ink.intersection(pixel_support(black)))
    bbox=ink.bounds
    s=WIDTH_MM/(bbox[2]-bbox[0])
    ox=-(bbox[0]+bbox[2])/2
    oy=-(bbox[1]+bbox[3])/2
    to_mm=lambda g: scale(translate(g, xoff=ox, yoff=oy),xfact=s,yfact=s,origin=(0,0))
    ink,face=to_mm(ink),to_mm(face)
    # Inset the opening inside the true yellow region. No copper under green,
    # white eye regions, black face features or the black face perimeter.
    opening=clean(face.buffer(-MASK_SILK_CLEARANCE_MM, quad_segs=12).difference(
        ink.buffer(MASK_SILK_CLEARANCE_MM+0.01,quad_segs=12)))
    assert not opening.is_empty and opening.is_valid
    assert opening.difference(face).area<1e-9
    assert ink.intersection(opening).area<1e-9
    font=TTFont(SOURCE/'caption-font.ttf' if (SOURCE/'caption-font.ttf').exists() else FONT)
    glyphs=[text_geometry(t,font) for t in CAPTION_LINES]
    # Preserve a single common font scale and fit the first line into 34.4 mm.
    capscale=min(CAPTION_HEIGHT_MM/max(g.bounds[3]-g.bounds[1] for g in glyphs),
                 34.4/max(g.bounds[2]-g.bounds[0] for g in glyphs))
    y=ink.bounds[3]+CAPTION_GAP_MM
    captions=[]
    for g in glyphs:
        g=scale(g,xfact=capscale,yfact=-capscale,origin=(0,0))
        x0,y0,x1,y1=g.bounds
        g=translate(g,xoff=-(x0+x1)/2,yoff=y-y0)
        captions.append(g)
        y+=y1-y0+CAPTION_LINE_GAP_MM
    caption=unary_union(captions)
    badge=unary_union([ink,caption])
    result={}
    for name,silk in [('Shoggoth_Badge_35mm',badge),('Shoggoth_Mascot_35mm',ink)]:
        total=unary_union([silk,opening])
        bounds=total.bounds
        mod=module(name,silk,opening)
        (ROOT/'ShoggothBadge.pretty'/f'{name}.kicad_mod').write_text(mod)
        (SOURCE/f'{name}.svg').write_text(source_svg(name,silk,opening,bounds))
        illustrative=source_svg(name,silk,opening,bounds,layout=True)
        (ROOT/'previews'/f'{name}-pcb-illustration.svg').write_text(illustrative)
        cairosvg.svg2png(bytestring=illustrative.encode(),write_to=str(ROOT/'previews'/f'{name}-pcb-illustration.png'),output_width=1400)
        (ROOT/'verification'/f'{name}.kicad_pcb').write_text(demo_board(name,mod,bounds))
        (ROOT/'verification'/f'{name}.kicad_pro').write_text(json.dumps({'meta':{'filename':f'{name}.kicad_pro','version':1},'board':{'design_settings':{'rules':{'min_silk_clearance':0.1,'min_silk_text_height':0.8,'min_silk_text_thickness':0.12,'min_copper_edge_clearance':0.3}}}},indent=2)+'\n')
        result[name]={
            'width_mm':bounds[2]-bounds[0], 'height_mm':bounds[3]-bounds[1],
            'bounds_mm':list(bounds), 'silkscreen_area_mm2':silk.area,
            'copper_and_mask_area_mm2':opening.area,
            'mask_to_silk_clearance_mm':opening.distance(silk),
            'copper_outside_yellow_area_mm2':opening.difference(face).area,
            'copper_silk_intersection_area_mm2':opening.intersection(silk).area,
            'silk_polygon_count':len(pieces(silk)),
            'copper_polygon_count':len(pieces(opening)),
            'face_holes':sum(len(p.interiors) for p in polygons(opening)),
            'caption':CAPTION if 'Badge' in name else None,
            'caption_cap_height_mm':captions[0].bounds[3]-captions[0].bounds[1] if 'Badge' in name else None,
        }
    # Retain the exact font used so rebuilds are independent of font discovery.
    if FONT.exists() and not (SOURCE/'caption-font.ttf').exists():
        shutil.copy2(FONT,SOURCE/'caption-font.ttf')
    licence=Path('/usr/share/doc/fonts-dejavu-core/copyright')
    if licence.exists():
        shutil.copy2(licence,SOURCE/'caption-font-LICENSE.txt')
    (SOURCE/'parameters.json').write_text(json.dumps({
        'caption':CAPTION,'caption_lines':CAPTION_LINES,'width_mm':WIDTH_MM,
        'mask_to_source_yellow_edge_inset_mm':MASK_SILK_CLEARANCE_MM,
        'source_pixel_to_mm':s,'black_threshold_max_rgb_exclusive':108,
        'tracer':'system libpotrace; opttolerance=0.15px; flattened cubic tolerance=0.08px',
        'silk_colour_safety':'Traced ink intersected with exact classified-black pixel cell union; no curve-fitting fringes outside source black cells',
        'font':'DejaVu Sans Condensed Bold (outlines, bundled with license)',
        'source_sha256':hashlib.sha256((SOURCE/'mascot-original.png').read_bytes()).hexdigest(),
        'source_black_paths':inkpaths,'source_yellow_paths':facepaths,
    },indent=2)+'\n')
    (ROOT/'verification'/'geometry-report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    main()
