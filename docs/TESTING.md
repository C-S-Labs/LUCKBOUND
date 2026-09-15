# LUCKBOUND — Testing Guide

Two layers: automated tests that run headlessly (no Studio), and a manual Studio
pass for the things only a running game can tell you.

---

## 1. Automated tests — run these first

83 tests, no Roblox required. They run against the real `src/` modules, not copies.

```bash
# one-time: get the Luau CLI from https://github.com/luau-lang/luau/releases
./tests/run.sh
```

Expected tail:

```
============================================================
83 passed, 0 failed, 83 total
```

They also run in CI on every push (`.github/workflows/ci.yml`).

### What they cover

| Group | Tests | The question it answers |
|---|---|---|
| Schema validation | 8 | Does the server refuse to boot on broken content? |
| Scripted onboarding | 8 | Are rolls 1–3 always forced, and do they survive a rejoin? |
| **True RNG** | 12 | **Is the roll genuinely unweighted by player state?** |
| WeightedRandom | 6 | Edge cases: zero weights, boundaries, single entry |
| Fate progression | 11 | Is the level curve monotonic and invertible? |
| Profile & migration | 11 | Does data survive, migrate, and stay in DataStore limits? |
| **Late-joiner visibility** | 21 | **Does someone joining mid-event see the right thing?** |
| Constants | 6 | Frozen, unique orders, sane reveal durations |

### The two that matter most to your direction

**True RNG is proven, not asserted.** 400,000 draws against the configured weights:

```
EMBERFALL        expected  20.00%  observed  20.10%  drift 0.097pp
VERDANT_VALLEY   expected  75.00%  observed  74.89%  drift 0.108pp
ASTRAL_REACH     expected   5.00%  observed   5.01%  drift 0.011pp
```

And the guarantee itself — a level-90 veteran and a level-1 newcomer, fed the
same random stream, produce **identical results across 50,000 rolls**. If anyone
ever adds a Fate term to the weighting, that test goes red immediately.

**Late joiners.** A player joining 4 minutes into a 5-minute Fatebreak gets
`RemainingSeconds = 60`, the triggering player's name, and elapsed time for
animation sync. Expired events vanish; stale announcements age out at 5 minutes.

---

## 2. Push to Studio with Rojo

```bash
# once
rokit install          # installs rojo 7.6.0, stylua, selene from rokit.toml
rojo plugin install    # installs the Studio plugin

# every session
rojo serve
```

Then in Studio: open a **new baseplate**, find **Rojo** in the Plugins tab,
click **Connect**. You should see `ReplicatedStorage.Luckbound`,
`ServerScriptService.LuckboundServer` and
`StarterPlayer.StarterPlayerScripts.LuckboundClient` appear.

**Before you press Play**, enable API access or DataStores will silently fail:
**Game Settings → Security → Enable Studio Access to API Services**.

There is no client code yet (T-114–T-117), so `LuckboundClient` will be empty.
That's expected — Phase 1 server logic is what you're testing here.

---

## 3. Manual Studio pass

### Test A — the server boots (2 min)

Press **Play**. Output should contain:

```
[LUCKBOUND] server ready -- phase 1, true RNG, 3-roll onboarding
[SaveSystem] created new profile for <you>
```

✅ Pass: no red errors.
❌ If you see `LUCKBOUND content validation failed:` — that's working as designed.
It names the exact field. Fix the content and reconnect.

### Test B — content validation actually blocks a bad boot (2 min)

Break something on purpose. In `src/shared/Content/Worlds/Emberfall.luau`,
change `Rarity = "RARE"` to `Rarity = "SUPER_RARE"`, save.

✅ Pass: the server **refuses to start** and Output names the field.
Revert it. This is the check that stops a broken prototype from booting silently.

### Test C — the roll works and onboarding is scripted (5 min)

There's no UI yet, so drive it from the **Server** console (View → Command Bar,
set to Server):

```lua
local Net = require(game.ReplicatedStorage.Luckbound.Core.Net)
Net.get("Fate_RequestRoll"):FireServer()  -- run this from the CLIENT console
```

Easier: from the **Client** command bar, run that line four times, waiting
~3 seconds between each (the cooldown). Watch the **Server** output:

```
[Roll] YourName (123) -> VERDANT_VALLEY [COMMON] (onboarding)
[Roll] YourName (123) -> EMBERFALL [RARE] (onboarding)
[Roll] YourName (123) -> ASTRAL_REACH [MYTHIC] (onboarding)
[Roll] YourName (123) -> VERDANT_VALLEY [COMMON]
```

✅ Pass: first three are exactly that order and marked `(onboarding)`.
The fourth has no marker — that's true RNG taking over.

### Test D — the cooldown holds (1 min)

Spam the roll line ten times fast from the client console.

✅ Pass: at most one roll appears in the server log per 3 seconds, and **no error
is sent back to the client**. Silence is deliberate — an error message tells an
exploiter exactly where the boundary is.

### Test E — a tampered client is rejected (1 min)

From the **client** console:

```lua
local Net = require(game.ReplicatedStorage.Luckbound.Core.Net)
Net.get("Fate_RequestRoll"):FireServer({ WorldId = "ASTRAL_REACH" })
```

✅ Pass: server logs `sent arguments with Fate_RequestRoll; discarded` and **no
roll happens**. The client cannot choose its own destination.

### Test F — data persists (3 min)

Roll 3–4 times. Note `TotalRolls`. **Stop**, then **Play** again.

```lua
-- server console
local S = require(game.ServerScriptService.LuckboundServer.Systems.SaveSystem)
print(S.get(game.Players:GetPlayers()[1]).TotalRolls)
```

✅ Pass: the count carried over, and onboarding resumes where it left off
(if you'd done 2 rolls, roll 3 is still Astral Reach).
❌ If it reset: API Services is off (see above).

### Test G — late joiners see a live event ⭐ (5 min)

**This is the one you asked about.** Needs two clients:
**Test → Clients and Servers → 2 players → Start**.

1. In the **server** console, start a Fatebreak:

```lua
local E = require(game.ServerScriptService.LuckboundServer.Systems.EventSystem)
E.triggerFatebreak({ Id = "STARFALL_1", Name = "The Eternal Star",
	Rarity = "UNKNOWN", TriggeredBy = "Player1", Duration = 300 })
```

2. Confirm both existing clients received `Announce_Global`.
3. **Now have a third player join mid-event** (Test → Start Player).
4. In that new player's **client** console:

```lua
local Net = require(game.ReplicatedStorage.Luckbound.Core.Net)
Net.get("Event_StateSync").OnClientEvent:Connect(print)
```

Or check server-side that the snapshot is correct:

```lua
local EventCore = require(game.ReplicatedStorage.Luckbound.Core.EventCore)
local E = require(game.ServerScriptService.LuckboundServer.Systems.EventSystem)
local GameConfig = require(game.ReplicatedStorage.Luckbound.Core.GameConfig)
print(EventCore.snapshot(E._state(), os.time(), GameConfig))
```

✅ Pass: the snapshot shows the event still active with a correct
`RemainingSeconds` countdown — **not** the full 300. The late joiner sees the
same Starfall, at the same point in its life, as everyone who was there when it
started.

5. Wait for it to expire (or set `Duration = 15`). A player joining *after*
expiry must see `ActiveEvents = {}` — no ghost event.

> Cross-server Fatebreaks use `MessagingService`, which does not work in Studio.
> You'll see `cross-server subscribe failed (expected in Studio...)` in Output —
> that's normal. Testing it needs a published place with 2+ servers.

### Test H — announcements reach everyone, onboarding doesn't (2 min)

With two clients connected, have Player 1 roll past onboarding until they hit
Astral Reach naturally (or temporarily set `PrototypeWeights.ASTRAL_REACH` high).

✅ Pass: **both** clients receive `Announce_Global`.
✅ Pass: a fresh player's *scripted* Astral Reach roll (roll 3) produces **no**
announcement. Otherwise every new player would spam a Mythic banner.

---

## 4. What to report back

The automated suite covers correctness. What it cannot tell us is the only
question that matters (Master Spec §25):

**After Test C, did you want to roll again?**

Specifically worth noting as you run through:
- Is 3 seconds of roll cooldown too long, or invisible?
- Does seeing Astral Reach on roll 3 make roll 4 feel exciting or like a letdown?
- Is 100 seconds right for an onboarding expedition, or still too long?

Those three answers drive the next round of tuning more than any test result.
