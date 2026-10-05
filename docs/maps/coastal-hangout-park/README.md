# Japan Coastal Hangout Park: traced layout at true scale

The reference top view (`reference.webp`, made with an image model) traced
area by area and redrawn at its true scale.

## Method

- **True scale.** The reference's 1:500 bar (50 m = 195 px) disagrees with
  everything drawn. Measured on the road (two lanes ≈ 7 m), people and doors,
  the image reads at **6 px = 1 m**, so the park is about **207 × 158 m**.
- **Traced outlines.** Every outline on the site plan is traced from the image in
  pixels and converted with `X = (px − 60) / 6`, `Y = (py − 75) / 6`
  (see `P()` and the `*_PX` lists in `build.py`). Shapes, positions and
  proportions match the reference.
- **Check it.** On sheet L-101 in `index.html`, turn on **Reference underlay** to see
  the original under the plan at 1:1.
- **What was resized.** Only real-world objects: food trucks (6.5 × 2.5 m), parasols
  (Ø 3.0 m) and stage speakers. Stairs keep their traced footprints, with risers
  fitted to the level change.
- **Levels.** The image is flat, so the levels come from the stair lengths:
  - street +8.40, falling to +6.00 toward the station
  - plaza +3.60
  - event lawn raked +3.60 → +4.80 (the 11-riser flight at its tip)
  - promenade +3.15 (3 steps down from the plaza)
  - sand +0.90
  - sea ±0.00

- **Drafting (rev E).** Paving is merged per level with Shapely, so every
  junction is one surface with filleted corners and a single curb line.
  Planting beds are trimmed to that curb, retaining walls are 0.40 m and
  planter walls 0.30 m (both in poché), and stairs carry cheek walls, nosings
  and a DN arrow. Floors are plain fills (no paving pattern), since the engine
  supplies the textures. Sand is cream-white so it doesn't read as soil or timber.

## Sheets

All are in `index.html`, with standalone copies in `svg/`.

- REF: the reference and the plan side by side
- S-1: scale corrections and traced sizes
- L-101: site plan with key numbers 1–12 as in the reference, and the reference underlay
- L-201 / L-202: sections
- D-401: main stair, seaside steps, pier, central planter
- S-2 / S-3 / S-4: key locations, gameplay metrics, connections

`build.py` stops with an error if any walkable area can't be reached from Spawn A.

## Editing

```sh
pip install shapely   # once
python3 build.py      # rewrites index.html and svg/*.svg
```

Shared drawing helpers live in `../drawkit.py`.
