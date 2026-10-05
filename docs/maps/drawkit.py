"""Shared drawing kit for the map layout packages in docs/maps.

Tokens, SVG styles, the world-to-pixel canvas, dimension helpers and the page
stylesheet. Each map's build.py imports from here.
"""
import math
import re

# --------------------------------------------------------------------- tokens
LIGHT = {
    "paper": "#E7EDF0", "sheet": "#FBFCFC", "rule": "#C4D1D8",
    "ink": "#16283A", "ink-2": "#4A5C6F", "ink-3": "#93A3B2",
    "accent": "#D93A55", "teal": "#0D7F8A",
    "sand": "#FBF7EA", "sea": "#BCE4EB", "sea-deep": "#8CC7D8",
    "lawn": "#CDE4B3", "brick": "#EDD0BD", "paver": "#E1E6EA",
    "conc": "#D3D9DC", "timber": "#E6CFA6", "rock": "#CBC5BC",
    "bldg": "#D5DFE9", "tree": "#9BCA84", "tree-edge": "#58894C",
    "chalk-y": "#F0BE2C", "chalk-p": "#E5539A", "chalk-c": "#24ABCC",
    "sak": "#F5C3D8", "shrub": "#86BB6D", "tree-2": "#7DB268", "foam": "#FFFFFF",
    "sea-mid": "#A5D6E2", "sand-wet": "#F0EAD8", "roof": "#BAC7D4", "roof-2": "#9DAFC1",
}
DARK = {
    "paper": "#0A1522", "sheet": "#0F1F31", "rule": "#233A52",
    "ink": "#DCE8F2", "ink-2": "#9EB3C7", "ink-3": "#566F88",
    "accent": "#FF6E86", "teal": "#45C6CF",
    "sand": "#5B5A52", "sea": "#1C4757", "sea-deep": "#133447",
    "lawn": "#29452F", "brick": "#4D3732", "paver": "#22354A",
    "conc": "#2B3B4C", "timber": "#463828", "rock": "#3A3F47",
    "bldg": "#1E3550", "tree": "#3D6942", "tree-edge": "#7DAE73",
    "chalk-y": "#D9AA2A", "chalk-p": "#D45591", "chalk-c": "#2E9EBB",
    "sak": "#6A3A50", "shrub": "#33603E", "tree-2": "#2E5535", "foam": "#CFE3EE",
    "sea-mid": "#173D4F", "sand-wet": "#4C4B45", "roof": "#2A4361", "roof-2": "#36537A",
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
.z-road{fill:var(--ink-3);opacity:.6}
.lane{fill:none;stroke:var(--sheet);stroke-width:1;stroke-dasharray:6 5}
.zebra{fill:var(--sheet)}
.tree-s{fill:var(--chalk-p);fill-opacity:.45;stroke:var(--chalk-p);stroke-width:.8}
.trim-y{fill:none;stroke:var(--chalk-y);stroke-width:2.4}
.arc-y{fill:var(--chalk-y);fill-opacity:.32}
.key{fill:var(--ink)}
.statue{fill:var(--sheet);stroke:var(--ink);stroke-width:1.2}
.tree-o{fill:var(--tree);stroke:var(--tree-edge);stroke-width:1.5}
.tree-f{fill:var(--tree)}
.sak-o{fill:var(--sak);stroke:var(--chalk-p);stroke-width:1.3}
.sak-f{fill:var(--sak)}
.shrub-o{fill:var(--shrub);stroke:var(--tree-edge);stroke-width:1}
.shrub-f{fill:var(--shrub)}
.bed{fill:var(--shrub);stroke:var(--tree-edge);stroke-width:.9}
.leaf{fill:none;stroke:var(--tree-edge);stroke-width:.7;opacity:.8;stroke-linecap:round}
.blossom{fill:var(--chalk-p)}
.palm{fill:var(--tree-2);stroke:var(--tree-edge);stroke-width:.6;stroke-linejoin:round}
.shadow{fill:var(--ink);opacity:.12}
.rock{fill:var(--rock);stroke:var(--ink-2);stroke-width:.8;stroke-linejoin:round}
.foam{fill:none;stroke:var(--foam);stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round}
.foam-d{fill:none;stroke:var(--foam);stroke-width:1;stroke-dasharray:4 3;stroke-linecap:round}
.z-mid{fill:var(--sea-mid)}
.z-wet{fill:var(--sand-wet)}
.roof{fill:var(--roof);stroke:var(--ink);stroke-width:1.6}
.roof-2{fill:var(--roof-2)}
.post{fill:var(--ink)}
.rail{fill:none;stroke:var(--ink);stroke-width:.9}
.tread{fill:none;stroke:var(--ink-2);stroke-width:.5}
.joint{fill:none;stroke:var(--ink-3);stroke-width:.45}
.band{fill:var(--rule)}
.wall-l{fill:none;stroke:var(--ink);stroke-width:3.2;stroke-linecap:square}
.wall6{fill:none;stroke:var(--ink);stroke-width:2.4}
.string{fill:none;stroke:var(--ink-2);stroke-width:.6;stroke-dasharray:1 2}
.bulb{fill:var(--chalk-y)}
.door{fill:none;stroke:var(--ink-2);stroke-width:.6}
.curb{fill:none;stroke:var(--ink);stroke-width:1.1;stroke-linejoin:round}
.wallp{fill:var(--ink-2);stroke:var(--ink);stroke-width:.5;stroke-linejoin:miter}
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
<pattern id="{p}-boardh" width="10" height="3" patternUnits="userSpaceOnUse"><path class="pat-s" d="M0 0H10"/></pattern>
<pattern id="{p}-pave" width="12" height="12" patternUnits="userSpaceOnUse"><path class="joint" d="M0 0H12M0 0V12"/></pattern>
<pattern id="{p}-stripe" width="5" height="5" patternUnits="userSpaceOnUse"><rect width="2.5" height="5" class="chalk-p"/></pattern>
<pattern id="{p}-stripey" width="5" height="5" patternUnits="userSpaceOnUse"><rect width="2.5" height="5" class="chalk-y"/></pattern>
<pattern id="{p}-stripec" width="5" height="5" patternUnits="userSpaceOnUse"><rect width="2.5" height="5" class="chalk-c"/></pattern>
<pattern id="{p}-thatch" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(30)"><path class="pat-s" d="M0 0V4M2 0V2"/></pattern>
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


# ===================================================================== export
def wrap(body, w, h, label, standalone=False):
    style = ""
    if standalone:
        tokens = dict(LIGHT, **FONTS)
        css = re.sub(r"var\(--([\w-]+)\)", lambda m: tokens[m.group(1)], SVG_CSS)
        body = re.sub(r"var\(--([\w-]+)\)", lambda m: tokens[m.group(1)], body)
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



# ================================================================ organic kit
import random  # noqa: E402


def cr_cmds(pts, closed=True):
    """Catmull-Rom spline through pts as Cv.path commands."""
    k = len(pts)
    cmds = [("M", pts[0][0], pts[0][1])]
    for i in range(k if closed else k - 1):
        p0 = pts[(i - 1) % k] if (closed or i > 0) else pts[0]
        p1, p2 = pts[i], pts[(i + 1) % k]
        p3 = pts[(i + 2) % k] if (closed or i + 2 < k) else pts[-1]
        cmds.append(("C", p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6,
                     p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6, p2[0], p2[1]))
    if closed:
        cmds.append(("Z",))
    return cmds


def cr_sample(pts, closed=False, per=10):
    """Dense points along the Catmull-Rom spline (for offsets and polygons)."""
    k = len(pts)
    out = []
    for i in range(k if closed else k - 1):
        p0 = pts[(i - 1) % k] if (closed or i > 0) else pts[0]
        p1, p2 = pts[i], pts[(i + 1) % k]
        p3 = pts[(i + 2) % k] if (closed or i + 2 < k) else pts[-1]
        for s in range(per):
            t = s / per
            t2, t3 = t * t, t * t * t
            out.append(tuple(.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                   + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    if not closed:
        out.append(pts[-1])
    return out


def offset_pts(pts, d):
    """Offset an open polyline by d along its left normal (dy, -dx)."""
    out = []
    for i, (x, y) in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        out.append((x + d * dy / L, y - d * dx / L))
    return out


def wobble(pts, amp, freq, seed=0):
    rnd = random.Random(seed)
    ph = rnd.uniform(0, 6.28)
    out = []
    acc = 0
    for i, (x, y) in enumerate(pts):
        if i:
            acc += math.hypot(x - pts[i - 1][0], y - pts[i - 1][1])
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        w = amp * math.sin(acc * freq + ph)
        out.append((x + w * dy / L, y - w * dx / L))
    return out


def blob(cx, cy, rx, ry=None, seed=0, amp=.18, k=10, rot=0.0):
    rnd = random.Random(seed)
    ry = ry or rx
    ph = [rnd.uniform(0, 6.283) for _ in range(3)]
    cr, sr = math.cos(rot), math.sin(rot)
    pts = []
    for i in range(k):
        a = 2 * math.pi * i / k
        f = 1 + amp * (.6 * math.sin(2 * a + ph[0]) + .3 * math.sin(3 * a + ph[1]) + .25 * math.sin(5 * a + ph[2])) \
            + rnd.uniform(-amp, amp) * .35
        x, y = rx * f * math.cos(a), ry * f * math.sin(a)
        pts.append((cx + x * cr - y * sr, cy + x * sr + y * cr))
    return pts


def inside(pt, poly):
    x, y = pt
    c = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def canopy(cv, u, v, r, seed=0, kind="tree", shadow=True, detail=True):
    """Top-view tree canopy: scalloped outline from lobes, shadow cast north-east."""
    rnd = random.Random(seed * 7919 + 13)
    k = 7 + seed % 3
    lobes = []
    for i in range(k):
        a = 2 * math.pi * i / k + rnd.uniform(-.25, .25)
        rr = r * rnd.uniform(.56, .68)
        lobes.append((u + rr * math.cos(a), v + rr * math.sin(a), r * rnd.uniform(.34, .44)))
    lobes.append((u, v, r * .72))
    s = abs(cv.sx)
    if shadow:
        cv.add('<g class="shadow">' + "".join(
            f'<circle cx="{n(cv.X(x + r * .22))}" cy="{n(cv.Y(y - r * .22))}" r="{n(rr * s)}"/>' for x, y, rr in lobes) + "</g>")
    cv.add(f'<g class="{kind}-o">' + "".join(
        f'<circle cx="{n(cv.X(x))}" cy="{n(cv.Y(y))}" r="{n(rr * s)}"/>' for x, y, rr in lobes) + "</g>")
    cv.add(f'<g class="{kind}-f">' + "".join(
        f'<circle cx="{n(cv.X(x))}" cy="{n(cv.Y(y))}" r="{n(rr * s - .9)}"/>' for x, y, rr in lobes) + "</g>")
    if detail:
        d = []
        for i in range(5 + seed % 3):
            a = rnd.uniform(0, 6.283)
            rr = r * rnd.uniform(.2, .62)
            x, y = u + rr * math.cos(a), v + rr * math.sin(a)
            b = a + 1.9
            L = r * .16
            d.append(f"M{n(cv.X(x))} {n(cv.Y(y))}q{n(L * s * math.cos(b) * .5 + L * s * .3)} {n(L * s * math.sin(b) * .5 - L * s * .3)} "
                     f"{n(L * s * math.cos(b))} {n(L * s * math.sin(b))}")
        cv.add(f'<path class="leaf" d="{" ".join(d)}"/>')
        if kind == "sak":
            cv.add("".join(f'<circle class="blossom" cx="{n(cv.X(u + r * rnd.uniform(-.6, .6)))}" '
                           f'cy="{n(cv.Y(v + r * rnd.uniform(-.6, .6)))}" r="{n(.18 * s)}"/>' for _ in range(7)))
    cv.add(f'<circle class="ink-f" cx="{n(cv.X(u))}" cy="{n(cv.Y(v))}" r="{n(max(.22 * s, 1))}"/>')


def palm_top(cv, u, v, r, seed=0, shadow=True):
    """Top-view palm: nine curved fronds with midribs."""
    rnd = random.Random(seed * 31 + 5)
    fr, ribs, sh = [], [], []
    for i in range(9):
        a = 2 * math.pi * i / 9 + rnd.uniform(-.18, .18)
        L = r * rnd.uniform(.85, 1.05)
        tip = (u + L * math.cos(a + .18), v + L * math.sin(a + .18))
        c1 = (u + .6 * L * math.cos(a - .26), v + .6 * L * math.sin(a - .26))
        c2 = (u + .6 * L * math.cos(a + .34), v + .6 * L * math.sin(a + .34))
        cm = (u + .55 * L * math.cos(a + .05), v + .55 * L * math.sin(a + .05))
        fr.append(cv.d([("M", u, v), ("Q", c1[0], c1[1], tip[0], tip[1]), ("Q", c2[0], c2[1], u, v), ("Z",)]))
        ribs.append(cv.d([("M", u, v), ("Q", cm[0], cm[1], tip[0], tip[1])]))
        if shadow:
            o = r * .3
            sh.append(cv.d([("M", u + o, v - o), ("Q", c1[0] + o, c1[1] - o, tip[0] + o, tip[1] - o),
                            ("Q", c2[0] + o, c2[1] - o, u + o, v - o), ("Z",)]))
    if shadow:
        cv.add(f'<path class="shadow" d="{" ".join(sh)}"/>')
    cv.add(f'<path class="palm" d="{" ".join(fr)}"/>')
    cv.add(f'<path class="leaf" d="{" ".join(ribs)}"/>')
    cv.add(f'<circle class="ink-f" cx="{n(cv.X(u))}" cy="{n(cv.Y(v))}" r="{n(.3 * abs(cv.sx))}"/>')


def rock(cv, u, v, r, seed=0, shadow=True, foam=False):
    rnd = random.Random(seed * 101 + 7)
    pts = blob(u, v, r, r * rnd.uniform(.66, .95), seed, amp=.24, k=7 + seed % 3, rot=rnd.uniform(0, 3.14))
    if foam:
        cv.path(cr_cmds(blob(u, v, r * 1.35, r * 1.2, seed + 3, amp=.12, k=9)), "foam-d")
    if shadow:
        cv.poly([(x + r * .25, y - r * .25) for x, y in pts], "shadow")
    cv.poly(pts, "rock")
    cx, cy = u + rnd.uniform(-.25, .25) * r, v + rnd.uniform(-.25, .25) * r
    for j in rnd.sample(range(len(pts)), 3):
        cv.line(cx, cy, pts[j][0], pts[j][1], "ln-f")


def rock_cluster(cv, poly, count, rmin, rmax, seed=0, foam=False):
    rnd = random.Random(seed)
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    placed = []
    tries = 0
    while len(placed) < count and tries < count * 60:
        tries += 1
        pt = (rnd.uniform(min(xs), max(xs)), rnd.uniform(min(ys), max(ys)))
        if not inside(pt, poly):
            continue
        r = rmin + (rmax - rmin) * rnd.random() ** 2.2
        if any(math.hypot(pt[0] - q[0], pt[1] - q[1]) < (r + q[2]) * .62 for q in placed):
            continue
        placed.append((pt[0], pt[1], r))
    for i, (x, y, r) in enumerate(sorted(placed, key=lambda q: -q[2])):
        rock(cv, x, y, r, seed * 1000 + i, foam=foam)


def shrub_bed(cv, pts, seed=0, density=.5, rmin=.7, rmax=1.3, smooth=True):
    """Planting bed: organic outline filled with small shrub canopies."""
    cv.path(cr_cmds(pts) if smooth else [("M",) + pts[0]] + [("L",) + p for p in pts[1:]] + [("Z",)], "bed")
    rnd = random.Random(seed)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    area = (max(xs) - min(xs)) * (max(ys) - min(ys))
    want = int(area * density / 3) + 2
    got = 0
    for _ in range(want * 30):
        if got >= want:
            break
        pt = (rnd.uniform(min(xs), max(xs)), rnd.uniform(min(ys), max(ys)))
        r = rnd.uniform(rmin, rmax)
        if inside(pt, pts):
            canopy(cv, pt[0], pt[1], r, seed * 100 + got, "shrub", shadow=False, detail=False)
            got += 1


def railing(cv, pts, spacing=2.0):
    cv.pline(pts, "rail")
    acc, nxt = 0.0, 0.0
    s = abs(cv.sx)
    for i in range(1, len(pts)):
        (x1, y1), (x2, y2) = pts[i - 1], pts[i]
        L = math.hypot(x2 - x1, y2 - y1)
        while nxt <= acc + L + 1e-6:
            t = (nxt - acc) / L if L else 0
            x, y = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
            cv.add(f'<rect class="post" x="{n(cv.X(x) - .9)}" y="{n(cv.Y(y) - .9)}" width="1.8" height="1.8"/>')
            nxt += spacing
        acc += L
    return s


def bench(cv, u, v, length=3.0, ang=0.0, depth=.7):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    hl, hd = length / 2, depth / 2
    corners = [(-hl, -hd), (hl, -hd), (hl, hd), (-hl, hd)]
    cv.poly([(u + x * ca - y * sa, v + x * sa + y * ca) for x, y in corners], "prop")
    for k in range(1, 3):
        y = -hd + depth * k / 3
        cv.line(u - hl * ca - y * sa, v - hl * sa + y * ca, u + hl * ca - y * sa, v + hl * sa + y * ca, "joint")


def parasol(cv, u, v, r=1.3, cls="umb-y", chairs=0, ribs=8):
    for k in range(chairs):
        a = 2 * math.pi * k / chairs + .4
        x, y = u + (r + .2) * math.cos(a), v + (r + .2) * math.sin(a)
        cv.rect(x - .3, y - .3, x + .3, y + .3, "prop")
    cv.circle(u, v, r, cls)
    for k in range(ribs):
        a = 2 * math.pi * k / ribs
        cv.line(u, v, u + r * math.cos(a), v + r * math.sin(a), "joint")
    cv.circle(u, v, .18, "ink-f")


def lounger(cv, u, v, ang=90.0, cls="prop"):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)

    def T(x, y):
        return (u + x * ca - y * sa, v + x * sa + y * ca)
    cv.poly([T(-.95, -.35), T(.95, -.35), T(.95, .35), T(-.95, .35)], cls)
    p, q = T(.5, -.35), T(.5, .35)
    cv.line(p[0], p[1], q[0], q[1], "joint")


def door_swing(cv, u, v, w, ang0, ang1):
    s = abs(cv.sx)
    x0, y0 = cv.X(u), cv.Y(v)
    a0, a1 = math.radians(ang0), math.radians(ang1)
    xa, ya = x0 + w * s * math.cos(a0), y0 + w * s * math.sin(a0)
    xb, yb = x0 + w * s * math.cos(a1), y0 + w * s * math.sin(a1)
    sweep = 1 if (ang1 - ang0) % 360 < 180 else 0
    cv.add(f'<path class="door" d="M{n(x0)} {n(y0)}L{n(xa)} {n(ya)}A{n(w * s)} {n(w * s)} 0 0 {sweep} {n(xb)} {n(yb)}"/>')


def tree_elev(cv, u, z, h=7.0, w=6.0, seed=0, kind="tree"):
    """Elevation tree: trunk plus lobed canopy, sized in px from the horizontal scale."""
    rnd = random.Random(seed * 17 + 3)
    sx, sy = abs(cv.sx), abs(cv.sy)
    top = z + h
    cz = z + h * .62
    cv.line(u, z, u, cz, "trunk")
    R = w / 2 * sx
    cxp, cyp = cv.X(u), cv.Y(cz)
    ry = (top - cz) * sy * .95
    lobes = [(cxp, cyp, R * .72, ry * .72)]
    for i in range(8):
        a = math.radians(165 + i * 30 + rnd.uniform(-8, 8))
        lobes.append((cxp + R * .62 * math.cos(a), cyp + ry * .58 * math.sin(a), R * rnd.uniform(.34, .44),
                      ry * rnd.uniform(.36, .46)))
    cv.add(f'<g class="{kind}-o">' + "".join(f'<ellipse cx="{n(x)}" cy="{n(y)}" rx="{n(a)}" ry="{n(b)}"/>' for x, y, a, b in lobes) + "</g>")
    cv.add(f'<g class="{kind}-f">' + "".join(f'<ellipse cx="{n(x)}" cy="{n(y)}" rx="{n(a - .9)}" ry="{n(b - .9)}"/>' for x, y, a, b in lobes) + "</g>")


def palm_elev(cv, u, z, h=7.0, seed=0, lean=.6):
    rnd = random.Random(seed * 13 + 1)
    tx, tz = u + lean, z + h
    cv.path([("M", u, z), ("Q", u + lean * .2, z + h * .6, tx, tz)], "trunk")
    fr = []
    s = abs(cv.sx)
    for i in range(7):
        a = math.radians(-160 + i * 23 + rnd.uniform(-6, 6))
        L = rnd.uniform(2.4, 3.0) * s
        x0, y0 = cv.X(tx), cv.Y(tz)
        x1, y1 = x0 + L * math.cos(a), y0 + L * math.sin(a) * .7 + abs(math.cos(a)) * L * .35
        mx, my = x0 + L * .5 * math.cos(a), y0 + L * .5 * math.sin(a) * .7 - L * .12
        fr.append(f"M{n(x0)} {n(y0)}Q{n(mx)} {n(my - 3)} {n(x1)} {n(y1)}Q{n(mx)} {n(my + 2)} {n(x0)} {n(y0)}Z")
    cv.add(f'<path class="palm" d="{" ".join(fr)}"/>')
