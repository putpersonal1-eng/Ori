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
STAGE_F = (192, 16)          # focus of the stage fan (NE corner)
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


def palm(cv, u, v, r=3, rot=0):
    pts = []
    for i in range(14):
        a = math.radians(rot + i * 360 / 14)
        rr = r if i % 2 == 0 else r * .38
        pts.append((u + rr * math.cos(a), v + rr * math.sin(a)))
    cv.poly(pts, "tree")
    cv.circle(u, v, .4, "ink-f")


def key(cv, u, v, num):
    cv.circle(u, v, 2.4, "key")
    cv.text(u, v + .95, str(num), "t-lbl t-inv")


# ================================================================ L-101 PLAN
def site_plan():
    p = "cp"
    W, H = 1230, 800
    cv = Cv(4, 4, 56, 56, -6, -14)
    A = cv.add
    A(defs(p))
    A(f'<rect class="sheet-bg" width="{W}" height="{H}"/>')

    def pat(name):
        return f' fill="url(#{p}-{name})"'

    # ------------------------------------------------------------- ground
    A('<g id="lyr-zones">')
    cv.rect(-6, 40, 210, 160, "z-deep")
    cv.rect(-6, 40, 210, 160, "", pat("water"))
    cv.path(SHORE + [("L", 40, 148), ("C", 112, 150, 162, 134, 184, 114), ("Z",)], "z-sea")
    land = [(-6, -14), (210, -14), (210, 40), (202, 40), (201, 52), (204, 64), (203, 76), (197, 88), (190, 94), (-6, 94)]
    cv.poly(land, "z-lawn")
    cv.poly(land, "", pat("lawn"))
    sand = [("M", 2, 94), ("L", 180, 94), ("L", 180, 104), ("L", 172, 106), ("C", 152, 122, 110, 135, 40, 134),
            ("L", 34, 124), ("L", 24, 110), ("L", 12, 100), ("Z",)]
    cv.path(sand, "z-sand")
    cv.path(sand, "", pat("sand"))
    cv.path([("M", 170, 103), ("C", 150, 119, 110, 132, 42, 131)], "ln-f", ' stroke-dasharray="2 3"')
    cv.path(SHORE, "ln-water")
    cv.path(WADE, "ln-f", ' stroke-dasharray="5 3"')
    # town, road, sidewalks
    cv.rect(-6, -14, 210, 0, "z-town")
    cv.rect(-6, -14, 210, 0, "", pat("hatch"))
    for a, b in [(-6, 40), (46, 78), (100, 122), (126, 156), (162, 210)]:
        cv.rect(a, -14, b, -3, "ln-m")
    cv.rect(82, -14, 96, 2, "z-road")
    cv.rect(-6, 0, 210, 2, "z-paver")
    cv.rect(-6, 2, 210, 10, "z-road")
    cv.line(-6, 6, 82, 6, "lane")
    cv.line(96, 6, 210, 6, "lane")
    cv.line(89, -14, 89, 2, "lane")
    for x0, x1 in [(84, 96), (168, 174)]:
        for x in frange(x0 + .3, x1, 1.2):
            cv.rect(x, 2.6, x + .6, 9.4, "zebra")
    cv.rect(-6, 10, 210, 13, "z-paver")
    cv.line(-6, 10, 210, 10, "ln-m")
    cv.rect(-6, 13, 2, 94, "z-town")
    cv.rect(-6, 13, 2, 94, "", pat("hatch"))
    cv.rect(202, 13, 210, 40, "z-town")
    cv.rect(202, 13, 210, 40, "", pat("hatch"))
    # paved plaza + street-level strip by the kiosks
    cv.rect(2, 13, 52, 21, "z-paver")
    plaza = [(46, 19), (152, 19), (152, 36), (157, 52), (160.5, 62), (166, 76), (171, 86), (46, 86)]
    cv.poly(plaza, "z-paver")
    cx, cy = PLAZA_C
    for r in (28, 20, 12):
        cv.circle(cx, cy, r, "ln-f")
    for k in range(12):
        a = math.radians(k * 30 + 15)
        cv.line(cx + 7.4 * math.cos(a), cy + 7.4 * math.sin(a), cx + 28 * math.cos(a), cy + 28 * math.sin(a), "ln-f")
    for (u, v, c, ru, rv) in [(71, 58, "chalk-c", 2.6, 1.4), (73, 62, "chalk-y", 1.6, 1.0), (111, 67, "chalk-p", 2.2, 1.2),
                              (108, 70, "chalk-y", 1.4, .9)]:
        cv.ellipse(u, v, ru, rv, c, ' fill-opacity=".5"')
    # west lane (stepped slope)
    cv.rect(2, 13, 12, 86, "z-paver")
    for y in frange(22, 86, 8):
        for k in range(3):
            cv.line(2, y + k * .6, 12, y + k * .6, "ln-m")
    # street bank, hedge
    cv.rect(52, 13, 202, 19, "z-lawn")
    cv.rect(110, 19, 152, 21.5, "z-lawn")
    cv.line(46, 19, 193, 19, "ln-h")
    # stage: path ring, lawn, deck
    fx, fy = STAGE_F
    cv.poly(sector(fx, fy, 38, 41, 100, 165), "z-paver")
    cv.poly(sector(fx, fy, 15, 38, 100, 165), "z-lawn")
    cv.poly(sector(fx, fy, 15, 38, 100, 165), "ln-m")
    for r in (21, 27, 33):
        cv.path([("M", fx + r * math.cos(math.radians(100)), fy + r * math.sin(math.radians(100)))] +
                [("L", fx + r * math.cos(math.radians(a)), fy + r * math.sin(math.radians(a))) for a in range(104, 166, 4)],
                "ln-f", ' stroke-dasharray="1.5 3"')
    cv.poly(sector(fx, fy, 3, 13, 100, 165), "z-timber")
    cv.poly(sector(fx, fy, 3, 13, 100, 165), "", pat("board"))
    cv.poly(sector(fx, fy, 3, 13, 100, 165), "ln")
    # east side path: ramp + curved garden steps + coastal walk
    cv.rect(193, 13, 199, 47, "z-paver")
    cv.rect(193, 13, 199, 47, "ln-m")
    cv.line(196, 17, 196, 42, "ln-m", f' marker-end="url(#{p}-arrk)"')
    cv.poly(sector(180, 47, 13, 19, 0, 40), "z-paver")
    for a in range(0, 41, 3):
        r0, r1 = 13, 19
        aa = math.radians(a)
        cv.line(180 + r0 * math.cos(aa), 47 + r0 * math.sin(aa), 180 + r1 * math.cos(aa), 47 + r1 * math.sin(aa), "ln-f")
    cv.poly(sector(180, 47, 13, 19, 0, 40), "ln-m")
    cv.path(COAST_WALK, "", ' style="fill:none;stroke:var(--ink-3);stroke-width:21"')
    cv.path(COAST_WALK, "", ' style="fill:none;stroke:var(--paver);stroke-width:19"')
    cv.circle(199, 70, 4, "z-paver")
    cv.circle(199, 70, 4, "ln-m")
    # curved path (food trucks -> promenade)
    cv.path(CURVED_PATH, "", ' style="fill:none;stroke:var(--ink-3);stroke-width:21"')
    cv.path(CURVED_PATH, "", ' style="fill:none;stroke:var(--paver);stroke-width:19"')
    # promenade
    cv.rect(2, 86, 176, 94, "z-timber")
    cv.rect(2, 86, 176, 94, "", pat("board"))
    # rocks
    wr = [(-6, 96), (10, 96), (16, 102), (24, 110), (32, 120), (38, 130), (40, 138), (34, 148), (24, 156), (10, 160), (-6, 160)]
    er = [(180, 95), (190, 95), (196, 100), (195, 108), (188, 113), (181, 110), (179, 103)]
    for r in (wr, er):
        cv.poly(r, "z-cliff")
        cv.poly(r, "", pat("rock"))
        cv.poly(r, "ln")
    for (u, v, r) in [(30, 104, 2.2), (44, 116, 2.6), (54, 128, 2.0), (186, 120, 1.6), (200, 104, 1.8)]:
        cv.circle(u, v, r, "z-cliff")
        cv.circle(u, v, r, "ln-m")
    A('</g>')

    # ------------------------------------------------------------- built
    A('<g id="lyr-built">')
    # street kiosks + bridge
    for x0 in (6, 16, 26, 36):
        cv.rect(x0, 13.5, x0 + 9, 18.5, "bldg-l")
        cv.rect(x0, 18.5, x0 + 9, 19.6, "umb-p", ' opacity=".75"')
    cv.rect(26, 18.5, 34, 21, "bldg-l")
    # west block
    cv.rect(14, 21, 46, 37, "bldg")
    cv.rect(14, 38, 46, 64, "bldg")
    cv.rect(14.6, 38.6, 45.4, 63.4, "arc-y")
    for row in range(4):
        for col in range(4):
            u, v = 20 + col * 4.4, 42 + row * 4.4
            cv.rect(u, v, u + 2.2, v + 1.4, "prop")
    cv.rect(38, 44, 44, 52, "prop")
    terr = [(36, 67), (46, 67), (46, 86), (14, 86), (14, 78), (36, 78)]
    cv.poly(terr, "z-timber")
    cv.poly(terr, "", pat("board"))
    cv.poly(terr, "ln")
    cv.rect(14, 67, 36, 78, "bldg")
    for (x, a, b) in [(46, 26, 32), (46, 47, 55), (36, 70, 75)]:
        cv.line(x, a, x, b, "gap")
        cv.line(x, a, x, b, "glass")
    # main entrance stair + NW stair + east stair (2 x 16R, landing)
    for (a, b) in [(85, 97), (54, 59), (104, 108)]:
        cv.rect(a, 17, b, 29, "z-paver")
        for y in frange(17.3, 21.5, .6) + frange(24.8, 29, .6):
            cv.line(a, y, b, y, "ln-m")
        cv.rect(a, 17, b, 29, "ln")
    for x in (89, 93):
        cv.line(x, 17, x, 29, "ln-f")
    for (a, b) in [(80, 85), (97, 102)]:
        cv.rect(a, 19, b, 29, "z-lawn")
        cv.rect(a, 19, b, 29, "ln-m")
    # food trucks
    for (u0, v0, u1, v1) in [(116, 24, 122.5, 26.5), (125, 24, 131.5, 26.5), (134, 24, 140.5, 26.5), (144, 27, 146.5, 33.5)]:
        cv.rect(u0, v0, u1, v1, "bldg-l")
    for (u, v, c) in [(118, 31, "umb-c"), (125, 33, "umb-y"), (132, 31, "umb-p"), (139, 33, "umb-c"),
                      (121, 40, "umb-y"), (130, 41, "umb-c")]:
        cv.circle(u, v, 1.3, c)
    # lifestyle shop + kiosks
    cv.rect(131, 51, 151, 67, "bldg")
    cv.rect(131.8, 51.8, 150.2, 66.2, "trim-y")
    cv.line(131, 56, 131, 62, "gap")
    cv.line(131, 56, 131, 62, "glass")
    for x0 in (131, 136.5, 142, 147.5):
        cv.rect(x0, 68.5, x0 + 4.5, 72.5, "bldg-l")
        cv.rect(x0, 68.5, x0 + 4.5, 69.4, "umb-y")
    cv.rect(125, 58, 129, 66, "bldg-l")
    # stage props
    for a in (110, 155):
        aa = math.radians(a)
        cv.rect(fx + 11 * math.cos(aa) - .8, fy + 11 * math.sin(aa) - .8, fx + 11 * math.cos(aa) + .8,
                fy + 11 * math.sin(aa) + .8, "prop-d")
    # promenade rail with gaps, beach stairs, pier stair, pier
    for a, b in [(2, 55), (61, 120), (126, 172.5)]:
        cv.line(a, 94, b, 94, "ln-h")
    for (a, b) in [(55, 61), (120, 126)]:
        cv.rect(a, 94, b, 100.2, "z-paver")
        for y in frange(94.3, 96.1, .3) + frange(98.4, 100.2, .3):
            cv.line(a, y, b, y, "ln-f")
        cv.rect(a, 94, b, 100.2, "ln")
    cv.rect(172.5, 94, 177.5, 96.1, "z-paver")
    for y in frange(94.3, 96.1, .3):
        cv.line(172.5, y, 177.5, y, "ln-f")
    cv.rect(172.5, 96.1, 177.5, 132, "z-timber")
    cv.rect(156, 132, 180, 142, "z-timber")
    cv.rect(172.5, 96.1, 177.5, 132, "", pat("board"))
    cv.rect(156, 132, 180, 142, "", pat("board"))
    cv.pline([(172.5, 94), (172.5, 132), (156, 132), (156, 142), (180, 142), (180, 132), (177.5, 132), (177.5, 94)], "ln")
    for y in frange(102, 132, 6):
        cv.circle(172.5, y, .35, "ink-f")
        cv.circle(177.5, y, .35, "ink-f")
    cv.rect(110, 110, 114, 114, "bldg-l")
    cv.rect(135, 99, 140, 100.4, "prop")
    A('</g>')

    # ------------------------------------------------------------- props
    A('<g id="lyr-props">')
    cv.poly(sector(cx, cy, 5.5, 7, 0 + 9, 90 - 9), "prop")
    for q in (1, 2, 3):
        cv.poly(sector(cx, cy, 5.5, 7, q * 90 + 9, q * 90 + 81), "prop")
    cv.circle(cx, cy, 4, "z-lawn")
    cv.circle(cx, cy, 4, "ln")
    cv.circle(cx, cy, 4.6, "tree", ' fill-opacity=".85"')
    cv.circle(cx, cy, .5, "ink-f")
    cv.circle(107, 45, 1.5, "statue")
    cv.circle(107, 45, .5, "chalk-p")
    for (u, v) in [(66, 38), (66, 74), (118, 47)]:
        cv.circle(u, v, 3, "z-lawn")
        cv.circle(u, v, 3, "ln-m")
        cv.circle(u, v, 3.4, "tree")
        cv.circle(u, v, .35, "ink-f")
    for ang in (30, 150, 210, 330):
        a = math.radians(ang)
        u, v = cx + 27 * math.cos(a), cy + 27 * math.sin(a)
        cv.circle(u, v, .7, "prop")
        cv.circle(u, v, .25, "ink-f")
    for x in range(8, 172, 12):
        cv.circle(x, 93.2, .7, "prop")
        cv.circle(x, 93.2, .25, "ink-f")
    for x in (20, 44, 80, 104, 140, 164):
        cv.rect(x - 1.5, 87.2, x + 1.5, 88, "prop")
    for (a, b) in [(52, 63), (70, 83), (99, 112), (128, 140), (146, 160)]:
        cv.rect(a, 84.6, b, 85.8, "z-lawn")
        cv.rect(a, 84.6, b, 85.8, "ln-m")
    for (u, v) in [(48, 30), (48, 50), (48, 70)]:
        cv.rect(u - .8, v - 1.5, u + .8, v + 1.5, "prop")
    for (u, v) in [(20, 82), (27, 82.5), (34, 82), (41, 80), (41, 72)]:
        cv.circle(u, v, 1.3, "umb-y")
    trees = [(4, 16, 2.6), (10, 30, 2.8), (4, 44, 2.6), (10, 58, 2.8), (4, 72, 2.6), (10, 84, 2.4),
             (60, 15.5, 2.8), (70, 15.5, 2.6), (112, 15.5, 2.8), (124, 15.5, 2.6), (136, 15.5, 2.8), (150, 15.5, 2.6),
             (164, 15.5, 2.8), (176, 15, 2.6), (114, 20, 1.6), (128, 20.2, 1.6), (142, 20.2, 1.6),
             (154, 44, 2.6), (166, 56, 2.8), (174, 66, 2.6), (170, 48, 2.4), (182, 56, 2.4), (178, 80, 2.6),
             (152, 80, 2.4), (122, 80, 2.4)]
    for u, v, r in trees:
        cv.circle(u, v, r, "tree")
        cv.circle(u, v, .3, "ink-f")
    for (u, v, r) in [(82, 22, 2.4), (16, 89, 2.6), (196, 66, 2.2), (201, 73, 2.0), (198, 76, 1.8), (184, 68, 2.2)]:
        cv.circle(u, v, r, "tree-s")
        cv.circle(u, v, .3, "ink-f")
    for i, (u, v) in enumerate([(26, 98.5), (42, 98.5), (68, 98.5), (82, 98), (104, 98.5), (132, 98.5),
                                (150, 98), (164, 98.5), (100, 84), (58, 84), (138, 84)]):
        palm(cv, u, v, 3, i * 17)
    umb = [(48, 115), (94, 111), (124, 114), (68, 111)]
    for i, (u, v) in enumerate(umb):
        cv.rect(u - 1.6, v + 1.5, u - .7, v + 3.3, "prop")
        cv.rect(u + .7, v + 1.5, u + 1.6, v + 3.3, "prop")
        cv.circle(u, v, 1.3, ("umb-c", "umb-y", "umb-p", "umb-y")[i])
    cv.circle(69, 131, .8, "ring-acc")
    cv.circle(118, 128, .7, "umb-p")
    cv.ellipse(86, 140, 1.2, .5, "chalk-y")
    for (u, v) in [(162, 137), (170, 137)]:
        cv.rect(u - 1.5, v - .4, u + 1.5, v + .4, "prop")
    A('</g>')

    # ------------------------------------------------------------- grid
    A('<g id="lyr-grid">')
    for x in range(0, 201, 20):
        cv.line(x, -14, x, 160, "grid")
    for y in range(0, 161, 20):
        cv.line(-6, y, 210, y, "grid")
    A('</g>')
    for i, letter in enumerate("ABCDEFGHIJ"):
        x = cv.X(10 + 20 * i)
        A(f'<circle class="bubble" cx="{n(x)}" cy="40" r="9"/><text class="t-lbl" x="{n(x)}" y="43.5" text-anchor="middle">{letter}</text>')
    for j in range(8):
        y = cv.Y(10 + 20 * j)
        A(f'<circle class="bubble" cx="38" cy="{n(y)}" r="9"/><text class="t-lbl" x="38" y="{n(y + 3.5)}" text-anchor="middle">{j + 1}</text>')

    # ------------------------------------------------------------- circulation
    A('<g id="lyr-circ">')
    cv.pline([(90, 11.5), (91, 18), (91, 30), (89, 50), (88, 68), (90, 90), (122, 92), (123, 101), (140, 112),
              (168, 108), (175, 112), (175, 133), (168, 137)], "circ1", f' marker-end="url(#{p}-arr)"')
    for pts in [[(7, 11.5), (7, 84)], [(56, 12), (56.5, 29), (60, 40), (47, 50)], [(30, 16), (30, 22)],
                [(196, 11.5), (196, 44), (192, 52), (189, 64), (184, 82), (177, 93)],
                [(150, 37), (157, 52), (163, 68), (172, 86)], [(106, 12), (106, 29), (118, 36)],
                [(92, 52), (140, 59)], [(160, 30), (172, 32)], [(58, 92), (58, 101), (50, 110)]]:
        cv.pline(pts, "circ2", f' marker-end="url(#{p}-arr)"')
    A('</g>')

    # ------------------------------------------------------------- sightlines
    A('<g id="lyr-sight">')
    for (a, b, lab, lu, lv) in [((93, 15), (93, 159), "V1", 94.5, 34), ((196, 12), (168, 138), "V2", 186, 31),
                                ((40, 84), (164, 136), "V3", 47, 90.6)]:
        cv.line(a[0], a[1], b[0], b[1], "sight", f' marker-end="url(#{p}-arrt)"')
        cv.circle(a[0], a[1], .9, "teal-f")
        cv.text(lu, lv, lab, "t-lbl t-teal halo", "start")
    A('</g>')

    # ------------------------------------------------------------- cuts
    A('<g id="lyr-cuts">')
    cv.line(91, -14, 91, 160, "cut")
    cv.line(91, -14, 91, -8, "cut-h")
    cv.line(91, 154, 91, 160, "cut-h")
    section_bubble(cv, cv.X(91) + 14, cv.Y(-10), "A", 0)
    section_bubble(cv, cv.X(91) + 14, cv.Y(156), "A", 0)
    cv.line(-6, 59, 210, 59, "cut")
    cv.line(-6, 59, 0, 59, "cut-h")
    cv.line(204, 59, 210, 59, "cut-h")
    section_bubble(cv, cv.X(-2), cv.Y(59) - 14, "B", -90)
    section_bubble(cv, cv.X(206), cv.Y(59) - 14, "B", -90)
    A('</g>')

    # ------------------------------------------------------------- labels
    A('<g id="lyr-labels">')
    T = cv.text
    T(40, -6.6, "TOWN · NON-PLAYABLE", "t-sm halo")
    T(150, -6.6, "TOWN · NON-PLAYABLE", "t-sm halo")
    T(89, -9, "CITY STREET", "t-sm halo", rot=-90)
    T(40, 7, "COASTAL STREET · +8.40 · cars only", "t-sm halo")
    T(176, 7, "→ TO STATION / TOWN", "t-sm halo", "start")
    T(25.5, 17, "STREET KIOSKS +8.40", "t-sm halo")
    T(30, 29.8, "FASHION & GOODS", "t-lbl")
    T(30, 33.4, "2 floors · bridge to street", "t-sm")
    T(30, 61.6, "ARCADE · 32 × 26", "t-lbl halo")
    T(27, 72.4, "CAFÉ", "t-lbl")
    T(27, 75.6, "22 × 11", "t-sm")
    T(31, 84.6, "CAFÉ TERRACE", "t-sm halo")
    T(7, 50, "WEST LANE · stepped slope +8.40 → +3.60", "t-sm halo", rot=-90)
    T(91, 26.2, "MAIN STAIR 12 m · 2 × 16R", "t-sm halo")
    T(56.5, 31.6, "NW STAIR", "t-sm halo")
    T(106, 31.6, "E STAIR", "t-sm halo")
    T(91, 47.6, "CENTRAL PLAZA", "t-zone halo")
    T(91, 51.2, "+3.60 · paving Ø56", "t-sm halo")
    T(91, 69.6, "planter Ø8 · bench ring Ø14", "t-sm halo")
    T(107, 41.8, "CAT STATUE", "t-sm halo")
    T(131, 38.8, "FOOD TRUCK ZONE", "t-lbl halo")
    T(131, 45.2, "4 trucks 6.5 × 2.5", "t-sm halo")
    T(141, 58.6, "LIFESTYLE &", "t-lbl")
    T(141, 62, "SOUVENIR · 20 × 16", "t-sm")
    T(141, 76, "KIOSKS", "t-sm halo")
    T(174, 37, "SMALL STAGE", "t-lbl halo")
    T(174, 40.4, "deck +4.20 · lawn +3.60", "t-sm halo")
    T(196, 30, "SIDE PATH · RAMP 1:12", "t-sm halo", rot=90)
    T(190, 54.6, "GARDEN STEPS 16R", "t-sm halo", "end")
    T(199, 79.5, "SAKURA", "t-sm halo")
    T(199, 82.6, "LOOKOUT", "t-sm halo")
    T(185, 88, "COASTAL WALK", "t-sm halo", rot=-62)
    T(76, 91.2, "BEACH PROMENADE · +3.60 · 8 m", "t-zone halo")
    T(58, 104, "8R+8R", "t-sm halo")
    T(123, 104, "8R+8R", "t-sm halo")
    T(96, 124, "BEACH AREA", "t-big halo")
    T(96, 128, "+1.20 → ±0.00", "t-sm halo")
    T(112, 117.4, "HUT", "t-sm halo")
    T(137.5, 98, "SURF", "t-sm halo")
    T(170, 120, "PIER 5 × 36 · +2.40", "t-sm halo", "end")
    T(168, 146.4, "PIER HEAD · PHOTO SPOT 24 × 10", "t-lbl halo")
    T(18, 132, "ROCKS", "t-sm halo")
    T(70, 144, "WADE ZONE ±0.00 → −0.90", "t-sm halo")
    T(60, 156.4, "SWIM ZONE · −0.90 → −2.50", "t-sm halo")
    T(205, 120, "SEA", "t-sm halo", rot=90)
    for (u, v, letter, lu, anchor) in [(90, 11.5, "A", 94, "start"), (196, 11.5, "B", 192, "end")]:
        cv.circle(u, v, 2.4, "acc-f")
        T(u, v + .95, letter, "t-lbl t-inv")
        T(lu, v + 1, f"SPAWN {letter}", "t-lbl t-acc halo", anchor)
    for (u, v, k) in [(78, 7.5, 1), (78, 54, 2), (16.8, 41, 3), (17, 70, 4), (17.4, 24.4, 5), (113, 30, 6), (166, 30, 7),
                      (136, 48.4, 8), (36, 91, 9), (74.5, 123.4, 10), (180, 128, 11), (199, 20, 12)]:
        key(cv, u, v, k)
    A('</g>')
    cv.rect(-6, -14, 210, 160, "frame")

    # ------------------------------------------------------------- legend + title block
    lx, ly = 942, 56
    A(f'<g transform="translate({lx} {ly})">')
    A('<rect class="frame-in" width="262" height="458"/>')
    A('<text class="t-head" x="14" y="24">LEGEND</text>')
    rows = [("z-road", None, "Street · cars only"), ("z-paver", None, "Stone paving · stairs"),
            ("z-timber", "board", "Wood deck · promenade, pier"), ("z-lawn", "lawn", "Grass & planting"),
            ("z-sand", "sand", "Sand"), ("z-sea", None, "Wade zone · depth ≤ 0.90"),
            ("z-deep", "water", "Swim zone · depth > 0.90"), ("z-cliff", "rock", "Rocks · climbable edge"),
            ("bldg", None, "Building (indoor)"), ("z-town", "hatch", "Non-playable")]
    y = 38
    for cls, pt, lab in rows:
        A(f'<rect class="{cls}" x="14" y="{y}" width="28" height="13"/>')
        if pt:
            A(f'<rect x="14" y="{y}" width="28" height="13" fill="url(#{p}-{pt})"/>')
        if cls != "bldg":
            A(f'<rect class="ln-f" x="14" y="{y}" width="28" height="13"/>')
        A(f'<text class="t-lbl" x="52" y="{y + 10}">{esc(lab)}</text>')
        y += 16
    y += 6
    A(f'<text class="t-head" x="14" y="{y + 6}">SYMBOLS</text>')
    y += 18
    sym = [
        ('<circle class="key" cx="28" cy="{c}" r="7"/><text class="t-lbl t-inv" x="28" y="{c3}" text-anchor="middle">1</text>', "Key location (reference numbering)"),
        ('<circle class="acc-f" cx="28" cy="{c}" r="7"/><text class="t-lbl t-inv" x="28" y="{c3}" text-anchor="middle">A</text>', "Spawn point"),
        ('<circle class="tree" cx="22" cy="{c}" r="5.5"/><circle class="tree-s" cx="36" cy="{c}" r="5.5"/>', "Tree · cherry (sakura)"),
        ('<circle class="umb-y" cx="28" cy="{c}" r="5.2"/>', "Parasol Ø2.6"),
        ('<line class="circ1" x1="14" y1="{c}" x2="42" y2="{c}"/>', "Main route"),
        ('<line class="circ2" x1="14" y1="{c}" x2="42" y2="{c}"/>', "Secondary route"),
        ('<line class="sight" x1="14" y1="{c}" x2="42" y2="{c}"/>', "Sightline V1–V3"),
        ('<line class="cut-h" x1="14" y1="{c}" x2="22" y2="{c}"/><line class="cut" x1="22" y1="{c}" x2="42" y2="{c}"/>', "Section cut A–A, B–B"),
    ]
    for tpl, lab in sym:
        c = y + 7
        A(tpl.replace("{c3}", n(c + 3.4)).replace("{c}", n(c)))
        A(f'<text class="t-lbl" x="52" y="{y + 10.5}">{esc(lab)}</text>')
        y += 16
    y += 6
    A(f'<text class="t-head" x="14" y="{y + 6}">LEVELS</text>')
    y += 21
    for z, name in [("+8.40", "Street, kiosks, side path top"), ("+4.20", "Stage deck"),
                    ("+3.60", "Plaza, shops, promenade"), ("+2.40", "Pier deck"), ("+1.20 → ±0.00", "Beach")]:
        A(f'<text class="t-dim" x="14" y="{y}">{esc(z)}</text><text class="t-sm" x="96" y="{y}">{esc(name)}</text>')
        y += 14
    A('</g>')
    ccx, ccy = 984, 548
    A(f'<circle class="frame-in" cx="{ccx}" cy="{ccy}" r="22"/>')
    A(f'<polygon class="ink-f" points="{ccx},{ccy - 20} {ccx + 7},{ccy + 7} {ccx},{ccy + 2} {ccx - 7},{ccy + 7}"/>')
    A(f'<text class="t-head" x="{ccx}" y="{ccy - 26}" text-anchor="middle">N</text>')
    bx, by = 1030, 546
    for k, (a, b) in enumerate([(0, 10), (10, 20), (20, 40)]):
        A(f'<rect class="{"ink-f" if k % 2 == 0 else "sheet-f"}" x="{bx + a * 4}" y="{by}" width="{(b - a) * 4}" height="6"/>')
    A(f'<rect class="ln" x="{bx}" y="{by}" width="160" height="6"/>')
    for m in (0, 10, 20, 40):
        A(f'<text class="t-dim" x="{bx + m * 4}" y="{by - 5}" text-anchor="middle">{m}</text>')
    A(f'<text class="t-sm" x="{bx}" y="{by + 19}">metres · true scale · grid 20 m</text>')
    tx, ty = 942, 582
    A(f'<g transform="translate({tx} {ty})">')
    A('<rect class="frame" width="262" height="170"/>')
    A('<text class="t-title" x="14" y="30" style="font-size:15px">Japan Coastal Hangout Park</text>')
    A('<text class="t-sm" x="14" y="45">Reference layout redrawn to true scale</text>')
    A('<line class="ln" x1="0" y1="54" x2="262" y2="54"/>')
    fields = [("SHEET", "L-101 Site plan"), ("SCALE", "4 px = 1 m"), ("FOOTPRINT", "216 × 174 m drawn"),
              ("UNITS", "m · 1 m = 100 UU"), ("DATUM", "±0.00 = sea level"), ("REVISION", "B · 2026-10-05")]
    for i, (k, v) in enumerate(fields):
        col, row = i % 2, i // 2
        fx_, fy_ = 14 + col * 130, 70 + row * 35
        A(f'<text class="t-sm" x="{fx_}" y="{fy_}">{k}</text><text class="t-lbl" x="{fx_}" y="{fy_ + 14}">{esc(v)}</text>')
        if col == 0 and row < 2:
            A(f'<line class="ln-f" x1="0" y1="{fy_ + 22}" x2="262" y2="{fy_ + 22}"/>')
    A('<line class="ln-f" x1="130" y1="54" x2="130" y2="170"/>')
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
    cv.line(98.5, 1.1, 98.5, 7.0, "trunk")
    for k in range(5):
        a = math.radians(200 + k * 35)
        cv.line(98.5, 7.0, 98.5 + 2.6 * math.cos(a), 7.0 + 1.0 * math.sin(a) * -1 + .2, "trunk")
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
    cv.line(59, 4.15, 59, 7.0, "trunk")
    cv.ellipse(59, 9.0, 4.6, 2.4, "tree")
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
    for x in (60, 70, 112, 124, 136, 150, 164, 176):
        cv.line(x, Z_STREET, x, Z_STREET + 1.6, "trunk")
        cv.ellipse(x, Z_STREET + 2.8, 2.6, 1.5, "tree")
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
    cv.line(91, 4.15, 91, 7.2, "trunk")
    cv.ellipse(91, 9.2, 4.6, 2.4, "tree")
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
    for x in (166, 182):
        cv.line(x, Z_PLAZA, x, 5.8, "trunk")
        cv.ellipse(x, 7.2, 2.8, 1.6, "tree")
    cv.line(202.5, Z_PLAZA, 202.5, Z_PLAZA + 1.1, "ln")
    for x in (24, 60, 72, 89, 93, 110, 159, 191):
        avatar(cv, x, Z_PLAZA)
    # tags + dims
    etag(cv, 4, 5.4, "+5.40 WEST LANE here")
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
    sc.line(0, .55, 0, 4.4, "trunk")
    sc.ellipse(0, 6.4, 4.6, 2.4, "tree")
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
    (7, "Small Stage (Events)", "deck +4.20, lawn +3.60", "H–J 1–3", "deck R 13 m, lawn R 38 m", "Backed by the street wall; the audience lawn faces north-east."),
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
        "Key numbers 1–12 match the reference's key list. Grid cells are 20 × 20 m (A–J, 1–8).",
        "The street sits 4.80 m above the plaza. Six routes link them: main stair, NW stair, E stair, the fashion shop's upper-floor bridge, the west lane and the east side path.",
        "Main route (red): Spawn A → main stair → plaza → promenade → east beach stair → beach → pier head. The pier deck crosses the upper beach at +2.40; block the low space under it.",
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
  </div>"""

    return f"""<title>Japan Coastal Hangout Park</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONT_URL}">
<style>{css}</style>
<div class="wrap">
<header>
  <p class="eyebrow">Level design package · reference layout redrawn to true scale · rev B</p>
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
  </ul>
</header>

<section class="block" id="compare">
  <div class="block-head"><span class="sheet-no">REF</span><h2>Reference vs corrected</h2><span class="scale">same layout, true scale</span></div>
  <div class="compare">
    <figure><img src="data:image/webp;base64,{ref64}" alt="Reference top-view map generated with an image model: Japan Coastal Hangout Park"><figcaption>Reference (image gen) · scale bar unreliable</figcaption></figure>
    <figure><div class="drawing mini">{wrap(mini, svgs["site"][1], svgs["site"][2], "Corrected site plan")}</div><figcaption>Corrected · L-101 at 4 px = 1 m</figcaption></figure>
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

{sheet("l101", "L-101", "Site plan", "4 px = 1 m · grid 20 m", "site", 980, layers)}
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

<footer><span>Japan Coastal Hangout Park · rev B · 2026-10-05</span><span>Source: docs/maps/coastal-hangout-park/build.py</span><span>Standalone SVGs in svg/</span></footer>
</div>
<script>
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
.kept { margin: 12px 0 0; font-size: 15px; color: var(--ink-2); max-width: 90ch; }
"""


def main():
    builders = {
        "site": (site_plan, "L-101 Site plan", "L-101-site-plan.svg"),
        "aa": (section_aa, "L-201 Section A-A", "L-201-section-AA.svg"),
        "bb": (section_bb, "L-202 Section B-B", "L-202-section-BB.svg"),
        "details": (details, "D-401 Details", "D-401-details.svg"),
    }
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
