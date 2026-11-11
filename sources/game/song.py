import arcade
from .events import on_step, on_beat

class SongManager:
    """Play the instrumental and vocals and emit step/beat events.

    Scripts can read ``song_ms``, ``beat``, ``step``, ``is_player_turn`` and
    ``current_section_data``. Time values are milliseconds unless noted.

    반주와 보컬을 재생하고 스텝/비트 이벤트를 보냅니다.
    스크립트에서 위 속성으로 재생 위치와 현재 구간을 읽을 수 있습니다.
    별도 표기가 없으면 시간 단위는 밀리초입니다.
    """
    def __init__(self, song_data: dict, assets, sounds=None):
        self._song_data = song_data

        if sounds is None:
            sounds = (
                arcade.load_sound(str(assets.path(song_data["inst"]))),
                arcade.load_sound(str(assets.path(song_data["voices"]))),
            )
        self._inst_sound, self._voices_sound = sounds

        self.inst_player = None
        self.voices_player = None
        self.volume_percent = 100

        self.music_playing = False
        self._paused = False
        self._pause_time = 0

        self._last_beat = -1
        self._last_step = -1

        self.sections = self._build_section_timeline()
        self._beat_times, self._step_times = self._build_time_timeline()

    @property
    def song_ms(self):
        """Current instrumental playback position in milliseconds, or 0 before play.

        현재 반주 재생 위치(밀리초)입니다. 재생 전에는 0입니다.
        """
        if not self.inst_player:
            return 0
        return self.inst_player.time * 1000

    @property
    def is_player_turn(self):
        """Whether the active chart section has ``mustHitSection`` enabled.

        현재 차트 구간의 ``mustHitSection``이 켜져 있는지 나타냅니다.
        """
        t = self.song_ms
        for sec in self.sections:
            if sec["start"] <= t < sec["end"]:
                return sec["mustHit"]
        return False

    @property
    def current_section_data(self):
        """Raw active chart section, or None outside the section timeline.

        현재 차트 구간의 원본 데이터입니다. 구간 밖에서는 None입니다.
        """
        t = self.song_ms
        for sec in self.sections:
            if sec["start"] <= t < sec["end"]:
                return sec["data"]
        return None

    @property
    def step(self):
        """Last emitted step index; -1 until the first step fires.

        마지막으로 발생한 스텝 번호입니다. 첫 스텝 전에는 -1입니다.
        """
        return self._last_step

    @property
    def beat(self):
        """Last emitted beat index; -1 until the first beat fires.

        마지막으로 발생한 비트 번호입니다. 첫 비트 전에는 -1입니다.
        """
        return self._last_beat

    def update(self):
        if not self.music_playing:
            return

        ms = self.song_ms
        for step in range(self._last_step + 1, len(self._step_times)):
            if ms >= self._step_times[step]:
                self._last_step = step
                on_step.send(self, step=step, ms=ms)
            else:
                break
        for beat in range(self._last_beat + 1, len(self._beat_times)):
            if ms >= self._beat_times[beat]:
                self._last_beat = beat
                on_beat.send(self, beat=beat, ms=ms)
            else:
                break

    def play(self):
        """Start both tracks from the beginning if they are not playing.

        재생 중이 아닐 때 반주와 보컬을 처음부터 시작합니다.
        """
        if self.music_playing:
            return

        self.inst_player = arcade.play_sound(self._inst_sound, volume=self.volume_percent / 100)
        self.voices_player = arcade.play_sound(self._voices_sound, volume=self.volume_percent / 100)

        self.music_playing = True
        self._paused = False
        self._last_beat = -1
        self._last_step = -1

    def change_volume(self, delta_percent):
        """Adjust both tracks by percentage points, clamped to 0-100.

        반주와 보컬의 볼륨을 퍼센트포인트만큼 조절하고 0~100으로 제한합니다.
        """
        self.volume_percent = max(0, min(100, self.volume_percent + delta_percent))
        for player in (self.inst_player, self.voices_player):
            if player:
                player.volume = self.volume_percent / 100

    def stop(self):
        """Stop both tracks and clear their players.

        두 트랙을 멈추고 플레이어 객체를 비웁니다.
        """
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
        """Stop both tracks while retaining the instrumental position.

        반주 위치를 저장한 뒤 두 트랙을 일시정지합니다.
        """
        if not self.music_playing or self._paused:
            return

        self._pause_time = self.song_ms
        arcade.stop_sound(self.inst_player)
        arcade.stop_sound(self.voices_player)

        self._paused = True

    def resume(self):
        """Restart both tracks at the saved pause position and current volume.

        저장한 위치와 현재 볼륨으로 두 트랙을 다시 재생합니다.
        """
        if not self._paused:
            return

        self.inst_player = arcade.play_sound(
            self._inst_sound,
            volume=self.volume_percent / 100
        )

        self.voices_player = arcade.play_sound(
            self._voices_sound,
            volume=self.volume_percent / 100
        )
        for player in (self.inst_player, self.voices_player):
            if player:
                player.seek(self._pause_time / 1000)

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
                "mustHit": sec["mustHitSection"],
                "data": sec
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
