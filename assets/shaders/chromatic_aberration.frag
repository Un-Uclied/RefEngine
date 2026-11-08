#version 330
uniform sampler2D u_texture;
uniform float strength;
in vec2 uv;
out vec4 fragColor;

void main() {
    vec2 shift = (uv - 0.5) * strength;
    vec4 center = texture(u_texture, uv);
    fragColor = vec4(
        texture(u_texture, uv + shift).r,
        center.g,
        texture(u_texture, uv - shift).b,
        center.a
    );
}
