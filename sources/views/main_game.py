import math

import arcade
import json
from sources.game import *
from sources.utils import *

class MainGameView(arcade.View):
    current : 'MainGameView' = None

    def __init__(self, song_name):
        super().__init__()

        with open(f"assets/songs/{song_name}/data.json", 'r') as f:
            self._song_data = json.load(f)
        with open("assets/config/score.json", 'r') as f:
            self._config_data = json.load(f)
        with open(f"assets/backgrounds/{self._song_data["background"]}/data.json", 'r') as f:
            self._background_data = json.load(f)
        with open("assets/config/judgements.json", 'r') as f:
            self._judgement_data = json.load(f)

    def on_show_view(self):
        MainGameView.current = self
        
        self.character_mgr  = SingerCharacterManager(self._song_data, self._background_data)
        self.receptor_mgr   = ReceptorManager(self._song_data["receptor_name"])
        self.note_mgr       = NoteManager(self._song_data)
        self.song_mgr       = SongManager(self._song_data)
        self.score_mgr      = ScoreManager(self._config_data)
        self.camera_mgr     = CameraManager(self._song_data, self._background_data)
        self.background_mgr = BackgroundManager(self._background_data)

        self.song_mgr.play()

        return super().on_show_view()
    
    def on_hide_view(self):
        self.character_mgr.on_hide_view()
        self.receptor_mgr.on_hide_view()
        self.score_mgr.on_hide_view()
        self.camera_mgr.on_hide_view()
    
        return super().on_hide_view()

    def on_update(self, delta_time):
        self.song_mgr.update()
        self.note_mgr.update(delta_time)
        self.receptor_mgr.update(delta_time)
        self.background_mgr.update(delta_time)
        self.character_mgr.update(delta_time)
        self.camera_mgr.update(delta_time)

    def on_draw(self):
        self.clear()
        with self.camera_mgr.camera_world.activate():
            self.background_mgr.draw_world()
            self.character_mgr.draw()
        with self.camera_mgr.camera_ui.activate():
            self.background_mgr.draw_camera()
            self.score_mgr.draw()
        with self.camera_mgr.camera_note.activate():
            self.receptor_mgr.draw()
            self.note_mgr.draw()
        
        arcade.draw_text(f"FPS : {math.floor(arcade.get_fps())}", 50, arcade.get_window().height - 50, arcade.color.GREEN, 24, bold=True)

    def on_key_press(self, key, modifiers):
        keys_arrow = {arcade.key.LEFT: 0, arcade.key.DOWN: 1, arcade.key.UP: 2, arcade.key.RIGHT: 3}
        keys_lane = {arcade.key.D: 0, arcade.key.F: 1, arcade.key.J: 2, arcade.key.K: 3}
        if key in keys_arrow:
            idx = keys_arrow[key]
            self.note_mgr.player_input_pressed(idx)
        if key in keys_lane:
            idx = keys_lane[key]
            self.note_mgr.player_input_pressed(idx)

    def on_key_release(self, key, modifiers):
        keys_arrow = {arcade.key.LEFT: 0, arcade.key.DOWN: 1, arcade.key.UP: 2, arcade.key.RIGHT: 3}
        keys_lane = {arcade.key.D: 0, arcade.key.F: 1, arcade.key.J: 2, arcade.key.K: 3}
        if key in keys_arrow:
            idx = keys_arrow[key]
            self.note_mgr.player_released(idx)
        if key in keys_lane:
            idx = keys_lane[key]
            self.note_mgr.player_released(idx)