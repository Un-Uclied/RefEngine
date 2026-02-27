from typing import Any
from collections import defaultdict

import arcade
from ..utils.event_bus import bus

class ScoreManager:
    def __init__(self, config: dict[Any, int]):
        # load configuration defaults
        self._config = config
        self.score = 0
        self._good_hits = 0
        self._total_notes = 0
        self.hit_counts: dict[str, int] = defaultdict(int)
        
        bus.subscribe("player_pressed", self._player_pressed)
        bus.subscribe("player_note_miss", self._player_note_miss)

    def on_hide_view(self):
        bus.unsubscribe("player_pressed", self._player_pressed)
        bus.unsubscribe("player_note_miss", self._player_note_miss)

    def _player_pressed(self, direction_index, note):
        if note is None:
            return
        
        # penalty notes deduct score when hit
        if note.penalty_note:
            self._total_notes += 1
            self.hit_counts["penalty"] += 1
            self.score += self._config.get("bad_note_hit", -100)
            self._publish_update()
            return
        
        # only count must_hit_note toward total and good_hits
        if note.must_hit_note:
            self._total_notes += 1
            self.hit_counts[note.judgement] += 1
            self._good_hits += 1
            self.score += self._config.get(note.judgement, 0)
            self._publish_update()

    def _player_note_miss(self, note):
        # only count miss if it's a must_hit_note
        if note.must_hit_note:
            self._total_notes += 1
            self.hit_counts["miss"] += 1
            self.score += self._config.get("miss", 0)
            self._publish_update()

    def _on_note_hold_lost(self, note, receptor_index=None, time=None):
        # consider holding break a penalty
        self._total_notes += 1
        self.hit_counts["hold_break"] += 1
        self.score += self._config.get("hold_break", self._config.get("bad_note_hit", -100))
        self._publish_update()

    def _publish_update(self):
        accuracy = (self._good_hits / self._total_notes * 100) if self._total_notes > 0 else 0.0
        bus.publish("score_updated", score=self.score, accuracy=accuracy, hit_counts=dict(self.hit_counts))

    def reset(self):
        self.score = 0
        self._good_hits = 0
        self._total_notes = 0
        self.hit_counts.clear()
        self._publish_update()

    def draw(self):
        arcade.draw_text(
            f"점수 : {self.score}, 히트 : {self._good_hits}, SICK!!   : {self.hit_counts["sick"]}  GOOD     : {self.hit_counts["good"]}  bad      : {self.hit_counts["bad"]}  shit..   : {self.hit_counts["shit"]} 미스      : {self.hit_counts["miss"]}",
            0, 100, arcade.color.BLUE, 36, bold=True, align="center")