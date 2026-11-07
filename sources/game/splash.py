"""Play note splash frames from an Adobe Animate XML atlas."""
import re
from xml.etree import ElementTree

import arcade
from PIL import Image

from .events import on_note_pressed


FRAME_MS = 50
LANE_COLORS = ("purple", "blue", "green", "red")
FRAME_NAME = re.compile(r"note splash (blue|green|purple|red) ([12])000([0-3])$")


class SplashManager:
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
        self._next_variant = [1] * 4
        on_note_pressed.connect(self._note_pressed)

    def on_hide_view(self):
        on_note_pressed.disconnect(self._note_pressed)

    def _note_pressed(self, sender, direction_index, note):
        if note is None or note.judgement != "sick":
            return
        lane = direction_index % 4
        receptor = self.game_context.receptor_mgr.receptors[direction_index]
        variant = self._next_variant[lane]
        self._next_variant[lane] = 3 - variant
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
