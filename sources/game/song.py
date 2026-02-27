import arcade
from sources.utils.event_bus import bus


class SongManager:
    def __init__(self, song_data: dict):
        self._song_data = song_data

        self._inst_sound = arcade.load_sound(song_data["inst_path"])
        self._voices_sound = arcade.load_sound(song_data["voices_path"])

        self.inst_player = None
        self.voices_player = None

        self.music_playing = False
        self._paused = False
        self._pause_time = 0

        self._last_beat = -1
        self._last_step = -1

        self.sections = self._build_section_timeline()
        self._beat_times, self._step_times = self._build_time_timeline()

    @property
    def song_ms(self):
        if not self.inst_player:
            return 0
        return self.inst_player.time * 1000

    @property
    def is_player_turn(self):
        t = self.song_ms
        for sec in self.sections:
            if sec["start"] <= t < sec["end"]:
                return sec["mustHit"]
        return False

    def update(self):
        if not self.music_playing:
            return

        t = self.song_ms

        for i in range(self._last_step + 1, len(self._step_times)):
            if t >= self._step_times[i]:
                self._last_step = i
                bus.publish("step", step=i, time=t)
            else:
                break

        for i in range(self._last_beat + 1, len(self._beat_times)):
            if t >= self._beat_times[i]:
                self._last_beat = i
                bus.publish("beat", beat=i, time=t)
            else:
                break

    def play(self):
        if self.music_playing:
            return

        self.inst_player = arcade.play_sound(self._inst_sound)
        self.voices_player = arcade.play_sound(self._voices_sound)

        self.music_playing = True
        self._paused = False
        self._last_beat = -1
        self._last_step = -1

    def stop(self):
        if self.inst_player:
            arcade.stop_sound(self.inst_player)
        if self.voices_player:
            arcade.stop_sound(self.voices_player)

        self.inst_player = None
        self.voices_player = None

        self.music_playing = False
        self._paused = False
        self._last_beat = -1
        self._last_step = -1

    def pause(self):
        if not self.music_playing or self._paused:
            return

        self._pause_time = self.song_ms
        arcade.stop_sound(self.inst_player)
        arcade.stop_sound(self.voices_player)

        self._paused = True

    def resume(self):
        if not self._paused:
            return

        self.inst_player = arcade.play_sound(
            self._inst_sound,
            start=self._pause_time / 1000
        )

        self.voices_player = arcade.play_sound(
            self._voices_sound,
            start=self._pause_time / 1000
        )

        self._paused = False
        self.music_playing = True

    def _build_section_timeline(self):
        base_bpm = self._song_data["bpm"]
        current_bpm = base_bpm

        sections = []
        current_time = 0

        for sec in self._song_data["notes"]:

            if sec.get("changeBPM", False):
                current_bpm = sec.get("bpm", current_bpm)

            step_ms = (60000 / current_bpm) / 4
            length_ms = sec.get("lengthInSteps", 16) * step_ms

            sections.append({
                "start": current_time,
                "end": current_time + length_ms,
                "mustHit": sec["mustHitSection"]
            })

            current_time += length_ms

        return sections

    def _build_time_timeline(self):
        base_bpm = self._song_data["bpm"]
        current_bpm = base_bpm

        beat_times = []
        step_times = []

        current_time = 0

        for sec in self._song_data["notes"]:

            if sec.get("changeBPM", False):
                current_bpm = sec.get("bpm", current_bpm)

            beat_ms = 60000 / current_bpm
            step_ms = beat_ms / 4

            for _ in range(sec.get("lengthInSteps", 16)):
                step_times.append(current_time)
                current_time += step_ms

            beats_in_section = sec.get("lengthInSteps", 16) // 4
            beat_start_time = step_times[-sec.get("lengthInSteps", 16)]

            for i in range(beats_in_section):
                beat_times.append(beat_start_time + i * beat_ms)

        return beat_times, step_times