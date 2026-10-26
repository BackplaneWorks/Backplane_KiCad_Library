#!/usr/bin/env python3
"""Make only catalogue instances resolve models from the saved project folder."""
from pathlib import Path
import json,hashlib,shutil,datetime
from ipc_catalogue import ROOT,Client

def rewrite(v):
    if isinstance(v,dict):return {k:rewrite(value) for k,value in v.items()}
    if isinstance(v,list):return [rewrite(value) for value in v]
    if isinstance(v,str):return v.replace('${BACKPLANE_KICAD_LIBRARY}/','${KIPRJMOD}/../../')
    return v

def main():
    path=ROOT/'boards/library_catalogue/library_catalogue.kicad_pcb'
    c=Client('/run/user/1000/backplane/kicad/a78161f6ac61dca2/api.sock')
    common='kiapi.common.commands.'
    doc={'type':'DOCTYPE_PCB','board_filename':path.name};header={'document':doc}
    items=c.call(common+'GetItems',{'header':header,'types':['KOT_PCB_FOOTPRINT']})['items']
    changed=[rewrite(v) for v in items if '${BACKPLANE_KICAD_LIBRARY}/' in json.dumps(v)]
    assert len(changed)==9
    backup=ROOT/'build/backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    backup.mkdir(parents=True);shutil.copy2(path,backup/path.name)
    companion=path.with_name(path.name+'.backplane.json')
    if companion.exists():shutil.copy2(companion,backup/companion.name)
    commit=c.call(common+'BeginCommit',{'header':header})['id']
    try:
        response=c.call(common+'UpdateItems',{'header':header,'items':changed})
        status=[v['status']['code'] for v in response['updated_items']]
        assert len(status)==9 and all(v=='ISC_OK' for v in status),response
        c.call(common+'EndCommit',{'header':header,'id':commit,'action':'CMA_COMMIT','message':'Resolve catalogue STEP bodies relative to project'})
    except BaseException:
        c.call(common+'EndCommit',{'header':header,'id':commit,'action':'CMA_DROP'});raise
    c.call(common+'SaveDocument',{'document':doc})
    content=path.read_text()
    assert content.count('${KIPRJMOD}/../../3dmodels/')==9
    assert '${BACKPLANE_KICAD_LIBRARY}/3dmodels/' not in content
    report={'canonical_path':str(path),'updated_footprints':9,'status':'all ISC_OK',
            'saved_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'model_path':'${KIPRJMOD}/../../3dmodels'}
    (ROOT/'verification/catalogue-model-paths.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
