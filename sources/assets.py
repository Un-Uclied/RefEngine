"""Resolve built-in assets and one song's optional mod overrides.

기본 애셋과 선택한 노래의 모드 덮어쓰기를 처리합니다.
"""
import json
from pathlib import Path

import arcade


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASE_ASSETS = PROJECT_ROOT / "assets"
MODS_ROOT = PROJECT_ROOT / "mods"


class AssetStore:
    """Resolve logical asset paths from the active mod, then built-in assets.

    Pass paths relative to ``assets/``; an optional ``assets/`` prefix also works.
    Images are decoded once per store and reused by game managers.

    선택한 모드에서 먼저 파일을 찾고, 없으면 기본 애셋을 사용합니다.
    경로는 ``assets/`` 기준이며 ``assets/`` 접두어를 붙여도 됩니다.
    이미지는 저장소별로 한 번만 디코딩해 재사용합니다.
    """
    # shortcut: one mod is active per song; add cross-mod lookup if mods need dependencies.
    def __init__(self, mod_name=None):
        if mod_name is not None:
            self._check_name(mod_name)
        self.mod_root = MODS_ROOT / mod_name / "assets" if mod_name else None
        if self.mod_root and not self.mod_root.is_dir():
            raise FileNotFoundError(f"Mod not found: {mod_name} ({self.mod_root})")
        self._images = {}

    @staticmethod
    def _check_name(name):
        if not name or name in (".", "..") or "/" in name or "\\" in name or ":" in name:
            raise ValueError(f"Invalid asset name: {name!r}")

    @classmethod
    def for_song(cls, song_id):
        """Return ``(store, song_name)`` for ``song`` or ``mod_id:song``.

        ``song`` 또는 ``mod_id:song``에서 (애셋 저장소, 노래 이름)을 반환합니다.
        """
        if ":" in song_id:
            mod_name, song_name = song_id.split(":", 1)
            cls._check_name(mod_name)
        else:
            mod_name, song_name = None, song_id
        cls._check_name(song_name)
        return cls(mod_name), song_name

    def path(self, name):
        """Find one file, preferring the selected mod's matching path.

        선택한 모드의 같은 경로를 우선하여 파일 하나를 찾습니다.
        """
        relative = Path(name.replace("\\", "/"))
        if relative.is_absolute() or ".." in relative.parts or ":" in name:
            raise ValueError(f"Invalid asset path: {name!r}")
        if relative.parts and relative.parts[0] == "assets":
            relative = Path(*relative.parts[1:])
        if self.mod_root:
            candidate = self.mod_root / relative
            if candidate.is_file():
                return candidate
        candidate = BASE_ASSETS / relative
        if not candidate.is_file():
            raise FileNotFoundError(f"Asset not found: {name} (looked in {self.mod_root} and {BASE_ASSETS})")
        return candidate

    def json(self, name):
        """Read a JSON asset and report malformed JSON with its file path.

        JSON을 읽고 형식이 잘못되면 파일 경로를 포함해 오류를 알립니다.
        """
        path = self.path(name)
        with path.open(encoding="utf-8") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSON in {path}: {error}") from error

    def song(self, name):
        """Load song metadata and its chart through the same mod lookup.

        모드 우선순위에 따라 곡 정보와 차트를 함께 읽습니다.
        """
        data = self.json(f"songs/{name}/data.json")
        chart = self.json(data["chart"])
        return {**data, **{key: chart[key] for key in ("bpm", "speed", "notes")},
                "events": chart.get("events", [])}

    def image(self, name):
        """Return a cached Texture or TextureAnimation for a PNG or GIF.

        PNG 또는 GIF를 캐시된 텍스처나 애니메이션으로 반환합니다.
        """
        path = self.path(name)
        if path not in self._images:
            if path.suffix.lower() == ".gif":
                self._images[path] = arcade.load_animated_gif(str(path)).animation
            else:
                self._images[path] = arcade.load_texture(str(path))
        return self._images[path]
