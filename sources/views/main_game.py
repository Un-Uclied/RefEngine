import math
import runpy
import arcade
from sources.game import *
from sources.game.post_process import PostProcessManager
from sources.assets import AssetStore

class MainGameView(arcade.View):
    """Active song view and entry point for SongScript and NoteScript ``game``.

    Public manager attributes are ready before song scripts are constructed and
    before note instances spawn. ``assets`` uses the selected mod's overrides.

    SongScript와 NoteScript에 전달되는 ``game`` 객체입니다.
    공개 매니저 속성은 노래 스크립트 생성과 노트 스폰 전에 준비됩니다.
    ``assets``는 선택한 모드의 덮어쓰기를 적용합니다.
    """
    current : 'MainGameView' = None

    def __init__(self, song_name, prepared=None):
        super().__init__()
        self.character_mgr: SingerCharacterManager
        self.receptor_mgr: ReceptorManager
        self.note_mgr: NoteManager
        self.splash_mgr: SplashManager
        self.song_mgr: SongManager
        self.score_mgr: ScoreManager
        self.camera_mgr: CameraManager
        self.background_mgr: BackgroundManager
        self.game_interface_mgr: GameInterfaceManager
        self.shader_mgr: PostProcessManager | None = None
        self._ready = False
        self._fade_alpha = 0
        self._sounds = None
        if prepared is None:
            self.assets, song_name = AssetStore.for_song(song_name)
            self._song_data = self.assets.json(f"songs/{song_name}/data.json")
            self._score_data = self.assets.json("config/score.json")
            self._background_data = self.assets.json(f"backgrounds/{self._song_data['background']}/data.json")
            self._judgement_data = self.assets.json("config/judgements.json")
        else:
            (self.assets, song_name, self._song_data, self._score_data,
             self._background_data, self._judgement_data, self._sounds) = prepared

    def on_show_view(self):
        MainGameView.current = self
        if not self._ready:
            for _ in self.load_steps():
                pass
            self.on_draw()
            self._ready = True
        if self._fade_alpha == 0:
            self.song_mgr.play()
        return super().on_show_view()

    def load_steps(self):
        """Build managers on the render thread, yielding labels for the loading UI.

        렌더 스레드에서 매니저를 단계별로 만들고 로딩 화면에 표시할 이름을 내보냅니다.
        """
        self.character_mgr  = SingerCharacterManager(self, self._song_data, self._background_data, self.assets)
        yield "Characters"
        for _ in self.character_mgr.preload_textures():
            yield "Character textures"
        self.receptor_mgr   = ReceptorManager(self, self._song_data["receptor_name"], self.assets)
        yield "Receptors"
        self.note_mgr       = NoteManager(self, self._song_data, self._judgement_data, is_bot_play=False)
        yield "Notes"
        self.splash_mgr     = SplashManager(self, self._song_data["splash_name"], self.assets)
        yield "Splashes"
        self.song_mgr       = SongManager(self._song_data, self.assets, self._sounds)
        yield "Music"
        self.score_mgr      = ScoreManager(self._score_data)
        self.camera_mgr     = CameraManager(self, self._song_data, self._background_data)
        self.background_mgr = BackgroundManager(self._background_data, self.assets)
        self.game_interface_mgr = GameInterfaceManager(self, self._song_data, self.assets)
        yield "Scene"
        if "shaders" in self._song_data:
            self.shader_mgr = PostProcessManager(self._song_data["shaders"], self.assets)
            yield "Shaders"
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
        yield "Scripts"
        self._start_pos = arcade.get_window().get_location()
    
    def on_hide_view(self):
        self.song_mgr.stop()
        for script in reversed(self.song_scripts):
            if hasattr(script, "on_hide"):
                script.on_hide()
        self.note_mgr.on_hide_view()
        self.character_mgr.on_hide_view()
        self.receptor_mgr.on_hide_view()
        self.splash_mgr.on_hide_view()
        self.score_mgr.on_hide_view()
        self.camera_mgr.on_hide_view()
        self.game_interface_mgr.on_hide_view()
        if self.shader_mgr is not None:
            self.shader_mgr.on_hide_view()
        self._ready = False
    
        return super().on_hide_view()

    def on_update(self, delta_time):
        if self._fade_alpha:
            self._fade_alpha = max(0, self._fade_alpha - delta_time * 850)
            if not self._fade_alpha:
                self.song_mgr.play()
            return
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

        arcade.get_window().set_location(int(self._start_pos[0] + math.cos(self.song_mgr.song_ms / 1000 * 5) * 100), int(self._start_pos[1] + math.sin(self.song_mgr.song_ms / 1000 * 5) * 100))
        for receptor in self.receptor_mgr.receptors:
            receptor.position = (receptor.spawn_x + math.cos(self.song_mgr.song_ms / 1000 * 2 + receptor.direction_index) * 15, receptor.spawn_y + math.sin(self.song_mgr.song_ms / 1000 * 2 + receptor.direction_index) * 15)
            receptor.angle = math.sin(self.song_mgr.song_ms / 1000 * 5 + receptor.direction_index) * 15 + math.cos(self.song_mgr.song_ms / 1000 * 3 + receptor.direction_index) * 10

    def on_draw(self):
        if self.shader_mgr is not None and self.shader_mgr.effects:
            self.shader_mgr.begin()
        else:
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
        if self.shader_mgr is not None and self.shader_mgr.effects:
            self.shader_mgr.finish()
        if self._fade_alpha:
            window = arcade.get_window()
            arcade.draw_lbwh_rectangle_filled(0, 0, window.width, window.height, (0, 0, 0, int(self._fade_alpha)))

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
