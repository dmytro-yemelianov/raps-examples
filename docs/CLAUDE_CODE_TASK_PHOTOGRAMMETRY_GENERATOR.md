# Claude Code Task: Photogrammetry Test Data Generator

## Goal
Build a lightweight Python script that generates synthetic photo sets suitable for photogrammetry reconstruction. Output images must work with Autodesk Reality Capture API (`raps reality create` → `raps reality process`) and other photogrammetry tools (Meshroom, COLMAP, RealityCapture).

**No Blender, no heavy 3D software.** Keep it minimal.

---

## Tech Stack

**Required:**
- Python 3.10+
- `moderngl` — headless OpenGL rendering (~2MB)
- `Pillow` — image output
- `numpy` — math
- `pyrr` — matrix/quaternion helpers (tiny)

**No:**
- Blender, Maya, 3ds Max, or any DCC tool
- PyQt, tkinter, or any windowing
- Large frameworks (PyTorch3D, Open3D, etc.)

**Install:**
```bash
pip install moderngl Pillow numpy pyrr
```

---

## What to Build

### Core: `photogrammetry_gen.py`

A single-file CLI script that:

1. **Creates a procedural 3D scene** (textured geometry — no blank surfaces)
2. **Renders it from N camera positions** orbiting the scene
3. **Outputs JPEG images** with optional EXIF metadata
4. **Outputs a `cameras.json`** with ground-truth camera poses (for validation)

### Usage:
```bash
# Basic — 36 views of a textured cube
python photogrammetry_gen.py --output ./test_photos --views 36

# Custom scene
python photogrammetry_gen.py --output ./test_photos --views 60 --scene sphere --texture noise --resolution 1920x1080

# Multiple orbits at different elevations
python photogrammetry_gen.py --output ./test_photos --views 72 --orbits 3 --elevation 15,45,70

# With EXIF metadata (some pipelines want focal length)
python photogrammetry_gen.py --output ./test_photos --views 36 --exif --focal-length 50
```

---

## Scene Generation Requirements

### Geometry Options (implement all)

1. **`cube`** — textured cube (default, simplest)
2. **`sphere`** — UV sphere with procedural texture
3. **`multi`** — multiple primitives scattered on a ground plane (best for photogrammetry)
4. **`terrain`** — heightmap-based terrain mesh (good for aerial sim)

### Texture Requirements (critical for photogrammetry)

Photogrammetry FAILS on uniform surfaces. Every face must have visible texture detail.

Generate procedural textures using:
```python
# Simplex/Perlin noise — rich detail, no external files needed
def generate_texture(width=1024, height=1024, scale=50.0, octaves=4):
    """Generate a procedural texture suitable for photogrammetry."""
    # Use numpy-based value noise (no 'noise' package dependency)
    # Mix multiple frequencies for rich detail
    # Add color variation (not grayscale)
    # Return as PIL Image
```

**Texture styles:**
- `noise` — Perlin-like noise with color tinting (default)
- `checker` — checkerboard with color variation per cell
- `stone` — rock-like texture using fractal noise
- `grid` — numbered grid (useful for debugging UV mapping)

### Ground Plane
Always include a textured ground plane beneath objects. This helps reconstruction anchor the scene.

---

## Camera Positioning

### Orbital Camera Rig
```python
def generate_camera_poses(n_views, n_orbits=2, radius=3.0, elevations=None):
    """
    Generate camera positions orbiting around origin.
    
    Args:
        n_views: total number of views (distributed across orbits)
        n_orbits: number of elevation rings
        radius: distance from center
        elevations: list of elevation angles in degrees
                    default: [20, 50] for 2 orbits
    
    Returns:
        list of (view_matrix_4x4, position_xyz) tuples
    """
```

### Camera Model
- **Perspective projection** matching a real camera
- Default: 50mm equivalent focal length on full-frame sensor
- Resolution: 1920×1080 default, configurable
- All cameras look at scene center (0, 0, 0)

### Overlap Requirement
Adjacent views must have **60-80% visual overlap** — this is critical for photogrammetry. For a 360° orbit:
- 36 views = 10° spacing ≈ good overlap ✓
- 12 views = 30° spacing ≈ borderline ✗
- Minimum recommended: 24 views

---

## OpenGL Rendering (moderngl)

### Shader Requirements

**Vertex shader:**
```glsl
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
```

**Fragment shader:**
```glsl
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
```

### Lighting
- Single directional light (sun-like)
- Slightly vary light direction between shots (±5°) to simulate real conditions
- Ambient term to prevent pure black shadows

### Rendering Loop
```python
ctx = moderngl.create_standalone_context()  # headless, no display
fbo = ctx.simple_framebuffer((width, height))
fbo.use()

for i, (view_matrix, cam_pos) in enumerate(camera_poses):
    mvp = projection @ view_matrix
    ctx.clear(0.6, 0.7, 0.9)  # sky-blue background
    # set uniforms, render, read pixels
    pixels = fbo.read(components=3)
    img = Image.frombytes('RGB', (width, height), pixels).transpose(Image.FLIP_TOP_BOTTOM)
    img.save(f'{output_dir}/IMG_{i:04d}.jpg', quality=95)
```

---

## Output Structure

```
test_photos/
├── IMG_0000.jpg
├── IMG_0001.jpg
├── ...
├── IMG_0035.jpg
├── cameras.json          ← ground truth poses
└── scene_info.json       ← scene parameters for reproducibility
```

### cameras.json Format
```json
{
  "camera_model": "PINHOLE",
  "focal_length_mm": 50.0,
  "sensor_width_mm": 36.0,
  "sensor_height_mm": 24.0,
  "image_width": 1920,
  "image_height": 1080,
  "views": [
    {
      "filename": "IMG_0000.jpg",
      "position": [3.0, 0.0, 1.5],
      "rotation_euler_deg": [70.0, 0.0, 90.0],
      "view_matrix": [[...], [...], [...], [...]],
      "projection_matrix": [[...], [...], [...], [...]]
    }
  ]
}
```

### EXIF Metadata (optional, `--exif` flag)
Write to JPEG using Pillow's `exif` support:
- `FocalLength`: from `--focal-length`
- `ImageWidth`, `ImageHeight`
- `Make`: "Synthetic"
- `Model`: "PhotogrammetryGen"
- `DateTimeOriginal`: timestamp per image

Some photogrammetry pipelines (Meshroom, COLMAP) use EXIF focal length to initialize camera intrinsics.

---

## Validation

### Self-Test Mode
```bash
python photogrammetry_gen.py --output ./test --views 36 --validate
```

Validation checks:
1. ✅ All images saved and readable
2. ✅ Image dimensions match spec
3. ✅ Adjacent views have visual difference (not identical frames)
4. ✅ Texture detail present (image entropy > threshold)
5. ✅ cameras.json parseable and complete
6. ✅ Camera positions form valid orbit (not clustered)

### Integration Test with RAPS
```bash
# Generate test photos
python photogrammetry_gen.py --output ./synthetic_test --views 36

# Create photoscene via RAPS
raps reality create --name "synthetic-test" --type object

# Upload photos (future RAPS feature or manual)
# raps reality upload <photoscene_id> ./synthetic_test/*.jpg

# Process
raps reality process <photoscene_id>

# Check status
raps reality status <photoscene_id>

# Download result
raps reality result <photoscene_id> --format obj
```

---

## Code Quality Requirements

- **Single file** — `photogrammetry_gen.py` (keep it self-contained)
- **No classes needed** — functions are fine for this scope
- **Type hints** on all functions
- **Docstrings** on public functions
- **`argparse`** for CLI interface
- **Error handling** — graceful failure if moderngl can't create context (suggest CPU fallback)
- **Progress output** — print render progress: `Rendering view 12/36...`

---

## CPU Fallback (stretch goal)

If `moderngl.create_standalone_context()` fails (no GPU, no EGL):

```python
def software_render(mesh, camera, width, height):
    """Pure numpy software rasterizer — slow but works anywhere."""
    # Project vertices with matrix multiply
    # Rasterize triangles with barycentric coords
    # Sample texture at interpolated UVs
    # Z-buffer for depth testing
```

This is 10-50x slower but requires zero GPU. Implement as automatic fallback:
```python
try:
    ctx = moderngl.create_standalone_context()
    render = gpu_render
except Exception:
    print("⚠ No GPU context available, falling back to CPU rasterizer")
    render = software_render
```

---

## Noise Generation Without External Package

Don't depend on the `noise` pip package. Implement value noise in numpy:

```python
def value_noise_2d(x: np.ndarray, y: np.ndarray, seed: int = 42) -> np.ndarray:
    """
    Generate 2D value noise using numpy only.
    Suitable for procedural textures.
    """
    rng = np.random.default_rng(seed)
    # Lattice-based interpolation
    # Multiple octaves for detail
    ...

def fractal_noise(width: int, height: int, octaves: int = 6, seed: int = 42) -> np.ndarray:
    """Stack multiple noise octaves for rich procedural texture."""
    result = np.zeros((height, width))
    for i in range(octaves):
        freq = 2 ** i
        amp = 0.5 ** i
        result += amp * value_noise_2d(..., freq, seed + i)
    return result
```

---

## CLI Interface

```
usage: photogrammetry_gen.py [-h] --output DIR [--views N] [--orbits N]
                              [--elevation DEGREES] [--scene TYPE]
                              [--texture TYPE] [--resolution WxH]
                              [--focal-length MM] [--radius FLOAT]
                              [--exif] [--validate] [--seed INT]

Generate synthetic photo sets for photogrammetry testing.

required:
  --output DIR          Output directory for images

camera:
  --views N             Number of views (default: 36)
  --orbits N            Number of elevation orbits (default: 2)
  --elevation DEGREES   Comma-separated elevation angles (default: 20,50)
  --focal-length MM     Simulated focal length (default: 50)
  --radius FLOAT        Camera orbit radius (default: 3.0)

scene:
  --scene TYPE          Scene type: cube|sphere|multi|terrain (default: multi)
  --texture TYPE        Texture: noise|checker|stone|grid (default: noise)
  --seed INT            Random seed for reproducibility (default: 42)

output:
  --resolution WxH      Image resolution (default: 1920x1080)
  --exif                Write EXIF metadata to images
  --validate            Run validation checks after generation
```

---

## Success Criteria

1. `python photogrammetry_gen.py --output ./test --views 36` completes in <30 seconds
2. Output images show textured 3D objects from different angles
3. Images work with COLMAP/Meshroom reconstruction (produce point cloud)
4. `cameras.json` has correct ground-truth poses
5. No dependency heavier than moderngl (~2MB)
6. Works headless (CI/server environments, no display)
7. Total script under 800 lines

---

## RAPS Integration Notes

This tool pairs with RAPS Reality Capture commands:
- `raps reality create` — create photoscene
- `raps reality process` — start reconstruction
- `raps reality status` — check progress
- `raps reality result` — download output
- `raps reality formats` — list output formats

Future: consider adding as `raps reality generate-test` subcommand if it proves useful.
