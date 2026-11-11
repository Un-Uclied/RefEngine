import math
import json
import runpy
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import arcade

from sources.assets import AssetStore, BASE_ASSETS
from sources.game.events import on_beat


class SongScriptTest(unittest.TestCase):
    def test_receptor_shuffle_uses_song_time_and_keeps_offsets(self):
        script = runpy.run_path(str(AssetStore().path("scripts/receptor_shuffle.py")))["SongScript"]
        receptors = [arcade.Sprite() for _ in range(8)]
        for index, receptor in enumerate(receptors):
            receptor.spawn_x, receptor.spawn_y = index * 100, 500
            receptor.position = (index * 100 + 3, 505)
            receptor.direction_index = index
        original = [(r.spawn_x, r.spawn_y) for r in receptors]
        note = Mock(segments=[Mock()])
        song = SimpleNamespace(song_ms=9999)
        game = SimpleNamespace(song_mgr=song, receptor_mgr=SimpleNamespace(receptors=receptors),
                               note_mgr=SimpleNamespace(notes=[note], pixels_per_ms=1.4))
        effect = script(game)
        with patch.dict(script.on_update.__globals__, random=SimpleNamespace(shuffle=lambda order: order.reverse())):
            effect.on_update(1 / 60)
            self.assertEqual([(r.spawn_x, r.spawn_y) for r in receptors], original)
            song.song_ms = 10000
            effect.on_update(1 / 60)
            self.assertEqual([(r.spawn_x, r.spawn_y) for r in receptors], original)
            song.song_ms = 10500
            effect.on_update(1 / 60)
            for receptor, start, target in zip(receptors, original, original[::-1]):
                self.assertEqual(receptor.spawn_x, (start[0] + target[0]) / 2)
            song.song_ms = 11000
            effect.on_update(1 / 60)
            self.assertEqual([(r.spawn_x, r.spawn_y) for r in receptors], original[::-1])
            effect.on_update(1 / 60)
            self.assertEqual(note.update_position.call_count, 3)
            self.assertEqual(note.segments[0].sync_position.call_count, 3)
            for index, receptor in enumerate(receptors):
                self.assertEqual(receptor.direction_index, index)
                self.assertEqual(receptor.position, (receptor.spawn_x + 3, receptor.spawn_y + 5))
            song.song_ms = 20000
            effect.on_update(1 / 60)
            self.assertEqual(note.update_position.call_count, 4)
        effect.on_hide()
        self.assertEqual([(r.spawn_x, r.spawn_y) for r in receptors], original)

    def test_all_builtin_songs_enable_beat_zoom(self):
        for path in (BASE_ASSETS / "songs").glob("*/data.json"):
            with self.subTest(song=path.parent.name):
                self.assertIn("beat_zoom", json.loads(path.read_text(encoding="utf-8")).get("scripts", []))

    def test_beat_zoom_pulses_and_recovers_on_any_song(self):
        script = runpy.run_path(str(AssetStore().path("scripts/beat_zoom.py")))["SongScript"]
        song = object()
        camera = SimpleNamespace(
            camera_world=SimpleNamespace(zoom=0.8),
            camera_note=SimpleNamespace(zoom=1.0),
            camera_ui=SimpleNamespace(zoom=1.0),
        )
        effect = script(SimpleNamespace(song_mgr=song, camera_mgr=camera))
        self.addCleanup(effect.on_hide)
        on_beat.send(song, beat=0, ms=0)
        self.assertAlmostEqual(camera.camera_world.zoom, 0.95)
        self.assertAlmostEqual(camera.camera_note.zoom, 1.15)
        self.assertAlmostEqual(camera.camera_ui.zoom, 1.1)
        effect.on_update(1 / 60)
        self.assertLess(camera.camera_world.zoom, 0.95)
        self.assertLess(camera.camera_note.zoom, 1.15)
        effect.on_hide()
        self.assertAlmostEqual(camera.camera_world.zoom, 0.8)
        self.assertEqual(list(on_beat.receivers_for(song)), [])

    def test_opponent_float_does_not_drift_or_lose_animation_offsets(self):
        script = runpy.run_path(str(AssetStore().path("scripts/opponent_float.py")))["SongScript"]
        opponent = SimpleNamespace(center_y=500.0)
        song = SimpleNamespace(song_ms=250)
        effect = script(SimpleNamespace(character_mgr=SimpleNamespace(opponent=opponent), song_mgr=song))
        effect.on_update(1 / 60)
        offset = math.sin(0.25 * math.tau * 0.7) * 70
        self.assertAlmostEqual(opponent.center_y, 500 + offset)
        effect.on_update(1 / 60)
        self.assertAlmostEqual(opponent.center_y, 500 + offset)
        opponent.center_y += 12  # An animation changes its own offset.
        song.song_ms = 500
        effect.on_update(1 / 60)
        self.assertAlmostEqual(opponent.center_y, 512 + math.sin(0.5 * math.tau * 0.7) * 70)
        effect.on_hide()
        self.assertAlmostEqual(opponent.center_y, 512)

    def test_alt_camera_works_with_another_song_context(self):
        script = runpy.run_path(str(AssetStore().path("scripts/alt_camera.py")))["SongScript"]
        camera = SimpleNamespace(shake_offset=arcade.Vec2())
        opponent = SimpleNamespace(
            current_animation_name="idle",
            loaded_animations={"sing_left_alt": object()},
        )
        game = SimpleNamespace(
            camera_mgr=camera,
            character_mgr=SimpleNamespace(opponent=opponent),
            song_mgr=SimpleNamespace(song_ms=125, current_section_data={"altAnim": False}),
        )
        effect = script(game)
        note = SimpleNamespace(character_animation="sing_left_alt")
        self.assertEqual(effect.note_move_multiplier(4, note), 1.8)
        self.assertEqual(effect.note_move_multiplier(0, note), 1.0)
        opponent.current_animation_name = "sing_left_alt"
        effect.on_update(1 / 60)
        self.assertNotEqual(camera.shake_offset, arcade.Vec2())
        opponent.current_animation_name = "idle"
        effect.on_update(1 / 60)
        self.assertEqual(camera.shake_offset, arcade.Vec2())
