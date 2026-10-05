"""Building elevations for the Umi Seaside Park (sheets A-501 to A-504).

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
    "f-indigo": "#2E3FB0", "f-verm": "#D9432F", "f-kawara": "#3B4352", "f-kawara-2": "#59627A", "f-plaster": "#FAF8F3",
    "f-gold": "#C9A24A", "f-led": "#FFB547", "f-portal": "#AEB6BF", "f-wood-d": "#8A5C3A",
    "f-arc": "#D8343F", "f-arc-2": "#B72632", "f-tile-b": "#2F6DB5",
}
F_DARK = {
    "f-yel": "#D7AE2F", "f-yel-2": "#B68B17", "f-yel-3": "#E6C55C", "f-cream": "#CFC9BB", "f-cream-2": "#A9A28F",
    "f-dark": "#151A20", "f-blue": "#2A78C2", "f-red": "#C2384A", "f-green": "#379C47", "f-glass": "#46707C",
    "f-glass-2": "#365C68", "f-pink": "#C97BA0", "f-lilac": "#8D7BC0", "f-poster": "#2F6FB5", "f-warm": "#D9B66E",
    "f-white": "#F2F4F6", "f-wall": "#BDB5A5", "f-coral": "#C46F55", "f-mint": "#7DAE98", "f-navy": "#1E2C40",
    "f-steel": "#6C7884", "f-sky": "#16293A", "f-thatch": "#A88A55", "f-orange": "#C97E31",
    "f-indigo": "#3447B8", "f-verm": "#B83A2A", "f-kawara": "#232A35", "f-kawara-2": "#3C4558", "f-plaster": "#CFCCC4",
    "f-gold": "#A88A3E", "f-led": "#E89E3A", "f-portal": "#7E8791", "f-wood-d": "#6B4630",
    "f-arc": "#B22F38", "f-arc-2": "#931F29", "f-tile-b": "#2A5C99",
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
.e-indigo{fill:var(--f-indigo);stroke:var(--ink);stroke-width:.8}
.e-verm{fill:var(--f-verm);stroke:var(--ink);stroke-width:.8}
.e-kawara{fill:var(--f-kawara);stroke:var(--ink);stroke-width:.7;stroke-linejoin:round}
.e-kawara-y{fill:var(--f-tile-b);stroke:var(--ink);stroke-width:.7;stroke-linejoin:round}
.e-tile{fill:none;stroke:var(--f-kawara-2);stroke-width:.8}
.e-plaster{fill:var(--f-plaster);stroke:var(--ink);stroke-width:.9;stroke-linejoin:round}
.e-gold{fill:var(--f-gold)}
.e-white-o{fill:var(--f-white);stroke:var(--ink);stroke-width:1.4;stroke-linejoin:round}
.e-portal{fill:var(--f-portal);stroke:var(--ink);stroke-width:.8}
.e-arc{fill:var(--f-arc);stroke:var(--ink);stroke-width:.9;stroke-linejoin:round}
.e-arc2{fill:var(--f-arc-2)}
.e-wood-d{fill:var(--f-wood-d);stroke:var(--ink);stroke-width:.8}
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


BANNERS = {   # design: (background, accent, text, text colour)
    "umi": ("var(--f-navy)", "var(--chalk-c)", "UMI", "var(--f-white)"),
    "cafe": ("var(--f-white)", "var(--f-wood-d)", "CAFE", "var(--f-wood-d)"),
    "games": ("var(--f-arc)", "var(--f-yel)", "GAMES", "var(--f-white)"),
    "omiyage": ("var(--f-yel)", "var(--f-red)", "おみやげ", "var(--f-dark)"),
    "beach": ("var(--chalk-c)", "var(--f-white)", "BEACH", "var(--f-white)"),
    "sakura": ("var(--f-pink)", "var(--f-white)", "さくら", "var(--f-white)"),
    "fes": ("var(--f-coral)", "var(--f-yel-3)", "夏まつり", "var(--f-white)"),
    "shell": ("var(--f-mint)", "var(--f-white)", "SEA", "var(--f-navy)"),
}


def banner_e(cv, u0, u1, z0, z1, design):
    bg, acc, txt, fg = BANNERS[design]
    cv.rect(u0, z0, u1, z1, "", f' style="fill:{bg};stroke:var(--ink);stroke-width:.7"')
    w = u1 - u0
    cv.circle((u0 + u1) / 2, z1 - w * .65, w * .3, "", f' style="fill:{acc}"')
    wave(cv, u0 + w * .15, u1 - w * .15, z0 + .3, .04, 2, "e-led")
    for i, ch in enumerate(txt if len(txt) <= 4 else [txt]):
        if len(txt) <= 4:
            stext(cv, (u0 + u1) / 2, z1 - w * 1.5 - i * w * .62, ch, w * .38, fill=fg, weight=800,
                  family="var(--f-body)" if not txt.isascii() else "var(--f-cond)")
        else:
            stext(cv, (u0 + u1) / 2, z0 + (z1 - z0) * .45, ch, w * .3, fill=fg, weight=800, family="var(--f-cond)", rot=-90)


def lamp_post(cv, u, z, h=6.2, banner=None, signs=None):
    """Post-top lantern lamp centred on the pole, with a bracket carrying two banners (and finger signs)."""
    cv.rect(u - .1, z, u + .1, z + 1.3, "e-yel")
    cv.rect(u - .07, z + 1.3, u + .07, z + h, "e-dark")
    cv.rect(u - .16, z, u + .16, z + .3, "e-dark")
    # lantern head: collar, glass lamp, cap
    cv.rect(u - .12, z + h, u + .12, z + h + .14, "e-dark")
    cv.poly([(u - .16, z + h + .14), (u + .16, z + h + .14), (u + .24, z + h + .82), (u - .24, z + h + .82)], "e-glow")
    cv.poly([(u - .16, z + h + .14), (u + .16, z + h + .14), (u + .24, z + h + .82), (u - .24, z + h + .82)], "e-out")
    cv.poly([(u - .32, z + h + .82), (u + .32, z + h + .82), (u + .1, z + h + 1.0), (u - .1, z + h + 1.0)], "e-dark")
    if banner:
        b0, b1, designs = banner
        cv.rect(u - 1.25, b1, u + 1.25, b1 + .05, "e-yel")
        cv.rect(u - 1.25, b0 - .05, u + 1.25, b0, "e-yel")
        banner_e(cv, u - 1.15, u - .2, b0, b1, designs[0])
        banner_e(cv, u + .2, u + 1.15, b0, b1, designs[1])
    if signs:
        for i, (lab, d) in enumerate(signs):
            zc = z + 2.6 - i * .45
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
ARC_STEP = 4.4       # half width of the entrance steps on the east face
ARC_PLANTERS = [(1.0, 8.6), (18.1, 26.0)]   # planter boxes against the east face, u from the south corner (m)
ARC_PLANTER_D, ARC_PLANTER_H = 1.2, .6


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
    # steps at the doors (3R x 0.15), planter boxes against the facade either side
    cv.rect(c - ARC_STEP, Z_PL, c + ARC_STEP, Z_FFL, "e-conc")
    for k in (1, 2):
        cv.line(c - ARC_STEP + k * .12, Z_PL + k * .15, c + ARC_STEP - k * .12, Z_PL + k * .15, "e-mull")
    for (u0, u1) in ARC_PLANTERS:
        cv.rect(u0, Z_PL, u1, Z_PL + ARC_PLANTER_H, "e-conc")
        shrubs_e(cv, u0 + .1, u1 - .2, Z_PL + ARC_PLANTER_H - .05, .6, int(u0 * 7))


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
    cv.rect(27.08, Z_PL, 30.2, 12.6, "e-plaster")
    gold_line(cv, 27.08, 30.2, 8.45)
    glazing(cv, 27.6, Z_PL, 30.2, 7.75, 2)
    glazing(cv, 27.6, 8.7, 30.2, 11.05, 2)
    kawara(cv, 27.08, 30.6, 12.6)
    break_line(cv, 30.2, Z_PL, 13.2)
    cv.text(28.7, 13.85, "FASHION & GOODS (A-502)", "t-sm halo")
    # main red body
    cv.rect(0, Z_PL, 27.08, Z_PAR, "e-arc")
    cv.rect(0, Z_PL, 27.08, Z_PAR, "", ' fill="url(#ce-clad)"')
    cv.rect(0, 9.72, 27.08, 9.92, "e-yel")
    cv.rect(0, Z_PAR - .12, 27.08, Z_PAR, "e-dark")
    for (a, b) in ((0, .55), (26.53, 27.08)):
        cv.rect(a, Z_PL, b, Z_PAR, "e-arc2")
    cv.rect(0, Z_PL, 27.08, Z_FFL, "e-conc")
    # outer bays: portholes and wave planters
    for u in (2.1, 4.4, 22.3, 24.6):
        porthole(cv, u, 8.55, .62)
    for u in (2.1, 4.4, 22.1):
        cv.rect(u - .7, 5.0, u + .7, 6.6, "e-arc2")
        cv.rect(u - .55, 5.15, u + .55, 6.45, "e-glass")
        cv.line(u - .3, 5.4, u + .1, 6.2, "e-hl")
    # spotlights on the parapet, aimed down at the sign
    for (u, f) in ((7.0, 1), (10.6, 1), (16.0, -1), (19.6, -1)):
        spotlight(cv, u, Z_PAR + .45, f)
    arcade_controller(cv)
    arcade_front_lower(cv)
    # strip annex end (prize corner), south, same face line
    cv.rect(-3.33, Z_PL, 0, 7.2, "e-arc")
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
    lamp_post(cv, 26.4, Z_PL, 6.3, banner=(6.6, 9.3, ("games", "umi")),
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
    cv.rect(13.75, Z_PL, 47.92, Z_PAR, "e-arc")
    cv.rect(13.75, Z_PL, 47.92, Z_PAR, "", ' fill="url(#ce-clad)"')
    cv.rect(13.75, 9.72, 47.92, 9.92, "e-yel")
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
    cv.rect(13.75, Z_PL, 47.92, 7.2, "e-arc")
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
    cv.rect(0, 4.4, 27.08, Z_PAR, "e-arc")
    cv.rect(0, 4.4, 27.08, Z_PAR, "", ' fill="url(#ce-clad)"')
    cv.rect(0, 9.72, 27.08, 9.92, "e-yel")
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
    cv.rect(27.08, lane_z(66.5), 30.41, 7.2, "e-arc")
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
    key = colour_key(root, 850, 760, [("e-arc", "Arcade red · fibre-cement panels"), ("e-yel", "Controller sign, trim band"), ("e-cream", "Cream GRC · controller grips"),
                                      ("e-dark", "Graphite · D-pad, frames, coping"), ("e-blue", "Button blue"),
                                      ("e-red", "Button red"), ("e-green", "Button green"),
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


# ================================================================ shop kit
# Japanese shopping-street facade, after the shop reference (a Korean mall front):
# white plaster, a kawara tile eave, an LED ticker band, a big ring logo, speech-bubble
# and cloud signs, vertical katakana, a disc-tile panel, a framed portal with speakers,
# a gold mid line - plus noren curtains, chochin lanterns and hanging kanban.
def kawara(cv, u0, u1, z, h=.62, glaze="e-kawara"):
    """Kawara tile eave seen from the front: tile face, round tile ends, ridge and oni end tiles."""
    cv.rect(u0, z - .45, u1, z, "e-shadow")
    cv.poly([(u0 - .35, z), (u1 + .35, z), (u1 + .15, z + h), (u0 - .15, z + h)], glaze)
    for u in frange(u0 - .05, u1 + .2, .32):
        cv.line(u, z + .14, u + .04, z + h - .02, "e-tile")
    for u in frange(u0 - .25, u1 + .3, .32):
        cv.circle(u, z + .07, .11, glaze)
    cv.rect(u0 - .15, z + h, u1 + .15, z + h + .15, "e-kawara")
    for u in (u0 - .4, u1 + .4):
        cv.poly([(u - .24, z), (u + .24, z), (u + .2, z + h + .32), (u, z + h + .5), (u - .2, z + h + .32)], "e-kawara")


def led_band(cv, u0, u1, z0, z1, text):
    cv.rect(u0, z0, u1, z1, "e-dark")
    cv.rect(u0 + .07, z0 + .07, u1 - .07, z1 - .07, "", ' style="fill:none;stroke:var(--f-steel);stroke-width:.6"')
    stext(cv, u0 + .3, z0 + (z1 - z0) * .3, text, (z1 - z0) * .42, fill="var(--f-led)", weight=700, family="var(--f-cond)",
          anchor="start", ls=.04)


def gold_line(cv, u0, u1, z):
    cv.rect(u0, z - .05, u1, z + .05, "e-gold")


def ring_logo(cv, u, z, R, color="var(--f-indigo)", notch=80):
    r = R * .55
    rm, sw = (R + r) / 2, (R - r) * abs(cv.sx)
    C = 2 * math.pi * rm * abs(cv.sx)
    x, y = cv.X(u), cv.Y(z)
    cv.add(f'<circle cx="{n(x + 2)}" cy="{n(y + 2)}" r="{n(rm * abs(cv.sx))}" class="e-shadow" style="fill:none;stroke:var(--ink);'
           f'stroke-width:{n(sw)}px;stroke-dasharray:{n(C * .88)} {n(C * .12)}" transform="rotate({notch} {n(x)} {n(y)})"/>')
    cv.add(f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(rm * abs(cv.sx))}" style="fill:none;stroke:{color};stroke-width:{n(sw)}px;'
           f'stroke-dasharray:{n(C * .88)} {n(C * .12)}" transform="rotate({notch} {n(x)} {n(y)})"/>')


def bubble(cv, u0, z0, w, h, dots="..."):
    cv.poly([(u0 + w * .2, z0 + .05), (u0 + w * .14, z0 - .42), (u0 + w * .38, z0 + .05)], "e-white-o")
    rrect(cv, u0, z0, u0 + w, z0 + h, .28, "e-white-o")
    cv.rect(u0 + w * .19, z0 - .02, u0 + w * .37, z0 + .1, "e-white")
    for k in (-1, 0, 1):
        cv.circle(u0 + w / 2 + k * w * .17, z0 + h / 2, min(w, h) * .085, "e-dark")


def vkana(cv, u, z_top, chars, cap, fill="var(--f-orange)", weight=800):
    for i, ch in enumerate(chars):
        stext(cv, u, z_top - (i + 1) * cap * 1.14, ch, cap, fill=fill, weight=weight, family="var(--f-body)")


def hang_sign(cv, u, z_top, text, w=.6, side=-1):
    h = len(text) * .56 + .3
    cv.line(u + side * (w / 2 + .35), z_top + .12, u + side * w / 2, z_top + .12, "e-mull-t")
    cv.rect(u - w / 2, z_top - h, u + w / 2, z_top, "e-white-o")
    cv.rect(u - w / 2 + .07, z_top - h + .07, u + w / 2 - .07, z_top - .07, "", ' style="fill:none;stroke:var(--f-dark);stroke-width:.7"')
    for i, ch in enumerate(text):
        stext(cv, u, z_top - .2 - (i + 1) * .56 + .06, ch, .38, fill="var(--f-dark)", weight=700, family="var(--f-body)")


def disc_panel(cv, u0, z0, u1, z1, cols, rows, base="e-indigo", seed=0):
    cv.rect(u0, z0, u1, z1, base)
    cw, rh = (u1 - u0) / cols, (z1 - z0) / rows
    r = min(cw, rh) * .38
    styles = ("gold", "ring", "silver", "deep")
    for i in range(cols):
        for j in range(rows):
            u, z = u0 + (i + .5) * cw, z0 + (j + .5) * rh
            st = styles[(i * 3 + j * 2 + seed) % 4]
            if st == "gold":
                cv.circle(u, z, r, "", ' style="fill:var(--f-gold);stroke:var(--ink);stroke-width:.6"')
            elif st == "silver":
                cv.circle(u, z, r, "e-steel")
                cv.circle(u, z, r * .35, "", ' style="fill:var(--f-cream-2)"')
            elif st == "ring":
                cv.circle(u, z, r, "e-cream")
                cv.circle(u, z, r * .55, base)
            else:
                cv.circle(u, z, r, "", ' style="fill:var(--f-dark);opacity:.35"')


def noren(cv, u0, u1, z_top, drop, cls="e-indigo", mark="ring", text=None, panels=3):
    cv.rect(u0 - .2, z_top - .04, u1 + .2, z_top + .06, "e-wood")
    w = (u1 - u0) / panels
    for i in range(panels):
        a = u0 + i * w + (.03 if i else 0)
        b = u0 + (i + 1) * w - (.03 if i < panels - 1 else 0)
        cv.rect(a, z_top - drop, b, z_top - .04, cls)
    um, zm = (u0 + u1) / 2, z_top - drop * .48
    if mark == "ring":
        cv.circle(um, zm, drop * .26, "", ' style="fill:none;stroke:var(--f-white);stroke-width:2.2"')
        cv.circle(um, zm, drop * .1, "e-white")
    if text:
        stext(cv, um, z_top - drop * .82, text, drop * .14, fill="var(--f-white)", weight=700, family="var(--f-body)")


def chochin(cv, u, z, r=.3, h=.72, cls="e-verm"):
    cv.line(u, z + h / 2, u, z + h / 2 + .28, "e-mull")
    cv.ellipse(u, z, r, h / 2, cls)
    for k in (-.25, 0, .25):
        cv.line(u - r * math.sqrt(1 - (k * 2) ** 2) * .98, z + k * h, u + r * math.sqrt(1 - (k * 2) ** 2) * .98, z + k * h, "e-joint")
    cv.rect(u - r * .55, z + h / 2 - .07, u + r * .55, z + h / 2 + .03, "e-dark")
    cv.rect(u - r * .55, z - h / 2 - .03, u + r * .55, z - h / 2 + .07, "e-dark")


def cloud_badge(cv, u, z, w, h, txt, fill="var(--f-blue)"):
    lobes = [(-.32, .1, .3), (-.05, .28, .34), (.28, .14, .3), (.0, -.12, .3), (-.3, -.14, .22), (.32, -.12, .24)]
    for dx, dz, rr in lobes:
        cv.ellipse(u + dx * w + .25, z + dz * h - .2, rr * w, rr * h * 1.25, "", ' style="fill:var(--f-steel);opacity:.55"')
    for dx, dz, rr in lobes:
        cv.ellipse(u + dx * w, z + dz * h, rr * w + .05, rr * h * 1.25 + .05, "", ' style="fill:var(--ink)"')
    for dx, dz, rr in lobes:
        cv.ellipse(u + dx * w, z + dz * h, rr * w, rr * h * 1.25, "", f' style="fill:{fill}"')
    stext(cv, u, z - h * .12, txt, h * .3, fill="var(--f-white)", weight=700, family="var(--f-body)")


def heart(cv, u, z, s, fill="var(--f-red)"):
    cv.path([("M", u, z - s * .55), ("C", u - s * 1.1, z + s * .1, u - s * .5, z + s * .75, u, z + s * .3),
             ("C", u + s * .5, z + s * .75, u + s * 1.1, z + s * .1, u, z - s * .55), ("Z",)], "",
            f' style="fill:{fill};stroke:var(--ink);stroke-width:.9"')


def red_panel(cv, u0, z0, u1, z1, txt):
    cv.rect(u0, z0, u1, z1, "e-red")
    cv.circle((u0 + u1) / 2 - (u1 - u0) * .18, (z0 + z1) / 2 + .12, (z1 - z0) * .34, "e-white")
    heart(cv, (u0 + u1) / 2 - (u1 - u0) * .18, (z0 + z1) / 2 + .1, (z1 - z0) * .22)
    stext(cv, (u0 + u1) / 2 + (u1 - u0) * .2, (z0 + z1) / 2 - (z1 - z0) * .1, txt, (z1 - z0) * .24, fill="var(--f-white)",
          weight=800, family="var(--f-body)")


def stickers(cv, u0, z0, u1, z1, n=6, seed=0):
    """Cute stickers on shop glass, as in the shop reference."""
    rnd = random.Random(seed)
    for i in range(n):
        u, z = rnd.uniform(u0 + .2, u1 - .4), rnd.uniform(z0 + .6, min(z1 - .3, z0 + 2.0))
        k = i % 4
        if k == 0:
            cv.circle(u, z, .16, "e-red")
            cv.rect(u - .03, z - .1, u + .03, z + .1, "e-white")
        elif k == 1:
            rrect(cv, u - .17, z - .13, u + .17, z + .13, .04, "e-white-o")
            cv.circle(u, z, .06, "e-pink")
        elif k == 2:
            heart(cv, u, z, .14, "var(--f-pink)")
        else:
            cv.rect(u - .14, z - .18, u + .14, z + .18, "e-yel")
            cv.circle(u, z + .02, .07, "e-dark")


def portal(cv, u0, u1, z0, z_door, z_top, inner="e-glow"):
    """Framed shop portal: grey surround, tiled head with a speaker either side, glass doors."""
    cv.rect(u0, z0, u1, z_top, "e-portal")
    cv.rect(u0 + .3, z_door + .25, u1 - .3, z_top - .2, "e-white")
    for uu in frange(u0 + .3, u1 - .29, .5):
        cv.line(uu, z_door + .25, uu, z_top - .2, "e-joint")
    for zz in frange(z_door + .25, z_top - .19, .5):
        cv.line(u0 + .3, zz, u1 - .3, zz, "e-joint")
    for uu in (u0 + .35, u1 - .95):
        cv.rect(uu, z_door + .3, uu + .6, z_door + .95, "e-dark")
        cv.circle(uu + .3, z_door + .62, .2, "e-steel")
    cv.rect(u0 + .3, z0, u1 - .3, z_door, inner)
    glazing(cv, u0 + .3, z0, u1 - .3, z_door, 2, inner="e-glass-t")


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
    cv.rect(u0, z0, u1, Z_PAR, "e-arc")
    cv.rect(u0, 9.72, u1, 9.92, "e-yel")
    cv.rect(u0, Z_PAR - .12, u1, Z_PAR, "e-dark")
    glass_rail(cv, u0, u1, Z_PAR, Z_RAIL - Z_PAR)
    if portholes:
        for u in frange(u0 + 1.5, u1 - .7, 3.0):
            porthole(cv, u, 8.55, .66)


def fashion_east():
    sx = 14.0
    cv = Cv(sx, -sx, 150 + 3.0 * sx, 250, 0, Z_PL)
    cv.rect(-3.0, Z_PL, 21.5, 14.6, "e-sky")
    # beyond (north): kiosk strip on its retaining wall, railing and trees
    cv.rect(17.5, Z_PL, 21.5, Z_UP, "beyond")
    cv.line(17.5, Z_UP + 1.1, 21.5, Z_UP + 1.1, "e-out")
    for u in frange(17.9, 21.5, 1.0):
        cv.line(u, Z_UP, u, Z_UP + 1.1, "e-mull")
    tree_elev(cv, 20.3, Z_UP, 6.0, 5.0, 51)
    arcade_stub(cv, -3.0, 0)
    break_line(cv, -3.0, Z_PL, Z_RAIL)
    # white plaster body, gold line at the upper floor, LED ticker, kawara eave
    cv.rect(0, Z_PL, 17.5, Z_FROOF, "e-plaster")
    gold_line(cv, 0, 17.5, Z_UP + .05)
    led_band(cv, .6, 16.9, 11.3, 11.95, "いらっしゃいませ · WELCOME · NEW ARRIVALS · ようこそ · SALE")
    kawara(cv, 0, 17.5, Z_FROOF)
    # big ring logo, speech bubble, vertical katakana at the corner
    ring_logo(cv, 9.6, 9.75, 1.45)
    bubble(cv, 12.0, 9.25, 2.6, 1.35)
    vkana(cv, 16.75, 11.0, "ファッション", .52)
    stext(cv, 16.75, 7.55, "雑貨", .5, fill="var(--f-dark)", weight=800, family="var(--f-body)")
    # glazed stair core above the entrance
    glazing(cv, .5, 8.7, 5.3, 11.05, 3)
    dogleg(cv, .8, 5.0, 8.7, 11.0)
    # SE corner portal with noren and lanterns, disc-tile panel, display window
    portal(cv, .5, 5.3, Z_PL, 6.25, 7.75)
    noren(cv, .85, 4.95, 6.25, .8, "e-indigo", "ring")
    for u in (.3, 5.5):
        chochin(cv, u, 6.75)
    disc_panel(cv, 5.8, Z_PL + .1, 9.6, 7.5, 3, 4, "e-indigo", 1)
    stext(cv, 7.7, 7.7, "GOODS", .32, fill="var(--f-indigo)", weight=800)
    cv.rect(10.1, Z_PL, 16.2, 7.4, "e-glow")
    for u in (11.2, 13.2, 15.2):
        avatar_p(cv, u, Z_PL + .1, 1.75, 0)
    glazing(cv, 10.1, Z_PL, 16.2, 7.4, 3, inner="e-glass-t")
    stickers(cv, 10.1, Z_PL, 16.2, 7.4, 7, 3)
    # (the two planters in front were merged into one planter at the street wall, so the shop front is clear)
    ground(cv, -3.0, 21.5, Z_PL, .5)
    hdim(cv, 0, 17.5, 2.6, "17.50 FASHION & GOODS")
    vdim(cv, 18.0, Z_PL, Z_FROOF + .77, "9.77", side=1)
    level_tags(cv, -3.15, [(Z_PL, "+3.60"), (Z_UP, "+8.40 UPPER FLOOR"), (Z_FROOF, "+12.60 EAVE")])
    note(cv, 6.5, 14.3, 9.6, 11.2, "Ring logo Ø2.9 · LED ticker · kawara eave", "start")
    panel_title(cv, -3.0, 1.45, "4", "FASHION & GOODS · EAST · FRONT", "looking west · portal with noren at the SE corner, disc-tile panel · shop front kept clear")
    return cv


def fashion_west():
    sx = 14.0
    cv = Cv(sx, -sx, 700 + 2.0 * sx, 250, 0, Z_PL)
    U = lambda y: y - 20.0  # noqa: E731  (left = north)
    cv.rect(-2.0, 5.0, 21.0, 14.6, "e-sky")
    arcade_stub(cv, 17.5, 21.0, 4.4)
    cv.rect(0, 5.2, 17.5, Z_FROOF, "e-plaster")
    gold_line(cv, 0, 17.5, Z_UP + .05)
    kawara(cv, 0, 17.5, Z_FROOF)
    for a in (3.2, 8.0, 12.8):
        cv.rect(a - .12, 9.18, a + 2.52, 11.82, "e-dark")
        glazing(cv, a, 9.3, a + 2.4, 11.7, 1)
    for u in (.3, 17.2):
        cv.rect(u - .07, 5.2, u + .07, Z_FROOF - .1, "e-steel")
    for u in (6.0, 10.9):
        cv.rect(u - .55, 7.6, u + .55, 8.3, "e-steel")
        cv.circle(u, 7.95, .25, "e-joint")
    zl = lane_z(21.0)
    cv.rect(.8, Z_UP, 2.0, Z_UP + 2.2, "e-steel")
    for k in range(4):
        cv.rect(.6, zl + k * .155, 2.4 + (3 - k) * .3, zl + (k + 1) * .155, "e-conc")
    hang_sign(cv, 3.0, 11.0, "裏口", side=-1)
    ground(cv, -2.0, 21.0, 0, .6, lane_profile(U, 18.0, 41.0, 1.2))
    hdim(cv, 0, 17.5, 3.1, "17.50")
    level_tags(cv, -2.15, [(lane_z(20.0), f"+{lane_z(20.0):.2f} LANE"), (Z_UP, "+8.40"), (Z_FROOF, "+12.60")])
    panel_title(cv, -2.0, 1.9, "6", "FASHION & GOODS · WEST · BACK", f"looking east · lane +{lane_z(20.0):.2f} → +{lane_z(37.5):.2f}")
    return cv


def fashion_north():
    sx = 14.0
    cv = Cv(sx, -sx, 150 + 8.0 * sx, 480, 0, Z_UP)
    # u = 47.92 - x (left = east end on the plaza side, right = west end at the lane)
    cv.rect(-8.0, Z_UP, 36.5, 15.0, "e-sky")
    glass_rail(cv, .4, 12.9, Z_FROOF + .77, 1.1)
    cv.rect(0, Z_UP, 34.17, Z_FROOF, "e-plaster")
    gold_line(cv, 0, 34.17, 9.0)
    led_band(cv, 3.0, 31.2, 11.35, 11.95, "海辺のファッション＆雑貨 · SEASIDE FASHION & GOODS · いらっしゃいませ · OPEN 10:00–21:00 · WELCOME")
    kawara(cv, 0, 34.17, Z_FROOF)
    vkana(cv, 1.0, 11.1, "ファッション", .4)
    ring_logo(cv, 5.4, 10.2, 1.05)
    bubble(cv, 7.6, 9.75, 2.2, 1.1)
    stext(cv, 15.4, 9.9, "FASHION & GOODS", .55, fill="var(--f-indigo)", weight=800)
    for a in frange(22.0, 33.0, 2.6):
        cv.rect(a - .1, 9.3, a + 1.9, 10.9, "e-dark")
        glazing(cv, a, 9.4, a + 1.8, 10.8, 1)
    hang_sign(cv, 33.6, 11.0, "服", side=1)
    # kiosks in front (dashed) and the planted strip along the face
    for (a, b_, lab) in ((12.4, 17.4, "KIOSK 3"), (17.4, 28.4, "KIOSK 2"), (28.4, 34.6, "KIOSK 1")):
        cv.rect(a, Z_UP, b_, Z_UP + 3.0, "e-ghost")
        cv.line(a, Z_UP + 2.3, b_, Z_UP + 2.3, "e-ghost")
        cv.text((a + b_) / 2, Z_UP + 1.3, lab + " in front", "t-sm halo")
    shrubs_e(cv, -7.4, 34.2, Z_UP + .5, .7, 53)
    cv.rect(-7.4, Z_UP, 34.25, Z_UP + .5, "e-conc")
    cv.line(-7.4, Z_UP + 1.6, 0, Z_UP + 1.6, "e-out")
    for u in frange(-7.2, 0, 1.0):
        cv.line(u, Z_UP + .5, u, Z_UP + 1.6, "e-mull")
    tree_elev(cv, -4.5, Z_UP, 6.5, 5.5, 54)
    ground(cv, -8.0, 36.5, 0, .5, [(-8.0, Z_UP), (34.17, Z_UP), (34.3, lane_z(20.2)), (36.5, lane_z(20.2))])
    hdim(cv, 0, 34.17, 7.55, "34.17")
    level_tags(cv, -8.15, [(Z_UP, "+8.40 KIOSK STRIP"), (Z_FROOF, "+12.60 EAVE")])
    note(cv, 1.0, 15.5, 6.0, Z_FROOF + 1.6, "Roof deck rail behind the eave", "start")
    panel_title(cv, -8.0, 6.25, "5", "FASHION & GOODS · NORTH · SIDE TO THE STREET", "looking south from the kiosk strip · the billboard face for arrivals from Spawn A")
    return cv


def cup_logo(cv, u, z, r):
    """Round café mark: white disc, dark ring, coffee cup with steam."""
    cv.circle(u, z, r, "e-white-o")
    cv.circle(u, z, r * .86, "", ' style="fill:none;stroke:var(--f-dark);stroke-width:1.2"')
    rrect(cv, u - r * .38, z - r * .42, u + r * .28, z + r * .12, r * .1, "e-dark")
    cv.add(f'<circle cx="{n(cv.X(u + r * .32))}" cy="{n(cv.Y(z - r * .14))}" r="{n(r * .14 * abs(cv.sx))}" '
           f'style="fill:none;stroke:var(--f-dark);stroke-width:{n(r * .07 * abs(cv.sx))}px"/>')
    cv.rect(u - r * .5, z - r * .52, u + r * .4, z - r * .46, "e-dark")
    for k in (-.18, 0, .18):
        cv.path([("M", u + k * r - .02, z + r * .2), ("Q", u + k * r + r * .1, z + r * .35, u + k * r - .02, z + r * .52)], "",
                ' style="fill:none;stroke:var(--f-dark);stroke-width:1"')


def wave_mark(cv, u, z, s):
    cv.path([("M", u - s, z - s * .35), ("Q", u - s * .55, z + s * .55, u + s * .1, z + s * .38), ("Q", u + s * .6, z + s * .2, u + s * .35, z - .02),
             ("Q", u + s * .1, z + s * .18, u - s * .05, z - .02), ("Q", u + s * .6, z - s * .1, u + s, z - s * .35), ("Z",)], "",
            ' style="fill:var(--f-blue);stroke:var(--ink);stroke-width:.7"')


def rail_black(cv, u0, u1, z, h=1.05):
    for u in frange(u0, u1 + .01, 1.2):
        cv.rect(u - .04, z, u + .04, z + h, "e-dark")
    for zz in (z + .35, z + .7):
        cv.line(u0, zz, u1, zz, "e-mull-t")
    cv.rect(u0 - .05, z + h - .02, u1 + .05, z + h + .1, "e-wood")


def chair_e(cv, u, z, face=1):
    cv.rect(u - .22, z + .44, u + .22, z + .5, "e-wood")
    cv.rect(u - face * .22 - .03, z, u - face * .22 + .03, z + .95, "e-wood")
    cv.rect(u + face * .2 - .03, z, u + face * .2 + .03, z + .47, "e-wood")


def table_set(cv, u, z, parasol=True):
    if parasol:
        parasol_e(cv, u, z, 1.45, 2.4, "e-white")
    cv.rect(u - .5, z + .72, u + .5, z + .78, "e-wood")
    cv.rect(u - .04, z, u + .04, z + .72, "e-dark")
    chair_e(cv, u - .85, z, 1)
    chair_e(cv, u + .85, z, -1)


def roof_terrace_back(cv, u0, u1, z, parasols):
    """What shows above a roof-terrace railing: parasols, chair backs, flower planters."""
    for u in parasols:
        parasol_e(cv, u, z, 1.3, 2.35, "e-white")
        chair_e(cv, u - .8, z, 1)
        chair_e(cv, u + .8, z, -1)


def flower_box(cv, u0, u1, z, seed=0):
    rnd = random.Random(seed)
    shrubs_e(cv, u0 + .05, u1 - .2, z + .45, .6, seed)
    for _ in range(int((u1 - u0) * 2.5)):
        cv.circle(rnd.uniform(u0 + .1, u1 - .1), z + rnd.uniform(.75, 1.15), .07, ("e-pink", "e-yel3", "e-white")[_ % 3])
    cv.rect(u0, z, u1, z + .45, "e-wood")


def cafe_glass(cv, u0, u1, z0, z1, panels):
    cv.rect(u0, z0, u1, z1, "e-glow")
    w = (u1 - u0) / panels
    for i in range(panels):
        uc = u0 + (i + .5) * w
        cv.line(uc, z1, uc, z1 - .55, "e-mull")
        cv.circle(uc, z1 - .62, .1, "e-yel3")
        if i % 2 == 0:
            cv.rect(uc - .45, z0 + .72, uc + .45, z0 + .78, "e-wood")
            cv.rect(uc - .04, z0, uc + .04, z0 + .72, "e-wood")
    cv.rect(u0, z0, u1, z1, "", ' style="fill:var(--f-glass);fill-opacity:.25"')
    for i in range(1, panels):
        cv.line(u0 + i * w, z0, u0 + i * w, z1, "e-mull")
    cv.rect(u0, z0, u1, z1, "", ' style="fill:none;stroke:var(--f-dark);stroke-width:1.4"')
    for i in range(panels):
        cv.line(u0 + i * w + w * .25, z0 + (z1 - z0) * .25, u0 + i * w + w * .5, z0 + (z1 - z0) * .7, "e-hl")


def timber_fascia(cv, u0, u1, z0, z1, logo=True, text="SEASIDE CAFE"):
    cv.rect(u0, z0 - .22, u1, z0, "e-shadow")
    cv.rect(u0, z0, u1, z1, "e-wood-d")
    for zz in frange(z0 + .17, z1, .17):
        cv.line(u0, zz, u1, zz, "e-joint")
    if logo:
        cup_logo(cv, u0 + (z1 - z0) * .75, (z0 + z1) / 2, (z1 - z0) * .36)
    if text:
        stext(cv, (u0 + u1) / 2 + (z1 - z0) * .4, (z0 + z1) / 2 - (z1 - z0) * .16, text, (z1 - z0) * .32, weight=700,
              family="var(--f-cond)", ls=.08)


def cafe_pier(cv, u0, u1, z0, z1, lines=True):
    cv.rect(u0, z0, u1, z1, "e-plaster")
    for zz in frange(z0 + .9, z1, .9):
        cv.line(u0, zz, u1, zz, "e-joint")
    if lines:
        for i, t in enumerate(("コーヒー", "スイーツ", "やすらぎ")):
            stext(cv, (u0 + u1) / 2, 7.05 - i * .48, t, .3, fill="var(--f-dark)", weight=700, family="var(--f-body)")
        wave_mark(cv, (u0 + u1) / 2, 4.95, .55)


def cafe_south():
    sx = 14.0
    cv = Cv(sx, -sx, 150 + 3.0 * sx, 700, 0, Z_PL)
    # u = x - 13.75 (left = west / lane)
    cv.rect(-3.0, Z_PL, 27.0, 12.0, "e-sky")
    # arcade beyond, above the café roof terrace
    cv.rect(0, 8.0, 27.0, Z_PAR, "e-arc")
    cv.rect(0, 9.72, 27.0, 9.92, "e-yel")
    cv.rect(0, Z_PAR - .12, 27.0, Z_PAR, "e-dark")
    glass_rail(cv, 0, 27.0, Z_PAR, Z_RAIL - Z_PAR)
    for u in frange(2.85, 26.5, 3.0):
        porthole(cv, u, 8.85, .5)
    cv.text(25.0, 11.75, "ARCADE beyond", "t-sm halo")
    roof_terrace_back(cv, 0, 23.33, Z_CROOF + .2, (4.0, 10.5, 17.0))
    # café: light stone, coping, roof-terrace railing with flower boxes
    cv.rect(0, Z_PL, 23.33, Z_CROOF + .2, "e-plaster")
    cv.rect(0, Z_CROOF, 23.33, Z_CROOF + .2, "", ' style="fill:var(--f-cream-2);stroke:var(--ink);stroke-width:.7"')
    rail_black(cv, .2, 23.1, Z_CROOF + .2)
    flower_box(cv, 1.0, 3.0, Z_CROOF + .2, 63)
    flower_box(cv, 19.6, 21.6, Z_CROOF + .2, 64)
    glazing(cv, .8, 5.0, 2.4, 6.6, 1)
    shrubs_e(cv, 0, 2.9, Z_PL, .8, 61)
    # full-height glass under a deep timber fascia with the sign; corner pier
    cafe_glass(cv, 3.6, 20.6, Z_PL, 6.0, 7)
    timber_fascia(cv, 3.25, 20.8, 6.15, 7.55)
    for u in frange(4.0, 20.4, 1.6):
        cv.circle(u, 6.08, .05, "e-yel3")
    cafe_pier(cv, 20.8, 23.33, Z_PL, Z_CROOF + .2)
    # terrace: white parasols with wooden tables and chairs, menu board, planters
    table_set(cv, 7.4, Z_PL)
    table_set(cv, 16.25, Z_PL)
    table_set(cv, 26.0, Z_PL)
    aframe(cv, 22.2, Z_PL, ("MENU", "COFFEE", "SWEETS"))
    flower_box(cv, 23.4, 24.9, Z_PL, 65)
    avatar_p(cv, 11.6, Z_PL, 1.68, 7)
    ground(cv, -3.0, 27.0, Z_PL, .5)
    cv.rect(3.0, Z_PL - .18, 27.0, Z_PL, "e-wood")
    hdim(cv, 0, 23.33, 2.95, "23.33 CAFÉ")
    hdim(cv, 3.25, 20.8, 2.3, "17.55 TIMBER CANOPY 2.5 DEEP")
    level_tags(cv, -3.15, [(Z_PL, "+3.60 TERRACE"), (Z_CROOF, "+7.80 ROOF TERRACE"), (Z_PAR, "+10.20")])
    note(cv, 4.5, 11.3, 6.0, 9.6, "Roof terrace: black rail, timber cap, white parasols", "start")
    panel_title(cv, -3.0, .55, "7", "CAFÉ · SOUTH · FRONT TO THE TERRACE",
                "looking north · white stone and timber, after the café reference · glass under a timber canopy, corner pier")
    return cv


def cafe_east():
    sx = 14.0
    cv = Cv(sx, -sx, 660 + 9.0 * sx, 700, 0, Z_PL)
    # u = 77.5 - y (left = south / terrace, right = north / strip and arcade)
    cv.rect(-9.0, Z_PL, 15.0, 12.0, "e-sky")
    cv.rect(12.5, Z_PL, 15.0, Z_PAR, "e-arc")
    cv.rect(12.5, 9.72, 15.0, 9.92, "e-yel")
    glass_rail(cv, 12.5, 15.0, Z_PAR, Z_RAIL - Z_PAR)
    break_line(cv, 15.0, Z_PL, Z_RAIL)
    cv.text(13.75, 11.75, "ARCADE", "t-sm halo")
    roof_terrace_back(cv, 0, 9.17, Z_CROOF + .2, (5.5,))
    cv.rect(0, Z_PL, 9.17, Z_CROOF + .2, "e-plaster")
    cv.rect(0, Z_CROOF, 9.17, Z_CROOF + .2, "", ' style="fill:var(--f-cream-2);stroke:var(--ink);stroke-width:.7"')
    rail_black(cv, .2, 9.0, Z_CROOF + .2)
    cafe_pier(cv, 0, 2.53, Z_PL, Z_CROOF + .2, lines=False)
    wave_mark(cv, 1.27, 6.6, .55)
    cafe_glass(cv, 2.9, 8.8, Z_PL, 6.0, 3)
    timber_fascia(cv, 2.53, 9.17, 6.15, 7.55, logo=True, text="")
    # prize & vending strip, nearer (east end on the plaza line)
    cv.rect(9.17, Z_PL, 12.5, 7.2, "e-arc")
    cv.rect(9.17, 6.9, 12.5, 7.2, "e-dark")
    glazing(cv, 9.5, Z_PL, 12.2, 6.1, 2, inner="e-glow")
    rrect(cv, 9.4, 6.25, 12.27, 6.8, .2, "e-pink-o")
    stext(cv, 10.83, 6.38, "PRIZE", .3, weight=800)
    table_set(cv, -1.0, Z_PL)
    table_set(cv, -6.5, Z_PL)
    avatar_p(cv, -3.7, Z_PL, 1.7, 8)
    ground(cv, -9.0, 15.0, Z_PL, .5)
    cv.rect(-9.0, Z_PL - .18, 9.17, Z_PL, "e-wood")
    hdim(cv, 0, 9.17, 2.6, "9.17 CAFÉ")
    level_tags(cv, -9.15, [(Z_PL, "+3.60"), (Z_CROOF, "+7.80")])
    panel_title(cv, -9.0, 1.35, "8", "CAFÉ · EAST · SIDE", "looking west across the terrace · corner pier, glass doors, timber band")
    return cv


def cafe_west():
    sx = 14.0
    cv = Cv(sx, -sx, 150 + 4.0 * sx, 910, 0, Z_PL)
    U = lambda y: y - 68.33  # noqa: E731  (left = north)
    cv.rect(-4.0, 3.9, 13.0, 12.0, "e-sky")
    arcade_stub(cv, -4.0, 0, 3.9)
    cv.rect(-3.33, 4.0, 0, 7.2, "e-arc")
    cv.rect(-3.33, 6.9, 0, 7.2, "e-dark")
    roof_terrace_back(cv, 0, 9.17, Z_CROOF + .2, (5.0,))
    cv.rect(0, 3.9, 9.17, Z_CROOF + .2, "e-plaster")
    cv.rect(0, Z_CROOF, 9.17, Z_CROOF + .2, "", ' style="fill:var(--f-cream-2);stroke:var(--ink);stroke-width:.7"')
    rail_black(cv, .2, 9.0, Z_CROOF + .2)
    cv.rect(2.3, Z_CROOF + .2, 2.6, 9.6, "e-steel")
    cv.rect(2.15, 9.6, 2.75, 9.8, "e-dark")
    cv.rect(.8, 6.1, 5.0, 6.9, "e-wood")
    glazing(cv, .95, 6.2, 4.85, 6.8, 3)
    cv.rect(3.4, 5.2, 4.6, 5.9, "e-steel")
    cv.circle(4.0, 5.55, .25, "e-joint")
    zl = lane_z(75.0)
    cv.rect(U(74.2), zl, U(75.3), zl + 2.2, "e-wood")
    cv.text(U(74.75), zl + 2.55, "KITCHEN", "t-sm halo")
    for u in (U(76.3), U(77.1)):
        cv.rect(u - .38, lane_z(77), u + .38, lane_z(77) + 1.1, "e-mint")
    shrubs_e(cv, 9.3, 12.8, lane_z(79.0), .8, 62)
    ground(cv, -4.0, 13.0, 0, .6, lane_profile(U, 64.33, 81.33, 1.2))
    hdim(cv, 0, 9.17, 2.9, "9.17")
    level_tags(cv, -4.15, [(lane_z(68.33), f"+{lane_z(68.33):.2f} LANE"), (Z_CROOF, "+7.80")])
    note(cv, 4.5, 11.4, 2.45, 9.7, "Kitchen flue", "start")
    panel_title(cv, -4.0, 2.1, "9", "CAFÉ · WEST · BACK",
                f"looking east · lane +{lane_z(68.33):.2f} → +{lane_z(77.5):.2f}, kitchen door 4R down inside")
    return cv


def sheet_a502():
    W, H = 1100, 1000
    root = Cv(1, 1, 0, 0)
    root.add(defs_e("ce"))
    root.add(f'<rect class="sheet-bg" width="{W}" height="{H}"/>')
    title_strip(root, 24, 30, "A-502", "FASHION & GOODS AND CAFÉ · ELEVATIONS",
                "Fashion & Goods after the shop reference, café after the café reference (white and wood) · footprints L-101 · levels L-202 · 14 px = 1 m")
    parts = [fashion_east(), fashion_west(), fashion_north(), cafe_south(), cafe_east(), cafe_west()]
    key = colour_key(root, 640, 790, [("e-plaster", "White plaster (shikkui finish)"), ("e-kawara", "Kawara tile eave"),
                                      ("e-indigo", "Indigo: ring logo, noren, disc panel"), ("e-gold", "Gold line"),
                                      ("e-dark", "LED ticker band"), ("e-wood-d", "Café timber fascia and canopy"), ("e-arc", "Arcade red"),
                                      ("e-glass", "Clear glazing")])
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


def life_main_upper(cv, u0, u1):
    cv.rect(u0, Z_PL, u1, Z_LROOF, "e-plaster")
    kawara(cv, u0, u1, Z_LROOF, h=.6, glaze="e-kawara-y")


def life_south():
    sx = 20.0
    cv = Cv(sx, -sx, 150 + 8.0 * sx, 290, 0, Z_PL)
    # u = x - 130.33 (left = west / plaza side)
    cv.rect(-8.0, Z_PL, 31.0, 11.0, "e-sky")
    cv.rect(8.83, Z_PL, 23.0, Z_ANNEX, "beyond")
    life_main_upper(cv, 0, 23.0)
    red_panel(cv, .6, 6.95, 5.6, 8.35, "おみやげ")
    stext(cv, 12.0, 7.95, "LIFESTYLE & SOUVENIR", .46, fill="var(--f-dark)", weight=800)
    stext(cv, 12.0, 7.3, "ライフスタイル＆おみやげ", .24, fill="var(--f-dark)", weight=700, family="var(--f-body)")
    cloud_badge(cv, 19.8, 7.65, 2.6, 1.2, "SOUVENIR")
    vkana(cv, 22.55, 8.55, "雑貨", .45, fill="var(--f-verm)")
    # canopy band, 4.2 m in front of the main face
    cv.rect(0, Z_PL, 23.0, Z_BAND, "e-plaster")
    gold_line(cv, 0, 23.0, Z_BAND - .3)
    cv.rect(0, Z_BAND - .25, 23.0, Z_BAND, "e-dark")
    shrubs_e(cv, 11.9, 18.8, Z_BAND, .7, 71)
    cv.rect(.17, 5.75, 8.83, Z_BAND - .35, "e-yel")
    stext(cv, 4.5, 5.85, "GOODS · HOME · GIFTS", .2, fill="var(--f-dark)", weight=700, family="var(--f-cond)")
    cv.rect(.5, Z_PL, 8.5, 5.7, "e-glow")
    glazing(cv, .5, Z_PL, 8.5, 5.7, 4, inner="e-glass-t")
    stickers(cv, 4.9, Z_PL, 8.5, 5.7, 5, 4)
    portal(cv, 8.95, 11.55, Z_PL, 5.25, 6.2)
    noren(cv, 9.25, 11.25, 5.25, .7, "e-verm", "ring", panels=2)
    disc_panel(cv, 19.4, 4.0, 22.7, 5.9, 4, 2, "e-verm", 2)
    # centre awning and the pink shop sign on posts (traced)
    cv.rect(11.67, 5.15, 19.17, 5.95, "e-yel")
    cv.rect(11.67, 5.15, 19.17, 5.95, "e-out")
    cv.rect(11.67, 4.8, 19.17, 5.15, "e-shadow")
    cv.rect(11.9, Z_PL, 19.0, 5.1, "e-glow")
    glazing(cv, 11.9, Z_PL, 19.0, 5.1, 4, inner="e-glass-t")
    for u in (12.6, 18.2):
        cv.rect(u - .06, Z_PL, u + .06, 4.4, "e-dark")
    rrect(cv, 12.0, 4.35, 18.8, 5.05, .15, "e-pink-o")
    stext(cv, 15.4, 4.5, "SOUVENIR", .38, weight=800)
    for u in (1.2, 4.5, 7.8, 19.9, 22.1):
        chochin(cv, u, 5.85 if u < 9 else 6.05, .26, .62)
    # forecourt: stall, photo statue, vending kiosk, planter box, heart sign
    stall_e(cv, .5, 4.67, Z_PL)
    cat_statue(cv, 9.84, Z_PL)
    cv.rect(21.0, Z_PL, 23.33, 5.4, "e-white")
    cv.rect(21.0, Z_PL, 23.33, 5.4, "e-out")
    cv.rect(21.3, 4.3, 23.0, 5.1, "e-blue")
    stext(cv, 22.15, 4.55, "DRINKS", .16, weight=700, family="var(--f-cond)")
    cv.rect(-2.06, Z_PL, -1.94, 6.2, "e-dark")
    heart(cv, -2.0, 6.6, .75)
    stext(cv, -2.0, 6.42, "すき", .22, fill="var(--f-white)", weight=800, family="var(--f-body)")
    parasol_e(cv, -4.8, Z_PL, 1.5, 2.4, "umb-y")
    tree_elev(cv, -6.6, Z_PL, 6.5, 4.5, 73)
    parasol_e(cv, 28.6, Z_PL, 1.5, 2.4, "umb-c")
    palm_elev(cv, 30.0, Z_PL, 6.5, 74)
    avatar_p(cv, 7.2, Z_PL, 1.65, 9)
    ground(cv, -8.0, 31.0, Z_PL, .5)
    hdim(cv, 0, 23.0, 2.85, "23.00 SHOP")
    hdim(cv, 11.67, 19.17, 2.35, "7.50 AWNING")
    vdim(cv, 23.9, Z_PL, Z_LROOF + .75, "5.85", side=1)
    level_tags(cv, -8.15, [(Z_PL, "+3.60"), (Z_BAND, "+6.60 CANOPY"), (Z_LROOF, "+8.70 EAVE")])
    note(cv, 13.0, 10.5, 12.0, Z_LROOF + .45, "Blue-glazed kawara eave on the traced trim line", "start")
    panel_title(cv, -8.0, .8, "10", "LIFESTYLE & SOUVENIR · SOUTH · FRONT", "looking north · red おみやげ panel, cloud badge, portal with noren, lanterns, stall and photo statue")
    return cv


def life_west():
    sx = 20.0
    cv = Cv(sx, -sx, 150 + 1.0 * sx, 575, 0, Z_PL)
    # u = y - 48 (left = north)
    cv.rect(-1.0, Z_PL, 33.0, 10.8, "e-sky")
    cv.rect(2.5, Z_PL, 7.0, Z_ANNEX, "beyond")
    cv.rect(.67, Z_ANNEX, 2.83, 8.2, "e-white")
    cv.rect(.67, Z_ANNEX, 2.83, 8.2, "e-out")
    life_main_upper(cv, 7.0, 23.67)
    gold_line(cv, 7.0, 23.67, 7.75)
    disc_panel(cv, 8.0, 4.3, 12.8, 7.3, 5, 3, "e-verm", 0)
    portal(cv, 13.5, 17.2, Z_PL, 6.3, 7.45)
    noren(cv, 13.85, 16.85, 6.3, .78, "e-verm", "ring")
    for u in (13.2, 17.5):
        chochin(cv, u, 6.75, .26, .62)
    glazing(cv, 18.0, 4.4, 23.0, 7.3, 3)
    bubble(cv, 18.6, 8.0, 1.9, .55)
    vkana(cv, 23.25, 8.45, "おみやげ", .38, fill="var(--f-verm)")
    # south band seen end-on, awning and sign beyond it
    cv.rect(23.67, Z_PL, 27.83, Z_BAND, "e-plaster")
    cv.rect(23.67, Z_BAND - .25, 27.83, Z_BAND, "e-dark")
    cv.poly([(27.83, 5.95), (29.67, 5.75), (29.67, 5.15), (27.83, 5.15)], "e-yel")
    cv.rect(29.6, Z_PL, 29.75, 5.05, "e-dark")
    cv.rect(29.67, 4.35, 31.33, 5.05, "e-pink-o")
    stall_e(cv, 27.83, 30.0, Z_PL)
    shrubs_e(cv, 2.7, 6.8, Z_PL + .6, .7, 75)                         # palm planter in the corner by the annex
    cv.rect(2.6, Z_PL, 6.9, Z_PL + .6, "e-conc")
    palm_elev(cv, 4.7, Z_PL + .6, 6.6, 81)
    parasol_e(cv, 20.0, Z_PL, 1.5, 2.4, "umb-y")
    avatar_p(cv, 12.6, Z_PL, 1.7, 10)
    ground(cv, -1.0, 33.0, Z_PL, .5)
    hdim(cv, 7.0, 23.67, 2.85, "16.67 SHOP")
    level_tags(cv, -1.15, [(Z_PL, "+3.60"), (Z_ANNEX, "+7.20 ANNEX"), (Z_LROOF, "+8.70")])
    panel_title(cv, -1.0, 1.35, "11", "LIFESTYLE & SOUVENIR · WEST · SIDE TO THE PLAZA", "looking east · portal with red noren on the seating terrace, disc-tile panel")
    return cv


def life_east():
    sx = 20.0
    cv = Cv(sx, -sx, 150 + 4.0 * sx, 860, 0, Z_PL)
    # u = 81.67 - y (left = south)
    cv.rect(-4.0, Z_PL, 34.0, 10.8, "e-sky")
    cv.rect(26.67, Z_PL, 31.17, Z_ANNEX, "e-plaster")
    kawara(cv, 26.67, 31.17, Z_ANNEX, h=.45, glaze="e-kawara-y")
    cv.rect(27.5, Z_PL, 28.7, 5.8, "e-steel")
    cv.rect(30.83, Z_ANNEX + .6, 33.0, 8.4, "e-white")
    cv.rect(30.83, Z_ANNEX + .6, 33.0, 8.4, "e-out")
    life_main_upper(cv, 10.0, 26.67)
    gold_line(cv, 10.0, 26.67, 7.75)
    for (a, b_) in ((10.8, 13.4), (16.6, 19.0), (21.4, 25.8)):
        glazing(cv, a, 5.0, b_, 7.4, 2)
    cv.rect(14.0, Z_PL, 15.2, 5.8, "e-steel")
    hang_sign(cv, 15.9, 6.4, "裏口", side=1)
    cv.rect(5.83, Z_PL, 10.0, Z_BAND, "e-plaster")
    cv.rect(5.83, Z_BAND - .25, 10.0, Z_BAND, "e-dark")
    cv.rect(3.67, Z_PL, 5.33, 5.4, "e-white")
    cv.rect(3.67, Z_PL, 5.33, 5.4, "e-out")
    tent_e(cv, 10.0, 13.83, Z_PL)
    tent_e(cv, 13.3, 16.67, Z_PL)
    shrubs_e(cv, 9.6, 30.8, Z_PL + .6, .75, 76)
    cv.rect(9.5, Z_PL, 30.9, Z_PL + .6, "e-conc")
    parasol_e(cv, -2.9, Z_PL, 1.5, 2.4, "umb-c")
    palm_elev(cv, 20.0, Z_PL, 6.8, 77)
    palm_elev(cv, 2.0, Z_PL, 6.0, 78)
    ground(cv, -4.0, 34.0, Z_PL, .5)
    hdim(cv, 10.0, 26.67, 2.85, "16.67 SHOP")
    hdim(cv, 26.67, 31.17, 2.85, "4.50")
    level_tags(cv, -4.15, [(Z_PL, "+3.60"), (Z_LROOF, "+8.70")])
    panel_title(cv, -4.0, 1.35, "12", "LIFESTYLE & SOUVENIR · EAST · BACK", "looking west · service door, annex; the terrace planter along the curved path in front")
    return cv


def life_north():
    sx = 20.0
    cv = Cv(sx, -sx, 150 + 4.0 * sx, 1145, 0, Z_PL)
    # u = 153.33 - x (left = east), seen from the truck pad and the palm row
    cv.rect(-4.0, Z_PL, 30.0, 10.8, "e-sky")
    life_main_upper(cv, 0, 23.0)
    gold_line(cv, 14.16, 23.0, 7.75)
    glazing(cv, 15.0, 4.9, 18.6, 7.3, 3, inner="e-glow")
    red_panel(cv, 19.2, 6.0, 22.5, 7.4, "おみやげ")
    # annex in front of the main block, roof sign standing behind its eave
    for uu in (7.07, 10.93):
        cv.rect(uu - .06, Z_ANNEX + .2, uu + .06, 8.6, "e-dark")
    rrect(cv, 6.5, 7.55, 11.5, 8.75, .3, "e-white-o")
    stext(cv, 9.0, 7.98, "おみやげ SOUVENIR", .32, fill="var(--f-verm)", weight=800, family="var(--f-body)")
    cv.rect(0, Z_PL, 14.16, Z_ANNEX, "e-plaster")
    kawara(cv, -.6, 14.76, Z_ANNEX, h=.45, glaze="e-kawara-y")
    gold_line(cv, 0, 14.16, 6.55)
    cv.rect(.3, 6.65, 6.0, 7.05, "e-white")
    cv.rect(.3, 6.65, 6.0, 7.05, "e-out")
    stext(cv, 3.15, 6.73, "SOUVENIR & GIFTS", .22, fill="var(--f-dark)", weight=700, family="var(--f-cond)")
    cv.rect(.5, Z_PL, 5.8, 5.6, "e-glow")
    glazing(cv, .5, Z_PL, 5.8, 5.6, 4, inner="e-glass-t")
    stickers(cv, 3.0, Z_PL, 5.8, 5.6, 4, 7)
    cv.rect(.3, 5.62, 6.0, 6.25, "e-yel")
    cv.rect(.3, 5.62, 6.0, 6.25, "e-out")
    cv.rect(.3, 5.4, 6.0, 5.62, "e-shadow")
    portal(cv, 6.4, 9.0, Z_PL, 5.25, 6.2)
    noren(cv, 6.7, 8.7, 5.25, .7, "e-verm", "ring", panels=2)
    for uu in (6.15, 9.25):
        chochin(cv, uu, 5.95, .26, .62)
    disc_panel(cv, 9.6, 4.0, 13.6, 6.2, 5, 2, "e-verm", 3)
    cv.rect(13.7, 4.2, 14.1, 6.3, "e-white")
    vkana(cv, 13.9, 6.2, "雑貨", .3, fill="var(--f-verm)")
    # corner palm planter against the main block
    cv.rect(14.26, Z_PL, 21.83, Z_PL + .6, "e-conc")
    shrubs_e(cv, 14.4, 21.6, Z_PL + .6, .7, 79)
    palm_elev(cv, 18.0, Z_PL + .6, 6.8, 80)
    avatar_p(cv, 10.6, Z_PL, 1.65, 12)
    ground(cv, -4.0, 30.0, Z_PL, .5)
    hdim(cv, 0, 14.16, 2.85, "14.16 ANNEX")
    hdim(cv, 14.16, 23.0, 2.85, "8.84 SHOP")
    level_tags(cv, -4.15, [(Z_PL, "+3.60"), (Z_ANNEX, "+7.20 ANNEX"), (Z_LROOF, "+8.70")])
    panel_title(cv, -4.0, 1.35, "13", "LIFESTYLE & SOUVENIR · NORTH · SIDE TO THE TRUCK PAD",
                "looking south · display windows under an awning, side entrance with noren and lanterns, disc-tile panel · palm row in front not shown")
    return cv


def sheet_a503():
    W, H = 1100, 1235
    root = Cv(1, 1, 0, 0)
    root.add(defs_e("ce"))
    root.add(f'<rect class="sheet-bg" width="{W}" height="{H}"/>')
    title_strip(root, 24, 30, "A-503", "LIFESTYLE & SOUVENIR · ELEVATIONS",
                "Japanese shopping-street front after the shop reference · footprint, canopy band, awning and sign as traced on L-101 · 20 px = 1 m")
    parts = [life_south(), life_west(), life_east(), life_north()]
    key = colour_key(root, 862, 455, [("e-plaster", "White plaster"), ("e-kawara-y", "Blue-glazed kawara eave"),
                                      ("e-verm", "Vermilion: noren, lanterns, disc panel"), ("e-red", "Red おみやげ panel"),
                                      ("e-pink-o", "Pink shop sign"), ("e-gold", "Gold line"), ("e-glass", "Clear glazing")])
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


# ================================================================ A-505 MAIN STAIR, ESCALATORS, GATE
ESC_X = [(88.75, 90.45, "UP"), (90.75, 92.45, "DN")]        # plan X (m) of each escalator in the stair's middle lane
ESC_Y0, ESC_PLATE, ESC_RUN = 18.5, 2.6, 4.8 / math.tan(math.radians(30))   # top edge, landing plates, incline run (m)
GATE_X, GATE_Y = (83.58, 97.58), 17.75                      # gate post centres and line on the forecourt (m)
Z_ST = 8.40


def mural(cv, u0, z0, u1, z1, seed=0):
    """Wall mural after the shop reference: a winged TV-head mascot, a sleeping cat, confetti."""
    rnd = random.Random(seed)
    W, H = u1 - u0, z1 - z0
    cv.rect(u0, z0, u1, z1, "e-plaster")
    for i in range(14):
        cls = ("e-pink", "e-yel3", "chalk-c", "e-lilac", "e-mint")[i % 5]
        cv.circle(u0 + rnd.uniform(.05, .95) * W, z0 + rnd.uniform(.1, .9) * H, rnd.uniform(.08, .22) * H, cls,
                  ' style="opacity:.55"')
    # TV-head mascot with wings
    tu, tz, s = u0 + W * (.3 if seed % 2 == 0 else .68), z0 + H * .55, H * .32
    for k in (-1, 1):
        cv.ellipse(tu + k * s * 1.35, tz + s * .2, s * .75, s * .4, "e-white-o")
        for j in range(3):
            cv.line(tu + k * s * (1.0 + j * .25), tz + s * .1, tu + k * s * (1.25 + j * .25), tz + s * .45, "e-joint")
    rrect(cv, tu - s, tz - s * .8, tu + s, tz + s * .8, s * .25, "e-mint")
    rrect(cv, tu - s * .72, tz - s * .52, tu + s * .72, tz + s * .55, s * .15, "e-dark")
    for k in (-1, 1):
        cv.rect(tu + k * s * .32 - s * .08, tz + s * .05, tu + k * s * .32 + s * .08, tz + s * .28, "", ' style="fill:var(--f-glass)"')
    cv.path([("M", tu - s * .25, tz - s * .22), ("Q", tu, tz - s * .42, tu + s * .25, tz - s * .22)], "",
            ' style="fill:none;stroke:var(--f-glass);stroke-width:2"')
    cv.line(tu - s * .3, tz + s * .8, tu - s * .55, tz + s * 1.15, "e-mull")
    cv.line(tu + s * .3, tz + s * .8, tu + s * .55, tz + s * 1.15, "e-mull")
    # sleeping cat
    cu, cz = u0 + W * (.7 if seed % 2 == 0 else .25), z0 + H * .25
    cv.ellipse(cu, cz, H * .34, H * .14, "", ' style="fill:var(--f-orange);stroke:var(--ink);stroke-width:1"')
    for k in range(4):
        cv.line(cu - H * .2 + k * H * .12, cz - H * .1, cu - H * .16 + k * H * .12, cz + H * .1, "", )
        cv.add(f'<line x1="{n(cv.X(cu - H * .2 + k * H * .12))}" y1="{n(cv.Y(cz + H * .11))}" '
               f'x2="{n(cv.X(cu - H * .17 + k * H * .12))}" y2="{n(cv.Y(cz - H * .06))}" style="stroke:var(--f-white);stroke-width:2.5"/>')
    hu = cu + H * .3
    cv.circle(hu, cz + H * .08, H * .12, "", ' style="fill:var(--f-orange);stroke:var(--ink);stroke-width:1"')
    for k in (-1, 1):
        cv.poly([(hu + k * H * .1, cz + H * .14), (hu + k * H * .08, cz + H * .26), (hu + k * H * .02, cz + H * .18)],
                "", ' style="fill:var(--f-orange);stroke:var(--ink);stroke-width:.8"')
    cv.path([("M", hu - H * .06, cz + H * .08), ("Q", hu - H * .035, cz + H * .06, hu - H * .01, cz + H * .08)], "e-mull")
    cv.path([("M", hu + H * .01, cz + H * .08), ("Q", hu + H * .035, cz + H * .06, hu + H * .06, cz + H * .08)], "e-mull")
    stext(cv, cu - H * .1, cz + H * .2, "zzz", H * .08, fill="var(--f-dark)", weight=700, family="var(--f-cond)")
    bubble(cv, tu + s * 1.0, tz + s * .95, H * .32, H * .15)


def gate_elev(cv, x0, x1, z, view="front"):
    """Shotengai gate: vermilion posts, nuki tie, plaque, shimaki and an upturned black kasagi, kumiko lattice, lanterns."""
    for x in (x0, x1):
        cv.rect(x - .45, z, x + .45, z + .5, "e-conc")
        cv.rect(x - .33, z + .5, x + .33, z + 7.25, "e-verm")
    cv.rect(x0 - .9, z + 5.55, x1 + .9, z + 6.05, "e-verm")
    for x, k in ((x0, 1), (x1, -1)):
        a, b = sorted((x + k * .33, x + k * 1.6))
        cv.rect(a, z + 6.05, b, z + 7.0, "", ' style="fill:var(--f-cream-2);stroke:var(--ink);stroke-width:.7"')
        for u in frange(a + .21, b, .21):
            cv.line(u, z + 6.05, u, z + 7.0, "e-mull")
        for zz in frange(z + 6.24, z + 7.0, .19):
            cv.line(a, zz, b, zz, "e-mull")
    xm = (x0 + x1) / 2
    cv.rect(xm - 1.9, z + 6.1, xm + 1.9, z + 7.0, "e-dark")
    cv.rect(xm - 1.8, z + 6.18, xm + 1.8, z + 6.92, "", ' style="fill:none;stroke:var(--f-gold);stroke-width:1"')
    stext(cv, xm, z + 6.47, "うみ シーサイドパーク", .26, fill="var(--f-gold)", weight=800, family="var(--f-body)")
    stext(cv, xm, z + 6.22, "UMI SEASIDE PARK", .13, fill="var(--f-gold)", weight=700, family="var(--f-cond)", ls=.05)
    cv.rect(x0 - 1.4, z + 7.0, x1 + 1.4, z + 7.25, "e-verm")
    cv.poly([(x0 - 2.0, z + 7.65), (x0 - 1.5, z + 7.25), (x1 + 1.5, z + 7.25), (x1 + 2.0, z + 7.65), (x1 + 2.05, z + 7.95),
             (x1 + .5, z + 7.85), (x0 - .5, z + 7.85), (x0 - 2.05, z + 7.95)], "e-dark")
    for i in range(5):
        chochin(cv, x0 + 1.6 + i * (x1 - x0 - 3.2) / 4, z + 4.92, .3, .72)
    hang_sign(cv, x0, z + 4.6, "ようこそ", w=.55, side=1)
    hang_sign(cv, x1, z + 4.6, "うみ", w=.55, side=-1)


def escalator_front(cv, e0, e1, z0, z1, d):
    cv.rect(e0 + .12, z0, e1 - .12, z1, "e-steel")
    for zz in frange(z0 + .2, z1, .2):
        cv.line(e0 + .12, zz, e1 - .12, zz, "e-joint")
    for u in (e0, e1 - .12):
        cv.rect(u, z0, u + .12, z1 + 1.0, "e-glass")
    cv.line(e0, z1 + 1.0, e1, z1 + 1.0, "e-mull-t")
    rrect(cv, e0 + .3, z0 + .25, e1 - .3, z0 + .75, .08, "e-green" if d == "UP" else "e-red")
    stext(cv, (e0 + e1) / 2, z0 + .38, d, .2, weight=800, family="var(--f-cond)")


def stair_front(cv, a, b, z0, z1, risers=32):
    cv.rect(a, z0, b, z1, "e-conc")
    r = (z1 - z0) / risers
    for k in range(1, risers):
        cv.line(a + .3, z0 + k * r, b - .3, z0 + k * r, "e-joint" if k != risers // 2 else "e-mull")
    for u in (a, b - .3):
        cv.rect(u, z0, u + .3, z1 + .45, "e-conc")


def stair_south():
    sx = 20.0
    cv = Cv(sx, -sx, 140 - 67.0 * sx, 470, 0, Z_PL)
    X = lambda px: (px - 60) / 6  # noqa: E731
    cv.rect(67.0, Z_PL, 114.2, 18.6, "e-sky")
    for (x, r) in ((517, 28), (683, 28), (455, 18)):
        tree_elev(cv, X(x), Z_ST, 6.5, r / 6 * 1.4, 90 + x)
    gate_elev(cv, GATE_X[0], GATE_X[1], Z_ST)
    # retaining walls with murals and the LED ticker, railing on top
    for (a, b, sd) in ((X(470), X(565), 0), (X(642), X(727), 1)):
        cv.rect(a, Z_PL, b, Z_ST, "e-plaster")
        if b - a > 4:
            mural(cv, a + .3, 4.25, b - .3, 7.55, sd)
        led_band(cv, a, b, 7.65, 8.3, "ようこそ うみ シーサイドパークへ · WELCOME TO UMI SEASIDE PARK · ゲーム · カフェ · ショップ · おみやげ"[: int((b - a) * 4.2)])
        cv.line(a, Z_ST + 1.1, b, Z_ST + 1.1, "e-out")
        for u in frange(a + .2, b, 2.0):
            cv.line(u, Z_ST, u, Z_ST + 1.1, "e-mull")
    # main stair: outer flights and the two escalators
    stair_front(cv, X(565), X(591), Z_PL, Z_ST)
    stair_front(cv, X(616), X(642), Z_PL, Z_ST)
    for (e0, e1, d) in ESC_X:
        escalator_front(cv, e0, e1, Z_PL, Z_ST, d)
    # planters in front, palms and the sakura
    for (a, b) in ((X(478), X(565)), (X(642), X(727))):
        shrubs_e(cv, a + .1, b - .3, Z_PL + .6, .7, int(a))
        cv.rect(a, Z_PL, b, Z_PL + .6, "e-conc")
    for (x, h) in ((548, 6.5), (658, 6.8), (715, 6.6)):
        palm_elev(cv, X(x), Z_PL + .6, h, x)
    tree_elev(cv, X(538), Z_PL + .6, 6.0, 7.5, 95, "sak")
    for (u, h) in ((89.6, 1.7), (91.6, 1.65), (86.3, 1.68)):
        avatar_p(cv, u, Z_PL if u > 88 else 5.2, h, int(u))
    ground(cv, 67.0, 114.2, Z_PL, .5)
    hdim(cv, X(565), X(642), 2.65, "12.83 MAIN STAIR")
    hdim(cv, 88.5, 92.67, 1.95, "4.17 ESCALATORS")
    hdim(cv, GATE_X[0], GATE_X[1], 17.9, "14.00 GATE", ext=Z_ST + 7.3)
    vdim(cv, 113.4, Z_PL, Z_ST, "4.80", side=1)
    vdim(cv, 113.4, Z_ST, Z_ST + 7.95, "7.95", side=1)
    level_tags(cv, 66.8, [(Z_PL, "+3.60 PLAZA"), (Z_ST, "+8.40 FORECOURT"), (Z_ST + 7.95, "+16.35 GATE")])
    note(cv, 68.0, 17.0, X(500), 6.8, "Mural: winged TV-head mascot and a sleeping cat", "start")
    note(cv, 100.0, 17.0, 101.0, 8.0, "LED ticker on the wall top, railing above", "start")
    panel_title(cv, 67.0, .95, "1", "MAIN STAIR · SOUTH ELEVATION FROM THE PLAZA",
                "looking north · stairs either side, escalators in the middle, shotengai gate at the top")
    return cv


def escalator_section():
    sx = 18.0
    cv = Cv(sx, -sx, 140 - 11.0 * sx, 860, 0, Z_PL)
    y0, y1 = ESC_Y0, ESC_Y0 + ESC_PLATE
    y2, y3 = y1 + ESC_RUN, y1 + ESC_RUN + ESC_PLATE
    cv.rect(11.0, 2.0, 41.0, 18.2, "e-sky")
    # stairs beyond (dashed), gate beyond with kasagi, nuki and plaque cut
    pts, yy, zz = [(y0, Z_ST)], y0, Z_ST
    for f in range(2):
        for k in range(16):
            zz -= .15
            pts += [(yy, zz)]
            if k < 15:
                yy += .45
                pts += [(yy, zz)]
        if f == 0:
            yy += 3.1
            pts += [(yy, zz)]
    cv.pline(pts, "e-ghost")
    cv.rect(GATE_Y - .33, Z_ST + .5, GATE_Y + .33, Z_ST + 7.25, "", ' style="fill:var(--f-verm);opacity:.45"')
    cv.rect(GATE_Y - .5, Z_ST + 7.25, GATE_Y + .5, Z_ST + 7.85, "solid")
    cv.rect(GATE_Y - .25, Z_ST + 5.55, GATE_Y + .25, Z_ST + 6.05, "e-verm")
    cv.rect(GATE_Y - .06, Z_ST + 6.1, GATE_Y + .06, Z_ST + 7.0, "solid")
    chochin(cv, GATE_Y, Z_ST + 4.92, .3, .72)
    # forecourt slab and retaining wall, escalator truss, pit, plaza
    earth = [(11.0, Z_ST), (y0 - .3, Z_ST), (y0 - .3, Z_PL - 1.6), (y3 + 1.2, Z_PL - 1.6), (y3 + 1.2, Z_PL), (41.0, Z_PL),
             (41.0, 1.0), (11.0, 1.0)]
    cv.poly(earth, "poche")
    cv.poly(earth, "", ' fill="url(#ce-earth)"')
    truss = [(y0 - .3, Z_ST), (y1, Z_ST), (y2, Z_PL), (y3 + 1.2, Z_PL), (y3 + 1.2, Z_PL - 1.2), (y2 - .4, Z_PL - 1.2),
             (y1 - .4, Z_ST - 1.2), (y0 - .3, Z_ST - 1.2)]
    void = [(y0 - .3, Z_ST - 1.2), (y1 - .4, Z_ST - 1.2), (y2 - .4, Z_PL - 1.2), (y3 + 1.2, Z_PL - 1.2), (y3 + 1.2, Z_PL - 1.6),
            (y0 - .3, Z_PL - 1.6)]
    cv.poly(void, "sheet-f")
    cv.poly(void, "e-ghost")
    cv.text((y0 + y2) / 2 - 1.5, Z_PL - .4, "SERVICE VOID", "t-sm")
    cv.poly(truss, "e-steel")
    for k in range(int(ESC_RUN / .4)):
        a = y1 + k * .4
        b = Z_ST - k * .4 * math.tan(math.radians(30))
        cv.line(a, b, a + .4, b, "e-mull")
        cv.line(a + .4, b, a + .4, b - .231, "e-mull")
    cv.pline([(y0 + .5, Z_ST + .9), (y1, Z_ST + 1.0), (y2, Z_PL + 1.0), (y3 - .5, Z_PL + .9)], "e-mull-t")
    cv.poly([(y0 + .5, Z_ST + .1), (y1, Z_ST + .1), (y2, Z_PL + .1), (y3 - .5, Z_PL + .1), (y3 - .5, Z_PL + .9), (y2, Z_PL + 1.0),
             (y1, Z_ST + 1.0), (y0 + .5, Z_ST + .9)], "e-glass-t")
    cv.pline([(11.0, Z_ST), (y0 - .3, Z_ST)], "e-ground")
    cv.pline([(y3 + 1.2, Z_PL), (41.0, Z_PL)], "e-ground")
    cv.line(y0 - .3, Z_ST, y0 - .3, Z_ST + 1.1, "e-out")
    for (yy, zz) in ((y1 + 2.0, Z_ST - 2.0 * math.tan(math.radians(30))), (y1 + 5.5, Z_ST - 5.5 * math.tan(math.radians(30)))):
        avatar_p(cv, yy, zz, 1.7, int(yy))
    avatar_p(cv, 14.0, Z_ST, 1.7, 3)
    avatar_p(cv, 36.0, Z_PL, 1.65, 4)
    hdim(cv, y0, y1, Z_PL - 2.2, "2.60")
    hdim(cv, y1, y2, Z_PL - 2.2, f"{ESC_RUN:.2f} AT 30°")
    hdim(cv, y2, y3, Z_PL - 2.2, "2.60")
    vdim(cv, y3 + 2.0, Z_PL, Z_ST, "4.80", side=1)
    level_tags(cv, 10.8, [(Z_PL, "+3.60"), (Z_ST, "+8.40"), (Z_ST + 7.85, "+16.25")])
    note(cv, 24.0, 15.6, GATE_Y, Z_ST + 7.6, "Kasagi and plaque cut; posts beyond", "start")
    note(cv, 26.0, 11.8, y1 + 3.0, Z_ST - 1.4, "Escalator truss in a 1.6 m pit at the foot", "start")
    panel_title(cv, 11.0, -.15, "2", "SECTION THROUGH THE UP ESCALATOR", "looking east · stairs beyond dashed · gate kasagi cut")
    return cv


def sheet_a505():
    W, H = 1100, 960
    root = Cv(1, 1, 0, 0)
    root.add(defs_e("ce"))
    root.add(f'<rect class="sheet-bg" width="{W}" height="{H}"/>')
    title_strip(root, 24, 30, "A-505", "MAIN STAIR · ESCALATORS, GATE AND MURAL WALLS",
                "After the shop references: stairs and escalators side by side, a gate at the top, mural walls with an LED ticker · 20 and 18 px = 1 m")
    parts = [stair_south(), escalator_section()]
    key = colour_key(root, 720, 650, [("e-verm", "Vermilion gate posts and ties"), ("e-dark", "Black kasagi, plaque, LED ticker"),
                                      ("e-gold", "Gold plaque lettering"), ("e-glass", "Glass balustrades"),
                                      ("e-steel", "Escalator truss and steps"), ("e-plaster", "Mural walls on white plaster"),
                                      ("e-conc", "Stairs, planters")])
    root.add(f'<rect class="frame" x="12" y="50" width="{W - 24}" height="{H - 62}"/>')
    return "\n".join([root.svg()] + [p.svg() for p in parts] + [key]), W, H


# ================================================================ arcade interior (shared by L-101, A-506 and P-601)
# Game hall in the facade's red, yellow and white, after the interior references: neon floor tiles, a block-puzzle LED wall, a tower of
# stacked CRT monitors with a robot face, two tiers of round drum machines, a row of cabinets, egg chairs,
# sphere TV pods and server stacks with green code screens. Metres: x east, z south, floor +4.05, ceiling +9.30.
ARC_IN = {
    "box": (14.05, 38.22, 47.62, 64.70),
    "door": (49.17, 54.17),
    "led": (24.0, 38.0, 4.65, 8.45),                  # x range on the north wall, y range
    "stacks": [(14.05, 38.22, 21.6, 40.1, 8.7), (39.6, 38.22, 47.62, 39.8, 7.9)],
    "drums": (14.05, 15.05, 42.0, 61.8, 1.8),          # x front band, z range, pitch (two tiers)
    "cabinets": [(18.2, 6), (27.2, 6), (36.2, 6)],     # first x and count per group, south wall, facing north
    "tower": (27.6, 48.67, 33.6, 54.67, 8.9),
    "eggs": [(38.0, 45.6), (38.0, 57.8), (23.4, 45.6), (23.4, 58.2)],
    "pods": [(42.2, 44.6), (42.2, 58.8)],
    "tvs": [(17.0, 48.9), (17.0, 54.4)],
    "stools": [(19.0 + i * 1.15, 61.3) for i in range(0, 24, 3)],
}
TILE_SHAPES = {"L": [(0, 0), (0, 1), (0, 2), (1, 2)], "T": [(0, 0), (1, 0), (2, 0), (1, 1)], "S": [(1, 0), (2, 0), (0, 1), (1, 1)],
               "I": [(0, 0), (1, 0), (2, 0), (3, 0)], "O": [(0, 0), (1, 0), (0, 1), (1, 1)], "J": [(1, 0), (1, 1), (1, 2), (0, 2)]}
NEON_TILES = [(43.0, 47.0, "L", "pink"), (39.5, 50.5, "I", "green"), (35.0, 47.4, "S", "cyan"), (35.5, 55.5, "T", "yellow"),
              (25.0, 55.6, "O", "pink"), (20.2, 44.6, "J", "cyan"), (29.0, 44.4, "I", "yellow"), (43.6, 55.4, "S", "green"),
              (21.0, 51.0, "T", "green"), (31.0, 58.0, "L", "cyan")]
NEON = {"pink": "#FF5FC8", "green": "#9BFF5A", "cyan": "#3FE6F0", "yellow": "#FFE45A", "purple": "#9B6BFF"}


def neon_tile_cells():
    out = []
    for (x0, z0, sh, col) in NEON_TILES:
        for (i, j) in TILE_SHAPES[sh]:
            out.append((x0 + i * 1.02, z0 + j * 1.02, col))
    return out
