"""Ori logo landmark at the centre of the plaza, in the spirit of the globe at Universal Studios Japan.

The logo (a thick ring with a bulb arm at the upper right, and a rounded "i" bar) stands on a round
plinth in a fountain basin with a low rail on the kerb and a ring of jets arcing in towards the plinth.
A planting ring fills the rest of the old Ø19 bed. The logo faces north, up the main stair, so it greets
people coming down from the gate. Shared by the plan (L-101), section A-A, D4 and the 3D model.
"""
import math

from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union

C = (90.833, 57.0)            # plaza centre, P(605, 417)
Z_PL = 3.6                    # plaza level
R_WATER, R_KERB, R_BED, R_WALL = 6.4, 6.9, 9.2, 9.5
Y_KERB, Y_WATER = 4.5, 4.25
R_PLINTH, R_DRUM = 3.0, 2.7
Y_PLINTH, Y_DRUM, Y_CAP = 4.85, 5.6, 5.7
R_JET0, R_JET1, H_JET, N_JET = 4.7, 3.35, 1.9, 12
DEPTH = .7                    # logo thickness
FACE = "N"


def logo_shape():
    """The logo in its own frame: x right, y up, baseline y = 0, centred on x = 0 (metres)."""
    rc, ro, ri = (0.0, 1.75), 1.75, .95
    ring = Point(rc).buffer(ro, quad_segs=24).difference(Point(rc).buffer(ri, quad_segs=24))
    a = math.radians(48)
    arm = LineString([(rc[0] + 1.3 * math.cos(a), rc[1] + 1.3 * math.sin(a)), (1.75, 3.2)]).buffer(.4, quad_segs=10)
    bulb = Point(1.95, 3.33).buffer(.56, quad_segs=16)
    foot = box(-.7, 0, .7, .3).intersection(Point(rc).buffer(ro + .4))
    o = unary_union([ring, arm, bulb, foot]).buffer(.06, quad_segs=8).buffer(-.06, quad_segs=8)
    bar = unary_union([LineString([(3.2, .3), (3.2, 2.6)]).buffer(.4, quad_segs=12), box(2.8, 0, 3.6, .5)])
    x0, x1 = -ro, 3.6
    dx = -(x0 + x1) / 2
    from shapely import affinity
    return [affinity.translate(o, dx), affinity.translate(bar, dx)]


def logo_size():
    parts = logo_shape()
    u = unary_union(parts)
    x0, y0, x1, y1 = u.bounds
    return x1 - x0, y1 - y0


def _ring(q):
    return [(round(x, 3), round(y, 3)) for x, y in list(q.coords)[:-1]]


def build_landmark(sc):
    cx, cz = C
    P = lambda r: Point(cx, cz).buffer(r, quad_segs=32)
    # basin: kerb ring with a granite coping, dark lining, round water surface, planting ring outside
    sc.prism(P(R_KERB).difference(P(R_WATER)), Z_PL - .6, Y_KERB - .06, "stone-w", "stone")
    sc.prism(P(R_KERB + .05).difference(P(R_WATER - .05)), Y_KERB - .06, Y_KERB, "cream", "stone")
    sc.prism(P(R_WATER), Z_PL - .3, Y_WATER - .45, "navy-d", "gloss")
    sc.label([cx, Y_WATER, cz], 0, 0, 0, "water", r=R_WATER)
    sc.prism(P(R_BED - .03).difference(P(R_KERB)), 3.0, 4.08, "bed", "ground")     # just inside the 24-sided bed wall
    # low rail on the kerb, posts every ~1.3 m
    n = 32
    rr = (R_WATER + R_KERB) / 2
    pts = [(cx + rr * math.cos(2 * math.pi * k / n), Y_KERB + .72, cz + rr * math.sin(2 * math.pi * k / n)) for k in range(n + 1)]
    sc.polyseg(pts, .035, "dark", "metal", 8)
    sc.polyseg([(x, y - .38, z) for x, y, z in pts], .022, "dark", "metal", 6)
    for x, y, z in pts[:-1]:
        sc.seg((x, Y_KERB, z), (x, y, z), .03, "dark", "metal", 8)
    # plinth: granite drum, deep purple drum with a lilac light band, white cap
    sc.cyl(cx, Y_WATER - .45, cz, R_PLINTH, R_PLINTH, Y_PLINTH - Y_WATER + .45, "stone-w", seg=48, mat="stone")
    sc.cyl(cx, Y_PLINTH - .02, cz, R_PLINTH + .08, R_PLINTH + .08, .07, "cream", seg=48, mat="stone")
    sc.cyl(cx, Y_PLINTH, cz, R_DRUM, R_DRUM, Y_DRUM - Y_PLINTH, "ori-p", seg=48, mat="gloss")
    sc.cyl(cx, Y_PLINTH + .22, cz, R_DRUM + .015, R_DRUM + .015, .07, "ori-l", seg=48, mat="led")
    sc.cyl(cx, Y_DRUM, cz, R_DRUM + .08, R_DRUM + .08, Y_CAP - Y_DRUM, "white", seg=48, mat="stone")
    # the logo: white body, glowing lilac face on both sides; mirrored so it reads from the north
    zf, zb = cz - DEPTH / 2, cz + DEPTH / 2
    for q in logo_shape():
        body = [(cx - x, Y_CAP + y) for x, y in _ring(q.exterior)]
        holes = [[(cx - x, Y_CAP + y) for x, y in _ring(h)] for h in q.interiors]
        sc.ext("xy", body, zf, DEPTH, "white", "gloss", .05, holes=holes)
        inl = q.buffer(-.13, quad_segs=8)
        for g in getattr(inl, "geoms", [inl]):
            ib = [(cx - x, Y_CAP + y) for x, y in _ring(g.exterior)]
            ih = [[(cx - x, Y_CAP + y) for x, y in _ring(h)] for h in g.interiors]
            sc.ext("xy", ib, zf - .035, .04, "ori-l", "led", 0, holes=ih)
            sc.ext("xy", ib, zb - .005, .04, "ori-l", "led", 0, holes=ih)
    # jets arcing in towards the plinth, with foam where they land
    for k in range(N_JET):
        a = 2 * math.pi * (k + .5) / N_JET
        ca, sa = math.cos(a), math.sin(a)
        arc = []
        for t in [i / 6 for i in range(7)]:
            r = R_JET0 + (R_JET1 - R_JET0) * t
            arc.append((cx + r * ca, Y_WATER + 4 * H_JET * t * (1 - t) * (1 - .25 * t), cz + r * sa))
        sc.polyseg(arc, .055, "jet", "jet", 8)
        sc.cyl(cx + R_JET0 * ca, Y_WATER - .02, cz + R_JET0 * sa, .16, .16, .05, "jet", seg=12, mat="jet")
        sc.cyl(cx + (R_JET1 - .08) * ca, Y_WATER - .02, cz + (R_JET1 - .08) * sa, .3, .3, .05, "white", seg=14, mat="jet")
    # planting ring: low shrubs, kept clear of the rail
    k = 0
    for rr_, nn in ((7.55, 26), (8.5, 30)):
        for i in range(nn):
            a = 2 * math.pi * (i + .5 * (k % 2)) / nn
            sc.shrubs.append([round(cx + rr_ * math.cos(a), 2), 4.06, round(cz + rr_ * math.sin(a), 2), .42 if rr_ < 8 else .5])
        k += 1
    # purple uplights on the logo and a soft light in the basin
    for (dx, dz, col, i_) in ((0, -4.2, "#B48CFF", 10), (0, 4.2, "#B48CFF", 8), (0, 0, "#E6D8FF", 6)):
        sc.lights.append([cx + dx, Y_CAP + (.8 if dz else 4.6), cz + dz, col, i_, 9.0])


# ---------------------------------------------------------------- 2D helpers (plan, D4)
def logo_plan_rect():
    w, _ = logo_size()
    cx, cz = C
    return (cx - w / 2, cz - DEPTH / 2, cx + w / 2, cz + DEPTH / 2)
