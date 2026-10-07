#!/usr/bin/env python3
"""Render the theme's cards from colors.toml with headless Chromium:

  unlock.png          the boot / disk-unlock wordmark: TRINITY in a drawing title block
  preview-unlock.png  that wordmark as Plymouth shows it
  docs-palette.webp   the palette card used in the README
  preview.webp        the theme-picker thumbnail: Neovim (aether, as Omarchy
                      generates it from colors.toml) and a terminal on a background

Every colour comes from ../colors.toml; the editor mock-up uses the highlight
rules of aether.nvim, which Omarchy's neovim.lua template loads.
Requires Pillow and a `chromium` binary.  Usage: cards.py
"""
import os, sys, subprocess, tempfile, tomllib, html
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oklch import cr, mix

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, os.pardir))
P = tomllib.load(open(os.path.join(ROOT, "colors.toml"), "rb"))
P.pop("mode")

MONO = "'JetBrainsMono Nerd Font', 'JetBrains Mono', monospace"
NARROW = "'Nimbus Sans Narrow', 'Liberation Sans Narrow', 'Arial Narrow', sans-serif"
TYPE = "'Nimbus Mono PS', 'Courier Prime', 'Courier New', monospace"

# The Omarchy mark, from /usr/share/omarchy/icon.txt: 27 x 26 units, one unit = two
# characters of a terminal row.
MARK = """\
███████████████████████████
███████████████████████████
██           ██          ██
██           ██          ██
██  ███████████    ████  ██
██  ███████████    ████  ██
██  ██               ██  ██
██  ██               ██  ██
██  ██               ██  ██
██  ██               ██  ██
██  ██               ██  ██
██  ██               ██  ██
██████               ██  ██
██████               ██  ██
██  ██               ██  ██
██  ██               ██  ██
██  ██               ██  ██
██  ██               ██  ██
██  ██               ██  ██
██  ██               ██  ██
██  ███████████████████  ██
██  ███████████████████  ██
██           ██          ██
██           ██          ██
███████████████  ██████████
███████████████  ██████████""".splitlines()


def mark_svg(color, size):
    cells = [(x, y) for y, row in enumerate(MARK) for x, ch in enumerate(row) if ch == "█"]
    rects = "".join(f'<rect x="{x}" y="{y}" width="1.02" height="1.02"/>' for x, y in cells)
    w = max(len(r) for r in MARK)
    return (f'<svg width="{size}" height="{size * len(MARK) / w:.1f}" viewBox="0 0 {w} {len(MARK)}" '
            f'fill="{color}" shape-rendering="crispEdges">{rects}</svg>')


def shoot(markup, out, w, h, transparent=False):
    with tempfile.TemporaryDirectory() as d:
        src, png = os.path.join(d, "card.html"), os.path.join(d, "card.png")
        open(src, "w").write(markup)
        cmd = ["chromium", "--headless=new", "--disable-gpu", "--hide-scrollbars",
               "--force-device-scale-factor=1", f"--window-size={w},{h}",
               "--allow-file-access-from-files", f"--screenshot={png}", "file://" + src]
        if transparent:
            cmd.insert(2, "--default-background-color=00000000")
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        im = Image.open(png)
        im = im.convert("RGBA" if transparent else "RGB")
        if out.endswith(".webp"):
            im.save(out, lossless=True, method=6)
        else:
            im.save(out, optimize=True)
    print(f"wrote {os.path.relpath(out, ROOT)} {w}x{h}")


def page(body, css, bg="transparent"):
    return f"""<!doctype html><meta charset="utf-8"><style>
html,body{{margin:0;padding:0;background:{bg};overflow:hidden}}
*{{box-sizing:border-box}}
{css}</style>{body}"""


# --------------------------------------------------------------------- unlock

def unlock():
    ink, rule, lamp = P["foreground"], P["dark_foreground"], P["accent"]
    label = P["muted"]
    css = f"""
.tb{{position:absolute;left:40px;top:14px;width:720px;height:160px;border:3px solid {rule};
     display:grid;grid-template-columns:120px 1fr 150px;grid-template-rows:1fr 38px}}
.c{{border-right:1px solid {rule};border-bottom:1px solid {rule};position:relative}}
.logo{{grid-row:1 / span 2;display:flex;align-items:center;justify-content:center}}
.name{{display:flex;align-items:center;justify-content:center;font:700 66px/1 {NARROW};
       letter-spacing:.34em;padding-left:.34em;color:{ink}}}
.side{{border-right:0;display:grid;grid-template-rows:1fr 1fr}}
.side>div{{border-bottom:1px solid {rule};padding:9px 12px}}
.side>div:last-child{{border-bottom:0}}
.lab{{font:600 9px/1 {TYPE};letter-spacing:.18em;color:{label};text-transform:uppercase}}
.val{{font:700 15px/1.25 {TYPE};letter-spacing:.12em;color:{ink};margin-top:4px}}
.foot{{border-bottom:0;grid-column:2 / span 2;display:flex;align-items:center;justify-content:center;
       padding:0 12px;font:600 11px/1 {TYPE};letter-spacing:.18em;color:{label};white-space:nowrap}}
"""
    body = f"""<div class="tb">
  <div class="c logo">{mark_svg(lamp, 58)}</div>
  <div class="c name">TRINITY</div>
  <div class="c side"><div><div class="lab">Sheet</div><div class="val">1 OF 1</div></div>
                      <div><div class="lab">Scale</div><div class="val">NONE</div></div></div>
  <div class="c foot"><span>THERE MUST BE NO BARRIERS TO FREEDOM OF INQUIRY</span></div>
</div>"""
    out = os.path.join(ROOT, "unlock.png")
    shoot(page(body, css), out, 800, 188, transparent=True)
    return out


def preview_unlock(logo_path):
    """Plymouth's layout: logo centred, entry 40 px below it, lock to its left."""
    W, H = 1920, 1080
    bg = Image.new("RGBA", (W, H), P["background"])
    logo = Image.open(logo_path)
    lx, ly = W // 2 - logo.width // 2, H // 2 - logo.height // 2
    bg.alpha_composite(logo, (lx, ly))
    ply = "/usr/share/omarchy/default/plymouth"
    # omarchy-plymouth-set tints these to the theme's text colour, keeping alpha
    def tint(path):
        im = Image.open(path).convert("RGBA")
        out = Image.new("RGBA", im.size, P["foreground"])
        out.putalpha(im.getchannel("A"))
        return out

    entry, lock, bullet = (tint(f"{ply}/{n}.png") for n in ("entry", "lock", "bullet"))
    ex, ey = W // 2 - entry.width // 2, ly + logo.height + 40
    bg.alpha_composite(entry, (ex, ey))
    lh = int(entry.height * 0.8)
    lock = lock.resize((int(84 * lh / 96), lh), Image.LANCZOS)
    bg.alpha_composite(lock, (ex - lock.width - 15, ey + entry.height // 2 - lh // 2))
    for i in range(4):
        bg.alpha_composite(bullet, (ex + 18 + i * (bullet.width + 6), ey + entry.height // 2 - bullet.height // 2))
    out = os.path.join(ROOT, "preview-unlock.png")
    bg.convert("RGB").save(out, optimize=True)
    print(f"wrote {os.path.relpath(out, ROOT)} {W}x{H}")


# --------------------------------------------------------------------- palette card

SPECTRUM = [  # name, slot, carries, side
    ("Ember", "orange", "numbers · bools", "warm"),
    ("Brass", "yellow", "types · accent", "warm"),
    ("Parchment", "bright_yellow", "constants", "warm"),
    ("Chalk", "green", "strings", "cool"),
    ("Verdigris", "cyan", "params · fields", "cool"),
    ("Plaster", "bright_cyan", "properties", "cool"),
    ("Blueprint", "blue", "functions", "cool"),
    ("Mauveine", "bright_magenta", "keywords", "apart"),
    ("Signal", "bright_red", "errors only", "signal"),
]
SURFACES = [("lead", "darker_background"), ("panel", "dark_background"), ("graphite", "background"),
            ("raised", "lighter_background"), ("dusk", "selection"), ("pencil", "muted"),
            ("dim text", "light_foreground"), ("paper", "foreground"), ("bright", "bright_foreground")]


def palette_card():
    bg, fg = P["darker_background"], P["foreground"]
    css = f"""
body{{font:400 15px/1.5 {MONO};color:{P['light_foreground']};padding:64px 72px}}
h1{{font:700 54px/1 {NARROW};letter-spacing:.42em;color:{P['bright_foreground']};margin:6px 0 26px}}
.rule{{height:2px;width:420px;background:linear-gradient(90deg,{P['accent']},{P['blue']})}}
.lede{{margin:18px 0 48px;color:{P['dark_foreground']}}}
.lede .w{{color:{P['accent']}}} .lede .c{{color:{P['blue']}}}
h2{{font:600 11px/1 {TYPE};letter-spacing:.42em;color:{P['muted']};margin:0 0 18px;text-transform:uppercase}}
.row{{display:grid;grid-template-columns:repeat(9,1fr);gap:14px}}
.sw{{height:92px;border-radius:2px}}
.nm{{font-weight:700;font-size:16px;margin-top:12px}}
.rl,.hx{{font-size:12.5px;color:{P['light_foreground']}}} .hx{{color:{P['dark_foreground']}}}
.ends{{display:flex;justify-content:space-between;margin:20px 0 52px;font:600 10.5px/1 {TYPE};
      letter-spacing:.36em;color:{P['muted']}}}
.surf{{display:grid;grid-template-columns:repeat(9,1fr);gap:0}}
.surf .sw{{height:62px;border-radius:0;border:1px solid {P['lighter_background']}}}
.surf .rl{{margin-top:10px}}
"""
    sw = "".join(
        f'<div><div class="sw" style="background:{P[k]}"></div><div class="nm" style="color:{P[k]}">{n}</div>'
        f'<div class="rl">{r}</div><div class="hx">{P[k]} · {cr(P[k], P["background"]):.1f}:1</div></div>'
        for n, k, r, _ in SPECTRUM)
    su = "".join(f'<div><div class="sw" style="background:{P[k]}"></div><div class="rl">{n}</div>'
                 f'<div class="hx">{P[k]}</div></div>' for n, k in SURFACES)
    body = f"""<h1>TRINITY</h1><div class="rule"></div>
<p class="lede">A desk after midnight. <span class="w">Warm is what things are</span>, under the lamp;
<span class="c">cool is what they do</span>, out in the night. Red is reserved for errors.</p>
<h2>Spectrum</h2><div class="row">{sw}</div>
<div class="ends"><span>&#9664; LAMP · WHAT THINGS ARE</span><span>WHAT THINGS DO · NIGHT &#9654;</span></div>
<h2>Surfaces &amp; text</h2><div class="surf">{su}</div>"""
    shoot(page(body, css, bg), os.path.join(ROOT, "docs-palette.webp"), 1400, 800)


# --------------------------------------------------------------------- preview

def S(cls, text):
    return f'<span class="{cls}">{html.escape(text)}</span>'


def code_lines():
    """A TypeScript buffer, tokenised by hand the way treesitter + aether colour it."""
    kw, kwf, fn, ty, st, nu, co, pa, pr, mb, pu, op, cm, cn, er = (
        "kw", "kwf", "fn", "ty", "st", "nu", "co", "pa", "pr", "mb", "pu", "op", "cm", "cn", "er")
    return [
        S(cm, "/** Integrate f over [a, b] by Simpson's rule, as it was done by hand. */"),
        S(kw, "import") + " " + S(pu, "{") + " " + S(cn, "TOLERANCE") + S(pu, ",") + " "
        + S(ty, "Estimate") + " " + S(pu, "}") + " " + S(kw, "from") + " " + S(st, '"./tables"') + S(pu, ";"),
        "",
        S(kw, "export") + " " + S(kwf, "function") + " " + S(fn, "simpson") + S(pu, "(")
        + S(pa, "f") + S(pu, ":") + " " + S(pu, "(") + S(pa, "x") + S(pu, ":") + " " + S(bt, "number") + S(pu, ")") + " " + S(op, "=>") + " "
        + S(bt, "number") + S(pu, ",") + " " + S(pa, "a") + S(pu, ":") + " " + S(bt, "number") + S(pu, ",") + " "
        + S(pa, "b") + S(pu, ":") + " " + S(bt, "number") + S(pu, ",") + " " + S(pa, "n") + " " + S(op, "=") + " " + S(nu, "64") + S(pu, ")")
        + S(pu, ":") + " " + S(ty, "Estimate") + " " + S(pu, "{"),
        "  " + S(kw, "if") + " " + S(pu, "(") + S(pa, "n") + " " + S(op, "%") + " " + S(nu, "2") + " " + S(op, "!==") + " " + S(nu, "0") + S(pu, ")")
        + " " + S(kw, "throw") + " " + S(kw, "new") + " " + S(ty, "RangeError") + S(pu, "(") + S(st, "`n must be even, got ")
        + S(pu, "${") + S(pa, "n") + S(pu, "}") + S(st, "`") + S(pu, ");"),
        "  " + S(kw, "const") + " h " + S(op, "=") + " " + S(pu, "(") + S(pa, "b") + " " + S(op, "-") + " " + S(pa, "a") + S(pu, ")")
        + " " + S(op, "/") + " " + S(pa, "n") + S(pu, ";"),
        "  " + S(kw, "let") + " sum " + S(op, "=") + " " + S(fn, "f") + S(pu, "(") + S(pa, "a") + S(pu, ")") + " " + S(op, "+") + " "
        + S(fn, "f") + S(pu, "(") + S(pa, "b") + S(pu, ");"),
        "",
        "  " + S(kw, "for") + " " + S(pu, "(") + S(kw, "let") + " i " + S(op, "=") + " " + S(nu, "1") + S(pu, ";") + " i " + S(op, "<") + " "
        + S(pa, "n") + S(pu, ";") + " i" + S(op, "++") + S(pu, ")") + " " + S(pu, "{"),
        "    sum " + S(op, "+=") + " " + S(pu, "(") + "i " + S(op, "%") + " " + S(nu, "2") + " " + S(op, "?") + " " + S(nu, "4") + " "
        + S(op, ":") + " " + S(nu, "2") + S(pu, ")") + " " + S(op, "*") + " " + S(fn, "f") + S(pu, "(") + S(pa, "a") + " " + S(op, "+")
        + " i " + S(op, "*") + " h" + S(pu, ");"),
        "  " + S(pu, "}"),
        "",
        "  " + S(cm, "// ") + S("todo", "TODO") + S(cm, ": check against the tables before morning"),
        "  " + S(kw, "const") + " drift " + S(op, "=") + " " + S(ty, "Math") + S(pu, ".") + S(fn, "abs") + S(pu, "(") + "sum "
        + S(op, "-") + " " + S(pa, "f") + S(pu, ".") + S(pr, "reference") + S(pu, ");"),
        "  " + S(kw, "return") + " " + S(pu, "{") + " " + S(pr, "value") + S(pu, ":") + " " + S(pu, "(") + "h " + S(op, "/") + " "
        + S(nu, "3") + S(pu, ")") + " " + S(op, "*") + " sum" + S(pu, ",") + " " + S(pr, "steps") + S(pu, ":") + " " + S(pa, "n")
        + S(pu, ",") + " " + S(pr, "exact") + S(pu, ":") + " drift " + S(op, "<") + " " + S(cn, "TOLERANCE") + " " + S(pu, "};"),
        S(pu, "}"),
    ]


bt = "bt"


def preview():
    p = P
    half = lambda c: mix(p["background"], c, 0.5)
    cur_bg = mix(p["background"], p["foreground"], 0.20)
    lines = code_lines()
    cursor = 13
    nums = []
    for i in range(len(lines)):
        rel = abs(i - cursor)
        nums.append(f'<span class="{"cln" if rel == 0 else "ln"}">{i + 1 if rel == 0 else rel}</span>')
    diag = {4: S("ve", "■ 'n' is possibly undefined"),
            12: S("vw", "▲ 'drift' is computed against an unchecked table")}
    rows = []
    for i, (n, l) in enumerate(zip(nums, lines)):
        cls = "row cur" if i == cursor else "row"
        sign = '<span class="gs">▎</span>' if i in (11, 12) else '<span class="gs"> </span>'
        rows.append(f'<div class="{cls}">{sign}{n} <span class="tx">{l}{"  " + diag[i] if i in diag else ""}</span></div>')
    ansi = ["red", "orange", "yellow", "green", "cyan", "blue", "magenta"]
    blocks = "".join(f'<span style="background:{p[k]}"></span>' for k in ansi) + "<br>" + \
             "".join(f'<span style="background:{p["bright_" + k]}"></span>' for k in ansi)
    border_active = f"linear-gradient(135deg,{p['accent']},{p['blue']})"
    idle = '#' + p['hyprland_inactive_border'].split('(')[1][:6]
    css = f"""
body{{width:1800px;height:1012px;background:#000 url('file://{ROOT}/backgrounds/1-handwriting.jpg') center/cover;
     font:400 15px/21px {MONO};color:{p['foreground']}}}
.bar{{position:absolute;left:0;right:0;top:0;height:26px;background:{p['darker_background']}e6;display:flex;
     align-items:center;justify-content:space-between;padding:0 14px;font-size:13px;color:{p['foreground']}}}
.bar .ws span{{margin-right:14px;color:{p['muted']}}} .bar .ws .on{{color:{p['accent']}}}
.win{{position:absolute;border-radius:0;padding:2px}}
.win.active{{background:{border_active}}} .win.idle{{background:{idle}}}
.inner{{width:100%;height:100%;background:{p['background']};position:relative;overflow:hidden}}
.ed{{left:10px;top:600px;width:1100px;height:402px}}
.term{{left:1120px;top:600px;width:670px;height:402px}}
.tabs{{height:30px;background:{p['dark_background']};display:flex;font-size:13px}}
.tabs span{{padding:5px 16px;color:{p['muted']}}} .tabs .sel{{color:{p['bright_foreground']};background:{p['background']};
          border-top:2px solid {p['accent']};font-weight:700}}
.code{{padding-top:8px;white-space:pre}}
.row{{height:21px}} .row.cur{{background:{cur_bg}}}
.gs{{display:inline-block;width:12px;color:{p['green']}}}
.ln,.cln{{display:inline-block;width:34px;text-align:right;color:{p['muted']}}} .cln{{color:{p['orange']};font-weight:700}}
.tx{{padding-left:14px}}
.kw{{color:{p['bright_magenta']};font-style:italic}} .kwf{{color:{p['bright_magenta']}}}
.fn{{color:{p['blue']};font-weight:700}} .ty{{color:{p['yellow']};font-weight:700}} .bt{{color:{p['foreground']}}}
.st{{color:{p['green']}}} .nu{{color:{p['orange']}}} .cn{{color:{p['bright_yellow']}}}
.pa{{color:{p['cyan']}}} .pr{{color:{p['bright_cyan']}}} .mb{{color:{p['cyan']}}}
.pu{{color:{half(p['foreground'])}}} .op{{color:{p['foreground']}}} .cm{{color:{p['muted']};font-style:italic}}
.todo{{background:{p['yellow']};color:{p['background']};font-weight:700;padding:0 2px}}
.ve{{color:{p['bright_red']};background:{mix(p['background'], p['red'], 0.1)};font-style:italic;padding:0 6px}}
.vw{{color:{p['yellow']};background:{mix(p['background'], p['yellow'], 0.1)};font-style:italic;padding:0 6px}}
.status{{position:absolute;left:0;right:0;bottom:0;height:24px;background:{p['dark_background']};display:flex;
        font-size:13px;line-height:24px}}
.status .mode{{background:{p['accent']};color:{p['background']};font-weight:700;padding:0 14px}}
.status span{{padding:0 12px}} .status .r{{margin-left:auto;color:{p['light_foreground']}}}
.t{{padding:14px 18px;white-space:pre;line-height:21px}}
.blocks span{{display:inline-block;width:52px;height:20px}}
"""
    g = lambda k, t: f'<span style="color:{p[k]}">{html.escape(t)}</span>'
    term = "\n".join([
        g("blue", "~/worksheets") + " " + g("green", "main") + " " + g("muted", "✓"),
        g("accent", "❯") + " git log --oneline -4",
        g("yellow", "c41e3a9") + " " + g("orange", "(HEAD → main)") + " check simpson against the tables",
        g("yellow", "7d0b2f1") + " tighten tolerance to 1e-9",
        g("yellow", "3a95e60") + " carry the remainder by hand",
        g("yellow", "0f17c2d") + " begin",
        "",
        g("accent", "❯") + " npm test",
        g("green", "✓") + " simpson.test.ts " + g("muted", "(6)"),
        g("green", "✓") + " tables.test.ts " + g("muted", "(3)"),
        g("bright_red", "✗") + " drift.test.ts " + g("muted", "(1)"),
        g("bright_red", "  expected drift < 1e-9, received 3.1e-7"),
        "",
        "Tests " + g("bright_red", "1 failed") + g("muted", " | ") + g("green", "9 passed") + g("muted", " (10)"),
        f'<span class="blocks">{blocks}</span>',
    ])
    body = f"""
<div class="bar"><div class="ws"><span class="on">●</span><span>2</span><span>3</span><span>4</span></div>
<div>Tuesday 00:40</div><div style="color:{p['light_foreground']}">󰖩&nbsp;&nbsp;󰕾&nbsp;&nbsp;󰁹 71%</div></div>
<div class="win active ed"><div class="inner">
  <div class="tabs"><span class="sel">simpson.ts</span><span>tables.ts</span><span>drift.test.ts</span></div>
  <div class="code">{''.join(rows)}</div>
  <div class="status"><span class="mode">NORMAL</span><span style="color:{p['accent']}">main</span>
    <span>src/simpson.ts</span><span class="r"><span style="color:{p['bright_red']}">● 1</span>
    <span style="color:{p['yellow']}">▲ 1</span>typescript&nbsp;&nbsp;&nbsp;74%&nbsp;&nbsp;&nbsp;14:9</span></div>
</div></div>
<div class="win idle term"><div class="inner"><div class="t">{term}</div></div></div>"""
    shoot(page(body, css, "#000"), os.path.join(ROOT, "preview.webp"), 1800, 1012)


if __name__ == "__main__":
    preview_unlock(unlock())
    palette_card()
    preview()
