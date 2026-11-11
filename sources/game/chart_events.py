"""Timed mod events / 차트의 시간 지정 모드 이벤트."""
import math
import runpy


class ChartEventManager:
    def __init__(self, game, events):
        self.game = game
        self.events = sorted(events, key=lambda event: event["time"])
        self.scripts = {}
        self.index = 0
        for event in self.events:
            if not isinstance(event["time"], (int, float)) or not math.isfinite(event["time"]) or event["time"] < 0:
                raise ValueError("Event time must be a nonnegative number of milliseconds")
            name = event["script"]
            game.assets._check_name(name)
            if not isinstance(event.get("params", {}), dict):
                raise ValueError("Event params must be an object")
            if name not in self.scripts:
                cls = runpy.run_path(str(game.assets.path(f"scripts/events/{name}.py")))["EventScript"]
                self.scripts[name] = cls(game)

    def update(self, delta_time=0.0):
        for script in self.scripts.values():
            if hasattr(script, "on_update"):
                script.on_update(delta_time)
        while self.index < len(self.events) and self.events[self.index]["time"] <= self.game.song_mgr.song_ms:
            event = self.events[self.index]
            self.index += 1
            self.scripts[event["script"]].on_event(event.get("params", {}))

    def on_hide_view(self):
        for script in self.scripts.values():
            if hasattr(script, "on_hide"):
                script.on_hide()
