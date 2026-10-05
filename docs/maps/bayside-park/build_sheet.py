#!/usr/bin/env python3
"""Build the Bayside Park level-design sheet.

Outputs, next to this script:
  index.html        the full sheet (title block, drawings, schedules)
  site-plan.svg     LD-01 site plan
  section-aa.svg    LD-02 section A-A'
  elevation-e1.svg  LD-03 shop row elevation
  interiors.svg     LD-04 arcade + cafe ground floors

Plan coordinates are metres: origin at the NW site corner, +x east, +y south.
Levels are metres relative to the Central Plaza datum (+-0.00).
Run:  python3 build_sheet.py
"""
from __future__ import annotations

import html
import math
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------- tokens ---
LIGHT = {
    "paper": "#e9edec", "sheet": "#fbfcfb", "ink": "#1c2930", "ink2": "#4e5c65", "ink3": "#9aa6ad",
    "rule": "#d0d8db", "accent": "#d63a73", "onaccent": "#ffffff", "spawn": "#17865a",
    "bound": "#cf3d28", "route": "#2a66cc", "sight": "#c08400", "skate": "#8a3ccf", "cut": "#3a4751",
    "mark": "#ffffff", "sand": "#f1e2bc", "grass": "#d3e6b9", "grass2": "#b9d69b", "tree": "#94c47d",
    "treeline": "#5a8a49", "pine": "#5e9858", "blossom": "#f3bfd0", "water": "#c4e1ed",
    "deep": "#a6cde1", "pond": "#b2d9e6", "foam": "#ffffff", "brick": "#ecd7c8", "pave": "#e2e6e8",
    "wood": "#e2c8a4", "conc": "#d5dade", "bldg": "#c3ccd4", "bldg2": "#dce2e7", "road": "#b9bfc4",
    "rock": "#cec7bb", "rockline": "#9d9487", "oob": "#e0e4e3", "umbrella": "#f3c43c",
    "chalk1": "#ff69a7", "chalk2": "#ffd343", "chalk3": "#43c4ee", "chalk4": "#78d987",
    "fire": "#ff7a2c", "led": "#3a49d6", "zchill": "#22a094", "zsocial": "#e8a900",
    "zactive": "#de3f78", "zleisure": "#2a82d4",
}
DARK = {
    "paper": "#0f1417", "sheet": "#161d22", "ink": "#e2e8eb", "ink2": "#a5b2b9", "ink3": "#5f6d75",
    "rule": "#2a353c", "accent": "#ff6b9e", "onaccent": "#1a0b11", "spawn": "#45c387",
    "bound": "#ff6b55", "route": "#6ea6ff", "sight": "#f1b52c", "skate": "#b47cf0", "cut": "#9ba9b2",
    "mark": "#c9d2d6", "sand": "#4a4231", "grass": "#2b4230", "grass2": "#36552f", "tree": "#3f6c3b",
    "treeline": "#86bb72", "pine": "#4f8a49", "blossom": "#7d4659", "water": "#1c3948",
    "deep": "#142d3a", "pond": "#22475a", "foam": "#8fb7c9", "brick": "#4b3a32", "pave": "#2b3338",
    "wood": "#4f3e2d", "conc": "#30383e", "bldg": "#4c5a64", "bldg2": "#3a464e", "road": "#23292d",
    "rock": "#3d3933", "rockline": "#756d61", "oob": "#1e2427", "umbrella": "#d8a92b",
    "chalk1": "#e2568f", "chalk2": "#e2b83a", "chalk3": "#36acd2", "chalk4": "#5fbf70",
    "fire": "#ff8a3d", "led": "#5e6cf0", "zchill": "#3cc4b6", "zsocial": "#f2be2e",
    "zactive": "#ff6b9e", "zleisure": "#5aa6f0",
}
FONTS = {
    "f-draw": '"Barlow Condensed", "Arial Narrow", "Roboto Condensed", sans-serif',
    "f-body": '"IBM Plex Sans", "Segoe UI", system-ui, sans-serif',
    "f-mono": '"IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace',
}


def svg_class_css() -> str:
    rules = []
    for k in LIGHT:
        rules.append(f".f-{k}{{fill:var(--{k})}}")
        rules.append(f".s-{k}{{stroke:var(--{k})}}")
    rules += [
        ".nf{fill:none}",
        ".t-draw{font-family:var(--f-draw)}",
        ".t-mono{font-family:var(--f-mono)}",
        ".halo{paint-order:stroke fill;stroke:var(--sheet);stroke-linejoin:round}",
    ]
    return "\n".join(rules)


def literal(css: str, tokens: dict) -> str:
    def sub(m):
        k = m.group(1)
        return tokens.get(k) or FONTS.get(k) or m.group(0)
    return re.sub(r"var\(--([a-z0-9-]+)\)", sub, css)


# ------------------------------------------------------------- svg helpers ---
def fmt(v) -> str:
    if isinstance(v, bool):
        return str(v).lower()
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        r = round(v, 3)
        return str(int(r)) if r == int(r) else f"{r:g}"
    return str(v)


def _a(**kw) -> str:
    parts = []
    for k, v in kw.items():
        if v is None or v == "":
            continue
        name = "class" if k == "cls" else k.replace("_", "-")
        parts.append(f'{name}="{fmt(v)}"')
    return (" " + " ".join(parts)) if parts else ""


def R(x, y, w, h, cls="", **kw):
    return f"<rect{_a(x=x, y=y, width=w, height=h, cls=cls, **kw)}/>"


def C(cx, cy, r, cls="", **kw):
    return f"<circle{_a(cx=cx, cy=cy, r=r, cls=cls, **kw)}/>"


def E(cx, cy, rx, ry, cls="", **kw):
    return f"<ellipse{_a(cx=cx, cy=cy, rx=rx, ry=ry, cls=cls, **kw)}/>"


def L(x1, y1, x2, y2, cls="", **kw):
    return f"<line{_a(x1=x1, y1=y1, x2=x2, y2=y2, cls=cls, **kw)}/>"


def P(d, cls="", **kw):
    return f"<path{_a(d=d, cls=cls, **kw)}/>"


def PG(pts, cls="", closed=True, **kw):
    tag = "polygon" if closed else "polyline"
    pts_s = " ".join(f"{fmt(float(x))},{fmt(float(y))}" for x, y in pts)
    return f"<{tag}{_a(points=pts_s, cls=cls, **kw)}/>"


def T(x, y, s, size, cls="f-ink t-draw", anchor="middle", weight=None, halo=None, rot=None,
      ls=None, base=None, **kw):
    c = cls + (" halo" if halo else "")
    tr = f"rotate({fmt(float(rot))} {fmt(float(x))} {fmt(float(y))})" if rot else None
    return (f"<text{_a(x=x, y=y, cls=c, font_size=size, text_anchor=anchor, font_weight=weight, letter_spacing=ls, stroke_width=halo, dominant_baseline=base, transform=tr, **kw)}>"
            f"{html.escape(s)}</text>")


def G(items, **kw):
    return f"<g{_a(**kw)}>" + "".join(items) + "</g>"


def svg_wrap(parts, viewbox, label, inline, cls="", el_id=None, px_per_unit=4.0):
    vb = [float(v) for v in viewbox.split()]
    if inline:
        return (f'<svg{_a(id=el_id, cls=cls, viewBox=viewbox, role="img", aria_label=label)} '
                f'preserveAspectRatio="xMidYMid meet">' + "".join(parts) + "</svg>")
    style = literal(svg_class_css(), LIGHT) + "\n[hidden]{display:none}"
    w, h = vb[2] * px_per_unit, vb[3] * px_per_unit
    return (f'<svg xmlns="http://www.w3.org/2000/svg"{_a(viewBox=viewbox, width=round(w), height=round(h), role="img", aria_label=label)}>'
            f"<style>{style}</style>"
            + R(vb[0], vb[1], vb[2], vb[3], fill=LIGHT["sheet"])
            + "".join(parts) + "</svg>")


def bubble(x, y, n, r=2.2, size=2.3):
    return C(x, y, r, "f-accent") + T(x, y + 0.08, str(n), size, "f-onaccent t-draw", weight=700, base="central")


def tree(x, y, r, W, cls="f-tree"):
    return C(x, y, r, f"{cls} s-treeline", stroke_width=W["t"], fill_opacity=0.92) + C(x, y, 0.35, "f-treeline")


def treads(x0, x1, y0, y1, step=0.6, sw=0.08):
    out, y = [], y0 + step
    while y < y1 - 1e-6:
        out.append(L(x0, y, x1, y, "s-ink3", stroke_width=sw))
        y += step
    return out


def polyline_len(pts):
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


# ------------------------------------------------------------ site geometry ---
SITE_W, SITE_D = 240, 260
HILL_PATH = ("M60,38 C48,38 44,46 50,52 C56,58 52,68 44,74 C36,80 26,84 30,94 "
             "C34,104 52,100 62,106 C70,111 76,108 84,110")
SAND = ("M10,164 L236,164 L234,186 L229,206 C214,211 200,206 184,209 S146,207 124,211 "
        "S82,206 60,210 S26,207 16,203 L12,182 Z")
FOAM = ("M229,207.6 C214,212.6 200,207.6 184,210.6 S146,208.6 124,212.6 S82,207.6 60,211.6 "
        "S26,208.6 16,204.6")
ROCK_W = [(0, 28), (10, 28), (11.5, 52), (9, 80), (11.5, 108), (9, 136), (12, 160), (14, 182),
          (17, 201), (28, 214), (36, 232), (30, 248), (20, 260), (0, 260)]
BREAK_E = [(240, 148), (238, 148), (236, 162), (233, 180), (230, 204), (225, 226), (221, 246),
           (224, 260), (240, 260)]
LOOP = [(66, 79), (228, 79), (227, 126), (227, 157), (18, 157), (30, 148), (62, 124), (74, 100),
        (74, 86), (66, 79)]
SKATE_LINE = [(184, 92), (200, 108), (227, 126), (227, 160.5), (16, 160.5)]
CONTOURS = [
    ("M10,48 C24,52 38,49 56,50", "+5", 47.2),
    ("M10,56 C24,60 40,56 56,57", "+4", 55.2),
    ("M10,64 C24,68 40,63 56,65", "+3", 63.2),
    ("M10,72 C24,77 42,72 56,73", "+2", 71.2),
    ("M10,81 C26,87 46,83 64,85", "+1", 80.2),
]
SHOPS = [  # key, x, y, w, h, fill, name, sub, callout
    ("cafe", 64, 48, 32, 18, "f-wood", "CAFÉ", "roof terrace +6.00", 4),
    ("photo", 96, 48, 12, 16, "f-bldg", "PHOTO", "+4.50", 5),
    ("mart", 132, 48, 16, 16, "f-bldg", "24 MART", "+4.50", 6),
    ("arcade", 148, 48, 40, 24, "f-bldg", "ARCADE", "2F · roof +11.50", 7),
    ("skate", 188, 48, 16, 16, "f-bldg", "SKATE SHOP", "+4.50", 8),
]
BUBBLES = {
    1: (131.6, 33.5), 2: (99, 44), 3: (120, 55.2), 4: (67.6, 51.6), 5: (99.4, 51.6),
    6: (135.4, 51.6), 7: (151.4, 51.6), 8: (191.4, 51.6), 9: (212, 55.2), 10: (226, 55.4),
    11: (190, 79.2), 12: (110.8, 94.8), 13: (155, 91.2), 14: (120, 128), 15: (94, 91.2),
    16: (92.5, 129), 17: (40.5, 35.5), 18: (40, 71.2), 19: (60, 55.2), 20: (60, 131.5),
    21: (33, 112), 22: (182, 93.2), 23: (196.6, 108), 24: (235.2, 105.2), 25: (196, 136),
    26: (227, 121.6), 27: (152, 146), 28: (40, 157.4), 29: (65.5, 154.4), 30: (64, 177),
    31: (44, 172), 32: (120, 181), 33: (172, 167.4), 34: (219, 171.5), 35: (126.2, 200),
    36: (104, 225), 37: (200, 190), 38: (204, 243), 39: (40, 228), 40: (5, 130), 41: (235.6, 190),
    42: (60, 22),
}
UMBRELLAS_BEACH = [(98, 174), (108, 179), (132, 176), (143, 181), (100, 188), (110, 193),
                   (130, 190), (141, 195)]


def site_plan(p="p"):
    W = dict(h=0.14, t=0.22, m=0.36, k=0.6)
    lay = {k: [] for k in ("base", "zones", "circ", "sight", "grid", "system", "labels")}
    b, lab, grid, sysl = lay["base"], lay["labels"], lay["grid"], lay["system"]

    defs = (
        "<defs>"
        f'<pattern id="{p}-hatch" width="2" height="2" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        f'<line x1="0" y1="0" x2="0" y2="2" class="s-ink3" stroke-width="0.16"/></pattern>'
        f'<pattern id="{p}-rock" width="3" height="3" patternUnits="userSpaceOnUse" patternTransform="rotate(-35)">'
        f'<line x1="0" y1="0" x2="0" y2="3" class="s-rockline" stroke-width="0.22"/>'
        f'<line x1="1.5" y1="0.6" x2="1.5" y2="1.8" class="s-rockline" stroke-width="0.22"/></pattern>'
        f'<pattern id="{p}-tetra" width="3.2" height="3.2" patternUnits="userSpaceOnUse">'
        f'<path d="M1.6 0.5 L2.7 2.6 L0.5 2.6 Z" class="nf s-rockline" stroke-width="0.18"/></pattern>'
        f'<pattern id="{p}-plankv" width="1.2" height="4" patternUnits="userSpaceOnUse">'
        f'<line x1="0" y1="0" x2="0" y2="4" class="s-ink3" stroke-width="0.07"/></pattern>'
        f'<pattern id="{p}-plankh" width="4" height="1.2" patternUnits="userSpaceOnUse">'
        f'<line x1="0" y1="0" x2="4" y2="0" class="s-ink3" stroke-width="0.07"/></pattern>'
        f'<pattern id="{p}-brick" width="2.4" height="1.2" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        f'<path d="M0 0H2.4M0 0V0.6M1.2 0.6V1.2M0 0.6H2.4" class="nf s-ink3" stroke-width="0.05"/></pattern>'
        f'<clipPath id="{p}-emote"><circle cx="120" cy="104" r="13"/></clipPath>'
        f'<marker id="{p}-arr" viewBox="0 0 6 6" refX="5" refY="3" markerWidth="4" markerHeight="4" orient="auto-start-reverse">'
        f'<path d="M0 0 L6 3 L0 6 Z" class="f-ink"/></marker>'
        "</defs>"
    )
    hatch = f"url(#{p}-hatch)"

    # sea, sand, promenade
    b.append(R(0, 190, SITE_W, 70, "f-water"))
    b.append(R(0, 232, SITE_W, 28, "f-deep"))
    b.append(P(SAND, "f-sand"))
    b.append(P(FOAM, "nf s-foam", stroke_width=0.45, stroke_dasharray="2.4 1.6"))
    # backdrop town + coastal road (north, out of bounds)
    b.append(R(0, 0, SITE_W, 16, "f-oob"))
    b.append(R(0, 0, SITE_W, 16, fill=hatch))
    for x0, w, h in [(3, 20, 12), (26, 14, 10), (43, 22, 13), (68, 16, 9), (88, 24, 12), (115, 18, 11),
                     (136, 22, 13), (161, 15, 10), (179, 24, 12), (206, 14, 11), (223, 15, 12)]:
        b.append(R(x0, 15 - h, w, h, "f-bldg2 s-ink3", stroke_width=W["h"]))
    b.append(R(0, 16, SITE_W, 12, "f-road"))
    b.append(L(0, 22, SITE_W, 22, "s-mark", stroke_width=0.3, stroke_dasharray="3 3"))
    for cx, cy in [(34, 18.2), (98, 23.4), (150, 18.2), (207, 23.4)]:
        b.append(R(cx, cy, 4.6, 2.0, "f-bldg s-ink", stroke_width=W["h"], rx=0.5))
    # park ground
    b.append(R(10, 28, 74, 122, "f-grass"))
    # paved tiers
    b.append(R(60, 28, 178, 20, "f-pave"))
    b.append(R(56, 48, 8, 24, "f-pave"))
    b.append(R(64, 48, 174, 36, "f-pave"))
    # central plaza (brick)
    b.append(R(84, 84, 88, 58, "f-brick"))
    b.append(R(84, 84, 88, 58, fill=f"url(#{p}-brick)"))
    # sunset steps
    b.append(R(84, 142, 88, 8, "f-conc"))
    for yy in (142, 144, 146, 148):
        b.append(L(84, yy, 172, yy, "s-ink", stroke_width=W["t"]))
    for ax, aw in ((94, 4), (116, 8), (142, 4)):
        b.append(R(ax, 142, aw, 8, "f-pave s-ink", stroke_width=W["h"]))
        b += [L(ax, 142 + i * 8 / 12, ax + aw, 142 + i * 8 / 12, "s-ink3", stroke_width=0.08) for i in range(1, 12)]
    # east deck
    b.append(R(172, 84, 66, 66, "f-conc"))
    # promenade + pier
    b.append(R(10, 150, 226, 14, "f-wood"))
    b.append(R(10, 150, 226, 14, fill=f"url(#{p}-plankv)"))
    b.append(R(10, 150, 226, 14, "nf s-ink", stroke_width=W["t"]))
    b.append(R(196, 164, 8, 72, "f-wood"))
    b.append(R(196, 164, 8, 72, fill=f"url(#{p}-plankh)"))
    b.append(R(184, 236, 32, 14, "f-wood"))
    b.append(R(184, 236, 32, 14, fill=f"url(#{p}-plankv)"))
    b.append(P("M196,164 V236 H184 V250 H216 V236 H204 V164", "nf s-ink", stroke_width=W["m"]))
    for yy in (180, 196, 212, 228):
        b.append(R(196.3, yy, 0.9, 3, "f-bldg s-ink", stroke_width=W["h"]))
        b.append(R(202.8, yy, 0.9, 3, "f-bldg s-ink", stroke_width=W["h"]))
    # edges: rock headland (W), breakwater (E), east wall
    b.append(PG(ROCK_W, "f-rock"))
    b.append(PG(ROCK_W, fill=f"url(#{p}-rock)"))
    b.append(PG(ROCK_W, "nf s-rockline", stroke_width=W["m"]))
    b.append(PG(BREAK_E, "f-rock"))
    b.append(PG(BREAK_E, fill=f"url(#{p}-tetra)"))
    b.append(PG(BREAK_E, "nf s-rockline", stroke_width=W["m"]))
    b.append(R(238, 28, 2, 120, "f-oob"))
    b.append(R(238, 28, 2, 120, fill=hatch))
    b.append(L(238, 28, 238, 150, "s-ink", stroke_width=W["k"]))
    for i, yy in enumerate(range(88, 146, 5)):
        b.append(R(236.4, yy, 0.9, 3.2, f"f-chalk{i % 4 + 1}"))

    # park: contours, knoll, path, pavilion, pond, trees
    for d, t, ly in CONTOURS:
        b.append(P(d, "nf s-treeline", stroke_width=W["h"], stroke_dasharray="1.2 0.8", opacity=0.85))
        b.append(T(12.8, ly, t, 1.9, "f-ink2 t-mono", anchor="start", halo=0.5))
    for yy in (143.5, 147):
        b.append(L(11, yy, 84, yy, "s-treeline", stroke_width=W["h"], stroke_dasharray="1.2 0.8", opacity=0.85))
    b.append(E(30, 42, 11, 7.5, "nf s-treeline", stroke_width=W["h"], stroke_dasharray="1.2 0.8"))
    b.append(E(30, 42, 6.5, 4.5, "nf s-treeline", stroke_width=W["h"], stroke_dasharray="1.2 0.8"))
    b.append(P(HILL_PATH, "nf s-ink2", stroke_width=3.5, stroke_linecap="round"))
    b.append(P(HILL_PATH, "nf s-pave", stroke_width=3.0, stroke_linecap="round"))
    b.append(L(44, 64, 52, 63.4, "s-ink2", stroke_width=2.6, stroke_linecap="round"))
    b.append(L(44, 64, 52, 63.4, "s-pave", stroke_width=2.1, stroke_linecap="round"))
    b.append(R(36, 60, 8, 8, "f-bldg s-ink", stroke_width=W["m"]))
    b.append(L(36, 60, 44, 68, "s-ink", stroke_width=W["h"]))
    b.append(L(44, 60, 36, 68, "s-ink", stroke_width=W["h"]))
    pond = "M13,110 C20,103 38,106 39,116 C40,128 31,135 21,134 C12,133 9,119 13,110 Z"
    b.append(P(pond, "f-pond s-ink", stroke_width=W["t"]))
    for i in range(7):
        b.append(C(17 + i * 3, 113 + i * 2.9, 0.75, "f-bldg2 s-ink", stroke_width=W["h"]))
    for lx, ly in [(28, 112), (34, 124), (16, 126), (24, 130)]:
        b.append(C(lx, ly, 1.0, "f-grass2"))
    b.append(L(84, 84, 84, 106, "s-ink2", stroke_width=W["m"]))
    b.append(L(84, 114, 84, 140, "s-ink2", stroke_width=W["m"]))
    b.append(L(64, 72, 64, 84, "s-ink2", stroke_width=W["m"]))
    for x, y, r in [(18, 34, 3.5), (48, 31, 3), (14, 62, 3), (22, 80, 3.5), (42, 88, 3), (14, 96, 3),
                    (52, 112, 3), (70, 97, 3), (78, 120, 3), (70, 137, 3.5), (50, 140, 3), (30, 142, 3),
                    (16, 141, 3), (23, 50, 2.6)]:
        b.append(tree(x, y, r, W))
    for x, y, r in [(62, 89, 3), (77, 90, 2.8), (76, 104, 2.6)]:
        b.append(tree(x, y, r, W, "f-blossom"))
    b.append(C(30, 42, 7, "f-pine s-treeline", stroke_width=W["t"]))
    b.append(C(30, 42, 4.2, "nf s-treeline", stroke_width=W["h"]))
    b.append(C(30, 42, 0.5, "f-treeline"))

    # stairs + escalators
    def stair(x, w):
        out = [R(x, 48, w, 16, "f-pave s-ink", stroke_width=W["t"])]
        out += treads(x, x + w, 48, 53.7) + treads(x, x + w, 56.7, 62.4)
        out += [L(x, 53.7, x + w, 53.7, "s-ink", stroke_width=W["t"]),
                L(x, 56.7, x + w, 56.7, "s-ink", stroke_width=W["t"]),
                L(x, 62.4, x + w, 62.4, "s-ink", stroke_width=W["t"])]
        return out
    b += stair(57, 6) + stair(112, 16) + stair(206, 12)
    for ex, word in ((108, "DN"), (128, "UP")):
        b.append(R(ex, 48, 4, 16, "f-bldg2 s-ink", stroke_width=W["t"]))
        b.append(R(ex + 0.6, 48.4, 2.8, 15.2, "nf s-ink3", stroke_width=W["h"]))
        b += [L(ex + 0.6, y, ex + 3.4, y, "s-ink3", stroke_width=0.08) for y in
              [50.5 + i * 0.52 for i in range(21)]]
        lab.append(T(ex + 2, 63.3, word, 1.5, "f-ink2 t-draw", weight=600))

    # shop buildings
    for key, x, y, w, h, fill, name, sub, n in SHOPS:
        b.append(R(x, y, w, h, fill))
        if key == "cafe":
            b.append(R(x, y, w, h, fill=f"url(#{p}-plankv)"))
            for ux in (70, 77, 84):
                b.append(C(ux, 59.5, 2.3, "nf s-ink2", stroke_width=W["h"], stroke_dasharray="0.8 0.6"))
            b.append(R(88, 49, 7, 8, "f-bldg2 s-ink", stroke_width=W["h"]))
            b.append(L(88, 49, 95, 57, "s-ink", stroke_width=W["h"]))
        b.append(R(x, y, w, h, "nf s-ink", stroke_width=W["k"]))
        cx = x + w / 2
        cy = y + h / 2 + (1.6 if key != "arcade" else 1.0)
        lab.append(T(cx, cy, name, 2.7 if len(name) < 8 else 2.4, "f-ink t-draw", weight=700, halo=0.5))
        lab.append(T(cx, cy + 2.9, sub, 1.9, "f-ink2 t-mono", halo=0.5))
    b.append(R(156, 71.1, 24, 0.9, "f-led"))
    b.append(R(160, 72, 16, 2.2, "nf s-ink", stroke_width=W["h"], stroke_dasharray="0.8 0.6"))
    b.append(PG([(166.8, 49.6), (169.2, 49.6), (168, 48.2)], "f-ink"))
    lab.append(T(168, 52.5, "L2 door to street", 1.6, "f-ink2 t-draw", halo=0.4))
    lab.append(T(168, 70.2, "LED BILLBOARD", 1.6, "f-ink2 t-draw", weight=600, halo=0.4))

    # upper street furniture
    b.append(R(112, 30, 16, 7, "f-bldg2 s-ink", stroke_width=W["m"]))
    b += treads(114, 126, 30.6, 36.4, step=0.6)
    lab.append(T(120, 34.3, "METRO", 2.2, "f-ink t-draw", weight=700, halo=0.5))
    b.append(R(196, 29.6, 10, 2.4, "f-bldg2 s-ink", stroke_width=W["t"]))
    lab.append(T(201, 35, "BUS", 1.8, "f-ink2 t-draw", weight=600, halo=0.4))
    for tx in (104, 136):
        b.append(C(tx, 46.4, 0.6, "f-ink"))
    for x0, x1 in ((60, 108), (132, 206), (218, 238)):
        b.append(L(x0, 47.8, x1, 47.8, "s-ink2", stroke_width=W["t"]))
    for x0, x1 in ((64, 108), (132, 206)):
        pts = [(x, 46.6 if i % 2 == 0 else 47.5) for i, x in enumerate(range(x0, x1 + 1, 2))]
        b.append(PG(pts, "nf s-chalk1", closed=False, stroke_width=0.28))
    for x in (74, 90, 146, 162, 178, 216, 232):
        b.append(tree(x, 31.6, 2.6, W))

    # shop lane: lamps, string lights, terrace, tables, vending
    for x in range(72, 237, 16):
        b.append(C(x, 83.2, 0.55, "f-sheet s-ink", stroke_width=W["h"]))
    zig = [(64 + 8 * i, 75.6 if i % 2 == 0 else 82.4) for i in range(22)]
    b.append(PG(zig, "nf s-umbrella", closed=False, stroke_width=0.3, stroke_dasharray="0.4 0.9"))
    b.append(R(64, 66, 32, 8, "f-wood"))
    b.append(R(64, 66, 32, 8, "nf s-ink2", stroke_width=W["h"], stroke_dasharray="1 0.8"))
    for ux in (69, 76.5, 84, 91.5):
        b.append(C(ux, 70, 2.2, "f-umbrella s-ink", stroke_width=W["h"]))
        b.append(C(ux, 70, 0.3, "f-ink"))
    for tx, ty in [(135, 67), (139.5, 67), (144, 67), (135, 71), (139.5, 71), (144, 71)]:
        b.append(R(tx - 0.6, ty - 0.6, 1.2, 1.2, "f-sheet s-ink", stroke_width=W["h"]))
    for i in range(7):
        b.append(R(220 + i * 1.5, 48.5, 1.2, 0.9, f"f-chalk{i % 4 + 1} s-ink", stroke_width=W["h"]))
    for i in range(5):
        b.append(L(222 + i * 1.6, 58.5, 222 + i * 1.6, 61.5, "s-ink2", stroke_width=W["t"]))
    b.append(tree(232, 70, 3, W))

    # central plaza
    chalk = [(113, 99, 6, 3, 30, 1), (126, 108, 7, 3.5, -20, 3), (118, 111, 5, 2.5, 10, 2),
             (124, 97, 4, 2, 60, 4), (110, 106, 3.5, 2, -40, 2), (129, 103, 3, 1.6, 20, 1),
             (120, 104, 2.6, 2.6, 0, 4)]
    b.append(C(120, 104, 13, "f-pave"))
    b.append(G([E(x, y, rx, ry, f"f-chalk{c}", opacity=0.8, transform=f"rotate({a} {x} {y})")
                for x, y, rx, ry, a, c in chalk], clip_path=f"url(#{p}-emote)"))
    b.append(C(120, 104, 13, "nf s-ink", stroke_width=W["t"], stroke_dasharray="1.4 0.7"))
    b.append(R(146, 94, 18, 12, "f-wood s-ink", stroke_width=W["k"]))
    b.append(L(146.8, 94, 146.8, 106, "s-ink", stroke_width=W["t"]))
    b.append(R(162.6, 94.6, 1.2, 1.8, "f-ink"))
    b.append(R(162.6, 103.6, 1.2, 1.8, "f-ink"))
    b.append(C(120, 128, 8, "f-pond s-ink", stroke_width=W["t"]))
    for i in range(12):
        a = math.radians(i * 30)
        b.append(C(120 + 5.6 * math.cos(a), 128 + 5.6 * math.sin(a), 0.35, "f-sheet"))
    for i in range(6):
        a = math.radians(i * 60 + 30)
        b.append(C(120 + 2.8 * math.cos(a), 128 + 2.8 * math.sin(a), 0.35, "f-sheet"))
    b.append(R(89, 94, 10, 3.6, "f-chalk3 s-ink", stroke_width=W["t"], rx=0.6))
    b.append(L(91, 97.6, 97, 97.6, "s-ink", stroke_width=W["m"]))
    b.append(R(89, 112, 8, 3.4, "f-chalk1 s-ink", stroke_width=W["t"], rx=0.6))
    for ux, uy in [(98, 129), (104, 135), (138, 135), (144, 129), (150, 135)]:
        b.append(C(ux, uy, 2.2, "f-umbrella s-ink", stroke_width=W["h"]))
        b.append(C(ux, uy, 0.3, "f-ink"))
    for x, y in [(88.5, 88.5), (167.5, 88.5), (88.5, 137), (167.5, 137)]:
        b.append(tree(x, y, 3, W))
    for bx, by in [(103, 87.5), (133, 87.5), (106, 118.8), (130, 118.8)]:
        b.append(R(bx, by, 4, 1, "f-bldg s-ink", stroke_width=W["h"]))

    # east deck (skate)
    b.append(R(192, 89, 16, 1.2, "f-bldg s-ink", stroke_width=W["t"]))
    b.append(R(212, 89, 14, 1.2, "f-bldg s-ink", stroke_width=W["t"]))
    b.append(C(182, 100, 4, "f-sheet s-ink", stroke_width=W["m"]))
    for ang, c in ((0, 1), (60, 2), (120, 3)):
        b.append(R(180.6, 96.4, 2.8, 7.2, f"f-chalk{c} s-ink", stroke_width=W["h"], rx=1.4,
                   transform=f"rotate({ang} 182 100)"))
    b.append(R(204, 102, 28, 12, "f-pave s-ink", stroke_width=W["m"]))
    b.append(R(200, 102, 4, 12, "f-pave s-ink", stroke_width=W["t"]))
    b += [L(x, 102, x, 114, "s-ink3", stroke_width=0.1) for x in (200.8, 201.6, 202.4, 203.2)]
    b.append(L(200, 108, 204, 108, "s-ink", stroke_width=W["k"]))
    b.append(R(233, 86, 4.5, 16, "f-bldg2 s-ink", stroke_width=W["t"]))
    b.append(L(233, 86, 233, 102, "s-ink", stroke_width=W["k"]))
    b += [L(x, 86, x, 102, "s-ink3", stroke_width=0.1) for x in (234.2, 235.4, 236.6)]
    b.append(R(178, 116, 12, 4, "f-bldg s-ink", stroke_width=W["t"]))
    b.append(R(208, 120, 12, 4, "f-bldg s-ink", stroke_width=W["t"]))
    b.append(E(196, 136, 14, 7.5, "f-bldg s-ink", stroke_width=W["m"]))
    b.append(E(196, 136, 10, 4.6, "nf s-ink3", stroke_width=W["h"]))
    b.append(E(196, 136, 5, 1.9, "nf s-ink3", stroke_width=W["h"]))
    b.append(R(222, 126, 10, 24, "f-pave s-ink", stroke_width=W["t"]))
    b.append(L(224.5, 129, 224.5, 147, "s-ink", stroke_width=W["t"], marker_end=f"url(#{p}-arr)"))
    lab.append(T(229.6, 138, "1:13", 1.8, "f-ink2 t-mono", rot=90, halo=0.4))
    b.append(R(176, 146.7, 14, 3.3, "f-pave s-ink", stroke_width=W["t"]))
    b += [L(176, y, 190, y, "s-ink3", stroke_width=0.08) for y in (147.4, 148.0, 148.6, 149.2)]
    b.append(L(183, 146.7, 183, 150, "s-ink", stroke_width=W["k"]))
    b.append(L(190, 149.5, 222, 149.5, "s-ink2", stroke_width=W["t"]))
    b.append(L(172, 149.5, 176, 149.5, "s-ink2", stroke_width=W["t"]))
    b.append(L(232, 149.5, 236, 149.5, "s-ink2", stroke_width=W["t"]))
    b.append(tree(176.6, 128, 2.4, W))
    lab.append(T(214, 110.6, "+0.75", 1.9, "f-ink2 t-mono", halo=0.4))
    lab.append(T(183, 145.4, "12-stair", 1.6, "f-ink2 t-draw", halo=0.4))

    # promenade furniture
    for x in range(18, 233, 16):
        b.append(C(x, 151.3, 0.55, "f-sheet s-ink", stroke_width=W["h"]))
        bx = x + 8
        if bx < 232 and not 192 <= bx <= 208:
            b.append(R(bx - 1.6, 162.3, 3.2, 0.9, "f-bldg s-ink", stroke_width=W["h"]))
    b.append(R(22, 152.4, 8, 4, "f-chalk3 s-ink", stroke_width=W["t"]))
    b.append(R(62, 152.4, 7, 4, "f-chalk2 s-ink", stroke_width=W["t"]))
    b.append(R(146, 152.4, 9, 4, "f-bldg2 s-ink", stroke_width=W["t"]))
    for sx in (92, 152):
        b.append(C(sx, 165.6, 0.55, "f-water s-ink", stroke_width=W["h"]))

    # beach
    b.append(L(26, 171, 40, 171, "s-ink", stroke_width=W["m"]))
    b += [R(26.8 + 3.4 * i, 171.7, 1.8, 0.7, "f-wood s-ink", stroke_width=W["h"]) for i in range(4)]
    for x, y in [(22, 184), (30, 190), (38, 184)]:
        b.append(tree(x, y, 2, W))
    b.append(P("M22,184 Q26.5,189.5 30,190", "nf s-chalk1", stroke_width=0.5))
    b.append(P("M30,190 Q35.5,189.5 38,184", "nf s-chalk3", stroke_width=0.5))
    b.append(C(64, 186, 1.8, "f-fire s-ink", stroke_width=W["t"]))
    for i in range(8):
        a = math.radians(i * 45)
        lx, ly = 64 + 6 * math.cos(a), 186 + 6 * math.sin(a)
        b.append(R(lx - 1.3, ly - 0.45, 2.6, 0.9, "f-wood s-ink", stroke_width=W["h"], rx=0.4,
                   transform=f"rotate({fmt(float(i * 45 + 90))} {fmt(lx)} {fmt(ly)})"))
    for ux, uy in UMBRELLAS_BEACH:
        b.append(R(ux + 2.6, uy - 0.45, 2.3, 0.9, "f-sheet s-ink", stroke_width=W["h"], rx=0.3))
        b.append(C(ux, uy, 2.2, "f-umbrella s-ink", stroke_width=W["h"]))
        b.append(C(ux, uy, 0.3, "f-ink"))
    b.append(C(154, 192, 3, "nf s-ink2", stroke_width=W["t"], stroke_dasharray="0.6 0.6"))
    b.append(R(118, 198, 4, 4, "f-sheet s-ink", stroke_width=W["m"]))
    b.append(L(118, 198, 122, 202, "s-ink", stroke_width=W["h"]))
    b.append(L(122, 198, 118, 202, "s-ink", stroke_width=W["h"]))
    b.append(R(160, 170, 24, 16, "nf s-ink3", stroke_width=W["h"], stroke_dasharray="1 0.8"))
    b.append(R(164, 174, 16, 8, "nf s-ink", stroke_width=W["t"]))
    b.append(L(172, 173, 172, 183, "s-ink", stroke_width=W["m"]))
    b.append(R(212, 167, 14, 9, "f-chalk3 s-ink", stroke_width=W["m"]))
    b.append(R(212, 176, 14, 3, "f-wood s-ink", stroke_width=W["h"]))
    for i, c in enumerate((2, 1, 4)):
        b.append(E(229 + i * 1.6, 171, 0.6, 2.6, f"f-chalk{c} s-ink", stroke_width=W["h"]))
    lab.append(T(154, 197, "sandcastles", 1.6, "f-ink2 t-draw", halo=0.4))

    # water
    b.append(R(100, 222, 8, 6, "f-wood s-ink", stroke_width=W["t"]))
    for x in range(38, 196, 8):
        b.append(C(x, 232, 0.7, "f-fire s-ink", stroke_width=W["h"]))
    b.append(C(211, 244, 3.2, "f-sheet s-ink", stroke_width=W["m"]))
    b.append(C(211, 244, 2.0, "f-bound"))
    b.append(C(211, 244, 0.9, "f-sheet"))
    for fx, fy in [(188, 249.3), (194, 249.3), (200, 249.3), (206, 249.3), (184.7, 240), (184.7, 245)]:
        b.append(C(fx, fy, 0.5, "nf s-ink", stroke_width=W["t"]))
    b.append(C(188, 239, 0.6, "f-ink"))

    # north arrow + scale bar
    b.append(G([C(0, 0, 4, "f-sheet s-ink", stroke_width=W["t"]),
                P("M0,-3.4 L1.6,2.2 L0,1 L-1.6,2.2 Z", "f-ink"),
                T(0, -5.4, "N", 2.6, "f-ink t-draw", weight=700)], transform="translate(251 -5)"))
    for i in range(5):
        b.append(R(40 + 10 * i, 252, 10, 1.4, ("f-ink" if i % 2 == 0 else "f-sheet") + " s-ink",
                   stroke_width=W["h"]))
    for i in range(6):
        b.append(T(40 + 10 * i, 256.6, str(10 * i), 1.9, "f-ink t-mono", halo=0.5))
    b.append(T(92, 253.4, "m", 1.9, "f-ink t-mono", anchor="start", halo=0.5))

    # ---- labels layer: zones + callouts
    def zone(x, y, name, sub=None, anchor="middle", size=3.6, rot=None):
        out = [T(x, y, name, size, "f-ink t-draw", anchor=anchor, weight=700, ls=0.15, halo=0.7, rot=rot)]
        if sub:
            if rot:
                out.append(T(x + 3.6, y, sub, 2.1, "f-ink2 t-mono", anchor=anchor, halo=0.5, rot=rot))
            else:
                out.append(T(x, y + 3.6, sub, 2.1, "f-ink2 t-mono", anchor=anchor, halo=0.5))
        return out
    lab += zone(180, 39, "UPPER STREET", "+6.00")
    lab += zone(207, 79, "SHOP LANE", "±0.00")
    lab += zone(150, 115.5, "CENTRAL PLAZA", "±0.00")
    lab += zone(60, 120.5, "PINE HILL PARK", "+7.50 → ±0.00")
    lab += zone(212, 95.4, "EAST DECK", "skate · ±0.00", size=3.2)
    lab += zone(86, 157.6, "SEASIDE PROMENADE", "−1.80")
    lab += zone(82, 200, "BEACH", "−2.10 → −3.00")
    lab += zone(70, 220.5, "SWIM ZONE", "≤ 2.5 m deep", size=3.0)
    lab += zone(150, 243, "DEEP WATER · OUT OF BOUNDS", size=2.6)
    lab.append(T(120, 104.9, "EMOTE SQUARE", 2.4, "f-ink t-draw", weight=700, halo=0.6))
    lab.append(T(155, 101, "STAGE", 2.4, "f-ink t-draw", weight=700, halo=0.5))
    lab.append(T(106, 147, "SUNSET STEPS", 2.2, "f-ink t-draw", weight=700, halo=0.5))
    lab.append(T(200.2, 213, "PIER  −1.80", 2.2, "f-ink t-draw", weight=700, rot=-90, halo=0.5))
    lab.append(T(90, 23.2, "COASTAL ROAD · ambient traffic", 2.2, "f-ink2 t-draw", weight=600, halo=0.5))
    lab.append(T(178, 9.2, "BACKDROP · HILLSIDE TOWN (OUT OF BOUNDS)", 2.2, "f-ink2 t-draw", weight=600, halo=0.6))
    lab.append(T(5.2, 100, "ROCK HEADLAND", 2.1, "f-ink2 t-draw", weight=700, rot=-90, halo=0.5))
    lab.append(T(236.4, 222, "BREAKWATER", 2.0, "f-ink2 t-draw", weight=700, rot=-90, halo=0.5))
    for n, (x, y) in BUBBLES.items():
        lab.append(bubble(x, y, n))

    # ---- grid layer: grid, dims, spot levels, section + elevation markers
    for i, x in enumerate(range(0, SITE_W + 1, 20)):
        grid.append(L(x, -4.8, x, SITE_D, "s-ink3", stroke_width=0.12, stroke_dasharray="1 1.4", opacity=0.8))
        grid.append(C(x, -8.5, 3.2, "f-sheet s-ink2", stroke_width=W["t"]))
        grid.append(T(x, -8.4, chr(65 + i), 2.8, "f-ink2 t-draw", weight=700, base="central"))
    for i, y in enumerate(range(0, SITE_D + 1, 20)):
        grid.append(L(-4.8, y, SITE_W, y, "s-ink3", stroke_width=0.12, stroke_dasharray="1 1.4", opacity=0.8))
        grid.append(C(-8.5, y, 3.2, "f-sheet s-ink2", stroke_width=W["t"]))
        grid.append(T(-8.5, y + 0.1, str(i + 1), 2.6, "f-ink2 t-draw", weight=700, base="central"))

    def tick(x, y):
        return L(x - 0.8, y + 0.8, x + 0.8, y - 0.8, "s-ink", stroke_width=W["t"])

    def hdim(x1, x2, y, text):
        return [L(x1, y, x2, y, "s-ink2", stroke_width=W["h"]), tick(x1, y), tick(x2, y),
                T((x1 + x2) / 2, y - 0.9, text, 2.0, "f-ink t-mono", halo=0.5)]

    def vdim(x, y1, y2, text):
        return [L(x, y1, x, y2, "s-ink2", stroke_width=W["h"]), tick(x, y1), tick(x, y2),
                T(x + 1.4, (y1 + y2) / 2 + 0.7, text, 2.0, "f-ink t-mono", anchor="start", halo=0.5)]
    for x1, x2 in ((10, 84), (84, 172), (172, 238)):
        grid += hdim(x1, x2, 264.5, f"{x2 - x1}")
    grid += hdim(0, 240, 270, "240 m")
    chain = [0, 16, 28, 48, 84, 142, 150, 164, 210, 260]
    for y1, y2 in zip(chain, chain[1:]):
        grid += vdim(244, y1, y2, f"{y2 - y1}")
    grid.append(L(254, 0, 254, 260, "s-ink2", stroke_width=W["h"]))
    grid += [tick(254, 0), tick(254, 260), T(257.6, 130, "260 m", 2.0, "f-ink t-mono", rot=-90, halo=0.5)]

    def spot(x, y, text):
        return [P(f"M{x - 0.9},{y}h1.8M{x},{y - 0.9}v1.8", "s-ink", stroke_width=W["t"]),
                C(x, y, 0.5, "nf s-ink", stroke_width=W["t"]),
                T(x + 1.3, y + 0.75, text, 2.0, "f-ink t-mono", anchor="start", halo=0.5)]
    for x, y, t in [(37.5, 50, "+7.50"), (58, 166.8, "−2.10"), (54, 213.5, "−3.00 WL"),
                    (150, 236.5, "−5.50"), (205.5, 137.4, "−1.80"), (138, 88.4, "±0.00")]:
        grid += spot(x, y, t)
    grid.append(L(120, 10, 120, 252, "s-accent", stroke_width=W["t"], stroke_dasharray="4 1.2 0.8 1.2"))
    for y, t in ((6.6, "A"), (255.4, "A′")):
        grid.append(PG([(122.4, y - 1.8), (126, y), (122.4, y + 1.8)], "f-accent"))
        grid.append(C(120, y, 2.8, "f-sheet s-accent", stroke_width=W["m"]))
        grid.append(T(120, y + 0.1, t, 2.4, "f-accent t-draw", weight=700, base="central"))
    grid.append(PG([(98.2, 77.6), (100, 75), (101.8, 77.6)], "f-accent"))
    grid.append(C(100, 80, 2.4, "f-sheet s-accent", stroke_width=W["m"]))
    grid.append(T(100, 80.1, "E1", 2.0, "f-accent t-draw", weight=700, base="central"))

    # ---- system layer: spawns + boundaries
    def spawn(x, y, name):
        return G([P("M-1.7,2.3 L1.7,2.3 L0,5.4 Z", "f-spawn"),
                  C(0, 0, 2.8, "f-spawn s-sheet", stroke_width=0.4),
                  T(0, 0.1, name, 2.3, "f-onaccent t-draw", weight=700, base="central")],
                 transform=f"translate({fmt(float(x))} {fmt(float(y))})")
    hard = dict(stroke_width=0.5, stroke_dasharray="2.2 1.2")
    sysl.append(L(10, 28.3, 238, 28.3, "s-bound", **hard))
    sysl.append(PG(ROCK_W[1:-2], "nf s-bound", closed=False, **hard))
    sysl.append(PG([(238, 28.3), (238, 148)] + BREAK_E[1:-1], "nf s-bound", closed=False, **hard))
    sysl.append(L(36, 240, 221, 240, "s-bound", stroke_width=0.45, stroke_dasharray="0.6 1.1"))
    sysl.append(L(30, 258, 224, 258, "s-bound", **hard))
    sysl.append(T(150, 26.9, "HARD EDGE · bollards + chain", 1.8, "f-bound t-draw", weight=700, halo=0.4))
    sysl.append(T(80, 239, "SOFT EDGE · swim push-back", 1.8, "f-bound t-draw", weight=700, halo=0.4))
    sysl.append(T(170, 256.8, "HARD EDGE", 1.8, "f-bound t-draw", weight=700, halo=0.4))
    sysl.append(spawn(120, 41.6, "S1"))
    sysl.append(spawn(106, 121, "S2"))
    sysl.append(spawn(120, 156.4, "S3"))

    # ---- circulation layer
    circ = lay["circ"]
    route = dict(stroke_linejoin="round", stroke_linecap="round", opacity=0.6)
    circ.append(PG(LOOP, "nf s-route", closed=False, stroke_width=1.6, **route))
    circ.append(L(120, 36, 120, 210, "s-route", stroke_width=0.9, stroke_dasharray="2.4 1.2", opacity=0.8))
    circ.append(L(62, 38, 236, 38, "s-route", stroke_width=0.9, opacity=0.6))
    circ.append(P(HILL_PATH, "nf s-route", stroke_width=0.9, opacity=0.6))
    circ.append(L(200, 164, 200, 242, "s-route", stroke_width=0.9, opacity=0.6))
    circ.append(PG(SKATE_LINE, "nf s-skate", closed=False, stroke_width=1.1, stroke_dasharray="2.4 1",
                   **route))
    loop_m = polyline_len(LOOP)
    skate_m = polyline_len(SKATE_LINE[2:])
    circ.append(T(146, 77.2, f"PRIMARY LOOP ≈ {loop_m:.0f} m · {loop_m / 5.5:.0f} s run", 2.0,
                  "f-route t-draw", weight=700, halo=0.5))
    circ.append(T(150, 161.8, f"SKATE CRUISE LINE ≈ {skate_m:.0f} m", 2.0, "f-skate t-draw", weight=700, halo=0.5))
    circ.append(T(123.4, 186, "MAIN AXIS · S1 → SEA", 2.0, "f-route t-draw", weight=700, rot=-90, halo=0.5))

    # ---- sightline layer
    sight = lay["sight"]
    sight.append(PG([(120, 41.6), (40, 236), (206, 236)], "f-sight", opacity=0.1))
    sight.append(PG([(40, 236), (120, 41.6), (206, 236)], "nf s-sight", closed=False, stroke_width=0.5,
                    stroke_dasharray="1.6 1"))
    sight.append(R(116, 64, 8, 146, "f-sight", opacity=0.14))
    sight.append(L(120, 186, 168, 73, "s-sight", stroke_width=0.5, stroke_dasharray="1.6 1"))
    sight.append(T(124, 228, "ARRIVAL VIEW FROM S1", 2.2, "f-sight t-draw", weight=700, halo=0.5))
    sight.append(T(137, 66.8, "KEEP CLEAR · VIEW AXIS 8 m", 1.9, "f-sight t-draw", weight=700, halo=0.5))
    sight.append(T(158, 125, "look-back to LED", 1.9, "f-sight t-draw", weight=700, halo=0.5, rot=-67))

    # ---- activity zones layer
    zones = lay["zones"]
    for (x, y, w, h), tok, name, tx, ty, anc in [
        ((10, 28, 86, 122), "zchill", "CHILL", 13, 146.4, "start"),
        ((96, 64, 52, 86), "zsocial", "SOCIAL", 122, 141.2, "middle"),
        ((148, 48, 90, 102), "zactive", "ACTIVE", 235, 146.4, "end"),
        ((10, 150, 226, 90), "zleisure", "LEISURE", 13, 236.8, "start"),
    ]:
        zones.append(R(x, y, w, h, f"f-{tok}", opacity=0.16))
        zones.append(R(x, y, w, h, f"nf s-{tok}", stroke_width=0.5, opacity=0.8))
        zones.append(T(tx, ty, name, 3.2, f"f-{tok} t-draw", anchor=anc, weight=700, ls=0.3, halo=0.6))

    meta = {"loop_m": loop_m, "skate_m": skate_m}
    return defs, lay, meta


def plan_svg(inline=True):
    defs, lay, meta = site_plan("p")
    on = {"base", "grid", "system", "labels"}
    parts = [defs]
    for k in ("base", "zones", "circ", "sight", "grid", "system", "labels"):
        if not inline and k not in on:
            continue
        parts.append(G(lay[k], id=f"p-{k}", hidden=None if k in on else "hidden"))
    svg = svg_wrap(parts, "-14 -14 272 288", "Bayside Park site plan, north up, 1 unit = 1 metre",
                   inline, el_id="plan-svg" if inline else None, px_per_unit=4.5)
    return svg, meta


# ---------------------------------------------------------------- section ---
def section_svg(inline=True):
    VE = 2.0

    def Y(z):
        return (20 - z) * VE
    W = dict(h=0.14, t=0.24, m=0.4, k=0.7)
    out = []
    # grid bubbles (plan rows) + datum lines
    for i, s in enumerate(range(0, 261, 20)):
        out.append(L(s, -5, s, 62, "s-ink3", stroke_width=0.12, stroke_dasharray="1 1.4", opacity=0.7))
        out.append(C(s, -8.5, 2.8, "f-sheet s-ink2", stroke_width=W["t"]))
        out.append(T(s, -8.4, str(i + 1), 2.4, "f-ink2 t-draw", weight=700, base="central"))
    for z in (6, 0, -1.8, -3):
        out.append(L(-4, Y(z), 266, Y(z), "s-ink3", stroke_width=W["h"], stroke_dasharray="1.4 1.4"))

    # beyond (looking east): farthest first, sheet-filled so nearer ones occlude
    beyond = "f-sheet s-ink3"
    for s0, w, top in [(0, 7, 18), (7.5, 8, 15)]:
        out.append(R(s0, Y(top), w, Y(6) - Y(top), "f-oob s-ink3", stroke_width=W["h"]))
    floor_z = lambda s: -3 - (s - 210) * 2.5 / 22 if s <= 232 else -5.5 - (s - 232) * 0.097
    sand_z = lambda s: -2.1 - (s - 164) * 0.9 / 46
    for s in range(170, 250, 6):
        zb = sand_z(s) if s < 210 else floor_z(s)
        out.append(L(s, Y(-2.2), s, Y(zb), "s-ink3", stroke_width=W["t"]))
    # sculpture + stage, arcade + mart + escalator
    for i in range(5):
        zc = 1.4 + i * 2.3
        out.append(R(96.5, Y(zc + 0.5), 7, VE, beyond, stroke_width=W["h"], rx=1,
                     transform=f"rotate({12 if i % 2 else -12} 100 {fmt(Y(zc))})"))
    out.append(R(94, Y(1.0), 12, Y(0) - Y(1.0), beyond, stroke_width=W["t"]))
    out.append(R(94.5, Y(7), 11, Y(1) - Y(7), "nf s-ink3", stroke_width=W["h"]))
    out.append(L(94.5, Y(7), 105.5, Y(1), "s-ink3", stroke_width=0.1))
    out.append(L(94.5, Y(1), 105.5, Y(7), "s-ink3", stroke_width=0.1))
    out.append(R(48, Y(11.5), 24, Y(0) - Y(11.5), beyond, stroke_width=W["t"]))
    out.append(L(48, Y(6), 72, Y(6), "s-ink3", stroke_width=W["h"], stroke_dasharray="1 0.8"))
    out.append(R(70.8, Y(18), 1.4, Y(11.5) - Y(18), "f-led", opacity=0.75))
    out.append(R(48, Y(4.5), 16, Y(0) - Y(4.5), beyond, stroke_width=W["t"]))
    esc = [(48, 6), (50.5, 6), (60.9, 0), (63.4, 0), (63.4, 1), (60.9, 1), (50.5, 7), (48, 7)]
    out.append(PG([(s, Y(z)) for s, z in esc], beyond, stroke_width=W["t"]))
    zs = sand_z(176)
    out.append(L(176, Y(zs), 176, Y(zs + 2.3), "s-ink3", stroke_width=W["t"]))
    out.append(PG([(173.6, Y(zs + 2.0)), (176, Y(zs + 2.7)), (178.4, Y(zs + 2.0))], "f-umbrella s-ink3",
                  stroke_width=W["h"]))

    # water body (cut)
    out.append(PG([(210, Y(-3)), (266, Y(-3)), (266, Y(-8.8)), (232, Y(-5.5))], "f-water", opacity=0.92))
    out.append(L(208, Y(-3), 266, Y(-3), "s-route", stroke_width=W["t"]))
    # pier deck + lighthouse (beyond, above water)
    out.append(R(164, Y(-1.8), 86, Y(-2.2) - Y(-1.8), "f-wood s-ink3", stroke_width=W["h"]))
    lh = [(240.8, -1.8), (247.2, -1.8), (246, 9), (242, 9)]
    out.append(PG([(s, Y(z)) for s, z in lh], beyond, stroke_width=W["t"]))
    for z0, z1 in ((1, 2.6), (5.2, 6.8)):
        w0 = 3.2 - 1.2 * (z0 + 1.8) / 10.8
        w1 = 3.2 - 1.2 * (z1 + 1.8) / 10.8
        out.append(PG([(244 - w0, Y(z0)), (244 + w0, Y(z0)), (244 + w1, Y(z1)), (244 - w1, Y(z1))], "f-bound",
                      opacity=0.75))
    out.append(R(242.5, Y(10.8), 3, Y(9) - Y(10.8), "f-umbrella s-ink3", stroke_width=W["h"]))
    out.append(PG([(242, Y(10.8)), (246, Y(10.8)), (244, Y(12))], beyond, stroke_width=W["h"]))

    # cut ground profile
    prof = [(-4, 5.85), (28, 5.85), (28, 6.0), (48, 6.0)]

    def flight(s, z):
        pts = []
        for i in range(20):
            z -= 0.15
            pts.append((s, z))
            if i < 19:
                s += 0.3
                pts.append((s, z))
        return pts, s, z
    f1, s, z = flight(48, 6.0)
    prof += f1 + [(56.7, 3.0)]
    f2, s, z = flight(56.7, 3.0)
    prof += f2
    prof += [(142, 0), (142, -0.45), (144, -0.45), (144, -0.9), (146, -0.9), (146, -1.35), (148, -1.35),
             (148, -1.8), (164, -1.8), (164, -2.1), (210, -3.0), (232, -5.5), (266, -8.8)]
    poche = [(s, Y(z)) for s, z in prof] + [(266, Y(-11)), (-4, Y(-11))]
    out.append(PG(poche, "f-cut"))
    out.append(PG([(s, Y(z)) for s, z in prof], "nf s-ink", closed=False, stroke_width=W["m"]))
    # cut items
    out.append(R(30, Y(10), 7, VE * 0.4, "f-cut"))
    out += [L(sx, Y(6), sx, Y(9.6), "s-ink2", stroke_width=W["t"]) for sx in (30.4, 36.6)]
    out.append(R(28.2, Y(6.9), 0.5, VE * 0.9, "f-cut"))
    for s0, s1, c in [(91, 96, 1), (96, 103, 3), (103, 108, 2), (108, 113, 4), (113, 117, 1)]:
        out.append(R(s0, Y(0) - 0.45, s1 - s0, 0.45, f"f-chalk{c}"))
    for i, sx in enumerate(range(121, 136, 2)):
        out.append(L(sx, Y(0), sx, Y(1.2 + 0.4 * (i % 2)), "s-route", stroke_width=W["t"]))
    zt = sand_z(200)
    out += [L(sx, Y(zt), sx, Y(-0.7), "s-ink", stroke_width=W["t"]) for sx in (198.4, 201.6)]
    out.append(R(197.6, Y(-0.6), 4.8, VE * 0.15, "f-cut"))
    out.append(R(198.4, Y(1.2), 3.2, Y(-0.6) - Y(1.2), "nf s-ink", stroke_width=W["t"]))
    out.append(PG([(197.8, Y(1.2)), (202.2, Y(1.2)), (200, Y(1.9))], "f-cut"))
    out.append(R(222, Y(-2.6), 6, VE * 0.4, "f-wood s-ink", stroke_width=W["t"]))
    out.append(C(232, Y(-2.85), 0.75, "f-fire s-ink", stroke_width=W["h"]))

    # scale figures (1.50 m)
    def fig(s, z):
        return G([C(s, Y(z + 1.36), 0.4, "f-ink2"),
                  R(s - 0.36, Y(z + 1.12), 0.72, Y(z + 0.55) - Y(z + 1.12), "f-ink2", rx=0.3),
                  L(s - 0.18, Y(z + 0.58), s - 0.22, Y(z), "s-ink2", stroke_width=0.28),
                  L(s + 0.18, Y(z + 0.58), s + 0.22, Y(z), "s-ink2", stroke_width=0.28)])
    out += [fig(41, 6.0), fig(72, 0), fig(112, 0), fig(156, -1.8), fig(186, sand_z(186))]
    out.append(C(218, Y(-2.85), 0.4, "f-ink2"))

    # sightline + horizon
    eye = (41, 7.35)
    out.append(L(eye[0], Y(eye[1]), 210, Y(-3.0), "s-sight", stroke_width=W["m"], stroke_dasharray="1.6 1"))
    out.append(L(eye[0], Y(eye[1]), 266, Y(eye[1]), "s-sight", stroke_width=W["h"], stroke_dasharray="0.6 1.2"))
    out.append(C(eye[0], Y(eye[1]), 0.6, "f-sight"))
    ang = math.degrees(math.atan2(Y(-3.0) - Y(eye[1]), 210 - eye[0]))
    ly = Y(eye[1]) + (160 - eye[0]) * math.tan(math.radians(ang)) - 1.0
    out.append(T(160, ly, "ARRIVAL SIGHTLINE", 1.9, "f-sight t-draw", weight=700, rot=ang, halo=0.45))
    out.append(T(238, Y(eye[1]) - 0.9, "HORIZON · EYE LEVEL", 1.8, "f-sight t-draw", anchor="end", weight=700,
                 halo=0.45))

    # annotations
    sky = [(41, Y(12.6), "S1 SPAWN · EYE +7.35", (41, Y(12.1), 41, Y(7.9))),
           (74, Y(17.4), "ARCADE + LED BILLBOARD +18.00 (BEYOND)", None),
           (100, Y(13.5), "SKATE SCULPTURE +12.00 (BEYOND)", None),
           (128, Y(3.0), "FLOOR FOUNTAIN · JETS ≤ 1.6 m", None),
           (200, Y(2.5), "LIFEGUARD TOWER", None),
           (244, Y(13.4), "PIER + LIGHTHOUSE (BEYOND)", None),
           (239, Y(-0.4), "BUOY LINE · SOFT EDGE", (232, Y(-0.8), 232, Y(-2.3)))]
    for x, y, t, lead in sky:
        anchor = "start" if t.startswith("ARCADE") else ("end" if t.startswith("BUOY") else "middle")
        out.append(T(x, y, t, 1.9, "f-ink t-draw", anchor=anchor, weight=600, halo=0.45))
        if lead:
            out.append(L(*lead, "s-ink2", stroke_width=W["h"]))
    poche_lbl = [(55, 46.5, "GRAND STEPS · 2 × 20 RISERS 0.15/0.30 · LANDING +3.00"),
                 (104, 46.5, "EMOTE SQUARE"), (128, 46.5, "FOUNTAIN"),
                 (147, 50.5, "SUNSET STEPS · 4 TIERS 0.45 × 2.00"), (157, 54.5, "BOARDWALK −1.80"),
                 (188, 52, "BEACH 1:51 → WL −3.00")]
    for x, y, t in poche_lbl:
        out.append(T(x, y, t, 1.8, "f-sheet t-draw", weight=600))
    out.append(T(246, 50, "SWIM ZONE ≤ 2.5 m", 1.8, "f-ink t-draw", weight=600))

    # levels on the right
    for z, t, dy in ((6, "+6.00", 0), (0, "±0.00", 0), (-1.8, "−1.80", -0.2), (-3, "−3.00 WL", 0.5)):
        out.append(PG([(266.6, Y(z)), (268.2, Y(z) - 0.9), (268.2, Y(z) + 0.9)], "f-ink"))
        out.append(T(269, Y(z) + 0.65 + dy, t, 1.9, "f-ink t-mono", anchor="start"))
    # zone strip
    zones = [(-4, 16, "BACKDROP"), (16, 28, "ROAD"), (28, 48, "UPPER ST"), (48, 64, "GRAND STEPS"),
             (64, 84, "SHOP LANE"), (84, 142, "CENTRAL PLAZA"), (142, 150, "STEPS"), (150, 164, "PROM."),
             (164, 210, "BEACH"), (210, 232, "SWIM ZONE"), (232, 266, "DEEP WATER · OOB")]
    for s0, s1, t in zones:
        out.append(L(s0, 63.4, s0, 68.4, "s-ink2", stroke_width=W["h"]))
        out.append(T((s0 + s1) / 2, 67, t, 1.8, "f-ink t-draw", weight=700, ls=0.08))
    out.append(L(266, 63.4, 266, 68.4, "s-ink2", stroke_width=W["h"]))
    out.append(L(-4, 63.4, 266, 63.4, "s-ink2", stroke_width=W["h"]))
    for s, t in ((-4, "A"), (266, "A′")):
        out.append(C(s, -1.5, 2.6, "f-sheet s-accent", stroke_width=W["m"]))
        out.append(T(s, -1.4, t, 2.2, "f-accent t-draw", weight=700, base="central"))
    return svg_wrap(out, "-8 -14 292 85", "Section A–A′ through the main axis, looking east", inline,
                    cls="sec-svg", px_per_unit=4.5)


# -------------------------------------------------------------- elevation ---
def elevation_svg(inline=True):
    def H(z):
        return 24 - z
    W = dict(h=0.1, t=0.16, m=0.26, k=0.42)
    out = []
    defs = ('<defs><pattern id="e-brick" width="1.2" height="0.6" patternUnits="userSpaceOnUse">'
            '<path d="M0 0H1.2M0 0V0.3M0.6 0.3V0.6M0 0.3H1.2" class="nf s-ink3" stroke-width="0.04"/>'
            '</pattern></defs>')
    out.append(defs)
    # backdrop town
    for x0, x1, top in [(46, 62, 15), (63, 80, 19), (81, 96, 13), (97, 112, 17), (113, 126, 21),
                        (127, 142, 14), (143, 160, 18), (161, 176, 22), (177, 194, 16), (195, 210, 20),
                        (211, 226, 14), (227, 244, 18)]:
        out.append(R(x0, H(top), x1 - x0, H(6) - H(top), "f-oob s-ink3", stroke_width=W["h"]))
    for x in (74, 90, 216):
        out.append(L(x, H(6), x, H(8), "s-treeline", stroke_width=W["m"]))
        out.append(C(x, H(9.4), 2.4, "f-tree s-treeline", stroke_width=W["h"], opacity=0.8))
    # retaining wall face + railing + bunting
    out.append(R(56, H(6), 184, 6, "f-brick"))
    out.append(R(56, H(6), 184, 6, fill="url(#e-brick)"))
    out.append(L(56, H(6), 240, H(6), "s-ink", stroke_width=W["t"]))
    out.append(L(56, H(7.1), 240, H(7.1), "s-ink2", stroke_width=W["t"]))
    out += [L(x, H(6), x, H(7.1), "s-ink2", stroke_width=W["h"]) for x in range(56, 241, 2)]
    for i, x in enumerate(range(56, 238, 2)):
        out.append(PG([(x + 0.1, H(7.05)), (x + 1.9, H(7.05)), (x + 1, H(6.4))], f"f-chalk{i % 4 + 1}"))
    for x, z, c in [(110, 8.6, 1), (111.6, 9.4, 3), (113, 8.4, 2), (129, 8.8, 4), (130.6, 9.6, 1),
                    (127.6, 9.2, 2)]:
        out.append(L(x, H(z - 0.6), x + 0.2, H(7.1), "s-ink3", stroke_width=0.06))
        out.append(E(x, H(z), 0.6, 0.75, f"f-chalk{c}"))
    # park hill + garden stair
    out.append(PG([(46, H(0)), (57, H(0)), (57, H(3)), (53, H(5.2)), (46, H(6.6))], "f-grass s-treeline",
                  stroke_width=W["t"]))
    out.append(L(51, H(5.8), 51, H(8.5), "s-treeline", stroke_width=W["m"]))
    out.append(C(51, H(10.5), 3.2, "f-pine s-treeline", stroke_width=W["t"]))
    out += [L(57, H(z), 63, H(z), "s-ink3", stroke_width=W["h"]) for z in [i * 0.6 for i in range(11)]]
    out.append(R(57, H(6), 6, 6, "nf s-ink2", stroke_width=W["t"]))
    # café
    out.append(R(64, H(6), 32, 6, "f-bldg2 s-ink", stroke_width=W["k"]))
    out.append(R(65.5, H(4.4), 29, 4.4, "f-water s-ink2", stroke_width=W["t"], opacity=0.85))
    out += [L(x, H(4.4), x, H(0), "s-ink2", stroke_width=W["h"]) for x in [65.5 + 2.9 * i for i in range(1, 10)]]
    out.append(R(64.4, H(5.0), 31.2, 0.6, "f-chalk3 s-ink", stroke_width=W["h"]))
    out.append(R(64, H(7.1), 32, 1.1, "f-water s-ink2", stroke_width=W["h"], opacity=0.55))
    for x in (69, 77, 85, 92):
        out.append(L(x, H(6), x, H(8.4), "s-ink", stroke_width=W["h"]))
        out.append(PG([(x - 2.1, H(8.0)), (x, H(8.8)), (x + 2.1, H(8.0))], "f-umbrella s-ink", stroke_width=W["h"]))
    for x in (69, 76.5, 84, 91.5):
        out.append(L(x, H(0), x, H(2.4), "s-ink", stroke_width=W["h"]))
        out.append(PG([(x - 2.2, H(2.2)), (x, H(2.9)), (x + 2.2, H(2.2))], "f-umbrella s-ink", stroke_width=W["h"]))
    # photo booth
    out.append(R(96, H(4.5), 12, 4.5, "f-bldg2 s-ink", stroke_width=W["k"]))
    out.append(R(96.4, H(4.2), 11.2, 0.9, "f-chalk1 s-ink", stroke_width=W["h"]))
    out.append(R(100, H(3.0), 4, 3.0, "f-water s-ink2", stroke_width=W["t"]))
    # grand steps + escalators
    out += [L(112, H(z), 128, H(z), "s-ink3", stroke_width=W["h"]) for z in [i * 0.6 for i in range(11)]]
    out.append(L(112, H(3), 128, H(3), "s-ink", stroke_width=W["t"]))
    for ex, word in ((108, "DN"), (128, "UP")):
        out.append(R(ex, H(7), 4, 7, "f-water s-ink", stroke_width=W["t"], opacity=0.6))
        out.append(R(ex + 0.4, H(7), 3.2, 7, "nf s-ink2", stroke_width=W["h"]))
        out.append(T(ex + 2, H(0.6), word, 1.1, "f-ink t-draw", weight=700))
    # mart
    out.append(R(132, H(4.5), 16, 4.5, "f-bldg2 s-ink", stroke_width=W["k"]))
    out.append(R(132.3, H(4.2), 15.4, 0.8, "f-chalk4 s-ink", stroke_width=W["h"]))
    out.append(R(133.5, H(3.2), 13, 3.2, "f-water s-ink2", stroke_width=W["t"], opacity=0.85))
    for tx in (135, 139.5, 144):
        out.append(R(tx - 0.6, H(0.75), 1.2, 0.08, "f-ink"))
        out.append(L(tx, H(0.72), tx, H(0), "s-ink", stroke_width=W["h"]))
    # arcade + billboard
    out.append(R(148, H(11.5), 40, 11.5, "f-bldg2 s-ink", stroke_width=W["k"]))
    out.append(R(150, H(5.0), 36, 5.0, "f-water s-ink2", stroke_width=W["t"], opacity=0.85))
    out += [L(x, H(5.0), x, H(0), "s-ink2", stroke_width=W["h"]) for x in range(153, 186, 3)]
    out.append(R(160, H(4.4), 16, 0.6, "f-ink2"))
    out.append(R(148, H(7.6), 40, 2.2, "f-cut"))
    out.append(T(168, H(5.95), "A R C A D E", 1.9, "f-chalk1 t-draw", weight=700, base="central"))
    out.append(R(150, H(10.6), 36, 2.4, "f-water s-ink2", stroke_width=W["t"], opacity=0.85))
    out += [L(x, H(10.6), x, H(8.2), "s-ink2", stroke_width=W["h"]) for x in range(154, 186, 4)]
    out += [L(x, H(11.5), x, H(12.4), "s-ink", stroke_width=W["m"]) for x in (160, 168, 176)]
    out.append(R(156, H(18), 24, 6.5, "f-cut s-ink", stroke_width=W["m"]))
    out.append(R(156.5, H(17.5), 23, 5.5, "f-led"))
    out.append(T(168, H(14.8), "LED 24 × 6.5 m", 1.3, "f-mark t-draw", weight=600, base="central"))
    # skate shop
    out.append(R(188, H(4.5), 16, 4.5, "f-bldg2 s-ink", stroke_width=W["k"]))
    out.append(R(191, H(3.4), 10, 3.4, "f-bldg s-ink2", stroke_width=W["t"]))
    out += [L(191, H(z), 201, H(z), "s-ink3", stroke_width=W["h"]) for z in (0.6, 1.2, 1.8, 2.4, 3.0)]
    out.append(R(194.5, H(11), 3, 6.5, "f-chalk2 s-ink", stroke_width=W["t"], rx=1.5))
    out += [C(196, H(z), 0.35, "f-ink") for z in (5.6, 9.9)]
    # east stair, vending, east wall
    out += [L(206, H(z), 218, H(z), "s-ink3", stroke_width=W["h"]) for z in [i * 0.6 for i in range(11)]]
    out.append(L(206, H(3), 218, H(3), "s-ink", stroke_width=W["t"]))
    for i in range(7):
        out.append(R(220 + i * 1.5, H(2.0), 1.2, 2.0, f"f-chalk{i % 4 + 1} s-ink", stroke_width=W["h"]))
    out.append(L(232, H(0), 232, H(3), "s-treeline", stroke_width=W["m"]))
    out.append(C(232, H(5), 2.8, "f-tree s-treeline", stroke_width=W["t"]))
    out.append(R(238, H(7.1), 2, 7.1, "f-oob s-ink", stroke_width=W["t"]))
    # lamps, foreground trees (outline only), figures
    for x in range(72, 237, 16):
        out.append(L(x, H(0), x, H(5.2), "s-ink", stroke_width=W["t"]))
        out.append(C(x, H(5.3), 0.35, "f-sheet s-ink", stroke_width=W["h"]))

    def fig(x):
        return G([C(x, H(1.36), 0.2, "f-ink2"), R(x - 0.2, H(1.14), 0.4, 0.6, "f-ink2", rx=0.15),
                  L(x - 0.1, H(0.56), x - 0.12, H(0), "s-ink2", stroke_width=0.16),
                  L(x + 0.1, H(0.56), x + 0.12, H(0), "s-ink2", stroke_width=0.16)])
    out += [fig(x) for x in (80, 81.2, 120, 156, 157, 196, 213)]
    # ground
    out.append(L(46, H(0), 242, H(0), "s-ink", stroke_width=W["k"] * 1.4))
    # levels
    for z, t, dy in ((18, "+18.00", 0), (11.5, "+11.50", 0), (6, "+6.00", -0.4), (4.5, "+4.50", 0.5),
                     (0, "±0.00", 0)):
        out.append(L(240.5, H(z), 243, H(z), "s-ink", stroke_width=W["t"]))
        out.append(T(243.6, H(z) + 0.45 + dy, t, 1.25, "f-ink t-mono", anchor="start"))
    # names + grid bubbles
    for x, t in [(51.5, "PARK"), (80, "CAFÉ"), (102, "PHOTO"), (120, "GRAND STEPS + ESCALATORS"),
                 (140, "24 MART"), (168, "ARCADE"), (196, "SKATE SHOP"), (212, "EAST STAIR"),
                 (229, "VENDING")]:
        out.append(T(x, H(-1.9), t, 1.35, "f-ink t-draw", weight=700, ls=0.06))
    for i, x in enumerate(range(60, 241, 20)):
        out.append(L(x, H(-2.6), x, H(-3.0), "s-ink3", stroke_width=W["h"]))
        out.append(C(x, H(-4.4), 1.4, "f-sheet s-ink2", stroke_width=W["t"]))
        out.append(T(x, H(-4.35), chr(68 + i), 1.3, "f-ink2 t-draw", weight=700, base="central"))
    return svg_wrap(out, "45 -1 211 31", "Elevation E1, shop row seen from Shop Lane, looking north",
                    inline, cls="elev-svg", px_per_unit=7)


# -------------------------------------------------------------- interiors ---
def interiors_svg(inline=True):
    W = dict(h=0.05, t=0.08, m=0.14, k=0.3)
    out = ['<defs><pattern id="i-hatch" width="0.7" height="0.7" patternUnits="userSpaceOnUse" '
           'patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="0.7" class="s-ink3" '
           'stroke-width="0.06"/></pattern></defs>']

    def lbl(x, y, t, size=0.85, **kw):
        return T(x, y, t, size, "f-ink t-draw", weight=600, halo=0.18, **kw)

    def ustair(x, y, w, h):
        o = [R(x, y, w, h, "f-sheet s-ink", stroke_width=W["t"]), L(x + w / 2, y, x + w / 2, y + h - 1.4,
                                                                    "s-ink", stroke_width=W["t"])]
        o += [L(x, yy, x + w / 2, yy, "s-ink3", stroke_width=W["h"]) for yy in [y + 0.6 * i for i in range(1, 11)]]
        o += [L(x + w / 2, yy, x + w, yy, "s-ink3", stroke_width=W["h"]) for yy in [y + 0.6 * i for i in range(1, 11)]]
        return o

    def stools(x0, x1, y, step=1.2):
        n = int((x1 - x0) / step) + 1
        return [C(x0 + i * step, y, 0.28, "f-bldg2 s-ink", stroke_width=W["h"]) for i in range(n)]

    # ---- arcade (origin 0,0) ----
    out.append(R(-1, -1.4, 42, 1.4, "f-rock"))
    out.append(R(-1, -1.4, 42, 1.4, fill="url(#i-hatch)"))
    out.append(R(0, 0, 40, 24, "f-pave"))
    out += ustair(1, 1, 6, 8.4)
    out.append(R(7.4, 1, 3, 3, "f-sheet s-ink", stroke_width=W["t"]))
    out += [L(7.4, 1, 10.4, 4, "s-ink", stroke_width=W["h"]), L(10.4, 1, 7.4, 4, "s-ink", stroke_width=W["h"])]
    out.append(lbl(5.7, 11.0, "STAIR + LIFT → L2"))
    for i in range(4):
        x = 12 + i * 3.1
        out.append(R(x, 1.2, 2.8, 2.6, "f-bldg s-ink", stroke_width=W["t"]))
        out.append(L(x + 1.4, 1.2, x + 1.4, 3.8, "s-ink", stroke_width=W["h"]))
    out.append(lbl(17.8, 5.2, "RACING × 8"))
    for x in (26, 30.6):
        out.append(R(x, 1.2, 4, 4, "f-chalk3 s-ink", stroke_width=W["t"]))
        out += [R(x + 0.4 + (k % 3) * 1.1, 1.6 + (k // 3) * 1.1, 1.0, 1.0, "nf s-ink", stroke_width=W["h"])
                for k in range(9)]
    out.append(lbl(30.3, 6.4, "DANCE × 2 (4 players)"))
    for i in range(4):
        out.append(R(35.6, 1.2 + i * 2.6, 3.8, 2.3, "f-chalk2 s-ink", stroke_width=W["t"]))
        out.append(C(38.6, 2.35 + i * 2.6, 0.45, "nf s-ink", stroke_width=W["t"]))
    out.append(lbl(37.4, 12.4, "HOOPS × 4"))
    for i in range(7):
        out.append(R(0.5, 11.4 + i * 1.6, 1.4, 1.4, "f-chalk1 s-ink", stroke_width=W["t"]))
    for i in range(5):
        for j in range(2):
            out.append(R(8 + j * 1.45, 12 + i * 1.5, 1.4, 1.4, "f-chalk1 s-ink", stroke_width=W["t"]))
    out.append(lbl(9.4, 21.2, "CLAW × 17"))
    for x in (15, 21):
        out.append(R(x, 10.4, 2.6, 1.4, "f-sheet s-ink", stroke_width=W["t"], rx=0.3))
        out.append(L(x + 1.3, 10.4, x + 1.3, 11.8, "s-ink3", stroke_width=W["h"]))
    out.append(lbl(19.6, 13.4, "AIR HOCKEY × 2"))
    for x in (30.6, 34.8):
        out.append(R(x, 15, 3.6, 3, "f-blossom s-ink", stroke_width=W["t"]))
    out.append(lbl(34.6, 19.4, "PHOTO STICKERS × 2"))
    out.append(R(24.8, 21.4, 7, 1.1, "f-wood s-ink", stroke_width=W["t"]))
    out.append(lbl(28.3, 21.0, "PRIZES + COINS"))
    out.append(R(2, 22.6, 9, 0.8, "f-bldg s-ink", stroke_width=W["t"]))
    out.append(lbl(6.5, 22.1, "WINDOW BENCH"))
    out += [L(13, 9.6, 13, 7.2, "s-accent", stroke_width=W["t"]), L(12.6, 7.2, 13.4, 7.2, "s-accent", stroke_width=W["t"]),
            L(12.6, 9.6, 13.4, 9.6, "s-accent", stroke_width=W["t"]),
            T(13.5, 8.7, "2.4 min", 0.75, "f-accent t-mono", anchor="start")]
    out.append(P("M0,24 V0 H40 V24 H24 M16,24 H0", "nf s-ink", stroke_width=W["k"]))
    out.append(L(16, 24, 24, 24, "s-ink2", stroke_width=W["t"], stroke_dasharray="0.6 0.4"))
    out.append(R(12, 24, 16, 2.2, "nf s-ink2", stroke_width=W["t"], stroke_dasharray="0.5 0.4"))
    out.append(lbl(20, 25.5, "ENTRANCE + CANOPY"))
    out.append(T(0, -3.2, "ARCADE · GF ±0.00 · 40 × 24 m · clear height 5.4 m", 1.3, "f-ink t-draw", anchor="start",
                 weight=700))
    out.append(T(0, 28.6, "L2 +6.00: coin karaoke × 6, VR × 2, lounge · back door opens onto Upper Street",
                 0.95, "f-ink2 t-draw", anchor="start", weight=600))

    # ---- café (origin 48,0) ----
    ox = 48
    out.append(R(ox - 1, -1.4, 34, 1.4, "f-rock"))
    out.append(R(ox - 1, -1.4, 34, 1.4, fill="url(#i-hatch)"))
    out.append(R(ox, 0, 32, 18, "f-pave"))
    out.append(R(ox, 18, 32, 8, "f-wood", opacity=0.75))
    out.append(R(ox, 18, 32, 8, "nf s-ink2", stroke_width=W["t"], stroke_dasharray="0.6 0.4"))
    out.append(R(ox + 3, 0.3, 13, 0.8, "f-bldg s-ink", stroke_width=W["t"]))
    out.append(R(ox + 3, 2.2, 13, 1.2, "f-wood s-ink", stroke_width=W["t"]))
    out.append(R(ox + 16.6, 2.2, 4, 1.2, "f-water s-ink", stroke_width=W["t"]))
    out.append(lbl(ox + 11.8, 4.7, "COUNTER + PASTRY CASE"))
    out += ustair(ox + 24, 1, 7, 8.4)
    out.append(lbl(ox + 27.5, 10.8, "STAIR → ROOF +6.00"))
    out.append(R(ox + 25, 12, 6, 4, "f-bldg2 s-ink", stroke_width=W["t"]))
    out.append(lbl(ox + 28, 14.3, "WC"))
    out.append(R(ox + 0.4, 5, 1.6, 9.6, "f-chalk3 s-ink", stroke_width=W["t"], rx=0.4))
    for ty in (6.5, 9.8, 13.1):
        out.append(C(ox + 3.2, ty, 0.65, "f-sheet s-ink", stroke_width=W["t"]))
    out.append(T(ox + 1.5, 9.8, "SOFA NOOK", 0.75, "f-ink t-draw", weight=600, rot=-90, base="central"))
    out.append(R(ox + 8, 7, 12, 1.4, "f-wood s-ink", stroke_width=W["t"]))
    out += stools(ox + 8.6, ox + 19.4, 6.4) + stools(ox + 8.6, ox + 19.4, 9.0)
    out.append(lbl(ox + 14, 10.8, "COMMUNAL TABLE"))
    for tx in (ox + 8, ox + 12.5, ox + 17, ox + 21.5):
        out.append(C(tx, 13.3, 0.55, "f-sheet s-ink", stroke_width=W["t"]))
        out += [C(tx - 1, 13.3, 0.3, "f-bldg2 s-ink", stroke_width=W["h"]),
                C(tx + 1, 13.3, 0.3, "f-bldg2 s-ink", stroke_width=W["h"])]
    out.append(R(ox + 2, 16.7, 21, 0.6, "f-wood s-ink", stroke_width=W["t"]))
    out += stools(ox + 2.6, ox + 22.4, 16.0)
    out.append(lbl(ox + 12.5, 15.4, "WINDOW COUNTER"))
    for i, ux in enumerate((5, 11, 17, 23, 29)):
        out.append(C(ox + ux, 22, 1.6, "f-umbrella s-ink", stroke_width=W["t"]))
        out.append(C(ox + ux, 22, 0.15, "f-ink"))
    out.append(lbl(ox + 16, 25.4, "TERRACE · 5 UMBRELLA TABLES"))
    out.append(P(f"M{ox},18 V0 H{ox + 32} V18", "nf s-ink", stroke_width=W["k"]))
    out.append(L(ox, 18, ox + 32, 18, "s-ink2", stroke_width=W["t"], stroke_dasharray="1.2 0.3"))
    out.append(T(ox, -3.2, "CAFÉ · GF ±0.00 · 32 × 18 m + terrace 8 m", 1.3, "f-ink t-draw", anchor="start",
                 weight=700))
    out.append(T(ox, 28.6, "Roof +6.00: 8 tables, sunset bar, string lights · level with Upper Street",
                 0.95, "f-ink2 t-draw", anchor="start", weight=600))
    out += [T(cx, -0.45, "RETAINING WALL (+6.00 STREET BEHIND)", 0.7, "f-ink t-draw", weight=700, halo=0.15, base="central") for cx in (20, 64)]
    # scale bar
    for i in range(5):
        out.append(R(ox + 22 + 2 * i, 31, 2, 0.5, ("f-ink" if i % 2 == 0 else "f-sheet") + " s-ink",
                     stroke_width=W["h"]))
    for i in (0, 5, 10):
        out.append(T(ox + 22 + i, 32.9, str(i), 0.8, "f-ink t-mono"))
    out.append(T(ox + 33, 31.6, "m", 0.8, "f-ink t-mono", anchor="start"))
    return svg_wrap(out, "-5 -6 92 40", "Arcade and café ground floor plans", inline, cls="int-svg",
                    px_per_unit=12)


# ------------------------------------------------------------------- page ---
KEY = [
    ("Upper Street", "+6.00", [(1, "Metro exit, main spawn S1"), (2, "Overlook rail with telescopes"),
                               (42, "Coastal road, ambient traffic (out of bounds)")]),
    ("Shop Row + Lane", "±0.00", [(3, "Grand Steps + twin escalators"), (4, "Café, roof terrace level with the street"),
                                  (5, "Photo booth studio"), (6, "24 Mart + outdoor tables"),
                                  (7, "Arcade, 2 floors, LED billboard (L2)"), (8, "Skate shop + board rental"),
                                  (9, "East Stair"), (10, "Vending corner + bike rack"),
                                  (11, "Shop Lane with string lights")]),
    ("Central Plaza", "±0.00", [(12, "Emote Square, chalk-art dance floor"), (13, "Pop-up stage"),
                                (14, "Floor fountain + warp point S2"), (15, "Food truck + ice-cream van"),
                                (16, "Umbrella tables")]),
    ("Pine Hill Park", "+7.50 → ±0.00", [(17, "Old Pine on its knoll (L4)"), (18, "Pavilion"),
                                          (19, "Garden Stair + winding hill path"), (20, "Picnic lawn"),
                                          (21, "Lily pond + stepping stones"), (40, "Rock headland, west edge")]),
    ("East Deck", "±0.00", [(22, "Skate-deck sculpture (L3)"), (23, "Ledges, 5-stair + rail, manual pads"),
                            (24, "Quarter pipe"), (25, "Mini bowl, 1.8 m deep"),
                            (26, "Skate ramp + 12-stair down to the promenade")]),
    ("Waterfront", "−1.80 → −3.00", [(27, "Sunset Steps, 4 seat tiers"), (28, "Seaside Promenade (boardwalk)"),
                                     (29, "Kiosks: bikes, smoothies, info"), (30, "Bonfire circle"),
                                     (31, "Swings + hammocks"), (32, "Umbrellas + loungers"),
                                     (33, "Beach volleyball"), (34, "Surf shack, float rental"),
                                     (35, "Lifeguard tower"), (36, "Swim float"), (37, "Pier + fishing T-head"),
                                     (38, "Lighthouse (L1)"), (39, "Buoy line"), (41, "Breakwater, east edge")]),
]

LEGEND_FILLS = [("pave", "Paving"), ("brick", "Plaza brick"), ("grass", "Lawn + park"), ("sand", "Sand"),
                ("wood", "Boardwalk + decks"), ("conc", "Skate concrete"), ("water", "Swim zone"),
                ("deep", "Deep water"), ("bldg", "Roof (building)"), ("rock", "Rock + out of bounds")]


def legend_html():
    rows = []
    for tok, name in LEGEND_FILLS:
        rows.append(f'<li><svg viewBox="0 0 22 14" aria-hidden="true"><rect x="0.5" y="0.5" width="21" height="13" '
                    f'class="f-{tok} s-ink" stroke-width="0.8"/></svg>{name}</li>')
    lines = [
        ('<line x1="1" y1="7" x2="21" y2="7" class="s-bound" stroke-width="1.6" stroke-dasharray="4 2"/>', "Hard boundary"),
        ('<line x1="1" y1="7" x2="21" y2="7" class="s-bound" stroke-width="1.4" stroke-dasharray="1 2"/>', "Soft boundary"),
        ('<line x1="1" y1="7" x2="21" y2="7" class="s-treeline" stroke-width="0.8" stroke-dasharray="2.5 1.5"/>', "Contour, 1 m"),
        ('<line x1="1" y1="7" x2="21" y2="7" class="s-accent" stroke-width="1" stroke-dasharray="6 2 1.5 2"/>', "Section cut A–A′"),
        ('<circle cx="11" cy="6" r="5" class="f-spawn"/><path d="M8 10 L14 10 L11 14Z" class="f-spawn"/>', "Spawn, facing"),
        ('<circle cx="11" cy="7" r="5.5" class="f-accent"/>', "Callout, see key"),
    ]
    for svg, name in lines:
        rows.append(f'<li><svg viewBox="0 0 22 14" aria-hidden="true">{svg}</svg>{name}</li>')
    return "<ul>" + "".join(rows) + "</ul>"


def key_html():
    groups = []
    for name, level, items in KEY:
        lis = "".join(f"<li><b>{n}</b><span>{html.escape(t)}</span></li>" for n, t in items)
        groups.append(f'<div class="key-group"><h4>{html.escape(name)} <span>{level}</span></h4><ol>{lis}</ol></div>')
    return "".join(groups)


ZONES = [
    ("Z1", "Upper Street", "+6.00", "178 × 20", "3,560", "Arrival", "Spawn S1 at the metro exit, overlook rail, bus stop. Café roof and arcade L2 open onto it."),
    ("Z2", "Shop Row", "±0.00 / +6.00", "5 buildings", "2,240", "Mixed", "Café, photo booth, 24 Mart, arcade, skate shop. Café and arcade each link both levels inside."),
    ("Z3", "Shop Lane + frontage", "±0.00", "174 × 20", "≈ 3,450", "Social", "East–west spine under string lights; café terrace and mart tables spill onto it."),
    ("Z4", "Central Plaza", "±0.00", "88 × 58", "5,104", "Social", "Emote Square, pop-up stage, floor fountain (S2), food truck, umbrella tables."),
    ("Z5", "Pine Hill Park", "+7.50 → ±0.00", "74 × 122", "≈ 8,800", "Chill", "Old Pine knoll, pavilion, winding hill path, picnic lawn, lily pond."),
    ("Z6", "East Deck", "±0.00 / +0.75", "66 × 66", "4,356", "Active", "Ledges, 5-stair and rail, manual pads, quarter pipe, bowl, 12-stair, ramp."),
    ("Z7", "Sunset Steps", "±0.00 → −1.80", "88 × 8", "704", "Chill", "Four 0.45 m seat tiers facing the sea; 500+ sit spots."),
    ("Z8", "Seaside Promenade", "−1.80", "226 × 14", "3,164", "Leisure", "Boardwalk, kiosks, benches every 16 m, skate cruise line, recovery spawn S3."),
    ("Z9", "Beach", "−2.10 → −3.00", "≈ 220 × 44", "≈ 9,700", "Leisure", "Bonfire, swings, hammocks, umbrellas, volleyball, surf shack, lifeguard tower."),
    ("Z10", "Pier", "−1.80", "8 × 72 + T-head", "1,024", "Chill", "Fishing T-head, lighthouse, telescope; jump-off into the swim zone."),
    ("Z11", "Swim Zone", "WL −3.00", "≈ 160 × 22", "≈ 3,500", "Leisure", "Wade and swim to the buoy line; swim float in the middle."),
]

LINKS = [
    ("V1", "Grand Steps", "+6.00 ↔ ±0.00", "16 m wide · 2 flights × 20 risers (0.15 / 0.30) · landing +3.00"),
    ("V1e", "Twin escalators", "+6.00 ↔ ±0.00", "Either side of V1 · 30° · west runs down, east runs up"),
    ("V2", "Garden Stair", "+6.00 ↔ ±0.00", "6 m wide beside the café · 2 × 20 risers"),
    ("V2b", "Hill path", "+6.00 ↔ ±0.00", "3 m wide · ≈ 105 m · average 1:17 · passes the Old Pine and pavilion"),
    ("V3", "East Stair", "+6.00 ↔ ±0.00", "12 m wide · 2 × 20 risers · lands at the skate shop"),
    ("V4", "Café stair", "±0.00 ↔ +6.00", "Interior U-stair to the roof terrace"),
    ("V5", "Arcade stair + lift", "±0.00 ↔ +6.00", "Interior U-stair and lift; L2 back door opens onto the street"),
    ("V6", "Sunset Steps", "±0.00 ↔ −1.80", "4 seat tiers 0.45 × 2.00 · three aisle stairs"),
    ("V7", "Lawn bank", "±0.00 ↔ −1.80", "Grass slope ≈ 1:5.5, walkable anywhere along the park edge"),
    ("V8", "12-stair + rail", "±0.00 ↔ −1.80", "Skate gap spot at the East Deck edge"),
    ("V9", "Skate ramp", "±0.00 ↔ −1.80", "24 m long · 1:13 · skate and walk"),
]

METRICS = [
    ("Character", "Height 1.50 m · capsule radius 0.35 m · eye height 1.35 m"),
    ("Speeds", "Walk 2.0 m/s · run 5.5 m/s · skate 9.0 m/s cruise"),
    ("Step + jump", "Step-up ≤ 0.45 m · jump apex 1.2 m · walkable slope ≤ 30°"),
    ("Stairs", "Riser 0.15 · tread 0.30 · landing every 20 risers"),
    ("Paths", "Primary ≥ 8 m · secondary 3–4 m · never under 2.4 m"),
    ("Interiors", "Doors ≥ 2.4 × 3.0 m · ceilings ≥ 4.0 m · aisles ≥ 2.4 m for the third-person camera"),
    ("Seating", "Seat height 0.45 m · seat tier 0.45 × 2.00 m"),
    ("Skate", "Ledge 0.45 · rail 0.60 · quarter pipe 1.8 m · bowl 1.8 m deep"),
    ("Water", "Wade ≤ 1.0 m · swim > 1.0 m · swim zone ≤ 2.5 m deep"),
    ("Guardrails", "1.10 m on drops over 0.6 m, except seat tiers and skate edges"),
    ("Lighting", "Lamp posts every 16 m on primary paths"),
    ("Engine", "1 m = 100 uu (Unreal) · snap 1 m · sheet grid 20 m"),
]

EDGES = [
    ("North", "Coastal Road", "Bollards + chain on the street edge (hard). Traffic and the hillside town are backdrop only."),
    ("West", "Rock headland", "Cliff at least 4 m above walkable ground (hard). It runs into the sea to hide the corner."),
    ("East", "Graffiti wall + breakwater", "Wall on grid x 238 (hard). Tetrapods and marina boats beyond."),
    ("South", "Sea", "Buoy line at 232 is visual. Soft push-back from 240, hard collision at 258. Distant islands and a bridge in the skybox."),
    ("Recovery", "Spawn S3", "A swimmer who stalls past the soft edge fades out and respawns on the promenade at S3."),
]

PAGE_CSS = r"""
/* Layout: a drawing set. Title block, design intent, one full-width sheet per drawing, then ruled schedules. */
:root{/*LIGHT*/;--f-draw:/*FDRAW*/;--f-body:/*FBODY*/;--f-mono:/*FMONO*/}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){/*DARK*/;color-scheme:dark}}
:root[data-theme="dark"]{/*DARK*/;color-scheme:dark}
body{background:var(--paper);color:var(--ink);font-family:var(--f-body);font-size:15px;line-height:1.55}
.wrap{max-width:1280px;margin:0 auto;padding-inline:clamp(16px,3vw,32px);padding-block:28px 72px;display:grid;gap:28px}
h1,h2,h3,h4{font-family:var(--f-draw);text-wrap:balance;margin:0;line-height:1.05}
p{margin:0}
.eyebrow{font-family:var(--f-draw);font-weight:600;letter-spacing:.14em;text-transform:uppercase;font-size:13px;color:var(--ink2)}
.titleblock{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,1fr);border:1.5px solid var(--ink);background:var(--sheet)}
.tb-main{padding:22px 24px 24px;display:grid;gap:12px;align-content:start;border-right:1.5px solid var(--ink)}
.tb-main h1{font-size:clamp(46px,7.4vw,92px);font-weight:700;letter-spacing:.005em;text-transform:uppercase}
.lede{max-width:58ch;color:var(--ink2);font-size:16px}
.tb-cells{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));margin:0}
.tb-cells div{padding:9px 14px 10px;border-bottom:1px solid var(--rule)}
.tb-cells div:nth-child(odd){border-right:1px solid var(--rule)}
.tb-cells div:nth-last-child(-n+2){border-bottom:0}
.tb-cells dt{font-family:var(--f-draw);font-weight:600;font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink2)}
.tb-cells dd{margin:2px 0 0;font-family:var(--f-mono);font-size:13.5px;font-variant-numeric:tabular-nums}
.intent{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));border-top:1.5px solid var(--ink);border-bottom:1px solid var(--rule)}
.intent div{padding:16px 20px 18px 0;display:grid;gap:6px;align-content:start}
.intent div+div{padding-left:20px;border-left:1px solid var(--rule)}
.intent h3{font-size:21px;font-weight:700;text-transform:uppercase;letter-spacing:.02em}
.intent p{color:var(--ink2);font-size:14.5px}
.sheet{background:var(--sheet);border:1.5px solid var(--ink);min-width:0}
.sheet-head{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 14px;padding:12px 18px;border-bottom:1px solid var(--rule)}
.sheet-no{font-family:var(--f-mono);font-size:13px;padding:1px 8px;border:1.5px solid var(--ink)}
.sheet-head h2{font-size:28px;font-weight:700;text-transform:uppercase;letter-spacing:.02em}
.sheet-meta{margin-left:auto;color:var(--ink2);font-size:13px;font-family:var(--f-mono)}
.toolbar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:10px 18px;border-bottom:1px solid var(--rule)}
.toolbar .lbl{font-family:var(--f-draw);font-weight:600;font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink2);margin-right:4px}
.chip{display:inline-flex;align-items:center;gap:7px;font-family:var(--f-draw);font-weight:600;font-size:14px;letter-spacing:.04em;text-transform:uppercase;padding:4px 11px 4px 9px;border:1px solid var(--rule);border-radius:999px;cursor:pointer;user-select:none;color:var(--ink2)}
.chip:has(input:checked){border-color:var(--ink);color:var(--ink)}
.chip input{accent-color:var(--accent);margin:0;width:14px;height:14px}
.chip:focus-within{outline:2px solid var(--accent);outline-offset:2px}
.zoom{display:inline-flex;margin-left:auto;border:1px solid var(--ink);border-radius:999px;overflow:hidden}
.zoom button{font:600 13px/1 var(--f-mono);padding:6px 11px;background:var(--sheet);color:var(--ink);border:0;cursor:pointer}
.zoom button+button{border-left:1px solid var(--rule)}
.zoom button[aria-pressed="true"]{background:var(--ink);color:var(--sheet)}
.zoom button:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
.scroll svg{display:block;height:auto}
#plan-svg{width:100%;min-width:920px}
.sec-svg{width:100%;min-width:1000px}
.elev-svg{width:100%;min-width:1240px}
.int-svg{width:100%;min-width:900px}
.sheet-foot{display:grid;grid-template-columns:minmax(0,1fr) 230px;border-top:1px solid var(--rule)}
.key{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:18px 26px;padding:16px 18px 20px}
.key h4,.legend h4{font-size:15px;font-weight:700;text-transform:uppercase;letter-spacing:.06em}
.key h4 span{font-family:var(--f-mono);font-size:12px;font-weight:400;color:var(--ink2);letter-spacing:0;margin-left:4px}
.key ol,.legend ul{list-style:none;margin:8px 0 0;padding:0;display:grid;gap:4px}
.key li{display:grid;grid-template-columns:22px minmax(0,1fr);gap:8px;align-items:center;font-size:13.5px;line-height:1.35}
.key li b{display:inline-grid;place-items:center;width:20px;height:20px;border-radius:50%;background:var(--accent);color:var(--onaccent);font:700 11.5px/1 var(--f-draw)}
.legend{padding:16px 18px 20px;border-left:1px solid var(--rule)}
.legend li{display:grid;grid-template-columns:26px 1fr;gap:8px;align-items:center;font-size:13px}
.legend svg{width:26px;height:16px;display:block}
.caption{padding:12px 18px 16px;border-top:1px solid var(--rule);color:var(--ink2);font-size:14.5px}
.caption p{max-width:82ch}
.caption b{color:var(--ink);font-weight:600}
.schedules{display:grid;gap:26px;padding:6px 18px 22px}
.schedules h3{font-size:19px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;margin:14px 0 6px}
.tablewrap{overflow-x:auto}
.schedules>div,.two>div,.sheet-foot>div,.notes>section,.intent>div,.key-group{min-width:0}
table{width:100%;border-collapse:collapse;font-size:13.5px}
th{font-family:var(--f-draw);font-weight:600;text-transform:uppercase;letter-spacing:.08em;font-size:12px;color:var(--ink2);text-align:left;padding:7px 10px;border-bottom:1.5px solid var(--ink);white-space:nowrap}
td{padding:7px 10px;border-bottom:1px solid var(--rule);vertical-align:top}
td.id,td.num{font-family:var(--f-mono);font-variant-numeric:tabular-nums;white-space:nowrap;font-size:13px}
td.num{text-align:right}
th.num{text-align:right}
.mood{display:inline-flex;align-items:center;gap:6px;white-space:nowrap}
.mood::before{content:"";width:9px;height:9px;border-radius:50%;background:var(--dot,var(--ink3))}
.mood.chill{--dot:var(--zchill)}.mood.social{--dot:var(--zsocial)}.mood.active{--dot:var(--zactive)}.mood.leisure{--dot:var(--zleisure)}.mood.arrival{--dot:var(--spawn)}.mood.mixed{--dot:var(--ink3)}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:10px 28px}
.notes{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:0;border:1.5px solid var(--ink);background:var(--sheet)}
.notes section{padding:16px 20px 20px;display:grid;gap:8px;align-content:start}
.notes section+section{border-left:1px solid var(--rule)}
.notes h3{font-size:19px;font-weight:700;text-transform:uppercase;letter-spacing:.04em}
.notes ol{margin:0;padding-left:20px;display:grid;gap:8px;font-size:14.5px}
.notes p{font-size:14.5px;color:var(--ink2)}
footer{font-family:var(--f-mono);font-size:12.5px;color:var(--ink2)}
@media (max-width:860px){
  .titleblock{grid-template-columns:1fr}
  .tb-main{border-right:0;border-bottom:1.5px solid var(--ink)}
  .sheet-foot{grid-template-columns:1fr}
  .legend{border-left:0;border-top:1px solid var(--rule)}
  .legend ul{grid-template-columns:repeat(auto-fill,minmax(150px,1fr))}
  .intent div+div{padding-left:0;border-left:0;border-top:1px solid var(--rule)}
  .notes section+section{border-left:0;border-top:1px solid var(--rule)}
  .zoom{margin-left:0}
}
@media (prefers-reduced-motion: no-preference){.zoom button,.chip{transition:background-color .15s,color .15s,border-color .15s}}
"""

PAGE_JS = r"""
<script>
(function () {
  document.querySelectorAll('input[data-layer]').forEach(function (cb) {
    var g = document.getElementById(cb.dataset.layer);
    if (!g) return;
    var sync = function () { if (cb.checked) g.removeAttribute('hidden'); else g.setAttribute('hidden', 'hidden'); };
    cb.addEventListener('change', sync);
    sync();
  });
  var plan = document.getElementById('plan-svg');
  var buttons = document.querySelectorAll('[data-zoom]');
  buttons.forEach(function (b) {
    b.addEventListener('click', function () {
      plan.style.width = (parseFloat(b.dataset.zoom) * 100) + '%';
      buttons.forEach(function (x) { x.setAttribute('aria-pressed', String(x === b)); });
    });
  });
})();
</script>
"""


def page(plan, meta, section, elevation, interiors):
    tok = lambda d: ";".join(f"--{k}:{v}" for k, v in d.items())
    css = (PAGE_CSS.replace("/*LIGHT*/", tok(LIGHT)).replace("/*DARK*/", tok(DARK))
           .replace("/*FDRAW*/", FONTS["f-draw"]).replace("/*FBODY*/", FONTS["f-body"])
           .replace("/*FMONO*/", FONTS["f-mono"]))
    css += "\n" + svg_class_css()
    loop_m, loop_s = meta["loop_m"], meta["loop_m"] / 5.5
    spawn_m = 210 - 41.6
    zone_rows = "".join(
        f'<tr><td class="id">{z}</td><td>{n}</td><td class="id">{lv}</td><td class="id">{sz}</td>'
        f'<td class="num">{a}</td><td><span class="mood {m.lower()}">{m}</span></td><td>{d}</td></tr>'
        for z, n, lv, sz, a, m, d in ZONES)
    link_rows = "".join(f'<tr><td class="id">{i}</td><td>{n}</td><td class="id">{lv}</td><td>{d}</td></tr>'
                        for i, n, lv, d in LINKS)
    metric_rows = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in METRICS)
    edge_rows = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in EDGES)
    chips = [("p-labels", "Labels", True), ("p-grid", "Grid + levels", True), ("p-system", "Spawns + edges", True),
             ("p-circ", "Circulation", False), ("p-sight", "Sightlines", False), ("p-zones", "Activity zones", False)]
    chip_html = "".join(
        f'<label class="chip"><input type="checkbox" id="lyr-{lid}" data-layer="{lid}"{" checked" if on else ""}>{name}</label>'
        for lid, name, on in chips)
    return f"""<title>Bayside Park Site Plan</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>{css}</style>
<div class="wrap">
<header class="titleblock">
  <div class="tb-main">
    <p class="eyebrow">ORI · Level design · Social hub</p>
    <h1>Bayside Park</h1>
    <p class="lede">An open map for hanging out with friends. A hillside park, an arcade and a café on a shop terrace, a plaza for dancing and emotes, and a city beach right in front.</p>
  </div>
  <dl class="tb-cells">
    <div><dt>Site</dt><dd>240 × 260 m</dd></div>
    <div><dt>Playable land</dt><dd>≈ 4.2 ha</dd></div>
    <div><dt>Levels</dt><dd>+6.00 / ±0.00 / −1.80</dd></div>
    <div><dt>Datum ±0.00</dt><dd>Central Plaza</dd></div>
    <div><dt>Spawn → sea</dt><dd>{spawn_m:.0f} m · {spawn_m / 5.5:.0f} s run</dd></div>
    <div><dt>Primary loop</dt><dd>≈ {loop_m:.0f} m · {loop_s:.0f} s run</dd></div>
    <div><dt>Units</dt><dd>1 unit = 1 m</dd></div>
    <div><dt>Sheets</dt><dd>LD-01 – LD-04</dd></div>
    <div><dt>Status</dt><dd>Concept · Rev A</dd></div>
    <div><dt>Date</dt><dd>2026-10-05</dd></div>
  </dl>
</header>

<section class="intent" aria-label="Design intent">
  <div><h3>Sea on arrival</h3><p>Spawn sits on the Upper Street, 6 m above the plaza. The first view runs down the Grand Steps, across the plaza and out to the water.</p></div>
  <div><h3>Three levels, eleven links</h3><p>Street +6.00, plaza ±0.00, promenade −1.80. Stairs, escalators, a hill path, the café and arcade interiors, seat steps, a lawn bank and a skate ramp connect them.</p></div>
  <div><h3>Quiet west, loud east</h3><p>Park, pond and café sit to the west. Stage, arcade and skate deck sit to the east. Groups pick a mood by walking a few steps.</p></div>
  <div><h3>Somewhere to sit</h3><p>Benches every 16 m, 500+ spots on the Sunset Steps, café and terrace tables, swings, hammocks and bonfire logs.</p></div>
</section>

<section class="sheet" id="ld-01" aria-labelledby="ld01-h">
  <header class="sheet-head"><span class="sheet-no">LD-01</span><h2 id="ld01-h">Site plan</h2><p class="sheet-meta">North up · grid 20 m · levels in metres</p></header>
  <div class="toolbar" role="group" aria-label="Plan layers and zoom">
    <span class="lbl">Layers</span>{chip_html}
    <div class="zoom" role="group" aria-label="Zoom"><button type="button" data-zoom="1" aria-pressed="true">Fit</button><button type="button" data-zoom="1.6" aria-pressed="false">1.6×</button><button type="button" data-zoom="2.4" aria-pressed="false">2.4×</button></div>
  </div>
  <div class="scroll">{plan}</div>
  <div class="sheet-foot">
    <div class="key">{key_html()}</div>
    <div class="legend"><h4>Legend</h4>{legend_html()}</div>
  </div>
</section>

<section class="sheet" id="ld-02" aria-labelledby="ld02-h">
  <header class="sheet-head"><span class="sheet-no">LD-02</span><h2 id="ld02-h">Section A–A′</h2><p class="sheet-meta">Cut on grid x 120 · looking east · vertical ×2</p></header>
  <div class="scroll">{section}</div>
  <div class="caption"><p>The spawn eye height is <b>+7.35</b>. From there the sightline clears the plaza and the beach and lands on the waterline, so the sea is in view the moment a player loads in. Keep the 8 m view axis clear of anything taller than <b>1.6 m</b> between the Grand Steps and the water.</p></div>
</section>

<section class="sheet" id="ld-03" aria-labelledby="ld03-h">
  <header class="sheet-head"><span class="sheet-no">LD-03</span><h2 id="ld03-h">Elevation E1 · Shop Row</h2><p class="sheet-meta">From Shop Lane · looking north · true scale</p></header>
  <div class="scroll">{elevation}</div>
  <div class="caption"><p>The café and arcade are the tall pair. The café roof is level with the Upper Street, and the arcade's second floor opens onto it at the back. The single-storey shops stay under the <b>+6.00</b> rail, so the street above keeps its view of the sea.</p></div>
</section>

<section class="sheet" id="ld-04" aria-labelledby="ld04-h">
  <header class="sheet-head"><span class="sheet-no">LD-04</span><h2 id="ld04-h">Arcade + café interiors</h2><p class="sheet-meta">Ground floors · 1 unit = 1 m</p></header>
  <div class="scroll">{interiors}</div>
  <div class="caption"><p>Interiors run at about 1.3× real scale so a third-person camera fits: aisles at least <b>2.4 m</b>, ceilings at least <b>4.0 m</b>. Group activities (dance machines, hoops, the communal table) sit by the windows, so friends outside can see the fun and come in.</p></div>
</section>

<section class="sheet" id="sched" aria-labelledby="sched-h">
  <header class="sheet-head"><span class="sheet-no">SCH</span><h2 id="sched-h">Schedules</h2><p class="sheet-meta">Areas in m² · levels in m</p></header>
  <div class="schedules">
    <div><h3>Zones</h3><div class="tablewrap"><table>
      <thead><tr><th>ID</th><th>Zone</th><th>Level</th><th>Size (m)</th><th class="num">Area</th><th>Mood</th><th>What happens here</th></tr></thead>
      <tbody>{zone_rows}</tbody></table></div></div>
    <div><h3>Vertical links</h3><div class="tablewrap"><table>
      <thead><tr><th>ID</th><th>Link</th><th>Between</th><th>Spec</th></tr></thead>
      <tbody>{link_rows}</tbody></table></div></div>
    <div class="two">
      <div><h3>Build metrics (assumed)</h3><div class="tablewrap"><table>
        <thead><tr><th>Item</th><th>Value</th></tr></thead><tbody>{metric_rows}</tbody></table></div></div>
      <div><h3>Edges + boundaries</h3><div class="tablewrap"><table>
        <thead><tr><th>Side</th><th>Edge</th><th>How it holds</th></tr></thead><tbody>{edge_rows}</tbody></table></div></div>
    </div>
  </div>
</section>

<div class="notes">
  <section><h3>Light + time of day</h3>
    <p>The sea faces south, so the sun crosses over the water all day and sets behind the west headland. At golden hour the Old Pine is backlit as seen from the Sunset Steps. At night the string lights, LED billboard, bonfire and lighthouse beam carry the mood.</p></section>
  <section><h3>Open questions</h3><ol>
    <li>The 4th reference image (beach) didn't come through. This layout assumes a city beach, with a boardwalk straight onto the sand. Send it and Z8–Z11 will be adjusted.</li>
    <li>Players per instance? Sized for 40–60 players plus an ambient NPC crowd, like the bystanders in reference 2.</li>
    <li>Is skating core traversal? If not, the East Deck becomes a sports court and street-dance stage.</li>
    <li>Character metrics are assumed. Swap in the real controller values and the stairs, paths and interiors can be re-checked.</li>
  </ol></section>
</div>

<footer>Source: docs/maps/bayside-park/ · build_sheet.py regenerates this page and four standalone SVGs from one set of coordinates.</footer>
</div>
{PAGE_JS}"""


def main():
    plan_inline, meta = plan_svg(inline=True)
    html_out = page(plan_inline, meta, section_svg(True), elevation_svg(True), interiors_svg(True))
    (HERE / "index.html").write_text(html_out, encoding="utf-8")
    (HERE / "site-plan.svg").write_text(plan_svg(inline=False)[0], encoding="utf-8")
    (HERE / "section-aa.svg").write_text(section_svg(False), encoding="utf-8")
    (HERE / "elevation-e1.svg").write_text(elevation_svg(False), encoding="utf-8")
    (HERE / "interiors.svg").write_text(interiors_svg(False), encoding="utf-8")
    print(f"loop {meta['loop_m']:.0f} m, skate line {meta['skate_m']:.0f} m")


if __name__ == "__main__":
    main()
