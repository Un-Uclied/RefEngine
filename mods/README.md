# RefEngine modding guide

[한국어](README.ko.md) · [Project README](../README.md)

Mods override built-in assets without changing the engine. Create `mods/<mod_id>/assets/` and mirror paths under the project's `assets/` directory. Start with `python run.py demo:track`, then select the preselected song and press **START**. A load error is shown on the loading screen; press `Esc` to return to the menu.

## 1. Files and lookup order

```text
mods/demo/assets/
├─ songs/track/
│  ├─ data.json
│  ├─ chart.json
│  ├─ Inst.ogg
│  └─ Voices.ogg
├─ notes/my_note/data.json
├─ scripts/my_song.py
├─ scripts/notes/my_effect.py
├─ shaders/my_effect.frag
└─ characters/my_character/data.json
```

For every logical path, RefEngine looks in `mods/demo/assets/` first, then in built-in `assets/`. Paths in JSON may start with `assets/`, for example `assets/songs/track/Inst.ogg`. A mod can replace one image or one script and use the remaining built-in files. If `mods/demo/assets/scripts/alt_camera.py` exists, it replaces the built-in script of that name; use two different script names if you need both. Mod, song, note type and script names must each be a single folder or file stem, without `/`, `\`, `:` or `..`.

The menu lists built-in songs and `mod_id:song_id` entries found under `mods/*/assets/songs/*/data.json`. A mod needs its own song `data.json` to appear there.

## 2. Song data and chart

Song metadata lives in `data.json`; timing and notes live in the referenced `chart.json`. Use [the song template](../assets/songs/README.md). Example:

`data.json`:

```json
{
  "name": "track",
  "description": "My song",
  "inst": "assets/songs/track/Inst.ogg",
  "voices": "assets/songs/track/Voices.ogg",
  "chart": "assets/songs/track/chart.json",
  "player_name": "null",
  "opponent_name": "crovan",
  "sub_character_name": null,
  "background": "crovan_stage",
  "receptor_name": "default",
  "splash_name": "default",
  "scripts": ["beat_zoom", "my_song"],
  "shaders": []
}

```

`chart.json`:

```json
{
  "bpm": 120,
  "speed": 1.6,
  "notes": [{
    "lengthInSteps": 16,
    "mustHitSection": true,
    "sectionNotes": [[500, 0, 0], [1000, 1, 0], [1500, 2, 0, "my_note"]]
  }]
}
```

Each chart note is `[strum_time_ms, lane, sustain_length_ms, optional_note_type]`. Omitting the fourth value uses `default`. Lanes 0–3 are left, down, up, right on the side indicated by `mustHitSection`; lanes 4–7 are the opposite side. Section lengths are measured in steps. Set `changeBPM: true` and a `bpm` in a section to change the timing from there. `altAnim: true` is supported by the built-in `section_alt` note script on note types that include it.

## 3. Note types and NoteScript

To make `my_note`, copy `assets/notes/default/` into `mods/demo/assets/notes/my_note/`. Edit its `data.json`: `scale`, `must_hit_note`, `penalty_note`, `scripts`, and the `paths` for all four directions. Every direction needs `head`, `hold` and `end` paths, even if your chart uses only tap notes. `head` can be a PNG or animated GIF. Use `my_note` as the fourth chart value.

`must_hit_note: false` excludes a miss from normal miss scoring. `penalty_note: true` makes bot play avoid the note and applies the configured penalty score when the player hits it. Use the exact spelling `penalty_note`; `penaly_note` is rejected. The built-in flame note uses a script to remove 5 player health on hit in addition to its penalty score. The built-in `no_animation` script suppresses singing, and `alt_animation` selects an available `sing_*_alt` animation.

List scripts in note data as `"scripts": ["my_effect"]`; the files live at `assets/scripts/notes/<name>.py` (or the matching mod path). Each spawned note gets a new `NoteScript(game, note)` instance. Optional methods are `on_hit()`, `on_miss()`, `on_update(delta_time)` and `on_despawn()`. `on_hit` runs before the hit signal reaches the score, character and camera managers. `on_miss` also runs when a sustain is released early. On view exit, remaining notes receive `on_despawn`.

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sources.views.main_game import MainGameView
    from sources.game.note import Note

class NoteScript:
    def __init__(self, game: MainGameView, note: Note):
        self.game = game
        self.note = note

    def on_hit(self):
        if not self.note.is_opponent:
            self.game.score_mgr.health -= 5
```

`note.direction_index` is 0–3 for the player and 4–7 for the opponent; `strum_time` and `sustain_length` are milliseconds. Set `note.character_animation` to a loaded animation name, or `None` to prevent a singing animation. See the English/Korean docstrings on `Note` and `NoteManager` for the other fields.

## 4. SongScript and events

Set `"scripts": ["my_song", "opponent_float"]` in song data and put each file at `assets/scripts/<name>.py` (or the mod equivalent). The older single `"script": "my_song"` works only when `scripts` is absent. Scripts run in list order and receive the active `MainGameView`. Add `on_update(delta_time)` for per-frame work and `on_hide()` to undo changes or disconnect signals when the view closes.

```python
from __future__ import annotations
import math
from typing import TYPE_CHECKING
import arcade

if TYPE_CHECKING:
    from sources.views.main_game import MainGameView

class SongScript:
    def __init__(self, game: MainGameView):
        self.game = game

    def on_update(self, delta_time: float):
        seconds = self.game.song_mgr.song_ms / 1000
        self.game.camera_mgr.shake_offset = arcade.Vec2(math.sin(seconds * 8) * 4, 0)

    def on_hide(self):
        self.game.camera_mgr.shake_offset = arcade.Vec2()
```

The `game` object exposes `assets`, `song_mgr`, `note_mgr`, `character_mgr`, `receptor_mgr`, `camera_mgr`, `shader_mgr`, `score_mgr`, `background_mgr`, `splash_mgr` and `game_interface_mgr`. Manager docstrings describe units and script-facing fields. Type imports inside `if TYPE_CHECKING:` enable editor completion without a runtime circular import. Built-in reusable examples are `assets/scripts/alt_camera.py`, `opponent_float.py` and `beat_zoom.py`. All built-in songs list `beat_zoom`; add it to a mod song's `scripts` list to use the same beat pulse.

Signals are defined in `sources/game/events.py`. A receiver takes `(sender, **event_values)`; disconnect it in `on_hide()` when you connect it yourself.

| Signal | Values |
| --- | --- |
| `on_step`, `on_beat` | `step` or `beat`, `ms` |
| `on_note_pressed`, `on_opponent_pressed` | `direction_index`, `note` |
| `on_note_released`, `on_opponent_released` | `direction_index` |
| `on_note_missed` | `note` |
| `on_score_changed` | `score`, `accuracy` |

An empty player key press sends `on_note_pressed` with `note=None`. Scripts are Python code: use only scripts you trust.

## 5. Characters, receptors and splashes

Character data lives at `assets/characters/<name>/data.json`. It needs `scale`, `camera_offset` and an `animations` map containing `idle` and the four `sing_*` directions. Each animation entry names a GIF `path` and can set `animation_speed`, `offset` and `loop`. The HUD also loads `normal.png`, `defeat.png` and `win.png` for the player and opponent. Run `python sprite_generator.py` to build character JSON and GIF copies; move the generated character folder into your mod if it should be mod-only.

Receptor data lives at `assets/ui/receptors/<name>/data.json` and supplies `idle`, `press` and `confirm` animations plus settings for all player and opponent directions. Set the song's `receptor_name` to select it.

For custom SICK splashes, set `splash_name` and place `noteSplashes.xml` plus the PNG named by its `imagePath` in `assets/ui/splashes/<name>/`. The XML needs four frames for each of variants 1 and 2 of blue, green, purple and red, following the built-in default atlas naming pattern.

## 6. Fullscreen shaders

Add an ordered `shaders` list to a song's `data.json`. Songs without this field render normally. Singularity uses these six effects:

```json
"shaders": [
  {"name": "chromatic_aberration", "uniforms": {"strength": 0.01}},
  {"name": "vignette", "uniforms": {"strength": 0.75, "radius": 0.65, "softness": 0.4}},
  {"name": "lens_distortion", "uniforms": {"strength": 0.05}},
  {"name": "vhs", "uniforms": {"scanline_strength": 0.22, "noise_strength": 0.035, "jitter_strength": 0.002}},
  {"name": "bloom", "uniforms": {"strength": 0.55, "threshold": 0.68, "radius": 5.0}},
  {"name": "seasick", "uniforms": {"strength": 0.009, "waves": 5.0, "speed": 2.0, "cycle_speed": 1.4}}
]
```

Each name loads `assets/shaders/<name>.frag`; a file in `mods/demo/assets/shaders/` with the same name replaces the built-in one. To add an effect, create a new `.frag` file and list its name in the song. The engine supplies GLSL 330 vertex output `in vec2 uv` (0–1 screen coordinates) and binds the preceding image to `uniform sampler2D u_texture` at texture unit 0. Declare `out vec4 fragColor` and write each output pixel. Put numeric shader parameters in `uniforms`, with matching GLSL uniform names. Optional `u_time` is song time in seconds; optional `u_resolution` is framebuffer size in pixels. The engine controls these three `u_*` uniforms. Effects run in array order over the whole game view, including HUD and notes. The final fade is drawn afterward.

During play, a `SongScript` or `NoteScript` can change a value without recompiling the shader: `game.shader_mgr.set_uniform("lens_distortion", "strength", 0.2)`. Read it with `game.shader_mgr.get_uniform("lens_distortion", "strength")`. The same name updates every instance of that shader in the song. `shader_mgr` is `None` when a song has no `shaders` field. VHS controls scanline darkness, grain and horizontal jitter; bloom controls glow strength, brightness threshold (0–1) and sample radius in pixels; seasick controls horizontal wave strength in UV units, wave count, motion speed and the distortion pulse speed.

## 7. Check your mod

1. Run `python run.py demo:track` and confirm the menu selects your song.
2. Press **START**. If loading fails, read the error on screen, then press `Esc`.
3. Check that every JSON asset path resolves inside your mod or the built-in assets. Script and note type names must be single names.
4. Run `python -B -m unittest discover -s tests -v` from the project root after engine changes.
