# Background credits

Six frames from the same room after midnight: the notes on the desk, the
marbles that kept count, the lamp, two views from the window, and the tower
the work was for.

| File | Subject | Source | Credit | Licence | Size |
| --- | --- | --- | --- | --- | --- |
| `1-handwriting.jpg` | Dense pages of working notes in a small, slanted script, dark ink over a gradient from black into slate | Original — `scripts/handwriting.py` | Trinity contributors; script face Herr Von Muellerhoff by Alejandro Paul (Sudtipos) | MIT (font: [SIL OFL 1.1](https://openfontlicense.org)) | 5120×2880 |
| `2-sangre-de-cristo.jpg` | A full moon rising over the snow on the Sangre de Cristo crest, seen from the Taos Plateau at blue hour, 20 January 2019 | ["Full moon rising1.jpg"](https://commons.wikimedia.org/wiki/File:Full_moon_rising1.jpg) via Wikimedia Commons ([Flickr](https://www.flickr.com/photos/ikewinski/39857719973/)) | [Mike Lewinski](https://www.flickr.com/photos/ikewinski/) | [CC BY 2.0](https://creativecommons.org/licenses/by/2.0/) — modified, see below | 5120×2880, from 5456×3632 |
| `3-marbles.jpg` | Three glass fishbowls filling with marbles on an old desk, one lamp | Original render — `scripts/marbles.py` (Mitsuba 3) | Render: Trinity contributors. Desk: [Wood Table Worn](https://polyhaven.com/a/wood_table_worn) scan by Dimitrios Savva and Rico Cilliers | MIT (scan: [CC0](https://polyhaven.com/license)) | 3840×2160 |
| `4-lamplight.webp` | The theme's own gradient: tungsten from off-frame left, cool night to the right, no objects | Original — `scripts/gradient.py` | Trinity contributors | MIT | 3840×2160 |
| `5-tower.jpg` | The Trinity shot tower and its shack against cumulus, July 1945 | ["Tower on top of which the first atomic bomb was detonated" (MED 316)](https://catalog.archives.gov/id/617585206), National Archives, RG 434 | Los Alamos (Manhattan Engineer District) | Public domain (work of the US federal government) | 3840×2160, from a 3040×1710 crop — see below |
| `6-cabezon.jpg` | Cabezon Peak, a lone volcanic neck over snow-dusted badlands in the Rio Puerco valley, under a mackerel sky at dusk, 5 February 2010 | ["Cabezon Peak WSA (9440790189).jpg"](https://commons.wikimedia.org/wiki/File:Cabezon_Peak_WSA_(9440790189).jpg) via Wikimedia Commons | Bob Wick, Bureau of Land Management | Public domain (work of the US federal government) | 5120×2880, from 5616×3744 |

Every frame is at least 3840×2160 and keeps its top edge dark (top 8% under
5% mean luminance) so the status bar has contrast. `scripts/check.py`
measures both. The Sangre de Cristo range is the one Oppenheimer knew best:
his ranch, Perro Caliente, sat on its Pecos side.

## The handwriting is not his

`1-handwriting.jpg` is a pattern in the manner of Oppenheimer's notebooks,
not a reproduction of them. His own unpublished papers at the Library of
Congress were dedicated to the public, but they are not digitized; the
handwritten pages that are online remain in copyright. So the frame is set
from an openly licensed script face, written fresh: original notes on the
physics he worked on in the 1930s (stellar collapse, cosmic-ray showers, the
positron, the mesotron), and lines from John Donne's Holy Sonnet XIV (1633,
public domain), the poem the name Trinity came from. It is drawn from vector
outlines at full resolution.

## The marbles are rendered, not photographed

In the film, Los Alamos keeps count of enriched material by dropping marbles
into glass bowls. `3-marbles.jpg` is an original still life on that idea, not
a frame from the film: three thick-walled fishbowls, path-traced with
Mitsuba 3, with marbles settled into each by a small physics pass, half of
them cat's-eyes. The only outside material is Poly Haven's CC0 scan of a
worn table.

## What was changed

The photographs are graded by `scripts/grade.py`, whose `FRAMES` table holds
every crop and every adjustment. As CC BY asks, the changes are:

- **cropped** to 16:9 and resampled to the output size. The Sangre de Cristo
  and Cabezon crops lose only sky and are downsampled.
- **exposed down** in linear light (about 2.7–3 stops), cooled slightly, and
  given back the saturation darkening takes away, so each scene reads as it
  would a little later in the evening
- the sky **darkened toward the zenith** and the top edge faded

The tower print is the one exception to "never upscaled". No archive holds
it larger than NARA's 16-bit scan of a 1945 print, and the 16:9 crop that
leaves out its border, caption and the vehicles at the base is 3040×1710. It
is enlarged 1.26× to 3840×2160 and given fresh film grain at full
resolution. Its sepia is neutralised toward graphite, and the sky taken
down toward black.

Nothing inside a crop is added, cloned or removed. The modified CC BY image
stays under CC BY 2.0. The photographers, the Bureau of Land Management and
the National Archives do not endorse this theme.

## Licences

The handwriting pattern, the marbles render and the gradient are MIT, like
the rest of the theme; the script face is under the SIL Open Font License,
and the desk scan is CC0. The Sangre de Cristo photograph is CC BY 2.0,
credited above. The tower and Cabezon Peak photographs are US government
works in the public domain; they are credited anyway.
