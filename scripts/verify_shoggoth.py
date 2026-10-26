#!/usr/bin/env python3
"""KiCad load, native roundtrip, per-layer plots, DRC and art geometry checks."""
from pathlib import Path
import sys, re, json, subprocess, hashlib, shutil
import shapely
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.affinity import scale

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'sources/shoggoth/original/source'))
import verify_badge as original
from build_shoggoth import read_layers
CLI='/home/h/.backplane-bend/kicad/10.99.0-bp.4/bin/kicad-cli'
V=ROOT/'verification/shoggoth'
LIB=ROOT/'libraries/Backplane_Shoggoth.pretty'
LOG=[]

def cli(*args):
    p=subprocess.run([CLI,*map(str,args)],text=True,capture_output=True,timeout=60)
    LOG.append({'argv':list(map(str,args)),'code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
    if p.returncode: raise RuntimeError(p.stdout+p.stderr)

def geometry(path):
    tree=original.parse_sexpr(path.read_text())
    d={}
    for p in tree:
        if isinstance(p,list) and p[0]=='fp_poly':
            layer=original.child(p,'layer')[1]
            pts=original.child(p,'pts')
            g=Polygon([(float(q[1]),float(q[2])) for q in pts[1:]])
            assert g.is_valid and g.area>0
            d.setdefault(layer,[]).append(g)
    return {k:unary_union(v) for k,v in d.items()}

def main():
    V.mkdir(exist_ok=True,parents=True)
    for folder in ['footprint-load','roundtrip-load','layers']:
        (V/folder).mkdir(exist_ok=True)
    output=V/'roundtrip.pretty'
    if output.exists(): shutil.rmtree(output)
    cli('fp','export','svg','--output',V/'footprint-load','--layers','F.Cu,F.Mask,F.SilkS',LIB)
    cli('fp','upgrade','--force','--output',output,LIB)
    cli('fp','export','svg','--output',V/'roundtrip-load','--layers','F.Cu,F.Mask,F.SilkS',output)
    assert len(list((V/'footprint-load').glob('*.svg')))==6
    assert len(list((V/'roundtrip-load').glob('*.svg')))==6
    report={}
    for p in sorted(LIB.glob('*.kicad_mod')):
        name=p.stem
        print('Checking '+name,flush=True)
        g=read_layers(p); rt=geometry(output/p.name)
        assert set(g)==set(rt)=={'F.Cu','F.Mask','F.SilkS'}
        assert g['F.Cu'].equals(g['F.Mask'])
        assert g['F.Cu'].distance(g['F.SilkS'])>.109
        assert g['F.Cu'].intersection(g['F.SilkS']).area<1e-9
        assert '(pad ' not in p.read_text() and 'F.Paste' not in p.read_text()
        deltas={k:g[k].symmetric_difference(rt[k]).area for k in g}
        assert max(deltas.values())<.0001,deltas
        kind='Badge' if 'Badge' in name else 'Mascot'
        size=int(name.split('_')[-1].replace('mm',''))
        orig=read_layers(ROOT/'sources/shoggoth/original/ShoggothBadge.pretty'/f'Shoggoth_{kind}_35mm.kicad_mod')
        if size==35: assert p.read_bytes()==(ROOT/'sources/shoggoth/original/ShoggothBadge.pretty'/p.name).read_bytes()
        source_deltas={k:g[k].difference(scale(orig[k],xfact=size/35,yfact=size/35,origin=(0,0))).area for k in g}
        # 25 mm edits subtract ink/copper only; 50 mm rounded coordinates have tiny error.
        grid_residual={k:g[k].difference(scale(orig[k],xfact=size/35,yfact=size/35,origin=(0,0)).buffer(.000002)).area for k in g}
        assert max(grid_residual.values())<1e-10,grid_residual
        cli('pcb','drc','--format','json','--output',V/f'{name}-drc.json','--severity-all',V/f'{name}.kicad_pcb')
        drc=json.loads((V/f'{name}-drc.json').read_text())
        assert not drc['violations'] and not drc['unconnected_items'],drc
        cli('pcb','export','svg','--output',V/'layers','--layers','F.Cu,F.Mask,F.SilkS,F.Paste','--mode-multi','--page-size-mode','2','--exclude-drawing-sheet','--black-and-white',V/f'{name}.kicad_pcb')
        plots=list((V/'layers').glob(name+'-*.svg'))
        cu=next(f for f in plots if f.stem.endswith('F_Cu'))
        mask=next(f for f in plots if f.stem.endswith('F_Mask'))
        paste=next(f for f in plots if f.stem.endswith('F_Paste'))
        # Native plots may differ in metadata; compare rasterized actual geometry.
        import cairosvg, io, numpy as np
        from PIL import Image
        raster=lambda f:np.asarray(Image.open(io.BytesIO(cairosvg.svg2png(url=str(f),output_width=1200,background_color='white'))).convert('RGB'))
        assert np.array_equal(raster(cu),raster(mask))
        assert np.all(raster(paste)==255)
        report[name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                      'roundtrip_difference_mm2':deltas,'outside_scaled_source_mm2':source_deltas,
                      'outside_source_with_2nm_grid_allowance_mm2':grid_residual,
                      'copper_mask_raster_equal':True,'paste_raster_blank':True,
                      'drc_violations':0,'unconnected_items':0,'layer_plots':[str(f.relative_to(ROOT)) for f in plots]}
    shutil.rmtree(output)
    (V/'cli-log.json').write_text(json.dumps(LOG,indent=2)+'\n')
    (V/'verification-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('All six Shoggoth footprints passed.',flush=True)

if __name__=='__main__':main()
