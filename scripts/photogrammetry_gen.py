#!/usr/bin/env python3
"""
Photogrammetry Test Data Generator

Generates synthetic photo sets suitable for photogrammetry reconstruction.
Renders textured 3D scenes from multiple orbital camera positions and outputs
JPEG images with optional EXIF metadata and ground-truth camera poses.

Usage:
    python photogrammetry_gen.py --output ./photos --views 36
    python photogrammetry_gen.py --output ./photos --views 72 --scene multi --texture noise
    python photogrammetry_gen.py --output ./photos --views 36 --validate
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

# ── Texture Generation ─────────────────────────────────────────────


def _value_noise_2d(
    width: int, height: int, scale: float, seed: int = 0
) -> np.ndarray:
    """Generate 2D value noise using lattice-based interpolation."""
    rng = np.random.default_rng(seed)
    grid_w = int(width / scale) + 2
    grid_h = int(height / scale) + 2
    lattice = rng.random((grid_h, grid_w)).astype(np.float32)

    y_coords = np.arange(height, dtype=np.float32) / scale
    x_coords = np.arange(width, dtype=np.float32) / scale

    y0 = np.floor(y_coords).astype(int)
    x0 = np.floor(x_coords).astype(int)
    fy = (y_coords - y0).reshape(-1, 1)
    fx = (x_coords - x0).reshape(1, -1)

    # Smoothstep interpolation
    fy = fy * fy * (3 - 2 * fy)
    fx = fx * fx * (3 - 2 * fx)

    v00 = lattice[y0][:, x0]
    v10 = lattice[y0 + 1][:, x0]
    v01 = lattice[y0][:, x0 + 1]
    v11 = lattice[y0 + 1][:, x0 + 1]

    top = v00 * (1 - fx) + v01 * fx
    bottom = v10 * (1 - fx) + v11 * fx
    return top * (1 - fy) + bottom * fy


def _fractal_noise(
    width: int, height: int, octaves: int = 4, base_scale: float = 50.0,
    seed: int = 0,
) -> np.ndarray:
    """Stack multiple octaves of value noise for fractal detail."""
    result = np.zeros((height, width), dtype=np.float32)
    amplitude = 1.0
    total_amp = 0.0
    scale = base_scale
    for i in range(octaves):
        result += amplitude * _value_noise_2d(width, height, scale, seed + i * 1000)
        total_amp += amplitude
        amplitude *= 0.5
        scale *= 0.5
    return result / total_amp


def generate_texture(
    width: int = 1024, height: int = 1024, style: str = "noise",
    seed: int = 42,
) -> np.ndarray:
    """Generate a procedural texture as RGB uint8 array (H, W, 3)."""
    if style == "noise":
        return _texture_noise(width, height, seed)
    elif style == "checker":
        return _texture_checker(width, height, seed)
    elif style == "stone":
        return _texture_stone(width, height, seed)
    elif style == "grid":
        return _texture_grid(width, height, seed)
    else:
        raise ValueError(f"Unknown texture style: {style}")


def _texture_noise(w: int, h: int, seed: int) -> np.ndarray:
    """Perlin-like noise with color tinting."""
    rng = np.random.default_rng(seed + 100)
    n = _fractal_noise(w, h, octaves=5, base_scale=60.0, seed=seed)
    # Color tint: warm earth tones
    base_color = rng.random(3).astype(np.float32) * 0.4 + 0.3
    img = np.stack([n * base_color[i] + (1 - n) * (base_color[i] * 0.5)
                    for i in range(3)], axis=-1)
    return np.clip(img * 255, 0, 255).astype(np.uint8)


def _texture_checker(w: int, h: int, seed: int) -> np.ndarray:
    """Checkerboard with color variation per cell."""
    rng = np.random.default_rng(seed + 200)
    cell_size = max(w, h) // 16
    rows = h // cell_size + 1
    cols = w // cell_size + 1
    colors = rng.integers(80, 220, size=(rows, cols, 3)).astype(np.uint8)

    img = np.zeros((h, w, 3), dtype=np.uint8)
    for cy in range(rows):
        for cx in range(cols):
            y0, y1 = cy * cell_size, min((cy + 1) * cell_size, h)
            x0, x1 = cx * cell_size, min((cx + 1) * cell_size, w)
            if (cy + cx) % 2 == 0:
                img[y0:y1, x0:x1] = colors[cy, cx]
            else:
                img[y0:y1, x0:x1] = 255 - colors[cy, cx]
    return img


def _texture_stone(w: int, h: int, seed: int) -> np.ndarray:
    """Rock-like texture using fractal noise with color mapping."""
    n = _fractal_noise(w, h, octaves=6, base_scale=40.0, seed=seed)
    # Map to stone colors (gray-brown range)
    r = np.clip(n * 140 + 60, 0, 255).astype(np.uint8)
    g = np.clip(n * 130 + 55, 0, 255).astype(np.uint8)
    b = np.clip(n * 110 + 50, 0, 255).astype(np.uint8)
    return np.stack([r, g, b], axis=-1)


def _texture_grid(w: int, h: int, seed: int) -> np.ndarray:
    """Numbered grid (useful for debugging UV mapping)."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (w, h), (240, 240, 240))
    draw = ImageDraw.Draw(img)

    cell_size = max(w, h) // 8
    rng = np.random.default_rng(seed + 300)

    for cy in range(h // cell_size + 1):
        for cx in range(w // cell_size + 1):
            y0, y1 = cy * cell_size, min((cy + 1) * cell_size, h)
            x0, x1 = cx * cell_size, min((cx + 1) * cell_size, w)
            color = tuple(rng.integers(100, 220, size=3).tolist())
            draw.rectangle([x0, y0, x1, y1], fill=color, outline=(40, 40, 40))
            label = f"{cy},{cx}"
            draw.text((x0 + 4, y0 + 4), label, fill=(0, 0, 0))

    return np.array(img)


# ── Scene Geometry ─────────────────────────────────────────────────


def _make_cube() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Create a textured cube (vertices, normals, uvs, indices)."""
    # 6 faces, 4 vertices each = 24 vertices
    verts = []
    norms = []
    uvs = []
    idxs = []

    faces = [
        # (normal, up, right, center_offset)
        ([0, 0, 1], [0, 1, 0], [1, 0, 0], [0, 0, 0.5]),   # front
        ([0, 0, -1], [0, 1, 0], [-1, 0, 0], [0, 0, -0.5]), # back
        ([1, 0, 0], [0, 1, 0], [0, 0, -1], [0.5, 0, 0]),   # right
        ([-1, 0, 0], [0, 1, 0], [0, 0, 1], [-0.5, 0, 0]),  # left
        ([0, 1, 0], [0, 0, -1], [1, 0, 0], [0, 0.5, 0]),   # top
        ([0, -1, 0], [0, 0, 1], [1, 0, 0], [0, -0.5, 0]),  # bottom
    ]

    for fi, (n, up, right, center) in enumerate(faces):
        n, up, right, center = map(np.array, [n, up, right, center])
        base = fi * 4
        corners = [
            center - 0.5 * right - 0.5 * up,
            center + 0.5 * right - 0.5 * up,
            center + 0.5 * right + 0.5 * up,
            center - 0.5 * right + 0.5 * up,
        ]
        verts.extend(corners)
        norms.extend([n] * 4)
        uvs.extend([(0, 0), (1, 0), (1, 1), (0, 1)])
        idxs.extend([base, base + 1, base + 2, base, base + 2, base + 3])

    return (
        np.array(verts, dtype=np.float32),
        np.array(norms, dtype=np.float32),
        np.array(uvs, dtype=np.float32),
        np.array(idxs, dtype=np.int32),
    )


def _make_sphere(segments: int = 24, rings: int = 16) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Create a UV sphere with procedural texture coordinates."""
    verts, norms, uvs, idxs = [], [], [], []
    radius = 0.5

    for j in range(rings + 1):
        theta = math.pi * j / rings
        for i in range(segments + 1):
            phi = 2 * math.pi * i / segments
            x = radius * math.sin(theta) * math.cos(phi)
            y = radius * math.cos(theta)
            z = radius * math.sin(theta) * math.sin(phi)
            nx, ny, nz = math.sin(theta) * math.cos(phi), math.cos(theta), math.sin(theta) * math.sin(phi)
            u, v = i / segments, j / rings
            verts.append([x, y, z])
            norms.append([nx, ny, nz])
            uvs.append([u, v])

    for j in range(rings):
        for i in range(segments):
            a = j * (segments + 1) + i
            b = a + segments + 1
            idxs.extend([a, b, a + 1, a + 1, b, b + 1])

    return (
        np.array(verts, dtype=np.float32),
        np.array(norms, dtype=np.float32),
        np.array(uvs, dtype=np.float32),
        np.array(idxs, dtype=np.int32),
    )


def _make_ground_plane(size: float = 3.0) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Create a textured ground plane."""
    s = size / 2
    verts = np.array([[-s, -0.5, -s], [s, -0.5, -s], [s, -0.5, s], [-s, -0.5, s]], dtype=np.float32)
    norms = np.array([[0, 1, 0]] * 4, dtype=np.float32)
    uvs = np.array([[0, 0], [3, 0], [3, 3], [0, 3]], dtype=np.float32)  # Tile texture
    idxs = np.array([0, 1, 2, 0, 2, 3], dtype=np.int32)
    return verts, norms, uvs, idxs


def _make_multi(seed: int = 42) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Create multiple primitives on a ground plane."""
    rng = np.random.default_rng(seed)
    all_v, all_n, all_u, all_i = [], [], [], []
    offset = 0

    # Ground plane
    gv, gn, gu, gi = _make_ground_plane(4.0)
    all_v.append(gv)
    all_n.append(gn)
    all_u.append(gu)
    all_i.append(gi)
    offset += len(gv)

    # Place 3-5 objects
    for _ in range(rng.integers(3, 6)):
        if rng.random() > 0.5:
            v, n, u, i = _make_cube()
        else:
            v, n, u, i = _make_sphere(16, 12)

        # Random scale and position
        scale = rng.uniform(0.2, 0.5)
        v = v * scale
        pos = rng.uniform(-1.2, 1.2, size=3).astype(np.float32)
        pos[1] = -0.5 + scale * 0.5  # Sit on ground
        v = v + pos

        all_v.append(v)
        all_n.append(n)
        all_u.append(u)
        all_i.append(i + offset)
        offset += len(v)

    return (
        np.concatenate(all_v),
        np.concatenate(all_n),
        np.concatenate(all_u),
        np.concatenate(all_i),
    )


def _make_terrain(size: float = 3.0, res: int = 32, seed: int = 42) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Create a heightmap terrain mesh."""
    heights = _fractal_noise(res + 1, res + 1, octaves=4, base_scale=8.0, seed=seed) * 0.5

    verts, norms, uvs, idxs = [], [], [], []
    step = size / res
    half = size / 2

    for j in range(res + 1):
        for i in range(res + 1):
            x = -half + i * step
            z = -half + j * step
            y = heights[j, i] - 0.5
            u, v = i / res, j / res
            verts.append([x, y, z])
            uvs.append([u * 3, v * 3])  # Tile texture

            # Approximate normal via finite differences
            h_l = heights[j, max(i - 1, 0)]
            h_r = heights[j, min(i + 1, res)]
            h_d = heights[max(j - 1, 0), i]
            h_u = heights[min(j + 1, res), i]
            nx = (h_l - h_r) / (2 * step)
            nz = (h_d - h_u) / (2 * step)
            norm = np.array([nx, 1.0, nz])
            norm = norm / np.linalg.norm(norm)
            norms.append(norm.tolist())

    for j in range(res):
        for i in range(res):
            a = j * (res + 1) + i
            b = a + res + 1
            idxs.extend([a, b, a + 1, a + 1, b, b + 1])

    return (
        np.array(verts, dtype=np.float32),
        np.array(norms, dtype=np.float32),
        np.array(uvs, dtype=np.float32),
        np.array(idxs, dtype=np.int32),
    )


def create_scene(
    scene_type: str = "cube", seed: int = 42,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Create a 3D scene. Returns (vertices, normals, uvs, indices)."""
    if scene_type == "cube":
        cv, cn, cu, ci = _make_cube()
        gv, gn, gu, gi = _make_ground_plane()
        gi = gi + len(cv)
        return (
            np.concatenate([cv, gv]),
            np.concatenate([cn, gn]),
            np.concatenate([cu, gu]),
            np.concatenate([ci, gi]),
        )
    elif scene_type == "sphere":
        sv, sn, su, si = _make_sphere()
        gv, gn, gu, gi = _make_ground_plane()
        gi = gi + len(sv)
        return (
            np.concatenate([sv, gv]),
            np.concatenate([sn, gn]),
            np.concatenate([su, gu]),
            np.concatenate([si, gi]),
        )
    elif scene_type == "multi":
        return _make_multi(seed)
    elif scene_type == "terrain":
        return _make_terrain(seed=seed)
    else:
        raise ValueError(f"Unknown scene type: {scene_type}")


# ── Camera ─────────────────────────────────────────────────────────


def _look_at(eye: np.ndarray, target: np.ndarray, up: np.ndarray) -> np.ndarray:
    """Compute a 4x4 view matrix (look-at)."""
    f = target - eye
    f = f / np.linalg.norm(f)
    s = np.cross(f, up)
    s = s / np.linalg.norm(s)
    u = np.cross(s, f)

    mat = np.eye(4, dtype=np.float32)
    mat[0, :3] = s
    mat[1, :3] = u
    mat[2, :3] = -f
    mat[0, 3] = -np.dot(s, eye)
    mat[1, 3] = -np.dot(u, eye)
    mat[2, 3] = np.dot(f, eye)
    return mat


def _perspective(fov_y_deg: float, aspect: float, near: float, far: float) -> np.ndarray:
    """Compute a 4x4 perspective projection matrix."""
    f = 1.0 / math.tan(math.radians(fov_y_deg) / 2.0)
    mat = np.zeros((4, 4), dtype=np.float32)
    mat[0, 0] = f / aspect
    mat[1, 1] = f
    mat[2, 2] = (far + near) / (near - far)
    mat[2, 3] = (2 * far * near) / (near - far)
    mat[3, 2] = -1.0
    return mat


def generate_camera_poses(
    n_views: int, n_orbits: int = 2, radius: float = 3.0,
    elevations: list[float] | None = None,
) -> list[dict[str, Any]]:
    """Generate orbital camera positions around the origin.

    Returns list of dicts with 'view_matrix', 'position', 'rotation_euler_deg'.
    """
    if elevations is None:
        if n_orbits == 1:
            elevations = [30.0]
        elif n_orbits == 2:
            elevations = [20.0, 50.0]
        else:
            elevations = [15.0 + i * (60.0 / (n_orbits - 1)) for i in range(n_orbits)]

    views_per_orbit = max(1, n_views // len(elevations))
    remainder = n_views - views_per_orbit * len(elevations)

    poses = []
    target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    up = np.array([0.0, 1.0, 0.0], dtype=np.float32)

    for oi, elev_deg in enumerate(elevations):
        n = views_per_orbit + (1 if oi < remainder else 0)
        elev_rad = math.radians(elev_deg)
        for vi in range(n):
            azimuth = 2 * math.pi * vi / n
            x = radius * math.cos(elev_rad) * math.cos(azimuth)
            z = radius * math.cos(elev_rad) * math.sin(azimuth)
            y = radius * math.sin(elev_rad)
            eye = np.array([x, y, z], dtype=np.float32)

            view_mat = _look_at(eye, target, up)

            # Euler angles (approximate)
            pitch = math.degrees(math.atan2(y, math.sqrt(x * x + z * z)))
            yaw = math.degrees(math.atan2(x, z))

            poses.append({
                "position": eye.tolist(),
                "rotation_euler_deg": [pitch, yaw, 0.0],
                "view_matrix": view_mat.tolist(),
            })

    return poses


# ── GPU Renderer (moderngl) ────────────────────────────────────────

VERTEX_SHADER = """
#version 330
uniform mat4 mvp;
in vec3 in_position;
in vec2 in_texcoord;
in vec3 in_normal;
out vec2 uv;
out vec3 normal;
out vec3 frag_pos;
void main() {
    gl_Position = mvp * vec4(in_position, 1.0);
    uv = in_texcoord;
    normal = in_normal;
    frag_pos = in_position;
}
"""

FRAGMENT_SHADER = """
#version 330
uniform sampler2D tex;
uniform vec3 light_dir;
in vec2 uv;
in vec3 normal;
in vec3 frag_pos;
out vec4 fragColor;
void main() {
    vec3 n = normalize(normal);
    float diffuse = max(dot(n, normalize(light_dir)), 0.0);
    float ambient = 0.3;
    vec3 color = texture(tex, uv).rgb * (ambient + 0.7 * diffuse);
    fragColor = vec4(color, 1.0);
}
"""


def render_gpu(
    verts: np.ndarray, norms: np.ndarray, uvs: np.ndarray,
    indices: np.ndarray, texture_data: np.ndarray,
    poses: list[dict], proj_mat: np.ndarray,
    width: int, height: int, seed: int = 42,
) -> list[np.ndarray]:
    """Render all views using moderngl (GPU). Returns list of RGB arrays."""
    import moderngl
    from PIL import Image

    ctx = moderngl.create_standalone_context()
    fbo = ctx.simple_framebuffer((width, height))
    fbo.use()

    prog = ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=FRAGMENT_SHADER)

    # Interleave vertex data: position(3) + texcoord(2) + normal(3)
    interleaved = np.hstack([verts, uvs, norms]).astype(np.float32)
    vbo = ctx.buffer(interleaved.tobytes())
    ibo = ctx.buffer(indices.astype(np.int32).tobytes())

    vao = ctx.vertex_array(
        prog,
        [(vbo, "3f 2f 3f", "in_position", "in_texcoord", "in_normal")],
        index_buffer=ibo,
    )

    # Upload texture
    tex_h, tex_w = texture_data.shape[:2]
    tex = ctx.texture((tex_w, tex_h), 3, texture_data.tobytes())
    tex.use(0)
    prog["tex"].value = 0

    ctx.enable(moderngl.DEPTH_TEST)

    images = []
    rng = np.random.default_rng(seed + 500)

    for i, pose in enumerate(poses):
        view_mat = np.array(pose["view_matrix"], dtype=np.float32)
        mvp = (proj_mat @ view_mat).astype(np.float32)
        prog["mvp"].write(mvp.T.tobytes())  # Column-major for OpenGL

        # Slightly vary light direction per view
        base_light = np.array([0.5, 0.8, 0.3], dtype=np.float32)
        jitter = rng.uniform(-0.05, 0.05, size=3).astype(np.float32)
        light = base_light + jitter
        light = light / np.linalg.norm(light)
        prog["light_dir"].value = tuple(light.tolist())

        fbo.clear(0.6, 0.7, 0.9, 1.0)
        vao.render()
        pixels = fbo.read(components=3)
        img = np.frombuffer(pixels, dtype=np.uint8).reshape(height, width, 3)
        img = img[::-1].copy()  # Flip vertically
        images.append(img)

    ctx.release()
    return images


# ── CPU Software Rasterizer (fallback) ─────────────────────────────


def render_cpu(
    verts: np.ndarray, norms: np.ndarray, uvs: np.ndarray,
    indices: np.ndarray, texture_data: np.ndarray,
    poses: list[dict], proj_mat: np.ndarray,
    width: int, height: int, seed: int = 42,
) -> list[np.ndarray]:
    """Pure numpy software rasterizer. Slower but works without GPU."""
    images = []
    rng = np.random.default_rng(seed + 500)
    tex_h, tex_w = texture_data.shape[:2]

    for pi, pose in enumerate(poses):
        view_mat = np.array(pose["view_matrix"], dtype=np.float32)
        mvp = proj_mat @ view_mat

        # Transform vertices to clip space
        v4 = np.hstack([verts, np.ones((len(verts), 1), dtype=np.float32)])
        clip = (mvp @ v4.T).T  # N x 4

        # Perspective divide
        w_clip = clip[:, 3:4]
        w_clip = np.where(np.abs(w_clip) < 1e-6, 1e-6, w_clip)
        ndc = clip[:, :3] / w_clip  # N x 3

        # NDC to screen
        sx = ((ndc[:, 0] + 1) * 0.5 * width).astype(np.float32)
        sy = ((1 - ndc[:, 1]) * 0.5 * height).astype(np.float32)  # Flip Y
        sz = ndc[:, 2]

        # Initialize framebuffer
        fb = np.full((height, width, 3), [153, 179, 230], dtype=np.uint8)  # Sky blue
        zbuf = np.full((height, width), np.inf, dtype=np.float32)

        # Light direction
        base_light = np.array([0.5, 0.8, 0.3], dtype=np.float32)
        jitter = rng.uniform(-0.05, 0.05, size=3).astype(np.float32)
        light = base_light + jitter
        light = light / np.linalg.norm(light)

        # Rasterize triangles
        tris = indices.reshape(-1, 3)
        for tri in tris:
            i0, i1, i2 = tri
            x0, y0, z0 = sx[i0], sy[i0], sz[i0]
            x1, y1, z1 = sx[i1], sy[i1], sz[i1]
            x2, y2, z2 = sx[i2], sy[i2], sz[i2]

            # Bounding box
            min_x = max(int(min(x0, x1, x2)), 0)
            max_x = min(int(max(x0, x1, x2)) + 1, width - 1)
            min_y = max(int(min(y0, y1, y2)), 0)
            max_y = min(int(max(y0, y1, y2)) + 1, height - 1)

            if min_x >= max_x or min_y >= max_y:
                continue

            # Skip triangles behind camera
            if z0 < -1 or z1 < -1 or z2 < -1:
                continue

            # Barycentric coordinates for the bounding box
            denom = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
            if abs(denom) < 1e-6:
                continue

            for py in range(min_y, max_y + 1):
                for px in range(min_x, max_x + 1):
                    w0 = ((y1 - y2) * (px - x2) + (x2 - x1) * (py - y2)) / denom
                    w1 = ((y2 - y0) * (px - x2) + (x0 - x2) * (py - y2)) / denom
                    w2 = 1 - w0 - w1

                    if w0 < 0 or w1 < 0 or w2 < 0:
                        continue

                    # Interpolate depth
                    z = w0 * z0 + w1 * z1 + w2 * z2
                    if z >= zbuf[py, px]:
                        continue
                    zbuf[py, px] = z

                    # Interpolate UV
                    u = w0 * uvs[i0, 0] + w1 * uvs[i1, 0] + w2 * uvs[i2, 0]
                    v = w0 * uvs[i0, 1] + w1 * uvs[i1, 1] + w2 * uvs[i2, 1]

                    # Sample texture (with wrapping)
                    tu = int(u % 1.0 * (tex_w - 1)) % tex_w
                    tv = int(v % 1.0 * (tex_h - 1)) % tex_h
                    tex_color = texture_data[tv, tu].astype(np.float32) / 255.0

                    # Interpolate normal and compute lighting
                    n = (w0 * norms[i0] + w1 * norms[i1] + w2 * norms[i2])
                    n_len = np.linalg.norm(n)
                    if n_len > 0:
                        n = n / n_len
                    diffuse = max(np.dot(n, light), 0.0)
                    ambient = 0.3
                    color = tex_color * (ambient + 0.7 * diffuse)
                    fb[py, px] = np.clip(color * 255, 0, 255).astype(np.uint8)

        images.append(fb)

    return images


# ── Output ─────────────────────────────────────────────────────────


def save_images(
    images: list[np.ndarray], output_dir: Path,
    write_exif: bool = False, focal_length_mm: float = 50.0,
) -> list[str]:
    """Save rendered images as JPEG files."""
    from PIL import Image

    filenames = []
    for i, img_data in enumerate(images):
        fname = f"IMG_{i:04d}.jpg"
        img = Image.fromarray(img_data, "RGB")

        if write_exif:
            from PIL.ExifTags import Base as ExifBase
            import struct

            exif = img.getexif()
            exif[ExifBase.Make] = "Synthetic"
            exif[ExifBase.Model] = "PhotogrammetryGen"
            exif[ExifBase.ImageWidth] = img.width
            exif[ExifBase.ImageLength] = img.height
            # FocalLength as rational
            fl_int = int(focal_length_mm * 100)
            exif[ExifBase.FocalLength] = (fl_int, 100)
            exif[ExifBase.DateTime] = datetime.now(timezone.utc).strftime("%Y:%m:%d %H:%M:%S")
            img.save(output_dir / fname, "JPEG", quality=95, exif=exif.tobytes())
        else:
            img.save(output_dir / fname, "JPEG", quality=95)

        filenames.append(fname)
    return filenames


def write_cameras_json(
    poses: list[dict], filenames: list[str],
    proj_mat: np.ndarray, focal_length_mm: float,
    width: int, height: int, output_dir: Path,
) -> None:
    """Write cameras.json with ground-truth poses."""
    # Standard full-frame sensor
    sensor_width_mm = 36.0
    sensor_height_mm = 24.0

    views = []
    for fname, pose in zip(filenames, poses):
        views.append({
            "filename": fname,
            "position": [round(v, 6) for v in pose["position"]],
            "rotation_euler_deg": [round(v, 2) for v in pose["rotation_euler_deg"]],
            "view_matrix": [[round(v, 6) for v in row] for row in pose["view_matrix"]],
            "projection_matrix": [[round(v, 6) for v in row] for row in proj_mat.tolist()],
        })

    data = {
        "camera_model": "PINHOLE",
        "focal_length_mm": focal_length_mm,
        "sensor_width_mm": sensor_width_mm,
        "sensor_height_mm": sensor_height_mm,
        "image_width": width,
        "image_height": height,
        "views": views,
    }

    (output_dir / "cameras.json").write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )


def write_scene_info(
    args: argparse.Namespace, output_dir: Path,
) -> None:
    """Write scene_info.json for reproducibility."""
    data = {
        "scene_type": args.scene,
        "texture_type": args.texture,
        "seed": args.seed,
        "views": args.views,
        "orbits": args.orbits,
        "elevations": args.elevation,
        "radius": args.radius,
        "resolution": f"{args.width}x{args.height}",
        "focal_length_mm": args.focal_length,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator": "photogrammetry_gen.py",
    }

    (output_dir / "scene_info.json").write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )


# ── Validation ─────────────────────────────────────────────────────


def validate_output(output_dir: Path, n_views: int, width: int, height: int) -> bool:
    """Run validation checks on generated output."""
    from PIL import Image

    all_pass = True

    def check(name: str, ok: bool, detail: str = "") -> None:
        nonlocal all_pass
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_pass = False
        msg = f"  [{status}] {name}"
        if detail:
            msg += f" — {detail}"
        print(msg)

    print("\nValidation:")

    # 1. All images saved and readable
    filenames = sorted(output_dir.glob("IMG_*.jpg"))
    check("Image count", len(filenames) == n_views,
          f"expected {n_views}, got {len(filenames)}")

    readable = 0
    for f in filenames:
        try:
            img = Image.open(f)
            img.verify()
            readable += 1
        except Exception:
            pass
    check("All images readable", readable == len(filenames),
          f"{readable}/{len(filenames)} readable")

    # 2. Image dimensions
    if filenames:
        img = Image.open(filenames[0])
        check("Image dimensions", img.size == (width, height),
              f"expected {width}x{height}, got {img.size[0]}x{img.size[1]}")

    # 3. Adjacent views have visual difference
    if len(filenames) >= 2:
        img0 = np.array(Image.open(filenames[0])).astype(np.float32)
        img1 = np.array(Image.open(filenames[1])).astype(np.float32)
        diff = np.mean(np.abs(img0 - img1))
        check("Adjacent views differ", diff > 1.0,
              f"mean pixel diff = {diff:.2f}")

    # 4. Texture entropy
    if filenames:
        img = np.array(Image.open(filenames[0]))
        # Simple entropy: std dev of pixel values
        entropy = np.std(img.astype(np.float32))
        check("Texture entropy", entropy > 15.0,
              f"std dev = {entropy:.2f}")

    # 5. cameras.json parseable and complete
    cam_path = output_dir / "cameras.json"
    check("cameras.json exists", cam_path.is_file())
    if cam_path.is_file():
        try:
            cam_data = json.loads(cam_path.read_text(encoding="utf-8"))
            n_cam_views = len(cam_data.get("views", []))
            check("cameras.json complete", n_cam_views == n_views,
                  f"expected {n_views} views, got {n_cam_views}")
        except Exception as e:
            check("cameras.json parseable", False, str(e))

    # 6. Camera positions form valid orbit
    if cam_path.is_file():
        try:
            cam_data = json.loads(cam_path.read_text(encoding="utf-8"))
            positions = [v["position"] for v in cam_data["views"]]
            if len(positions) >= 2:
                pos_arr = np.array(positions)
                # Check positions aren't all clustered
                spread = np.std(pos_arr, axis=0).sum()
                check("Camera positions spread", spread > 0.5,
                      f"position spread = {spread:.3f}")
        except Exception:
            pass

    # Scene info
    scene_path = output_dir / "scene_info.json"
    check("scene_info.json exists", scene_path.is_file())

    return all_pass


# ── Main ───────────────────────────────────────────────────────────


def parse_resolution(s: str) -> tuple[int, int]:
    """Parse 'WxH' resolution string."""
    parts = s.lower().split("x")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError(f"Invalid resolution: {s} (expected WxH)")
    return int(parts[0]), int(parts[1])


def parse_elevations(s: str) -> list[float]:
    """Parse comma-separated elevation angles."""
    return [float(x.strip()) for x in s.split(",")]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate synthetic photo sets for photogrammetry testing",
    )
    parser.add_argument("--output", type=Path, required=True,
                        help="Output directory for images and metadata")
    parser.add_argument("--views", type=int, default=36,
                        help="Number of views to render (default: 36)")
    parser.add_argument("--orbits", type=int, default=2,
                        help="Number of elevation rings (default: 2)")
    parser.add_argument("--elevation", type=parse_elevations, default=None,
                        help="Comma-separated elevation angles in degrees (e.g., '15,45,70')")
    parser.add_argument("--scene", choices=["cube", "sphere", "multi", "terrain"],
                        default="cube", help="Scene type (default: cube)")
    parser.add_argument("--texture", choices=["noise", "checker", "stone", "grid"],
                        default="noise", help="Texture style (default: noise)")
    parser.add_argument("--resolution", type=parse_resolution, default=(1920, 1080),
                        help="Image resolution WxH (default: 1920x1080)")
    parser.add_argument("--focal-length", type=float, default=50.0,
                        help="Focal length in mm (default: 50)")
    parser.add_argument("--radius", type=float, default=3.0,
                        help="Camera orbit radius (default: 3.0)")
    parser.add_argument("--exif", action="store_true",
                        help="Write EXIF metadata to JPEG files")
    parser.add_argument("--validate", action="store_true",
                        help="Run validation checks after generation")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--cpu", action="store_true",
                        help="Force CPU software rendering (no GPU)")
    args = parser.parse_args()

    args.width, args.height = args.resolution
    n_orbits = len(args.elevation) if args.elevation else args.orbits

    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)

    print(f"Photogrammetry Generator")
    print(f"  Scene: {args.scene}, Texture: {args.texture}")
    print(f"  Views: {args.views}, Orbits: {n_orbits}, Radius: {args.radius}")
    print(f"  Resolution: {args.width}x{args.height}, Focal: {args.focal_length}mm")
    print(f"  Seed: {args.seed}")
    print()

    # 1. Generate texture
    print("Generating texture...")
    tex_data = generate_texture(1024, 1024, style=args.texture, seed=args.seed)

    # 2. Create scene
    print(f"Creating {args.scene} scene...")
    verts, norms, uvs, indices = create_scene(args.scene, seed=args.seed)
    print(f"  {len(verts)} vertices, {len(indices) // 3} triangles")

    # 3. Generate camera poses
    print("Generating camera poses...")
    poses = generate_camera_poses(
        args.views, n_orbits, args.radius,
        elevations=args.elevation,
    )
    print(f"  {len(poses)} poses across {n_orbits} orbits")

    # 4. Compute projection matrix
    aspect = args.width / args.height
    # Convert focal length to FoV
    sensor_height_mm = 24.0
    fov_y = 2 * math.degrees(math.atan(sensor_height_mm / (2 * args.focal_length)))
    proj_mat = _perspective(fov_y, aspect, 0.1, 100.0)

    # 5. Render
    use_gpu = not args.cpu
    if use_gpu:
        try:
            import moderngl
            print("Rendering with GPU (moderngl)...")
            t0 = time.monotonic()
            images = render_gpu(
                verts, norms, uvs, indices, tex_data,
                poses, proj_mat, args.width, args.height, args.seed,
            )
            elapsed = time.monotonic() - t0
            print(f"  Rendered {len(images)} views in {elapsed:.1f}s")
        except Exception as e:
            print(f"  GPU rendering failed: {e}")
            print("  Falling back to CPU software renderer...")
            use_gpu = False

    if not use_gpu:
        print("Rendering with CPU (software rasterizer)...")
        print("  Warning: CPU rendering is much slower than GPU")
        t0 = time.monotonic()
        images = render_cpu(
            verts, norms, uvs, indices, tex_data,
            poses, proj_mat, args.width, args.height, args.seed,
        )
        elapsed = time.monotonic() - t0
        print(f"  Rendered {len(images)} views in {elapsed:.1f}s")

    # 6. Save images
    print("Saving images...")
    filenames = save_images(images, args.output, args.exif, args.focal_length)

    # 7. Write metadata
    print("Writing metadata...")
    write_cameras_json(poses, filenames, proj_mat, args.focal_length,
                       args.width, args.height, args.output)
    write_scene_info(args, args.output)

    print(f"\nDone! {len(filenames)} images saved to {args.output}")

    # 8. Validate
    if args.validate:
        ok = validate_output(args.output, args.views, args.width, args.height)
        return 0 if ok else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
