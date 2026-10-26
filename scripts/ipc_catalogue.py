#!/usr/bin/env python3
"""Import a validated staging board's items into the canonical catalogue over IPC.

Uses the selected runtime's own descriptor, not SWIG or guessed protobuf types.
uv run --no-project --with protobuf==7.36.2 --with pynng==0.9.0 scripts/ipc_catalogue.py <staging.kicad_pcb>
Start the project's Backplane IPC server before running this script.
"""
from pathlib import Path
import json, sys, hashlib, shutil, datetime, re, uuid
import pynng
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory, json_format, empty_pb2

ROOT=Path(__file__).resolve().parents[1]
CLI_ROOT=Path('/home/h/.backplane-bend/kicad/10.99.0-bp.4')
POOL=descriptor_pool.DescriptorPool()
POOL.AddSerializedFile(empty_pb2.DESCRIPTOR.serialized_pb)
files=list(descriptor_pb2.FileDescriptorSet.FromString((CLI_ROOT/'share/backplane/api.desc').read_bytes()).file)
while files:
    progress=False
    for f in files[:]:
        try: POOL.Add(f)
        except TypeError: continue
        files.remove(f); progress=True
    if not progress: raise RuntimeError('Unresolved descriptor dependencies')

def msg(name,data=None):
    result=message_factory.GetMessageClass(POOL.FindMessageTypeByName(name))()
    if data: json_format.ParseDict(data,result,descriptor_pool=POOL)
    return result

def dic(m): return json_format.MessageToDict(m,preserving_proto_field_name=True,descriptor_pool=POOL)

class Client:
    def __init__(self,socket):
        self.sock=pynng.Req0(dial='ipc://'+str(socket),send_timeout=30000,recv_timeout=30000)
        self.token=''
    def call(self,name,data=None):
        req=msg('kiapi.common.ApiRequest')
        req.header.client_name='works.backplane.library-catalogue'
        req.header.kicad_token=self.token
        req.message.Pack(msg(name,data))
        self.sock.send(req.SerializeToString())
        res=msg('kiapi.common.ApiResponse');res.ParseFromString(self.sock.recv())
        self.token=res.header.kicad_token
        if res.status.status!=1: raise RuntimeError(name+': '+str(res.status))
        result=msg(res.message.type_url.split('/')[-1]);result.ParseFromString(res.message.value)
        return dic(result)

def main():
    canonical=ROOT/'boards/library_catalogue/library_catalogue.kicad_pcb'
    staging=Path(sys.argv[1]).resolve(strict=True)
    config=json.loads((ROOT/'.backplane.json').read_text())
    assert ROOT/config['project']==canonical.with_suffix('.kicad_pro')
    socket=Path('/run/user/1000/backplane/kicad/a78161f6ac61dca2/api.sock')
    c=Client(socket)
    common='kiapi.common.commands.'
    doc={'type':'DOCTYPE_PCB','board_filename':canonical.name}
    c.call(common+'CloseAllDocuments')
    loaded=c.call(common+'OpenDocument',{'type':'DOCTYPE_PCB','path':str(staging)})['document']
    items=c.call(common+'GetItems',{'header':{'document':loaded},'types':['KOT_PCB_FOOTPRINT','KOT_PCB_SHAPE','KOT_PCB_TEXT']}).get('items',[])
    if not items: raise RuntimeError('No staging items read')
    # Pending deletes retain IDs until EndCommit; give imported items fresh IDs
    # while preserving every reference between them, so refresh is atomic.
    id_map={}
    def rekey(value):
        if isinstance(value,dict):return {k:rekey(v) for k,v in value.items()}
        if isinstance(value,list):return [rekey(v) for v in value]
        if isinstance(value,str) and re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}',value):
            return id_map.setdefault(value,str(uuid.uuid4()))
        return value
    items=rekey(items)
    c.call(common+'CloseAllDocuments')
    doc=c.call(common+'OpenDocument',{'type':'DOCTYPE_PCB','path':str(canonical)})['document']
    old=c.call(common+'GetItems',{'header':{'document':doc},'types':['KOT_PCB_FOOTPRINT','KOT_PCB_SHAPE','KOT_PCB_TEXT']}).get('items',[])
    header={'document':doc}
    stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    backup=ROOT/'build/backups'/stamp;backup.mkdir(parents=True,exist_ok=True)
    shutil.copy2(canonical,backup/canonical.name)
    companion=canonical.with_name(canonical.name+'.backplane.json')
    if companion.exists(): shutil.copy2(companion,backup/companion.name)
    commit=c.call(common+'BeginCommit',{'header':header})['id']
    try:
        if old:
            deleted=c.call(common+'DeleteItems',{'header':header,'item_ids':[it['id'] for it in old]})
            assert all(it['status']=='IDS_OK' for it in deleted.get('deleted_items',[])),deleted
        created=c.call(common+'CreateItems',{'header':header,'items':items})
        status=[it['status']['code'] for it in created.get('created_items',[])]
        if len(status)!=len(items) or any(s!='ISC_OK' for s in status): raise RuntimeError(str(status))
        c.call(common+'EndCommit',{'header':header,'id':commit,'action':'CMA_COMMIT','message':'Refresh reusable footprint library catalogue'})
    except BaseException:
        c.call(common+'EndCommit',{'header':header,'id':commit,'action':'CMA_DROP'})
        raise
    c.call(common+'SaveDocument',{'document':doc})
    readback=c.call(common+'GetItems',{'header':header,'types':['KOT_PCB_FOOTPRINT','KOT_PCB_SHAPE','KOT_PCB_TEXT']}).get('items',[])
    assert len(readback)==len(items)
    receipt={'canonical_path':str(canonical),'staging_source':str(staging),'saved_sha256':hashlib.sha256(canonical.read_bytes()).hexdigest(),
             'saved_bytes':canonical.stat().st_size,'item_count':len(readback),'import_status':'all ISC_OK','backup':str(backup)}
    (ROOT/'verification/catalogue-ipc-save.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))

if __name__=='__main__': main()
