#!/usr/bin/env python3
"""Build a local handoff ZIP, manifests and checksum list. Never publishes."""
from pathlib import Path
import json,csv,hashlib,zipfile,collections,io
ROOT=Path(__file__).resolve().parents[1]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    rows=[]
    for lib in sorted((ROOT/'libraries').glob('*.pretty')):
        for p in sorted(lib.glob('*.kicad_mod')):
            family='mounting_hole' if 'MountingHole' in lib.stem else 'artwork' if 'Shoggoth' in lib.stem else 'passive'
            rows.append({'id':lib.stem+':'+p.stem,'library':lib.stem,'name':p.stem,'family':family,
                         'density':lib.stem.rsplit('_',1)[1].lower() if family=='passive' else '',
                         'variant_status':'original_local_least_only' if 'LegacyLocal' in p.stem else 'standard',
                         'file':str(p.relative_to(ROOT)),'sha256':sha(p)})
    assert len(rows)==199
    counts=dict(collections.Counter(r['library'] for r in rows))
    manifest={'name':'Backplane_KiCad_Library','version':'2026.10.26','footprint_count':len(rows),
              'libraries':counts,'step_models':len(list((ROOT/'3dmodels').rglob('*.step'))),
              'tested_runtime':'10.99.0-bp.4','runtime_source_commit':'5dbc22d292704d02b609d5b7a0edc971f1b7f08b',
              'canonical_project':'boards/library_catalogue/library_catalogue.kicad_pro',
              'canonical_board_sha256':sha(ROOT/'boards/library_catalogue/library_catalogue.kicad_pcb'),
              'provenance':['sources/holes/manifest.json','sources/passives/provenance.json','docs/shoggoth.md'],
              'entries':rows}
    (ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    with (ROOT/'CATALOGUE.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    folders=['libraries','3dmodels','sources','docs','scripts','verification','previews','boards','.github']
    files=[ROOT/n for n in ['README.md','LICENSES.md','manifest.json','CATALOGUE.csv','fp-lib-table.example','.gitignore','.backplane.json','.backplane/intent.md']]
    for folder in folders:
        for p in (ROOT/folder).rglob('*'):
            rel=p.relative_to(ROOT)
            if not p.is_file() or any(v in {'build','__pycache__','.git','.venv'} for v in rel.parts):continue
            if p.suffix in {'.pyc','.kicad_prl','.lck'} or any(v.endswith('-backups') for v in rel.parts):continue
            if p.name in {'.DS_Store'}:continue
            files.append(p)
    files=sorted(set(files))
    checksums=''.join(f'{sha(p)}  {p.relative_to(ROOT)}\n' for p in files)
    (ROOT/'SHA256SUMS').write_text(checksums)
    files.append(ROOT/'SHA256SUMS')
    release=ROOT/'release';release.mkdir(exist_ok=True)
    destination=release/'Backplane_KiCad_Library-2026.10.26.zip'
    with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in files:
            info=zipfile.ZipInfo('Backplane_KiCad_Library/'+str(p.relative_to(ROOT)),date_time=(2026,10,26,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=(0o100755 if p.stat().st_mode&0o111 else 0o100644)<<16
            z.writestr(info,p.read_bytes())
    with zipfile.ZipFile(destination) as z:
        assert z.testzip() is None
        names=set(z.namelist())
        assert len(names)==len(files)
        for p in files:assert hashlib.sha256(z.read('Backplane_KiCad_Library/'+str(p.relative_to(ROOT)))).hexdigest()==sha(p)
    (release/(destination.name+'.sha256')).write_text(sha(destination)+'  '+destination.name+'\n')
    print(json.dumps({'zip':str(destination),'sha256':sha(destination),'bytes':destination.stat().st_size,
                      'files':len(files),'footprints':counts,'step_models':manifest['step_models']},indent=2))

if __name__=='__main__':main()
