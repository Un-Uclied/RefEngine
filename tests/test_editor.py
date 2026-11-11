import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import arcade
from sources.assets import AssetStore, PROJECT_ROOT
from sources.game.chart_events import ChartEventManager
from sources.views.chart_editor import ChartDocument, ChartEditor
from sources.views.system_ui import fps_color


class EditorTest(unittest.TestCase):
    def test_save_undo_conflict_and_mod_override(self):
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT) as directory:
            root = Path(directory)
            source = root / "chart.json"
            source.write_text(json.dumps({"bpm": 120, "speed": 1, "notes": []}))
            assets = SimpleNamespace(path=lambda _: source, mod_root=root / "mod")
            doc = ChartDocument(assets, "songs/test/chart.json")
            doc.checkpoint()
            doc.data["speed"] = 2
            doc.undo()
            self.assertEqual(doc.data["speed"], 1)
            doc.undo(redo=True)
            doc.save()
            self.assertEqual(json.loads(doc.path.read_text())["speed"], 2)
            self.assertEqual(json.loads(source.read_text())["speed"], 1)
            doc.path.write_text("external edit")
            with self.assertRaises(ValueError):
                doc.save()

    def test_events_fire_once_in_time_order(self):
        shader = Mock()
        shader.get_uniform.return_value = 0.0
        game = SimpleNamespace(assets=AssetStore(), song_mgr=SimpleNamespace(song_ms=0), shader_mgr=shader)
        params = {"shader": "lens_distortion", "uniform": "strength", "value": 0.2, "duration": 0}
        manager = ChartEventManager(game, [{"time": 100, "script": "shader_value", "params": params}])
        manager.update()
        shader.set_uniform.assert_not_called()
        game.song_mgr.song_ms = 100
        manager.update()
        manager.update()
        shader.set_uniform.assert_called_once_with("lens_distortion", "strength", 0.2)

    def test_shader_event_lerps_and_retargets_from_current_value(self):
        shader = Mock()
        shader.get_uniform.return_value = 0.0
        song = SimpleNamespace(song_ms=0)
        params = {"shader": "lens_distortion", "uniform": "strength", "value": 1.0}
        game = SimpleNamespace(assets=AssetStore(), song_mgr=song, shader_mgr=shader)
        manager = ChartEventManager(game, [{"time": 0, "script": "shader_value", "params": params}])
        manager.update()
        shader.set_uniform.assert_not_called()
        song.song_ms = 250
        manager.update()
        shader.set_uniform.assert_called_with("lens_distortion", "strength", 0.5)
        shader.get_uniform.return_value = 0.5
        manager.scripts["shader_value"].on_event({**params, "value": 0})
        song.song_ms = 500
        manager.update()
        shader.set_uniform.assert_called_with("lens_distortion", "strength", 0.25)
        song.song_ms = 750
        manager.update()
        shader.set_uniform.assert_called_with("lens_distortion", "strength", 0)
        count = shader.set_uniform.call_count
        manager.update()
        self.assertEqual(shader.set_uniform.call_count, count)

    def test_grid_edit_and_render(self):
        window = arcade.Window(1280, 720, visible=False)
        self.addCleanup(window.close)
        arcade.load_font("assets/fonts/SeoulAlrimTTF-Medium.ttf")
        arcade.load_font("assets/fonts/SeoulAlrimTTF-Heavy.ttf")
        game = SimpleNamespace(window=window, assets=AssetStore(),
                               _song_data={"name": "test", "chart": "songs/test/chart.json"})
        editor = ChartEditor(game)
        before = len(editor.doc.data["notes"][0]["sectionNotes"])
        x, y, width, height = editor.geometry()
        editor.click(x + width / 18, y + height - 1, arcade.MOUSE_BUTTON_LEFT)
        self.assertEqual(len(editor.doc.data["notes"][0]["sectionNotes"]), before + 1)
        editor.key(arcade.key.EQUAL, 0)
        self.assertGreater(editor.selected[2], 0)
        editor.click(x + width * 8.5 / 9, y + height - 1, arcade.MOUSE_BUTTON_LEFT)
        self.assertEqual(editor.selected["script"], "shader_value")
        editor.draw()
        editor.key(arcade.key.DELETE, 0)
        self.assertEqual(editor.doc.data["events"], [])

    def test_fps_thresholds(self):
        self.assertEqual(fps_color(144, 240), (255, 177, 70))
        self.assertEqual(fps_color(140, 240), (245, 95, 100))
        self.assertEqual(fps_color(240, 240), (183, 219, 197))
