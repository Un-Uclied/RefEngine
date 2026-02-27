import copy
import json
import time
import arcade
from sources.utils import *

class ReceptorManager:
    def __init__(self, receptor_name : str):
        with open(f"assets/ui/receptors/{receptor_name}/data.json", 'r') as f:
            data = json.load(f)

        loaded_animation = {"left" : {}, "down" : {}, "up" : {}, "right" : {}}
        for direction_name in ["left", "down", "up", "right"]:
            for animation_name in ["idle", "press", "confirm"]:
                loaded_animation[direction_name][animation_name] = arcade.load_animated_gif(data["animations"][direction_name][animation_name]).animation

        self.receptors = arcade.SpriteList()
        for actor_role in ["player", "opponent"]:
            for direction_name in ["left", "down", "up", "right"]:
                receptor = Receptor(
                    direction_index     =ReceptorManager.name_to_index(f"{actor_role}_{direction_name}"),
                    loaded_settings     =data["settings"][actor_role][direction_name],
                    loaded_animation    =copy.deepcopy(loaded_animation[direction_name])
                    )
                self.receptors.append(receptor)

        bus.subscribe("player_pressed", self._note_pressed)
        bus.subscribe("opponent_pressed", self._note_pressed)
        bus.subscribe("player_released", self._note_released)
        bus.subscribe("opponent_released", self._note_released)

    def on_hide_view(self):
        bus.unsubscribe("player_pressed", self._note_pressed)
        bus.unsubscribe("opponent_pressed", self._note_pressed)
        bus.unsubscribe("player_released", self._note_released)
        bus.unsubscribe("opponent_released", self._note_released)

    @staticmethod
    def index_to_name(index : int):
        return {
                0 : "player_left",
                1 : "player_down",
                2 : "player_up",
                3 : "player_right",
                4 : "opponent_left",
                5 : "opponent_down",
                6 : "opponent_up",
                7 : "opponent_right"
            }[index]
    @staticmethod
    def name_to_index(name : str):
        return {
                "player_left" : 0,
                "player_down" : 1,
                "player_up" : 2,
                "player_right" : 3,
                "opponent_left" : 4,
                "opponent_down" : 5,
                "opponent_up" : 6,
                "opponent_right" : 7,
            }[name]

    def _note_pressed(self, direction_index, note):
        if note is None:
            self.receptors[direction_index].set_animation("press")
        else:
            self.receptors[direction_index].set_animation("confirm")

    def _note_released(self, direction_index, **kwargs):
        self.receptors[direction_index].request_idle()

    def update(self, delta_time : float):
        from sources.views import MainGameView
        song_mgr = MainGameView.current.song_mgr

        for r in self.receptors:
            r.update(delta_time)
            r.update_from_song_time(song_mgr.song_ms)
            r.update_idle_transition()
    
    def draw(self):
        self.receptors.draw()
        
class Receptor(arcade.Sprite):
    PRESS_MIN_DISPLAY_MS = 80

    def __init__(self, direction_index, loaded_settings, loaded_animation):
        super().__init__()
        self.direction_index = direction_index
        self._loaded_settings = loaded_settings
        self._loaded_animation = loaded_animation

        self._current_animation = ""
        self._press_start_time = None
        self._pending_idle = False

        self.position = self._loaded_settings["position"]
        self.scale = self._loaded_settings["scale"]
        self.alpha = self._loaded_settings["alpha"]
        self.set_animation("idle")
        self.spawn_x, self.spawn_y = self.center_x, self.center_y

        self._update_texture(0)

    def set_animation(self, name: str):
        self._current_animation = name
        # record when press animation started
        if name == "press" or name == "confirm":
            self._press_start_time = time.time() * 1000  # ms
            self._pending_idle = False
        elif name == "idle":
            self._press_start_time = None
            self._pending_idle = False

    def request_idle(self):
        if self._current_animation in ["press", "confirm"]:
            self._pending_idle = True
        else:
            self.set_animation("idle")

    def update_idle_transition(self):
        if self._pending_idle and self._press_start_time is not None:
            elapsed = time.time() * 1000 - self._press_start_time
            if elapsed >= self.PRESS_MIN_DISPLAY_MS:
                self.set_animation("idle")

    def update_from_song_time(self, song_ms: float):
        anim = self._loaded_animation[self._current_animation]
        anim_time = (song_ms / 1000) * self._loaded_settings["speed"]

        index, keyframe = anim.get_keyframe(anim_time, loop=True)

        self.texture = keyframe.texture

    def _update_texture(self, time_sec):
        anim = self._loaded_animation[self._current_animation]
        index, keyframe = anim.get_keyframe(time_sec, loop=True)
        self.texture = keyframe.texture