#!/usr/bin/env python3
"""Generate an explicitly disposable catalogue staging board for IPC import.

The canonical board is edited by ipc_catalogue.py, never by this generator.
"""
from pathlib import Path
import sys,json,re,uuid
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'sources/shoggoth/original/source'))
class Quoted(str): pass

def parse_sexpr(text):
    tokens=iter(re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+',text))
    def node():
        result=[]
        for token in tokens:
            if token==')':return result
            if token=='(':result.append(node())
            else:result.append(Quoted(json.loads(token)) if token.startswith('"') else token)
        raise ValueError('unclosed expression')
    assert next(tokens)=='('
    return node()

def atom(v):
    return json.dumps(v,ensure_ascii=False) if isinstance(v,Quoted) else v
def sexpr(t):
    return '('+' '.join(sexpr(x) if isinstance(x,list) else atom(x) for x in t)+')'

def footprint(lib,name,x,y,ref):
    tree=parse_sexpr((ROOT/'libraries'/f'{lib}.pretty'/f'{name}.kicad_mod').read_text())
    tree[1]=Quoted(lib+':'+name)
    tree=[v for v in tree if not isinstance(v,list) or v[0] not in ['version','generator','at','uuid']]
    tree.extend([['at',str(x),str(y)],['uuid',Quoted(str(uuid.uuid5(uuid.NAMESPACE_URL,lib+name+ref)))]])
    for p in tree:
        if isinstance(p,list) and p[0]=='property' and p[1] in ['Reference','Value']:
            if p[1]=='Reference':p[2]=Quoted(ref)
            if not any(isinstance(v,list) and v[0]=='hide' for v in p):p.append(['hide','yes'])
        elif isinstance(p,list) and p[0]=='fp_text' and p[1] in ['reference','value']:
            if p[1]=='reference':p[2]=Quoted(ref)
            if 'hide' not in p:p.append('hide')
        elif isinstance(p,list) and p[0]=='model':
            p[1]=Quoted(p[1].replace('${BACKPLANE_KICAD_LIBRARY}/','${KIPRJMOD}/../../'))
    return sexpr(tree)

def label(text,x,y,size=1):
    return f'(gr_text {json.dumps(text)} (at {x} {y}) (layer "F.SilkS") (effects (font (size {size} {size}) (thickness .15))))'

def main():
    parts=[]
    parts += [label('BACKPLANE KICAD LIBRARY',120,10,2),label('CATALOGUE / NO CIRCUIT / NOT FOR MANUFACTURE',120,15,1)]
    # Artwork keeps its mascot-centred origin, including the badge caption below.
    for row,kind in enumerate(['Mascot','Badge']):
        for size,x in zip([25,35,50],[28,68,120]):
            y=47+row*61
            parts.append(footprint('Backplane_Shoggoth',f'Shoggoth_{kind}_{size}mm',x,y,f'LOGO{row}{size}'))
            parts.append(label(f'{kind.upper()} {size} mm',x,y-26,1))
    parts += [label('EXPOSED SUBSTRATE / NPTH',193,22,1),label('CENTER       EDGE       CORNER',193,27,.85)]
    for row,(drill,screw) in enumerate([('2.2','M2'),('3.2','M3'),('4.3','M4')]):
        for col,suffix in enumerate(['','_Edge','_Corner']):
            name=f'MountingHole_{drill}mm_{screw}_ExposedSubstrate{suffix}'
            if not (ROOT/'libraries/Backplane_MountingHole.pretty'/f'{name}.kicad_mod').exists():
                matches=list((ROOT/'libraries/Backplane_MountingHole.pretty').glob(f'*_{screw}_ExposedSubstrate{suffix}.kicad_mod'))
                assert len(matches)==1
                name=matches[0].stem
            x=166+col*25;y=39+row*23
            parts.append(footprint('Backplane_MountingHole',name,x,y,f'H{row}{col}'))
        parts.append(label(f'{screw} / {drill} mm',194,50+row*23,.85))
    parts.append(label('R / C / L 0603: DENSITY COMPARISON',195,104,.95))
    for col,density in enumerate(['Least','Nominal','Most']):
        x=168+col*25
        parts.append(label(density.upper(),x,110,.9))
        for row,kind in enumerate(['R','C','L']):
            y=117+row*9
            parts.append(footprint('Backplane_Passives_'+density,f'{kind}_0603_1608Metric',x,y,f'{kind}{col+1}'))
            parts.append(label(kind,x+5,y,.9))
    parts += [label('199 FOOTPRINTS / 5 LIBRARIES / SEE README FOR FULL COVERAGE',120,146,1),
              label('Mask openings clip silk only when enabled in plotting. Check your destination board.',120,151,.85)]
    for a,b in [((4,4),(236,4)),((236,4),(236,156)),((236,156),(4,156)),((4,156),(4,4))]:
        parts.append(f'(gr_line (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) (stroke (width .05) (type default)) (layer "Edge.Cuts"))')
    header='''(kicad_pcb (version 20260206) (generator "backplane_library_catalogue")
    (general (thickness 1.6)) (paper "A3")
    (layers (0 "F.Cu" signal) (1 "In1.Cu" signal) (2 "In2.Cu" signal) (31 "B.Cu" signal)
    (34 "B.Paste" user) (35 "F.Paste" user) (36 "B.SilkS" user "B.Silkscreen") (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user) (39 "F.Mask" user) (44 "Edge.Cuts" user)
    (46 "B.CrtYd" user "B.Courtyard") (47 "F.CrtYd" user "F.Courtyard") (48 "B.Fab" user) (49 "F.Fab" user))
    (setup (pad_to_mask_clearance 0))
    '''
    dest=ROOT/'build/catalogue-staging.kicad_pcb'
    dest.write_text(header+'\n'.join(parts)+'\n)\n')
    print(dest)

if __name__=='__main__':main()
