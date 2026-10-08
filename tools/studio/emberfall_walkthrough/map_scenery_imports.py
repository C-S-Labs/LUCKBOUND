"""Persist attributable Studio import IDs after the scenery-only FBX import."""
import json
from pathlib import Path

runtime = Path('E:/BlenderAIProjects/Runtime/Emberfall_SceneryScaling')
target = Path(__file__).parent
manifest = json.loads((runtime/'scenery_manifest.json').read_text())
trees = json.loads((runtime/'trees_manifest.json').read_text())
ids = json.loads((runtime/'scenery_clump_ids.json').read_text())
ids.update(json.loads((runtime/'tree_ids.json').read_text()))
data = dict(records=manifest['records']+trees,ids=ids,mode='Layout1BakedScenery',editableMeshes=0)
assert len(ids)==len(data['records'])==61
assert all(r['key'] in ids and ids[r['key']].startswith('rbxassetid://') for r in data['records'])
source = '--!strict\n-- Generated assembled scenery; frozen playable source is read-only.\nreturn game:GetService("HttpService"):JSONDecode(\n\t[==['+json.dumps(data,separators=(',',':'))+']==]\n)\n'
(target/'SceneryData.luau').write_text(source,encoding='utf8')
for record in data['records']:
    record['assetId']=ids[record['key']]
    record['sourceExport']=str(runtime/('EF_SCENERY_TREES.fbx' if record['role']=='sceneryProps' else 'EF_SCENERY_CONTINUATION.fbx'))
    record['destination']='ReplicatedStorage.EmberfallSceneryData.ids.'+record['key']
(target/'scenery_asset_mapping.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
print('Mapped61 scenery assets; run StyLua on SceneryData.luau')
