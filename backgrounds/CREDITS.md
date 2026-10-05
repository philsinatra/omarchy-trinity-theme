# Background credits

Four frames from the same room after midnight: three views from the window —
New Mexico at dusk, from the Sangre de Cristo range to White Sands and the
Rio Puerco valley — and the lamp with nothing in its light.

| File | Subject | Source | Credit | Licence | Size |
| --- | --- | --- | --- | --- | --- |
| `1-sangre-de-cristo.jpg` | A full moon rising over the snow on the Sangre de Cristo crest, seen from the Taos Plateau at blue hour, 20 January 2019 | ["Full moon rising1.jpg"](https://commons.wikimedia.org/wiki/File:Full_moon_rising1.jpg) via Wikimedia Commons ([Flickr](https://www.flickr.com/photos/ikewinski/39857719973/)) | [Mike Lewinski](https://www.flickr.com/photos/ikewinski/) | [CC BY 2.0](https://creativecommons.org/licenses/by/2.0/) — modified, see below | 5120×2880, from 5456×3632 |
| `2-lamplight.webp` | The theme's own gradient: tungsten from off-frame left, cool night to the right, no objects | Original — `scripts/gradient.py` | Trinity contributors | MIT | 3840×2160 |
| `3-gloaming.jpg` | White Sands a few minutes after sunset: gypsum dunes, the belt of Venus over the San Andres range | ["Start of Gloaming, White Sands National Park, 04-03-2023"](https://commons.wikimedia.org/wiki/File:Start_of_Gloaming,_White_Sands_National_Park,_04-03-2023_(52801020712).jpg) via Wikimedia Commons ([Flickr](https://www.flickr.com/photos/charlesandmaggie/52801020712)) | [Charles & Maggie Boyer](https://www.flickr.com/people/charlesandmaggie/) | [CC BY 2.0](https://creativecommons.org/licenses/by/2.0/) — modified, see below | 3840×2160, from 8256×5504 |
| `4-cabezon.jpg` | Cabezon Peak, a lone volcanic neck over snow-dusted badlands in the Rio Puerco valley, under a mackerel sky at dusk, 5 February 2010 | ["Cabezon Peak WSA (9440790189).jpg"](https://commons.wikimedia.org/wiki/File:Cabezon_Peak_WSA_(9440790189).jpg) via Wikimedia Commons | Bob Wick, Bureau of Land Management | Public domain (work of the US federal government) | 5120×2880, from 5616×3744 |

Every frame is at least 3840×2160 and none is upscaled. Every frame keeps its
top edge dark (top 8% under 5% mean luminance) so the status bar has contrast.
`scripts/check.py` measures both.

The Sangre de Cristo range is the one Oppenheimer knew best: his ranch, Perro
Caliente, sat on its Pecos side. None of these places is the Trinity site,
and nothing in them refers to it.

## What was changed

The three photographs are graded by `scripts/grade.py`, whose `FRAMES` table
holds every crop and every adjustment. As CC BY asks, the changes are:

- **cropped** to 16:9 at native resolution, then downsampled — never upscaled.
  The White Sands crop (4392×2470 of 8256×5504) leaves three distant walkers
  and two trail markers out of frame; the other two crops lose only sky.
- **exposed down** in linear light (about 2.7–4 stops), cooled slightly, and
  given back the saturation darkening takes away, so each scene reads as it
  would a little later in the evening
- the sky **darkened toward the zenith** and the top edge faded

Nothing inside a crop is added, cloned or removed. The modified CC BY images
stay under CC BY 2.0. The photographers and the Bureau of Land Management do
not endorse this theme.

## Licences

The gradient is MIT, like the rest of the theme. The White Sands and Sangre de
Cristo photographs are CC BY 2.0, credited above. The Cabezon Peak photograph
is a US government work in the public domain; it is credited anyway.
