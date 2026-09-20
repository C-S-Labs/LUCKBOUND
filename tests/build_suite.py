#!/usr/bin/env python3
"""Bundles the real src/ modules + tests/cases.luau into one runnable Luau file.

Tests run against the actual source files, not copies. Roblox-only globals are
shimmed; Roblox-only modules (SaveSystem, FateSystem, EventSystem, the Worlds
registry's script:GetChildren loop) are excluded -- their pure logic lives in
Core/*Core.luau and ProfileSchema, which ARE tested here.
"""
import re, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

PURE_MODULES = [
    ("Types",            "src/shared/Core/Types.luau"),
    ("Constants",        "src/shared/Core/Constants.luau"),
    ("GameConfig",       "src/shared/Core/GameConfig.luau"),
    ("Result",           "src/shared/Core/Result.luau"),
    ("WeightedRandom",   "src/shared/Util/WeightedRandom.luau"),
    ("FateCore",         "src/shared/Core/FateCore.luau"),
    ("ProgressionCore",  "src/shared/Core/ProgressionCore.luau"),
    ("ProfileSchema",    "src/shared/Core/ProfileSchema.luau"),
    ("EventCore",        "src/shared/Core/EventCore.luau"),
    ("AssetManifest",    "src/shared/Content/AssetManifest.luau"),
    ("ChunkCore",        "src/shared/Util/ChunkCore.luau"),
    ("ExpeditionCore",   "src/shared/Core/ExpeditionCore.luau"),
    ("Schema",           "src/shared/Util/Schema.luau"),
    ("UITheme",          "src/shared/Core/UITheme.luau"),
    ("Crossroads",       "src/shared/Content/Hub/Crossroads.luau"),
    ("SettingsCore",     "src/shared/Core/SettingsCore.luau"),
    ("HubMenuCore",      "src/shared/Core/HubMenuCore.luau"),
    ("CodeCore",         "src/shared/Core/CodeCore.luau"),
    ("LocomotionCore",   "src/shared/Core/LocomotionCore.luau"),
    ("Menu",             "src/shared/Content/Hub/Menu.luau"),
    ("Cinematics",       "src/shared/Content/Hub/Cinematics.luau"),
    ("Codes",            "src/shared/Content/Codes.luau"),
]

WORLD_FILES = sorted((ROOT / "src/shared/Content/Worlds").glob("*.luau"))

REQUIRE_RE = re.compile(r'require\(\s*script[\w.]*?\.(\w+)\s*\)')

def transform(src: str) -> str:
    # require(script.Parent.Parent.Core.Constants) -> __require("Constants")
    return REQUIRE_RE.sub(lambda m: f'__require("{m.group(1)}")', src)

SHIM = '''
-- === Roblox global shims ===========================================
local Color3 = {}
function Color3.fromHex(hex) return { __c3 = true, hex = hex } end
function Color3.fromRGB(r, g, b) return { __c3 = true, r = r, g = g, b = b } end

-- typeof() must distinguish Roblox datatypes the way the real engine does.
-- Shimming these as plain tables is what let a type()-vs-typeof() bug reach
-- Studio: type() on a real Vector3 returns "vector", never "table".
local _luatype = type
local function typeof(v)
	if _luatype(v) == "table" then
		if rawget(v, "__v3") then return "Vector3" end
		if rawget(v, "__c3") then return "Color3" end
		if rawget(v, "__udim") then return "UDim" end
	end
	return _luatype(v)
end

local UDim = {}
function UDim.new(scale, offset) return { __udim = true, Scale = scale, Offset = offset } end

-- A Vector3 that ADDS like one. The first shim was a plain table, so
-- `anchor + landing` -- which is how the hub menu states where a traveller
-- lands -- would have raised in the harness while working in Studio, and the
-- test would have been deleted rather than the bug found. CLAUDE.md: a shim
-- that does not behave like the real type is worse than no test.
local Vector3 = {}
local __v3meta = {}
__v3meta.__index = function(v, key)
	if key == "Magnitude" then
		return math.sqrt(rawget(v, "X") ^ 2 + rawget(v, "Y") ^ 2 + rawget(v, "Z") ^ 2)
	end
	return nil
end
__v3meta.__add = function(a, b) return Vector3.new(a.X + b.X, a.Y + b.Y, a.Z + b.Z) end
__v3meta.__sub = function(a, b) return Vector3.new(a.X - b.X, a.Y - b.Y, a.Z - b.Z) end
__v3meta.__mul = function(a, b)
	if type(b) == "number" then return Vector3.new(a.X * b, a.Y * b, a.Z * b) end
	return Vector3.new(a.X * b.X, a.Y * b.Y, a.Z * b.Z)
end
-- Roblox Vector3 compares BY VALUE. Two separately constructed anchors at the
-- same point are equal there, so they must be equal here.
__v3meta.__eq = function(a, b) return a.X == b.X and a.Y == b.Y and a.Z == b.Z end
__v3meta.__tostring = function(v) return string.format("%g, %g, %g", v.X, v.Y, v.Z) end
function Vector3.new(x, y, z)
	return setmetatable({ __v3 = true, X = x or 0, Y = y or 0, Z = z or 0 }, __v3meta)
end
Vector3.zero = Vector3.new(0, 0, 0)
Vector3.one = Vector3.new(1, 1, 1)

-- Enum values only need to be distinct and comparable here.
-- Roblox EnumItems are SINGLETONS: Enum.Material.Neon == Enum.Material.Neon.
-- The first version of this shim built a fresh table on every access, so that
-- comparison was always false and any test asserting a material silently could
-- not pass. Same class of bug as the Vector3-as-table shim recorded in
-- CLAUDE.md -- an unfaithful shim is worse than no test. Each item is now
-- cached, so identity behaves the way the real engine does.
local Enum = setmetatable({}, { __index = function(t, category)
	local items = {}
	local c = setmetatable({}, { __index = function(_, name)
		if items[name] == nil then
			items[name] = { __enum = true, Category = category, Name = name }
		end
		return items[name]
	end })
	rawset(t, category, c)
	return c
end })

local __modules = {}
local __cache = {}
function __require(name)
	if __cache[name] ~= nil then return __cache[name] end
	local factory = __modules[name]
	if not factory then error("test harness: no module registered named " .. name, 2) end
	local value = factory()
	__cache[name] = value
	return value
end

local function __define(name, factory) __modules[name] = factory end
'''

def main():
    out = [SHIM]

    for name, rel in PURE_MODULES:
        src = transform((ROOT / rel).read_text())
        out.append(f'\n-- === {rel} ===\n__define("{name}", function()\n{src}\nend)\n')

    # Worlds registry: the real init.luau walks script:GetChildren(), which has
    # no headless equivalent. Rebuild it from the same world files.
    world_defs = []
    for wf in WORLD_FILES:
        if wf.name == "init.luau":
            continue
        src = transform(wf.read_text())
        world_defs.append(f'\tdo\n\t\tlocal w = (function()\n{src}\n\t\tend)()\n\t\tassert(registry[w.Id] == nil, "duplicate world Id: " .. w.Id)\n\t\tregistry[w.Id] = w\n\tend')
    out.append('\n-- === Worlds registry (rebuilt for headless) ===\n__define("Worlds", function()\n\tlocal registry = {}\n'
               + "\n".join(world_defs) + '\n\treturn registry\nend)\n')

    chunk_files = sorted((ROOT / "src/shared/Content/Chunks").glob("*.luau"))
    kits = []
    for cf in chunk_files:
        if cf.name == "init.luau":
            continue
        kits.append(f'\tdo\n\t\tlocal kit = (function()\n{transform(cf.read_text())}\n\t\tend)()\n\t\tfor _, c in kit do\n\t\t\tassert(registry[c.Id] == nil, "duplicate chunk Id: " .. c.Id)\n\t\t\tregistry[c.Id] = c\n\t\tend\n\tend')
    out.append('\n-- === Chunk registry (rebuilt for headless) ===\n__define("Chunks", function()\n\tlocal registry = {}\n'
               + "\n".join(kits) + '\n\treturn registry\nend)\n')

    out.append("\n-- === test cases ===\n")
    out.append((ROOT / "tests/cases.luau").read_text())

    target = ROOT / "tests/generated_suite.luau"
    target.write_text("".join(out))
    print(f"wrote {target.relative_to(ROOT)} ({len(''.join(out))} bytes, {len(PURE_MODULES)} modules, {len(world_defs)} worlds)")

if __name__ == "__main__":
    sys.exit(main())
