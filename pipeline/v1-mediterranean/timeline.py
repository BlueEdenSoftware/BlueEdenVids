"""Parallel Earth #1 v2 - shot list and captions (all numbers from terrain2.npz model or cited sources)."""
FPS = 24

# (start_s, end_s, scene, shot, year_from, year_to, caption, sub_caption)
SHOTS = [
    (0.0, 4.5, "beach", "beach_hook", 0, 3, "This sea disappeared once.", "And it could happen again."),
    (4.5, 9.0, "map", "gibraltar", 0, 0, "Close Gibraltar.", "It's only 14 km wide."),
    (9.0, 13.5, "beach", "beach_far", 0, 10, "Year 10: the sea walks away.", None),
    (13.5, 18.5, "map", "sicily", 10, 190, "Year 190: walk from Tunisia to Sicily.", None),
    (18.5, 23.0, "map", "wide", 190, 443, "Year 443: the sea is 1 km down.", None),
    (23.0, 28.5, "map", "high", 443, 1100, "Year 1,100: 90% gone.", "Only salt lakes remain."),
    (28.5, 33.5, "map", "abyss", 1100, 1500, "Summers up to 15°C hotter down here.", None),
    (33.5, 37.5, "map", "high2", 1500, 1500, "Oceans everywhere rise about 10 m.", None),
    (37.5, 41.0, "map", "wide2", 1500, 1500, "Impossible?", "It happened 5.6 million years ago."),
    (41.0, 48.0, "flood", "flood", 1500, 1500, "Then the Atlantic broke back in.", "1,000× the Amazon. 10 m a day."),
    (48.0, 52.0, "beach", "beach_hook", 0, 0, None, None),
]
DUR = SHOTS[-1][1]

# Facts (for captions / pinned comment)
FACTS = {
    "gibraltar_width_km": 14,          # Strait of Gibraltar narrowest ~14 km
    "sicily_sill_m": 430,              # Wikipedia, Strait of Sicily western sill ~430 m
    "dry_90pct_years": 1100,           # literature: "scarcely more than a thousand years" (model scaled to this)
    "summer_warming_c": 15,            # Wikipedia: modelling, up to 15 C summer warming
    "global_rise_m": 10.7,             # 3.86M km3 / 361M km2 ocean area (Wikipedia quotes ~12 m)
    "flood_vs_amazon": 1000,           # Garcia-Castellanos et al. 2009
    "flood_m_per_day": 10,
    "when_ma": 5.6,
}

# ---------------- helpers shared by renderers and compositor ----------------
import math as _m
import numpy as _np
_T = _np.load("/home/claude/pe/v2/terrain2.npz")
_YRS, _LEV = _T["yrs"], _T["levels"]


def ss(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def lerp(a, b, t):
    return a + (b - a) * t


def shot_at(t):
    for k, s in enumerate(SHOTS):
        if s[0] <= t < s[1]:
            return k, s
    return len(SHOTS) - 1, SHOTS[-1]


def level_for_year(y):
    return float(_np.interp(y, _YRS, _LEV))


def year_at(t):
    k, s = shot_at(t)
    p = (t - s[0]) / (s[1] - s[0])
    return lerp(s[4], s[5], ss(p / 0.75))


FLOOD_START, FLOOD_END = 41.6, 47.4      # refill animation inside the flood shot
RETURN_START, RETURN_END = 48.0, 50.6    # sea comes back on the final beach shot


def level_at(t):
    k, s = shot_at(t)
    if s[3] == "flood":
        u = ss((t - FLOOD_START) / (FLOOD_END - FLOOD_START))
        return lerp(level_for_year(1500), -40.0, u ** 0.7)
    if k == len(SHOTS) - 1:
        u = ss((t - RETURN_START) / (RETURN_END - RETURN_START))
        return lerp(-40.0, 0.0, u)
    return level_for_year(year_at(t))


def frames_for(scene):
    out = []
    for i in range(int(DUR * FPS)):
        t = i / FPS
        k, s = shot_at(t)
        if s[2] == scene:
            out.append((i, t, k, s))
    return out
