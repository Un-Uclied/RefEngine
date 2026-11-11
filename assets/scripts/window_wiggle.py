"""Make the current song's opponent float without changing animation offsets.

애니메이션 오프셋을 유지하면서 현재 노래의 상대 캐릭터를 둥둥 띄웁니다.
"""
from __future__ import annotations
import math, arcade
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sources.views.main_game import MainGameView

class SongScript:
    def __init__(self, game: MainGameView):
        self.game = game
        self._start_pos = arcade.get_window().get_location()

    def on_update(self, delta_time):
        arcade.get_window().set_location(int(self._start_pos[0] + math.cos(self.game.song_mgr.song_ms / 1000 * 5) * 100), int(self._start_pos[1] + math.sin(self.game.song_mgr.song_ms / 1000 * 5) * 100))
        for receptor in self.game.receptor_mgr.receptors:
            receptor.position = (receptor.spawn_x + math.cos(self.game.song_mgr.song_ms / 1000 * 2 + receptor.direction_index) * 15, receptor.spawn_y + math.sin(self.game.song_mgr.song_ms / 1000 * 2 + receptor.direction_index) * 15)
            receptor.angle = math.sin(self.game.song_mgr.song_ms / 1000 * 5 + receptor.direction_index) * 15 + math.cos(self.game.song_mgr.song_ms / 1000 * 3 + receptor.direction_index) * 10