#version 330
uniform sampler2D u_texture;
uniform vec2 u_resolution;
uniform float strength;
uniform float threshold;
uniform float radius;
in vec2 uv;
out vec4 fragColor;

vec3 bright(vec3 color) {
    float luminance = dot(color, vec3(0.2126, 0.7152, 0.0722));
    return color * smoothstep(threshold - 0.1, threshold + 0.1, luminance);
}

void main() {
    vec4 base = texture(u_texture, uv);
    vec2 step_uv = vec2(radius) / u_resolution;
    vec3 glow = vec3(0.0);
    for (int y = -1; y <= 1; y++) {
        for (int x = -1; x <= 1; x++) {
            glow += bright(texture(u_texture, uv + vec2(x, y) * step_uv).rgb);
        }
    }
    fragColor = vec4(clamp(base.rgb + glow * (strength / 9.0), 0.0, 1.0), base.a);
}
