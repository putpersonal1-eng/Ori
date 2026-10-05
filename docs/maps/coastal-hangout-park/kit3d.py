"""Detailed model kit for the P-601 3D view: building faces, openings, eaves, stairs, rails and props.

Every part is built from the scene primitives in model3d.Scene (boxes, tubes, extrusions,
plates, tori, 3D text, painted labels), with a material name that the viewer turns into a
textured PBR material. Units are metres; x = east, z = south, y = level above sea.
"""
import math

from shapely.geometry import LineString, Polygon


class Face:
    """An axis-aligned building face. u runs left to right as seen from outside, d points outward."""

    def __init__(self, sc, side, x0, z0, x1, z1):
        self.sc, self.side = sc, side
        if side == "E":
            self.o, self.t, self.n, self.L, self.ry = (x1, z1), (0, -1), (1, 0), z1 - z0, 90
        elif side == "W":
            self.o, self.t, self.n, self.L, self.ry = (x0, z0), (0, 1), (-1, 0), z1 - z0, -90
        elif side == "S":
            self.o, self.t, self.n, self.L, self.ry = (x0, z1), (1, 0), (0, 1), x1 - x0, 0
        else:
            self.o, self.t, self.n, self.L, self.ry = (x1, z0), (-1, 0), (0, -1), x1 - x0, 180
        self.bb = (x0, z0, x1, z1)

    def p(self, u, d=0.0):
        return (self.o[0] + self.t[0] * u + self.n[0] * d, self.o[1] + self.t[1] * u + self.n[1] * d)

    def box(self, u0, u1, y0, y1, d0, d1, col, mat="std"):
        a, b = self.p(u0, d0), self.p(u1, d1)
        self.sc.box(min(a[0], b[0]), y0, min(a[1], b[1]), max(a[0], b[0]), y1, max(a[1], b[1]), col, mat)

    def label(self, uc, yc, w, h, kind, d=.02, **kw):
        x, z = self.p(uc, d)
        self.sc.label([x, yc, z], w, h, self.ry, kind, **kw)

    def disc(self, uc, yc, r, d0, d1, col, mat="std", seg=24, r_out=None):
        x, z = self.p(uc, (d0 + d1) / 2)
        r_out = r if r_out is None else r_out
        pos = self.n[0] > 0 or self.n[1] > 0
        r0, r1 = (r, r_out) if pos else (r_out, r)
        self.sc.cyl(x, yc, z, r0, r1, d1 - d0, col, axis="x" if self.side in "EW" else "z", seg=seg, mat=mat)

    def seg(self, a, b, r, col, mat="metal", n=8):
        (ua, ya, da), (ub, yb, db) = a, b
        pa, pb = self.p(ua, da), self.p(ub, db)
        self.sc.seg((pa[0], ya, pa[1]), (pb[0], yb, pb[1]), r, col, mat, n)

    def ext(self, pts, d0, d1, col, mat="std", bevel=0.0):
        x0, z0, x1, z1 = self.bb
        if self.side == "S":
            self.sc.ext("xy", [(x0 + u, y) for u, y in pts], z1 + d0, d1 - d0, col, mat, bevel)
        elif self.side == "N":
            self.sc.ext("xy", [(x1 - u, y) for u, y in pts], z0 - d1, d1 - d0, col, mat, bevel)
        elif self.side == "E":
            self.sc.ext("zy", [(z1 - u, y) for u, y in pts], x1 + d0, d1 - d0, col, mat, bevel)
        else:
            self.sc.ext("zy", [(z0 + u, y) for u, y in pts], x0 - d1, d1 - d0, col, mat, bevel)

    def torus(self, uc, yc, R, r, d, col, arc=360, rz=0, mat="gloss"):
        x, z = self.p(uc, d)
        self.sc.torus(x, yc, z, R, r, arc, rz, self.ry, col, mat)

    def text(self, txt, uc, y, size, depth, col, d=0.0, mat="gloss", align="c"):
        x, z = self.p(uc, d)
        self.sc.text(txt, x, y, z, size, depth, self.ry, col, mat, align)

    # ---- openings
    def window(self, u0, u1, y0, y1, cols=1, rows=1, frame="dark", fmat="metal", sill="stone", inner=None, ft=.07, depth=.09):
        """Framed window: frame and mullions proud of the wall, glass set back, stone sill."""
        if inner:
            self.label((u0 + u1) / 2, (y0 + y1) / 2, u1 - u0 - .04, y1 - y0 - .04, inner, d=.006)
        self.box(u0 + ft, u1 - ft, y0 + ft, y1 - ft, .012, .03, "glass", "glass")
        for (a, b, c, e) in ((u0, u0 + ft, y0, y1), (u1 - ft, u1, y0, y1), (u0, u1, y1 - ft, y1), (u0, u1, y0, y0 + ft)):
            self.box(a, b, c, e, 0, depth, frame, fmat)
        for i in range(1, cols):
            u = u0 + (u1 - u0) * i / cols
            self.box(u - .03, u + .03, y0, y1, 0, depth * .8, frame, fmat)
        for j in range(1, rows):
            y = y0 + (y1 - y0) * j / rows
            self.box(u0, u1, y - .03, y + .03, 0, depth * .8, frame, fmat)
        if sill:
            self.box(u0 - .08, u1 + .08, y0 - .07, y0 + .01, 0, .16, "cream", sill)

    def shopfront(self, u0, u1, y0, y1, bays, frame="dark", inner="glow", transom=None):
        """Full-height glazing to the floor with a base rail and an optional transom."""
        self.window(u0, u1, y0, y1, cols=bays, rows=1, frame=frame, sill=None, inner=inner, ft=.09, depth=.12)
        self.box(u0, u1, y0, y0 + .18, 0, .14, frame, "metal")
        if transom:
            self.box(u0, u1, transom - .04, transom + .04, 0, .1, frame, "metal")

    def door_slide(self, uc, w, y0, h, frame="dark", off=0.0):
        u0, u1 = uc - w / 2, uc + w / 2
        self.box(u0 - .1, u1 + .1, y0 + h, y0 + h + .22, off, off + .16, frame, "metal")
        for (a, b) in ((u0 - .1, u0), (u1, u1 + .1)):
            self.box(a, b, y0, y0 + h, off, off + .16, frame, "metal")
        for k, (a, b) in enumerate(((u0, uc + .02), (uc - .02, u1))):
            dd = off + (.05 if k == 0 else .1)
            self.box(a, b, y0, y0 + h, dd, dd + .02, "glass", "glass")
            for (c, e) in ((a, a + .05), (b - .05, b)):
                self.box(c, e, y0, y0 + h, dd - .01, dd + .04, frame, "metal")
            self.box(a, b, y0, y0 + .1, dd - .01, dd + .04, frame, "metal")
        self.seg((uc - .25, y0 + .9, off + .16), (uc - .25, y0 + 1.5, off + .16), .015, "steel")
        self.seg((uc + .25, y0 + .9, off + .16), (uc + .25, y0 + 1.5, off + .16), .015, "steel")

    def door_solid(self, uc, w, y0, h, col="steel", mat="metal"):
        u0, u1 = uc - w / 2, uc + w / 2
        self.box(u0 - .08, u1 + .08, y0, y0 + h + .08, 0, .05, "dark", "metal")
        self.box(u0, u1, y0, y0 + h, .03, .07, col, mat)
        self.seg((u1 - .15, y0 + 1.0, .1), (u1 - .45, y0 + 1.0, .1), .018, "steel")

    def downpipe(self, u, y0, y1, d=.12):
        self.seg((u, y0, d), (u, y1, d), .05, "dark", "metal")
        for y in (y0 + .6, (y0 + y1) / 2, y1 - .4):
            self.box(u - .08, u + .08, y - .03, y + .03, 0, d + .02, "dark", "metal")
        self.seg((u, y0, d), (u, y0 - .02, d + .25), .05, "dark", "metal")


# ---------------------------------------------------------------- roofs
def ac_unit(sc, x, y, z, ry=0):
    sc.boxc(x, y + .4, z, 1.0, .8, .45, "white", "paint", ry=ry)
    a = math.radians(ry)
    fx, fz = -math.sin(a) * .23, math.cos(a) * .23
    sc.seg((x + fx * .9, y + .42, z + fz * .9), (x + fx * 1.08, y + .42, z + fz * 1.08), .3, "dark", "metal", 20)
    sc.boxc(x, y + .05, z, 1.1, .1, .55, "dark", "metal", ry=ry)


def flat_roof(sc, x0, z0, x1, z1, y, par, wall_col, wall_mat, cap_col="cream", cap_mat="stone", t=.3, deck=None, sides="NESW"):
    """Flat roof with a parapet and a stone coping; deck colour fills the roof inside."""
    sc.box(x0 + t, y - .05, z0 + t, x1 - t, y + .03, z1 - t, deck or "conc-2", "deck" if deck else "conc")
    walls = {"N": (x0, z0, x1, z0 + t), "S": (x0, z1 - t, x1, z1), "W": (x0, z0, x0 + t, z1), "E": (x1 - t, z0, x1, z1)}
    for k in sides:
        a, b, c, d = walls[k]
        sc.box(a, y, b, c, par, d, wall_col, wall_mat)
        sc.box(a - .04, par, b - .04, c + .04, par + .08, d + .04, cap_col, cap_mat)


def kawara_eave(sc, x0, z0, x1, z1, y, sides, glaze="kawara", proj=.8, inset=.45, rise=.55, ridge="kawara", ends=1.0):
    """Kawara tile eave on the given sides of a rectangle, with mitred hip corners, a ridge,
    round tile ends along the drip edge and onigawara blocks at the corners. ends: how far an eave
    runs past a side with no eave (1.0 = full overhang, 0 = stops flush, e.g. against a taller wall)."""
    out = {"N": z0 - proj, "S": z1 + proj, "W": x0 - proj, "E": x1 + proj}
    inn = {"N": z0 + inset, "S": z1 - inset, "W": x0 + inset, "E": x1 - inset}
    has = set(sides)

    def corner(a, b):            # (outer, inner) plan points of the corner between sides a (N/S) and b (W/E)
        xo, zo = out[b], out[a]
        xi, zi = inn[b], inn[a]
        return (xo, zo), (xi, zi)
    yo, yi = y, y + rise
    mat_for = {"N": "kawara", "S": "kawara", "E": "kawarar", "W": "kawarar"}
    for s in sides:
        if s in "NS":
            if "W" in has:
                ow, iw = corner(s, "W")
            else:
                ow, iw = (x0 - proj * ends, out[s]), (x0 - proj * ends, inn[s])
            if "E" in has:
                oe, ie = corner(s, "E")
            else:
                oe, ie = (x1 + proj * ends, out[s]), (x1 + proj * ends, inn[s])
        else:
            if "N" in has:
                ow, iw = corner("N", s)
            else:
                ow, iw = (out[s], z0 - proj * ends), (inn[s], z0 - proj * ends)
            if "S" in has:
                oe, ie = corner("S", s)
            else:
                oe, ie = (out[s], z1 + proj * ends), (inn[s], z1 + proj * ends)
        pts = [ow, oe, ie, iw]
        sc.plate(pts, [yo, yo, yi, yi], glaze, mat_for[s], t=.12)
        # soffit / wall-top fill under the plate along the wall line
        wl = {"N": z0, "S": z1, "W": x0, "E": x1}[s]
        yw = yo + rise * proj / (proj + inset) - .12
        if s in "NS":
            sc.box(x0, y - .3, min(wl, wl + (.3 if s == "N" else -.3)), x1, yw, max(wl, wl + (.3 if s == "N" else -.3)), "plaster", "plaster")
        else:
            sc.box(min(wl, wl + (.3 if s == "W" else -.3)), y - .3, z0, max(wl, wl + (.3 if s == "W" else -.3)), yw, z1, "plaster", "plaster")
        # ridge along the inner edge
        (ax, az), (bx, bz) = iw, ie
        if s in "NS":
            sc.box(min(ax, bx) - .14, yi - .02, az - .14, max(ax, bx) + .14, yi + .24, az + .14, ridge, "kawara")
        else:
            sc.box(ax - .14, yi - .02, min(az, bz) - .14, ax + .14, yi + .24, max(az, bz) + .14, ridge, "kawara")
        # round tile ends along the drip edge
        (px, pz), (qx, qz) = ow, oe
        L = math.hypot(qx - px, qz - pz)
        k = int(L / .3)
        for i in range(1, k):
            t = i / k
            x, z = px + (qx - px) * t, pz + (qz - pz) * t
            sc.cyl(x, yo + .02, z, .1, .1, .1, glaze, axis="x" if s in "EW" else "z", seg=10, mat="gloss")
    # onigawara at the outer corners and ridge corners
    for a in "NS":
        for b in "WE":
            if a in has and b in has:
                (xo, zo), (xi, zi) = corner(a, b)
                sc.boxc(xo, yo + .18, zo, .34, .42, .34, ridge, "kawara")
                sc.boxc(xi, yi + .22, zi, .4, .34, .4, ridge, "kawara")


# ---------------------------------------------------------------- rails and stairs
def rail_line(sc, pts3, h=1.05, post=1.5, style="bar", cap=None):
    """Railing along a 3D polyline at walking level: posts, a top rail and two mid rails (or glass)."""
    for (a, b) in zip(pts3, pts3[1:]):
        L = math.dist(a, b)
        k = max(1, int(round(L / post)))
        for i in range(k + 1):
            t = i / k
            x, y, z = (a[j] + (b[j] - a[j]) * t for j in range(3))
            sc.seg((x, y, z), (x, y + h, z), .025, "dark", "metal", 8)
        if style == "glass":
            dx, dz = b[0] - a[0], b[2] - a[2]
            ang = math.degrees(math.atan2(dz, dx))
            mx, my, mz = ((a[j] + b[j]) / 2 for j in range(3))
            pitch = math.degrees(math.atan2(b[1] - a[1], math.hypot(dx, dz)))
            sc.boxc(mx, my + h / 2, mz, L, h - .15, .02, "glass", "glass", ry=-ang, rx=0)
        else:
            for f in (.35, .7):
                sc.seg((a[0], a[1] + h * f, a[2]), (b[0], b[1] + h * f, b[2]), .012, "dark", "metal", 6)
        if cap == "timber":
            dx, dz = b[0] - a[0], b[2] - a[2]
            ang = math.degrees(math.atan2(dz, dx))
            sc.boxc((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + h + .03, (a[2] + b[2]) / 2, L + .05, .06, .16, "timber", "timber", ry=-ang)
        else:
            sc.seg((a[0], a[1] + h, a[2]), (b[0], b[1] + h, b[2]), .03, "dark", "metal", 8)


def stair_ns_hq(sc, x0, y0, x1, y1, flights, landing, rails, zt, zb, cheek=True):
    """Straight stair running south (down) between x0..x1: solid treads with rubber nosings,
    cheek walls with a stone coping, and handrails on the cheeks and the centre rails."""
    run = (y1 - y0) - landing * (len(flights) - 1)
    tr = run / sum(f - 1 for f in flights)
    nr = sum(flights)
    r = (zt - zb) / nr
    line = [(y0, zt)]
    y, z = y0, zt
    cx0, cx1 = (x0 + .3, x1 - .3) if cheek else (x0, x1)
    for i, f in enumerate(flights):
        for k in range(1, f):
            z -= r
            sc.box(cx0, zb - .4, y + (k - 1) * tr, cx1, z, y + k * tr, "conc-2", "conc")
            sc.box(cx0, z - .015, y + (k - 1) * tr, cx1, z + .012, y + (k - 1) * tr + .05, "dark", "rubber")
        y += (f - 1) * tr
        line.append((y, z - r))
        if i < len(flights) - 1:
            z -= r
            sc.box(cx0, zb - .4, y, cx1, z, y + landing, "conc-2", "conc")
            y += landing
            line.append((y, z - r))
    line[-1] = (y1, zb)
    if cheek:
        prof_top = [(yy, zz + .55) for yy, zz in line]
        prof = [(y0 - .02, zb - .4)] + [(y0 - .02, zt + .55)] + prof_top[1:] + [(y1, zb + .55), (y1, zb - .4)]
        for xx in (x0, x1 - .3):
            sc.ext("zy", [(a, b) for a, b in prof], xx, .3, "conc", "conc", .02)
        hand = [(yy, zz + .55 + .85) for yy, zz in line]
        for xx in (x0 + .15, x1 - .15):
            pts = [(xx, b, a) for a, b in hand]
            for (p, q) in zip(pts, pts[1:]):
                sc.seg(p, q, .03, "steel", "metal", 8)
            for (a, b) in hand:
                sc.seg((xx, b - .85, a), (xx, b, a), .02, "steel", "metal", 6)
    for xr in rails:
        pts = [(xr, zz, yy) for yy, zz in line]
        rail_line(sc, [(p[0], p[1], p[2]) for p in pts], h=.95, post=1.6)


def quad_steps_hq(sc, q, n_treads, zt, zb, bow=(0.0, 0.0), rails=True):
    """Steps in a traced quad (a-b top, d-c foot), treads following arcs when bow is set."""
    a, b, c, d = q

    def edge(t, k=10):
        p0 = (a[0] + (d[0] - a[0]) * t, a[1] + (d[1] - a[1]) * t)
        p1 = (b[0] + (c[0] - b[0]) * t, b[1] + (c[1] - b[1]) * t)
        bw = bow[0] + (bow[1] - bow[0]) * t
        L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        nx, ny = -(p1[1] - p0[1]) / L, (p1[0] - p0[0]) / L
        if ny < 0:
            nx, ny = -nx, -ny
        m = ((p0[0] + p1[0]) / 2 + nx * bw * 2, (p0[1] + p1[1]) / 2 + ny * bw * 2)
        return [((1 - s) ** 2 * p0[0] + 2 * (1 - s) * s * m[0] + s * s * p1[0],
                 (1 - s) ** 2 * p0[1] + 2 * (1 - s) * s * m[1] + s * s * p1[1]) for s in [j / k for j in range(k + 1)]]
    r = (zt - zb) / (n_treads + 1)
    for k in range(1, n_treads + 1):
        top, bot = edge((k - 1) / n_treads), edge(k / n_treads)      # one tread band per riser
        y = zt - k * r
        sc.prism(Polygon(top + bot[::-1]).buffer(0), zb - .4, y, "conc-2", "conc")
        sc.polyseg([(x, y + .006, z) for x, z in top], .02, "dark", "rubber")
    for side in ((0, -1) if rails else ()):
        pts = []
        for k in range(0, n_treads + 1):
            e = edge(k / n_treads)
            x, z = e[side]
            pts.append((x, zt - k * r + .9, z))
        sc.polyseg(pts, .03, "steel", "metal")
        for p in pts[::3]:
            sc.seg((p[0], p[1] - .9, p[2]), p, .02, "steel", "metal", 6)


# ---------------------------------------------------------------- props
BANNER_DESIGNS = ["umi", "cafe", "games", "omiyage", "beach", "sakura", "fes", "shell"]


def lamp(sc, x, y, z, h=5.2, ry=0.0, banners=None):
    """Post-top lantern lamp centred on the pole; optional bracket with two hanging banners (designs)."""
    sc.cyl(x, y, z, .2, .17, .35, "dark", seg=14, mat="metal")
    sc.cyl(x, y + .35, z, .1, .09, 1.0, "yel", seg=14, mat="paint")
    sc.seg((x, y + 1.35, z), (x, y + h, z), .07, "dark", "metal", 12)
    sc.cyl(x, y + h, z, .12, .14, .12, "dark", seg=12, mat="metal")
    sc.cyl(x, y + h + .12, z, .16, .24, .62, "warm", seg=12, mat="led")
    for k in range(4):
        a = k * math.pi / 2 + math.radians(ry) + math.pi / 4
        sc.seg((x + math.cos(a) * .17, y + h + .13, z + math.sin(a) * .17),
               (x + math.cos(a) * .25, y + h + .73, z + math.sin(a) * .25), .012, "dark", "metal", 4)
    sc.cyl(x, y + h + .74, z, .33, .08, .22, "dark", seg=12, mat="metal")
    sc.cyl(x, y + h + .96, z, .05, .05, .1, "dark", seg=8, mat="metal")
    if banners:
        a = math.radians(ry)
        ux, uz = math.cos(a), math.sin(a)
        for yy in (y + h - .55, y + h - 3.15):
            sc.seg((x - ux * 1.2, yy, z - uz * 1.2), (x + ux * 1.2, yy, z + uz * 1.2), .025, "yel", "paint", 8)
            for s_ in (-1.2, 1.2):
                sc.cyl(x + ux * s_, yy, z + uz * s_, .04, .04, 0, "yel", axis="s", mat="paint")
        for k, (u0, u1) in enumerate(((-1.12, -.16), (.16, 1.12))):
            uc = (u0 + u1) / 2
            bx, bz = x + ux * uc, z + uz * uc
            nx, nz = -math.sin(a), math.cos(a)
            for sgn, rot in ((1, -ry), (-1, -ry + 180)):
                sc.label([bx + nx * .012 * sgn, y + h - 1.85, bz + nz * .012 * sgn], u1 - u0, 2.5, rot, "banner", d=banners[k])


def bench_hq(sc, x, y, z, L=2.0, ang=0.0):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)

    def P(u, v):
        return (x + u * ca - v * sa, z + u * sa + v * ca)
    for v in (-.2, 0, .2):
        px, pz = P(0, v)
        sc.boxc(px, y + .44, pz, L, .04, .16, "timber", "timber", ry=-ang)
    for v in (.3,):
        for hh in (.62, .78):
            px, pz = P(0, v + .02)
            sc.boxc(px, y + hh, pz, L, .12, .04, "timber", "timber", ry=-ang)
    for u in (-L / 2 + .2, L / 2 - .2):
        px, pz = P(u, 0)
        sc.boxc(px, y + .21, pz, .06, .42, .5, "dark", "metal", ry=-ang)
        qx, qz = P(u, .3)
        sc.seg((qx, y, qz), (qx, y + .85, qz), .025, "dark", "metal", 6)


def parasol_set(sc, x, y, z, r=1.5, col="white", chairs=4, wood=True, seed=0):
    sc.cyl(x, y, z, .28, .28, .05, "dark", seg=16, mat="metal")
    sc.seg((x, y, z), (x, y + 2.55, z), .028, "steel", "metal", 8)
    sc.cyl(x, y + 2.05, z, r, .06, .5, col, seg=8, mat="paint")
    sc.cyl(x, y + 1.93, z, r, r, .12, col, seg=8, mat="paint")
    for k in range(8):
        a = k * math.pi / 4
        sc.seg((x, y + 2.3, z), (x + math.cos(a) * r * .92, y + 2.02, z + math.sin(a) * r * .92), .01, "steel", "metal", 4)
    tcol, tmat = ("timber", "timber") if wood else ("white", "paint")
    sc.cyl(x, y + .72, z, .48, .48, .04, tcol, seg=20, mat=tmat)
    sc.seg((x, y, z), (x, y + .72, z), .04, "dark", "metal", 8)
    sc.cyl(x, y, z, .25, .25, .03, "dark", seg=14, mat="metal")
    for k in range(chairs):
        a = k * 2 * math.pi / chairs + .4 + seed * .3
        cx, cz = x + math.cos(a) * .95, z + math.sin(a) * .95
        chair(sc, cx, y, cz, math.degrees(a) + 180, tcol, tmat)


def chair(sc, x, y, z, face_deg, col="timber", mat="timber"):
    """Bistro chair facing face_deg (plan angle the sitter looks towards)."""
    a = math.radians(face_deg)
    fx, fz = math.cos(a), math.sin(a)
    rx, rz = -fz, fx
    sc.boxc(x, y + .45, z, .44, .04, .42, col, mat, ry=-face_deg)
    bx, bz = x - fx * .2, z - fz * .2
    sc.boxc(bx, y + .72, bz, .04, .32, .4, col, mat, ry=-face_deg)
    for (u, v) in ((.18, .17), (.18, -.17), (-.18, .17), (-.18, -.17)):
        lx, lz = x + fx * u + rx * v, z + fz * u + rz * v
        sc.seg((lx, y, lz), (lx, y + .45, lz), .015, "dark", "metal", 5)


def lounger_hq(sc, x, y, z, ang):
    a = math.radians(ang)
    sc.boxc(x, y + .3, z, 1.9, .08, .65, "white", "paint", ry=-ang + 90)
    sc.boxc(x, y + .37, z, 1.3, .06, .6, "cyan", "std", ry=-ang + 90)
    ex, ez = x + math.sin(a) * .0, z + math.cos(a) * .7
    for (u, v) in ((.8, .28), (.8, -.28), (-.8, .28), (-.8, -.28)):
        c, s = math.cos(math.radians(-ang + 90)), math.sin(math.radians(-ang + 90))
        lx, lz = x + u * c, z - u * s
        sc.seg((lx + v * s, y, lz + v * c), (lx + v * s, y + .3, lz + v * c), .02, "white", "paint", 5)


def planter_hq(sc, g, base, inner_t=.3, h=.6, cap="cream"):
    """Raised planter: concrete wall, stone coping with a small overhang, soil bed."""
    inner = g.buffer(-inner_t, join_style="mitre")
    sc.prism(g.difference(inner), base - .2, base + h - .06, "conc", "conc")
    ring = g.buffer(.03, join_style="mitre").difference(g.buffer(-inner_t - .03, join_style="mitre"))
    sc.prism(ring, base + h - .06, base + h, cap, "stone")
    sc.prism(inner, base - .2, base + h - .12, "bed", "ground")
    return inner


def _simple_parts(g):
    """Split a polygon with holes into hole-free pieces (cuts through each hole's centre)."""
    from shapely.geometry import MultiPolygon, box as _box
    out = []
    for q in (g.geoms if isinstance(g, MultiPolygon) else [g]):
        if q.is_empty:
            continue
        if not q.interiors:
            out.append(q)
            continue
        cx = Polygon(q.interiors[0]).centroid.x
        x0, z0, x1, z1 = q.bounds
        for half in (_box(x0 - 1, z0 - 1, cx, z1 + 1), _box(cx, z0 - 1, x1 + 1, z1 + 1)):
            out += _simple_parts(q.intersection(half))
    return [p for p in out if p.geom_type == "Polygon" and p.area > .005]


def planter_ground(sc, g, ground_fn, inner_t=.3, h=.6, cap="cream"):
    """Raised planter that follows the ground under it: wall, stone coping and soil, each vertex at ground + height.
    The ground is read 0.7 m inside the outline, so an edge on a level boundary (plaza / promenade) does not pick up
    the neighbouring level and tilt the planter; along a sloping street it still follows the slope."""
    from shapely.geometry import Point
    from shapely.ops import nearest_points
    core = g.buffer(-.7)
    if core.is_empty:
        core = g.representative_point()

    def ground(x, z):
        p = Point(x, z)
        if not core.contains(p):
            p = nearest_points(core, p)[0]
        return ground_fn(p.x, p.y)
    inner = g.buffer(-inner_t, join_style="mitre")
    gl = [ground(x, z) for x, z in list(g.exterior.coords)]
    bot = min(gl) - .3
    for part in _simple_parts(g.difference(inner)):
        sc.plate_poly(part.segmentize(1.5), lambda x, z: ground(x, z) + h - .06, "conc", "conc", bot=bot)
    ring = g.buffer(.03, join_style="mitre").difference(g.buffer(-inner_t - .03, join_style="mitre"))
    for part in _simple_parts(ring):
        sc.plate_poly(part.segmentize(1.5), lambda x, z: ground(x, z) + h, cap, "stone", t=.06)
    for part in _simple_parts(inner):
        sc.plate_poly(part.segmentize(2.0), lambda x, z: ground(x, z) + h - .12, "bed", "ground", bot=bot)
    return inner, ground


def truck_hq(sc, cx, cz, ang, base, col):
    """Food truck: chassis, glossy body, cab, open serving hatch with an awning flap, wheels, lights."""
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)

    def P(u, v):
        return (cx + u * ca - v * sa, cz + u * sa + v * ca)

    def B(u, v, y, su, sy, sv, c, m, rx=0.0):
        x, z = P(u, v)
        sc.boxc(x, base + y, z, su, sy, sv, c, m, ry=-ang, rx=rx)
    B(0, 0, .55, 6.2, .22, 2.1, "dark", "metal")
    B(-.75, 0, 1.85, 5.0, 2.45, 2.5, "cream", "gloss")
    B(-.75, 0, 3.12, 4.8, .1, 2.3, "white", "paint")
    B(2.5, 0, 1.6, 1.5, 1.95, 2.4, col, "gloss")
    B(3.24, 0, 2.05, .04, .7, 2.0, "glass", "glass")
    for v in (1.21, -1.21):
        B(2.45, v, 2.05, 1.0, .6, .03, "glass", "glass")
    # serving hatch on the +v side, open, with counter and flap
    B(-1.0, 1.24, 2.05, 3.4, 1.15, .04, "dark", "rubber")
    B(-1.0, 1.4, 1.42, 3.5, .06, .36, "steel", "metal")
    x, z = P(-1.0, 1.65)
    sc.boxc(x, base + 2.85, z, 3.6, .05, .95, col, "gloss", ry=-ang, rx=-25)
    sc.label([x, base + 3.25, z], 2.4, .45, -ang, "pill", txt="STREET EATS", fg="#FFFFFF", bg="#2E333B")
    B(-.75, 1.255, 1.15, 5.0, .25, .02, col, "gloss")
    B(-.75, -1.255, 1.15, 5.0, .25, .02, col, "gloss")
    for (u, v) in ((-2.1, 1.0), (-2.1, -1.0), (2.3, 1.0), (2.3, -1.0)):
        p0 = P(u, v * 1.02)
        p1 = P(u, v * 1.3)
        sc.seg((p0[0], base + .42, p0[1]), (p1[0], base + .42, p1[1]), .42, "dark", "rubber", 18)
        p2 = P(u, v * 1.31)
        sc.seg((p1[0], base + .42, p1[1]), (p2[0], base + .42, p2[1]), .22, "steel", "metal", 14)
    for v in (.85, -.85):
        x, z = P(3.26, v)
        sc.cyl(x, base + 1.15, z, .12, .12, 0, "yel-3", axis="s", mat="led")


def gate_hq(sc, x0, x1, gy, base):
    """Shotengai gate: vermilion posts on stone plinths, tie beam, kumiko lattice, plaque,
    an upturned black kasagi (extruded curve) and lanterns."""
    for x in (x0, x1):
        sc.boxc(x, base + .25, gy, 1.0, .5, 1.0, "conc", "stone")
        sc.boxc(x, base + .5 + 3.4, gy, .66, 6.8, .66, "verm", "gloss")
        sc.boxc(x, base + .55, gy, .78, .1, .78, "dark", "metal")
    sc.box(x0 - .95, base + 5.5, gy - .2, x1 + .95, base + 6.05, gy + .2, "verm", "gloss")
    for x, k in ((x0, 1), (x1, -1)):
        a, c = sorted((x + k * .33, x + k * 1.65))
        sc.box(a, base + 6.05, gy - .05, c, base + 7.0, gy + .05, "cream", "std")
        for i in range(1, 6):
            u = a + (c - a) * i / 6
            sc.box(u - .02, base + 6.05, gy - .07, u + .02, base + 7.0, gy + .07, "dark", "timber")
        for j in range(1, 4):
            yy = base + 6.05 + .95 * j / 4
            sc.box(a, yy - .02, gy - .07, c, yy + .02, gy + .07, "dark", "timber")
    xm = (x0 + x1) / 2
    sc.box(xm - 1.95, base + 6.08, gy - .14, xm + 1.95, base + 7.02, gy + .14, "dark", "gloss")
    for ry, off in ((0, .15), (180, -.15)):
        sc.label([xm, base + 6.55, gy + off], 3.7, .82, ry, "plaque", txt="うみ シーサイドパーク", sub="UMI SEASIDE PARK")
    sc.box(x0 - 1.45, base + 7.0, gy - .26, x1 + 1.45, base + 7.25, gy + .26, "verm", "gloss")
    # kasagi: upturned ends, extruded across the gate depth
    L = (x1 - x0) / 2 + 2.1
    top, bot = [], []
    for i in range(25):
        t = -1 + 2 * i / 24
        lift = .55 * abs(t) ** 3
        top.append((xm + t * L, base + 7.9 + lift))
        bot.append((xm + t * (L - .15), base + 7.25 + lift * .9))
    sc.ext("xy", top + bot[::-1], gy - .48, .96, "dark", "gloss", .03)
    for i in range(5):
        x = x0 + 1.6 + i * (x1 - x0 - 3.2) / 4
        lantern(sc, x, base + 4.92, gy, .3)


def lantern(sc, x, y, z, r=.3):
    sc.seg((x, y + r * 1.25, z), (x, y + r * 2.2, z), .008, "dark", "metal", 4)
    sc.cyl(x, y, z, r, r, r * 2.6, "verm", axis="s", mat="led")
    sc.cyl(x, y + r * 1.2, z, r * .55, r * .55, .08, "dark", seg=12, mat="metal")
    sc.cyl(x, y - r * 1.3, z, r * .55, r * .55, .08, "dark", seg=12, mat="metal")
