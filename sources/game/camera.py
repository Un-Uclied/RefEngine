import arcade
from sources.utils import *

class CameraManager:
    def __init__(self, song_data : dict, background_data : dict):
        self.camera_world = arcade.Camera2D()
        self.camera_note = arcade.Camera2D()
        self.camera_ui = arcade.Camera2D()

        self._spawn_camera_world_zoom = background_data["default_zoom"]
        self.camera_world.zoom = self._spawn_camera_world_zoom

        self._camera_target_position = arcade.Vec2()
        bus.subscribe("beat", self._beat)
        bus.subscribe("player_pressed", self._note_pressed)
        bus.subscribe("opponent_pressed", self._note_pressed)

    def on_hide_view(self):
        bus.unsubscribe("beat", self._beat)
        bus.unsubscribe("player_pressed", self._note_pressed)
        bus.unsubscribe("opponent_pressed", self._note_pressed)

    def _note_pressed(self, direction_index, note):
        from sources.views import MainGameView
        character_mgr = MainGameView.current.character_mgr
        song_mgr = MainGameView.current.song_mgr


        if direction_index < 3:
            if note is not None:
                if character_mgr.player.current_animation_name in ["sing_left_alt", "sing_down_alt", "sing_up_alt", "sing_right_alt"]:
                    amount = 85
                else:
                    amount = 50
                self._camera_target_position = character_mgr.player.camera_position if song_mgr.is_player_turn else character_mgr.opponent.camera_position
                self._camera_target_position += [arcade.Vec2(-amount, 0), arcade.Vec2(0, -amount), arcade.Vec2(0, amount), arcade.Vec2(amount, 0)][direction_index % 4]
        else:
            if character_mgr.opponent.current_animation_name in ["sing_left_alt", "sing_down_alt", "sing_up_alt", "sing_right_alt"]:
                amount = 85
            else:
                amount = 50
            self._camera_target_position = character_mgr.player.camera_position if song_mgr.is_player_turn else character_mgr.opponent.camera_position
            self._camera_target_position += [arcade.Vec2(-amount, 0), arcade.Vec2(0, -amount), arcade.Vec2(0, amount), arcade.Vec2(amount, 0)][direction_index % 4]
        
    def _beat(self, beat, time):
        from sources.views import MainGameView
        character_mgr = MainGameView.current.character_mgr
        song_mgr = MainGameView.current.song_mgr

        self.camera_target_position = character_mgr.player.camera_position if song_mgr.is_player_turn else character_mgr.opponent.camera_position

    def update(self, delta_time):
        self.camera_world.position = self.camera_world.position.lerp(
            self._camera_target_position,
            delta_time * 5)
    
        self.camera_world.zoom = arcade.math.lerp(self.camera_world.zoom, self._spawn_camera_world_zoom, delta_time)
        self.camera_note.zoom = arcade.math.lerp(self.camera_note.zoom, 1, delta_time)