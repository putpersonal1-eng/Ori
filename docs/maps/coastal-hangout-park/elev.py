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
        cv.rect(u + .1, b0, u + 1.25, b1, "e-poster")
        cv.line(u + .1, b1, u + 1.35, b1, "e-mull-t")
        cv.line(u + .1, b0, u + 1.35, b0, "e-mull-t")
        for i, line in enumerate(txt):
            stext(cv, u + .68, b1 - .45 - i * .3, line, .15, weight=700, family="var(--f-cond)")
        wave(cv, u + .3, u + 1.05, b0 + .25, .05, 2, "e-led")
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
    rrect(cv, c - 3.75, 7.65, c + 3.75, 10.5, .5, "e-yel3", top_only=True)
    stext(cv, c - .6, 9.25, "ARCADE", .82, fill="var(--f-white)", weight=800, stroke="var(--f-lilac)", sw=3.5)
    rrect(cv, c - 2.6, 8.2, c + 1.4, 8.78, .29, "e-dark")
    stext(cv, c - .6, 8.33, "ゲームセンター", .34, fill="var(--f-white)", weight=700, family="var(--f-body)")
    mascot(cv, c + 2.25, 9.85, .085)
    sparkle(cv, c + 2.5, 9.95, .32)
    # left grip with D-pad, poster frame below
    rrect(cv, c - 7.0, 7.42, c - 3.75, 11.0, .75, "e-cream", top_only=True)
    cv.rect(c - 7.0, 7.42, c - 3.75, 7.62, "e-cream2")
    rrect(cv, c - 6.55, 10.38, c - 5.85, 10.56, .06, "e-steel")
    du, dz, a, t = c - 5.35, 9.12, .88, .3
    rrect(cv, du - a - .08, dz - t - .08, du + a - .08, dz + t - .08, .1, "e-shadow")
    rrect(cv, du - t - .08, dz - a - .08, du + t - .08, dz + a - .08, .1, "e-shadow")
    rrect(cv, du - a, dz - t, du + a, dz + t, .1, "e-dark")
    rrect(cv, du - t, dz - a, du + t, dz + a, .1, "e-dark")
    cv.circle(du, dz, .14, "", ' style="fill:var(--f-steel)"')
    for (ox, oz) in ((0, .62), (0, -.62), (.62, 0), (-.62, 0)):
        cv.circle(du + ox, dz + oz, .05, "", ' style="fill:var(--f-steel)"')
    # right grip with buttons
    rrect(cv, c + 3.75, 7.42, c + 7.0, 11.0, .75, "e-cream", top_only=True)
    cv.rect(c + 3.75, 7.42, c + 7.0, 7.62, "e-cream2")
    rrect(cv, c + 4.2, 10.42, c + 4.95, 10.6, .06, "e-steel")
    for (bu, bz, cls) in ((c + 4.75, 9.95, "e-blue"), (c + 6.0, 9.3, "e-red"), (c + 4.8, 8.55, "e-green")):
        cv.circle(bu + .06, bz - .07, .47, "e-shadow")
        cv.circle(bu, bz, .45, cls)
        cv.add(f'<path class="e-hl" d="M{n(cv.X(bu - .28))} {n(cv.Y(bz + .1))}A{n(.3 * abs(cv.sx))} {n(.3 * abs(cv.sx))} 0 0 1 '
               f'{n(cv.X(bu + .05))} {n(cv.Y(bz + .3))}"/>')


def arcade_front_lower(cv, c=CTR):
    """Entrance bay: pillars, glazing with lit interior, posters, steps."""
    # door opening and interior
    interior(cv, c - 2.5, Z_FFL, c + 2.5, 7.2, seed=5)
    cv.rect(c + .2, Z_FFL, c + 1.05, 6.9, "e-yel")
    for i, w_ in enumerate(("PLAY", "MEET", "ENJOY")):
        stext(cv, c + .625, 6.3 - i * .3, w_, .17, fill="var(--f-dark)", weight=700, family="var(--f-cond)")
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
    for (a, b) in ((c - 3.75, c - 3.05), (c + 3.05, c + 3.75)):
        cv.rect(a, Z_FFL, b, 7.42, "e-yel2")
    # poster panel (left)
    cv.rect(c - 6.75, Z_FFL + .1, c - 4.0, 7.42, "e-cream")
    cv.rect(c - 6.5, 4.4, c - 4.25, 7.15, "e-yel3")
    cv.rect(c - 6.5, 5.62, c - 4.25, 7.15, "e-poster")
    stext(cv, c - 5.37, 6.65, "あそぼう!", .28, fill="var(--f-white)", weight=800, family="var(--f-body)")
    mascot(cv, c - 5.97, 6.42, .086)
    for (su, sz) in ((c - 6.25, 6.0), (c - 4.5, 6.1)):
        cv.add(f'<path d="{cv.d([("M", su, sz + .12), ("L", su + .04, sz + .03), ("L", su + .13, sz), ("L", su + .04, sz - .03), ("L", su, sz - .12), ("L", su - .04, sz - .03), ("L", su - .13, sz), ("L", su - .04, sz + .03), ("Z",)])}" class="e-yel3"/>')
    for i, s in enumerate(("GAMES", "FRIENDS", "GOOD TIMES")):
        stext(cv, c - 6.3, 5.25 - i * .27, s, .17, fill="var(--f-dark)", weight=700, family="var(--f-cond)", anchor="start")
    wave(cv, c - 6.3, c - 4.6, 4.58, .05, 3, "e-wave")
    # info panel (right)
    cv.rect(c + 4.0, Z_FFL + .1, c + 6.75, 7.42, "e-cream")
    for i, s in enumerate(("SMALL", "GAMES", "BIG", "HAPPINESS")):
        stext(cv, c + 4.35, 6.2 - i * .3, s, .19, fill="var(--f-dark)", weight=700, family="var(--f-cond)", anchor="start")
    wave(cv, c + 4.35, c + 5.8, 4.75, .05, 3, "e-wave")
    for k in range(3):
        cv.rect(c + 4.8, 6.75 + k * .14, c + 6.0, 6.8 + k * .14, "e-dark")
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
    for u in (2.1, 4.4, 22.1):
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
    for (u, sd) in ((5.5, 1), (21.2, 2), (24.3, 3)):
        wave_planter(cv, u, Z_FFL if 3.1 < u < 23.5 else Z_PL, 1.6, .72, sd)
    lamp_post(cv, 26.4, Z_PL, 6.3, banner=(7.3, 9.4, ("GOOD", "GAMES", "BRIGHT", "DAYS")),
              signs=(("BEACH", -1), ("SHOPS", -1), ("FOOD", -1), ("PHOTO SPOT", -1)))
    aframe(cv, -4.6, Z_PL, ("PLAY", "EAT", "CHILL"))
    bench_e(cv, 1.1, Z_PL, 1.8)
    avatar_p(cv, -5.6, Z_PL, 1.66, 4)
    ground(cv, -6.6, 30.2, Z_PL, .55)
    # dims and tags
    hdim(cv, CTR - 2.5, CTR + 2.5, 2.75, "5.00 DOORS")
    hdim(cv, CTR - 7.1, CTR + 7.1, 2.25, "14.20 CONTROLLER SIGN")
    hdim(cv, 0, 27.08, 1.75, "27.08 ARCADE FRONT")
    vdim(cv, 30.6, Z_PL, Z_PAR, "6.60", side=1)
    vdim(cv, 30.6, Z_PAR, Z_RAIL, "1.10", side=1)
    level_tags(cv, -6.75, [(Z_PL, "+3.60 PLAZA"), (Z_FFL, "+4.05 FFL"), (Z_ROOF, "+9.60 ROOF TERRACE"),
                           (Z_PAR, "+10.20 PARAPET"), (Z_RAIL, "+11.30 RAIL")])
    note(cv, -6.3, 12.95, 1.0, 10.9, "Glass rail 1.10 m on 0.60 m parapet", "start")
    note(cv, 9.6, 12.95, CTR - .6, 10.1, "ARCADE · ゲームセンター · pixel mascot", "start")
    note(cv, 19.6, 12.95, CTR + 6.0, 9.75, "Buttons grip · Ø0.90 domes", "start")
    note(cv, 3.0, 12.4, CTR - 5.35, 10.0, "D-pad grip · cream GRC panels", "start")
    note(cv, 15.8, 12.4, 16.0, 11.25, "Floodlights on the parapet", "start")
    panel_title(cv, -6.6, .95, "1", "EAST ELEVATION · FRONT TO THE PLAZA", "looking west · 1:100 at sheet size · steps 3R × 0.15, treads 0.40")
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
    cv.text(21.0, 12.55, "FASHION & GOODS beyond · +13.20", "t-sm halo")
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
    hdim(cv, 13.75, 47.92, 2.75, "34.17 ARCADE + STRIP")
    level_tags(cv, u0 - .2, [(Z_PL, "+3.60"), (7.2, "+7.20 STRIP ROOF"), (Z_ROOF, "+9.60"), (Z_PAR, "+10.20")])
    note(cv, 33.0, 12.55, 34.6, 9.1, "Porthole windows Ø1.32 at 3.0 m centres", "start")
    panel_title(cv, u0, 1.1, "2", "SOUTH ELEVATION · SIDE", "looking north · prize & vending strip in front · café dashed")
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
    hdim(cv, 0, 27.08, 2.6, "27.08 ARCADE BACK")
    level_tags(cv, ua - .2, [(lane_z(37.92), f"+{lane_z(37.92):.2f} LANE"), (lane_z(65.0), f"+{lane_z(65.0):.2f}"),
                             (Z_PAR, "+10.20")])
    note(cv, 1.0, 12.0, 6.5, Z_PAR + .7, "Condensers screened behind the rail", "start")
    note(cv, 17.0, 6.2, U(63.0) - .9, yz + 1.2, "Fire exit at lane level, 6R down inside", "start")
    panel_title(cv, ua, 1.45, "3", "WEST ELEVATION · BACK TO THE LANE", "looking east · lane steps down +6.63 → +4.91 along the wall")
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


# ================================================================ A-502 FASHION + CAFÉ
Z_UP, Z_FROOF, Z_FPAR = 8.40, 12.60, 13.20     # fashion: upper floor, roof, parapet
Z_CROOF, Z_CPAR = 7.80, 8.20                    # café: roof, parapet


def fins(cv, u0, u1, z0, z1, step=.7, w=.14):
    for u in frange(u0 + step / 2, u1, step):
        cv.rect(u - w / 2, z0, u + w / 2, z1, "e-wood")


def dogleg(cv, u0, u1, z0, z1):
    """Dogleg stair seen through glass: two flights and a half landing."""
    zm = (z0 + z1) / 2
    um = (u0 + u1) / 2
    for (ua, za, ub, zb) in ((u0 + .2, z0, u1 - .4, zm), (u1 - .4, zm, u0 + .2, z1)):
        k = 8
        pts = []
        for i in range(k + 1):
            t = i / k
            u = ua + (ub - ua) * t
            z = za + (zb - za) * t
            pts += [(u, z), (u + (ub - ua) / k, z)] if i < k else [(u, z)]
        cv.pline(pts, "e-mull")
        cv.line(ua, za + 1.0, ub, zb + 1.0, "e-mull")
    cv.rect(u1 - .5, zm - .12, u1 - .1, zm, "e-dark")
    cv.text(um, zm + 1.4, "", "t-sm")


def arcade_stub(cv, u0, u1, z0=Z_PL, portholes=False):
    cv.rect(u0, z0, u1, Z_PAR, "e-yel")
    cv.rect(u0, 9.72, u1, 9.92, "e-pink")
    cv.rect(u0, Z_PAR - .12, u1, Z_PAR, "e-dark")
    glass_rail(cv, u0, u1, Z_PAR, Z_RAIL - Z_PAR)
    if portholes:
        for u in frange(u0 + 1.5, u1 - .7, 3.0):
            porthole(cv, u, 8.55, .66)


def fashion_east():
    sx = 14.0
    cv = Cv(sx, -sx, 150 + 3.0 * sx, 250, 0, Z_PL)
    cv.rect(-3.0, Z_PL, 21.5, 14.2, "e-sky")
    # beyond (north): kiosk strip on its retaining wall, railing and trees
    cv.rect(17.5, Z_PL, 21.5, Z_UP, "beyond")
    cv.line(17.5, Z_UP + 1.1, 21.5, Z_UP + 1.1, "e-out")
    for u in frange(17.9, 21.5, 1.0):
        cv.line(u, Z_UP, u, Z_UP + 1.1, "e-mull")
    tree_elev(cv, 20.2, Z_UP, 6.0, 5.0, 51)
    arcade_stub(cv, -3.0, 0)
    break_line(cv, -3.0, Z_PL, Z_RAIL)
    # body
    cv.rect(0, Z_PL, 17.5, Z_FPAR, "e-wall")
    cv.rect(0, Z_FROOF, 17.5, Z_FPAR, "e-coral")
    cv.rect(0, Z_FPAR - .12, 17.5, Z_FPAR, "e-dark")
    cv.rect(5.6, Z_UP, 17.5, Z_UP + .3, "e-coral")
    # SE corner: entrance and glazed stair core
    glazing(cv, .4, Z_PL, 5.4, Z_FROOF - .3, 3, inner="e-glass")
    dogleg(cv, .7, 5.1, Z_UP - 4.8 + .0, Z_UP)
    cv.rect(.4, Z_UP - .05, 5.4, Z_UP + .12, "e-dark")
    cv.rect(1.0, Z_PL, 3.4, 6.3, "e-glow")
    glazing(cv, 1.0, Z_PL, 3.4, 6.3, 2, inner="e-glass-t")
    cv.rect(.2, 6.55, 5.8, 6.8, "e-coral")
    cv.rect(.4, 6.25, 5.6, 6.55, "e-shadow")
    stext(cv, 2.9, 6.95, "ENTRANCE", .2, fill="var(--f-dark)", weight=700, family="var(--f-cond)")
    # ground floor display windows, fascia sign, upper floor with timber fins
    glazing(cv, 6.0, Z_PL, 17.1, 7.5, 4, inner="e-glow")
    for u in (7.4, 9.9, 12.4, 15.0):
        avatar_p(cv, u, Z_PL + .1, 1.75, 0)
    glazing(cv, 6.0, Z_PL, 17.1, 7.5, 4, inner="e-glass-t")
    stext(cv, 11.55, 7.75, "FASHION & GOODS", .42, fill="var(--f-dark)", weight=800)
    stext(cv, 11.55, 7.58 - .45, "", .1)
    glazing(cv, 6.0, 9.0, 17.1, 12.2, 4)
    fins(cv, 6.0, 17.1, 8.9, 12.3)
    stext(cv, 8.8, Z_FROOF + .15, "ファッション＆グッズ", .26, fill="var(--f-white)", weight=700, family="var(--f-body)")
    # raised planters in front (traced: 0.6 m high, 1.9 m from the face)
    for (a, b) in ((5.83, 15.83),):
        shrubs_e(cv, a + .1, b - .3, Z_PL + .6, .75, 52)
        cv.rect(a, Z_PL, b, Z_PL + .6, "e-conc")
    ground(cv, -3.0, 21.5, Z_PL, .5)
    hdim(cv, 0, 17.5, 2.6, "17.50 FASHION & GOODS")
    vdim(cv, 18.0, Z_PL, Z_FPAR, "9.60", side=1)
    level_tags(cv, -3.15, [(Z_PL, "+3.60"), (Z_UP, "+8.40 UPPER FLOOR"), (Z_FROOF, "+12.60 ROOF"), (Z_FPAR, "+13.20")])
    note(cv, 8.0, 14.6, 3.0, 9.5, "Glazed stair core · 2 × 16R dogleg", "start")
    panel_title(cv, -3.0, 1.45, "4", "FASHION & GOODS · EAST · FRONT", "looking west · entrance at the SE corner, planters in front")
    return cv


def fashion_west():
    sx = 14.0
    cv = Cv(sx, -sx, 700 + 2.0 * sx, 250, 0, Z_PL)
    U = lambda y: y - 20.0  # noqa: E731  (left = north)
    cv.rect(-2.0, 5.0, 21.0, 14.2, "e-sky")
    arcade_stub(cv, 17.5, 21.0, 4.4)
    cv.rect(0, 5.2, 17.5, Z_FPAR, "e-wall")
    cv.rect(0, Z_FROOF, 17.5, Z_FPAR, "e-coral")
    cv.rect(0, Z_FPAR - .12, 17.5, Z_FPAR, "e-dark")
    for a in (3.2, 8.0, 12.8):
        glazing(cv, a, 9.3, a + 2.4, 11.7, 1)
        cv.rect(a - .1, 9.15, a + 2.5, 9.3, "e-coral")
    for u in (.3, 17.2):
        cv.rect(u - .07, 5.2, u + .07, Z_FROOF, "e-steel")
    for u in (6.0, 10.9):
        cv.rect(u - .55, 7.6, u + .55, 8.3, "e-steel")
        cv.circle(u, 7.95, .25, "e-joint")
    # service door on the upper floor, 4R up from the lane
    zl = lane_z(21.0)
    cv.rect(.8, Z_UP, 2.0, Z_UP + 2.2, "e-steel")
    for k in range(4):
        cv.rect(.6, zl + k * .155, 2.4 + (3 - k) * .3, zl + (k + 1) * .155, "e-conc")
    cv.text(1.4, Z_UP + 2.55, "SERVICE", "t-sm halo")
    ground(cv, -2.0, 21.0, 0, .6, lane_profile(U, 18.0, 41.0, 1.2))
    hdim(cv, 0, 17.5, 3.1, "17.50")
    level_tags(cv, -2.15, [(lane_z(20.0), f"+{lane_z(20.0):.2f} LANE"), (Z_UP, "+8.40"), (Z_FPAR, "+13.20")])
    panel_title(cv, -2.0, 1.9, "6", "FASHION & GOODS · WEST · BACK", f"looking east · lane +{lane_z(20.0):.2f} → +{lane_z(37.5):.2f}")
    return cv


def fashion_north():
    sx = 14.0
    cv = Cv(sx, -sx, 150 + 8.0 * sx, 480, 0, Z_UP)
    # u = 47.92 - x (left = east end on the plaza side, right = west end at the lane)
    cv.rect(-8.0, Z_UP, 36.5, 14.6, "e-sky")
    # roof deck rail and vents above the parapet
    glass_rail(cv, .4, 12.9, Z_FPAR, 1.1)
    for u in frange(15.0, 33.0, 2.6):
        cv.rect(u, Z_FPAR, u + 1.6, Z_FPAR + .45, "e-steel")
    cv.rect(0, Z_UP, 34.17, Z_FPAR, "e-wall")
    cv.rect(0, Z_FROOF, 34.17, Z_FPAR, "e-coral")
    cv.rect(0, Z_FPAR - .12, 34.17, Z_FPAR, "e-dark")
    glazing(cv, 1.0, 9.1, 33.2, 12.1, 12)
    fins(cv, 1.0, 33.2, 9.0, 12.2, step=1.34)
    stext(cv, 17.1, Z_FROOF + .14, "FASHION & GOODS", .32, fill="var(--f-white)", weight=800)
    # kiosks in front (dashed) and the planted strip along the face
    for (a, b, lab) in ((12.4, 17.4, "KIOSK 3"), (17.4, 28.4, "KIOSK 2"), (28.4, 34.6, "KIOSK 1")):
        cv.rect(a, Z_UP, b, Z_UP + 3.0, "e-ghost")
        cv.line(a, Z_UP + 2.3, b, Z_UP + 2.3, "e-ghost")
        cv.text((a + b) / 2, Z_UP + 1.3, lab + " in front", "t-sm halo")
    shrubs_e(cv, -7.4, 34.2, Z_UP + .5, .7, 53)
    cv.rect(-7.4, Z_UP, 34.25, Z_UP + .5, "e-conc")
    # NE: kiosk-strip railing over the plaza drop
    cv.line(-7.4, Z_UP + 1.6, 0, Z_UP + 1.6, "e-out")
    for u in frange(-7.2, 0, 1.0):
        cv.line(u, Z_UP + .5, u, Z_UP + 1.6, "e-mull")
    tree_elev(cv, -4.5, Z_UP, 6.5, 5.5, 54)
    ground(cv, -8.0, 36.5, 0, .5, [(-8.0, Z_UP), (34.17, Z_UP), (34.3, lane_z(20.2)), (36.5, lane_z(20.2))])
    hdim(cv, 0, 34.17, 7.55, "34.17")
    level_tags(cv, -8.15, [(Z_UP, "+8.40 KIOSK STRIP"), (Z_FROOF, "+12.60"), (Z_FPAR, "+13.20")])
    note(cv, 1.0, 15.2, 6.0, Z_FPAR + .9, "Roof deck rail (stair core continues up)", "start")
    panel_title(cv, -8.0, 6.25, "5", "FASHION & GOODS · NORTH · SIDE TO THE STREET", "looking south from the kiosk strip · kiosks dashed (A-504)")
    return cv


def cafe_south():
    sx = 14.0
    cv = Cv(sx, -sx, 150 + 3.0 * sx, 700, 0, Z_PL)
    # u = x - 13.75 (left = west / lane)
    cv.rect(-3.0, Z_PL, 27.0, 11.8, "e-sky")
    # arcade beyond, above the café parapet
    cv.rect(0, Z_CPAR, 27.0, Z_PAR, "e-yel")
    cv.rect(0, 9.72, 27.0, 9.92, "e-pink")
    cv.rect(0, Z_PAR - .12, 27.0, Z_PAR, "e-dark")
    glass_rail(cv, 0, 27.0, Z_PAR, Z_RAIL - Z_PAR)
    for u in frange(2.85, 26.5, 3.0):
        porthole(cv, u, 8.85, .5)
    cv.text(13.5, 11.65, "ARCADE beyond", "t-sm halo")
    # café body
    cv.rect(0, Z_PL, 23.33, Z_CPAR, "e-cream")
    cv.rect(0, Z_CROOF, 23.33, Z_CPAR, "e-yel")
    cv.rect(0, Z_CPAR - .1, 23.33, Z_CPAR, "e-dark")
    glazing(cv, .8, 5.0, 2.4, 6.6, 1)
    shrubs_e(cv, 0, 2.9, Z_PL, .8, 61)
    # folding glass front with the café inside
    cv.rect(3.6, Z_PL, 23.0, 6.15, "e-glow")
    for u in frange(4.6, 22.5, 2.6):
        cv.rect(u, Z_PL, u + .08, Z_PL + .75, "e-dark")
        cv.rect(u - .45, Z_PL + .72, u + .53, Z_PL + .78, "e-dark")
    cv.rect(18.0, Z_PL, 22.6, Z_PL + 1.1, "e-wood")
    glazing(cv, 3.6, Z_PL, 23.0, 6.15, 8, inner="e-glass-t")
    # awning: striped canvas, white valance with the café name
    cv.rect(3.25, 6.35, 23.33, 7.0, "", ' fill="url(#ce-awn-y)"')
    cv.rect(3.25, 6.35, 23.33, 7.0, "e-out")
    cv.rect(3.25, 5.95, 23.33, 6.35, "e-white")
    cv.rect(3.25, 5.95, 23.33, 6.35, "e-out")
    cv.rect(3.25, 5.6, 23.33, 5.95, "e-shadow")
    stext(cv, 13.3, 6.04, "SEASIDE CAFE", .26, fill="var(--f-dark)", weight=700, family="var(--f-cond)", ls=.12)
    for u in (6.0, 13.3, 20.6):
        cv.rect(u - .15, 7.15, u + .15, 7.55, "e-dark")
        cv.circle(u, 7.05, .14, "e-yel3")
    # terrace (east part) and props
    parasol_e(cv, 26.0, Z_PL, 1.5, 2.4, "umb-c")
    aframe(cv, 24.6, Z_PL, ("PLAY", "EAT", "CHILL"))
    avatar_p(cv, 9.5, Z_PL, 1.68, 7)
    ground(cv, -3.0, 27.0, Z_PL, .5)
    cv.rect(3.0, Z_PL - .18, 27.0, Z_PL, "e-wood")
    hdim(cv, 0, 23.33, 2.85, "23.33 CAFÉ")
    hdim(cv, 3.25, 23.33, 2.4, "20.08 AWNING")
    level_tags(cv, -3.15, [(Z_PL, "+3.60 TERRACE"), (Z_CROOF, "+7.80 ROOF"), (Z_PAR, "+10.20")])
    panel_title(cv, -3.0, .75, "7", "CAFÉ · SOUTH · FRONT TO THE TERRACE", "looking north · folding glass front, 2.5 m awning")
    return cv


def cafe_east():
    sx = 14.0
    cv = Cv(sx, -sx, 660 + 9.0 * sx, 700, 0, Z_PL)
    # u = 77.5 - y (left = south / terrace, right = north / strip and arcade)
    cv.rect(-9.0, Z_PL, 15.0, 11.8, "e-sky")
    cv.rect(12.5, Z_PL, 15.0, Z_PAR, "e-yel")
    cv.rect(12.5, 9.72, 15.0, 9.92, "e-pink")
    glass_rail(cv, 12.5, 15.0, Z_PAR, Z_RAIL - Z_PAR)
    break_line(cv, 15.0, Z_PL, Z_RAIL)
    cv.text(13.75, 11.65, "ARCADE", "t-sm halo")
    # café east face (set back 10.8 m)
    cv.rect(0, Z_PL, 9.17, Z_CPAR, "e-cream")
    cv.rect(0, Z_CROOF, 9.17, Z_CPAR, "e-yel")
    glazing(cv, .6, 4.6, 2.6, 6.4, 1)
    glazing(cv, 5.8, 4.6, 8.6, 6.4, 2)
    cv.rect(3.1, Z_PL, 5.2, 6.4, "e-glow")
    glazing(cv, 3.1, Z_PL, 5.2, 6.4, 2, inner="e-glass-t")
    cv.rect(-2.5, 5.6, 0, 7.0, "", ' fill="url(#ce-awn-y)"')
    cv.rect(-2.5, 5.6, 0, 7.0, "e-out")
    # prize & vending strip, nearer (east end on the plaza line)
    cv.rect(9.17, Z_PL, 12.5, 7.2, "e-yel")
    cv.rect(9.17, 6.9, 12.5, 7.2, "e-dark")
    glazing(cv, 9.5, Z_PL, 12.2, 6.1, 2, inner="e-glow")
    rrect(cv, 9.4, 6.25, 12.27, 6.8, .2, "e-pink-o")
    stext(cv, 10.83, 6.38, "PRIZE", .3, weight=800)
    # terrace parasols and people
    for (u, cls) in ((-1.0, "umb-p"), (-6.5, "umb-y")):
        parasol_e(cv, u, Z_PL, 1.5, 2.4, cls)
    avatar_p(cv, -3.6, Z_PL, 1.7, 8)
    ground(cv, -9.0, 15.0, Z_PL, .5)
    cv.rect(-9.0, Z_PL - .18, 9.17, Z_PL, "e-wood")
    hdim(cv, 0, 9.17, 2.6, "9.17 CAFÉ")
    level_tags(cv, -9.15, [(Z_PL, "+3.60"), (Z_CPAR, "+8.20")])
    panel_title(cv, -9.0, 1.35, "8", "CAFÉ · EAST · SIDE", "looking west across the terrace")
    return cv


def cafe_west():
    sx = 14.0
    cv = Cv(sx, -sx, 150 + 4.0 * sx, 910, 0, Z_PL)
    U = lambda y: y - 68.33  # noqa: E731  (left = north)
    cv.rect(-4.0, 3.9, 13.0, 11.8, "e-sky")
    arcade_stub(cv, -4.0, 0, 3.9)
    cv.rect(-3.33, 4.0, 0, 7.2, "e-yel")
    cv.rect(-3.33, 6.9, 0, 7.2, "e-dark")
    cv.rect(0, 3.9, 9.17, Z_CPAR, "e-cream")
    cv.rect(0, Z_CROOF, 9.17, Z_CPAR, "e-yel")
    cv.rect(2.3, Z_CPAR, 2.6, 9.6, "e-steel")
    cv.rect(2.15, 9.6, 2.75, 9.8, "e-dark")
    glazing(cv, .8, 6.1, 5.0, 6.9, 3)
    cv.rect(3.4, 5.2, 4.6, 5.9, "e-steel")
    cv.circle(4.0, 5.55, .25, "e-joint")
    zl = lane_z(75.0)
    cv.rect(U(74.2), zl, U(75.3), zl + 2.2, "e-steel")
    cv.text(U(74.75), zl + 2.55, "KITCHEN", "t-sm halo")
    for u in (U(76.3), U(77.1)):
        cv.rect(u - .38, lane_z(77), u + .38, lane_z(77) + 1.1, "e-mint")
    shrubs_e(cv, 9.3, 12.8, lane_z(79.0), .8, 62)
    ground(cv, -4.0, 13.0, 0, .6, lane_profile(U, 64.33, 81.33, 1.2))
    hdim(cv, 0, 9.17, 2.9, "9.17")
    level_tags(cv, -4.15, [(lane_z(68.33), f"+{lane_z(68.33):.2f} LANE"), (Z_CPAR, "+8.20")])
    note(cv, 4.5, 11.2, 2.45, 9.7, "Kitchen flue", "start")
    panel_title(cv, -4.0, 2.1, "9", "CAFÉ · WEST · BACK", f"looking east · lane +{lane_z(68.33):.2f} → +{lane_z(77.5):.2f}, kitchen door 4R down inside")
    return cv


def sheet_a502():
    W, H = 1100, 1000
    root = Cv(1, 1, 0, 0)
    root.add(defs_e("ce"))
    root.add(f'<rect class="sheet-bg" width="{W}" height="{H}"/>')
    title_strip(root, 24, 30, "A-502", "FASHION & GOODS AND CAFÉ · ELEVATIONS",
                "Footprints from L-101 · levels from L-202 · all views 14 px = 1 m (1:100 at sheet size)")
    parts = [fashion_east(), fashion_west(), fashion_north(), cafe_south(), cafe_east(), cafe_west()]
    key = colour_key(root, 640, 800, [("e-wall", "Warm white render"), ("e-coral", "Terracotta bands and coping"),
                                      ("e-wood", "Timber fins"), ("e-cream", "Café render"), ("e-yel", "Yellow trim, arcade"),
                                      ("e-glass", "Clear glazing"), ("e-glow", "Lit interior")])
    root.add(f'<rect class="frame" x="12" y="50" width="{W - 24}" height="{H - 62}"/>')
    return "\n".join([root.svg()] + [p.svg() for p in parts] + [key]), W, H


# ================================================================ A-503 LIFESTYLE & SOUVENIR
Z_LROOF, Z_LPAR, Z_LCAP, Z_BAND, Z_ANNEX = 8.70, 9.00, 9.40, 6.60, 7.20


def cat_statue(cv, u, z, h=2.2):
    """Photo-spot mascot statue on a pink drum (as the plaza cat, smaller)."""
    cv.rect(u - .9, z, u + .9, z + .5, "e-pink-o")
    r = h * .22
    cv.ellipse(u, z + .5 + r * 1.1, r * 1.25, r * 1.1, "statue")
    cv.circle(u, z + .5 + r * 2.6, r * .85, "statue")
    for k in (-1, 1):
        cv.poly([(u + k * r * .75, z + .5 + r * 3.0), (u + k * r * .55, z + .5 + r * 3.65), (u + k * r * .2, z + .5 + r * 3.3)], "statue")
    cv.circle(u + r * .9, z + .5 + r * 1.4, r * .28, "chalk-p")


def stall_e(cv, u0, u1, z, pat="awn-c"):
    cv.rect(u0, z, u1, z + 1.0, "e-wood")
    cv.rect(u0 + .1, z + .9, u1 - .1, z + 1.05, "e-cream")
    for u in (u0 + .1, u1 - .1):
        cv.rect(u - .05, z, u + .05, z + 2.35, "e-dark")
    cv.rect(u0 - .2, z + 2.3, u1 + .2, z + 2.65, "", f' fill="url(#ce-{pat})"')
    cv.rect(u0 - .2, z + 2.3, u1 + .2, z + 2.65, "e-out")
    for u in frange(u0 + .4, u1 - .3, .55):
        cv.circle(u, z + 1.25, .17, ("chalk-p", "chalk-y", "chalk-c")[int(u * 5) % 3])


def tent_e(cv, u0, u1, z):
    cv.rect(u0, z, u1, z + 2.2, "e-white")
    cv.rect(u0, z, u1, z + 2.2, "e-out")
    cv.poly([(u0 - .15, z + 2.2), ((u0 + u1) / 2, z + 3.3), (u1 + .15, z + 2.2)], "e-cream")
    cv.line((u0 + u1) / 2, z, (u0 + u1) / 2, z + 2.2, "e-joint")


def life_main_upper(cv, u0, u1, sign=True):
    cv.rect(u0, Z_PL, u1, Z_LPAR, "e-white")
    cv.rect(u0, Z_PL, u1, Z_LPAR, "e-out")
    cv.rect(u0, Z_LPAR, u1, Z_LCAP, "e-yel")


def life_south():
    sx = 20.0
    cv = Cv(sx, -sx, 150 + 8.0 * sx, 290, 0, Z_PL)
    # u = x - 130.33 (left = west / plaza side)
    cv.rect(-8.0, Z_PL, 31.0, 11.6, "e-sky")
    cv.rect(8.83, Z_PL, 23.0, Z_ANNEX, "beyond")
    life_main_upper(cv, 0, 23.0)
    stext(cv, 11.5, 8.1, "LIFESTYLE & SOUVENIR", .5, fill="var(--f-dark)", weight=800)
    stext(cv, 5.2, 7.35, "ライフスタイル＆おみやげ", .24, fill="var(--f-dark)", weight=700, family="var(--f-body)")
    # south band (canopy), 4.2 m in front of the main face
    cv.rect(0, Z_PL, 23.0, Z_BAND, "e-white")
    cv.rect(0, Z_BAND - .25, 23.0, Z_BAND, "e-dark")
    shrubs_e(cv, 11.9, 18.8, Z_BAND, .7, 71)
    cv.rect(.17, 5.75, 8.83, Z_BAND - .25, "e-yel")
    stext(cv, 4.5, 5.9, "GOODS · HOME · GIFTS", .2, fill="var(--f-dark)", weight=700, family="var(--f-cond)")
    cv.rect(.5, Z_PL, 8.5, 5.7, "e-glow")
    glazing(cv, .5, Z_PL, 8.5, 5.7, 4, inner="e-glass-t")
    cv.rect(9.0, Z_PL, 11.5, 5.9, "e-glow")
    glazing(cv, 9.0, Z_PL, 11.5, 5.9, 2, inner="e-glass-t")
    glazing(cv, 19.5, 4.4, 22.6, 5.9, 2)
    # centre awning and the pink shop sign on posts
    cv.rect(11.67, 5.15, 19.17, 5.95, "e-yel")
    cv.rect(11.67, 5.15, 19.17, 5.95, "e-out")
    cv.rect(11.67, 4.8, 19.17, 5.15, "e-shadow")
    cv.rect(11.9, Z_PL, 19.0, 5.1, "e-glow")
    glazing(cv, 11.9, Z_PL, 19.0, 5.1, 4, inner="e-glass-t")
    for u in (12.6, 18.2):
        cv.rect(u - .06, Z_PL, u + .06, 4.4, "e-dark")
    rrect(cv, 12.0, 4.35, 18.8, 5.05, .15, "e-pink-o")
    stext(cv, 15.4, 4.5, "SOUVENIR", .38, weight=800)
    # forecourt: stall, photo statue, vending kiosk, planter box
    stall_e(cv, .5, 4.67, Z_PL)
    cat_statue(cv, 9.84, Z_PL)
    cv.rect(21.0, Z_PL, 23.33, 5.4, "e-white")
    cv.rect(21.0, Z_PL, 23.33, 5.4, "e-out")
    cv.rect(21.3, 4.3, 23.0, 5.1, "e-blue")
    stext(cv, 22.15, 4.55, "DRINKS", .16, weight=700, family="var(--f-cond)")
    shrubs_e(cv, 23.4, 27.6, Z_PL + .6, .7, 72)
    cv.rect(23.33, Z_PL, 27.67, Z_PL + .6, "e-conc")
    # neighbours: west terrace parasol + tree, east terrace parasol + palm
    parasol_e(cv, -4.5, Z_PL, 1.5, 2.4, "umb-y")
    tree_elev(cv, -6.5, Z_PL, 6.5, 4.5, 73)
    parasol_e(cv, 28.6, Z_PL, 1.5, 2.4, "umb-c")
    palm_elev(cv, 30.0, Z_PL, 6.5, 74)
    avatar_p(cv, 7.2, Z_PL, 1.65, 9)
    ground(cv, -8.0, 31.0, Z_PL, .5)
    hdim(cv, 0, 23.0, 2.85, "23.00 SHOP")
    hdim(cv, 11.67, 19.17, 2.35, "7.50 AWNING")
    vdim(cv, 23.9, Z_PL, Z_LCAP, "5.80", side=1)
    level_tags(cv, -8.15, [(Z_PL, "+3.60"), (Z_BAND, "+6.60 CANOPY"), (Z_LCAP, "+9.40 TRIM")])
    note(cv, 13.0, 10.9, 15.3, Z_BAND + .5, "Roof garden on the canopy (traced)", "start")
    panel_title(cv, -8.0, .8, "10", "LIFESTYLE & SOUVENIR · SOUTH · FRONT", "looking north · canopy band, centre awning, shop sign, stall and photo statue")
    return cv


def life_west():
    sx = 20.0
    cv = Cv(sx, -sx, 150 + 1.0 * sx, 575, 0, Z_PL)
    # u = y - 48 (left = north)
    cv.rect(-1.0, Z_PL, 33.0, 11.4, "e-sky")
    cv.rect(2.5, Z_PL, 7.0, Z_ANNEX, "beyond")
    cv.rect(.67, Z_ANNEX, 2.83, 8.2, "e-white")
    cv.rect(.67, Z_ANNEX, 2.83, 8.2, "e-out")
    life_main_upper(cv, 7.0, 23.67)
    for (a, b) in ((8.0, 12.8), (18.0, 23.0)):
        glazing(cv, a, 4.4, b, 7.6, 3)
    cv.rect(13.67, Z_PL, 17.0, 6.6, "e-glow")
    glazing(cv, 13.67, Z_PL, 17.0, 6.6, 2, inner="e-glass-t")
    cv.rect(13.3, 6.8, 17.4, 7.1, "e-yel")
    cv.rect(13.5, 6.5, 17.2, 6.8, "e-shadow")
    stext(cv, 15.33, 7.4, "WELCOME", .22, fill="var(--f-dark)", weight=700, family="var(--f-cond)")
    # south band seen end-on, awning and sign beyond it
    cv.rect(23.67, Z_PL, 27.83, Z_BAND, "e-white")
    cv.rect(23.67, Z_PL, 27.83, Z_BAND, "e-out")
    cv.rect(23.67, Z_BAND - .25, 27.83, Z_BAND, "e-dark")
    cv.poly([(27.83, 5.95), (29.67, 5.75), (29.67, 5.15), (27.83, 5.15)], "e-yel")
    cv.rect(29.6, Z_PL, 29.75, 5.05, "e-dark")
    cv.rect(29.67, 4.35, 31.33, 5.05, "e-pink-o")
    stall_e(cv, 27.83, 30.0, Z_PL)
    # planter, seating terrace parasol in front
    shrubs_e(cv, 3.4, 10.6, Z_PL + .6, .7, 75)
    cv.rect(3.3, Z_PL, 10.67, Z_PL + .6, "e-conc")
    parasol_e(cv, 19.5, Z_PL, 1.5, 2.4, "umb-y")
    avatar_p(cv, 12.5, Z_PL, 1.7, 10)
    ground(cv, -1.0, 33.0, Z_PL, .5)
    hdim(cv, 7.0, 23.67, 2.85, "16.67 SHOP")
    level_tags(cv, -1.15, [(Z_PL, "+3.60"), (Z_ANNEX, "+7.20 ANNEX"), (Z_LCAP, "+9.40")])
    panel_title(cv, -1.0, 1.35, "11", "LIFESTYLE & SOUVENIR · WEST · SIDE TO THE PLAZA", "looking east · double doors on the seating terrace")
    return cv


def life_east():
    sx = 20.0
    cv = Cv(sx, -sx, 150 + 4.0 * sx, 860, 0, Z_PL)
    # u = 81.67 - y (left = south)
    cv.rect(-4.0, Z_PL, 34.0, 11.4, "e-sky")
    cv.rect(26.67, Z_PL, 31.17, Z_ANNEX, "e-white")
    cv.rect(26.67, Z_PL, 31.17, Z_ANNEX, "e-out")
    cv.rect(26.67, Z_ANNEX - .3, 31.17, Z_ANNEX, "e-yel")
    cv.rect(27.5, Z_PL, 28.7, 5.8, "e-steel")
    cv.rect(30.83, Z_ANNEX, 33.0, 8.2, "e-white")
    cv.rect(30.83, Z_ANNEX, 33.0, 8.2, "e-out")
    life_main_upper(cv, 10.0, 26.67)
    for (a, b) in ((10.8, 13.4), (16.6, 19.0), (21.4, 25.8)):
        glazing(cv, a, 5.0, b, 7.4, 2)
    cv.rect(14.0, Z_PL, 15.2, 5.8, "e-steel")
    for u in (18.0, 24.0):
        cv.rect(u - .55, 7.9, u + .55, 8.6, "e-steel")
    cv.rect(5.83, Z_PL, 10.0, Z_BAND, "e-white")
    cv.rect(5.83, Z_PL, 10.0, Z_BAND, "e-out")
    cv.rect(5.83, Z_BAND - .25, 10.0, Z_BAND, "e-yel")
    cv.rect(3.67, Z_PL, 5.33, 5.4, "e-white")
    cv.rect(3.67, Z_PL, 5.33, 5.4, "e-out")
    shrubs_e(cv, .05, 1.6, Z_PL + .6, .7, 76)
    cv.rect(0, Z_PL, 1.67, Z_PL + .6, "e-conc")
    # east terrace in front: two white tents, parasol, palms
    tent_e(cv, 10.0, 13.83, Z_PL)
    tent_e(cv, 13.3, 16.67, Z_PL)
    parasol_e(cv, -2.9, Z_PL, 1.5, 2.4, "umb-c")
    palm_elev(cv, 20.0, Z_PL, 6.8, 77)
    palm_elev(cv, 2.0, Z_PL, 6.0, 78)
    ground(cv, -4.0, 34.0, Z_PL, .5)
    hdim(cv, 10.0, 26.67, 2.85, "16.67 SHOP")
    hdim(cv, 26.67, 31.17, 2.85, "4.50")
    level_tags(cv, -4.15, [(Z_PL, "+3.60"), (Z_LCAP, "+9.40")])
    panel_title(cv, -4.0, 1.35, "12", "LIFESTYLE & SOUVENIR · EAST · BACK", "looking west · service door, annex, east terrace tents in front")
    return cv


def sheet_a503():
    W, H = 1100, 950
    root = Cv(1, 1, 0, 0)
    root.add(defs_e("ce"))
    root.add(f'<rect class="sheet-bg" width="{W}" height="{H}"/>')
    title_strip(root, 24, 30, "A-503", "LIFESTYLE & SOUVENIR · ELEVATIONS",
                "Re-traced footprint (L-101): yellow trim on three sides, canopy band with roof garden, centre awning and shop sign · 20 px = 1 m")
    parts = [life_south(), life_west(), life_east()]
    key = colour_key(root, 862, 455, [("e-white", "White render"), ("e-yel", "Yellow trim and canopy"), ("e-pink-o", "Pink shop sign"),
                                      ("e-dark", "Graphite fascia"), ("e-glass", "Clear glazing"), ("e-glow", "Lit interior")])
    root.add(f'<rect class="frame" x="12" y="50" width="{W - 24}" height="{H - 62}"/>')
    return "\n".join([root.svg()] + [p.svg() for p in parts] + [key]), W, H


# ================================================================ A-504 SMALL STRUCTURES
def truck_side(cv, u0, z, stripe="awn-p"):
    w = (.42, )
    cv.rect(u0, z + .45, u0 + 5.0, z + 3.0, "e-cream")
    rrect(cv, u0, z + .45, u0 + 5.0, z + 3.0, .25, "e-out")
    cv.path([("M", u0 + 5.0, z + .45), ("L", u0 + 6.5, z + .45), ("L", u0 + 6.5, z + 1.5), ("L", u0 + 6.1, z + 2.55),
             ("L", u0 + 5.0, z + 2.55), ("Z",)], "e-pink-o")
    cv.poly([(u0 + 5.25, z + 1.65), (u0 + 6.2, z + 1.65), (u0 + 5.95, z + 2.35), (u0 + 5.25, z + 2.35)], "e-glass")
    cv.rect(u0, z + .45, u0 + 6.5, z + .75, "e-dark")
    cv.rect(u0 + .9, z + 1.25, u0 + 4.3, z + 2.35, "e-glow")
    cv.rect(u0 + .8, z + 1.15, u0 + 4.4, z + 1.25, "e-steel")
    cv.poly([(u0 + .7, z + 2.45), (u0 + 4.5, z + 2.45), (u0 + 4.7, z + 2.95), (u0 + .5, z + 2.95)], "", f' fill="url(#ce-{stripe})"')
    cv.poly([(u0 + .7, z + 2.45), (u0 + 4.5, z + 2.45), (u0 + 4.7, z + 2.95), (u0 + .5, z + 2.95)], "e-out")
    rrect(cv, u0 + 1.4, z + 3.05, u0 + 3.8, z + 3.55, .12, "e-dark")
    stext(cv, u0 + 2.6, z + 3.18, "STREET EATS", .22, weight=700, family="var(--f-cond)")
    for u in (u0 + 1.2, u0 + 5.4):
        cv.circle(u, z + .42, .42, "e-dark")
        cv.circle(u, z + .42, .18, "e-steel")
    cv.rect(u0 - .5, z, u0 - .1, z + 1.2, "e-dark")
    stext(cv, u0 - .3, z + .7, "MENU", .1, weight=700, family="var(--f-cond)", rot=-90)


def truck_front(cv, u0, z):
    cv.rect(u0, z + .45, u0 + 2.5, z + 2.55, "e-pink-o")
    cv.rect(u0 + .2, z + 1.55, u0 + 2.3, z + 2.35, "e-glass")
    cv.rect(u0 + .3, z + .55, u0 + 2.2, z + 1.0, "e-dark")
    for u in (u0 + .4, u0 + 2.1):
        cv.circle(u, z + 1.2, .14, "e-yel3")
    cv.rect(u0 + .15, z + 2.55, u0 + 2.35, z + 3.0, "e-cream")
    cv.rect(u0 - .15, z + 1.7, u0, z + 2.1, "e-dark")
    cv.rect(u0 + 2.5, z + 1.7, u0 + 2.65, z + 2.1, "e-dark")
    for u in (u0 + .3, u0 + 2.2):
        cv.rect(u - .15, z, u + .15, z + .5, "e-dark")


def truck_back(cv, u0, z):
    cv.rect(u0, z + .45, u0 + 2.5, z + 3.0, "e-cream")
    cv.rect(u0, z + .45, u0 + 2.5, z + 3.0, "e-out")
    cv.line(u0 + 1.25, z + .6, u0 + 1.25, z + 2.8, "e-mull")
    cv.rect(u0, z + .45, u0 + 2.5, z + .75, "e-dark")
    for u in (u0 + .2, u0 + 2.1):
        cv.rect(u, z + .9, u + .2, z + 1.2, "e-red")
    cv.rect(u0 + .6, z + 1.6, u0 + 1.9, z + 2.3, "", ' fill="url(#ce-awn-p)"')
    for u in (u0 + .3, u0 + 2.2):
        cv.rect(u - .15, z, u + .15, z + .5, "e-dark")


def kiosk_front(cv, u0, z, L=11.0, pat="awn-y"):
    cv.rect(u0, z, u0 + L, z + 3.0, "e-wall")
    cv.rect(u0, z, u0 + L, z + 3.0, "e-out")
    n_ = int(L // 2.6)
    w = L / n_
    for i in range(n_):
        a = u0 + i * w
        cv.rect(a + .25, z + 1.0, a + w - .25, z + 2.2, "e-glow")
        cv.rect(a + .25, z + 2.05, a + w - .25, z + 2.2, "e-steel")
        cv.rect(a + .15, z + .95, a + w - .15, z + 1.05, "e-wood")
        for u in frange(a + .5, a + w - .4, .5):
            cv.circle(u, z + 1.25, .16, ("chalk-p", "chalk-y", "chalk-c", "e-green")[int(u * 3) % 4])
    cv.rect(u0 - .2, z + 2.3, u0 + L + .2, z + 2.75, "", f' fill="url(#ce-{pat})"')
    cv.rect(u0 - .2, z + 2.3, u0 + L + .2, z + 2.75, "e-out")
    cv.rect(u0, z + 2.85, u0 + L, z + 3.1, "e-dark")


def kiosk_side(cv, u0, z, D=4.7):
    cv.rect(u0, z, u0 + D, z + 3.0, "e-wall")
    cv.rect(u0, z, u0 + D, z + 3.0, "e-out")
    cv.poly([(u0 - 1.2, z + 2.3), (u0, z + 2.75), (u0, z + 2.3)], "e-yel")
    cv.rect(u0, z + 2.85, u0 + D, z + 3.1, "e-dark")
    cv.rect(u0 + 2.4, z, u0 + 3.3, z + 2.1, "e-steel")


def kiosk_back(cv, u0, z, L=11.0):
    cv.rect(u0, z, u0 + L, z + 3.0, "e-wall")
    cv.rect(u0, z, u0 + L, z + 3.0, "e-out")
    cv.rect(u0, z + 2.85, u0 + L, z + 3.1, "e-dark")
    cv.rect(u0 + 1.0, z, u0 + 1.9, z + 2.1, "e-steel")
    cv.rect(u0 + 6.0, z + 1.6, u0 + 7.2, z + 2.2, "e-steel")


def hut(cv, u0, z, W, view="front"):
    """Beach hut: timber walls on a 0.3 m deck, thatched hip roof (eaves +2.7, ridge +4.6 above sand)."""
    cv.rect(u0 - (1.0 if view == "side" else 0), z, u0 + W + (2.7 if view == "side" else 0), z + .3, "e-wood")
    cv.rect(u0 + .3, z + .3, u0 + W - .3, z + 2.6, "e-wood")
    for u in frange(u0 + .3, u0 + W - .3, .25):
        cv.line(u, z + .3, u, z + 2.6, "e-joint")
    if view == "front":
        cv.rect(u0 + 1.0, z + 1.3, u0 + W - 1.0, z + 2.2, "e-glow")
        cv.rect(u0 + .9, z + 1.2, u0 + W - .9, z + 1.32, "e-wood")
        rrect(cv, u0 + 1.6, z + 2.25, u0 + W - 1.6, z + 2.55, .08, "e-cream")
        stext(cv, u0 + W / 2, z + 2.31, "RENTAL · LIFEGUARD", .16, fill="var(--f-dark)", weight=700, family="var(--f-cond)")
        for (u, cls) in ((u0 + 1.4, "e-blue"), (u0 + 1.9, "e-yel"), (u0 + W - 1.9, "e-pink-o")):
            rrect(cv, u - .17, z + .3, u + .17, z + 2.1, .17, cls)
    elif view == "back":
        cv.rect(u0 + W / 2 - .45, z + .3, u0 + W / 2 + .45, z + 2.3, "e-steel")
    else:
        cv.rect(u0 + 2.0, z + 1.3, u0 + 3.6, z + 2.0, "e-glass")
    ov = .8
    if view == "side":
        cv.poly([(u0 - ov, z + 2.6), (u0 + W / 2 - .6, z + 4.6), (u0 + W / 2 + .6, z + 4.6), (u0 + W + ov, z + 2.6)], "e-thatch")
    else:
        cv.poly([(u0 - ov, z + 2.6), (u0 + W / 2, z + 4.6), (u0 + W + ov, z + 2.6)], "e-thatch")
    cv.add("")


def speaker(cv, u, z, back=False):
    for k in range(2):
        cv.rect(u - .8, z + k * 1.6, u + .8, z + (k + 1) * 1.6, "e-dark")
        if not back:
            cv.circle(u, z + k * 1.6 + .55, .42, "e-steel")
            cv.circle(u, z + k * 1.6 + 1.25, .18, "e-steel")


def stage_view(cv, view):
    """Stage deck +4.20 on the lawn. view: front (from the lawn), back (from the top plaza), side."""
    zl, zd = Z_PL, 4.20
    if view in ("front", "back"):
        a, b = (-1.6, 23.2)
        s1, s2 = (6.6, 20.7) if view == "front" else (a + b - 6.6, a + b - 20.7)
        cv.rect(a - 2.0, zl, b + 2.0, 6.6, "beyond")
        cv.line(a - 2.0, 7.7, b + 2.0, 7.7, "e-out")
        for u in frange(a - 1.8, b + 2.0, 2.0):
            cv.line(u, 6.6, u, 7.7, "e-mull")
        for i, u in enumerate((1.0, 9.0, 16.0)):
            tree_elev(cv, u, 6.6, 6.0, 5.0, 81 + i)
        cv.rect(a, zl, b, zd, "e-wood")
        for k in (1, 2, 3):
            cv.line(a + .2, zl + k * .15, b - .2, zl + k * .15, "e-mull")
        speaker(cv, s1, zd, back=(view == "back"))
        speaker(cv, s2, zd, back=(view == "back"))
        for u in frange(a, b, 4.0):
            cv.line(u, zd, u, zd + 4.4, "e-mull")
        cv.pline([(u, zd + 4.4 - .35 * math.sin((u - a) / 4.0 * math.pi) ** 2) for u in frange(a, b + .01, .5)], "string")
        return a, b
    a, b = 0.0, 18.5
    cv.rect(a - 2.0, zl, b + 6.0, 6.6, "beyond")
    cv.rect(b + 2.0, zl, b + 6.0, 6.6, "e-conc")
    for k in range(20):
        cv.line(b + 2.0 + k * .2, zl + k * .15, b + 2.2 + k * .2, zl + k * .15, "e-mull")
    cv.rect(a, zl, b, zd, "e-wood")
    speaker(cv, 16.75, zd)
    speaker(cv, 13.6, zd)
    return a, b


def sheet_a504():
    W, H = 1100, 990
    root = Cv(1, 1, 0, 0)
    root.add(defs_e("ce"))
    root.add(f'<rect class="sheet-bg" width="{W}" height="{H}"/>')
    title_strip(root, 24, 30, "A-504", "SMALL STRUCTURES · FOOD TRUCK, STREET KIOSK, BEACH HUT, STAGE",
                "Truck 34 px = 1 m · kiosk and hut 21 px = 1 m · stage 11 px = 1 m · each set: front, side, back")
    out = [root.svg()]
    sx = 34.0
    # food truck
    cv = Cv(sx, -sx, 100, 200, 0, 0)
    for (u0, lab) in ((0, "SIDE · SERVING HATCH"), (8.2, "FRONT · CAB"), (12.0, "BACK")):
        cv.text(u0 + (3.25 if u0 == 0 else 1.25), -1.0, lab, "t-lbl")
    truck_side(cv, 0, 0)
    truck_front(cv, 8.2, 0)
    truck_back(cv, 12.0, 0)
    for (a, b) in ((-.8, 7.0), (7.8, 11.1), (11.6, 14.9)):
        ground(cv, a, b, 0, .25)
    hdim(cv, 0, 6.5, -1.6, "6.50")
    hdim(cv, 8.2, 10.7, -1.6, "2.50")
    vdim(cv, 15.4, 0, 3.0, "3.00", side=1)
    panel_title(cv, -.8, -2.35, "13", "FOOD TRUCK", "4 at the truck zone, real size (S-1) · pink, cyan and yellow stripe sets")
    out.append(cv.svg())
    # street kiosk (the 11 m middle unit)
    cv = Cv(sx * .62, -sx * .62, 100, 420, 0, 0)
    kiosk_front(cv, 0, 0)
    kiosk_side(cv, 14.0, 0)
    kiosk_back(cv, 21.5, 0)
    for (u0, w, lab) in ((0, 11.0, "FRONT · TO THE STREET"), (14.0, 4.7, "SIDE"), (21.5, 11.0, "BACK")):
        cv.text(u0 + w / 2, -1.2, lab, "t-lbl")
    for (a, b) in ((-1.0, 12.0), (12.6, 19.5), (20.8, 33.2)):
        ground(cv, a, b, 0, .35)
    hdim(cv, 0, 11.0, -1.9, "11.00")
    hdim(cv, 14.0, 18.7, -1.9, "4.70")
    vdim(cv, 33.6, 0, 3.1, "3.10", side=1)
    panel_title(cv, -1.0, -2.9, "14", "STREET KIOSK (KIOSK 2)", "on the kiosk strip +8.40 · kiosks 1 and 3 use the same kit at 6.2 and 5.0 m")
    out.append(cv.svg())
    # beach hut
    cv = Cv(sx * .62, -sx * .62, 100, 650, 0, Z_BC_E)
    hut(cv, 0, Z_BC_E, 7.5, "front")
    hut(cv, 11.5, Z_BC_E, 6.67, "side")
    hut(cv, 23.5, Z_BC_E, 7.5, "back")
    for (u0, w, lab) in ((0, 7.5, "FRONT · TO THE SEA"), (11.5, 6.67, "SIDE · DECK 3.7 m"), (23.5, 7.5, "BACK")):
        cv.text(u0 + w / 2, Z_BC_E - 1.2, lab, "t-lbl")
    for (a, b) in ((-1.4, 9.0), (9.8, 21.6), (22.1, 32.4)):
        ground(cv, a, b, Z_BC_E, .35)
    hdim(cv, 0, 7.5, Z_BC_E - 1.9, "7.50")
    vdim(cv, 32.8, Z_BC_E, Z_BC_E + 4.6, "4.60", side=1)
    panel_title(cv, -1.4, Z_BC_E - 2.9, "15", "BEACH HUT", "sand +1.00 · thatched hip roof, rental counter, boards")
    out.append(cv.svg())
    # stage
    ss = 11.0
    for (x0, view, lab) in ((90, "front", "FRONT · FROM THE LAWN"), (440, "back", "BACK · FROM THE TOP PLAZA")):
        cv = Cv(ss, -ss, x0 + 3.6 * ss, 900, 0, Z_PL)
        a, b = stage_view(cv, view)
        ground(cv, a - 2.0, b + 2.0, Z_PL, .45)
        cv.text((a + b) / 2, 12.6, lab, "t-lbl")
        hdim(cv, a, b, 2.65, f"{b - a:.1f} DECK")
        out.append(cv.svg())
    cv = Cv(ss, -ss, 790 + 2.0 * ss, 900, 0, Z_PL)
    a, b = stage_view(cv, "side")
    ground(cv, a - 2.0, b + 6.0, Z_PL, .45)
    cv.text((a + b) / 2 + 2, 12.6, "SIDE", "t-lbl")
    out.append(cv.svg())
    cv = Cv(ss, -ss, 90 + 3.6 * ss, 900, 0, Z_PL)
    etag(cv, -3.4, Z_PL, "+3.60", anchor="end")
    etag(cv, -3.4, 4.2, "+4.20 DECK", anchor="end")
    panel_title(cv, -3.6, .9, "16", "SMALL STAGE", "deck 26 × 21 m at +4.20 · 4R edge steps · PA stacks 1.6 × 1.6 × 3.2 m · festoon lights")
    out.append(cv.svg())
    root2 = Cv(1, 1, 0, 0)
    root2.add(f'<rect class="frame" x="12" y="50" width="{W - 24}" height="{H - 62}"/>')
    out.append(root2.svg())
    return "\n".join(out), W, H


Z_BC_E = 1.00
