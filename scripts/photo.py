"""Shared helpers for the background scripts: sources, colour, tone, grain, save.

Requires numpy and Pillow.
"""
import os, urllib.request
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
BACKGROUNDS = os.path.normpath(os.path.join(HERE, os.pardir, "backgrounds"))
CACHE = os.path.join(HERE, ".cache")
UA = "omarchy-trinity-theme/0.1 (background build script)"

Image.MAX_IMAGE_PIXELS = None   # the source scans are 8k x 8k


def fetch(url, name):
    """Download a source file once into scripts/.cache and return its path."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name)
    if not os.path.exists(path):
        print(f"fetching {url}")
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req) as r, open(path + ".part", "wb") as f:
            while chunk := r.read(1 << 20):
                f.write(chunk)
        os.replace(path + ".part", path)
    return path


def load(path, box=None, size=None):
    """Open an image, crop to box, downsample (never upsample) to size, as float 0..1."""
    im = Image.open(path).convert("RGB")
    if box:
        im = im.crop(box)
    if size and size != im.size:
        assert size[0] <= im.size[0] and size[1] <= im.size[1], "refusing to upscale"
        im = im.resize(size, Image.LANCZOS)
    return np.asarray(im, dtype=np.float32) / 255


def to_linear(x):
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4).astype(np.float32)


def to_srgb(x):
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(np.clip(x, 0, None), 1 / 2.4) - 0.055)


def filmic(x):
    # ACES approximation (Narkowicz)
    a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    return np.clip((x * (a * x + b)) / (x * (c * x + d) + e), 0, 1)


def blur(img, sigma):
    """Gaussian blur (sigma in px) of an (H, W[, C]) float image via FFT, edge-padded."""
    if sigma <= 0:
        return img
    flat = img.ndim == 2
    if flat:
        img = img[..., None]
    pad = int(3 * sigma) + 1
    H, W, C = img.shape
    p = np.pad(img, ((pad, pad), (pad, pad), (0, 0)), mode="edge")
    fy = np.fft.fftfreq(p.shape[0])[:, None]
    fx = np.fft.rfftfreq(p.shape[1])[None, :]
    k = np.exp(-2 * (np.pi * sigma) ** 2 * (fx ** 2 + fy ** 2)).astype(np.float32)
    out = np.empty_like(img)
    for c in range(C):
        out[..., c] = np.fft.irfft2(np.fft.rfft2(p[..., c]) * k, s=p.shape[:2])[pad:pad + H, pad:pad + W]
    return out[..., 0] if flat else out


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def finish(srgb, name, grain=0.010, seed=1943, quality=93):
    """Add film grain, quantise, save into backgrounds/ and report the luminance rule."""
    rng = np.random.default_rng(seed)
    out = srgb + rng.normal(0, grain, srgb.shape).astype(np.float32) if grain else srgb
    img = Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8))
    path = os.path.join(BACKGROUNDS, name)
    if name.endswith(".jpg"):
        img.save(path, quality=quality, subsampling=0, optimize=True, progressive=True)
    else:
        img.save(path, lossless=True, method=6, exact=True)
    lum = np.asarray(img.convert("L"), dtype=np.float32) / 255
    print(f"wrote {path} {img.size[0]}x{img.size[1]}  mean {lum.mean()*100:.1f}%  "
          f"top8 {lum[:int(lum.shape[0]*0.08)].mean()*100:.1f}%")
    return path
