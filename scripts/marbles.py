#!/usr/bin/env python3
"""Render backgrounds/3-marbles.jpg — glass fishbowls of marbles on an old desk.

Three bowls in a row, filling with marbles from left to right: the way the
film shows Los Alamos keeping count of enriched material. Nothing here is
taken from the film; it is an original still life, rendered physically with
Mitsuba 3 (path tracing, thin-lens depth of field) and lit like one:
  * a large warm key from the left, the lamp
  * a soft pool of light on the wall behind, so the glass glows against it
  * a faint cool fill from a window to the right, and a dim room
The bowls are thick-walled solids of revolution with analytic normals and a
faint green cast, like period soda glass. The marbles are settled into each
bowl by a small physics pass; half are cat's-eyes, with a three-bladed
coloured vane set in the glass. The desk is Poly Haven's CC0 "Wood Table
Worn" scan, darkened.

Usage: marbles.py [render [WIDTH HEIGHT SPP]] [finish]
  render  path-traces the HDR frame into scripts/.cache/marbles.npy (about an
          hour on 8 cores at 3840x2160, 640 spp)
  finish  tone-maps it into the background: firefly filter, filmic curve,
          a dark top edge for the status bar, film grain
With no arguments it does both. Requires numpy, Pillow and mitsuba.
"""
import os, sys, math, time
import numpy as np
from PIL import Image, ImageEnhance

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from photo import CACHE, fetch, to_srgb, filmic, blur, smooth, finish

OUT_NAME = "3-marbles.jpg"
HDR = os.path.join(CACHE, "marbles.npy")
WOOD = "https://dl.polyhaven.org/file/ph-assets/Textures/jpg/4k/wood_table_worn/wood_table_worn_{}_4k.jpg"


# ---------------------------------------------------------------- bowl
R, RB, RO, T = 0.110, 0.055, 0.068, 0.0045      # sphere radius, base radius, opening radius, wall
CY = math.sqrt(R * R - RB * RB)                  # sphere centre height (outer base at y = 0)
YRIM = CY + math.sqrt(R * R - RO * RO)
RI = R - T


def arc(r0, ang0, ang1, n, rad):
    a = np.linspace(ang0, ang1, n)
    return np.stack([rad * np.sin(a), CY - rad * np.cos(a)], 1)   # angle from the downward axis


def bowl_profile():
    """Runs of (r, y) points; each run is smooth, corners between runs are sharp."""
    a_base = math.asin(RB / R)
    a_rim = math.pi - math.asin(RO / R)
    ri_rim = math.sqrt(RI * RI - (YRIM - CY) ** 2)
    ai_rim = math.pi - math.asin(ri_rim / RI)
    ai_floor_r = math.sqrt(RI * RI - (CY - T) ** 2)
    ai_floor = math.asin(ai_floor_r / RI)
    runs = [
        np.stack([np.linspace(0, RB, 12), np.zeros(12)], 1),                      # outer foot
        arc(0, a_base, a_rim, 140, R),                                              # outer wall
    ]
    # rounded lip from outer rim to inner rim
    cr, cy_ = (RO + ri_rim) / 2, YRIM
    lip_r = (RO - ri_rim) / 2
    th = np.linspace(0, math.pi, 16)
    runs.append(np.stack([cr + lip_r * np.cos(th), cy_ + lip_r * np.sin(th) * 0.9], 1))
    runs.append(arc(0, ai_rim, ai_floor, 130, RI))                                  # inner wall, down
    runs.append(np.stack([np.linspace(ai_floor_r, 0, 12), np.full(12, T)], 1))      # inner floor
    return runs


def revolve(runs, seg=160):
    V, N, F = [], [], []
    for run in runs:
        d = np.gradient(run, axis=0)
        n2 = np.stack([d[:, 1], -d[:, 0]], 1)
        n2 /= np.linalg.norm(n2, axis=1, keepdims=True) + 1e-12
        base = len(V)
        th = np.linspace(0, 2 * math.pi, seg, endpoint=False)
        for (r, y), (nr, ny) in zip(run, n2):
            for t in th:
                V.append((r * math.cos(t), y, r * math.sin(t)))
                N.append((nr * math.cos(t), ny, nr * math.sin(t)))
        m = len(run)
        for i in range(m - 1):
            for j in range(seg):
                a, b = base + i * seg + j, base + i * seg + (j + 1) % seg
                c, d_ = base + (i + 1) * seg + (j + 1) % seg, base + (i + 1) * seg + j
                F += [(a, b, c), (a, c, d_)]
    V, N, F = np.array(V, np.float32), np.array(N, np.float32), np.array(F, np.uint32)
    # orient faces to agree with the analytic normals
    e = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    flip = np.sum(e * N[F].mean(1), 1) < 0
    F[flip] = F[flip][:, ::-1]
    return V, N, F


def bowl_ply(name, offset):
    V, N, F = revolve(bowl_profile())
    V = V + np.array(offset, np.float32)
    m = mi.Mesh(name, len(V), len(F), has_vertex_normals=True)
    p = mi.traverse(m)
    p["vertex_positions"] = mi.Float(V.ravel())
    p["vertex_normals"] = mi.Float(N.ravel())
    p["faces"] = mi.UInt32(F.ravel())
    p.update()
    path = os.path.join(CACHE, f"{name}.ply")
    m.write_ply(path)
    return path


# ---------------------------------------------------------------- marbles
RM = 0.0080


def settle(n, seed):
    cache = os.path.join(CACHE, f"settle_{n}_{seed}.npy")
    if os.path.exists(cache):
        return np.load(cache)
    p = _settle(n, seed)
    np.save(cache, p)
    return p


def _settle(n, seed):
    """Drop n marbles into the bowl and let them settle (position-based)."""
    rng = np.random.default_rng(seed)
    c = np.array([0, CY, 0])
    a = rng.uniform(0, 2 * math.pi, n); rr = np.sqrt(rng.uniform(0, 1, n)) * 0.045
    p = np.stack([rr * np.cos(a), T + RM + np.linspace(0, 0.6, n) + rng.uniform(0, 0.01, n), rr * np.sin(a)], 1)
    for it in range(1600):
        p[:, 1] -= 0.0009 * (1 - it / 1800)
        for _ in range(2):
            d = p[:, None] - p[None]
            dist = np.linalg.norm(d, axis=2) + np.eye(n)
            ov = np.clip(2 * RM - dist, 0, None)
            np.fill_diagonal(ov, 0)
            p += 0.5 * np.sum(d / dist[..., None] * ov[..., None], 1)
            v = p - c
            L = np.linalg.norm(v, axis=1)
            lim = RI - RM
            out = L > lim
            p[out] = c + v[out] / L[out, None] * lim
            p[:, 1] = np.maximum(p[:, 1], T + RM)
        p[:, [0, 2]] += rng.normal(0, 0.00003, (n, 2)) * (it < 800)
    return p[p[:, 1] < YRIM - RM]


VANES = [(0.55, 0.10, 0.06), (0.05, 0.22, 0.45), (0.70, 0.48, 0.10), (0.06, 0.32, 0.26), (0.75, 0.73, 0.68)]
GLASS = [(1.0, 1.0, 1.0), (0.80, 0.93, 0.84), (0.95, 0.86, 0.66), (0.78, 0.86, 0.92), (0.86, 0.86, 0.84)]


# ---------------------------------------------------------------- desk
def wood_maps():
    paths = {k: fetch(WOOD.format(k), f"wood_table_worn_{k}_4k.jpg") for k in ("diff", "nor_gl", "rough")}
    dark = os.path.join(CACHE, "wood_table_worn_diffdark_4k.jpg")
    if not os.path.exists(dark):   # stained darker and less red: an old desk at night
        im = Image.open(paths["diff"]).convert("RGB")
        im = ImageEnhance.Brightness(ImageEnhance.Color(im).enhance(0.55)).enhance(0.55)
        im.save(dark, quality=92)
    paths["diffdark"] = dark
    return paths


def build(w, h, spp):
    maps = wood_maps()

    def wood(name):
        return {"type": "bitmap", "filename": maps[name],
                "to_uv": mi.ScalarTransform4f().scale([5.0 / 0.55, 5.0 / 0.55, 1]), "raw": not name.startswith("diff")}

    scene = {
        "type": "scene",
        "integrator": {"type": "path", "max_depth": 28, "rr_depth": 12},
        "sensor": {
            "type": "thinlens", "fov": 36, "fov_axis": "x",
            "aperture_radius": 0.0050, "focus_distance": 1.47,
            "to_world": mi.ScalarTransform4f().look_at(origin=[0.05, 0.36, 1.45], target=[0.0, 0.13, 0.0], up=[0, 1, 0]),
            "film": {"type": "hdrfilm", "width": w, "height": h, "rfilter": {"type": "gaussian"}},
            "sampler": {"type": "independent", "sample_count": spp},
        },
        "desk": {
            "type": "rectangle",
            "to_world": mi.ScalarTransform4f().rotate([1, 0, 0], -90).scale([2.5, 2.5, 1]),
            "bsdf": {"type": "normalmap", "normalmap": {**wood("nor_gl")},
                     "bsdf": {"type": "principled", "base_color": {**wood("diffdark")},
                              "roughness": {**wood("rough")}, "specular": 0.4}},
        },
        "lamp": {
            "type": "disk",
            "to_world": mi.ScalarTransform4f().look_at(origin=[-0.60, 0.46, 0.10], target=[0.0, 0.06, -0.02], up=[0, 1, 0]).scale([0.22, 0.22, 1]),
            "emitter": {"type": "area", "radiance": {"type": "rgb", "value": [5.0, 3.42, 1.92]}},
        },
        "room": {"type": "constant", "radiance": {"type": "rgb", "value": [0.020, 0.019, 0.018]}},
        "backdrop": {
            "type": "rectangle",
            "to_world": mi.ScalarTransform4f().translate([0.0, 1.0, -0.75]).scale([3.0, 1.0, 1]),
            "bsdf": {"type": "diffuse", "reflectance": {"type": "rgb", "value": [0.16, 0.155, 0.15]}},
        },
        "backlight": {
            "type": "spot",
            "to_world": mi.ScalarTransform4f().look_at(origin=[0.0, 0.03, -0.42], target=[0.0, 0.02, -0.75], up=[0, 1, 0]),
            "intensity": {"type": "rgb", "value": [0.42, 0.37, 0.31]},
            "cutoff_angle": 62.0, "beam_width": 18.0,
        },
        "window": {
            "type": "rectangle",
            "to_world": mi.ScalarTransform4f().look_at(origin=[0.9, 0.5, -0.6], target=[0, 0.08, 0], up=[0, 1, 0]).scale([0.4, 0.3, 1]),
            "emitter": {"type": "area", "radiance": {"type": "rgb", "value": [0.22, 0.30, 0.48]}},
        },
    }

    BOWLS = [((-0.27, 0.0, -0.03), 200, 3), ((0.0, 0.0, 0.0), 420, 2), ((0.27, 0.0, 0.03), 640, 1)]
    for bi, (pos, n, seed) in enumerate(BOWLS):
        scene[f"bowl{bi}"] = {"type": "ply", "filename": bowl_ply(f"bowl{bi}", pos), "face_normals": False,
                              "bsdf": {"type": "dielectric", "int_ior": 1.5,
                                       "specular_transmittance": {"type": "rgb", "value": [0.95, 0.985, 0.965]}}}
        rng = np.random.default_rng(100 + seed)
        for k, q in enumerate(settle(n, seed)):
            tint = GLASS[rng.integers(len(GLASS))]
            c = q + np.array(pos)
            scene[f"m{bi}_{k}"] = {"type": "sphere", "center": c.tolist(), "radius": RM,
                                   "bsdf": {"type": "dielectric", "int_ior": 1.52, "specular_transmittance": {"type": "rgb", "value": list(tint)}}}
            if rng.random() < 0.5:   # cat's-eye: a twisted coloured vane set in the glass
                axis = rng.normal(size=3); axis /= np.linalg.norm(axis)
                col = VANES[rng.integers(len(VANES))]
                for j, ang in enumerate((0.0, 120.0, 240.0)):
                    scene[f"v{bi}_{k}_{j}"] = {
                        "type": "rectangle",
                        "to_world": mi.ScalarTransform4f().translate(c.tolist())
                                    @ mi.ScalarTransform4f().look_at(origin=[0, 0, 0], target=axis.tolist(), up=[0.31, 0.95, 0.07] if abs(axis[1]) < 0.9 else [1, 0, 0])
                                    @ mi.ScalarTransform4f().rotate([0, 0, 1], ang + rng.uniform(-10, 10))
                                    @ mi.ScalarTransform4f().rotate([1, 0, 0], 90).scale([RM * 0.22, RM * 0.70, 1]),
                        "bsdf": {"type": "twosided", "bsdf": {"type": "diffuse", "reflectance": {"type": "rgb", "value": list(col)}}}}
    return scene


def render(w, h, spp):
    os.makedirs(CACHE, exist_ok=True)
    scene = build(w, h, spp)
    print(f"marbles: {sum(1 for k in scene if k.startswith('m'))}, rendering {w}x{h} at {spp} spp")
    t0 = time.time()
    img = mi.render(mi.load_dict(scene))
    np.save(HDR, np.array(img, dtype=np.float32))
    print(f"rendered in {(time.time() - t0) / 60:.1f} min -> {HDR}")


def defirefly(img, k=4.0, passes=2):
    """Replace isolated hot pixels (caustic fireflies) with their neighbourhood mean."""
    for _ in range(passes):
        lum = img @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        local = blur(lum, 1.5)
        hot = lum > k * local + 0.02
        img[hot] = blur(img, 1.5)[hot]
    return img


def finish_frame(exposure=1.6):
    img = defirefly(np.load(HDR)) * exposure
    h, w, _ = img.shape
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    x = np.linspace(-1, 1, w, dtype=np.float32)[None, :]
    img *= (0.15 + 0.85 * smooth(y / 0.30))[..., None]                    # dark top edge
    img *= (1 - 0.30 * np.clip(0.5 * x ** 2 + 0.6 * (y - 0.55) ** 2, 0, 1))[..., None]
    finish(to_srgb(filmic(img)), OUT_NAME, grain=0.007, seed=1945)


if __name__ == "__main__":
    args = sys.argv[1:] or ["render", "finish"]
    if "render" in args:
        i = args.index("render")
        nums = [int(a) for a in args[i + 1:i + 4] if a.isdigit()]
        import mitsuba as mi
        mi.set_variant("llvm_ad_rgb")
        render(*(nums if len(nums) == 3 else (3840, 2160, 640)))
    if "finish" in args:
        finish_frame()
