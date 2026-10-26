#!/usr/bin/env python3
"""Reproducible experiments; never opens or edits a source/canonical board.

Uses exact copied footprints. These fixtures intentionally include violations.
IPC was attempted before bootstrap and refused because there is no project.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CLI = '/home/h/.backplane-bend/kicad/10.99.0-bp.4/bin/kicad-cli'
LIB = ROOT / 'libraries/Backplane_MountingHole.pretty'

def parse(text):
    tokens = iter(re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text))
    def read(token):
        if token != '(':
            return token
        result = []
        for token in tokens:
            if token == ')':
                return result
            result.append(read(token))
        raise ValueError('unclosed s-expression')
    return read(next(tokens))

def dump(value):
    return '(' + ' '.join(map(dump, value)) + ')' if isinstance(value, list) else str(value)

def children(node, key):
    return [v for v in node[1:] if isinstance(v, list) and v[0] == key]

def one(node, key):
    return children(node, key)[0]

def uid(seed):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'backplane-holes-experiment/' + seed))

def footprint(variant, x, y, seed, zone_control=False):
    name = 'MountingHole_2.2mm_M2_ExposedSubstrate' + ('' if variant == 'center' else '_' + variant.title())
    fp = parse((LIB / (name + '.kicad_mod')).read_text())
    fp[1] = '"Backplane_MountingHole:' + name + '"'
    fp[:] = [v for v in fp if not isinstance(v, list) or v[0] not in ('version', 'generator')]
    fp.extend([['at', x, y], ['uuid', uid(seed)]])
    if zone_control:
        # Experimental ablation, only in this generated board: prove zone
        # exclusion samples fill when both original copper mechanisms are off.
        fp[:] = [v for v in fp if not isinstance(v,list) or v[0]!='zone']
        for pad in children(fp,'pad'):
            one(pad,'clearance')[1]='0'
    for i, v in enumerate(fp):
        if isinstance(v, list) and v[0] in ('property', 'fp_circle', 'fp_poly', 'fp_text', 'pad', 'zone'):
            v.append(['uuid', uid(seed + '/' + str(i))])
        if isinstance(v, list) and v[0] == 'property' and v[1] == '"Reference"':
            v[2] = '"' + seed + '"'
            v.append(['hide', 'yes'])
    return dump(fp)

def probe(kind, x, y, layer, seed):
    u = uid(seed)
    if kind == 'track':
        points=[(x,y),(x,y+0.4),(x+0.4,y+0.4),(x+0.4,y)]
        return ' '.join(f'(segment (start {a} {b}) (end {c} {d}) (width 0.2) (layer "{layer}") (net 1) (uuid {u if i==0 else uid(seed+str(i))}))' for i,((a,b),(c,d)) in enumerate(zip(points,points[1:]+points[:1])))
    if kind == 'via':
        return f'(via (at {x} {y}) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net 0) (uuid {u}))'
    if kind == 'pad':
        pad=f'(pad "1" smd circle (at 0 0) (size 0.4 0.4) (layers "{layer}") (uuid {uid(seed+"/pad")}))'
        if layer.startswith('In'):
            pad=f'(pad "1" thru_hole circle (at 0 0) (size 0.6 0.6) (drill 0.3) (layers "*.Cu" "*.Mask") (uuid {uid(seed+"/pad")}))'
        return f'(footprint "" (layer "F.Cu") (at {x} {y}) (uuid {u}) (attr board_only exclude_from_pos_files exclude_from_bom) {pad})'
    if kind == 'silk':
        return f'(gr_line (start {x} {y}) (end {x} {y+0.4}) (stroke (width 0.15) (type solid)) (layer "{layer}") (uuid {u}))'
    raise ValueError(kind)

def zone(x, y, layer, seed):
    points = [(x-8,y-8),(x+12,y-8),(x+12,y+12),(x-8,y+12)]
    return f'''(zone (net 1) (net_name "TEST") (layer "{layer}") (uuid {uid(seed)})
      (hatch edge 0.5) (connect_pads (clearance 0.2)) (min_thickness 0.1)
      (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3) (island_removal_mode 0))
      (polygon (pts {' '.join(f'(xy {px} {py})' for px,py in points)})))'''

def build(layers, negative, zone_control=False):
    tag = f'holes_{layers}layer_' + ('zone_control' if zone_control else 'negative' if negative else 'positive')
    layer_defs = '(0 "F.Cu" signal) ' + ('(2 "In1.Cu" signal) (4 "In2.Cu" signal) ' if layers == 4 else '') + '(31 "B.Cu" signal)'
    active = ['F.Cu', 'B.Cu'] if layers == 2 else ['F.Cu','In1.Cu','In2.Cu','B.Cu']
    # Separate cells ensure no probe can be rejected by a different hole.
    items, cases = [], []
    index = 0
    for variant in ('center','edge','corner'):
        for layer in active:
            for kind in ('track','pad','zone') + (('via',) if layer == 'F.Cu' else ()):
                if zone_control and kind!='zone':
                    continue
                x, y = 20 + (index % 6)*26, 20 + (index // 6)*26
                seed = f'{variant}-{layer}-{kind}'
                index += 1
                items.append(footprint(variant,x,y,seed,zone_control))
                if kind == 'zone':
                    items.append(zone(x,y,layer,seed+'/zone'))
                    # A connected same-net anchor retains the outside fill.
                    if layer.startswith('In'):
                        anchor=f'(pad "1" thru_hole circle (at 0 0) (size 1 1) (drill 0.3) (layers "*.Cu" "*.Mask") (net 1 "TEST") (uuid {uid(seed+"/anchor-pad")}))'
                    else:
                        anchor=f'(pad "1" smd circle (at 0 0) (size 1 1) (layers "{layer}") (net 1 "TEST") (uuid {uid(seed+"/anchor-pad")}))'
                    items.append(f'(footprint "" (layer "F.Cu") (at {x-6} {y-6}) (uuid {uid(seed+"/anchor")}) (attr board_only exclude_from_pos_files exclude_from_bom) {anchor})')
                    cases.append(dict(id=seed,kind=kind,variant=variant,layer=layer,center=[x,y],zone_uuid=uid(seed+'/zone')))
                else:
                    dx,dy = ((2.0,0) if variant == 'center' else (5.0,0) if variant == 'edge' else (5.0,5.0)) if negative else (-5.0,0)
                    items.append(probe(kind,x+dx,y+dy,layer,seed+'/probe'))
                    cases.append(dict(id=seed,kind=kind,variant=variant,layer=layer,center=[x,y],probe_uuid=uid(seed+'/probe'),expected=('hole_clearance' if variant=='center' else 'items_not_allowed') if negative else None))
    # Silk graphics inside the exposed-mask region, away from the actual drill.
    # These document actual stock behavior; no custom silk rule is added.
    for side in ('F.SilkS','B.SilkS'):
        if zone_control:
            continue
        x,y=20+(index%6)*26,20+(index//6)*26
        index+=1
        seed='silk-'+side
        items.append(footprint('edge',x,y,seed))
        items.append(probe('silk',x+(5 if negative else -5),y,side,seed+'/probe'))
        cases.append(dict(id=seed,kind='silk',probe_uuid=uid(seed+'/probe'),expected='silk_over_copper' if negative else None))
    height = 20 + ((index-1)//6)*26 + 16
    outline = f'(gr_rect (start 5 5) (end 164 {height}) (stroke (width 0.05) (type solid)) (fill none) (layer "Edge.Cuts") (uuid {uid(tag+"/outline")}))'
    text = f'''(kicad_pcb (version 20260206) (generator "pcbnew")
      (general (thickness 1.6)) (paper "A3")
      (layers {layer_defs} (36 "B.SilkS" user "b.silkscreen") (37 "F.SilkS" user "f.silkscreen")
       (38 "B.Mask" user) (39 "F.Mask" user) (44 "Edge.Cuts" user) (41 "Cmts.User" user "user.comments") (49 "F.Fab" user) (47 "F.CrtYd" user))
      (setup (pad_to_mask_clearance 0)) (net 0 "") (net 1 "TEST")
      {outline} {' '.join(items)})'''
    path=HERE/(tag+'.kicad_pcb')
    path.write_text(text+'\n')
    (HERE/(tag+'.cases.json')).write_text(json.dumps(cases,indent=2)+'\n')
    return path,cases

def contains(points,x,y):
    inside=False
    for (x1,y1),(x2,y2) in zip(points,points[1:]+points[:1]):
        if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1:
            inside=not inside
    return inside

def filled_at(board,zone_uuid,x,y):
    z=next(v for v in children(board,'zone') if one(v,'uuid')[1].strip('"')==zone_uuid)
    for poly in children(z,'filled_polygon'):
        points=[(float(p[1]),float(p[2])) for p in one(poly,'pts')[1:]]
        if contains(points,x,y):
            return True
    return False

def run():
    manifest=json.loads((ROOT/'sources/holes/manifest.json').read_text())
    assert len(manifest['entries'])==60
    assert len(list(LIB.glob('*.kicad_mod')))==60
    for entry in manifest['entries']:
        p=ROOT/entry['destination']
        assert hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256'], f'Original footprint modified: {p}'
        fp=parse(p.read_text())
        pad=one(fp,'pad')
        assert pad[2]=='np_thru_hole' and pad[3]=='circle'
        for z in children(fp,'zone'):
            assert one(z,'layers')[1:]==['"*.Cu"']
            assert one(z,'keepout')[1:]==[['tracks','not_allowed'],['vias','not_allowed'],['pads','not_allowed'],['copperpour','not_allowed'],['footprints','allowed']]
    (HERE/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "Backplane_MountingHole") (type "KiCad") (uri "${KIPRJMOD}/../../libraries/Backplane_MountingHole.pretty") (options "") (descr "Experiment-only local table")))\n')
    summary=[]
    for layers in (2,4):
        for negative,control in ((False,False),(True,False),(False,True)):
            path,cases=build(layers,negative,control)
            report=path.with_suffix('.drc.json')
            cmd=[CLI,'pcb','drc','--format','json','--refill-zones','--save-board','--severity-all','-o',str(report),str(path)]
            result=subprocess.run(cmd,capture_output=True,text=True)
            path.with_suffix('.drc.log').write_text('$ '+' '.join(cmd)+'\n'+result.stdout+result.stderr)
            if result.returncode:
                raise RuntimeError(result.stdout+result.stderr)
            data=json.loads(report.read_text())
            errors=data['violations']
            board=parse(path.read_text())
            checks=[]
            allowed={'lib_footprint_mismatch'} if control else {'items_not_allowed','hole_clearance','silk_over_copper','pth_inside_courtyard'} if negative else set()
            unexpected=[v['type'] for v in errors if v['type'] not in allowed]
            checks.append(dict(id='no-unexpected-drc-violations',actual=unexpected,pass_=not unexpected))
            for case in cases:
                if case['kind']=='zone':
                    x,y=case['center']
                    samples=[(x+2,y)] + ([(x+5,y)] if case['variant']=='edge' else [(x+5,y+5)] if case['variant']=='corner' else [])
                    excluded=all(not filled_at(board,case['zone_uuid'],a,b) for a,b in samples)
                    retained=filled_at(board,case['zone_uuid'],x-6,y-5)
                    expected_fill=all(filled_at(board,case['zone_uuid'],a,b) for a,b in samples) if control else False
                    checks.append(dict(id=case['id'],excluded=excluded,outside_retained=retained,control_fill=expected_fill,pass_=(expected_fill if control else excluded) and retained))
                else:
                    matches=[v for v in errors if any(i.get('uuid')==case['probe_uuid'] or i.get('uuid')==uid(case['id']+'/probe/pad') for i in v.get('items',[]))]
                    types=[v['type'] for v in matches]
                    expected=case['expected']
                    ok=any(expected in t for t in types) if expected else not matches
                    checks.append(dict(id=case['id'],expected=expected,actual=types,pass_=ok))
            summary.append(dict(board=path.name,violations=dict(Counter(v['type'] for v in errors)),unconnected_count=len(data.get('unconnected_items',[])),checks=checks,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    (HERE/'results.json').write_text(json.dumps(summary,indent=2)+'\n')
    for path in HERE.glob('holes_*.kicad_prl'):
        path.unlink()
    failures=[(b['board'],c) for b in summary for c in b['checks'] if not c['pass_']]
    print(json.dumps(dict(boards=len(summary),checks=sum(len(b['checks']) for b in summary),failures=failures),indent=2))
    return bool(failures)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    raise SystemExit(run())
