import arcade
import json
from sources.utils import *

IDLE_DELAY = .1

class SingerCharacterManager:
    def __init__(self, song_data, background_data):
        self.player     = SingerCharacter(song_data["player_name"],
                                            background_data["player"]["position"][0], background_data["player"]["position"][1],
                                            background_data["player"]["scale"])
        self.opponent   = SingerCharacter(song_data["opponent_name"],
                                            background_data["opponent"]["position"][0], background_data["opponent"]["position"][1],
                                            background_data["opponent"]["scale"])
        if not (song_data["sub_character_name"] is None) and not (song_data["sub_character_name"] == ""):
            self.sub_character = SingerCharacter(song_data["sub_character_name"],
                                      background_data["sub_character"]["position"][0], background_data["sub_character"]["position"][1],
                                    background_data["sub_character"]["scale"])
        
        self._character_spritelist = arcade.SpriteList()
        self._character_spritelist.append(self.player)
        self._character_spritelist.append(self.opponent)
        self._character_spritelist.append(self.sub_character)

        self._should_player_go_idle = True
        self._should_opponent_go_idle = True
        self._player_idle_timer = 0.0
        self._opponent_idle_timer = 0.0

        bus.subscribe("beat", self._beat)
        bus.subscribe("player_pressed", self._note_pressed)
        bus.subscribe("opponent_pressed", self._note_pressed)
        bus.subscribe("player_released", self._player_released)
        bus.subscribe("opponent_released", self._opponent_released)

    def on_hide_view(self):
        bus.unsubscribe("beat", self._beat)
        bus.unsubscribe("player_pressed", self._note_pressed)
        bus.unsubscribe("opponent_pressed", self._note_pressed)
        bus.unsubscribe("player_released", self._player_released)
        bus.unsubscribe("opponent_released", self._opponent_released)

    def _note_pressed(self, direction_index, note):
        if note is None:
            return
        from sources.views import MainGameView

        anim = ["sing_left", "sing_down", "sing_up", "sing_right"][direction_index % 4]
        if direction_index < 4:
            if f"{anim}_alt" in self.player.loaded_animations and (getattr(note, "note_type", "") == "alt_animation" or MainGameView.current.song_mgr.current_section_data.get("altAnim", False)):
                anim = f"{anim}_alt"
            self.player.play_animation(anim)
            self._should_player_go_idle = False
        if direction_index >= 4:
            if f"{anim}_alt" in self.opponent.loaded_animations and (getattr(note, "note_type", "") == "alt_animation" or MainGameView.current.song_mgr.current_section_data.get("altAnim", False)):
                anim = f"{anim}_alt"
            self.opponent.play_animation(anim)
            self._should_opponent_go_idle = False
            
    def _player_released(self, direction_index):
        self._should_player_go_idle = True
        self._player_idle_timer = IDLE_DELAY
    
    def _opponent_released(self, direction_index):
        self._should_opponent_go_idle = True
        self._opponent_idle_timer = IDLE_DELAY

    def _beat(self, beat: int, time: float):
        self._advance_sprite(self.player, self._should_player_go_idle, self._player_idle_timer)
        self._advance_sprite(self.opponent, self._should_opponent_go_idle, self._opponent_idle_timer)

        if self.sub_character is not None:
            self._advance_sprite(self.sub_character, True, 0)

    def _advance_sprite(self, sprite, should_go_idle: bool, timer: float):
        is_animation_end = sprite._current_keyframe_index >= sprite.animation.num_frames - 1
        if not is_animation_end:
            return

        if should_go_idle:
            if timer <= 0:
                sprite.play_animation("idle")
        else:
            sprite.play_animation(sprite.current_animation_name)

    def update(self, delta_time) : 
        if self._player_idle_timer > 0:
            self._player_idle_timer -= delta_time
        if self._opponent_idle_timer > 0:
            self._opponent_idle_timer -= delta_time

        self._character_spritelist.update(delta_time)
        self._character_spritelist.update_animation(delta_time)

    def draw(self):
        self._character_spritelist.draw()

class SingerCharacter(arcade.TextureAnimationSprite):
    def __init__(self, name : str, center_x : float, center_y : float, scale : float):
        with open(f"assets/characters/{name}/data.json", 'r', encoding='utf-8') as f:
            self._data : dict = json.load(f)

        self.name = name
        self.loaded_animations = {
            anim_name: arcade.load_animated_gif(self._data["animations"][anim_name]["path"]).animation
            for anim_name in self._data.get("animations", {})
        }

        self.current_animation_name = None
        self._should_loop = False
        super().__init__(center_x, center_y, scale * self._data["scale"], None)
        self.play_animation("idle")

    @property
    def camera_position(self):
        return arcade.Vec2(self.center_x + self._data["camera_offset"][0], self.center_y + self._data["camera_offset"][1])

    def play_animation(self, name : str):
        if not name in self.loaded_animations:
            print(f"Error: Animation '{name}' not found for character '{self.name}'")
            return
        
        self.center_x -= self._data["animations"].get(self.current_animation_name, {}).get("offset", [0, 0])[0] if self.current_animation_name else 0
        self.center_y -= self._data["animations"].get(self.current_animation_name, {}).get("offset", [0, 0])[1] if self.current_animation_name else 0

        self.time = 0
        self._current_keyframe_index = 0
        self.current_animation_name = name
        self.animation = self.loaded_animations[self.current_animation_name]
        self._should_loop = self._data["animations"][self.current_animation_name].get("loop", False)
        
        self.center_x += self._data["animations"][self.current_animation_name].get("offset", [0, 0])[0]
        self.center_y += self._data["animations"][self.current_animation_name].get("offset", [0, 0])[1]

    def update_animation(self, delta_time, *args, **kwargs):
        if not self.animation:
            return
        if self._should_loop:
            return super().update_animation(delta_time, *args, **kwargs)
        else:
            if self._current_keyframe_index < len(self.animation.keyframes) - 1:
                return super().update_animation(delta_time, *args, **kwargs)