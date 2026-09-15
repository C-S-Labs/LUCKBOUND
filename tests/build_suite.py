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
    ("Schema",           "src/shared/Util/Schema.luau"),
    ("Crossroads",       "src/shared/Content/Hub/Crossroads.luau"),
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

local Vector3 = {}
function Vector3.new(x, y, z) return { __v3 = true, X = x or 0, Y = y or 0, Z = z or 0 } end
Vector3.zero = Vector3.new(0, 0, 0)
Vector3.one = Vector3.new(1, 1, 1)

-- Enum values only need to be distinct and comparable here.
local Enum = setmetatable({}, { __index = function(t, category)
	local c = setmetatable({}, { __index = function(_, name)
		return { __enum = true, Category = category, Name = name }
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

    out.append("\n-- === test cases ===\n")
    out.append((ROOT / "tests/cases.luau").read_text())

    target = ROOT / "tests/generated_suite.luau"
    target.write_text("".join(out))
    print(f"wrote {target.relative_to(ROOT)} ({len(''.join(out))} bytes, {len(PURE_MODULES)} modules, {len(world_defs)} worlds)")

if __name__ == "__main__":
    sys.exit(main())
