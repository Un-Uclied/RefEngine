from typing import Any
from collections import defaultdict
import arcade
from sources.utils import bus

class ScoreManager:
    def __init__(self, config: dict[Any, int]):
        self._config = config
        self._score = 0
        self._health = 50
        self._good_hits = 0
        self._total_notes = 0
        self._hit_counts: dict[str, int] = defaultdict(int)
        
        bus.subscribe("player_pressed", self._player_pressed)
        bus.subscribe("player_note_miss", self._player_note_miss)

    @property
    def score(self):
        return self._score
    
    @property
    def health(self):
        return self._health
    
    @health.setter
    def health(self, value):
        self._health = min(max(value, 0), 100)
        accuracy = (self._good_hits / self._total_notes * 100) if self._total_notes > 0 else 0.0
        bus.publish("score_updated", score=self._score, accuracy=accuracy)

    def on_hide_view(self):
        bus.unsubscribe("player_pressed", self._player_pressed)
        bus.unsubscribe("player_note_miss", self._player_note_miss)

    def _player_pressed(self, direction_index, note):
        if note is None:
            return
        
        # penalty notes deduct score when hit
        if note.penalty_note:
            self._total_notes += 1
            self._hit_counts["penalty"] += 1
            self._score += self._config.get("bad_note_hit", -100)
            self._publish_update()
            return
        
        # only count must_hit_note toward total and good_hits
        if note.must_hit_note:
            self._total_notes += 1
            self._health += self._config["hit_health"]
            self._health = min(max(self._health, 0), 100)
            self._hit_counts[note.judgement] += 1
            self._good_hits += 1
            self._score += self._config.get(note.judgement, 0)
            self._publish_update()

    def _player_note_miss(self, note):
        # only count miss if it's a must_hit_note
        if note.must_hit_note:
            self._total_notes += 1
            self._health += self._config["miss_health"]
            self._health = min(max(self._health, 0), 100)
            self._hit_counts["miss"] += 1
            self._score += self._config.get("miss", 0)
            self._publish_update()

    def _on_note_hold_lost(self, note, receptor_index=None, time=None):
        # consider holding break a penalty
        self._total_notes += 1
        self._hit_counts["hold_break"] += 1
        self._score += self._config.get("hold_break", self._config.get("bad_note_hit", -100))
        self._publish_update()

    def _publish_update(self):
        accuracy = (self._good_hits / self._total_notes * 100) if self._total_notes > 0 else 0.0
        bus.publish("score_updated", score=self._score, accuracy=accuracy)

    def reset(self):
        self._score = 0
        self._good_hits = 0
        self._total_notes = 0
        self._hit_counts.clear()
        self._publish_update()