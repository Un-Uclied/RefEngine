"""Graybox song selection and non-blocking loading screen.

회색 박스 곡 선택 메뉴와 화면을 멈추지 않는 로딩 화면입니다.
"""
from concurrent.futures import ThreadPoolExecutor
from queue import Empty, SimpleQueue

import arcade

from sources.assets import AssetStore, BASE_ASSETS, MODS_ROOT
from .main_game import MainGameView


def available_songs():
    paths = [(path.parent.name, path) for path in BASE_ASSETS.glob("songs/*/data.json")]
    paths += [
        (f"{path.parents[3].name}:{path.parent.name}", path)
        for path in MODS_ROOT.glob("*/assets/songs/*/data.json")
    ]
    songs = []
    for song_id, _ in sorted(paths):
        store, name = AssetStore.for_song(song_id)
        try:
            title = store.json(f"songs/{name}/data.json").get("name", name)
        except (OSError, ValueError):
            title = name
        songs.append((song_id, title))
    return songs


def prepare_song(song_id, report):
    assets, name = AssetStore.for_song(song_id)
    song = assets.json(f"songs/{name}/data.json")
    score = assets.json("config/score.json")
    background = assets.json(f"backgrounds/{song['background']}/data.json")
    judgements = assets.json("config/judgements.json")
    report(0.05, "Reading song data")

    paths = {entry["path"] for entry in background["backgrounds"]}
    paths.add("ui/general/center_vignette.png")
    for character in {song["player_name"], song["opponent_name"], song.get("sub_character_name")} - {None, ""}:
        data = assets.json(f"characters/{character}/data.json")
        paths.update(animation["path"] for animation in data["animations"].values())
    for character in {song["player_name"], song["opponent_name"]}:
        paths.update(f"characters/{character}/{state}.png" for state in ("normal", "defeat", "win"))
    receptor = assets.json(f"ui/receptors/{song['receptor_name']}/data.json")
    paths.update(path for direction in receptor["animations"].values() for path in direction.values())
    note_types = {"default"}
    note_types.update(
        note[3] for section in song["notes"] for note in section["sectionNotes"]
        if len(note) > 3 and isinstance(note[3], str)
    )
    for note_type in note_types:
        assets._check_name(note_type)
        data = assets.json(f"notes/{note_type}/data.json")
        paths.update(path for direction in data["paths"].values() for path in direction.values())
    for index, path in enumerate(sorted(paths), 1):
        assets.image(path)
        report(0.05 + 0.7 * index / len(paths), f"Images {index}/{len(paths)}")
    sounds = (
        arcade.load_sound(str(assets.path(song["inst_path"]))),
        arcade.load_sound(str(assets.path(song["voices_path"]))),
    )
    if any(sound is None for sound in sounds):
        raise ValueError(f"Could not load audio for {song_id}")
    report(0.8, "Audio ready")
    return assets, name, song, score, background, judgements, sounds


class MenuView(arcade.View):
    def __init__(self, initial_song=None):
        super().__init__()
        self.songs = available_songs()
        self.selected = next((i for i, song in enumerate(self.songs) if song[0] == initial_song), 0)
        self.title = arcade.Text("REFENGINE / SONG SELECT", 100, 610, arcade.color.WHITE, 28)
        self.hint = arcade.Text("UP / DOWN  SELECT     ENTER  START", 100, 570, arcade.color.LIGHT_GRAY, 16)
        self.start_text = arcade.Text("START", 990, 90, arcade.color.WHITE, 22, anchor_x="center", anchor_y="center")

    def on_draw(self):
        self.clear(color=(35, 35, 35))
        self.title.draw()
        self.hint.draw()
        first = max(0, self.selected - 6)
        for row, (song_id, name) in enumerate(self.songs[first:first + 7]):
            index = first + row
            y = 495 - row * 55
            arcade.draw_lbwh_rectangle_filled(100, y, 790, 45, (90, 90, 90) if index == self.selected else (55, 55, 55))
            arcade.draw_text(f"{name}   [{song_id}]", 115, y + 12, arcade.color.WHITE, 16)
        arcade.draw_lbwh_rectangle_filled(870, 65, 240, 55, (100, 100, 100))
        self.start_text.draw()

    def start(self):
        if self.songs:
            self.window.show_view(LoadingView(self.songs[self.selected][0]))

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP and self.songs:
            self.selected = (self.selected - 1) % len(self.songs)
        elif key == arcade.key.DOWN and self.songs:
            self.selected = (self.selected + 1) % len(self.songs)
        elif key in (arcade.key.ENTER, arcade.key.RETURN):
            self.start()

    def on_mouse_press(self, x, y, button, modifiers):
        if 870 <= x <= 1110 and 65 <= y <= 120:
            self.start()
            return
        first = max(0, self.selected - 6)
        row = int((495 + 45 - y) // 55)
        if 100 <= x <= 890 and 0 <= row < 7 and first + row < len(self.songs):
            if 495 - row * 55 <= y <= 540 - row * 55:
                self.selected = first + row


class LoadingView(arcade.View):
    def __init__(self, song_id):
        super().__init__()
        self.song_id = song_id
        self.progress = 0.0
        self.status = "Starting"
        self.error = None
        self._events = SimpleQueue()
        self._executor = None
        self._future = None
        self._steps = None
        self._game = None
        self._fade = 0.0
        self.title = arcade.Text(f"LOADING  {song_id}", 100, 400, arcade.color.WHITE, 28)
        self.status_text = arcade.Text("Starting", 100, 340, arcade.color.LIGHT_GRAY, 16)

    def on_show_view(self):
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._future = self._executor.submit(
            prepare_song, self.song_id,
            lambda progress, status: self._events.put((progress, status)),
        )

    def on_hide_view(self):
        self._executor.shutdown(wait=False, cancel_futures=True)

    def _fail(self, exc):
        self.error = str(exc)
        if self._game is None:
            return
        for script in reversed(getattr(self._game, "song_scripts", [])):
            if hasattr(script, "on_hide"):
                script.on_hide()
        for name in ("note_mgr", "character_mgr", "receptor_mgr", "splash_mgr",
                     "score_mgr", "camera_mgr", "game_interface_mgr"):
            manager = getattr(self._game, name, None)
            if manager is not None:
                manager.on_hide_view()

    def on_update(self, delta_time):
        if self.error:
            return
        while True:
            try:
                self.progress, self.status = self._events.get_nowait()
            except Empty:
                break
        if self._fade:
            self._fade = min(255, self._fade + delta_time * 850)
            if self._fade == 255:
                self._game._fade_alpha = 255
                self.window.show_view(self._game)
            return
        if self._steps is None:
            if not self._future.done():
                return
            try:
                self._game = MainGameView(self.song_id, self._future.result())
                self._steps = self._game.load_steps()
            except Exception as exc:
                self._fail(exc)
                return
        try:
            self.status = next(self._steps)
            self.progress = min(0.98, self.progress + 0.01)
        except StopIteration:
            try:
                self._game.on_draw()
                self._game._ready = True
                self.progress = 1.0
                self.status = "Ready"
                self._fade = 0.001
            except Exception as exc:
                self._fail(exc)
        except Exception as exc:
            self._fail(exc)

    def on_draw(self):
        self.clear(color=(25, 25, 25))
        self.title.draw()
        self.status_text.text = f"{self.status}  {int(self.progress * 100)}%"
        self.status_text.draw()
        arcade.draw_lbwh_rectangle_filled(100, 55, 1080, 18, (65, 65, 65))
        arcade.draw_lbwh_rectangle_filled(100, 55, 1080 * self.progress, 18, arcade.color.WHITE)
        if self.error:
            arcade.draw_text(f"Load failed: {self.error}", 100, 285, arcade.color.RED, 16)
            arcade.draw_text("Press ESC to return", 100, 250, arcade.color.WHITE, 16)
        if self._fade:
            arcade.draw_lbwh_rectangle_filled(0, 0, self.window.width, self.window.height, (0, 0, 0, int(self._fade)))

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE and self.error:
            self.window.show_view(MenuView(self.song_id))
