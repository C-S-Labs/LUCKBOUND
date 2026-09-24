#!/usr/bin/env python3
"""Copy uploaded mesh ids out of saved .rbxmx files into AssetManifest.luau.

When Studio's 3D Importer uploads a chunk, the new mesh id is written into the
MeshPart's MeshId. Save the imported Model as .rbxmx into
assets/rbxm/chunks/<world>/ and run:

    python tools/sync_asset_ids.py verdant_valley          # dry run: shows changes
    python tools/sync_asset_ids.py verdant_valley --write  # updates the manifest

Each MeshPart NAME decides the manifest key: <PREFIX>_<NAME UPPERCASE>.
    chunk_entry                     -> VV_CHUNK_ENTRY
    chunk_archive__siege            -> SC_CHUNK_ARCHIVE__SIEGE
Only existing manifest entries are updated (AssetId, Status = "UPLOADED",
Source). A name with no entry is reported, never invented -- a new chunk also
needs its Content/Chunks entry, which is design work, not bookkeeping.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "src/shared/Content/AssetManifest.luau"
PREFIX = {"verdant_valley": "VV", "sky_citadel": "SC", "ethereal_scape": "ES",
          "astral_reach": "AR", "emberfall": "EF"}

ITEM = re.compile(r'<Item class="MeshPart"[^>]*>\s*<Properties>(.*?)</Properties>', re.S)
NAME = re.compile(r'<string name="Name">([^<]*)</string>')
MESH = re.compile(r'<Content name="MeshId">\s*<url>([^<]*)</url>')


def read_ids(folder: pathlib.Path):
    found = {}
    for f in sorted(folder.glob("*.rbxmx")):
        # properties are read per MeshPart: a Name and a MeshId are only paired
        # when they sit in the same Properties block
        for props in ITEM.findall(f.read_text(encoding="utf-8")):
            name, mesh = NAME.search(props), MESH.search(props)
            if name and mesh and mesh.group(1).startswith("rbxassetid://"):
                found[name.group(1)] = (mesh.group(1), f)
    return found


def main(argv):
    if not argv or argv[0] not in PREFIX:
        print(__doc__)
        print("worlds:", ", ".join(PREFIX))
        return 2
    world, write = argv[0], "--write" in argv
    folder = ROOT / "assets/rbxm/chunks" / world
    ids = read_ids(folder)
    text = MANIFEST.read_text(encoding="utf-8")
    changed, same, unknown = 0, 0, []
    for name, (url, f) in sorted(ids.items()):
        key = f"{PREFIX[world]}_{name.upper()}"
        entry = re.compile(r'(\t%s = \{\n)(.*?)(\n\t\},)' % re.escape(key), re.S)
        m = entry.search(text)
        if not m:
            unknown.append(f"{name} -> {key}")
            continue
        body = m.group(2)
        src = f.relative_to(ROOT).as_posix()
        new = re.sub(r'AssetId = (?:"[^"]*"|nil)', f'AssetId = "{url}"', body, count=1)
        new = re.sub(r'Status = "[A-Z]+"', 'Status = "UPLOADED"', new, count=1)
        new = re.sub(r'Source = "[^"]*"', f'Source = "{src}"', new, count=1)
        if new == body:
            same += 1
            continue
        print(f"  {key}: {url}")
        text = text[:m.start(2)] + new + text[m.end(2):]
        changed += 1
    print(f"{world}: {len(ids)} meshes in {folder.relative_to(ROOT).as_posix()}, "
          f"{changed} to update, {same} already current")
    for u in unknown:
        print("  NO MANIFEST ENTRY:", u)
    if write and changed:
        MANIFEST.write_text(text, encoding="utf-8", newline="\n")
        print("manifest written -- run the tests next")
    elif changed:
        print("dry run -- add --write to apply")
    return 1 if unknown else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
