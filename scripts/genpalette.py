#!/usr/bin/env python3
"""Trinity — regenerate ../colors.toml and ../btop.theme from OKLCH constants.

Edit the constants below, run this, then `omarchy theme set trinity`.

Trinity ships no Lua: Omarchy generates Neovim, VS Code, Helix, terminals,
Chromium and the rest from colors.toml, so a `git clone` install gets the
whole theme. The palette is therefore designed for the role each key plays
in those templates (aether.nvim and the VS Code template agree):

  yellow          types, accent     brass — the lamp
  orange          numbers           ember
  bright_yellow   constants         parchment
  green           strings           chalk
  cyan            parameters        verdigris
  bright_cyan     properties        plaster
  blue            functions         blueprint
  bright_magenta  keywords          mauveine — the language itself
  bright_red      errors            the only signal colour
  muted           comments          pencil, readable after midnight

The construction:
  * Surfaces are graphite: pencil lead at near-zero chroma, leaning the same
    faint violet as Adwaita-dark (hue 286). Nautilus, GTK dialogs and every
    other libadwaita window are always stock Adwaita-dark under Omarchy, so
    the chassis is made of the same material; the lamp is the only warmth.
  * Warm hues (brass, ember, parchment) carry what things *are* — types and
    literal values, the things under the lamp. Cool hues carry what things
    *do* and are *called* — functions, parameters, properties, strings: the
    night, the plaster, the blackboard. Keywords sit apart in mauveine, the
    aniline violet of copying pencils and ditto masters.
  * Inks, not neon: syntax chroma stays at 0.025-0.075 (errors excepted),
    and lightness does as much of the separating as hue.
  * Trinity is not Endurance re-tinted. Every role must sit a visible step
    away from the same role in Endurance's palette (ENDURANCE below).
The generator refuses to write if any colour leaves sRGB, if body text drops
under 11:1, comments under 4.8:1 or any syntax role under 7:1, if any two
roles a reader must tell apart fall closer than dE 0.07 in OKLab, if the
chassis drifts from Adwaita's grey or the lamp gets too saturated, or if any
role comes back within reach of Endurance.
"""
import os, sys, re, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oklch import hexof, in_gamut, cr, delta_e, srgb_to_oklch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, os.pardir))

GRAPHITE_H = 286.0   # pencil lead, with Adwaita-dark's own faint violet lean
PAPER_H = 85.0       # text is paper under the lamp, never pure grey

# Surfaces — (L, C). Same hue, rising lightness.
SURFACES = {
    "darker_background":  (0.155, 0.0055),
    "dark_background":    (0.185, 0.0060),
    "background":         (0.215, 0.0060),
    "lighter_background": (0.255, 0.0065),
}
SELECTION = (0.335, 0.040, 250.0)           # the window at dusk: cool, obvious
RULE = (0.360, 0.008, GRAPHITE_H)           # inactive window border

# Text — (L, C) on PAPER_H.
TEXT = {
    "muted":             (0.655, 0.012),    # comments, line numbers: pencil
    "dark_foreground":   (0.725, 0.011),
    "light_foreground":  (0.805, 0.010),
    "foreground":        (0.895, 0.010),    # body text
    "bright_foreground": (0.960, 0.008),
}

# Syntax — (L, C, H), keyed by the palette slot the templates read.
SYNTAX = {
    "red":            (0.715, 0.135, 27.0),
    "bright_red":     (0.750, 0.150, 26.0),   # errors
    "orange":         (0.740, 0.068, 37.4),   # numbers, booleans
    "bright_orange":  (0.830, 0.060, 45.0),
    "yellow":         (0.792, 0.070, 96.0),   # types, accent
    "bright_yellow":  (0.860, 0.072, 61.0),   # constants
    "green":          (0.841, 0.065, 150.1),  # strings
    "bright_green":   (0.895, 0.055, 150.0),
    "cyan":           (0.764, 0.062, 186.7),  # parameters, fields
    "bright_cyan":    (0.815, 0.031, 240.0),  # properties
    "blue":           (0.725, 0.054, 249.8),  # functions
    "bright_blue":    (0.820, 0.050, 250.0),
    "magenta":        (0.700, 0.065, 338.0),
    "bright_magenta": (0.780, 0.075, 338.0),  # keywords
}
BROWN = (0.585, 0.045, 60.0)

ORDER = ["red", "orange", "yellow", "green", "cyan", "blue", "magenta"]

# Roles a reader must tell apart, as the stock templates assign them.
ROLES = {
    "keyword": "bright_magenta", "type": "yellow", "constant": "bright_yellow",
    "number": "orange", "string": "green", "parameter": "cyan",
    "property": "bright_cyan", "function": "blue", "error": "bright_red",
    "comment": "muted", "variable": "foreground",
}
SYNTAX_ROLES = [r for r in ROLES if r not in ("comment", "variable")]
MIN_DE = 0.070
ADWAITA_VIEW = "#1d1d20"   # libadwaita dark view background (Nautilus file pane)
MAX_CHASSIS_C = 0.008      # graphite, not a colour: sits with Adwaita
MAX_ADWAITA_DE = 0.025     # editor background within a whisker of Nautilus
MAX_LAMP_C = 0.100         # brass and tungsten, not safety orange or gold foil

# Endurance v0.2.0, the sibling theme. Same templates, same role structure,
# so without a guard the two palettes converge. Errors may stay closer: red
# has to stay red.
ENDURANCE = {
    "keyword": "#c4a6f2", "type": "#eebd67", "constant": "#efe0a7", "number": "#ef9e70",
    "string": "#9aca90", "parameter": "#87d4d3", "property": "#a8ceff", "function": "#82b8ef",
    "error": "#ff7379",
}
MIN_FROM_ENDURANCE = 0.050
MIN_FROM_ENDURANCE_ERROR = 0.030


def build():
    p = {k: hexof(L, C, GRAPHITE_H) for k, (L, C) in SURFACES.items()}
    p.update({k: hexof(L, C, PAPER_H) for k, (L, C) in TEXT.items()})
    p["selection"] = hexof(*SELECTION)
    p.update({k: hexof(*v) for k, v in SYNTAX.items()})
    p["brown"] = hexof(*BROWN)
    p["accent"] = p["yellow"]
    p["cursor"] = p["yellow"]
    p["selection_foreground"] = p["bright_foreground"]
    p["selection_background"] = p["selection"]
    p["rule"] = hexof(*RULE)
    return p


def report(p):
    bad = [k for k, (L, C, H) in SYNTAX.items() if not in_gamut(L, C, H)]
    bad += [k for k, (L, C) in SURFACES.items() if not in_gamut(L, C, GRAPHITE_H)]
    bad += [k for k, (L, C) in TEXT.items() if not in_gamut(L, C, PAPER_H)]
    bad += [k for k, v in (("selection", SELECTION), ("rule", RULE), ("brown", BROWN)) if not in_gamut(*v)]
    bg = p["background"]
    roles = {r: p[k] for r, k in ROLES.items()}
    pairs = sorted((delta_e(roles[a], roles[b]), a, b)
                   for a, b in itertools.combinations(roles, 2))
    body, cmt = cr(p["foreground"], bg), cr(p["muted"], bg)
    syn = {r: cr(roles[r], bg) for r in SYNTAX_ROLES}
    chassis = max(C for _, C in SURFACES.values())
    lamp = SYNTAX["yellow"][1]
    print(f"out of gamut   : {bad or 'none'}")
    print(f"background     : {bg}")
    print(f"body text      : {body:.2f}:1  (>= 11)")
    print(f"comments       : {cmt:.2f}:1  (>= 4.8)")
    for r, k in ROLES.items():
        print(f"  {r:<10} {k:<15} {p[k]}  {cr(p[k], bg):5.2f}:1")
    print(f"syntax range   : {min(syn.values()):.2f} - {max(syn.values()):.2f}:1  (>= 7)")
    adw = delta_e(bg, ADWAITA_VIEW)
    endu = {r: delta_e(roles[r], h) for r, h in ENDURANCE.items()}
    endu_ok = all(d >= (MIN_FROM_ENDURANCE_ERROR if r == "error" else MIN_FROM_ENDURANCE) for r, d in endu.items())
    near = min((d, r) for r, d in endu.items() if r != "error")
    print(f"chassis chroma : {chassis:.4f}  (<= {MAX_CHASSIS_C})   lamp chroma {lamp:.3f}  (<= {MAX_LAMP_C})")
    print(f"vs Adwaita     : dE {adw:.3f} from {ADWAITA_VIEW}  (<= {MAX_ADWAITA_DE})")
    print(f"vs Endurance   : nearest role {near[1]} {near[0]:.3f} (>= {MIN_FROM_ENDURANCE}), "
          f"error {endu['error']:.3f} (>= {MIN_FROM_ENDURANCE_ERROR})")
    print("closest roles  : " + ", ".join(f"{a}/{b} {d:.3f}" for d, a, b in pairs[:4]))
    ok = (not bad and body >= 11 and cmt >= 4.8 and min(syn.values()) >= 7
          and pairs[0][0] >= MIN_DE and chassis <= MAX_CHASSIS_C and lamp <= MAX_LAMP_C
          and adw <= MAX_ADWAITA_DE and endu_ok)
    return ok, dict(body=body, cmt=cmt, syn=syn, pairs=pairs, adw=adw, endu=endu)


def emit_colors(p, r):
    g = lambda *ks: "\n".join(f'{k} = "{p[k]}"' for k in ks)
    d, a, b = r["pairs"][0]
    lamp, night, rule = p["yellow"][1:], p["blue"][1:], p["rule"][1:]
    return f'''# Trinity — Omarchy theme palette
#
# GENERATED by scripts/genpalette.py — do not hand-edit.
#
# Graphite surfaces at hue {GRAPHITE_H:.0f}deg, near-zero chroma. Each syntax
# slot is chosen for the role Omarchy's templates give it (Neovim, VS Code):
#   bright_magenta keywords · yellow types · orange numbers · bright_yellow
#   constants · blue functions · cyan parameters · bright_cyan properties ·
#   green strings · bright_red errors · muted comments
#
# Measured against background {p["background"]}:
#   body text    {r["body"]:.1f}:1
#   comments     {r["cmt"]:.1f}:1
#   syntax       {min(r["syn"].values()):.1f} - {max(r["syn"].values()):.1f}:1
#   closest pair {a}/{b} dE {d:.3f} (OKLab)

mode = "dark"

# Brass: the lamp. Borders, focus, cursor, bar accents.
{g("accent", "cursor", "selection", "muted")}

# Graphite — one hue, rising lightness, the same grey as Adwaita-dark.
{g("background", "dark_background", "darker_background", "lighter_background")}

# Paper under the lamp: the text ramp.
{g("foreground", "dark_foreground", "light_foreground", "bright_foreground")}

{g(*ORDER, "brown")}

{g(*["bright_" + k for k in ORDER])}

{g("selection_foreground", "selection_background")}

# Window borders: the lamp on the left, the night on the right.
hyprland_active_border = "rgba({lamp}ee) rgba({night}ee) 45deg"
hyprland_inactive_border = "rgba({rule}aa)"
'''


BTOP_TPL = "/usr/share/omarchy/default/themed/btop.theme.tpl"


def emit_btop(p):
    """Omarchy's btop template, with red kept for real alarms (temperature)
    instead of decorating the network box and ordinary graph peaks."""
    if not os.path.exists(BTOP_TPL):
        return None
    t = re.sub(r"\{\{\s*([a-z_]+)\s*\}\}", lambda m: p.get(m.group(1), m.group(0)), open(BTOP_TPL).read())
    t = t.replace(f'theme[net_box]="{p["red"]}"', f'theme[net_box]="{p["blue"]}"')
    t = re.sub(r'^(theme\[(?:available|download)_(?:mid|end)\]=)"' + p["red"] + '"',
               lambda m: m.group(1) + '"' + p["orange"] + '"', t, flags=re.M)
    alarms = [l for l in t.splitlines() if p["red"] in l and not l.startswith("theme[temp_end]")]
    if alarms:
        sys.exit("refusing to write btop.theme: red used outside alarms:\n  " + "\n  ".join(alarms))
    return "# Trinity btop theme — GENERATED by scripts/genpalette.py from Omarchy's template.\n" \
           "# Red is kept for alarms only.\n" + t


if __name__ == "__main__":
    p = build()
    ok, r = report(p)
    if not ok:
        sys.exit("\nrefusing to write: a constraint above failed")
    outputs = (("colors.toml", emit_colors(p, r)), ("btop.theme", emit_btop(p)))
    for name, text in outputs:
        if text is None:
            print(f"skipped {name} (template not found)")
            continue
        with open(os.path.join(ROOT, name), "w") as f:
            f.write(text)
        print(f"wrote {name}")
