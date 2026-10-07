#!/usr/bin/env python3
"""Render backgrounds/1-handwriting.jpg — dense pages of working notes, dark on dark.

Not Oppenheimer's hand, and not meant to be read: a pattern in the manner of
his notebooks. Small, fast, right-leaning script, lines packed close,
exponents raised, a word struck out here and there, a phrase underlined,
written over a gradient that runs from black into dark slate. The ink sits
darker than the slate, so the writing shows where the slate is lightest and
disappears into the black.

The script face is Herr Von Muellerhoff (Alejandro Paul, Sudtipos; SIL OFL 1.1),
fetched once from the Google Fonts repository. The text is original: notes
on the physics he worked on in the 1930s (stellar collapse, cosmic-ray
showers, the positron, the mesotron), with lines from John Donne's Holy
Sonnet XIV (1633), the poem the name Trinity came from. Everything is drawn
from vector outlines at the final resolution, so nothing is upscaled.

Requires numpy and Pillow.  Usage: handwriting.py
"""
import os, sys, math, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from photo import fetch, to_linear, to_srgb, blur, smooth, finish
from oklch import hexof

OUT_NAME = "1-handwriting.jpg"
W, H = 5120, 2880
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/herrvonmuellerhoff/HerrVonMuellerhoff-Regular.ttf"
SIZE = 60                 # px; the script is small, as his was
LEADING = 1.42            # line pitch / size: lines packed close
TILT = -2.4               # degrees: the page sits a little askew
SEED = 1904               # his birth year

# The gradient: black at the top left, dark slate toward the bottom right.
BLACK = hexof(0.105, 0.004, 286)
SLATE = hexof(0.345, 0.014, 245)
INK_DEPTH = 0.68          # ink transmits this much less light than the slate around it

# Original notes, with ^{} and _{} for raised and lowered type.
NOTES = """
on the continued contraction of a heavy star. once the sources of thermonuclear energy are spent the
pressure can no longer hold, and the radius falls toward r_{g} = 2GM/c^{2} ; to an outside observer the
collapse slows and the light from the surface is reddened without limit, while for an observer riding
with the matter the fall is finished in a time of order (r_{0}^{3}/2GM)^{1/2} , a day or less
the neutron core : if the mass exceeds some 0.7 sun the degenerate neutrons cannot support it ; check
against Tolman's static solutions before writing to Volkoff
showers in the upper air : an electron of energy E radiates in a length X_{0} , the photon materializes
in a pair, and the number doubles at each step until E/2^{n} falls to the critical energy ; the
penetrating component cannot be electrons at all , a heavier particle , the mesotron , with a life
tau = 2 x 10^{-6} sec at rest and longer in flight by (1 - v^{2}/c^{2})^{-1/2}
the positron as a hole in the sea of negative energy states ; the self energy diverges again , as
log (hbar / mc a) , and the charge of the electron must be renormalized ; not yet , not this way
the deuteron : binding 2.2 MeV , the force short in range , a depth of some 20 MeV over 2 x 10^{-13} cm ;
on a heavy nucleus the deuteron gives up its neutron and the proton is turned back , Phillips ' process
dE/dx = (4 pi N Z e^{4} / m v^{2}) log (2 m v^{2} / I) for the loss in passing through matter
batter my heart , three person'd God ; for you as yet but knock , breathe , shine , and seek to mend
that I may rise and stand , o'erthrow me , and bend your force to break , blow , burn and make me new
the cross section for scattering of fast electrons falls as the energy rises ; at small angles the
Rutherford law holds , at large ones the screening and the spin both matter ; compute for Z = 79
the field of the electron is not to be taken classically at distances below e^{2}/mc^{2}
consider again the stability : a star of mass M , radius R , the gravitational energy GM^{2}/R
against the Fermi energy of the degenerate gas , which goes as N^{5/3}/R^{2} when slow ,
as N^{4/3}/R when relativistic , and there is the limit ; for neutrons it lies lower than one had hoped
reasonable men may differ ; the calculation does not
""".strip()


def tokens(text):
    """Split into words, keeping ^{..} and _{..} attached to the word before them."""
    return re.findall(r"\S+", text.replace("\n", " "))


def draw_word(draw, x, y, word, font, small, fill):
    """Draw one word, handling raised ^{} and lowered _{} groups; returns the advance."""
    x0 = x
    for part in re.split(r"([\^_]\{[^}]*\})", word):
        if not part:
            continue
        if part[0] in "^_" and part[1:2] == "{":
            body = part[2:-1]
            # align the small type's baseline to the line's, then raise or lower it
            base = font.getmetrics()[0] - small.getmetrics()[0]
            dy = base + (-0.30 if part[0] == "^" else 0.12) * font.size
            draw.text((x, y + dy), body, font=small, fill=fill)
            x += small.getlength(body)
        else:
            draw.text((x, y), part, font=font, fill=fill)
            x += font.getlength(part)
    return x - x0


def write_page(font_path):
    rng = np.random.default_rng(SEED)
    # draw on a canvas big enough to stay full after the tilt
    cw, ch = int(W * 1.08), int(H * 1.12)
    mask = Image.new("L", (cw, ch), 0)
    draw = ImageDraw.Draw(mask)
    words = tokens(NOTES)
    wi = 0
    pitch = SIZE * LEADING
    y = -0.3 * SIZE
    margin = 0.035 * cw
    while y < ch:
        size = SIZE * rng.uniform(0.96, 1.04)
        font = ImageFont.truetype(font_path, round(size))
        small = ImageFont.truetype(font_path, round(size * 0.62))
        x = margin + rng.uniform(-10, 10) + (rng.uniform(40, 220) if rng.random() < 0.12 else 0)
        right = cw - margin - rng.uniform(0, 160)
        line_y = y + rng.uniform(-3, 3)
        drift = rng.uniform(-6, 6)                       # the line wanders off level
        while x < right:
            word = words[wi % len(words)]
            wi += 1
            wy = line_y + drift * (x / cw)
            adv = draw_word(draw, x, wy, word, font, small, 255)
            if rng.random() < 0.018:                     # struck out
                yy = wy + 0.62 * size
                pts = [(x - 4 + t * (adv + 8), yy + 3 * math.sin(t * 9 + wi)) for t in np.linspace(0, 1, 12)]
                draw.line(pts, fill=230, width=max(2, round(size / 26)))
            elif rng.random() < 0.012:                   # underlined
                yy = wy + 0.98 * size
                draw.line([(x, yy), (x + adv, yy + rng.uniform(-3, 3))], fill=220, width=max(2, round(size / 30)))
            x += adv + size * rng.uniform(0.28, 0.42)
            if word.endswith(";") and rng.random() < 0.10:
                break                                    # a thought ends early
        y += pitch * rng.uniform(0.97, 1.05) + (pitch * 0.6 if rng.random() < 0.05 else 0)
    mask = mask.rotate(TILT, resample=Image.BICUBIC, center=(cw / 2, ch / 2))
    left, top = (cw - W) // 2, (ch - H) // 2
    return np.asarray(mask.crop((left, top, left + W, top + H)), dtype=np.float32) / 255


def main():
    font_path = fetch(FONT_URL, "HerrVonMuellerhoff-Regular.ttf")
    ink = write_page(font_path)
    ink = blur(ink, 0.6)                                 # a fine nib on soft paper bleeds a little
    rng = np.random.default_rng(SEED + 1)
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    x = np.linspace(0, 1, W, dtype=np.float32)[None, :]

    # pressure: the pen presses harder and lighter across the page
    press = blur(rng.standard_normal((H // 8, W // 8)).astype(np.float32), 6)
    press = np.asarray(Image.fromarray(press).resize((W, H), Image.BICUBIC))
    ink = ink * np.clip(0.80 + 0.35 * press / (press.std() + 1e-6) * 0.5, 0.55, 1.0)

    # the ground: black at the top left into slate at the bottom right, with a stone's mottle
    t = smooth(np.clip(0.62 * y + 0.38 * x - 0.08, 0, 1) / 0.92) ** 1.15
    black = to_linear(np.array([int(BLACK[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255)
    slate = to_linear(np.array([int(SLATE[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255)
    ground = black + (slate - black) * t[..., None]
    mottle = blur(rng.standard_normal((H // 4, W // 4)).astype(np.float32), 3)
    mottle = np.asarray(Image.fromarray(mottle).resize((W, H), Image.BICUBIC))
    ground *= (1 + 0.035 * mottle / (mottle.std() + 1e-6))[..., None]

    img = ground * (1 - INK_DEPTH * ink[..., None])
    img *= (0.35 + 0.65 * smooth(y / 0.12))[..., None]  # the status bar always sits on black
    finish(to_srgb(img), OUT_NAME, grain=0.005, seed=SEED)


if __name__ == "__main__":
    main()
