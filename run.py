import arcade
import sys
from sources.assets import BASE_ASSETS
from sources.views import *

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WINDOW_NAME = "Friday Night Funkin : RefEngine"
FULLSCREEN = False
ANTIALIASING = True
UPDATE_RATE = 1/240
FIXED_RATE = 1/60
DRAW_RATE = 1/240

class Application:
    def __init__(self):
        self.window = arcade.Window(
            width=SCREEN_WIDTH,
            height=SCREEN_HEIGHT,
            title=WINDOW_NAME,
            fullscreen=FULLSCREEN,
            antialiasing=ANTIALIASING,
            update_rate=UPDATE_RATE,
            fixed_rate=FIXED_RATE,
            draw_rate=DRAW_RATE,
            center_window=True,
        )
        arcade.enable_timings()

        # arcade.resources.add_resource_handle("")

        arcade.load_font(str(BASE_ASSETS / "fonts/SeoulAlrimTTF-Heavy.ttf"))

        self.stage_view = MenuView(sys.argv[1] if len(sys.argv) > 1 else None)
        
        self.window.show_view(self.stage_view)
        arcade.run()

if __name__ == "__main__":
    app = Application()
