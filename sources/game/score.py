from typing import Any
from collections import defaultdict
import arcade
from .events import on_note_pressed, on_note_missed, on_score_changed

class ScoreManager:
    """Track score, hit counts, accuracy and player health from note events.

    노트 이벤트를 받아 점수, 판정 횟수, 정확도와 플레이어 체력을 관리합니다.
    """
    def __init__(self, config: dict[Any, int]):
        self._config = config
        self._score = 0
        self._health = 50
        self._good_hits = 0
        self._total_notes = 0
        self._hit_counts: dict[str, int] = defaultdict(int)
        
        on_note_pressed.connect(self._player_pressed)
        on_note_missed.connect(self._player_note_miss)

    @property
    def score(self):
        """Current integer score; judgement and penalty notes update it.

        현재 정수 점수입니다. 판정과 페널티 노트가 값을 바꿉니다.
        """
        return self._score
    
    @property
    def health(self):
        """Player health on a 0-100 scale.

        0~100 범위의 플레이어 체력입니다.
        """
        return self._health
    
    @health.setter
    def health(self, value):
        """Clamp health and notify HUD listeners through ``on_score_changed``.

        체력을 0~100으로 제한하고 ``on_score_changed``로 HUD에 알립니다.
        """
        self._health = min(max(value, 0), 100)
        accuracy = (self._good_hits / self._total_notes * 100) if self._total_notes > 0 else 0.0
        on_score_changed.send(self, score=self._score, accuracy=accuracy)

    def on_hide_view(self):
        on_note_pressed.disconnect(self._player_pressed)
        on_note_missed.disconnect(self._player_note_miss)

    def _player_pressed(self, sender, direction_index, note):
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

    def _player_note_miss(self, sender, note):
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
        on_score_changed.send(self, score=self._score, accuracy=accuracy)

    def reset(self):
        """Clear scoring counters; keep the current health value.

        점수 관련 누적값을 지우되 현재 체력은 유지합니다.
        """
        self._score = 0
        self._good_hits = 0
        self._total_notes = 0
        self._hit_counts.clear()
        self._publish_update()
