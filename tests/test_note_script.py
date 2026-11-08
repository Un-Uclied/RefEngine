import runpy
import unittest
from types import SimpleNamespace

from sources.assets import AssetStore


def load_script(name):
    return runpy.run_path(str(AssetStore().path(f"scripts/notes/{name}.py")))["NoteScript"]


class NoteScriptTest(unittest.TestCase):
    def test_builtin_note_effects(self):
        player = SimpleNamespace(loaded_animations={"sing_left_alt": object()})
        opponent = SimpleNamespace(loaded_animations={})
        game = SimpleNamespace(
            character_mgr=SimpleNamespace(player=player, opponent=opponent),
            song_mgr=SimpleNamespace(current_section_data={"altAnim": True}),
            score_mgr=SimpleNamespace(health=50),
        )
        note = SimpleNamespace(is_opponent=False, character_animation="sing_left")

        load_script("section_alt")(game, note).on_hit()
        self.assertEqual(note.character_animation, "sing_left_alt")
        note.character_animation = "sing_left"
        game.song_mgr.current_section_data = {"altAnim": False}
        load_script("alt_animation")(game, note).on_hit()
        self.assertEqual(note.character_animation, "sing_left_alt")

        note.character_animation = "sing_left"
        note.is_opponent = True
        load_script("alt_animation")(game, note).on_hit()
        self.assertEqual(note.character_animation, "sing_left")
        note.is_opponent = False
        load_script("no_animation")(game, note)
        self.assertIsNone(note.character_animation)

        load_script("flame_note")(game, note).on_hit()
        self.assertEqual(game.score_mgr.health, 45)
        note.is_opponent = True
        load_script("flame_note")(game, note).on_hit()
        self.assertEqual(game.score_mgr.health, 45)
