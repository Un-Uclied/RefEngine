#version 330
uniform sampler2D u_texture;
uniform float u_time;
uniform float strength;
uniform float waves;
uniform float speed;
uniform float cycle_speed;
in vec2 uv;
out vec4 fragColor;

void main() {
    float pulse = sin(u_time * cycle_speed);
    float offset = sin(uv.y * waves * 6.2831853 + u_time * speed) * strength * pulse;
    fragColor = texture(u_texture, clamp(uv + vec2(offset, 0.0), 0.0, 1.0));
}
