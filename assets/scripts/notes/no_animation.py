from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sources.views.main_game import MainGameView
    from sources.game.note import Note

class NoteScript:
    def __init__(self, game: MainGameView, note: Note):
        note.character_animation = None
