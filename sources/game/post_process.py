"""Song-selected fullscreen shaders. / 곡별 전체 화면 셰이더."""

import arcade


VERTEX_SHADER = """#version 330
in vec2 in_vert;
in vec2 in_uv;
out vec2 uv;
void main() {
    gl_Position = vec4(in_vert, 0.0, 1.0);
    uv = in_uv;
}
"""


class PostProcessManager:
    """Render a song's ordered shaders, resolving GLSL through AssetStore.

    곡의 shaders 순서대로 화면 효과를 적용하며, GLSL은 모드 애셋을 우선합니다.
    """

    def __init__(self, effects, assets):
        self.ctx = arcade.get_window().ctx
        self.geometry = arcade.gl.geometry.quad_2d_fs()
        self.effects = []
        self._textures = []
        self._buffers = []
        self._size = None
        if not isinstance(effects, list):
            raise ValueError("Song 'shaders' must be a list")
        for effect in effects:
            if not isinstance(effect, dict) or not isinstance(effect.get("name"), str):
                raise ValueError("Each shader needs a string 'name'")
            name = effect["name"]
            assets._check_name(name)
            uniforms = effect.get("uniforms", {})
            if not isinstance(uniforms, dict):
                raise ValueError(f"Shader {name!r} 'uniforms' must be an object")
            path = assets.path(f"shaders/{name}.frag")
            try:
                program = self.ctx.program(vertex_shader=VERTEX_SHADER,
                                           fragment_shader=path.read_text(encoding="utf-8"))
                program["u_texture"] = 0
                for key, value in uniforms.items():
                    if not isinstance(key, str) or not isinstance(value, (int, float, list)):
                        raise ValueError(f"Invalid uniform {key!r} for shader {name!r}")
                    program[key] = value
            except Exception as error:
                raise ValueError(f"Shader {name!r} ({path}): {error}") from error
            self.effects.append(program)

    def _ensure_buffers(self):
        size = arcade.get_window().get_framebuffer_size()
        if size == self._size:
            return
        for buffer in self._buffers:
            buffer.delete()
        for texture in self._textures:
            texture.delete()
        self._size = size
        self._textures = [self.ctx.texture(size, components=4,
                                           wrap_x=self.ctx.CLAMP_TO_EDGE,
                                           wrap_y=self.ctx.CLAMP_TO_EDGE)
                          for _ in range(2)]
        self._buffers = [self.ctx.framebuffer(color_attachments=[texture])
                         for texture in self._textures]

    def begin(self):
        """Capture scene drawing. / 화면 그리기를 텍스처에 담기 시작합니다."""
        self._ensure_buffers()
        self._buffers[0].use()
        self._buffers[0].clear(color=(0, 0, 0, 255))

    def finish(self):
        """Apply effects in order and present. / 순서대로 효과를 적용합니다."""
        for index, program in enumerate(self.effects):
            target = (index + 1) % 2
            if index == len(self.effects) - 1:
                self.ctx.screen.use()
            else:
                self._buffers[target].use()
            self.ctx.viewport = (0, 0, *self._size)
            self._textures[index % 2].use(0)
            self.geometry.render(program)

    def on_hide_view(self):
        for buffer in self._buffers:
            buffer.delete()
        for texture in self._textures:
            texture.delete()
        for program in self.effects:
            program.delete()
        self._buffers.clear()
        self._textures.clear()
        self._size = None
