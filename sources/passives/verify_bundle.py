#!/usr/bin/env python3
"""Independent saved-asset checks, KiCad SVG loading, and deterministic rebuild."""
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
DENSITIES=('least','nominal','most')

def parse(path):
    tokens=re.findall(r'"(?:\\.|[^"\\])*"|\(|\)|[^\s()]+',path.read_text())
    stack=[]
    result=None
    for token in tokens:
        if token=='(':
            node=[]
            if stack:stack[-1].append(node)
            stack.append(node)
        elif token==')':
            assert stack, path
            result=stack.pop()
        else:
            assert stack,path
            stack[-1].append(json.loads(token) if token.startswith('"') else token)
    assert not stack and result[0]=='footprint',path
    return result

def fields(node,key):return [x for x in node if isinstance(x,list) and x and x[0]==key]
def field(node,key):
    result=fields(node,key)
    assert len(result)==1,(key,result)
    return result[0]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def pads(node):
    return {x[1]:x for x in fields(node,'pad') if 'F.Cu' in field(x,'layers')}
def geometry(node):
    pad=pads(node)['1']
    x,y=map(float,field(pad,'at')[1:3]);sx,sy=map(float,field(pad,'size')[1:3])
    cy=next(x for x in fields(node,'fp_rect') if field(x,'layer')[1]=='F.CrtYd')
    fab=next(x for x in fields(node,'fp_rect') if field(x,'layer')[1]=='F.Fab')
    a,b=field(cy,'start'),field(cy,'end')
    return {'pad_x_mm':sx,'pad_y_mm':sy,'center_spacing_mm':abs(x)*2,'inner_gap_mm':abs(x)*2-sx,'outer_span_mm':abs(x)*2+sx,'courtyard_x_mm':abs(float(b[1])-float(a[1])),'courtyard_y_mm':abs(float(b[2])-float(a[2])),'fab_rect':fab}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kicad-cli',default='/home/h/.backplane-bend/kicad/10.99.0-bp.4/bin/kicad-cli')
    parser.add_argument('--original',type=Path,help='Optional recovered amemb footprints directory (read only)')
    args=parser.parse_args()
    out=ROOT/'verification/passives';out.mkdir(parents=True,exist_ok=True)
    report={'kicad_version':subprocess.check_output([args.kicad_cli,'--version'],text=True).strip(),'counts':{},'original_geometry_matches':[],'original_geometry_differences':[],'missing_models':[]}
    for manifest in ['upstream.sha256.json','configs.sha256.json']:
        prefix=HERE/'upstream' if manifest.startswith('upstream') else HERE
        for name,digest in json.loads((HERE/manifest).read_text()).items():
            assert sha(prefix/name)==digest,(manifest,name)
    report['source_and_config_hashes_pass']=True
    for item in json.loads((HERE/'recovered/original-outputs.json').read_text()):
        assert sha(HERE/'recovered'/item['snapshot'])==item['sha256'],item
    for item in json.loads((ROOT/'3dmodels/passives-provenance.json').read_text()):
        assert sha(ROOT/item['file'])==item['sha256'],item
    report['recovered_original_and_model_hashes_pass']=True
    report['original_comparison_directory']=str(args.original) if args.original else None
    measurements={};files={};hashes={};rows=[]
    for density in DENSITIES:
        lib=ROOT/'libraries'/f'Backplane_Passives_{density.title()}.pretty'
        fps=sorted(lib.glob('*.kicad_mod'))
        assert len(fps)==(45 if density=='least' else 44),(density,len(fps))
        report['counts'][density]=dict(Counter(p.name[0] for p in fps))
        svg=out/'svg'/density;svg.mkdir(parents=True,exist_ok=True)
        result=subprocess.run([args.kicad_cli,'fp','export','svg','--layers','F.Cu,F.Paste,F.SilkS,F.Fab,F.CrtYd','--output',str(svg),str(lib)],capture_output=True,text=True)
        (out/f'kicad-svg-{density}.log').write_text(result.stdout+result.stderr)
        assert result.returncode==0 and not re.search('Failed|Error',result.stdout+result.stderr),result
        assert {p.stem for p in svg.glob('*.svg')}=={p.stem for p in fps}
        for path in fps:
            node=parse(path)
            assert node[1]==path.stem,path
            xml=ET.parse(svg/(path.stem+'.svg')).getroot()
            assert xml.tag.endswith('svg') and len(xml)>2,path
            assert set(pads(node))=={'1','2'},path
            assert not fields(node,'fp_poly'),path
            for number,pad in pads(node).items():
                assert pad[2:4]==['smd','roundrect'],path
                assert set(field(pad,'layers')[1:]) in ({'F.Cu','F.Mask','F.Paste'},{'F.Cu','F.Mask'}),path
                assert all(float(v)>0 for v in field(pad,'size')[1:3]),path
            m=geometry(node)
            assert m['inner_gap_mm']>0,path
            p1,p2=pads(node).values()
            assert field(p1,'size')==field(p2,'size')
            assert float(field(p1,'at')[1])==-float(field(p2,'at')[1])
            assert m['courtyard_x_mm']>=m['outer_span_mm'] and m['courtyard_y_mm']>=m['pad_y_mm'],path
            model=fields(node,'model')
            if model:
                assert len(model)==1
                assert model[0][1].startswith('${BACKPLANE_KICAD_LIBRARY}/3dmodels/'),path
                modelpath=ROOT/model[0][1].split('}/',1)[1]
                assert modelpath.is_file() and modelpath.stat().st_size>100,path
                assert field(model[0],'scale')[1]==['xyz','1','1','1'],path
                assert field(model[0],'offset')[1]==['xyz','0','0','0'],path
                assert field(model[0],'rotate')[1]==['xyz','0','0','0'],path
            else:report['missing_models'].append(f'{lib.stem}:{path.stem}')
            if not path.stem.endswith('_LegacyLocal'):
                measurements.setdefault(path.stem,{})[density]=m
            else:
                report['legacy_local_geometry']=m
            files[str(path.relative_to(ROOT))]=sha(path)
            hashes[str(path.relative_to(ROOT/'libraries'))]=sha(path)
            if args.original:
                fam={'C':'Capacitor_SMD','R':'Resistor_SMD','L':'Inductor_SMD'}[path.stem[0]]
                old=args.original/f'amemb-{fam}.pretty'/(path.stem+{'least':'_L','nominal':'','most':'_M'}[density]+'.kicad_mod')
                if path.stem.endswith('_LegacyLocal'):
                    old=args.original/'amemb-Inductor_SMD.pretty/L_0806_2016Metric_L.kicad_mod'
                if old.is_file():
                    oldnode=parse(old)
                    oldm=geometry(oldnode)
                    same=all(abs(m[k]-oldm[k])<1e-8 for k in m if k!='fab_rect')
                    key='original_geometry_matches' if same else 'original_geometry_differences'
                    report[key].append(str(path.relative_to(ROOT)))
        print(f'{density}: KiCad loaded and exported {len(fps)} SVGs')
    for name,variants in sorted(measurements.items()):
        l,n,m=(variants[x] for x in DENSITIES)
        for k in ['pad_x_mm','pad_y_mm','center_spacing_mm','outer_span_mm','courtyard_x_mm','courtyard_y_mm']:
            assert l[k]<n[k]<m[k],(name,k,l[k],n[k],m[k])
        assert abs(l['inner_gap_mm']-m['inner_gap_mm'])<1e-8,name
        assert l['fab_rect']==n['fab_rect']==m['fab_rect'],name
        for density,geom in variants.items():
            rows.append({'name':name,'density':density,**{k:round(v,6) for k,v in geom.items() if k!='fab_rect'}})
    with (out/'measurements.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    delta_rows=[]
    for name,variants in sorted(measurements.items()):
        for start,end in [('least','nominal'),('nominal','most')]:
            delta_rows.append({'name':name,'from':start,'to':end,**{k:round(variants[end][k]-variants[start][k],6) for k in variants[start] if k!='fab_rect'}})
    with (out/'density-deltas.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(delta_rows[0]));w.writeheader();w.writerows(delta_rows)
    # Independent fresh-directory build, compare all asset bytes with delivered files.
    rebuild=HERE/'build/determinism'
    if rebuild.exists():shutil.rmtree(rebuild)
    subprocess.run([sys.executable,str(HERE/'build_bundle.py'),'--output',str(rebuild)],check=True)
    rebuilt={str(p.relative_to(rebuild)):sha(p) for p in rebuild.glob('*.pretty/*.kicad_mod')}
    assert hashes==rebuilt,'Fresh-build SHA256 mismatch'
    report.update({'footprints_loaded':sum(sum(x.values()) for x in report['counts'].values()),'all_density_deltas_pass':True,'fab_geometry_unchanged':True,'inner_gap_unchanged':True,'deterministic_byte_matches':len(rebuilt),'footprint_sha256':files})
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f"Deterministic: {len(rebuilt)} byte-identical assets; original geometry matches: {len(report['original_geometry_matches'])}; differences: {len(report['original_geometry_differences'])}")

if __name__=='__main__':main()
