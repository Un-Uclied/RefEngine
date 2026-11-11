"""Run from the project root: python -B -m unittest discover -s tests -v."""
import unittest
import math
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

import arcade
from PIL import ImageChops

from sources.game.events import (
    on_note_missed, on_note_pressed, on_note_released,
    on_opponent_pressed, on_opponent_released, on_score_changed, on_beat,
)
from sources.views import MainGameView
from sources.game.song import SongManager
from sources.game.post_process import PostProcessManager
from sources.assets import AssetStore


class GameSmokeTest(unittest.TestCase):
    def test_vignette_darkens_edges(self):
        window = arcade.Window(64, 64, visible=False)
        self.addCleanup(window.close)
        shaders = PostProcessManager(
            [{"name": "vignette", "uniforms": {
                "strength": 1.0, "radius": 0.7, "softness": 0.3,
            }}], AssetStore(),
        )
        self.addCleanup(shaders.on_hide_view)
        shaders.begin()
        arcade.draw_lbwh_rectangle_filled(0, 0, 64, 64, arcade.color.RED)
        shaders.finish()
        image = arcade.get_image()
        self.assertGreater(image.getpixel((32, 32))[0], image.getpixel((2, 2))[0] + 100)
        shaders.set_uniform("vignette", "strength", 0.0)
        self.assertAlmostEqual(shaders.get_uniform("vignette", "strength"), 0.0)
        shaders.begin()
        arcade.draw_lbwh_rectangle_filled(0, 0, 64, 64, arcade.color.RED)
        shaders.finish()
        self.assertGreater(arcade.get_image().getpixel((2, 2))[0], image.getpixel((2, 2))[0] + 100)

    def test_bloom_spreads_bright_pixels(self):
        window = arcade.Window(64, 64, visible=False)
        self.addCleanup(window.close)
        shaders = PostProcessManager(
            [{"name": "bloom", "uniforms": {
                "strength": 1.0, "threshold": 0.5, "radius": 6.0,
            }}], AssetStore(),
        )
        self.addCleanup(shaders.on_hide_view)
        shaders.begin()
        arcade.draw_lbwh_rectangle_filled(28, 28, 8, 8, arcade.color.WHITE)
        shaders.finish()
        self.assertGreater(arcade.get_image().getpixel((40, 32))[0], 0)

    def test_vhs_scanlines_and_seasick_motion(self):
        window = arcade.Window(64, 64, visible=False)
        self.addCleanup(window.close)
        vhs = PostProcessManager(
            [{"name": "vhs", "uniforms": {
                "scanline_strength": 1.0, "noise_strength": 0.0, "jitter_strength": 0.0,
            }}], AssetStore(),
        )
        self.addCleanup(vhs.on_hide_view)
        vhs.begin()
        arcade.draw_lbwh_rectangle_filled(0, 0, 64, 64, arcade.color.WHITE)
        vhs.finish()
        image = arcade.get_image()
        self.assertGreater(abs(image.getpixel((32, 32))[0] - image.getpixel((32, 33))[0]), 100)

        seasick = PostProcessManager(
            [{"name": "seasick", "uniforms": {
                "strength": 0.1, "waves": 2.0, "speed": 0.0, "cycle_speed": 1.0,
            }}], AssetStore(),
        )
        self.addCleanup(seasick.on_hide_view)
        images = []
        for time_seconds in (0.0, math.pi / 2):
            seasick.begin()
            arcade.draw_lbwh_rectangle_filled(0, 0, 32, 64, arcade.color.RED)
            arcade.draw_lbwh_rectangle_filled(32, 0, 32, 64, arcade.color.BLUE)
            seasick.finish(time_seconds)
            images.append(arcade.get_image().convert("RGB"))
        self.assertIsNotNone(ImageChops.difference(*images).getbbox())

    def test_resume_keeps_volume_and_song_position(self):
        song = SongManager.__new__(SongManager)
        song._paused = True
        song._pause_time = 1250
        song.volume_percent = 40
        song._inst_sound = object()
        song._voices_sound = object()
        players = (Mock(), Mock())
        with patch("arcade.play_sound", side_effect=players) as play_sound:
            song.resume()
        self.assertEqual(play_sound.call_args_list, [
            call(song._inst_sound, volume=0.4),
            call(song._voices_sound, volume=0.4),
        ])
        for player in players:
            player.seek.assert_called_once_with(1.25)

    def test_signals_gameplay_and_view_cleanup(self):
        window = arcade.Window(1280, 720, visible=False)
        self.addCleanup(window.close)
        self.addCleanup(setattr, MainGameView, "current", None)
        arcade.enable_timings()
        arcade.load_font("assets/fonts/SeoulAlrimTTF-Heavy.ttf")
        view = MainGameView("singularity")
        player = SimpleNamespace(time=0, source=SimpleNamespace(duration=240))
        voices = SimpleNamespace()
        with patch("arcade.play_sound", side_effect=(player, voices)):
            window.show_view(view)
        self.assertEqual(len(view.shader_mgr.effects), len(view._song_data["shaders"]))
        self.assertTrue({"vhs", "bloom", "seasick"}.issubset(
            {effect["name"] for effect in view._song_data["shaders"]}
        ))
        with_effects = arcade.get_image().convert("RGB").crop((100, 100, 1180, 620))
        shaders = view.shader_mgr
        view.shader_mgr = None
        view.on_draw()
        without_effects = arcade.get_image().convert("RGB").crop((100, 100, 1180, 620))
        view.shader_mgr = shaders
        self.assertIsNotNone(ImageChops.difference(with_effects, without_effects).getbbox())
        view.note_mgr.is_bot_play = True
        view.on_key_press(arcade.key.MINUS, 0)
        self.assertEqual(view.song_mgr.volume_percent, 90)
        self.assertAlmostEqual(player.volume, 0.9)
        self.assertAlmostEqual(voices.volume, 0.9)
        for _ in range(10):
            view.on_key_press(arcade.key.NUM_SUBTRACT, 0)
        self.assertEqual(view.song_mgr.volume_percent, 0)
        view.on_key_press(arcade.key.EQUAL, 0)
        self.assertEqual(view.song_mgr.volume_percent, 10)
        self.assertAlmostEqual(player.volume, 0.1)
        self.assertAlmostEqual(voices.volume, 0.1)
        for _ in range(10):
            view.on_key_press(arcade.key.NUM_ADD, 0)
        self.assertEqual(view.song_mgr.volume_percent, 100)
        view.note_mgr.is_bot_play = False
        self.assertEqual(len(view.song_scripts), len(view._song_data["scripts"]))
        self.assertTrue(any(
            note["penalty_note"] for note in view.note_mgr.chart_data
            if note["note_type"] == "flame_note"
        ))
        character = view.character_mgr.player
        character._data["animations"]["idle"]["animation_speed"] = 2
        character.time = 0
        character.update_animation(0.01)
        self.assertAlmostEqual(character.time, 0.02)
        character._data["animations"]["idle"]["animation_speed"] = 1
        view.on_key_press(arcade.key.D, 0)
        self.assertEqual(view.receptor_mgr.receptors[0]._current_animation, "press")
        self.assertEqual(view.score_mgr.score, 0)
        view.on_key_release(arcade.key.D, 0)

        # Exercise the real keyboard -> note -> score/UI signal chain.
        first_hold = next(
            note for note in view.note_mgr.chart_data
            if note["direction_index"] < 4 and note["sustain_length"] > 0
            and note["must_hit_note"]
        )
        player.time = first_hold["strum_time"] / 1000
        view.on_update(1 / 60)
        previous_score = view.score_mgr.score
        key = (arcade.key.D, arcade.key.F, arcade.key.J, arcade.key.K)[
            first_hold["direction_index"]
        ]
        view.on_key_press(key, 0)
        self.assertGreater(view.score_mgr.score, previous_score)
        self.assertEqual(len(view.splash_mgr.sprites), 1)
        splash = view.splash_mgr.sprites[0]
        receptor = view.receptor_mgr.receptors[first_hold["direction_index"]]
        self.assertEqual(splash.position, receptor.position)
        color = ("purple", "blue", "green", "red")[first_hold["direction_index"]]
        self.assertIs(splash.animation, view.splash_mgr.animations[(color, 1)])
        view.splash_mgr._note_pressed(None, first_hold["direction_index"], SimpleNamespace(judgement="good"))
        self.assertEqual(len(view.splash_mgr.sprites), 1)
        view.splash_mgr._note_pressed(None, first_hold["direction_index"], SimpleNamespace(judgement="sick"))
        self.assertIs(view.splash_mgr.sprites[1].animation, view.splash_mgr.animations[(color, 2)])
        judgement = view.game_interface_mgr._judgement._judgement_sprite
        self.assertEqual(judgement.center_x, window.width / 2)
        self.assertLess(judgement.width, 350)
        self.assertEqual(
            view.game_interface_mgr._score._score_text.text,
            f"Score : {view.score_mgr.score}",
        )
        previous_misses = view.score_mgr._hit_counts["miss"]
        player.time += 0.001
        view.on_key_release(key, 0)
        self.assertGreater(view.score_mgr._hit_counts["miss"], previous_misses)
        view.on_draw()
        view.splash_mgr.update(0.21)
        self.assertEqual(len(view.splash_mgr.sprites), 0)

        # Traverse the remaining chart, including every custom note type and hold.
        view.note_mgr.is_bot_play = True
        end_ms = max(
            note["strum_time"] + note["sustain_length"]
            for note in view.note_mgr.chart_data
        ) + 1000
        for ms in range(int(player.time * 1000) + 50, int(end_ms), 50):
            player.time = ms / 1000
            view.on_update(0.05)
            if ms % 1000 < 50:
                view.on_draw()
        self.assertEqual(view.note_mgr.next_spawn_index, len(view.note_mgr.chart_data))
        self.assertEqual(len(view.note_mgr.notes), 0)
        self.assertTrue(all(len(tail) == 0 for tail in view.note_mgr.sustains.values()))
        self.assertGreater(view.score_mgr._hit_counts["auto"], 0)

        self.assertIn(view.character_mgr._beat, on_beat.receivers_for(view.song_mgr))
        with patch("arcade.stop_sound"):
            window.show_view(arcade.View())
        for signal in (
            on_beat, on_note_pressed, on_note_released, on_note_missed,
            on_opponent_pressed, on_opponent_released, on_score_changed,
        ):
            self.assertEqual(list(signal.receivers_for(view.note_mgr)), [])
