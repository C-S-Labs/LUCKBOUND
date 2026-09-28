# Developer tools — commands and the dev panel

Testing tooling, not a feature. On only while `GameConfig.Debug.AllowCommands` is true, and only for
**Studio or the place's creator** — the panel is never built for anyone else, and every server
command is permission-checked again by `Systems/DebugSystem`. Turn `AllowCommands` off before the
place goes public.

## Using it

- **Panel:** press **F4** (`GameConfig.Debug.PanelKey`), click the **DEV** button top-right, or type `/panel`. Drag the header to move it, and drag the
  **gold ridged grip in the bottom-right corner** to resize it (minimum `GameConfig.Debug.PanelMinWidth/Height`).
  - **Category tabs** down the left: World & Map, Chunks, Player, Fate & Loot, Events, Ambience,
    Bosses, Diagnostics, General.
  - **A card per command.** Click an argument's picker to choose from its live values (world ids,
    events, atmospheres, bosses, keys, the chunks of the map you are on…). Number arguments
    offer quick values. **Presets** run in one click. **Run** sends it.
  - **Command bar** (top): autocompletes command names *and* argument values. Click a suggestion
    or press **Tab**; **Up/Down** walk the suggestions, or your history when there are none;
    **Enter** runs.
  - **Output log** (bottom): every reply, client and server; failures in red.
  - Drag the header to move the window.
- **Chat:** every command is also a slash command. Roblox's chat autocompletes the command
  *names*. Its input bar can't be extended with argument suggestions, so for those use the panel's
  command bar.

## Commands

| Tab | Commands |
|---|---|
| World & Map | `/roll <world> [test]`, `/enter [seed]`, `/leave`, `/seed`, `/worlds` |
| Chunks | `/chunks [on/off]` (bounds + labels; red = blockout), `/chunklist`, `/chunktp <chunk>` |
| Player | `/fly`, `/noclip`, `/speed [n]`, `/tp <place>`, `/where`, `/god`, `/heal`, `/respawn` |
| Fate & Loot | `/boss`, `/givekey [key]`, `/takekey`, `/keys`, `/keychance`, `/vaultchance`, `/ledger` |
| Events | `/event <id>`, `/endevents` |
| Ambience | `/atmosphere <id>`, `/tint`, `/props on/off`, `/clock <hour>` |
| Bosses | `/showboss <boss> [height]`, `/bossphase <1/2>`, `/clearboss` |
| Diagnostics | `/stats [on/off]` (FPS, ping, memory, instances), `/assets` (which chunks drew as blockout) |
| General | `/panel`, `/help`, `/clear` |

## Adding a command

1. **One entry** in `src/shared/Content/DevCommands.luau`: `Name`, `Category`, `Side`, `Summary`,
   optional `Args` and `Presets`. A new category is one line in `Categories`.
   - `Side = "CLIENT"` for what the client already owns (its movement, camera, what it draws);
     `"SERVER"` for anything a client must not be trusted with (rolls, entry, loot, health).
   - Argument `Type`: `choice` (with literal `Options`, or a `Source` — see `DevCore.SOURCES`),
     `number` (optional `Min`/`Max`/`Suggest`), or `text`. Optional arguments come last.
2. **Its handler:** a function in `DebugCommands.CLIENT` (client), or in `COMMANDS` in
   `Systems/DebugSystem.luau` (server), returning `(ok, message)` on the server.
3. That's all: chat registration, the panel card, autocomplete and the pickers come from the entry.
   A new live list (a new `Source`) is one name in `DevCore.SOURCES` plus one function in
   `DebugCommands`' `SOURCES`.

The tests (`tests/cases.luau`, "dev registry") fail on a malformed entry, a duplicate name, an
unknown category or source, an empty tab, or a required argument after an optional one. At boot, the client and
server each warn about any entry with no handler (and the server about any handler with no entry).

## Where it lives

- `src/shared/Content/DevCommands.luau` — the registry (data only)
- `src/shared/Core/DevCore.luau` — parse, validate, autocomplete (pure; tested headless)
- `src/client/Controllers/DebugCommands.luau` — client handlers, argument sources, chat registration, `run()`
- `src/client/UI/DevPanel.luau` — the panel (UIKit / UITheme only, like every other screen)
- `src/server/Systems/DebugSystem.luau` — server handlers and the permission gate
- `UIKit.textbox` — the themed text field the panel uses, available to every screen
