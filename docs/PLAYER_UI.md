# LUCKBOUND — Player UI

**Owns:** the loading screen, the hub menu (rail + panels), the shared widget
kit, and the rules about when any of it is on screen.
**Does not own:** the roll (`UI/FateRoll`), the expedition banner
(`UI/ExpeditionHud`), global announcements. Those predate this document and
are unchanged by it.

---

## 1. The shape of it

```
src/shared/Core/UITheme.luau        colours, spacing, radii, motion   (design tokens)
src/shared/Core/HubMenuCore.luau    panel/travel RULES                (pure, tested)
src/shared/Core/SettingsCore.luau   settings schema + validation      (pure, tested)
src/shared/Content/Hub/Menu.luau    which panels and destinations EXIST
src/shared/Content/Hub/Cinematics.luau  the loading screen's camera shots
src/client/UI/UIKit.luau            buttons, toggles, sliders, tweens (widgets)
src/client/UI/HubMenu.luau          the rail and the panels           (pixels only)
src/client/UI/LoadingScreen.luau    title, camera tour, PLAY
src/server/Systems/HubUISystem.luau travel, codes, settings           (authority)
```

The split is the same one the rest of the project runs on. **Adding a panel is
a row in `Content/Hub/Menu`.** Adding a travel destination is a row in the same
file. Neither touches the rail, the panel builder or the server.

If a new panel seems to need a change to `HubMenu.luau` beyond a body builder,
the schema is wrong — say so and amend it rather than special-casing.

---

## 2. The loading screen

Owner-directed. Its purpose is half technical: the hub is hundreds of instances
of authored art, and until they replicate the player is standing in a
half-built world with no explanation.

| | |
|---|---|
| Camera | `Scriptable`, flying a slow arc per shot from `Content/Hub/Cinematics` |
| Backdrop | the live hub, blurred (`GameConfig.Loading.BlurSize`) with a vignette over it |
| Progress | the **slower** of "instances arrived" and "minimum time elapsed" |
| PLAY | lights at `MinimumSeconds` **and** readiness — or at `MaximumSeconds` regardless |
| Buttons | **PLAY, and nothing else.** Owner-directed: an EXIT that can only kick you back to the app's home screen is a button whose best outcome is leaving. If anything ever joins it, it should be something a player arrives *wanting* |

**Two rules it keeps.** It never traps a player — every wait is bounded, and a
stalled client is let in with an apology rather than held. And it restores
everything it took: camera type, field of view, blur, and the character's
WalkSpeed and JumpPower. That last one is why `LocomotionController` is
started *by* the loading screen finishing, rather than at client boot — it
writes WalkSpeed every frame and would otherwise simply undo the hold.

**Why the shots are all hub shots.** An expedition map is built 20000 studs up
and only while somebody is inside one, so a shot of Ethereal Scape today would
be a shot of empty sky. `WorldId` exists on the shot schema and the client
skips any shot whose world is not loaded, so biome shots can be added the day
expeditions move to their own place — a shot added early degrades to being
absent, never to a black screen. A test pins that every shipped shot is a hub
shot.

---

## 3. The hub menu

### It is only in the Crossroads

One function: `HubMenuCore.isVisible(expedition, config)` — `nil` expedition
means "in the hub". The client uses it to show the GUI; the server uses the
same module to refuse travel from an expedition. Owner-directed, and the
reason is that an expedition is meant to be the game rather than a screen with
the game behind it.

It also hides during a roll (`GameConfig.HubMenu.HideDuringRoll`), because the
reveal is the four seconds the whole game rests on and must not be framed by a
side rail.

### The arrow

The collapse arrow is the one thing a collapse leaves on screen. Collapsing
slides the **whole rail off the left edge** — not down to a strip of glyphs,
because a rail shrunk to icons is still a rail on the screen and the ask was
for the screen back. Collapsing also closes any open panel, for the same
reason.

Starts collapsed on touch, open on desktop. A player's own `AutoHideMenu`
setting overrides both, applied **once** when their profile arrives.

### The panels

| Panel | Status | What it does today |
|---|---|---|
| Travel | **LIVE** | Five destinations, server-validated, **no cooldown** — press, a ~0.5s fade, arrive |
| Codes | **LIVE** | A text box; the server decides and the answer is what the player reads |
| Settings | **LIVE** | Drawn from `SettingsCore.SPEC`; saved to the profile |
| Shop | PREVIEW | Designed screen, placeholder copy, labelled |
| Fate Tree | PREVIEW | ditto — see `PLAYER_ABILITIES.md` §3 for the branch design |
| Party | PREVIEW | ditto |
| Rebirth | PREVIEW | ditto, with prestige inside it rather than beside it |

**PREVIEW is an honest label, not a placeholder.** The owner's direction is
that these are designed now and implemented after testing, so they draw their
real design over placeholder data and say so on a badge. A button that
silently does nothing would be worse than no button.

### Travel, precisely

1. Client sends `{ DestinationId }` — and nothing else, ever.
2. `HubMenuCore.canTravel` decides: known Id, not on an expedition, not
   mid-roll. The **client calls the same function** to grey its own buttons
   out, which is a courtesy and never the authority. **There is no cooldown**
   (owner-directed) — the server's 60/min rate limit is a spam guard, and the
   client must never grey a button out for it.
3. The server resolves the Id to `Anchors[AnchorId] + Landing`, drops a ray
   from `TeleportProbeHeight` above it, and stands the player on what it hits.
   Nothing hit → the content point is used and the server warns by name.
4. The character is moved with `PivotTo` and turned to the destination's
   `Facing` bearing, so nobody arrives with their back to the district.

**Why the ray.** The authored districts' deck heights are a property of a mesh
nothing in code can measure — the same problem the mountain ring ran into. The
content point is a guess at X/Z; the ray decides Y.

---

## 4. The design system

Everything visual comes from `UITheme`: three surface depths, one spacing
scale, two radii, and a `Motion` table of durations and easings. **A literal
in a UI module is the same violation as a magic number in a System** — it is
just harder to spot, because a slightly-wrong purple does not throw.

`UIKit` is the only place a tween is created, which is what makes the
**Reduce Motion** setting real: it collapses every duration to 0.05s in one
function. A tween built directly with `TweenService` would quietly opt that
player back in. Reduce Motion does **not** shorten the roll reveal — that is
the game, not the chrome.

Panels come in on Quint/Out and leave on Quad/In. Using one easing for both
directions is what makes a menu feel rubbery.

---

## 5. Known gaps

| Item | Severity | Notes |
|---|---|---|
| **None of this has been seen in Studio** | **Open** | Every number below is reasoned, not observed. First-walk priorities are in `TESTING.md` |
| Rail position on a phone in portrait | Medium | The rail is left-anchored and centred; on a tall narrow screen it may want to be a bottom bar instead. Judge it on a device |
| The loading screen's instance target | Medium | `RequiredHubInstances = 380` against a hub that built 436. If the authored hub's count changes, this wants changing with it — it is asserted to stay under 436 by test, not to be correct |
| Shop / Tree / Party / Rebirth are copy | Expected | Deliberate. They ship designed and labelled |
| No sound | Low | Every one of these beats wants a sound: the rail opening, PLAY, a code accepted. There is no audio system yet |
| Settings do not drive anything yet | Medium | `ReduceMotion` and `AutoHideMenu` do. `MusicVolume`, `SfxVolume`, `UiScale`, `ScreenShake` and `ShowGlobalAnnouncements` are stored and honoured by nothing, because the systems they would drive do not exist |
| The travel fade is open-loop | Low | The client fades out, *then* sends the request. If the server refuses mid-fade, the player gets a brief black screen and a refusal rather than no fade at all. The fade is ~0.5s end to end, so the cost of being wrong is small |
