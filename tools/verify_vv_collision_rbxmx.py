"""Read-only production VV collider checks; legacy mutation helpers remain guarded.

Default success verifies structure, not omitted serialized collision fidelity.
Use --strict-fidelity to require explicit precise tokens; Studio/Rojo inspection
is still required when physical configuration is serialized without those tokens.
"""

import base64
import json
import math
import re
import shutil
import sys
import tempfile
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

from wire_vv_imports import chunk_id

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "assets/export/worlds/verdant_valley/walk_collision_kit/kit_report.json"
RBXMX = ROOT / "assets/rbxm/chunks/verdant_valley/VV_COLLISION.rbxmx"
PRODUCTION_MANIFEST = ROOT / "assets/export/worlds/verdant_valley_staging_refresh/export_manifest.json"
CHUNKS = ROOT / "src/shared/Content/Chunks/VerdantValley.luau"
STONE = ROOT / "assets/rbxm/chunks/verdant_valley/VV_STONE_SENTINELS_COLLISION_MERGED.rbxmx"


def normalize():
    """Wrap the 28 new models and add Studio-omitted precise fidelity tokens."""
    from lxml import etree

    expected = {row["model"]: row["merged_colliders"]
                for row in json.loads(REPORT.read_text(encoding="utf-8"))["chunks"]}
    parser = etree.XMLParser(strip_cdata=False, huge_tree=True)
    tree = etree.parse(str(RBXMX), parser)
    root = tree.getroot()
    models = root.findall("./Item")
    names = [named(model) for model in models]
    extras = {"VV_STONE_SENTINELS_COLLISION", "VV_STONE_SENTINELS_COLLISION_MERGED", "VV_STRUCTURE"}
    if len(models) != 31 or set(names) != set(expected) | extras or len(names) != len(set(names)):
        raise ValueError("Unexpected export roots; refusing to rewrite the RBXMX")
    ids = set()
    for model in models:
        if named(model) not in expected:
            continue
        parts = descendants(model, "MeshPart")
        if len(parts) != expected[named(model)]:
            raise ValueError(f"{named(model)} has {len(parts)} MeshParts")
        for part in parts:
            mesh = prop(part, "Content", "MeshId")
            url = mesh.findtext("url", "") if mesh is not None else ""
            if not re.fullmatch(r"rbxassetid://\d+", url) or url in ids:
                raise ValueError(f"{named(model)} has an invalid or duplicate MeshId")
            ids.add(url)
            fidelity = prop(part, "token", "CollisionFidelity")
            if fidelity is None:
                fidelity = etree.Element("token", name="CollisionFidelity")
                fidelity.text = "3"
                properties = part.find("Properties")
                properties.insert(0, fidelity)
            else:
                fidelity.text = "3"
    container = etree.Element("Item", {"class": "Model", "referent": "RBX" + uuid.uuid4().hex.upper()})
    properties = etree.SubElement(container, "Properties")
    etree.SubElement(properties, "bool", name="NeedsPivotMigration").text = "false"
    etree.SubElement(properties, "Ref", name="PrimaryPart").text = "null"
    pivot = etree.SubElement(properties, "OptionalCoordinateFrame", name="WorldPivotData")
    frame = etree.SubElement(pivot, "CFrame")
    for axis, value in (("X", "0"), ("Y", "0"), ("Z", "0"),
                        ("R00", "1"), ("R01", "0"), ("R02", "0"),
                        ("R10", "0"), ("R11", "1"), ("R12", "0"),
                        ("R20", "0"), ("R21", "0"), ("R22", "1")):
        etree.SubElement(frame, axis).text = value
    etree.SubElement(properties, "string", name="Name").text = "VV_COLLISION"
    for model in models:
        root.remove(model)
        if named(model) in expected:
            container.append(model)
    root.append(container)
    backup = Path(tempfile.gettempdir()) / f"vv_collision_original_{uuid.uuid4().hex}.rbxmx"
    shutil.copy2(RBXMX, backup)
    replacement = RBXMX.with_suffix(".rbxmx.tmp")
    tree.write(str(replacement), encoding="utf-8", xml_declaration=False)
    replacement.replace(RBXMX)
    print(f"Normalized 28 models and {len(ids)} MeshIds; original saved at {backup}")


def raise_surface(amount):
    """Move only the 28 new collider parts upward without changing their MeshIds."""
    from lxml import etree

    if amount <= 0 or amount > 0.25:
        raise ValueError("Raise must be greater than zero and at most 0.25 stud")
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    if any(row.get("surface_offset_studs", 0.35) <= 0.20 for row in report["chunks"]):
        raise ValueError("Current generation report already targets a 0.20-stud offset")
    tree = etree.parse(str(RBXMX), etree.XMLParser(strip_cdata=False, huge_tree=True))
    root = tree.getroot()
    containers = root.findall("./Item")
    if len(containers) != 1 or named(containers[0]) != "VV_COLLISION":
        raise ValueError("Expected one VV_COLLISION wrapper")
    if any("VV_COLLISION_SURFACE_RAISE_STUDS=" in (node.text or "") for node in root.xpath("./comment()")):
        raise ValueError("Surface raise is already recorded; refusing a second shift")
    expected = {row["model"]: row["merged_colliders"]
                for row in json.loads(REPORT.read_text(encoding="utf-8"))["chunks"]}
    models = containers[0].findall("./Item[@class='Model']")
    if {named(model) for model in models} != set(expected):
        raise ValueError("Child model names do not match the report")
    moved = 0
    for model in models:
        parts = descendants(model, "MeshPart")
        if len(parts) != expected[named(model)]:
            raise ValueError(f"{named(model)} count differs from report")
        for part in parts:
            frame = prop(part, "CoordinateFrame", "CFrame")
            y = frame.find("Y") if frame is not None else None
            if y is None:
                raise ValueError(f"{named(model)} part lacks a CFrame Y")
            y.text = format(float(y.text) + amount, ".9g")
            moved += 1
    root.insert(0, etree.Comment(f"VV_COLLISION_SURFACE_RAISE_STUDS={amount:g}"))
    backup = Path(tempfile.gettempdir()) / f"vv_collision_before_raise_{uuid.uuid4().hex}.rbxmx"
    shutil.copy2(RBXMX, backup)
    replacement = RBXMX.with_suffix(".rbxmx.tmp")
    tree.write(str(replacement), encoding="utf-8", xml_declaration=False)
    replacement.replace(RBXMX)
    print(f"Raised {moved} collider parts by {amount:g} stud; original saved at {backup}")


def repair_fidelity():
    """Restore precise-fidelity XML tokens omitted by a Studio re-export."""
    from lxml import etree

    tree = etree.parse(str(RBXMX), etree.XMLParser(strip_cdata=False, huge_tree=True))
    root = tree.getroot()
    containers = root.findall("./Item")
    if len(containers) != 1 or named(containers[0]) != "VV_COLLISION":
        raise ValueError("Expected one VV_COLLISION wrapper")
    expected = {row["model"]: row["merged_colliders"]
                for row in json.loads(REPORT.read_text(encoding="utf-8"))["chunks"]}
    models = containers[0].findall("./Item[@class='Model']")
    if len(models) != 28 or {named(model) for model in models} != set(expected):
        raise ValueError("Child model names do not match the report")
    changed = 0
    for model in models:
        parts = descendants(model, "MeshPart")
        if len(parts) != expected[named(model)]:
            raise ValueError(f"{named(model)} count differs from report")
        for part in parts:
            fidelity = prop(part, "token", "CollisionFidelity")
            if fidelity is None:
                fidelity = etree.Element("token", name="CollisionFidelity")
                part.find("Properties").insert(0, fidelity)
                changed += 1
            fidelity.text = "3"
    if changed:
        backup = Path(tempfile.gettempdir()) / f"vv_collision_before_fidelity_{uuid.uuid4().hex}.rbxmx"
        shutil.copy2(RBXMX, backup)
        replacement = RBXMX.with_suffix(".rbxmx.tmp")
        tree.write(str(replacement), encoding="utf-8", xml_declaration=False)
        replacement.replace(RBXMX)
    print(f"Restored {changed} precise-fidelity tokens")


def prop(item, tag, name):
    return item.find(f"./Properties/{tag}[@name='{name}']")


def named(item):
    value = prop(item, "string", "Name")
    return value.text if value is not None else ""


def descendants(item, kind):
    return item.findall(f".//Item[@class='{kind}']")


def expected_counts():
    """Use the independent refreshed export ledger and current content identities."""
    definitions = dict(re.findall(
        r'Id = "(VV_[^"]+)",.*?CollisionTemplate = "([^"]+)"',
        CHUNKS.read_text(encoding="utf-8"), re.S))
    expected = {}
    seen = set()
    manifest = json.loads(PRODUCTION_MANIFEST.read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        if entry["category"] != "collision":
            continue
        ident = chunk_id(entry["chunk"])
        if ident not in definitions or ident in seen:
            raise ValueError(f"Unknown/duplicate collision chunk in production ledger: {ident}")
        seen.add(ident)
        template = definitions[ident]
        if template in expected or not entry["sources"]:
            raise ValueError(f"Duplicate/empty collision template: {template}")
        expected[template] = len(entry["sources"])
    if set(definitions) != seen:
        raise ValueError(f"Production ledger lacks current chunk collision: {set(definitions) - seen}")
    return expected


def check_fidelity(part, shared_strings, label, errors, pending):
    """Reject contradictory tokens or missing configuration; never guess baked fidelity."""
    fidelity = prop(part, "token", "CollisionFidelity")
    if fidelity is not None:
        if fidelity.text != "3":
            errors.append(f"{label}: explicit CollisionFidelity is not precise")
        return
    physical = prop(part, "SharedString", "PhysicalConfigData")
    data = shared_strings.get(physical.text) if physical is not None else None
    try:
        valid = bool(data and base64.b64decode(data, validate=True))
    except ValueError:
        valid = False
    if not valid:
        errors.append(f"{label}: no explicit fidelity or valid serialized physical configuration")
    else:
        pending.append(label)


def check_model(model, expected_count, shared_strings, mesh_ids, errors, pending):
    name = named(model)
    parts = descendants(model, "MeshPart")
    if len(parts) != expected_count:
        errors.append(f"{name}: {len(parts)} MeshParts, expected {expected_count}")
    primary = prop(model, "Ref", "PrimaryPart")
    if primary is None or primary.text != "null":
        errors.append(f"{name}: PrimaryPart is set or absent")
    pivot = prop(model, "OptionalCoordinateFrame", "WorldPivotData")
    frame = pivot.find("CFrame") if pivot is not None else None
    values = [float(frame.findtext(axis, "nan")) for axis in ("X", "Y", "Z")] if frame is not None else []
    if not values or any(not math.isfinite(value) or abs(value) > 0.001 for value in values):
        errors.append(f"{name}: nonzero or absent WorldPivot")
    # ChunkLoader.attachWalkCollision sets runtime Transparency=1; Stone retains
    # source review transparency. Do not rewrite a working template to hide it.
    for part in parts:
        label = f"{name}/{named(part)}"
        if named(part) == "CollisionOrigin":
            errors.append(f"{label}: origin marker remains")
        mesh = prop(part, "Content", "MeshId")
        url = mesh.findtext("url", "") if mesh is not None else ""
        if not re.fullmatch(r"rbxassetid://\d+", url):
            errors.append(f"{label}: missing or invalid MeshId")
        elif url in mesh_ids:
            errors.append(f"{label}: duplicate MeshId {url}")
        mesh_ids.add(url)
        check_fidelity(part, shared_strings, label, errors, pending)
        transparency = prop(part, "float", "Transparency")
        if transparency is None or not 0.0 <= float(transparency.text) <= 1.0:
            errors.append(f"{label}: absent/invalid source transparency")
        for field, value in (("Anchored", "true"), ("CanCollide", "true"),
                             ("CanQuery", "true"), ("CanTouch", "false")):
            entry = prop(part, "bool", field)
            if entry is None or entry.text != value:
                errors.append(f"{label}: {field} is not {value}")
    return len(parts)


def main():
    expected = expected_counts()
    stone_name = "VV_STONE_SENTINELS_COLLISION_MERGED"
    stone_count = expected.pop(stone_name)
    errors, pending = [], []
    mesh_ids = set()
    total = 0
    for path, wrapper, counts in ((RBXMX, "VV_COLLISION", expected),
                                  (STONE, stone_name, {stone_name: stone_count})):
        root = ET.parse(path).getroot()
        roots = root.findall("./Item")
        if len(roots) != 1 or roots[0].get("class") != "Model" or named(roots[0]) != wrapper:
            errors.append(f"{path.name}: expected one top-level Model named {wrapper}")
            continue
        container = roots[0]
        models = container.findall("./Item[@class='Model']") if path == RBXMX else [container]
        names = [named(model) for model in models]
        if set(names) != set(counts) or len(names) != len(set(names)):
            errors.append(f"{path.name}: template names differ, missing={sorted(set(counts)-set(names))}, extra={sorted(set(names)-set(counts))}")
        if path == RBXMX and len(container.findall("./Item")) != len(models):
            errors.append("VV_COLLISION has extra direct children")
        shared = {node.get("md5"): re.sub(r"\s+", "", node.text or "")
                  for node in root.findall("./SharedStrings/SharedString")}
        subtotal = 0
        for model in models:
            subtotal += check_model(model, counts.get(named(model)), shared, mesh_ids, errors, pending)
        total += subtotal
        print(f"{path.name}: {len(models)}/{len(counts)} templates, {subtotal}/{sum(counts.values())} MeshParts")
    print(f"Total: {total} active colliders; {len(mesh_ids)} unique MeshIds")
    if pending:
        print(f"PENDING Studio/Rojo fidelity verification: {len(pending)} parts use serialized PhysicalConfigData without explicit CollisionFidelity; no asset was rewritten.")
    for error in errors[:20]:
        print("ERROR:", error)
    if len(errors) > 20:
        print(f"... {len(errors)-20} more errors")
    if errors:
        return 1
    print("Structural checks passed; physical traversal/fidelity remain Studio checks.")
    return 2 if pending and "--strict-fidelity" in sys.argv else 0


if __name__ == "__main__":
    if "--normalize" in sys.argv:
        normalize()
    if "--raise" in sys.argv:
        raise_surface(float(sys.argv[sys.argv.index("--raise") + 1]))
    if "--repair-fidelity" in sys.argv:
        repair_fidelity()
    sys.exit(main())
