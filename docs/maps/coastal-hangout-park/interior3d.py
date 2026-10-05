"""Arcade interior for the P-601 3D model: a dark purple game hall after the interior references.

Glossy floor, neon wall art and ceiling strips, a block-puzzle LED wall, a tower of stacked CRT
monitors with a robot face, two tiers of drum machines, cabinets, egg chairs, sphere TV pods,
server stacks with code screens, neon floor tiles and coloured lights. The layout is elev.ARC_IN,
shared with the plan (L-101) and sheet A-506.
"""
import math
import random

import elev

NEON_COL = {"pink": "neon-p", "green": "neon-g", "cyan": "neon-c", "yellow": "neon-y"}


def _monitor_face(sc, rnd, side, x0, z0, x1, z1, y0, y1, inset=.4):
    """Monitors stacked on one face of a block (E, W, N or S), each a box with a lit screen."""
    L = (z1 - z0) if side in "EW" else (x1 - x0)
    u = .2
    while u < L - .8:
        w = min(rnd.uniform(.9, 1.5), L - .2 - u)
        y = y0 + .2
        while y < y1 - .9:
            hh = rnd.uniform(.8, 1.2)
            dd = rnd.uniform(.25, .55)
            if side == "E":
                xa, xb, za, zb = x1 - inset, x1 - inset + dd, z1 - u - w, z1 - u
                lab = ([xb + .005, y + hh / 2, z1 - u - w / 2], 90)
            elif side == "W":
                xa, xb, za, zb = x0 + inset - dd, x0 + inset, z0 + u, z0 + u + w
                lab = ([xa - .005, y + hh / 2, z0 + u + w / 2], -90)
            elif side == "N":
                xa, xb, za, zb = x1 - u - w, x1 - u, z0 + inset - dd, z0 + inset
                lab = ([x1 - u - w / 2, y + hh / 2, za - .005], 180)
            else:
                xa, xb, za, zb = x0 + u, x0 + u + w, z1 - inset, z1 - inset + dd
                lab = ([x0 + u + w / 2, y + hh / 2, zb + .005], 0)
            sc.box(xa, y, za, xb, y + hh, zb, rnd.choice(["navy-d", "cab-2", "steel"]), "metal")
            sc.label(lab[0], w - .16, hh - .16, lab[1], rnd.choice(["crt", "code", "static", "crt"]), seed=rnd.randrange(99))
            y += hh + .06
        u += w + .06


def build_arcade_interior(sc):
    A = elev.ARC_IN
    x0, z0, x1, z1 = A["box"]
    yf, yc = 4.05, 9.3
    rnd = random.Random(11)
    sc.box(x0, yf - .01, z0, x1, yf + .012, z1, "in-floor", "gloss")
    # wall lining with neon line art, LED skirting, ceiling strips
    for (lx, lz, w, ry) in (((x0 + x1) / 2, z0 + .02, x1 - x0, 0), ((x0 + x1) / 2, z1 - .02, x1 - x0, 180),
                            (x0 + .02, (z0 + z1) / 2, z1 - z0, 90), (x1 - .02, (z0 + z1) / 2, z1 - z0, -90)):
        sc.label([lx, (yf + yc) / 2, lz], w, yc - yf, ry, "neonwall", seed=int(lx + lz))
    for (a, b, c, d) in ((x0, z0 + .03, x1, z0 + .1), (x0, z1 - .1, x1, z1 - .03), (x0 + .03, z0, x0 + .1, z1), (x1 - .1, z0, x1 - .03, z1)):
        sc.box(a, yf + .02, b, c, yf + .08, d, "neon-v", "led")
    for k in range(5):
        z = z0 + 3 + k * (z1 - z0 - 6) / 4
        sc.box(x0 + 3, yc - .06, z - .05, x1 - 3, yc - .02, z + .05, "neon-c" if k % 2 else "neon-v", "led")
    # block-puzzle LED wall on the north wall, framed, with next-piece panels
    lx0, lx1, ly0, ly1 = A["led"]
    sc.box(lx0 - .4, ly0 - .4, z0, lx1 + .4, ly1 + .4, z0 + .35, "navy-d", "metal")
    sc.box(lx0 - .45, ly0 - .45, z0 + .35, lx1 + .45, ly0 - .38, z0 + .4, "neon-v", "led")
    sc.label([(lx0 + lx1) / 2, (ly0 + ly1) / 2, z0 + .36], lx1 - lx0, ly1 - ly0, 0, "tetris")
    for k, y in enumerate((ly0 + .6, ly0 + 1.9, ly0 + 3.2)):
        sc.box(lx1 + .8, y - .55, z0, lx1 + 2.0, y + .55, z0 + .25, "navy-d", "metal")
        sc.label([lx1 + 1.4, y, z0 + .26], 1.0, .9, 0, "piece", seed=k)
    # server and monitor stacks with code screens (NW and NE corners)
    for (a, b, c, d, h) in A["stacks"]:
        sc.box(a, yf, b, c, h, d, "navy-d", "metal")
        _monitor_face(sc, rnd, "S", a, b, c, d + .4, yf, h, inset=.4)
    # CRT monitor tower with the robot face on top, facing the doors
    tx0, tz0, tx1, tz1, th = A["tower"]
    sc.box(tx0 + .4, yf, tz0 + .4, tx1 - .4, th - 1.6, tz1 - .4, "navy-d", "metal")
    for side in "EWNS":
        _monitor_face(sc, rnd, side, tx0, tz0, tx1, tz1, yf, th - 1.6)
    tc = ((tx0 + tx1) / 2, (tz0 + tz1) / 2)
    sc.box(tc[0] - 1.2, th - 1.6, tc[1] - 1.4, tc[0] + 1.2, th, tc[1] + 1.4, "navy-d", "metal")
    sc.label([tc[0] + 1.205, th - .8, tc[1]], 2.4, 1.2, 90, "robot")
    for s_ in (-1, 1):
        sc.box(tc[0] - .5, th, tc[1] + s_ * .9 - .15, tc[0] + .3, th + .35, tc[1] + s_ * .9 + .15, "steel", "metal")
    # drum machines along the west wall, two tiers on a shelf, facing east
    dx0, dx1, dz0, dz1, pitch = A["drums"]
    for tier, yb in enumerate((yf, yf + 1.85)):
        sc.box(x0, yb + 1.65, dz0 - .2, dx1 + .35, yb + 1.75, dz1 + .2, "navy-d", "metal")
        z = dz0
        while z + pitch <= dz1 + .01:
            sc.box(x0, yb, z + .05, dx1, yb + 1.6, z + pitch - .05, "drum", "paint")
            sc.cyl(dx1 + .04, yb + .85, z + pitch / 2, .68, .68, .08, "neon-v" if (int(z) + tier) % 2 else "neon-g", axis="x", seg=28, mat="led")
            sc.cyl(dx1 + .09, yb + .85, z + pitch / 2, .55, .55, .06, "navy-d", axis="x", seg=28, mat="gloss")
            sc.label([dx1 + .125, yb + .85, z + pitch / 2], .95, .95, 90, "drum", seed=int(z * 3) + tier)
            sc.box(dx1, yb + 1.42, z + .2, dx1 + .03, yb + 1.56, z + pitch - .2, "neon-c", "led")
            z += pitch
    # cabinets along the south wall, facing north (teal, angled screen, lit marquee, buttons)
    for (gx, cnt) in A["cabinets"]:
        for i in range(cnt):
            x = gx + i * 1.15
            zb = z1 - .05
            sc.box(x, yf, zb - .8, x + .9, yf + 1.05, zb, "cab", "gloss")
            sc.boxc(x + .45, yf + 1.12, zb - .78, .9, .1, .45, "cab-2", "gloss", rx=-18)
            sc.box(x, yf + 1.05, zb - .55, x + .9, yf + 1.95, zb, "cab", "gloss")
            sc.label([x + .45, yf + 1.5, zb - .56], .74, .62, 180, "game", seed=int(x * 7))
            sc.box(x - .02, yf + 1.95, zb - .7, x + .92, yf + 2.25, zb, "cab-2", "gloss")
            sc.label([x + .45, yf + 2.1, zb - .705], .84, .24, 180, "marquee", seed=int(x))
            for (bx, col) in ((.25, "neon-p"), (.45, "neon-y"), (.65, "neon-c")):
                sc.cyl(x + bx, yf + 1.17, zb - .86, .045, .045, .04, col, seg=10, mat="led")
    for (x, z) in A["stools"]:
        sc.cyl(x, yf, z, .22, .18, .05, "dark", seg=14, mat="metal")
        sc.seg((x, yf, z), (x, yf + .62, z), .04, "steel", "metal", 8)
        sc.cyl(x, yf + .62, z, .2, .2, .08, "neon-p" if int(x) % 2 else "neon-c", seg=16, mat="gloss")
    # egg chairs: white shells open towards the tower, lined in pink or cyan, on a swivel foot
    for i, (x, z) in enumerate(A["eggs"]):
        face = math.degrees(math.atan2(51.67 - z, 30.6 - x))
        sc.cyl(x, yf, z, .45, .3, .12, "steel", seg=18, mat="metal")
        sc.seg((x, yf + .1, z), (x, yf + .4, z), .08, "steel", "metal", 10)
        sc.egg(x, yf + 1.35, z, .82, 1.22, face, "white", "neon-c" if i % 2 else "neon-p")
        fr = math.radians(face)
        sc.cyl(x + math.cos(fr) * .12, yf + .78, z + math.sin(fr) * .12, .5, .5, .12, "in-wall", seg=18, mat="rubber")
    # sphere TV pods with rainbow static, facing the doors
    for (x, z) in A["pods"]:
        sc.cyl(x, yf, z, .8, .7, .3, "navy-d", seg=24, mat="metal")
        sc.cyl(x, yf + .3, z, .6, .6, .12, "neon-g", seg=24, mat="led")
        sc.cyl(x, yf + 1.35, z, .95, .95, 0, "in-wall", axis="s", mat="gloss")
        sc.cyl(x + .62, yf + 1.35, z, .6, .6, .1, "neon-g", axis="x", seg=24, mat="led")
        sc.label([x + .73, yf + 1.35, z], .9, .7, 90, "static", seed=int(z))
    for (x, z) in A["tvs"]:
        sc.box(x - .5, yf, z - .7, x + .5, yf + 1.1, z + .7, "steel", "metal")
        sc.label([x + .505, yf + .6, z], 1.1, .8, 90, "static", seed=int(z) + 3)
    # neon floor tiles (tetromino groups)
    for (x, z, col) in elev.neon_tile_cells():
        sc.box(x + .04, yf, z + .04, x + .98, yf + .03, z + .98, NEON_COL[col], "led")
    # coloured lights, kept well inside the hall so they do not reach the plaza through the walls
    for (x, y, z, col, i_) in ((24.0, 8.2, 45.0, "#9B6BFF", 22), (38.0, 8.2, 45.0, "#3FE6F0", 16), (24.0, 8.2, 58.0, "#FF5FC8", 16),
                               (38.0, 8.2, 58.0, "#9B6BFF", 22), (31.0, 6.0, 51.7, "#9BFF5A", 9)):
        sc.lights.append([x, y, z, col, i_, 11.0])
