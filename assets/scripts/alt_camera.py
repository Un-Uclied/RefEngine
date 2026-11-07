"""Extra camera motion whenever the opponent performs an alt animation."""
import math

import arcade


class SongScript:
    def __init__(self, game):
        self.game = game
        game.camera_mgr.note_move_multiplier = self.note_move_multiplier

    def opponent_is_alt(self, direction_index=None, note=None):
        opponent = self.game.character_mgr.opponent
        if opponent.current_animation_name.endswith("_alt"):
            return True
        if note is None or direction_index < 4:
            return False
        direction = ("left", "down", "up", "right")[direction_index % 4]
        section = self.game.song_mgr.current_section_data or {}
        return (f"sing_{direction}_alt" in opponent.loaded_animations
                and (note.note_type == "alt_animation" or section.get("altAnim", False)))

    def note_move_multiplier(self, direction_index, note):
        return 1.8 if self.opponent_is_alt(direction_index, note) else 1.0

    def on_update(self, delta_time):
        camera = self.game.camera_mgr
        if self.opponent_is_alt():
            seconds = self.game.song_mgr.song_ms / 1000
            camera.shake_offset = arcade.Vec2(
                math.sin(seconds * 25) * 22,
                math.sin(seconds * 31) * 16,
            )
        else:
            camera.shake_offset = arcade.Vec2()
