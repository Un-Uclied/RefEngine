"""Play note splash frames from an Adobe Animate XML atlas.

Adobe Animate XML 아틀라스에서 노트 스플래시 프레임을 읽어 재생합니다.
"""
import re
from xml.etree import ElementTree

import arcade
from PIL import Image

from .events import on_note_pressed, on_opponent_pressed


FRAME_MS = 50
LANE_COLORS = ("purple", "blue", "green", "red")
FRAME_NAME = re.compile(r"note splash (blue|green|purple|red) ([12])000([0-3])$")


class SplashManager:
    """Show a note splash at the matching receptor after a SICK or AUTO hit.

    ``sprites`` contains active splashes. ``animations`` maps
    ``(color, variant)`` to a four-frame animation loaded from the XML atlas.

    SICK 또는 AUTO 판정 시 양쪽 리셉터에 노트 스플래시를 표시합니다.
    ``sprites``는 활성 스플래시 목록이고 ``animations``는 XML 아틀라스에서
    읽은 4프레임 애니메이션을 ``(색상, 변형 번호)``로 찾는 매핑입니다.
    """
    def __init__(self, game_context, splash_name, assets):
        self.game_context = game_context
        atlas_name = f"ui/splashes/{splash_name}/noteSplashes.xml"
        atlas = ElementTree.parse(assets.path(atlas_name)).getroot()
        image_name = f"ui/splashes/{splash_name}/{atlas.attrib['imagePath']}"
        image_path = assets.path(image_name)

        groups = {}
        for entry in atlas.findall("SubTexture"):
            match = FRAME_NAME.fullmatch(entry.attrib["name"])
            if match:
                color, variant, frame = match.groups()
                groups.setdefault((color, int(variant)), {})[int(frame)] = entry

        self.animations = {}
        with Image.open(image_path) as source:
            sheet = source.convert("RGBA")
            for color in LANE_COLORS:
                for variant in (1, 2):
                    frames = groups.get((color, variant), {})
                    if set(frames) != set(range(4)):
                        raise ValueError(f"Incomplete splash animation in {atlas_name}: {color} {variant}")
                    width = max(
                        max(int(frame.get("frameWidth", frame.get("width"))),
                            int(frame.get("width")) - int(frame.get("frameX", "0")))
                        for frame in frames.values()
                    )
                    height = max(
                        max(int(frame.get("frameHeight", frame.get("height"))),
                            int(frame.get("height")) - int(frame.get("frameY", "0")))
                        for frame in frames.values()
                    )
                    keyframes = []
                    for index in range(4):
                        frame = frames[index]
                        x, y = int(frame.get("x")), int(frame.get("y"))
                        w, h = int(frame.get("width")), int(frame.get("height"))
                        canvas = Image.new("RGBA", (width, height))
                        canvas.paste(
                            sheet.crop((x, y, x + w, y + h)),
                            (-int(frame.get("frameX", "0")), -int(frame.get("frameY", "0"))),
                        )
                        texture = arcade.Texture(canvas, hash=f"{image_path}:{frame.get('name')}")
                        keyframes.append(arcade.TextureKeyframe(texture, FRAME_MS))
                    self.animations[(color, variant)] = arcade.TextureAnimation(keyframes)

        self.sprites = arcade.SpriteList()
        self._next_variant = [1] * 8
        on_note_pressed.connect(self._note_pressed)
        on_opponent_pressed.connect(self._note_pressed)

    def on_hide_view(self):
        on_note_pressed.disconnect(self._note_pressed)
        on_opponent_pressed.disconnect(self._note_pressed)

    def _note_pressed(self, sender, direction_index, note):
        if note is None or note.judgement not in ("sick", "auto"):
            return
        lane = direction_index % 4
        receptor = self.game_context.receptor_mgr.receptors[direction_index]
        variant = self._next_variant[direction_index]
        self._next_variant[direction_index] = 3 - variant
        sprite = arcade.TextureAnimationSprite(
            receptor.center_x, receptor.center_y, receptor.scale_x,
            self.animations[(LANE_COLORS[lane], variant)],
        )
        self.sprites.append(sprite)

    def update(self, delta_time):
        self.sprites.update_animation(delta_time)
        for sprite in tuple(self.sprites):
            if sprite.time >= len(sprite.animation.keyframes) * FRAME_MS / 1000:
                sprite.remove_from_sprite_lists()

    def draw(self):
        self.sprites.draw()
