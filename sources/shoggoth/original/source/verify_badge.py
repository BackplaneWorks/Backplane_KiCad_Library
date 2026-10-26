#!/usr/bin/env python3
"""Verify delivered, parsed geometry and actual KiCad CLI exports.

All CLI writes are confined to this bundle's verification directory.
No pcbnew, user board, project settings or global library tables are used.
"""
from pathlib import Path
import io
import re
import json
import math
import shutil
import hashlib
import subprocess
import xml.etree.ElementTree as ET
from collections import defaultdict

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import shapely
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.affinity import scale, translate
import cairosvg
import generate_badge as gen

ROOT=gen.ROOT
V=ROOT/'verification'
CLI='/home/h/.backplane-bend/kicad/10.99.0-bp.4/bin/kicad-cli'
LOG=[]

def cli(*args):
    p=subprocess.run([CLI,*map(str,args)],text=True,capture_output=True,timeout=60)
    LOG.append({'argv':[CLI,*map(str,args)],'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
    if p.returncode:
        raise RuntimeError(p.stdout+p.stderr)
    return p.stdout

def parse_sexpr(text):
    tokens=iter(re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+',text))
    def node(first):
        assert first=='('
        result=[]
        for t in tokens:
            if t==')':
                return result
            if t=='(':
                result.append(node(t))
            else:
                result.append(json.loads(t) if t.startswith('"') else t)
        raise ValueError('Unclosed s-expression')
    return node(next(tokens))

def child(node,key):
    return next(v for v in node if isinstance(v,list) and v and v[0]==key)

def read_footprint(path):
    t=parse_sexpr(path.read_text())
    assert t[0]=='footprint'
    bylayer=defaultdict(list)
    for p in t[2:]:
        if not isinstance(p,list):
            continue
        if p[0]=='fp_poly':
            assert child(p,'stroke')[1][1]=='0'
            assert child(p,'fill')[1] in ['solid','yes']
            pts=child(p,'pts')
            g=Polygon([(float(q[1]),float(q[2])) for q in pts[1:]])
            assert g.is_valid and not g.interiors and g.area>0
            bylayer[child(p,'layer')[1]].append(g)
        elif p[0]=='fp_text':
            assert 'hide' in p and child(p,'layer')[1]=='F.Fab'
        elif p[0]=='property':
            assert child(p,'hide')[1]=='yes' and child(p,'layer')[1]=='F.Fab'
        else:
            assert p[0] in ['version','generator','generator_version','layer','descr','tags','attr','embedded_fonts','duplicate_pad_numbers_are_jumpers'],p[0]
    return t,{k:unary_union(v) for k,v in bylayer.items()}

def render_composite():
    # These are KiCad's actual exported layer polygons, rasterized and recoloured.
    images={}
    for p in (V/'layers').glob('*.svg'):
        data=p.read_text()
        # Supersample with common-edge rasterization to avoid artificial AA
        # seams between exact adjoining fill pieces. No geometry is modified.
        data=data.replace('<svg\n','<svg shape-rendering="crispEdges"\n',1)
        raster=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=data.encode(),output_width=2800,background_color='white'))).convert('RGBA')
        backing=Image.new('RGBA',raster.size,'white')
        backing.alpha_composite(raster)
        target=(1400,round(raster.height/2))
        backing.convert('RGB').resize(target,Image.Resampling.LANCZOS).save(ROOT/'previews'/p.with_suffix('.png').name)
        key=p.stem.split('35mm-')[1]
        colour={'F_Cu':'#dab45c','F_Silkscreen':'#f5f3de'}.get(key)
        if colour:
            data=data.replace('#000000',colour)
            raw=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=data.encode(),output_width=2800))).convert('RGBA')
            images[key]=raw.resize(target,Image.Resampling.LANCZOS)
    base=Image.new('RGBA',images['F_Cu'].size,'#244d3f')
    for key in ['F_Cu','F_Silkscreen']:
        base.alpha_composite(images[key])
    # Explicit preview label outside the example board area.
    out=Image.new('RGB',(base.width,base.height+98),'#f3f2e9')
    out.paste(base,(0,98))
    d=ImageDraw.Draw(out)
    f=ImageFont.truetype(str(gen.SOURCE/'caption-font.ttf'),24)
    measurements=json.loads((V/'geometry-report.json').read_text())['Shoggoth_Badge_35mm']
    d.text((24,17),f'ACTUAL KiCad layer composite | 35 x {measurements["height_mm"]:.3f} mm',font=f,fill='#172d27')
    d.text((24,51),'Illustrative mask / ink / metal colours; not physical qualification.',font=f,fill='#172d27')
    out.save(ROOT/'previews'/'Shoggoth_Badge_35mm-kicad-composite.png')
    # Printable physical-size proof; SVG root explicitly uses millimetres.
    src=ET.fromstring((gen.SOURCE/'Shoggoth_Badge_35mm.svg').read_text())
    ns='{http://www.w3.org/2000/svg}'
    src.set('x','7');src.set('y','15')
    proof=ET.Element(ns+'svg',{'width':'50mm','height':'66mm','viewBox':'0 0 50 66'})
    ET.SubElement(proof,ns+'rect',{'width':'50','height':'66','fill':'white'})
    ET.SubElement(proof,ns+'text',{'x':'5','y':'6','font-size':'2.3','font-family':'sans-serif'}).text='35 mm badge — print at 100%'
    ET.SubElement(proof,ns+'text',{'x':'5','y':'10','font-size':'1.7','font-family':'sans-serif'}).text='Size proof only; colours are illustrative.'
    proof.append(src)
    ET.SubElement(proof,ns+'path',{'d':'M5 56 H15 M5 55 V57 M15 55 V57','fill':'none','stroke':'black','stroke-width':'0.15'})
    ET.SubElement(proof,ns+'text',{'x':'5','y':'60','font-size':'2','font-family':'sans-serif'}).text='10 mm reference'
    data=ET.tostring(proof)
    (ROOT/'previews'/'actual-size-proof.svg').write_bytes(data)
    cairosvg.svg2pdf(bytestring=data,write_to=str(ROOT/'previews'/'actual-size-proof.pdf'))

def main():
    report={}
    production={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'ShoggothBadge.pretty').glob('*.kicad_mod')}
    cli('--version'); cli('version','--format','about')
    for folder in ['footprint-load','layers','roundtrip-svg']:
        (V/folder).mkdir(exist_ok=True)
    cli('fp','export','svg','--output',V/'footprint-load','--layers','F.SilkS,F.Cu,F.Mask',ROOT/'ShoggothBadge.pretty')
    # Round-trip only disposable copies. The production library stays in stable
    # KiCad 8 syntax (20240108); runtime saves use its current native version.
    staging=V/'roundtrip.pretty'
    if staging.exists():
        shutil.rmtree(staging)
    cli('fp','upgrade','--force','--output',staging,ROOT/'ShoggothBadge.pretty')
    cli('fp','export','svg','--output',V/'roundtrip-svg','--layers','F.SilkS,F.Cu,F.Mask',staging)
    for p in sorted((ROOT/'ShoggothBadge.pretty').glob('*.kicad_mod')):
        tree,layers=read_footprint(p)
        rt,roundlayers=read_footprint(staging/p.name)
        assert child(tree,'version')[1]=='20240108'
        assert set(child(tree,'attr')[1:])=={'board_only','exclude_from_pos_files','exclude_from_bom'}
        assert set(layers)=={'F.SilkS','F.Cu','F.Mask'}
        silk,cu,mask=(layers[k] for k in ['F.SilkS','F.Cu','F.Mask'])
        assert cu.symmetric_difference(mask).area<1e-10
        assert cu.intersection(silk).area<1e-10
        assert cu.distance(silk)>0.109
        assert sum(len(q.interiors) for q in gen.polygons(cu))==3
        delta={k:layers[k].symmetric_difference(roundlayers[k]).area for k in layers}
        assert max(delta.values())<0.0001,delta
        total=unary_union(list(layers.values()))
        assert abs(total.bounds[2]-total.bounds[0]-35)<0.00001
        # Validate against yellow trace in original image coordinates.
        ink,_=gen.trace(Image.open(gen.SOURCE/'classified-black.png'))
        ink=gen.clean(ink.intersection(gen.pixel_support(Image.open(gen.SOURCE/'classified-black.png'))))
        face,_=gen.trace(Image.open(gen.SOURCE/'classified-yellow.png'))
        x0,y0,x1,y1=ink.bounds
        s=35/(x1-x0)
        mm=lambda g:scale(translate(g,xoff=-(x0+x1)/2,yoff=-(y0+y1)/2),xfact=s,yfact=s,origin=(0,0))
        face=mm(face)
        assert cu.difference(face).area<1e-9
        # Exact pixel support clipping prevents curve-fitting overshoot into
        # the protected green and white source regions.
        rgb=np.asarray(Image.open(gen.SOURCE/'mascot-original.png').convert('RGB')).astype(float)
        # Original black ink is green-tinted (e.g. RGB 12,36,10), so hue alone
        # cannot distinguish it from the body. Require body-level brightness.
        green=(rgb[:,:,1]>=130)&(rgb[:,:,0]>=90)&(rgb[:,:,2]>=70)&(rgb[:,:,1]-rgb[:,:,0]>22)&(rgb[:,:,1]-rgb[:,:,2]>22)
        white=(rgb.min(axis=2)>245)
        sample={}
        # Use the delivered footprint, excluding the caption outside the mascot.
        art=unary_union([silk.intersection(shapely.geometry.box(-18,-15,18,14.4)),cu])
        for key,valid in [('solid_green',green),('white',white)]:
            ys,xs=np.nonzero(valid)
            x=(xs+0.5-(x0+x1)/2)*s
            y=(ys+0.5-(y0+y1)/2)*s
            inside=shapely.contains_xy(art,x,y)
            sample[key]={'source_pixel_centres_tested':len(xs),'centres_inside_traced_geometry':int(inside.sum())}
            assert not inside.any(),sample
        # Measure enclosed negative detail, not the polygon vertices' spacing.
        holes=[]
        for q in gen.polygons(mm(ink)):
            for ring in q.interiors:
                hole=Polygon(ring)
                corners=list(hole.minimum_rotated_rectangle.exterior.coords)
                holes.append(min(math.dist(a,b) for a,b in zip(corners,corners[1:])))
        # Morphological screening: recover after a 0.15 mm diameter opening.
        # This is a feature screen, not a guaranteed minimum stroke certificate.
        mmink=mm(ink)
        recovered=mmink.buffer(-0.075,quad_segs=12).buffer(0.075,quad_segs=12)
        lost=mmink.difference(recovered)
        cli('pcb','drc','--format','json','--output',V/f'{p.stem}-drc.json','--severity-all',V/f'{p.stem}.kicad_pcb')
        drc=json.loads((V/f'{p.stem}-drc.json').read_text())
        assert not drc['violations'] and not drc['unconnected_items']
        report[p.stem]={
            'production_format':20240108,'kiCAD_roundtrip_format':int(child(rt,'version')[1]),
            'production_file_sha256':production[p.name],
            'width_mm':total.bounds[2]-total.bounds[0],
            'height_mm':total.bounds[3]-total.bounds[1],
            'layers':sorted(layers),'copper_equals_mask':True,'paste_pads_nets':0,
            'face_holes':3,'silk_to_mask_mm':cu.distance(silk),
            'copper_outside_yellow_mm2':cu.difference(face).area,
            'roundtrip_geometry_difference_mm2':delta,
            'source_pixel_screen':sample,
            'smallest_enclosed_silk_negative_detail_short_caliper_mm':min(holes),
            'mascot_silk_0_15mm_morphological_opening_lost_area_mm2':lost.area,
            'mascot_silk_0_15mm_morphological_opening_lost_area_percent':100*lost.area/mmink.area,
            'feature_note':f'Curved contours and tapered tips have no single guaranteed minimum width. Smallest enclosed negative eye detail short caliper is {min(holes):.6f} mm. Fine details need fab confirmation; no 25 mm variant supplied.',
            'drc_violations':len(drc['violations']),'unconnected_items':len(drc['unconnected_items']),
        }
    # These newer-format files are disposable verification only; do not ship them
    # as another importable variant of the footprint library.
    shutil.rmtree(staging)
    assert production=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'ShoggothBadge.pretty').glob('*.kicad_mod')}
    cli('pcb','export','svg','--output',V/'layers','--layers','F.SilkS,F.Cu,F.Mask,F.Paste','--mode-multi','--page-size-mode','2','--exclude-drawing-sheet','--black-and-white',V/'Shoggoth_Badge_35mm.kicad_pcb')
    render_composite()
    cu=np.asarray(Image.open(ROOT/'previews'/'Shoggoth_Badge_35mm-F_Cu.png'))
    mask=np.asarray(Image.open(ROOT/'previews'/'Shoggoth_Badge_35mm-F_Mask.png'))
    paste=np.asarray(Image.open(ROOT/'previews'/'Shoggoth_Badge_35mm-F_Paste.png'))
    assert np.array_equal(cu,mask)
    assert np.all(paste==255)
    (V/'verification-report.json').write_text(json.dumps(report,indent=2)+'\n')
    (V/'cli-log.json').write_text(json.dumps(LOG,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    main()
