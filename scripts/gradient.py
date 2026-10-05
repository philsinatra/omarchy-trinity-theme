#!/usr/bin/env python3
"""Render backgrounds/2-lamplight.webp (lossless) — the theme's own gradient.

A room after midnight, with nothing in it: tungsten light falling in from a
lamp just off the left edge, cool night from a window somewhere to the
right, and lamp-shadow everywhere else. The base ramp is blended in OKLab so
it stays perceptually even; light is added in linear RGB so the tungsten
warms the dark instead of greying it; the result is dithered so it never
bands.

Requires numpy and Pillow.  Usage: gradient.py [WIDTH HEIGHT]
"""
import os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oklch import srgb_to_oklab

W, H = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (3840, 2160)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "backgrounds", "2-lamplight.webp")

CEILING = "#07070a"  # top edge, darker than darker_background
SHADOW = "#0f0f12"   # mid-field: graphite in shadow
FLOOR = "#141417"    # lower field, within the lamp's reach
# light sources, linear RGB, added on top (light adds; it never greys the dark)
TUNGSTEN = np.array([1.00, 0.52, 0.20])   # a 2700 K bulb, seen as light, not as a colour chip
FILAMENT = np.array([1.00, 0.70, 0.40])   # the hot centre of the pool
NIGHT = np.array([0.16, 0.26, 0.52])      # dusk through a window, off to the right


def lab(hx):
    return np.array(srgb_to_oklab(hx), dtype=np.float64)


def oklab_to_srgb(L, a, b):
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    bb = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    rgb = np.clip(np.stack([r, g, bb], -1), 0, 1)
    return np.where(rgb <= 0.0031308, 12.92 * rgb, 1.055 * rgb ** (1 / 2.4) - 0.055)


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


y = np.linspace(0, 1, H)[:, None]
x = np.linspace(0, 1, W)[None, :]
aspect = W / H

# base: ceiling -> shadow -> floor, top to bottom
t = np.broadcast_to(y, (H, W))
base = (lab(CEILING)[None, None] * (1 - smooth(t / 0.55))[..., None]
        + lab(SHADOW)[None, None] * (smooth(t / 0.55) * (1 - smooth((t - 0.55) / 0.45)))[..., None]
        + lab(FLOOR)[None, None] * smooth((t - 0.55) / 0.45)[..., None])

rgb = oklab_to_srgb(base[..., 0], base[..., 1], base[..., 2])
lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)

# the lamp: a broad, low pool spilling in from past the left edge, a little
# below centre — a shaded bulb, so the light is wide and falls off softly,
# and the ceiling above it stays dark
lx, ly = -0.16, 0.70
R = np.sqrt(((x - lx) * aspect) ** 2 + ((y - ly) * 1.35) ** 2)
pool = 1 / (1 + (R / 0.55) ** 2) ** 1.6
core = np.exp(-(R / 0.42) ** 2)
# the shade's rim: light falls off faster upward than downward
shade = smooth((y - 0.10) / 0.55)
# the night: cool, faint, from the right, strongest at window height
night = smooth((x - 0.45) / 0.55) * np.exp(-((y - 0.48) / 0.42) ** 2)

lin = (lin + TUNGSTEN * (0.075 * pool * shade)[..., None] + FILAMENT * (0.060 * core * shade)[..., None]
       + NIGHT * (0.026 * night)[..., None])
rgb = np.where(lin <= 0.0031308, 12.92 * lin, 1.055 * np.clip(lin, 0, None) ** (1 / 2.4) - 0.055)

# dither: triangular noise at +-1 LSB, so 8-bit output never bands
rng = np.random.default_rng(1945)
noise = (rng.random(rgb.shape) - rng.random(rgb.shape)) / 255.0
img = np.clip(np.round((rgb + noise) * 255), 0, 255).astype(np.uint8)

Image.fromarray(img).save(os.path.normpath(OUT), lossless=True, method=6, exact=True)
lum = img.mean(axis=2) / 255
print(f"wrote {os.path.normpath(OUT)} {W}x{H}  mean {lum.mean()*100:.1f}%  top8 {lum[:int(H*0.08)].mean()*100:.1f}%")
