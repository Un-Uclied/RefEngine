"""Shuffle eight receptor slots every ten song seconds.

곡 재생 시간 10초마다 0~7번 리셉터를 1초 동안 보간해 이동합니다.
입력 레인과 방향은 유지하며 window_wiggle의 이동 오프셋을 보존합니다.
"""
from __future__ import annotations
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sources.views.main_game import MainGameView


class SongScript:
    def __init__(self, game: MainGameView):
        self.game = game
        self.receptors = list(game.receptor_mgr.receptors)[:8]
        self.original = [(r.spawn_x, r.spawn_y) for r in self.receptors]
        self.last_interval = 0
        self.targets = self.original[:]
        self.starts = self.original[:]
        self.transition_start = None

    def on_update(self, delta_time):
        interval = int(self.game.song_mgr.song_ms // 10000)
        if len(self.receptors) < 2:
            return
        if interval > self.last_interval:
            self.last_interval = interval
            order = list(range(len(self.receptors)))
            while any(index == slot for index, slot in enumerate(order)):
                random.shuffle(order)
            self.starts = [(r.spawn_x, r.spawn_y) for r in self.receptors]
            self.targets = [self.targets[index] for index in order]
            self.transition_start = self.game.song_mgr.song_ms
        if self.transition_start is None:
            return
        progress = min(1.0, max(0.0, (self.game.song_mgr.song_ms - self.transition_start) / 1000))
        self._place([(x + (tx - x) * progress, y + (ty - y) * progress)
                     for (x, y), (tx, ty) in zip(self.starts, self.targets)])
        if progress == 1:
            self.transition_start = None
        # Notes have already updated this frame; move heads and tails immediately.
        for note in self.game.note_mgr.notes:
            note.update_position(self.game.song_mgr.song_ms, self.game.note_mgr.pixels_per_ms)
            for segment in note.segments:
                segment.sync_position()

    def _place(self, positions):
        for receptor, (x, y) in zip(self.receptors, positions):
            receptor.position = (receptor.center_x + x - receptor.spawn_x,
                                 receptor.center_y + y - receptor.spawn_y)
            receptor.spawn_x, receptor.spawn_y = x, y

    def on_hide(self):
        self._place(self.original)
