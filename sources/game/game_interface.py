import math, arcade

from .events import on_score_changed, on_beat, on_note_pressed

BAR_WIDTH = 400
BAR_HEIGHT = 10
BAR_Y = 20
NAME_Y = 40
TIME_Y = 65
NAME_FONT_SIZE = 18
TIME_FONT_SIZE = 14

class TimebarInterface:
    def __init__(self, game_context, song_name):
        self.game_context = game_context
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
        song_mgr = self.game_context.song_mgr

        if song_mgr.inst_player.source is not None:
            ratio = song_mgr.inst_player.time / song_mgr.inst_player.source.duration
            self._time_bar_fg.width = self._time_bar_bg.width * ratio

    def _update_time_text(self):
        song_mgr = self.game_context.song_mgr
        
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
    def __init__(self, game_context):
        self.game_context = game_context
        self._score_text    = arcade.Text("Score : 0", 400, 25, arcade.color.WHITE, font_name="Paperlogy 8")
        self._accuracy_text = arcade.Text("Accuracy : 100%", 400, 5, arcade.color.WHITE, font_name="Paperlogy 8")
        self._bot_play_text = arcade.Text("[ BOT PLAY ENABLED ]", arcade.get_window().width/2, arcade.get_window().height - 120, arcade.color.RED, font_name="Paperlogy 8", anchor_x="center", anchor_y="center", align="center", font_size=20)

        on_score_changed.connect(self._score_updated)

    def _score_updated(self, sender, score, accuracy):
        self._score_text.text       = f"Score : {score}"
        self._accuracy_text.text    = f"Accuracy : {math.floor(accuracy):02d}%"

    def draw(self):

        self._score_text.draw()
        self._accuracy_text.draw()
        if self.game_context.note_mgr.is_bot_play:
            self._bot_play_text.draw()

class HealthInterface:
    def __init__(self, game_context, song_data, assets):
        self.game_context = game_context
        self.bg                     = arcade.SpriteSolidColor(500, 30, arcade.get_window().width/2, 60, arcade.color.BLACK)
        self._player_health_bar     = arcade.SpriteSolidColor(490, 20, arcade.get_window().width/2, 60, arcade.color.GREEN)
        self._opponent_health_bar   = arcade.SpriteSolidColor(490, 20, arcade.get_window().width/2, 60, arcade.color.RED)

        self._icons = {
            "opponent": {
                "normal": assets.image(f"characters/{song_data['opponent_name']}/normal.png"),
                "defeat": assets.image(f"characters/{song_data['opponent_name']}/defeat.png"),
                "win": assets.image(f"characters/{song_data['opponent_name']}/win.png")
            },
            "player": {
                "normal": assets.image(f"characters/{song_data['player_name']}/normal.png"),
                "defeat": assets.image(f"characters/{song_data['player_name']}/defeat.png"),
                "win": assets.image(f"characters/{song_data['player_name']}/win.png")
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

        on_score_changed.connect(self._score_updated)
        on_beat.connect(self._beat)

    def _score_updated(self, sender, score, accuracy):
        self._health = self.game_context.score_mgr._health
        self._update_icon()
    
    def _beat(self, sender, beat, ms):
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
        self._opponent_icon.scale = min(arcade.math.lerp_2d(self._opponent_icon.scale, arcade.Vec2(0.75, 0.75), delta_time * 10), arcade.Vec2(1, 1))
        
        self._player_icon.center_x = icon_x + 40
        self._player_icon.center_y = self.bg.center_y
        self._player_icon.scale = min(arcade.math.lerp_2d(self._player_icon.scale, arcade.Vec2(0.75, 0.75), delta_time * 10), arcade.Vec2(1, 1))

    def draw(self):
        self._sprites.draw()

class JudgementInterface:
    def __init__(self):
        self._judgement_sprite = None
        self._prev_judgement = None

        self._sprite_list = arcade.SpriteList()

        on_note_pressed.connect(self._player_pressed)

    def _player_pressed(self, sender, direction_index, note):
        if note is None:
            return
        if not note.judgement == self._prev_judgement:
            self._sprite_list.clear()
            self._judgement_sprite = arcade.create_text_sprite(note.judgement.upper(), arcade.color.WHITE, font_size=24, font_name="Paperlogy 8", bold=True, background_color=arcade.color.TRANSPARENT_BLACK)
            self._sprite_list.append(self._judgement_sprite)
            self._judgement_sprite.position = (arcade.get_window().width / 2, arcade.get_window().height - 100)
    
        self._judgement_sprite.scale = 1.5
        self._prev_judgement = note.judgement

    def update(self, delta_time):
        if self._judgement_sprite is not None:
            self._judgement_sprite.scale = arcade.math.lerp_2d(self._judgement_sprite.scale, arcade.Vec2(0, 0), delta_time * 5)

    def draw(self):
        self._sprite_list.draw()

class GameInterfaceManager:
    def __init__(self, game_context, song_data, assets):
        self._data = song_data
        self._sprites = arcade.SpriteList()
        self._sprites.append(arcade.Sprite(assets.image("ui/general/center_vignette.png"), scale=2, center_x=arcade.get_window().width/2, center_y=arcade.get_window().height/2))
        self._timebar = TimebarInterface(game_context, song_data["name"])
        self._score = ScoreInterface(game_context)
        self._health = HealthInterface(game_context, song_data, assets)
        self._judgement = JudgementInterface()

    def on_hide_view(self):
        on_score_changed.disconnect(self._score._score_updated)
        on_score_changed.disconnect(self._health._score_updated)
        on_beat.disconnect(self._health._beat)
        on_note_pressed.disconnect(self._judgement._player_pressed)

    def update(self, delta_time):
        self._timebar.update(delta_time)
        self._health.update(delta_time)
        self._judgement.update(delta_time)

    def draw(self):
        self._sprites.draw()
        self._timebar.draw()
        self._health.draw()
        self._score.draw()
        self._judgement.draw()
