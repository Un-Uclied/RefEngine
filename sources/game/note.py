import json
import math
import pathlib
from typing import Dict, List, Tuple, Any, Optional
import arcade
from sources.utils.event_bus import *

REMOVE_DELAY_MS = 200
MISS_ALPHA = 50

def calculate_line_bounds(
    point_a: Tuple[float, float], 
    point_b: Tuple[float, float], 
    thickness: float, 
    min_width: float, 
    min_height: float
) -> Tuple[float, float, float, float]:
    raw_left, raw_right = min(point_a[0], point_b[0]), max(point_a[0], point_b[0])
    raw_bottom, raw_top = min(point_a[1], point_b[1]), max(point_a[1], point_b[1])

    offset = thickness / 2.0
    left, bottom = raw_left - offset, raw_bottom - offset
    width, height = (raw_right - raw_left) + thickness, (raw_top - raw_bottom) + thickness

    final_width, final_height = max(width, min_width), max(height, min_height)
    if final_width > width:
        left -= (final_width - width) / 2.0
    if final_height > height:
        bottom -= (final_height - height) / 2.0

    return left, bottom, final_width, final_height

class HoldSegment(arcade.Sprite):
    def __init__(
        self, 
        note: 'Note', 
        index: int, 
        texture_source: Any, 
        base_height: float, 
        scale: float,
    ):
        texture = texture_source.keyframes[0].texture if hasattr(texture_source, "keyframes") else texture_source
        super().__init__(texture, scale, 0, 0)
        self.parent_note = note
        self.segment_index = index
        self._base_height = base_height
        self._sync_position()

    def update(self, delta_time: float):
        self._sync_position()
        return super().update(delta_time)

    def _sync_position(self):
        self.angle = self.parent_note.angle
        direction_radian = math.radians(-self.angle - 90)
        step = self._base_height * self.scale_y
        offset = (self.segment_index + 1) * step
        
        self.center_x = self.parent_note.center_x + math.cos(direction_radian) * offset
        self.center_y = self.parent_note.center_y + math.sin(direction_radian) * offset

class Note(arcade.TextureAnimationSprite):
    def __init__(
        self, 
        direction_index: int,
        strum_time: float, 
        sustain_length: float,
        note_type: str, 
        settings: dict, 
        assets: dict,
        must_hit_note: bool = True,
        penalty_note: bool = False
    ):
        self.direction_index = direction_index
        self.strum_time = strum_time
        self.sustain_length = sustain_length
        self.note_type = note_type
        self._settings = settings
        self._assets = assets
        self.must_hit_note = must_hit_note
        self.penalty_note = penalty_note
        
        # flags used by the AI/opponent logic
        self._pressed = False
        self._released = False

        head_asset = assets["head"]
        if isinstance(head_asset, arcade.Texture):
            head_asset = arcade.TextureAnimation([arcade.TextureKeyframe(head_asset, 100)])
        super().__init__(0, 0, settings["scale"], head_asset)

        from sources.views import MainGameView
        receptor_mgr = MainGameView.current.receptor_mgr
        self.target_receptor = receptor_mgr.receptors[direction_index]
        self.is_hit = False
        self.is_miss = False
        self.is_released_early = False
        self.judgement = ""
        self._segments: List[HoldSegment] = []
        
        if self.sustain_length > 0:
            self._create_sustain_tail()

    @property
    def should_despawn(self) -> bool:
        from sources.views import MainGameView
        song_mgr = MainGameView.current.song_mgr
        return song_mgr.song_ms >= self.strum_time + self.sustain_length + REMOVE_DELAY_MS

    @property
    def is_opponent(self) -> bool:
        return self.direction_index >= 4

    def update(self, delta_time: float):
        self._update_position()
        if self.should_despawn:
            self.despawn()
        self.visible = not self.is_hit
        return super().update(delta_time)

    def set_visual_miss(self):
        self.alpha = MISS_ALPHA
        for segment in self._segments:
            segment.alpha = MISS_ALPHA

    def _update_position(self):
        from sources.views import MainGameView
        song_mgr = MainGameView.current.song_mgr
        note_mgr = MainGameView.current.note_mgr

        time_gap = self.strum_time - song_mgr.song_ms
        distance = time_gap * note_mgr.pixels_per_ms
        self.angle = self.target_receptor.angle
        rad = math.radians(-self.angle + 90)
        self.center_x = self.target_receptor.center_x - math.cos(rad) * distance
        self.center_y = self.target_receptor.center_y - math.sin(rad) * distance

    def _create_sustain_tail(self):
        from sources.views import MainGameView
        note_mgr = MainGameView.current.note_mgr
    
        hold_tex = self._assets["hold"]
        base_h = hold_tex.height if isinstance(hold_tex, arcade.Texture) else hold_tex.keyframes[0].texture.height
        px_length = self.sustain_length * note_mgr.pixels_per_ms
        count = math.ceil(px_length / (base_h * self.scale_y))
        
        for i in range(count):
            seg = HoldSegment(self, i, hold_tex, base_h, self.scale_y)
            note_mgr.sustains[self.direction_index].append(seg)
            self._segments.append(seg)
        
        if self._segments:
            self._segments[-1].texture = self._assets["end"]

    def despawn(self):
        self.remove_from_sprite_lists()
        for seg in self._segments:
            seg.remove_from_sprite_lists()

class NoteManager:
    def __init__(self, song_data: dict):
        self._song_data = song_data
        self.pixels_per_ms = 0.45 * song_data["speed"]
        self._note_assets = {}
        self._note_settings = {}
        self._load_resources()

        self.notes = arcade.SpriteList()
        self.sustains = {i: arcade.SpriteList() for i in range(8)}
        self._chart = []
        self._parse_chart()
        
        self.spawn_lead_ms = 2000
        self._next_spawn_idx = 0
        
        with open("assets/config/judgements.json", 'r') as file:
            self._judgement_windows = json.load(file)
        self.hit_window_ms = max(self._judgement_windows.values())

    def _load_resources(self):
        types = {"default", "alt_animation"}
        for section in self._song_data.get("notes", []):
            for note in section.get("sectionNotes", []):
                if len(note) > 3 and isinstance(note[3], str): types.add(note[3])
        
        for type_name in types:
            with open(f"assets/ui/notes/{type_name}/data.json", 'r') as file:
                self._note_settings[type_name] = json.load(file)
            self._note_assets[type_name] = {}
            for direction in ["left", "down", "up", "right"]:
                self._note_assets[type_name][direction] = {}
                for part in ["head", "hold", "end"]:
                    path = pathlib.Path(self._note_settings[type_name]["paths"][direction][part])
                    self._note_assets[type_name][direction][part] = (
                        arcade.load_animated_gif(str(path)).animation if path.suffix == ".gif" 
                        else arcade.load_texture(str(path))
                    )

    def _parse_chart(self):
        for section in self._song_data["notes"]:
            for raw_note in section["sectionNotes"]:
                lane = raw_note[1] % 4
                side = (0 if raw_note[1] < 4 else 4) if section["mustHitSection"] else (4 if raw_note[1] < 4 else 0)
                note_type = raw_note[3] if len(raw_note) > 3 else "default"
                # load must_hit_note and penalty_note from note_type settings
                note_settings = self._note_settings.get(note_type, self._note_settings.get("default", {}))
                must_hit = note_settings.get("must_hit_note", True)
                is_penalty = note_settings.get("penaly_note", False)  # note: typo in original data
                self._chart.append({
                    "direction_index": lane + side,
                    "strum_time": raw_note[0],
                    "sustain_length": raw_note[2],
                    "note_type": note_type,
                    "must_hit_note": must_hit,
                    "penalty_note": is_penalty
                })
        self._chart.sort(key=lambda x: x["strum_time"])

    def _process_hit(self, direction_index : int, ms : int):
        candidates = [note for note in self.notes if not note.is_hit and not note.is_miss 
                      and note.direction_index == direction_index 
                      and abs(note.strum_time - ms) <= self.hit_window_ms]
        
        if not candidates:
            return None
        
        hit_note = min(candidates, key=lambda n: n.strum_time)
        hit_note.is_hit = True
        diff = abs(hit_note.strum_time - ms)
        
        for name, window in self._judgement_windows.items():
            if diff <= window:
                hit_note.judgement = name
                break
        
        return hit_note

    def _spawn_notes(self):
        from sources.views import MainGameView
        song_mgr = MainGameView.current.song_mgr
        while self._next_spawn_idx < len(self._chart):
            info = self._chart[self._next_spawn_idx]
            if info["strum_time"] > song_mgr.song_ms + self.spawn_lead_ms:
                break

            direction_name = ["left", "down", "up", "right"][info["direction_index"] % 4]
            new_note = Note(
                info["direction_index"], info["strum_time"], info["sustain_length"], info["note_type"],
                self._note_settings[info["note_type"]], self._note_assets[info["note_type"]][direction_name],
                info["must_hit_note"], info["penalty_note"]
            )
            self.notes.append(new_note)
            self._next_spawn_idx += 1

    def _opponent_input(self):
        from sources.views import MainGameView
        song_mgr = MainGameView.current.song_mgr
    
        song_ms = song_mgr.song_ms
        for note in self.notes:
            if note.is_opponent:
                # fire press event once when the note becomes active
                if not note._pressed and song_ms >= note.strum_time:
                    note._pressed = True
                    note.is_hit = True
                    note.judgement = "auto"
                    bus.publish("opponent_pressed", direction_index=note.direction_index, note=note)
                # fire release event once after sustain ends
                if not note._released and song_ms > note.strum_time + note.sustain_length:
                    note._released = True
                    bus.publish("opponent_released", direction_index=note.direction_index)
                continue
    
    def _draw_sustains(self):
        from sources.views import MainGameView
        camera_mgr = MainGameView.current.camera_mgr
        receptor_mgr = MainGameView.current.receptor_mgr
    
        win = arcade.get_window()
        zoom = camera_mgr.camera_note.zoom
        offset_x, offset_y = (win.width / 2) * (1 - zoom), (win.height / 2) * (1 - zoom)

        for i, sustain_list in self.sustains.items():
            receptor = receptor_mgr.receptors[i]
            rad = math.radians(-receptor.angle + 90)
            
            cx = (receptor.center_x * zoom) + offset_x
            cy = (receptor.center_y * zoom - math.sin(rad) * receptor.texture.height * zoom * 0.3) + offset_y
            dx, dy = cx - math.cos(rad) * (2000 * zoom), cy - math.sin(rad) * (2000 * zoom)
            
            hold_width = self._note_assets["default"]["left"]["hold"].width
            bx, by, bw, bh = calculate_line_bounds((cx, cy), (dx, dy), (hold_width * 2) * zoom, (hold_width * 4) * zoom, 0)

            if len(sustain_list) > 0:
                if sustain_list[0].parent_note.is_hit:
                    arcade.get_window().ctx.scissor = (int(bx), int(by), int(bw), int(bh))
                    sustain_list.draw()
                    arcade.get_window().ctx.scissor = None
                else:
                    sustain_list.draw()

    def on_key_press(self, direction_index: int):
        from sources.views import MainGameView
        song_mgr = MainGameView.current.song_mgr
        
        note = self._process_hit(direction_index, song_mgr.song_ms)
        bus.publish("player_pressed", direction_index=direction_index, note=note)

    def on_key_release(self, direction_index: int):
        from sources.views import MainGameView
        song_mgr = MainGameView.current.song_mgr

        song_ms = song_mgr.song_ms
        bus.publish("player_released", direction_index=direction_index)

        for note in self.notes:
            if (not note.is_opponent and note.direction_index == direction_index and 
                note.is_hit and not note.is_released_early and 
                note.strum_time <= song_ms < note.strum_time + note.sustain_length):
                
                note.is_released_early = True
                note.set_visual_miss()
                bus.publish("player_note_miss", note=note)
                break

    def update(self, delta_time: float):
        from sources.views import MainGameView
        song_mgr = MainGameView.current.song_mgr

        self._spawn_notes()
        self._opponent_input()

        self.notes.update(delta_time)
        self.notes.update_animation(delta_time)
        for sustain_list in self.sustains.values():
            sustain_list.update(delta_time)

        # Apply visual miss for player notes in the update loop so misses
        # always get their visual state even if no explicit input release occurs.
        song_ms = song_mgr.song_ms
        for note in list(self.notes):
            if not note.is_opponent and not note.is_hit and not note.is_miss:
                if song_ms > note.strum_time + self.hit_window_ms:
                    note.is_miss = True
                    note.set_visual_miss()
                    # only publish miss event if this is a must-hit note
                    if note.must_hit_note:
                        bus.publish("player_note_miss", note=note)

    def draw(self):
        self._draw_sustains()
        self.notes.draw()