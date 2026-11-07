import json
import tempfile
import unittest
from pathlib import Path

from sprite_generator import ROOT, extra_fields, number, save_character


class SpriteGeneratorTest(unittest.TestCase):
    def test_creates_character_data_and_copies_alt_gif(self):
        gif = ROOT / "assets/ui/receptors/default/left.gif"
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            root = Path(directory)
            self.assertTrue(root.resolve().is_relative_to(ROOT.resolve()))
            (root / "assets/characters").mkdir(parents=True)
            animations = {
                "idle": {"file": gif, "speed": 1.0, "offset": [0, 0], "loop": True, "extra": {}},
                "sing_left_alt": {"file": gif, "speed": 1.5, "offset": [4, -2], "loop": False, "extra": {"tag": "alt"}},
            }
            root_json, character_dir = save_character(root, "example", "test", True, 0.5, [3, 6], animations, {"custom": 7})
            data = json.loads(root_json.read_text(encoding="utf-8"))
            self.assertEqual(data, json.loads((character_dir / "data.json").read_text(encoding="utf-8")))
            self.assertEqual(data["animations"]["sing_left_alt"]["animation_speed"], 1.5)
            self.assertEqual(data["animations"]["sing_left_alt"]["path"], "assets/characters/example/sing_left_alt.gif")
            self.assertEqual(data["animations"]["sing_left_alt"]["tag"], "alt")
            self.assertTrue((character_dir / "sing_left_alt.gif").is_file())
            with self.assertRaises(FileExistsError):
                save_character(root, "example", "test", True, 0.5, [3, 6], animations, {})

    def test_rejects_invalid_extra_fields_and_speed(self):
        with self.assertRaises(ValueError):
            extra_fields('{"path": "wrong"}', {"path"})
        with self.assertRaises(ValueError):
            number("0", "Speed", positive=True)
