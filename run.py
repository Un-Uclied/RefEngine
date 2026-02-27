import arcade
from sources.views import *

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WINDOW_NAME = "My Arcade Game"
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

        # Initialize the stage
        self.stage_view = MainGameView("singularity")
        
        # Show the stage
        self.window.show_view(self.stage_view)
        arcade.run()

if __name__ == "__main__":
    app = Application()