"""Lerp a scalar shader value at a chart event. / 지정 시점부터 셰이더 수치를 보간합니다."""
from __future__ import annotations
import math
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sources.views.main_game import MainGameView


class EventScript:
    def __init__(self, game: MainGameView):
        self.game = game
        self.transitions = {}

    def on_event(self, params: dict):
        if self.game.shader_mgr is None:
            return
        key = (params["shader"], params["uniform"])
        target = params["value"]
        duration = params.get("duration", 0.5)
        start = self.game.shader_mgr.get_uniform(*key)
        if any(not isinstance(value, (int, float)) or not math.isfinite(value)
               for value in (start, target, duration)) or duration < 0:
            raise ValueError("shader_value requires finite scalar values and a nonnegative duration (seconds)")
        if duration == 0:
            self.transitions.pop(key, None)
            self.game.shader_mgr.set_uniform(*key, target)
        else:
            self.transitions[key] = (start, target, self.game.song_mgr.song_ms, duration * 1000)

    def on_update(self, delta_time):
        for key, (start, target, time, duration) in list(self.transitions.items()):
            progress = min(1.0, max(0.0, (self.game.song_mgr.song_ms - time) / duration))
            self.game.shader_mgr.set_uniform(*key, start + (target - start) * progress)
            if progress == 1:
                del self.transitions[key]
