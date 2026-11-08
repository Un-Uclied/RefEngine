"""Public Blinker signals for scripts and managers.

Receivers take ``(sender, **event_values)``. Step/beat events provide their
index and ``ms``. Player and opponent press events provide ``direction_index``
and ``note`` (None for an empty player press); release events provide the lane
index. A miss provides ``note``. Disconnect a script's receivers when it ends.

스크립트와 매니저가 사용하는 Blinker 신호입니다. 수신 함수는
``(sender, **event_values)``를 받습니다. 스텝/비트에는 번호와 밀리초 단위
``ms``가, 노트 입력에는 ``direction_index``와 ``note``가 전달됩니다.
빈 플레이어 입력의 ``note``는 None입니다. 스크립트가 끝나면 연결을 해제하세요.
"""
from blinker import Signal


on_step = Signal("step: step, ms")
on_beat = Signal("beat: beat, ms")
on_note_pressed = Signal("player note: direction_index, note")
on_note_released = Signal("player release: direction_index")
on_note_missed = Signal("player miss: note")
on_opponent_pressed = Signal("opponent note: direction_index, note")
on_opponent_released = Signal("opponent release: direction_index")
on_score_changed = Signal("score: score, accuracy")
