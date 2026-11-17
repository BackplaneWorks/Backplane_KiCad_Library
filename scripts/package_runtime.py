#!/usr/bin/env python3
"""Build and verify the portable footprint/model payload for Backplane releases."""
from pathlib import Path
import argparse,hashlib,io,json,subprocess,tarfile,gzip

ROOT=Path(__file__).resolve().parents[1]

def digest(data):return hashlib.sha256(data).hexdigest()

def build(output,version,commit):
    manifest=json.loads((ROOT/'manifest.json').read_text())
    files={}
    for folder in ['libraries','3dmodels']:
        for p in sorted((ROOT/folder).rglob('*')):
            if p.is_file() and 'renders' not in p.relative_to(ROOT).parts:
                files[str(p.relative_to(ROOT))]=p.read_bytes()
    for name in ['README.md','LICENSES.md','manifest.json','CATALOGUE.csv','fp-lib-table.example','previews/catalogue.png']:
        files[name]=(ROOT/name).read_bytes()
    for p in sorted((ROOT/'docs').glob('*.md')):
        files[str(p.relative_to(ROOT))]=p.read_bytes()
    for name in ['sources/holes/LICENSE-STATUS.md','sources/shoggoth/original/source/caption-font-LICENSE.txt']:
        files[name]=(ROOT/name).read_bytes()
    # Include complete notices already bundled with copied library/model sources.
    for p in sorted((ROOT/'sources/holes/licenses').rglob('*')):
        if p.is_file():files[str(p.relative_to(ROOT))]=p.read_bytes()
    for p in sorted((ROOT/'sources/passives/upstream').glob('LICENSE*')):
        if p.is_file():files[str(p.relative_to(ROOT))]=p.read_bytes()
    footprints=[p for p in files if p.startswith('libraries/') and p.endswith('.kicad_mod')]
    models=[p for p in files if p.endswith('.step')]
    assert len(footprints)==manifest['footprint_count']==len(manifest['entries'])
    assert len(models)==manifest['step_models']
    for entry in manifest['entries']:
        assert digest(files[entry['file']])==entry['sha256'],entry['file']
    bundle={'schema_version':1,'repository':'BackplaneWorks/Backplane_KiCad_Library',
            'version':version,'source_commit':commit,'root':'Backplane_KiCad_Library',
            'footprint_count':len(footprints),'step_model_count':len(models),
            'library_nicknames':list(manifest['libraries']),
            'footprint_path':'libraries','model_path':'3dmodels',
            'required_path_variable':'BACKPLANE_KICAD_LIBRARY',
            'files':{p:digest(data) for p,data in sorted(files.items())}}
    files['BUNDLE_MANIFEST.json']=(json.dumps(bundle,indent=2)+'\n').encode()
    files['SHA256SUMS']=''.join(f'{digest(data)}  {p}\n' for p,data in sorted(files.items())).encode()
    output.mkdir(parents=True,exist_ok=True)
    archive=output/f'backplane-kicad-library-{version}.tar.gz'
    with archive.open('wb') as raw:
        with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0,compresslevel=9) as compressed:
            with tarfile.open(fileobj=compressed,mode='w') as tar:
                for name,data in sorted(files.items()):
                    info=tarfile.TarInfo('Backplane_KiCad_Library/'+name)
                    info.size=len(data);info.mode=0o644;info.mtime=0;info.uid=0;info.gid=0
                    tar.addfile(info,io.BytesIO(data))
    with tarfile.open(archive,'r:gz') as tar:
        assert len(tar.getmembers())==len(files)
        for name,data in files.items():
            member=tar.getmember('Backplane_KiCad_Library/'+name)
            assert member.isfile() and tar.extractfile(member).read()==data,name
    checksum=digest(archive.read_bytes())
    archive.with_name(archive.name+'.sha256').write_text(checksum+'  '+archive.name+'\n')
    print(json.dumps({'archive':str(archive),'sha256':checksum,'bytes':archive.stat().st_size,
                      'source_commit':commit,'footprints':len(footprints),'step_models':len(models)},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'release')
    parser.add_argument('--version',default='2026.11.17')
    parser.add_argument('--source-commit',default=None)
    args=parser.parse_args()
    commit=args.source_commit or subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    build(args.output,args.version,commit)
