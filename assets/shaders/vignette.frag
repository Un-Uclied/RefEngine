#version 330
uniform sampler2D u_texture;
uniform float strength;
uniform float radius;
uniform float softness;
in vec2 uv;
out vec4 fragColor;

void main() {
    vec4 color = texture(u_texture, uv);
    float edge = smoothstep(radius - softness, radius, length((uv - 0.5) * 1.41421356));
    fragColor = vec4(color.rgb * (1.0 - strength * edge), color.a);
}
