# LUCKBOUND — Toolchain & AI Access Setup

How to give an AI agent real hands on Roblox Studio, Blender, and asset pipelines.

---

## 0. The one thing to understand first

There are **two different places Claude can run**, and they have very different powers.

| | **This cloud session** (claude.ai/code) | **Claude Code on your own machine** |
|---|---|---|
| Write Luau, data, docs, tests | ✅ | ✅ |
| Run the headless test suite | ✅ | ✅ |
| Git / GitHub | ✅ | ✅ |
| Open Roblox Studio | ❌ | ✅ via Studio MCP |
| Run the game & watch it | ❌ | ✅ via Studio MCP playtest tools |
| Take screenshots of the game | ❌ | ✅ |
| Read Studio's console output | ❌ | ✅ |
| Drive Blender | ❌ | ✅ via Blender MCP |
| Insert Creator Store models | ❌ | ✅ |

The cloud session is sandboxed with no route to your desktop. **Anything that touches Studio or Blender has to run from Claude Code installed locally.** The repo is the handoff point between the two: I write code here and push, you pull locally and the local agent syncs it into Studio.

> **This corrects what I told you in my first answer.** I said I couldn't playtest or see whether combat feels good. That is true of *this* session, but it is not true of Claude Code running on your machine with the Studio MCP connected — that setup can enter play mode, simulate input, capture the screen, and read console output. The "can't test it" limit is much narrower than I first described. What remains genuinely yours is the judgement call: whether what it captures is *fun*.

---

## 1. Roblox Studio access — the built-in MCP server

Roblox ships an MCP server **inside Studio itself**. This is now the supported path; the older standalone `Roblox/studio-rust-mcp-server` repo is explicitly no longer actively developed and its README points here.

### Setup (about 3 minutes)

1. Update Roblox Studio to the current version.
2. In Studio, open **Assistant**.
3. Click the **…** menu → **Manage MCP Servers**.
4. Turn on **Enable Studio as MCP server**.
5. Expand **Quick connect** and enable **Claude Code** from the list of detected clients.
6. If Claude Code isn't listed: install it, then restart Studio.

A green indicator shows the number of connected clients. Verify from the Claude Code side with `/mcp`.

### What it gives the agent (25+ tools, eight categories)

- **Scripts** — read, edit, search and grep across every script in the place
- **Asset generation** — generate meshes, materials and procedural models; search and insert Creator Store assets
- **Data model** — walk the instance hierarchy, inspect any object's properties
- **Luau execution** — run code inside Studio contexts
- **Playtesting** — start/stop play mode, capture the screen, pull console output
- **Input simulation** — move the character, send keyboard and mouse input
- **Documentation** — Roblox API reference lookup
- **Session management** — list connected Studio instances

For LUCKBOUND specifically this means an agent can: build the Crossroads blockout by running geometry code, enter play mode, walk the character to the Fate Engine, press the roll key, screenshot the reveal, read any errors, and iterate — without you touching the mouse.

### ⚠️ Security

Roblox's own warning, and it is the real one: *MCP clients can read and modify content in your open Roblox places. Only connect clients you trust.*

Practical rules:
- Keep Studio open on a **scratch place** while an agent is working, never your published production place.
- The agent can run arbitrary Luau in Studio. Treat "let the agent drive Studio" as equivalent to giving it a shell.
- Turn the toggle **off** when you are not actively running an agent session.

---

## 2. Code sync — Rojo

The Studio MCP can edit scripts directly, but you do not want it to be the only path: Studio-side edits don't reach git, and the whole anti-`CombatSystem_Final2` discipline in §18 depends on the repo being the source of truth.

**Division of labour:**
- **Rojo** owns everything under `src/` — all Systems, Content, UI logic. Repo → Studio, one direction.
- **Studio MCP** owns Workspace geometry, playtesting, asset insertion, and inspection.
- An agent that wants to change a System edits the file and lets Rojo sync it. It does **not** edit the script in Studio.

### Setup (Windows / PowerShell — verified working)

```powershell
Invoke-RestMethod https://raw.githubusercontent.com/rojo-rbx/rokit/main/scripts/install.ps1 | Invoke-Expression
```

**Then close PowerShell and open a new window.** The installer edits PATH, and an
already-open shell will not see it. This is the single most common "command not
found right after installing" cause. A terminal inside VS Code inherits the old
PATH too — restart the whole app, not just the tab.

```powershell
rokit --version        # confirm it is on PATH
cd C:\Dev\luckbound
rokit install          # reads rokit.toml: rojo 7.7.0 + stylua + selene
rojo serve
```

Expect a **trust prompt** on first install — Rokit asks before running each tool.
Say yes to all three; it remembers per tool. If it errors instead of prompting:

```powershell
rokit trust rojo-rbx/rojo
rokit trust JohnnyMorganz/StyLua
rokit trust Kampfkarren/selene
```

In Studio: **Rojo** panel → **Connect** → **Accept** the sync preview (Rojo 7.7+
asks before touching the place). Then edit a file → save → it appears instantly.

#### If the installer fails silently

PowerShell 5.1 defaults to old TLS, and `Invoke-RestMethod | Invoke-Expression`
produces **no error** when the download fails — it just executes nothing. Force
TLS 1.2 and retry:

```powershell
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
```

Diagnose with `Test-Path "$HOME\.rokit\bin\rokit.exe"` — `False` means the
install never happened; `True` means it is only a PATH problem.

#### Escape hatch

Rokit is only a version manager, and StyLua/Selene are linters CI already runs.
**The one tool you actually need is Rojo.** Download `rojo-win64.zip` from the
[Rojo 7.7.0 release](https://github.com/rojo-rbx/rojo/releases/tag/v7.7.0), drop
`rojo.exe` in the repo folder, and run `.\rojo.exe serve` (the `.\` is required
in PowerShell).

### Two gotchas that cost real time

**Rojo does not clean up.** It manages only the three paths in
`default.project.json`. Old scripts elsewhere in the place keep running
alongside the new ones — two architectures at once. Converting an existing place
means deleting the old scripts by hand first.

**Read-only properties break the sync.** `Workspace.FilteringEnabled` is
permanently true in modern Roblox; a project file that tries to set it makes Rojo
error mid-apply and can leave the tree half-built with no scripts running.
Keep `$properties` out of the project file unless genuinely needed.

### Keep the code off OneDrive

The repo must live outside OneDrive (`C:\Dev\luckbound` is fine). The `.rbxl`
place file on OneDrive is harmless — only the synced source matters.

---

## 3. Blender access — Blender MCP

For anything beyond blockout geometry — the Fate Engine itself, bosses, Discovery objects.

### Setup

```bash
claude mcp add blender -- uvx blender-mcp
```

Then in Blender:
1. Download `addon.py` from the [blender-mcp repo](https://github.com/ahujasid/blender-mcp).
2. **Edit → Preferences → Add-ons → Install…** → select `addon.py`.
3. Tick **Interface: Blender MCP**.
4. In the 3D viewport press **N** → open the **BlenderMCP** tab → start the connection.

There is also a Blender connector available through Claude's connector directory if you prefer not to manage the MCP config by hand.

### Honest expectations

Blender MCP is genuinely good at: procedural and parametric geometry, scene assembly, batch operations, materials, modifier stacks, running Python against the scene.

It is weak at: character modelling, topology that has to deform well, sculpting, anything where the goal is "make this look beautiful". An agent driving Blender produces *serviceable* assets fast. It does not replace an artist for hero assets, and the Fate Engine is a hero asset — it's on screen for the entire game.

**Recommended split for LUCKBOUND:** Blender MCP for environment kit-bash pieces (rocks, pillars, runes, crystals, floating island chunks) where volume matters and each piece is background. Commission or buy the Fate Engine.

---

## 4. Asset sources, ranked by effort

1. **Roblox Creator Store** — free and paid models, insertable directly by the agent via the MCP `insert_model` tool. Fastest path to a non-embarrassing prototype. Check licences before publishing.
2. **Roblox's built-in generative asset tools** — mesh, material and procedural model generation, exposed through the Studio MCP's asset-generation category. Good for materials and simple props.
3. **Blender MCP** — as above, for kit pieces.
4. **Paid marketplaces** — Sketchfab, Kitbash3D, Quixel. Export FBX/OBJ → import to Studio. Verify the licence permits Roblox publishing.
5. **Audio** — Roblox's audio library, or Suno/ElevenLabs for original music and SFX. Note Roblox's audio privacy rules: uploaded audio over 6 seconds is private to your experience by default.

For Phase 1 you need exactly one sound: the roll SFX. Do not build an audio pipeline yet.

---

## 5. Publishing & CI (optional, later)

Roblox **Open Cloud API** allows programmatic place publishing with an API key. That means a GitHub Action can build the place with `rojo build` and publish it — an agent *can* own the deploy step, unlike Studio work.

Worth setting up once you have real testers and are shipping more than once a day. Not worth it for Phase 1.

For automated tests, `run-in-roblox` executes a test suite in a headless Roblox instance from CI. Pair with Jest-Lua or TestEZ. The WeightedRandom distribution test (T-106) is the first thing worth running this way.

---

## 5.1 Publishing — now a real blocker, not optional polish

Two Phase 1 acceptance criteria (P1-8, P1-9) **cannot be verified on a local
place**, because `DataStoreService` raises there. `MessagingService` — which
cross-server Fatebreaks depend on — is unavailable for the same reason.

The server handles both gracefully: `SaveSystem` runs in volatile mode and says
so, and the cross-server subscribe runs off-thread so it cannot stall the
bootstrap. But **saving and cross-server events stay untestable until the place
is published** and Studio Access to API Services is enabled.

Worth doing when you next want to confirm persistence.

## 6. Recommended setup order

| Step | Time | Unlocks |
|---|---|---|
| 1. Install Claude Code locally | 5 min | Everything below |
| 2. Enable Studio built-in MCP + Quick connect | 3 min | Agent can build, playtest, screenshot |
| 3. `rokit install` + `rojo serve` + plugin | 10 min | Repo ↔ Studio code sync |
| 4. Clone this repo locally, `rojo build` | 2 min | Phase 1 scaffold opens in Studio |
| 5. Publish the place | 10 min | Unblocks DataStores and MessagingService (P1-8, P1-9) |
| 6. Blender MCP | 15 min | Defer until Phase 3 — you don't need art yet |
| 7. Open Cloud + CI | 1 hr | Defer until you have testers |

**Steps 1–4 are the whole critical path.** Under 25 minutes and the local agent can build Phase 1 against this spec, run it, and show you a screenshot of the reveal.

---

## Sources

- [Roblox Studio MCP documentation (creator-docs)](https://github.com/Roblox/creator-docs/blob/main/content/en-us/studio/mcp.md) · [Creator Hub page](https://create.roblox.com/docs/studio/mcp)
- [Roblox/studio-rust-mcp-server](https://github.com/Roblox/studio-rust-mcp-server) — legacy standalone server, no longer actively developed
- [Assistant Updates: Studio Built-in MCP Server and Playtest Automation](https://devforum.roblox.com/t/assistant-updates-studio-built-in-mcp-server-and-playtest-automation/4474643)
- [Rojo releases](https://github.com/rojo-rbx/rojo/releases) · [Rojo installation docs](https://rojo.space/docs/v7/getting-started/installation/) · [Rokit](https://github.com/rojo-rbx/rokit)
- [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) · [Blender connector tutorial](https://academy.claude.com/tutorials/using-the-blender-connector-in-claude)
