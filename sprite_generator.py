"""Create RefEngine character data from GIF animations. Run: python sprite_generator.py"""
import json
import math
import re
import shutil
import tempfile
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image


ROOT = Path(__file__).resolve().parent
ANIMATION_NAMES = (
    "idle", "sing_left", "sing_down", "sing_up", "sing_right",
    "sing_left_alt", "sing_down_alt", "sing_up_alt", "sing_right_alt",
)
RESERVED_CHARACTER = {"name", "description", "is_player_character", "camera_offset", "scale", "animations"}
RESERVED_ANIMATION = {"path", "animation_speed", "offset", "loop"}


def number(value, label, *, positive=False):
    result = float(value)
    if not math.isfinite(result) or (positive and result <= 0):
        raise ValueError(f"{label} must be a finite {'positive ' if positive else ''}number")
    return result


def extra_fields(value, reserved):
    fields = json.loads(value.strip() or "{}")
    if not isinstance(fields, dict):
        raise ValueError("Custom properties must be a JSON object")
    overlap = reserved & fields.keys()
    if overlap:
        raise ValueError(f"Custom properties cannot replace {', '.join(sorted(overlap))}")
    return fields


def save_character(root, name, description, is_player, scale, camera_offset, animations, custom):
    if not name or name in (".", "..") or "/" in name or "\\" in name or ":" in name:
        raise ValueError("Character name must be one folder name")
    if "idle" not in animations:
        raise ValueError("Add an idle animation before generating")
    output_dir = root / "assets" / "characters" / name
    root_json = root / f"{name}.json"
    if output_dir.exists() or root_json.exists():
        raise FileExistsError(f"Output already exists for {name}. Choose a new character name.")

    data = {
        "name": name,
        "is_player_character": is_player,
        "description": description,
        "camera_offset": camera_offset,
        "scale": scale,
        "animations": {},
        **custom,
    }
    for animation_name, animation in animations.items():
        data["animations"][animation_name] = {
            "path": f"assets/characters/{name}/{animation_name}.gif",
            "animation_speed": animation["speed"],
            "offset": animation["offset"],
            "loop": animation["loop"],
            **animation["extra"],
        }

    # Stage all files before publishing either JSON path.
    with tempfile.TemporaryDirectory(dir=root) as temporary:
        staged = Path(temporary) / name
        staged.mkdir()
        for animation_name, animation in animations.items():
            shutil.copy2(animation["file"], staged / f"{animation_name}.gif")
        payload = json.dumps(data, ensure_ascii=False, indent=4) + "\n"
        (staged / "data.json").write_text(payload, encoding="utf-8")
        staged.replace(output_dir)
        root_json.write_text(payload, encoding="utf-8")
    return root_json, output_dir


class SpriteGenerator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RefEngine Sprite Generator")
        self.geometry("860x710")
        self.animations = {}

        self.character_name = tk.StringVar()
        self.description = tk.StringVar()
        self.scale = tk.StringVar(value="0.5")
        self.camera_x = tk.StringVar(value="0")
        self.camera_y = tk.StringVar(value="0")
        self.is_player = tk.BooleanVar(value=True)
        self.animation_name = tk.StringVar(value="idle")
        self.gif_path = tk.StringVar()
        self.speed = tk.StringVar(value="1")
        self.offset_x = tk.StringVar(value="0")
        self.offset_y = tk.StringVar(value="0")
        self.loop = tk.BooleanVar()

        character = ttk.LabelFrame(self, text="Character")
        character.pack(fill="x", padx=10, pady=6)
        self._field(character, "Name", self.character_name, 0, 0)
        self._field(character, "Description", self.description, 0, 2)
        self._field(character, "Scale", self.scale, 1, 0)
        self._field(character, "Camera X", self.camera_x, 1, 2)
        self._field(character, "Camera Y", self.camera_y, 1, 4)
        ttk.Checkbutton(character, text="Player character", variable=self.is_player).grid(row=2, column=0, columnspan=2, sticky="w", padx=6, pady=4)
        ttk.Label(character, text="Extra character properties (JSON object)").grid(row=3, column=0, columnspan=6, sticky="w", padx=6)
        self.character_extra = tk.Text(character, height=2)
        self.character_extra.insert("1.0", "{}")
        self.character_extra.grid(row=4, column=0, columnspan=6, sticky="ew", padx=6, pady=4)
        character.columnconfigure(5, weight=1)

        animation = ttk.LabelFrame(self, text="Animation — use *_alt names for alternate singing")
        animation.pack(fill="x", padx=10, pady=6)
        ttk.Label(animation, text="Name").grid(row=0, column=0, sticky="w", padx=6)
        ttk.Combobox(animation, textvariable=self.animation_name, values=ANIMATION_NAMES, width=20).grid(row=0, column=1, sticky="ew", padx=6, pady=4)
        ttk.Label(animation, text="GIF").grid(row=1, column=0, sticky="w", padx=6)
        ttk.Entry(animation, textvariable=self.gif_path).grid(row=1, column=1, columnspan=4, sticky="ew", padx=6)
        ttk.Button(animation, text="Browse…", command=self.browse).grid(row=1, column=5, padx=6)
        self._field(animation, "Speed", self.speed, 2, 0)
        self._field(animation, "Offset X", self.offset_x, 2, 2)
        self._field(animation, "Offset Y", self.offset_y, 2, 4)
        ttk.Checkbutton(animation, text="Loop", variable=self.loop).grid(row=3, column=0, sticky="w", padx=6)
        ttk.Label(animation, text="Extra animation properties (JSON object)").grid(row=4, column=0, columnspan=6, sticky="w", padx=6)
        self.animation_extra = tk.Text(animation, height=2)
        self.animation_extra.insert("1.0", "{}")
        self.animation_extra.grid(row=5, column=0, columnspan=6, sticky="ew", padx=6, pady=4)
        ttk.Button(animation, text="Add / Update animation", command=self.add_animation).grid(row=6, column=0, columnspan=3, sticky="ew", padx=6, pady=6)
        ttk.Button(animation, text="Remove selected", command=self.remove_animation).grid(row=6, column=3, columnspan=3, sticky="ew", padx=6, pady=6)
        for column in (1, 3, 5):
            animation.columnconfigure(column, weight=1)

        self.tree = ttk.Treeview(self, columns=("name", "gif", "speed", "offset", "loop"), show="headings", height=8)
        for column, width in (("name", 160), ("gif", 350), ("speed", 80), ("offset", 100), ("loop", 60)):
            self.tree.heading(column, text=column.title())
            self.tree.column(column, width=width)
        self.tree.pack(fill="both", expand=True, padx=10, pady=6)
        self.tree.bind("<<TreeviewSelect>>", self.select_animation)
        ttk.Button(self, text="Generate character JSON and copy GIFs", command=self.generate).pack(fill="x", padx=10, pady=10)

    @staticmethod
    def _field(parent, label, variable, row, column):
        ttk.Label(parent, text=label).grid(row=row, column=column, sticky="w", padx=6)
        ttk.Entry(parent, textvariable=variable, width=16).grid(row=row, column=column + 1, sticky="ew", padx=6, pady=4)

    def browse(self):
        path = filedialog.askopenfilename(filetypes=[("GIF images", "*.gif")])
        if path:
            self.gif_path.set(path)

    def add_animation(self):
        try:
            name = self.animation_name.get().strip()
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", name):
                raise ValueError("Animation name must use letters, digits, and underscores")
            path = Path(self.gif_path.get())
            with Image.open(path) as image:
                if image.format != "GIF":
                    raise ValueError("Select a GIF image")
            item = {
                "file": path,
                "speed": number(self.speed.get(), "Animation speed", positive=True),
                "offset": [number(self.offset_x.get(), "Offset X"), number(self.offset_y.get(), "Offset Y")],
                "loop": self.loop.get(),
                "extra": extra_fields(self.animation_extra.get("1.0", "end"), RESERVED_ANIMATION),
            }
            self.animations[name] = item
            values = (name, path.name, item["speed"], item["offset"], item["loop"])
            if self.tree.exists(name):
                self.tree.item(name, values=values)
            else:
                self.tree.insert("", "end", iid=name, values=values)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            messagebox.showerror("Invalid animation", str(error))

    def select_animation(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        name = selected[0]
        item = self.animations[name]
        self.animation_name.set(name)
        self.gif_path.set(str(item["file"]))
        self.speed.set(str(item["speed"]))
        self.offset_x.set(str(item["offset"][0]))
        self.offset_y.set(str(item["offset"][1]))
        self.loop.set(item["loop"])
        self.animation_extra.delete("1.0", "end")
        self.animation_extra.insert("1.0", json.dumps(item["extra"], ensure_ascii=False))

    def remove_animation(self):
        for name in self.tree.selection():
            self.tree.delete(name)
            del self.animations[name]

    def generate(self):
        try:
            name = self.character_name.get().strip()
            custom = extra_fields(self.character_extra.get("1.0", "end"), RESERVED_CHARACTER)
            files = save_character(
                ROOT, name, self.description.get(), self.is_player.get(),
                number(self.scale.get(), "Scale", positive=True),
                [number(self.camera_x.get(), "Camera X"), number(self.camera_y.get(), "Camera Y")],
                self.animations, custom,
            )
            messagebox.showinfo("Created", f"JSON: {files[0]}\nCharacter assets: {files[1]}")
        except (OSError, ValueError, json.JSONDecodeError) as error:
            messagebox.showerror("Cannot generate character", str(error))


if __name__ == "__main__":
    SpriteGenerator().mainloop()
