import arcade


class BackgroundManager:
    """Own stage sprites defined in background data.json.

    ``world_sprites`` move with the world camera; ``screen_sprites`` stay in
    screen space. Song scripts may adjust their sprite positions and opacity.

    배경 data.json에 정의된 스테이지 스프라이트를 관리합니다.
    ``world_sprites``는 월드 카메라를 따라가고 ``screen_sprites``는 화면 좌표에
    고정됩니다. 노래 스크립트에서 위치와 불투명도를 조절할 수 있습니다.
    """
    def __init__(self, background_data, assets):
        self.assets = assets
        self.world_sprites = arcade.SpriteList()
        self.screen_sprites = arcade.SpriteList()
        window = arcade.get_window()

        for bg in background_data["backgrounds"]:
            sprite, full_screen = self._create_sprite(bg)
            self._scale_sprite(sprite, bg, window, full_screen)
            self._position_sprite(sprite, bg, window, full_screen)
            target = self.screen_sprites if bg["screen_space"] else self.world_sprites
            target.append(sprite)

    def _create_sprite(self, bg):
        path = bg["path"]
        speed = bg.get("speed", 1)

        if path.lower().endswith(".gif"):
            anim = self.assets.image(path)
            sprite = arcade.TextureAnimationSprite()
            sprite.animation = anim
            sprite.time = 0
            sprite._current_keyframe_index = 0
            sprite._should_loop = True
        else:
            sprite = arcade.Sprite()
            sprite.texture = self.assets.image(path)

        sprite.speed = speed

        scale = bg["scale"]
        return sprite, scale == "full_screen"

    def _scale_sprite(self, sprite : arcade.TextureAnimationSprite, bg, window, full_screen):
        if full_screen:
            sprite.width = window.width
            sprite.height = window.height
        else:
            sprite.scale = bg["scale"]

    def _position_sprite(self, sprite, bg, window, full_screen):
        x, y = tuple(bg.get("position", (0, 0)))
        if bg.get("screen_space", False):
            sprite.center_x = x + sprite.width / 2
            sprite.center_y = window.height - y - sprite.height / 2
        else:
            sprite.position = (x, y)

        if full_screen:
            sprite.center_x = window.width / 2
            sprite.center_y = window.height / 2

    def update(self, delta_time):
        for sprite in self.world_sprites:
            if hasattr(sprite, "update_animation"):
                sprite.update_animation(delta_time * getattr(sprite, "speed", 1))
        for sprite in self.screen_sprites:
            if hasattr(sprite, "update_animation"):
                sprite.update_animation(delta_time * getattr(sprite, "speed", 1))

    def draw_world(self):
        self.world_sprites.draw()

    def draw_camera(self):
        self.screen_sprites.draw()
