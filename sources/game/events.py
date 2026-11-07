"""Public game signals. Receivers take (sender, **listed keyword arguments)."""
from blinker import Signal


on_step = Signal("step: step, ms")
on_beat = Signal("beat: beat, ms")
on_note_pressed = Signal("player note: direction_index, note")
on_note_released = Signal("player release: direction_index")
on_note_missed = Signal("player miss: note")
on_opponent_pressed = Signal("opponent note: direction_index, note")
on_opponent_released = Signal("opponent release: direction_index")
on_score_changed = Signal("score: score, accuracy")
