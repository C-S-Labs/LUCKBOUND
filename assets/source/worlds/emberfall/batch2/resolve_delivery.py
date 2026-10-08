"""Read preserved operation; allow one authorized new-only retry, then 9/10.

Credentials stay inside the external approved workflow and are never reported.
Successful mappings and the original failed-operation log are never overwritten.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

OUT = Path('E:/BlenderAIProjects/Runtime/Emberfall_Batch2')
EXTERNAL = Path('C:/Users/jhpel/RobloxAssetUpload')
sys.path.insert(0, str(EXTERNAL))
import upload_fbx as workflow


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--deliver', action='store_true')
    parser.add_argument('--bounds', action='store_true')
    parser.add_argument('--cell', action='store_true')
    parser.add_argument('--inspect-mesh')
    args = parser.parse_args()
    if args.inspect_mesh:
        assert args.inspect_mesh.isdigit()
        response=workflow.request_json('https://apis.roblox.com/asset-delivery-api/v1/assetId/'+args.inspect_mesh,os.environ.get('ROBLOX_OPEN_CLOUD_API_KEY'),stage='Mesh delivery inspection')
        location=response.get('location')
        payload=workflow.fetch(location,stage='Mesh content inspection') if location else b''
        result=dict(assetId=args.inspect_mesh,deliveryLocationPresent=bool(location),errors=response.get('errors'),bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest())
        (OUT/('mesh_delivery_'+args.inspect_mesh+'.json')).write_text(json.dumps(result,indent=2))
        print('MESH_DELIVERY',json.dumps(result),flush=True)
        return
    operation = workflow.request_json(
        workflow.API_BASE + '/operations/fea2f937-03a8-4978-8c70-27d22ddf4c2d',
        os.environ.get('ROBLOX_OPEN_CLOUD_API_KEY'), stage='Preserved operation read',
    )
    (OUT / 'failed_operation_reinspection.json').write_text(json.dumps(operation, indent=2))
    print('PRESERVED_OPERATION', json.dumps(operation), flush=True)
    if args.bounds or args.cell:
        prefix='review_cell' if args.cell else 'review_bounds'
        manifest = json.loads((OUT / (prefix+'_manifest.json')).read_text())
        for i,record in enumerate(manifest['files']):
            mapping = OUT / f'{prefix}_{i}_mapping.json'
            log = OUT / f'{prefix}_{i}_upload.log'
            assert not mapping.exists() and not log.exists(), 'Bounds delivery already attempted; inspect before any repeat'
            assert hashlib.sha256(Path(record['path']).read_bytes()).hexdigest()==record['sha256']
            with log.open('x', encoding='utf8') as stream:
                result=subprocess.run([sys.executable,str(EXTERNAL/'upload_fbx.py'),record['path'],'--name',f'Emberfall Batch 2 Bounded Scenery {prefix} {i}','--json',str(mapping),'--timeout','600'],cwd=str(EXTERNAL),stdout=stream,stderr=subprocess.STDOUT)
            assert result.returncode==0, 'Bounds delivery stopped; inspect '+str(log)
            m=json.loads(mapping.read_text());assert len(m['meshParts'])==record['meshes']
            print('BOUNDS_DELIVERY',i,m['modelAssetId'],len(m['meshParts']),flush=True)
        return
    if not args.deliver:
        return
    # A later successful response must be recovered rather than uploaded again.
    assert operation.get('done') and operation.get('error'), 'Operation is not a confirmed terminal failure; recover/reinspect before creation'
    assert not operation.get('response', {}).get('assetId'), 'Original operation returned an asset; reuse it'
    manifest = json.loads((OUT / 'review_export_manifest.json').read_text())
    for i in (8, 9, 10):
        mapping = OUT / f'review_visual_{i}_mapping.json'
        if mapping.exists():
            print('PRESERVED', i, flush=True)
            continue
        record = manifest['files'][i]
        path = Path(record['path'])
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256']
        log = OUT / ('review_visual_8_controlled_retry.log' if i == 8 else f'review_visual_{i}_upload.log')
        assert not log.exists(), 'An attempt already exists; no automatic repeats'
        with log.open('x', encoding='utf8') as stream:
            result = subprocess.run([
                sys.executable, str(EXTERNAL / 'upload_fbx.py'), str(path),
                '--name', f'Emberfall Batch 2 Bounded Production Review {i}',
                '--json', str(mapping), '--timeout', '600',
            ], cwd=str(EXTERNAL), stdout=stream, stderr=subprocess.STDOUT)
        assert result.returncode == 0, 'Delivery stopped; inspect preserved ' + str(log)
        m = json.loads(mapping.read_text())
        assert len(m['meshParts']) == record['meshes']
        print('NEW_DELIVERY', i, m['modelAssetId'], len(m['meshParts']), flush=True)


if __name__ == '__main__':
    main()
