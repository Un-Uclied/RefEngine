#version 330
uniform sampler2D u_texture;
uniform vec2 u_resolution;
uniform float u_time;
uniform float scanline_strength;
uniform float noise_strength;
uniform float jitter_strength;
in vec2 uv;
out vec4 fragColor;

float hash(vec2 value) {
    return fract(sin(dot(value, vec2(12.9898, 78.233))) * 43758.5453);
}

void main() {
    float row = floor(uv.y * u_resolution.y / 48.0);
    float jitter = (hash(vec2(row, floor(u_time * 12.0))) - 0.5) * jitter_strength;
    vec4 color = texture(u_texture, clamp(uv + vec2(jitter, 0.0), 0.0, 1.0));
    float scanline = 0.5 + 0.5 * sin(uv.y * u_resolution.y * 3.14159265);
    float grain = hash(floor(uv * u_resolution) + floor(u_time * 30.0));
    color.rgb = clamp(color.rgb * (1.0 - scanline_strength * scanline)
                      + (grain - 0.5) * noise_strength, 0.0, 1.0);
    fragColor = color;
}
