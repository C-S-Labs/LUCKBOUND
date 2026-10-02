"""Print a compact summary; persist complete untruncated authored template metadata."""
import collections
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
envelope = json.loads((root / '.tools/template_inventory.json').read_text(encoding='utf-16'))
value = json.loads(envelope['result']['content'][0]['text'])
if isinstance(value, str):
    value = json.loads(value)
out = root / 'docs/benchmarks/asset_template_inventory.json'
out.write_text(json.dumps(value, indent=2), encoding='utf-8')
print('Total MeshParts:', value['MeshPartCount'])
print('Visuals:', len(value['Visuals']))
print('Fidelities:', dict(collections.Counter(row['Fidelity'] for row in value['Visuals'])))
print('Examples:', [row['Path'] for row in value['Visuals'][:4]])
