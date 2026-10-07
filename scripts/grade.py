#!/usr/bin/env python3
"""Crop and grade the photographic backgrounds.

Every change made to a photograph is in the FRAMES table below, so the list
CC BY asks for is the code itself. For each frame:
  * crop to 16:9, then resample to the output size. Downsampling is the rule;
    the one exception is the 1945 tower print, which no archive holds large
    enough, and is enlarged 1.26x and given fresh grain at full resolution
  * expose down in linear light, so the scene reads as it would a little
    later in the evening; cool it slightly; give back the saturation that
    darkening takes away (or, for the black-and-white print, neutralise its
    sepia toward graphite)
  * darken the sky toward the zenith, as twilight does, and fade the top edge
    so the status bar always sits on dark
Nothing inside a crop is added, cloned or removed.

Requires numpy and Pillow, and ImageMagick for the 16-bit archival TIFF.
Originals are fetched into scripts/.cache once.
Usage: grade.py [name ...]   (default: all frames)
"""
import os, sys, subprocess
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from photo import fetch, load, to_linear, to_srgb, smooth, blur, finish

FRAMES = {
    # Full moon over the Sangre de Cristo crest, from the Taos Plateau, 20 January
    # 2019. Mike Lewinski, CC BY 2.0. Bottom-aligned crop: only empty sky is lost.
    "2-sangre-de-cristo.jpg": dict(
        url="https://upload.wikimedia.org/wikipedia/commons/2/24/Full_moon_rising1.jpg",
        cache="full-moon-rising1.jpg",
        box=(0, 563, 5456, 3632), size=(5120, 2880),
        exposure=0.150, cool=(0.92, 0.98, 1.06), saturation=1.25,
        zenith=0.30, horizon=0.72, top=(0.20, 0.16)),
    # Cabezon Peak under a mackerel sky at dusk, 5 February 2010. Bob Wick, Bureau
    # of Land Management; public domain (US government work).
    "6-cabezon.jpg": dict(
        url="https://upload.wikimedia.org/wikipedia/commons/8/80/Cabezon_Peak_WSA_%289440790189%29.jpg",
        cache="cabezon-peak-wsa.jpg",
        box=(0, 585, 5616, 3744), size=(5120, 2880),
        exposure=0.130, cool=(0.92, 0.98, 1.06), saturation=1.25,
        zenith=0.30, horizon=0.82, top=(0.22, 0.14)),
    # The Trinity shot tower and its shack against cumulus, July 1945. Los Alamos;
    # US government work, public domain (NARA 434-OR-42-MED-316, catalog id
    # 617585206). A 16-bit scan of a print: the top crop leaves out the border,
    # the caption and the vehicles at the base. Enlarged 1.26x (see above).
    "5-tower.jpg": dict(
        url="https://catalog.archives.gov/medialz/stillpix/434-or/binder42/434-OR-42-MED-316_001.tif",
        cache="nara-434-OR-42-MED-316.tif",
        box=(116, 380, 3156, 2090), size=(3840, 2160), mono=True, upscale=True,
        exposure=0.22, tone=(0.94, 0.98, 1.04), contrast=1.30,
        zenith=0.55, horizon=1.00, top=(0.25, 0.14)),
}
LUMA = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def load_print(path, box, size):
    """A 16-bit archival TIFF: crop with ImageMagick, keep 16 bits, return linear grey."""
    x0, y0, x1, y1 = box
    raw = subprocess.run(["magick", path, "-crop", f"{x1 - x0}x{y1 - y0}+{x0}+{y0}", "+repage",
                          "-colorspace", "Gray", "-depth", "16", "-endian", "MSB", "gray:-"],
                         capture_output=True, check=True).stdout
    g = np.frombuffer(raw, dtype=">u2").reshape(y1 - y0, x1 - x0).astype(np.float32) / 65535
    g = to_linear(g)                                  # magick hands back gamma-encoded grey
    return np.asarray(Image.fromarray(g).resize(size, Image.LANCZOS))


def film_grain(h, w, rng, size_px=1.4):
    """Grain with a body to it: slightly clumped, as silver is, not per-pixel noise."""
    n = blur(rng.standard_normal((h, w)).astype(np.float32), size_px * 0.5)
    return n / (n.std() + 1e-6)


def grade(name, f):
    w, h = f["size"]
    path = fetch(f["url"], f["cache"])
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    # the sky falls off toward the zenith; the horizon sits at f["horizon"] of the frame
    sky = f["zenith"] + (1 - f["zenith"]) * smooth(y / f["horizon"]) ** 0.9
    floor, depth = f["top"]
    top = floor + (1 - floor) * smooth(y / depth)
    if f.get("mono"):
        g = load_print(path, f["box"], (w, h))
        g = np.clip(g / np.percentile(g, 99.5), 0, 1) ** f["contrast"]   # set the clouds' white, deepen the sky
        g = g * f["exposure"] * sky * top
        img = g[..., None] * np.array(f["tone"], dtype=np.float32)        # sepia out, graphite in
        rng = np.random.default_rng(1945)
        img = img * (1 + 0.10 * film_grain(h, w, rng)[..., None]) + 0.0015 * film_grain(h, w, rng)[..., None]
        img = np.clip(img, 0, None)
        grain = 0.004
    else:
        assert not f.get("upscale")
        img = to_linear(load(path, f["box"], (w, h)))
        img = img * (f["exposure"] * sky * top)[..., None] * np.array(f["cool"], dtype=np.float32)
        lum = (img @ LUMA)[..., None]
        img = np.clip(lum + f["saturation"] * (img - lum), 0, None)
        grain = 0.006
    # a gentle shoulder so snow, moon and cloud never clip, then back to sRGB
    img = img / (1 + 0.6 * img)
    finish(to_srgb(img), name, grain=grain)


if __name__ == "__main__":
    for name in sys.argv[1:] or FRAMES:
        grade(name, FRAMES[name])
