# RefEngine 모딩 가이드

[English](README.md) · [프로젝트 README](../README.md)

모드는 엔진 코드를 수정하지 않고 기본 애셋을 덮어쓰는 방식입니다. `mods/<모드 ID>/assets/` 아래에 프로젝트의 `assets/`와 같은 폴더 구조를 만드세요. `python run.py demo:track`으로 실행하면 해당 곡이 메뉴에서 미리 선택됩니다. **START**를 눌러 로드하고, 오류가 나타나면 메시지를 확인한 뒤 `Esc`로 메뉴에 돌아갈 수 있습니다.

## 1. 폴더 구조와 애셋 우선순위

```text
mods/demo/assets/
├─ songs/track/
│  ├─ data.json
│  ├─ Inst.ogg
│  └─ Voices.ogg
├─ notes/my_note/data.json
├─ scripts/my_song.py
├─ scripts/notes/my_effect.py
└─ characters/my_character/data.json
```

엔진은 논리 경로마다 `mods/demo/assets/`를 먼저 찾고, 파일이 없으면 기본 `assets/`에서 찾습니다. JSON 경로에는 `assets/songs/track/Inst.ogg`처럼 `assets/` 접두어를 붙여도 됩니다. 이미지나 스크립트 하나만 모드에서 교체하고 나머지는 기본 파일을 써도 됩니다. 같은 경로의 `mods/demo/assets/scripts/alt_camera.py`가 있으면 기본 `alt_camera.py` 대신 실행합니다. 두 스크립트를 함께 쓰려면 서로 다른 이름으로 지정하세요. 모드·곡·노트 종류·스크립트 이름은 각각 경로 구분자(`/`, `\`)나 `:`, `..`가 없는 단일 이름이어야 합니다.

메뉴는 기본 곡과 `mods/*/assets/songs/*/data.json`에 있는 `모드 ID:곡 ID`를 보여줍니다. 모드 곡이 목록에 나오려면 그 곡의 `data.json`이 필요합니다.

## 2. 곡 데이터와 차트

기존 곡의 `data.json`을 복사하면 전체 차트 구조를 확인하기 쉽습니다. 아래는 기본 캐릭터·배경·리셉터·스플래시를 재사용하는 작은 예시입니다.

```json
{
  "name": "track",
  "player_name": "null",
  "opponent_name": "crovan",
  "sub_character_name": null,
  "background": "crovan_stage",
  "receptor_name": "default",
  "splash_name": "default",
  "inst_path": "assets/songs/track/Inst.ogg",
  "voices_path": "assets/songs/track/Voices.ogg",
  "bpm": 120,
  "speed": 1.6,
  "scripts": ["my_song"],
  "notes": [
    {
      "lengthInSteps": 16,
      "mustHitSection": true,
      "sectionNotes": [
        [500, 0, 0],
        [1000, 1, 0],
        [1500, 2, 0, "my_note"]
      ]
    }
  ]
}
```

각 노트는 `[판정 시각(ms), 레인, 롱 노트 길이(ms), 선택적 노트 종류]`입니다. 네 번째 값을 생략하면 `default`를 씁니다. 레인 0~3은 왼쪽·아래·위·오른쪽이며 `mustHitSection`이 가리키는 쪽에 배치됩니다. 레인 4~7은 반대쪽입니다. 구간 길이는 스텝 수로 지정합니다. BPM을 구간 중간에 바꾸려면 해당 구간에 `"changeBPM": true`와 새 `bpm`을 넣으세요. `"altAnim": true`는 해당 노트 종류가 기본 `section_alt` 스크립트를 포함할 때 alt 애니메이션을 선택합니다.

## 3. 노트 종류와 NoteScript

`my_note`를 만들려면 `assets/notes/default/`를 `mods/demo/assets/notes/my_note/`로 복사한 뒤 `data.json`을 수정하세요. `scale`, `must_hit_note`, `penalty_note`, `scripts`와 네 방향의 `paths`를 설정합니다. 탭 노트만 쓰더라도 모든 방향에 `head`, `hold`, `end` 경로가 있어야 합니다. `head`는 PNG나 애니메이션 GIF를 사용할 수 있습니다. 차트 노트의 네 번째 값에 `"my_note"`를 적으면 적용됩니다.

`must_hit_note: false`인 노트를 놓쳐도 일반 미스 점수에는 포함되지 않습니다. `penalty_note: true`는 자동 플레이가 그 노트를 피하게 하고, 플레이어가 치면 설정된 페널티 점수를 적용합니다. 키 이름은 정확히 `penalty_note`여야 하며 `penaly_note`는 오류로 거부됩니다. 기본 `flame_note`는 페널티 점수에 더해 스크립트로 플레이어 체력 5를 깎습니다. `no_animation`은 노래 애니메이션을 막고, `alt_animation`은 캐릭터에 있는 `sing_*_alt` 애니메이션을 선택합니다.

노트 데이터에 `"scripts": ["my_effect"]`를 넣으면 `assets/scripts/notes/my_effect.py` 또는 같은 모드 경로의 파일을 로드합니다. 스폰된 노트마다 별도의 `NoteScript(game, note)` 인스턴스를 만듭니다. 선택적으로 `on_hit()`, `on_miss()`, `on_update(delta_time)`, `on_despawn()`을 구현할 수 있습니다. `on_hit`은 점수·캐릭터·카메라 매니저가 히트 신호를 받기 전에 실행됩니다. 롱 노트를 일찍 놓았을 때도 `on_miss`가 호출됩니다. 게임 화면을 나갈 때 남아 있는 노트에는 `on_despawn`이 호출됩니다.

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sources.views.main_game import MainGameView
    from sources.game.note import Note

class NoteScript:
    def __init__(self, game: MainGameView, note: Note):
        self.game = game
        self.note = note

    def on_hit(self):
        if not self.note.is_opponent:
            self.game.score_mgr.health -= 5
```

`note.direction_index`는 플레이어 0~3, 상대 4~7입니다. `strum_time`과 `sustain_length`는 밀리초입니다. `note.character_animation`에 로드된 애니메이션 이름을 넣거나 `None`으로 설정해 노래 애니메이션을 막을 수 있습니다. 다른 속성은 `Note`와 `NoteManager`의 한영 docstring을 참고하세요.

## 4. SongScript와 이벤트

곡 데이터에 `"scripts": ["my_song", "opponent_float"]`를 넣고 각 파일을 `assets/scripts/<이름>.py` 또는 모드의 같은 경로에 둡니다. 예전 단일 `"script": "my_song"` 필드는 `scripts`가 없을 때만 사용됩니다. 스크립트는 배열 순서대로 실행되고 현재 `MainGameView`를 받습니다. 매 프레임 작업에는 `on_update(delta_time)`, 변경 복구나 이벤트 연결 해제에는 `on_hide()`를 사용하세요.

```python
from __future__ import annotations
import math
from typing import TYPE_CHECKING
import arcade

if TYPE_CHECKING:
    from sources.views.main_game import MainGameView

class SongScript:
    def __init__(self, game: MainGameView):
        self.game = game

    def on_update(self, delta_time: float):
        seconds = self.game.song_mgr.song_ms / 1000
        self.game.camera_mgr.shake_offset = arcade.Vec2(math.sin(seconds * 8) * 4, 0)

    def on_hide(self):
        self.game.camera_mgr.shake_offset = arcade.Vec2()
```

`game`에서 `assets`, `song_mgr`, `note_mgr`, `character_mgr`, `receptor_mgr`, `camera_mgr`, `score_mgr`, `background_mgr`, `splash_mgr`, `game_interface_mgr`에 접근할 수 있습니다. 각 매니저의 한영 docstring에 단위와 스크립트용 필드가 설명되어 있습니다. `if TYPE_CHECKING:` 안에서 타입을 가져오면 실행 중 순환 import 없이 에디터 자동완성을 사용할 수 있습니다. 다른 곡에도 적용할 수 있는 예시는 `assets/scripts/alt_camera.py`와 `opponent_float.py`입니다.

이벤트 신호는 `sources/game/events.py`에 있습니다. 수신 함수는 `(sender, **event_values)` 형태이며, 직접 연결했다면 `on_hide()`에서 해제하세요.

| 신호 | 전달 값 |
| --- | --- |
| `on_step`, `on_beat` | `step` 또는 `beat`, `ms` |
| `on_note_pressed`, `on_opponent_pressed` | `direction_index`, `note` |
| `on_note_released`, `on_opponent_released` | `direction_index` |
| `on_note_missed` | `note` |
| `on_score_changed` | `score`, `accuracy` |

플레이어가 노트 없이 버튼을 눌러도 `on_note_pressed`가 발생하며 이때 `note`는 `None`입니다. 스크립트는 Python 코드 그대로 실행되므로 신뢰하는 파일만 사용하세요.

## 5. 캐릭터·리셉터·스플래시

캐릭터 데이터는 `assets/characters/<이름>/data.json`에 둡니다. `scale`, `camera_offset`, `animations`가 필요하며 애니메이션에는 `idle`과 네 방향의 `sing_*`을 준비하세요. 각 애니메이션에는 GIF `path`를 쓰고 `animation_speed`, `offset`, `loop`를 설정할 수 있습니다. HUD는 플레이어와 상대의 `normal.png`, `defeat.png`, `win.png`도 읽습니다. `python sprite_generator.py`로 캐릭터 JSON과 GIF 복사본을 만들 수 있습니다. 모드 전용이면 생성된 캐릭터 폴더를 모드의 `assets/characters/`로 옮기세요.

리셉터 데이터는 `assets/ui/receptors/<이름>/data.json`에 둡니다. 플레이어·상대의 모든 방향에 대한 설정과 `idle`, `press`, `confirm` 애니메이션이 필요합니다. 곡의 `receptor_name`으로 선택합니다.

SICK 스플래시를 교체하려면 곡의 `splash_name`을 설정하고 `assets/ui/splashes/<이름>/`에 `noteSplashes.xml`과 XML의 `imagePath`가 가리키는 PNG를 둡니다. XML에는 blue·green·purple·red 각각의 변형 1·2에 대해 4프레임이 있어야 합니다. 프레임 이름 규칙은 기본 아틀라스를 참고하세요.

## 6. 모드 확인

1. `python run.py demo:track`을 실행해 메뉴에 곡이 선택되는지 확인합니다.
2. **START**를 누릅니다. 로딩 오류가 뜨면 메시지를 확인하고 `Esc`로 돌아갑니다.
3. JSON의 모든 애셋 경로가 모드나 기본 애셋에 실제로 있는지 확인합니다. 스크립트·노트 종류 이름은 단일 이름이어야 합니다.
4. 엔진 코드를 바꿨다면 프로젝트 루트에서 `python -B -m unittest discover -s tests -v`를 실행합니다.
