"""Composite renders + captions + HUD into final 1080x1920 frames."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
sys.path.insert(0, "/home/claude/pe/v2")
import timeline as T

W, H = 1080, 1920
F = "/usr/share/fonts/opentype/inter/"
_fc = {}


def font(name, size):
    k = (name, size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(F + name, size)
    return _fc[k]


def wrap(d, text, fnt, maxw):
    lines = []
    for para in text.split("\n"):
        line = ""
        for w in para.split():
            test = (line + " " + w).strip()
            if d.textlength(test, font=fnt) <= maxw:
                line = test
            else:
                lines.append(line); line = w
        lines.append(line)
    return lines


def text_block(img, text, cx, y, fnt, maxw, alpha=1.0, fill=(255, 255, 255), pop=1.0, shadow=True):
    if alpha <= 0.01:
        return 0
    d = ImageDraw.Draw(img)
    lines = wrap(d, text, fnt, maxw)
    lh = int(fnt.size * 1.15)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    for i, ln in enumerate(lines):
        w = ld.textlength(ln, font=fnt)
        x = cx - w / 2; yy = y + i * lh + (1 - pop) * 30
        ld.text((x, yy), ln, font=fnt, fill=fill + (int(255 * alpha),))
        sd.text((x + 2, yy + 5), ln, font=fnt, fill=(0, 0, 0, int(210 * alpha)))
        if shadow:
            sd.text((x, yy), ln, font=fnt, fill=(0, 0, 0, int(140 * alpha)), stroke_width=6, stroke_fill=(0, 0, 0, int(140 * alpha)))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    img.alpha_composite(layer)
    return lh * len(lines)


def fmt_level(v):
    v = int(round(v))
    if v == 0:
        return "0 m"
    return ("−" if v < 0 else "+") + f"{abs(v):,} m"


def hud(img, t, k, sh):
    if k == 0:
        return
    a = T.ss((t - sh[0]) / 0.3) if k == 1 else 1.0
    lv = T.level_at(t)
    teal = (110, 225, 230)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    x, y = 70, 210
    d.text((x, y), "SEA LEVEL", font=font("Inter-Bold.otf", 30), fill=teal + (int(255 * a),))
    d.text((x - 4, y + 34), fmt_level(lv), font=font("InterDisplay-Black.otf", 104), fill=(255, 255, 255, int(255 * a)))
    if sh[3] == "flood":
        day = int(max(0, lv - T.level_for_year(1500)) / 10)
        lab, val = "FLOOD DAY", f"{day:,}"
    elif k == len(T.SHOTS) - 1:
        lab, val = None, None
    else:
        lab, val = "YEAR", f"{int(round(T.year_at(t))):,}"
    if lab:
        d.text((x, y + 160), lab, font=font("Inter-Bold.otf", 30), fill=teal + (int(255 * a),))
        d.text((x - 2, y + 194), val, font=font("InterDisplay-Bold.otf", 64), fill=(255, 255, 255, int(255 * a)))
    shd = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shd.paste((0, 0, 0, 170), mask=layer.split()[3].filter(ImageFilter.GaussianBlur(10)))
    img.alpha_composite(shd); img.alpha_composite(layer)


_TB = np.load("/home/claude/pe/v2/terrain_big.npz")
_BT, _BLAT, _BLON = _TB["topo"], _TB["lat"], _TB["lon"]
_KX = 111.32 * np.cos(np.radians(38.0)); _KY = 111.32; _EX = 25.0
MAPCAMS = {
    "gibraltar": dict(lon=-4.9, lat=36.0, heading=72, pitch=45, dist=600),
    "sicily":    dict(lon=11.9, lat=36.9, heading=15, pitch=45, dist=760),
    "wide":      dict(lon=10.0, lat=38.0, heading=80, pitch=30, dist=2100),
    "high":      dict(lon=17.0, lat=37.5, heading=85, pitch=55, dist=3300),
    "high2":     dict(lon=15.0, lat=37.0, heading=100, pitch=65, dist=3600),
    "wide2":     dict(lon=12.0, lat=37.5, heading=60, pitch=28, dist=2500),
}
LABELS = {
    "gibraltar": [("SPAIN", -4.3, 37.1), ("MOROCCO", -5.2, 35.1), ("ATLANTIC", -6.6, 35.75), ("MEDITERRANEAN", -3.4, 36.25)],
    "sicily": [("TUNISIA", 10.4, 36.6), ("SICILY", 14.0, 37.5)],
    "wide": [("SPAIN", -3.5, 40.0), ("ITALY", 12.8, 42.6), ("TUNISIA", 9.5, 34.5)],
    "wide2": [("ITALY", 12.8, 42.6), ("AFRICA", 8.0, 31.5)],
    "flood": [("ATLANTIC", -6.0, 35.95), ("GIBRALTAR", -5.6, 36.35)],
}


def _xy(lon, lat):
    return (lon - _BLON[0]) * _KX, (lat - _BLAT[0]) * _KY


def _topo(lon, lat):
    return float(_BT[np.argmin(abs(_BLAT - lat)), np.argmin(abs(_BLON - lon))])


def map_cam(name, t, sh):
    if name == "flood":
        p = (t - sh[0]) / (sh[1] - sh[0])
        c = dict(lon=T.lerp(-4.5, -3.9, p), lat=36.0, heading=80, pitch=T.lerp(40, 34, p), dist=T.lerp(440, 380, p))
    else:
        c = dict(MAPCAMS[name]); p = (t - sh[0]) / (sh[1] - sh[0])
        c["dist"] *= T.lerp(1.06, 0.92, p); c["heading"] += T.lerp(-3, 3, p)
    tx, ty = _xy(c["lon"], c["lat"])
    h, pi = np.radians(c["heading"]), np.radians(c["pitch"])
    cam = np.array([tx - c["dist"] * np.cos(pi) * np.sin(h), ty - c["dist"] * np.cos(pi) * np.cos(h), c["dist"] * np.sin(pi)])
    f = np.array([tx, ty, 0.0]) - cam; f /= np.linalg.norm(f)
    r = np.cross(f, [0, 0, 1.0]); r /= np.linalg.norm(r); u = np.cross(r, f)
    return cam, f, r, u


def labels(img, t, k, sh):
    name = sh[3]
    if name not in LABELS:
        return
    cam, f, r, u = map_cam(name, t, sh)
    th = 12.0 / 26.0
    a = T.ss((t - sh[0] - 0.4) / 0.4) * (1 - T.ss((t - sh[1] + 0.3) / 0.3))
    if a <= 0.01:
        return
    lv = T.level_at(t)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    fl = font("Inter-ExtraBold.otf", 34)
    for txt, lo, la in LABELS[name]:
        x, y = _xy(lo, la)
        z = max(_topo(lo, la), lv if txt not in ("ATLANTIC",) else 0.0, 0.0 if txt in ("ATLANTIC", "MEDITERRANEAN") else -1e9) / 1000 * _EX
        v = np.array([x, y, z]) - cam
        dz = v @ f
        if dz <= 1:
            continue
        sx = W / 2 + (v @ r) / dz / th * H / 2
        sy = H / 2 - (v @ u) / dz / th * H / 2
        if not (60 < sx < W - 60 and 380 < sy < 1150):
            continue
        spaced = " ".join(txt)
        tw = d.textlength(spaced, font=fl)
        d.ellipse([sx - 7, sy - 7, sx + 7, sy + 7], fill=(255, 255, 255, int(255 * a)))
        d.text((sx - tw / 2, sy - 52), spaced, font=fl, fill=(255, 255, 255, int(255 * a)))
    shd = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shd.paste((0, 0, 0, 190), mask=layer.split()[3].filter(ImageFilter.GaussianBlur(6)))
    img.alpha_composite(shd); img.alpha_composite(layer)


def grade(im):
    im = ImageEnhance.Contrast(im).enhance(1.08)
    im = ImageEnhance.Color(im).enhance(1.15)
    return im


VIG = None
_yy = np.arange(H)[:, None]
_sa = (np.exp(-((_yy - 1290) / 210.0) ** 2) * 105).astype(np.uint8)
SCRIM = Image.new("RGBA", (W, H), (0, 0, 0, 0)); SCRIM.putalpha(Image.fromarray(np.repeat(_sa, W, axis=1)))


def vignette():
    global VIG
    if VIG is None:
        yy, xx = np.mgrid[0:H, 0:W]
        r = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2)
        a = (np.clip(r - 0.55, 0, 1) * 200).astype(np.uint8)
        top = (np.clip(1 - yy / 520, 0, 1) ** 1.6 * 120).astype(np.uint8)
        a = np.maximum(a, top)
        VIG = Image.new("RGBA", (W, H), (0, 0, 0, 0)); VIG.putalpha(Image.fromarray(a))
    return VIG


def compose(i):
    t = i / T.FPS
    k, sh = T.shot_at(t)
    src = Image.open(f"/home/claude/pe/v2/frames/{i:05d}.png").convert("RGB")
    im = grade(src.resize((W, H), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 60, 2))).convert("RGBA")
    if sh[3] == "abyss":
        a = np.asarray(im).astype(np.float32)
        a = (a - 128) * 1.25 + 118
        a[..., 0] *= 1.10; a[..., 1] *= 0.94; a[..., 2] *= 0.78
        # heat shimmer: small sinusoidal row offsets in the lower half
        yy = np.arange(H)
        shift = (np.sin(yy / 9.0 + t * 9) * 3 * np.clip((yy - 700) / 500, 0, 1)).astype(int)
        for r0 in range(700, H, 2):
            a[r0:r0 + 2] = np.roll(a[r0:r0 + 2], shift[r0], axis=1)
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    im.alpha_composite(vignette())
    im.alpha_composite(SCRIM)
    # cut flash: quick white dip on first 2 frames of each new shot (except loop end)
    p = t - sh[0]
    if k == 0:
        # hook: huge headline immediately, subline at 1.6 s
        a1 = T.ss(t / 0.15) * (1 - T.ss((t - 4.2) / 0.3))
        hh = text_block(im, sh[6], W // 2, 290, font("InterDisplay-Black.otf", 112), 960, a1, pop=T.ss(t / 0.25))
        a2 = T.ss((t - 1.6) / 0.3) * (1 - T.ss((t - 4.2) / 0.3))
        text_block(im, sh[7], W // 2, 290 + max(hh, 390) + 24, font("InterDisplay-Bold.otf", 62), 900, a2, fill=(255, 226, 150), pop=T.ss((t - 1.6) / 0.3))
    else:
        labels(im, t, k, sh)
        if sh[6]:
            a = T.ss(p / 0.2) * (1 - T.ss((t - sh[1] + 0.25) / 0.25))
            hgt = text_block(im, sh[6], W // 2, 1180, font("InterDisplay-Black.otf", 74), 940, a, pop=T.ss(p / 0.25))
            if sh[7]:
                a2 = T.ss((p - 1.0) / 0.25) * (1 - T.ss((t - sh[1] + 0.25) / 0.25))
                text_block(im, sh[7], W // 2, 1180 + hgt + 14, font("InterDisplay-Bold.otf", 56), 900, a2, fill=(255, 226, 150), pop=T.ss((p - 1.0) / 0.25))
        hud(im, t, k, sh)
    d = ImageDraw.Draw(im)
    d.text((72, 150), "PARALLEL EARTH", font=font("Inter-SemiBold.otf", 26), fill=(255, 255, 255, 170))
    if p < 2 / T.FPS and k > 0:
        im.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, 70 if p < 1 / T.FPS else 30)))
    return im.convert("RGB")


if __name__ == "__main__":
    os.makedirs("/home/claude/pe/v2/final", exist_ok=True)
    if sys.argv[1] == "test":
        for s in sys.argv[2:]:
            compose(int(float(s) * T.FPS)).save(f"/home/claude/pe/v2/c_{s}.png")
    else:
        part, n = int(sys.argv[1]), int(sys.argv[2])
        for i in range(part, int(T.DUR * T.FPS), n):
            out = f"/home/claude/pe/v2/final/{i:05d}.jpg"
            if not os.path.exists(out) and os.path.exists(f"/home/claude/pe/v2/frames/{i:05d}.png"):
                compose(i).save(out, quality=94)
