#!/usr/bin/env python3
"""Crop and grade the three photographic backgrounds: the window at dusk.

Every change made to a photograph is in the FRAMES table below, so the list
CC BY asks for is the code itself. For each frame:
  * crop to 16:9 at native resolution, then downsample (never upscale)
  * expose down in linear light, so the scene reads as it would a little
    later in the evening; cool it slightly; give back the saturation that
    darkening takes away
  * darken the sky toward the zenith, as twilight does, and fade the top edge
    so the status bar always sits on dark
Nothing inside a crop is added, cloned or removed.

Requires numpy and Pillow; originals are fetched into scripts/.cache once.
Usage: grade.py [name ...]   (default: all frames)
"""
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from photo import fetch, load, to_linear, to_srgb, smooth, finish

FRAMES = {
    # White Sands, a few minutes after sunset. Charles & Maggie Boyer, CC BY 2.0.
    # The crop leaves out three distant walkers and two trail markers.
    "3-gloaming.jpg": dict(
        url="https://upload.wikimedia.org/wikipedia/commons/a/a5/"
            "Start_of_Gloaming%2C_White_Sands_National_Park%2C_04-03-2023_%2852801020712%29.jpg",
        cache="start-of-gloaming.jpg",
        box=(2724, 820, 2724 + 4392, 820 + 2470), size=(3840, 2160),
        exposure=0.060, cool=(0.86, 0.96, 1.10), saturation=1.45,
        zenith=0.25, horizon=0.74, top=(0.22, 0.14)),
    # Full moon over the Sangre de Cristo crest, from the Taos Plateau, 20 January
    # 2019. Mike Lewinski, CC BY 2.0. Bottom-aligned crop: only empty sky is lost.
    "1-sangre-de-cristo.jpg": dict(
        url="https://upload.wikimedia.org/wikipedia/commons/2/24/Full_moon_rising1.jpg",
        cache="full-moon-rising1.jpg",
        box=(0, 563, 5456, 3632), size=(5120, 2880),
        exposure=0.150, cool=(0.92, 0.98, 1.06), saturation=1.25,
        zenith=0.30, horizon=0.72, top=(0.20, 0.16)),
    # Cabezon Peak under a mackerel sky at dusk, 5 February 2010. Bob Wick, Bureau
    # of Land Management; public domain (US government work).
    "4-cabezon.jpg": dict(
        url="https://upload.wikimedia.org/wikipedia/commons/8/80/Cabezon_Peak_WSA_%289440790189%29.jpg",
        cache="cabezon-peak-wsa.jpg",
        box=(0, 585, 5616, 3744), size=(5120, 2880),
        exposure=0.130, cool=(0.92, 0.98, 1.06), saturation=1.25,
        zenith=0.30, horizon=0.82, top=(0.22, 0.14)),
}
LUMA = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def grade(name, f):
    w, h = f["size"]
    img = to_linear(load(fetch(f["url"], f["cache"]), f["box"], (w, h)))
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    # the sky falls off toward the zenith; the horizon sits at f["horizon"] of the frame
    sky = f["zenith"] + (1 - f["zenith"]) * smooth(y / f["horizon"]) ** 0.9
    # top edge: a further fade so the status bar keeps contrast
    floor, depth = f["top"]
    top = floor + (1 - floor) * smooth(y / depth)
    img = img * (f["exposure"] * sky * top)[..., None] * np.array(f["cool"], dtype=np.float32)
    lum = (img @ LUMA)[..., None]
    img = np.clip(lum + f["saturation"] * (img - lum), 0, None)
    # a gentle shoulder so snow and moon never clip, then back to sRGB
    img = img / (1 + 0.6 * img)
    finish(to_srgb(img), name, grain=0.006)


if __name__ == "__main__":
    for name in sys.argv[1:] or FRAMES:
        grade(name, FRAMES[name])
