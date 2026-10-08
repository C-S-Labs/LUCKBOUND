"""Bounded Batch 2 planning exercise; actual ChunkCore, proposed sockets only."""
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
READBACK = HERE / 'source_readback.json'
TEMP = Path('E:/BlenderAIProjects/Runtime/Emberfall_Batch2Plan')
REAL = json.loads(READBACK.read_text())
accepted = json.loads((HERE.parent / 'batch1/batch1_report.json').read_text())['kit']
for row in REAL:
    assert row['geometry_sha256'] == accepted[row['id']]['geometry_sha256']
ALIASES = ['Windward', 'Drainage', 'Orchard', 'Ridge', 'Switchback', 'Waymark', 'Clearing', 'Wagon', 'Fenceline']
defs = {}
for name, row in zip(ALIASES, REAL):
    defs[name] = dict(Id=name, Role='PATH', SizeX=256, SizeZ=256, Sockets=row['sockets'])
PROPOSED = {
    'QuietBend': [('S', 'HOLLOW', 0), ('W', 'HOLLOW', 0)],
    'PastureBend': [('S', 'CREST', 0), ('E', 'CREST', 0)],
    'Swale': [('S', 'HOLLOW', 0), ('N', 'HOLLOW', 0)],
    'Grove': [('S', 'CREST', 0), ('N', 'CREST', 0)],
    'Shoulder': [('S', 'HOLLOW', 0), ('N', 'CREST', 12)],
    'Saddle': [('S', 'CREST', 0), ('N', 'CREST', -8)],
    'Ditch': [('S', 'HOLLOW', 0), ('N', 'HOLLOW', 0)],
    'Fieldstead': [('S', 'CREST', 0), ('N', 'CREST', 0)],
}
for name, edges in PROPOSED.items():
    sockets = []
    for side, kind, datum in edges:
        x, z, face = {'S': (0, 128, 180), 'N': (0, -128, 0), 'W': (-128, 0, 270), 'E': (128, 0, 90)}[side]
        sockets.append(dict(Id=side, Kind='BP_EDGE_' + kind, OffsetX=x, OffsetY=datum, OffsetZ=z, Facing=face, Width=24))
    # Only adjacent connected sides share a corner; opposite-edge rise is free.
    if {edges[0][0], edges[1][0]} not in ({'S', 'N'}, {'E', 'W'}):
        signs = {'HOLLOW': 12, 'CREST': -12}
        assert edges[0][2] + signs[edges[0][1]] == edges[1][2] + signs[edges[1][1]]
    defs[name] = dict(Id=name, Role='PATH', SizeX=256, SizeZ=256, Sockets=sockets)

signature = dict.fromkeys(['Clearing', 'Fenceline', 'QuietBend', 'PastureBend', 'Swale', 'Shoulder', 'Saddle', 'Ditch'], 'LOW')
signature.update(dict.fromkeys(['Windward', 'Drainage', 'Ridge', 'Switchback', 'Grove'], 'MEDIUM'))
signature.update(dict.fromkeys(['Orchard', 'Waymark', 'Wagon', 'Fieldstead'], 'HIGH'))
RECIPES = {
    'Batch 1 repeated control / 16': ['Windward','Clearing','Drainage','Ridge','Orchard','Clearing','Drainage','Clearing','Ridge','Orchard','Clearing','Drainage','Clearing','Ridge','Drainage','Clearing'],
    'Hollow countryside / 16': ['Windward','Swale','QuietBend','Ditch','Clearing','Orchard','Swale','Drainage','Ditch','Ridge','QuietBend','Clearing','Shoulder','Grove','PastureBend','Saddle'],
    'Mixed elevation / 20': ['Windward','Drainage','Swale','Switchback','Saddle','Grove','PastureBend','Fenceline','Waymark','Saddle','Shoulder','Ditch','QuietBend','Clearing','Swale','Wagon','Grove','PastureBend','Saddle','Fenceline'],
    'Long repeated route / 24': ['Windward','Swale','QuietBend','Ditch','Clearing','Shoulder','Saddle','Grove','PastureBend','Fenceline','Fieldstead','Saddle','Shoulder','Swale','QuietBend','Clearing','Ditch','Orchard','Swale','Ridge','Shoulder','Grove','PastureBend','Saddle'],
}

def luau(value):
    if isinstance(value, dict):
        return '{' + ','.join('[' + json.dumps(k) + ']=' + luau(v) for k, v in value.items()) + '}'
    if isinstance(value, list):
        return '{' + ','.join(luau(v) for v in value) + '}'
    return json.dumps(value)

core = (ROOT / 'src/shared/Util/ChunkCore.luau').read_text().replace('local WeightedRandom = require(script.Parent.WeightedRandom)', 'local WeightedRandom = {}')
code = 'local Core=(function()\n' + core + '\nend)()\nlocal defs=' + luau(defs) + '\nlocal recipes=' + luau(RECIPES) + '''
local labels={}
for label in recipes do table.insert(labels,label) end
table.sort(labels)
for _,label in labels do
 local order=recipes[label]
 local placed={{ChunkId=order[1],X=0,Y=0,Z=0,Yaw=0,Index=1}}
 local arrived=nil
 local edgeY={defs[order[1]].Sockets[1].OffsetY}
 for i=2,#order do
  local before=defs[order[i-1]]
  local departure=before.Sockets[2]
  if arrived and departure.Id==arrived.Id then departure=before.Sockets[1] end
  local open=Core.worldSocket(placed[i-1],before,departure)
  local p,a=Core.placeAgainst(defs[order[i]],open,i)
  assert(p,label..": profile mismatch at "..i)
  for j,q in placed do assert(not Core.overlaps(q,defs[order[j]],p,defs[order[i]]),label..": overlap "..i.."/"..j) end
  table.insert(edgeY,open.Y)
  table.insert(placed,p);arrived=a
 end
 local last=defs[order[#order]]
 local exit=last.Sockets[2]
 if arrived and exit.Id==arrived.Id then exit=last.Sockets[1] end
 table.insert(edgeY,Core.worldSocket(placed[#placed],last,exit).Y)
 local rows={}
 for i,p in placed do
  table.insert(rows,string.format('{"name":"%s","x":%.9f,"y":%.9f,"z":%.9f,"yaw":%d,"entryY":%.9f,"exitY":%.9f}',order[i],p.X,p.Y,p.Z,p.Yaw,edgeY[i],edgeY[i+1]))
 end
 print(label.."|["..table.concat(rows,",").."]")
end
'''
(TEMP / 'layout_audit.luau').write_text(code)
proc = subprocess.run(['C:/Users/jhpel/.rokit/bin/luau.exe', str(TEMP / 'layout_audit.luau')], capture_output=True, text=True)
assert proc.returncode == 0, proc.stderr + proc.stdout
result = dict(scope='Planning only: actual Batch 1 sockets plus hypothetical Batch 2 sockets; no new geometry, appearance, collision or gameplay proof.', real_source_hashes={r['id']: r['geometry_sha256'] for r in REAL}, proposed_edges=PROPOSED, layouts={})
for line in proc.stdout.splitlines():
    label, raw = line.split('|', 1)
    rows = json.loads(raw)
    order = [r['name'] for r in rows]
    repeated = {name: [i+1 for i,n in enumerate(order) if n==name] for name in sorted(set(order)) if order.count(name)>1}
    high = [i+1 for i,n in enumerate(order) if signature[n]=='HIGH']
    warnings = []
    for name, positions in repeated.items():
        minimum = 5 if signature[name]=='LOW' else 7
        if signature[name]=='HIGH' or len(positions)> (3 if signature[name]=='LOW' else 2):
            warnings.append(name + ': repeat cap')
        if any(b-a<minimum for a,b in zip(positions,positions[1:])):
            warnings.append(name + ': spacing')
    if any(b-a<5 for a,b in zip(high,high[1:])):
        warnings.append('landmark spacing')
    triples = [tuple(order[i:i+3]) for i in range(len(order)-2)]
    if len(triples) != len(set(triples)):
        warnings.append('repeated three-source motif')
    if label.startswith('Batch 1'):
        assert warnings, 'Control should expose repetition pressure'
    else:
        assert not warnings, (label, warnings)
    low = sum(signature[n]=='LOW' for n in order)
    turns = sum(n in ('Orchard','Switchback','Wagon','QuietBend','PastureBend') for n in order)
    result['layouts'][label] = dict(placements=rows, repeated_sources=repeated, signature_counts={s:sum(signature[n]==s for n in order) for s in ('LOW','MEDIUM','HIGH')}, low_share=round(low/len(order),3), turns=turns, regular_quarter_circle_turns=sum(n in ('Orchard','Switchback','Wagon') for n in order), high_positions=high, socket_elevation_change=round(rows[-1]['exitY']-rows[0]['entryY'],3), warnings=warnings)
(HERE / 'layout_audit.json').write_text(json.dumps(result,indent=2)+'\n')
for label,r in result['layouts'].items():
    print(label, r['signature_counts'], 'turns',r['turns'],'old arcs',r['regular_quarter_circle_turns'],'net rise',r['socket_elevation_change'],'warnings',r['warnings'])
