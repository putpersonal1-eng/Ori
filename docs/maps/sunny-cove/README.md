# Sunny Cove Park: hangout map layout

A seaside social hangout map: a cozy park with an arcade, a café and small shops,
stepping down in four levels to a beach in front.

Open `index.html` in a browser for the full drawing set with layer toggles.
The standalone sheets in `svg/` open at natural size and import into Figma,
Illustrator or Inkscape.

| Sheet | Content |
| --- | --- |
| L-101 | Site plan: zones, 20 m grid (A–J / 1–10), spawns, circulation, sightlines |
| L-201 | Section A–A along the main axis (X = 100), looking east |
| L-202 | Section B–B across the plaza (Y = 56), looking north |
| A-301 | Pixel Pop Arcade, ground and upper floor plans |
| A-302 | Wave Café plan and sea-view terrace |
| D-401 | Details: Sunset Steps, sea wall + beach stair, skate set, shop unit |
| S-1, S-2 | Zone schedule and gameplay metrics (in `index.html`) |

## Key numbers

- Footprint 200 × 200 m playable, 30–50 players per instance.
- Units in metres (1 m = 100 Unreal units). Z datum ±0.00 = sea level.
- Levels: Hill Terrace +9.60 · Chalk Plaza +4.80 · lawn / skate / promenade +2.40 · beach +1.20 → ±0.00 · sea to −3.00.
- Plan X runs east and Y runs south, measured from the north-west corner of grid cell A1.
- Assumed avatar is 1.30 m tall (chibi), with max step 0.45 m and jump apex 0.90 m. Confirm these against the real character before blockout.

## Editing

All geometry lives in `build.py` (Python 3, no dependencies). Change a number, then rebuild:

```sh
python3 build.py   # rewrites index.html and svg/*.svg
```
