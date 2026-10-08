"""Sequential new-Model delivery via owner-approved external tooling; never retry."""
import json
import subprocess
from pathlib import Path
OUT=Path('E:/BlenderAIProjects/Runtime/Emberfall_Batch2')
EXTERNAL=Path('C:/Users/jhpel/RobloxAssetUpload')
PYTHON='C:/Users/jhpel/AppData/Local/Programs/Python/Python314/python.exe'
manifest=json.loads((OUT/'review_export_manifest.json').read_text())
progress=[]
for index,file in enumerate(manifest['files']):
    mapping=OUT/('review_visual_'+str(index)+'_mapping.json')
    log=OUT/('review_visual_'+str(index)+'_upload.log')
    if mapping.exists():
        result=json.loads(mapping.read_text())
        assert len(result['meshParts'])==file['meshes'],'Inspect existing mapping before proceeding'
    else:
        assert not log.exists(),'Prior upload attempt exists; inspect operation/Model ID, never retry blindly'
        with log.open('x',encoding='utf8') as stream:
            proc=subprocess.run([PYTHON,str(EXTERNAL/'upload_fbx.py'),file['path'],'--name','Emberfall Batch 2 Bounded Production Review '+str(index),'--json',str(mapping),'--timeout','600'],cwd=str(EXTERNAL),stdout=stream,stderr=subprocess.STDOUT)
        assert proc.returncode==0,'Upload stopped; inspect '+str(log)
        result=json.loads(mapping.read_text())
        assert len(result['meshParts'])==file['meshes'],'Returned mesh count mismatch'
    progress.append(dict(file=file['path'],mapping=str(mapping),modelAssetId=result['modelAssetId'],meshes=len(result['meshParts'])))
    (OUT/'review_upload_progress.json').write_text(json.dumps(progress,indent=2))
    print('UPLOAD_COMPLETE',index,result['modelAssetId'],len(result['meshParts']),flush=True)
