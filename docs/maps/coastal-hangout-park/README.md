# Japan Coastal Hangout Park: scale-corrected layout

The reference top view (`reference.webp`, made with an image model) redrawn at
true scale. The layout is kept as drawn; sizes and levels are corrected.

## What was wrong with the reference

The 1:500 scale bar (50 m = 195 px) disagrees with everything drawn on the map.
Measured against people, food trucks and doors, the image reads at about
**6 px per metre**, so the park is about **205 × 158 m**, not 330 × 260 m.
At that scale most buildings are right. These were drawn too big and are corrected:

| Element | As drawn | Corrected |
| --- | --- | --- |
| Central planter + seats | Ø 27 m | Ø 8 m planter, Ø 14 m bench ring |
| Plaza paving | Ø 77 m | Ø 56 m |
| Main entrance stair | 13 × 16 m, one flight | 12 × 12 m, 2 × 16R + landing |
| Beach stairs | 11 × 11 m | 6 × 6.2 m, 2 × 8R |
| Pier | 7.5 m wide | 5 m wide, head 24 × 10 m |
| Food trucks / parasols / palms | 7.5 m / Ø 5 m / Ø 10 m | 6.5 m / Ø 2.6 m / Ø 6 m |
| Small stage deck | 25 × 22 m | fan R 13 m |

The full list is in `index.html` (sheet S-1).

## Sheets

`index.html` holds all of these. Standalone copies are in `svg/`.

- REF: the reference and the corrected plan side by side
- S-1: scale corrections
- L-101: site plan with key numbers 1–12 as in the reference
- L-201 / L-202: sections (street +8.40, plaza +3.60, sand +1.20, sea ±0.00)
- D-401: entrance stair, sea wall + beach stair, pier, central planter
- S-2 / S-3: key locations and gameplay metrics

## Editing

```sh
python3 build.py   # rewrites index.html and svg/*.svg
```

Shared drawing helpers live in `../drawkit.py`.
