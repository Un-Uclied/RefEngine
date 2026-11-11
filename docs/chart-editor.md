# 차트 에디터 / Chart editor

플레이 중 **7**로 엽니다. 에디터에서 나가면 곡을 처음부터 다시 로드합니다. 저장 전 변경은 게임에 적용되지 않습니다.

Press **7** during play. Leaving reloads the song from the beginning; only saved edits are used by gameplay.

| 조작 / Control | 동작 / Action |
| --- | --- |
| 왼쪽 클릭 / Left click | 노트 추가 또는 선택 / Add or select a note |
| 오른쪽 클릭, Delete / Right click, Delete | 삭제 / Delete |
| + / - | 선택 노트의 롱 노트 길이 / Selected sustain length |
| PageUp / PageDown, 휠 / wheel | 구간 이동 / Navigate sections |
| [ / ] | 비트 스냅 / Beat snap |
| Tab, T | 노트/이벤트 타입 선택 모드 전환, 타입 순환 / Choose mode and cycle types |
| 마지막 격자 열 / Last grid column | 이벤트 추가/선택 / Add or select events |
| P | 선택 이벤트의 params JSON 편집 / Edit event JSON parameters |
| B / V | 기본 BPM / 노트 스크롤 속도 / Base BPM or scroll speed |
| H | 구간 mustHitSection 전환 / Switch the section's player side |
| A | 마지막에 구간 추가 / Append a section |
| Space | 현재 구간부터 오디오 미리듣기 / Preview audio from this section |
| Ctrl+S | 저장 / Save |
| Ctrl+Z / Ctrl+Y | 실행 취소 / 복원 / Undo or redo |
| Esc | 나가기, 미저장 변경이 있으면 다시 눌러 버리기 / Exit; press again to discard unsaved edits |

입력창에서는 Ctrl+A로 내용을 지우고 새 값을 입력한 뒤 Enter를 누릅니다. 이벤트 코드는 [EventScript 가이드](../assets/scripts/events/README.md)를 참고하세요. 타입 파일은 에디터를 다시 열면 검색됩니다.

In a text field, Ctrl+A clears the value, Enter applies it, and Esc cancels. See the [EventScript guide](../assets/scripts/events/README.md). Reopen the editor after adding new script/type files.

모드 곡을 저장하면 모드 폴더에 차트를 만듭니다. 기본 차트는 덮어쓰지 않습니다. 외부에서 파일이 바뀌면 저장을 거부하며, 편집기는 전체 JSON의 추가 필드도 보존합니다.

Saving a mod song writes its chart under the mod. External file changes block saving. Unknown chart fields are retained.

현재 미리듣기는 오디오와 재생선만 표시하며 EventScript를 실행하지 않습니다. 웨이브폼, 다중 선택, 드래그 이동과 구간별 BPM 편집 UI는 아직 없습니다. 기존 구간별 BPM은 읽고 보존합니다.

Preview plays audio and shows a playhead without running EventScripts. Waveforms, multiselect, drag movement and a section BPM editor are not included yet; existing section BPM changes are preserved.
