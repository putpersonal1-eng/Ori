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
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from drawkit import *  # noqa: E402,F401,F403

HERE = os.path.dirname(os.path.abspath(__file__))

# Levels
Z_STREET, Z_PLAZA, Z_STAGE, Z_PIER, Z_BEACH = 8.4, 3.6, 4.2, 2.4, 1.2

SHORE = [("M", 172, 106), ("C", 152, 122, 110, 135, 40, 134)]
WADE = [("M", 184, 114), ("C", 162, 134, 112, 150, 40, 148)]
CURVED_PATH = [("M", 150, 36), ("C", 156, 52, 162, 70, 173, 87)]
COAST_WALK = [("M", 192, 57), ("C", 188, 66, 186, 80, 177, 93)]
STAGE_F = (192, 19.5)          # focus of the stage fan (NE corner)
PLAZA_C = (91, 59)           # centre of the plaza circle


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
S = 6                                    # px per metre on the site plan
SH_PTS = [(36, 128), (48, 133.4), (62, 135), (78, 134.2), (92, 133), (106, 131.4), (120, 128.4), (134, 124.4),
          (148, 119), (160, 113), (168, 108.4), (174, 104.6), (179, 102), (183, 100.5)]
WADE_PTS = [(38, 142), (50, 147.5), (64, 149.2), (80, 148.6), (94, 147.4), (108, 145.6), (122, 142.4), (136, 138),
            (150, 132.4), (162, 126), (171, 120.4), (180, 115.4), (186, 112), (190, 108)]
DEEP_PTS = [(36, 158), (52, 161), (80, 161), (110, 159), (136, 153), (156, 145), (172, 137), (186, 128),
            (198, 118), (206, 108), (210, 100)]
COAST_PTS = [(202, 40), (200.5, 46), (200, 52), (199.5, 58), (200.5, 63.5), (205, 66.5), (206, 71), (204, 75.5),
             (198.5, 78.5), (195, 83), (191.5, 89), (188, 94), (185, 97)]
CURVE_C = [(157.2, 41.2), (158.8, 50), (161.5, 60), (165.3, 72), (169.6, 82), (172.5, 88)]
COAST_C = [(191.8, 57.5), (190.2, 64), (189.2, 70), (187.8, 77), (184.8, 84), (180.8, 90), (177, 93.6)]
GROVE_C = [(163.5, 62.5), (170, 64.5), (177, 68), (183, 70), (188.8, 71.2)]
LANE_C = [(7, 13), (7, 86)]
WROCK = [(-6, 96), (4, 95.4), (12, 99), (20, 106), (28, 115), (34, 124), (38, 131), (40, 139), (35, 148), (26, 156),
         (14, 160), (-6, 160)]
EROCK = [(179, 99.5), (186, 97.5), (193, 100), (196, 106), (192, 113), (185, 115.5), (180, 110)]


def arc_pts(cx, cy, r, a0, a1, step=2.0):
    k = max(2, int(abs(a1 - a0) / step) + 1)
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / (k - 1))),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / (k - 1)))) for i in range(k)]


def band(cv, centre_pts, width, fill="paver", edge="ink-3"):
    """Curved path drawn as an outlined band along a Catmull-Rom centreline."""
    d = cv.d(cr_cmds(centre_pts, closed=False))
    cv.add(f'<path d="{d}" style="fill:none;stroke:var(--{edge});stroke-width:{n(width * S + 1.6)};stroke-linejoin:round"/>')
    cv.add(f'<path d="{d}" style="fill:none;stroke:var(--{fill});stroke-width:{n(width * S)};stroke-linejoin:round"/>')


def stair(cv, x0, y0, x1, y1, flights, tread=.3, landing=None, rail_x=()):
    """N-S stair: treads every 0.3 m in each flight, cheek lines, handrails, DN arrow."""
    cv.rect(x0, y0, x1, y1, "z-paver")
    y = y0
    for i, cnt in enumerate(flights):
        for k in range(cnt):
            cv.line(x0, y + k * tread, x1, y + k * tread, "tread")
        y += (cnt - 1) * tread + tread
        if landing and i < len(flights) - 1:
            y += landing - tread
    cv.rect(x0, y0, x1, y1, "ln")
    for x in rail_x:
        cv.line(x, y0, x, y1, "rail")
    cv.line(x0 + .3, y0, x0 + .3, y1, "ln-m")
    cv.line(x1 - .3, y0, x1 - .3, y1, "ln-m")


def maneki(cv, u, v):
    cv.rect(u - 1.5, v - 1.5, u + 1.5, v + 1.5, "prop")
    cv.ellipse(u, v + .3, .9, .7, "statue")
    cv.circle(u, v - .55, .6, "statue")
    cv.poly([(u - .55, v - .9), (u - .35, v - 1.35), (u - .15, v - .95)], "statue")
    cv.poly([(u + .55, v - .9), (u + .35, v - 1.35), (u + .15, v - .95)], "statue")
    cv.circle(u + .75, v - .2, .22, "chalk-p")


def truck(cv, x0, y0, L=6.5, Wd=2.5, vertical=False, seed=0):
    if not vertical:
        cv.rect(x0 + 1.4, y0 - .1, x0 + 1.4 + .2, y0 + Wd + .1, "shadow")
        cv.rect(x0, y0, x0 + L, y0 + Wd, "bldg-l")
        cv.rect(x0 + L - 1.6, y0 + .15, x0 + L - .1, y0 + Wd - .15, "roof-2")
        cv.line(x0 + L - 1.6, y0, x0 + L - 1.6, y0 + Wd, "ln-m")
        cv.rect(x0 + .6, y0 + Wd, x0 + L - 2.2, y0 + Wd + 1.1, "", f' fill="url(#cp-stripe{("", "y", "c")[seed % 3]})"')
        cv.rect(x0 + .6, y0 + Wd, x0 + L - 2.2, y0 + Wd + 1.1, "ln-m")
    else:
        cv.rect(x0, y0, x0 + Wd, y0 + L, "bldg-l")
        cv.rect(x0 + .15, y0 + L - 1.6, x0 + Wd - .15, y0 + L - .1, "roof-2")
        cv.rect(x0 - 1.1, y0 + .6, x0, y0 + L - 2.2, "", ' fill="url(#cp-stripey)"')
        cv.rect(x0 - 1.1, y0 + .6, x0, y0 + L - 2.2, "ln-m")


def site_plan():
    p = "cp"
    W, H = 1660, 1150
    cv = Cv(S, S, 56, 56, -6, -14)
    A = cv.add
    A(defs(p))
    A(f'<rect class="sheet-bg" width="{W}" height="{H}"/>')

    def pat(name):
        return f' fill="url(#{p}-{name})"'

    sh = cr_sample(SH_PTS, per=8)
    wade = cr_sample(WADE_PTS, per=8)
    deep = cr_sample(DEEP_PTS, per=8)
    coast = cr_sample(COAST_PTS, per=6)
    curve = cr_sample(CURVE_C, per=10)
    curve_w = offset_pts(curve, -2.5)
    fx, fy = STAGE_F

    # ================================================================ ground
    A('<g id="lyr-zones">')
    # sea: deep base, depth bands, waves
    cv.rect(-6, 40, 210, 160, "z-deep")
    cv.poly(wade + deep[::-1], "z-mid")
    cv.poly(sh + wade[::-1], "z-sea")
    cv.rect(-6, 40, 210, 160, "", pat("water"))
    cv.pline(wade, "ln-f", ' stroke-dasharray="5 3"')
    cv.pline(deep, "ln-f", ' stroke-dasharray="2 4"')
    # land base
    land = [(-6, -14), (210, -14), (210, 40)] + coast + [(180, 95.5), (177.5, 94), (-6, 94)]
    cv.poly(land, "z-lawn")
    cv.poly(land, "", pat("lawn"))
    # beach: sand, wet band, foam
    sand = [(2, 94), (177.5, 94), (180, 95.5), (184, 97.5)] + sh[::-1] + [(30, 118), (20, 106), (10, 98), (2, 96)]
    cv.poly(sand, "z-sand")
    cv.poly(sand, "", pat("sand"))
    cv.poly(sh + offset_pts(sh, 2.6)[::-1], "z-wet")
    cv.pline(sh, "ln-water")
    cv.pline(wobble(offset_pts(sh, -.8), .35, 1.2, 3), "foam")
    cv.pline(wobble(offset_pts(sh, -2.4), .55, .7, 9), "foam-d")
    cv.pline(wobble(offset_pts(sh, -4.6), .7, .5, 21), "foam-d")
    # town, road, sidewalks
    cv.rect(-6, -14, 210, 0, "z-town")
    cv.rect(-6, -14, 210, 0, "", pat("hatch"))
    for a, b, c in [(-6, 40, -3), (44, 79, -2.5), (99, 122, -4), (126, 156, -3), (160, 210, -3.5)]:
        cv.rect(a + 1, -14, b - 1, c, "roof")
        cv.line(a + 1, (-14 + c) / 2, b - 1, (-14 + c) / 2, "ln-m")
    cv.rect(82, -14, 96, 2, "z-road")
    cv.line(89, -14, 89, 2, "lane")
    cv.rect(-6, 0, 210, 2, "z-paver")
    cv.rect(-6, 2, 210, 10, "z-road")
    cv.line(-6, 6, 82, 6, "lane")
    cv.line(96, 6, 210, 6, "lane")
    for x0, x1 in [(84, 96), (168, 174)]:
        for x in frange(x0 + .3, x1, 1.2):
            cv.rect(x, 2.6, x + .6, 9.4, "zebra")
    cv.rect(-6, 10, 210, 13, "z-paver")
    cv.rect(-6, 10, 210, 13, "", pat("pave"))
    cv.line(-6, 10, 210, 10, "ln")
    cv.line(-6, 2, 210, 2, "ln-m")
    # non-playable edges
    for (a, b, c, d) in [(-6, 13, 2, 94), (202, 13, 210, 40)]:
        cv.rect(a, b, c, d, "z-town")
        cv.rect(a, b, c, d, "", pat("hatch"))
    # kiosk strip (+8.40), west lane
    cv.rect(2, 13, 52, 19.4, "z-paver")
    cv.rect(2, 13, 52, 19.4, "", pat("pave"))
    cv.rect(2, 13, 12, 86, "z-paver")
    for y in frange(21, 86, 8):
        for k in range(3):
            cv.line(2, y + k * .4, 12, y + k * .4, "tread")
    # plaza paving (+3.60) with ring pattern, clipped to the plaza outline
    ring_outer = arc_pts(fx, fy, 43, 170, 151, 1)
    plaza = [(46, 19), (152, 19)] + ring_outer + [q for q in curve_w if q[1] < 86] + [(170.6, 86), (46, 86)]
    A(f'<clipPath id="{p}-plz"><path d="{cv.d([("M",) + plaza[0]] + [("L",) + q for q in plaza[1:]] + [("Z",)])}"/></clipPath>')
    cv.poly(plaza, "z-paver")
    cv.poly(plaza, "", pat("pave"))
    cx, cy = PLAZA_C
    A(f'<g clip-path="url(#{p}-plz)">')
    cv.circle(cx, cy, 28.4, "z-paver")
    for r0, r1 in [(7.4, 8.2), (17.6, 18.4), (27.6, 28.4)]:
        cv.poly(sector(cx, cy, r0, r1, 0, 359.9, 72), "band")
    for r in frange(10, 27.6, 2):
        if abs(r - 18) > .9:
            cv.circle(cx, cy, r, "joint")
    for k in range(36):
        a = math.radians(k * 10)
        for r0, r1 in [(8.2, 17.6), (18.4, 27.6)]:
            cv.line(cx + r0 * math.cos(a), cy + r0 * math.sin(a), cx + r1 * math.cos(a), cy + r1 * math.sin(a), "joint")
    A('</g>')
    # chalk art
    for i, (u, v, c, r) in enumerate([(71.5, 58, "chalk-c", 2.4), (73.5, 62.5, "chalk-y", 1.5), (111, 67.5, "chalk-p", 2.1),
                                      (108, 71, "chalk-y", 1.3), (104, 51, "chalk-c", 1.2)]):
        cv.path(cr_cmds(blob(u, v, r * 1.3, r * .8, 40 + i, .3, 9)), c, ' fill-opacity=".45"')
    # street bank (planted slope) and retaining walls
    for i, (a, b) in enumerate([(52.2, 53.8), (59.4, 84.6), (97.4, 103.6), (108.4, 192.8)]):
        shrub_bed(cv, [(a, 13.6), (b, 13.6), (b, 19), (a, 19)], seed=3 + i, density=.55, smooth=False)
    for (a, b) in [(54, 59), (85, 97), (104, 108)]:
        cv.rect(a, 13, b, 17, "z-paver")
        cv.rect(a, 13, b, 17, "", pat("pave"))
        cv.line(a, 13, a, 17, "ln")
        cv.line(b, 13, b, 17, "ln")
    cv.rect(110, 19, 152, 21.5, "bed")
    for x in frange(111, 151, 2.2):
        canopy(cv, x, 20.3, 1.1, int(x), "shrub", shadow=False, detail=False)
    # stage area: path ring, service path, lawn, deck
    cv.poly(sector(fx, fy, 39, 43, 92, 170, 60), "z-paver")
    cv.poly(sector(fx, fy, 13, 39, 163, 170, 8), "z-paver")
    for a in range(94, 170, 6):
        q0 = (fx + 39 * math.cos(math.radians(a)), fy + 39 * math.sin(math.radians(a)))
        q1 = (fx + 43 * math.cos(math.radians(a)), fy + 43 * math.sin(math.radians(a)))
        cv.line(q0[0], q0[1], q1[0], q1[1], "joint")
    cv.pline(arc_pts(fx, fy, 39, 92, 170, 1), "ln-m")
    cv.pline(arc_pts(fx, fy, 43, 92, 170, 1), "ln-m")
    cv.poly(sector(fx, fy, 14.2, 39, 100, 161, 40), "z-lawn")
    cv.poly(sector(fx, fy, 14.2, 39, 100, 161, 40), "", pat("lawn"))
    for r in (21, 27, 33):
        cv.pline(arc_pts(fx, fy, r, 101, 160, 2), "ln-m", ' stroke-dasharray="1.5 2.5"')
    cv.poly(sector(fx, fy, 14.2, 39, 100, 161, 40), "ln-m")
    cv.poly(sector(fx, fy, 3, 13, 106, 161, 30), "z-timber")
    for r in frange(4, 13, 1):
        cv.pline(arc_pts(fx, fy, r, 106, 161, 3), "pat-s")
    cv.poly(sector(fx, fy, 3, 13, 106, 161, 30), "ln")
    for r in (13.4, 13.8):
        cv.pline(arc_pts(fx, fy, r, 106, 161, 3), "tread")
    cv.pline(arc_pts(fx, fy, 3, 106, 161, 4), "wall-l")
    # east bed between lawn and ramp
    shrub_bed(cv, [(191.2, 33), (192.6, 33), (192.6, 46.5), (190.6, 54.6), (187.6, 55.4), (189.6, 42)], seed=11, density=.6)
    # side path: ramp runs + landings, garden steps
    cv.rect(193, 13, 199, 47.5, "z-paver")
    for (a, b) in [(13.5, 20.7), (22.2, 29.4), (30.9, 38.1), (39.6, 46.8)]:
        cv.rect(193, a, 199, b, "z-conc")
        cv.line(196, a + .8, 196, b - .8, "ln-m", f' marker-end="url(#{p}-arrk)"')
    railing(cv, [(193, 13.5), (193, 47.5)], 2.4)
    railing(cv, [(199, 13.5), (199, 47.5)], 2.4)
    cv.poly(sector(180, 47, 13, 19, 0, 40, 16), "z-paver")
    for a in frange(0, 40.1, 2.5):
        aa = math.radians(a)
        cv.line(180 + 13 * math.cos(aa), 47 + 13 * math.sin(aa), 180 + 19 * math.cos(aa), 47 + 19 * math.sin(aa), "tread")
    cv.poly(sector(180, 47, 13, 19, 0, 40, 16), "ln-m")
    cv.poly(sector(180, 47, 11.6, 13, 2, 40, 12), "bed")
    cv.poly(sector(180, 47, 19, 20.6, 0, 36, 12), "bed")
    # curved path, grove footpath, coastal walk, lookout spur
    band(cv, CURVE_C, 5)
    band(cv, GROVE_C, 2.5, "conc")
    band(cv, COAST_C, 5)
    cv.rect(190.5, 68.5, 196, 71.5, "z-paver")
    cv.circle(199.5, 70, 4.5, "z-timber")
    for k in range(-4, 5):
        cv.line(199.5 + k, 70 - math.sqrt(max(0, 20.25 - k * k)), 199.5 + k, 70 + math.sqrt(max(0, 20.25 - k * k)), "pat-s")
    cv.circle(199.5, 70, 4.5, "ln")
    # promenade boardwalk
    cv.rect(2, 86, 176, 94, "z-timber")
    cv.rect(2, 86, 176, 94, "", pat("board"))
    cv.line(2, 86, 176, 86, "ln-m")
    # rocks: west outcrop, tide pool, east cluster, riprap, rocks in the surf
    cv.poly(WROCK, "z-wet")
    cv.poly(WROCK, "", pat("sand"))
    cv.path(cr_cmds(blob(15, 131, 3.2, 2.2, 5, .25, 9)), "z-sea")
    cv.path(cr_cmds(blob(15, 131, 3.2, 2.2, 5, .25, 9)), "ln-water")
    rock_cluster(cv, WROCK, 70, .6, 5.6, seed=7)
    for i, (u, v, r) in enumerate([(45, 141, 1.7), (52, 149, 2.3), (43, 154, 1.4), (31, 159, 2.0), (58, 156, 1.1)]):
        rock(cv, u, v, r, 500 + i, foam=True)
    rock_cluster(cv, EROCK, 14, .8, 3.2, seed=19)
    rr = cr_sample(COAST_PTS[2:], per=10)
    rip = offset_pts(rr, -1.3)
    for i in range(0, len(rip), 2):
        u, v = rip[i]
        rock(cv, u, v, .7 + (i * 37 % 10) / 10, 900 + i, shadow=False)
    A('</g>')

    # ================================================================ built
    A('<g id="lyr-built">')
    # walls: kiosk strip edge, bank foot (with stair openings)
    cv.line(12, 19.4, 52, 19.4, "wall-l")
    for a, b in [(52, 54), (59, 85), (97, 104), (108, 193)]:
        cv.line(a, 19, b, 19, "wall-l")
    railing(cv, [(12, 19.2), (26, 19.2)], 2)
    railing(cv, [(34, 19.2), (52, 19.2)], 2)
    # street kiosks with striped awnings
    for i, x0 in enumerate((13.5, 20.5, 36, 43.5)):
        cv.rect(x0, 14.6, x0 + 6.5, 18.2, "roof")
        cv.line(x0, 16.4, x0 + 6.5, 16.4, "ln-m")
        cv.rect(x0, 13.4, x0 + 6.5, 14.6, "", pat(("stripe", "stripey", "stripec", "stripe")[i]))
        cv.rect(x0, 13.4, x0 + 6.5, 14.6, "ln-m")
    cv.rect(26, 19.4, 34, 21, "z-paver")
    railing(cv, [(26, 19.4), (26, 21)], 1.6)
    railing(cv, [(34, 19.4), (34, 21)], 1.6)
    # bus shelter at spawn A
    cv.rect(70, 11, 78, 12.6, "roof")
    bench(cv, 74, 11.8, 5, 0, .5)
    # street lamps
    for x in range(8, 210, 20):
        cv.circle(x, 12.5, .5, "prop")
    # stairs: main, NW, E
    stair(cv, 85, 17, 97, 29, (16, 16), landing=3.0, rail_x=(89, 93))
    stair(cv, 54, 17, 59, 29, (16, 16), landing=3.0, rail_x=(56.5,))
    stair(cv, 104, 17, 108, 29, (16, 16), landing=3.0, rail_x=(106,))
    for (a, b) in [(80, 85), (97, 102)]:
        cv.rect(a, 19, b, 29, "bed")
        cv.rect(a, 19, b, 29, "wall6")
    # fashion & goods: roof plan
    cv.rect(15.6, 19.4, 47.6, 35.4, "shadow")
    cv.rect(14, 21, 46, 37, "roof")
    cv.rect(14.6, 21.6, 45.4, 36.4, "ln-m")
    for y0 in (24.5, 31):
        cv.rect(19, y0, 41, y0 + 1.6, "roof-2")
        for x in frange(19, 41, 2.2):
            cv.line(x, y0, x, y0 + 1.6, "ln-f")
    for (u, v) in [(17, 28.6), (20.5, 28.6), (43, 28.6)]:
        cv.rect(u - 1, v - .8, u + 1, v + .8, "prop")
        cv.circle(u, v, .55, "joint")
    cv.rect(46, 25, 48.6, 33, "prop")
    door_swing(cv, 46, 27, 1.8, 0, 90)
    door_swing(cv, 46, 31, 1.8, 0, -90)
    # arcade: roof removed, interior shown
    cv.rect(14, 37, 46, 64, "arc-y")
    cv.rect(14, 37, 46, 64, "wall6")
    for row in range(3):
        for col in range(4):
            u, v = 23 + col * 4.2, 42.5 + row * 5
            cv.rect(u, v, u + 1.6, v + 1.6, "prop")
            cv.rect(u + 1.9, v, u + 3.5, v + 1.6, "prop")
            cv.circle(u + .8, v + .8, .45, "chalk-c")
            cv.circle(u + 2.7, v + .8, .45, "chalk-p")
    for k in range(6):
        cv.rect(15, 39 + k * 2.6, 17.6, 40.6 + k * 2.6, "prop")
        cv.rect(17.6, 39.3 + k * 2.6, 18.6, 40.3 + k * 2.6, "prop-d")
    for k in range(3):
        cv.rect(15.2 + k * 3, 59.6, 17.6 + k * 3, 62.8, "prop")
    cv.poly([(37, 58), (44.6, 58), (44.6, 62.6), (43.2, 62.6), (43.2, 59.4), (37, 59.4)], "prop")
    cv.rect(38, 39, 44.6, 45.6, "prop")
    for (u, v, c) in [(39.6, 40.6, "chalk-p"), (42.8, 40.6, "chalk-c"), (39.6, 43.9, "chalk-y"), (42.8, 43.9, "chalk-p")]:
        cv.rect(u - 1.2, v - 1.2, u + 1.2, v + 1.2, c)
    cv.line(46, 47, 46, 55, "gap")
    cv.line(46, 47, 46, 55, "glass")
    door_swing(cv, 46, 47, 2, 0, 90)
    door_swing(cv, 46, 55, 2, 0, -90)
    cv.rect(46, 46, 48.6, 56, "prop")
    # vending alcove between arcade and café
    for u in (41.5, 43.4):
        cv.rect(u, 64.6, u + 1.6, 65.6, "umb-c")
    # café: interior + L-terrace
    terr = [(36, 67), (46, 67), (46, 86), (14, 86), (14, 78), (36, 78)]
    cv.poly(terr, "z-timber")
    cv.poly(terr, "", pat("board"))
    cv.rect(14, 67, 36, 78, "z-paver")
    cv.rect(14, 67, 36, 78, "wall6")
    cv.line(16, 78, 34, 78, "gap")
    cv.line(16, 78, 34, 78, "glass")
    cv.poly([(16, 68.4), (28, 68.4), (28, 69.6), (17.2, 69.6), (17.2, 72), (16, 72)], "prop")
    for (u, v) in [(21, 73), (25, 73), (29, 73), (33, 70), (33, 74), (21, 76.2), (27, 76.2)]:
        cv.circle(u, v, .55, "prop")
        cv.circle(u - .9, v, .28, "prop-d")
        cv.circle(u + .9, v, .28, "prop-d")
    cv.line(36, 70, 36, 75, "gap")
    door_swing(cv, 36, 70, 1.6, 0, 90)
    for i, (u, v) in enumerate([(19, 82), (25.5, 82.4), (32, 82), (40.5, 80.5), (41, 72.5)]):
        parasol(cv, u, v, 1.3, ("umb-y", "umb-c", "umb-y", "umb-p", "umb-y")[i], chairs=4)
    shrub_bed(cv, [(14.4, 84.8), (24, 84.8), (24, 85.8), (14.4, 85.8)], seed=31, density=1.2, rmin=.4, rmax=.6, smooth=False)
    shrub_bed(cv, [(44.6, 68), (45.8, 68), (45.8, 85.6), (44.6, 85.6)], seed=32, density=1.2, rmin=.4, rmax=.6, smooth=False)
    # food trucks + seating + string lights
    truck(cv, 115.5, 23.6, seed=0)
    truck(cv, 124.5, 23.6, seed=1)
    truck(cv, 133.5, 23.6, seed=2)
    truck(cv, 145.5, 27, vertical=True)
    for i, (u, v) in enumerate([(118, 31.5), (125, 33.5), (132, 31.5), (139, 33.5), (121.5, 40.5), (130, 41.5)]):
        parasol(cv, u, v, 1.3, ("umb-c", "umb-y", "umb-p")[i % 3], chairs=4)
    poles = [(112.5, 22.5), (150.5, 22.5), (150.5, 37), (112.5, 37)]
    for i in range(4):
        a, b = poles[i], poles[(i + 1) % 4]
        cv.line(a[0], a[1], b[0], b[1], "string")
        for t in frange(.1, 1, .12):
            cv.circle(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, .2, "bulb")
    cv.line(112.5, 22.5, 150.5, 37, "string")
    for (u, v) in poles:
        cv.circle(u, v, .4, "post")
    # lifestyle & souvenir: roof plan, fascia, kiosks
    cv.rect(132.6, 49.4, 152.6, 65.4, "shadow")
    cv.rect(131, 51, 151, 67, "roof")
    cv.rect(131.8, 51.8, 150.2, 66.2, "trim-y")
    cv.rect(136, 55, 146, 63, "roof-2")
    for x in frange(136, 146, 2):
        cv.line(x, 55, x, 63, "ln-f")
    cv.rect(128.6, 55.5, 131, 62.5, "prop")
    door_swing(cv, 131, 57, 1.6, 180, 90)
    door_swing(cv, 131, 61, 1.6, 180, 270)
    for i, x0 in enumerate((131, 136.5, 142, 147.5)):
        cv.rect(x0, 68.5, x0 + 4.5, 72.5, "roof")
        cv.rect(x0, 68.5, x0 + 4.5, 69.6, "", pat(("stripey", "stripe")[i % 2]))
        cv.rect(x0, 68.5, x0 + 4.5, 69.6, "ln-m")
    cv.rect(124.6, 63.4, 128.2, 67, "roof")
    cv.rect(123.6, 63.4, 124.6, 67, "", pat("stripec"))
    # stage props
    for a in (110, 157):
        q = (fx + 11.6 * math.cos(math.radians(a)), fy + 11.6 * math.sin(math.radians(a)))
        cv.rect(q[0] - .8, q[1] - .8, q[0] + .8, q[1] + .8, "solid")
    # promenade rail, beach stairs, pier
    for a, b in [(2, 55), (61, 120), (126, 172.5)]:
        railing(cv, [(a, 94), (b, 94)], 2)
    for (a, b) in [(55, 61), (120, 126)]:
        stair(cv, a, 94, b, 100.2, (8, 8), landing=2.0, rail_x=((a + b) / 2,))
    stair(cv, 172.5, 94, 177.5, 96.1, (8,))
    cv.rect(172.5, 96.1, 177.5, 132, "z-timber")
    cv.rect(172.5, 96.1, 177.5, 132, "", pat("boardh"))
    cv.rect(156, 132, 180, 142, "z-timber")
    cv.rect(156, 132, 180, 142, "", pat("board"))
    cv.pline([(172.5, 96.1), (172.5, 132), (156, 132), (156, 142), (180, 142), (180, 132), (177.5, 132), (177.5, 96.1)], "ln")
    railing(cv, [(172.8, 96.4), (172.8, 132.3)], 3)
    railing(cv, [(177.2, 96.4), (177.2, 132.3)], 3)
    railing(cv, [(172.8, 132.3), (156.3, 132.3), (156.3, 141.7), (179.7, 141.7), (179.7, 132.3), (177.2, 132.3)], 3)
    for y in frange(102, 132, 6):
        cv.circle(173.3, y, .35, "ln-b")
        cv.circle(176.7, y, .35, "ln-b")
    for y in (105, 114, 123):
        cv.circle(173.4, y, .45, "prop")
    cv.rect(166, 141.2, 170, 141.9, "solid")
    cv.text(168, 140.4, "PHOTO FRAME", "t-sm halo")
    bench(cv, 160, 137, 3, 90)
    bench(cv, 176, 137, 3, 90)
    cv.rect(156.1, 135.4, 156.9, 137, "prop")
    cv.circle(179.2, 133.4, .5, "ring-acc")
    # beach hut, surf rack, kayak
    cv.rect(108.6, 107.4, 112.6, 111.4, "shadow")
    cv.rect(108, 108, 112, 112, "roof")
    cv.rect(108, 108, 112, 112, "", pat("thatch"))
    cv.line(108, 108, 112, 112, "ln-m")
    cv.line(112, 108, 108, 112, "ln-m")
    cv.rect(108, 112, 112, 113.6, "z-timber")
    cv.rect(108, 112, 112, 113.6, "ln-m")
    cv.rect(134, 99.4, 140.6, 100.6, "prop")
    for k in range(4):
        cv.ellipse(134.8 + k * 1.65, 101.6, .35, 1.1, ("umb-c", "umb-y", "umb-p", "umb-c")[k])
    cv.ellipse(146, 103.5, 2.0, .45, "umb-y", ' transform="rotate(-20 ' + n(cv.X(146)) + " " + n(cv.Y(103.5)) + ')"')
    A('</g>')

    # ================================================================ planting + props
    A('<g id="lyr-props">')
    # plaza islands with seat walls
    for i, (u, v, rx, ry, kind, tr) in enumerate([(66, 38, 6.4, 4.8, "tree", [(64.2, 37.2, 3.6), (69, 40, 2.8)]),
                                                  (64, 72, 5.8, 4.4, "tree", [(64, 72, 3.8)]),
                                                  (118, 47, 4.8, 3.8, "sak", [(118, 47, 3.4)]),
                                                  (150.6, 45.5, 3.0, 2.6, "tree", [(150.6, 45.5, 2.6)]),
                                                  (154.5, 78, 3.6, 3.0, "tree", [(154.5, 78, 3.0)])]):
        pts = blob(u, v, rx, ry, 60 + i, .14, 12)
        cv.path(cr_cmds(offset_pts(pts + pts[:1], 0)[:-1]), "wall6")
        shrub_bed(cv, pts, seed=70 + i, density=.7)
        for (a, b, r) in tr:
            canopy(cv, a, b, r, 80 + i + int(a), kind)
    # central planter, bench ring with slats, uplights
    for q in range(4):
        a0, a1 = q * 90 + 9, q * 90 + 81
        cv.poly(sector(cx, cy, 5.5, 7, a0, a1, 16), "prop")
        for a in frange(a0 + 4, a1, 4):
            aa = math.radians(a)
            cv.line(cx + 5.5 * math.cos(aa), cy + 5.5 * math.sin(aa), cx + 7 * math.cos(aa), cy + 7 * math.sin(aa), "joint")
    cv.circle(cx, cy, 4, "bed")
    cv.circle(cx, cy, 4, "wall6")
    for q in range(4):
        aa = math.radians(q * 90 + 45)
        cv.circle(cx + 4.6 * math.cos(aa), cy + 4.6 * math.sin(aa), .3, "bulb")
    canopy(cv, cx, cy, 6.2, 3, "tree")
    maneki(cv, 107, 45)
    # west frontage beds + benches
    for i, (a, b) in enumerate([(21, 29), (39.5, 45.5), (57, 63), (67, 76)]):
        shrub_bed(cv, blob(49, (a + b) / 2, 2.4, (b - a) / 2, 90 + i, .1, 10), seed=95 + i, density=.8)
    for v in (33.5, 51.5):
        bench(cv, 49, v, 3, 90)
    # promenade-edge beds with palms
    for i, (a, b) in enumerate([(50, 63), (70, 84), (98, 112), (128, 141), (146, 158)]):
        shrub_bed(cv, blob((a + b) / 2, 84.9, (b - a) / 2, 1.1, 110 + i, .08, 12), seed=120 + i, density=.9, rmin=.5, rmax=.8)
        palm_top(cv, (a + b) / 2, 84.9, 3.0, 130 + i)
    # lamps
    for ang in (30, 150, 210, 330):
        a = math.radians(ang)
        cv.circle(cx + 27 * math.cos(a), cy + 27 * math.sin(a), .55, "prop")
        cv.circle(cx + 27 * math.cos(a), cy + 27 * math.sin(a), .2, "ink-f")
    for x in range(8, 172, 12):
        cv.circle(x, 93.1, .55, "prop")
        cv.circle(x, 93.1, .2, "ink-f")
    for a in range(105, 170, 16):
        q = (fx + 43.8 * math.cos(math.radians(a)), fy + 43.8 * math.sin(math.radians(a)))
        cv.circle(q[0], q[1], .5, "prop")
    for q in cr_sample(COAST_C, per=2)[1::3]:
        cv.circle(q[0] + 2.9, q[1], .5, "prop")
    # promenade benches facing the sea
    for x in (14, 38, 66, 86, 110, 134, 158):
        bench(cv, x, 92.1, 3, 0)
    # coastal walk railing (seaward side) + benches + lookout rail
    cwr = offset_pts(cr_sample(COAST_C, per=4), -2.6)
    railing(cv, [q for q in cwr if q[1] < 67.8 or q[1] > 72.2], 2.4)
    railing(cv, arc_pts(199.5, 70, 4.3, -80, 80, 8), 2.0)
    bench(cv, 197, 70, 2.4, 90)
    bench(cv, 186.8, 80.5, 2.4, 70)
    # trees: bank, west lane, grove, stage edge, coast
    trees = [(66, 16.4, 2.8), (74, 15.8, 2.4), (112, 16.2, 2.8), (122, 15.8, 2.4), (132, 16.2, 2.6),
             (142, 15.8, 2.4), (152, 16.2, 2.8), (162, 15.8, 2.4), (172, 16.2, 2.6), (182, 15.8, 2.4),
             (3.4, 26, 2.2), (10.6, 34, 2.2), (3.4, 46, 2.2), (10.6, 58, 2.2), (3.4, 70, 2.2), (10.6, 80, 2.0),
             (165.4, 60.2, 3.0), (178.6, 63.6, 2.6), (168.5, 75, 3.6), (180.5, 79.5, 3.0),
             (191.6, 38, 1.4), (190.8, 46, 1.8), (100, 23.5, 2.2)]
    for i, (u, v, r) in enumerate(trees):
        canopy(cv, u, v, r, 200 + i, "tree")
    for i, (u, v, r) in enumerate([(82.5, 23, 2.2), (16, 88.6, 2.4), (196, 64.4, 2.2), (202.6, 64.8, 1.9),
                                   (197, 76, 2.0), (184.6, 66.2, 2.0), (176.5, 85.4, 2.2)]):
        canopy(cv, u, v, r, 300 + i, "sak")
    for i, x in enumerate([24, 38, 70, 84, 104, 113, 134, 148, 162]):
        palm_top(cv, x, 97.6, 3.2, 400 + i)
    # beach furniture
    for i, (u, v, c) in enumerate([(46, 114, "umb-c"), (68, 111.5, "umb-y"), (92, 112, "umb-y"), (126, 114, "umb-p"),
                                   (143, 109.5, "umb-c")]):
        for s_ in (-1.2, 1.2):
            lounger(cv, u + s_, v + 2.6, 90)
            cv.rect(u + s_ - .25, v + 2.0, u + s_ + .25, v + 3.4, c, ' fill-opacity=".55"')
        parasol(cv, u, v, 1.3, c)
    for (u, v, c) in [(57, 121, "chalk-p"), (101, 119, "chalk-c"), (131, 120, "chalk-y")]:
        cv.rect(u - .8, v - .45, u + .8, v + .45, c, ' fill-opacity=".7"')
    cv.circle(70, 140.5, .8, "ring-acc")
    cv.circle(118, 136, .7, "ring-acc")
    cv.circle(100, 124, .35, "umb-p")
    A('</g>')

    # ================================================================ grid
    A('<g id="lyr-grid">')
    for x in range(0, 201, 20):
        cv.line(x, -14, x, 160, "grid")
    for y in range(0, 161, 20):
        cv.line(-6, y, 210, y, "grid")
    A('</g>')
    for i, letter in enumerate("ABCDEFGHIJ"):
        x = cv.X(10 + 20 * i)
        A(f'<circle class="bubble" cx="{n(x)}" cy="40" r="10"/><text class="t-lbl" x="{n(x)}" y="43.5" text-anchor="middle">{letter}</text>')
    for j in range(8):
        y = cv.Y(10 + 20 * j)
        A(f'<circle class="bubble" cx="36" cy="{n(y)}" r="10"/><text class="t-lbl" x="36" y="{n(y + 3.5)}" text-anchor="middle">{j + 1}</text>')

    # ================================================================ routes
    A('<g id="lyr-circ">')
    cv.pline([(90, 11.5), (91, 18), (91, 30), (88.5, 50), (88, 68), (90, 90), (123, 92), (123, 101), (140, 112),
              (168, 108), (175, 112), (175, 133), (168, 137)], "circ1", f' marker-end="url(#{p}-arr)"')
    for pts in [[(7, 11.5), (7, 84)], [(56.5, 11.5), (56.5, 29), (60, 40), (47.5, 51)], [(30, 16), (30, 22)],
                [(196, 11.5), (196, 46), (190, 55), (189, 66), (185, 82), (177.5, 92.5)],
                [(106, 11.5), (106, 29), (114, 36)], [(144, 38), (152, 29)],
                [(154, 33.5), (163, 47.5), (172, 55), (181.5, 59), (189, 60.5)],
                [(158.5, 46), (160, 60), (166, 74), (172, 86)], [(165, 63), (177, 68), (188, 71)],
                [(92, 52), (128, 59)], [(58, 93), (58, 101), (50, 110)], [(190, 70), (196, 70)]]:
        cv.pline(pts, "circ2", f' marker-end="url(#{p}-arr)"')
    A('</g>')

    # ================================================================ sightlines
    A('<g id="lyr-sight">')
    for (a, b, lab, lu, lv) in [((93, 15), (93, 159), "V1", 94.5, 35), ((196, 12), (168, 138), "V2", 186.5, 33),
                                ((40, 84), (164, 136), "V3", 46, 91)]:
        cv.line(a[0], a[1], b[0], b[1], "sight", f' marker-end="url(#{p}-arrt)"')
        cv.circle(a[0], a[1], .9, "teal-f")
        cv.text(lu, lv, lab, "t-lbl t-teal halo", "start")
    A('</g>')

    # ================================================================ cuts
    A('<g id="lyr-cuts">')
    cv.line(91, -14, 91, 160, "cut")
    cv.line(91, -14, 91, -8, "cut-h")
    cv.line(91, 154, 91, 160, "cut-h")
    section_bubble(cv, cv.X(91) + 16, cv.Y(-10), "A", 0)
    section_bubble(cv, cv.X(91) + 16, cv.Y(156), "A", 0)
    cv.line(-6, 59, 210, 59, "cut")
    cv.line(-6, 59, 0, 59, "cut-h")
    cv.line(204, 59, 210, 59, "cut-h")
    section_bubble(cv, cv.X(-2), cv.Y(59) - 16, "B", -90)
    section_bubble(cv, cv.X(206), cv.Y(59) - 16, "B", -90)
    A('</g>')

    # ================================================================ labels
    A('<g id="lyr-labels">')
    T = cv.text
    T(40, -7.4, "TOWN · NON-PLAYABLE", "t-sm halo")
    T(140, -7.4, "TOWN · NON-PLAYABLE", "t-sm halo")
    T(89, -9, "CITY STREET", "t-sm halo", rot=-90)
    T(40, 6.8, "COASTAL STREET · +8.40 · cars only", "t-sm halo")
    T(176, 6.8, "→ TO STATION / TOWN", "t-sm halo", "start")
    T(74, 9.6, "BUS STOP", "t-sm halo")
    T(31, 16.4, "KIOSKS +8.40", "t-sm halo")
    T(30, 20.6, "BRIDGE", "t-sm halo")
    T(30, 29.4, "FASHION & GOODS", "t-lbl halo")
    T(30, 34.6, "2 floors · roof plan", "t-sm halo")
    T(30, 56.2, "ARCADE · 32 × 27", "t-lbl halo")
    T(30, 58.6, "roof removed", "t-sm halo")
    T(25, 76.9, "CAFÉ 22 × 11", "t-lbl halo")
    T(30, 80.2, "TERRACE", "t-sm halo")
    T(42.5, 66.5, "VENDING", "t-sm halo")
    T(7, 52, "WEST LANE · stepped slope +8.40 → +3.60", "t-sm halo", rot=-90)
    T(91, 31.4, "MAIN STAIR 12 m · 2 × 16R", "t-sm halo")
    T(56.5, 31.4, "NW STAIR", "t-sm halo")
    T(106, 31.4, "E STAIR", "t-sm halo")
    T(91, 49.6, "CENTRAL PLAZA", "t-zone halo")
    T(91, 52.6, "+3.60 · paving Ø56", "t-sm halo")
    T(91, 68.8, "planter Ø8 · bench ring Ø14", "t-sm halo")
    T(107, 42.4, "CAT STATUE", "t-sm halo")
    T(131, 38.6, "FOOD TRUCK ZONE", "t-lbl halo")
    T(131, 44.6, "4 trucks · 6 tables", "t-sm halo")
    T(141, 59.4, "LIFESTYLE &", "t-lbl halo")
    T(141, 61.8, "SOUVENIR 20 × 16", "t-sm halo")
    T(141, 75, "KIOSKS", "t-sm halo")
    T(174, 39, "SMALL STAGE", "t-lbl halo")
    T(174, 41.8, "deck +4.20 · lawn +3.60", "t-sm halo")
    T(162, 34.6, "SERVICE PATH", "t-sm halo", rot=-12)
    T(170, 52.4, "LAWN RING PATH", "t-sm halo", rot=-35)
    T(196, 30, "SIDE PATH · RAMP 1:12 · 4 runs", "t-sm halo", rot=90)
    T(185.5, 52.6, "GARDEN STEPS 16R", "t-sm halo", "end")
    T(199.5, 77.2, "SAKURA LOOKOUT", "t-sm halo")
    T(181.6, 86, "COASTAL WALK", "t-sm halo", rot=-58)
    T(175, 67.4, "GROVE PATH", "t-sm halo", rot=22)
    T(162.6, 56, "CURVED PATH 5 m", "t-sm halo", rot=76)
    T(76, 90.4, "BEACH PROMENADE · +3.60 · 8 m", "t-zone halo")
    T(58, 104, "2 × 8R", "t-sm halo")
    T(123, 104, "2 × 8R", "t-sm halo")
    T(96, 126, "BEACH AREA", "t-big halo")
    T(96, 128.8, "+1.20 → ±0.00", "t-sm halo")
    T(110, 106.6, "HUT", "t-sm halo")
    T(137.4, 98.6, "SURF RACK", "t-sm halo")
    T(170.6, 118, "PIER 5 × 36 · +2.40", "t-sm halo", "end")
    T(168, 145.6, "PIER HEAD · PHOTO SPOT 24 × 10", "t-lbl halo")
    T(18, 140, "ROCKS", "t-sm halo")
    T(15, 127.4, "TIDE POOL", "t-sm halo")
    T(76, 143.4, "WADE ZONE ±0.00 → −0.90", "t-sm halo")
    T(80, 155.8, "−0.90 → −1.80", "t-sm halo")
    T(130, 158.4, "SWIM ZONE · to −2.50", "t-sm halo")
    T(207, 120, "SEA", "t-sm halo", rot=90)
    for (u, v, letter, lu, anchor) in [(90, 11.5, "A", 93.6, "start"), (196, 11.5, "B", 192.4, "end")]:
        cv.circle(u, v, 2.2, "acc-f")
        T(u, v + .9, letter, "t-lbl t-inv")
        T(lu, v + 1, f"SPAWN {letter}", "t-lbl t-acc halo", anchor)
    for (u, v, k) in [(80, 7.5, 1), (79, 56, 2), (17.6, 40, 3), (15.8, 69.6, 4), (17.4, 24, 5), (113.6, 29.6, 6),
                      (181, 31.5, 7), (136, 48.2, 8), (36, 90.2, 9), (74.5, 125.6, 10), (181.6, 127, 11), (200.6, 18, 12)]:
        key(cv, u, v, k)
    A('</g>')
    cv.rect(-6, -14, 210, 160, "frame")

    # ================================================================ legend + title block
    lx, ly = 1374, 56
    A(f'<g transform="translate({lx} {ly})">')
    A('<rect class="frame-in" width="266" height="664"/>')
    A('<text class="t-head" x="14" y="26">LEGEND</text>')
    rows = [("z-road", None, "Street · cars only"), ("z-paver", "pave", "Stone paving · 2 m joints"),
            ("z-timber", "board", "Wood deck · promenade, pier, terrace"), ("z-lawn", "lawn", "Grass"),
            ("bed", None, "Planting bed · shrubs"), ("z-sand", "sand", "Sand · wet sand at the shoreline"),
            ("z-sea", None, "Wade · ±0.00 to −0.90"), ("z-mid", None, "Swim · −0.90 to −1.80"),
            ("z-deep", "water", "Swim · below −1.80"), ("roof", None, "Roof plan"), ("arc-y", None, "Interior shown (roof removed)"),
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
    entries = [("canopy", "Broadleaf tree · canopy to scale"), ("sak", "Cherry (sakura)"), ("palm", "Palm"),
               ("rock", "Boulder"), ("parasol", "Parasol + chairs"), ("bench", "Bench"), ("rail", "Railing · posts 2 m"),
               ("stair", "Stair · treads 0.30"), ("key", "Key location · reference numbering"), ("spawn", "Spawn point"),
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
    ccx, ccy = 1400, 760
    A(f'<circle class="frame-in" cx="{ccx}" cy="{ccy}" r="22"/>')
    A(f'<polygon class="ink-f" points="{ccx},{ccy - 20} {ccx + 7},{ccy + 7} {ccx},{ccy + 2} {ccx - 7},{ccy + 7}"/>')
    A(f'<text class="t-head" x="{ccx}" y="{ccy - 26}" text-anchor="middle">N</text>')
    bx, by = 1438, 758
    for k, (a, b) in enumerate([(0, 10), (10, 20), (20, 30)]):
        A(f'<rect class="{"ink-f" if k % 2 == 0 else "sheet-f"}" x="{bx + a * S}" y="{by}" width="{(b - a) * S}" height="6"/>')
    A(f'<rect class="ln" x="{bx}" y="{by}" width="{30 * S}" height="6"/>')
    for m in (0, 10, 20, 30):
        A(f'<text class="t-dim" x="{bx + m * S}" y="{by - 5}" text-anchor="middle">{m}</text>')
    A(f'<text class="t-sm" x="{bx}" y="{by + 19}">metres · true scale · grid 20 m</text>')
    tx, ty = 1374, 806
    A(f'<g transform="translate({tx} {ty})">')
    A('<rect class="frame" width="266" height="294"/>')
    A('<text class="t-title" x="14" y="32" style="font-size:15px">Japan Coastal Hangout Park</text>')
    A('<text class="t-sm" x="14" y="48">Reference layout redrawn to true scale · rev C</text>')
    A('<line class="ln" x1="0" y1="60" x2="266" y2="60"/>')
    fields = [("SHEET", "L-101 Site plan"), ("SCALE", "6 px = 1 m"), ("FOOTPRINT", "216 × 174 m drawn"),
              ("UNITS", "m · 1 m = 100 UU"), ("DATUM", "±0.00 = sea level"), ("NORTH", "up · sun from SW"),
              ("REVISION", "C · 2026-10-05"), ("STATUS", "Concept / blockout")]
    for i, (k, v) in enumerate(fields):
        col, row = i % 2, i // 2
        fx_, fy_ = 14 + col * 133, 82 + row * 52
        A(f'<text class="t-sm" x="{fx_}" y="{fy_}">{k}</text><text class="t-lbl" x="{fx_}" y="{fy_ + 16}">{esc(v)}</text>')
        if col == 0 and row < 3:
            A(f'<line class="ln-f" x1="0" y1="{fy_ + 30}" x2="266" y2="{fy_ + 30}"/>')
    A('<line class="ln-f" x1="133" y1="60" x2="133" y2="294"/>')
    A('</g>')
    return cv.svg(), W, H


# ============================================================== L-201 SECTION
def section_aa():
    p = "ca"
    W, H = 1000, 380
    cv = Cv(5, -10, 50, 250, -14, 0)
    A = cv.add
    A(defs(p))
    A(f'<rect class="sheet-bg" width="{W}" height="{H}"/>')
    title_strip(cv, 24, 30, "L-201", "SECTION A–A · X = 91 · STREET → PLAZA → BEACH · LOOKING EAST",
                "Horizontal 5 px = 1 m · vertical 10 px = 1 m (vertical exaggeration 2×) · light line = beyond")
    # beyond
    cv.rect(-14, 8.4, -2, 13.4, "beyond")
    for (a, b) in [(24, 26.5)]:
        cv.rect(a, 3.6, b, 6.4, "beyond")
    cv.text(25.2, 10.2, "FOOD TRUCKS beyond", "t-sm halo")
    cv.rect(51, 3.6, 67, 9.0, "beyond")
    cv.rect(51, 9.0, 67, 9.4, "chalk-y")
    cv.text(59, 4.7, "LIFESTYLE SHOP beyond", "t-sm halo")
    cv.rect(44.4, 3.6, 45.6, 6.6, "beyond")
    cv.circle(45, 7.2, .7, "statue")
    cv.rect(96.1, 2.1, 142, 2.4, "beyond")
    for y in frange(102, 142, 6):
        cv.line(y, 2.1, y, -2.0, "ln-m")
    cv.text(120, 2.9, "PIER DECK +2.40 beyond", "t-sm halo")
    cv.rect(110, .9, 114, 4.4, "beyond")
    cv.poly([(109.4, 4.4), (114.6, 4.4), (112, 5.2)], "beyond")
    cv.text(112, 5.8, "HUT", "t-sm")
    cv.line(111, .95, 111, 3.2, "ln-m")
    cv.ellipse(111, 3.3, 1.3, .25, "umb-y")
    for y in (92.8, 80.0):
        cv.line(y, 3.6, y, 8.6, "ln-m")
        cv.circle(y, 8.7, .7, "prop")
    palm_elev(cv, 98.5, 1.1, 6.2, 2)
    # ground
    top = [(-14, Z_STREET), (19, Z_STREET), (19, Z_PLAZA), (94, Z_PLAZA), (94, Z_BEACH), (132.6, 0), (147.6, -.9), (160, -2.5)]
    cv.poly([(132.6, 0), (160, 0), (160, -2.5), (147.6, -.9)], "water")
    cv.line(132.6, 0, 160, 0, "ln-water")
    poche = top + [(160, -4), (-14, -4)]
    cv.poly(poche, "poche")
    cv.poly(poche, "", f' fill="url(#{p}-earth)"')
    cv.pline(top, "ln-h")
    cv.rect(2, 8.4, 10, 8.45, "solid")
    cv.text(6, 9.1, "ROAD", "t-sm halo")
    # main stair (cut): flight 16R, landing 3.0, flight 16R
    st = [(17, Z_STREET)]
    z, y = Z_STREET, 17
    for flight in range(2):
        for k in range(16):
            z -= .15
            st.append((y, z + .15))
            st.append((y, z))
            if k < 15:
                y += .3
                st.append((y, z))
        if flight == 0:
            y += 3.0
            st.append((y, z))
    st += [(29, Z_PLAZA - .3), (24.5, 5.7), (21.5, 5.7), (17, 8.1)]
    cv.poly(st, "conc")
    cv.line(17, Z_STREET + .9, 21.5, 6.9, "ln")
    cv.line(24.5, 6.9, 29, 4.5, "ln")
    # central planter + bench ring (cut)
    for (a, b) in [(52, 53.5), (64.5, 66)]:
        cv.rect(a, Z_PLAZA, b, Z_PLAZA + .45, "conc")
    cv.rect(55, Z_PLAZA, 55.3, Z_PLAZA + .6, "solid")
    cv.rect(62.7, Z_PLAZA, 63, Z_PLAZA + .6, "solid")
    cv.rect(55.3, Z_PLAZA + .4, 62.7, Z_PLAZA + .55, "z-lawn")
    tree_elev(cv, 59, 4.15, 7.4, 9.6, 1)
    # promenade rail + sea wall
    cv.line(93.9, Z_PLAZA, 93.9, Z_PLAZA + 1.1, "ln")
    cv.rect(86, Z_PLAZA, 94, Z_PLAZA + .08, "z-timber")
    # people
    for (y, z) in [(11.5, Z_STREET + .15), (40, Z_PLAZA), (44, Z_PLAZA), (72, Z_PLAZA), (90, Z_PLAZA), (106, .97),
                   (122, .4)]:
        avatar(cv, y, z)
    avatar(cv, 53, Z_PLAZA + .45, seated=True)
    cv.add(f'<circle class="avatar" cx="{n(cv.X(140))}" cy="{n(cv.Y(0) - 3)}" r="3.4"/>')
    # tags, callouts, dims
    etag(cv, -12, Z_STREET, "+8.40 STREET")
    etag(cv, 31, Z_PLAZA, "+3.60 PLAZA", below=True)
    etag(cv, 76, Z_PLAZA, "+3.60 PROMENADE", below=True)
    etag(cv, 95.5, Z_BEACH, "+1.20 BEACH", below=True)
    etag(cv, 157, 0, "±0.00 SWL", anchor="end")
    etag(cv, 147.6, -.9, "−0.90 WADE LIMIT", below=True)
    callout(cv, 23, 6.2, 28, 12.6, "MAIN STAIR · 2 × 16R · LANDING 3.00")
    callout(cv, 59, 4.1, 66, 11.6, "PLANTER Ø8 · BENCH RING Ø14")
    callout(cv, 93.9, 4.3, 98, 9.8, "RAIL 1.10 · SEA WALL 2.40")
    vdim(cv, 16, Z_PLAZA, Z_STREET, "4.80", ext=19)
    vdim(cv, 96.6, Z_BEACH, Z_PLAZA, "2.40", side=1)
    segs = [(2, 13, "STREET"), (13, 29, "ENTRY"), (29, 86, "CENTRAL PLAZA"), (86, 94, "PROM."),
            (94, 132.6, "BEACH"), (132.6, 147.6, "WADE"), (147.6, 160, "SWIM")]
    for a, b, name in segs:
        hdim(cv, a, b, -5.2, f"{b - a:.1f}", ext=-4)
        cv.text((a + b) / 2, -7.0, name, "t-sm")
    hdim(cv, 2, 160, -8.6, "158.0 · STREET TO SOFT BOUNDARY", ext=-7.6)
    cv.rect(-14, 16, 160, -10, "frame")
    return cv.svg(), W, H


# ============================================================== L-202 SECTION
def section_bb():
    p = "cb"
    W, H = 1080, 360
    cv = Cv(4.6, -10, 46, 256, -6, 0)
    A = cv.add
    A(defs(p))
    A(f'<rect class="sheet-bg" width="{W}" height="{H}"/>')
    title_strip(cv, 24, 30, "L-202", "SECTION B–B · Y = 59 · ARCADE → PLAZA → COAST · LOOKING NORTH",
                "Horizontal 4.6 px = 1 m · vertical 10 px = 1 m · light line = beyond (street wall, stairs, food trucks, stage)")
    # beyond: street wall with planting, stairs, trucks, stage, ramp
    cv.rect(46, Z_PLAZA, 193, Z_STREET, "beyond")
    for (a, b) in [(54, 59), (85, 97), (104, 108)]:
        cv.rect(a, Z_PLAZA, b, Z_STREET, "prop")
        for z in frange(Z_PLAZA + .6, Z_STREET, .6):
            cv.line(a, z, b, z, "ln-f")
    cv.text(91, 6.2, "MAIN STAIR", "t-sm halo")
    for i, x in enumerate((60, 70, 112, 124, 136, 150, 164, 176)):
        tree_elev(cv, x, Z_STREET, 4.6, 5.0, 10 + i)
    for (a, b) in [(116, 122.5), (125, 131.5), (134, 140.5)]:
        cv.rect(a, Z_PLAZA, b, Z_PLAZA + 2.8, "beyond")
    cv.text(121, 7.1, "FOOD TRUCKS", "t-sm halo")
    cv.poly([(172, Z_STAGE), (191, Z_STAGE), (191, Z_PLAZA), (172, Z_PLAZA)], "z-timber")
    cv.text(181.5, 4.6, "STAGE", "t-sm halo")
    cv.rect(193, 6.0, 199, Z_STREET, "beyond")
    cv.line(193, Z_STREET + 1.1, 199, Z_STREET + 1.1, "ln-m")
    cv.text(196, 7.4, "RAMP", "t-sm halo")
    cv.rect(106.4, Z_PLAZA, 107.6, Z_PLAZA + 3.0, "beyond")
    cv.circle(107, Z_PLAZA + 3.6, .7, "statue")
    # ground cut
    ground = [(-6, 5.4), (14, 5.4), (14, Z_PLAZA), (202.7, Z_PLAZA), (202.7, -1.0), (210, -2.0)]
    cv.poly([(202.7, 0), (210, 0), (210, -2.0), (202.7, -1.0)], "water")
    cv.line(202.7, 0, 210, 0, "ln-water")
    poche = ground + [(210, -3.4), (-6, -3.4)]
    cv.poly(poche, "poche")
    cv.poly(poche, "", f' fill="url(#{p}-earth)"')
    cv.pline(ground, "ln-h")
    cv.rect(-6, 5.4, 2, 12, "z-town")
    cv.rect(-6, 5.4, 2, 12, "", f' fill="url(#{p}-hatch)"')
    cv.text(-2, 13, "TOWN", "t-sm")
    # arcade (cut)
    cv.rect(14, Z_PLAZA, 46, 9.6, "sheet-f")
    cv.rect(14, Z_PLAZA, 14.4, 10.2, "solid")
    cv.rect(45.6, Z_PLAZA, 46, 10.2, "solid")
    cv.rect(14, 9.3, 46, 9.6, "solid")
    cv.rect(14.4, 9.0, 45.6, 9.3, "arc-y")
    for u in (18, 23.2, 28.4, 33.6):
        cv.rect(u, Z_PLAZA, u + 2.2, Z_PLAZA + 1.7, "prop")
    cv.rect(36, Z_PLAZA, 44, Z_PLAZA + 1.0, "prop")
    cv.text(31, 7.6, "ARCADE +3.60 · 5.70 clear", "t-sm halo")
    # planters, central planter, lifestyle shop, kiosk
    cv.rect(46.6, Z_PLAZA, 51.4, Z_PLAZA + .6, "z-lawn")
    for (a, b) in [(84, 85.5), (96.5, 98)]:
        cv.rect(a, Z_PLAZA, b, Z_PLAZA + .45, "conc")
    cv.rect(87, Z_PLAZA, 87.3, Z_PLAZA + .6, "solid")
    cv.rect(94.7, Z_PLAZA, 95, Z_PLAZA + .6, "solid")
    cv.rect(87.3, Z_PLAZA + .4, 94.7, Z_PLAZA + .55, "z-lawn")
    tree_elev(cv, 91, 4.15, 7.4, 9.6, 3)
    cv.rect(131, Z_PLAZA, 151, 9.0, "sheet-f")
    cv.rect(131, Z_PLAZA, 131.4, 9.4, "solid")
    cv.rect(150.6, Z_PLAZA, 151, 9.4, "solid")
    cv.rect(131, 8.7, 151, 9.0, "solid")
    cv.rect(131, 9.0, 151, 9.4, "chalk-y")
    cv.rect(135, Z_PLAZA, 147, Z_PLAZA + 1.0, "prop")
    cv.text(141, 6.4, "LIFESTYLE & SOUVENIR", "t-sm halo")
    cv.rect(125, Z_PLAZA, 129, Z_PLAZA + 2.8, "bldg-l")
    cv.rect(124.6, 6.4, 129.4, 6.7, "umb-y")
    for x in (64, 118):
        cv.line(x, Z_PLAZA, x, 8.6, "ln")
        cv.circle(x, 8.7, .6, "prop")
    for i, x in enumerate((166, 182)):
        tree_elev(cv, x, Z_PLAZA, 5.6, 5.6, 20 + i)
    cv.line(202.5, Z_PLAZA, 202.5, Z_PLAZA + 1.1, "ln")
    for x in (24, 60, 72, 89, 93, 110, 159, 191):
        avatar(cv, x, Z_PLAZA)
    # tags + dims
    etag(cv, 3, 5.4, "+5.40 LANE")
    etag(cv, 54, Z_PLAZA, "+3.60 PLAZA", below=True)
    etag(cv, 160, Z_STREET, "+8.40 STREET beyond")
    etag(cv, 191.4, Z_STAGE, "+4.20")
    etag(cv, 208, 0, "±0.00", anchor="end")
    hdim(cv, 2, 12, 13.2, "10.0 LANE")
    hdim(cv, 14, 46, 13.2, "32.0 ARCADE", ext=10.2)
    hdim(cv, 52, 125, 13.2, "73.0 OPEN PLAZA")
    hdim(cv, 131, 151, 13.2, "20.0 SHOP", ext=9.4)
    hdim(cv, 84, 98, 2.2, "Ø14.0 BENCH RING")
    vdim(cv, 15.6, Z_PLAZA, 9.3, "6.00", side=1)
    vdim(cv, 152.6, Z_PLAZA, 9.0, "5.40", side=1)
    vdim(cv, 49.4, Z_PLAZA, Z_STREET, "4.80 WALL", side=1)
    cv.rect(-6, 15, 210, -3.4, "frame")
    return cv.svg(), W, H


# ============================================================== D-401 DETAILS
def details():
    p = "cd"
    W, H = 1100, 720
    root = Cv(1, 1, 0, 0)
    root.add(defs(p))
    root.add(f'<rect class="sheet-bg" width="{W}" height="{H}"/>')
    title_strip(root, 24, 26, "D-401", "STAIR, SEA WALL, PIER AND PLANTER DETAILS",
                "D1 20 px = 1 m · D2 32 px = 1 m · D3 24 px = 1 m · D4 12 px = 1 m · avatars 1.30 m")
    out = [root.svg()]
    panels = [(20, 60), (560, 60), (20, 390), (560, 390)]
    for (x, y) in panels:
        out.append(f'<rect class="frame-in" x="{x}" y="{y}" width="520" height="310"/>')

    def head(cv, x, y, no, title, sub):
        cv.add(f'<circle class="bubble" cx="{x + 22}" cy="{y + 24}" r="12"/>'
               f'<text class="t-lbl" x="{x + 22}" y="{y + 27.5}" text-anchor="middle">{no}</text>'
               f'<text class="t-head" x="{x + 42}" y="{y + 24}">{esc(title)}</text>'
               f'<text class="t-sm" x="{x + 42}" y="{y + 37}">{esc(sub)}</text>')

    # D1 main entrance stair
    x, y = panels[0]
    cv = Cv(20, -20, x + 70, y + 262, 12, 3.0)
    head(cv, x, y, "D1", "MAIN ENTRANCE STAIR · SECTION", "street +8.40 to plaza +3.60 · 12.00 wide · handrails every 4 m")
    earth = [(10, Z_STREET), (19, Z_STREET), (19, Z_PLAZA), (31, Z_PLAZA), (31, 3.0), (10, 3.0)]
    cv.poly(earth, "poche")
    cv.poly(earth, "", f' fill="url(#{p}-earth)"')
    st = [(17, Z_STREET)]
    z, yy = Z_STREET, 17
    for flight in range(2):
        for k in range(16):
            z -= .15
            st += [(yy, z + .15), (yy, z)]
            if k < 15:
                yy += .3
                st.append((yy, z))
        if flight == 0:
            yy += 3.0
            st.append((yy, z))
    st += [(29, 3.3), (24.5, 5.7), (21.5, 5.7), (17, 8.1)]
    cv.poly(st, "conc")
    cv.pline([(10, Z_STREET), (17, Z_STREET)], "ln-h")
    cv.pline([(29, Z_PLAZA), (31, Z_PLAZA)], "ln-h")
    cv.line(17, Z_STREET + .9, 21.5, 6.9, "ln")
    cv.line(21.5, 6.9, 24.5, 6.9, "ln")
    cv.line(24.5, 6.9, 29, 4.5, "ln")
    avatar(cv, 14, Z_STREET)
    avatar(cv, 23, 6.0)
    avatar(cv, 30, Z_PLAZA)
    vdim(cv, 16.2, 6.0, Z_STREET, "16R × 0.150 = 2.40")
    vdim(cv, 30.6, Z_PLAZA, 6.0, "2.40", side=1)
    hdim(cv, 17, 21.5, 4.5, "15T × 0.300 = 4.50")
    hdim(cv, 21.5, 24.5, 4.9, "3.00")
    hdim(cv, 17, 29, 3.4, "12.00 RUN")
    etag(cv, 10.4, Z_STREET, "+8.40 STREET")
    etag(cv, 25.5, 6.0, "+6.00 LANDING")
    callout(cv, 19.3, 7.6, 21, 9.6, "HANDRAIL 0.90", cls="t-sm halo")
    cv.text(10.2, 2.4, "Image drew one 16 m flight. Two flights with a landing keep 4.80 m of rise readable and restful.", "t-sm", "start")
    out.append(cv.svg())

    # D2 sea wall + beach stair
    x, y = panels[1]
    cv = Cv(32, -32, x + 70, y + 268, 0, .7)
    head(cv, x, y, "D2", "SEA WALL + BEACH STAIR · SECTION", "promenade +3.60 to sand +1.20 · 6.00 wide · 2 stairs + pier stair")
    cv.poly([(8.2, Z_BEACH), (12.4, 1.12), (12.4, .7), (2.0, .7)], "z-sand")
    cv.poly([(8.2, Z_BEACH), (12.4, 1.12), (12.4, .7), (2.0, .7)], "", f' fill="url(#{p}-sand)"')
    cv.line(8.2, Z_BEACH, 12.4, 1.12, "ln")
    earth = [(-1, 3.45), (1.6, 3.45), (1.6, .7), (-1, .7)]
    cv.poly(earth, "poche")
    cv.poly(earth, "", f' fill="url(#{p}-earth)"')
    cv.rect(1.6, .7, 2.0, 3.45, "conc")
    cv.rect(-1, 3.45, 2.0, Z_PLAZA, "z-timber")
    cv.rect(-1, 3.45, 2.0, Z_PLAZA, "ln")
    st = [(2.0, Z_PLAZA)]
    z, xx = Z_PLAZA, 2.0
    for flight in range(2):
        for k in range(8):
            z -= .15
            st += [(xx, z + .15), (xx, z)]
            if k < 7:
                xx += .3
                st.append((xx, z))
        if flight == 0:
            xx += 2.0
            st.append((xx, z))
    st += [(8.2, .7), (2.0, .7)]
    cv.poly(st, "conc")
    cv.line(1.92, Z_PLAZA, 1.92, Z_PLAZA + 1.1, "ln-b")
    cv.line(2.0, Z_PLAZA + .9, 4.1, 3.3, "ln")
    cv.line(4.1, 3.3, 6.1, 3.3, "ln")
    cv.line(6.1, 3.3, 8.2, 2.1, "ln")
    avatar(cv, .1, Z_PLAZA)
    avatar(cv, 5.75, Z_PIER)
    avatar(cv, 10.4, 1.16)
    vdim(cv, 8.7, Z_BEACH, Z_PIER, "8R = 1.20", side=1)
    vdim(cv, 4.6, Z_PIER, Z_PLAZA, "8R = 1.20", side=1)
    hdim(cv, 2.0, 8.2, .25, "6.20 = 2.10 + 2.00 + 2.10")
    vdim(cv, 1.4, Z_PLAZA, Z_PLAZA + 1.1, "1.10 RAIL")
    etag(cv, -.9, Z_PLAZA, "+3.60", below=True)
    etag(cv, 11.2, Z_BEACH, "+1.20 SAND")
    cv.text(1.1, 2.0, "SEA WALL 2.40", "t-sm halo", rot=-90)
    out.append(cv.svg())

    # D3 pier cross-section
    x, y = panels[2]
    cv = Cv(24, -24, x + 260, y + 235, 0, 0)
    head(cv, x, y, "D3", "PIER · CROSS-SECTION", "deck 5.00 wide at +2.40 · head platform 24 × 10 · dive spot at the head")
    cv.rect(-7, -2.6, 7, 0, "water")
    cv.line(-7, 0, 7, 0, "ln-water")
    cv.rect(-7, -3.0, 7, -2.6, "poche")
    cv.rect(-7, -3.0, 7, -2.6, "", f' fill="url(#{p}-earth)"')
    cv.line(-7, -2.6, 7, -2.6, "ln-h")
    cv.rect(-2.5, 2.3, 2.5, Z_PIER, "z-timber")
    cv.rect(-2.5, 2.3, 2.5, Z_PIER, "ln")
    cv.rect(-2.3, 1.9, 2.3, 2.3, "conc")
    for u in (-2.0, 2.0):
        cv.rect(u - .2, -2.6, u + .2, 1.9, "conc")
        cv.line(u * 1.22, Z_PIER, u * 1.22, Z_PIER + 1.1, "ln")
        cv.line(u * 1.22 - .08, Z_PIER + 1.1, u * 1.22 + .08, Z_PIER + 1.1, "ln-h")
    cv.line(-2.3, Z_PIER, -2.3, Z_PIER + 3.6, "ln")
    cv.circle(-2.3, Z_PIER + 3.7, .18, "chalk-y")
    avatar(cv, .6, Z_PIER)
    cv.add(f'<circle class="avatar" cx="{n(cv.X(4.8))}" cy="{n(cv.Y(0) - 4)}" r="5"/>')
    hdim(cv, -2.5, 2.5, 4.4, "5.00 DECK")
    vdim(cv, 3.4, 0, Z_PIER, "2.40", side=1)
    vdim(cv, 3.4, Z_PIER, Z_PIER + 1.1, "1.10", side=1)
    vdim(cv, -4.2, -2.0, 0, "≥ 2.00 AT HEAD")
    etag(cv, -6.6, 0, "±0.00 SWL")
    callout(cv, -2.3, 5.9, -6.2, 5.2, "LAMP 3.60", "start", cls="t-sm halo")
    cv.add(f'<text class="t-sm" x="{x + 42}" y="{y + 50}">Image drew the pier 7.5 m wide; 5.00 m reads as a pier and fits three abreast.</text>')

    # D4 central planter: plan + section
    x, y = panels[3]
    head(cv, x, y, "D4", "CENTRAL PLANTER + BENCH RING", "plan and section · image drew it Ø27 m, corrected to Ø14 m")
    pl = Cv(12, 12, x + 130, y + 175, 0, 0)
    pl.circle(0, 0, 8.5, "z-paver")
    pl.poly(sector(0, 0, 5.5, 7, 9, 81), "prop")
    for q in (1, 2, 3):
        pl.poly(sector(0, 0, 5.5, 7, q * 90 + 9, q * 90 + 81), "prop")
    pl.circle(0, 0, 4, "z-lawn")
    pl.circle(0, 0, 4, "ln")
    pl.circle(0, 0, 4.6, "tree", ' fill-opacity=".55" stroke-dasharray="3 2"')
    pl.circle(0, 0, .4, "ink-f")
    hdim(pl, -7, 7, -9.2, "Ø14.00")
    hdim(pl, -4, 4, 8.6, "Ø8.00 PLANTER")
    pl.text(-9.6, 9.7, "4 gaps × 2.00", "t-sm", "start")
    pl.text(-9.6, 11.1, "for access", "t-sm", "start")
    pl.text(-9.6, -6.6, "PLAN", "t-lbl", "start")
    out.append(cv.svg())
    out.append(pl.svg())
    sc = Cv(12, -12, x + 370, y + 250, 0, 0)
    sc.rect(-8.5, -.6, 8.5, 0, "poche")
    sc.rect(-8.5, -.6, 8.5, 0, "", f' fill="url(#{p}-earth)"')
    sc.line(-8.5, 0, 8.5, 0, "ln-h")
    for s in (-1, 1):
        sc.rect(s * 5.5, 0, s * 7, .45, "conc")
        sc.rect(s * 4, 0, s * 3.7, .6, "solid")
    sc.rect(-3.7, .4, 3.7, .55, "z-lawn")
    tree_elev(sc, 0, .55, 8.4, 9.2, 4)
    avatar(sc, 6.6, .45, seated=True)
    avatar(sc, -8, 0)
    vdim(sc, 7.6, 0, .45, "0.45", side=1)
    vdim(sc, -3.1, 0, .6, "0.60", side=1)
    sc.text(-8.4, 9.6, "SECTION", "t-lbl", "start")
    out.append(sc.svg())
    return "\n".join(out), W, H


# ================================================================ schedules
CORRECTIONS = [
    ("Scale bar", "1:500 · 50 m = 195 px (3.9 px/m)", "≈ 6 px/m", "Measured on people (1.3 m), trucks and doors. The bar disagrees with everything drawn."),
    ("Whole park", "≈ 330 × 260 m by the bar", "≈ 205 × 158 m", "Same layout, read at the true scale."),
    ("Central plaza paving", "Ø 77 m", "Ø 56 m", "Fits between the west block and the food trucks; groups stay within talking distance."),
    ("Central planter + seats", "Ø 27 m", "Ø 8 m planter, Ø 14 m bench ring", "At 27 m it filled a quarter of the plaza. Now a 21 m clear ring is left for dancing and emotes."),
    ("Main entrance stair", "13 × 16 m, one flight", "12 × 12 m, 2 × 16R + 3 m landing", "4.80 m rise from the street. 32 risers need a landing."),
    ("Beach stairs", "11 × 11 m", "6 × 6.2 m, 2 × 8R", "2.40 m drop from the promenade to the sand."),
    ("Beach promenade", "10 m wide", "8 m wide", "Main path rule: ≥ 8 m."),
    ("Pier", "7.5 m wide, head 28 × 12 m", "5 × 36 m, head 24 × 10 m", "Reads as a pier. The head still fits a group photo."),
    ("Food trucks", "7.5 × 4.2 m", "6.5 × 2.5 m", "Real truck width is about 2.5 m."),
    ("Parasols", "Ø 5 m", "Ø 2.6 m", "Real parasol size."),
    ("Palm trees", "canopy Ø 10 m", "Ø 6 m", "Big canopies hid the promenade and stairs from the top-down camera."),
    ("Small stage deck", "25 × 22 m", "fan R 13 m (≈ 18 m arc × 10 m)", "A small stage; the lawn holds the audience."),
    ("Cat statue", "6.5 m", "3 m", "Photo prop, still readable from the top of the main stair."),
    ("Beach hut", "6.5 × 6.5 m", "4 × 4 m", "Lifeguard / rental hut."),
    ("Coastal street", "6.7 m", "8 m", "Two 3.5 m lanes plus gutters."),
    ("East curved path", "6.7 m", "5 m", "Secondary path rule: ≥ 4 m."),
    ("Heights", "none (flat image)", "street +8.40 · plaza +3.60 · sand +1.20", "The image shows stairs but no levels. L-201 and L-202 set them."),
]
KEPT = "Kept as drawn (within about 10%): arcade 32 × 26 m, fashion shop 32 × 16 m, café 22 × 11 m + terrace, lifestyle shop 20 × 16 m, food truck zone 40 × 15 m, beach depth ≈ 38 m."

LOCATIONS = [
    (1, "City Street (Entrance)", "+8.40", "E1", "road 8 m + sidewalk 3 m", "Spawn A at the crosswalk. Main stair down to the plaza."),
    (2, "Central Plaza", "+3.60", "D–F 2–5", "paving Ø 56 m", "Planter Ø 8, bench ring Ø 14, cat statue, chalk art."),
    (3, "Arcade (Indoor)", "+3.60", "A–C 2–4", "32 × 26 m, 6.0 m high", "Entry from the plaza on the east."),
    (4, "Café (Indoor + Outdoor)", "+3.60", "A–C 4–5", "22 × 11 m + L-terrace 8 m", "Terrace faces the promenade and the pier."),
    (5, "Shop (Fashion / Goods)", "+3.60 / +8.40", "A–C 2", "32 × 16 m, 2 floors", "Upper floor bridges to the street kiosks: a route through the building."),
    (6, "Food Truck Zone", "+3.60", "F–H 2", "40 × 15 m", "4 trucks, 6 parasol tables, hedge to the street."),
    (7, "Small Stage (Events)", "deck +4.20, lawn +3.60", "H–J 1–3", "deck R 13 m, lawn R 39 m, ring path 4 m", "Backed by the street wall; the audience lawn faces north-east; ring path links to all sides."),
    (8, "Shop (Lifestyle / Souvenir)", "+3.60", "G–H 3–4", "20 × 16 m + 5 kiosks", "Entry from the plaza on the west."),
    (9, "Beach Promenade", "+3.60", "A–I 5", "174 × 8 m", "Lamps every 12 m, 2 beach stairs and the pier stair."),
    (10, "Beach Area", "+1.20 → ±0.00", "A–H 5–7", "≈ 4,500 m²", "Parasols, hut, surf rack, rocks at the west end."),
    (11, "Pier / Photo Spot", "+2.40", "H–I 5–8", "5 × 36 m + head 24 × 10 m", "Photo frame and dive spot at the head."),
    (12, "Side Path (to Town / Station)", "+8.40 → +3.60", "J 1–5", "6 m ramp 1:12 + garden steps 16R", "Spawn B on the station side, sakura lookout, coastal walk to the pier."),
]

METRICS = [
    ("Avatar height (assumed)", "1.30 m · capsule r 0.34", "Chibi proportions. Every other number scales from this."),
    ("Max step height", "0.45 m", "Bench ring (0.45) and planter walls (0.60) can be hopped onto."),
    ("Main path width", "≥ 8 m", "Promenade 8 m, main stair 12 m."),
    ("Secondary path width", "≥ 4 m", "Curved path 5 m, side path 6 m, NW and E stairs 4–5 m."),
    ("Exterior stairs", "riser 0.15 · tread 0.30", "Landing every 16 risers at most."),
    ("Ramps", "≤ 1:12", "Side path ramp 1:12; west lane ≈ 1:15 with short step runs."),
    ("Rails", "1.10 m", "Above the assumed 0.90 m jump apex, so the beach is reached by stairs."),
    ("Doorway · interior clear", "3.0 × 3.2 m · ≥ 4.5 m", "Camera boom 3.5 m never clips."),
    ("Swim transition", "depth > 0.90 m", "About 15 m out from the shoreline."),
    ("Target players", "30–50 per instance", "Plaza Ø 56 m ≈ 2,460 m² plus the beach and promenade."),
]

NOTES = {
    "l101": [
        "Same layout as the reference: street on the north, west block (fashion shop, arcade, café), round central plaza, food trucks and lifestyle shop to the east, stage lawn in the north-east corner, promenade, beach, pier to the south-east.",
        "Key numbers 1–12 match the reference's key list. Grid cells are 20 × 20 m (A–J, 1–8). Use Zoom to read furniture, stair treads and railings.",
        "The street sits 4.80 m above the plaza. Six routes link them: main stair, NW stair, E stair, the fashion shop's upper-floor bridge, the west lane and the east side path.",
        "Main route (red): Spawn A → main stair → plaza → promenade → east beach stair → beach → pier head. The pier deck crosses the upper beach at +2.40; block the low space under it.",
        "Every path joins another: the stage lawn sits inside a 4 m ring path linked to the food truck zone, the curved path, the grove path and the coastal walk. Table S-4 lists all 39 links and the build fails if any area is unreachable.",
        "Trees, palms, sakura and shrub beds are drawn at canopy size with shadows cast north-east (sun from the south-west). Boulders are placed one by one; the shoreline has wet sand, foam lines and depth bands.",
    ],
    "l201": [
        "Cut on the main axis X = 91, looking east. The main stair projects from the 4.80 m street wall into the plaza.",
        "Promenade and plaza share +3.60, so the planters between them have gaps instead of steps.",
        "The sea wall is 2.40 m with a 1.10 m rail; the shoreline is about 38 m from the wall on this axis.",
    ],
    "l202": [
        "Cut across the plaza centre at Y = 59, looking north at the street wall, the stairs, the food trucks and the stage.",
        "The west lane is at +5.40 here, so the arcade's west wall retains 1.80 m of ground.",
        "Arcade 6.00 m high (5.70 m clear) and lifestyle shop 5.40 m keep the plaza edge low, so the street and the stage stay visible over them.",
    ],
    "d401": [
        "D1: the reference drew one long flight. Two flights of 16 risers with a 3 m landing carry the 4.80 m rise.",
        "D2: beach stairs drop 2.40 m in two flights; the pier stair at the east end is one 8R flight down to the +2.40 deck.",
        "D3: the pier deck sits 2.40 m above still water with at least 2.00 m depth at the head for diving.",
        "D4: the bench ring seats about 40 avatars facing out, with four 2 m gaps to reach the tree.",
    ],
}

# Walkable areas and the links between them. main() checks every area is
# reachable from Spawn A, so a disconnected zone fails the build.
AREAS = {
    "sidewalk": "Street sidewalk +8.40", "kiosks": "Kiosk strip +8.40", "fashion_up": "Fashion shop upper floor +8.40",
    "fashion": "Fashion shop +3.60", "plaza": "Central plaza +3.60", "arcade": "Arcade +3.60", "cafe": "Café +3.60",
    "terrace": "Café terrace +3.60", "trucks": "Food truck zone +3.60", "lifestyle": "Lifestyle shop +3.60",
    "ring": "Lawn ring path +3.60", "service": "Service path +3.60", "lawn": "Stage lawn +3.60", "deck": "Stage deck +4.20",
    "curved": "Curved path +3.60", "grove": "Grove path +3.60", "coast": "Coastal walk +3.60", "lookout": "Sakura lookout +3.60",
    "ramp": "Side path ramp +8.40 → +6.00", "steps": "Garden steps +6.00 → +3.60", "lane": "West lane +8.40 → +3.60",
    "prom": "Beach promenade +3.60", "beach": "Beach +1.20 → ±0.00", "rocks_w": "West rocks", "rocks_e": "East rocks",
    "pier": "Pier +2.40", "head": "Pier head +2.40", "sea": "Sea",
}
LINKS = [
    ("sidewalk", "plaza", "Main stair · 12 m · 2 × 16R + 3 m landing"),
    ("sidewalk", "plaza", "NW stair · 5 m · 2 × 16R"),
    ("sidewalk", "plaza", "E stair · 4 m · 2 × 16R"),
    ("sidewalk", "kiosks", "Open frontage, same level"),
    ("kiosks", "fashion_up", "Bridge · 8 m"),
    ("fashion_up", "fashion", "Stair + lift inside the shop"),
    ("sidewalk", "lane", "West lane top"),
    ("lane", "prom", "West lane foot"),
    ("sidewalk", "ramp", "Side path top · Spawn B"),
    ("ramp", "steps", "Ramp foot landing"),
    ("steps", "coast", "Garden steps foot"),
    ("plaza", "fashion", "East doors"),
    ("plaza", "arcade", "East doors · 8 m"),
    ("plaza", "cafe", "East door"),
    ("cafe", "terrace", "Folding glass wall"),
    ("terrace", "prom", "Open edge"),
    ("plaza", "trucks", "Same paving"),
    ("plaza", "lifestyle", "West doors"),
    ("plaza", "prom", "4 gaps between the palm beds"),
    ("trucks", "ring", "Ring path west end"),
    ("ring", "service", "Service path fork"),
    ("service", "deck", "Stage side"),
    ("ring", "lawn", "Open lawn edge"),
    ("lawn", "deck", "Front steps · 2R"),
    ("ring", "curved", "Fork at the south-west of the lawn"),
    ("curved", "prom", "Joins the promenade east end"),
    ("curved", "grove", "Gravel path through the grove"),
    ("grove", "coast", "Grove path end"),
    ("ring", "coast", "Ring path east end"),
    ("coast", "lookout", "Spur · 3 m"),
    ("coast", "prom", "Coastal walk end"),
    ("prom", "beach", "West beach stair · 2 × 8R"),
    ("prom", "beach", "East beach stair · 2 × 8R"),
    ("prom", "pier", "Pier stair · 8R"),
    ("pier", "head", "Same deck"),
    ("beach", "rocks_w", "Sand edge"),
    ("beach", "rocks_e", "Sand edge"),
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
  <p class="eyebrow">Level design package · reference layout redrawn to true scale · rev C</p>
  <h1>Japan Coastal <span class="wave">Hangout Park</span></h1>
  <p class="lede">The reference top view, kept as laid out and redrawn at one consistent scale. The image's 1:500 bar was wrong:
  measured against its people, food trucks and doors, the map reads at about 6 px per metre. At that scale the park is about
  205 × 158 m. Most buildings were already right; the plaza planter, stairs, pier, parasols, palms and stage were drawn too big
  and are corrected here, and the flat image now has real levels.</p>
  <dl class="tblock">
    <div><dt>Footprint</dt><dd>≈ 205 × 158 m playable</dd></div>
    <div><dt>True scale of image</dt><dd>≈ 6 px/m (bar said 3.9)</dd></div>
    <div><dt>Players</dt><dd>30–50 per instance</dd></div>
    <div><dt>Units</dt><dd>metres · 1 m = 100 UU</dd></div>
    <div><dt>Levels</dt><dd>+8.40 / +3.60 / sand +1.20</dd></div>
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
  <div class="block-head"><span class="sheet-no">S-1</span><h2>Scale corrections</h2><span class="scale">“as drawn” measured at ≈ 6 px/m</span></div>
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

<footer><span>Japan Coastal Hangout Park · rev C · 2026-10-05</span><span>Source: docs/maps/coastal-hangout-park/build.py</span><span>Standalone SVGs in svg/</span></footer>
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
    for k, (fn, label, fname) in builders.items():
        body, w, h = fn()
        svgs[k] = (body, w, h, label)
        with open(os.path.join(HERE, "svg", fname), "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n' + wrap(body, w, h, label, standalone=True) + "\n")
    with open(os.path.join(HERE, "index.html"), "w", encoding="utf-8") as f:
        f.write(page(svgs))
    print("wrote index.html and", len(builders), "SVG sheets")


if __name__ == "__main__":
    main()
