"""Unprocessed screen-space UI / 후처리되지 않는 시스템 UI."""
import arcade
from sources.fonts import FONT_NAME


def fps_color(fps, target):
    ratio = fps / max(target, 1)
    return (245, 95, 100) if ratio < 0.60 else (255, 177, 70) if ratio < 0.85 else (183, 219, 197)


class SystemUI:
    def __init__(self, game):
        self.game = game
        self.camera = arcade.Camera2D()
        self.fps = arcade.Text("", 0, 0, font_name=FONT_NAME, font_size=11, bold=False, anchor_x="right", anchor_y="top")
        self.title = arcade.Text("일시 정지", 0, 0, font_name=FONT_NAME, font_size=38, bold=True, anchor_x="center")
        self.options = [arcade.Text("", 0, 0, font_name=FONT_NAME, font_size=23, bold=False, anchor_x="center") for _ in range(4)]

    def draw(self):
        game = self.game
        width, height = game.window.width, game.window.height
        with self.camera.activate():
            if game.paused:
                arcade.draw_lbwh_rectangle_filled(0, 0, width, height, (0, 0, 0, 180))
                self.title.position = (width / 2, height * 0.73)
                self.title.draw()
                labels = ["재개", "처음부터 다시 시작", f"봇플레이: {'활성화' if game.note_mgr.is_bot_play else '비활성화'}", "메인 메뉴로"]
                for index, (label, text) in enumerate(zip(labels, self.options)):
                    text.text = ("›  " if index == game.pause_selection else "") + label
                    text.position = (width / 2, height * 0.58 - index * 52)
                    text.color = (255, 219, 136) if index == game.pause_selection else (185, 192, 207)
                    text.draw()
            fps = arcade.get_fps()
            target = 1 / game.window._draw_rate
            self.fps.text = f"{fps:.0f} / {target:.0f} FPS  ·  {1000 / fps if fps else 0:.1f} ms"
            self.fps.color = fps_color(fps, target)
            self.fps.position = (width - 16, height - 12)
            self.fps.draw()
