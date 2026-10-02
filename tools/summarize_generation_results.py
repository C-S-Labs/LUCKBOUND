"""Consolidate preserved raw cohorts; never invent missing stage results."""
import json
import math
import statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'docs/benchmarks'


def stats(values):
    values=list(values)
    return {'Median':statistics.median(values),'Worst':max(values),'Minimum':min(values)} if values else None


def key(row):
    return row['WorldId'],row['Seed'],row['Repeat']


def differences(expected,actual,tolerance):
    count=0
    maximum=0
    keys=set(expected)|set(actual)
    for name in keys:
        a,b=expected.get(name),actual.get(name)
        if a is None or b is None or len(a)!=len(b):
            count+=1
            continue
        for x,y in zip(a,b):
            if type(x) is bool or type(y) is bool:
                count+=x!=y
            else:
                distance=abs(x-y)
                maximum=max(maximum,distance)
                count+=distance>tolerance
    return {'DifferentSamples':count,'MaximumDifferenceStuds':maximum}


def main():
    result={}
    control_file=OUTPUT/'asset_ASSET_CONTROL.json'
    control={key(row):row for row in json.loads(control_file.read_text())} if control_file.exists() else {}
    for path in sorted(OUTPUT.glob('generation_paired_*.json'))+sorted(OUTPUT.glob('asset_*.json')):
        if path.name in {'asset_content_boot.json','asset_cache_invariants.json','asset_template_inventory.json'}:
            continue
        rows=json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(rows,list) or not rows or 'WorldId' not in rows[0]:
            continue
        name=path.stem.removeprefix('generation_paired_').removeprefix('asset_')
        if name=='L':
            by_pair={}
            comparisons=[]
            for row in rows:
                pair=(row['SampleId'],row['Yaw'],row['Repeat'])
                if row['Mode']=='CONTROL': by_pair[pair]=row
                else: comparisons.append(differences(by_pair[pair]['CollisionSamples'],row['CollisionSamples'],row['ToleranceStuds']))
            result[name]={'SampleBuilds':len(rows),'CollisionComparisons':comparisons,
                          'ControlMaterialization':stats(row['MaterializationSeconds'] for row in rows if row['Mode']=='CONTROL'),
                          'ProxyMaterialization':stats(row['MaterializationSeconds'] for row in rows if row['Mode']=='PROXY')}
            continue
        worlds={}
        for world in sorted({row['WorldId'] for row in rows}):
            subset=[row for row in rows if row['WorldId']==world]
            worlds[world]={'Playable':stats(row['PlayableSeconds'] for row in subset),
                           'Complete':stats(row['CompletionSeconds'] for row in subset),
                           'AssetInitialization':stats(row['Times'].get('AssetInitialization',0) for row in subset)}
        counters={}
        unique=set()
        collision=[]
        visual_mismatches=0
        yaw_mismatches=0
        for row in rows:
            for counter,value in row['Counters'].items(): counters[counter]=counters.get(counter,0)+value
            unique.update((row.get('CreatedAssets') or {}).keys())
            expected=control.get(key(row))
            if expected and name not in {'A','B','C','D','E','F','ASSET_CONTROL'}:
                collision.append(differences(expected['CollisionSamples'],row['CollisionSamples'],0.05))
                visual_mismatches+=expected['VisualSignatures']!=row['VisualSignatures']
                yaw_mismatches+=expected['ArtYaws']!=row['ArtYaws']
        result[name]={'Samples':len(rows),'Worlds':worlds,
                      'Playable':stats(row['PlayableSeconds'] for row in rows),
                      'Complete':stats(row['CompletionSeconds'] for row in rows),
                      'Counters':counters,'UniqueCreatedAssetKeys':len(unique),
                      'DuplicateCreations':max(0,counters.get('CreateMeshPartAsyncCalls',0)-len(unique)),
                      'CreationWall':stats(row['Times'].get('CreateMeshPartAsync',0) for row in rows),
                      'MemoryDeltaMb':stats(row['MemoryDeltaMb'] for row in rows),
                      'LuaHeapDeltaKb':stats(row.get('LuaHeapAfterKb',0)-row.get('LuaHeapBeforeKb',0) for row in rows),
                      'CorrectnessFailures':sum(bool(row.get('Failure')) or not row.get('StructuralValid',False) or row.get('BlockoutCount',0)>0 for row in rows),
                      'CollisionDifferentSamples':sum(row['DifferentSamples'] for row in collision),
                      'CollisionWorstDifferenceStuds':max((row['MaximumDifferenceStuds'] for row in collision),default=0),
                      'VisualSignatureMismatchMaps':visual_mismatches,'YawMismatchMaps':yaw_mismatches}
        result[name]['ColdFirstMapByWorld'] = {
            world: next(row['PlayableSeconds'] for row in rows if row['WorldId']==world)
            for world in worlds
        }
        result[name]['PhaseMedians'] = {
            field: stats(row[field] for row in rows if field in row)
            for field in ['LayoutSolvedSeconds','AssetsPreparedSeconds','MaterializationReadySeconds',
                          'CollisionReadySeconds','PlayerPlacedSeconds','SafePlayerReadySeconds',
                          'ServerPresentationReadySeconds']
        }
        result[name]['TimeMedians'] = {
            field: stats(row['Times'].get(field,0) for row in rows)
            for field in sorted({field for row in rows for field in row['Times']})
        }
        result[name]['RetainedCache'] = {
            field: rows[-1].get(field) for field in ['TemplateCacheEntries','RuntimeTemplateInstances',
            'CacheRetentionBeforeDestroyMb','CacheRetentionAfterDestroyMb',
            'CacheInstancesBeforeDestroyMb','CacheInstancesAfterDestroyMb','AnchorCache','PropStats']
        }
        client_path=OUTPUT/f'asset_{name}_client.json'
        if client_path.exists():
            clients=json.loads(client_path.read_text())
            by_epoch={row['RequestEpochMs']:row for row in clients}
            safe=[]
            failures=0
            for row in rows:
                client=by_epoch.get(row['RequestEpochMs'])
                if client is None:
                    failures+=1
                    continue
                failed=bool(client['FailedAssets']) or not client['ModelStillPresent'] or client['Meshes']!=client['ExpectedMeshes'] or client['CollisionParts']!=client['ExpectedCollision'] or not row['PlayerGrounded']
                failures+=failed
                if failed:
                    continue
                safe.append((max(client['ReadyEpochMs'],row['SafePlayerReadyEpochMs'])-row['RequestEpochMs'])/1000)
            result[name]['ClientAndGroundedReady']=stats(safe)
            result[name]['ClientValidatedSamples']=len(safe)
            result[name]['ClientOrGroundingFailures']=failures
    boot=json.loads((OUTPUT/'asset_server_boot.json').read_text())
    result['SERVER_BOOT']={mode:{field:stats(row[field] for row in boot if row['Mode']==mode)
                               for field in ['Ready','ContentReady','TotalMemoryMb']}
                           for mode in ['A','J']}
    (OUTPUT/'generation_consolidated_summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    for name,row in result.items():
        if 'Playable' in row:
            print(f"{name}: {row['Samples']} maps, median {row['Playable']['Median']:.3f}s worst {row['Playable']['Worst']:.3f}s, create {row['Counters'].get('CreateMeshPartAsyncCalls','unmeasured')}, query differences {row['CollisionDifferentSamples']}, visual signature mismatches {row['VisualSignatureMismatchMaps']}")
        elif name=='L':
            print(f"L: {row['SampleBuilds']} sample builds, proxy median {row['ProxyMaterialization']['Median']:.3f}s, query differences {sum(item['DifferentSamples'] for item in row['CollisionComparisons'])}")


if __name__=='__main__': main()
