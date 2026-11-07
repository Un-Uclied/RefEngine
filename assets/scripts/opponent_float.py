"""Make the current song's opponent float without changing animation offsets."""
import math

class SongScript:
    def __init__(self, game):
        self.game = game
        self.previous_offset = 0.0

    def on_update(self, delta_time):
        opponent = self.game.character_mgr.opponent
        seconds = self.game.song_mgr.song_ms / 1000
        offset = math.sin(seconds * math.tau * 0.7) * 70
        opponent.center_y += offset - self.previous_offset
        self.previous_offset = offset

    def on_hide(self):
        self.game.character_mgr.opponent.center_y -= self.previous_offset