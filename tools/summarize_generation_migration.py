"""Summarize preserved targeted verification; performs no Studio execution."""
import json
import statistics
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/benchmarks'


def differences(expected, actual):
    failures, maximum, count = 0, 0, 0
    for key in expected.keys() | actual.keys():
        left, right = expected.get(key), actual.get(key)
        if left is None or right is None or len(left) != len(right):
            failures += 1
            continue
        for a, b in zip(left, right):
            count += 1
            if isinstance(a, bool) or isinstance(b, bool):
                failures += a != b
            else:
                maximum = max(maximum, abs(a-b))
                failures += abs(a-b) > 0.05
    return {'DifferentSamples': failures, 'ComparedSamples': count,
            'MaximumDifferenceStuds': maximum}


def main():
    baseline = subprocess.run(
        ['git', 'show', 'bb47f91:docs/benchmarks/asset_ASSET_CONTROL.json'],
        cwd=ROOT, capture_output=True, encoding='utf-8', check=True)
    controls = {(r['WorldId'], r['Seed'], r['Repeat']): r for r in json.loads(baseline.stdout)}
    rows = json.loads((OUT/'generation_migration_studio.json').read_text())
    comparisons, original, final = [], {}, {}
    for row in rows:
        control = controls[row['WorldId'], row['Seed'], row['Repeat']]
        geometry = row['Geometry']
        result = differences(control['CollisionSamples'], geometry['CollisionSamples'])
        result.update(WorldId=row['WorldId'], Repeat=row['Repeat'],
                      VisualSignaturesMatch=control['VisualSignatures'] == geometry['VisualSignatures'],
                      ArtYawsMatch=control['ArtYaws'] == geometry['ArtYaws'])
        comparisons.append(result)
        for name in ['CreateMeshPartAsyncCalls', 'PreciseRequests', 'VisualOnlyPreciseRequests']:
            original[name] = original.get(name, 0) + control['Counters'].get(name, 0)
            final[name] = final.get(name, 0) + row['Counters'].get(name, 0)
    contracts_path = OUT/'generation_migration_contracts.json'
    contracts = json.loads(contracts_path.read_text())
    catalogue = contracts['vv_catalogue']
    catalogue['Comparison'] = differences(catalogue['Control']['CollisionSamples'], catalogue['Prepared']['CollisionSamples'])
    catalogue['Comparison'].update(
        VisualSignaturesMatch=catalogue['Control']['VisualSignatures'] == catalogue['Prepared']['VisualSignatures'],
        VerifiedArtRotations=catalogue['Chunks'], VerifiedProxyParts=catalogue['ProxyParts'])
    contracts_path.write_text(json.dumps(contracts, indent=2), encoding='utf-8')
    assert all(r['Grounded'] and r['AtmosphereReady'] for r in rows)
    assert all(r['DifferentSamples'] == 0 and r['VisualSignaturesMatch'] and r['ArtYawsMatch'] for r in comparisons)
    assert catalogue['Comparison']['DifferentSamples'] == 0 and catalogue['Comparison']['VisualSignaturesMatch']
    summary = {
        'BaselineCommit': '714fa33', 'EvidenceCommit': 'bb47f91', 'Maps': len(rows),
        'Method': 'fresh Play per world, seed 1 twice; cold application cache, existing Studio process/native asset cache',
        'PlayableMedianSeconds': statistics.median(r['PlayerGroundedSeconds'] for r in rows),
        'PlayableWorstSeconds': max(r['PlayerGroundedSeconds'] for r in rows),
        'PairedControlCounters': original, 'MigrationCounters': final,
        'ColdMisses': sum(r['Counters'].get('CacheMisses',0) for r in rows if r['Repeat']==1),
        'AuthoredResolutions': sum(r['Counters'].get('AuthoredTemplateResolutions',0) for r in rows),
        'WarmMisses': sum(r['Counters'].get('CacheMisses',0) for r in rows if r['Repeat']==2),
        'WarmHits': sum(r['Counters'].get('CacheHits',0) for r in rows if r['Repeat']==2),
        'InFlightDeduplications': sum(r['Counters'].get('InFlightDeduplications',0) for r in rows),
        'DuplicatePreparations': sum(r['Counters'].get('DuplicatePreparations',0) for r in rows),
        'Comparisons': comparisons, 'Catalogue': catalogue['Comparison'],
        'Limits': ['one cold application-cache run per world', 'native cache memory not isolated',
                   'manual traversal/rendered visual acceptance and published client/network validation pending'],
    }
    (OUT/'generation_migration_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    (OUT/'generation_migration_comparison.json').write_text(json.dumps(comparisons,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k not in {'Comparisons','Catalogue'}},indent=2))


if __name__ == '__main__':
    main()
