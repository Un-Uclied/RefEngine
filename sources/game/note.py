import math, arcade
from typing import Dict, List, Tuple, Any, Optional
from .events import on_note_pressed, on_note_released, on_note_missed, on_opponent_pressed, on_opponent_released

REMOVE_DELAY_MS = 200
MISS_ALPHA = 50

def calculate_line_bounds(
    point_a: Tuple[float, float],
    point_b: Tuple[float, float],
    thickness: float,
    min_width: float,
    min_height: float
) -> Tuple[float, float, float, float]:
    raw_left = min(point_a[0], point_b[0])
    raw_right = max(point_a[0], point_b[0])
    raw_bottom = min(point_a[1], point_b[1])
    raw_top = max(point_a[1], point_b[1])

    offset = thickness / 2.0
    left = raw_left - offset
    bottom = raw_bottom - offset
    width = (raw_right - raw_left) + thickness
    height = (raw_top - raw_bottom) + thickness

    final_width = max(width, min_width)
    final_height = max(height, min_height)
    if final_width > width:
        left -= (final_width - width) / 2.0
    if final_height > height:
        bottom -= (final_height - height) / 2.0

    return left, bottom, final_width, final_height

class HoldSegment(arcade.Sprite):
    def __init__(self, note: 'Note', index: int, texture_source: Any, base_height: float, scale: float):
        texture = texture_source.keyframes[0].texture if hasattr(texture_source, "keyframes") else texture_source
        super().__init__(texture, scale, 0, 0)
        self.parent_note = note
        self.segment_index = index
        self.base_height = base_height
        self.sync_position()

    def update(self, delta_time: float):
        self.sync_position()
        return super().update(delta_time)

    def sync_position(self):
        self.angle = self.parent_note.angle
        direction_radian = math.radians(-self.angle - 90)
        step = self.base_height * self.scale_y
        offset = (self.segment_index + 1) * step
        self.center_x = self.parent_note.center_x + math.cos(direction_radian) * offset
        self.center_y = self.parent_note.center_y + math.sin(direction_radian) * offset

class Note(arcade.TextureAnimationSprite):
    def __init__(self, note_data: dict, assets: dict, target_receptor: Any):
        self.direction_index = note_data["direction_index"]
        self.strum_time = note_data["strum_time"]
        self.sustain_length = note_data["sustain_length"]
        self.note_type = note_data["note_type"]
        self.must_hit_note = note_data["must_hit_note"]
        self.penalty_note = note_data["penalty_note"]
        self.settings = note_data["settings"]
        self.assets = assets
        self.target_receptor = target_receptor

        self.pressed = False
        self.released = False
        self.is_hit = False
        self.is_miss = False
        self.is_released_early = False
        self.judgement = ""
        self.segments: List[HoldSegment] = []

        head_asset = assets["head"]
        if isinstance(head_asset, arcade.Texture):
            head_asset = arcade.TextureAnimation([arcade.TextureKeyframe(head_asset, 100)])
        super().__init__(0, 0, self.settings["scale"], head_asset)

    @property
    def is_opponent(self) -> bool:
        return self.direction_index >= 4

    def set_visual_miss(self):
        self.alpha = MISS_ALPHA
        for segment in self.segments:
            segment.alpha = MISS_ALPHA

    def update_position(self, song_ms: float, pixels_per_ms: float):
        time_gap = self.strum_time - song_ms
        distance = time_gap * pixels_per_ms
        self.angle = self.target_receptor.angle
        radian = math.radians(-self.angle + 90)
        self.center_x = self.target_receptor.center_x - math.cos(radian) * distance
        self.center_y = self.target_receptor.center_y - math.sin(radian) * distance

    def create_sustain_tail(self, note_manager: 'NoteManager'):
        hold_texture = self.assets["hold"]
        base_height = hold_texture.height if isinstance(hold_texture, arcade.Texture) else hold_texture.keyframes[0].texture.height
        pixel_length = self.sustain_length * note_manager.pixels_per_ms
        segment_count = math.ceil(pixel_length / (base_height * self.scale_y))

        for index in range(segment_count):
            segment = HoldSegment(self, index, hold_texture, base_height, self.scale_y)
            note_manager.sustains[self.direction_index].append(segment)
            self.segments.append(segment)

        if self.segments:
            self.segments[-1].texture = self.assets["end"]

    def despawn(self):
        self.remove_from_sprite_lists()
        for segment in self.segments:
            segment.remove_from_sprite_lists()

class NoteManager:
    def __init__(self, game_context: Any, song_data: dict, judgement_data: dict, is_bot_play: bool):
        self.game_context = game_context
        self.song_data = song_data
        self.pixels_per_ms = 0.45 * song_data["speed"]
        self.is_bot_play = is_bot_play
        self.spawn_lead_ms = 2000
        self.hit_window_ms = max(judgement_data.values())
        self.next_spawn_index = 0
        self.note_assets = {}
        self.note_settings = {}
        self.chart_data = []
        self.judgement_windows = judgement_data

        self.notes = arcade.SpriteList()
        self.sustains = {index: arcade.SpriteList() for index in range(8)}

        self.load_resources()
        self.parse_chart()

    def load_resources(self):
        note_types = {"default"}
        for section in self.song_data.get("notes", []):
            for raw_note in section.get("sectionNotes", []):
                if len(raw_note) > 3 and isinstance(raw_note[3], str):
                    note_types.add(raw_note[3])

        for note_type in note_types:
            self.note_settings[note_type] = self.game_context.assets.json(f"ui/notes/{note_type}/data.json")

            self.note_assets[note_type] = {}
            for direction in ["left", "down", "up", "right"]:
                self.note_assets[note_type][direction] = {}
                for part in ["head", "hold", "end"]:
                    path = self.note_settings[note_type]["paths"][direction][part]
                    self.note_assets[note_type][direction][part] = self.game_context.assets.image(path)

    def parse_chart(self):
        for section in self.song_data["notes"]:
            for raw_note in section["sectionNotes"]:
                lane = raw_note[1] % 4
                side = (0 if raw_note[1] < 4 else 4) if section["mustHitSection"] else (4 if raw_note[1] < 4 else 0)
                note_type = raw_note[3] if len(raw_note) > 3 and isinstance(raw_note[3], str) else "default"
                settings = self.note_settings[note_type]

                self.chart_data.append({
                    "direction_index": lane + side,
                    "strum_time": raw_note[0],
                    "sustain_length": raw_note[2],
                    "note_type": note_type,
                    "must_hit_note": settings.get("must_hit_note", True),
                    "penalty_note": settings.get("penalty_note", settings.get("penaly_note", False)),
                    "settings": settings
                })
        self.chart_data.sort(key=lambda note: note["strum_time"])

    def process_hit(self, direction_index: int, current_ms: float) -> Optional[Note]:
        candidates = [note for note in self.notes if not note.is_hit and not note.is_miss and note.direction_index == direction_index and abs(note.strum_time - current_ms) <= self.hit_window_ms]
        if not candidates:
            return None

        hit_note = min(candidates, key=lambda note: note.strum_time)
        hit_note.is_hit = True
        time_difference = abs(hit_note.strum_time - current_ms)

        for name, window in self.judgement_windows.items():
            if time_difference <= window:
                hit_note.judgement = name
                break
        return hit_note

    def spawn_notes(self):
        song_ms = self.game_context.song_mgr.song_ms
        while self.next_spawn_index < len(self.chart_data):
            note_info = self.chart_data[self.next_spawn_index]
            if note_info["strum_time"] > song_ms + self.spawn_lead_ms:
                break

            direction_name = ["left", "down", "up", "right"][note_info["direction_index"] % 4]
            assets = self.note_assets[note_info["note_type"]][direction_name]
            target_receptor = self.game_context.receptor_mgr.receptors[note_info["direction_index"]]

            new_note = Note(note_info, assets, target_receptor)
            if new_note.sustain_length > 0:
                new_note.create_sustain_tail(self)

            self.notes.append(new_note)
            self.next_spawn_index += 1

    def handle_automated_input(self):
        song_ms = self.game_context.song_mgr.song_ms
        for note in self.notes:
            is_valid_bot_target = self.is_bot_play and not note.is_opponent and not note.penalty_note
            if not note.is_opponent and not is_valid_bot_target:
                continue

            if not note.pressed and song_ms >= note.strum_time:
                note.pressed = True
                note.is_hit = True
                note.judgement = "auto"
                if note.is_opponent:
                    on_opponent_pressed.send(self, direction_index=note.direction_index, note=note)
                else:
                    on_note_pressed.send(self, direction_index=note.direction_index, note=note)

            if not note.released and song_ms > note.strum_time + note.sustain_length:
                note.released = True
                if note.is_opponent:
                    on_opponent_released.send(self, direction_index=note.direction_index)
                else:
                    on_note_released.send(self, direction_index=note.direction_index)

    def draw_sustains(self):
        camera_zoom = self.game_context.camera_mgr.camera_note.zoom
        window = arcade.get_window()
        offset_x = (window.width / 2) * (1 - camera_zoom)
        offset_y = (window.height / 2) * (1 - camera_zoom)

        for index, sustain_list in self.sustains.items():
            if len(sustain_list) == 0:
                continue

            receptor = self.game_context.receptor_mgr.receptors[index]
            radian = math.radians(-receptor.angle + 90)
            center_x = (receptor.center_x * camera_zoom) + offset_x
            center_y = (receptor.center_y * camera_zoom - math.sin(radian) * receptor.texture.height * camera_zoom * 0.3) + offset_y
            destination_x = center_x - math.cos(radian) * (2000 * camera_zoom)
            destination_y = center_y - math.sin(radian) * (2000 * camera_zoom)

            hold_width = self.note_assets["default"]["left"]["hold"].width
            bound_x, bound_y, bound_w, bound_h = calculate_line_bounds((center_x, center_y), (destination_x, destination_y), (hold_width * 2) * camera_zoom, (hold_width * 4) * camera_zoom, 0)

            if sustain_list[0].parent_note.is_hit:
                window.ctx.scissor = (int(bound_x), int(bound_y), int(bound_w), int(bound_h))
                sustain_list.draw()
                window.ctx.scissor = None
            else:
                sustain_list.draw()

    def on_key_press(self, direction_index: int):
        song_ms = self.game_context.song_mgr.song_ms
        note = self.process_hit(direction_index, song_ms)
        if note:
            on_note_pressed.send(self, direction_index=direction_index, note=note)

    def on_key_release(self, direction_index: int):
        song_ms = self.game_context.song_mgr.song_ms
        on_note_released.send(self, direction_index=direction_index)

        for note in self.notes:
            if not note.is_opponent and note.direction_index == direction_index and note.is_hit and not note.is_released_early and note.strum_time <= song_ms < note.strum_time + note.sustain_length:
                note.is_released_early = True
                note.set_visual_miss()
                on_note_missed.send(self, note=note)
                break

    def update(self, delta_time: float):
        song_ms = self.game_context.song_mgr.song_ms
        self.spawn_notes()
        self.handle_automated_input()

        for note in self.notes:
            note.update_position(song_ms, self.pixels_per_ms)
            if song_ms >= note.strum_time + note.sustain_length + REMOVE_DELAY_MS:
                note.despawn()
            note.visible = not note.is_hit

            if not note.is_opponent and not note.is_hit and not note.is_miss:
                if song_ms > note.strum_time + self.hit_window_ms:
                    note.is_miss = True
                    note.set_visual_miss()
                    if note.must_hit_note:
                        on_note_missed.send(self, note=note)

        self.notes.update(delta_time)
        self.notes.update_animation(delta_time)
        for sustain_list in self.sustains.values():
            sustain_list.update(delta_time)

    def draw(self):
        self.draw_sustains()
        self.notes.draw()
