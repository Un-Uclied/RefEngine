# RefEngine

Python과 Arcade로 만드는 Friday Night Funkin' 스타일 리듬 게임 엔진입니다. 현재 개발 중이며, 곡·노트·캐릭터를 파일과 스크립트로 교체할 수 있습니다.

## 시작하기

Python 3.13 / Arcade 3.3.3 환경에서 확인했습니다.

```powershell
python -m pip install arcade blinker pillow
python run.py
```

메뉴에서 곡을 고른 뒤 **START**를 누르세요. `python run.py <mod_id>:<song_id>`로 실행하면 해당 모드 곡이 메뉴에서 미리 선택됩니다. 로딩 진행률이 표시되고 화면 전환이 끝나면 노래가 시작됩니다.

| 위치 | 조작 |
| --- | --- |
| 메뉴 | `↑` / `↓`로 선택, `Enter`로 시작 · 마우스로 선택 및 START 클릭 |
| 플레이 | `D` `F` `J` `K` 또는 방향키로 노트 입력 |
| 볼륨 | `-` / `+`로 마스터 볼륨을 10%씩 조절 (0~100%) |

## 모딩

모드는 `mods/<mod_id>/assets/` 아래에 기본 `assets/`와 같은 경로로 놓습니다. 같은 경로의 파일이 있으면 모드 파일이 우선하고, 없으면 기본 애셋을 사용합니다.

```text
mods/demo/assets/
├─ songs/track/data.json
├─ notes/my_note/data.json
├─ scripts/my_song.py
└─ scripts/notes/my_effect.py
```

- 곡의 `data.json`에서 `"scripts": ["my_song"]`으로 `SongScript(game)`를 지정합니다.
- 노트의 `data.json`에서 `"scripts": ["my_effect"]`로 `NoteScript(game, note)`를 지정합니다.
- 스크립트에서 쓰는 매니저·노트 API는 코드의 **영어/한국어 docstring**과 [모딩 가이드](mods/README.md)를 참고하세요.

GIF 캐릭터 애니메이션의 JSON을 만들 때는 `python sprite_generator.py`를 실행하세요. 생성기가 루트에 JSON을 내보내고 `assets/characters/<이름>/`에도 필요한 파일을 설치합니다.

## 개발

```powershell
python -B -m unittest discover -s tests -v
```

## 미리보기

<p align="center">
  <img src="image.png" alt="RefEngine 게임 화면 1" width="49%">
  <img src="image2.png" alt="RefEngine 게임 화면 2" width="49%">
</p>
