import arcade
from .events import on_beat, on_note_pressed, on_opponent_pressed

BEAT_UI_CAMERA_ADD_ZOOM = 0.1
BEAT_NOTE_CAMERA_ADD_ZOOM = 0.15
BEAT_WORLD_CAMERA_ADD_ZOOM = 0.15

class CameraManager:
    def __init__(self, game_context, song_data : dict, background_data : dict):
        self.game_context = game_context
        self.camera_world = arcade.Camera2D()
        self.camera_note = arcade.Camera2D()
        self.camera_ui = arcade.Camera2D()

        self._spawn_camera_world_zoom = background_data["default_zoom"]
        self.camera_world.zoom = self._spawn_camera_world_zoom

        self._camera_target_position = arcade.Vec2()

        on_beat.connect(self._beat)
        on_note_pressed.connect(self._note_pressed)
        on_opponent_pressed.connect(self._note_pressed)

    def on_hide_view(self):
        on_beat.disconnect(self._beat)
        on_note_pressed.disconnect(self._note_pressed)
        on_opponent_pressed.disconnect(self._note_pressed)

    def _note_pressed(self, sender, direction_index, note):
        character_mgr = self.game_context.character_mgr
        song_mgr = self.game_context.song_mgr


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
        
    def _beat(self, sender, beat, ms):
        character_mgr = self.game_context.character_mgr
        song_mgr = self.game_context.song_mgr

        self.camera_target_position = character_mgr.player.camera_position if song_mgr.is_player_turn else character_mgr.opponent.camera_position

        self.camera_ui.zoom = 1 + BEAT_UI_CAMERA_ADD_ZOOM
        self.camera_note.zoom = 1 + BEAT_NOTE_CAMERA_ADD_ZOOM
        self.camera_world.zoom = self._spawn_camera_world_zoom + BEAT_WORLD_CAMERA_ADD_ZOOM

    def update(self, delta_time):
        self.camera_world.position = self.camera_world.position.lerp(
            self._camera_target_position,
            delta_time * 5)
    
        self.camera_world.zoom = min(arcade.math.lerp(self.camera_world.zoom, self._spawn_camera_world_zoom, delta_time), self._spawn_camera_world_zoom + BEAT_WORLD_CAMERA_ADD_ZOOM)
        self.camera_note.zoom = min(arcade.math.lerp(self.camera_note.zoom, 1, delta_time), 1 + BEAT_NOTE_CAMERA_ADD_ZOOM)
        self.camera_ui.zoom = min(arcade.math.lerp(self.camera_ui.zoom, 1, delta_time * 10), 1 + BEAT_UI_CAMERA_ADD_ZOOM)
