"""Building elevations for the Japan Coastal Hangout Park (sheets A-501 to A-504).

Every elevation is drawn in metres on a Cv whose vertical axis is the real
level (datum ±0.00 = sea level), so plinths, steps and parapets line up with
the plan (L-101) and the sections (L-201/L-202). Horizontal positions come
from the traced plan footprints: u is measured along the face, left to right
as the viewer sees it.
"""
import math
import random

from drawkit import Cv, avatar, esc, etag, frange, hdim, n, palm_elev, title_strip, tree_elev, vdim

# facade palette, light and dark (sheets keep their colours, a little muted in dark mode)
F_LIGHT = {
    "f-yel": "#F7CB3B", "f-yel-2": "#E3AE1F", "f-yel-3": "#FFE27A", "f-cream": "#F7F2E6", "f-cream-2": "#DED6C3",
    "f-dark": "#2E333B", "f-blue": "#2F8FE8", "f-red": "#E8414E", "f-green": "#3FB950", "f-glass": "#CBE8EE",
    "f-glass-2": "#9CCFDB", "f-pink": "#F59BC3", "f-lilac": "#B9A2EE", "f-poster": "#3D8BE0", "f-warm": "#FFE7B0",
    "f-white": "#FFFFFF", "f-wall": "#F1E9DA", "f-coral": "#EE8A6B", "f-mint": "#A9DCC6", "f-navy": "#2C3E57",
    "f-steel": "#8C99A6", "f-sky": "#E4F2F7", "f-thatch": "#D9B477", "f-orange": "#F59A3A",
}
F_DARK = {
    "f-yel": "#D7AE2F", "f-yel-2": "#B68B17", "f-yel-3": "#E6C55C", "f-cream": "#CFC9BB", "f-cream-2": "#A9A28F",
    "f-dark": "#151A20", "f-blue": "#2A78C2", "f-red": "#C2384A", "f-green": "#379C47", "f-glass": "#46707C",
    "f-glass-2": "#365C68", "f-pink": "#C97BA0", "f-lilac": "#8D7BC0", "f-poster": "#2F6FB5", "f-warm": "#D9B66E",
    "f-white": "#F2F4F6", "f-wall": "#BDB5A5", "f-coral": "#C46F55", "f-mint": "#7DAE98", "f-navy": "#1E2C40",
    "f-steel": "#6C7884", "f-sky": "#16293A", "f-thatch": "#A88A55", "f-orange": "#C97E31",
}

ELEV_CSS = """
.e-yel{fill:var(--f-yel);stroke:var(--ink);stroke-width:.9;stroke-linejoin:round}
.e-yel2{fill:var(--f-yel-2)}
.e-yel3{fill:var(--f-yel-3)}
.e-cream{fill:var(--f-cream);stroke:var(--ink);stroke-width:.9;stroke-linejoin:round}
.e-cream2{fill:var(--f-cream-2)}
.e-dark{fill:var(--f-dark)}
.e-blue{fill:var(--f-blue);stroke:var(--ink);stroke-width:.7}
.e-red{fill:var(--f-red);stroke:var(--ink);stroke-width:.7}
.e-green{fill:var(--f-green);stroke:var(--ink);stroke-width:.7}
.e-glass{fill:var(--f-glass);stroke:var(--ink);stroke-width:.8}
.e-glass-t{fill:var(--f-glass);fill-opacity:.45;stroke:none}
.e-glow{fill:var(--f-warm)}
.e-pink{fill:var(--f-pink)}
.e-pink-o{fill:var(--f-pink);stroke:var(--ink);stroke-width:.7}
.e-lilac{fill:var(--f-lilac)}
.e-poster{fill:var(--f-poster);stroke:var(--ink);stroke-width:.6}
.e-wall{fill:var(--f-wall);stroke:var(--ink);stroke-width:.9;stroke-linejoin:round}
.e-coral{fill:var(--f-coral);stroke:var(--ink);stroke-width:.8}
.e-mint{fill:var(--f-mint);stroke:var(--ink);stroke-width:.8}
.e-navy{fill:var(--f-navy)}
.e-steel{fill:var(--f-steel);stroke:var(--ink);stroke-width:.6}
.e-wood{fill:var(--timber);stroke:var(--ink);stroke-width:.8}
.e-conc{fill:var(--conc);stroke:var(--ink);stroke-width:.8}
.e-thatch{fill:var(--f-thatch);stroke:var(--ink);stroke-width:.9;stroke-linejoin:round}
.e-orange{fill:var(--f-orange)}
.e-white{fill:var(--f-white)}
.e-sky{fill:var(--f-sky)}
.e-shadow{fill:var(--ink);opacity:.15}
.e-joint{fill:none;stroke:var(--ink);stroke-width:.45;opacity:.3}
.e-mull{fill:none;stroke:var(--ink);stroke-width:1}
.e-mull-t{fill:none;stroke:var(--f-dark);stroke-width:1.6}
.e-hl{fill:none;stroke:var(--f-white);stroke-width:1.4;opacity:.75;stroke-linecap:round}
.e-led{fill:none;stroke:var(--f-white);stroke-width:1.6;stroke-linecap:round}
.e-led-p{fill:none;stroke:var(--f-pink);stroke-width:1.4;stroke-linecap:round}
.e-led-c{fill:none;stroke:var(--chalk-c);stroke-width:1.4;stroke-linecap:round}
.e-out{fill:none;stroke:var(--ink);stroke-width:1.3;stroke-linejoin:round}
.e-ghost{fill:none;stroke:var(--ink-2);stroke-width:.8;stroke-dasharray:4 3}
.e-ground{fill:none;stroke:var(--ink);stroke-width:2.2;stroke-linecap:square}
.e-wave{fill:none;stroke:var(--f-poster);stroke-width:1.2;stroke-linecap:round}
.e-wave-y{fill:none;stroke:var(--f-yel-2);stroke-width:1.4;stroke-linecap:round}
.e-break{fill:none;stroke:var(--ink-2);stroke-width:.8}
.e-rope{fill:none;stroke:var(--ink-2);stroke-width:.6}
.e-fern{fill:var(--shrub);stroke:var(--tree-edge);stroke-width:.6;stroke-linejoin:round}
.e-key{font:600 9px var(--f-cond);letter-spacing:.03em;fill:var(--ink)}
.e-fd{font-family:var(--f-display)}
.e-fb{font-family:var(--f-body)}
.e-fc{font-family:var(--f-cond)}
"""

SKY_PAD = 1.4


# ----------------------------------------------------------------- primitives
def stext(cv, u, z, s, cap, fill="var(--f-white)", weight=800, family="var(--f-display)", anchor="middle",
          stroke=None, sw=0.0, ls=0.0, rot=None):
    """Sign text sized by cap height in metres (the drawing's own scale)."""
    size = cap * abs(cv.sy) / .72
    fam = {"var(--f-display)": "e-fd", "var(--f-body)": "e-fb", "var(--f-cond)": "e-fc"}[family]
    st = f"font-weight:{weight};font-size:{n(size)}px;fill:{fill};letter-spacing:{n(ls * abs(cv.sx))}px"
    if stroke:
        st += f";stroke:{stroke};stroke-width:{n(sw)}px;paint-order:stroke;stroke-linejoin:round"
    x, y = cv.X(u), cv.Y(z)
    tr = f' transform="rotate({n(rot)} {n(x)} {n(y)})"' if rot else ""
    cv.add(f'<text class="{fam}" x="{n(x)}" y="{n(y)}" text-anchor="{anchor}" style="{st}"{tr}>{esc(s)}</text>')


def rrect(cv, u0, z0, u1, z1, r, cls, extra="", top_only=False):
    """Rounded rectangle in metres; top_only rounds just the upper corners."""
    ua, ub = sorted((u0, u1))
    za, zb = sorted((z0, z1))
    r = min(r, (ub - ua) / 2, (zb - za) / 2)
    if top_only:
        cmds = [("M", ua, za), ("L", ua, zb - r), ("Q", ua, zb, ua + r, zb), ("L", ub - r, zb), ("Q", ub, zb, ub, zb - r),
                ("L", ub, za), ("Z",)]
    else:
        cmds = [("M", ua + r, za), ("L", ub - r, za), ("Q", ub, za, ub, za + r), ("L", ub, zb - r), ("Q", ub, zb, ub - r, zb),
                ("L", ua + r, zb), ("Q", ua, zb, ua, zb - r), ("L", ua, za + r), ("Q", ua, za, ua + r, za), ("Z",)]
    cv.path(cmds, cls, extra)


def wave(cv, u0, u1, z, amp, k, cls="e-wave"):
    pts = []
    for i in range(int(k * 12) + 1):
        t = i / (k * 12)
        pts.append((u0 + (u1 - u0) * t, z + amp * math.sin(t * k * 2 * math.pi)))
    cv.pline(pts, cls)


def ground(cv, u0, u1, z, depth=.7, prof=None):
    """Ground line with an earth band below. prof: optional [(u, z)] profile instead of a flat line."""
    pts = prof or [(u0, z), (u1, z)]
    zb = min(p[1] for p in pts) - depth
    cv.poly(pts + [(pts[-1][0], zb), (pts[0][0], zb)], "poche")
    cv.poly(pts + [(pts[-1][0], zb), (pts[0][0], zb)], "", ' fill="url(#ce-earth)"')
    cv.pline(pts, "e-ground")


def break_line(cv, u, z0, z1):
    zm = (z0 + z1) / 2
    cv.pline([(u, z0), (u, zm - .35), (u - .25, zm - .12), (u + .25, zm + .12), (u, zm + .35), (u, z1)], "e-break")


def glass_rail(cv, u0, u1, z0, h=1.1, post=1.5):
    cv.rect(u0, z0, u1, z0 + h, "e-glass-t")
    for u in frange(u0, u1 + .01, post):
        cv.line(u, z0, u, z0 + h, "e-mull")
    cv.line(u0, z0 + h, u1, z0 + h, "e-out")
    for u in frange(u0 + .3, u1 - .3, post * 2):
        cv.line(u, z0 + .25, u + .4, z0 + h - .2, "e-hl")


def parasol_e(cv, u, z, r=1.5, h=2.4, cls="e-cream"):
    cv.line(u, z, u, z + h, "e-mull")
    top = z + h
    cv.path([("M", u - r, top - .35), ("Q", u - r * .4, top + .1, u, top + .45), ("Q", u + r * .4, top + .1, u + r, top - .35),
             ("Z",)], cls)
    for k in (-.5, 0, .5):
        cv.line(u + k * r * .2, top + .4, u + k * r, top - .3, "e-joint")
    cv.circle(u, top + .5, .06, "ink-f")


def spotlight(cv, u, z, face=-1):
    """Floodlight on a short arm, aimed down at the sign."""
    cv.line(u, z, u, z + .55, "e-mull")
    cv.line(u, z + .55, u + face * .35, z + .62, "e-mull")
    hx = u + face * .35
    cv.poly([(hx - .3, z + .5), (hx + .3, z + .62), (hx + .26, z + .82), (hx - .34, z + .7)], "e-dark")
    cv.line(hx - .28, z + .52, hx + .28, z + .63, "e-led")


def porthole(cv, u, z, r=.65):
    cv.circle(u, z, r, "e-cream")
    cv.circle(u, z, r * .74, "e-glass")
    cv.add(f'<path class="e-hl" d="M{n(cv.X(u - r * .45))} {n(cv.Y(z + r * .2))}A{n(r * .5 * abs(cv.sx))} '
           f'{n(r * .5 * abs(cv.sx))} 0 0 1 {n(cv.X(u + r * .1))} {n(cv.Y(z + r * .5))}"/>')


def fern(cv, u, z, w, h, seed=0):
    rnd = random.Random(seed)
    d = []
    for i in range(9):
        a = math.radians(25 + i * 16 + rnd.uniform(-5, 5))
        L = h * rnd.uniform(.75, 1.05)
        x0, y0 = cv.X(u), cv.Y(z)
        x1 = x0 - math.cos(a) * L * abs(cv.sx) * (w / h) * .9
        y1 = y0 - math.sin(a) * L * abs(cv.sy)
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        d.append(f"M{n(x0)} {n(y0)}Q{n(mx - 3)} {n(my - 3)} {n(x1)} {n(y1)}Q{n(mx + 2)} {n(my + 2)} {n(x0)} {n(y0)}Z")
    cv.add(f'<path class="e-fern" d="{" ".join(d)}"/>')


def wave_planter(cv, u, z, w=1.7, h=.75, seed=0, plant=True):
    if plant:
        fern(cv, u, z + h - .05, w * .55, 1.0, seed)
    cv.rect(u - w / 2, z, u + w / 2, z + h, "e-conc")
    cv.line(u - w / 2, z + h - .1, u + w / 2, z + h - .1, "e-joint")
    wave(cv, u - w * .32, u + w * .32, z + h * .5, .06, 2, "e-wave-y")
    wave(cv, u - w * .32, u + w * .32, z + h * .3, .06, 2, "e-wave-y")


def avatar_p(cv, u, z, h=1.7, seed=0):
    """Plain person silhouette (adult proportions) for scale on elevations."""
    sx = abs(cv.sx)
    x, y = cv.X(u), cv.Y(z)
    hh = h * sx
    cv.add(f'<g class="avatar"><circle cx="{n(x)}" cy="{n(y - hh * .9)}" r="{n(hh * .075)}"/>'
           f'<rect x="{n(x - hh * .1)}" y="{n(y - hh * .82)}" width="{n(hh * .2)}" height="{n(hh * .4)}" rx="{n(hh * .06)}"/>'
           f'<rect x="{n(x - hh * .085)}" y="{n(y - hh * .45)}" width="{n(hh * .075)}" height="{n(hh * .45)}" rx="{n(hh * .03)}"/>'
           f'<rect x="{n(x + hh * .01)}" y="{n(y - hh * .45)}" width="{n(hh * .075)}" height="{n(hh * .45)}" rx="{n(hh * .03)}"/></g>')


MASCOT = [
    "...O......O...",
    "..OYO....OYO..",
    "..OYYOOOOYYO..",
    ".OYYYYYYYYYYO.",
    ".OYYKYYYYKYYO.",
    "OYYYKYYYYKYYYO",
    "OYPYYYYYYYYPYO",
    "OYYYYYKKYYYYYO",
    ".OYYYYYYYYYYO.",
    "..OOYYYYYYOO..",
    "....OOOOOO....",
]


def mascot(cv, u0, z_top, px):
    """Pixel mascot (yellow cat-blob) as on the arcade sign; px = pixel size in metres."""
    cls = {"O": "e-yel2", "Y": "e-yel3", "K": "e-dark", "P": "e-pink"}
    for r, row in enumerate(MASCOT):
        for c, ch in enumerate(row):
            if ch in cls:
                u, z = u0 + c * px, z_top - (r + 1) * px
                cv.rect(u, z, u + px * 1.02, z + px * 1.02, cls[ch])


def sparkle(cv, u, z, s):
    for (a, L, cls) in [(70, 1.0, "e-pink"), (100, .8, "e-yel2"), (130, .9, "chalk-c"), (40, .7, "e-lilac")]:
        r = math.radians(a)
        cv.add(f'<line x1="{n(cv.X(u + math.cos(r) * s * .5))}" y1="{n(cv.Y(z + math.sin(r) * s * .5))}" '
               f'x2="{n(cv.X(u + math.cos(r) * s * (.5 + L)))}" y2="{n(cv.Y(z + math.sin(r) * s * (.5 + L)))}" '
               f'style="stroke:var(--{ {"e-pink": "f-pink", "e-yel2": "f-yel-2", "chalk-c": "chalk-c", "e-lilac": "f-lilac"}[cls]});'
               f'stroke-width:{n(s * .28 * abs(cv.sx))}px;stroke-linecap:round"/>')


def lamp_post(cv, u, z, h=6.2, banner=None, signs=None):
    """Street lamp with an optional pixel banner and finger signs (BEACH / SHOPS / ...)."""
    cv.rect(u - .09, z, u + .09, z + h, "e-dark")
    cv.rect(u - .16, z, u + .16, z + .5, "e-dark")
    cv.line(u, z + h, u - .7, z + h + .1, "e-mull-t")
    cv.poly([(u - .95, z + h - .05), (u - .45, z + h - .05), (u - .52, z + h + .15), (u - .88, z + h + .15)], "e-dark")
    if banner:
        b0, b1, txt = banner
        cv.rect(u + .1, b0, u + 1.05, b1, "e-poster")
        cv.line(u + .1, b1, u + 1.15, b1, "e-mull-t")
        cv.line(u + .1, b0, u + 1.15, b0, "e-mull-t")
        for i, line in enumerate(txt):
            stext(cv, u + .58, b1 - .55 - i * .32, line, .2, weight=700, family="var(--f-cond)")
        wave(cv, u + .25, u + .95, b0 + .3, .05, 2, "e-led")
    if signs:
        for i, (lab, d) in enumerate(signs):
            zc = z + 3.5 - i * .5
            a0, a1 = (u + .1, u + 1.6) if d > 0 else (u - 1.6, u - .1)
            tip = a1 + .25 if d > 0 else a0 - .25
            pts = [(a0, zc - .17), (a1, zc - .17), (tip, zc), (a1, zc + .17), (a0, zc + .17)] if d > 0 else \
                  [(a1, zc - .17), (a0, zc - .17), (tip, zc), (a0, zc + .17), (a1, zc + .17)]
            cv.poly(pts, "e-navy")
            stext(cv, (a0 + a1) / 2, zc - .08, lab, .17, weight=700, family="var(--f-cond)")


def bench_e(cv, u, z, L=1.8):
    cv.rect(u - L / 2, z + .42, u + L / 2, z + .48, "e-wood")
    cv.rect(u - L / 2, z + .62, u + L / 2, z + .8, "e-wood")
    for k in (-1, 1):
        cv.rect(u + k * (L / 2 - .15) - .04, z, u + k * (L / 2 - .15) + .04, z + .8, "e-dark")


def aframe(cv, u, z, lines):
    cv.poly([(u - .45, z), (u - .3, z + 1.05), (u + .3, z + 1.05), (u + .45, z)], "e-wood")
    cv.poly([(u - .36, z + .15), (u - .25, z + .95), (u + .25, z + .95), (u + .36, z + .15)], "e-dark")
    for i, s in enumerate(lines):
        stext(cv, u, z + .75 - i * .2, s, .12, weight=600, family="var(--f-cond)")


def shrubs_e(cv, u0, u1, z, h=.7, seed=0):
    rnd = random.Random(seed)
    u = u0
    while u < u1:
        r = rnd.uniform(.3, .5) * h / .7
        cv.add(f'<ellipse class="shrub-o" cx="{n(cv.X(u + r))}" cy="{n(cv.Y(z + r * .8))}" rx="{n(r * abs(cv.sx))}" '
               f'ry="{n(r * .9 * abs(cv.sy))}"/>')
        u += r * 1.3


def glazing(cv, u0, z0, u1, z1, panels, frame="e-mull-t", inner="e-glass", hl=True):
    cv.rect(u0, z0, u1, z1, inner)
    w = (u1 - u0) / panels
    for i in range(1, panels):
        cv.line(u0 + i * w, z0, u0 + i * w, z1, frame)
    cv.rect(u0, z0, u1, z1, "", ' style="fill:none;stroke:var(--f-dark);stroke-width:1.8"')
    if hl:
        for i in range(panels):
            a = u0 + i * w
            cv.line(a + w * .2, z0 + (z1 - z0) * .25, a + w * .55, z0 + (z1 - z0) * .75, "e-hl")


def interior(cv, u0, z0, u1, z1, seed=0):
    """Lit arcade interior behind glass: glow, cabinets, LED strips."""
    rnd = random.Random(seed)
    cv.rect(u0, z0, u1, z1, "e-glow")
    for z, cls in ((z1 - .35, "e-led-p"), (z1 - .7, "e-led-c")):
        cv.line(u0 + .1, z, u1 - .1, z, cls)
    u = u0 + .25
    while u < u1 - .9:
        w = rnd.uniform(.62, .8)
        h = rnd.uniform(1.75, 2.05)
        cv.rect(u, z0, u + w, z0 + h, ("e-pink-o", "e-cream", "e-mint", "e-cream")[int(u * 7) % 4])
        cv.rect(u + .1, z0 + h * .55, u + w - .1, z0 + h * .85, ("e-blue", "e-dark", "e-blue")[int(u * 3) % 3])
        cv.rect(u + .08, z0 + h * .9, u + w - .08, z0 + h - .04, "e-yel3")
        u += w + rnd.uniform(.12, .4)


def level_tags(cv, u, tags):
    for z, lab in tags:
        etag(cv, u, z, lab, anchor="end")


def panel_title(cv, u, z, no, title, sub):
    x, y = cv.X(u), cv.Y(z)
    cv.add(f'<circle class="bubble" cx="{n(x + 11)}" cy="{n(y - 4)}" r="11"/>'
           f'<text class="t-lbl" x="{n(x + 11)}" y="{n(y - .5)}" text-anchor="middle">{esc(no)}</text>'
           f'<text class="t-head" x="{n(x + 28)}" y="{n(y)}">{esc(title)}</text>'
           f'<text class="t-sm" x="{n(x + 28)}" y="{n(y + 12)}">{esc(sub)}</text>')


def scale_bar(cv, u, z, m=5):
    for i in range(m):
        cv.rect(u + i, z, u + i + 1, z + .18 * 12 / abs(cv.sx), "ink-f" if i % 2 == 0 else "prop")
    cv.text(u, z - .5 * 12 / abs(cv.sx) - .2, "0", "t-sm")
    cv.text(u + m, z - .5 * 12 / abs(cv.sx) - .2, f"{m} m", "t-sm")


def note(cv, u, z, pu, pz, label, anchor="start"):
    cv.line(pu, pz, u, z, "ln-m")
    cv.add(f'<circle class="ink-f" cx="{n(cv.X(pu))}" cy="{n(cv.Y(pz))}" r="1.8"/>')
    off = 3 if anchor == "start" else -3
    cv.add(f'<text class="e-key halo" x="{n(cv.X(u) + off)}" y="{n(cv.Y(z) + 3)}" text-anchor="{anchor}">{esc(label)}</text>')


def defs_e(p):
    return (f'<defs><pattern id="{p}-earth" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            f'<path class="pat-s" d="M0 0V6"/><circle class="pat-d" cx="3" cy="3" r=".5"/></pattern>'
            f'<pattern id="{p}-clad" width="10" height="10" patternUnits="userSpaceOnUse"><path class="e-joint" d="M0 10H10"/></pattern>'
            f'<pattern id="{p}-slat" width="4" height="10" patternUnits="userSpaceOnUse"><path class="e-joint" d="M2 0V10"/></pattern>'
            f'<pattern id="{p}-awn-y" width="12" height="10" patternUnits="userSpaceOnUse"><rect width="6" height="10" class="e-yel3"/>'
            f'<rect x="6" width="6" height="10" class="e-white"/></pattern>'
            f'<pattern id="{p}-awn-p" width="12" height="10" patternUnits="userSpaceOnUse"><rect width="6" height="10" class="e-pink"/>'
            f'<rect x="6" width="6" height="10" class="e-white"/></pattern>'
            f'<pattern id="{p}-awn-c" width="12" height="10" patternUnits="userSpaceOnUse"><rect width="6" height="10" class="chalk-c"/>'
            f'<rect x="6" width="6" height="10" class="e-white"/></pattern>'
            f'<pattern id="{p}-thatch" width="5" height="6" patternUnits="userSpaceOnUse"><path class="e-joint" d="M0 6L2.5 0M2.5 6L5 0"/></pattern>'
            f'<marker id="{p}-arrk" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="4.5" markerHeight="4.5" orient="auto-start-reverse">'
            f'<path class="ink-f" d="M0 0 10 5 0 10z"/></marker></defs>')


def awning(cv, u0, u1, z_top, drop, pat, valance=.3, scallop=True, text=None, text_fill="var(--f-dark)"):
    """Awning seen from the front: sloped canvas face plus a scalloped valance."""
    cv.rect(u0, z_top - drop, u1, z_top, "", f' fill="url(#ce-{pat})"')
    cv.rect(u0, z_top - drop, u1, z_top, "e-out")
    zv = z_top - drop
    if scallop:
        k = max(2, int((u1 - u0) / .6))
        w = (u1 - u0) / k
        d = [("M", u0, zv)]
        for i in range(k):
            d += [("Q", u0 + (i + .5) * w, zv - valance * 1.6, u0 + (i + 1) * w, zv)]
        cv.path(d + [("Z",)], "", f' fill="url(#ce-{pat})"')
        cv.path(d, "e-out")
    cv.rect(u0, zv - .35, u1, zv - .05, "e-shadow")
    if text:
        stext(cv, (u0 + u1) / 2, z_top - drop * .62, text, drop * .32, fill=text_fill, weight=700, family="var(--f-cond)", ls=.04)


# ================================================================== A-501 ARCADE
Z_PL, Z_FFL, Z_ROOF, Z_PAR, Z_RAIL = 3.60, 4.05, 9.60, 10.20, 11.30
CTR = 13.33          # controller frame centre on the east face (door centre from the plan)


def lane_z(y_m):
    """West lane level at plan Y (m): +8.40 at the street falling to +3.15 at the promenade (stepped)."""
    py = 75 + 6 * y_m
    return 8.40 - (py - 135) * 5.25 / 497


def lane_profile(u_of_y, y0, y1, step=1.2):
    """Stepped lane profile between plan Y y0..y1 mapped to elevation u."""
    pts = []
    y = y0
    while (y < y1) if y1 > y0 else (y > y1):
        z = lane_z(y)
        yn = y + (step if y1 > y0 else -step)
        if (y1 > y0 and yn > y1) or (y1 < y0 and yn < y1):
            yn = y1
        pts += [(u_of_y(y), z), (u_of_y(yn), z)]
        y = yn
    return pts


def arcade_controller(cv, c=CTR):
    """Game-controller sign: yellow body, cream grips with D-pad and buttons, ARCADE band."""
    # shadow cast by the 0.6 m projection
    rrect(cv, c - 6.75, 7.05, c + 7.4, 10.4, .7, "e-shadow")
    rrect(cv, c - 7.1, 7.3, c + 7.1, 10.65, .8, "e-yel", top_only=True)
    cv.rect(c - 7.1, 7.3, c + 7.1, 7.48, "e-yel2")
    # middle band
    rrect(cv, c - 3.05, 7.65, c + 3.05, 10.5, .5, "e-yel3", top_only=True)
    stext(cv, c - .45, 9.2, "ARCADE", 1.05, fill="var(--f-white)", weight=800, stroke="var(--f-lilac)", sw=4, ls=.02)
    rrect(cv, c - 2.4, 8.2, c + 1.55, 8.78, .29, "e-dark")
    stext(cv, c - .42, 8.33, "ゲームセンター", .34, fill="var(--f-white)", weight=700, family="var(--f-body)")
    mascot(cv, c + 1.75, 9.95, .088)
    sparkle(cv, c + 2.0, 10.0, .35)
    # left grip with D-pad, poster frame below
    rrect(cv, c - 6.8, 7.42, c - 3.05, 11.0, .75, "e-cream", top_only=True)
    cv.rect(c - 6.8, 7.42, c - 3.05, 7.62, "e-cream2")
    rrect(cv, c - 6.25, 10.38, c - 5.55, 10.56, .06, "e-steel")
    du, dz, a, t = c - 4.95, 9.12, .88, .3
    rrect(cv, du - a - .08, dz - t - .08, du + a - .08, dz + t - .08, .1, "e-shadow")
    rrect(cv, du - t - .08, dz - a - .08, du + t - .08, dz + a - .08, .1, "e-shadow")
    rrect(cv, du - a, dz - t, du + a, dz + t, .1, "e-dark")
    rrect(cv, du - t, dz - a, du + t, dz + a, .1, "e-dark")
    cv.circle(du, dz, .14, "", ' style="fill:var(--f-steel)"')
    for (ox, oz) in ((0, .62), (0, -.62), (.62, 0), (-.62, 0)):
        cv.circle(du + ox, dz + oz, .05, "", ' style="fill:var(--f-steel)"')
    # right grip with buttons
    rrect(cv, c + 3.05, 7.42, c + 6.8, 11.0, .75, "e-cream", top_only=True)
    cv.rect(c + 3.05, 7.42, c + 6.8, 7.62, "e-cream2")
    rrect(cv, c + 3.55, 10.42, c + 4.3, 10.6, .06, "e-steel")
    for (bu, bz, cls) in ((c + 4.2, 9.95, "e-blue"), (c + 5.5, 9.3, "e-red"), (c + 4.25, 8.55, "e-green")):
        cv.circle(bu + .06, bz - .07, .47, "e-shadow")
        cv.circle(bu, bz, .45, cls)
        cv.add(f'<path class="e-hl" d="M{n(cv.X(bu - .28))} {n(cv.Y(bz + .1))}A{n(.3 * abs(cv.sx))} {n(.3 * abs(cv.sx))} 0 0 1 '
               f'{n(cv.X(bu + .05))} {n(cv.Y(bz + .3))}"/>')


def arcade_front_lower(cv, c=CTR):
    """Entrance bay: pillars, glazing with lit interior, posters, steps."""
    # door opening and interior
    interior(cv, c - 2.5, Z_FFL, c + 2.5, 7.2, seed=5)
    cv.rect(c - .3, Z_FFL, c + .3, 6.9, "e-yel")
    stext(cv, c, 6.25, "PLAY", .16, fill="var(--f-dark)", weight=700, family="var(--f-cond)")
    stext(cv, c, 5.98, "MEET", .16, fill="var(--f-dark)", weight=700, family="var(--f-cond)")
    stext(cv, c, 5.71, "ENJOY", .16, fill="var(--f-dark)", weight=700, family="var(--f-cond)")
    avatar_p(cv, c - .55, Z_FFL + .05, 1.72, 1)
    avatar_p(cv, c + .45, Z_FFL + .05, 1.62, 2)
    glazing(cv, c - 2.5, Z_FFL, c + 2.5, 7.2, 4, inner="e-glass-t")
    cv.line(c, Z_FFL, c, 7.2, "e-mull-t")
    # pillars with LED strips and lintel
    for (a, b) in ((c - 3.05, c - 2.5), (c + 2.5, c + 3.05)):
        cv.rect(a, Z_FFL, b, 7.65, "e-yel")
        cv.line((a + b) / 2, Z_FFL + .3, (a + b) / 2, 7.2, "e-led")
    cv.rect(c - 2.5, 7.2, c + 2.5, 7.65, "e-yel")
    cv.line(c - 2.2, 7.42, c + 2.2, 7.42, "e-led")
    # poster panel (left)
    cv.rect(c - 6.5, Z_FFL + .1, c - 3.35, 7.42, "e-cream")
    cv.rect(c - 6.25, 4.4, c - 3.6, 7.15, "e-yel3")
    cv.rect(c - 6.25, 5.62, c - 3.6, 7.15, "e-poster")
    stext(cv, c - 4.92, 6.62, "あそぼう!", .3, fill="var(--f-white)", weight=800, family="var(--f-body)")
    mascot(cv, c - 5.55, 6.4, .1)
    for (su, sz) in ((c - 5.9, 6.0), (c - 3.95, 6.1)):
        cv.add(f'<path d="{cv.d([("M", su, sz + .12), ("L", su + .04, sz + .03), ("L", su + .13, sz), ("L", su + .04, sz - .03), ("L", su, sz - .12), ("L", su - .04, sz - .03), ("L", su - .13, sz), ("L", su - .04, sz + .03), ("Z",)])}" class="e-yel3"/>')
    for i, s in enumerate(("GAMES", "FRIENDS", "GOOD TIMES")):
        stext(cv, c - 6.0, 5.25 - i * .27, s, .17, fill="var(--f-dark)", weight=700, family="var(--f-cond)", anchor="start")
    wave(cv, c - 6.0, c - 4.3, 4.58, .05, 3, "e-wave")
    # info panel (right)
    cv.rect(c + 3.35, Z_FFL + .1, c + 6.5, 7.42, "e-cream")
    for i, s in enumerate(("SMALL", "GAMES", "BIG", "HAPPINESS")):
        stext(cv, c + 3.75, 6.2 - i * .3, s, .19, fill="var(--f-dark)", weight=700, family="var(--f-cond)", anchor="start")
    wave(cv, c + 3.75, c + 5.2, 4.75, .05, 3, "e-wave")
    for k in range(3):
        cv.rect(c + 4.4, 6.75 + k * .14, c + 5.6, 6.8 + k * .14, "e-dark")
    # steps across the frame (3R x 0.15)
    cv.rect(c - 10.3, Z_PL, c + 10.3, Z_FFL, "e-conc")
    for k in (1, 2):
        cv.line(c - 10.3 + k * .12, Z_PL + k * .15, c + 10.3 - k * .12, Z_PL + k * .15, "e-mull")


def arcade_east():
    p = "ce"
    sx = 24.0
    cv = Cv(sx, -sx, 140 + 6.6 * sx, 360, 0, Z_PL)
    A = cv.add
    # sky band
    cv.rect(-6.6, Z_PL, 30.2, 13.4, "e-sky")
    # beyond: café roof and terrace parasol (south, set back 10.8 m)
    cv.rect(-6.6, Z_PL, -3.33, 8.2, "beyond")
    cv.rect(-6.6, 7.8, -3.33, 8.2, "", ' style="fill:var(--f-yel);opacity:.6"')
    break_line(cv, -6.6, Z_PL, 8.2)
    cv.text(-5.0, 8.55, "CAFÉ beyond", "t-sm halo")
    # beyond: roof-terrace parasols behind the rail
    for (u, cls) in ((3.0, "e-cream"), (9.0, "e-cream"), (22.0, "e-cream"), (25.4, "e-cream")):
        parasol_e(cv, u, Z_ROOF, 1.45, 2.35, cls)
    glass_rail(cv, 0, 27.08, Z_PAR, Z_RAIL - Z_PAR)
    # fashion shop (north, same face line) - stub
    cv.rect(27.08, Z_PL, 30.2, 13.2, "e-wall")
    cv.rect(27.08, 8.1, 30.2, 8.4, "e-coral")
    glazing(cv, 27.6, Z_PL, 30.2, 7.4, 2)
    glazing(cv, 27.6, 9.0, 30.2, 12.0, 2)
    cv.rect(27.08, 12.6, 30.2, 13.2, "e-coral")
    break_line(cv, 30.2, Z_PL, 13.2)
    cv.text(28.7, 13.55, "FASHION & GOODS (A-502)", "t-sm halo")
    # main yellow body
    cv.rect(0, Z_PL, 27.08, Z_PAR, "e-yel")
    cv.rect(0, Z_PL, 27.08, Z_PAR, "", ' fill="url(#ce-clad)"')
    cv.rect(0, 9.72, 27.08, 9.92, "e-pink")
    cv.rect(0, Z_PAR - .12, 27.08, Z_PAR, "e-dark")
    for (a, b) in ((0, .55), (26.53, 27.08)):
        cv.rect(a, Z_PL, b, Z_PAR, "e-yel2")
    cv.rect(0, Z_PL, 27.08, Z_FFL, "e-conc")
    # outer bays: portholes and wave planters
    for u in (2.1, 4.4, 22.3, 24.6):
        porthole(cv, u, 8.55, .62)
    for u in (2.1, 4.4, 22.3, 24.6):
        cv.rect(u - .7, 5.0, u + .7, 6.6, "e-yel2")
        cv.rect(u - .55, 5.15, u + .55, 6.45, "e-glass")
        cv.line(u - .3, 5.4, u + .1, 6.2, "e-hl")
    # spotlights on the parapet, aimed down at the sign
    for (u, f) in ((7.0, 1), (10.6, 1), (16.0, -1), (19.6, -1)):
        spotlight(cv, u, Z_PAR + .45, f)
    arcade_controller(cv)
    arcade_front_lower(cv)
    # strip annex end (prize corner), south, same face line
    cv.rect(-3.33, Z_PL, 0, 7.2, "e-yel")
    cv.rect(-3.33, 6.9, 0, 7.2, "e-dark")
    glazing(cv, -3.0, Z_PL, -.3, 6.1, 2, inner="e-glow")
    for (a, cls) in ((-2.85, "e-pink-o"), (-1.55, "e-mint")):
        cv.rect(a, Z_PL, a + 1.0, Z_PL + 1.6, cls)
    glazing(cv, -3.0, Z_PL, -.3, 6.1, 2, inner="e-glass-t")
    rrect(cv, -3.1, 6.25, -.23, 6.8, .2, "e-pink-o")
    stext(cv, -1.665, 6.38, "PRIZE", .3, fill="var(--f-white)", weight=800)
    # foreground: planters, lamp + signposts, A-frame, bench
    for (u, sd) in ((5.5, 1), (21.2, 2), (25.5, 3)):
        wave_planter(cv, u, Z_FFL if 3.1 < u < 23.5 else Z_PL, 1.6, .72, sd)
    lamp_post(cv, 26.4, Z_PL, 6.3, banner=(7.3, 9.4, ("GOOD", "GAMES", "BRIGHT", "DAYS")),
              signs=(("BEACH", -1), ("SHOPS", -1), ("FOOD", -1), ("PHOTO SPOT", -1)))
    aframe(cv, -4.6, Z_PL, ("PLAY", "EAT", "CHILL"))
    bench_e(cv, 1.1, Z_PL, 1.8)
    avatar_p(cv, -5.6, Z_PL, 1.66, 4)
    ground(cv, -6.6, 30.2, Z_PL, .55)
    # dims and tags
    hdim(cv, 0, 27.08, 12.45, "27.08 ARCADE FRONT", ext=Z_PAR)
    hdim(cv, CTR - 2.5, CTR + 2.5, 2.75, "5.00 DOORS")
    hdim(cv, CTR - 7.1, CTR + 7.1, 2.25, "14.20 CONTROLLER SIGN")
    vdim(cv, 30.6, Z_PL, Z_PAR, "6.60", side=1)
    vdim(cv, 30.6, Z_PAR, Z_RAIL, "1.10", side=1)
    level_tags(cv, -6.75, [(Z_PL, "+3.60 PLAZA"), (Z_FFL, "+4.05 FFL"), (Z_ROOF, "+9.60 ROOF TERRACE"),
                           (Z_PAR, "+10.20 PARAPET"), (Z_RAIL, "+11.30 RAIL")])
    note(cv, 1.0, 12.9, CTR - 4.95, 9.9, "D-pad grip · cream GRC panels", "start")
    note(cv, 22.5, 12.9, CTR + 5.0, 10.5, "Buttons grip · blue / red / green, Ø0.90 domes", "start")
    note(cv, 9.3, 12.0, CTR - 1.0, 10.15, "ARCADE · ゲームセンター · pixel mascot", "start")
    note(cv, -6.3, 11.3, 1.8, 10.8, "Glass rail 1.10 m on 0.60 m parapet", "start")
    note(cv, 17.2, 11.9, 16.1, 11.0, "Floodlights on the parapet", "start")
    panel_title(cv, -6.6, 1.35, "1", "EAST ELEVATION · FRONT TO THE PLAZA", "looking west · 1:100 at sheet size · steps 3R × 0.15, treads 0.40")
    return cv, p


def arcade_south():
    sx = 14.0
    cv = Cv(sx, -sx, 150 - 4.6 * sx, 640, 0, Z_PL)
    # u = plan X (m); left = west (lane), right = east (plaza)
    u0, u1 = 4.6, 52.5
    cv.rect(u0, Z_PL, u1, 13.0, "e-sky")
    for u in (18.0, 26.0, 34.5, 42.0):
        parasol_e(cv, u, Z_ROOF, 1.45, 2.35)
    glass_rail(cv, 13.75, 47.92, Z_PAR, Z_RAIL - Z_PAR)
    # fashion shop beyond (north, taller)
    cv.rect(13.75, Z_PAR, 47.92, 13.2, "beyond")
    cv.text(30.8, 12.55, "FASHION & GOODS beyond · +13.20", "t-sm halo")
    cv.rect(13.75, Z_PL, 47.92, Z_PAR, "e-yel")
    cv.rect(13.75, Z_PL, 47.92, Z_PAR, "", ' fill="url(#ce-clad)"')
    cv.rect(13.75, 9.72, 47.92, 9.92, "e-pink")
    cv.rect(13.75, Z_PAR - .12, 47.92, Z_PAR, "e-dark")
    for u in frange(16.6, 45.5, 3.0):
        porthole(cv, u, 8.55, .66)
    # controller profile and steps at the east end (0.6 m proud)
    rrect(cv, 47.92, 7.3, 48.52, 11.0, .2, "e-cream", top_only=True)
    cv.rect(47.92, 7.3, 48.52, 7.5, "e-cream2")
    for (u, f) in ((47.6, 1),):
        spotlight(cv, u, Z_PAR + .45, f)
    for k in range(3):
        cv.rect(47.92 + k * .4, Z_PL, 49.12, Z_PL + (3 - k) * .15, "e-conc")
    # strip annex in front (south face), café ghosted in front of its west part
    cv.rect(13.75, Z_PL, 47.92, 7.2, "e-yel")
    cv.rect(13.75, 6.9, 47.92, 7.2, "e-dark")
    for (a, b, cls, lab) in ((37.6, 41.2, "e-glow", "PRIZE CORNER"), (41.7, 45.3, "e-glow", "VENDING"), (45.6, 47.6, "e-glass", "")):
        glazing(cv, a, Z_PL + .4, b, 6.2, 2, inner=cls)
        if lab:
            stext(cv, (a + b) / 2, 6.45, lab, .22, fill="var(--f-dark)", weight=700, family="var(--f-cond)")
    for u in frange(38.0, 44.8, 1.1):
        cv.rect(u, Z_PL + .4, u + .8, Z_PL + 2.0, ("e-pink-o", "e-mint", "e-cream")[int(u) % 3])
    for u in frange(15.5, 36.0, 4.2):
        cv.rect(u, 5.6, u + 2.4, 6.3, "e-glass")
    cv.rect(13.75, Z_PL, 37.08, 8.2, "e-ghost")
    cv.line(13.75, 7.8, 37.08, 7.8, "e-ghost")
    cv.text(25.4, 7.25, "CAFÉ in front (dashed, see A-502)", "t-sm halo")
    # lane on the west
    prof = [(u0, lane_z(65.0)), (13.75, lane_z(65.0))]
    ground(cv, u0, 13.75, 0, .6, prof)
    ground(cv, 13.75, u1, Z_PL, .55, [(13.75, Z_PL), (u1, Z_PL)])
    cv.line(13.75, Z_PL, 13.75, lane_z(65.0), "e-ground")
    tree_elev(cv, 9.0, lane_z(65.0), 6.5, 5.2, 31)
    avatar_p(cv, 50.4, Z_PL, 1.7, 5)
    hdim(cv, 13.75, 47.92, 12.1, "34.17", ext=Z_PAR)
    level_tags(cv, u0 - .2, [(Z_PL, "+3.60"), (7.2, "+7.20 STRIP ROOF"), (Z_ROOF, "+9.60"), (Z_PAR, "+10.20")])
    note(cv, 30.0, 11.65, 31.6, 8.9, "Porthole windows Ø1.32 at 3.0 m centres", "start")
    panel_title(cv, u0, 1.5, "2", "SOUTH ELEVATION · SIDE", "looking north · prize & vending strip in front · café dashed")
    return cv


def arcade_west():
    sx = 14.0
    cv = Cv(sx, -sx, 150 + 4.0 * sx, 930, 0, Z_PL)
    # u = plan Y - 37.92: left = north (fashion), right = south (strip, café)
    def U(y):
        return y - 37.92
    ua, ub = -4.0, 36.0
    cv.rect(ua, Z_PL, ub, 13.6, "e-sky")
    for u in (4.0, 13.0, 22.0):
        parasol_e(cv, u, Z_ROOF, 1.45, 2.35)
    glass_rail(cv, 0, 27.08, Z_PAR, Z_RAIL - Z_PAR)
    # fashion (north) stub, taller
    cv.rect(-4.0, 6.0, 0, 13.2, "e-wall")
    glazing(cv, -3.5, 9.0, -.5, 12.0, 2)
    cv.rect(-4.0, 12.6, 0, 13.2, "e-coral")
    break_line(cv, -4.0, 6.0, 13.2)
    # back wall (service face)
    zl = lane_z(37.92)
    cv.rect(0, 4.4, 27.08, Z_PAR, "e-yel")
    cv.rect(0, 4.4, 27.08, Z_PAR, "", ' fill="url(#ce-clad)"')
    cv.rect(0, 9.72, 27.08, 9.92, "e-pink")
    cv.rect(0, Z_PAR - .12, 27.08, Z_PAR, "e-dark")
    for u in (.4, 9.2, 18.2, 26.7):
        cv.rect(u - .07, 4.4, u + .07, Z_PAR - .1, "e-steel")
    for u in (4.5, 13.5, 22.0):
        cv.rect(u - .9, 8.3, u + .9, 9.1, "e-steel")
        for k in range(4):
            cv.line(u - .8, 8.42 + k * .18, u + .8, 8.42 + k * .18, "e-mull")
    # fire exit at the south end, service door at the north end
    yz = lane_z(62.5)
    cv.rect(U(62.0), yz, U(64.0), yz + 2.4, "e-steel")
    cv.line(U(63.0), yz, U(63.0), yz + 2.4, "e-mull")
    cv.rect(U(62.0) - .2, yz + 2.4, U(64.0) + .2, yz + 2.6, "e-dark")
    cv.text(U(63.0), yz + 2.95, "FIRE EXIT", "t-sm halo")
    yz2 = lane_z(42.0)
    cv.rect(U(41.4), yz2, U(42.6), yz2 + 2.2, "e-steel")
    cv.text(U(42.0), yz2 + 2.55, "STAFF", "t-sm halo")
    # AC units on the parapet line, bins
    for u in (6.5, 8.0, 15.5):
        cv.rect(u - .6, Z_PAR, u + .6, Z_PAR + .7, "e-steel")
        cv.circle(u, Z_PAR + .35, .25, "e-joint")
    for u in (U(45.5), U(46.6)):
        cv.rect(u - .45, lane_z(46) , u + .45, lane_z(46) + 1.1, "e-mint")
    # strip annex + café (south) stub
    cv.rect(27.08, lane_z(66.5), 30.41, 7.2, "e-yel")
    cv.rect(27.08, 6.9, 30.41, 7.2, "e-dark")
    cv.rect(30.41, lane_z(72.0), 36.0, 8.2, "e-cream")
    cv.rect(30.41, 7.8, 36.0, 8.2, "e-yel")
    cv.rect(31.2, 6.3, 33.0, 7.2, "e-glass")
    break_line(cv, 36.0, lane_z(72.0), 8.2)
    cv.text(33.2, 8.6, "CAFÉ (A-502)", "t-sm halo")
    prof = lane_profile(U, 33.92, 73.92, 1.2)
    ground(cv, ua, ub, 0, .6, prof)
    avatar_p(cv, U(52.0), lane_z(52.0), 1.7, 6)
    tree_elev(cv, U(70.5), lane_z(70.5), 6.0, 5.0, 41)
    hdim(cv, 0, 27.08, 12.4, "27.08", ext=Z_PAR)
    level_tags(cv, ua - .2, [(lane_z(37.92), f"+{lane_z(37.92):.2f} LANE"), (lane_z(65.0), f"+{lane_z(65.0):.2f}"),
                             (Z_PAR, "+10.20")])
    note(cv, 1.0, 12.0, 6.5, Z_PAR + .7, "Condensers screened behind the rail", "start")
    note(cv, 17.0, 6.2, U(63.0) - .9, yz + 1.2, "Fire exit at lane level, 6R down inside", "start")
    panel_title(cv, ua, 2.0, "3", "WEST ELEVATION · BACK TO THE LANE", "looking east · lane steps down +6.63 → +4.91 along the wall")
    return cv


def sheet_a501():
    W, H = 1100, 1010
    root = Cv(1, 1, 0, 0)
    root.add(defs_e("ce"))
    root.add(f'<rect class="sheet-bg" width="{W}" height="{H}"/>')
    title_strip(root, 24, 30, "A-501", "ARCADE · ELEVATIONS (FRONT, SIDE, BACK)",
                "Front from the reference facade image · levels from L-202 · 24 px = 1 m (1) and 14 px = 1 m (2, 3)")
    e, _ = arcade_east()
    s = arcade_south()
    w = arcade_west()
    key = colour_key(root, 850, 760, [("e-yel", "Arcade yellow · fibre-cement panels"), ("e-cream", "Cream GRC · controller grips"),
                                      ("e-dark", "Graphite · D-pad, frames, coping"), ("e-blue", "Button blue"),
                                      ("e-red", "Button red"), ("e-green", "Button green"), ("e-pink", "Pink trim band"),
                                      ("e-glass", "Clear glazing"), ("e-glow", "Lit interior"), ("e-conc", "Precast steps, planters")])
    root.add(f'<rect class="frame" x="12" y="50" width="{W - 24}" height="{H - 62}"/>')
    return "\n".join([root.svg(), e.svg(), s.svg(), w.svg(), key]), W, H


def colour_key(root, x, y, rows):
    out = [f'<text class="t-head" x="{x}" y="{y}">MATERIALS</text>']
    for i, (cls, lab) in enumerate(rows):
        yy = y + 14 + i * 19
        out.append(f'<rect class="{cls}" x="{x}" y="{yy}" width="22" height="13" style="stroke:var(--ink);stroke-width:.7"/>'
                   f'<text class="e-key" x="{x + 30}" y="{yy + 10}">{esc(lab)}</text>')
    return "\n".join(out)
