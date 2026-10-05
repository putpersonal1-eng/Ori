#!/usr/bin/env python3
"""Japan Coastal Hangout Park - scale-corrected layout of the reference top view.

The reference (reference.webp) is an image-gen map whose scale bar disagrees
with its own contents. Measured against people, food trucks and buildings it
reads at about 6 px per metre, so plan coordinates here come from
X = (px - 60) / 6 and Y = (py - 75) / 6, then each element is resized to real
metrics (see CORRECTIONS).

Geometry is in metres: X west -> east, Y north -> south, Z above sea level.

    python3 build.py   -> index.html + svg/*.svg
"""
import base64
import math
import os
import random
import sys

from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from drawkit import *  # noqa: E402,F401,F403

HERE = os.path.dirname(os.path.abspath(__file__))

# Levels
Z_STREET, Z_PLAZA, Z_STAGE, Z_PIER, Z_BEACH = 8.4, 3.6, 4.2, 2.4, 1.2

SHORE = [("M", 172, 106), ("C", 152, 122, 110, 135, 40, 134)]
WADE = [("M", 184, 114), ("C", 162, 134, 112, 150, 40, 148)]
CURVED_PATH = [("M", 150, 36), ("C", 156, 52, 162, 70, 173, 87)]
COAST_WALK = [("M", 192, 57), ("C", 188, 66, 186, 80, 177, 93)]


def sector(cx, cy, r0, r1, a0, a1, steps=28):
    pts = []
    for i in range(steps + 1):
        a = math.radians(a0 + (a1 - a0) * i / steps)
        pts.append((cx + r1 * math.cos(a), cy + r1 * math.sin(a)))
    for i in range(steps, -1, -1):
        a = math.radians(a0 + (a1 - a0) * i / steps)
        pts.append((cx + r0 * math.cos(a), cy + r0 * math.sin(a)))
    return pts


def key(cv, u, v, num):
    cv.circle(u, v, 2.4, "key")
    cv.text(u, v + .95, str(num), "t-lbl t-inv")


# ================================================================ L-101 PLAN
# Every outline below is traced from reference.webp in image pixels and
# converted with P(): X = (px - 60) / 6, Y = (py - 75) / 6  (true scale 6 px = 1 m).
S = 6
X0, Y0, X1, Y1 = -4, -12, 207, 158          # drawing frame (m)
OX, OY = 56, 56                              # frame origin on the sheet (px)


def P(x, y):
    return ((x - 60) / 6, (y - 75) / 6)


def PP(pts):
    return [P(x, y) for x, y in pts]


def M(px):
    return px / 6


def RP(x0, y0, x1, y1):
    a, b = P(x0, y0), P(x1, y1)
    return (a[0], a[1], b[0], b[1])


def G(px_pts):
    return Polygon(PP(px_pts))


def GB(x0, y0, x1, y1):
    q = RP(x0, y0, x1, y1)
    return box(min(q[0], q[2]), min(q[1], q[3]), max(q[0], q[2]), max(q[1], q[3]))


def GL(px_pts, half, per=10):
    return LineString(cr_sample(PP(px_pts), per=per)).buffer(half, cap_style="flat", join_style="round", quad_segs=12)


def close_(g, r):
    """Fillet concave corners (where paths meet) with radius r."""
    return g.buffer(r, quad_segs=12).buffer(-r, quad_segs=12)


def open_(g, r):
    """Round convex corners with radius r."""
    return g.buffer(-r, quad_segs=8, join_style="mitre").buffer(r, quad_segs=8)


def gpath(cv, g):
    polys = [g] if g.geom_type == "Polygon" else [q for q in getattr(g, "geoms", []) if q.geom_type == "Polygon"]
    d = []
    for pg in polys:
        if pg.is_empty:
            continue
        for ring in [pg.exterior] + list(pg.interiors):
            d.append("M" + "L".join(f"{n(cv.X(x))} {n(cv.Y(y))}" for x, y in ring.coords) + "Z")
    return " ".join(d)


def gd(cv, g, cls, extra=""):
    if g is None or g.is_empty:
        return
    cv.add(f'<path d="{gpath(cv, g)}" class="{cls}" fill-rule="evenodd"{extra}/>')


def scatter_shrubs(cv, g, seed, density=.6, rmin=.5, rmax=1.0):
    if g.is_empty:
        return
    rnd = random.Random(seed)
    x0, y0, x1, y1 = g.bounds
    want = int(g.area * density / 3) + 1
    got = 0
    for _ in range(want * 30):
        if got >= want:
            break
        pt = (rnd.uniform(x0, x1), rnd.uniform(y0, y1))
        r = rnd.uniform(rmin, rmax)
        if g.buffer(-r * .6).contains(Point(pt)):
            canopy(cv, pt[0], pt[1], r, seed * 100 + got, "shrub", shadow=False, detail=False)
            got += 1


def bed_g(cv, g, seed, density=.55, rmin=.6, rmax=1.1):
    gd(cv, g, "bed")
    scatter_shrubs(cv, g, seed, density, rmin, rmax)


def planter_g(cv, g, seed, density=.8, rmin=.4, rmax=.8, wall=.3, radius=.35):
    """Raised planter: rounded outline, 0.3 m wall in poché, shrubs inside."""
    g = open_(g, radius) if radius else g
    inner = g.buffer(-wall, join_style="mitre")
    gd(cv, g.difference(inner), "wallp")
    gd(cv, inner, "bed")
    scatter_shrubs(cv, inner, seed, density, rmin, rmax)
    return inner


def wall_line(cv, px_pts, t=.4):
    gd(cv, LineString(PP(px_pts)).buffer(t / 2, cap_style="flat", join_style="mitre"), "wallp")


def edge_y(x):
    """Shared plaza/promenade edge (reference px)."""
    pts = [(142, 592), (347, 592), (520, 594), (1022, 598)]
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        if xa <= x <= xb:
            return ya + (yb - ya) * (x - xa) / (xb - xa)
    return pts[-1][1]


# ---- traced outlines (reference px) ----
SHORE_PX = [(150, 868), (260, 880), (350, 886), (450, 893), (550, 895), (614, 892), (700, 880), (780, 860),
            (844, 832), (945, 795), (1000, 775), (1045, 757), (1066, 750)]
COAST_PX = [(1302, 404), (1248, 410), (1243, 450), (1238, 490), (1232, 525), (1215, 555), (1198, 585),
            (1178, 612), (1170, 640), (1176, 665), (1188, 682)]
SEAWALL_PX = [(1038.8, 637), (875, 637), (840, 654), (836, 655), (770, 655), (764, 672), (452.5, 675), (382.5, 675),
              (170, 635)]
PROM_PX = [(142, 592), (347, 592), (520, 594), (1022, 598), (1033, 614.5)] + SEAWALL_PX + [(142, 630)]
CURVE_LINE_PX = [(974, 197), (974, 250), (976, 300), (986, 338), (1004, 370), (1031, 405), (1060, 434), (1084, 460),
                 (1102, 490), (1122, 522)]
COAST_LINE_PX = [(1186, 461), (1189, 495), (1180, 520), (1158, 542), (1132, 556)]
EAST_PATH_PX = [(1238.5, 145), (1238.5, 330), (1232, 365), (1218, 395), (1200, 414)]
CURVED_STAIR_PX = [(1153, 432), (1188, 421), (1204, 451), (1167, 463)]
SAKURA_PLANTER_PX = [(1112, 450), (1146, 443), (1158, 452), (1162, 480), (1159, 505), (1140, 513), (1115, 500), (1108, 475)]
PALM_ISLAND_PX = [(1060, 478), (1085, 470), (1103, 482), (1104, 515), (1098, 545), (1080, 552), (1062, 540), (1056, 505)]
CURVE_PX = [(980, 192), (983, 260), (987, 330), (1010, 372), (1037, 405), (1063, 447), (1090, 490), (1106, 528),
            (1098, 562)]
COASTWALK_PX = [(1182, 462), (1176, 490), (1160, 520), (1140, 548), (1108, 572)]
DECK_PX = [(1100, 190), (1207, 237), (1163, 320), (1107, 307), (1050, 292), (1050, 252)]
LAWN_DECK_PX = [(1048, 292), (1107, 307), (1168, 320)]          # straight: the deck's front edges
LAWN_EAST_PX = [(1168, 320), (1185, 334), (1200, 350), (1207, 368), (1207, 388), (1200, 405), (1188, 421)]
LAWN_WEST_PX = [(1153, 432), (1133, 427), (1110, 418), (1090, 407), (1067, 387), (1047, 363), (1033, 337), (1030, 317),
                (1036, 302), (1048, 292)]                     # stone curb, 5 m planted bank to the curved path
WEST_ROCK_PX = [(36, 690), (60, 700), (110, 705), (160, 720), (175, 760), (160, 820), (165, 870), (200, 900),
                (255, 930), (250, 1000), (220, 1023), (36, 1023)]
EAST_ROCK_PX = [(1112, 700), (1150, 668), (1195, 672), (1215, 700), (1205, 740), (1170, 762), (1128, 758)]
BOULDERS_W = [(15, 735, 25), (50, 745, 27), (95, 735, 27), (135, 765, 30), (90, 790, 25), (115, 825, 20),
              (150, 837, 17), (90, 850, 20), (130, 870, 20), (100, 885, 17), (135, 900, 22), (85, 930, 22),
              (175, 920, 30), (210, 920, 20), (240, 930, 17), (115, 940, 17), (160, 960, 22), (200, 960, 20),
              (110, 975, 15), (200, 990, 17), (235, 985, 12), (60, 800, 22), (40, 860, 24), (55, 905, 20),
              (45, 960, 22), (70, 1005, 18), (140, 1005, 16)]
ROCKS_SAND = [(210, 780, 9), (222, 786, 7), (240, 855, 24), (175, 847, 11), (203, 773, 6)]
BOULDERS_E = [(1185, 680, 20), (1160, 705, 20), (1135, 730, 19), (1190, 720, 15), (1170, 742, 15),
              (1125, 750, 12), (1205, 697, 12), (1150, 685, 10)]
ROCKS_SEA_E = [(1252, 571, 10), (1252, 594, 15), (1220, 590, 14)]
PIER_O = P(1065, 647.5)
PIER_ANG = 15.0


def lawn_poly():
    pts = PP(LAWN_DECK_PX[:-1]) + cr_sample(PP(LAWN_EAST_PX), per=8) + cr_sample(PP(LAWN_WEST_PX), per=8)[:-1]
    return Polygon(pts).buffer(0)


def lawn_curb_pts():
    return cr_sample(PP(LAWN_WEST_PX), per=8)


def pier_pt(t, nn):
    a = math.radians(PIER_ANG)
    d = (math.sin(a), math.cos(a))
    nr = (math.cos(a), -math.sin(a))
    return (PIER_O[0] + t * d[0] + nn * nr[0], PIER_O[1] + t * d[1] + nn * nr[1])


def pier_rect(t0, t1, n0, n1):
    return [pier_pt(t0, n0), pier_pt(t0, n1), pier_pt(t1, n1), pier_pt(t1, n0)]


def rrect(cx, cy, L, Wd, ang):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in
            [(-L / 2, -Wd / 2), (L / 2, -Wd / 2), (L / 2, Wd / 2), (-L / 2, Wd / 2)]]


def quad_treads(cv, q, count, fill="z-paver"):
    a, b, c, d = q
    cv.poly(q, fill)
    for i in range(count + 1):
        t = i / count
        cv.line(a[0] + (d[0] - a[0]) * t, a[1] + (d[1] - a[1]) * t, b[0] + (c[0] - b[0]) * t, b[1] + (c[1] - b[1]) * t, "tread")
    cv.poly(q, "ln")


def quad_stair(cv, q, risers, label=None, cheek=(.3, .6)):
    """Stair in a traced quad (a-b top, d-c foot): one nosing line per riser, poché cheek walls, DN arrow."""
    a, b, c, d = q
    cv.poly(q, "z-paver")
    n = risers - 1
    for i in range(risers):
        t = i / n
        cv.line(a[0] + (d[0] - a[0]) * t, a[1] + (d[1] - a[1]) * t, b[0] + (c[0] - b[0]) * t, b[1] + (c[1] - b[1]) * t, "tread")
    body = Polygon(q)
    for (p0, p1), w in zip(((a, d), (b, c)), cheek):
        gd(cv, body.intersection(LineString([p0, p1]).buffer(w, cap_style="flat")), "wallp")
    cv.poly(q, "ln")
    if label:
        m0 = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        m1 = ((d[0] + c[0]) / 2, (d[1] + c[1]) / 2)
        k = .12
        cv.line(m0[0] + (m1[0] - m0[0]) * k, m0[1] + (m1[1] - m0[1]) * k, m1[0] - (m1[0] - m0[0]) * k,
                m1[1] - (m1[1] - m0[1]) * k, "ln", ' marker-end="url(#cp-arrk)"')


def stair_ns(cv, x0, y0, x1, y1, flights, landing=0.0, cheek=True, rails=(), label=None):
    """N-S stair in a rectangle (metres): treads fill the run, 0.3 m cheek walls, DN arrow and riser count."""
    cv.rect(x0, y0, x1, y1, "z-paver")
    run = (y1 - y0) - landing * (len(flights) - 1)
    tr = run / sum(f - 1 for f in flights)
    y = y0
    for i, f in enumerate(flights):
        for k in range(f):
            cv.line(x0, y + k * tr, x1, y + k * tr, "tread")
        y += (f - 1) * tr
        if i < len(flights) - 1:
            y += landing
    for x in rails:
        cv.line(x, y0 + .2, x, y1 - .2, "rail")
    if cheek:
        cv.rect(x0, y0, x0 + .3, y1, "wallp")
        cv.rect(x1 - .3, y0, x1, y1, "wallp")
    cv.rect(x0, y0, x1, y1, "ln")
    if label:
        xm = (x0 + x1) / 2 + (.9 if rails and abs(rails[0] - (x0 + x1) / 2) < .5 else 0)
        cv.line(xm, y0 + .6, xm, y1 - .6, "ln", ' marker-end="url(#cp-arrk)"')
        cv.text(xm + .5, y0 + 1.4, label, "t-sm halo", "start")


def truck_r(cv, cx, cy, ang, cls_stripe, L=6.5, Wd=2.5):
    body = rrect(cx, cy, L, Wd, ang)
    cv.poly([(x + .5, y - .5) for x, y in body], "shadow")
    cv.poly(body, "bldg-l")
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    cab = rrect(cx + (L / 2 - .85) * ca, cy + (L / 2 - .85) * sa, 1.5, Wd - .3, ang)
    cv.poly(cab, "roof-2")
    aw = rrect(cx - .6 * ca - (Wd / 2 + .55) * sa, cy - .6 * sa + (Wd / 2 + .55) * ca, L - 2.4, 1.1, ang)
    cv.poly(aw, "", f' fill="url(#cp-{cls_stripe})"')
    cv.poly(aw, "ln-m")


def maneki_big(cv, u, v, r):
    cv.circle(u, v, r, "prop")
    cv.ellipse(u, v + r * .2, r * .62, r * .5, "statue")
    cv.circle(u, v - r * .38, r * .42, "statue")
    for s_ in (-1, 1):
        cv.poly([(u + s_ * r * .38, v - r * .62), (u + s_ * r * .25, v - r * .95), (u + s_ * r * .1, v - r * .7)], "statue")
    cv.circle(u + r * .52, v - r * .1, r * .16, "chalk-p")
    cv.circle(u, v + r * .05, r * .12, "chalk-p")


def site_plan(underlay=False):
    p = "cp"
    W, H = 1630, 1110
    cv = Cv(S, S, OX, OY, X0, Y0)
    A = cv.add
    A(defs(p))
    A(f'<rect class="sheet-bg" width="{W}" height="{H}"/>')

    def pat(name):
        return f' fill="url(#{p}-{name})"'

    A(f'<clipPath id="{p}-frm"><rect x="{n(cv.X(X0))}" y="{n(cv.Y(Y0))}" width="{n((X1 - X0) * S)}" height="{n((Y1 - Y0) * S)}"/></clipPath>')
    sh = cr_sample(PP(SHORE_PX), per=8)
    wade = offset_pts(sh, -15)
    deep = offset_pts(sh, -27)
    coast = cr_sample(PP(COAST_PX), per=6)
    curve = cr_sample(PP(CURVE_PX), per=10)
    prom = PP(PROM_PX)

    # ================================================================ ground
    A(f'<g id="lyr-zones" clip-path="url(#{p}-frm)">')
    cv.rect(X0, 50, X1, Y1, "z-deep")
    cv.poly(wade + deep[::-1], "z-mid")
    cv.poly(sh + wade[::-1], "z-sea")
    cv.rect(X0, 50, X1, Y1, "", pat("water"))
    cv.pline(wade, "ln-f", ' stroke-dasharray="5 3"')
    cv.pline(deep, "ln-f", ' stroke-dasharray="2 4"')
    land = [(X0, Y0), (X1, Y0)] + coast + PP([(1150, 700), (1100, 712), (1087, 700), (1087, 647), (1043, 653)]) + \
        PP(SEAWALL_PX) + PP([(55, 700), (36, 700)])
    cv.poly(land, "z-lawn")
    cv.poly(land, "", pat("lawn"))
    sand = PP([(170, 635), (382.5, 675), (452.5, 675), (764, 672), (770, 655), (836, 655), (840, 654), (875, 637),
               (1038.8, 637), (1043, 653), (1090, 648), (1100, 712), (1068, 752)]) + sh[::-1] + \
        PP([(150, 820), (160, 760), (175, 700), (170, 640)])
    cv.poly(sand, "z-sand")
    cv.poly(sand, "", pat("sand"))
    sand_e = PP([(1087, 647), (1170, 640), (1176, 665), (1188, 682), (1150, 690), (1118, 704), (1100, 712), (1090, 700)])
    cv.poly(sand_e, "z-sand")
    cv.poly(sand_e, "", pat("sand"))
    cv.poly(sh + offset_pts(sh, 2.4)[::-1], "z-wet")
    cv.pline(sh, "ln-water")
    cv.pline(wobble(offset_pts(sh, -.8), .35, 1.2, 3), "foam")
    cv.pline(wobble(offset_pts(sh, -2.4), .55, .7, 9), "foam-d")
    cv.pline(wobble(offset_pts(sh, -4.6), .7, .5, 21), "foam-d")
    # town, roads, sidewalks
    cv.rect(*RP(36, -9, 1302, 80), "z-town")
    cv.rect(*RP(36, -9, 1302, 80), "", pat("hatch"))
    for b in [(40, -6, 300, 70), (310, -6, 540, 70), (668, -6, 826, 70), (836, -6, 1000, 90), (1010, -6, 1120, 70),
              (1130, -6, 1298, 70)]:
        cv.rect(*RP(*b), "roof")
        q = RP(*b)
        cv.line(q[0], (q[1] + q[3]) / 2, q[2], (q[1] + q[3]) / 2, "ln-m")
    cv.rect(*RP(546, -9, 663, 95), "z-road")
    cv.line(*P(605, -9), *P(605, 95), "lane")
    cv.rect(*RP(36, 80, 1302, 95), "z-paver")
    cv.rect(*RP(36, 95, 1302, 135), "z-road")
    cv.line(*P(36, 115), *P(546, 115), "lane")
    cv.line(*P(663, 115), *P(1302, 115), "lane")
    for x0, x1 in [(567, 640), (1069, 1095)]:
        for x in frange(x0 + 2, x1, 7):
            cv.rect(*RP(x, 98, x + 3.5, 132), "zebra")
    cv.rect(*RP(36, 135, 1302, 145), "z-paver")
    cv.line(*P(36, 135), *P(1302, 135), "ln")
    cv.line(*P(36, 95), *P(1302, 95), "ln-m")
    # non-playable edges
    for b in [(36, 145, 55, 700), (1250, 140, 1302, 330)]:
        cv.rect(*RP(*b), "z-town")
        cv.rect(*RP(*b), "", pat("hatch"))
    cv.rect(*RP(1252, 142, 1300, 328), "roof")
    # ---- hardscape: one surface per level, filleted junctions, one curb line ----
    street_g = close_(unary_union([
        GB(36, 135, 1302, 145), GB(470, 135, 727, 186), GB(88, 135, 392, 196), open_(GB(88, 135, 142, 632), 1.6), GB(120, 600, 142, 632),
        GB(677, 184, 703, 217), GB(940, 140, 972, 155), GB(1060, 140, 1090, 165)]), 1.2)
    plaza_core = G([(347, 197), (478, 197), (478, 186), (727, 186), (727, 192), (974, 192), (974, 250), (976, 300), (986, 338),
                    (1004, 370), (1031, 405), (1060, 434), (1060, 478), (1056, 505), (1062, 540), (1050, 553), (1022, 598),
                    (520, 594), (347, 592)])
    junction = G([(1050, 553), (1080, 546), (1100, 546), (1106, 520), (1125, 516), (1160, 512), (1172, 524), (1197, 527),
                  (1163, 550), (1130, 557), (1088, 572), (1082, 588), (1083, 600), (1076.3, 602.9), (1033, 614.5), (1020, 600),
                  (1030, 575)])
    plaza_g = close_(unary_union([plaza_core, GL(CURVE_LINE_PX, 3.25), GB(730, 192, 995, 217), GB(733, 217, 942, 312),
                                  junction, GL(COAST_LINE_PX, 3.1)]), 2.0)
    east_g = close_(unary_union([GL(EAST_PATH_PX, 1.2), G([(1188, 410), (1206, 404), (1210, 418), (1195, 422)])]), .8)
    island = G(PALM_ISLAND_PX)
    plaza_g = unary_union([plaza_g, east_g, island.buffer(2.5)]).difference(island)
    top_g = close_(G([(1050, 200), (1094, 200), (1100, 190), (1050, 252)]), .6)
    prom_g = G(PROM_PX)
    terr_g = G([(282, 485), (347, 485), (347, 592), (160, 592), (160, 540), (282, 540)])
    lawn_g = lawn_poly().difference(plaza_g).difference(top_g)
    deck_g = G(DECK_PX)
    paved = unary_union([street_g, plaza_g, top_g])
    for g in (street_g, plaza_g.difference(prom_g), top_g):
        gd(cv, g, "z-paver")
    cx, cy = P(605, 417)
    for i, (u, v, rx, ry, c) in enumerate([(403, 474, 17, 18, "chalk-c"), (498, 453, 14, 18, "chalk-y"),
                                           (715, 486, 25, 24, "chalk-p"), (722, 478, 10, 9, "chalk-c")]):
        q = P(u, v)
        cv.path(cr_cmds(blob(q[0], q[1], M(rx), M(ry), 40 + i, .3, 9)), c, ' fill-opacity=".42"')
    # lawn + planting beds trimmed exactly to the curb lines
    gd(cv, lawn_g, "z-lawn")
    gd(cv, lawn_g, "", f' fill="url(#{p}-lawn)"')
    for arc in [[(1052, 312), (1072, 352), (1105, 386), (1145, 404), (1182, 392), (1204, 360)],
                [(1078, 322), (1098, 350), (1128, 368), (1162, 366), (1186, 344)]]:
        cv.path(cr_cmds(PP(arc), closed=False), "ln-m", ' stroke-dasharray="1.2 2.6"')
    beds = [
        (G([(990, 145), (1060, 145), (1060, 200), (1047.5, 200), (1047.5, 292.5), (1032.5, 305), (1030, 330), (1042.5, 360),
            (1065, 390), (1090, 410), (1120, 422.5), (1150, 430), (1164, 424), (1150, 445), (1110, 445), (1060, 420), (1020, 380),
            (1000, 330), (995, 250), (990, 200)]), 13),
        (G([(1092, 150), (1207, 150), (1207, 237), (1100, 190), (1094, 200), (1092, 200)]), 14),
        (G([(1207, 145), (1250, 145), (1250, 335), (1302, 290), (1302, 404), (1248, 410), (1243, 430), (1212, 425), (1207, 400)]), 15),
        (G([(1080, 572), (1130, 557), (1163, 551), (1197, 528), (1215, 555), (1198, 585), (1176, 612), (1166, 636),
            (1086.7, 641.7), (1076.3, 602.9), (1083, 600)]), 17),
        (G([(1104, 402), (1148, 408), (1150, 430), (1112, 450), (1095, 448)]), 18),
        (G([(1207, 425), (1243, 430), (1238, 490), (1232, 525), (1215, 555), (1197, 528), (1209, 500), (1207, 460)]), 19),
        (GB(55, 145, 88, 640), 20), (GB(1160, 230, 1212, 425), 16), (GB(142, 540, 160, 592), 21), (GB(423, 145, 470, 196), 22)]
    # one bed surface: neighbouring beds merge, so no seams between them
    bed_all = unary_union([g for g, sd in beds]).difference(paved).difference(prom_g).difference(lawn_g).difference(deck_g)
    bed_g(cv, bed_all, 13)
    # timber decks
    for g in (prom_g, terr_g):
        gd(cv, g, "z-timber")
        gd(cv, g, "", f' fill="url(#{p}-board)"')
    gd(cv, GB(93, 153, 140, 207), "z-timber")
    gd(cv, GB(93, 153, 140, 207), "", f' fill="url(#{p}-board)"')
    truck_deck = open_(GB(733, 219, 770, 302), 1.2)
    gd(cv, truck_deck, "z-timber")
    gd(cv, truck_deck, "", f' fill="url(#{p}-board)"')
    gd(cv, GB(770, 217, 942, 302), "z-road")
    gd(cv, deck_g, "z-timber")
    deck = PP(DECK_PX)
    a_, b_ = deck[0], deck[1]
    ux, uy = (b_[0] - a_[0]), (b_[1] - a_[1])
    L_ = math.hypot(ux, uy)
    ux, uy = ux / L_, uy / L_
    A(f'<clipPath id="{p}-deck"><path d="{gpath(cv, deck_g)}"/></clipPath>')
    A(f'<g clip-path="url(#{p}-deck)">')
    for k in range(0, 40):
        ox_, oy_ = a_[0] - uy * k * 1.0, a_[1] + ux * k * 1.0
        cv.line(ox_ - ux * 10, oy_ - uy * 10, ox_ + ux * 40, oy_ + uy * 40, "pat-s")
    A('</g>')
    # deck edge steps (0.60 m in 4 risers) along the top-plaza edge and the lawn edge
    for (pa, pb) in [(deck[0], deck[5]), (deck[4], deck[3]), (deck[3], deck[2])]:
        dx, dy = pb[0] - pa[0], pb[1] - pa[1]
        L = math.hypot(dx, dy)
        nx, ny = -dy / L, dx / L
        mid = ((pa[0] + pb[0]) / 2 + nx * .5, (pa[1] + pb[1]) / 2 + ny * .5)
        if not deck_g.contains(Point(mid)):
            nx, ny = -nx, -ny
        for k in (1, 2, 3):
            o = k * .45
            seg = LineString([(pa[0] + nx * o, pa[1] + ny * o), (pb[0] + nx * o, pb[1] + ny * o)]).intersection(deck_g)
            if not seg.is_empty and seg.geom_type == "LineString":
                (x0_, y0_), (x1_, y1_) = seg.coords[0], seg.coords[-1]
                cv.line(x0_, y0_, x1_, y1_, "tread")
    # curb lines: drawn once per surface, after everything that touches them
    for g in (street_g, plaza_g.difference(prom_g), top_g):
        gd(cv, g, "curb")
    for g in (prom_g, terr_g, deck_g, truck_deck):
        gd(cv, g, "ln")
    gd(cv, lawn_g, "ln-m")
    # rocks
    cv.poly(PP(WEST_ROCK_PX), "z-wet")
    cv.poly(PP(WEST_ROCK_PX), "", pat("sand"))
    for i, (x, y, r) in enumerate(sorted(BOULDERS_W, key=lambda q: -q[2])):
        u, v = P(x, y)
        rock(cv, u, v, M(r), 700 + i, foam=y > 880)
    for i, (x, y, r) in enumerate(ROCKS_SAND):
        u, v = P(x, y)
        rock(cv, u, v, M(r), 760 + i)
    for i, (x, y, r) in enumerate(sorted(BOULDERS_E, key=lambda q: -q[2])):
        u, v = P(x, y)
        rock(cv, u, v, M(r), 800 + i, foam=True)
    for i, (x, y, r) in enumerate(ROCKS_SEA_E):
        u, v = P(x, y)
        rock(cv, u, v, M(r), 830 + i, foam=True)
    rr = offset_pts(cr_sample(PP(COAST_PX[1:]), per=10), -1.2)
    for i in range(0, len(rr), 2):
        u, v = rr[i]
        rock(cv, u, v, .6 + (i * 37 % 10) / 12, 900 + i, shadow=False)
    A('</g>')

    # ================================================================ built
    A(f'<g id="lyr-built" clip-path="url(#{p}-frm)">')
    # retaining walls along the street edge (0.40 m, poché), openings exactly at the stairs
    for seg in [[(347.5, 196), (392, 196)], [(423, 196), (470, 196), (470, 186), (565, 186)], [(642, 186), (677, 186)],
                [(703, 186), (727, 186), (727, 192), (940, 192)], [(972, 192), (992, 192)], [(972, 149), (1058, 149)],
                [(1092, 149), (1207, 149)], [(1246.5, 145), (1246.5, 335)]]:
        wall_line(cv, seg)
    railing(cv, PP([(470, 184), (565, 184)]), 2)
    railing(cv, PP([(642, 184), (677, 184)]), 2)
    railing(cv, PP([(703, 184), (727, 184)]), 2)
    railing(cv, PP([(347.5, 194), (392, 194)]), 2.2)
    # kiosks
    for i, b in enumerate([(140, 145, 177, 178), (177, 152, 243, 180), (243, 155, 273, 180)]):
        q = RP(*b)
        cv.rect(q[0], q[1] + 1.2, q[2], q[3], "roof")
        cv.rect(q[0], q[1], q[2], q[1] + 1.2, "", pat(("stripe", "stripey", "stripec")[i]))
        cv.rect(q[0], q[1], q[2], q[1] + 1.2, "ln-m")
        cv.line(q[0], (q[1] + q[3]) / 2 + .6, q[2], (q[1] + q[3]) / 2 + .6, "ln-m")
    for (x, y) in [(105, 170), (125, 172), (105, 192), (125, 194)]:
        u, v = P(x, y)
        parasol(cv, u, v, .9, "umb-y", chairs=3, ribs=6)
    # stairs (risers fitted to the traced footprints), cheek walls tie into the retaining wall
    stair_ns(cv, *RP(565, 186, 642, 287), (16, 16), landing=3.1, rails=(P(591, 0)[0], P(616, 0)[0]), label="DN 2 × 16R")
    stair_ns(cv, *RP(392, 145, 423, 197), (32,), rails=(P(407.5, 0)[0],), label="DN 32R")
    stair_ns(cv, *RP(677, 217, 703, 273), (32,), rails=(P(690, 0)[0],), label="DN 32R")
    stair_ns(cv, *RP(940, 155, 972, 192), (20,), label="DN 20R")
    stair_ns(cv, *RP(1058, 149, 1092, 198), (20,), label="DN 20R")
    quad_stair(cv, PP(CURVED_STAIR_PX), 11, label=True)
    gd(cv, LineString(lawn_curb_pts()).buffer(.15, cap_style="flat", join_style="mitre"), "wallp")
    planter_g(cv, G(SAKURA_PLANTER_PX), 140, density=.4, radius=0)
    planter_g(cv, G(PALM_ISLAND_PX), 141, density=.5, radius=0)
    planter_g(cv, LineString(PP([(980, 382), (1000, 402), (1028, 432), (1050, 452)])).buffer(1.1), 142, density=.6, radius=0)
    # planters by the main stair (raised, walled), terrace bench, art block
    planter_g(cv, G([(478, 188), (565, 188), (565, 287), (552, 287), (552, 236), (478, 236)]), 21, density=.5, radius=0)
    cv.poly(rrect(*P(496, 258), M(44), 1.1, 59), "umb-c")
    cv.poly(rrect(*P(496, 258), M(44), 1.1, 59), "ln-m")
    for i, b_ in enumerate([(642, 188, 677, 217), (703, 188, 727, 287), (643, 240, 677, 287)]):
        planter_g(cv, GB(*b_), 30 + i, density=.6, radius=0)
    cv.rect(*RP(643, 217, 677, 240), "chalk-y", ' fill-opacity=".6"')
    cv.rect(*RP(643, 217, 677, 240), "ln-m")
    for i, b_ in enumerate([(730, 147, 940, 189), (280, 147, 390, 178), (142, 182, 222, 193), (248, 182, 392, 193), (112, 210, 140, 305),
                            (733, 303, 940, 312), (828, 383, 841, 427)]):
        planter_g(cv, GB(*b_), 40 + i, density=.55)
    # fashion & goods: roof plan + east stair
    q = RP(142.5, 195, 347.5, 300)
    cv.rect(q[0] + 1.5, q[1] - 1.5, q[2] + 1.5, q[3] - 1.5, "shadow")
    cv.rect(*q, "roof")
    cv.rect(q[0] + .6, q[1] + .6, q[2] - .6, q[3] - .6, "ln-m")
    cv.rect(*RP(142.5, 195, 347.5, 217), "roof-2")
    cv.rect(*RP(270, 200, 345, 230), "z-paver")
    for x in frange(P(150, 0)[0], P(260, 0)[0], 2.6):
        cv.rect(x, P(0, 200)[1], x + 1.6, P(0, 212)[1], "prop")
    stair_ns(cv, *RP(315, 262, 345, 300), (16,))
    # arcade: interior (roof removed), traced cabinet blocks
    q = RP(142.5, 302.5, 347.5, 465)
    cv.rect(*q, "arc-y")
    cv.rect(*q, "wall6")
    for b in [(187, 355, 201, 440), (203, 355, 217, 440), (250, 345, 270, 435), (280, 345, 300, 435), (145, 355, 160, 405),
              (310, 345, 345, 450), (245, 440, 320, 460), (155, 322, 205, 345)]:
        qb = RP(*b)
        cv.rect(*qb, "prop")
        if b[3] - b[1] > 60:
            for y in frange(qb[1] + 1.2, qb[3], 2.4):
                cv.line(qb[0], y, qb[2], y, "ln-f")
    for (x, y) in [(194, 370), (210, 395), (260, 360), (290, 410), (327, 380), (277, 450)]:
        u, v = P(x, y)
        cv.circle(u, v, .5, ("chalk-p", "chalk-c")[x % 2])
    cv.line(*P(226, 195.5), *P(244, 195.5), "gap")
    cv.line(*P(226, 195.5), *P(244, 195.5), "glass")
    st = RP(347.5, 333, 354.7, 438)
    cv.rect(*st, "z-paver")
    for k in range(4):
        cv.line(st[0] + k * .4, st[1], st[0] + k * .4, st[3], "tread" if 0 < k < 3 else "ln-m")
    cv.line(*P(347.5, 370), *P(347.5, 400), "gap")
    cv.line(*P(347.5, 370), *P(347.5, 400), "glass")
    door_swing(cv, *P(347.5, 370), 2.0, 0, 90)
    door_swing(cv, *P(347.5, 400), 2.0, 0, -90)
    # strip shops + café roof + L terrace
    q = RP(142.5, 465, 347.5, 485)
    cv.rect(*q, "roof")
    for x in frange(q[0], q[2], 4.2):
        cv.line(x, q[1], x, q[3], "ln-m")
    terr = PP([(282, 485), (347, 485), (347, 592), (160, 592), (160, 540), (282, 540)])
    cv.poly(terr, "z-timber")
    cv.poly(terr, "", pat("board"))
    cv.poly(terr, "ln")
    q = RP(142.5, 485, 282.5, 540)
    cv.rect(q[0] + 1.4, q[1] - 1.4, q[2] + 1.4, q[3] - 1.4, "shadow")
    cv.rect(*q, "roof")
    cv.rect(q[0] + .6, q[1] + .6, q[2] - .6, q[3] - .6, "ln-m")
    cv.rect(*RP(162, 540, 282, 555), "chalk-y", ' fill-opacity=".5"')
    for i, (x, y) in enumerate([(187, 548), (240, 560), (300, 537), (318, 575), (205, 578)]):
        u, v = P(x, y)
        parasol(cv, u, v, 1.5, ("umb-y", "umb-y", "umb-c", "umb-p", "umb-y")[i], chairs=4)
    # food trucks (real size, traced positions and headings)
    for (x, y, ang, st) in [(787.5, 241, 27.6, "stripec"), (853.75, 237.5, 4, "stripe"), (922.5, 237.5, 0, "stripey"),
                            (940, 275, 90, "stripey")]:
        u, v = P(x, y)
        truck_r(cv, u, v, ang, st)
    for i, (x, y) in enumerate([(750, 252.5), (777.5, 282.5), (892.5, 261), (914, 267.5), (837.5, 322.5), (797.5, 342.5)]):
        u, v = P(x, y)
        parasol(cv, u, v, 1.5, ("umb-p", "prop", "umb-c", "umb-y", "prop", "umb-c")[i], chairs=4)
    poles = PP([(772, 219), (940, 219), (940, 300), (772, 300)])
    for i in range(4):
        a, b = poles[i], poles[(i + 1) % 4]
        cv.line(a[0], a[1], b[0], b[1], "string")
        for t in frange(.08, 1, .1):
            cv.circle(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, .18, "bulb")
    # lifestyle & souvenir: traced block, yellow trim, awnings, stalls
    for b in [(895, 378, 980, 405), (842, 405, 980, 505)]:
        q = RP(*b)
        cv.rect(q[0] + 1.4, q[1] - 1.4, q[2] + 1.4, q[3] - 1.4, "shadow")
    cv.rect(*RP(895, 378, 980, 405), "roof")
    cv.rect(*RP(842, 405, 980, 505), "roof")
    cv.rect(*RP(912, 367, 942, 380), "prop")
    cv.rect(*RP(842, 505, 980, 530), "roof")
    # yellow parapet on the west, south and east edges; plant deck in the NW corner; inner parapet line
    for b in [(842, 405, 847, 505), (842, 500, 980, 505), (976, 380, 980, 528)]:
        cv.rect(*RP(*b), "chalk-y")
    cv.rect(*RP(847, 407, 968, 497), "ln-m")
    cv.rect(*RP(847, 409, 895, 428), "chalk-y", ' fill-opacity=".55"')
    for x in (856, 868, 880):
        cv.rect(*RP(x - 4, 413, x + 4, 423), "prop")
    # south band: solid yellow canopy, roof garden, centre awning with the pink shop sign
    cv.rect(*RP(843, 508, 895, 528), "chalk-y")
    cv.rect(*RP(843, 508, 895, 528), "ln-m")
    planter_g(cv, GB(913, 507, 955, 527), 150, density=.9, radius=0)
    cv.rect(*RP(912, 528, 957, 541), "chalk-y")
    cv.rect(*RP(912, 528, 957, 541), "ln-m")
    cv.rect(*RP(914, 541, 955, 551), "chalk-p")
    cv.rect(*RP(914, 541, 955, 551), "ln-m")
    # forecourt: white stall, mascot photo statue, vending kiosk, planter box
    cv.rect(*RP(845, 538, 870, 551), "prop")
    cv.rect(*RP(845, 538, 870, 541), "", pat("stripec"))
    cv.circle(*P(901, 553), 1.4, "chalk-p")
    cv.circle(*P(901, 553), 1.4, "ln-m")
    cv.circle(*P(901, 549), .7, "statue")
    cv.rect(*RP(968, 533, 982, 543), "prop")
    planter_g(cv, GB(982, 555, 1008, 565), 151, density=.9)
    door_swing(cv, *P(842, 445), 1.6, 180, 90)
    door_swing(cv, *P(842, 465), 1.6, 180, 270)
    u, v = P(815, 480)
    parasol(cv, u, v, 1.5, "umb-y", chairs=4)
    for (x, y) in [(823, 452), (830, 505)]:
        parasol(cv, *P(x, y), .5, "prop", chairs=3, ribs=0)
    for i, (x, y) in enumerate([(1007.5, 507.5)]):
        u, v = P(x, y)
        parasol(cv, u, v, 1.5, "umb-c", chairs=4)
    for b in [(987, 465, 1007, 485), (1022, 482, 1042, 505)]:
        cv.rect(*RP(*b), "prop")
        q = RP(*b)
        cv.line(q[0], q[1], q[2], q[3], "joint")
        cv.line(q[2], q[1], q[0], q[3], "joint")
    # stage props + curved steps
    for (x, y) in [(1112.5, 204), (1190, 242.5)]:
        u, v = P(x, y)
        cv.rect(u - .8, v - .8, u + .8, v + .8, "solid")
    cv.circle(*P(1105, 165), 1.5, "umb-y")
    # promenade: rail in segments, full-width steps in every planter opening, stairs on the sea-wall line
    for seg in [SEAWALL_PX[0:4], SEAWALL_PX[4:7], SEAWALL_PX[7:9]]:
        railing(cv, PP(seg), 2)
    for (xa, xb) in [(267, 410), (520, 628), (728, 792), (865, 902)]:
        top = [P(xa, edge_y(xa)), P(xb, edge_y(xb))]
        for k in range(4):
            o = k * .45
            cv.line(top[0][0], top[0][1] + o, top[1][0], top[1][1] + o, "tread" if 0 < k < 3 else "ln-m")
    stair_ns(cv, *RP(382.5, 675, 452.5, 745), (15,), rails=(P(417.5, 0)[0],), label="DN 15R")
    stair_ns(cv, *RP(770, 655, 836, 722), (15,), rails=(P(803, 0)[0],), label="DN 15R")
    ps = pier_rect(-6.7, 0, -3.75, 3.75)
    quad_treads(cv, ps, 5)
    for nn in (-3.6, 3.6):
        a1, b1 = pier_pt(-6.7, nn), pier_pt(0, nn)
        cv.line(a1[0], a1[1], b1[0], b1[1], "rail")
    # pier (traced 15 deg heading), head platform, rails, piles
    body = pier_rect(0, 34, -3.75, 3.75)
    head = pier_rect(34, 45.5, -22, 5.2)
    for poly in (body, head):
        cv.poly([(x + .8, y - .8) for x, y in poly], "shadow")
    for poly in (body, head):
        cv.poly(poly, "z-timber")
    for t in frange(.5, 45.5, .9):
        n0, n1 = (-3.75, 3.75) if t < 34 else (-22, 5.2)
        a, b = pier_pt(t, n0), pier_pt(t, n1)
        cv.line(a[0], a[1], b[0], b[1], "pat-s")
    outline = [pier_pt(0, -3.75), pier_pt(34, -3.75), pier_pt(34, -22), pier_pt(45.5, -22), pier_pt(45.5, 5.2),
               pier_pt(34, 5.2), pier_pt(34, 3.75), pier_pt(0, 3.75)]
    cv.pline(outline, "ln")
    railing(cv, [pier_pt(.3, -3.5), pier_pt(34.2, -3.5), pier_pt(34.2, -21.7), pier_pt(45.2, -21.7), pier_pt(45.2, 4.9),
                 pier_pt(34.2, 4.9), pier_pt(34.2, 3.5), pier_pt(.3, 3.5)], 3)
    for t in frange(6, 46, 6):
        for nn in ((-3.1, 3.1) if t < 34 else (-21.2, -12, -3, 4.4)):
            q = pier_pt(t, nn)
            cv.circle(q[0], q[1], .35, "ln-b")
    for t in (8, 17, 26):
        q = pier_pt(t, -2.7)
        cv.circle(q[0], q[1], .45, "prop")
    for (t, nn) in [(37, -19), (37, -15), (40, -19), (40, -15)]:
        cv.poly(rrect(*pier_pt(t, nn), 2.4, 1.2, 75), "umb-y")
    for (t, nn, ang) in [(43.5, -6, 75), (43.5, 1, 75), (37.5, -6, 75)]:
        bench(cv, *pier_pt(t, nn), 2.4, ang)
    q = pier_pt(31.4, 0)
    cv.circle(q[0], q[1], 1.2, "statue")
    cv.text(q[0], q[1] + .45, "H", "t-lbl")
    # beach hut, boards
    q = RP(697, 720, 742, 760)
    cv.rect(q[0] + 1, q[1] - 1, q[2] + 1, q[3] - 1, "shadow")
    cv.rect(*q, "roof")
    cv.rect(*q, "", pat("thatch"))
    cv.line(q[0], q[1], q[2], q[3], "ln-m")
    cv.line(q[2], q[1], q[0], q[3], "ln-m")
    cv.rect(*RP(700, 760, 740, 782), "z-timber")
    cv.rect(*RP(700, 760, 740, 782), "ln-m")
    for k, x in enumerate((934, 945, 957, 969)):
        u, v = P(x, 668)
        cv.ellipse(u, v, .32, 1.1, ("umb-c", "umb-y", "prop", "umb-y")[k])
    for x in (873, 886):
        u, v = P(x, 702)
        cv.ellipse(u, v, .35, 1.2, "umb-c")
    A('</g>')

    # ================================================================ planting + props
    A(f'<g id="lyr-props" clip-path="url(#{p}-frm)">')
    # central planter: bed, bench ring with slats and gaps, big tree
    rb, ro = M(57), M(81)
    for q in range(4):
        a0, a1 = q * 90 + 45 + 7, q * 90 + 135 - 7
        cv.poly(sector(cx, cy, rb, ro, a0, a1, 18), "prop")
        for a in frange(a0 + 3, a1, 3):
            aa = math.radians(a)
            cv.line(cx + rb * math.cos(aa), cy + rb * math.sin(aa), cx + (rb + 1.4) * math.cos(aa), cy + (rb + 1.4) * math.sin(aa), "joint")
        cv.poly(sector(cx, cy, rb + 1.6, ro - .3, a0 + 2, a1 - 2, 16), "bed")
    cv.circle(cx, cy, rb, "bed")
    cv.circle(cx, cy, rb, "wall6")
    canopy(cv, *P(605, 410), M(67), 3, "tree")
    # plaza islands (traced)
    for i, (x, y, rx, ry, kind, trees_) in enumerate([
            (452, 310, 42, 52, "tree", [(430, 272, 25), (466, 292, 28), (444, 330, 26), (470, 338, 20)]),
            (450, 493, 37, 35, "tree", [(447, 490, 33)]),
            (792, 416, 35, 33, "sak", [(792, 416, 33)]),
            (800, 537, 32, 37, "tree", [(800, 537, 32)])]):
        u, v = P(x, y)
        pts = cr_sample(blob(u, v, M(rx), M(ry), 60 + i, .1, 10), closed=True, per=6)
        planter_g(cv, Polygon(pts), 70 + i, density=.6, rmin=.5, rmax=.9, radius=0)
        for (a, b, r) in trees_:
            canopy(cv, *P(a, b), M(r), 80 + i + a, kind)
    maneki_big(cv, *P(707, 350), M(23))
    # frontage planters (traced)
    for i, b_ in enumerate([(350, 205, 365, 265), (370, 205, 387, 265), (370, 395, 387, 430), (360, 430, 372, 495),
                            (357, 515, 390, 588)]):
        planter_g(cv, GB(*b_), 90 + i, density=.9)
    # promenade-edge planters: north face on the plaza edge, steps fill the openings between them
    for i, (xa, xb, yb) in enumerate([(170, 267, 627), (410, 520, 635), (628, 728, 622), (792, 865, 612), (902, 1022, 611)]):
        planter_g(cv, G([(xa, edge_y(xa)), (xb, edge_y(xb)), (xb, yb), (xa, yb)]), 110 + i, density=.8)
    for i, b_ in enumerate([(300, 615, 350, 635), (737, 300, 780, 345), (830, 335, 865, 365)]):
        planter_g(cv, GB(*b_), 120 + i, density=.8)
    for (x, y) in [(1000, 437), (1025, 465), (1022, 540)]:
        planter_g(cv, Point(*P(x, y)).buffer(1.6), 130 + x, density=.2, radius=0)
    # lamps
    for (x, y) in [(514, 580), (752, 575), (480, 330), (730, 330), (470, 520), (740, 520)]:
        u, v = P(x, y)
        cv.circle(u, v, .55, "prop")
        cv.circle(u, v, .2, "ink-f")
    for (x, y) in [(200, 640), (270, 656), (340, 670), (440, 669), (520, 669), (600, 668), (690, 668), (760, 668),
                   (900, 632), (970, 632)]:
        u, v = P(x, y)
        cv.circle(u, v, .55, "prop")
        cv.circle(u, v, .2, "ink-f")
    for (x, y, ang) in [(229, 630, 15), (812, 618, 0), (560, 650, 0), (660, 650, 0), (950, 618, 0), (330, 650, 12)]:
        bench(cv, *P(x, y), 2.0, ang)
    # trees and palms (traced positions and canopy sizes)
    trees = [(517, 133, 28), (683, 133, 28), (303, 167, 20), (438, 157, 30), (455, 150, 18), (505, 205, 22),
             (815, 165, 25), (855, 165, 25), (895, 160, 25), (1000, 150, 22), (1035, 135, 25),
             (75, 170, 25), (77, 230, 20), (105, 390, 35), (85, 445, 28), (95, 570, 35), (1035, 222, 30),
             (1115, 420, 18), (1135, 426, 16), (1255, 375, 42)]
    for i, (x, y, r) in enumerate(trees):
        canopy(cv, *P(x, y), M(r), 200 + i, "tree")
    for i, (x, y, r) in enumerate([(538, 237, 25), (77, 272, 18), (152, 587, 22), (1155, 172, 15), (1140, 478, 28),
                                   (1235, 480, 30)]):
        canopy(cv, *P(x, y), M(r), 300 + i, "sak")
    palms = [(340, 160, 22), (370, 160, 22), (548, 193, 18), (658, 192, 20), (715, 207, 20), (713, 270, 18), (740, 155, 20),
             (758, 322, 25), (848, 350, 20), (372, 545, 25), (85, 340, 35), (85, 495, 30), (1170, 150, 25), (1195, 170, 22),
             (1005, 290, 25), (1180, 305, 22), (1190, 280, 20), (1190, 355, 20), (1000, 437, 22), (1025, 465, 20),
             (1022, 540, 20), (1080, 512, 22), (645, 587, 25), (465, 612, 30), (295, 640, 28),
             (195, 685, 30), (295, 700, 28), (365, 715, 25), (470, 715, 25), (517, 680, 30), (605, 702, 18), (640, 700, 20),
             (675, 700, 20), (735, 655, 28), (860, 660, 28), (1030, 655, 26), (1157, 600, 30)]
    for i, (x, y, r) in enumerate(palms):
        palm_top(cv, *P(x, y), M(r), 400 + i)
    # beach furniture (real sizes at traced spots)
    for i, (x, y, c, lgs) in enumerate([(350, 765, "umb-c", [(363, 784), (377, 788)]),
                                        (622, 740, "umb-c", [(596, 763), (609, 765), (632, 767), (646, 766)]),
                                        (795, 760, "umb-y", [(783, 780), (800, 782)]), (905, 662, "umb-y", [])]):
        for (lx, ly) in lgs:
            u, v = P(lx, ly)
            lounger(cv, u, v, 80)
            cv.rect(u - .25, v - .7, u + .25, v + .7, ("chalk-c", "chalk-p", "chalk-y", "chalk-c")[i], ' fill-opacity=".55"')
        parasol(cv, *P(x, y), 1.5, c)
    for (x, y) in [(330, 1000), (480, 950), (610, 1000)]:
        cv.circle(*P(x, y), .8, "ring-acc")
    A('</g>')

    # ================================================================ grid
    A('<g id="lyr-grid">')
    for x in range(0, 201, 20):
        cv.line(x, Y0, x, Y1, "grid")
    for y in range(0, 158, 20):
        cv.line(X0, y, X1, y, "grid")
    A('</g>')
    for i, letter in enumerate("ABCDEFGHIJ"):
        x = cv.X(10 + 20 * i)
        A(f'<circle class="bubble" cx="{n(x)}" cy="40" r="10"/><text class="t-lbl" x="{n(x)}" y="43.5" text-anchor="middle">{letter}</text>')
    for j in range(8):
        y = cv.Y(10 + 20 * j)
        A(f'<circle class="bubble" cx="36" cy="{n(y)}" r="10"/><text class="t-lbl" x="36" y="{n(y + 3.5)}" text-anchor="middle">{j + 1}</text>')

    # ================================================================ routes
    A(f'<g id="lyr-circ" clip-path="url(#{p}-frm)">')
    cv.pline(PP([(603, 128), (603, 190), (603, 287), (595, 330), (560, 470), (590, 585), (610, 640), (803, 655),
                 (803, 722), (880, 760), (1000, 700), (1052, 606), (1052, 645), (1080, 740), (1110, 830)]),
             "circ1", f' marker-end="url(#{p}-arr)"')
    for pts in [[(115, 140), (115, 590), (160, 620)], [(407, 140), (407, 205), (400, 260), (350, 300)],
                [(690, 186), (690, 280), (720, 300)], [(956, 150), (956, 195), (900, 210)],
                [(1075, 150), (1075, 205), (1120, 230)], [(1238, 140), (1238, 330), (1218, 395), (1196, 418), (1186, 462)],
                [(974, 200), (976, 300), (1004, 370), (1060, 434), (1102, 490), (1120, 530)], [(1186, 465), (1185, 505), (1150, 545), (1110, 560)],
                [(640, 420), (842, 455)], [(417, 640), (417, 745), (400, 790)], [(1080, 330), (1120, 360)]]:
        cv.pline(PP(pts), "circ2", f' marker-end="url(#{p}-arr)"')
    A('</g>')

    # ================================================================ sightlines
    A(f'<g id="lyr-sight" clip-path="url(#{p}-frm)">')
    for (a, b, lab, lo) in [((615, 190), (615, 1020), "V1", (8, 18)), ((1238, 140), (1100, 880), "V2", (-26, 30)),
                            ((300, 575), (1050, 880), "V3", (6, 26))]:
        pa, pb = P(*a), P(*b)
        cv.line(pa[0], pa[1], pb[0], pb[1], "sight", f' marker-end="url(#{p}-arrt)"')
        cv.circle(pa[0], pa[1], .9, "teal-f")
        cv.text(*P(a[0] + lo[0], a[1] + lo[1]), lab, "t-lbl t-teal halo", "start")
    A('</g>')

    # ================================================================ cuts
    A('<g id="lyr-cuts">')
    xa = P(605, 0)[0]
    cv.line(xa, Y0, xa, Y1, "cut")
    cv.line(xa, Y0, xa, Y0 + 6, "cut-h")
    cv.line(xa, Y1 - 6, xa, Y1, "cut-h")
    section_bubble(cv, cv.X(xa) + 16, cv.Y(Y0 + 2), "A", 0)
    section_bubble(cv, cv.X(xa) + 16, cv.Y(Y1 - 2), "A", 0)
    yb = P(0, 417)[1]
    cv.line(X0, yb, X1, yb, "cut")
    cv.line(X0, yb, X0 + 6, yb, "cut-h")
    cv.line(X1 - 6, yb, X1, yb, "cut-h")
    section_bubble(cv, cv.X(X0 + 2), cv.Y(yb) - 16, "B", -90)
    section_bubble(cv, cv.X(X1 - 2), cv.Y(yb) - 16, "B", -90)
    A('</g>')

    # ================================================================ labels
    A('<g id="lyr-labels">')

    def T(x, y, s, cls="t-sm halo", anchor="middle", rot=None):
        u, v = P(x, y)
        cv.text(u, v, s, cls, anchor, rot)

    T(300, 40, "TOWN · NON-PLAYABLE")
    T(1200, 40, "TOWN · NON-PLAYABLE")
    T(605, 30, "CITY STREET", rot=-90)
    T(300, 120, "COASTAL STREET · +8.40 west → +6.00 east · cars only")
    T(1110, 120, "→ TO STATION / TOWN", anchor="start")
    T(210, 189, "KIOSKS +8.40")
    T(598, 168, "FORECOURT +8.40")
    T(245, 250, "FASHION & GOODS", "t-lbl halo")
    T(245, 262, "2 floors · roof plan")
    T(278, 328, "ARCADE · interior shown", "t-lbl halo")
    T(212, 516, "CAFÉ", "t-lbl halo")
    T(258, 584, "CAFÉ TERRACE")
    T(115, 400, "WEST LANE · stepped slope +8.40 → +3.15", rot=-90)
    T(603, 240, "MAIN STAIR 2 × 16R", rot=-90)
    T(407, 214, "NW STAIR 32R")
    T(690, 284, "E STAIR 32R")
    T(956, 150, "20R", anchor="start")
    T(1075, 160, "20R")
    T(605, 372, "CENTRAL PLAZA", "t-zone halo")
    T(605, 384, "+3.60 · open paving Ø53")
    T(605, 503, "planter Ø19 · bench ring Ø27 · tree Ø22")
    T(707, 320, "CAT STATUE")
    T(856, 210, "FOOD TRUCK ZONE", "t-lbl halo")
    T(856, 296, "4 trucks 6.5 × 2.5 · real size")
    T(911, 452, "LIFESTYLE &", "t-lbl halo")
    T(911, 465, "SOUVENIR")
    T(935, 562, "SHOP SIGN · STALL")
    T(1020, 420, "EAST TERRACE", rot=56)
    T(1110, 270, "SMALL STAGE", "t-lbl halo")
    T(1110, 282, "event deck +4.20 · 26 × 21 m")
    T(1125, 375, "EVENT LAWN", "t-lbl halo")
    T(1125, 387, "raked +3.60 → +4.80 · 1:18")
    T(1238.5, 250, "EAST PATH 2.4 m · 1:36", rot=90)
    T(1150, 445, "CURVED STEPS 11R", anchor="end")
    T(1196, 500, "WALK +3.15", rot=-80)
    T(975, 300, "CURVED PATH 6.5 m", rot=88)
    T(1135, 538, "JUNCTION")
    T(1105, 176, "TOP PLAZA")
    T(600, 625, "BEACH PROMENADE · +3.15 · 3 steps down from the plaza", "t-zone halo")
    T(1052, 600, "5R")
    T(560, 830, "BEACH AREA", "t-big halo")
    T(560, 845, "+0.90 → ±0.00")
    T(720, 716, "HUT")
    T(952, 650, "SURF BOARDS")
    T(1150, 880, "PIER 7.5 m · +2.40", "t-sm halo", "start")
    T(1040, 965, "PIER HEAD 27 × 11.5 · PHOTO SPOT", "t-lbl halo")
    T(120, 960, "ROCKS")
    T(680, 960, "WADE ZONE ±0.00 → −0.90")
    T(680, 1012, "SWIM ZONE")
    T(1285, 700, "SEA", rot=90)
    for (x, y, letter, lx, anchor) in [(603, 128, "A", 618, "start"), (1238.5, 142, "B", 1222, "end")]:
        u, v = P(x, y)
        cv.circle(u, v, 2.2, "acc-f")
        cv.text(u, v + .9, letter, "t-lbl t-inv")
        T(lx, y + 6, f"SPAWN {letter}", "t-lbl t-acc halo", anchor)
    for (x, y, k) in [(540, 110, 1), (540, 400, 2), (160, 320, 3), (160, 500, 4), (160, 212, 5), (758, 205, 6),
                      (1070, 230, 7), (862, 488, 8), (190, 640, 9), (480, 840, 10), (1135, 800, 11), (1238.5, 205, 12)]:
        key(cv, *P(x, y), k)
    A('</g>')
    if underlay:
        ix, iy = OX - 60 - X0 * S, OY - 75 - Y0 * S
        A(f'<g id="lyr-ref" hidden="" opacity=".6" clip-path="url(#{p}-frm)"><image href="{underlay}" x="{ix}" y="{iy}" '
          f'width="1536" height="1024"/></g>')
    cv.rect(X0, Y0, X1, Y1, "frame")
    legend_and_title(cv, p)
    return cv.svg(), W, H


def legend_and_title(cv, p):
    A = cv.add
    lx, ly = 1344, 56
    A(f'<g transform="translate({lx} {ly})">')
    A('<rect class="frame-in" width="268" height="650"/>')
    A('<text class="t-head" x="14" y="26">LEGEND</text>')
    rows = [("z-road", None, "Street · cars only"), ("z-paver", None, "Paving · plain, texture set in engine"),
            ("z-timber", "board", "Wood deck · promenade, pier, stage"), ("z-lawn", "lawn", "Grass"),
            ("bed", None, "Planting bed · shrubs"), ("z-sand", "sand", "Sand · wet sand at the shoreline"),
            ("z-sea", None, "Wade · ±0.00 to −0.90"), ("z-mid", None, "Swim · −0.90 to −1.60"),
            ("z-deep", "water", "Swim · below −1.60"), ("roof", None, "Roof plan"), ("arc-y", None, "Interior shown (roof removed)"),
            ("z-town", "hatch", "Non-playable")]
    y = 42
    for cls, pt, lab in rows:
        A(f'<rect class="{cls}" x="14" y="{y}" width="30" height="14"/>')
        if pt:
            A(f'<rect x="14" y="{y}" width="30" height="14" fill="url(#{p}-{pt})"/>')
        A(f'<rect class="ln-f" x="14" y="{y}" width="30" height="14"/>')
        A(f'<text class="t-lbl" x="54" y="{y + 10.5}">{esc(lab)}</text>')
        y += 20
    y += 8
    A(f'<text class="t-head" x="14" y="{y + 6}">SYMBOLS</text>')
    y += 22
    entries = [("canopy", "Tree · canopy as traced"), ("sak", "Cherry (sakura)"), ("palm", "Palm"),
               ("rock", "Boulder"), ("parasol", "Parasol Ø3.0 + chairs"), ("bench", "Bench"), ("rail", "Railing · posts 2 m"),
               ("stair", "Stair · risers fitted to footprint"), ("key", "Key location · reference numbering"), ("spawn", "Spawn point"),
               ("circ1", "Main route"), ("circ2", "Secondary route"), ("sight", "Sightline V1–V3"), ("cut", "Section cut")]
    for kind, lab in entries:
        c = y + 8
        g = Cv(6, 6, 29, c, 0, 0)
        if kind == "canopy":
            canopy(g, 0, 0, 1.4, 5, "tree", shadow=False)
        elif kind == "sak":
            canopy(g, 0, 0, 1.4, 6, "sak", shadow=False)
        elif kind == "palm":
            palm_top(g, 0, 0, 1.5, 7, shadow=False)
        elif kind == "rock":
            rock(g, 0, 0, 1.2, 8, shadow=False)
        elif kind == "parasol":
            parasol(g, 0, 0, 1.0, "umb-y", chairs=4)
        elif kind == "bench":
            bench(g, 0, 0, 2.4, 0)
        elif kind == "rail":
            railing(g, [(-2.2, 0), (2.2, 0)], 1.4)
        elif kind == "stair":
            g.rect(-2.2, -1, 2.2, 1, "z-paver")
            for x in frange(-2.2, 2.3, .4):
                g.line(x, -1, x, 1, "tread")
        elif kind == "key":
            key(g, 0, 0, 1)
        elif kind == "spawn":
            g.circle(0, 0, 1.1, "acc-f")
        elif kind in ("circ1", "circ2", "sight"):
            g.line(-2.4, 0, 2.4, 0, kind)
        elif kind == "cut":
            g.line(-2.4, 0, -1, 0, "cut-h")
            g.line(-1, 0, 2.4, 0, "cut")
        A(g.svg())
        A(f'<text class="t-lbl" x="54" y="{y + 11.5}">{esc(lab)}</text>')
        y += 21
    A('</g>')
    ccx, ccy = 1370, 752
    A(f'<circle class="frame-in" cx="{ccx}" cy="{ccy}" r="22"/>')
    A(f'<polygon class="ink-f" points="{ccx},{ccy - 20} {ccx + 7},{ccy + 7} {ccx},{ccy + 2} {ccx - 7},{ccy + 7}"/>')
    A(f'<text class="t-head" x="{ccx}" y="{ccy - 26}" text-anchor="middle">N</text>')
    bx, by = 1408, 750
    for k, (a, b) in enumerate([(0, 10), (10, 20), (20, 30)]):
        A(f'<rect class="{"ink-f" if k % 2 == 0 else "sheet-f"}" x="{bx + a * S}" y="{by}" width="{(b - a) * S}" height="6"/>')
    A(f'<rect class="ln" x="{bx}" y="{by}" width="{30 * S}" height="6"/>')
    for m in (0, 10, 20, 30):
        A(f'<text class="t-dim" x="{bx + m * S}" y="{by - 5}" text-anchor="middle">{m}</text>')
    A(f'<text class="t-sm" x="{bx}" y="{by + 19}">metres · true scale · grid 20 m</text>')
    tx, ty = 1344, 796
    A(f'<g transform="translate({tx} {ty})">')
    A('<rect class="frame" width="268" height="280"/>')
    A('<text class="t-title" x="14" y="32" style="font-size:15px">Japan Coastal Hangout Park</text>')
    A('<text class="t-sm" x="14" y="48">Traced from the reference · true scale · rev E</text>')
    A('<line class="ln" x1="0" y1="60" x2="268" y2="60"/>')
    fields = [("SHEET", "L-101 Site plan"), ("SCALE", "6 px = 1 m"), ("TRACE", "ref px ÷ 6 = m"),
              ("UNITS", "m · 1 m = 100 UU"), ("DATUM", "±0.00 = sea level"), ("NORTH", "up · sun from SW"),
              ("REVISION", "E · 2026-10-05"), ("STATUS", "Concept / blockout")]
    for i, (k, v) in enumerate(fields):
        col, row = i % 2, i // 2
        fx_, fy_ = 14 + col * 134, 82 + row * 50
        A(f'<text class="t-sm" x="{fx_}" y="{fy_}">{k}</text><text class="t-lbl" x="{fx_}" y="{fy_ + 16}">{esc(v)}</text>')
        if col == 0 and row < 3:
            A(f'<line class="ln-f" x1="0" y1="{fy_ + 30}" x2="268" y2="{fy_ + 30}"/>')
    A('<line class="ln-f" x1="134" y1="60" x2="134" y2="280"/>')
    A('</g>')


def band(cv, centre_pts, width, fill="paver", edge="ink-3"):
    """Curved path drawn as an outlined band along a Catmull-Rom centreline."""
    d = cv.d(cr_cmds(centre_pts, closed=False))
    cv.add(f'<path d="{d}" style="fill:none;stroke:var(--{edge});stroke-width:{n(width * S + 1.6)};stroke-linejoin:round"/>')
    cv.add(f'<path d="{d}" style="fill:none;stroke:var(--{fill});stroke-width:{n(width * S)};stroke-linejoin:round"/>')


def steps_profile(y0, z0, risers, tread, rise=.15):
    """Section profile of a descending stair starting at (y0, z0)."""
    pts = [(y0, z0)]
    y, z = y0, z0
    for k in range(risers):
        z -= rise
        pts.append((y, z))
        if k < risers - 1:
            y += tread
            pts.append((y, z))
    return pts, y


# ============================================================== L-201 SECTION
Z_ST, Z_PL, Z_PR, Z_BC = 8.4, 3.6, 3.15, 0.9


def section_aa():
    p = "ca"
    W, H = 1040, 390
    cv = Cv(5.2, -10, 50, 250, -12, 0)
    A = cv.add
    A(defs(p))
    A(f'<rect class="sheet-bg" width="{W}" height="{H}"/>')
    title_strip(cv, 24, 30, "L-201", "SECTION A–A · X = 90.8 · STREET → PLAZA → BEACH · LOOKING EAST",
                "Horizontal 5.2 px = 1 m · vertical 10 px = 1 m (vertical exaggeration 1.9×) · light line = beyond")
    Y = lambda py: (py - 75) / 6  # noqa: E731
    # beyond
    cv.rect(-12, Z_ST, -1, Z_ST + 6, "beyond")
    cv.rect(Y(220), Z_PL, Y(262), Z_PL + 2.8, "beyond")
    cv.text(Y(241), 7.2, "FOOD TRUCKS", "t-sm halo")
    cv.rect(Y(378), Z_PL, Y(567), Z_PL + 5.4, "beyond")
    cv.rect(Y(405), Z_PL + 5.4, Y(505), Z_PL + 5.8, "chalk-y")
    cv.text(Y(470), 6.2, "LIFESTYLE SHOP beyond", "t-sm halo")
    cv.ellipse(Y(350), Z_PL + 2.6, 3.4, .26, "statue")
    cv.text(Y(350), 7.0, "CAT", "t-sm halo")
    tree_elev(cv, Y(416), Z_PL, 7, 11, 31)
    cv.rect(95, 2.1, 145, 2.4, "beyond")
    for y in frange(101, 145, 6):
        cv.line(y, 2.1, y, -1.6, "ln-m")
    cv.text(128, 2.9, "PIER +2.40 beyond", "t-sm halo")
    cv.rect(Y(720), Z_BC, Y(760), Z_BC + 3.6, "beyond")
    cv.poly([(Y(716), Z_BC + 3.6), (Y(764), Z_BC + 3.6), (Y(740), Z_BC + 4.6)], "beyond")
    cv.text(Y(740), Z_BC + 5.2, "HUT", "t-sm")
    palm_elev(cv, Y(700), .5, 6.4, 2)
    palm_elev(cv, Y(612), 3.6, 6.8, 5)
    # ground
    stp, _ = steps_profile(Y(187), Z_ST, 16, .45)
    stp2, _ = steps_profile(Y(187) + 15 * .45 + 3.1, Z_ST - 2.4, 16, .45)
    top = [(-12, Z_ST), (Y(187), Z_ST)] + stp + stp2 + [(Y(287), Z_PL), (Y(594), Z_PL)] + \
        steps_profile(Y(594), Z_PL, 3, .45)[0] + [(Y(673), Z_PR), (Y(673), Z_BC), (Y(892.4), 0), (Y(892.4) + 15, -.9), (158, -1.5)]
    cv.poly([(Y(892.4), 0), (158, 0), (158, -1.5), (Y(892.4) + 15, -.9)], "water")
    cv.line(Y(892.4), 0, 158, 0, "ln-water")
    poche = top + [(158, -4), (-12, -4)]
    cv.poly(poche, "poche")
    cv.poly(poche, "", f' fill="url(#{p}-earth)"')
    cv.pline(top, "ln-h")
    cv.rect(Y(95), Z_ST, Y(135), Z_ST + .05, "solid")
    cv.text(Y(115), Z_ST + .6, "ROAD", "t-sm halo")
    cv.line(Y(185), Z_ST, Y(185), Z_ST + 1.1, "ln")
    # central planter (cut): bench ring, bed wall, big tree
    cy = Y(417)
    for (a, b) in [(cy - 13.5, cy - 11.2), (cy + 11.2, cy + 13.5)]:
        cv.rect(a, Z_PL, b, Z_PL + .6, "z-lawn")
        cv.rect(a, Z_PL, b, Z_PL + .6, "ln-m")
    for (a, b) in [(cy - 11.2, cy - 9.5), (cy + 9.5, cy + 11.2)]:
        cv.rect(a, Z_PL, b, Z_PL + .45, "conc")
    cv.rect(cy - 9.5, Z_PL, cy - 9.2, Z_PL + .6, "solid")
    cv.rect(cy + 9.2, Z_PL, cy + 9.5, Z_PL + .6, "solid")
    cv.rect(cy - 9.2, Z_PL + .4, cy + 9.2, Z_PL + .55, "z-lawn")
    tree_elev(cv, Y(410), Z_PL + .55, 10, 22, 1)
    cv.line(Y(672), Z_PR, Y(672), Z_PR + 1.1, "ln")
    for (y, z, s) in [(Y(145), Z_ST, False), (Y(320), Z_PL, False), (Y(340), Z_PL, False), (Y(530), Z_PL, False),
                      (cy - 10.4, Z_PL + .45, True), (Y(640), Z_PR, False), (Y(800), .7, False), (Y(830), .4, False)]:
        avatar(cv, y, z, seated=s)
    cv.add(f'<circle class="avatar" cx="{n(cv.X(141))}" cy="{n(cv.Y(0) - 3)}" r="3.4"/>')
    etag(cv, -10, Z_ST, "+8.40 STREET · FORECOURT")
    etag(cv, Y(300), Z_PL, "+3.60 PLAZA", below=True)
    etag(cv, Y(625), Z_PR, "+3.15 PROMENADE", below=True)
    etag(cv, Y(676), Z_BC, "+0.90 BEACH", below=True)
    etag(cv, 156, 0, "±0.00 SWL", anchor="end")
    etag(cv, Y(892.4) + 15, -.9, "−0.90 WADE LIMIT", below=True)
    callout(cv, Y(250), 6.4, Y(255), 12.4, "MAIN STAIR · 2 × 16R · TREAD 0.45 · LANDING 3.10")
    callout(cv, cy, 4.1, cy + 8, 15.4, "PLANTER Ø19 · BENCH RING Ø27 · TREE Ø22")
    callout(cv, Y(598), 3.4, Y(600), 9.6, "3 STEPS DOWN TO THE PROMENADE")
    callout(cv, Y(672), 2.2, Y(700), 6.6, "SEA WALL 2.25 · RAIL 1.10")
    vdim(cv, Y(182), Z_PL, Z_ST, "4.80", ext=Y(187))
    segs = [(Y(95), Y(135), "ROAD"), (Y(135), Y(187), "FORECOURT"), (Y(187), Y(287), "MAIN STAIR"), (Y(287), Y(594), "CENTRAL PLAZA"),
            (Y(594), Y(673), "PROMENADE"), (Y(673), Y(892.4), "BEACH"), (Y(892.4), Y(892.4) + 15, "WADE")]
    for a, b, name in segs:
        hdim(cv, a, b, -5.2, f"{b - a:.1f}", ext=-4)
        cv.text((a + b) / 2, -7.0, name, "t-sm")
    hdim(cv, Y(95), Y(892.4), -8.6, f"{Y(892.4) - Y(95):.1f} · ROAD TO SHORELINE", ext=-7.6)
    cv.rect(-12, 18.4, 158, -10, "frame")
    return cv.svg(), W, H


# ============================================================== L-202 SECTION
def section_bb():
    p = "cb"
    W, H = 1100, 370
    cv = Cv(4.9, -10, 40, 262, -4, 0)
    A = cv.add
    A(defs(p))
    A(f'<rect class="sheet-bg" width="{W}" height="{H}"/>')
    title_strip(cv, 24, 30, "L-202", "SECTION B–B · Y = 57 · ARCADE → PLAZA → STAGE LAWN → COAST · LOOKING NORTH",
                "Horizontal 4.9 px = 1 m · vertical 10 px = 1 m · light line = beyond (street wall, stairs, trucks, stage)")
    X = lambda px: (px - 60) / 6  # noqa: E731
    # beyond: street wall top follows the falling street
    street = [(X(142), Z_ST), (X(730), Z_ST), (X(940), 6.6), (X(1100), 6.6), (X(1230), 6.0), (X(1250), 6.0)]
    cv.poly(street + [(X(1250), Z_PL), (X(142), Z_PL)], "beyond")
    cv.pline([(x, z + 1.1) for x, z in street], "ln-m")
    for (a, b, zt) in [(392, 423, Z_ST), (565, 642, Z_ST), (677, 703, Z_ST), (940, 972, 6.6), (1060, 1090, 6.6)]:
        cv.rect(X(a), Z_PL, X(b), zt, "prop")
        for z in frange(Z_PL + .6, zt, .6):
            cv.line(X(a), z, X(b), z, "ln-f")
    cv.text(X(603), 6.3, "MAIN STAIR", "t-sm halo")
    for i, x in enumerate((440, 505, 815, 855, 895, 1000)):
        tree_elev(cv, X(x), Z_ST if x < 730 else 6.8, 4.6, 5.0, 10 + i)
    for (a, b) in [(770, 805), (835, 873), (903, 942)]:
        cv.rect(X(a), Z_PL, X(b), Z_PL + 2.8, "beyond")
    cv.text(X(856), 7.2, "FOOD TRUCKS", "t-sm halo")
    cv.rect(X(1212), Z_PL, X(1240), 6.0, "beyond")
    cv.text(X(1226), 6.6, "EAST PATH", "t-sm halo")
    cv.rect(X(1252), 6.0, X(1300), 13, "z-town")
    cv.rect(X(1252), 6.0, X(1300), 13, "", f' fill="url(#{p}-hatch)"')
    cv.ellipse(X(707), Z_PL + 2.6, 3.4, .26, "statue")
    # ground cut
    lane_z = 5.25
    Z_LT = 4.75  # raked lawn at its south tip; landing +4.80
    ground = [(-4, lane_z), (X(142.5), lane_z), (X(142.5), Z_PL), (X(1056), Z_PL), (X(1066), Z_LT - .35), (X(1066), Z_LT),
              (X(1150), Z_LT), (X(1150), 4.8), (X(1247), 4.8), (X(1247), -1.0), (207, -1.8)]
    cv.poly([(X(1247), 0), (207, 0), (207, -1.8), (X(1247), -1.0)], "water")
    cv.line(X(1247), 0, 207, 0, "ln-water")
    poche = ground + [(207, -3.4), (-4, -3.4)]
    cv.poly(poche, "poche")
    cv.poly(poche, "", f' fill="url(#{p}-earth)"')
    cv.pline(ground, "ln-h")
    cv.rect(-4, lane_z, X(55), 12, "z-town")
    cv.rect(-4, lane_z, X(55), 12, "", f' fill="url(#{p}-hatch)"')
    for i, x in enumerate((85, 105)):
        tree_elev(cv, X(x), lane_z, 6, 5.8, 40 + i)
    # arcade (cut)
    a0, a1 = X(142.5), X(347.5)
    cv.rect(a0, Z_PL, a1, 9.6, "sheet-f")
    cv.rect(a0, Z_PL, a0 + .4, 10.2, "solid")
    cv.rect(a1 - .4, Z_PL, a1, 10.2, "solid")
    cv.rect(a0, 9.3, a1, 9.6, "solid")
    cv.rect(a0 + .4, 9.0, a1 - .4, 9.3, "arc-y")
    for b in [(187, 217), (250, 270), (280, 300), (310, 345)]:
        cv.rect(X(b[0]), Z_PL, X(b[1]), Z_PL + 1.7, "prop")
    cv.rect(a0 + .4, Z_PL, a1 - .4, 4.05, "conc")
    for u_ in (a0 + .2, a1 - .2):
        cv.line(u_, 10.2, u_, 11.3, "glass")
    cv.text((a0 + a1) / 2, 7.8, "ARCADE FFL +4.05 · 5.25 clear", "t-sm halo")
    cv.text((a0 + a1) / 2, 11.7, "roof terrace +9.60 · glass rail", "t-sm halo")
    # planter, central planter, island, lifestyle shop
    cv.rect(X(370), Z_PL, X(387), Z_PL + .6, "z-lawn")
    cx = X(605)
    for (a, b) in [(cx - 13.5, cx - 11.2), (cx + 11.2, cx + 13.5)]:
        cv.rect(a, Z_PL, b, Z_PL + .6, "z-lawn")
    for (a, b) in [(cx - 11.2, cx - 9.5), (cx + 9.5, cx + 11.2)]:
        cv.rect(a, Z_PL, b, Z_PL + .45, "conc")
    cv.rect(cx - 9.5, Z_PL, cx - 9.2, Z_PL + .6, "solid")
    cv.rect(cx + 9.2, Z_PL, cx + 9.5, Z_PL + .6, "solid")
    cv.rect(cx - 9.2, Z_PL + .4, cx + 9.2, Z_PL + .55, "z-lawn")
    tree_elev(cv, cx, Z_PL + .55, 10, 22, 3)
    cv.rect(X(792) - 5.8, Z_PL, X(792) + 5.8, Z_PL + .5, "z-lawn")
    tree_elev(cv, X(792), Z_PL + .5, 7, 11, 21, "sak")
    s0, s1 = X(842), X(980)
    cv.rect(X(825), Z_PL, s0, Z_PL + .6, "z-lawn")
    cv.rect(s0, Z_PL, s1, 9.0, "sheet-f")
    cv.rect(s0, Z_PL, s0 + .4, 9.4, "solid")
    cv.rect(s1 - .4, Z_PL, s1, 9.4, "solid")
    cv.rect(s0, 8.7, s1, 9.0, "solid")
    cv.rect(s0, 9.0, s1, 9.4, "chalk-y")
    cv.rect(s0 + 3, Z_PL, s1 - 3, Z_PL + 1.0, "prop")
    cv.text((s0 + s1) / 2, 6.6, "LIFESTYLE & SOUVENIR", "t-sm halo")
    palm_elev(cv, X(1000), Z_PL, 6.4, 7)
    cv.rect(X(1065.5), Z_PL, X(1067), Z_LT + .1, "solid")
    cv.rect(X(1067), Z_LT - .02, X(1098), Z_LT + .1, "z-lawn")
    cv.rect(X(1047.5), 3.6, X(1202.5), 4.2, "", ' fill="none" stroke="var(--ink-2)" stroke-width=".8" stroke-dasharray="3 2"')
    cv.text(X(1125), 3.0, "STAGE DECK +4.20 beyond (hidden)", "t-sm halo")
    tree_elev(cv, X(1120), Z_LT, 6, 8, 23)
    tree_elev(cv, X(1255), 4.8, 9, 14, 24)
    cv.line(X(1246.5), 4.8, X(1246.5), 5.9, "ln")
    for x in (X(250), X(450), X(520), cx - 10.4, X(700), X(1010), X(1085), X(1170)):
        seat = abs(x - (cx - 10.4)) < .1
        z = Z_LT if x > X(1066) else Z_PL
        avatar(cv, x, z + (.45 if seat else 0), seated=seat)
    etag(cv, -3, lane_z, "+5.25 LANE")
    etag(cv, X(420), Z_PL, "+3.60 PLAZA", below=True)
    etag(cv, X(760), Z_ST, "+8.40 STREET beyond")
    etag(cv, X(1035), 6.6, "+6.60 beyond")
    etag(cv, 205, 0, "±0.00", anchor="end")
    hdim(cv, X(142.5), X(347.5), 14.0, f"{X(347.5) - X(142.5):.1f} ARCADE", ext=10.2)
    hdim(cv, X(347.5), X(825), 14.0, f"{X(825) - X(347.5):.1f} PLAZA")
    hdim(cv, X(842), X(980), 14.0, f"{X(980) - X(842):.1f} SHOP", ext=9.4)
    hdim(cv, X(1066), X(1207), 14.0, f"{X(1207) - X(1066):.1f} LAWN TIP · LANDING")
    etag(cv, X(1180), 4.8, "+4.80 LANDING")
    vdim(cv, X(1060), Z_PL, Z_LT, "1.15", side=-1)
    hdim(cv, cx - 13.5, cx + 13.5, 2.0, "Ø27.0 BENCH RING")
    vdim(cv, a0 + 1.6, Z_PL, 9.3, "6.00", side=1)
    vdim(cv, s1 + 1.0, Z_PL, 9.0, "5.40", side=1)
    cv.rect(-4, 15.6, 207, -3.4, "frame")
    return cv.svg(), W, H


# ============================================================== D-401 DETAILS
def details():
    p = "cd"
    W, H = 1100, 720
    root = Cv(1, 1, 0, 0)
    root.add(defs(p))
    root.add(f'<rect class="sheet-bg" width="{W}" height="{H}"/>')
    title_strip(root, 24, 26, "D-401", "STAIR, SEA STEPS, PIER AND PLANTER DETAILS",
                "Footprints as traced; risers fitted to the level change · D1 18 px · D2 26 px · D3 24 px · D4 7 px = 1 m · avatars 1.30 m")
    out = [root.svg()]
    panels = [(20, 60), (560, 60), (20, 390), (560, 390)]
    for (x, y) in panels:
        out.append(f'<rect class="frame-in" x="{x}" y="{y}" width="520" height="310"/>')

    def head(cv, x, y, no, title, sub):
        cv.add(f'<circle class="bubble" cx="{x + 22}" cy="{y + 24}" r="12"/>'
               f'<text class="t-lbl" x="{x + 22}" y="{y + 27.5}" text-anchor="middle">{no}</text>'
               f'<text class="t-head" x="{x + 42}" y="{y + 24}">{esc(title)}</text>'
               f'<text class="t-sm" x="{x + 42}" y="{y + 37}">{esc(sub)}</text>')

    # D1 main stair: footprint 16.6 m, 2 x 16R, tread 0.42, landing 3.10
    x, y = panels[0]
    cv = Cv(18, -18, x + 40, y + 262, 13, 2.6)
    head(cv, x, y, "D1", "MAIN STAIR · SECTION", "traced footprint 12.8 × 16.6 m · street +8.40 to plaza +3.60")
    y0 = 18.67
    earth = [(13, Z_ST), (y0, Z_ST), (y0 + .3, Z_ST - .3), (36.5, Z_PL - 1.0), (36.5, 2.6), (13, 2.6)]
    cv.poly(earth, "poche")
    cv.poly(earth, "", f' fill="url(#{p}-earth)"')
    s1, ye = steps_profile(y0, Z_ST, 16, .45)
    s2, ye2 = steps_profile(ye + 3.1, Z_ST - 2.4, 16, .45)
    prof = [(13, Z_ST)] + s1 + s2 + [(36.5, Z_PL)]
    cv.poly(prof + [(36.5, Z_PL - .4), (ye2, Z_PL - .4), (ye + 3.1, 5.6), (ye, 5.6), (y0, Z_ST - .4)], "conc")
    cv.pline(prof, "ln-h")
    cv.line(y0, Z_ST + .9, ye, Z_ST - 2.4 + .9, "ln")
    cv.line(ye, 6.9, ye + 3.1, 6.9, "ln")
    cv.line(ye + 3.1, 6.9, ye2, Z_PL + .9, "ln")
    avatar(cv, 15.5, Z_ST)
    avatar(cv, ye + 1.5, 6.0)
    avatar(cv, 35, Z_PL)
    vdim(cv, y0 - .6, 6.0, Z_ST, "16R × 0.150")
    vdim(cv, 36.0, Z_PL, 6.0, "2.40", side=1)
    hdim(cv, y0, ye, 4.4, "15T × 0.45 = 6.75")
    hdim(cv, ye, ye + 3.1, 4.8, "3.10")
    hdim(cv, y0, ye2, 3.2, f"{ye2 - y0:.2f} RUN = TRACED 16.6")
    etag(cv, 13.4, Z_ST, "+8.40 FORECOURT")
    etag(cv, ye + 3.5, 6.0, "+6.00 LANDING")
    cv.text(13.2, 1.7, "Tread 0.45 with riser 0.15 keeps the traced 16.6 m run and reads as the long stair in the reference.", "t-sm", "start")
    out.append(cv.svg())

    # D2 seaside steps: promenade +3.15 to sand +0.90, 15R x 0.15, tread 0.75
    x, y = panels[1]
    cv = Cv(26, -26, x + 40, y + 262, -2, .3)
    head(cv, x, y, "D2", "SEA WALL + SEASIDE STEPS · SECTION", "traced footprints 11.7 × 11.3 m (west) and 11 × 11.2 m (east)")
    cv.poly([(11.2, Z_BC), (15.6, Z_BC - .1), (15.6, .3), (0, .3)], "z-sand")
    cv.poly([(10.5, Z_BC), (15.6, Z_BC - .1), (15.6, .3), (0, .3)], "", f' fill="url(#{p}-sand)"')
    earth = [(-2, Z_PR - .15), (-.4, Z_PR - .15), (-.4, .3), (-2, .3)]
    cv.poly(earth, "poche")
    cv.poly(earth, "", f' fill="url(#{p}-earth)"')
    cv.rect(-.4, .3, 0, Z_PR - .15, "conc")
    cv.rect(-2, Z_PR - .15, 0, Z_PR, "z-timber")
    cv.rect(-2, Z_PR - .15, 0, Z_PR, "ln")
    s, ye = steps_profile(0, Z_PR, 15, .80)
    cv.poly(s + [(ye, .3), (0, .3)], "conc")
    cv.line(-.08, Z_PR, -.08, Z_PR + 1.1, "ln-b")
    cv.line(0, Z_PR + .9, ye, Z_BC + .9, "ln")
    avatar(cv, -1.1, Z_PR)
    avatar(cv, 5.3, Z_PR - .15 * 8)
    avatar(cv, 13.4, Z_BC - .05)
    vdim(cv, ye + .5, Z_BC, Z_PR, "15R × 0.150 = 2.25", side=1)
    hdim(cv, 0, ye, .0, f"14T × 0.80 = {ye:.2f}")
    vdim(cv, -1.5, Z_PR, Z_PR + 1.1, "1.10")
    etag(cv, -1.9, Z_PR, "+3.15", below=True)
    etag(cv, 14.2, Z_BC - .05, "+0.90 SAND")
    cv.text(-1.9, 4.75, "Long 0.80 m treads keep the traced length and double as seating facing the sea.", "t-sm", "start")
    out.append(cv.svg())

    # D3 pier cross-section, 7.5 m deck
    x, y = panels[2]
    cv = Cv(24, -24, x + 260, y + 232, 0, 0)
    head(cv, x, y, "D3", "PIER · CROSS-SECTION", "traced deck 7.5 m wide, heading 15° east of south · head platform 27 × 11.5 m")
    cv.rect(-8, -2.4, 8, 0, "water")
    cv.line(-8, 0, 8, 0, "ln-water")
    cv.rect(-8, -2.8, 8, -2.4, "poche")
    cv.rect(-8, -2.8, 8, -2.4, "", f' fill="url(#{p}-earth)"')
    cv.line(-8, -2.4, 8, -2.4, "ln-h")
    cv.rect(-3.75, 2.3, 3.75, Z_PIER, "z-timber")
    cv.rect(-3.75, 2.3, 3.75, Z_PIER, "ln")
    cv.rect(-3.5, 1.9, 3.5, 2.3, "conc")
    for u in (-3.1, 0, 3.1):
        cv.rect(u - .2, -2.4, u + .2, 1.9, "conc")
    for u in (-3.5, 3.5):
        cv.line(u, Z_PIER, u, Z_PIER + 1.1, "ln")
        cv.line(u - .1, Z_PIER + 1.1, u + .1, Z_PIER + 1.1, "ln-h")
    cv.line(-2.7, Z_PIER, -2.7, Z_PIER + 3.6, "ln")
    cv.circle(-2.7, Z_PIER + 3.7, .18, "chalk-y")
    avatar(cv, .4, Z_PIER)
    avatar(cv, 2.2, Z_PIER)
    cv.add(f'<circle class="avatar" cx="{n(cv.X(6.2))}" cy="{n(cv.Y(0) - 4)}" r="5"/>')
    hdim(cv, -3.75, 3.75, 4.6, "7.50 DECK (TRACED)")
    vdim(cv, 4.6, 0, Z_PIER, "2.40", side=1)
    vdim(cv, 4.6, Z_PIER, Z_PIER + 1.1, "1.10", side=1)
    vdim(cv, -5.4, -2.0, 0, "≥ 2.00 AT HEAD")
    etag(cv, -7.6, 0, "±0.00 SWL")
    out.append(cv.svg())

    # D4 central planter: plan + section
    x, y = panels[3]
    pl = Cv(7, 7, x + 140, y + 178, 0, 0)
    head(pl, x, y, "D4", "CENTRAL PLANTER + BENCH RING", "traced: bed Ø19 · bench ring Ø27 · tree crown Ø22 · gaps on the diagonals")
    pl.circle(0, 0, 15, "z-paver")
    for q in range(4):
        a0, a1 = q * 90 + 52, q * 90 + 128
        pl.poly(sector(0, 0, 9.5, 13.5, a0, a1, 18), "prop")
        pl.poly(sector(0, 0, 11.2, 13.3, a0 + 2, a1 - 2, 16), "bed")
    pl.circle(0, 0, 9.5, "bed")
    pl.circle(0, 0, 9.5, "wall6")
    pl.circle(0, 0, 11, "tree", ' fill-opacity=".35" stroke-dasharray="3 2"')
    hdim(pl, -13.5, 13.5, -16, "Ø27.0")
    hdim(pl, -9.5, 9.5, 15.6, "Ø19.0 BED")
    pl.text(-19, -12, "PLAN", "t-lbl", "start")
    out.append(pl.svg())
    sc = Cv(7, -7, x + 390, y + 250, 0, 0)
    sc.rect(-15, -.6, 15, 0, "poche")
    sc.rect(-15, -.6, 15, 0, "", f' fill="url(#{p}-earth)"')
    sc.line(-15, 0, 15, 0, "ln-h")
    for s_ in (-1, 1):
        sc.rect(s_ * 9.5, 0, s_ * 11.2, .45, "conc")
        sc.rect(s_ * 11.2, 0, s_ * 13.5, .6, "z-lawn")
        sc.rect(s_ * 9.5, 0, s_ * 9.2, .6, "solid")
    sc.rect(-9.2, .4, 9.2, .55, "z-lawn")
    tree_elev(sc, 0, .55, 11, 22, 4)
    avatar(sc, 10.3, .45, seated=True)
    avatar(sc, -14, 0)
    vdim(sc, 14.4, 0, .6, "0.60", side=1)
    sc.text(-15, 16, "SECTION", "t-lbl", "start")
    out.append(sc.svg())
    return "\n".join(out), W, H


# ================================================================ schedules
CORRECTIONS = [
    ("Scale bar", "1:500 · 50 m = 195 px (3.9 px/m)", "6 px = 1 m", "Measured on the road (two lanes ≈ 7 m), people and doors. The bar disagrees with everything drawn."),
    ("Whole park", "≈ 330 × 260 m by the bar", "≈ 207 × 158 m", "Same drawing, read at the true scale."),
    ("Layout and area shapes", "as drawn", "kept exactly", "Every outline on L-101 is traced from the reference in pixels and divided by 6. Use the reference underlay to check."),
    ("Food trucks", "7.5 × 4.2 m", "6.5 × 2.5 m", "Real truck size at the traced positions and headings."),
    ("Parasols", "Ø 5 m", "Ø 3.0 m", "Large café parasol at each traced spot."),
    ("Stage speakers", "3.3 m boxes", "1.6 m", "Real PA stack size at the traced corners."),
    ("Main stair", "16.6 m long, no landing shown", "2 × 16R · tread 0.45 · landing 3.10", "Fits the traced footprint and the 4.80 m drop from the forecourt."),
    ("NW and E stairs", "9.3–9.5 m long", "32R · tread 0.30", "The traced length matches 4.80 m of rise exactly."),
    ("East stairs to the truck walkway and stage", "≈ 6 m long", "20R · 3.00 m drop", "The street falls toward the station, so these stairs are shorter."),
    ("Seaside steps", "11 × 11 m", "15R · tread 0.80", "2.25 m drop from the promenade; long treads double as seating."),
    ("Curved steps at the lawn tip", "≈ 10 treads drawn", "11R · raked lawn +3.60 → +4.80",
     "The flight in the reference needs a 1.65 m drop, so the event lawn rises gently away from the stage (1:18). It also gives the back rows a view over the front."),
    ("Heights", "none (flat image)", "street +8.40 → +6.00 · plaza +3.60 · promenade +3.15 · sand +0.90", "Set from the stair lengths in the reference; see L-201 and L-202."),
]
KEPT = ("Traced sizes at true scale: open plaza Ø53 m, central planter bed Ø19 m with a Ø27 m bench ring and a Ø22 m tree, "
        "stage deck 26 × 21 m, event lawn ≈ 30 × 22 m, promenade 6–13 m wide, pier 7.5 × 34 m with a 27 × 11.5 m head, "
        "arcade 34 × 27 m, fashion shop 34 × 17.5 m, lifestyle shop 23 × 21 m, beach 30–36 m deep.")

LOCATIONS = [
    (1, "City Street (Entrance)", "+8.40", "E1", "road 6.7 m · forecourt 43 × 7.5 m", "Spawn A at the crosswalk; main stair down from the forecourt."),
    (2, "Central Plaza", "+3.60", "C–F 2–4", "open paving Ø53 m", "Planter bed Ø19, bench ring Ø27, tree Ø22, four tree islands, cat statue, chalk art."),
    (3, "Arcade (Indoor)", "+4.05", "A–B 2–3", "34 × 27 m, parapet +10.20", "Interior as in the reference; game-controller front on the plaza (A-501) with 3 entrance steps; roof terrace +9.60."),
    (4, "Café (Indoor + Outdoor)", "+3.60", "A–B 4", "23 × 9 m + L-terrace", "Terrace faces the plaza and the promenade; 5 parasols."),
    (5, "Shop (Fashion / Goods)", "+3.60 / +8.40", "A–B 2", "34 × 17.5 m, 2 floors", "Upper floor opens onto the kiosk strip; east stair to the roof deck."),
    (6, "Food Truck Zone", "+3.60", "F–G 1–2", "36 × 14 m pad + walkway", "4 trucks, 6 parasol tables, string lights, deck on the west end."),
    (7, "Small Stage (Events)", "deck +4.20, lawn +3.60 → +4.80", "H–J 1–3", "deck 26 × 21 m · lawn ≈ 30 × 22 m", "Deck shape and lawn traced; top plaza and 20R stair from the street."),
    (8, "Shop (Lifestyle / Souvenir)", "+3.60", "G–H 3–4", "23 × 21 m + stalls", "Yellow trim, awnings and stall row as traced; east terrace beside the curved path."),
    (9, "Beach Promenade", "+3.15", "A–H 4–5", "146 m long · 6–13 m wide", "3 steps down from the plaza at five openings; rail and lamps along the sea wall."),
    (10, "Beach Area", "+0.90 → ±0.00", "A–H 5–7", "30–36 m deep", "Parasols, hut, surf boards, rocks at the west end."),
    (11, "Pier / Photo Spot", "+2.40", "H–I 5–7", "7.5 × 34 m + head 27 × 11.5 m", "Heading 15° east of south as traced; photo spot marker and lounge on the head."),
    (12, "Side Path (to Town / Station)", "+6.00 → +3.60", "J 1–3", "4.7 m wide, ramp 1:19", "Spawn B at the top; ends at the curved steps and the coastal walk."),
]

METRICS = [
    ("Avatar height (assumed)", "1.30 m · capsule r 0.34", "Chibi proportions. Every other number scales from this."),
    ("Max step height", "0.45 m", "Bench ring seats (0.45) and planter edges (0.60) can be hopped onto."),
    ("Main paths", "5–13 m", "Promenade 6–13 m, main stair 12.8 m, curved path 5.5 m, coastal walk 5 m."),
    ("Exterior stairs", "riser 0.15 · tread 0.30–0.80", "Treads stretched where the traced footprint is long."),
    ("Ramps", "≤ 1:12", "East side path averages 1:19."),
    ("Rails", "1.10 m", "Above the assumed 0.90 m jump apex."),
    ("Under the pier", "1.50 m clear", "Avatars (1.30 m) can walk under the deck to the east sand."),
    ("Doorway · interior clear", "3.0 × 3.2 m · ≥ 4.5 m", "Camera boom 3.5 m never clips."),
    ("Swim transition", "depth > 0.90 m", "About 15 m out from the shoreline."),
    ("Target players", "30–50 per instance", "Plaza Ø53 ≈ 2,200 m² plus promenade, lawn and beach."),
]

NOTES = {
    "l101": [
        "Every outline here is traced from the reference image in pixels and divided by 6 (the image's true scale). Turn on Reference underlay to see the original under the plan at 1:1.",
        "Only real-world objects were resized: trucks, parasols and speakers. Stairs keep their traced footprints with risers fitted to the level change.",
        "The coastal street falls about 2.4 m toward the station, which is why the eastern stairs are shorter than the main stair.",
        "Key numbers 1–12 match the reference's key list. Grid cells are 20 × 20 m (A–J, 1–8). Use Zoom to read furniture, stair treads and railings.",
        "Table S-4 lists every link between walkable areas; the build fails if any area is unreachable from Spawn A.",
    ],
    "l201": [
        "Cut on the main axis through the crosswalk, main stair and central planter, looking east.",
        "The plaza sits 4.80 m below the forecourt. The promenade is 3 steps (0.45 m) below the plaza, and the sand is 2.25 m below the promenade.",
        "The shoreline is about 37 m from the sea wall on this axis; wading depth runs out 15 m further.",
    ],
    "l202": [
        "Cut through the centre of the plaza, looking north at the street wall, the stairs, the food trucks and the stage deck.",
        "The street wall drops from 4.80 m in the west to 2.40 m at the east path because the street falls toward the station.",
        "The arcade (6.0 m) and the lifestyle shop (5.4 m) stay low so the stage and the street trees read over them.",
    ],
    "d401": [
        "D1: the traced 16.6 m main stair carries 4.80 m in two flights of 16 risers with 0.45 m treads and a 3.10 m landing.",
        "D2: the traced 11 m seaside steps carry 2.25 m in 15 risers with 0.80 m treads that double as seating.",
        "D3: the pier deck is 7.5 m wide as traced, 2.40 m above still water, with at least 2.00 m depth at the head.",
        "D4: the planter bed (Ø19), bench ring (Ø27) and tree crown (Ø22) are traced; gaps sit on the diagonals as in the reference.",
    ],
}

# Walkable areas and the links between them. main() checks every area is
# reachable from Spawn A, so a disconnected zone fails the build.
AREAS = {
    "sidewalk": "Street sidewalk +8.40 → +6.00", "forecourt": "Forecourt +8.40", "kiosks": "Kiosk strip +8.40",
    "fashion_up": "Fashion shop upper floor +8.40", "fashion": "Fashion shop +3.60", "plaza": "Central plaza +3.60",
    "arcade": "Arcade +4.05", "arcade_roof": "Arcade roof terrace +9.60", "cafe": "Café +3.60", "terrace": "Café terrace +3.60", "trucks": "Food truck zone + walkway +3.60",
    "lifestyle": "Lifestyle shop +3.60", "east_terrace": "Lifestyle east terrace +3.60", "curved": "Curved path +3.60 → +3.15",
    "stage_top": "Stage top plaza +3.60", "deck": "Stage deck +4.20", "lawn": "Event lawn +3.60 → +4.80 (raked)", "east_path": "East side path +6.00 → +4.80",
    "landing": "Lawn tip landing +4.80", "coast": "Coastal walk +3.15", "junction": "Junction +3.15", "prom": "Beach promenade +3.15",
    "lane": "West lane +8.40 → +3.15", "beach": "Beach +0.90 → ±0.00", "beach_e": "East sand", "rocks_w": "West rocks",
    "rocks_e": "East rocks", "pier": "Pier +2.40", "head": "Pier head +2.40", "sea": "Sea",
}
LINKS = [
    ("sidewalk", "forecourt", "Open frontage"),
    ("sidewalk", "kiosks", "Open frontage"),
    ("kiosks", "fashion_up", "Upper-floor shopfront on the kiosk strip"),
    ("fashion_up", "arcade_roof", "Door and 8R stair onto the arcade roof"),
    ("fashion_up", "fashion", "Stair inside the shop"),
    ("plaza", "fashion_up", "Glazed stair core, SE corner · 2 × 16R"),
    ("forecourt", "plaza", "Main stair · 12.8 m · 2 × 16R + landing"),
    ("forecourt", "plaza", "E stair · 4.3 m · 32R"),
    ("sidewalk", "plaza", "NW stair · 5.2 m · 32R"),
    ("sidewalk", "trucks", "Stair to the truck walkway · 20R"),
    ("sidewalk", "stage_top", "Stage stair · 20R"),
    ("sidewalk", "east_path", "Side path top · Spawn B"),
    ("sidewalk", "lane", "West lane top"),
    ("lane", "prom", "Lane foot connector"),
    ("plaza", "fashion", "East doors"),
    ("plaza", "arcade", "East doors · 3 steps"),
    ("plaza", "cafe", "Terrace edge and door"),
    ("cafe", "terrace", "Open front"),
    ("terrace", "prom", "Open edge"),
    ("plaza", "trucks", "Same paving"),
    ("plaza", "lifestyle", "West doors"),
    ("lifestyle", "east_terrace", "Around the stall row"),
    ("plaza", "prom", "3 steps at five openings"),
    ("trucks", "curved", "Walkway east end"),
    ("curved", "east_terrace", "Open edge"),
    ("stage_top", "deck", "Deck edge · 4R"),
    ("deck", "lawn", "Open deck edge"),
    ("curved", "lawn", "North end, level with the path"),
    ("east_path", "landing", "Path foot"),
    ("lawn", "landing", "Lawn tip"),
    ("landing", "coast", "Curved steps · 11R"),
    ("curved", "junction", "Path foot"),
    ("coast", "junction", "Walk foot"),
    ("junction", "prom", "Promenade east end"),
    ("junction", "pier", "Pier stair · 5R"),
    ("pier", "head", "Same deck"),
    ("prom", "beach", "West seaside steps · 15R"),
    ("prom", "beach", "East seaside steps · 15R"),
    ("beach", "beach_e", "Under the pier · 1.50 m clear"),
    ("beach", "rocks_w", "Sand edge"),
    ("beach_e", "rocks_e", "Sand edge"),
    ("beach", "sea", "Shoreline"),
    ("head", "sea", "Swim ladder · dive spot"),
]


def check_connected(start="sidewalk"):
    adj = {k: set() for k in AREAS}
    for a, b, _ in LINKS:
        adj[a].add(b)
        adj[b].add(a)
    seen, todo = {start}, [start]
    while todo:
        for nb in adj[todo.pop()]:
            if nb not in seen:
                seen.add(nb)
                todo.append(nb)
    missing = sorted(set(AREAS) - seen)
    if missing:
        raise SystemExit(f"disconnected areas: {', '.join(missing)}")
    return len(seen)



def notes_html(k):
    return "\n".join(f'<li data-n="{i + 1:02d}">{esc(t)}</li>' for i, t in enumerate(NOTES[k]))


def page(svgs):
    css = (PAGE_CSS.replace("%LIGHT%", css_tokens(LIGHT)).replace("%FONTS%", css_tokens(FONTS))
           .replace("%DARK%", css_tokens(DARK, "    ")) + SVG_CSS + EXTRA_CSS)
    corr = "\n".join(f'<tr><td><b>{esc(a)}</b></td><td class="num was">{esc(b)}</td><td class="num">{esc(c)}</td><td>{esc(d)}</td></tr>'
                     for a, b, c, d in CORRECTIONS)
    locs = "\n".join(f'<tr><td class="num"><span class="kn">{k}</span></td><td><b>{esc(a)}</b></td><td class="num">{esc(b)}</td>'
                     f'<td class="num">{esc(c)}</td><td class="num">{esc(d)}</td><td>{esc(e)}</td></tr>'
                     for k, a, b, c, d, e in LOCATIONS)
    links = "\n".join(f'<tr><td>{esc(AREAS[a])}</td><td>{esc(AREAS[b])}</td><td>{esc(v)}</td></tr>' for a, b, v in LINKS)
    mets = "\n".join(f'<tr><td><b>{esc(a)}</b></td><td class="num">{esc(b)}</td><td>{esc(c)}</td></tr>' for a, b, c in METRICS)
    mini = svgs["site"][0].replace("cp-", "cpm-").replace('id="lyr-', 'id="mini-lyr-')
    with open(os.path.join(HERE, "reference.webp"), "rb") as f:
        ref64 = base64.b64encode(f.read()).decode()

    def sheet(sid, no, title, scale, key, minw, extra=""):
        body, w, h, label = svgs[key]
        return f"""
<section class="block" id="{sid}">
  <div class="block-head"><span class="sheet-no">{no}</span><h2>{esc(title)}</h2><span class="scale">{esc(scale)}</span></div>
  {extra}
  <div class="drawing" style="--minw:{minw}px">{wrap(body, w, h, label)}</div>
  <ul class="notes">{notes_html(sid)}</ul>
</section>"""

    layers = """
  <div class="layers" role="group" aria-label="Plan layers">
    <span class="lbl">Layers</span>
    <label><input type="checkbox" id="ly-zones" data-layer="lyr-zones" checked><span>Ground</span></label>
    <label><input type="checkbox" id="ly-props" data-layer="lyr-props" checked><span>Props</span></label>
    <label><input type="checkbox" id="ly-labels" data-layer="lyr-labels" checked><span>Labels</span></label>
    <label><input type="checkbox" id="ly-circ" data-layer="lyr-circ" checked><span>Routes</span></label>
    <label><input type="checkbox" id="ly-sight" data-layer="lyr-sight" checked><span>Sightlines</span></label>
    <label><input type="checkbox" id="ly-grid" data-layer="lyr-grid" checked><span>Grid</span></label>
    <label><input type="checkbox" id="ly-cuts" data-layer="lyr-cuts" checked><span>Section cuts</span></label>
    <label><input type="checkbox" id="ly-ref" data-layer="lyr-ref"><span>Reference underlay</span></label>
    <span class="lbl zl">Zoom</span>
    <button type="button" class="zb" data-zoom="1" aria-pressed="true">Fit</button>
    <button type="button" class="zb" data-zoom="2" aria-pressed="false">2×</button>
    <button type="button" class="zb" data-zoom="3" aria-pressed="false">3×</button>
  </div>"""

    return f"""<title>Japan Coastal Hangout Park</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONT_URL}">
<style>{css}</style>
<div class="wrap">
<header>
  <p class="eyebrow">Level design package · reference layout redrawn to true scale · rev E</p>
  <h1>Japan Coastal <span class="wave">Hangout Park</span></h1>
  <p class="lede">The reference top view, traced area by area and redrawn at its true scale. The image's 1:500 bar was wrong:
  measured against its road, people and doors, it reads at 6 px per metre, so the park is about 207 × 158 m. Every outline is
  traced from the image and divided by 6; only real objects such as trucks, parasols and speakers were resized, stairs got real
  risers, and the flat image now has levels. Turn on the reference underlay on L-101 to check the match.</p>
  <dl class="tblock">
    <div><dt>Footprint</dt><dd>≈ 207 × 158 m playable</dd></div>
    <div><dt>True scale of image</dt><dd>6 px = 1 m (bar said 3.9)</dd></div>
    <div><dt>Players</dt><dd>30–50 per instance</dd></div>
    <div><dt>Units</dt><dd>metres · 1 m = 100 UU</dd></div>
    <div><dt>Levels</dt><dd>+8.40 / +3.60 / +3.15 / sand +0.90</dd></div>
    <div><dt>Datum</dt><dd>±0.00 = sea level</dd></div>
  </dl>
  <ul class="index">
    <li><a href="#compare"><b>REF</b> Reference vs corrected</a></li>
    <li><a href="#corrections"><b>S-1</b> Scale corrections</a></li>
    <li><a href="#l101"><b>L-101</b> Site plan</a></li>
    <li><a href="#l201"><b>L-201</b> Section A–A</a></li>
    <li><a href="#l202"><b>L-202</b> Section B–B</a></li>
    <li><a href="#d401"><b>D-401</b> Details</a></li>
    <li><a href="#locations"><b>S-2</b> Key locations</a></li>
    <li><a href="#metrics"><b>S-3</b> Metrics</a></li>
    <li><a href="#connections"><b>S-4</b> Connections</a></li>
  </ul>
</header>

<section class="block" id="compare">
  <div class="block-head"><span class="sheet-no">REF</span><h2>Reference vs corrected</h2><span class="scale">same layout, true scale</span></div>
  <div class="compare">
    <figure><img src="data:image/webp;base64,{ref64}" alt="Reference top-view map generated with an image model: Japan Coastal Hangout Park"><figcaption>Reference (image gen) · scale bar unreliable</figcaption></figure>
    <figure><div class="drawing mini">{wrap(mini, svgs["site"][1], svgs["site"][2], "Corrected site plan")}</div><figcaption>Corrected · L-101 at 6 px = 1 m</figcaption></figure>
  </div>
</section>

<section class="block" id="corrections">
  <div class="block-head"><span class="sheet-no">S-1</span><h2>Scale corrections</h2><span class="scale">“as drawn” measured at 6 px/m</span></div>
  <div class="tablewrap"><table>
    <thead><tr><th>Element</th><th>As drawn</th><th>Corrected</th><th>Why</th></tr></thead>
    <tbody>{corr}</tbody>
  </table></div>
  <p class="kept">{esc(KEPT)}</p>
</section>

{sheet("l101", "L-101", "Site plan", "6 px = 1 m · grid 20 m", "site", 1100, layers)}
{sheet("l201", "L-201", "Section A–A", "H 5 px = 1 m · V 10 px = 1 m", "aa", 900)}
{sheet("l202", "L-202", "Section B–B", "H 4.6 px = 1 m · V 10 px = 1 m", "bb", 940)}
{sheet("d401", "D-401", "Details", "mixed scales, see sheet", "details", 900)}

<section class="block" id="locations">
  <div class="block-head"><span class="sheet-no">S-2</span><h2>Key locations</h2><span class="scale">numbering as in the reference</span></div>
  <div class="tablewrap"><table>
    <thead><tr><th>#</th><th>Location</th><th>Level</th><th>Grid</th><th>Corrected size</th><th>Notes</th></tr></thead>
    <tbody>{locs}</tbody>
  </table></div>
</section>

<section class="block" id="metrics">
  <div class="block-head"><span class="sheet-no">S-3</span><h2>Gameplay metrics</h2><span class="scale">confirm against the final avatar</span></div>
  <div class="tablewrap"><table>
    <thead><tr><th>Metric</th><th>Value</th><th>Why</th></tr></thead>
    <tbody>{mets}</tbody>
  </table></div>
</section>

<section class="block" id="connections">
  <div class="block-head"><span class="sheet-no">S-4</span><h2>Connections</h2><span class="scale">{len(LINKS)} links · {len(AREAS)} areas · all reachable from Spawn A</span></div>
  <div class="tablewrap"><table>
    <thead><tr><th>From</th><th>To</th><th>Via</th></tr></thead>
    <tbody>{links}</tbody>
  </table></div>
</section>

<footer><span>Japan Coastal Hangout Park · rev E · 2026-10-05</span><span>Source: docs/maps/coastal-hangout-park/build.py</span><span>Standalone SVGs in svg/</span></footer>
</div>
<script>
document.querySelectorAll('.zb').forEach(function (b) {{
  b.addEventListener('click', function () {{
    var svg = document.querySelector('#l101 .drawing svg');
    var k = Number(b.dataset.zoom);
    svg.style.width = (k * 100) + '%';
    svg.style.maxWidth = 'none';
    document.querySelectorAll('.zb').forEach(function (o) {{ o.setAttribute('aria-pressed', String(o === b)); }});
  }});
}});
document.querySelectorAll('[data-layer]').forEach(function (cb) {{
  cb.addEventListener('change', function () {{
    document.querySelectorAll('#l101 #' + cb.dataset.layer).forEach(function (g) {{ g.toggleAttribute('hidden', !cb.checked); }});
  }});
}});
</script>
"""


EXTRA_CSS = """
.compare { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; margin-top: 14px; }
.compare figure { margin: 0; min-width: 0; }
.compare img { display: block; width: 100%; height: auto; border: 1px solid var(--rule); }
.compare .drawing.mini { margin-top: 0; }
.compare .drawing.mini svg { min-width: 0; }
.compare figcaption { font: 600 13px var(--f-cond); letter-spacing: .08em; text-transform: uppercase; color: var(--ink-2); margin-top: 8px; }
td.was { color: var(--accent); text-decoration: line-through; text-decoration-thickness: 1px; }
.kn { display: inline-grid; place-items: center; width: 22px; height: 22px; border-radius: 50%; background: var(--ink); color: var(--sheet); font: 700 12px var(--f-cond); }
.zb { font: 600 13px var(--f-cond); letter-spacing: .06em; text-transform: uppercase; border: 1px solid var(--rule); background: var(--sheet); color: var(--ink); padding: 5px 11px; border-radius: 999px; cursor: pointer; }
.zb[aria-pressed="true"] { background: var(--ink); color: var(--sheet); border-color: var(--ink); }
.zb:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.zl { margin-left: 12px; }
.kept { margin: 12px 0 0; font-size: 15px; color: var(--ink-2); max-width: 90ch; }
"""


def main():
    builders = {
        "site": (site_plan, "L-101 Site plan", "L-101-site-plan.svg"),
        "aa": (section_aa, "L-201 Section A-A", "L-201-section-AA.svg"),
        "bb": (section_bb, "L-202 Section B-B", "L-202-section-BB.svg"),
        "details": (details, "D-401 Details", "D-401-details.svg"),
    }
    print("connected areas:", check_connected())
    svgs = {}
    os.makedirs(os.path.join(HERE, "svg"), exist_ok=True)
    with open(os.path.join(HERE, "reference.webp"), "rb") as f:
        ref_uri = "data:image/webp;base64," + base64.b64encode(f.read()).decode()
    for k, (fn, label, fname) in builders.items():
        body, w, h = fn()
        svgs[k] = (site_plan(underlay=ref_uri)[0] if k == "site" else body, w, h, label)
        with open(os.path.join(HERE, "svg", fname), "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n' + wrap(body, w, h, label, standalone=True) + "\n")
    with open(os.path.join(HERE, "index.html"), "w", encoding="utf-8") as f:
        f.write(page(svgs))
    print("wrote index.html and", len(builders), "SVG sheets")


if __name__ == "__main__":
    main()
