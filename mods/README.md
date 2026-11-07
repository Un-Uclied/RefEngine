# RefEngine mods

Create `mods/<mod_id>/assets/` with the same folders as the built-in `assets/` directory.
Only files that differ need to be copied. Missing files fall back to the built-in assets.

For a song called `track` in a mod called `demo`, use this layout:

```text
mods/demo/assets/
  songs/track/data.json
  songs/track/Inst.ogg
  songs/track/Voices.ogg
  ui/notes/my_note/data.json
  ui/notes/my_note/left.png
  characters/my_character/data.json
```

Start it with `python run.py demo:track`. Without an argument, the built-in `singularity` song starts.
The song chart keeps the existing JSON format. Refer to files by logical paths such as
`assets/songs/track/Inst.ogg` or `assets/ui/notes/my_note/left.png`. These resolve in the
selected mod first, then in the built-in `assets/` folder. Song and mod IDs must be single
folder names. Put a note type's complete `data.json` under `ui/notes/<type>/` and use that
type as the fourth value in a chart note. `penalty_note` is the supported setting name.
The older `penaly_note` spelling remains readable for existing content.

Game signals are defined in `sources/game/events.py`. Connect a receiver that accepts
`(sender, **event_values)` and disconnect it when its view closes. Beat events carry `beat`
and `ms`. Player note presses carry `direction_index` and `note`, releases carry
`direction_index`, and misses carry `note`. Score changes carry `score` and `accuracy`.
