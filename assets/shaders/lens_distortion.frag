#version 330
uniform sampler2D u_texture;
uniform float strength;
in vec2 uv;
out vec4 fragColor;

void main() {
    vec2 centered = uv * 2.0 - 1.0;
    vec2 warped = (centered * (1.0 + strength * dot(centered, centered))) * 0.5 + 0.5;
    fragColor = any(lessThan(warped, vec2(0.0))) || any(greaterThan(warped, vec2(1.0)))
        ? vec4(0.0, 0.0, 0.0, 1.0)
        : texture(u_texture, warped);
}
