# RefEngine mods

Create `mods/<mod_id>/assets/` with the same folders as the built-in `assets/` directory.
Only files that differ need to be copied. Missing files fall back to the built-in assets.

For a song called `track` in a mod called `demo`, use this layout:

```text
mods/demo/assets/
  songs/track/data.json
  songs/track/Inst.ogg
  songs/track/Voices.ogg
  notes/my_note/data.json
  notes/my_note/left.png
  scripts/notes/my_effect.py
  characters/my_character/data.json
```

Open the menu with `python run.py demo:track` to preselect that song. Without an argument,
the menu opens with the first song selected.
The song chart keeps the existing JSON format. Refer to files by logical paths such as
`assets/songs/track/Inst.ogg` or `assets/notes/my_note/left.png`. These resolve in the
selected mod first, then in the built-in `assets/` folder. Song and mod IDs must be single
folder names. Put a note type's complete `data.json` under `notes/<type>/` and use that
type as the fourth value in a chart note. `penalty_note` is the supported setting name.
The misspelled `penaly_note` key is rejected with an error.

Note data can declare `"scripts": ["my_effect"]`. Put each Python file at
`assets/scripts/notes/<name>.py` and define `NoteScript(game, note)`. A new instance
is created for each spawned note. Optional hooks are `on_hit()`, `on_miss()`,
`on_update(delta_time)`, and `on_despawn()`. A script can set
`note.character_animation` to an animation name or `None` to suppress singing.
For editor completion, annotate parameters as `MainGameView` and `Note` with
`from __future__ import annotations` and imports inside `if TYPE_CHECKING:`;
see the built-in scripts in `assets/scripts/notes/` for examples.
The built-in `flame_note` subtracts 5 health when the player hits it;
`no_animation` suppresses singing, and `alt_animation` selects an available
`sing_*_alt` animation. Built-in `section_alt` preserves chart `altAnim` sections.

To replace note splashes, set the song's `splash_name` and put an Adobe Animate
`noteSplashes.xml` plus its referenced PNG at `assets/ui/splashes/<splash_name>/`.
The atlas needs four frames for both variants of blue, green, purple, and red
`note splash` animations, following the built-in default atlas names.

Game signals are defined in `sources/game/events.py`. Connect a receiver that accepts
`(sender, **event_values)` and disconnect it when its view closes. Beat events carry `beat`
and `ms`. Player note presses carry `direction_index` and `note`, releases carry
`direction_index`, and misses carry `note`. Score changes carry `score` and `accuracy`.

To add song scripts, set `"scripts": ["my_script", "opponent_float"]` in the song's
`data.json` and put each script under `assets/scripts/` in the selected mod. The older
single `"script": "my_script"` field still works. Define `SongScript(game)` with an
`on_update(delta_time)` method. The `game` object exposes `song_mgr`, `camera_mgr`,
`character_mgr`, and the other managers. Add `on_hide()` if the script needs cleanup.
The built-in `assets/scripts/alt_camera.py` and `opponent_float.py` work with other songs
that select them. The camera effect needs an opponent with `sing_*_alt` animations.
Song scripts are Python code and run when selected.
Manager and note docstrings in `sources/game/` describe script-facing fields,
units and lifecycle behavior.

For editor completion in song scripts, use `from __future__ import annotations`,
import `MainGameView` inside `if TYPE_CHECKING:`, and annotate
`def __init__(self, game: MainGameView):` as in the built-in scripts.
