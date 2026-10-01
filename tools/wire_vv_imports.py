"""Wire current Studio imports to the production export manifest for local testing.

Reads the read-only Studio capture in verdant_valley_staging_validation,
matches shortened importer names, and writes existing content plus a save plan.
No Blender edits, asset upload, geometry generation or new runtime schema.
"""

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAGING = ROOT / "assets/export/worlds/verdant_valley_staging_validation"
ALIASES = {"chunk_side_treasure_hollow": "VV_CAP_TREASURE_HOLLOW",
           "chunk_side_wardens_clearing": "VV_CAP_WARDENS_CLEARING"}


def chunk_id(name):
    return ALIASES.get(name, "VV_" + name.removeprefix("chunk_").upper())


def short_name(name):
    if len(name) <= 50:
        return name
    compact = name.replace("detail_scatter_", "").replace("landmark_", "")
    compact = compact.replace("surround_tree_", "tree_").replace("tree_canopy", "canopy")
    if len(compact) > 50:
        compact = compact[:39] + "_" + hashlib.sha256(name.encode()).hexdigest()[:10]
    return compact


def matches(actual, source):
    if actual == source:
        return True
    if "..." in actual:
        head, tail = actual.split("...", 1)
        return source.startswith(head) and source.endswith(tail)
    return False


def numbers(values):
    return "{ " + ", ".join(f"{v:.6f}".rstrip("0").rstrip(".") if v else "0" for v in values) + " }"


def main():
    imports = json.loads((STAGING / "studio_imports.json").read_text(encoding="utf-8-sig"))
    manifest = json.loads((STAGING / "export_manifest.json").read_text())
    structure_frames = {f['chunk']: f['sources'][0]['matrix_world']
                        for f in manifest['files'] if f['chunk'] and f['category']=='structure'}
    yaws = json.loads((STAGING / "studio_chunk_yaws.json").read_text(encoding="utf-8-sig"))
    assert len(yaws) == 30 and set(yaws.values()) <= {0, 180}
    models = {row["model"]: row for row in imports}
    assert len(models) == len(imports), "Duplicate root import names"
    plan = {"parts": [], "structures": [], "collision": None, "rename_count": 0}
    seen = set()
    for file in manifest["files"]:
        if not file["chunk"]:
            continue
        category = file["category"]
        if category == "collision" and file["chunk"] != "chunk_path_cliff_passage":
            continue  # Keep the existing 29 collision templates.
        model = Path(file["filename"]).stem
        assert model in models, f"Missing Studio import {model}"
        actual = models[model]["parts"]
        assert len(actual) == len(file["sources"]), f"Wrong object count: {model}"
        claimed = set()
        for source in file["sources"]:
            found = [i for i,p in enumerate(actual) if matches(p["name"],source["name"])]
            assert len(found) == 1, f"Ambiguous source mapping: {model}/{source['name']}"
            index = found[0]
            assert index not in claimed, f"Import claimed twice: {model}"
            claimed.add(index)
            part = actual[index]
            assert re.fullmatch(r"rbxassetid://\d+",part["meshId"]), f"Missing MeshId: {model}"
            name = short_name(source["name"])
            record = dict(part, model=model, source=source["name"], target=name,
                          chunk=file["chunk"], chunk_id=chunk_id(file["chunk"]),
                          category=category, chest_role=source.get("chest_role"))
            # These six preserved chest components kept their Crossroads names
            # when duplicated, but are authored on the other two chest chunks.
            destination = None
            if source.get('chest_role') in ('Body', 'Lid', 'BodyHardware'):
                if source['name'].endswith('_02'):
                    destination = 'chunk_side_treasure_hollow'
                elif source['name'].endswith('_03'):
                    destination = 'chunk_cap_cave_mouth'
            if destination:
                old, new = structure_frames[file['chunk']], structure_frames[destination]
                assert all(old[i][j]==new[i][j]==float(i==j) for i in range(3) for j in range(3))
                delta = [old[i][3]-new[i][3] for i in range(3)]
                record['relative'] = part['relative'][:]
                for i, shift in enumerate((-delta[0], delta[2], delta[1])):
                    record['relative'][i] += shift
                record['export_chunk'] = file['chunk']
                record['chunk'], record['chunk_id'] = destination, chunk_id(destination)
            if category == "collision":
                if plan["collision"] is None:
                    plan["collision"] = {"model":model,"parts":[]}
                plan["collision"]["parts"].append(record)
                continue
            assert name not in seen and len(name)<=50, f"Duplicate/long target name: {name}"
            seen.add(name)
            plan["rename_count"] += part["name"] != name
            plan["structures" if category == "structure" else "parts"].append(record)
    assert len(plan["structures"]) == 30 and len(plan["parts"]) == 823
    assert len(plan["collision"]["parts"]) == 66
    assert sum(bool(p["chest_role"]) for p in plan["parts"]) == 12
    (STAGING / "studio_save_plan.json").write_text(json.dumps(plan,indent=2),encoding="utf-8")

    path = ROOT / "src/shared/Content/AssetManifest.luau"
    text = path.read_text(encoding="utf-8")
    for record in plan["structures"]:
        key = "VV_CHUNK_" + record["chunk_id"].removeprefix("VV_")
        pattern = re.compile(r"(\t"+re.escape(key)+r" = \{\n)(.*?)(\n\t\},)",re.S)
        match = pattern.search(text)
        assert match, f"Missing manifest key {key}"
        body = re.sub(r'AssetId = "[^"]*"',f'AssetId = "{record["meshId"]}"',match[2],count=1)
        text = text[:match.start(2)] + body + text[match.end(2):]
    path.write_text(text,encoding="utf-8",newline="\n")

    path = ROOT / "src/shared/Content/Chunks/VerdantValley.luau"
    text = path.read_text(encoding="utf-8")
    for record in plan["structures"]:
        pattern = re.compile(r'(Id = "'+record['chunk_id']+r'",)(.*?)(\n\t\},)',re.S)
        match = pattern.search(text)
        assert match, record["chunk_id"]
        x,y,z = record["size"]
        ground = y/2-record["relative"][1]
        assert abs(x-(384 if record['chunk_id']=='VV_BOSS_SANCTUARY' else 256))<.02 and abs(z-256)<.02
        assert abs(record['relative'][0])<.02 and abs(record['relative'][2])<.02
        body = re.sub(r'SizeX = [\d.]+, SizeY = [\d.]+, SizeZ = [\d.]+,',f'SizeX = {x:.6f}, SizeY = {y:.6f}, SizeZ = {z:.6f},',match[2])
        body = re.sub(r'GroundOffsetY = [\d.]+,',f'GroundOffsetY = {ground:.6f},',body)
        text = text[:match.start(2)] + body + text[match.end(2):]
    text = text.replace('c.MeshYawOffset = 180','c.MeshYawOffset = 0')
    text = re.sub(r'local productionYaws = \{.*?\}\n', '', text, flags=re.S)
    mapping = 'local productionYaws = {\n' + ''.join(f'\t{key} = {value},\n' for key,value in sorted(yaws.items())) + '}\n'
    text = text.replace('local out = {}', mapping + 'local out = {}', 1)
    text = text.replace('c.MeshYawOffset = 0', 'c.MeshYawOffset = productionYaws[c.Id] or 0')
    text = text.replace('-- MeshYawOffset = 180: the same half turn the Sky Citadel export landed at;', '-- Current production imports are already in the chunk frame: MeshYawOffset = 0;')
    path.write_text(text,encoding="utf-8",newline="\n")

    lines = ['--!strict','-- GENERATED by tools/wire_vv_imports.py from verified Studio imports.',
             '-- Independent canopies use Sway; chest pieces and joined scenery remain Static.',
             'return {','\tId = "VERDANT_VALLEY",','\tLibrary = {']
    for record in sorted(plan['parts'],key=lambda p:p['target']):
        lines.append(f'\t\t"{record["target"]}",')
    lines += ['\t},','\tPlacements = {']
    for chunk in sorted({p['chunk_id'] for p in plan['parts']}):
        lines.append(f'\t\t{chunk} = {{')
        for record in sorted((p for p in plan['parts'] if p['chunk_id']==chunk),key=lambda p:p['target']):
            # Captured imported positions are in the art frame. The existing
            # runtime applies the import turn last, about each mesh centre.
            # Convert positions and conjugate rotations into the layout frame.
            pose = record['relative'][:]
            if yaws[chunk] == 180:
                pose[0], pose[2] = -pose[0], -pose[2]
                signs = (-1, 1, -1)
                pose[3:] = [pose[3+i*3+j]*signs[i]*signs[j] for i in range(3) for j in range(3)]
            lines += ['\t\t\t{',f'\t\t\t\tProp = "{record["target"]}",',
                      '\t\t\t\tP = '+numbers(pose[:3])+',',
                      '\t\t\t\tR = '+numbers(pose[3:])+',',
                      '\t\t\t\tS = '+numbers(record['size'])+',',
                      f'\t\t\t\tAnim = "{"Sway" if record["category"] == "wind_canopies" else "Static"}",','\t\t\t\tTier = 1,',
                      '\t\t\t\tCollide = '+str(record['category']=='solid_props' or (record['category']=='special' and record['chest_role'] in ('Body','Lid','BodyHardware'))).lower()+',','\t\t\t},']
        lines.append('\t\t},')
    lines += ['\t},','}','']
    (ROOT/'src/shared/Content/Props/VerdantValley.luau').write_text('\n'.join(lines),encoding='utf-8')
    print(f"Wired 30 structure IDs, 823 prop rows; {plan['rename_count']} names need shortening")


def refresh_import_ids():
    """Refresh installed terrain IDs without rebuilding validated placements."""
    path = ROOT / 'assets/export/worlds/verdant_valley_staging_refresh/studio_refresh_install.json'
    installed = json.loads(path.read_text(encoding='utf-8-sig'))['installed']
    records = [r for r in installed['visuals'] if r['category']=='structure']
    assert len(records)==2
    manifest = ROOT / 'src/shared/Content/AssetManifest.luau'
    text = manifest.read_text(encoding='utf-8')
    for record in records:
        assert re.fullmatch(r'rbxassetid://\d+', record['id'])
        key = 'VV_CHUNK_' + chunk_id(record['source']).removeprefix('VV_')
        pattern = re.compile(r'(\t'+re.escape(key)+r' = \{\n)(.*?)(\n\t\},)',re.S)
        match = pattern.search(text)
        assert match, key
        body = re.sub(r'AssetId = "[^"]*"',f'AssetId = "{record["id"]}"',match[2],count=1)
        text = text[:match.start(2)] + body + text[match.end(2):]
    manifest.write_text(text,encoding='utf-8',newline='\n')
    print('Refreshed two terrain IDs; existing placement/chest/yaw data preserved')


if __name__ == '__main__':
    import sys
    if '--refresh' in sys.argv:
        refresh_import_ids()
    else:
        main()
