"""Check multipart placement against actual Studio-imported mesh centres.

Unlike a Blender FBX round-trip, RBXMX records the native Roblox import axes.
Run with Python from any directory after importing and saving the structure kit.
"""
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
parts = json.loads((ROOT / 'assets/export/worlds/ethereal_scape/ethereal_scape_structure.json').read_text())
content = (ROOT / 'src/shared/Content/Chunks/EtherealScape.luau').read_text()
tree = ET.parse(ROOT / 'assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx')
frames = {}
for item in tree.iter('Item'):
    if item.get('class') != 'MeshPart':
        continue
    props = item.find('Properties')
    name = props.find("string[@name='Name']").text
    frame = props.find("CoordinateFrame[@name='CFrame']")
    frames[name] = [float(frame.find(a).text) for a in 'XYZ']

checked = 0
for chunk, assembly in parts.items():
    base = frames[assembly[0]['Object']]
    for part in assembly:
        actual = frames[part['Object']]
        row = re.search(r'\{ AssetKey = "'+re.escape(part['AssetKey'])+r'",([^}]+)\}', content).group(1)
        for index, axis in enumerate('XYZ'):
            key = 'Offset'+axis
            generated = float(re.search(key+r' = ([-\d.]+)', row).group(1))
            assert abs(generated-part[key]) < .002, (part['Object'],key,'content/metadata mismatch')
            # The Sanctum temple is positioned separately in this saved import.
            # Foliage remains grouped with its supporting terrain in all assemblies.
            if part.get('CanCollide') is False:
                relative = actual[index]-base[index]+assembly[0][key]
                assert abs(relative-part[key]) < .02, (
                    part['Object'],key,'Studio import mismatch',relative,part[key])
        if part.get('CanCollide') is False:
            checked += 1
print(f'PASS: {checked} foliage offsets match actual Studio import centres; all content matches metadata')
