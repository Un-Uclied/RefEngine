"""First chart editor: section grid, note types, holds and timed events.

구간별 노트·롱 노트·이벤트 편집기. 저장은 원본 변경을 확인한 뒤 원자적으로 수행합니다.
"""
import copy
import json
import math
import os
import tempfile
from pathlib import Path

import arcade
from sources.assets import BASE_ASSETS
from sources.fonts import FONT_NAME


class ChartDocument:
    def __init__(self, assets, chart_path):
        self.source = assets.path(chart_path)
        relative = Path(chart_path.replace("\\", "/"))
        if relative.parts[0] == "assets":
            relative = Path(*relative.parts[1:])
        self.path = assets.mod_root / relative if assets.mod_root else self.source
        self.original = self.source.read_bytes()
        self.target_original = self.path.read_bytes() if self.path.exists() else None
        self.data = json.loads(self.original)
        self.data.setdefault("events", [])
        self.saved = copy.deepcopy(self.data)
        self.undo_stack = []
        self.redo_stack = []

    @property
    def dirty(self):
        return self.data != self.saved

    def checkpoint(self):
        self.undo_stack.append(copy.deepcopy(self.data))
        self.redo_stack.clear()

    def undo(self, redo=False):
        source, target = (self.redo_stack, self.undo_stack) if redo else (self.undo_stack, self.redo_stack)
        if source:
            target.append(self.data)
            self.data = source.pop()

    def timeline(self):
        time, bpm = 0.0, self.data["bpm"]
        result = []
        for section in self.data["notes"]:
            if section.get("changeBPM"):
                bpm = section["bpm"]
            duration = section.get("lengthInSteps", 16) * 15000 / bpm
            result.append((time, duration, bpm))
            time += duration
        return result

    def save(self):
        current = self.path.read_bytes() if self.path.exists() else None
        if current != self.target_original:
            raise ValueError("파일이 외부에서 변경되었습니다. 덮어쓰지 않았습니다.")
        if self.path != self.source and self.source.read_bytes() != self.original:
            raise ValueError("기본 차트가 외부에서 변경되었습니다. 다시 열어 주세요.")
        payload = (json.dumps(self.data, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as file:
                file.write(payload)
            os.replace(name, self.path)
        finally:
            if os.path.exists(name):
                os.unlink(name)
        self.target_original = payload
        self.saved = copy.deepcopy(self.data)


class ChartEditor:
    def __init__(self, game):
        self.game = game
        self.doc = ChartDocument(game.assets, game._song_data["chart"])
        if not self.doc.data["notes"]:
            self.doc.data["notes"].append({"lengthInSteps": 16, "mustHitSection": True, "sectionNotes": []})
        self.section = 0
        self.snap = 4
        self.mode = "note"
        self.selected = None
        self.preview = False
        self.input_kind = None
        self.input_text = ""
        self.skip_text = False
        self.status = "왼쪽 클릭: 추가/선택 · 오른쪽 클릭: 삭제"
        self.exit_armed = False
        roots = [BASE_ASSETS] + ([game.assets.mod_root] if game.assets.mod_root else [])
        self.note_types = sorted({p.parent.name for root in roots for p in (root / "notes").glob("*/data.json")})
        self.event_types = sorted({p.stem for root in roots for p in (root / "scripts/events").glob("*.py")})
        self.note_type = "default"
        self.event_type = self.event_types[0] if self.event_types else ""

    def label(self, text, x, y, size=14, color=(215, 221, 235), heavy=False):
        arcade.draw_text(text, x, y, color, size, font_name=FONT_NAME, bold=heavy)

    def geometry(self):
        return 40, 90, min(620, self.game.window.width * 0.53), self.game.window.height - 190

    def draw(self):
        self.game.window.clear((19, 22, 32))
        x, y, width, height = self.geometry()
        timeline = self.doc.timeline()
        self.section = min(self.section, len(timeline) - 1)
        start, duration, bpm = timeline[self.section]
        section = self.doc.data["notes"][self.section]
        self.label("CHART EDITOR", 40, self.game.window.height - 48, 24, heavy=True)
        self.label(f"{self.game._song_data['name']}  {'● 수정됨' if self.doc.dirty else '저장됨'}", 340, self.game.window.height - 44)
        self.label(f"구간 {self.section + 1}/{len(timeline)} · {start/1000:.2f}s · {bpm:g} BPM · 1/{self.snap} beat", x, y + height + 16)
        cell = width / 9
        rows = max(1, round(duration / (60000 / bpm / self.snap)))
        for lane in range(9):
            arcade.draw_lbwh_rectangle_filled(x + lane * cell, y, cell - 1, height, (34 + lane % 2 * 8, 39, 55))
        for row in range(rows + 1):
            py = y + height - row / rows * height
            arcade.draw_line(x, py, x + width, py, (105, 113, 138) if row % self.snap == 0 else (51, 58, 76))
        self.label("레인 0–3: " + ("플레이어" if section["mustHitSection"] else "상대") + "   |   4–7: 반대편   |   이벤트", x, y - 25, 12)
        colors = [(194, 108, 241), (79, 177, 242), (106, 221, 139), (244, 115, 135)]
        for note in section["sectionNotes"]:
            px = x + (note[1] + 0.5) * cell
            py = y + height - (note[0] - start) / duration * height
            if not y <= py <= y + height:
                continue
            end_y = max(y, py - note[2] / duration * height)
            arcade.draw_line(px, py, px, end_y, colors[note[1] % 4], 7)
            arcade.draw_circle_filled(px, py, 10, (255, 255, 255) if note is self.selected else colors[note[1] % 4])
            if len(note) > 3 and note[3] != "default":
                self.label(note[3][:8], px - 22, py + 12, 9)
        for event in self.doc.data["events"]:
            if start <= event["time"] < start + duration:
                py = y + height - (event["time"] - start) / duration * height
                arcade.draw_circle_filled(x + 8.5 * cell, py, 9, (255, 255, 255) if event is self.selected else (255, 199, 85))
        if self.preview:
            py = y + height - (self.game.song_mgr.song_ms - start) / duration * height
            arcade.draw_line(x, py, x + width, py, (255, 255, 255), 2)
        side = x + width + 35
        lines = [f"모드: {'노트' if self.mode == 'note' else '이벤트'} (Tab)",
                 f"타입: {self.note_type if self.mode == 'note' else self.event_type} (T)",
                 "PageUp/Down · 휠: 구간 이동", "[ / ]: 스냅 해상도", "+ / -: 선택 노트 길이", "Delete: 선택 삭제",
                 "H: 구간의 플레이어/상대 전환", "A: 마지막에 구간 추가", "B: 기본 BPM · V: 노트 속도",
                 "P: 이벤트 JSON 매개변수", "Space: 이 구간부터 오디오 미리듣기", "Ctrl+S: 저장 · Ctrl+Z/Y: 실행 취소/복원",
                 "Esc: 게임 처음부터 다시 로드"]
        for index, line in enumerate(lines):
            self.label(line, side, y + height - index * 29, 12)
        if isinstance(self.selected, dict):
            self.label(json.dumps(self.selected.get("params", {}), ensure_ascii=False)[:64], side, y + 48, 11)
        self.label(self.status, 40, 40, 12)
        if self.input_kind:
            arcade.draw_lbwh_rectangle_filled(20, 15, self.game.window.width - 40, 100, (35, 42, 62))
            self.label(f"{self.input_kind} · Enter 적용 / Esc 취소", 40, 82, 14)
            self.label(self.input_text[-100:] + "|", 40, 45, 14)

    def click(self, px, py, button):
        self.exit_armed = False
        if self.input_kind or self.preview:
            return
        x, y, width, height = self.geometry()
        if not (x <= px < x + width and y < py <= y + height):
            return
        start, duration, bpm = self.doc.timeline()[self.section]
        lane = int((px - x) / (width / 9))
        step = 60000 / bpm / self.snap
        time = start + min(math.floor((y + height - py) / height * duration / step + 0.5), math.ceil(duration / step) - 1) * step
        section = self.doc.data["notes"][self.section]
        items = self.doc.data["events"] if lane == 8 else section["sectionNotes"]
        found = next((item for item in items if abs((item["time"] if lane == 8 else item[0]) - time) < step / 2 and (lane == 8 or item[1] == lane)), None)
        if found is not None:
            self.selected = found
            if button == arcade.MOUSE_BUTTON_RIGHT:
                self.doc.checkpoint()
                items.remove(found)
                self.selected = None
            return
        if button != arcade.MOUSE_BUTTON_LEFT:
            return
        if lane == 8 and not self.event_type:
            self.status = "assets/scripts/events/에 EventScript를 먼저 추가하세요."
            return
        self.doc.checkpoint()
        item = {"time": time, "script": self.event_type, "params": {}} if lane == 8 else [time, lane, 0, self.note_type]
        if lane == 8 and self.event_type == "shader_value":
            item["params"] = {"shader": "lens_distortion", "uniform": "strength", "value": 0.05, "duration": 0.5}
        items.append(item)
        self.selected = item

    def text(self, text):
        if self.skip_text:
            self.skip_text = False
            return
        if self.input_kind and text.isprintable():
            self.input_text += text

    def key(self, key, modifiers):
        if key != arcade.key.ESCAPE:
            self.exit_armed = False
        if self.input_kind:
            if modifiers & arcade.key.MOD_CTRL and key == arcade.key.A:
                self.input_text = ""
            elif key == arcade.key.ESCAPE:
                self.input_kind = None
            elif key == arcade.key.BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif key == arcade.key.ENTER:
                try:
                    value = json.loads(self.input_text)
                    if self.input_kind == "params":
                        if not isinstance(value, dict):
                            raise ValueError("JSON 객체가 필요합니다")
                    elif not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                        raise ValueError("0보다 큰 숫자를 입력하세요")
                    self.doc.checkpoint()
                    if self.input_kind == "params":
                        self.selected["params"] = value
                    else:
                        self.doc.data[self.input_kind] = value
                    self.input_kind = None
                except (ValueError, TypeError) as error:
                    self.status = str(error)
            return
        if self.preview and key not in (arcade.key.SPACE, arcade.key.ESCAPE):
            return
        ctrl = modifiers & arcade.key.MOD_CTRL
        if ctrl and key == arcade.key.S:
            try:
                self.doc.save()
                self.status = f"저장 완료: {self.doc.path.name}"
                self.exit_armed = False
            except (OSError, ValueError) as error:
                self.status = str(error)
        elif ctrl and key in (arcade.key.Z, arcade.key.Y):
            self.doc.undo(key == arcade.key.Y)
            self.selected = None
            self.section = min(self.section, len(self.doc.data["notes"]) - 1)
        elif key == arcade.key.ESCAPE:
            if self.doc.dirty and not self.exit_armed:
                self.exit_armed = True
                self.status = "저장하지 않은 변경이 있습니다. Ctrl+S 저장 / Esc 다시 누르면 버리고 나가기"
            else:
                self.game.restart()
        elif key == arcade.key.SPACE:
            self.selected = None
            if self.preview:
                self.game.song_mgr.pause()
            else:
                self.game.song_mgr._pause_time = self.doc.timeline()[self.section][0]
                self.game.song_mgr.resume()
            self.preview = not self.preview
        elif key in (arcade.key.PAGEUP, arcade.key.PAGEDOWN):
            self.section = max(0, min(len(self.doc.data["notes"]) - 1, self.section + (1 if key == arcade.key.PAGEDOWN else -1)))
            self.selected = None
        elif key in (arcade.key.BRACKETLEFT, arcade.key.BRACKETRIGHT):
            snaps = [1, 2, 3, 4, 6, 8, 12, 16]
            self.snap = snaps[max(0, min(len(snaps) - 1, snaps.index(self.snap) + (1 if key == arcade.key.BRACKETRIGHT else -1)))]
        elif key == arcade.key.TAB:
            self.mode = "event" if self.mode == "note" else "note"
        elif key == arcade.key.T:
            choices = self.note_types if self.mode == "note" else self.event_types
            if choices:
                old = self.note_type if self.mode == "note" else self.event_type
                value = choices[(choices.index(old) + 1) % len(choices)]
                if self.mode == "note":
                    self.note_type = value
                    if isinstance(self.selected, list):
                        self.doc.checkpoint()
                        self.selected[3:] = [value]
                else:
                    self.event_type = value
                    if isinstance(self.selected, dict):
                        self.doc.checkpoint()
                        self.selected["script"] = value
        elif key in (arcade.key.B, arcade.key.V, arcade.key.P):
            if key == arcade.key.P and not isinstance(self.selected, dict):
                return
            self.input_kind = {arcade.key.B: "bpm", arcade.key.V: "speed", arcade.key.P: "params"}[key]
            self.input_text = json.dumps(self.selected.get("params", {}) if key == arcade.key.P else self.doc.data[self.input_kind])
            self.skip_text = True
        elif key == arcade.key.DELETE and self.selected is not None:
            self.doc.checkpoint()
            (self.doc.data["events"] if isinstance(self.selected, dict) else self.doc.data["notes"][self.section]["sectionNotes"]).remove(self.selected)
            self.selected = None
        elif key in (arcade.key.MINUS, arcade.key.EQUAL, arcade.key.PLUS) and isinstance(self.selected, list):
            self.doc.checkpoint()
            self.selected[2] = max(0, self.selected[2] + (1 if key != arcade.key.MINUS else -1) * 60000 / self.doc.timeline()[self.section][2] / self.snap)
        elif key == arcade.key.H:
            self.doc.checkpoint()
            section = self.doc.data["notes"][self.section]
            section["mustHitSection"] = not section["mustHitSection"]
        elif key == arcade.key.A:
            self.doc.checkpoint()
            self.doc.data["notes"].append({"lengthInSteps": 16, "mustHitSection": True, "sectionNotes": []})
            self.section = len(self.doc.data["notes"]) - 1
            self.selected = None

    def update(self):
        if self.preview:
            time = self.game.song_mgr.song_ms
            for index, (start, duration, _) in enumerate(self.doc.timeline()):
                if start <= time < start + duration:
                    self.section = index
                    break
