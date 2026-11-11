# EventScript

`chart.json` may contain an `events` array. Time is milliseconds from the start of the song. Events fire once in time order; restarting the song resets them.

`chart.json`에 `events` 배열을 넣습니다. `time`은 곡 시작부터의 밀리초이며, 시간순으로 한 번씩 실행됩니다. 곡을 다시 시작하면 이벤트도 초기화됩니다.

```json
"events": [
  {"time": 4000, "script": "shader_value", "params": {"shader": "lens_distortion", "uniform": "strength", "value": 0.2, "duration": 0.5}}
]
```

`shader_value` linearly interpolates a numeric scalar from its current value to `value`. `duration` is seconds (default 0.5; 0 applies immediately). Repeated events for the same uniform replace the active transition from its current value. Song pause also pauses interpolation. Custom EventScripts may implement `on_update(delta_time)` for ongoing effects.

`shader_value`는 현재 숫자 값에서 `value`까지 선형 보간합니다. `duration`은 초 단위이며 기본 0.5, 0이면 즉시 적용합니다. 같은 uniform의 새 이벤트는 현재 값에서 새 목표로 이어집니다. 일시 정지 중에는 보간도 멈춥니다. 커스텀 EventScript도 `on_update(delta_time)`을 구현해 지속적인 연출을 만들 수 있습니다.

Put a Python file at `assets/scripts/events/<script>.py`, or the same path under a mod. Each script is loaded before play. One instance is reused for that song's events. `params` must be a JSON object. Optional `on_hide()` cleans up subscriptions.

파일은 `assets/scripts/events/<이름>.py` 또는 모드의 같은 경로에 둡니다. 재생 전에 로드하며 같은 곡에서는 인스턴스를 재사용합니다. `params`는 JSON 객체입니다. 선택적으로 `on_hide()`에서 이벤트 연결 등을 정리하세요.

```python
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sources.views.main_game import MainGameView

class EventScript:
    def __init__(self, game: MainGameView):
        self.game = game

    def on_event(self, params: dict):
        self.game.score_mgr.health += params.get("health", 0)
```
