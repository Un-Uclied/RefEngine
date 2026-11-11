import arcade
from .events import on_beat, on_note_pressed, on_opponent_pressed

class CameraManager:
    """Control world, note and HUD cameras during beats and note hits.

    Scripts can set ``shake_offset`` to a world-space Vec2. Set
    ``note_move_multiplier`` to a callable ``(direction_index, note) -> float``
    to scale the camera's movement on note hits; the default returns 1.0.

    비트와 노트 히트에 맞춰 월드·노트·HUD 카메라를 제어합니다.
    스크립트에서 ``shake_offset``에 월드 좌표 Vec2를 넣어 흔들림을 줄 수 있습니다.
    ``note_move_multiplier``에는 ``(direction_index, note) -> float`` 함수를
    지정해 노트 히트 시 이동량을 배율로 조절합니다. 기본값은 1.0입니다.
    """
    def __init__(self, game_context, song_data : dict, background_data : dict):
        self.game_context = game_context
        self.camera_world = arcade.Camera2D()
        self.camera_note = arcade.Camera2D()
        self.camera_ui = arcade.Camera2D()

        self.camera_world.zoom = background_data["default_zoom"]

        self._camera_target_position = arcade.Vec2()
        self._camera_position = arcade.Vec2()
        self.shake_offset = arcade.Vec2()
        self.note_move_multiplier = lambda direction_index, note: 1.0

        on_beat.connect(self._beat)
        on_note_pressed.connect(self._note_pressed)
        on_opponent_pressed.connect(self._note_pressed)

    def on_hide_view(self):
        on_beat.disconnect(self._beat)
        on_note_pressed.disconnect(self._note_pressed)
        on_opponent_pressed.disconnect(self._note_pressed)

    def _note_pressed(self, sender, direction_index, note):
        if note is None:
            return
        character_mgr = self.game_context.character_mgr
        song_mgr = self.game_context.song_mgr

        character = character_mgr.player if direction_index < 4 else character_mgr.opponent
        amount = 85 if character.current_animation_name in ["sing_left_alt", "sing_down_alt", "sing_up_alt", "sing_right_alt"] else 50
        amount *= self.note_move_multiplier(direction_index, note)
        self._camera_target_position = character_mgr.player.camera_position if song_mgr.is_player_turn else character_mgr.opponent.camera_position
        self._camera_target_position += [arcade.Vec2(-amount, 0), arcade.Vec2(0, -amount), arcade.Vec2(0, amount), arcade.Vec2(amount, 0)][direction_index % 4]
        
    def _beat(self, sender, beat, ms):
        character_mgr = self.game_context.character_mgr
        song_mgr = self.game_context.song_mgr

        self._camera_target_position = character_mgr.player.camera_position if song_mgr.is_player_turn else character_mgr.opponent.camera_position

    def update(self, delta_time):
        self._camera_position = self._camera_position.lerp(
            self._camera_target_position,
            delta_time * 5)
        self.camera_world.position = self._camera_position + self.shake_offset
