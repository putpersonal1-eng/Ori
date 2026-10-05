# Umi Seaside Park: traced layout at true scale

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
  - event lawn +3.60, level with the plaza; the curved flight at its tip takes the east path (+4.80) down 8 risers
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
- D-401: main stair, seaside steps, pier, and the Ori logo landmark (fountain, plinth, logo)
- A-501: arcade elevations (front from the reference facade image, side, back)
- A-502: Fashion & Goods and café elevations
- A-503: Lifestyle & Souvenir elevations
- A-504: food truck, street kiosk, beach hut and stage (front, side, back)
- A-505: main stair with escalators, the shotengai gate and the mural walls
- P-601: perspective, with a live three.js model (orbit, preset views) and rendered stills;
  hills wall the map on three sides with a tunnel at each end of the road. Structures and
  buildings are modelled in detail (framed openings, copings, tile eaves, 3D lettering,
  railings, escalators, the gate) with procedural PBR materials and ambient occlusion;
  trees, plants and rocks stay simple placeholders for the engine. The arcade has a full
  interior (dark purple game hall), and the Ori logo landmark stands in the central fountain
- S-2 / S-3 / S-4: key locations, gameplay metrics, connections

`build.py` stops with an error if any walkable area can't be reached from Spawn A.

## Editing

```sh
pip install shapely   # once
python3 build.py      # rewrites index.html, svg/*.svg and model/scene.json
```

To refresh the rendered perspective stills in `img/` (needs Node and a Chromium):

```sh
npm i --no-save three@0.160.0 playwright
node render_views.js && python3 build.py
```

Files:

- `build.py`: plan, sections, details, schedules and the page
- `elev.py`: elevation sheets A-501 to A-504
- `model3d.py`: builds the 3D model from the plan data (`model/scene.json`)
- `kit3d.py`: detailed parts for the 3D model (faces, windows, doors, eaves, stairs, rails, props)
- `interior3d.py`: the arcade interior (layout in `elev.ARC_IN`, shared with the plan)
- `landmark.py`: the Ori logo landmark (logo shape, plinth, fountain), shared by the plan, sections, D4 and the model
- `park3d.js`: the three.js viewer used on the page and by `render_views.js`

Every tree and palm is checked against the planting (beds, lawn, planter soil; palms may also
stand on sand). Any that lands on paving, decks or road is moved to the nearest planting within
6 m; street trees get tree pits on the town-side pavement. Palms on the sand keep 1.6 m off the
sea wall. Lamps keep their traced spots unless they land in planting, under a crown, near a stair,
bench, parasol set or truck, or within 1 m of a walkway edge; then they move to the nearest clear
spot (`place_lamps`). In the model, planters stop short of walls, stair cheeks and facades, roof
furniture is built only by its building, and soil and sand are cut into cells so their surfaces
follow the real levels.

Shared drawing helpers live in `../drawkit.py`.
