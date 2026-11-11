# Song files / 곡 파일 템플릿

Place `data.json` and `chart.json` in `assets/songs/<song_id>/`, or the same path under a mod. `chart` is an asset path resolved from the active mod first. / 두 파일을 같은 곡 폴더에 둡니다. `chart` 경로는 선택한 모드의 파일을 우선합니다.

`data.json`:

```json
{
  "name": "track",
  "description": "Song description",
  "inst": "assets/songs/track/Inst.ogg",
  "voices": "assets/songs/track/Voices.ogg",
  "chart": "assets/songs/track/chart.json",
  "player_name": "null",
  "opponent_name": "crovan",
  "sub_character_name": null,
  "background": "crovan_stage",
  "receptor_name": "default",
  "splash_name": "default",
  "scripts": ["beat_zoom"],
  "shaders": []
}
```

`chart.json`:

```json
{
  "bpm": 120,
  "speed": 1.6,
  "notes": [
    {
      "lengthInSteps": 16,
      "mustHitSection": true,
      "sectionNotes": [[500, 0, 0], [1000, 1, 0]]
    }
  ]
}
```

Change `track` in asset paths to your song folder name. `sub_character_name` may be `null`. Scripts and shaders may be empty lists. / 애셋 경로의 `track`은 실제 곡 폴더 이름으로 바꾸세요. 보조 캐릭터는 `null`, 스크립트와 셰이더는 빈 배열로 둘 수 있습니다.
