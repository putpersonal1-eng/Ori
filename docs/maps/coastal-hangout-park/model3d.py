"""3D model of the Umi Seaside Park for the perspective views (P-601).

The model is generated from the same data as the drawings: the walkable surfaces come
from build.hardscape(), planters, trees, palms, parasols, benches, stairs, walls, rails,
trucks and rocks are recorded while build.site_plan() draws them, and the buildings follow
the elevations in elev.py, built with the detailed parts in kit3d.py. Trees, plants and
rocks stay as simple placeholders for the engine. Plan metres map to three.js as
x = east, z = south, y = level above sea (±0.00).
"""
import json
import math
import random

import numpy as np
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
from shapely.ops import nearest_points, unary_union
from shapely.prepared import prep

import elev
import kit3d as K
from interior3d import build_arcade_interior
from landmark import build_landmark

COL = {
    "paver": "#E3E6E8", "street": "#CDD3D8", "road": "#6E7780", "timber": "#C9935C", "timber-2": "#A87A4C",
    "lawn": "#8CC36A", "bed": "#5E9C4C", "shrub": "#4F8F45", "sand": "#F7F1DE", "sand-wet": "#E6DCC0",
    "seabed": "#9FCFCB", "water": "#43A9C6", "conc": "#CDD1D3", "conc-2": "#BEC3C7", "rock": "#A9A39A", "town": "#D7DCE1",
    "town-roof": "#AEB8C2", "glass": "#BFE6F0", "glow": "#FFE2A0", "dark": "#2E333B", "steel": "#9AA6B2",
    "white": "#F7F7F5", "cream": "#EFE8D8", "wall": "#EFE6D6", "coral": "#E98564",
    "yel": "#F6C833", "yel-2": "#E0A915", "yel-3": "#FFE07A", "pink": "#F59BC3", "lilac": "#B9A2EE",
    "blue": "#2F8FE8", "red": "#E8414E", "green": "#3FB950", "cyan": "#24ABCC", "navy": "#2C3E57",
    "tree": "#6DAA55", "tree-2": "#5B9A49", "sak": "#F4B8D1", "palm": "#5E9A4A", "trunk": "#8A6A4A", "mint": "#A9DCC6",
    "thatch": "#CFA866", "plaster": "#F6F3EC", "kawara": "#3B4352", "verm": "#D9432F", "gold": "#C9A24A",
    "portal": "#AEB6BF", "indigo": "#2E3FB0", "wood-d": "#7E5234", "arc": "#D8343F", "arc-2": "#B72632",
    "in-wall": "#B4232C", "in-floor": "#1E1718", "in-ceil": "#241A1B", "cab": "#D8343F", "cab-2": "#F6C833",
    "drum": "#F3EBDD", "in-dark": "#2B2224", "neon-r": "#FF4A4A", "neon-w": "#FFF2D8", "neon-o": "#FF9A2E", "navy-d": "#1B2A4A", "neon-p": "#FF5FC8", "neon-g": "#9BFF5A", "neon-c": "#3FE6F0",
    "neon-y": "#FFE45A", "neon-v": "#9B6BFF",
    "ori-p": "#3A1A7A", "ori-l": "#E6D9FF", "jet": "#E8F6FF",
    "tile-b": "#2F6DB5", "brick": "#CFA088", "stone-w": "#EEEAE2", "warm": "#FFE3A8", "facade": "#DCE1E6", "rubber": "#23262B",
}


class Scene:
    def __init__(self, b):
        self.b = b
        self.pal, self.pal_i = [], {}
        self.slabs, self.boxes, self.cyls, self.prisms = [], [], [], []
        self.segs, self.exts, self.tori, self.texts, self.plates = [], [], [], [], []
        self.trees, self.shrubs, self.labels, self.rocks = [], [], [], []
        self.eggs = []
        self.hard = []          # (polygon, hspec) for level lookups
        self._prep = None
        self.terrain = None
        self.lights = []

    # ------------------------------------------------------------- data
    def c(self, name):
        hexv = COL.get(name, name)
        if hexv not in self.pal_i:
            self.pal_i[hexv] = len(self.pal)
            self.pal.append(hexv)
        return self.pal_i[hexv]

    @staticmethod
    def ring(coords, nd=2):
        return [[round(x, nd), round(z, nd)] for x, z in list(coords)[:-1]]

    def polys(self, g, simplify=.05):
        if g.is_empty:
            return []
        g = g.simplify(simplify, preserve_topology=True)
        parts = list(g.geoms) if isinstance(g, MultiPolygon) else [g] if isinstance(g, Polygon) else \
            [q for q in getattr(g, "geoms", []) if isinstance(q, Polygon)]
        return [q for q in parts if q.area > .02]

    def slab(self, g, top, color, mat="std", bot=-1.0, hard=True, vh=None, skirt=True, soft=True, skirt_color=None, skirt_on=None):
        """Ground surface: polygon with a height spec (number, axis profile) or per-vertex heights."""
        if not hard and mat == "std" and soft:
            mat = "soft"
        if isinstance(top, dict) and vh is None:
            # sloped profile: cut into cells so the surface follows the profile between the outline's corners
            self.grid_slab(g, lambda x, z, t=top: self.h_eval(t, x, z), color, mat, cell=3.0, bot=bot)
            if hard:
                for q in self.polys(g):
                    self.hard.append((q, top))
                self._prep = None
            return
        for q in self.polys(g):
            rec = {"o": self.ring(q.exterior.coords), "h": [self.ring(r.coords) for r in q.interiors],
                   "c": self.c(color), "m": mat, "b": bot}
            if not skirt:
                rec["ns"] = 1
            if skirt_color:
                rec["sk"] = self.c(skirt_color)               # exposed edge reads as a concrete retaining face
            if skirt_on is not None:                          # skirt only the edges on the outline (not between cells)
                def on(ring):
                    out = []
                    for (x0, z0), (x1, z1) in zip(ring, ring[1:] + ring[:1]):
                        out.append(1 if skirt_on.distance(Point((x0 + x1) / 2, (z0 + z1) / 2)) < .02 else 0)
                    return out
                rec["se"] = [on(rec["o"])] + [on(r) for r in rec["h"]]
            if vh is not None:
                rec["vo"] = [round(vh(x, z), 2) for x, z in rec["o"]]
                rec["vh"] = [[round(vh(x, z), 2) for x, z in r] for r in rec["h"]]
            else:
                rec["t"] = top
            self.slabs.append(rec)
            if hard:
                self.hard.append((q, top))
                self._prep = None

    def grid_slab(self, g, vh, color, mat="std", cell=2.0, bot=-1.0, skirt_color=None):
        """Per-vertex-height ground cut into cells, so the surface follows vh inside the outline too
        (an outline-only triangulation stretches flat planes across level changes)."""
        g = g.buffer(0)
        if g.is_empty:
            return
        pg = prep(g)
        edge = g.boundary
        x0, z0, x1, z1 = g.bounds
        for i in range(math.floor(x0 / cell), math.ceil(x1 / cell)):
            for j in range(math.floor(z0 / cell), math.ceil(z1 / cell)):
                c = box(i * cell, j * cell, (i + 1) * cell, (j + 1) * cell)
                if not pg.intersects(c):
                    continue
                inside = pg.contains(c)
                q = c if inside else c.intersection(g)
                if q.area < .08 or (not inside and q.area < .25 * q.length * .12):
                    continue                                  # fragments and slivers at the outline
                self.slab(q, None, color, mat, bot=bot, hard=False, vh=vh, skirt=not inside, soft=False, skirt_color=skirt_color,
                          skirt_on=None if inside else edge)

    def prism(self, g, y0, y1, color, mat="std", shadow=True):
        for q in self.polys(g, .02):
            self.prisms.append({"o": self.ring(q.exterior.coords, 3), "h": [self.ring(r.coords, 3) for r in q.interiors],
                                "y0": round(y0, 3), "y1": round(y1, 3), "c": self.c(color), "m": mat, "s": int(shadow)})

    def plate(self, pts, tops, color, mat="std", t=None, bot=None):
        """Polygon (x, z) with a top height per vertex; bottom parallel (t) or flat (bot)."""
        self.plates.append([[[round(x, 3), round(z, 3)] for x, z in pts], [round(v, 3) for v in tops],
                            None if t is None else round(t, 3), None if bot is None else round(bot, 3), self.c(color), mat])

    def plate_poly(self, g, top_fn, color, mat="std", t=None, bot=None):
        for q in self.polys(g, .02):
            pts = list(q.exterior.coords)[:-1]
            self.plate(pts, [top_fn(x, z) for x, z in pts], color, mat, t, bot)

    def box(self, x0, y0, z0, x1, y1, z1, color, mat="std", ry=0.0, rx=0.0):
        self.boxes.append([round((x0 + x1) / 2, 3), round((y0 + y1) / 2, 3), round((z0 + z1) / 2, 3),
                           round(abs(x1 - x0), 3), round(abs(y1 - y0), 3), round(abs(z1 - z0), 3),
                           round(ry, 2), round(rx, 2), self.c(color), mat])

    def boxc(self, cx, cy, cz, sx, sy, sz, color, mat="std", ry=0.0, rx=0.0):
        self.boxes.append([round(cx, 3), round(cy, 3), round(cz, 3), round(sx, 3), round(sy, 3), round(sz, 3),
                           round(ry, 2), round(rx, 2), self.c(color), mat])

    def cyl(self, x, y, z, r0, r1, h, color, axis="y", seg=16, mat="std"):
        """Cylinder or cone; (x, y, z) is the base centre (y axis) or the centre (x / z axis); axis 's' = sphere."""
        self.cyls.append([round(x, 3), round(y, 3), round(z, 3), round(r0, 3), round(r1, 3), round(h, 3),
                          self.c(color), axis, seg, mat])

    def seg(self, p0, p1, r, color, mat="metal", n=8):
        self.segs.append([round(p0[0], 3), round(p0[1], 3), round(p0[2], 3), round(p1[0], 3), round(p1[1], 3),
                          round(p1[2], 3), round(r, 3), self.c(color), n, mat])

    def polyseg(self, pts, r, color, mat="metal", n=8):
        for a, b in zip(pts, pts[1:]):
            self.seg(a, b, r, color, mat, n)

    def ext(self, plane, pts, off, depth, color, mat="std", bevel=0.0, holes=None):
        e = [plane, [[round(a, 3), round(b, 3)] for a, b in pts], round(off, 3), round(depth, 3), self.c(color), mat, round(bevel, 3)]
        if holes:
            e.append([[[round(a, 3), round(b, 3)] for a, b in h] for h in holes])
        self.exts.append(e)

    def torus(self, x, y, z, R, r, arc, rz, ry, color, mat="gloss"):
        self.tori.append([round(x, 3), round(y, 3), round(z, 3), R, r, arc, rz, ry, self.c(color), mat])

    def egg(self, x, y, z, r, hs, face, color, lining, mat="gloss"):
        """Egg chair shell: sphere of radius r (centre x, y, z) stretched hs in height, open towards face (deg, atan2 z/x)."""
        self.eggs.append([round(x, 3), round(y, 3), round(z, 3), round(r, 3), round(hs, 3), round(face, 1),
                          self.c(color), self.c(lining), mat])

    def text(self, txt, x, y, z, size, depth, ry, color, mat="gloss", align="c"):
        self.texts.append([txt, round(x, 3), round(y, 3), round(z, 3), size, depth, ry, self.c(color), mat, align])

    def label(self, p, w, h, ry, kind, **kw):
        d = {"p": [round(v, 3) for v in p], "w": round(w, 3), "h": round(h, 3), "ry": ry, "k": kind}
        d.update(kw)
        self.labels.append(d)

    # ------------------------------------------------------------- heights
    @staticmethod
    def h_eval(spec, x, z):
        if callable(spec):
            return float(spec(x, z))
        if isinstance(spec, (int, float)):
            return float(spec)
        ox, oz, dx, dz = spec["ax"]
        t = (x - ox) * dx + (z - oz) * dz
        pts = spec["pts"]
        if t <= pts[0][0]:
            return pts[0][1]
        for (t0, h0), (t1, h1) in zip(pts, pts[1:]):
            if t <= t1:
                return h0 + (h1 - h0) * (t - t0) / (t1 - t0)
        return pts[-1][1]

    def level_in(self, x, z):
        """Height of the hard surface at (x, z), or None when no hard surface covers the point."""
        if self._prep is None:
            self._prep = [(prep(q.buffer(.01)), q, s) for q, s in self.hard]
        p = Point(x, z)
        hs = [self.h_eval(s, x, z) for pg, q, s in self._prep if pg.contains(p)]
        return max(hs) if hs else None

    def level_at(self, x, z, default=None):
        if self._prep is None:
            self._prep = [(prep(q.buffer(.01)), q, s) for q, s in self.hard]
        p = Point(x, z)
        hs = [self.h_eval(s, x, z) for pg, q, s in self._prep if pg.contains(p)]
        if hs:
            return max(hs)
        if default is not None:
            return default
        best, bd = 3.6, 1e9
        for pg, q, s in self._prep:
            d = q.distance(p)
            if d < bd:
                bd, best = d, self.h_eval(s, x, z)
        return best

    def idw_builder(self, step=2.0, skip=()):
        pts, hs = [], []
        for i, (q, s) in enumerate(self.hard):
            if i in skip:
                continue
            rings = [r for pg in getattr(q, "geoms", [q]) if pg.geom_type == "Polygon" for r in [pg.exterior] + list(pg.interiors)]
            for r in rings:
                L = r.length
                k = max(4, int(L / step))
                for i in range(k):
                    pt = r.interpolate(i / k, normalized=True)
                    pts.append((pt.x, pt.y))
                    hs.append(self.h_eval(s, pt.x, pt.y))
        P_ = np.array(pts)
        H_ = np.array(hs)

        def f(x, z, k=6):
            d = np.hypot(P_[:, 0] - x, P_[:, 1] - z)
            idx = np.argpartition(d, k)[:k]
            w = 1.0 / np.maximum(d[idx], .3) ** 2
            return float((H_[idx] * w).sum() / w.sum())
        return f

    def data(self):
        return {"pal": self.pal, "slabs": self.slabs, "prisms": self.prisms, "boxes": self.boxes, "cyls": self.cyls,
                "segs": self.segs, "exts": self.exts, "tori": self.tori, "texts": self.texts, "plates": self.plates, "eggs": self.eggs,
                "trees": self.trees, "shrubs": self.shrubs, "labels": self.labels, "rocks": self.rocks, "terrain": self.terrain, "lights": self.lights,
                "views": VIEWS, "sun": [80, 140, 120], "center": [100, 0, 70],
                "notes": {"terrain": "IMPORTANT: terrain (hills, sea floor, soil and sand surfaces) is a stand-in; the Ori engine's "
                                     "terrain system recreates it on import. Import structures, paving, stairs and props only.",
                          "planting": "Trees, plants and rocks are placeholders for the engine's own."}}


# camera presets: position, target, field of view
VIEWS = {
    "aerial": {"name": "Aerial from the south", "pos": [150, 105, 215], "tgt": [100, 4, 62], "fov": 46},
    "arcade": {"name": "Arcade front from the plaza", "pos": [63.5, 5.35, 59.5], "tgt": [47.0, 7.6, 51.6], "fov": 55},
    "gate": {"name": "Main stair, escalators and gate", "pos": [91.0, 5.4, 44.0], "tgt": [90.6, 9.6, 18.0], "fov": 58},
    "fashion": {"name": "Fashion & Goods from the plaza", "pos": [66.0, 5.4, 41.0], "tgt": [47.5, 8.4, 28.0], "fov": 58},
    "plaza": {"name": "Central plaza from the east", "pos": [118.0, 14.0, 28.0], "tgt": [86.0, 3.6, 66.0], "fov": 55},
    "cafe": {"name": "Seaside café from the promenade", "pos": [50.0, 6.0, 99.0], "tgt": [25.0, 6.2, 76.0], "fov": 56},
    "lifestyle": {"name": "Lifestyle & Souvenir from the promenade", "pos": [124.0, 5.4, 93.0], "tgt": [143.0, 6.0, 64.0], "fov": 58},
    "stage": {"name": "Stage and event lawn from the curved path", "pos": [163.0, 7.4, 62.0], "tgt": [180.0, 4.8, 36.0], "fov": 58},
    "beach": {"name": "Beach, promenade and pier", "pos": [70.0, 12.0, 160.0], "tgt": [110.0, 2.5, 105.0], "fov": 55},
    "arcade_in": {"name": "Arcade interior from the doors", "pos": [46.2, 5.9, 51.7], "tgt": [30.0, 6.4, 50.0], "fov": 72},
    "arcade_in2": {"name": "Arcade interior: LED wall and tower", "pos": [35.5, 6.4, 62.7], "tgt": [27.0, 6.4, 44.0], "fov": 70},
    "landmark": {"name": "Ori logo landmark from the main stair", "pos": [90.6, 7.4, 37.5], "tgt": [90.8, 6.6, 57.0], "fov": 52},
}


# ---------------------------------------------------------------- recording
def record_plan(b):
    """Run site_plan() with the prop helpers wrapped, collecting what it places."""
    rec = {k: [] for k in ("planter", "canopy", "palm", "parasol", "bench", "stair", "quad", "treads", "truck", "rock",
                           "railing", "lounger", "wall")}
    orig = {}

    def wrap(name, fn):
        orig[name] = getattr(b, name)
        setattr(b, name, fn)

    def planter_g(cv, g, seed, density=.8, rmin=.4, rmax=.8, wall=.3, radius=.35):
        rec["planter"].append((b.open_(g, radius) if radius else g, seed, density))
        return orig["planter_g"](cv, g, seed, density, rmin, rmax, wall, radius)

    def canopy(cv, u, v, r, seed=0, kind="tree", shadow=True, detail=True):
        if (u, v) != (0, 0):                 # (0, 0) are the legend's sample symbols
            rec["canopy"].append((u, v, r, kind, seed))
        return orig["canopy"](cv, u, v, r, seed, kind, shadow, detail)

    def palm_top(cv, u, v, r, seed=0, shadow=True):
        if (u, v) != (0, 0):
            rec["palm"].append((u, v, r, seed))
        return orig["palm_top"](cv, u, v, r, seed, shadow)

    def parasol(cv, u, v, r=1.3, cls="umb-y", chairs=0, ribs=8):
        rec["parasol"].append((u, v, r, cls, chairs))
        return orig["parasol"](cv, u, v, r, cls, chairs, ribs)

    def bench(cv, u, v, length=3.0, ang=0.0, depth=.7):
        rec["bench"].append((u, v, length, ang))
        return orig["bench"](cv, u, v, length, ang, depth)

    def stair_ns(cv, x0, y0, x1, y1, flights, landing=0.0, cheek=True, rails=(), label=None):
        rec["stair"].append((x0, y0, x1, y1, flights, landing, tuple(rails)))
        return orig["stair_ns"](cv, x0, y0, x1, y1, flights, landing, cheek, rails, label)

    def quad_stair(cv, q, risers, label=None, cheek=(.3, .6), bow=(0.0, 0.0)):
        rec["quad"].append((q, risers, bow))
        return orig["quad_stair"](cv, q, risers, label, cheek, bow)

    def quad_treads(cv, q, count, fill="z-paver"):
        rec["treads"].append((q, count))
        return orig["quad_treads"](cv, q, count, fill)

    def truck_r(cv, cx, cy, ang, cls_stripe, L=6.5, Wd=2.5):
        rec["truck"].append((cx, cy, ang, cls_stripe))
        return orig["truck_r"](cv, cx, cy, ang, cls_stripe, L, Wd)

    def rock(cv, u, v, r, seed=0, shadow=True, foam=False):
        rec["rock"].append((u, v, r, seed))
        return orig["rock"](cv, u, v, r, seed, shadow, foam)

    def railing(cv, pts, spacing=2.0):
        rec["railing"].append(pts)
        return orig["railing"](cv, pts, spacing)

    def lounger(cv, u, v, ang=90.0, cls="prop"):
        rec["lounger"].append((u, v, ang))
        return orig["lounger"](cv, u, v, ang, cls)

    def wall_line(cv, px_pts, t=.4):
        rec["wall"].append((px_pts, t))
        return orig["wall_line"](cv, px_pts, t)

    for name, fn in [("planter_g", planter_g), ("canopy", canopy), ("palm_top", palm_top), ("parasol", parasol),
                     ("bench", bench), ("stair_ns", stair_ns), ("quad_stair", quad_stair), ("quad_treads", quad_treads),
                     ("truck_r", truck_r), ("rock", rock), ("railing", railing), ("lounger", lounger), ("wall_line", wall_line)]:
        wrap(name, fn)
    try:
        b.site_plan()
    finally:
        for name, fn in orig.items():
            setattr(b, name, fn)
    for k in ("parasol", "bench", "rock", "lounger"):        # drop the legend's sample symbols at (0, 0)
        rec[k] = [e for e in rec[k] if (abs(e[0]) > .01 or abs(e[1]) > .01)]
    return rec


# ---------------------------------------------------------------- ground
def street_level(b):
    P = b.P
    prof = [(P(730, 0)[0], 8.4), (P(940, 0)[0], 6.6), (P(1100, 0)[0], 6.6), (P(1230, 0)[0], 6.0)]

    def f(x):
        if x <= prof[0][0]:
            return prof[0][1]
        for (a, ha), (c, hc) in zip(prof, prof[1:]):
            if x <= c:
                return ha + (hc - ha) * (x - a) / (c - a)
        return prof[-1][1]
    return f


def wall_line_z(b, rec):
    """Northernmost street retaining wall at each x (m): the street is north of it, the park south."""
    spans = []
    for px_pts, t in rec["wall"]:
        pts = b.PP(px_pts)
        for (xa, za), (xb, zb) in zip(pts, pts[1:]):
            if abs(zb - za) < .5 and abs(xb - xa) > .5:
                spans.append((min(xa, xb), max(xa, xb), (za + zb) / 2))

    def f(x):
        zs = [z for a, c, z in spans if a - .01 <= x <= c + .01]
        if zs:
            return min(zs)
        # stair openings and building ends: carry the nearest wall line across, so the strip
        # between the sidewalk and the wall stays at street level instead of sinking to the plaza
        if not spans:
            return None
        return min(spans, key=lambda s_: max(s_[0] - x, x - s_[1]))[2]
    return f


def stair_footprints(rec):
    parts = [box(x0, y0, x1, y1) for (x0, y0, x1, y1, *_r) in rec["stair"]]
    parts += [Polygon(q).buffer(0) for q, *_r in rec["quad"]] + [Polygon(q).buffer(0) for q, *_r in rec["treads"]]
    return unary_union(parts)


def ring_sign(R_out, R_in, uc, yc, gap_mid=-60.0, gap=44.0, n=56):
    """Flat ring logo with a notch, in face coordinates (u right, y up)."""
    a0, a1 = gap_mid + gap / 2, gap_mid + 360 - gap / 2
    outer = [(uc + R_out * math.cos(math.radians(a0 + (a1 - a0) * i / n)), yc + R_out * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
             for i in range(n + 1)]
    inner = [(uc + R_in * math.cos(math.radians(a1 - (a1 - a0) * i / n)), yc + R_in * math.sin(math.radians(a1 - (a1 - a0) * i / n)))
             for i in range(n + 1)]
    return outer + inner


BLDG_PX = ((142.5, 195, 347.5, 300), (142.5, 300, 347.5, 485), (142.5, 485, 282.5, 540),
           (842, 405, 980, 505), (895, 378, 980, 405), (842, 505, 980, 530), (140, 145, 273, 180))   # lifestyle: shop, annex, canopy band


def bldg_footprints(b):
    """Fashion, arcade, café, lifestyle and the kiosk row (metres)."""
    return unary_union([box(*b.P(x0, y0), *b.P(x1, y1)) for (x0, y0, x1, y1) in BLDG_PX])


def prom_step_quads(b):
    """The 3R steps in each opening between the promenade-edge planters: (head a, head b, foot b, foot a)."""
    out = []
    for (xa, xb) in b.PROM_OPENINGS:
        t0, t1 = b.P(xa, b.edge_y(xa)), b.P(xb, b.edge_y(xb))
        L = math.hypot(t1[0] - t0[0], t1[1] - t0[1])
        nx, nz = -(t1[1] - t0[1]) / L, (t1[0] - t0[0]) / L
        if nz < 0:
            nx, nz = -nx, -nz
        out.append((t0, t1, (t1[0] + nx * .9, t1[1] + nz * .9), (t0[0] + nx * .9, t0[1] + nz * .9)))
    return out


def footprints(b, rec):
    """Areas that carry their own structure, so no soil is laid over them."""
    P = b.P
    parts = [box(x0, y0, x1, y1) for (x0, y0, x1, y1, *_r) in rec["stair"]]
    parts += [Polygon(q).buffer(.05) for q in prom_step_quads(b)]                 # promenade steps
    parts.append(Polygon(b.pier_rect(b.PIER_RAMP_T - .3, .3, -4.0, 4.0)))        # pier ramp
    parts += [Polygon(q).buffer(0) for q, *_r in rec["quad"]] + [Polygon(q).buffer(0) for q, *_r in rec["treads"]]
    parts += [g for g, *_r in rec["planter"]]
    parts.append(bldg_footprints(b))
    return unary_union(parts).buffer(.02)


def build_ground(sc, b, rec):
    P, GB = b.P, b.GB
    hs = b.hardscape()
    X0, Y0, X1, Y1 = b.X0, b.Y0, b.X1, b.Y1
    frame = box(X0, Y0, X1, Y1)

    def ax_y(pts_px):  # profile along the plan's south axis (z), given as (y_px, level)
        return {"ax": [0, 0, 0, 1], "pts": [[round(P(0, y)[1], 3), h] for y, h in pts_px]}

    def ax_x(pts_px):
        return {"ax": [0, 0, 1, 0], "pts": [[round(P(x, 0)[0], 3), h] for x, h in pts_px]}

    street_prof = ax_x([(730, 8.4), (940, 6.6), (1100, 6.6), (1230, 6.0)])
    sc.slab(GB(36, -12, 1302, 95), street_prof, "town", hard=False)
    sc.slab(GB(36, 95, 1302, 135), {"ax": street_prof["ax"], "pts": [[t, h - .15] for t, h in street_prof["pts"]]}, "road")
    lane_box = GB(88, 196, 142, 640)
    lane = hs["street"].intersection(lane_box)
    sfp = stair_footprints(rec)                     # stairs carry their own treads: no paving over them
    n_st = len(sc.hard)
    sc.slab(hs["street"].difference(lane_box).difference(sfp), street_prof, "street")
    street_idx = set(range(n_st, len(sc.hard)))
    sc.slab(lane, ax_y([(135, 8.4), (632, 3.15)]), "street")    # the lane counts as park ground, so the bank beside it follows it
    east = hs["east"].difference(hs["tipzone"])     # the path end is part of the smoothed plaza at the lawn tip
    plaza = hs["plaza"].difference(east.buffer(.05)).difference(sfp)
    # the east end of the plaza falls 0.45 m toward the promenade; the fall fades in over 14 m so there is no seam
    cut, blend = P(1040, 0)[0], 14.0
    za, zb = P(0, 470)[1], P(0, 560)[1]

    def plaza_h(x, z):
        s_ = min(max((z - za) / (zb - za), 0.0), 1.0)
        w_ = min(max((x - (cut - blend)) / blend, 0.0), 1.0)
        return 3.6 - .45 * s_ * w_
    flat = box(-50, -50, cut - blend, 300)
    sc.slab(plaza.intersection(flat), 3.6, "paver")
    east_pl = plaza.difference(flat)
    sc.grid_slab(east_pl, plaza_h, "paver", "std", cell=2.0)
    sc.hard.append((east_pl, plaza_h))
    sc._prep = None
    sc.slab(east, ax_y([(145, 6.0), (380, 3.6)]), "paver")         # ramps down to +3.60 where it meets the lawn tip
    sc.slab(hs["top"].difference(sfp), 3.6, "paver")
    sc.slab(hs["lawn"], 3.6, "lawn", skirt_color="conc")                # event lawn level with the plaza (no longer raked)
    sc.slab(hs["prom"], 3.15, "timber")
    # wooden ramp from the coastal walk (+3.15) down to the pier deck (+2.40), boards and rails continuing the pier
    t0r = b.PIER_RAMP_T
    pa = math.radians(b.PIER_ANG)

    def ramp_h(x, z):
        t = (x - b.PIER_O[0]) * math.sin(pa) + (z - b.PIER_O[1]) * math.cos(pa)
        return 3.15 + (2.4 - 3.15) * min(max((t - t0r) / -t0r, 0.0), 1.0)
    ramp = Polygon(b.pier_rect(t0r, .12, -3.75, 3.75)).difference(hs["plaza"].buffer(.02)).buffer(0)   # laps onto the deck
    sc.plate_poly(ramp, ramp_h, "timber", "deck", t=.25)
    sc.hard.append((ramp, ramp_h))
    sc._prep = None
    # sand under the ramp where the old landing stood (no water showing through)
    under = Polygon(b.pier_rect(t0r - .5, .5, -5.0, 5.0)).difference(hs["plaza"]).difference(b.sand_poly()).buffer(0)
    sc.slab(under, .7, "sand", "ground", bot=-3, hard=False)
    b.RAMP_H = ramp_h
    sc.slab(hs["terr"], 3.66, "timber")
    sc.slab(GB(93, 153, 140, 207), 8.42, "timber")
    dy = b.TRUCK_DY
    sc.slab(b.open_(GB(733, 219 + dy, 770, 302 + dy), 1.2), 3.67, "timber")
    sc.slab(GB(770, 217 + dy, 942, 302 + dy), 3.62, "brick", "ground")
    sc.hard.append((hs["deck"], 4.2))
    # beach: +0.95 at the sea wall sloping into the water, then a shallow shelf
    sh = b.cr_sample(b.PP(b.SHORE_PX), per=8)
    sand = b.sand_poly()
    wall_l = LineString(b.PP(b.SEAWALL_PX))
    shore_l = LineString(sh)

    def sand_h(x, z):
        dw, ds = wall_l.distance(Point(x, z)), shore_l.distance(Point(x, z))
        return .95 * ds / (ds + dw + 1e-6) - .2
    sc.grid_slab(sand, sand_h, "sand", "ground", cell=3.0, bot=-3)
    sc.hard.append((sand, sand_h))
    shelf = Polygon(sh + b.offset_pts(sh, -18)[::-1]).buffer(0).difference(sand)

    def shelf_h(x, z):
        return -.2 - 1.5 * min(1.0, shore_l.distance(Point(x, z)) / 18)
    sc.grid_slab(shelf, shelf_h, "sand-wet", "ground", cell=3.0, bot=-3)
    # west rock outcrop: a natural sand-and-rock spit that falls from the beach level into the sea (no flat platform)
    wrock = Polygon(b.PP(b.WEST_ROCK_PX)).buffer(0).difference(sand)
    land_edge = sand.boundary

    def wrock_h(x, z):
        p = Point(x, z)
        d = land_edge.distance(p)
        base = sand_h(*nearest_points(sand, p)[0].coords[0])
        t = min(d / 22.0, 1.0)
        return base + (-.9 - base) * (t * t * (3 - 2 * t)) + .25 * math.sin(x / 3.1) * math.cos(z / 2.7) * t * (1 - t) * 4
    sc.grid_slab(wrock, wrock_h, "sand", "ground", cell=3.0, bot=-3)
    sc.hard.append((wrock, wrock_h))                  # rocks sit on it
    sc._prep = None
    idw_all = sc.idw_builder()
    idw_low = sc.idw_builder(skip=street_idx)
    wz = wall_line_z(b, rec)
    st = street_level(b)

    def idw_raw(x, z):
        """Ground level for soil: street level north of the retaining walls, park level south of them."""
        w = wz(x)
        if w is None:
            return idw_all(x, z)
        return st(x) if z < w else idw_low(x, z)
    # soil meets every path flush: within 2.5 m of paving on its own side of the street walls it blends to that
    # paving's level (a level jump of 2.5 m or more is a wall, and is left to the wall)
    from shapely.strtree import STRtree
    hard_n = [(q, sp) for i, (q, sp) in enumerate(sc.hard) if i in street_idx]
    hard_s = [(q, sp) for i, (q, sp) in enumerate(sc.hard) if i not in street_idx]
    trees_ = [STRtree([q for q, _ in hl]) if hl else None for hl in (hard_n, hard_s)]
    near_cache = {}

    def idw(x, z):
        base = idw_raw(x, z)
        key = (round(x, 2), round(z, 2))
        if key in near_cache:
            return near_cache[key]
        w = wz(x)
        side = 0 if (w is not None and z < w) else 1
        tr, hl = trees_[side], (hard_n, hard_s)[side]
        out = base
        if tr is not None:
            p = Point(x, z)
            cand = []
            for j in tr.query(p.buffer(2.5)):
                q, sp = hl[int(j)]
                d = q.distance(p)
                if d <= 2.5:
                    qp = p if d == 0 else nearest_points(q, p)[0]
                    cand.append((d, sc.h_eval(sp, qp.x, qp.y)))
            if cand:
                dmin = min(c[0] for c in cand)
                d, lv = max((c for c in cand if c[0] <= dmin + .3), key=lambda c: c[1])   # touching surfaces: the higher one
                if abs(lv - base) < 2.5:
                    t = min(d / 2.5, 1.0)
                    t = t * t * (3 - 2 * t)
                    out = lv + (base - lv) * t
        near_cache[key] = out
        return out
    coast = b.cr_sample(b.PP(b.COAST_PX), per=6)
    land = Polygon([(X0, Y0), (X1, Y0)] + coast + b.PP([(1150, 700), (1100, 712), (1087, 700), (1087, 647), (1043, 653)]) +
                   b.PP(b.SEAWALL_PX) + b.PP([(55, 700), (36, 700)])).buffer(0)
    covered = unary_union([q for q, s in sc.hard])
    rest = land.difference(covered).difference(sand).intersection(frame)
    beds = hs["beds"].intersection(frame)
    soil = unary_union([beds, rest]).buffer(0).difference(footprints(b, rec))
    beach_edge = unary_union([sand.buffer(1.0), Polygon(b.PP(b.EAST_ROCK_PX)).buffer(1.0)])
    gap = soil.buffer(.6).intersection(beach_edge).difference(sand.buffer(-.4)).intersection(land)   # strip between beach and planting
    soil = soil.difference(beach_edge)                                          # no planting on the beach
    if not gap.is_empty:                                                        # fill it with sand at the beach level
        sc.grid_slab(gap, lambda x, z: max(sand_h(*nearest_points(sand, Point(x, z))[0].coords[0]), .4) - .02, "sand", "ground",
                     cell=2.0, bot=-3)
    thick = soil.buffer(-.3, join_style="mitre").buffer(.3, join_style="mitre").intersection(soil)
    slivers = soil.difference(thick.buffer(.01))      # strips under 0.6 m wide (beside planters, steps, walls)
    soil = thick
    if not slivers.is_empty:                          # paved flush with the ground around them: no hole, no kerb
        def low_s(x, z):                              # lowest surface around, so a strip never rides up onto a step or deck
            vs = [idw(x, z)] + [v for v in (sc.level_in(x + dx, z + dz) for dx, dz in ((.35, 0), (-.35, 0), (0, .35), (0, -.35)))
                                if v is not None]
            return min(vs) - .01
        sc.grid_slab(slivers.buffer(.02).intersection(land), low_s, "paver", "std", cell=2.0, bot=-1.0)
    # split at the street retaining-wall line so no cell spans the drop between street and park
    xs = np.arange(X0 - 1, X1 + 1.01, .25)
    north = Polygon([(X0 - 1, Y0 - 5)] + [(x, wz(x)) for x in xs] + [(X1 + 1, Y0 - 5)]).buffer(0)
    for part in (soil.intersection(north), soil.difference(north)):
        sc.grid_slab(part, lambda x, z: idw(x, z) + .1, "bed", "soft", cell=2.0, skirt_color="conc")
    # stone kerbs where planting meets paving
    paved = unary_union([hs["paved"], hs["prom"], hs["terr"]])
    edge = soil.boundary.intersection(paved.buffer(.05))
    kerb = edge.buffer(.09, cap_style="flat", join_style="mitre").intersection(soil.buffer(.12))
    sc.plate_poly(kerb, lambda x, z: idw(x, z) + .16, "conc", "stone", bot=0.0)
    # seabed under the whole sea between the headlands (the water plane runs well past the drawing frame)
    sea_floor = box(-1000, Y0, 1200, 1300).difference(land.buffer(-.5)).difference(sand)    # out to the fogged horizon
    sc.slab(sea_floor, -2.4, "seabed", "ground", bot=-3, hard=False)
    sc.label([100, -.05, 600], 2200, 1390, 0, "water")       # sea out to the horizon (fog hides the far edge)
    return hs, idw


def build_walls(sc, b, rec):
    """Retaining walls at the street edge (with coping), the sea wall, and mural walls with LED tickers."""
    st = street_level(b)
    for px_pts, t in rec["wall"]:
        pts = b.PP(px_pts)
        g = LineString(pts).buffer(t / 2, cap_style="flat", join_style="mitre")
        vertical = all(abs(p[0] - pts[0][0]) < .01 for p in pts)
        top = (lambda x, z: 7.0) if vertical else (lambda x, z: st(x))
        sc.plate_poly(g, top, "conc", "conc", bot=2.9)
        cap = LineString(pts).buffer(t / 2 + .06, cap_style="flat", join_style="mitre")
        sc.plate_poly(cap, lambda x, z, top=top: top(x, z) + .1, "cream", "stone", t=.1)
    # sea wall: three runs between the stair openings, stone face, coping
    sw = b.SEAWALL_PX
    sfp = stair_footprints(rec).buffer(.02)
    for run in (sw[0:4], sw[4:7], sw[7:9]):
        line = LineString(b.PP(run))
        sc.prism(line.buffer(.35, cap_style="flat", join_style="mitre").difference(sfp), -1.6, 3.2, "conc-2", "stone")
        sc.prism(line.buffer(.42, cap_style="flat", join_style="mitre").difference(sfp), 3.2, 3.3, "cream", "stone")
    # mural walls facing the plaza under the forecourt, LED tickers on top
    zf = (186 - 75) / 6 + .2 + .03
    for i, (a, c) in enumerate(((68.33, 84.17), (97.0, 111.17))):
        sc.label([(a + c) / 2, 5.95, zf], c - a - .6, 3.3, 0, "mural", seed=i)
        sc.box(a, 7.62, zf - .03, c, 8.32, zf + .08, "dark", "metal")
        sc.label([(a + c) / 2, 7.97, zf + .09], c - a - .1, .6, 0, "led",
                 txt="ようこそ うみ シーサイドパークへ · WELCOME TO UMI SEASIDE PARK · ゲーム · カフェ · ショップ")


# ---------------------------------------------------------------- props
def build_props(sc, b, rec, idw):
    rnd = random.Random(7)
    lv = sc.level_at

    wz_, st_ = wall_line_z(b, rec), street_level(b)

    def base_at(x, z):
        v = sc.level_in(x, z)
        w = wz_(x)
        if v is not None and w is not None and z < w - .05 and v < st_(x) - 1.0:
            v = None                                  # park paving that runs under the street wall: use street level
        return idw(x, z) if v is None else v
    bl = bldg_footprints(b)
    walls = unary_union([LineString(b.PP(px)).buffer(t / 2, cap_style="flat", join_style="mitre") for px, t in rec["wall"]])
    keep_out = unary_union([stair_footprints(rec), bl, walls]).buffer(.06)
    planter_gnd = []                                  # (prepared outline, ground sampler) per planter
    for g, seed, dens in rec["planter"]:
        if bl.contains(g.centroid):
            continue                                  # roof gardens: the building builds its own
        g = g.difference(keep_out)                    # copings stop short of stair cheeks, walls and facades
        for q in getattr(g, "geoms", [g]):
            if q.area < .5:
                continue
            inner, gq = K.planter_ground(sc, q, base_at)
            planter_gnd.append((prep(q.buffer(.05)), gq))
            inner = inner.difference(Point(*b.P(*b.STATUE_PX)).buffer(b.STATUE_R + .4))
            scatter(sc, inner, None, rnd, dens * .5, .35, .7, idw=lambda x, z, gq=gq: gq(x, z) + .38)
    hs = b.hardscape()
    scatter(sc, hs["beds"], None, rnd, .16, .45, 1.0, idw=idw)
    # trees sit on their planting: planter soil (+0.48), bed soil, lawn or sand
    def tree_base(x, z):
        p = Point(x, z)
        for pg, gq in planter_gnd:
            if pg.contains(p):
                return gq(x, z) + .48                 # on the planter's soil, read the same way the planter is built
        return base_at(x, z) + .1
    st = street_level(b)
    gate = unary_union([box(x - .4, b.GATE_Y - .4, x + .4, b.GATE_Y + .4) for x in b.GATE_X])
    obst = [(bl, 99.0), (gate, 99.0), (box(-60, -60, 300, -.83), 99.0)] + \
           [(LineString(b.PP(px)).buffer(t / 2 + .1), st(b.PP(px)[0][0]) + .2) for px, t in rec["wall"]]

    def fit(u, v, r, crown_y):
        """Shrink a crown that would push through a wall or a building above its lowest leaves."""
        p = Point(u, v)
        for g, top in obst:
            if top > crown_y:
                dd = g.distance(p)
                if dd < r + .2:
                    r = max(1.4, dd - .2)
        return r
    for (u, v, r, kind, seed) in rec["canopy"]:
        if kind not in ("tree", "sak"):
            continue
        y = tree_base(u, v)
        r = fit(u, v, r, y + (3.2 + r * 1.15) * .45)
        sc.trees.append([round(u, 2), round(y, 2), round(v, 2), round(r, 2), round(3.2 + r * 1.15, 2),
                         "s" if kind == "sak" else "t", seed % 97])
    for (u, v, r, seed) in rec["palm"]:
        y = tree_base(u, v)
        h = 5.5 + r * .6
        r = fit(u, v, r, y + h - r * .55)
        sc.trees.append([round(u, 2), round(y, 2), round(v, 2), round(r, 2), round(h, 2), "p", seed % 97])
    colors = {"umb-y": "yel", "umb-c": "cyan", "umb-p": "pink", "prop": "white"}
    for i, (u, v, r, cls, chairs) in enumerate(rec["parasol"]):
        if bl.contains(Point(u, v)):
            continue                                  # roof-terrace sets are placed by the building
        y = lv(u, v)
        if r < .8:
            sc.cyl(u, y + .72, v, .45, .45, .04, "white", seg=18, mat="paint")
            sc.seg((u, y, v), (u, y + .72, v), .04, "dark", "metal", 8)
            for k in range(3):
                a = k * 2.1 + .5
                K.chair(sc, u + math.cos(a) * .75, y, v + math.sin(a) * .75, math.degrees(a) + 180, "white", "paint")
            continue
        K.parasol_set(sc, u, y, v, min(r, 1.5), colors.get(cls, "white"), chairs, wood=(cls == "prop"), seed=i)
    for (u, v, L, ang) in rec["bench"]:
        K.bench_hq(sc, u, lv(u, v), v, L, ang)
    for (u, v, ang) in rec["lounger"]:
        K.lounger_hq(sc, u, lv(u, v), v, ang)
    for (u, v, r, seed) in rec["rock"]:
        y = sc.level_in(u, v)
        if y is None:
            y = -.6 if v > 105 else .6
        sc.rocks.append([round(u, 2), round(y + r * .25, 2), round(v, 2), round(r, 2), seed % 89])
    for (x0, y0, x1, y1, flights, landing, rails) in rec["stair"]:
        if abs(x0 - b.P(315, 0)[0]) < .5:
            continue                                  # fashion stair core is inside the building
        zt = lv((x0 + x1) / 2, y0 - .8)
        zb = lv((x0 + x1) / 2, y1 + .8)
        K.stair_ns_hq(sc, x0, y0, x1, y1, flights, landing, rails, zt, zb)
    for (q, risers, bow) in rec["quad"]:
        K.quad_steps_hq(sc, q, risers - 1, 4.8, 3.6, bow)
    for (q, count) in rec["treads"]:
        a, b_, c, d = q
        hx, hz = (a[0] + b_[0]) / 2, (a[1] + b_[1]) / 2
        fx, fz = (c[0] + d[0]) / 2, (c[1] + d[1]) / 2
        L = math.hypot(fx - hx, fz - hz) or 1
        ux, uz = (fx - hx) / L, (fz - hz) / L
        zt = lv(hx - ux * .6, hz - uz * .6)
        zb = lv(fx + ux * .6, fz + uz * .6)
        if zt - zb < .05:
            zt, zb = 3.15, 2.4
        K.quad_steps_hq(sc, q, count, zt, zb)
    # three steps (3R x 0.15) down from the plaza to the promenade in every opening between the edge planters
    spans = []
    for (xa, xb) in b.PROM_OPENINGS:                  # split where the café terrace (+3.66) meets the plaza (+3.60)
        spans += [(xa, 347), (347, xb)] if xa < 347 < xb else [(xa, xb)]
    for (xa, xb) in spans:
        t0, t1 = b.P(xa, b.edge_y(xa)), b.P(xb, b.edge_y(xb))
        L = math.hypot(t1[0] - t0[0], t1[1] - t0[1])
        nx, nz = -(t1[1] - t0[1]) / L, (t1[0] - t0[0]) / L
        if nz < 0:
            nx, nz = -nx, -nz
        f0, f1 = (t0[0] + nx * .9, t0[1] + nz * .9), (t1[0] + nx * .9, t1[1] + nz * .9)
        mx, mz = (t0[0] + t1[0]) / 2 - nx * .5, (t0[1] + t1[1]) / 2 - nz * .5
        K.quad_steps_hq(sc, (t0, t1, f1, f0), 2, sc.level_in(mx, mz) or 3.6, 3.15, rails=False)
    sw = [tuple(p) for p in b.PP(b.SEAWALL_PX)]
    pier0 = b.pier_pt(.3, -3.5)
    for pts in rec["railing"]:
        if math.dist(pts[0], pier0) < .5:
            continue                                  # the pier builds its own timber-capped rail on the deck edge
        if min(math.dist(pts[0], s) for s in sw) < 1.5:
            K.rail_line(sc, [(x, 3.3, z) for x, z in pts], h=1.05, post=1.8, cap="timber")
            continue
        K.rail_line(sc, [(x, max(lv(x, z - .6), lv(x, z + .6)) + .1, z) for (x, z) in pts], h=1.05, post=1.6)
    stripe = {"stripe": "pink", "stripec": "cyan", "stripey": "yel"}
    for (cx, cy, ang, st) in rec["truck"]:
        K.truck_hq(sc, cx, cy, ang, 3.66, stripe.get(st, "pink"))
    # lamp posts: plaza ones carry two banners each, in rotating designs
    designs = K.BANNER_DESIGNS
    for (x, z, grp, i) in b.LAMPS:               # spots placed by build.place_lamps (clear of planting, crowns, furniture)
        if grp == "plaza":
            K.lamp(sc, x, lv(x, z), z, 5.2, 0, (designs[(2 * i) % 8], designs[(2 * i + 1) % 8]))
        else:
            K.lamp(sc, x, lv(x, z), z, 4.6, 0, (designs[(i + 4) % 8], designs[(i + 1) % 8]) if i % 2 == 0 else None)


def scatter(sc, g, y, rnd, density, rmin, rmax, idw=None):
    if g.is_empty:
        return
    x0, z0, x1, z1 = g.bounds
    n_ = int(g.area * density)
    tries = 0
    pg = prep(g)
    while n_ > 0 and tries < n_ * 6:
        tries += 1
        x, z = rnd.uniform(x0, x1), rnd.uniform(z0, z1)
        if pg.contains(Point(x, z)):
            r = rnd.uniform(rmin, rmax)
            yy = y if y is not None else idw(x, z) + .1
            sc.shrubs.append([round(x, 2), round(yy, 2), round(z, 2), round(r, 2)])
            n_ -= 1


# ---------------------------------------------------------------- buildings
def rounded_top(u0, u1, y0, y1, r, n=6):
    pts = [(u0, y0), (u1, y0)]
    for i in range(n + 1):
        a = i / n * math.pi / 2
        pts.append((u1 - r + r * math.cos(a), y1 - r + r * math.sin(a)))
    for i in range(n + 1):
        a = math.pi / 2 + i / n * math.pi / 2
        pts.append((u0 + r + r * math.cos(a), y1 - r + r * math.sin(a)))
    return pts


def rounded_rect(u0, u1, y0, y1, r, n=5):
    pts = []
    for (cu, cy, a0) in ((u1 - r, y0 + r, -90), (u1 - r, y1 - r, 0), (u0 + r, y1 - r, 90), (u0 + r, y0 + r, 180)):
        for i in range(n + 1):
            a = math.radians(a0 + i * 90 / n)
            pts.append((cu + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def bubble_pts(u0, u1, y0, y1, r=.28):
    w = u1 - u0
    body = rounded_rect(u0, u1, y0, y1, r)
    tail = [(u0 + w * .38, y0 + .01), (u0 + w * .14, y0 - .42), (u0 + w * .2, y0 + .01)]
    return list(Polygon(body).union(Polygon(tail)).buffer(0).exterior.coords)[:-1]


def build_arcade(sc, b):
    """Red arcade after the reference facade: controller sign, posters, glass doors, portholes, roof terrace."""
    c = elev.CTR
    W, xe, zn, zs = 13.75, 47.92, 37.92, 65.0
    d0, d1 = elev.ARC_IN["door"]
    sc.box(W, 3.0, zn, xe, 4.05, zs, "conc", "conc")                       # floor slab
    sc.box(W, 4.05, zn, xe, 9.6, zn + .3, "arc", "clad")                   # shell walls (hollow: the interior is modelled)
    sc.box(W, 4.05, zs - .3, xe, 9.6, zs, "arc", "clad")
    sc.box(W, 4.05, zn + .3, W + .3, 9.6, zs - .3, "arc", "clad")
    sc.box(xe - .3, 4.05, zn + .3, xe, 9.6, d0, "arc", "clad")
    sc.box(xe - .3, 4.05, d1, xe, 9.6, zs - .3, "arc", "clad")
    sc.box(xe - .3, 7.2, d0, xe, 9.6, d1, "arc", "clad")
    sc.box(W + .3, 9.3, zn + .3, xe - .3, 9.6, zs - .3, "in-ceil", "std")
    K.flat_roof(sc, W, zn, xe, zs, 9.6, 10.2, "arc", "clad", "dark", "metal", deck="timber")
    E = K.Face(sc, "E", W, zn, xe, zs)
    S = K.Face(sc, "S", W, zn, xe, zs)
    Wf = K.Face(sc, "W", W, zn, xe, zs)
    for f in (E, S, Wf):
        f.box(0, f.L, 9.72, 9.92, 0, .04, "yel", "paint")
    E.box(0, 27.08, 3.0, 4.05, 0, .05, "conc", "conc")
    for (a, b_) in ((0, .55), (26.53, 27.08)):
        E.box(a, b_, 3.6, 9.6, 0, .08, "arc-2", "clad")
    # controller sign
    E.ext(rounded_top(c - 7.1, c + 7.1, 7.3, 10.65, .8), 0, .6, "yel", "paint", .04)
    E.ext(rounded_top(c - 3.75, c + 3.75, 7.65, 10.5, .5), .6, .72, "yel-3", "paint", .02)
    E.text("ARCADE", c - .75, 9.2, .92, .14, "white", d=.72)
    E.box(c - 2.6, c + 1.4, 8.2, 8.78, .72, .76, "dark", "gloss")
    E.label(c - .6, 8.49, 3.9, .54, "pill", d=.765, txt="ゲームセンター", fg="#FFFFFF", bg="#2E333B")
    E.label(c + 2.85, 9.38, 1.2, .95, "mascot", d=.73)
    for (u0, u1) in ((c - 7.0, c - 3.75), (c + 3.75, c + 7.0)):
        E.ext(rounded_top(u0, u1, 7.42, 11.0, .75), 0, .78, "cream", "paint", .05)
    E.box(c - 6.55, c - 5.85, 10.38, 10.56, .78, .83, "steel", "metal")
    E.box(c + 4.2, c + 4.95, 10.42, 10.6, .78, .83, "steel", "metal")
    du, dz, a_, t_ = c - 5.35, 9.12, .88, .3
    cross = [(du - t_, dz - a_), (du + t_, dz - a_), (du + t_, dz - t_), (du + a_, dz - t_), (du + a_, dz + t_), (du + t_, dz + t_),
             (du + t_, dz + a_), (du - t_, dz + a_), (du - t_, dz + t_), (du - a_, dz + t_), (du - a_, dz - t_), (du - t_, dz - t_)]
    E.ext(cross, .78, .98, "dark", "gloss", .03)
    E.disc(du, dz, .14, .98, 1.0, "steel", "metal")
    for (bu, bz, col) in ((c + 4.75, 9.95, "blue"), (c + 6.0, 9.3, "red"), (c + 4.8, 8.55, "green")):
        E.disc(bu, bz, .48, .78, .84, "dark", "metal", 28)
        E.disc(bu, bz, .45, .84, 1.02, col, "gloss", 28, r_out=.36)
    # entrance: lit interior, sliding glass doors, pillars with LED strips, lintel
    E.door_slide(c, 5.0, 4.05, 3.15)                          # automatic sliding doors: open on approach in the engine
    for (a, b_) in ((c - 3.05, c - 2.5), (c + 2.5, c + 3.05)):
        E.box(a, b_, 4.05, 7.65, 0, .3, "yel", "paint")
        E.box((a + b_) / 2 - .04, (a + b_) / 2 + .04, 4.35, 7.2, .3, .33, "white", "led")
    E.box(c - 2.5, c + 2.5, 7.2, 7.65, 0, .3, "yel", "paint")
    E.box(c - 2.2, c + 2.2, 7.39, 7.45, .3, .33, "white", "led")
    for (a, b_) in ((c - 3.75, c - 3.05), (c + 3.05, c + 3.75)):
        E.box(a, b_, 4.05, 7.42, 0, .22, "yel-2", "paint")
    E.box(c - 6.75, c - 4.0, 4.15, 7.42, 0, .22, "cream", "paint")
    E.label(c - 5.37, 5.78, 2.25, 2.75, "poster", d=.225)
    E.box(c + 4.0, c + 6.75, 4.15, 7.42, 0, .22, "cream", "paint")
    E.label(c + 5.37, 5.78, 2.5, 2.9, "panel", d=.225)
    # entrance steps across the controller frame (3R)
    for k in range(3):
        d1 = 1.2 - k * .4
        E.box(c - elev.ARC_STEP, c + elev.ARC_STEP, 3.0, 3.75 + k * .15, 0, d1, "conc-2", "conc")
        E.box(c - elev.ARC_STEP, c + elev.ARC_STEP, 3.735 + k * .15, 3.765 + k * .15, d1 - .05, d1, "dark", "rubber")
    # outer bays: portholes and framed windows
    for u in (2.1, 4.4, 22.3, 24.6):
        E.disc(u, 8.55, .5, 0, .02, "dark", "rubber", 24)
        E.torus(u, 8.55, .57, .09, .06, "cream", mat="paint")
        E.disc(u, 8.55, .5, .02, .05, "glass", "glass", 24)
    for u in (2.1, 4.4, 22.1):
        E.window(u - .75, u + .75, 5.0, 6.6, frame="arc-2", fmat="clad", inner="glow")
    x = 16.6
    while x < 45.6:
        S.disc(x - W, 8.55, .52, 0, .02, "dark", "rubber", 24)
        S.torus(x - W, 8.55, .6, .09, .06, "cream", mat="paint")
        S.disc(x - W, 8.55, .52, .02, .05, "glass", "glass", 24)
        x += 3.0
    # floodlights on the parapet aimed at the sign
    for u in (7.0, 10.6, 16.0, 19.6):
        E.seg((u, 10.27, -.1), (u, 10.75, .35), .03, "dark")
        E.box(u - .3, u + .3, 10.65, 10.95, .25, .55, "dark", "metal")
        E.box(u - .25, u + .25, 10.62, 10.66, .3, .5, "white", "led")
    # roof terrace: glass rail on the parapet, parasols and tables
    ring = [(W + .15, zn + .15), (xe - .15, zn + .15), (xe - .15, zs - .15), (W + .15, zs - .15), (W + .15, zn + .15)]
    K.rail_line(sc, [(x_, 10.28, z_) for x_, z_ in ring], h=1.05, post=1.5, style="glass")
    for i, (px, pz) in enumerate(((22.0, 42.5), (30.0, 46.0), (38.0, 42.5), (24.0, 58.0), (40.0, 59.0))):
        K.parasol_set(sc, px, 9.66, pz, 1.4, "white", 3, wood=True, seed=i)
    # back: service doors, downpipes, louvres, condensers
    for u in (.4, 9.2, 18.2, 26.7):
        Wf.downpipe(u, elev.lane_z(37.92 + u), 9.6)
    Wf.door_solid(25.08, 1.9, elev.lane_z(62.5), 2.3)
    Wf.box(23.9, 26.3, elev.lane_z(62.5) + 2.35, elev.lane_z(62.5) + 2.55, 0, .5, "dark", "metal")
    Wf.door_solid(4.08, 1.1, elev.lane_z(42.0), 2.15)
    for u in (4.5, 13.5, 22.0):
        Wf.box(u - .9, u + .9, 8.3, 9.1, 0, .08, "steel", "groove")
    for (px, pz) in ((15.5, 41.0), (15.5, 44.0), (15.5, 50.0)):
        K.ac_unit(sc, px, 9.66, pz, 90)
    # prize & vending strip south of the arcade
    sc.box(W, 3.0, zs, xe, 6.9, 68.33, "arc", "clad")
    K.flat_roof(sc, W, zs, xe, 68.33, 6.9, 7.2, "arc", "clad", "dark", "metal")
    SE = K.Face(sc, "E", W, zs, xe, 68.33)
    SE.window(.3, 3.05, 3.6, 6.1, cols=2, frame="dark", inner="glow", sill=None)
    SE.box(.23, 3.1, 6.25, 6.8, 0, .12, "pink", "gloss")
    SE.text("PRIZE", 1.665, 6.33, .38, .06, "white", d=.12)
    SS = K.Face(sc, "S", W, zs, xe, 68.33)
    for (a, b_) in ((23.85, 27.45), (27.95, 31.55)):
        SS.shopfront(a, b_, 3.6, 6.2, 2, inner="glow")
    SS.window(31.85, 33.85, 4.2, 6.2, frame="dark", inner="glass")


def build_fashion(sc, b):
    x0, x1, z0, z1 = 13.75, 47.92, 20.0, 37.5
    sc.box(x0, 3.0, z0, x1, 12.6, z1, "plaster", "plaster")
    sc.box(x0, 3.0, z1, x1, 9.6, 37.92, "plaster", "plaster")
    K.kawara_eave(sc, x0, z0, x1, z1, 12.6, "NESW", "kawara")
    K.flat_roof(sc, x0, z0, x1, z1, 12.6, 12.95, "plaster", "plaster", sides="")
    sc.box(36.0, 12.6, 22.0, 40.0, 15.0, 26.0, "plaster", "plaster")
    K.kawara_eave(sc, 36.0, 22.0, 40.0, 26.0, 15.0, "NESW", "kawara", proj=.45, inset=.3, rise=.35)
    sc.box(36.3, 14.95, 22.3, 39.7, 15.3, 25.7, "conc-2", "conc")
    K.Face(sc, "S", 36.0, 22.0, 40.0, 26.0).door_solid(2.0, 1.0, 12.63, 2.1)
    for (px, pz) in ((20.0, 26.0), (23.0, 26.0), (26.0, 26.0)):
        K.ac_unit(sc, px, 12.65, pz, 0)
    E = K.Face(sc, "E", x0, z0, x1, z1)
    N = K.Face(sc, "N", x0, z0, x1, z1)
    Wf = K.Face(sc, "W", x0, z0, x1, z1)
    E.box(0, 17.5, 3.0, 3.6, 0, .04, "conc-2", "stone")
    E.box(0, 17.5, 8.4, 8.5, 0, .04, "gold", "metal")
    E.box(.6, 16.9, 11.3, 11.95, 0, .12, "dark", "metal")
    E.label(8.75, 11.625, 16.1, .55, "led", d=.125, txt="いらっしゃいませ · WELCOME · NEW ARRIVALS · ようこそ · SALE")
    E.ext(ring_sign(1.45, .8, 9.6, 9.75), 0, .3, "indigo", "gloss", .05)
    E.ext(bubble_pts(12.0, 14.6, 9.25, 10.6), 0, .16, "white", "gloss", .03)
    for k in (-1, 0, 1):
        E.disc(13.3 + k * .44, 9.925, .11, .16, .2, "dark", "gloss")
    E.box(16.4, 17.1, 6.9, 11.0, 0, .08, "white", "paint")
    E.label(16.75, 9.3, .62, 3.6, "vkana", d=.085, txt="ファッション", fg="#F59A3A")
    E.label(16.75, 7.4, .62, 1.0, "vkana", d=.085, txt="雑貨", fg="#2E333B")
    E.window(.5, 5.3, 8.7, 11.05, cols=3, rows=2, inner="glass", sill=None)
    E.box(.5, 5.3, 3.6, 7.75, 0, .25, "portal", "metal")
    E.label(2.9, 4.92, 3.9, 2.6, "glow", d=.255)
    E.door_slide(2.9, 3.8, 3.6, 2.65, off=.25)
    E.box(.8, 5.0, 6.45, 7.55, .25, .27, "white", "paint")
    for u in (1.15, 4.65):
        E.box(u - .3, u + .3, 6.6, 7.2, .25, .45, "dark", "metal")
        E.disc(u, 6.9, .18, .45, .47, "steel", "metal")
    E.seg((.75, 6.28, .5), (5.05, 6.28, .5), .03, "timber", "timber")
    E.box(.85, 4.95, 5.45, 6.25, .48, .5, "indigo", "std")
    E.label(2.9, 5.85, 4.1, .8, "noren", d=.505, bg="#2E3FB0")
    for u in (.3, 5.5):
        x, z = E.p(u, .45)
        K.lantern(sc, x, 6.75, z, .3)
    E.box(5.8, 9.6, 3.7, 7.5, 0, .1, "indigo", "gloss")
    cw, rh = 3.8 / 3, 3.8 / 4
    for i in range(3):
        for j in range(4):
            u, y = 5.8 + (i + .5) * cw, 3.7 + (j + .5) * rh
            st = (i * 3 + j * 2 + 1) % 4
            if st == 0:
                E.disc(u, y, .36, .1, .18, "gold", "metal")
            elif st == 1:
                E.disc(u, y, .36, .1, .16, "cream", "paint")
                E.disc(u, y, .2, .16, .17, "indigo", "gloss")
            elif st == 2:
                E.disc(u, y, .36, .1, .18, "steel", "metal")
            else:
                E.disc(u, y, .36, .1, .12, "navy", "gloss")
    E.text("GOODS", 7.7, 7.58, .36, .05, "indigo", d=.02)
    E.shopfront(10.1, 16.2, 3.6, 7.4, 3, inner="glow")
    E.text("FASHION & GOODS", 13.15, 7.6, .5, .08, "dark", d=.02)
    # north face to the street
    N.box(0, 34.17, 9.0, 9.08, 0, .04, "gold", "metal")
    N.box(3.0, 31.2, 11.35, 11.95, 0, .12, "dark", "metal")
    N.label(17.1, 11.65, 28.0, .5, "led", d=.125, txt="海辺のファッション＆雑貨 · SEASIDE FASHION & GOODS · いらっしゃいませ · WELCOME")
    N.ext(ring_sign(1.03, .57, 5.4, 10.2), 0, .25, "indigo", "gloss", .04)
    N.ext(bubble_pts(7.6, 9.8, 9.85, 10.85), 0, .14, "white", "gloss", .03)
    for k in (-1, 0, 1):
        N.disc(8.7 + k * .36, 10.35, .09, .14, .18, "dark", "gloss")
    N.text("FASHION & GOODS", 15.4, 9.75, .72, .1, "indigo", d=.02)
    u = 22.0
    while u < 33.0:
        N.window(u, u + 1.8, 9.4, 10.8, frame="dark", inner="glass")
        u += 2.6
    N.box(.7, 1.3, 8.7, 11.2, 0, .08, "white", "paint")
    N.label(1.0, 9.95, .5, 2.4, "vkana", d=.085, txt="ファッション", fg="#F59A3A")
    # back to the lane
    for a in (3.2, 8.0, 12.8):
        Wf.window(a, a + 2.4, 9.3, 11.7, cols=2, frame="dark", inner="glass")
    for u in (.3, 17.2):
        Wf.downpipe(u, elev.lane_z(20.0 + u), 12.5)
    for u in (6.0, 10.9):
        Wf.box(u - .55, u + .55, 7.6, 8.3, 0, .5, "white", "paint")
        Wf.disc(u, 7.95, .25, .5, .52, "dark", "metal")
    Wf.door_solid(1.4, 1.2, 8.4, 2.2)
    zl = elev.lane_z(21.0)
    for k in range(4):
        Wf.box(.6, 2.4 + (3 - k) * .3, zl + k * .155, zl + (k + 1) * .155, 0, .3 + (3 - k) * .3, "conc-2", "conc")


def build_cafe(sc, b):
    """White stone and timber seaside café after the café reference, with a roof terrace."""
    x0, x1, z0, z1 = 13.75, 37.08, 68.33, 77.5
    sc.box(x0, 3.0, z0, x1, 7.8, z1, "stone-w", "panel")
    sc.box(x0 - .05, 7.8, z0 - .05, x1 + .05, 8.0, z1 + .05, "cream", "stone")
    sc.box(x0 + .2, 7.98, z0 + .2, x1 - .2, 8.02, z1 - .2, "timber", "deck")
    ring = [(x0 + .12, z0 + .12), (x1 - .12, z0 + .12), (x1 - .12, z1 - .12), (x0 + .12, z1 - .12), (x0 + .12, z0 + .12)]
    K.rail_line(sc, [(x, 8.0, z) for x, z in ring], h=1.05, post=1.2, cap="timber")
    for i, (px, py) in enumerate(((170, 500), (205, 522), (245, 503))):
        u, v = b.P(px, py)
        K.parasol_set(sc, u, 8.02, v, 1.3, "white", 3, wood=True, seed=i)
    rnd = random.Random(5)
    for xx in (16.0, 22.0, 28.0, 33.5):
        sc.box(xx, 8.0, z1 - 1.0, xx + 1.8, 8.45, z1 - .4, "timber", "timber")
        for k in range(3):
            sc.shrubs.append([round(xx + .4 + k * .5, 2), 8.45, round(z1 - .7, 2), .32])
        for k in range(6):
            sc.cyl(xx + rnd.uniform(.2, 1.6), 8.85 + rnd.uniform(0, .2), z1 - .7 + rnd.uniform(-.2, .2), .07, .07, 0,
                   ("pink", "yel-3", "white")[k % 3], axis="s", mat="paint")
    S = K.Face(sc, "S", x0, z0, x1, z1)
    E = K.Face(sc, "E", x0, z0, x1, z1)
    Wf = K.Face(sc, "W", x0, z0, x1, z1)
    S.shopfront(3.6, 20.6, 3.6, 6.0, 7, inner="glow")
    S.box(3.25, 20.8, 6.0, 6.15, 0, 2.5, "wood-d", "timber")
    S.box(3.25, 20.8, 6.15, 7.55, 0, .35, "wood-d", "timber")
    S.text("SEASIDE CAFE", 12.6, 6.6, .62, .08, "white", d=.35)
    S.label(4.25, 6.85, 1.1, 1.1, "cafesign", d=.355, txt="")
    for k in range(10):
        x, z = S.p(4.0 + k * 1.75, 1.6)
        sc.cyl(x, 5.96, z, .08, .08, .03, "warm", seg=10, mat="led")
    S.box(20.8, 23.63, 3.0, 8.0, 0, .3, "stone-w", "panel")
    S.label(22.2, 5.9, 2.5, 4.0, "pier", d=.305)
    E.box(-.3, 2.53, 3.0, 8.0, 0, .3, "stone-w", "panel")
    E.shopfront(2.9, 8.8, 3.6, 6.0, 3, inner="glow")
    E.box(2.53, 9.17, 6.15, 7.55, 0, .35, "wood-d", "timber")
    E.label(5.8, 6.85, 1.1, 1.1, "cafesign", d=.355, txt="")
    Wf.box(.8, 5.0, 6.1, 6.9, 0, .06, "wood-d", "timber")
    Wf.window(.95, 4.85, 6.2, 6.8, cols=3, frame="dark", inner="glow", sill=None)
    Wf.door_solid(6.42, 1.1, elev.lane_z(75.0), 2.2, "wood-d", "timber")
    Wf.box(3.4, 4.6, 5.2, 5.9, 0, .45, "white", "paint")
    sc.seg((16.05, 8.0, 70.3), (16.05, 9.7, 70.3), .15, "steel", "metal", 12)
    sc.cyl(16.05, 9.7, 70.3, .28, .05, .25, "dark", seg=12, mat="metal")


def build_lifestyle(sc, b):
    """Lifestyle & Souvenir in the Japanese shopping-street style: blue-glazed kawara eave, signs, noren, lanterns."""
    x0, x1, z0, z1 = 130.33, 153.33, 55.0, 71.67
    sc.box(x0, 3.0, z0, x1, 8.7, z1, "plaster", "plaster")
    K.kawara_eave(sc, x0, z0, x1, z1, 8.7, "NESW", "tile-b")
    K.flat_roof(sc, x0, z0, x1, z1, 8.7, 9.0, "plaster", "plaster", sides="")
    sc.box(x0 + 1.0, 8.68, z0 + 1.0, 138.5, 8.76, 58.6, "yel", "deck")
    for k in range(3):
        sc.box(132.0 + k * 2.0, 8.7, 56.2, 133.3 + k * 2.0, 9.25, 57.6, "timber", "timber")
        for j in range(2):
            sc.shrubs.append([round(132.3 + k * 2.0 + j * .6, 2), 9.25, 56.9, .35])
    for (px, pz) in ((141.0, 60.0), (144.0, 60.0)):
        K.ac_unit(sc, px, 8.72, pz, 0)
    # annex to the north
    sc.box(139.17, 3.0, 50.5, x1, 7.2, z0, "plaster", "plaster")
    K.kawara_eave(sc, 139.17, 50.5, x1, z0, 7.2, "NEW", "tile-b", proj=.6, rise=.4, ends=0.0)
    K.flat_roof(sc, 139.17, 50.5, x1, z0, 7.2, 7.4, "plaster", "plaster", sides="")
    sc.box(139.17 + .35, 7.2, z0 - .25, x1 - .35, 7.75, z0, "conc-2", "metal")        # flashing against the main wall
    # roof sign (kanban) standing behind the eave ridge, so the eave never hides it
    sc.box(141.83, 7.55, 51.12, 146.83, 8.75, 51.24, "white", "paint")
    sc.label([144.33, 8.15, 51.11], 4.8, 1.08, 180, "pill", txt="おみやげ SOUVENIR", fg="#D9432F", bg="#FFFFFF")
    for u in (142.4, 146.26):
        sc.box(u - .06, 7.4, 51.24, u + .06, 8.6, 51.36, "dark", "metal")
    # canopy band on the south with the roof garden
    sc.box(x0, 3.0, z1, x1, 6.35, 75.83, "plaster", "plaster")
    K.flat_roof(sc, x0, z1, x1, 75.83, 6.35, 6.62, "plaster", "plaster", "dark", "metal")
    sc.prism(box(142.17, 72.0, 149.17, 75.33), 6.35, 6.7, "bed", "soft")
    for k in range(8):
        sc.shrubs.append([round(142.6 + k * .85, 2), 6.7, 73.6 + (k % 2) * .8, .45])
    B = K.Face(sc, "S", x0, z1, x1, 75.83)
    B.box(0, 23.0, 5.95, 6.05, 0, .04, "gold", "metal")
    B.box(.17, 8.83, 5.75, 6.3, 0, .1, "yel", "paint")
    B.text("GOODS · HOME · GIFTS", 4.5, 5.86, .22, .03, "dark", d=.1)
    B.shopfront(.5, 8.5, 3.6, 5.7, 4, inner="glow")
    B.box(8.95, 11.55, 3.6, 6.2, 0, .2, "portal", "metal")
    B.label(10.25, 4.42, 2.0, 1.6, "glow", d=.205)
    B.door_slide(10.25, 1.8, 3.6, 1.65, off=.2)
    B.box(9.25, 11.25, 4.55, 5.25, .42, .44, "verm", "std")
    B.label(10.25, 4.9, 2.0, .7, "noren", d=.445, bg="#D9432F")
    pts = [B.p(11.67, 0), B.p(19.17, 0), B.p(19.17, 1.5), B.p(11.67, 1.5)]
    sc.plate(pts, [6.0, 6.0, 5.35, 5.35], "yel", "paint", t=.06)
    B.box(11.67, 19.17, 5.12, 5.35, 1.45, 1.5, "yel", "paint")
    B.shopfront(11.9, 19.0, 3.6, 5.1, 4, inner="glow")
    for u in (12.6, 18.2):
        B.seg((u, 3.6, 2.67), (u, 4.4, 2.67), .05, "dark")
    B.box(12.0, 18.8, 4.35, 5.05, 2.6, 2.72, "pink", "gloss")
    B.text("SOUVENIR", 15.4, 4.5, .5, .06, "white", d=2.72)
    B.box(19.4, 22.7, 4.0, 5.9, 0, .1, "verm", "gloss")
    for i in range(4):
        for j in range(2):
            u, y = 19.4 + (i + .5) * .825, 4.0 + (j + .5) * .95
            B.disc(u, y, .3, .1, .17, ("gold", "cream", "steel", "navy")[(i + j * 2) % 4], "metal" if (i + j) % 2 else "gloss")
    for u in (1.2, 4.5, 7.8, 19.9, 22.1):
        x, z = B.p(u, .4)
        K.lantern(sc, x, 5.85 if u < 9 else 6.05, z, .26)
    # main south face above the band
    S = K.Face(sc, "S", x0, z0, x1, z1)
    S.box(.6, 5.6, 6.95, 8.35, 0, .08, "red", "gloss")
    S.label(3.1, 7.65, 4.9, 1.32, "redpanel", d=.085, txt="おみやげ")
    S.text("LIFESTYLE & SOUVENIR", 12.0, 7.65, .52, .08, "dark", d=.02)
    S.label(19.8, 7.65, 2.9, 1.6, "cloud", d=.06, txt="SOUVENIR")
    S.box(22.25, 22.85, 7.1, 8.5, 0, .06, "white", "paint")
    S.label(22.55, 7.8, .5, 1.2, "vkana", d=.065, txt="雑貨", fg="#D9432F")
    # west face on the seating terrace
    Wf = K.Face(sc, "W", x0, z0, x1, z1)
    Wf.box(0, 16.67, 7.7, 7.8, 0, .04, "gold", "metal")
    Wf.box(1.0, 5.8, 4.3, 7.3, 0, .1, "verm", "gloss")
    for i in range(5):
        for j in range(3):
            u, y = 1.0 + (i + .5) * .96, 4.3 + (j + .5) * 1.0
            Wf.disc(u, y, .34, .1, .17, ("gold", "cream", "steel", "navy")[(i * 3 + j * 2) % 4], "gloss")
    Wf.box(6.5, 10.2, 3.6, 7.45, 0, .2, "portal", "metal")
    Wf.label(8.35, 4.95, 3.1, 2.7, "glow", d=.205)
    Wf.door_slide(8.35, 2.9, 3.6, 2.65, off=.2)
    Wf.box(6.85, 9.85, 5.52, 6.3, .42, .44, "verm", "std")
    Wf.label(8.35, 5.91, 3.0, .78, "noren", d=.445, bg="#D9432F")
    for u in (6.2, 10.5):
        x, z = Wf.p(u, .4)
        K.lantern(sc, x, 6.75, z, .26)
    Wf.window(11.0, 16.0, 4.4, 7.3, cols=3, frame="dark", inner="glow")
    Wf.ext(bubble_pts(11.6, 13.5, 8.0, 8.55, .2), 0, .1, "white", "gloss", .02)
    # north side to the truck pad and palm row (u = 153.33 - x for both faces, left = east as seen from the north)
    N = K.Face(sc, "N", 139.17, 50.5, x1, z0)                 # annex front
    N.box(0, 14.16, 6.5, 6.6, 0, .04, "gold", "metal")
    N.box(.3, 6.0, 6.65, 7.05, 0, .06, "white", "paint")
    N.text("SOUVENIR & GIFTS", 3.15, 6.73, .26, .03, "dark", d=.06)
    N.shopfront(.5, 5.8, 3.6, 5.6, 4, inner="glow")
    pts = [N.p(.3, 0), N.p(6.0, 0), N.p(6.0, 1.1), N.p(.3, 1.1)]
    sc.plate(pts, [6.25, 6.25, 5.8, 5.8], "yel", "paint", t=.06)       # awning over the display windows
    N.box(.3, 6.0, 5.62, 5.8, 1.05, 1.1, "yel", "paint")
    N.box(6.4, 9.0, 3.6, 6.2, 0, .2, "portal", "metal")
    N.label(7.7, 4.42, 2.0, 1.6, "glow", d=.205)
    N.door_slide(7.7, 1.8, 3.6, 1.65, off=.2)
    N.box(6.7, 8.7, 4.55, 5.25, .42, .44, "verm", "std")
    N.label(7.7, 4.9, 2.0, .7, "noren", d=.445, bg="#D9432F")
    for u in (6.15, 9.25):
        x, z = N.p(u, .4)
        K.lantern(sc, x, 5.95, z, .26)
    N.box(9.6, 13.6, 4.0, 6.2, 0, .1, "verm", "gloss")
    for i in range(5):
        for j in range(2):
            u, y = 9.6 + (i + .5) * .8, 4.0 + (j + .5) * 1.1
            N.disc(u, y, .3, .1, .17, ("gold", "cream", "steel", "navy")[(i + j * 2) % 4], "metal" if (i + j) % 2 else "gloss")
    N.box(13.7, 14.1, 4.2, 6.3, 0, .06, "white", "paint")
    N.label(13.9, 5.25, .36, 1.9, "vkana", d=.065, txt="雑貨", fg="#D9432F")
    M = K.Face(sc, "N", x0, z0, x1, z1)                      # main block, west of the annex (behind the palm planter)
    M.box(14.16, 23.0, 7.7, 7.8, 0, .04, "gold", "metal")
    M.window(15.0, 18.6, 4.9, 7.3, cols=3, frame="dark", inner="glow")
    M.box(19.2, 22.5, 6.0, 7.4, 0, .08, "red", "gloss")
    M.label(20.85, 6.7, 3.1, 1.2, "redpanel", d=.085, txt="おみやげ")
    # east face: windows, service door, condensers
    E = K.Face(sc, "E", x0, z0, x1, z1)
    for (a, b_) in ((.8, 3.4), (6.6, 9.0), (11.4, 15.8)):
        E.window(a, b_, 5.0, 7.4, cols=2, frame="dark", inner="glass")
    E.door_solid(4.6, 1.2, 3.6, 2.2)
    for u in (8.0, 14.0):
        E.box(u - .55, u + .55, 7.9, 8.6, 0, .5, "white", "paint")
        E.disc(u, 8.25, .25, .5, .52, "dark", "metal")
    # forecourt: stall, photo statue, vending kiosk, heart sign, tents on the east terrace
    sc.box(130.83, 3.6, 76.33, 135.0, 4.6, 78.0, "timber", "timber")
    sc.box(130.83, 4.6, 76.33, 135.0, 4.65, 78.0, "cream", "paint")
    for (px, pz) in ((130.95, 76.45), (134.88, 76.45), (130.95, 77.88), (134.88, 77.88)):
        sc.seg((px, 3.6, pz), (px, 5.9, pz), .04, "dark")
    sc.boxc(132.92, 6.0, 77.17, 4.6, .08, 2.1, "cyan", "paint", rx=-12)
    for k in range(7):
        sc.cyl(131.3 + k * .55, 4.82, 77.0, .16, .16, 0, ("pink", "yel-3", "cyan", "green")[k % 4], axis="s", mat="gloss")
    sc.cyl(140.17, 3.6, 79.67, 1.4, 1.4, .5, "pink", seg=28, mat="gloss")
    sc.cyl(140.17, 4.85, 79.67, .78, .78, 0, "white", axis="s", mat="gloss")
    sc.cyl(140.17, 5.95, 79.67, .58, .58, 0, "white", axis="s", mat="gloss")
    for s_ in (-1, 1):
        sc.cyl(140.17 + s_ * .32, 6.35, 79.67, .18, .02, .35, "white", seg=6, mat="gloss")
    gk = sc.level_at(152.5, 77.17)                    # the east end of the plaza falls toward the promenade
    sc.box(151.33, gk - .3, 76.33, 153.67, 5.4, 78.0, "white", "paint")
    sc.box(151.5, 4.3, 77.98, 153.5, 5.1, 78.02, "blue", "gloss")
    sc.label([152.5, 4.0, 78.03], 1.6, .5, 0, "pill", txt="DRINKS", fg="#FFFFFF", bg="#2F8FE8")
    sc.seg((128.33, 3.6, 79.5), (128.33, 6.0, 79.5), .05, "dark")
    sc.label([128.33, 6.6, 79.5], 1.5, 1.3, 0, "heart")
    for (a, c, d, e) in ((154.5, 65.0, 157.83, 68.33), (160.33, 67.83, 163.67, 71.67)):
        for (px, pz) in ((a, c), (d, c), (a, e), (d, e)):
            sc.seg((px, sc.level_at(px, pz) - .05, pz), (px, 5.8, pz), .04, "steel")
        sc.box(a, 5.55, c, d, 5.8, e, "white", "paint")
        sc.cyl((a + d) / 2, 5.8, (c + e) / 2, (d - a) * .74, .05, 1.1, "white", seg=4, mat="paint")
        gc = sc.level_at((a + d) / 2, c + .6)
        sc.box(a + .2, gc - .2, c + .3, d - .2, gc + .9, c + .9, "timber", "timber")


def build_kiosks(sc, b):
    P = b.P
    names = [("たこ焼き", "pink"), ("クレープ", "yel"), ("かき氷", "cyan")]
    for i, (x0, y0, x1, y1) in enumerate(((140, 145, 177, 178), (177, 152, 243, 180), (243, 155, 273, 180))):
        u0, v0 = P(x0, y0)
        u1, v1 = P(x1, y1)
        u0, u1 = u0 + (.15 if i else 0), u1 - (.15 if i < 2 else 0)      # stalls stand apart, so roofs and parapets don't overlap
        txt, col = names[i]
        sc.box(u0, 8.4, v0, u1, 11.2, v1, "plaster", "plaster")
        K.flat_roof(sc, u0, v0, u1, v1, 11.2, 11.45, "plaster", "plaster", "dark", "metal")
        N = K.Face(sc, "N", u0, v0, u1, v1)
        L = N.L
        N.box(.4, L - .4, 9.3, 10.6, 0, .015, "rubber", "rubber")
        N.label(L / 2, 9.95, L - 1.0, 1.2, "glow", d=.02)
        N.box(.3, L - .3, 9.22, 9.32, 0, .5, "timber", "timber")
        N.box(.3, L - .3, 10.6, 10.9, 0, .28, "steel", "groove")
        x, z = N.p(L / 2, .9)
        sc.boxc(x, 10.72, z, L - .2, .06, 1.25, col, "paint", ry=0, rx=-25)
        sc.label([x, 10.76, z - .03], L - .3, 1.15, 180, "stripe", rx=-65, a=COL[col], b2="#FFFFFF")
        N.box(.1, L - .1, 10.18, 10.4, 1.45, 1.5, col, "paint")
        N.box(L / 2 - 1.6, L / 2 + 1.6, 11.45, 12.25, .1, .25, "white", "paint")
        N.label(L / 2, 11.85, 3.0, .7, "pill", d=.255, txt=txt, fg="#2E333B", bg="#FFFFFF")


def build_town(sc, b):
    P = b.P
    st = street_level(b)
    blocks = [(40, -6, 300, 70, 12), (310, -6, 540, 70, 15), (668, -6, 826, 70, 11), (836, -6, 1000, 90, 16),
              (1010, -6, 1120, 70, 12), (1130, -6, 1298, 70, 14)]
    awn = ["cyan", "coral", "yel", "navy", "pink", "green"]
    for i, (x0, y0, x1, y1, ht) in enumerate(blocks):
        u0, v0 = P(x0, y0)
        u1, v1 = P(x1, y1)
        base = st((u0 + u1) / 2)
        sc.box(u0, base - 1, v0, u1, base + ht, v1, "facade", "facade")
        sc.box(u0 - .05, base + ht, v0 - .05, u1 + .05, base + ht + .5, v1 + .05, "town-roof", "conc")
        S = K.Face(sc, "S", u0, v0, u1, v1)
        S.box(0, S.L, base, base + 3.6, 0, .03, "facade", "panel")
        S.label(S.L / 2, base + 1.6, S.L - 1.2, 2.8, "glow", d=.035)
        S.box(.4, S.L - .4, base + 3.0, base + 3.12, 0, 1.4, awn[i], "paint")
        for k in range(int((u1 - u0) / 9)):
            K.ac_unit(sc, u0 + 4 + k * 9, base + ht + .5, (v0 + v1) / 2, 0)
    u0, v0 = P(1250, 140)
    u1, v1 = P(1302, 330)
    sc.box(u0, 5.0, v0, u1, 18.0, v1, "facade", "facade")
    sc.box(u0 - .05, 18.0, v0 - .05, u1 + .05, 18.5, v1 + .05, "town-roof", "conc")


def build_hut(sc, b):
    P = b.P
    u0, v0 = P(697, 720)
    u1, v1 = P(742, 760)
    a0, b0 = P(700, 760)
    a1, b1 = P(740, 782)
    sc.box(u0, .6, v0, u1, 1.0, b1, "timber", "deck")
    for (px, pz) in ((u0 + .2, v0 + .2), (u1 - .2, v0 + .2), (u0 + .2, b1 - .2), (u1 - .2, b1 - .2)):
        sc.seg((px, -.2, pz), (px, .6, pz), .12, "timber-2", "timber", 8)
    sc.box(u0 + .3, 1.0, v0 + .3, u1 - .3, 3.6, v1 - .3, "timber", "timberv")
    S = K.Face(sc, "S", u0 + .3, v0 + .3, u1 - .3, v1 - .3)
    S.box(1.0, S.L - 1.0, 2.2, 3.1, 0, .02, "rubber", "rubber")
    S.label(S.L / 2, 2.65, S.L - 2.2, .8, "glow", d=.025)
    S.box(.9, S.L - .9, 2.1, 2.2, 0, .55, "timber", "timber")
    S.box(1.6, S.L - 1.6, 3.15, 3.45, 0, .05, "cream", "paint")
    S.label(S.L / 2, 3.3, S.L - 3.4, .26, "pill", d=.055, txt="RENTAL · LIFEGUARD", fg="#2E333B", bg="#EFE8D8")
    for k, col in enumerate(("blue", "yel", "pink")):
        x, z = S.p(1.2 + k * .5, .35)
        sc.boxc(x, 2.0, z, .3, 2.0, .06, col, "gloss", rx=-8)
    sc.cyl((u0 + u1) / 2, 3.6, (v0 + v1) / 2, (u1 - u0) * .8, .05, 2.0, "thatch", seg=4, mat="thatch")
    sc.box(u0, 3.5, v0, u1, 3.65, v1, "timber-2", "timber")


def build_stage(sc, b):
    hs = b.hardscape()
    deck = hs["deck"]
    sc.prism(deck, 3.0, 4.2, "timber", "deck")
    sc.prism(deck.buffer(.06).difference(deck), 3.0, 4.22, "wood-d", "timber")
    # 4R x 0.15 down to the lawn and top plaza (+3.60): steps only along the deck edges that face them, ending square
    front = unary_union([hs["lawn"], hs["top"]]).buffer(.6).difference(stair_footprints(REC).buffer(.05))
    dq = deck.simplify(.05)
    cs = list(dq.exterior.coords)[:-1]
    if not dq.exterior.is_ccw:
        cs = cs[::-1]                                 # counter-clockwise: (dz, -dx) points outward
    n_ = len(cs)
    sel = []
    for i in range(n_):
        (x0, z0), (x1, z1) = cs[i], cs[(i + 1) % n_]
        L = math.hypot(x1 - x0, z1 - z0)
        if L < .3:
            sel.append(False)
            continue
        nx, nz = (z1 - z0) / L, -(x1 - x0) / L         # outward normal
        mp = Point((x0 + x1) / 2 + nx * 1.0, (z0 + z1) / 2 + nz * 1.0)
        sel.append(front.contains(mp) and not dq.contains(mp))
    for k, y in enumerate((4.05, 3.9, 3.75)):
        ring = deck.buffer(.45 * (k + 1), join_style="mitre").difference(deck.buffer(.45 * k, join_style="mitre"))
        keep = []
        for i in range(n_):
            if not sel[i]:
                continue
            (x0, z0), (x1, z1) = cs[i], cs[(i + 1) % n_]
            L = math.hypot(x1 - x0, z1 - z0)
            nx, nz = (z1 - z0) / L, -(x1 - x0) / L
            d_ = 1.4
            keep.append(Polygon([(x0, z0), (x1, z1), (x1 + nx * d_, z1 + nz * d_), (x0 + nx * d_, z0 + nz * d_)]))
            if sel[(i + 1) % n_]:                     # outside corner between two stepped edges: keep the mitre
                keep.append(Point(x1, z1).buffer(2.0))
        if keep:
            sc.prism(ring.intersection(unary_union(keep)).difference(stair_footprints(REC).buffer(.05)), 3.0, y, "timber", "deck")
    P = b.P
    (ax, az), (bx, bz) = P(1100, 190), P(1207, 237)
    dx, dz = bx - ax, bz - az
    L = math.hypot(dx, dz)
    ux, uz = dx / L, dz / L
    nx, nz = -uz, ux
    posts = [(ax + ux * 2 + nx * 1.5, az + uz * 2 + nz * 1.5), (bx - ux * 2 + nx * 1.5, bz - uz * 2 + nz * 1.5)]
    fwd = 9.0
    pts2 = posts + [(posts[1][0] + nx * fwd, posts[1][1] + nz * fwd), (posts[0][0] + nx * fwd, posts[0][1] + nz * fwd)]
    top = 4.2 + 6.0
    for (px, pz) in pts2:
        sc.boxc(px, 4.2 + 3.0, pz, .32, 6.0, .32, "steel", "metal")
        sc.boxc(px, 4.3, pz, .7, .2, .7, "dark", "metal")
    for (p, q) in zip(pts2, pts2[1:] + pts2[:1]):
        for oy in (0, .32):
            sc.seg((p[0], top - oy, p[1]), (q[0], top - oy, q[1]), .04, "steel", "metal", 6)
        n_ = int(math.dist(p, q) / .6)
        for k in range(n_):
            t0, t1 = k / n_, (k + 1) / n_
            sc.seg((p[0] + (q[0] - p[0]) * t0, top, p[1] + (q[1] - p[1]) * t0),
                   (p[0] + (q[0] - p[0]) * t1, top - .32, p[1] + (q[1] - p[1]) * t1), .015, "steel", "metal", 4)
        m_ = int(math.dist(p, q) / 1.6)
        for k in range(1, m_):
            t = k / m_
            x, z = p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t
            sc.cyl(x, top - .55, z, .12, .12, 0, "warm", axis="s", mat="led")
    ang = math.degrees(math.atan2(dz, dx))
    for (px, py) in ((1112.5, 204), (1190, 242.5)):
        u, v = P(px, py)
        for k in range(2):
            sc.boxc(u, 4.2 + .8 + k * 1.6, v, 1.6, 1.58, 1.4, "dark", "rubber", ry=-ang)
            for (oy, r) in ((-.3, .38), (.4, .2)):
                fx, fz = u + nx * .71, v + nz * .71
                sc.seg((fx, 4.2 + .8 + k * 1.6 + oy, fz), (fx + nx * .03, 4.2 + .8 + k * 1.6 + oy, fz + nz * .03), r, "steel", "metal", 18)


def build_pier(sc, b):
    body = Polygon(b.pier_rect(0, 34, -3.75, 3.75))
    head = Polygon(b.pier_rect(34, 45.5, -22, 5.2))
    deck = unary_union([body, head])
    sc.prism(deck, 2.15, 2.4, "timber", "deck")
    ramp_end = Polygon(b.pier_rect(-1.0, .3, -3.9, 3.9))
    sc.prism(deck.buffer(.08).difference(deck).difference(ramp_end), 1.95, 2.42, "wood-d", "timber")   # no trim across the ramp foot
    sc.hard.append((deck, 2.4))
    for t in range(2, 46, 4):
        for nn in (-3.4, 3.4) if t < 34 else (-21.5, -14, -7, 0, 4.8):
            x, z = b.pier_pt(t, nn)
            sc.cyl(x, -2.6, z, .2, .2, 4.75, "timber-2", seg=10, mat="timber")
        if t < 34:
            a, c = b.pier_pt(t, -3.6), b.pier_pt(t, 3.6)
            sc.seg((a[0], 1.95, a[1]), (c[0], 1.95, c[1]), .12, "timber-2", "timber", 6)
    for nn in (-3.4, 3.4):
        a, c = b.pier_pt(0, nn), b.pier_pt(34, nn)
        sc.seg((a[0], 2.0, a[1]), (c[0], 2.0, c[1]), .14, "timber-2", "timber", 6)

    def edge(t0, n0, t1, n1):
        a, c = b.pier_pt(t0, n0), b.pier_pt(t1, n1)
        return [(a[0], 2.4, a[1]), (c[0], 2.4, c[1])]
    for nn in (-3.6, 3.6):                            # ramp rails, continuing the pier's timber-capped rails
        a, c = b.pier_pt(b.PIER_RAMP_T + .3, nn), b.pier_pt(.5, nn)
        K.rail_line(sc, [(a[0], 3.15, a[1]), (c[0], 2.4, c[1])], h=1.05, post=1.6, cap="timber")
        for t in (b.PIER_RAMP_T + 1.5, b.PIER_RAMP_T / 2):   # piles under the ramp, up to its underside
            x, z = b.pier_pt(t, nn * .94)
            sc.cyl(x, -1.5, z, .2, .2, b.RAMP_H(x, z) - .27 + 1.5, "timber-2", seg=10, mat="timber")
    for pts in (edge(.5, -3.6, 34, -3.6), edge(.5, 3.6, 34, 3.6), edge(34, -3.6, 34, -21.85), edge(34, -21.85, 45.35, -21.85),
                edge(45.35, -21.85, 45.35, -1.3), edge(45.35, 1.3, 45.35, 5.05), edge(45.35, 5.05, 34, 5.05), edge(34, 5.05, 34, 3.6)):
        K.rail_line(sc, pts, h=1.05, post=1.8, cap="timber")
    for nn in (-1.0, 1.0):
        a = b.pier_pt(45.55, nn)
        sc.seg((a[0], -1.5, a[1]), (a[0], 3.3, a[1]), .03, "steel", "metal", 6)
    for k in range(9):
        a, c = b.pier_pt(45.55, -1.0), b.pier_pt(45.55, 1.0)
        y = -1.2 + k * .4
        sc.seg((a[0], y, a[1]), (c[0], y, c[1]), .02, "steel", "metal", 6)
    for (t, nn) in ((35.0, -21.0), (44.5, -21.0), (35.0, 4.3), (44.5, 4.3), (20.0, -3.2), (20.0, 3.2)):
        x, z = b.pier_pt(t, nn)
        sc.cyl(x, 2.4, z, .16, .16, .45, "dark", seg=12, mat="metal")
        sc.cyl(x, 2.85, z, .2, .2, 0, "dark", axis="s", mat="metal")


def build_stair_gate(sc, b):
    """Escalators in the main stair's middle lane: skirts, glass balustrades, rubber handrails, grooved steps, combs;
    and the shotengai gate on the forecourt."""
    zt, zb = 8.4, 3.6
    y0 = elev.ESC_Y0
    y1, y2 = y0 + elev.ESC_PLATE, y0 + elev.ESC_PLATE + elev.ESC_RUN
    y3 = y2 + elev.ESC_PLATE
    tn = math.tan(math.radians(30))

    def surf(z):
        if z <= y1:
            return zt
        if z >= y2:
            return zb
        return zt - (z - y1) * tn
    top_line = [(z, surf(z)) for z in (y0, y1, y2, y3)]
    for (e0, e1, d) in elev.ESC_X:
        for xx in (e0, e1 - .12):
            skirt = [(z, h + .12) for z, h in top_line] + [(z, h - .95) for z, h in top_line[::-1]]
            sc.ext("zy", skirt, xx, .12, "steel", "metal", .01)
            glass = [(y0 + .45, zt + .14), (y1, zt + .14), (y2, zb + .14), (y3 - .45, zb + .14), (y3 - .25, zb + .55),
                     (y3 - .45, zb + .98), (y2, zb + .98), (y1, zt + .98), (y0 + .45, zt + .98), (y0 + .25, zt + .55)]
            sc.ext("zy", glass, xx + .045, .03, "glass", "glass", 0)
            rail = [(xx + .06, h + 1.0, z) for z, h in zip([y0 + .45, y1, y2, y3 - .45], [zt, zt, zb, zb])]
            sc.polyseg(rail, .04, "rubber", "rubber", 10)
            for (zc, hc, sgn) in ((y0 + .45, zt + .58, -1), (y3 - .45, zb + .58, 1)):
                # newel return: the handrail rounds outward past the landing (top end north, bottom end south)
                sc.torus(xx + .06, hc, zc, .42, .04, 180, 90 * sgn, 90, "rubber", "rubber")
        n_ = int(elev.ESC_RUN / .4)
        for k in range(n_):
            zz = y1 + (k + .5) * .4
            h = surf(zz)
            sc.box(e0 + .14, h - .23, zz - .2, e1 - .14, h + .005, zz + .2, "steel", "groove")
            sc.box(e0 + .14, h - .005, zz - .2, e1 - .14, h + .01, zz - .16, "yel", "paint")
        for (za, zc, h) in ((y0, y1, zt), (y2, y3, zb)):
            sc.box(e0 + .14, h - .3, za, e1 - .14, h + .02, zc, "steel", "groove")
            zm = zc if h == zt else za
            sc.box(e0 + .14, h, zm - .12, e1 - .14, h + .03, zm + .12, "yel", "paint")
        x, z = (e0 + e1) / 2, y3 - .3
        sc.box(x - .35, zb + .9, z - .02, x + .35, zb + 1.25, z + .02, "green" if d == "UP" else "red", "gloss")
    for (xa, xb) in ((88.5, 88.75), (90.45, 90.75), (92.45, 92.67)):
        deck = [(z, h + .14) for z, h in top_line] + [(z, h - .4) for z, h in top_line[::-1]]
        sc.ext("zy", deck, xa, xb - xa, "steel", "metal", .005)
    K.gate_hq(sc, elev.GATE_X[0], elev.GATE_X[1], elev.GATE_Y, 8.4)
    for x, txt in ((elev.GATE_X[0], "ようこそ"), (elev.GATE_X[1], "うみ")):
        sc.box(x - .3, 8.4 + 2.1, elev.GATE_Y - .345, x + .3, 8.4 + 4.7, elev.GATE_Y - .33, "white", "paint")
        sc.box(x - .3, 8.4 + 2.1, elev.GATE_Y + .33, x + .3, 8.4 + 4.7, elev.GATE_Y + .345, "white", "paint")
        for ry, off in ((180, -.35), (0, .35)):
            sc.label([x, 8.4 + 3.4, elev.GATE_Y + off], .56, 2.5, ry, "hsign", txt=txt)


def build_misc(sc, b):
    P = b.P
    u, v = P(*b.STATUE_PX)                          # on its plinth in the planter by the main stair
    sc.cyl(u, 3.9, v, b.STATUE_R - .1, b.STATUE_R - .1, .6, "white", seg=40, mat="stone")
    sc.cyl(u, 4.5, v, b.STATUE_R, b.STATUE_R, .08, "cream", seg=40, mat="stone")
    dy = 4.58 - 4.12                                # the figure stands on the plinth top (+4.58)
    sc.cyl(u, 5.3 + dy, v, 1.45, 1.45, 0, "white", axis="s", mat="gloss")
    sc.cyl(u, 6.85 + dy, v, 1.1, 1.1, 0, "white", axis="s", mat="gloss")
    sc.cyl(u + 1.3, 5.6 + dy, v - .4, .32, .32, 0, "pink", axis="s", mat="gloss")
    for s_ in (-1, 1):
        sc.cyl(u + s_ * .6, 7.55 + dy, v, .38, .02, .7, "white", seg=6, mat="gloss")
    cx, cy = P(605, 417)
    bed = Point(cx, cy).buffer(9.5, quad_segs=24)
    sc.prism(bed.difference(bed.buffer(-.3)), 3.0, 4.14, "conc", "conc")
    sc.prism(bed.buffer(.05).difference(bed.buffer(-.33)), 4.14, 4.2, "cream", "stone")
    ring = Point(cx, cy).buffer(13.5, quad_segs=24).difference(Point(cx, cy).buffer(11.2, quad_segs=24))
    seat = Point(cx, cy).buffer(11.2, quad_segs=24).difference(Point(cx, cy).buffer(9.5, quad_segs=24))
    cuts = unary_union([LineString([(cx - 20, cy - 20), (cx + 20, cy + 20)]).buffer(1.2),
                        LineString([(cx - 20, cy + 20), (cx + 20, cy - 20)]).buffer(1.2)])
    K.planter_hq(sc, ring.difference(cuts), 3.6, inner_t=.25)
    sc.prism(seat.difference(cuts), 3.0, 3.95, "conc", "conc")
    sc.prism(seat.difference(cuts).buffer(-.05), 3.95, 4.05, "timber", "timber")


# hills that wall the map (north, west and an east headland); the sea stays open to the south
INNER = [(-4, -14.5), (207, -14.5), (207, 30), (200, 46), (199.5, 100), (200.5, 160), (204, 215), (204, 420), (-4, 420)]


def build_terrain(sc, b):
    import shapely
    d = 2.5
    xs = np.arange(-90, 300.01, d)
    zs = np.arange(-90, 240.01, d)
    X, Z = np.meshgrid(xs, zs)
    inner = Polygon(INNER).buffer(-3.0)
    dist = shapely.distance(inner, shapely.points(X.ravel(), Z.ravel())).reshape(X.shape)
    g0w = np.interp(Z, [-14, 40, 90, 105, 125], [8.4, 7.0, 4.0, 1.0, -1.5])
    g0e = np.interp(Z, [-14, 30, 50, 60, 75], [8.4, 6.0, 3.0, 0.0, -2.0])
    g0 = np.where(X < 100, g0w, g0e)
    base = 30 - .09 * np.clip(Z + 14, 0, None)
    base = np.where(Z > 195, base * np.clip((245 - Z) / 50, 0, 1), base)
    noise = 4 * np.sin(X / 23) + 3 * np.cos(Z / 17 + X / 41) + 2 * np.sin((X + Z) / 11) + 1.5 * np.cos(X / 7 - Z / 9)
    target = np.maximum(base + noise, g0 + 4)
    m = np.clip((dist - 3.0) / 38, 0, 1)
    m = m * m * (3 - 2 * m)
    h = g0 - .4 + (target - g0 + .4) * m
    for (px, pz, top) in ((-15, 6.7, 17.0), (218, 6.7, 15.0)):        # mounds over the tunnel portals
        h = np.maximum(h, np.where(np.abs(X - px) < 30, top - ((X - px) ** 2 + (Z - pz) ** 2) / 45, -99))
    fall = np.clip((Z - 192) / 42, 0, 1)                             # headlands slope into the sea before the mesh edge
    fall = fall * fall * (3 - 2 * fall)
    h = h * (1 - fall) - 3.2 * fall
    h = np.where(dist <= 0, -30, h)
    sc.terrain = {"x0": float(xs[0]), "z0": float(zs[0]), "d": d, "nx": len(xs), "nz": len(zs),
                  "h": [int(round(v * 10)) for v in h.ravel()]}
    rnd = random.Random(31)
    n_ = 0
    while n_ < 420:
        i, j = rnd.randrange(1, len(xs) - 1), rnd.randrange(1, len(zs) - 1)
        hh = h[j, i]
        if dist[j, i] < 6 or hh < 3 or hh > 48:
            continue
        sl = math.hypot(h[j, i + 1] - h[j, i - 1], h[j + 1, i] - h[j - 1, i]) / (2 * d)
        if sl > .9:
            continue
        x, z = xs[i] + rnd.uniform(-1, 1), zs[j] + rnd.uniform(-1, 1)
        r = rnd.uniform(2.6, 4.6)
        kind = "s" if rnd.random() < .06 else ("p" if z > 120 and rnd.random() < .3 else "t")
        sc.trees.append([round(x, 2), round(hh - .3, 2), round(z, 2), round(r, 2), round(3.2 + r * 1.15, 2), kind, n_ % 97])
        n_ += 1
    # tunnel portals where the coastal road leaves the map: concrete headwall, coping, dark bore
    for (x0, x1, face, ry, yb) in ((-6.0, -4.0, -3.97, 90, 8.25), (207.0, 209.0, 206.97, -90, 5.85)):
        sc.box(x0, yb - 1, 1.0, x1, yb + 7.4, 12.4, "conc", "conc")
        sc.box(x0 - .1, yb + 7.4, .8, x1 + .1, yb + 7.7, 12.6, "cream", "stone")
        sc.label([face, yb + 3.4, 6.67], 10.0, 6.8, ry, "tunnel")
        sc.box(x0 - 6 if x0 < 0 else x1, yb - .3, 2.5, x0 if x0 < 0 else x1 + 6, yb + 5.8, 10.9, "rubber", "rubber")


REC = {}


def fill_holes(sc, b, rec, idw):
    """Last pass: any land not covered by a surface, a structure or a stair gets ground at the right level,
    so no hairline gap ever shows the sea through the park."""
    cov = []
    for s_ in sc.slabs:
        q = Polygon(s_["o"], s_["h"]).buffer(0)
        if q.area < 1e5:
            cov.append(q)
    cov += [Polygon(s_["o"], s_["h"]).buffer(0) for s_ in sc.prisms]
    cov += [Polygon(pl[0]).buffer(0) for pl in sc.plates]
    cov.append(stair_footprints(rec))
    cov.append(bldg_footprints(b))
    cu = unary_union(cov)
    coast = b.cr_sample(b.PP(b.COAST_PX), per=6)
    land = Polygon([(b.X0, b.Y0), (b.X1, b.Y0)] + coast + b.PP([(1150, 700), (1100, 712), (1087, 700), (1087, 647), (1043, 653)]) +
                   b.PP(b.SEAWALL_PX) + b.PP([(55, 700), (36, 700)])).buffer(0)
    holes = land.difference(cu)
    parts = [g for g in getattr(holes, "geoms", [holes]) if g.geom_type == "Polygon" and g.area > .002]
    if parts:
        fill = unary_union([g.buffer(.06) for g in parts]).intersection(land.buffer(.06))
        def low(x, z):                                # the lowest surface around: hidden under anything beside it
            vs = [sc.level_in(x + dx, z + dz) for dx, dz in ((0, 0), (.35, 0), (-.35, 0), (0, .35), (0, -.35))]
            vs = [v for v in vs if v is not None]
            return (min(vs) if vs else idw(x, z)) - .02
        sc.grid_slab(fill, low, "paver", "std", cell=2.0, bot=-1.0)


def scene_data(b):
    sc = Scene(b)
    b.planting_region()            # cache before recording, so the check's own plan pass is not recorded
    rec = record_plan(b)
    REC.clear()
    REC.update(rec)
    hs, idw = build_ground(sc, b, rec)
    build_walls(sc, b, rec)
    build_arcade(sc, b)
    build_arcade_interior(sc)
    build_cafe(sc, b)
    build_fashion(sc, b)
    build_lifestyle(sc, b)
    build_kiosks(sc, b)
    build_town(sc, b)
    build_hut(sc, b)
    build_stage(sc, b)
    build_pier(sc, b)
    build_stair_gate(sc, b)
    build_misc(sc, b)
    build_landmark(sc)
    build_terrain(sc, b)
    build_props(sc, b, rec, idw)
    fill_holes(sc, b, rec, idw)
    return sc.data()


def scene_json(b):
    return json.dumps(scene_data(b), separators=(",", ":"), ensure_ascii=False)
