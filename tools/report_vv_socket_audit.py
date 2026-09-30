"""Classify complete VV socket evidence without treating query hulls as visible mesh."""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def classify(c, s, authored, width_evidence=None):
    centre = [p for p in s['samples'] if p['lateral'] == 0]
    failures = []
    warnings = []
    mouth_evidence = None
    if width_evidence:
        edge = next(e for e in width_evidence['edges'] if e['runtime_facing'] == s['facing'])
        mouth = edge['slices'][0]
        path = next((r for r in mouth['material_runs'] if r['material'] == 'VV_Path' and r['start'] <= 0 <= r['end']), None)
        if not path:
            failures.append('Declared socket lacks a centered authored VV_Path mouth')
        else:
            path_width = path['end'] - path['start']
            physical_kind = 'WIDE' if path_width >= 48 and mouth['flat_pad']['width'] >= 50 else 'PATH'
            mouth_evidence = {'path_width':path_width,'level_pad_width':mouth['flat_pad']['width'],'physical_kind':physical_kind}
            if s['kind'] != physical_kind:
                failures.append(f"Socket Kind {s['kind']} reverses the independently measured {physical_kind} mouth ({path_width}-stud path)")
    if not any(p['collision']['walk'] for p in centre[:4]):
        failures.append('No centre collision from the edge through 12 studs inward')
    elif not all(p['collision']['walk'] for p in centre):
        warnings.append('Isolated centre collision miss: ' + ', '.join(str(p['depth']) for p in centre if not p['collision']['walk']))
    rotation = c['selected']
    native_index = ((s['facing'] - rotation) % 360) // 90
    # Roblox N under import yaw zero is native -Y; E is native -X.
    label = ['-Y', '-X', '+Y', '+X'][native_index]
    a = next(d for d in authored['directions'] if d['native_direction'] == label)
    core = [p for p in a['samples'] if p['depth'] > 0 and abs(p['lateral']) <= 8]
    good = lambda p: p['hit'] and abs(p['z']) <= c['tolerance'] and p['normal'] >= .65
    if not any(good(p) for p in core if p['depth'] <= 12):
        failures.append('Authored triangles lack the declared centre approach')
    elif not all(good(p) for p in core):
        warnings.append('Authored central corridor incomplete or above socket tolerance')
    edge_lateral = s['width'] / 2 - 8
    breadth = [p for p in a['samples'] if p['depth'] in (2, 6, 12, 24) and abs(p['lateral']) == edge_lateral]
    if not all(good(p) for p in breadth):
        warnings.append('Authored representative width samples incomplete or steep')
    if any(p['solid_obstruction'] for p in core):
        warnings.append('Authored solid-prop intersection at central corridor sample')
    if any(p['solidObstruction'] for p in s['samples']):
        warnings.append('Saved solid-prop query obstruction')
    query_notes = []
    terrain_misses = [p for p in centre[1:] if not p['terrain']['walk']]
    if terrain_misses:
        # A no-hit confined to the mouth is not contrary visible-surface
        # evidence when the exact exported triangles and walk collision agree.
        if all(p['depth'] <= 2 and not p['terrain']['hit'] for p in terrain_misses) and all(good(p) for p in core) and all(p['collision']['walk'] for p in centre):
            query_notes.append('Precise query mouth no-hit; exact export triangles and saved walk corridor agree')
        else:
            warnings.append('Runtime precise terrain queries disagree with a usable centre approach')
    lateral_misses = [p for p in s['samples'] if p['depth'] > 0 and not p['collision']['walk']]
    if lateral_misses:
        warnings.append('Inset collision sample misses: ' + ', '.join(f"d{p['depth']}/l{p['lateral']}" for p in lateral_misses))
    return {'class': 'FAIL' if failures else 'SUSPICIOUS' if warnings else 'PASS', 'failures': failures, 'warnings': warnings,
            'mouth_evidence':mouth_evidence, 'query_notes': query_notes, 'native_direction': label, 'authored_core_hits':sum(good(p) for p in core), 'authored_core_count':len(core),
            'authored_width_hits':sum(good(p) for p in breadth), 'authored_width_count':len(breadth)}


def main():
    authored = json.loads((ROOT / 'docs/VV_SOCKET_AUTHORED_SURFACES.json').read_text())
    authors = {c['name']: c for c in authored['chunks']}
    if '--width-followup' in sys.argv:
        widths={c['id']:c for c in json.loads((ROOT / 'docs/VV_SOCKET_WIDTH_EVIDENCE.json').read_text())['chunks']}
        phases=[('WIDTH_BEFORE','VV_SOCKET_AUDIT_AFTER.json'),('WIDTH_AFTER','VV_SOCKET_WIDTH_RUNTIME_AFTER.json')]
    else:
        widths={}
        phases=[('BEFORE','VV_SOCKET_AUDIT_BEFORE.json')] + ([('AFTER','VV_SOCKET_AUDIT_AFTER.json')] if (ROOT / 'docs/VV_SOCKET_AUDIT_AFTER.json').exists() else [])
    for phase, capture in phases:
        data = json.loads((ROOT / 'docs' / capture).read_text())
        assert len(data['chunks']) == 30 and len({c['id'] for c in data['chunks']}) == 30
        counts = Counter()
        chunk_counts = Counter()
        lines = [f'# Verdant Valley complete socket audit — {phase.lower()}', '',
                 'All 30 production chunks were sampled before production corrections. Sky Citadel and Ethereal Scape were untouched.', '',
                 'Samples: edge centre plus 2, 6, 12, 24 and 40 studs inward; lateral 0, ±8 and ±(Width/2−8). Runtime freshly cooked precise terrain queries; saved dedicated collision and solid props. All four cardinal approaches and all four runtime calibration scores retained in JSON. Layout yaw is zero, so layout-facing direction equals declared facing. Width/edge margin constrain the tested corridor, not the entire perimeter.', '',
                 'Independent visible-surface evidence: Blender triangle BVH from the preserved refreshed export input; source SHA256 and all 30 terrain digests match the production ledger. Export-local Blender axes map to imported Roblox (−X, Z, +Y), followed by selected art yaw. Boundary triangle misses at exactly depth zero are inconclusive; inset central corridor and representative width are assessed. All raw heights/normals/obstructions remain available.', '',
                 'PASS means sampled source/composition agreement, not a completed character traversal. SUSPICIOUS is retained for owner inspection; no automatic repair. No unusual socket has enough documented evidence to assign INTENTIONAL/SPECIAL merely to dismiss a miss.', '',
                 '| Chunk | Socket | Kind / direction / offset / width | Hint → selected; score / centres | Collision centre /30 grid | Terrain centre /30 grid | Authored core / width | Class |',
                 '|---|---|---|---|---|---|---|---|']
        anomalies = []
        for c in data['chunks']:
            name = 'chunk_' + c['id'][3:].lower()
            name = {'VV_CAP_TREASURE_HOLLOW':'chunk_side_treasure_hollow','VV_CAP_WARDENS_CLEARING':'chunk_side_wardens_clearing'}.get(c['id'],name)
            labels=[]
            calibration=next(k for k in c['calibration'] if k['offset']==c['selected'])
            for s in c['sockets']:
                result=classify(c,s,authors[name],widths.get(c['id']));s['assessment']=result
                counts[result['class']]+=1;labels.append(result['class'])
                centre=[p for p in s['samples'] if p['lateral']==0]
                ch=sum(p['collision']['walk'] for p in centre);th=sum(p['terrain']['walk'] for p in centre)
                cw=sum(p['collision']['walk'] for p in s['samples']);tw=sum(p['terrain']['walk'] for p in s['samples'])
                lines.append(f"| {c['id']} | {s['index']}:{s['name']} | {s['kind']} / {s['facing']}° / {s['offset']} / {s['width']} | {c['hint']}→{c['selected']}; {calibration['score']} / {calibration['centreHits']} | {ch}/6; {cw}/30 | {th}/6; {tw}/30 | {result['authored_core_hits']}/{result['authored_core_count']}; {result['authored_width_hits']}/{result['authored_width_count']} | {result['class']} |")
                if result['failures'] or result['warnings'] or result['query_notes']:
                    anomalies.append(f"- **{c['id']} / {s['name']} ({result['class']}):** " + '; '.join(result['failures']+result['warnings']+result['query_notes']) + '.')
            c['assessment']='FAIL' if 'FAIL' in labels else 'SUSPICIOUS' if 'SUSPICIOUS' in labels else 'PASS'
            chunk_counts[c['assessment']]+=1
        lines[2:2]=[f"30 chunks; {sum(counts.values())} sockets. Socket counts: {dict(counts)}. Chunk counts: {dict(chunk_counts)}. INTENTIONAL/SPECIAL: 0.",'']
        lines += ['', '## Every detected anomaly', ''] + anomalies
        if widths:
            lines += ['', '## Added path identity and width criterion', '',
                      'These follow-up verdicts include exact VV_Path mouth identity and independently measured 2-stud level pad/material widths. A 50-stud colored path with a pad at least 50 studs is the WIDE signature; a 43-stud path is PATH. No centered path mouth is FAIL even when grass/query hulls are walkable. Existing authored buffer remains included in the declared 48/52 widths. Full slices and root cause are in VV_SOCKET_WIDTH_EVIDENCE.json and VV_SOCKET_WIDTH_REVIEW.md. Original Session 204 snapshots remain unchanged.', '']
        lines += ['', '## Evidence limitations and preservation', '',
                  'The saved default terrain hull differs from runtime precise hulls (comparison JSON retained). Neither hull is the visible triangle mesh. Isolated sample misses may be collider seams or query cooking artifacts and are not proof of an unusable player corridor. EditableMesh/security settings were not changed. No existing asset, ID, staging export, recovery material or protected Stone rollback was replaced.', '',
                  'The entire authored source was read without saving. Prop placements resolved against the saved library; solid/nonsolid/Sway counts and runtime calibration are in raw JSON. Source solid obstruction probes cover nearby authored meshes; large joined prop bounds alone are not treated as obstacles.', '']
        (ROOT / f'docs/VV_SOCKET_AUDIT_{phase}.md').write_text('\n'.join(lines),encoding='utf-8')
        data['counts']={'sockets':dict(counts),'chunks':dict(chunk_counts),'total_sockets':sum(counts.values())}
        (ROOT / f'docs/VV_SOCKET_AUDIT_{phase}.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
        print(phase, data['counts'])


if __name__ == '__main__':
    main()
