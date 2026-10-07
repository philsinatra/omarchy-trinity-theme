#!/usr/bin/env python3
"""Check that Trinity is shippable. Exits non-zero on the first class of failure.

  1. palette     genpalette's constraints hold, and colors.toml / btop.theme on
                 disk are exactly what it generates (nobody hand-edited them)
  2. backgrounds every frame is 16:9, at least 3840x2160, low mean luminance,
                 and the top 8% under 5% mean luminance for the status bar
  3. install     every file a `git clone` brings would survive Omarchy's staging
                 of git-installed themes (no Lua, no terminal configs, no
                 vscode.json, no symlinks), and every file the theme needs is there

Requires Pillow for (2).  Usage: check.py
"""
import os, re, sys, subprocess, contextlib, io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import genpalette

ROOT = genpalette.ROOT
REQUIRED = ["colors.toml", "btop.theme", "icons.theme", "keyboard.rgb", "backgrounds/CREDITS.md",
            "preview.webp", "docs-palette.webp", "unlock.png", "preview-unlock.png",
            "README.md", "CHANGELOG.md", "LICENSE"]
MAX_MEAN, MAX_TOP = 0.15, 0.05
THEME_SET = "/usr/bin/omarchy-theme-set"
FALLBACK_DENIED = ["alacritty.toml", "foot.ini", "ghostty.conf", "kitty.conf", "vscode.json"]


def check_palette():
    p = genpalette.build()
    with contextlib.redirect_stdout(io.StringIO()) as out:
        ok, r = genpalette.report(p)
    errs = [] if ok else ["genpalette constraints fail:\n" + out.getvalue()]
    for name, text in (("colors.toml", genpalette.emit_colors(p, r)), ("btop.theme", genpalette.emit_btop(p))):
        if text is not None and open(os.path.join(ROOT, name)).read() != text:
            errs.append(f"{name} differs from what genpalette.py generates")
    d, a, b = r["pairs"][0]
    print(f"palette     body {r['body']:.1f}:1  comments {r['cmt']:.1f}:1  syntax "
          f"{min(r['syn'].values()):.1f}-{max(r['syn'].values()):.1f}:1  closest {a}/{b} {d:.3f}")
    return errs


def check_backgrounds():
    from PIL import Image
    import numpy as np
    errs, d = [], os.path.join(ROOT, "backgrounds")
    frames = sorted(f for f in os.listdir(d) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")))
    if not 3 <= len(frames) <= 6:
        errs.append(f"expected 3 to 6 backgrounds, found {len(frames)}")
    for f in frames:
        im = Image.open(os.path.join(d, f))
        w, h = im.size
        lum = np.asarray(im.convert("L"), dtype=np.float32) / 255
        mean, top = lum.mean(), lum[:int(h * 0.08)].mean()
        print(f"background  {f:<22} {w}x{h}  mean {mean*100:4.1f}%  top8 {top*100:3.1f}%")
        if w < 3840 or h < 2160 or w * 9 != h * 16:
            errs.append(f"{f}: {w}x{h} is not 16:9 at 3840x2160 or larger")
        if mean > MAX_MEAN:
            errs.append(f"{f}: mean luminance {mean*100:.1f}% > {MAX_MEAN*100:.0f}%")
        if top >= MAX_TOP:
            errs.append(f"{f}: top 8% luminance {top*100:.1f}% >= {MAX_TOP*100:.0f}%")
        if f not in open(os.path.join(d, "CREDITS.md")).read():
            errs.append(f"{f}: not credited in backgrounds/CREDITS.md")
    return errs


def denied_names():
    try:
        m = re.search(r"^INSTALLED_THEME_DENIED=\(([^)]*)\)", open(THEME_SET).read(), re.M)
        return m.group(1).split()
    except (OSError, AttributeError):
        return FALLBACK_DENIED


def check_install():
    errs = []
    files = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                           cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    denied = denied_names()
    for f in files:
        top = f.split("/")[0]
        path = os.path.join(ROOT, f)
        if os.path.islink(path) or os.path.islink(os.path.join(ROOT, top)):
            errs.append(f"{f}: symlinks are dropped from git-installed themes")
        elif top.endswith(".lua") or top in denied:
            errs.append(f"{f}: Omarchy drops this from git-installed themes")
    for f in REQUIRED:
        if f not in files:
            errs.append(f"{f}: missing (or ignored by git)")
    src = os.path.basename(THEME_SET) if os.path.exists(THEME_SET) else "the fallback list"
    print(f"install     {len(files)} files would be cloned; denied by {src}: {len(errs) or 'none'}")
    return errs


if __name__ == "__main__":
    errs = check_palette() + check_backgrounds() + check_install()
    if errs:
        sys.exit("\nFAIL\n  " + "\n  ".join(errs))
    print("\nOK — palette, backgrounds and install all pass")
