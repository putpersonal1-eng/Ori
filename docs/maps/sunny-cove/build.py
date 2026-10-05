#!/usr/bin/env python3
"""Sunny Cove Park - layout and technical drawing generator.

Writes index.html (all sheets, light/dark themed) and svg/*.svg (standalone,
light theme) next to this file.

Geometry is in metres. Plan X runs west -> east, plan Y runs north -> south,
Z is height above sea level (datum +-0.00). Multiply by 100 for Unreal units.

    python3 build.py
"""
import math
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------------------------- tokens
LIGHT = {
    "paper": "#E7EDF0", "sheet": "#FBFCFC", "rule": "#C4D1D8",
    "ink": "#16283A", "ink-2": "#4A5C6F", "ink-3": "#93A3B2",
    "accent": "#D93A55", "teal": "#0D7F8A",
    "sand": "#F2E1BA", "sea": "#BCE4EB", "sea-deep": "#8CC7D8",
    "lawn": "#CDE4B3", "brick": "#EDD0BD", "paver": "#E1E6EA",
    "conc": "#D3D9DC", "timber": "#E6CFA6", "rock": "#CBC5BC",
    "bldg": "#D5DFE9", "tree": "#9BCA84", "tree-edge": "#58894C",
    "chalk-y": "#F0BE2C", "chalk-p": "#E5539A", "chalk-c": "#24ABCC",
}
DARK = {
    "paper": "#0A1522", "sheet": "#0F1F31", "rule": "#233A52",
    "ink": "#DCE8F2", "ink-2": "#9EB3C7", "ink-3": "#566F88",
    "accent": "#FF6E86", "teal": "#45C6CF",
    "sand": "#4A4231", "sea": "#1C4757", "sea-deep": "#133447",
    "lawn": "#29452F", "brick": "#4D3732", "paver": "#22354A",
    "conc": "#2B3B4C", "timber": "#463828", "rock": "#3A3F47",
    "bldg": "#1E3550", "tree": "#3D6942", "tree-edge": "#7DAE73",
    "chalk-y": "#D9AA2A", "chalk-p": "#D45591", "chalk-c": "#2E9EBB",
}
FONT_URL = ("https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600&amp;family=Barlow+Condensed:wght@500;600;700"
            "&amp;family=Bricolage+Grotesque:opsz,wght@12..96,700;12..96,800&amp;display=swap")
FONTS = {
    "f-display": '"Bricolage Grotesque", ui-sans-serif, system-ui, sans-serif',
    "f-body": '"Barlow", ui-sans-serif, system-ui, sans-serif',
    "f-cond": '"Barlow Condensed", "Arial Narrow", ui-sans-serif, sans-serif',
}

SVG_CSS = """
.sheet-bg{fill:var(--sheet)}
.frame{fill:none;stroke:var(--ink);stroke-width:1.4}
.frame-in{fill:none;stroke:var(--ink);stroke-width:.7}
.ln{fill:none;stroke:var(--ink);stroke-width:1}
.ln-h{fill:none;stroke:var(--ink);stroke-width:2;stroke-linejoin:round;stroke-linecap:round}
.ln-m{fill:none;stroke:var(--ink-2);stroke-width:.8}
.ln-f{fill:none;stroke:var(--ink-3);stroke-width:.6}
.ln-b{fill:none;stroke:var(--ink-2);stroke-width:.8;stroke-dasharray:4 3}
.ln-water{fill:none;stroke:var(--teal);stroke-width:1.2}
.gap{stroke:var(--sheet);stroke-width:5}
.z-paver,.z-town{fill:var(--paver)}
.z-brick{fill:var(--brick)}
.z-lawn{fill:var(--lawn)}
.z-conc{fill:var(--conc)}
.z-timber{fill:var(--timber)}
.z-sand{fill:var(--sand)}
.z-sea{fill:var(--sea)}
.z-deep{fill:var(--sea-deep)}
.z-cliff{fill:var(--rock)}
.z-rockp{fill:var(--rock);opacity:.75}
.bldg{fill:var(--bldg);stroke:var(--ink);stroke-width:1.6}
.bldg-l{fill:var(--bldg);stroke:var(--ink);stroke-width:.9}
.beyond{fill:var(--bldg);fill-opacity:.55;stroke:var(--ink-2);stroke-width:.8}
.under{fill:var(--bldg);fill-opacity:.5;stroke:var(--ink-2);stroke-width:.8;stroke-dasharray:3 2}
.wall{fill:var(--sheet);stroke:var(--ink);stroke-width:4}
.glass{fill:none;stroke:var(--teal);stroke-width:1.6}
.solid{fill:var(--ink)}
.led{fill:var(--ink);opacity:.85}
.conc{fill:var(--conc);stroke:var(--ink);stroke-width:1}
.poche{fill:var(--rock)}
.water{fill:var(--sea);opacity:.85}
.tree{fill:var(--tree);stroke:var(--tree-edge);stroke-width:.7}
.trunk{fill:none;stroke:var(--tree-edge);stroke-width:1.4}
.prop{fill:var(--sheet);stroke:var(--ink);stroke-width:.7}
.prop-d{fill:var(--ink-2)}
.umb-y{fill:var(--chalk-y);stroke:var(--ink);stroke-width:.5}
.umb-p{fill:var(--chalk-p);stroke:var(--ink);stroke-width:.5}
.umb-c{fill:var(--chalk-c);stroke:var(--ink);stroke-width:.5}
.chalk-y{fill:var(--chalk-y)}
.chalk-p{fill:var(--chalk-p)}
.chalk-c{fill:var(--chalk-c)}
.ring-acc{fill:none;stroke:var(--accent);stroke-width:1.6}
.bunting{fill:none;stroke:var(--chalk-p);stroke-width:1;stroke-dasharray:2.5 2}
.pat-s{fill:none;stroke:var(--ink-3);stroke-width:.5}
.pat-d{fill:var(--ink-3)}
.pat-w{fill:none;stroke:var(--sheet);stroke-width:.7;opacity:.7}
.pat-g{fill:none;stroke:var(--tree-edge);stroke-width:.6;opacity:.55}
.path-edge{fill:none;stroke:var(--ink-3);stroke-width:17}
.path-fill{fill:none;stroke:var(--paver);stroke-width:15}
.grid{fill:none;stroke:var(--ink-3);stroke-width:.5;stroke-dasharray:2 4}
.bubble{fill:var(--sheet);stroke:var(--ink);stroke-width:.8}
.circ1{fill:none;stroke:var(--accent);stroke-width:2.2;stroke-dasharray:8 4;stroke-linecap:round}
.circ2{fill:none;stroke:var(--accent);stroke-width:1.2;stroke-dasharray:3 3;stroke-linecap:round}
.sight{fill:none;stroke:var(--teal);stroke-width:1.4;stroke-dasharray:1.5 3.5;stroke-linecap:round}
.cut{fill:none;stroke:var(--accent);stroke-width:.9;stroke-dasharray:14 3 2 3}
.cut-h{fill:none;stroke:var(--accent);stroke-width:3}
.acc-f{fill:var(--accent)}
.teal-f{fill:var(--teal)}
.ink-f{fill:var(--ink)}
.sheet-f{fill:var(--sheet)}
.dim{fill:none;stroke:var(--ink);stroke-width:.6}
.dim-t{fill:none;stroke:var(--ink);stroke-width:1.1}
.avatar{fill:var(--chalk-c);stroke:var(--ink);stroke-width:.6}
.cam{fill:var(--teal)}
.t-zone{font:700 12px var(--f-cond);letter-spacing:.08em;fill:var(--ink)}
.t-big{font:700 16px var(--f-cond);letter-spacing:.14em;fill:var(--ink)}
.t-lbl{font:600 9.5px var(--f-cond);letter-spacing:.03em;fill:var(--ink)}
.t-sm{font:500 8px var(--f-cond);letter-spacing:.02em;fill:var(--ink-2)}
.t-dim{font:600 8.5px var(--f-cond);fill:var(--ink)}
.t-head{font:700 15px var(--f-cond);letter-spacing:.12em;fill:var(--ink)}
.t-title{font:800 21px var(--f-display);fill:var(--ink)}
.t-acc{fill:var(--accent)}
.t-teal{fill:var(--teal)}
.t-inv{fill:var(--sheet)}
.halo{paint-order:stroke;stroke:var(--sheet);stroke-width:3px;stroke-linejoin:round}
"""


# -------------------------------------------------------------------- helpers
def n(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def frange(a, b, step):
    out, v = [], a
    while v < b - 1e-9:
        out.append(round(v, 4))
        v += step
    return out


class Cv:
    """World -> SVG px mapping. px = ox + (u-u0)*sx ; py = oy + (v-v0)*sy."""

    def __init__(self, sx, sy, ox, oy, u0=0.0, v0=0.0):
        self.sx, self.sy, self.ox, self.oy, self.u0, self.v0 = sx, sy, ox, oy, u0, v0
        self.o = []

    def X(self, u):
        return self.ox + (u - self.u0) * self.sx

    def Y(self, v):
        return self.oy + (v - self.v0) * self.sy

    def add(self, s):
        self.o.append(s)

    @staticmethod
    def _a(cls, extra):
        return (f' class="{cls}"' if cls else "") + extra

    def _pts(self, pts):
        return " ".join(f"{n(self.X(u))},{n(self.Y(v))}" for u, v in pts)

    def rect(self, u0, v0, u1, v1, cls="", extra="", rx=0):
        xa, xb = sorted((self.X(u0), self.X(u1)))
        ya, yb = sorted((self.Y(v0), self.Y(v1)))
        r = f' rx="{n(rx)}"' if rx else ""
        self.add(f'<rect x="{n(xa)}" y="{n(ya)}" width="{n(xb - xa)}" height="{n(yb - ya)}"{r}{self._a(cls, extra)}/>')

    def poly(self, pts, cls="", extra=""):
        self.add(f'<polygon points="{self._pts(pts)}"{self._a(cls, extra)}/>')

    def pline(self, pts, cls="", extra=""):
        self.add(f'<polyline points="{self._pts(pts)}"{self._a(cls, extra)}/>')

    def line(self, u0, v0, u1, v1, cls="", extra=""):
        self.add(f'<line x1="{n(self.X(u0))}" y1="{n(self.Y(v0))}" x2="{n(self.X(u1))}" '
                 f'y2="{n(self.Y(v1))}"{self._a(cls, extra)}/>')

    def circle(self, u, v, r, cls="", extra=""):
        self.add(f'<circle cx="{n(self.X(u))}" cy="{n(self.Y(v))}" r="{n(r * abs(self.sx))}"{self._a(cls, extra)}/>')

    def ellipse(self, u, v, ru, rv, cls="", extra=""):
        self.add(f'<ellipse cx="{n(self.X(u))}" cy="{n(self.Y(v))}" rx="{n(ru * abs(self.sx))}" '
                 f'ry="{n(rv * abs(self.sy))}"{self._a(cls, extra)}/>')

    def d(self, cmds):
        out = []
        for c in cmds:
            k, vals = c[0], c[1:]
            pts = [f"{n(self.X(vals[i]))} {n(self.Y(vals[i + 1]))}" for i in range(0, len(vals), 2)]
            out.append(k + " ".join(pts))
        return " ".join(out)

    def path(self, cmds, cls="", extra=""):
        self.add(f'<path d="{self.d(cmds)}"{self._a(cls, extra)}/>')

    def text(self, u, v, s, cls="t-lbl", anchor="middle", rot=None, extra=""):
        x, y = self.X(u), self.Y(v)
        tr = f' transform="rotate({n(rot)} {n(x)} {n(y)})"' if rot else ""
        self.add(f'<text x="{n(x)}" y="{n(y)}" text-anchor="{anchor}" class="{cls}"{tr}{extra}>{esc(s)}</text>')

    def svg(self):
        return "\n".join(self.o)


def hdim(cv, u0, u1, v, label=None, ext=None, cls="t-dim halo"):
    x0, x1, y = cv.X(u0), cv.X(u1), cv.Y(v)
    s = []
    if ext is not None:
        ye = cv.Y(ext)
        sgn = 1 if y > ye else -1
        for x in (x0, x1):
            s.append(f'<line class="dim" x1="{n(x)}" y1="{n(ye + 2 * sgn)}" x2="{n(x)}" y2="{n(y + 3 * sgn)}"/>')
    s.append(f'<line class="dim" x1="{n(x0 - 3)}" y1="{n(y)}" x2="{n(x1 + 3)}" y2="{n(y)}"/>')
    for x in (x0, x1):
        s.append(f'<line class="dim-t" x1="{n(x - 3)}" y1="{n(y + 3)}" x2="{n(x + 3)}" y2="{n(y - 3)}"/>')
    lab = label if label is not None else f"{abs(u1 - u0):.2f}"
    s.append(f'<text class="{cls}" x="{n((x0 + x1) / 2)}" y="{n(y - 3)}" text-anchor="middle">{esc(lab)}</text>')
    cv.add("".join(s))


def vdim(cv, u, v0, v1, label=None, ext=None, cls="t-dim halo", side=-1):
    x, y0, y1 = cv.X(u), cv.Y(v0), cv.Y(v1)
    s = []
    if ext is not None:
        xe = cv.X(ext)
        sgn = 1 if x > xe else -1
        for y in (y0, y1):
            s.append(f'<line class="dim" x1="{n(xe + 2 * sgn)}" y1="{n(y)}" x2="{n(x + 3 * sgn)}" y2="{n(y)}"/>')
    s.append(f'<line class="dim" x1="{n(x)}" y1="{n(min(y0, y1) - 3)}" x2="{n(x)}" y2="{n(max(y0, y1) + 3)}"/>')
    for y in (y0, y1):
        s.append(f'<line class="dim-t" x1="{n(x - 3)}" y1="{n(y + 3)}" x2="{n(x + 3)}" y2="{n(y - 3)}"/>')
    lab = label if label is not None else f"{abs(v1 - v0):.2f}"
    tx, ty = (x + 10 if side > 0 else x - 4), (y0 + y1) / 2
    s.append(f'<text class="{cls}" x="{n(tx)}" y="{n(ty)}" text-anchor="middle" '
             f'transform="rotate(-90 {n(tx)} {n(ty)})">{esc(lab)}</text>')
    cv.add("".join(s))


def etag(cv, u, z, label, below=False, anchor="start"):
    """Section elevation tag: filled triangle on the level, text beside it."""
    x, y = cv.X(u), cv.Y(z)
    cv.add(f'<polygon class="ink-f" points="{n(x - 4)},{n(y - 7)} {n(x + 4)},{n(y - 7)} {n(x)},{n(y)}"/>')
    tx = x + 7 if anchor == "start" else x - 7
    ty = y + 11 if below else y - 3
    cv.add(f'<text class="t-dim halo" x="{n(tx)}" y="{n(ty)}" text-anchor="{anchor}">{esc(label)}</text>')


def callout(cv, pu, pv, tu, tv, label, anchor="start", cls="t-lbl halo"):
    cv.line(pu, pv, tu, tv, "ln-m")
    cv.circle(pu, pv, 0, "")
    cv.add(f'<circle class="ink-f" cx="{n(cv.X(pu))}" cy="{n(cv.Y(pv))}" r="1.8"/>')
    off = 3 if anchor == "start" else -3
    cv.add(f'<text class="{cls}" x="{n(cv.X(tu) + off)}" y="{n(cv.Y(tv) - 2)}" text-anchor="{anchor}">{esc(label)}</text>')


def avatar(cv, u, z, h=1.3, seated=False):
    """Chibi avatar silhouette (big head), drawn undistorted from px height."""
    x, y0 = cv.X(u), cv.Y(z)
    H = h * abs(cv.sy)
    if seated:
        bw, bh, hr = .36 * H, .34 * H, .22 * H
        cv.add(f'<rect class="avatar" x="{n(x - bw / 2)}" y="{n(y0 - bh)}" width="{n(bw)}" height="{n(bh)}" rx="{n(bw * .4)}"/>')
        cv.add(f'<rect class="avatar" x="{n(x)}" y="{n(y0 - .12 * H)}" width="{n(.34 * H)}" height="{n(.12 * H)}" rx="{n(.05 * H)}"/>')
        cv.add(f'<rect class="avatar" x="{n(x + .26 * H)}" y="{n(y0 - .12 * H)}" width="{n(.1 * H)}" height="{n(.4 * H)}" rx="{n(.04 * H)}"/>')
        cv.add(f'<circle class="avatar" cx="{n(x)}" cy="{n(y0 - bh - hr * .85)}" r="{n(hr)}"/>')
        return
    bw, bh, hr = .36 * H, .56 * H, .22 * H
    cv.add(f'<rect class="avatar" x="{n(x - bw / 2)}" y="{n(y0 - bh)}" width="{n(bw)}" height="{n(bh)}" rx="{n(bw * .4)}"/>')
    cv.add(f'<circle class="avatar" cx="{n(x)}" cy="{n(y0 - bh - hr * .85)}" r="{n(hr)}"/>')


def defs(p):
    return f"""<defs>
<pattern id="{p}-brick" width="8" height="8" patternUnits="userSpaceOnUse"><path class="pat-s" d="M0 4 2 2 4 4 6 2 8 4M0 8 2 6 4 8 6 6 8 8"/></pattern>
<pattern id="{p}-sand" width="9" height="9" patternUnits="userSpaceOnUse"><circle class="pat-d" cx="1.5" cy="1.5" r=".55"/><circle class="pat-d" cx="6" cy="4.5" r=".5"/><circle class="pat-d" cx="3" cy="7.5" r=".45"/></pattern>
<pattern id="{p}-board" width="3" height="10" patternUnits="userSpaceOnUse"><path class="pat-s" d="M0 0V10"/></pattern>
<pattern id="{p}-rock" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><path class="pat-s" d="M0 0V6"/></pattern>
<pattern id="{p}-water" width="18" height="10" patternUnits="userSpaceOnUse"><path class="pat-w" d="M1 6q2-2.4 4 0t4 0"/></pattern>
<pattern id="{p}-lawn" width="14" height="12" patternUnits="userSpaceOnUse"><path class="pat-g" d="M3 3l1.2 2 1.2-2M9 8l1.2 2 1.2-2"/></pattern>
<pattern id="{p}-hatch" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)"><path class="pat-s" d="M0 0V5"/></pattern>
<pattern id="{p}-earth" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><path class="pat-s" d="M0 0V6"/><circle class="pat-d" cx="3" cy="3" r=".5"/></pattern>
<marker id="{p}-arr" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path class="acc-f" d="M0 0 10 5 0 10z"/></marker>
<marker id="{p}-arrt" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path class="teal-f" d="M0 0 10 5 0 10z"/></marker>
<marker id="{p}-arrk" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="4.5" markerHeight="4.5" orient="auto-start-reverse"><path class="ink-f" d="M0 0 10 5 0 10z"/></marker>
</defs>"""


def title_strip(cv, x, y, no, title, sub):
    cv.add(f'<rect class="ink-f" x="{x}" y="{y - 13}" width="{len(no) * 8.6 + 12}" height="18"/>')
    cv.add(f'<text class="t-head t-inv" x="{x + 6}" y="{y + 1}">{esc(no)}</text>')
    cv.add(f'<text class="t-head" x="{x + len(no) * 8.6 + 22}" y="{y + 1}">{esc(title)}</text>')
    cv.add(f'<text class="t-sm" x="{x}" y="{y + 18}">{esc(sub)}</text>')


def section_bubble(cv, px, py, letter, angle):
    """Section marker: circle + letter + view-direction triangle (angle deg, 0 = east, -90 = north)."""
    a = math.radians(angle)
    tx, ty = px + math.cos(a) * 15, py + math.sin(a) * 15
    lx, ly = px + math.cos(a + 1.9) * 9, py + math.sin(a + 1.9) * 9
    rx, ry = px + math.cos(a - 1.9) * 9, py + math.sin(a - 1.9) * 9
    cv.add(f'<polygon class="acc-f" points="{n(tx)},{n(ty)} {n(lx)},{n(ly)} {n(rx)},{n(ry)}"/>')
    cv.add(f'<circle class="bubble" cx="{n(px)}" cy="{n(py)}" r="9"/>')
    cv.add(f'<text class="t-lbl t-acc" x="{n(px)}" y="{n(py + 3.5)}" text-anchor="middle">{letter}</text>')


# ================================================================ L-101 PLAN
SHORE = (("M", 12, 150), ("C", 40, 162, 140, 172, 162, 158))
RAMP = [("M", 32, 74), ("C", 32, 92, 72, 80, 72, 96), ("C", 72, 110, 38, 102, 38, 116)]


def site_plan():
    p = "sp"
    W, H = 1160, 1000
    cv = Cv(4, 4, 56, 56, 0, -12)
    A = cv.add
    A(defs(p))
    A(f'<rect class="sheet-bg" width="{W}" height="{H}"/>')

    def pat(name):
        return f' fill="url(#{p}-{name})"'

    # ---------------------------------------------------------------- zones
    A('<g id="lyr-zones">')
    cv.rect(0, 136, 200, 212, "z-deep")
    cv.rect(0, 136, 200, 212, "", pat("water"))
    cv.path([("M", 12, 150), ("C", 40, 162, 140, 172, 162, 158), ("L", 168, 172),
             ("C", 140, 187, 40, 177, 10, 165), ("Z",)], "z-sea")
    sand = [("M", 18, 128), ("L", 158, 128), ("L", 158, 140), ("L", 162, 158),
            ("C", 140, 172, 40, 162, 12, 150), ("L", 16, 138), ("Z",)]
    cv.path(sand, "z-sand")
    cv.path(sand, "", pat("sand"))
    cv.path([("M", 15, 146), ("C", 40, 158, 140, 168, 160, 154)], "ln-f", ' stroke-dasharray="2 3"')
    cv.path(list(SHORE), "ln-water")
    cv.path([("M", 10, 165), ("C", 40, 177, 140, 187, 168, 172)], "ln-f", ' stroke-dasharray="5 3"')
    cv.rect(18, 116, 158, 128, "z-timber")
    cv.rect(18, 116, 158, 128, "", pat("board"))
    lawn = [(26, 74), (176, 74), (182, 100), (182, 108), (158, 108), (158, 116), (22, 116), (20, 96)]
    cv.poly(lawn, "z-lawn")
    cv.poly(lawn, "", pat("lawn"))
    cv.rect(80, 74, 132, 80, "z-paver")
    cv.rect(80, 80, 120, 98, "z-paver")
    cv.poly([(122, 80), (177.4, 80), (181.5, 98), (182, 108), (158, 108), (158, 116), (122, 116)], "z-conc")
    cv.path(RAMP, "path-edge")
    cv.path(RAMP, "path-fill")
    plaza = [(26, 30), (176, 30), (176, 74), (26, 74)]
    cv.poly(plaza, "z-brick")
    cv.poly(plaza, "", pat("brick"))
    cv.rect(20, 0, 182, 30, "z-paver")
    cv.rect(0, -12, 200, 0, "z-town")
    cv.rect(0, -12, 200, 0, "", pat("hatch"))
    cv.line(0, -6, 200, -6, "ln-m", ' stroke-dasharray="6 5"')
    cv.line(0, -0.6, 200, -0.6, "ln-m")
    rp = [(158, 128), (186, 128), (186, 136), (190, 150), (186, 162), (174, 167), (163, 160), (157, 148), (158, 140)]
    cv.poly(rp, "z-rockp")
    cv.poly(rp, "", pat("sand"))
    wc = [(0, 0), (20, 0), (20, 30), (26, 30), (26, 74), (20, 96), (22, 116), (18, 128), (16, 138), (12, 150),
          (10, 165), (12, 182), (10, 212), (0, 212)]
    ec = [(200, 0), (182, 0), (182, 30), (176, 30), (176, 74), (182, 100), (182, 108), (186, 128), (186, 136),
          (190, 150), (192, 170), (194, 190), (194, 212), (200, 212)]
    for c in (wc, ec):
        cv.poly(c, "z-cliff")
        cv.poly(c, "", pat("rock"))
        cv.pline(c[1:-1], "ln")
    # chalk art dance circle
    cv.circle(100, 56, 9, "chalk-y", ' fill-opacity=".5"')
    star = []
    for i in range(10):
        r = 7.6 if i % 2 == 0 else 3.2
        a = math.radians(-90 + i * 36)
        star.append((100 + r * math.cos(a), 56 + r * math.sin(a)))
    cv.poly(star, "chalk-p", ' fill-opacity=".55"')
    for (u, v, ru, rv) in [(90, 50, 2.4, 1.2), (110, 63, 2.8, 1.3), (108, 47, 1.6, .9), (91, 64, 1.8, 1)]:
        cv.ellipse(u, v, ru, rv, "chalk-c", ' fill-opacity=".5"')
    cv.circle(100, 56, 9, "ln-m", ' stroke-dasharray="2 2"')
    A('</g>')

    # ---------------------------------------------------------------- built
    A('<g id="lyr-built">')
    shops = [(62, 76, "MINI MART"), (76, 90, "PHOTO BOOTH"), (110, 126, "AVATAR|BOUTIQUE"),
             (126, 140, "BINGSU"), (140, 156, "GACHA"), (156, 172, "FLOWERS")]
    for a, b, _ in shops:
        cv.rect(a, 20, b, 30, "under")
    for seg in [(20, 40), (48, 90), (110, 174)]:
        cv.line(seg[0], 30, seg[1], 30, "ln-h")
    # escalator + stair
    cv.rect(90, 30, 110, 44, "bldg-l")
    cv.rect(91, 30, 94, 42, "prop")
    cv.rect(95, 30, 98, 42, "prop")
    cv.line(92.5, 41, 92.5, 32, "ln", f' marker-end="url(#{p}-arrk)"')
    cv.line(96.5, 32, 96.5, 41, "ln", f' marker-end="url(#{p}-arrk)"')
    for y in frange(30.6, 34.8, 0.6) + frange(37.8, 42.0, 0.6):
        cv.line(99, y, 109, y, "ln-m")
    cv.rect(89, 29.5, 111, 44.5, "ln-b")
    # arcade
    cv.rect(28, 34, 60, 66, "bldg")
    cv.line(60, 46, 60, 54, "gap")
    cv.line(60, 46, 60, 54, "ln-m", ' stroke-dasharray="1.5 1.5"')
    cv.rect(60.5, 43, 61.5, 57, "led")
    cv.rect(40, 30, 48, 34, "bldg-l")
    # cafe + terrace
    cv.rect(132, 70, 172, 80, "z-timber")
    cv.rect(132, 70, 172, 80, "", pat("board"))
    cv.line(132, 80, 166, 80, "ln-h")
    cv.line(172, 70, 172, 80, "ln-h")
    cv.rect(142, 46, 170, 70, "bldg")
    cv.line(142, 52, 142, 58, "gap")
    cv.line(142, 52, 142, 58, "ln-m", ' stroke-dasharray="1.5 1.5"')
    cv.line(144, 70, 168, 70, "glass")
    # hill terrace buildings
    cv.rect(120, 2, 168, 20, "bldg")
    cv.rect(128, 20, 160, 22.5, "prop")
    cv.rect(36, 6, 52, 9, "bldg-l")
    cv.rect(174, 30, 180, 46, "bldg-l")
    for y in frange(30.6, 37.2, 0.6) + frange(39.6, 45.6, 0.6):
        cv.line(174, y, 180, y, "ln-m")
    # beach house, pier, raft, small structures
    cv.rect(158, 128, 180, 136, "z-timber")
    cv.rect(158, 128, 180, 136, "ln")
    cv.rect(158, 108, 182, 128, "bldg")
    cv.line(158, 116, 158, 120, "gap")
    cv.rect(168, 160, 172, 186, "z-timber")
    cv.rect(160, 186, 180, 198, "z-timber")
    cv.rect(168, 160, 172, 186, "", pat("board"))
    cv.rect(160, 186, 180, 198, "", pat("board"))
    cv.pline([(168, 160), (168, 186), (160, 186), (160, 198), (180, 198), (180, 186), (172, 186), (172, 160)], "ln")
    cv.circle(174, 192, 2.4, "bldg")
    cv.circle(174, 192, 1.1, "acc-f")
    cv.rect(75, 183, 81, 189, "z-timber")
    cv.rect(75, 183, 81, 189, "ln")
    cv.rect(120, 63, 127, 65.6, "bldg-l")
    cv.rect(119, 152, 122, 155, "prop")
    cv.line(119, 152, 122, 155, "ln-m")
    cv.line(122, 152, 119, 155, "ln-m")
    # sea wall with stair gaps, beach stairs and ramp
    for a, b in [(18, 46), (54, 96), (104, 158)]:
        cv.line(a, 128, b, 128, "ln-h")
    for a, b in [(46, 54), (96, 104)]:
        cv.rect(a, 128, b, 130.4, "z-paver")
        cv.rect(a, 128, b, 130.4, "ln")
        for y in frange(128.6, 130.4, 0.6):
            cv.line(a, y, b, y, "ln-m")
    cv.rect(120, 128.4, 134.4, 131, "z-paver")
    cv.rect(120, 128.4, 134.4, 131, "ln")
    cv.line(133, 129.7, 122, 129.7, "ln-m", f' marker-end="url(#{p}-arrk)"')
    # sunset steps
    cv.rect(80, 80, 120, 98, "ln")
    for y in (83, 86, 89, 92, 95):
        cv.line(82, y, 97, y, "ln")
        cv.line(103, y, 118, y, "ln")
    for y in frange(81.5, 98, 1.5):
        for a, b in [(80, 82), (97, 103), (118, 120)]:
            cv.line(a, y, b, y, "ln-f")
    for x in (82, 97, 103, 118):
        cv.line(x, 80, x, 98, "ln-m")
    # skate garden
    cv.rect(122, 80, 128, 92, "z-paver")
    cv.rect(122, 80, 128, 92, "ln")
    for y in frange(80.6, 84.8, 0.6) + frange(87.8, 92, 0.6):
        cv.line(122, y, 128, y, "ln-m")
    cv.line(125, 80, 125, 92, "ln-h")
    cv.line(128, 80, 177.4, 80, "ln")
    cv.line(128, 96, 181.3, 96, "ln-m", ' stroke-dasharray="3 2"')
    for x in (131.5, 174):
        cv.line(x, 82, x, 94, "ln-m", f' marker-end="url(#{p}-arrk)"')
    cv.rect(134, 100, 146, 100.8, "prop-d")
    cv.rect(148, 104, 158, 104.8, "prop-d")
    cv.line(134, 110, 146, 110, "ln-h")
    cv.rect(150, 108, 162, 112, "prop")
    cv.rect(168, 98, 174, 114, "prop")
    cv.line(168, 98, 168, 114, "ln-h")
    for x in (170, 172):
        cv.line(x, 98, x, 114, "ln-f")
    cv.poly([(129, 104), (132, 104), (132, 107)], "prop")
    cv.line(122, 116, 158, 116, "ln-h")
    A('</g>')

    # ---------------------------------------------------------------- props
    A('<g id="lyr-props">')
    trees = [(26, 22, 3), (62, 24, 2.6), (80, 6, 3), (112, 6, 2.6), (174, 22, 3), (176, 8, 2.6),
             (68, 40, 2.8), (132, 38, 2.8), (80, 70, 3), (120, 70, 3), (68, 66, 2.6),
             (30, 80, 3.2), (36, 88, 2.6), (28, 102, 3.2), (46, 78, 2.8), (74, 77, 2.6), (75, 90, 2.8),
             (62, 93, 2.6), (53, 99, 2.8), (30, 112, 3), (50, 114, 2.6), (78, 112, 2.6),
             (178, 88, 2.6), (180, 142, 2.8)]
    for u, v, r in trees:
        cv.circle(u, v, r, "tree")
        cv.circle(u, v, .35, "ink-f")
    cv.circle(42, 96, 5, "z-sea")
    cv.circle(42, 96, 5, "ln")
    cv.circle(42, 96, 1.4, "ln-m")
    for ang in (22.5, 67.5, 112.5, 157.5, 202.5, 337.5):
        a = math.radians(ang)
        u, v = 100 + 12.5 * math.cos(a), 56 + 12.5 * math.sin(a)
        cv.rect(u - 1.5, v - .4, u + 1.5, v + .4, "prop",
                f' transform="rotate({n(ang + 90)} {n(cv.X(u))} {n(cv.Y(v))})"')
    lamps = [(115, 56), (107.5, 69), (92.5, 69), (85, 56), (72, 34), (128, 34)]
    lamps += [(x, 127.2) for x in range(28, 157, 12)]
    for u, v in lamps:
        cv.circle(u, v, .7, "prop")
        cv.circle(u, v, .25, "ink-f")
    for a, b in [((72, 34), (85, 56)), ((128, 34), (115, 56)), ((85, 56), (92.5, 69)),
                 ((115, 56), (107.5, 69)), ((92.5, 69), (107.5, 69)), ((72, 34), (88, 31)), ((128, 34), (112, 31))]:
        cv.line(a[0], a[1], b[0], b[1], "bunting")
    for x in (34, 58, 82, 118, 142):
        cv.rect(x - 1.5, 125.6, x + 1.5, 126.4, "prop")
    umb = [(84, 136), (91, 142), (110, 136), (117, 143), (127, 137), (137, 143), (144, 136), (106, 150), (132, 151)]
    for i, (u, v) in enumerate(umb):
        cv.rect(u - 1.6, v + 1.7, u - .7, v + 3.5, "prop")
        cv.rect(u + .7, v + 1.7, u + 1.6, v + 3.5, "prop")
        cv.circle(u, v, 1.5, ("umb-y", "umb-p", "umb-c")[i % 3])
    cv.rect(54, 138, 70, 146, "ln")
    cv.line(62, 137, 62, 147, "ln-h")
    cv.rect(51, 135, 73, 149, "ln-f", ' stroke-dasharray="3 2"')
    cv.circle(34, 140, 1, "acc-f")
    for k in range(6):
        a = math.radians(k * 60 + 15)
        u, v = 34 + 3.4 * math.cos(a), 140 + 3.4 * math.sin(a)
        cv.rect(u - .9, v - .3, u + .9, v + .3, "prop-d",
                f' transform="rotate({n(k * 60 + 105)} {n(cv.X(u))} {n(cv.Y(v))})"')
    cv.circle(82, 156, 3, "ln-m", ' stroke-dasharray="2 2"')
    cv.ellipse(148, 150, 2, 1.2, "chalk-p")
    cv.circle(144, 153.5, .9, "umb-y")
    cv.circle(151, 154.5, .9, "umb-c")
    cv.circle(140, 156, .5, "umb-p")
    for x in (150, 152.2, 154.4):
        cv.circle(x, 129.4, .85, "ring-acc")
    cv.rect(152, 131.2, 157, 132.4, "prop")
    for u in (84, 116):
        cv.circle(u, 28, .7, "prop")
    cv.rect(60, 109, 63, 111, "prop")
    cv.rect(68, 111, 71, 113, "prop")
    cv.rect(30, 101.5, 36, 103, "prop")
    for (u, v, c) in [(80, 101, "chalk-y"), (116, 101, "chalk-c"), (87, 113.5, "chalk-p")]:
        cv.rect(u - 2, v - 1.5, u + 2, v + 1.5, c, ' fill-opacity=".6"')
    for (u, v, c) in [(88, 84.5, "umb-y"), (112, 87.5, "umb-p"), (86, 93.5, "umb-c"), (114, 81.5, "umb-c")]:
        cv.circle(u, v, .8, c)
    for x in frange(14, 194, 8):
        cv.circle(x, 200, .7, "acc-f")
    cv.line(10, 200, 194, 200, "ln-f", ' stroke-dasharray="1 2"')
    for (u, v) in [(136, 75), (143, 75), (157, 75), (164, 75)]:
        cv.circle(u, v, 1.6, "umb-y")
    A('</g>')

    # ---------------------------------------------------------------- grid
    A('<g id="lyr-grid">')
    for x in range(0, 201, 20):
        cv.line(x, -12, x, 212, "grid")
    for y in range(0, 201, 20):
        cv.line(0, y, 200, y, "grid")
    A('</g>')
    for i, letter in enumerate("ABCDEFGHIJ"):
        x = cv.X(10 + 20 * i)
        A(f'<circle class="bubble" cx="{n(x)}" cy="40" r="9"/><text class="t-lbl" x="{n(x)}" y="43.5" text-anchor="middle">{letter}</text>')
    for j in range(10):
        y = cv.Y(10 + 20 * j)
        A(f'<circle class="bubble" cx="38" cy="{n(y)}" r="9"/><text class="t-lbl" x="38" y="{n(y + 3.5)}" text-anchor="middle">{j + 1}</text>')

    # ---------------------------------------------------------------- circulation
    A('<g id="lyr-circ">')
    main = [(44, 15), (86, 17), (97, 26), (98.5, 36), (98, 56), (98, 90), (98, 108), (98, 122), (98, 131),
            (106, 144), (150, 150), (166, 157), (170, 172), (171, 187)]
    cv.pline(main, "circ1", f' marker-end="url(#{p}-arr)"')
    cv.path(RAMP, "circ2")
    for pts in [[(88, 56), (64, 50), (62, 50)], [(32, 74), (40, 66)], [(38, 116), (40, 122), (50, 124), (50, 131), (38, 137)],
                [(108, 56), (140, 55)], [(126, 74), (125, 80), (125, 92), (138, 104), (156, 118)],
                [(156, 122), (110, 122)], [(177, 24), (177, 46), (168, 42)], [(48, 22), (44, 28), (44, 34)]]:
        cv.pline(pts, "circ2", f' marker-end="url(#{p}-arr)"')
    A('</g>')

    # ---------------------------------------------------------------- sightlines
    A('<g id="lyr-sight">')
    for (a, b, lab, lu, lv) in [((102, 28), (102, 211), "V1", 104, 33.5),
                                ((152, 78), (173, 189), "V2", 155, 83),
                                ((44, 15), (171, 189), "V3", 50, 25)]:
        cv.line(a[0], a[1], b[0], b[1], "sight", f' marker-end="url(#{p}-arrt)"')
        cv.circle(a[0], a[1], .9, "teal-f")
        cv.text(lu, lv, lab, "t-lbl t-teal halo", "start")
    A('</g>')

    # ---------------------------------------------------------------- section cuts
    A('<g id="lyr-cuts">')
    cv.line(100, -12, 100, 212, "cut")
    cv.line(100, -12, 100, -6, "cut-h")
    cv.line(100, 206, 100, 212, "cut-h")
    section_bubble(cv, cv.X(100) + 14, cv.Y(-8), "A", 0)
    section_bubble(cv, cv.X(100) + 14, cv.Y(208), "A", 0)
    cv.line(0, 56, 200, 56, "cut")
    cv.line(0, 56, 6, 56, "cut-h")
    cv.line(194, 56, 200, 56, "cut-h")
    section_bubble(cv, cv.X(4), cv.Y(56) - 14, "B", -90)
    section_bubble(cv, cv.X(196), cv.Y(56) - 14, "B", -90)
    A('</g>')

    # ---------------------------------------------------------------- labels
    A('<g id="lyr-labels">')
    T = cv.text
    T(54, -4.2, "TOWN BACKDROP · ROAD & FACADES · NON-PLAYABLE", "t-sm halo")
    T(90, 12.5, "HILL TERRACE · L3", "t-zone halo")
    T(90, 16.6, "+9.60 · spawn · viewpoint · cinema", "t-sm halo")
    T(144, 11, "COVE CINEMA", "t-lbl")
    T(144, 15, "lobby + marquee", "t-sm")
    T(44, 8.3, "BUS STOP", "t-sm")
    for a, b, name in shops:
        parts = name.split("|")
        for k, part in enumerate(parts):
            T((a + b) / 2, 25.8 + (k - (len(parts) - 1) / 2) * 3.4, part, "t-sm")
    T(100, 24.6, "VIEWPOINT", "t-sm halo")
    T(44, 48.5, "PIXEL POP ARCADE", "t-lbl")
    T(44, 52.5, "2 floors · sheet A-301", "t-sm")
    T(44, 61, "bridge to L3 ↑ at north", "t-sm")
    T(57.6, 50, "LED 14 × 8 on facade", "t-sm", rot=-90)
    T(75, 57.5, "CHALK PLAZA · L2", "t-zone halo")
    T(75, 61.4, "+4.80 · dance circle Ø18", "t-sm halo")
    T(156, 57, "WAVE CAFÉ", "t-lbl")
    T(156, 61, "sheet A-302", "t-sm")
    T(150, 76.2, "TERRACE +4.80", "t-sm halo")
    T(123.5, 62.2, "FOOD TRUCK", "t-sm halo")
    T(177, 38, "EAST STAIR", "t-sm", rot=-90)
    T(100, 77.8, "SUNSET DECK +4.80", "t-sm halo")
    T(100, 88.8, "SUNSET STEPS", "t-zone halo")
    T(100, 92.8, "6 terraces × 0.40", "t-sm halo")
    T(100, 106.4, "SUNSET LAWN · L1", "t-zone halo")
    T(100, 110.2, "+2.40", "t-sm halo")
    T(60, 79, "PINE GARDEN", "t-zone halo")
    T(60, 82.8, "+4.80 → +2.40 · ramp ≈ 4%", "t-sm halo")
    T(42, 96.9, "FOUNTAIN", "t-sm")
    T(33, 100.5, "SWINGS", "t-sm halo")
    T(66, 108, "PICNIC", "t-sm halo")
    T(152, 88.6, "SKATE GARDEN · L1", "t-zone halo")
    T(152, 92.6, "bank 1:6.7 ↓ · ledges · rail · QP", "t-sm halo")
    T(125, 97.5, "16R", "t-sm halo")
    T(140, 114.6, "+2.40 · grind curb", "t-sm halo")
    T(76, 122.8, "PROMENADE · L1 · +2.40", "t-zone halo")
    T(170, 117.2, "BEACH HOUSE", "t-lbl")
    T(170, 121.2, "roof deck +6.60", "t-sm")
    T(169, 133, "DECK", "t-sm")
    T(98, 159.2, "SUNNY COVE BEACH", "t-big halo")
    T(74, 132.2, "+1.20 crest", "t-sm halo")
    T(127, 134, "RAMP 1:12", "t-sm halo")
    T(34, 134.6, "BONFIRE", "t-sm halo")
    T(62, 152.6, "BEACH VOLLEY 16 × 8", "t-sm halo")
    T(120.5, 151, "LIFEGUARD", "t-sm halo")
    T(146, 147.6, "INFLATABLES (PHYSICS)", "t-sm halo")
    T(82, 162, "SANDCASTLE", "t-sm halo")
    T(173, 151.6, "ROCKY POINT", "t-lbl halo")
    T(164.6, 176, "PIER +2.40", "t-sm halo", "end")
    T(158, 193.2, "LIGHTHOUSE", "t-lbl halo", "end")
    T(126, 170.8, "SWL ±0.00", "t-sm halo")
    T(50, 168.6, "WADE ZONE  ±0.00 → −0.90", "t-sm halo")
    T(44, 191.5, "SWIM ZONE  −0.90 → −3.00", "t-sm halo")
    T(78, 181.6, "FLOAT RAFT", "t-sm halo")
    T(50, 205, "BUOY LINE · SOFT BOUNDARY", "t-sm t-acc halo")
    T(110, 210.6, "↓ TURTLE ISLAND · 400 m offshore · vista on the main axis", "t-sm halo", "start")
    T(10, 104, "WEST CLIFF · BLOCKING", "t-sm halo", rot=-90)
    T(191, 104, "EAST CLIFF · BLOCKING", "t-sm halo", rot=90)
    for (u, v, letter, lu) in [(44, 15, "A", 48.4), (30, 122, "B", 34.4)]:
        cv.circle(u, v, 2.6, "acc-f")
        T(u, v + 1, letter, "t-lbl t-inv")
        T(lu, v + 1, f"SPAWN {letter}", "t-lbl t-acc halo", "start")
    A('</g>')

    cv.rect(0, -12, 200, 212, "frame")

    # ---------------------------------------------------------------- legend
    lx, ly = 884, 56
    A(f'<g transform="translate({lx} {ly})">')
    A('<rect class="frame-in" width="260" height="580"/>')
    A('<text class="t-head" x="14" y="26">LEGEND</text>')
    rows = [("z-paver", None, "Hill Terrace · pavers · L3"), ("z-brick", "brick", "Chalk Plaza · brick · L2"),
            ("z-lawn", "lawn", "Garden & lawn · L2 → L1"), ("z-conc", None, "Skate concrete · L1"),
            ("z-timber", "board", "Promenade & decks · timber"), ("z-sand", "sand", "Beach sand · +1.20 → ±0.00"),
            ("z-sea", None, "Wade zone · depth ≤ 0.90"), ("z-deep", "water", "Swim zone · depth 0.90 – 3.00"),
            ("z-cliff", "rock", "Cliff & rock · blocking"), ("bldg", None, "Building footprint"),
            ("under", None, "Shop units under the terrace")]
    y = 42
    for cls, pt, lab in rows:
        A(f'<rect class="{cls}" x="14" y="{y}" width="28" height="14"/>')
        if pt:
            A(f'<rect x="14" y="{y}" width="28" height="14" fill="url(#{p}-{pt})"/>')
        if cls not in ("bldg", "under"):
            A(f'<rect class="ln-f" x="14" y="{y}" width="28" height="14"/>')
        A(f'<text class="t-lbl" x="52" y="{y + 10.5}">{esc(lab)}</text>')
        y += 19
    y += 8
    A(f'<text class="t-head" x="14" y="{y + 6}">SYMBOLS</text>')
    y += 20
    sym = [
        (f'<circle class="tree" cx="28" cy="{{c}}" r="7"/><circle class="ink-f" cx="28" cy="{{c}}" r="1.2"/>', "Tree (pine) · canopy to scale"),
        (f'<rect class="prop" x="22" y="{{c0}}" width="12" height="3.2"/>', "Bench · seat 0.40"),
        (f'<circle class="prop" cx="28" cy="{{c}}" r="2.8"/><circle class="ink-f" cx="28" cy="{{c}}" r="1"/>', "Lamp post"),
        (f'<circle class="umb-y" cx="28" cy="{{c}}" r="6"/>', "Umbrella + 2 deck chairs"),
        (f'<circle class="acc-f" cx="28" cy="{{c}}" r="7"/><text class="t-lbl t-inv" x="28" y="{{c3}}" text-anchor="middle">A</text>', "Spawn point"),
        (f'<line class="circ1" x1="14" y1="{{c}}" x2="42" y2="{{c}}"/>', "Main loop"),
        (f'<line class="circ2" x1="14" y1="{{c}}" x2="42" y2="{{c}}"/>', "Secondary route"),
        (f'<line class="sight" x1="14" y1="{{c}}" x2="42" y2="{{c}}"/>', "Sightline V1–V3"),
        (f'<line class="cut-h" x1="14" y1="{{c}}" x2="22" y2="{{c}}"/><line class="cut" x1="22" y1="{{c}}" x2="42" y2="{{c}}"/>', "Section cut A–A, B–B"),
        (f'<line class="ln-water" x1="14" y1="{{c}}" x2="42" y2="{{c}}"/>', "Shoreline · still water ±0.00"),
    ]
    for tpl, lab in sym:
        c = y + 7
        A(tpl.replace("{c0}", n(c - 1.6)).replace("{c3}", n(c + 3.4)).replace("{c}", n(c)))
        A(f'<text class="t-lbl" x="52" y="{y + 10.5}">{esc(lab)}</text>')
        y += 18
    y += 8
    A(f'<text class="t-head" x="14" y="{y + 6}">LEVELS</text>')
    y += 22
    for lv, z, name in [("L3", "+9.60", "Hill Terrace"), ("L2", "+4.80", "Chalk Plaza, arcade, café"),
                        ("L1", "+2.40", "Lawn, skate, promenade"), ("B", "+1.20 → ±0.00", "Beach"),
                        ("SEA", "±0.00 → −3.00", "Wade, then swim")]:
        A(f'<text class="t-lbl" x="14" y="{y}">{lv}</text><text class="t-dim" x="44" y="{y}">{esc(z)}</text>'
          f'<text class="t-sm" x="124" y="{y}">{esc(name)}</text>')
        y += 15
    A('</g>')

    # compass, sun and scale bar
    cx, cy = 930, 690
    A(f'<circle class="frame-in" cx="{cx}" cy="{cy}" r="24"/>')
    A(f'<polygon class="ink-f" points="{cx},{cy - 22} {cx + 7},{cy + 8} {cx},{cy + 2} {cx - 7},{cy + 8}"/>')
    A(f'<text class="t-head" x="{cx}" y="{cy - 28}" text-anchor="middle">N</text>')
    az = math.radians(235)
    sx, sy = cx + 40 * math.sin(az), cy - 40 * math.cos(az)
    A(f'<circle class="chalk-y" cx="{n(sx)}" cy="{n(sy)}" r="5"/>')
    A(f'<line class="ln-m" x1="{n(sx + 6)}" y1="{n(sy - 4)}" x2="{n(cx - 9)}" y2="{n(cy + 6)}" marker-end="url(#{p}-arrk)"/>')
    A(f'<text class="t-sm" x="{cx - 2}" y="{cy + 46}" text-anchor="middle">sun az 235° · golden hour</text>')
    bx, by = 982, 690
    for k, (a, b) in enumerate([(0, 10), (10, 20), (20, 40)]):
        cls = "ink-f" if k % 2 == 0 else "sheet-f"
        A(f'<rect class="{cls}" x="{bx + a * 4}" y="{by}" width="{(b - a) * 4}" height="6"/>')
    A(f'<rect class="ln" x="{bx}" y="{by}" width="160" height="6"/>')
    for m in (0, 10, 20, 40):
        A(f'<text class="t-dim" x="{bx + m * 4}" y="{by - 5}" text-anchor="middle">{m}</text>')
    A(f'<text class="t-sm" x="{bx}" y="{by + 20}">metres · grid cell 20 × 20 m</text>')

    # title block
    tx, ty = 884, 750
    A(f'<g transform="translate({tx} {ty})">')
    A('<rect class="frame" width="260" height="222"/>')
    A('<text class="t-title" x="14" y="32">Sunny Cove Park</text>')
    A('<text class="t-sm" x="14" y="48">Social hangout map · concept layout</text>')
    A('<line class="ln" x1="0" y1="60" x2="260" y2="60"/>')
    fields = [("SHEET", "L-101"), ("TITLE", "Site plan"), ("SCALE", "4 px = 1 m"), ("UNITS", "m · 1 m = 100 UU"),
              ("DATUM", "±0.00 = sea level"), ("NORTH", "up · sea to south"), ("REVISION", "A · 2026-10-05"),
              ("STATUS", "Concept / blockout")]
    for i, (k, v) in enumerate(fields):
        col, row = i % 2, i // 2
        fx, fy = 14 + col * 128, 78 + row * 37
        A(f'<text class="t-sm" x="{fx}" y="{fy}">{k}</text><text class="t-lbl" x="{fx}" y="{fy + 14}">{esc(v)}</text>')
        if col == 0:
            A(f'<line class="ln-f" x1="0" y1="{fy + 23}" x2="260" y2="{fy + 23}"/>')
    A('<line class="ln-f" x1="128" y1="60" x2="128" y2="222"/>')
    A('</g>')
    return cv.svg(), W, H


# ============================================================== L-201 SECTION
def section_aa():
    p = "aa"
    W, H = 1020, 400
    cv = Cv(4, -10, 60, 270, -12, 0)
    A = cv.add
    A(defs(p))
    A(f'<rect class="sheet-bg" width="{W}" height="{H}"/>')
    title_strip(cv, 24, 30, "L-201", "SECTION A–A · MAIN AXIS X = 100 · LOOKING EAST",
                "Horizontal 4 px = 1 m · vertical 10 px = 1 m (vertical exaggeration 2.5×) · light line = beyond · dashed = hidden")

    # beyond (drawn first)
    cv.rect(2, 9.6, 20, 17.6, "beyond")
    cv.rect(20, 12.6, 22.5, 13.2, "beyond")
    cv.text(11, 14.2, "COVE CINEMA", "t-sm", extra="")
    cv.text(11, 12.4, "beyond · roof +17.60", "t-sm")
    cv.rect(46, 4.8, 70, 10.2, "beyond")
    cv.rect(52, 10.2, 64, 12.4, "beyond")
    cv.text(58, 11.0, "WAVE CAFÉ", "t-sm")
    cv.text(58, 7.6, "café beyond", "t-sm")
    cv.rect(70, 4.5, 80, 4.8, "beyond")
    cv.line(80, 4.8, 80, 5.9, "ln-m")
    cv.line(70, 5.9, 80, 5.9, "ln-m")
    cv.line(80, 4.8, 96, 2.4, "ln-b")
    cv.rect(108, 2.4, 128, 6.6, "beyond")
    cv.line(108, 7.7, 128, 7.7, "ln-m")
    for y in (108, 118, 128):
        cv.line(y, 6.6, y, 7.7, "ln-m")
    cv.text(118, 5.2, "BEACH HOUSE", "t-sm")
    cv.rect(128, 2.1, 136, 2.4, "beyond")
    for y in (130, 134):
        cv.line(y, 2.1, y, .6, "ln-m")
    cv.poly([(128, 1.2), (136, 2.2), (146, 2.0), (156, 1.6), (162, .9), (167, 0), (167, -.6), (128, -.6)], "beyond")
    cv.text(155, 1.9, "ROCKY POINT", "t-sm")
    cv.rect(160, 2.1, 198, 2.4, "beyond")
    for y in frange(162, 199, 6):
        cv.line(y, 2.1, y, -2.6, "ln-m")
    cv.poly([(189.8, 2.4), (194.2, 2.4), (193.4, 15.6), (190.6, 15.6)], "beyond")
    for z0, z1 in [(6.0, 7.6), (10.4, 12.0)]:
        cv.poly([(189.8 + (z0 - 2.4) * .06, z0), (194.2 - (z0 - 2.4) * .06, z0),
                 (194.2 - (z1 - 2.4) * .06, z1), (189.8 + (z1 - 2.4) * .06, z1)], "acc-f", ' opacity=".8"')
    cv.rect(190.4, 15.6, 193.6, 17.4, "beyond")
    cv.poly([(190, 17.4), (194, 17.4), (192, 18.6)], "beyond")
    for y in (127, 69):
        z = 2.4 if y == 127 else 4.8
        cv.line(y, z, y, z + 5, "ln-m")
        cv.circle(y, z + 5.1, .7, "prop")
    cv.line(70, 4.8, 70, 7.0, "trunk")
    cv.ellipse(70, 8.4, 3, 1.8, "tree")

    # cut ground
    top = [(-12, 9.6), (30, 9.6), (30, 4.8), (80, 4.8),
           (80, 4.4), (83, 4.4), (83, 4.0), (86, 4.0), (86, 3.6), (89, 3.6), (89, 3.2), (92, 3.2), (92, 2.8),
           (95, 2.8), (95, 2.4), (128, 2.4), (128, 1.2), (164.5, 0.0), (179.5, -0.9), (200, -3.0), (212, -3.6)]
    cv.poly([(164.5, 0), (212, 0), (212, -3.6), (200, -3.0), (179.5, -.9)], "water")
    cv.line(164.5, 0, 212, 0, "ln-water")
    cv.rect(20, 4.8, 30, 9.3, "ln-b")
    poche = top + [(212, -6), (-12, -6)]
    cv.poly(poche, "poche")
    cv.poly(poche, "", f' fill="url(#{p}-earth)"')
    cv.rect(20, 4.8, 30, 9.3, "ln-b")
    cv.text(25, 8.2, "SHOP ROW", "t-sm halo")
    cv.text(25, 7.1, "hidden", "t-sm halo")
    cv.pline(top, "ln-h")
    # escalator stair (cut)
    st = [(30, 9.6)]
    y, z = 30, 9.6
    for _ in range(4):
        y += 1.2
        st.append((y, z))
        z -= .6
        st.append((y, z))
    st.append((37.2, 7.2))
    y, z = 37.2, 7.2
    for _ in range(4):
        y += 1.2
        st.append((y, z))
        z -= .6
        st.append((y, z))
    st[-1] = (42, 4.8)
    st += [(44, 4.8), (42, 4.8), (37.2, 6.8), (34.8, 6.8), (30, 9.2)]
    cv.poly(st, "conc")
    cv.line(29, 13.2, 45, 8.4, "glass")
    cv.line(29.5, 9.6, 29.5, 13.05, "ln-m")
    cv.line(44.5, 4.8, 44.5, 8.55, "ln-m")
    cv.line(30, 9.6, 30, 10.7, "ln")
    # beach stair (cut)
    cv.poly([(128, 2.4), (130.4, 1.2), (128, 1.2)], "conc")
    cv.line(128, 3.5, 130.4, 2.1, "ln-m")
    # sunset step seat caps
    for yy, zz in [(80, 4.4), (83, 4.0), (86, 3.6), (89, 3.2), (92, 2.8)]:
        cv.rect(yy - .45, zz + .4, yy, zz + .46, "solid")
    # buoy
    cv.circle(200, .25, .8, "acc-f")
    cv.line(200, .25, 200, -3.0, "ln-f", ' stroke-dasharray="1 2"')
    # people
    for (yy, zz, s) in [(52, 4.8, False), (55, 4.8, False), (60, 4.8, False), (86.4, 4.0, True), (89.4, 3.6, True),
                        (104, 2.4, False), (121, 2.4, False), (140, .8, False), (145, .64, False)]:
        avatar(cv, yy, zz, seated=s)
    for yy in (186, 191):
        cv.add(f'<circle class="avatar" cx="{n(cv.X(yy))}" cy="{n(cv.Y(0) - 3)}" r="3.4"/>')

    # tags
    etag(cv, -8, 9.6, "+9.60 HILL TERRACE · L3")
    etag(cv, 32, 4.8, "+4.80 CHALK PLAZA · L2", below=True)
    etag(cv, 100, 2.4, "+2.40 LAWN · PROMENADE · L1")
    etag(cv, 129, 1.2, "+1.20 BEACH CREST", below=True)
    etag(cv, 204, 0, "±0.00 SWL", anchor="end")
    etag(cv, 179.5, -.9, "−0.90 WADE LIMIT", below=True)
    etag(cv, 200, -3.0, "−3.00 SWIM", below=True, anchor="end")
    etag(cv, 188, 18.6, "+18.60 LIGHTHOUSE", anchor="end")
    callout(cv, 37, 10.6, 40, 15.2, "ESCALATOR + STAIR 32R · GLASS CANOPY")
    callout(cv, 87.5, 3.8, 84, 9.2, "SUNSET STEPS · 6 × 0.40 × 3.00")
    callout(cv, 129.2, 1.9, 136, 5.8, "BEACH STAIR 8R · RAIL 1.10")
    callout(cv, 88, 4.4, 92, 6.2, "SKATE BANK beyond", cls="t-sm halo")
    cv.text(171, 2.9, "PIER DECK +2.40 beyond", "t-sm halo")
    cv.text(201.5, 1.6, "BUOY LINE", "t-sm t-acc halo")
    cv.text(212, -5.1, "→ TURTLE ISLAND", "t-sm halo", "end")
    vdim(cv, 17, 4.8, 9.6, "4.80 WALL")
    vdim(cv, 99.5, 2.4, 4.8, "2.40", ext=80)
    vdim(cv, 126, 1.2, 2.4, "1.20")

    # zone dimension string
    segs = [(0, 30, "HILL TERRACE"), (30, 74, "CHALK PLAZA"), (74, 98, "SUNSET STEPS"), (98, 116, "LAWN"),
            (116, 128, "PROMENADE"), (128, 164.5, "BEACH"), (164.5, 179.5, "WADE"), (179.5, 200, "SWIM")]
    for a, b, name in segs:
        hdim(cv, a, b, -7.2, f"{b - a:.1f}", ext=-6)
        cv.text((a + b) / 2, -9.0, name, "t-sm")
    hdim(cv, 0, 200, -10.6, "200.0 PLAYABLE · Y 0 → BUOY LINE", ext=-9.6)
    cv.rect(-12, 20, 212, -12, "frame")
    return cv.svg(), W, H


# ============================================================== L-202 SECTION
def section_bb():
    p = "bb"
    W, H = 1100, 340
    cv = Cv(5, -10, 50, 266, 0, 0)
    A = cv.add
    A(defs(p))
    A(f'<rect class="sheet-bg" width="{W}" height="{H}"/>')
    title_strip(cv, 24, 30, "L-202", "SECTION B–B · ACROSS THE PLAZA Y = 56 · LOOKING NORTH",
                "Horizontal 5 px = 1 m · vertical 10 px = 1 m (vertical exaggeration 2×) · light line = beyond (retaining wall, shops, cinema)")
    # beyond: retaining wall, shops, escalator, terrace, cinema
    cv.rect(26, 4.8, 176, 9.6, "beyond")
    for a, b in [(62, 76), (76, 90), (110, 126), (126, 140)]:
        m = (a + b) / 2
        cv.rect(m - 1.5, 4.8, m + 1.5, 8.0, "prop")
        cv.poly([(a + .8, 8.4), (b - .8, 8.4), (b - .8, 7.9), (a + .8, 7.9)], "umb-p", ' opacity=".8"')
    cv.rect(120, 9.6, 168, 17.6, "beyond")
    cv.rect(128, 12, 160, 13.2, "prop")
    cv.text(144, 15.2, "COVE CINEMA · L3 beyond", "t-sm")
    cv.line(20, 10.7, 182, 10.7, "ln-m")
    for x in frange(20, 183, 6):
        cv.line(x, 9.6, x, 10.7, "ln-f")
    cv.rect(90, 4.8, 110, 13.1, "beyond")
    for x in (95, 100, 105):
        cv.line(x, 4.8, x, 13.1, "ln-f")
    cv.path([("M", 90, 13.1), ("Q", 100, 14.6, 110, 13.1)], "glass")
    cv.text(100, 11.6, "ESCALATOR", "t-sm halo")
    cv.rect(174, 4.8, 180, 9.6, "beyond")
    cv.line(174, 9.6, 180, 4.8, "ln-m")
    for (x, z) in [(68, 4.8), (132, 4.8)]:
        cv.line(x, z, x, z + 2.2, "trunk")
        cv.ellipse(x, z + 3.8, 2.8, 2.0, "tree")
    for x in (64, 136):
        cv.line(x, 9.6, x, 11.6, "trunk")
        cv.ellipse(x, 13, 2.4, 1.6, "tree")
    # bunting across
    cv.path([("M", 76, 9.8), ("Q", 92, 7.6, 100, 8.6), ("Q", 108, 7.6, 124, 9.8)], "bunting")
    # ground cut
    ground = [(0, 16), (6, 15.4), (12, 14), (18, 11.5), (22, 8.5), (26, 6), (26, 4.8), (176, 4.8), (180, 7),
              (186, 10), (192, 12.5), (200, 13.5)]
    poche = ground + [(200, 1), (0, 1)]
    cv.poly(poche, "poche")
    cv.poly(poche, "", f' fill="url(#{p}-earth)"')
    cv.pline(ground, "ln-h")
    cv.rect(91, 4.8, 109, 4.92, "chalk-y")
    # arcade (cut) - interior back wall hides what lies beyond
    cv.rect(28, 4.8, 60, 15.2, "sheet-f")
    cv.rect(142, 4.8, 170, 10.8, "sheet-f")
    for x0, x1 in [(28, 28.4), (59.6, 60)]:
        cv.rect(x0, 4.8, x1, 15.2, "solid")
    cv.rect(28, 9.3, 60, 9.6, "solid")
    cv.rect(28, 14.1, 60, 14.4, "solid")
    cv.rect(36, 14.4, 52, 17.2, "beyond")
    cv.text(44, 15.5, "PIXEL POP", "t-sm")
    cv.rect(42, 4.8, 50, 14.1, "ln-b")
    cv.line(42, 4.8, 50, 9.3, "ln-f")
    cv.line(42, 9.6, 50, 14.1, "ln-f")
    for x0, x1, z1 in [(29, 31.5, 6.3), (33, 36, 5.7), (52, 55, 5.9), (55.5, 58.5, 6.4)]:
        cv.rect(x0, 4.8, x1, z1, "prop")
    for x0, x1 in [(30, 33), (34, 37), (52.5, 56)]:
        cv.rect(x0, 9.6, x1, 11.6, "prop")
    cv.rect(60, 8.6, 60.6, 16.6, "led")
    cv.text(36, 7.9, "GF +4.80 · games floor", "t-sm halo", "start")
    cv.text(36, 12.6, "UF +9.60 · arena · VR · lounge", "t-sm halo", "start")
    # cafe (cut)
    for x0, x1 in [(142, 142.4), (169.6, 170)]:
        cv.rect(x0, 4.8, x1, 10.8, "solid")
    cv.rect(142, 9.9, 170, 10.2, "solid")
    cv.rect(148, 10.8, 164, 12.4, "beyond")
    cv.text(156, 11.3, "WAVE CAFÉ", "t-sm")
    cv.rect(148, 4.8, 164, 5.9, "prop")
    for x in (150, 156, 162):
        cv.line(x, 9.9, x, 8.8, "ln-m")
        cv.circle(x, 8.6, .4, "chalk-y")
    cv.text(156, 7.2, "counter beyond", "t-sm halo")
    # plaza furniture + people
    for x in (87.5, 112.5):
        cv.rect(x - 1.5, 4.8, x + 1.5, 5.25, "prop")
    for x in (76, 124):
        cv.line(x, 4.8, x, 9.8, "ln")
        cv.circle(x, 9.9, .6, "prop")
    for x in (94, 98, 101, 105, 118, 70, 150, 160):
        avatar(cv, x, 4.8)
    # tags + dims
    etag(cv, 64, 4.8, "+4.80 PLAZA", below=True)
    etag(cv, 112, 9.6, "+9.60 HILL TERRACE beyond")
    etag(cv, 60.8, 16.6, "+16.60 TOP OF LED")
    etag(cv, 28.5, 14.4, "+14.40 ROOF", anchor="end")
    etag(cv, 166, 10.2, "+10.20 CAFÉ ROOF", anchor="end")
    hdim(cv, 28, 60, 19.0, "32.00 ARCADE", ext=17.2)
    hdim(cv, 60, 142, 19.0, "82.00 OPEN PLAZA", ext=17.2)
    hdim(cv, 142, 170, 19.0, "28.00 CAFÉ", ext=12.4)
    hdim(cv, 91, 109, 3.6, "Ø18.00 DANCE CIRCLE")
    vdim(cv, 39.6, 4.8, 9.3, "4.50 CLEAR")
    vdim(cv, 39.6, 9.6, 14.1, "4.50 CLEAR")
    vdim(cv, 63, 8.6, 16.6, "LED 8.00", side=1)
    vdim(cv, 172.4, 4.8, 10.2, "5.40", side=1)
    cv.rect(0, 20, 200, 1, "frame")
    return cv.svg(), W, H


# ============================================================== A-301 ARCADE
def arcade_plans():
    p = "ar"
    W, H = 800, 470
    root = Cv(1, 1, 0, 0)
    root.add(defs(p))
    root.add(f'<rect class="sheet-bg" width="{W}" height="{H}"/>')
    title_strip(root, 24, 26, "A-301", "PIXEL POP ARCADE · FLOOR PLANS",
                "10 px = 1 m · 32 × 32 m · world X 28–60, Y 34–66 · entrance faces the plaza (east)")
    out = [root.svg()]

    def plan(ox, oy, upper):
        cv = Cv(10, 10, ox, oy, 0, 0)
        cv.rect(0, 0, 32, 32, "wall")
        cv.rect(14, 10, 22, 20, "ln-h")
        for y in frange(13.6, 18.6, .6):
            cv.line(14.4, y, 17.8, y, "ln-m")
            cv.line(18.2, y, 21.6, y, "ln-m")
        cv.line(18, 10.4, 18, 19.6, "ln")
        cv.line(16.1, 18.2, 16.1, 12.4, "ln", f' marker-end="url(#{p}-arrk)"')
        cv.rect(22.6, 14, 25, 17, "prop")
        cv.line(22.6, 14, 25, 17, "ln-f")
        cv.line(25, 14, 22.6, 17, "ln-f")
        cv.text(23.8, 18.6, "LIFT", "t-sm")
        cv.text(18, 21.6, "CORE · 2 × 16R", "t-sm")
        if not upper:
            cv.line(32, 12, 32, 20, "gap")
            cv.line(32, 12, 32, 20, "glass")
            cv.rect(24, 2, 31, 6, "prop")
            cv.text(27.5, 3.9, "TOKENS", "t-sm")
            cv.text(27.5, 5.3, "PRIZES", "t-sm")
            for i in range(6):
                cv.rect(1, 1.5 + i * 2.4, 4, 3.5 + i * 2.4, "prop")
            cv.text(5.4, 9, "RACING ×6", "t-sm", rot=-90)
            for yy in (3, 8):
                cv.rect(8, yy, 12, yy + 2.4, "prop")
                cv.line(10, yy, 10, yy + 2.4, "ln-f")
            cv.text(10, 13.4, "AIR HOCKEY ×2", "t-sm")
            for i in range(4):
                cv.rect(14 + i * 2, .6, 15.6 + i * 2, 4, "prop")
            cv.text(18, 6, "HOOPS ×4", "t-sm")
            cv.rect(3, 18, 13, 30, "z-paver")
            cv.rect(3, 18, 13, 30, "ln")
            for (u, v) in [(4.5, 20), (8.5, 20), (4.5, 25), (8.5, 25)]:
                cv.rect(u, v, u + 3.2, v + 3.2, ("umb-y", "umb-p", "umb-c", "umb-y")[int(u + v) % 4])
            cv.rect(2.4, 17.4, 13.6, 30.6, "ln-b")
            cv.text(8, 29.4, "BEAT STAGE +0.30", "t-sm halo")
            for i in range(6):
                cv.rect(14 + i * 2, 24, 15.8 + i * 2, 25.8, "prop")
                cv.rect(14 + i * 2, 28.4, 15.8 + i * 2, 30.2, "prop")
            cv.text(20, 27.6, "CLAW ALLEY ×12", "t-sm")
            for yy in (23, 27.2):
                cv.rect(27.5, yy, 31.5, yy + 3.8, "prop")
            cv.text(26.9, 27, "PHOTO STICKER ×2", "t-sm", rot=-90)
            cv.text(28, 16.6, "FOYER", "t-lbl")
            cv.text(28, 18.4, "FFL +4.80", "t-sm")
            cv.line(36, 16, 32.6, 16, "ln-h", f' marker-end="url(#{p}-arrk)"')
            cv.text(37.6, 16, "ENTRY FROM PLAZA · 8.00", "t-sm", rot=-90)
            hdim(cv, 0, 32, -1.6, "32.00", ext=0)
            vdim(cv, -1.6, 0, 32, "32.00", ext=0)
            cv.text(16, 35, "GROUND FLOOR +4.80", "t-head")
        else:
            cv.line(12, 0, 20, 0, "gap")
            cv.rect(12, -4, 20, 0, "bldg-l")
            cv.line(12, -4, 12, 0, "ln-h")
            cv.line(20, -4, 20, 0, "ln-h")
            cv.text(21, -1.6, "BRIDGE → HILL TERRACE +9.60", "t-sm", "start")
            cv.line(32, 8, 32, 26, "gap")
            cv.line(32, 8, 32, 26, "glass")
            cv.rect(32.3, 9, 33, 23, "led")
            cv.text(34.4, 16, "LED SCREEN · exterior", "t-sm", rot=-90)
            for (u, v) in [(4, 3.5), (9, 3.5), (4, 8.5), (9, 8.5)]:
                cv.circle(u, v, 1.5, "prop")
                cv.circle(u, v, .6, "umb-c")
            cv.text(6.5, 12.6, "VR PODS ×4", "t-sm")
            for yy in (3, 6.5, 10):
                cv.rect(24, yy, 31, yy + 2, "prop")
            cv.text(27.5, 2.3, "MUSIC CABINETS", "t-sm")
            cv.rect(2, 16, 13, 30, "z-paver")
            cv.rect(2, 16, 13, 30, "ln-b")
            cv.circle(7.5, 23, 4, "ln-m", ' stroke-dasharray="2 2"')
            cv.text(7.5, 23.6, "PARTY ARENA", "t-sm halo")
            cv.text(7.5, 25.2, "11 × 14", "t-sm halo")
            cv.rect(14.5, 22, 21.5, 23.6, "prop")
            cv.text(18, 25, "VENDING", "t-sm")
            cv.rect(28.4, 19, 31.2, 30, "prop")
            for (u, v) in [(25, 21.5), (25, 25), (25, 28.5)]:
                cv.rect(u - .9, v - .9, u + .9, v + .9, "prop")
            cv.text(24.6, 31, "LOUNGE · view to plaza", "t-sm")
            cv.text(16, 29.4, "FFL +9.60", "t-sm")
            cv.text(16, 35, "UPPER FLOOR +9.60", "t-head")
        return cv.svg()

    out.append('<g transform="translate(770 34)"><polygon class="ink-f" points="0,-10 5,4 0,1 -5,4"/>'
               '<text class="t-sm" x="0" y="-13" text-anchor="middle">N</text></g>')
    out.append(plan(40, 80, False))
    out.append(plan(430, 80, True))
    return "\n".join(out), W, H


# ============================================================== A-302 CAFE
def cafe_plan():
    p = "cf"
    W, H = 620, 590
    root = Cv(1, 1, 0, 0)
    root.add(defs(p))
    root.add(f'<rect class="sheet-bg" width="{W}" height="{H}"/>')
    title_strip(root, 24, 26, "A-302", "WAVE CAFÉ · PLAN + TERRACE",
                "12 px = 1 m · café 28 × 24 m, terrace 40 × 10 m · world X 132–172, Y 46–80")
    cv = Cv(12, 12, 60, 76, 0, 0)
    cv.add(root.svg())
    cv.rect(0, 0, 10, 24, "z-brick")
    cv.rect(0, 0, 10, 24, "", f' fill="url(#{p}-brick)"')
    cv.text(5, 12.4, "PLAZA", "t-lbl halo", rot=-90)
    cv.rect(0, 24, 40, 34, "z-timber")
    cv.rect(0, 24, 40, 34, "", f' fill="url(#{p}-board)"')
    cv.line(0, 34, 34, 34, "ln-h")
    cv.line(40, 24, 40, 34, "ln-h")
    cv.text(37, 35.5, "open to bank top", "t-sm", "middle")
    cv.rect(10, 0, 38, 24, "wall")
    cv.line(10, 6, 10, 12, "gap")
    cv.line(10, 6, 10, 12, "glass")
    cv.line(12, 24, 36, 24, "gap")
    cv.line(12, 24, 36, 24, "glass")
    cv.line(4, 9, 9.4, 9, "ln-h", f' marker-end="url(#{p}-arrk)"')
    cv.text(4.6, 7.8, "ENTRY 6.00", "t-sm halo", "start")
    cv.rect(14, 1.2, 30, 3.4, "prop")
    cv.rect(28, 3.4, 30, 8, "prop")
    cv.rect(16, 3.4, 22, 4.4, "umb-y")
    cv.text(21, 2.7, "COUNTER · ESPRESSO BAR", "t-sm")
    cv.rect(30.5, .4, 37.6, 9, "conc")
    cv.rect(30.5, .4, 37.6, 9, "", f' fill="url(#{p}-hatch)"')
    cv.text(34, 4.6, "KITCHEN", "t-sm halo")
    cv.text(34, 6, "back of house", "t-sm halo")
    for (u, v) in [(14, 8.5), (18.5, 8.5), (23, 8.5), (18.5, 12.5), (23, 12.5), (27.5, 12.5),
                   (18.5, 16.5), (23, 16.5), (27.5, 16.5)]:
        cv.circle(u, v, .6, "prop")
        cv.circle(u - 1, v, .3, "prop-d")
        cv.circle(u + 1, v, .3, "prop-d")
    for v in (11, 14, 17, 20):
        cv.rect(35.4, v, 37.6, v + 2.4, "umb-c", ' opacity=".7"')
        cv.rect(33.6, v + .5, 35, v + 1.9, "prop")
    cv.text(32.6, 16.4, "BOOTHS ×4", "t-sm", rot=-90)
    cv.rect(13, 22.4, 33, 23.1, "prop")
    for u in frange(14, 33, 2):
        cv.circle(u, 21.8, .3, "prop-d")
    cv.text(23, 21.2, "WINDOW BAR · SEA VIEW", "t-sm")
    cv.rect(10.6, 14, 16.4, 22, "ln-b")
    cv.rect(10.4, 13.6, 11, 22.8, "prop-d")
    for (u, v) in [(13, 15.6), (15, 18), (13, 20.4)]:
        cv.circle(u, v, .8, "umb-p", ' opacity=".8"')
    cv.text(13.6, 13.2, "BOOK NOOK", "t-sm")
    for (u, v) in [(4, 28), (10, 28.5), (16, 28), (22, 28.5), (28, 28), (34, 28.5)]:
        cv.circle(u, v, 1.6, "umb-y")
        cv.circle(u, v, .3, "ink-f")
    cv.rect(2, 32.6, 32, 33.6, "z-lawn")
    cv.rect(2, 32.6, 32, 33.6, "ln-m")
    cv.text(17, 32, "PLANTER BENCH · glass rail 1.10", "t-sm halo")
    cv.line(30, 34, 36, 40, "sight", f' marker-end="url(#{p}-arrt)"')
    cv.text(28, 40.2, "V2 → LIGHTHOUSE", "t-sm t-teal")
    cv.text(24, 36.8, "SKATE GARDEN BANK BELOW ↓", "t-sm")
    cv.text(24, 18.6, "FFL +4.80", "t-sm")
    cv.text(20, 25.9, "TERRACE +4.80 · cantilevered over the bank", "t-sm halo")
    hdim(cv, 10, 38, -1.6, "28.00", ext=0)
    hdim(cv, 0, 40, 38.4, "40.00 TERRACE", ext=34)
    vdim(cv, 39.6, 0, 24, "24.00", ext=38, side=1)
    vdim(cv, -1.6, 24, 34, "10.00", ext=0)
    cv.add(f'<g transform="translate({n(cv.X(2))} {n(cv.Y(2))})"><polygon class="ink-f" points="0,-9 4,3 0,0 -4,3"/>'
           f'<text class="t-sm" x="0" y="-11" text-anchor="middle">N</text></g>')
    return cv.svg(), W, H


# ============================================================== D-401 DETAILS
def details():
    p = "dt"
    W, H = 1100, 720
    root = Cv(1, 1, 0, 0)
    root.add(defs(p))
    root.add(f'<rect class="sheet-bg" width="{W}" height="{H}"/>')
    title_strip(root, 24, 26, "D-401", "STANDARD DETAILS",
                "D1–D2 at 48 px = 1 m · D3 at 40 px = 1 m · D4 at 24 px = 1 m · avatar silhouettes are 1.30 m")
    out = [root.svg()]
    panels = [(20, 60), (560, 60), (20, 390), (560, 390)]
    for (x, y) in panels:
        out.append(f'<rect class="frame-in" x="{x}" y="{y}" width="520" height="310"/>')

    def head(cv, x, y, no, title, sub):
        cv.add(f'<circle class="bubble" cx="{x + 22}" cy="{y + 24}" r="12"/>'
               f'<text class="t-lbl" x="{x + 22}" y="{y + 27.5}" text-anchor="middle">{no}</text>'
               f'<text class="t-head" x="{x + 42}" y="{y + 24}">{esc(title)}</text>'
               f'<text class="t-sm" x="{x + 42}" y="{y + 37}">{esc(sub)}</text>')

    # D1 sunset steps
    x, y = panels[0]
    cv = Cv(48, -48, x + 60, y + 225, 0, 0)
    head(cv, x, y, "D1", "SUNSET STEPS · SECTION", "terrace seating facing the sea · e.g. +4.40 / +4.00 / +3.60")
    pc = [(0, .8), (1.5, .8), (1.5, .4), (4.5, .4), (4.5, 0), (8.5, 0), (8.5, -.6), (0, -.6)]
    cv.poly(pc, "poche")
    cv.poly(pc, "", f' fill="url(#{p}-earth)"')
    cv.pline(pc[:6], "ln-h")
    cv.pline([(0, .8), (1.5, .8), (1.5, .6), (3, .6), (3, .4), (4.5, .4), (4.5, .2), (6, .2), (6, 0), (8.5, 0)], "ln-b")
    for (a, z) in [(1.5, .8), (4.5, .4)]:
        cv.rect(a - .45, z, a, z + .06, "z-timber")
        cv.rect(a - .45, z, a, z + .06, "ln")
    avatar(cv, 1.25, .86, seated=True)
    avatar(cv, 3.0, .4)
    avatar(cv, 6.6, 0)
    cv.ellipse(7.6, .18, .45, .18, "umb-p")
    vdim(cv, 1.75, .4, .8, "0.40", side=1)
    vdim(cv, 4.75, 0, .4, "0.40", side=1)
    hdim(cv, 1.5, 4.5, -.9, "3.00 TERRACE", ext=-.6)
    hdim(cv, 1.5, 3.6, 1.95, "2.10 LOUNGE", ext=.4)
    hdim(cv, 3.6, 4.5, 1.95, "0.90 SEAT", ext=.4)
    vdim(cv, 2.55, .4, 1.7, "1.30", side=-1)
    callout(cv, 5.3, .2, 6.0, 1.15, "AISLE beyond · 0.20 risers", cls="t-sm halo")
    callout(cv, 1.1, .84, -.9, 1.3, "TIMBER SEAT CAP 0.45", "start", cls="t-sm halo")
    cv.text(8.4, -1.45, "SEA →", "t-lbl", "end")
    cv.text(-.9, -1.45, "Riser 0.40 < max step 0.45: terraces are walkable without the aisle.", "t-sm", "start")
    out.append(cv.svg())

    # D2 sea wall + beach stair
    x, y = panels[1]
    cv = Cv(48, -48, x + 80, y + 262, 0, .8)
    head(cv, x, y, "D2", "SEA WALL + BEACH STAIR · SECTION", "promenade +2.40 to beach +1.20 · 3 stairs + 1 ramp along the wall")
    cv.poly([(4.1, 1.2), (8.4, 1.12), (8.4, .9), (2.0, .9)], "z-sand")
    cv.poly([(4.1, 1.2), (8.4, 1.12), (8.4, .9), (2.0, .9)], "", f' fill="url(#{p}-sand)"')
    cv.line(4.1, 1.2, 8.4, 1.12, "ln")
    earth = [(-1, 2.25), (1.6, 2.25), (1.6, .9), (-1, .9)]
    cv.poly(earth, "poche")
    cv.poly(earth, "", f' fill="url(#{p}-earth)"')
    cv.rect(1.6, .9, 2.0, 2.25, "conc")
    cv.rect(-1, 2.25, 2.0, 2.4, "z-timber")
    cv.rect(-1, 2.25, 2.0, 2.4, "ln")
    st = [(2.0, 2.4)]
    z = 2.4
    for k in range(8):
        z -= .15
        st.append((2.0 + .3 * k, z))
        if k < 7:
            st.append((2.0 + .3 * (k + 1), z))
    st += [(4.1, .9), (2.0, .9)]
    cv.poly(st, "conc")
    cv.line(1.92, 2.4, 1.92, 3.5, "ln-b")
    cv.line(1.8, 3.5, 2.04, 3.5, "ln-b")
    cv.line(2.0, 3.3, 4.1, 2.1, "ln")
    cv.line(2.15, 3.21, 2.15, 2.25, "ln-m")
    cv.line(3.95, 2.18, 3.95, 1.35, "ln-m")
    for k in range(3):
        cv.circle(6.4, 1.32 + k * .26, .14, "ring-acc")
    avatar(cv, -.3, 2.4)
    avatar(cv, 5.3, 1.17)
    vdim(cv, 4.6, 1.2, 2.4, "8R × 0.150 = 1.20", ext=2.0, side=1)
    hdim(cv, 2.0, 4.1, .55, "7T × 0.300 = 2.10", ext=.9)
    vdim(cv, 1.5, 2.4, 3.5, "1.10 RAIL")
    callout(cv, 3.1, 2.68, 3.6, 3.4, "HANDRAIL 0.90 over nosing", cls="t-sm halo")
    callout(cv, 6.4, 1.7, 7.0, 2.4, "LIFEBUOY STACK (ref 4)", cls="t-sm halo")
    etag(cv, -.8, 2.4, "+2.40 PROMENADE", below=True)
    etag(cv, 7.6, 1.13, "+1.20 BEACH")
    cv.text(1.1, 1.6, "SEA WALL", "t-sm halo", rot=-90)
    out.append(cv.svg())

    # D3 skate set
    x, y = panels[2]
    cv = Cv(40, -40, x + 24, y + 210, 0, 0)
    head(cv, x, y, "D3", "SKATE GARDEN SET · ELEVATION", "grindables need an ollie: set CanStepUpOn = No on rails and ledges")
    cv.rect(-.3, -.5, 12, 0, "poche")
    cv.rect(-.3, -.5, 12, 0, "", f' fill="url(#{p}-earth)"')
    cv.line(-.3, 0, 12, 0, "ln-h")
    cv.line(-.3, .45, 12, .45, "ln-b")
    cv.line(-.3, .9, 12, .9, "sight")
    cv.text(-.2, .52, "MAX STEP 0.45", "t-sm halo", "start")
    cv.text(-.2, .97, "JUMP APEX 0.90 (assumed)", "t-sm t-teal halo", "start")
    cv.rect(.2, 0, 1.6, .15, "conc")
    cv.rect(2.2, 0, 4.8, .3, "conc")
    cv.rect(5.4, 0, 7.8, .5, "conc")
    cv.rect(5.4, .47, 7.8, .52, "solid")
    for xx in (8.6, 10.4):
        cv.line(xx, 0, xx, .38, "ln")
    cv.rect(8.3, .38, 10.7, .42, "solid")
    avatar(cv, 11.6, 0)
    vdim(cv, 1.8, 0, .15, "0.15", side=1)
    vdim(cv, 5.0, 0, .3, "0.30", side=1)
    vdim(cv, 8.0, 0, .52, "0.50", side=1)
    vdim(cv, 10.9, 0, .42, "0.40", side=1)
    for (a, b, t1, t2) in [(.2, 1.6, "GRIND CURB", "walk-on"), (2.2, 4.8, "MANUAL PAD", "walk-on"),
                           (5.4, 7.8, "LEDGE + STEEL COPING", "ollie-on"), (8.3, 10.7, "FLAT RAIL Ø50", "ollie-on")]:
        cv.text((a + b) / 2, -.85, t1, "t-lbl")
        cv.text((a + b) / 2, -1.15, t2 + " · length 8–12 m", "t-sm")
    cv.text(-.2, -1.75, "White paver curbs along the promenade edge copy ref 1. Quarter pipe 1.50 high on the east edge.", "t-sm", "start")
    out.append(cv.svg())

    # D4 shop unit
    x, y = panels[3]
    cv = Cv(24, -24, x + 60, y + 258, 0, 4.8)
    head(cv, x, y, "D4", "SHOP UNIT UNDER THE TERRACE · SECTION", "6 units built into the brick retaining wall · plaza +4.80, terrace +9.60")
    back = [(-2, 4.2), (16, 4.2), (16, 4.8), (0, 4.8), (0, 9.6), (-2, 9.6)]
    cv.poly(back, "poche")
    cv.poly(back, "", f' fill="url(#{p}-earth)"')
    cv.rect(-2, 9.3, 10.2, 9.6, "solid")
    cv.rect(-2, 9.6, 10.2, 9.7, "z-paver")
    cv.line(10.05, 9.6, 10.05, 10.7, "ln")
    cv.line(9.6, 10.7, 10.3, 10.7, "ln-h")
    cv.line(0, 4.8, 16, 4.8, "ln-h")
    cv.line(10, 8.0, 10, 9.3, "glass")
    cv.line(10, 4.8, 10, 8.0, "ln-b")
    cv.rect(9.8, 8.4, 10.2, 9.3, "solid")
    cv.poly([(10.2, 8.4), (12.6, 8.0), (12.6, 7.85), (10.2, 8.2)], "umb-p")
    cv.path([("M", 10.05, 10.6), ("Q", 13, 9.2, 16, 10.0)], "bunting")
    cv.rect(2, 4.8, 3.2, 5.9, "prop")
    cv.rect(.1, 4.8, .6, 7.2, "prop")
    for u in (3, 6):
        cv.line(u, 9.3, u, 8.9, "ln-m")
        cv.circle(u, 8.8, .12, "chalk-y")
    avatar(cv, 5.2, 4.8)
    avatar(cv, 12.6, 4.8)
    cv.line(5.2, 5.9, 2.0, 7.1, "sight")
    cv.rect(1.6, 6.95, 2.2, 7.3, "cam")
    cv.text(1.2, 7.6, "CAMERA BOOM 3.50", "t-sm t-teal halo", "start")
    hdim(cv, 0, 10, 4.45, "10.00 UNIT DEPTH")
    vdim(cv, 7.6, 4.8, 9.3, "4.50 CLEAR")
    vdim(cv, 9.4, 4.8, 8.0, "3.20 DOOR")
    vdim(cv, 11.0, 9.6, 10.7, "1.10", side=1)
    hdim(cv, 10.2, 12.6, 7.3, "2.40 AWNING")
    etag(cv, 13.2, 4.8, "+4.80 PLAZA · FFL")
    etag(cv, 1.0, 9.7, "+9.60 HILL TERRACE")
    cv.text(-2, 3.75, "Doors 3.00 × 3.20 min · interiors 4.50 clear so the third-person camera never clips.", "t-sm", "start")

    out.append(cv.svg())
    return "\n".join(out), W, H


# ===================================================================== export
def wrap(body, w, h, label, standalone=False):
    style = ""
    if standalone:
        tokens = dict(LIGHT, **FONTS)
        css = re.sub(r"var\(--([\w-]+)\)", lambda m: tokens[m.group(1)], SVG_CSS)
        style = f"<style>@import url('{FONT_URL}');{css}</style>"
    xmlns = ' xmlns="http://www.w3.org/2000/svg"'
    size = f' width="{w}" height="{h}"' if standalone else ""
    return (f'<svg{xmlns}{size} viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}">'
            f'{style}{body}</svg>')


# ======================================================================= page
def css_tokens(tokens, indent="  "):
    return "\n".join(f"{indent}--{k}: {v};" for k, v in tokens.items())


PAGE_CSS = """
/* Layout: a drawing set - title-block header, then full-width sheets in sheet order, each followed by its notes */
:root {
%LIGHT%
%FONTS%
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
%DARK%
    color-scheme: dark;
  }
}
:root[data-theme="dark"] {
%DARK%
  color-scheme: dark;
}
* { box-sizing: border-box; }
body { background: var(--paper); color: var(--ink); font: 400 16px/1.55 var(--f-body); }
.wrap { max-width: 1240px; margin: 0 auto; padding-inline: clamp(16px, 3vw, 40px); padding-block: 36px 72px; }
a { color: inherit; }
a:focus-visible, input:focus-visible + span { outline: 2px solid var(--accent); outline-offset: 2px; }
.eyebrow { font: 600 13px/1.3 var(--f-cond); letter-spacing: .16em; text-transform: uppercase; color: var(--ink-2); margin: 0 0 10px; }
h1 { font: 800 clamp(44px, 8vw, 92px)/.92 var(--f-display); letter-spacing: -.025em; margin: 0; text-wrap: balance; }
h1 .wave { color: var(--teal); }
.lede { max-width: 66ch; font-size: 18px; margin: 18px 0 0; color: var(--ink); }
.tblock { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); border: 1.5px solid var(--ink); margin: 28px 0 0; background: var(--sheet); }
.tblock div { padding: 10px 14px 12px; border-right: 1px solid var(--rule); border-bottom: 1px solid var(--rule); min-width: 0; }
.tblock dt { font: 600 11px var(--f-cond); letter-spacing: .14em; text-transform: uppercase; color: var(--ink-2); }
.tblock dd { margin: 2px 0 0; font: 600 18px/1.25 var(--f-cond); font-variant-numeric: tabular-nums; }
h2 { font: 700 clamp(24px, 3.4vw, 32px)/1.1 var(--f-display); margin: 0; letter-spacing: -.01em; text-wrap: balance; }
h3 { font: 700 15px var(--f-cond); letter-spacing: .12em; text-transform: uppercase; margin: 0 0 8px; color: var(--ink); }
.block { margin-top: 64px; }
.block-head { display: flex; align-items: baseline; gap: 14px; flex-wrap: wrap; border-bottom: 1.5px solid var(--ink); padding-bottom: 10px; }
.sheet-no { font: 700 14px/1 var(--f-cond); letter-spacing: .12em; background: var(--ink); color: var(--sheet); padding: 5px 9px; }
.scale { margin-left: auto; font: 500 14px var(--f-cond); letter-spacing: .04em; color: var(--ink-2); }
.index { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 28px; padding: 0; list-style: none; }
.index a { display: inline-flex; gap: 8px; align-items: baseline; text-decoration: none; border: 1px solid var(--rule); background: var(--sheet); padding: 6px 12px; font: 600 14px var(--f-cond); letter-spacing: .04em; }
.index a b { color: var(--accent); font-weight: 700; letter-spacing: .1em; }
.index a:hover { border-color: var(--ink); }
.pillars { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 0; margin: 20px 0 0; border-top: 1px solid var(--rule); }
.pillars div { padding: 16px 20px 18px 0; border-bottom: 1px solid var(--rule); min-width: 0; }
.pillars dt { font: 700 17px/1.25 var(--f-cond); letter-spacing: .02em; }
.pillars dd { margin: 6px 0 0; color: var(--ink-2); font-size: 15px; max-width: 46ch; }
.refs { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; margin-top: 20px; }
.ref { background: var(--sheet); border: 1px solid var(--rule); padding: 16px 18px; min-width: 0; }
.ref .tag { font: 700 12px var(--f-cond); letter-spacing: .14em; text-transform: uppercase; color: var(--accent); }
.ref h4 { font: 700 20px/1.2 var(--f-cond); margin: 4px 0 6px; }
.ref p { margin: 0; font-size: 15px; color: var(--ink-2); }
.drawing { overflow-x: auto; background: var(--sheet); border: 1px solid var(--rule); margin-top: 14px; -webkit-overflow-scrolling: touch; }
.drawing svg { display: block; width: 100%; height: auto; min-width: var(--minw, 900px); }
.drawing svg [hidden] { display: none; }
.layers { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 14px; }
.layers .lbl { font: 600 12px var(--f-cond); letter-spacing: .14em; text-transform: uppercase; color: var(--ink-2); margin-right: 4px; }
.layers label { display: inline-flex; gap: 7px; align-items: center; border: 1px solid var(--rule); background: var(--sheet); padding: 5px 11px 5px 9px; border-radius: 999px; font: 600 13px var(--f-cond); letter-spacing: .06em; text-transform: uppercase; cursor: pointer; user-select: none; }
.layers input { accent-color: var(--accent); margin: 0; width: 15px; height: 15px; }
.notes { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 10px 36px; margin: 16px 0 0; padding: 0; list-style: none; }
.notes li { padding-left: 26px; position: relative; font-size: 15px; color: var(--ink); min-width: 0; }
.notes li::before { content: attr(data-n); position: absolute; left: 0; top: 2px; font: 700 12px var(--f-cond); color: var(--accent); letter-spacing: .06em; }
.tablewrap { overflow-x: auto; margin-top: 16px; background: var(--sheet); border: 1px solid var(--rule); }
table { border-collapse: collapse; width: 100%; min-width: 760px; font-size: 14.5px; }
th, td { text-align: left; vertical-align: top; padding: 9px 12px; border-bottom: 1px solid var(--rule); }
th { font: 600 12px var(--f-cond); letter-spacing: .12em; text-transform: uppercase; color: var(--ink-2); background: var(--paper); position: sticky; top: 0; }
td.num { font: 600 15px var(--f-cond); font-variant-numeric: tabular-nums; white-space: nowrap; }
td b { font: 700 16px var(--f-cond); letter-spacing: .02em; }
.chip { display: inline-block; width: 12px; height: 12px; border: 1px solid var(--ink-3); vertical-align: -1px; margin-right: 8px; }
.cols { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px 40px; margin-top: 18px; }
.cols > div { min-width: 0; }
.cols ul { margin: 0; padding-left: 18px; }
.cols li { margin: 0 0 6px; font-size: 15px; }
.cols li::marker { color: var(--accent); }
code { font: 600 14px var(--f-cond); background: var(--sheet); border: 1px solid var(--rule); padding: 1px 5px; }
footer { margin-top: 64px; padding-top: 14px; border-top: 1px solid var(--rule); font: 500 13px var(--f-cond); letter-spacing: .04em; color: var(--ink-2); display: flex; flex-wrap: wrap; gap: 6px 24px; }
@media (prefers-reduced-motion: no-preference) { .index a { transition: border-color .15s; } }
"""

ZONES = [
    ("z-paver", "Hill Terrace", "L3 · +9.60", "B–I 1–2", "≈ 4,000 m²",
     "Arrive, take in the sea view, meet up before heading down; cinema events later.",
     "Bus shelter (Spawn A), viewpoint with coin telescopes, balloon arch, cinema marquee, planters"),
    ("z-brick", "Chalk Plaza", "L2 · +4.80", "B–I 2–4", "≈ 4,600 m² open",
     "Main social room: dance circle, emotes, LED-screen events, shopping.",
     "Chalk star Ø18 m, bunting, balloons, 6 benches, lamp ring, food truck, trees in planters"),
    ("bldg", "Pixel Pop Arcade", "L2 + L3 interior", "B–C 2–4", "2 × 1,024 m²",
     "Mini-games: Beat Stage, claw alley, racing, hoops, VR, party arena.",
     "See A-301. Upper floor bridges to the Hill Terrace."),
    ("bldg", "Wave Café", "L2 interior + terrace", "H–I 3–4", "672 m² + 400 m²",
     "Sit and chat; terrace watches the skate garden and the lighthouse.",
     "Counter, booths, window bar, book nook, parasols. See A-302."),
    ("under", "Shop Row", "L2, under the terrace", "D–I 2", "6 × 140–160 m²",
     "Cosmetics and avatar shop, photo booth, gacha, mini mart, bingsu, flowers.",
     "Awnings, signage band, bunting anchors (D4)"),
    ("z-paver", "Sunset Steps", "L2 → L1", "E–F 4–5", "≈ 960 m²",
     "Sit facing the sunset, group photos, concerts facing the sea.",
     "6 terraces × 0.40 m, timber seat caps, beanbags"),
    ("z-lawn", "Pine Garden", "L2 → L1 slope", "B–D 4–6", "≈ 2,300 m²",
     "Quiet corner: picnic, fountain, swings, hammocks between pines.",
     "Fountain Ø10 m, 4 m ramp path (≈ 4%), picnic tables, swings"),
    ("z-lawn", "Sunset Lawn", "L1 · +2.40", "D–G 5–6", "≈ 1,000 m²",
     "Lie on the grass between the steps and the promenade.",
     "Picnic blankets, beanbags"),
    ("z-conc", "Skate Garden", "L1 · +2.40 (bank from L2)", "G–I 4–6", "≈ 1,900 m²",
     "Skate tricks with an audience on the café terrace above.",
     "Bank 1:6.7, 16-stair with hubba, 2 ledges, flat rail, manual pad, quarter pipe (D3)"),
    ("z-timber", "Promenade", "L1 · +2.40", "A–H 6–7", "≈ 1,680 m²",
     "Stroll loop along the sea; Spawn B sits at the west end.",
     "Lamps every 12 m, benches every 24 m, lifebuoy stands, 2 beach stairs + ramp (D2)"),
    ("bldg", "Beach House", "L1 · +2.40, roof +6.60", "H–I 6–7", "480 m² + roof deck",
     "Snacks, float and surfboard rental, rooftop hangout.",
     "Tiki bar, lifebuoy stacks, surf rack, deck over Rocky Point"),
    ("z-sand", "Sunny Cove Beach", "+1.20 → ±0.00", "A–H 7–9", "≈ 4,600 m²",
     "Volleyball, bonfire nights, sunbathing, physics play with inflatables.",
     "Umbrellas + deck chairs, volleyball court, bonfire ring, lifeguard tower, sandcastle spot"),
    ("z-cliff", "Rocky Point & Pier", "+0.60 → +2.40", "H–I 7–10", "≈ 700 m² + 330 m²",
     "Rock pools, fishing, diving off the pier end, lighthouse photos.",
     "Lighthouse (landmark), rock pools, fishing spots"),
    ("z-deep", "Sea", "±0.00 → −3.00", "A–J 8–10", "≈ 7,000 m²",
     "Wade near the shore, swim out to the raft, stop at the buoy line.",
     "Float raft 6 × 6 m, buoy line (soft boundary)"),
]

METRICS = [
    ("Avatar height (assumed)", "1.30 m · capsule r 0.34, half-height 0.65",
     "Chibi proportions as in the references. Every other number scales from this."),
    ("Max step height", "0.45 m", "Terraces (0.40) and curbs are walkable; ledges (0.50) need a jump."),
    ("Walkable slope", "≤ 44°", "The bank (8.5°) and ramps are walkable; cliffs are steeper than 50° and block."),
    ("Jump apex (assumed)", "0.90 m", "Rails at 1.10 m stop players; benches, planters (0.60) and ledges can be jumped on."),
    ("Main path width", "≥ 8.0 m", "Groups of 4–6 walk side by side with room for the camera."),
    ("Secondary path width", "≥ 4.0 m", "Pine Garden ramp, east stair, beach stairs."),
    ("Minimum clear width", "2.4 m", "Two avatars pass without camera collision."),
    ("Doorway", "3.0 W × 3.2 H m min", "Accessories, wings and hats fit through."),
    ("Interior clear height", "≥ 4.5 m", "Third-person camera boom 3.5 m never clips the ceiling."),
    ("Exterior stairs", "riser 0.15 · tread 0.30", "Escalator stair 32R, east stair 32R, beach stairs 8R, skate stair 16R."),
    ("Ramps", "≤ 1:12 general · 1:6.7 skate bank", "Beach ramp 1:12; Pine Garden path ≈ 1:25."),
    ("Seating", "every ≤ 25 m", "Sitting is the main hangout verb. Benches, terraces, deck chairs, café seats."),
    ("Lighting", "lamps 12 m on the promenade · ring of 4 in the plaza", "Night hangout readability."),
    ("Swim transition", "water depth > 0.90 m", "Wade below that depth (about chest height), swim above it."),
    ("Soft boundary", "buoy line at Y 200", "A current pushes swimmers back after 3 s. No visible wall."),
    ("Target players", "30–50 per instance", "Social nodes total ≈ 11,000 m², about 220 m² per player at 50."),
]

NOTES = {
    "l101": [
        "Grid cells are 20 × 20 m, lettered A–J west to east and numbered 1–10 north to south. Use them in callouts: the café is H3, the bonfire B8, the lighthouse I10.",
        "The map falls 9.6 m from the Hill Terrace to the sea in four steps. Seating on every level faces south, so the sea and the sunset stay in view.",
        "Spawn A (bus stop, L3) frames the sea and the lighthouse in the first shot (sightline V3). Spawn B (shuttle stop, west promenade) is the beach-side spawn and the return point after a long swim.",
        "Boundaries are part of the world: cliffs east and west, the town road north (rail plus a blocking volume at the sidewalk), and the buoy line south, where a current pushes swimmers back.",
        "Main loop (red dashed): Spawn A → escalator → Chalk Plaza → Sunset Steps → beach → pier → lighthouse. About 280 m, or 45 s at an assumed 6 m/s run.",
        "Three links join L3 and L2 (escalator + stair, arcade bridge, east stair) and three join L2 and L1 (Sunset Steps, Pine Garden ramp, skate stair and bank). There are no dead ends.",
    ],
    "l201": [
        "Cut along the main axis X = 100, looking east. Objects beyond the cut are drawn in light line; hidden objects are dashed.",
        "Sunset Steps cover the 2.40 m between the plaza and the lawn in six 0.40 m terraces, each 3.00 m deep (detail D1).",
        "The seabed reaches −0.90 m about 15 m from the shoreline. Avatars wade until that depth and swim beyond it. The buoy line sits at −3.00 m.",
        "The lighthouse at the pier end (+18.60) is the tallest object on the map and the main orientation landmark.",
    ],
    "l202": [
        "Cut across the plaza at Y = 56, looking north toward the brick retaining wall, the escalator and the cinema.",
        "The arcade has 4.80 m floor to floor with 4.50 m clear inside, so the camera never clips. Its upper floor opens straight onto the Hill Terrace by a bridge, which makes it a second route up.",
        "The LED screen (14 × 8 m) sits above the arcade entrance and rises 2.20 m above the roof so it reads from the escalator and the Sunset Deck.",
    ],
    "a301": [
        "Ground floor: loud, crowd-friendly games (Beat Stage, claw alley) sit near the glass so people in the plaza see the activity.",
        "Upper floor: quieter games and the lounge. The north bridge lands on the Hill Terrace at +9.60.",
        "Central core: switchback stair 2 × 16R plus a lift. Keep 3.0 m clear around it.",
        "Cabinets are drawn at chibi scale (claw machines 1.8 × 1.8 m). Adjust to the final meshes.",
    ],
    "a302": [
        "Entry from the plaza on the west. Full-width folding glass on the south opens the café onto the terrace.",
        "The terrace hangs over the skate garden bank: guests watch tricks below and the lighthouse beyond (sightline V2).",
        "The kitchen is back of house: blocked, but visible through the pass.",
        "The book nook in the south-west corner is the quiet spot; the booths on the east wall seat groups of four.",
    ],
    "d401": [
        "D1: terrace risers stay under the max step height, so the steps work as seating and as a walkable slope.",
        "D2: the promenade rail is 1.10 m, above the 0.90 m jump apex, so players use the stairs and the ramp to reach the sand.",
        "D3: rails and ledges use CanStepUpOn = No (Unreal) so walkers bump into them while skaters ollie on.",
        "D4: shop units are 10 m deep with 4.50 m clear. Awnings at +8.00 cast the shade seen in refs 2–3.",
    ],
}


def notes_html(key):
    return "\n".join(f'<li data-n="{i + 1:02d}">{esc(t)}</li>' for i, t in enumerate(NOTES[key]))


def page(svgs):
    css = (PAGE_CSS.replace("%LIGHT%", css_tokens(LIGHT)).replace("%FONTS%", css_tokens(FONTS))
           .replace("%DARK%", css_tokens(DARK, "    ")) + SVG_CSS)
    zone_rows = "\n".join(
        f'<tr><td><span class="chip" style="background:var(--{_chip(c)})"></span><b>{esc(z)}</b></td>'
        f'<td class="num">{esc(lv)}</td><td class="num">{esc(g)}</td><td class="num">{esc(a)}</td>'
        f'<td>{esc(do)}</td><td>{esc(props)}</td></tr>' for c, z, lv, g, a, do, props in ZONES)
    metric_rows = "\n".join(
        f'<tr><td><b>{esc(m)}</b></td><td class="num">{esc(v)}</td><td>{esc(w)}</td></tr>' for m, v, w in METRICS)

    def sheet(sid, no, title, scale, svg_key, minw, extra=""):
        body, w, h, label = svgs[svg_key]
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
    <label><input type="checkbox" id="ly-circ" data-layer="lyr-circ" checked><span>Circulation</span></label>
    <label><input type="checkbox" id="ly-sight" data-layer="lyr-sight" checked><span>Sightlines</span></label>
    <label><input type="checkbox" id="ly-grid" data-layer="lyr-grid" checked><span>Grid</span></label>
    <label><input type="checkbox" id="ly-cuts" data-layer="lyr-cuts" checked><span>Section cuts</span></label>
  </div>"""

    html = f"""<title>Sunny Cove Park</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONT_URL}">
<style>{css}</style>
<div class="wrap">
<header>
  <p class="eyebrow">Level design package · social hangout map · concept rev A</p>
  <h1>Sunny Cove <span class="wave">Park</span></h1>
  <p class="lede">A seaside hangout map that steps down from a hilltop street to the sea in four levels. Players arrive at the top,
  gather in a brick chalk-art plaza lined with an arcade, a café and small shops, drift down through a pine garden and sunset terraces,
  and end on a crescent beach with a pier and a lighthouse. Every level looks at the water.</p>
  <dl class="tblock">
    <div><dt>Footprint</dt><dd>200 × 200 m · 4.0 ha</dd></div>
    <div><dt>Players</dt><dd>30–50 per instance</dd></div>
    <div><dt>Units</dt><dd>metres · 1 m = 100 UU</dd></div>
    <div><dt>Datum</dt><dd>±0.00 = sea level</dd></div>
    <div><dt>Levels</dt><dd>+9.60 / +4.80 / +2.40 / beach</dd></div>
    <div><dt>Orientation</dt><dd>north up · sun from SW</dd></div>
  </dl>
  <ul class="index">
    <li><a href="#l101"><b>L-101</b> Site plan</a></li>
    <li><a href="#l201"><b>L-201</b> Section A–A</a></li>
    <li><a href="#l202"><b>L-202</b> Section B–B</a></li>
    <li><a href="#a301"><b>A-301</b> Arcade plans</a></li>
    <li><a href="#a302"><b>A-302</b> Café plan</a></li>
    <li><a href="#d401"><b>D-401</b> Details</a></li>
    <li><a href="#zones"><b>S-1</b> Zone schedule</a></li>
    <li><a href="#metrics"><b>S-2</b> Gameplay metrics</a></li>
  </ul>
</header>

<section class="block" id="concept">
  <div class="block-head"><h2>How the map works</h2></div>
  <dl class="pillars">
    <div><dt>Every level sees the sea</dt><dd>The ground falls 9.6 m toward the south. Benches, terraces and the café terrace all face the water and the sunset.</dd></div>
    <div><dt>Loops, no dead ends</dt><dd>Three links between the Hill Terrace and the plaza, three between the plaza and the promenade. Friends can split up and meet again without backtracking.</dd></div>
    <div><dt>Somewhere to sit every 25 m</dt><dd>Sitting is the main hangout verb: terraces, benches, deck chairs, booths, logs around the bonfire.</dd></div>
    <div><dt>Four landmarks</dt><dd>Lighthouse to the south-east, LED screen in the plaza, cinema marquee to the north, and Turtle Island on the main axis.</dd></div>
  </dl>
  <h3 style="margin-top:28px">From the references</h3>
  <div class="refs">
    <div class="ref"><span class="tag">Ref 1 · skate jump street</span><h4>Hill Terrace + Skate Garden</h4>
      <p>White paver hardscape, grindable curbs and ledges, food truck, roadside bollards and the town street as the backdrop.</p></div>
    <div class="ref"><span class="tag">Refs 2–3 · chalk plaza</span><h4>Chalk Plaza + Shop Row</h4>
      <p>Herringbone brick, chalk paint on the floor, bunting and balloons, a brick retaining wall with an escalator up to a cinema, and a large screen.</p></div>
    <div class="ref"><span class="tag">Ref 4 · beach</span><h4>Beach + Beach House</h4>
      <p>Striped deck chairs, umbrellas, stacked lifebuoys, inflatables as physics props, and a beach building with window boxes against a cliff.</p></div>
  </div>
</section>

{sheet("l101", "L-101", "Site plan", "4 px = 1 m · grid 20 m", "site", 960, layers)}
{sheet("l201", "L-201", "Section A–A", "H 4 px = 1 m · V 10 px = 1 m", "aa", 900)}
{sheet("l202", "L-202", "Section B–B", "H 5 px = 1 m · V 10 px = 1 m", "bb", 940)}
{sheet("a301", "A-301", "Pixel Pop Arcade", "10 px = 1 m", "arcade", 720)}
{sheet("a302", "A-302", "Wave Café", "12 px = 1 m", "cafe", 560)}
{sheet("d401", "D-401", "Standard details", "40 px = 1 m · D4 20 px = 1 m", "details", 900)}

<section class="block" id="zones">
  <div class="block-head"><span class="sheet-no">S-1</span><h2>Zone schedule</h2><span class="scale">areas approximate</span></div>
  <div class="tablewrap"><table>
    <thead><tr><th>Zone</th><th>Level</th><th>Grid</th><th>Area</th><th>What players do</th><th>Key props</th></tr></thead>
    <tbody>{zone_rows}</tbody>
  </table></div>
</section>

<section class="block" id="metrics">
  <div class="block-head"><span class="sheet-no">S-2</span><h2>Gameplay metrics</h2><span class="scale">confirm against the final avatar</span></div>
  <div class="tablewrap"><table>
    <thead><tr><th>Metric</th><th>Value</th><th>Why</th></tr></thead>
    <tbody>{metric_rows}</tbody>
  </table></div>
</section>

<section class="block" id="blockout">
  <div class="block-head"><h2>Blockout notes</h2></div>
  <div class="cols">
    <div><h3>Coordinates</h3><ul>
      <li>Plan coordinates are metres from the north-west corner of grid cell A1: X runs east, Y runs south. Multiply by 100 for Unreal units.</li>
      <li>Z = 0 is sea level and the water plane. Level heights: <code>+960</code> <code>+480</code> <code>+240</code> <code>+120</code> UU.</li>
      <li>Keep one axis mapping for every sheet when you place the blockout.</li>
    </ul></div>
    <div><h3>Collision and boundaries</h3><ul>
      <li>Blocking volumes on both cliffs and along the town sidewalk rail.</li>
      <li>Promenade and terrace rails are 1.10 m and block, with gaps at stairs and the ramp.</li>
      <li>Buoy line: trigger volume that applies a return current after 3 s.</li>
      <li>Town backdrop, Turtle Island and the open sea are visual only (HLOD or impostors, no collision).</li>
    </ul></div>
    <div><h3>Lighting and props</h3><ul>
      <li>Sun azimuth about 235° (south-west), 15–25° elevation for golden hour. The steps and the café terrace face it.</li>
      <li>Physics props as in ref 4: inflatables, beach balls, umbrellas and deck chairs. Cap active bodies per area.</li>
      <li>Bonfire, lamps and the LED screen carry the night version of the map.</li>
    </ul></div>
  </div>
</section>

<footer><span>Sunny Cove Park · concept layout rev A · 2026-10-05</span><span>Source: docs/maps/sunny-cove/build.py</span><span>Standalone SVGs in docs/maps/sunny-cove/svg</span></footer>
</div>
<script>
document.querySelectorAll('[data-layer]').forEach(function (cb) {{
  cb.addEventListener('change', function () {{
    var g = document.getElementById(cb.dataset.layer);
    if (g) g.toggleAttribute('hidden', !cb.checked);
  }});
}});
</script>
"""
    return html


def _chip(cls):
    return {"z-paver": "paver", "z-brick": "brick", "bldg": "bldg", "under": "bldg", "z-lawn": "lawn",
            "z-conc": "conc", "z-timber": "timber", "z-sand": "sand", "z-cliff": "rock", "z-deep": "sea-deep"}[cls]


def main():
    builders = {
        "site": (site_plan, "L-101 Site plan", "L-101-site-plan.svg"),
        "aa": (section_aa, "L-201 Section A-A", "L-201-section-AA.svg"),
        "bb": (section_bb, "L-202 Section B-B", "L-202-section-BB.svg"),
        "arcade": (arcade_plans, "A-301 Pixel Pop Arcade plans", "A-301-arcade-plans.svg"),
        "cafe": (cafe_plan, "A-302 Wave Cafe plan", "A-302-cafe-plan.svg"),
        "details": (details, "D-401 Standard details", "D-401-details.svg"),
    }
    svgs = {}
    os.makedirs(os.path.join(HERE, "svg"), exist_ok=True)
    for key, (fn, label, fname) in builders.items():
        body, w, h = fn()
        svgs[key] = (body, w, h, label)
        with open(os.path.join(HERE, "svg", fname), "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n' + wrap(body, w, h, label, standalone=True) + "\n")
    with open(os.path.join(HERE, "index.html"), "w", encoding="utf-8") as f:
        f.write(page(svgs))
    print("wrote index.html and", len(builders), "SVG sheets")


if __name__ == "__main__":
    main()
