"""3D massing model of the Japan Coastal Hangout Park for the perspective views (P-601).

The model is generated from the same data as the drawings: the walkable
surfaces come from build.hardscape(), planters, trees, palms, parasols,
benches, stairs, trucks and rocks are recorded while build.site_plan() draws
them, and the buildings follow the elevations in elev.py. Plan metres map to
three.js as x = east, z = south, y = level above sea (±0.00).
"""
import json
import math
import random

import numpy as np
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
from shapely.ops import unary_union

import elev

COL = {
    "paver": "#E3E6E8", "street": "#CDD3D8", "road": "#6E7780", "timber": "#D8B07E", "timber-2": "#C99C68",
    "lawn": "#8CC36A", "bed": "#5E9C4C", "shrub": "#4F8F45", "sand": "#F7F1DE", "sand-wet": "#E9DFC4",
    "seabed": "#9FCFCB", "water": "#43A9C6", "conc": "#C9CDD0", "conc-2": "#B3B9BE", "rock": "#A9A39A", "town": "#D7DCE1",
    "town-roof": "#AEB8C2", "glass": "#BFE6F0", "glow": "#FFE2A0", "dark": "#2E333B", "steel": "#8C99A6",
    "white": "#F7F7F5", "cream": "#F4EEDF", "wall": "#EFE6D6", "coral": "#E98564",
    "yel": "#F6C833", "yel-2": "#E0A915", "yel-3": "#FFE07A", "pink": "#F59BC3", "lilac": "#B9A2EE",
    "blue": "#2F8FE8", "red": "#E8414E", "green": "#3FB950", "cyan": "#24ABCC", "navy": "#2C3E57",
    "tree": "#6DAA55", "tree-2": "#5B9A49", "sak": "#F4B8D1", "palm": "#5E9A4A", "trunk": "#8A6A4A", "mint": "#A9DCC6",
    "thatch": "#CFA866",
}


class Scene:
    def __init__(self, b):
        self.b = b
        self.pal, self.pal_i = [], {}
        self.slabs, self.boxes, self.cyls, self.prisms = [], [], [], []
        self.trees, self.shrubs, self.labels, self.rocks = [], [], [], []
        self.hard = []          # (polygon, hspec) for level lookups

    # ------------------------------------------------------------- data
    def c(self, name):
        hexv = COL.get(name, name)
        if hexv not in self.pal_i:
            self.pal_i[hexv] = len(self.pal)
            self.pal.append(hexv)
        return self.pal_i[hexv]

    @staticmethod
    def ring(coords):
        return [[round(x, 2), round(z, 2)] for x, z in list(coords)[:-1]]

    def polys(self, g, simplify=.08):
        if g.is_empty:
            return []
        g = g.simplify(simplify, preserve_topology=True)
        parts = list(g.geoms) if isinstance(g, MultiPolygon) else [g] if isinstance(g, Polygon) else \
            [q for q in getattr(g, "geoms", []) if isinstance(q, Polygon)]
        return [q for q in parts if q.area > .05]

    def slab(self, g, top, color, mat="std", bot=-1.0, hard=True, vh=None):
        """Ground surface: polygon with a height spec (number, axis profile) or per-vertex heights."""
        for q in self.polys(g):
            rec = {"o": self.ring(q.exterior.coords), "h": [self.ring(r.coords) for r in q.interiors],
                   "c": self.c(color), "m": mat, "b": bot}
            if vh is not None:
                rec["vo"] = [round(vh(x, z), 2) for x, z in rec["o"]]
                rec["vh"] = [[round(vh(x, z), 2) for x, z in r] for r in rec["h"]]
            else:
                rec["t"] = top
            self.slabs.append(rec)
            if hard:
                self.hard.append((q, top))

    def prism(self, g, y0, y1, color, mat="std", shadow=True):
        for q in self.polys(g, .03):
            self.prisms.append({"o": self.ring(q.exterior.coords), "h": [self.ring(r.coords) for r in q.interiors],
                                "y0": round(y0, 3), "y1": round(y1, 3), "c": self.c(color), "m": mat, "s": int(shadow)})

    def box(self, x0, y0, z0, x1, y1, z1, color, mat="std", ry=0.0, rx=0.0):
        self.boxes.append([round((x0 + x1) / 2, 3), round((y0 + y1) / 2, 3), round((z0 + z1) / 2, 3),
                           round(abs(x1 - x0), 3), round(abs(y1 - y0), 3), round(abs(z1 - z0), 3),
                           round(ry, 2), round(rx, 2), self.c(color), mat])

    def boxc(self, cx, cy, cz, sx, sy, sz, color, mat="std", ry=0.0, rx=0.0):
        self.boxes.append([round(cx, 3), round(cy, 3), round(cz, 3), round(sx, 3), round(sy, 3), round(sz, 3),
                           round(ry, 2), round(rx, 2), self.c(color), mat])

    def cyl(self, x, y, z, r0, r1, h, color, axis="y", seg=16, mat="std"):
        """Cylinder or cone; (x, y, z) is the base centre (y axis) or the centre (x / z axis)."""
        self.cyls.append([round(x, 3), round(y, 3), round(z, 3), round(r0, 3), round(r1, 3), round(h, 3),
                          self.c(color), axis, seg, mat])

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

    def level_at(self, x, z, default=None):
        p = Point(x, z)
        hs = [self.h_eval(s, x, z) for q, s in self.hard if q.buffer(.01).contains(p)]
        if hs:
            return max(hs)
        if default is not None:
            return default
        best, bd = 3.6, 1e9
        for q, s in self.hard:
            d = q.distance(p)
            if d < bd:
                bd, best = d, self.h_eval(s, x, z)
        return best

    def idw_builder(self, step=2.0):
        pts, hs = [], []
        for q, s in self.hard:
            for r in [q.exterior] + list(q.interiors):
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
                "trees": self.trees, "shrubs": self.shrubs, "labels": self.labels, "rocks": self.rocks,
                "views": VIEWS, "sun": [80, 140, 120], "center": [100, 0, 70]}


# camera presets: position, target, field of view
VIEWS = {
    "aerial": {"name": "Aerial from the south-east", "pos": [168, 92, 182], "tgt": [96, 2, 66], "fov": 42},
    "arcade": {"name": "Arcade front from the plaza", "pos": [63.5, 5.35, 59.5], "tgt": [47.0, 7.6, 51.6], "fov": 55},
    "plaza": {"name": "Central plaza from the east stair", "pos": [118.0, 14.0, 28.0], "tgt": [86.0, 3.6, 66.0], "fov": 55},
    "cafe": {"name": "Café terrace from the plaza edge", "pos": [57.0, 5.5, 90.5], "tgt": [27.0, 5.4, 76.5], "fov": 60},
    "lifestyle": {"name": "Lifestyle & Souvenir from the promenade", "pos": [124.0, 5.4, 93.0], "tgt": [143.0, 6.0, 64.0], "fov": 58},
    "stage": {"name": "Stage and event lawn from the curved path", "pos": [163.0, 7.4, 62.0], "tgt": [180.0, 4.8, 36.0], "fov": 58},
    "beach": {"name": "Beach, promenade and pier", "pos": [70.0, 12.0, 150.0], "tgt": [110.0, 2.5, 100.0], "fov": 55},
}


# ---------------------------------------------------------------- recording
def record_plan(b):
    """Run site_plan() with the prop helpers wrapped, collecting what it places."""
    rec = {k: [] for k in ("planter", "canopy", "palm", "parasol", "bench", "stair", "quad", "treads", "truck", "rock",
                           "railing", "lounger")}
    orig = {}

    def wrap(name, fn):
        orig[name] = getattr(b, name)
        setattr(b, name, fn)

    def planter_g(cv, g, seed, density=.8, rmin=.4, rmax=.8, wall=.3, radius=.35):
        rec["planter"].append((b.open_(g, radius) if radius else g, seed, density))
        return orig["planter_g"](cv, g, seed, density, rmin, rmax, wall, radius)

    def canopy(cv, u, v, r, seed=0, kind="tree", shadow=True, detail=True):
        rec["canopy"].append((u, v, r, kind, seed))
        return orig["canopy"](cv, u, v, r, seed, kind, shadow, detail)

    def palm_top(cv, u, v, r, seed=0, shadow=True):
        rec["palm"].append((u, v, r, seed))
        return orig["palm_top"](cv, u, v, r, seed, shadow)

    def parasol(cv, u, v, r=1.3, cls="umb-y", chairs=0, ribs=8):
        rec["parasol"].append((u, v, r, cls, chairs))
        return orig["parasol"](cv, u, v, r, cls, chairs, ribs)

    def bench(cv, u, v, length=3.0, ang=0.0, depth=.7):
        rec["bench"].append((u, v, length, ang))
        return orig["bench"](cv, u, v, length, ang, depth)

    def stair_ns(cv, x0, y0, x1, y1, flights, landing=0.0, cheek=True, rails=(), label=None):
        rec["stair"].append((x0, y0, x1, y1, flights, landing))
        return orig["stair_ns"](cv, x0, y0, x1, y1, flights, landing, cheek, rails, label)

    def quad_stair(cv, q, risers, label=None, cheek=(.3, .6)):
        rec["quad"].append((q, risers))
        return orig["quad_stair"](cv, q, risers, label, cheek)

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

    for name, fn in [("planter_g", planter_g), ("canopy", canopy), ("palm_top", palm_top), ("parasol", parasol),
                     ("bench", bench), ("stair_ns", stair_ns), ("quad_stair", quad_stair), ("quad_treads", quad_treads),
                     ("truck_r", truck_r), ("rock", rock), ("railing", railing), ("lounger", lounger)]:
        wrap(name, fn)
    try:
        b.site_plan()
    finally:
        for name, fn in orig.items():
            setattr(b, name, fn)
    return rec


# ---------------------------------------------------------------- ground
def build_ground(sc, b):
    P, GB, G = b.P, b.GB, b.G
    hs = b.hardscape()
    X0, Y0, X1, Y1 = b.X0, b.Y0, b.X1, b.Y1
    frame = box(X0, Y0, X1, Y1)

    def ax_y(pts_px):  # profile along the plan's south axis (z), given as (y_px, level)
        return {"ax": [0, 0, 0, 1], "pts": [[round(P(0, y)[1], 3), h] for y, h in pts_px]}

    def ax_x(pts_px):
        return {"ax": [0, 0, 1, 0], "pts": [[round(P(x, 0)[0], 3), h] for x, h in pts_px]}

    street_prof = ax_x([(730, 8.4), (940, 6.6), (1100, 6.6), (1230, 6.0)])
    # town (non-playable) and the coastal road
    sc.slab(GB(36, -12, 1302, 95), street_prof, "town", hard=False)
    sc.slab(GB(36, 95, 1302, 135), {"ax": street_prof["ax"], "pts": [[t, h - .15] for t, h in street_prof["pts"]]}, "road")
    for (x0, y0, x1, y1, ht) in [(40, -6, 300, 70, 12), (310, -6, 540, 70, 15), (668, -6, 826, 70, 11), (836, -6, 1000, 90, 16),
                                 (1010, -6, 1120, 70, 12), (1130, -6, 1298, 70, 14), (1250, 140, 1302, 330, 12)]:
        u0, v0 = P(x0, y0)
        u1, v1 = P(x1, y1)
        base = sc.h_eval(street_prof, (u0 + u1) / 2, 0)
        sc.box(u0, base - 1, v0, u1, base + ht, v1, "town")
        sc.box(u0 + .4, base + ht, v0 + .4, u1 - .4, base + ht + .3, v1 - .4, "town-roof")
    # west lane (stepped slope) and the rest of the street level
    lane_box = GB(88, 196, 142, 640)
    lane = hs["street"].intersection(lane_box)
    sc.slab(hs["street"].difference(lane_box), street_prof, "street")
    sc.slab(lane, ax_y([(135, 8.4), (632, 3.15)]), "street")
    # plaza: flat, the east end falls to the junction (+3.15); east path ramps +6.00 -> +4.80
    east = hs["east"]
    plaza = hs["plaza"].difference(east)
    cut = b.P(1040, 0)[0]
    plaza_w = plaza.intersection(box(-50, -50, cut, 300))
    plaza_e = plaza.difference(box(-50, -50, cut, 300))
    sc.slab(plaza_w, 3.6, "paver")
    sc.slab(plaza_e, ax_y([(470, 3.6), (560, 3.15)]), "paver")
    sc.slab(east, ax_y([(145, 6.0), (414, 4.8)]), "paver")
    sc.slab(hs["top"], 3.6, "paver")
    # raked lawn: +3.60 at the stage, +4.80 at the curved steps
    o = P(1107, 307)
    t = P(1172, 426)
    L = math.hypot(t[0] - o[0], t[1] - o[1])
    sc.slab(hs["lawn"], {"ax": [o[0], o[1], (t[0] - o[0]) / L, (t[1] - o[1]) / L], "pts": [[0, 3.6], [L, 4.8]]}, "lawn")
    sc.slab(hs["prom"], 3.15, "timber")
    sc.slab(hs["terr"], 3.62, "timber")
    sc.slab(GB(93, 153, 140, 207), 8.42, "timber")
    sc.slab(b.open_(GB(733, 219, 770, 302), 1.2), 3.63, "timber")
    sc.slab(GB(770, 217, 942, 302), 3.62, "road")
    # stage deck
    sc.prism(hs["deck"], 3.0, 4.2, "timber")
    sc.hard.append((hs["deck"], 4.2))
    # sand: +0.90 at the sea wall sloping into the water
    sh = b.cr_sample(b.PP(b.SHORE_PX), per=8)
    sand = Polygon(b.PP([(170, 635), (382.5, 675), (452.5, 675), (764, 672), (770, 655), (836, 655), (840, 654), (875, 637),
                         (1038.8, 637), (1043, 653), (1090, 648), (1100, 712), (1068, 752)]) + sh[::-1] +
                   b.PP([(150, 820), (160, 760), (175, 700), (170, 640)])).buffer(0)
    wall_l = LineString(b.PP(b.SEAWALL_PX))
    shore_l = LineString(sh)

    def sand_h(x, z):
        dw, ds = wall_l.distance(Point(x, z)), shore_l.distance(Point(x, z))
        return .95 * ds / (ds + dw + 1e-6) - .2
    sc.slab(sand.segmentize(3.0), None, "sand", bot=-3, vh=sand_h, hard=False)
    sand_e = Polygon(b.PP([(1087, 647), (1170, 640), (1176, 665), (1188, 682), (1150, 690), (1118, 704), (1100, 712), (1090, 700)]))
    sc.slab(sand_e, .6, "sand", bot=-3, hard=False)
    sc.slab(Polygon(b.PP(b.WEST_ROCK_PX)), .9, "sand", bot=-3, hard=False)
    sc.hard.append((sand, sand_h))
    # base land (banks behind the beds) and planting beds shaped by their neighbours
    idw = sc.idw_builder()
    coast = b.cr_sample(b.PP(b.COAST_PX), per=6)
    land = Polygon([(X0, Y0), (X1, Y0)] + coast + b.PP([(1150, 700), (1100, 712), (1087, 700), (1087, 647), (1043, 653)]) +
                   b.PP(b.SEAWALL_PX) + b.PP([(55, 700), (36, 700)])).buffer(0)
    covered = unary_union([q for q, s in sc.hard])
    rest = land.difference(covered).intersection(frame)
    beds = hs["beds"].intersection(frame)
    sc.slab(unary_union([beds, rest]).simplify(.3).segmentize(2.5), None, "bed", vh=lambda x, z: idw(x, z) + .25, hard=False)
    # sea bed and water
    sc.slab(frame.difference(land.buffer(-.5)), -2.4, "seabed", bot=-3, hard=False)
    sc.label([(X0 + X1) / 2, -.05, (Y0 + Y1) / 2 + 40], X1 - X0 + 80, Y1 - Y0 + 120, 0, "water")
    return hs, idw


# ---------------------------------------------------------------- props
def build_props(sc, b, rec, idw):
    rnd = random.Random(7)
    lv = sc.level_at
    # planters: 0.6 m walls, bed and shrubs
    for g, seed, dens in rec["planter"]:
        c = g.representative_point()
        base = lv(c.x, c.y, None)
        if base is None:
            base = idw(c.x, c.y)
        inner = g.buffer(-.3, join_style="mitre")
        sc.prism(g, base - .2, base + .6, "conc")
        sc.prism(inner, base + .4, base + .62, "bed")
        scatter(sc, inner, base + .6, rnd, dens * .5, .35, .7)
    # beds: shrubs
    hs = b.hardscape()
    scatter(sc, hs["beds"], None, rnd, .16, .45, 1.0, idw=idw)
    # trees, sakura, palms
    for (u, v, r, kind, seed) in rec["canopy"]:
        if kind not in ("tree", "sak"):
            continue
        base = lv(u, v, None)
        if base is None:
            base = idw(u, v)
        h = 3.2 + r * 1.15
        sc.trees.append([round(u, 2), round(base, 2), round(v, 2), round(r, 2), round(h, 2), "s" if kind == "sak" else "t", seed % 97])
    for (u, v, r, seed) in rec["palm"]:
        base = lv(u, v, None)
        if base is None:
            base = idw(u, v)
        sc.trees.append([round(u, 2), round(base, 2), round(v, 2), round(r, 2), round(5.5 + r * .6, 2), "p", seed % 97])
    # parasols and café tables
    colors = {"umb-y": "yel", "umb-c": "cyan", "umb-p": "pink", "prop": "white"}
    for (u, v, r, cls, chairs) in rec["parasol"]:
        base = lv(u, v)
        if r < .8:
            sc.cyl(u, base, v, .45, .45, .75, "white", seg=14)
            continue
        sc.cyl(u, base, v, .04, .04, 2.45, "dark", seg=6)
        sc.cyl(u, base + 2.1, v, r, .05, .55, colors.get(cls, "white"), seg=12)
        sc.cyl(u, base, v, .5, .5, .74, "white", seg=12)
        for k in range(chairs):
            a = k * 2 * math.pi / chairs + .4
            sc.boxc(u + math.cos(a) * 1.0, base + .23, v + math.sin(a) * 1.0, .45, .46, .45, "white")
    for (u, v, L, ang) in rec["bench"]:
        base = lv(u, v)
        sc.boxc(u, base + .43, v, L, .08, .5, "timber-2", ry=-ang)
        sc.boxc(u, base + .2, v, L * .9, .4, .3, "dark", ry=-ang)
    for (u, v, ang) in rec["lounger"]:
        base = lv(u, v)
        sc.boxc(u, base + .25, v, .7, .12, 1.9, "white", ry=-ang + 90)
    for (u, v, r, seed) in rec["rock"]:
        base = lv(u, v, None)
        if base is None:
            base = -.6 if v > 105 else .6
        sc.rocks.append([round(u, 2), round(base + r * .25, 2), round(v, 2), round(r, 2), seed % 89])
    # stairs: treads stacked over the traced footprints, levels read from the surfaces at either end
    for (x0, y0, x1, y1, flights, landing) in rec["stair"]:
        if abs(x0 - b.P(315, 0)[0]) < .5:
            continue                                  # fashion stair core is inside the building
        zt = lv((x0 + x1) / 2, y0 - .8)
        zb = lv((x0 + x1) / 2, y1 + .8)
        run = (y1 - y0) - landing * (len(flights) - 1)
        tr = run / sum(f - 1 for f in flights)
        nr = sum(flights)
        r = (zt - zb) / nr
        y, z = y0, zt
        for i, f in enumerate(flights):
            for k in range(1, f):
                z -= r
                sc.box(x0, zb - .4, y + (k - 1) * tr, x1, z, y + k * tr, "conc")
            y += (f - 1) * tr
            if i < len(flights) - 1:
                z -= r
                sc.box(x0, zb - .4, y, x1, z, y + landing, "conc")
                y += landing
    for (q, risers) in rec["quad"]:
        quad_steps(sc, q, risers - 1, 4.8, 3.15)
    for (q, count) in rec["treads"]:
        quad_steps(sc, q, count, 3.15, 2.4)
    # railings
    for pts in rec["railing"]:
        for (a, c) in zip(pts, pts[1:]):
            mx, mz = (a[0] + c[0]) / 2, (a[1] + c[1]) / 2
            dx, dz = c[0] - a[0], c[1] - a[1]
            L = math.hypot(dx, dz)
            nx, nz = -dz / L, dx / L
            top = max(lv(mx + nx * .7, mz + nz * .7), lv(mx - nx * .7, mz - nz * .7))
            ang = math.degrees(math.atan2(dz, dx))
            sc.boxc(mx, top + 1.08, mz, L, .06, .06, "dark", ry=-ang)
            for k in range(int(L / 2) + 1):
                t = k / max(1, int(L / 2))
                sc.boxc(a[0] + dx * t, top + .54, a[1] + dz * t, .05, 1.08, .05, "dark")
    # food trucks
    stripe = {"stripe": "pink", "stripec": "cyan", "stripey": "yel"}
    for (cx, cy, ang, st) in rec["truck"]:
        a = math.radians(ang)
        ca, sa = math.cos(a), math.sin(a)
        sc.boxc(cx - .7 * ca, 1.73 + 3.6, cy - .7 * sa, 5.0, 2.55, 2.5, "cream", ry=-ang)
        sc.boxc(cx + 2.5 * ca, 1.5 + 3.6, cy + 2.5 * sa, 1.5, 2.1, 2.4, stripe.get(st, "pink"), ry=-ang)
        sc.boxc(cx - .7 * ca - 1.5 * sa, 2.75 + 3.6, cy - .7 * sa + 1.5 * ca, 3.8, .1, .9, stripe.get(st, "pink"), ry=-ang)
        sc.boxc(cx, 3.6 + .3, cy, 6.0, .6, 2.2, "dark", ry=-ang)


def quad_steps(sc, q, n_treads, zt, zb):
    a, b_, c, d = q
    r = (zt - zb) / (n_treads + 1)
    for k in range(1, n_treads + 1):
        t0 = (k - 1) / n_treads
        p0 = (a[0] + (d[0] - a[0]) * t0, a[1] + (d[1] - a[1]) * t0)
        p1 = (b_[0] + (c[0] - b_[0]) * t0, b_[1] + (c[1] - b_[1]) * t0)
        sc.prism(Polygon([p0, p1, c, d]), zb - .4, zt - k * r, "conc")


def scatter(sc, g, y, rnd, density, rmin, rmax, idw=None):
    if g.is_empty:
        return
    x0, z0, x1, z1 = g.bounds
    n_ = int(g.area * density)
    tries = 0
    from shapely.prepared import prep
    pg = prep(g)
    while n_ > 0 and tries < n_ * 6:
        tries += 1
        x, z = rnd.uniform(x0, x1), rnd.uniform(z0, z1)
        if pg.contains(Point(x, z)):
            r = rnd.uniform(rmin, rmax)
            yy = y if y is not None else idw(x, z) + .2
            sc.shrubs.append([round(x, 2), round(yy, 2), round(z, 2), round(r, 2)])
            n_ -= 1


# ---------------------------------------------------------------- buildings
def roof(sc, x0, z0, x1, z1, y, par_top, par_col, roof_col="conc-2", t=.3, sides="NESW", cap=None):
    """Flat roof at y with a parapet of thickness t up to par_top on the given sides (N = north / -z)."""
    sc.box(x0 + t, y, z0 + t, x1 - t, y + .03, z1 - t, roof_col)
    walls = {"N": (x0, z0, x1, z0 + t), "S": (x0, z1 - t, x1, z1), "W": (x0, z0, x0 + t, z1), "E": (x1 - t, z0, x1, z1)}
    for k in "NESW":
        a, b, c, d = walls[k]
        sc.box(a, y, b, c, par_top, d, par_col if k in sides else "conc")
        if cap:
            sc.box(a - .02, par_top, b - .02, c + .02, par_top + .07, d + .02, cap)


def face_east(x_face, z_of_u):
    def F(u, y, d=0.0):
        return (x_face + d, y, z_of_u(u))
    return F


def build_arcade(sc, b):
    c = elev.CTR
    xe, zs, zn = 47.92, 65.0, 37.92          # east face, south and north walls
    W = 13.75
    sc.box(W, 3.0, zn, xe, 9.6, zs, "yel")
    roof(sc, W, zn, xe, zs, 9.6, 10.2, "yel", "timber", cap="dark")
    for (x0, z0, x1, z1) in ((xe, zn, xe + .03, zs), (W, zs, xe, zs + .03), (W - .03, zn, W, zs)):
        sc.box(x0, 9.72, z0, x1, 9.92, z1, "pink")
    for (x0, z0, x1, z1) in ((W, zn, xe, zn + .05), (W, zs - .05, xe, zs), (W, zn, W + .05, zs), (xe - .05, zn, xe, zs)):
        sc.box(x0, 10.27, z0, x1, 11.3, z1, "glass", "glass")
    sc.box(W, 3.0, zn, xe + .02, 4.05, zs, "conc")
    Z = lambda u: zs - u  # noqa: E731
    # steps (3R) across the controller frame
    for k in range(3):
        sc.box(xe, 3.0, Z(c + 10.3), xe + 1.2 - k * .4, 3.75 + k * .15, Z(c - 10.3), "conc")
    # controller sign
    sc.box(xe, 7.3, Z(c + 7.1), xe + .6, 10.65, Z(c - 7.1), "yel")
    sc.box(xe + .6, 7.65, Z(c + 3.75), xe + .7, 10.5, Z(c - 3.75), "yel-3")
    for (u0, u1) in ((c - 7.0, c - 3.75), (c + 3.75, c + 7.0)):
        sc.box(xe, 7.42, Z(u1), xe + .78, 11.0, Z(u0), "cream")
    sc.box(xe, 4.15, Z(c - 4.0), xe + .25, 7.42, Z(c - 6.75), "cream")
    sc.box(xe, 4.15, Z(c + 6.75), xe + .25, 7.42, Z(c + 4.0), "cream")
    du, dz = c - 5.35, 9.12
    sc.box(xe + .78, dz - .3, Z(du + .88), xe + .92, dz + .3, Z(du - .88), "dark")
    sc.box(xe + .78, dz - .88, Z(du + .3), xe + .92, dz + .88, Z(du - .3), "dark")
    for (bu, bz, col) in ((c + 4.75, 9.95, "blue"), (c + 6.0, 9.3, "red"), (c + 4.8, 8.55, "green")):
        sc.cyl(xe + .78 + .1, bz, Z(bu), .45, .45, .2, col, axis="x", seg=20)
    sc.label([xe + .72, 9.62, Z(c - .6)], 5.6, 1.3, 90, "text", txt="ARCADE", fg="#FFFFFF", stroke="#B9A2EE", font="800", bg=None)
    sc.label([xe + .72, 8.49, Z(c - .6)], 4.0, .58, 90, "pill", txt="ゲームセンター", fg="#FFFFFF", bg="#2E333B")
    sc.label([xe + .72, 9.38, Z(c + 2.85)], 1.2, .95, 90, "mascot")
    # entrance: lit interior behind glass, pillars, lintel LED
    sc.label([xe + .03, 5.62, Z(c)], 5.0, 3.15, 90, "door")
    for (u0, u1) in ((c - 3.05, c - 2.5), (c + 2.5, c + 3.05)):
        sc.box(xe, 4.05, Z(u1), xe + .3, 7.65, Z(u0), "yel")
    sc.box(xe, 7.2, Z(c + 2.5), xe + .3, 7.65, Z(c - 2.5), "yel")
    sc.label([xe + .27, 5.78, Z(c - 5.37)], 2.25, 2.75, 90, "poster")
    sc.label([xe + .27, 5.78, Z(c + 5.37)], 2.5, 2.9, 90, "panel")
    # portholes and lower windows on the outer bays; portholes on the south wall
    for u in (2.1, 4.4, 22.3, 24.6):
        sc.cyl(xe + .05, 8.55, Z(u), .62, .62, .12, "cream", axis="x", seg=20)
        sc.cyl(xe + .1, 8.55, Z(u), .46, .46, .06, "glass", axis="x", seg=20, mat="glass")
    for u in (2.1, 4.4, 22.1):
        sc.box(xe, 4.85, Z(u + .85), xe + .05, 6.75, Z(u - .85), "yel-2")
        sc.label([xe + .07, 5.8, Z(u)], 1.4, 1.6, 90, "glass")
    x = 16.6
    while x < 45.6:
        sc.cyl(x, 8.55, zs + .05, .66, .66, .12, "cream", axis="z", seg=20)
        sc.cyl(x, 8.55, zs + .1, .48, .48, .06, "glass", axis="z", seg=20, mat="glass")
        x += 3.0
    # floodlights, roof parasols
    for u in (7.0, 10.6, 16.0, 19.6):
        sc.box(xe - .3, 10.9, Z(u + .3), xe + .1, 11.15, Z(u - .3), "dark")
    for (px, pz) in ((22.0, 42.0), (30.0, 46.0), (38.0, 42.5), (24.0, 58.0), (40.0, 60.0)):
        sc.cyl(px, 9.6, pz, .04, .04, 2.3, "dark", seg=6)
        sc.cyl(px, 11.4, pz, 1.45, .05, .55, "cream", seg=12)
    # prize & vending strip, south of the arcade
    sc.box(W, 3.0, zs, xe, 6.9, 68.33, "yel")
    roof(sc, W, zs, xe, 68.33, 6.9, 7.2, "dark")
    sc.label([xe + .03, 4.85, 66.67], 2.7, 2.5, 90, "glow")
    sc.label([xe + .03, 6.52, 66.67], 2.87, .55, 90, "pill", txt="PRIZE", fg="#FFFFFF", bg="#F59BC3")
    sc.label([42.6, 4.9, 68.36], 9.6, 2.2, 0, "glow")


def build_cafe(sc, b):
    x0, x1, z0, z1 = 13.75, 37.08, 68.33, 77.5
    sc.box(x0, 3.0, z0, x1, 7.8, z1, "cream")
    roof(sc, x0, z0, x1, z1, 7.8, 8.2, "yel", sides="ES", cap="dark")
    sc.box(x0 + 3, 8.2, z0 + 2.0, x0 + 4.2, 8.9, z0 + 3.0, "steel")
    sc.label([27.3, 4.88, z1 + .03], 19.4, 2.55, 0, "glow")
    # striped awning sloping down to the south, valance with the name
    sc.label([27.29, 6.68, z1 + 1.2], 20.1, 2.5, 0, "stripe", rx=-75, a="#F6C833", b2="#FFFFFF")
    sc.label([27.29, 6.15, z1 + 2.45], 20.1, .4, 0, "pill", txt="SEASIDE CAFE", fg="#2E333B", bg="#FFFFFF")
    sc.label([x1 + .03, 4.9, 73.4], 2.1, 2.8, 90, "glow")
    for u in (6.0, 13.3, 20.6):
        sc.box(x0 + u - .15, 7.1, z1, x0 + u + .15, 7.5, z1 + .12, "dark")


def build_fashion(sc, b):
    x0, x1, z0, z1 = 13.75, 47.92, 20.0, 37.5
    sc.box(x0, 3.0, z0, x1, 12.6, z1, "wall")
    roof(sc, x0, z0, x1, z1, 12.6, 13.2, "coral", cap="dark")
    sc.box(35.0, 12.63, z0 + .3, 47.6, 12.68, z0 + 5.0, "timber")
    for k in range(7):
        sc.box(16.5 + k * 2.6, 12.6, z0 + .6, 18.1 + k * 2.6, 13.3, z0 + 2.6, "steel")
    sc.box(x1, 8.4, z0, x1 + .04, 8.7, z1 - 5.6, "coral")
    Z = lambda u: z1 - u  # noqa: E731
    sc.label([x1 + .03, 5.55, Z(11.55)], 11.1, 3.9, 90, "glow")
    sc.label([x1 + .03, 10.6, Z(11.55)], 11.1, 3.2, 90, "glass")
    k = 6.35
    while k < 17.1:
        sc.box(x1, 8.9, Z(k + .07), x1 + .25, 12.3, Z(k - .07), "timber")
        k += .7
    sc.label([x1 + .03, 8.0, Z(11.55)], 9.0, .7, 90, "pill", txt="FASHION & GOODS", fg="#2E333B", bg="#EFE6D6")
    sc.label([x1 + .03, 8.1, Z(2.9)], 5.0, 9.4, 90, "glass")
    sc.label([x1 + .05, 4.95, Z(2.2)], 2.4, 2.7, 90, "glow")
    sc.box(x1, 6.55, Z(5.8), x1 + 1.4, 6.8, Z(.2), "coral")
    # north face to the kiosk strip: ribbon window with fins, roof sign
    sc.label([30.8, 10.6, z0 - .03], 32.2, 3.0, 180, "glass")
    k = x0 + 1.6
    while k < x1 - 1:
        sc.box(k - .07, 9.0, z0 - .25, k + .07, 12.2, z0, "timber")
        k += 1.34
    sc.label([30.8, 12.9, z0 - .05], 9.0, .45, 180, "pill", txt="FASHION & GOODS", fg="#FFFFFF", bg="#E98564")
    sc.box(35.0, 13.2, z0, 47.5, 14.3, z0 + .05, "glass", "glass")


def build_lifestyle(sc, b):
    x0, x1, z0, z1 = 130.33, 153.33, 55.0, 71.67
    sc.box(x0, 3.0, z0, x1, 8.7, z1, "white")
    roof(sc, x0, z0, x1, z1, 8.7, 9.0, "white", "dark")
    for (a, c, d, e) in ((x0 - .03, z0, x0 + .35, z1), (x0, z1 - .35, x1, z1 + .03), (x1 - .35, z0, x1 + .03, z1)):
        sc.box(a, 9.0, c, d, 9.4, e, "yel")
    sc.box(x0 + .35, 8.73, z0 + .35, 138.0, 8.76, 58.0, "yel")
    for k in range(3):
        sc.box(132.0 + k * 2.0, 8.7, 55.8, 133.3 + k * 2.0, 9.4, 57.2, "steel")
    sc.box(139.17, 3.0, 50.5, x1, 7.2, z0, "white")
    sc.box(141.83, 7.2, 48.67, 146.83, 8.2, 50.83, "white")
    sc.box(x0, 3.0, z1, x1, 6.35, 75.83, "white")
    roof(sc, x0, z1, x1, 75.83, 6.35, 6.62, "dark", "dark")
    sc.box(130.5, 5.75, 75.83, 139.17, 6.35, 76.3, "yel")
    sc.box(142.17, 6.6, 72.0, 149.17, 7.0, 75.33, "bed")
    sc.label([145.75, 5.55, 76.75], 7.5, 1.95, 0, "stripe", rx=-70, a="#F6C833", b2="#F6C833")
    sc.label([134.5, 4.6, 75.86], 8.0, 2.1, 0, "glow")
    sc.label([145.45, 4.35, 75.86], 7.1, 1.5, 0, "glow")
    sc.label([142.0, 8.1, z1 - .68], 17.0, .9, 0, "pill", txt="LIFESTYLE & SOUVENIR", fg="#2E333B", bg="#FFFFFF")
    for u in (142.9, 148.5):
        sc.box(u - .06, 3.6, 78.44, u + .06, 4.4, 78.56, "dark")
    sc.label([145.75, 4.7, 78.5], 6.8, .7, 0, "pill", txt="SOUVENIR", fg="#FFFFFF", bg="#F59BC3")
    sc.label([x0 - .03, 5.2, 63.33], 3.3, 3.0, -90, "glow")
    for (a, c) in ((56.0, 60.8), (66.0, 71.0)):
        sc.label([x0 - .03, 6.0, (a + c) / 2], c - a, 3.2, -90, "glass")
    # stall, photo statue, vending kiosk, tents on the east terrace
    sc.box(130.83, 3.6, 76.33, 135.0, 4.6, 78.0, "timber")
    sc.box(130.6, 5.9, 76.1, 135.2, 6.25, 78.2, "cyan")
    sc.cyl(140.17, 3.6, 79.67, 1.4, 1.4, .5, "pink", seg=20)
    sc.cyl(140.17, 4.1, 79.67, .65, .55, 1.0, "white", seg=16)
    sc.cyl(140.17, 5.1, 79.67, .5, .5, .5, "white", seg=16)
    sc.box(151.33, 3.6, 76.33, 153.67, 5.4, 78.0, "white")
    for (a, c, d, e) in ((154.5, 65.0, 157.83, 68.33), (160.33, 67.83, 163.67, 71.67)):
        sc.box(a, 3.6, c, d, 5.8, e, "white")
        sc.cyl((a + d) / 2, 5.8, (c + e) / 2, (d - a) * .74, .05, 1.1, "cream", seg=4)


def build_small(sc, b):
    P = b.P
    # kiosks on the kiosk strip, striped awnings to the street
    for (x0, y0, x1, y1, col) in ((140, 145, 177, 178, "pink"), (177, 152, 243, 180, "yel"), (243, 155, 273, 180, "cyan")):
        u0, v0 = P(x0, y0)
        u1, v1 = P(x1, y1)
        sc.box(u0, 8.4, v0, u1, 11.4, v1, "wall")
        sc.box(u0 - .1, 11.4, v0 - .1, u1 + .1, 11.55, v1 + .1, "dark")
        sc.label([(u0 + u1) / 2, 10.85, v0 - .55], u1 - u0 + .3, 1.2, 180, "stripe", rx=-55, a=COL[col], b2="#FFFFFF")
        sc.label([(u0 + u1) / 2, 9.6, v0 - .02], u1 - u0 - .5, 1.2, 180, "glow")
    # beach hut on its deck
    u0, v0 = P(697, 720)
    u1, v1 = P(742, 760)
    sc.box(u0 + .3, 1.0, v0 + .3, u1 - .3, 3.6, v1 - .3, "timber")
    sc.cyl((u0 + u1) / 2, 3.6, (v0 + v1) / 2, (u1 - u0) * .78, .05, 2.0, "thatch", seg=4)
    a0, b0 = P(700, 760)
    a1, b1 = P(740, 782)
    sc.box(a0, .6, b0, a1, 1.3, b1, "timber")
    sc.label([(u0 + u1) / 2, 2.4, v1 - .28], 4.0, .9, 0, "glow")
    # stage PA stacks
    for (x, y) in ((1112.5, 204), (1190, 242.5)):
        u, v = P(x, y)
        sc.boxc(u, 4.2 + 1.6, v, 1.6, 3.2, 1.6, "dark")
    # cat statue in the plaza
    u, v = P(707, 350)
    sc.cyl(u, 3.6, v, 3.2, 3.2, .45, "white", seg=28)
    sc.cyl(u, 5.3, v, 1.45, 1.45, 0, "white", axis="s")
    sc.cyl(u, 6.85, v, 1.1, 1.1, 0, "white", axis="s")
    sc.cyl(u + 1.3, 5.6, v + .4, .32, .32, 0, "pink", axis="s")
    for s_ in (-1, 1):
        sc.cyl(u + s_ * .6, 7.55, v, .38, .02, .7, "white", seg=6)
    # central planter: bed with a 0.6 m wall and the bench ring with diagonal gaps
    cx, cy = P(605, 417)
    sc.cyl(cx, 3.0, cy, 9.5, 9.5, 1.2, "conc", seg=48)
    sc.cyl(cx, 4.2, cy, 9.2, 9.2, .02, "bed", seg=48)
    ring = Point(cx, cy).buffer(13.5, quad_segs=24).difference(Point(cx, cy).buffer(11.2, quad_segs=24))
    seat = Point(cx, cy).buffer(11.2, quad_segs=24).difference(Point(cx, cy).buffer(9.5, quad_segs=24))
    cuts = unary_union([LineString([(cx - 20, cy - 20), (cx + 20, cy + 20)]).buffer(1.2),
                        LineString([(cx - 20, cy + 20), (cx + 20, cy - 20)]).buffer(1.2)])
    sc.prism(ring.difference(cuts), 3.4, 4.2, "bed")
    sc.prism(seat.difference(cuts), 3.4, 4.05, "timber")
    # pier: deck on posts, head
    body = Polygon(b.pier_rect(0, 34, -3.75, 3.75))
    head = Polygon(b.pier_rect(34, 45.5, -22, 5.2))
    sc.prism(unary_union([body, head]), 2.0, 2.4, "timber")
    sc.hard.append((unary_union([body, head]), 2.4))
    for t in range(2, 46, 4):
        for nn in (-3.4, 3.4) if t < 34 else (-21.5, -14, -7, 0, 4.8):
            x, z = b.pier_pt(t, nn)
            sc.cyl(x, -2.4, z, .2, .2, 4.4, "timber-2", seg=8)
    for (t0, t1, n0, n1) in ((0, 34, -3.85, -3.75), (0, 34, 3.75, 3.85)):
        q = Polygon(b.pier_rect(t0, t1, n0, n1))
        sc.prism(q, 3.45, 3.5, "dark")


def scene_data(b):
    sc = Scene(b)
    rec = record_plan(b)
    hs, idw = build_ground(sc, b)
    build_arcade(sc, b)
    build_cafe(sc, b)
    build_fashion(sc, b)
    build_lifestyle(sc, b)
    build_small(sc, b)
    build_props(sc, b, rec, idw)
    return sc.data()


def scene_json(b):
    return json.dumps(scene_data(b), separators=(",", ":"), ensure_ascii=False)
