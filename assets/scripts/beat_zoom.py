"""Pulse the three cameras on every beat. / 매 박자마다 세 카메라를 확대합니다."""

from __future__ import annotations
from typing import TYPE_CHECKING

import arcade
from sources.game.events import on_beat

if TYPE_CHECKING:
    from sources.views.main_game import MainGameView


class SongScript:
    def __init__(self, game: MainGameView):
        self.game = game
        self.world_zoom = game.camera_mgr.camera_world.zoom
        on_beat.connect(self._beat)

    def _beat(self, sender, beat, ms):
        if sender is not self.game.song_mgr:
            return
        camera = self.game.camera_mgr
        camera.camera_ui.zoom = 1.1
        camera.camera_note.zoom = 1.15
        camera.camera_world.zoom = self.world_zoom + 0.15

    def on_update(self, delta_time):
        camera = self.game.camera_mgr
        camera.camera_world.zoom = arcade.math.lerp(camera.camera_world.zoom, self.world_zoom, min(delta_time, 1))
        camera.camera_note.zoom = arcade.math.lerp(camera.camera_note.zoom, 1, min(delta_time, 1))
        camera.camera_ui.zoom = arcade.math.lerp(camera.camera_ui.zoom, 1, min(delta_time * 10, 1))

    def on_hide(self):
        on_beat.disconnect(self._beat)
        camera = self.game.camera_mgr
        camera.camera_world.zoom = self.world_zoom
        camera.camera_note.zoom = 1
        camera.camera_ui.zoom = 1
