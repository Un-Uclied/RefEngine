import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import arcade

from sources import assets
from sources.game.note import NoteManager
from sources.views import MainGameView


class AssetStoreTest(unittest.TestCase):
    def test_misspelled_penalty_setting_is_rejected(self):
        manager = NoteManager.__new__(NoteManager)
        manager.game_context = SimpleNamespace(assets=SimpleNamespace(
            _check_name=assets.AssetStore._check_name,
            json=lambda path: {"penaly_note": True},
        ))
        manager.song_data = {"notes": []}
        manager.note_settings = {}
        manager.note_assets = {}
        with self.assertRaisesRegex(ValueError, "penalty_note"):
            manager.load_resources()

    def test_mod_override_fallback_and_cached_image(self):
        with tempfile.TemporaryDirectory(dir=assets.PROJECT_ROOT) as directory:
            root = Path(directory)
            self.assertTrue(root.resolve().is_relative_to(assets.PROJECT_ROOT.resolve()))
            base = root / "assets"
            mod = root / "mods" / "demo" / "assets"
            (base / "notes/default").mkdir(parents=True)
            (mod / "notes/default").mkdir(parents=True)
            (base / "notes/default/data.json").write_text('{"value": "base"}')
            (mod / "notes/default/data.json").write_text('{"value": "mod"}')
            (base / "notes/default/left.png").touch()
            (mod / "notes/default/right.png").touch()
            with patch.object(assets, "BASE_ASSETS", base), patch.object(assets, "MODS_ROOT", root / "mods"):
                store, song = assets.AssetStore.for_song("demo:track")
                self.assertEqual(song, "track")
                self.assertEqual(store.json("notes/default/data.json"), {"value": "mod"})
                self.assertEqual(store.path("assets/notes/default/left.png"), base / "notes/default/left.png")
                self.assertEqual(store.path("assets/notes/default/right.png"), mod / "notes/default/right.png")
                with patch("arcade.load_texture", return_value=object()) as load:
                    self.assertIs(store.image("notes/default/right.png"), store.image("assets/notes/default/right.png"))
                    load.assert_called_once()
                with self.assertRaises(ValueError):
                    store.path("../secret")
                with self.assertRaises(ValueError):
                    assets.AssetStore.for_song("../secret:track")

    def test_mod_song_uses_its_chart_and_builtin_fallback(self):
        window = arcade.Window(1280, 720, visible=False)
        self.addCleanup(window.close)
        with tempfile.TemporaryDirectory(dir=assets.PROJECT_ROOT) as directory:
            root = Path(directory)
            self.assertTrue(root.resolve().is_relative_to(assets.PROJECT_ROOT.resolve()))
            song_path = root / "demo/assets/songs/endless-D/data.json"
            song_path.parent.mkdir(parents=True)
            chart = json.loads((assets.BASE_ASSETS / "songs/endless-D/data.json").read_text(encoding="utf-8"))
            chart["name"] = "Modded test"
            song_path.write_text(json.dumps(chart), encoding="utf-8")
            with patch.object(assets, "MODS_ROOT", root):
                view = MainGameView("demo:endless-D")
                self.assertEqual(view._song_data["name"], "Modded test")
                self.assertEqual(view._background_data["default_zoom"], 0.5)
            self.assertEqual(MainGameView("test")._song_data["name"], "test")
