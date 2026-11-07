"""Run from the project root: python -B -m unittest discover -s tests -v."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import arcade

from sources.game.events import (
    on_note_missed, on_note_pressed, on_note_released,
    on_opponent_pressed, on_opponent_released, on_score_changed, on_beat,
)
from sources.views import MainGameView


class GameSmokeTest(unittest.TestCase):
    def test_signals_gameplay_and_view_cleanup(self):
        window = arcade.Window(1280, 720, visible=False)
        self.addCleanup(window.close)
        self.addCleanup(setattr, MainGameView, "current", None)
        arcade.enable_timings()
        arcade.load_font("assets/fonts/Paperlogy-8ExtraBold.ttf")
        view = MainGameView("singularity")
        player = SimpleNamespace(time=0, source=SimpleNamespace(duration=240))
        with patch("arcade.play_sound", return_value=player):
            window.show_view(view)
        self.assertTrue(any(
            note["penalty_note"] for note in view.note_mgr.chart_data
            if note["note_type"] == "flame_note"
        ))

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
