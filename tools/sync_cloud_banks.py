"""Copy current Crossroads cloud banks into the shared client cloud library.
HUB_SKY is read-only. Existing uploaded mesh IDs and SharedStrings are preserved.
"""
from pathlib import Path
import copy
import xml.etree.ElementTree as ET
ROOT = Path(__file__).resolve().parents[1]
NAMES = ('hubsky_cloudbank_a', 'hubsky_cloudbank_b', 'hubsky_cloudbank_c')

def main():
    source = ET.parse(ROOT / 'assets/rbxm/prefabs/HUB_SKY.rbxmx').getroot()
    out = ET.Element('roblox', {'version': '4'})
    model = ET.SubElement(out, 'Item', {'class': 'Model', 'referent': 'CLOUD_BANKS'})
    props = ET.SubElement(model, 'Properties')
    ET.SubElement(props, 'string', {'name': 'Name'}).text = 'CLOUD_BANKS'
    for name in NAMES:
        matches = [i for i in source.iter('Item') if i.get('class') == 'MeshPart'
                   and i.findtext('./Properties/string[@name="Name"]') == name]
        assert len(matches) == 1, name
        model.append(copy.deepcopy(matches[0]))
    required = {i.text for i in model.iter('SharedString')}
    strings = ET.SubElement(out, 'SharedStrings')
    for item in source.findall('./SharedStrings/SharedString'):
        if item.get('md5') in required:
            strings.append(copy.deepcopy(item))
    assert required == {i.get('md5') for i in strings}
    ET.indent(out)
    ET.ElementTree(out).write(ROOT / 'assets/rbxm/props/CLOUD_BANKS.rbxmx',
                             encoding='utf-8', xml_declaration=True)
    print('Copied three Crossroads cloud banks with uploaded IDs and shared mesh data')

if __name__ == '__main__':
    main()
