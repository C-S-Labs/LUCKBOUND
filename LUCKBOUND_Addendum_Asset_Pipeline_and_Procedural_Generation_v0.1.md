# LUCKBOUND — Addendum: Asset Pipeline & Procedural Generation Architecture
**Version 0.1 (Draft) — Future Development Reference**
**Status: Not in active scope.** Current build phase is a pure skeleton focused on gameplay loop functionality (roll → enter → fight → discover → return → roll again). No model/asset generation work begins from this point forward until the loop is proven. This addendum exists so the target architecture is documented and doesn't need to be re-derived later.

---

## A1. Model & Asset Import Pipeline

Roblox does not load raw mesh files (.fbx/.obj/.blend) at runtime. All MeshParts reference a `MeshId` pointing to a mesh already uploaded to Roblox's asset servers — there is no way to skip this step, regardless of tooling.

**Pipeline:**
1. **Generate/author the model.** ChatGPT does not output mesh data directly — it can generate `bpy` (Blender Python) scripts to procedurally build geometry, or assist with materials/rigging/shaders. Organic/freeform meshes are authored directly in Blender or via a dedicated AI mesh-gen tool, then cleaned up in Blender.
2. **Export from Blender** as FBX.
3. **Upload to Roblox** to obtain an asset ID — via Studio's Bulk Import / Avatar Importer (manual), or the Open Cloud Assets API (scriptable, for a more automated pipeline at scale).
4. **Reference the asset ID** from the Rojo-synced project, via one of:
   - A baked `.rbxm`/`.rbxmx` binary model file checked into the Rojo tree (synced via `$path` in `default.project.json`), or
   - A manifest (JSON/Luau module) of asset IDs that code reads to construct `MeshPart` instances at runtime — fits the existing "Content is data" principle (Section 18 of the master spec).

The mesh geometry itself always ends up hosted on Roblox's CDN, referenced by ID. Rojo/Luau code only ever orchestrates placement and logic, never the binary mesh data.

**Important distinction:** Rojo only operates at dev-time, syncing the filesystem into Studio while editing. Once published, Rojo is no longer running — everything is either baked into the place file or is Luau code executing live on the server. "Generation via Rojo" in practice means Rojo delivers the Luau systems; the systems generate things live.

## A2. Asset Storage Location

- **`ServerStorage`** — primary home for the prefab library (enemies, bosses, items, discoveries, world chunks). Invisible to clients, preventing exploiters from inspecting the client to dump the full discovery/loot/enemy roster ahead of time. Synced here from disk via Rojo, mapped from `Content/Worlds/`, `Content/Enemies/`, `Content/Items/`, etc.
- **`ReplicatedStorage`** — reserved for the exception cases: assets the client genuinely needs pre-placed or predicted client-side.
- **`Workspace`** — live, rendered, replicated scene only. World instances are cloned into Workspace from ServerStorage at expedition start and torn down (folder `:Destroy()`, Terrain region cleared) at expedition end/return, rather than persisting.

## A3. Terrain Strategy

**Decision: native Roblox voxel Terrain for macro landscape, authored MeshParts for anything that needs to read as a designed object** (bosses, enemies, weapons, discoveries, landmarks, the Fate Engine).

Rationale:
- Terrain is scriptable (`Terrain:FillRegion`, `WriteVoxels`), has built-in collision, and skips the asset-upload round trip entirely.
- Given expeditions are temporary (12-minute) instances rolled repeatedly, cheap generate/destroy of terrain per instance is a meaningful advantage over pre-baked mesh landscapes.
- Voxel terrain is cheaper at scale than unique high-poly meshes for macro shapes like hillsides.

## A4. Procedural Variation — Target Design (Post-Skeleton)

Goal: avoid a stale, identical, infinitely-repeating loop — vary terrain, mobs, and encounters per playthrough — while bounding exploit surface and asset cost.

**Low-risk, straightforward (do first once past skeleton phase):**
- **Mob pool selection**: weighted RNG roll per spawn point from each world's existing enemy roster, instead of fixed spawns. Reuses `LootSystem`-style weighted RNG already planned for loot.
- **Loot/encounter variance**: already implied by the spec's existing World Modifiers (Night, Eclipse, Corrupted, Invasion, Boss Rush, etc.) — different enemy density/type/loot tables per run with no new architecture required.
- **Per-expedition seeding**: generate a server-side seed (e.g. time + UserId + roll index) and feed it into all RNG for that instance. Enables deterministic replay for debugging and exploit investigation.

**Higher-risk — explicitly deferred, not recommended for early builds:**
- **Freeform noise-generated terrain** (Perlin/Simplex carving unique landscape per run) risks: traversal failures (boss/loot unreachable or buried, requiring an automated pathfinding validation pass before letting players in), exploit surface (voxel micro-gaps enabling clipping/skip-combat), and performance variance on mobile/console targets.
- Recommendation: hold off on raw procedural terrain generation until well past prototype, once the core loop is validated as fun.

**Recommended middle path — procedural *composition*, not procedural *terrain*:**
1. Hand-author a kit of modular terrain chunks/rooms/landmarks per world (~15–25 to start), each pre-validated for traversability, collision, and no exploit gaps.
2. Per expedition, seed-select and arrange a subset of chunks along a graph (linear, branching, or hub-and-spoke) sized to the expedition duration.
3. Populate the assembled layout using the weighted mob/loot pools from A4 above.
4. Run one automated spawn→boss pathfinding validation pass server-side before allowing entry.

This extends the same combinatorial philosophy already in the master spec (Section 14: `BASE × ELEMENT × RARITY × MUTATION × WORLD`) from items to level layout — combinatorial variety from a bounded, authored chunk library rather than unbounded generation.

## A5. Sequencing Note

This entire addendum is intentionally out of scope until the gameplay loop skeleton (roll → enter → fight → discover → return → roll again) is proven fun with placeholder/primitive geometry. No asset generation, Blender work, or terrain-chunk authoring begins before that milestone.
