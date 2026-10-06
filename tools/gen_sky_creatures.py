"""Generates src/shared/Content/Hub/SkyCreatures.luau, the sky's creature roster.

    python tools/gen_sky_creatures.py          # write the file
    python tools/gen_sky_creatures.py --check  # exit 1 if the file is stale

Merges:
  * every assets/export/hub/crossroads/creatures_<group>.json sidecar (schema in
    docs/design/SKY_ECOSYSTEM_CONTRACT.md 4.1; missing sidecars are fine: the
    roster is then just what exists), and
  * the retained sky whale, whose body size and moving parts come from the
    generated Content/Hub/CrossroadsV2.luau (Orbiters / OrbiterParts), unchanged.

Behaviour is NOT here: it is the class profile in GameConfig.HubLayout.V2.SkyLife.
This file is data only (model, class, size, biome, CanLand, weight, parts).
Util/Schema.validateSkyCreatures checks it at boot.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXPORT = ROOT / "assets" / "export" / "hub" / "crossroads"
LAYOUT_LUAU = ROOT / "src" / "shared" / "Content" / "Hub" / "CrossroadsV2.luau"
OUT = ROOT / "src" / "shared" / "Content" / "Hub" / "SkyCreatures.luau"

CLASSES = ("TINY", "SMALL", "MEDIUM", "LARGE", "COLOSSAL")
KINDS = ("Flap", "Spin", "Flicker", "Pulse")
GAITS = ("Always", "Flight", "Idle", "Turn", "Thrust")

# Which species may perch (owner: some small/medium species only, never colossals).
# A data flag: flip it here and regenerate.
CAN_LAND = {"skyfinch", "canopy_drake"}
# Relative spawn weight within a class (default 1).
WEIGHT: dict[str, float] = {}
# Per-species scale range applied by HubV2.buildSky (the whale has always varied).
SCALE = {"sky_whale": (1.0, 1.6)}

WHALE = "sky_whale"


def vec(v) -> str:
    return "Vector3.new(%s, %s, %s)" % tuple(num(x) for x in v)


def num(x: float) -> str:
    s = ("%.4f" % float(x)).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def upper_id(species: str) -> str:
    return species.upper()


def to_orbiter(v):
    """Blender axes (head +X, up +Z) to the OrbiterParts frame, as make_layout_luau.local()."""
    return [round(-v[0], 3), round(v[2], 3), round(v[1], 3)]


def load_sidecars() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for path in sorted(EXPORT.glob("creatures_*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        # "frame": "orbiter" (default) is already OrbiterParts space; "blender" is converted here
        conv = to_orbiter if data.get("frame") == "blender" else (lambda v: v)
        for cid, c in data.get("creatures", {}).items():
            if cid in out:
                sys.exit(f"duplicate creature {cid} (in {path.name})")
            parts = {}
            for pname, p in c.get("parts", {}).items():
                parts[pname] = {
                    "Kind": p["kind"],
                    "Offset": conv(p["offset"]),
                    "Hinge": conv(p["hinge"]),
                    "Axis": conv(p["axis"]),
                    "Amp": p["amp"],
                    "Rate": p["rate"],
                    "Phase": p["phase"],
                    "Chain": p.get("chain"),
                    "Lag": p.get("lag", 0),
                    "Gait": p.get("gait", "Always"),
                    # soft hinge-angle range, radians [min, max] (contract 7.5), optional
                    "Limit": p.get("limit"),
                }
            spine = c.get("spine")
            out[cid] = {
                # serpent / eel locomotion (contract 7.4), optional:
                # {"parts": [root segment first...], "wavelength": studs, "amp": studs,
                #  "rate": Hz, "plane": "lateral"|"vertical"}
                "Spine": spine,
                "Model": c["model"],
                "Class": c["class"],
                "Size": c["size"],
                "Biome": c.get("biome", []),
                "Tris": c.get("tris"),
                "Centre": conv(c["centre"]) if c.get("centre") else None,
                "Parts": parts,
            }
    return out


def load_whale() -> dict | None:
    if not LAYOUT_LUAU.exists():
        return None
    text = LAYOUT_LUAU.read_text(encoding="utf-8")
    m = re.search(r"hubprop_sky_whale = \{ Size = Vector3\.new\(([^)]*)\) \}", text)
    if not m:
        return None
    size = [float(x) for x in m.group(1).split(",")]
    parts = {}
    pat = re.compile(
        r'(hubprop_sky_whale__\w+) = \{ Parent = "hubprop_sky_whale", Kind = "(\w+)", '
        r"Offset = Vector3\.new\(([^)]*)\), Hinge = Vector3\.new\(([^)]*)\), "
        r"Axis = Vector3\.new\(([^)]*)\), Amp = ([-\d.]+), Rate = ([-\d.]+), Phase = ([-\d.]+) \}"
    )
    for m in pat.finditer(text):
        name, kind, off, hinge, axis, amp, rate, phase = m.groups()
        f3 = lambda s: [float(x) for x in s.split(",")]
        parts[name] = {
            "Kind": kind,
            "Offset": f3(off),
            "Hinge": f3(hinge),
            "Axis": f3(axis),
            "Amp": float(amp),
            "Rate": float(rate),
            "Phase": float(phase),
            "Chain": None,
            "Lag": 0,
            "Gait": "Always",
            "Limit": None,
        }
    return {
        "Model": "hubprop_sky_whale",
        "Class": "LARGE",
        "Size": size,
        "Biome": [],
        "Tris": None,
        "Parts": parts,
    }


def render(roster: dict[str, dict]) -> str:
    o = [
        "--!strict",
        "-- GENERATED by tools/gen_sky_creatures.py from the creature sidecars",
        "-- (assets/export/hub/crossroads/creatures_<group>.json) and the sky whale in",
        "-- Content/Hub/CrossroadsV2.luau. Do not edit by hand: change the sidecar or the",
        "-- generator and regenerate.",
        "--",
        "-- The sky's creature roster: DATA ONLY. How each one flies is its class profile,",
        "-- GameConfig.HubLayout.V2.SkyLife.Classes. Each Parts entry is a hinged rigid",
        "-- sub-mesh of the body, in the body's own space, exactly as CrossroadsV2.OrbiterParts:",
        "-- Kind Flap | Spin | Flicker | Pulse; Chain names the part whose motion this one",
        "-- rides on (tail, neck, wing tip) and Lag its phase lag behind it; Gait says when",
        "-- it moves (Always | Flight | Idle | Turn | Thrust). CanLand: may perch on backdrop islands.",
        "-- Limit = { min, max } radians soft-clamps the part's hinge angle (no self-clipping).",
        "-- Spine = serpent / eel locomotion: Parts root-first, Wavelength/Amp studs, Rate Hz, Plane.",
        "-- Biome is RESERVED (unread): see docs/RESERVED.md.",
        "",
        "return {",
    ]
    for species in sorted(roster):
        c = roster[species]
        lo, hi = SCALE.get(species, (1.0, 1.0))
        biome = ", ".join('"%s"' % b for b in c["Biome"])
        o.append(f"	{upper_id(species)} = {{")
        o.append(f'		Model = "{c["Model"]}",')
        o.append(f'		Class = "{c["Class"]}",')
        o.append(f"		Size = {vec(c['Size'])},")
        o.append(f"		Biome = {{ {biome} }}," if biome else "		Biome = {},")
        o.append(f"		CanLand = {'true' if species in CAN_LAND else 'false'},")
        o.append(f"		Weight = {num(WEIGHT.get(species, 1))},")
        o.append(f"		ScaleMin = {num(lo)},")
        o.append(f"		ScaleMax = {num(hi)},")
        if c.get("Centre") and any(abs(x) > 1e-6 for x in c["Centre"]):
            o.append(f"		Centre = {vec(c['Centre'])},")
        sp = c.get("Spine")
        if sp:
            o.append("		Spine = {")
            o.append("			Parts = {")
            for name in sp["parts"]:
                o.append(f'				"{name}",')
            o.append("			},")
            o.append(f"			Wavelength = {num(sp['wavelength'])},")
            o.append(f"			Amp = {num(sp['amp'])},")
            o.append(f"			Rate = {num(sp['rate'])},")
            o.append(f'			Plane = "{sp["plane"]}",')
            o.append("		},")
        o.append("		Parts = {")
        for pname in sorted(c["Parts"]):
            p = c["Parts"][pname]
            # one field per line: this is how StyLua lays these out at 100 columns,
            # so the file is formatter-clean as generated
            o.append(f"			{pname} = {{")
            o.append(f'				Kind = "{p["Kind"]}",')
            o.append(f"				Offset = {vec(p['Offset'])},")
            o.append(f"				Hinge = {vec(p['Hinge'])},")
            o.append(f"				Axis = {vec(p['Axis'])},")
            o.append(f"				Amp = {num(p['Amp'])},")
            o.append(f"				Rate = {num(p['Rate'])},")
            o.append(f"				Phase = {num(p['Phase'])},")
            if p["Chain"]:
                o.append(f'				Chain = "{p["Chain"]}",')
            o.append(f"				Lag = {num(p['Lag'])},")
            o.append(f'				Gait = "{p["Gait"]}",')
            if p.get("Limit"):
                o.append(f"				Limit = {{ {num(p['Limit'][0])}, {num(p['Limit'][1])} }},")
            o.append("			},")
        o.append("		},")
        o.append("	},")
    o.append("}")
    return "\n".join(o) + "\n"


def main() -> int:
    roster = load_sidecars()
    for cid, c in roster.items():
        if c["Class"] not in CLASSES:
            sys.exit(f"{cid}: unknown class {c['Class']}")
        for pname, p in c["Parts"].items():
            if p["Kind"] not in KINDS or p["Gait"] not in GAITS:
                sys.exit(f"{cid}/{pname}: bad kind or gait")
            lim = p.get("Limit")
            if lim is not None and not (len(lim) == 2 and lim[0] <= lim[1]):
                sys.exit(f"{cid}/{pname}: limit must be [min, max] radians with min <= max")
        sp = c.get("Spine")
        if sp:
            if sp.get("plane") not in ("lateral", "vertical") or len(sp.get("parts", [])) < 2:
                sys.exit(f"{cid}: spine needs >= 2 parts and plane lateral|vertical")
            for name in sp["parts"]:
                if name not in c["Parts"]:
                    sys.exit(f"{cid}: spine part {name} is not a part of the creature")
    whale = load_whale()
    if whale and WHALE not in roster:
        roster[WHALE] = whale
    elif not whale:
        print("note: sky whale not found in CrossroadsV2.luau; roster has no whale", file=sys.stderr)
    text = render(roster)
    if "--check" in sys.argv:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current.replace("\r\n", "\n") != text:
            print("SkyCreatures.luau is stale: run python tools/gen_sky_creatures.py")
            return 1
        return 0
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(roster)} creature(s): {', '.join(sorted(roster))})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
