import math
import arcade
from sources.utils import *

BAR_WIDTH = 400
BAR_HEIGHT = 10
BAR_Y = 20
NAME_Y = 40
TIME_Y = 65
NAME_FONT_SIZE = 18
TIME_FONT_SIZE = 14

class TimebarInterface:
    def __init__(self, song_name):
        self._time_bar_bg = arcade.SpriteSolidColor(BAR_WIDTH, BAR_HEIGHT, arcade.get_window().width/2, arcade.get_window().height - BAR_Y, arcade.color.BLACK)
        self._time_bar_fg = arcade.SpriteSolidColor(BAR_WIDTH-2, BAR_HEIGHT-2, arcade.get_window().width/2, arcade.get_window().height - BAR_Y, arcade.color.WHITE)
        
        self._time_bar_name_text = arcade.Text(f"< {song_name} >", arcade.get_window().width/2, arcade.get_window().height - NAME_Y,
                                            arcade.color.WHITE, NAME_FONT_SIZE, font_name="Paperlogy 8", align="center", anchor_x="center", anchor_y="center")
        self._time_bar_time_text = arcade.Text("| 0:00 |", arcade.get_window().width/2, arcade.get_window().height - TIME_Y,
                                            arcade.color.WHITE, TIME_FONT_SIZE, font_name="Paperlogy 8", align="center", anchor_x="center", anchor_y="center")

        self._bar_sprites = arcade.SpriteList()
        self._bar_sprites.append(self._time_bar_bg)
        self._bar_sprites.append(self._time_bar_fg)

    def _update_bar_length(self, delta_time):
        from sources.views import MainGameView
        song_mgr = MainGameView.current.song_mgr

        if song_mgr.inst_player.source is not None:
            ratio = song_mgr.inst_player.time / song_mgr.inst_player.source.duration
            self._time_bar_fg.width = self._time_bar_bg.width * ratio

    def _update_time_text(self):
        from sources.views import MainGameView
        song_mgr = MainGameView.current.song_mgr
        
        minutes, seconds = divmod(song_mgr.inst_player.time, 60)
        self._time_bar_time_text.text = f"| {math.floor(minutes)}:{math.floor(seconds):02d} |"

    def update(self, delta_time):
        self._update_bar_length(delta_time)
        self._update_time_text()

    def draw(self):
        self._bar_sprites.draw()
        self._time_bar_name_text.draw()
        self._time_bar_time_text.draw()

class ScoreInterface:
    def __init__(self):
        self._score_text    = arcade.Text("Score : 0", 400, 25, arcade.color.WHITE, font_name="Paperlogy 8")
        self._accuracy_text = arcade.Text("Accuracy : 100%", 400, 5, arcade.color.WHITE, font_name="Paperlogy 8")

        bus.subscribe("score_updated", self._score_updated)

    def _score_updated(self, score, accuracy):
        self._score_text.text       = f"Score : {score}"
        self._accuracy_text.text    = f"Accuracy : {math.floor(accuracy):02d}%"

    def draw(self):
        self._score_text.draw()
        self._accuracy_text.draw()

class HealthInterface:
    def __init__(self, song_data):
        self.bg                     = arcade.SpriteSolidColor(500, 30, arcade.get_window().width/2, 60, arcade.color.BLACK)
        self._player_health_bar     = arcade.SpriteSolidColor(490, 20, arcade.get_window().width/2, 60, arcade.color.GREEN)
        self._opponent_health_bar   = arcade.SpriteSolidColor(490, 20, arcade.get_window().width/2, 60, arcade.color.RED)

        self._icons = {
            "opponent": {
                "normal": arcade.load_texture(f"assets/characters/{song_data['opponent_name']}/normal.png"),
                "defeat": arcade.load_texture(f"assets/characters/{song_data['opponent_name']}/defeat.png"),
                "win": arcade.load_texture(f"assets/characters/{song_data['opponent_name']}/win.png")
            },
            "player": {
                "normal": arcade.load_texture(f"assets/characters/{song_data['player_name']}/normal.png"),
                "defeat": arcade.load_texture(f"assets/characters/{song_data['player_name']}/defeat.png"),
                "win": arcade.load_texture(f"assets/characters/{song_data['player_name']}/win.png")
            }
        }
        
        self._opponent_icon = arcade.Sprite(self._icons["opponent"]["normal"])
        self._player_icon   = arcade.Sprite(self._icons["player"]["normal"])
        
        self._sprites = arcade.SpriteList()
        self._sprites.append(self.bg)
        self._sprites.append(self._opponent_health_bar)
        self._sprites.append(self._player_health_bar)
        self._sprites.append(self._opponent_icon)
        self._sprites.append(self._player_icon)

        self._health = 50.0

        bus.subscribe("score_updated", self._score_updated)
        bus.subscribe("beat", self._beat)

    def _score_updated(self, score, accuracy):
        from sources.views import MainGameView
        self._health = MainGameView.current.score_mgr._health
        self._update_icon()
    
    def _beat(self, beat, time):
        if beat % 2 == 0:
            self._player_icon.scale = arcade.Vec2(1, 1)
        else:
            self._opponent_icon.scale = arcade.Vec2(1, 1)

    def _update_icon(self):
        if self._health <= 20:
            self._player_icon.texture = self._icons["player"]["defeat"]
        elif self._health >= 80:
            self._player_icon.texture = self._icons["player"]["win"]
        else:
            self._player_icon.texture = self._icons["player"]["normal"]
            
        if self._health >= 80:
            self._opponent_icon.texture = self._icons["opponent"]["defeat"]
        elif self._health <= 20:
            self._opponent_icon.texture = self._icons["opponent"]["win"]
        else:
            self._opponent_icon.texture = self._icons["opponent"]["normal"]

    def update(self, delta_time):
        health_ratio = self._health / 100.0
        
        usable_width = self.bg.width - 10 
        
        self._player_health_bar.width = usable_width * health_ratio
        self._player_health_bar.right = self.bg.right - 5
        
        icon_x = self._player_health_bar.left
        
        self._opponent_icon.center_x = icon_x - 40
        self._opponent_icon.center_y = self.bg.center_y
        self._opponent_icon.scale = min(arcade.math.lerp_2d(self._opponent_icon.scale, arcade.Vec2(0.75, 0.75), delta_time * 10), 0.75)
        
        self._player_icon.center_x = icon_x + 40
        self._player_icon.center_y = self.bg.center_y
        self._player_icon.scale = min(arcade.math.lerp_2d(self._player_icon.scale, arcade.Vec2(0.75, 0.75), delta_time * 10), 0.75)

    def draw(self):
        self._sprites.draw()

class GameInterfaceManager:
    def __init__(self, song_data):
        self._data = song_data
        self._sprites = arcade.SpriteList()
        self._sprites.append(arcade.Sprite(arcade.load_texture("assets/ui/general/center_vignette.png"), scale=2, center_x=arcade.get_window().width/2, center_y=arcade.get_window().height/2))
        self._timebar = TimebarInterface(song_data["name"])
        self._score = ScoreInterface()
        self._health = HealthInterface(song_data)

    def update(self, delta_time):
        self._timebar.update(delta_time)
        self._health.update(delta_time)

    def draw(self):
        self._sprites.draw()
        self._timebar.draw()
        self._health.draw()
        self._score.draw()