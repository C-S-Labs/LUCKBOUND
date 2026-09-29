"""Check the combined Verdant Valley collision export before Studio walking."""

import json
import re
import shutil
import sys
import tempfile
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "assets/export/worlds/verdant_valley/walk_collision_kit/kit_report.json"
RBXMX = ROOT / "assets/rbxm/chunks/verdant_valley/VV_COLLISION.rbxmx"


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


def main():
    expected = {row["model"]: row["merged_colliders"]
                for row in json.loads(REPORT.read_text(encoding="utf-8"))["chunks"]}
    root = ET.parse(RBXMX).getroot()
    errors = []
    roots = root.findall("./Item")
    if len(roots) != 1 or roots[0].get("class") != "Model" or named(roots[0]) != "VV_COLLISION":
        errors.append("Expected one top-level Model named VV_COLLISION")
    if not roots:
        print("\n".join(errors))
        return 1
    container = roots[0]
    models = container.findall("./Item[@class='Model']")
    names = [named(model) for model in models]
    if len(models) != 28 or set(names) != set(expected) or len(set(names)) != len(names):
        errors.append(f"Child model names differ from report: {len(models)} found, "
                      f"missing={sorted(set(expected)-set(names))}, extra={sorted(set(names)-set(expected))}")
    if len(container.findall("./Item")) != len(models):
        errors.append("Container has extra direct children")
    mesh_ids = set()
    total = 0
    for model in models:
        name = named(model)
        parts = descendants(model, "MeshPart")
        count = len(parts)
        total += count
        if count != expected.get(name):
            errors.append(f"{name}: {count} MeshParts, expected {expected.get(name)}")
        if prop(model, "Ref", "PrimaryPart") is None or prop(model, "Ref", "PrimaryPart").text != "null":
            errors.append(f"{name}: PrimaryPart is set")
        pivot = prop(model, "OptionalCoordinateFrame", "WorldPivotData")
        frame = pivot.find("CFrame") if pivot is not None else None
        if frame is None or any(abs(float(frame.findtext(axis, "nan"))) > 0.001
                                for axis in ("X", "Y", "Z")):
            errors.append(f"{name}: nonzero or absent WorldPivot")
        for part in parts:
            if named(part) == "CollisionOrigin":
                errors.append(f"{name}: origin marker remains")
            mesh = prop(part, "Content", "MeshId")
            url = mesh.findtext("url", "") if mesh is not None else ""
            if not re.fullmatch(r"rbxassetid://\d+", url):
                errors.append(f"{name}: missing or invalid MeshId")
            elif url in mesh_ids:
                errors.append(f"{name}: duplicate MeshId {url}")
            mesh_ids.add(url)
            fidelity = prop(part, "token", "CollisionFidelity")
            if fidelity is None or fidelity.text != "3":
                errors.append(f"{name}: missing precise CollisionFidelity")
            transparency = prop(part, "float", "Transparency")
            if transparency is None or float(transparency.text) != 1.0:
                errors.append(f"{name}: collider is visible")
            for field, value in (("Anchored", "true"), ("CanCollide", "true"),
                                 ("CanQuery", "true"), ("CanTouch", "false")):
                entry = prop(part, "bool", field)
                if entry is None or entry.text != value:
                    errors.append(f"{name}: {field} is not {value}")
    expected_total = sum(expected.values())
    print(f"Models: {len(models)}/28; MeshParts: {total}/{expected_total}; unique MeshIds: {len(mesh_ids)}")
    for error in errors[:20]:
        print("ERROR:", error)
    if len(errors) > 20:
        print(f"... {len(errors)-20} more errors")
    return 1 if errors else 0


if __name__ == "__main__":
    if "--normalize" in sys.argv:
        normalize()
    if "--raise" in sys.argv:
        raise_surface(float(sys.argv[sys.argv.index("--raise") + 1]))
    if "--repair-fidelity" in sys.argv:
        repair_fidelity()
    sys.exit(main())
