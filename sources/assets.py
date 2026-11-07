"""Resolve built-in assets and one song's optional mod overrides."""
import json
from pathlib import Path

import arcade


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASE_ASSETS = PROJECT_ROOT / "assets"
MODS_ROOT = PROJECT_ROOT / "mods"


class AssetStore:
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
        if ":" in song_id:
            mod_name, song_name = song_id.split(":", 1)
            cls._check_name(mod_name)
        else:
            mod_name, song_name = None, song_id
        cls._check_name(song_name)
        return cls(mod_name), song_name

    def path(self, name):
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
        path = self.path(name)
        with path.open(encoding="utf-8") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSON in {path}: {error}") from error

    def image(self, name):
        path = self.path(name)
        if path not in self._images:
            if path.suffix.lower() == ".gif":
                self._images[path] = arcade.load_animated_gif(str(path)).animation
            else:
                self._images[path] = arcade.load_texture(str(path))
        return self._images[path]
