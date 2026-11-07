import math
import runpy
import arcade
from sources.game import *
from sources.assets import AssetStore

class MainGameView(arcade.View):
    current : 'MainGameView' = None

    def __init__(self, song_name):
        super().__init__()

        self.assets, song_name = AssetStore.for_song(song_name)
        self._song_data = self.assets.json(f"songs/{song_name}/data.json")
        self._score_data = self.assets.json("config/score.json")
        self._background_data = self.assets.json(f"backgrounds/{self._song_data['background']}/data.json")
        self._judgement_data = self.assets.json("config/judgements.json")

    def on_show_view(self):
        MainGameView.current = self
        
        self.character_mgr  = SingerCharacterManager(self, self._song_data, self._background_data, self.assets)
        self.receptor_mgr   = ReceptorManager(self, self._song_data["receptor_name"], self.assets)
        self.note_mgr       = NoteManager(self, self._song_data, self._judgement_data, is_bot_play=False)
        self.splash_mgr     = SplashManager(self, self._song_data["splash_name"], self.assets)
        self.song_mgr       = SongManager(self._song_data, self.assets)
        self.score_mgr      = ScoreManager(self._score_data)
        self.camera_mgr     = CameraManager(self, self._song_data, self._background_data)
        self.background_mgr = BackgroundManager(self._background_data, self.assets)
        self.game_interface_mgr = GameInterfaceManager(self, self._song_data, self.assets)
        script_names = self._song_data.get("scripts")
        if script_names is None:
            script_names = [self._song_data["script"]] if self._song_data.get("script") else []
        if not isinstance(script_names, list):
            raise ValueError("Song 'scripts' must be a list of script names")
        self.song_scripts = []
        for script_name in script_names:
            if not isinstance(script_name, str):
                raise ValueError("Song script names must be strings")
            self.assets._check_name(script_name)
            script = runpy.run_path(str(self.assets.path(f"scripts/{script_name}.py")))["SongScript"]
            self.song_scripts.append(script(self))

        self.song_mgr.play()

        self._start_pos = arcade.get_window().get_location()

        return super().on_show_view()
    
    def on_hide_view(self):
        self.song_mgr.stop()
        for script in reversed(self.song_scripts):
            if hasattr(script, "on_hide"):
                script.on_hide()
        self.character_mgr.on_hide_view()
        self.receptor_mgr.on_hide_view()
        self.splash_mgr.on_hide_view()
        self.score_mgr.on_hide_view()
        self.camera_mgr.on_hide_view()
        self.game_interface_mgr.on_hide_view()
    
        return super().on_hide_view()

    def on_update(self, delta_time):
        self.song_mgr.update()
        self.note_mgr.update(delta_time)
        self.splash_mgr.update(delta_time)
        self.receptor_mgr.update(delta_time)
        self.background_mgr.update(delta_time)
        self.character_mgr.update(delta_time)
        for script in self.song_scripts:
            script.on_update(delta_time)
        self.camera_mgr.update(delta_time)
        self.game_interface_mgr.update(delta_time)

        # arcade.get_window().set_location(int(self._start_pos[0] + math.cos(self.song_mgr.song_ms / 1000 * 5) * 100), int(self._start_pos[1] + math.sin(self.song_mgr.song_ms / 1000 * 5) * 100))
        # for receptor in self.receptor_mgr.receptors:
            # receptor.position = (receptor.spawn_x + math.cos(self.song_mgr.song_ms / 1000 * 2 + receptor.direction_index) * 15, receptor.spawn_y + math.sin(self.song_mgr.song_ms / 1000 * 2 + receptor.direction_index) * 15)
            # receptor.angle = math.sin(self.song_mgr.song_ms / 1000 * 5 + receptor.direction_index) * 15 + math.cos(self.song_mgr.song_ms / 1000 * 3 + receptor.direction_index) * 10

    def on_draw(self):
        self.clear()
        with self.camera_mgr.camera_world.activate():
            self.background_mgr.draw_world()
            self.character_mgr.draw()
        with self.camera_mgr.camera_ui.activate():
            self.background_mgr.draw_camera()
            self.game_interface_mgr.draw()
        with self.camera_mgr.camera_note.activate():
            self.receptor_mgr.draw()
            self.note_mgr.draw()
            self.splash_mgr.draw()
        
        arcade.draw_text(f"FPS : {math.floor(arcade.get_fps())}", 20, arcade.get_window().height - 20, arcade.color.GREEN, 24, bold=False)

    def on_key_press(self, key, modifiers):
        if key in (arcade.key.MINUS, arcade.key.NUM_SUBTRACT):
            self.song_mgr.change_volume(-10)
            return
        if key in (arcade.key.PLUS, arcade.key.EQUAL, arcade.key.NUM_ADD):
            self.song_mgr.change_volume(10)
            return
        if self.note_mgr.is_bot_play:
            return
        keys_arrow = {arcade.key.LEFT: 0, arcade.key.DOWN: 1, arcade.key.UP: 2, arcade.key.RIGHT: 3}
        keys_lane = {arcade.key.D: 0, arcade.key.F: 1, arcade.key.J: 2, arcade.key.K: 3}
        if key in keys_arrow:
            idx = keys_arrow[key]
            self.note_mgr.on_key_press(idx)
        if key in keys_lane:
            idx = keys_lane[key]
            self.note_mgr.on_key_press(idx)

    def on_key_release(self, key, modifiers):
        if self.note_mgr.is_bot_play:
            return
        keys_arrow = {arcade.key.LEFT: 0, arcade.key.DOWN: 1, arcade.key.UP: 2, arcade.key.RIGHT: 3}
        keys_lane = {arcade.key.D: 0, arcade.key.F: 1, arcade.key.J: 2, arcade.key.K: 3}
        if key in keys_arrow:
            idx = keys_arrow[key]
            self.note_mgr.on_key_release(idx)
        if key in keys_lane:
            idx = keys_lane[key]
            self.note_mgr.on_key_release(idx)
