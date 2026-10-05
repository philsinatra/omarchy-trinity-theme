# Changelog

All notable changes to Trinity are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-05

First release.

### Added

- Graphite chassis (`#19191c`) at near-zero chroma, measured against the
  Adwaita-dark that Nautilus and GTK dialogs always use under Omarchy: the
  editor background is 0.017 OKLab from Nautilus's file pane.
- "Inks" syntax palette generated in OKLCH, designed for the roles Omarchy's
  templates give each slot:
  - lamp: ember numbers, brass types and accent, parchment constants
  - night: chalk strings, verdigris parameters, plaster properties, blueprint
    functions
  - apart: mauveine keywords
  - signal: red for errors only
- Enforced checks: body text 12.8:1, comments 5.5:1, every syntax role at
  least 7.2:1, every pair of roles at least 0.071 apart in OKLab, chassis and
  lamp chroma ceilings, a ceiling on distance from Adwaita, and a floor on
  distance from Endurance's palette (every role 0.057 or more, errors 0.038).
- `btop.theme` with red reserved for alarms.
- `icons.theme` (`Yaru-yellow-dark`) and `keyboard.rgb` (brass).
- Four backgrounds, each with a dark top edge:
  - `1-sangre-de-cristo.jpg`, moonrise over the Sangre de Cristo (Mike
    Lewinski, CC BY 2.0)
  - `2-lamplight.webp`, an original lossless gradient
  - `3-gloaming.jpg`, White Sands at dusk (Charles & Maggie Boyer, CC BY 2.0)
  - `4-cabezon.jpg`, Cabezon Peak at dusk (Bob Wick, BLM, public domain)
- Plymouth unlock title block with "There must be no barriers to freedom of
  inquiry" (Oppenheimer, *Life*, 1949), its preview, the theme-switcher preview
  and the palette card, all rendered from `colors.toml`.
- `scripts/check.py`: palette, background luminance and git-install checks.

[0.1.0]: https://github.com/philsinatra/omarchy-trinity-theme/releases/tag/v0.1.0
