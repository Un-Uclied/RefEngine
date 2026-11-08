import copy, arcade, time
from .events import on_note_pressed, on_note_released, on_opponent_pressed, on_opponent_released

PRESS_MIN_DISPLAY_MS = 80

class ReceptorManager:
    """Own eight receptor sprites in player-then-opponent lane order.

    ``receptors[0:4]`` are player lanes, ``receptors[4:8]`` are opponent lanes;
    each group is ordered left, down, up, right.

    리셉터 8개를 플레이어·상대 순서로 관리합니다.
    ``receptors[0:4]``는 플레이어, ``receptors[4:8]``은 상대 레인이며
    각 그룹의 방향 순서는 왼쪽·아래·위·오른쪽입니다.
    """
    def __init__(self, game_context, receptor_name : str, assets):
        self.game_context = game_context
        data = assets.json(f"ui/receptors/{receptor_name}/data.json")

        loaded_animation = {"left" : {}, "down" : {}, "up" : {}, "right" : {}}
        for direction_name in ["left", "down", "up", "right"]:
            for animation_name in ["idle", "press", "confirm"]:
                loaded_animation[direction_name][animation_name] = assets.image(data["animations"][direction_name][animation_name])

        self.receptors = arcade.SpriteList()
        for actor_role in ["player", "opponent"]:
            for direction_name in ["left", "down", "up", "right"]:
                receptor = Receptor(
                    direction_index     =ReceptorManager.name_to_index(f"{actor_role}_{direction_name}"),
                    loaded_settings     =data["settings"][actor_role][direction_name],
                    loaded_animation    =copy.deepcopy(loaded_animation[direction_name])
                    )
                self.receptors.append(receptor)

        on_note_pressed.connect(self._note_pressed)
        on_note_released.connect(self._note_released)
        on_opponent_pressed.connect(self._note_pressed)
        on_opponent_released.connect(self._note_released)

    def on_hide_view(self):
        on_note_pressed.disconnect(self._note_pressed)
        on_note_released.disconnect(self._note_released)
        on_opponent_pressed.disconnect(self._note_pressed)
        on_opponent_released.disconnect(self._note_released)

    @staticmethod
    def index_to_name(index : int):
        """Convert a lane index such as 4 to ``opponent_left``.

        4 같은 레인 번호를 ``opponent_left`` 같은 이름으로 바꿉니다.
        """
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
        """Convert a name such as ``player_up`` to its lane index.

        ``player_up`` 같은 이름을 레인 번호로 바꿉니다.
        """
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

    def _note_pressed(self, sender, direction_index, note):
        if note is None:
            self.receptors[direction_index].set_animation("press")
        else:
            self.receptors[direction_index].set_animation("confirm")

    def _note_released(self, sender, direction_index, **kwargs):
        self.receptors[direction_index].request_idle()

    def update(self, delta_time : float):
        song_mgr = self.game_context.song_mgr

        for r in self.receptors:
            r.update(delta_time)
            r.update_from_song_time(song_mgr.song_ms)
            r.update_idle_transition()
    
    def draw(self):
        self.receptors.draw()
        
class Receptor(arcade.Sprite):
    """One arrow target with idle, press and confirm animations.

    ``spawn_x`` and ``spawn_y`` retain its initial position for script effects.

    idle·press·confirm 애니메이션이 있는 화살표 리셉터 하나입니다.
    ``spawn_x``와 ``spawn_y``에는 스크립트 효과에 쓸 초기 위치가 보관됩니다.
    """
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
        """Select ``idle``, ``press`` or ``confirm`` immediately.

        ``idle``·``press``·``confirm`` 중 하나를 즉시 선택합니다.
        """
        self._current_animation = name
        # record when press animation started
        if name == "press" or name == "confirm":
            self._press_start_time = time.time() * 1000  # ms
            self._pending_idle = False
        elif name == "idle":
            self._press_start_time = None
            self._pending_idle = False

    def request_idle(self):
        """Return to idle after the minimum press/confirm display time.

        press/confirm이 최소 표시 시간을 채운 뒤 idle로 돌아가게 요청합니다.
        """
        if self._current_animation in ["press", "confirm"]:
            self._pending_idle = True
        else:
            self.set_animation("idle")

    def update_idle_transition(self):
        if self._pending_idle and self._press_start_time is not None:
            elapsed = time.time() * 1000 - self._press_start_time
            if elapsed >= PRESS_MIN_DISPLAY_MS:
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
