"""Extra camera motion whenever the opponent performs an alt animation.

상대가 alt 애니메이션을 재생할 때 카메라 움직임을 강화합니다.
"""
from __future__ import annotations
import math
from typing import TYPE_CHECKING

import arcade

if TYPE_CHECKING:
    from sources.views.main_game import MainGameView


class SongScript:
    def __init__(self, game: MainGameView):
        self.game = game
        game.camera_mgr.note_move_multiplier = self.note_move_multiplier

    def opponent_is_alt(self, direction_index=None, note=None):
        opponent = self.game.character_mgr.opponent
        if note is not None and direction_index >= 4:
            animation = getattr(note, "character_animation", None)
            return bool(animation and animation.endswith("_alt"))
        if opponent.current_animation_name.endswith("_alt"):
            return True
        return False

    def note_move_multiplier(self, direction_index, note):
        return 1.8 if self.opponent_is_alt(direction_index, note) else 1.0

    def on_update(self, delta_time):
        camera = self.game.camera_mgr
        if self.opponent_is_alt():
            seconds = self.game.song_mgr.song_ms / 1000
            camera.shake_offset = arcade.Vec2(
                math.sin(seconds * 25) * 22,
                math.sin(seconds * 31) * 16,
            )
        else:
            camera.shake_offset = arcade.Vec2()
