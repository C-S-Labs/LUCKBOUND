"""Cheap delivery audit; incomplete Roblox imports remain an explicit HOLD."""
import hashlib
import json
from pathlib import Path
import py_compile

HERE = Path(__file__).resolve().parent
OUT = Path('E:/BlenderAIProjects/Runtime/Emberfall_Batch2')


def main():
    for script in HERE.glob('*.py'):
        py_compile.compile(str(script), doraise=True)
    for path in HERE.glob('*.json'):
        json.loads(path.read_text())
    rows = json.loads((HERE / 'batch2_sources.json').read_text())
    by_id = {r['id']: r for r in rows}
    assert len(by_id) == 8
    for r in rows:
        c = r['source_checks']
        assert c['closed'] and c['origin'] == [0, 0, 0] and c['footprint'] == [256, 256]
        assert c['profile_error'] < 1e-5 and c['hull_halfspace_error'] < 1e-5
        assert r['max_mesh_triangles'] < 10000
        assert all(s['Width'] == 24 and s['Kind'] in ('BP_EDGE_HOLLOW', 'BP_EDGE_CREST') for s in r['sockets'])
    variants = json.loads((HERE / 'batch2_variants.json').read_text())
    assert len(variants) == 4
    for r in variants:
        base = by_id[r['variant_of']]
        assert r['geometry_sha256'] == base['geometry_sha256']
        assert r['sockets'] == base['sockets'] and r['collision_parts'] == base['collision_parts']
    combined = json.loads((HERE / 'combined_review.json').read_text())
    canonical = set()
    for d in combined['layouts'].values():
        canonical.update(r.get('source_id', r['id']) for r in d['rows'])
        assert d['max_seam'] < 0.001
        assert abs(d['balance_percent'][0] - 18.88) < 0.01
        assert abs(d['balance_percent'][1] - 31.05) < 0.01
        assert abs(d['balance_percent'][2] - 50.07) < 0.01
    assert len(canonical) == 17
    source = json.loads((HERE / 'source_export_manifest.json').read_text())
    review = json.loads((HERE / 'review_export_manifest.json').read_text())
    bounds = json.loads((HERE / 'review_bounds_manifest.json').read_text()) if (HERE / 'review_bounds_manifest.json').exists() else None
    cell = json.loads((HERE / 'review_cell_manifest.json').read_text()) if (HERE / 'review_cell_manifest.json').exists() else None
    files = source['files'] + review['files'] + (bounds['files'] if bounds else []) + (cell['files'] if cell else [])
    for f in files:
        payload = Path(f['path']).read_bytes()
        assert len(payload) == f['bytes']
        assert hashlib.sha256(payload).hexdigest() == f['sha256']
    ledger = json.loads((HERE / 'asset_mapping.json').read_text())
    assert set(ledger['sourceIds']) == {r['key'] for r in source['assets']}
    assert all(v.startswith('rbxassetid://') for v in ledger['sourceIds'].values())
    result = dict(
        source_sanity='PASS', variant_identity='PASS', canonical_library_sources=17,
        combined_layouts={name: len(d['rows']) for name, d in combined['layouts'].items()},
        exports_checked=len(files),
        source_mesh_mappings=len(ledger['sourceIds']), delivered_review_mesh_mappings=len(ledger['reviewIds']),
        source_visual_triangles=sum(r['triangles'] for r in rows), source_visual_objects=sum(r['objects'] for r in rows),
        canonical_collision_parts=sum(r['collision_parts'] for r in rows),
        pending_review_files=ledger['pendingReviewFiles'],
        readiness='HOLD' if ledger['pendingReviewFiles'] else 'Studio validation required',
    )
    if bounds:
        assert len(bounds['replaced'])==23
        assert sum(r['triangles'] for r in bounds['records'])==bounds['triangles']
        assert max(max(r['size']) for r in bounds['records'])<2048
        assert all(r['key'] in ledger['reviewIds'] for r in bounds['records'])
        result['bounds_repair'] = dict(replaced=23,parts=len(bounds['records']),triangles=bounds['triangles'],exports=len(bounds['files']))
    if cell:
        assert len(cell['records']) == 2
        assert sum(r['triangles'] for r in cell['records']) == cell['triangles']
        assert all(r['key'] in ledger['reviewIds'] for r in cell['records'])
        result['cell_repair'] = dict(parts=2, triangles=cell['triangles'], exports=len(cell['files']))
    studio_path = HERE / 'studio_validation.json'
    if studio_path.exists():
        studio = json.loads(studio_path.read_text())
        result['imported_validation'] = 'PASS' if studio['imported']['misses'] == 0 else 'HOLD'
        if studio.get('walk', {}).get('completed') and not studio.get('preload', {}).get('failures', {'pending': True}):
            result['readiness'] = 'READY FOR OWNER REVIEW'
    (HERE / 'delivery_validation.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
