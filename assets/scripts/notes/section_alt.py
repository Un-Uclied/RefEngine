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
        if not (self.game.song_mgr.current_section_data or {}).get("altAnim", False):
            return
        character = (self.game.character_mgr.opponent if self.note.is_opponent
                     else self.game.character_mgr.player)
        alt = f"{self.note.character_animation}_alt"
        if alt in character.loaded_animations:
            self.note.character_animation = alt
