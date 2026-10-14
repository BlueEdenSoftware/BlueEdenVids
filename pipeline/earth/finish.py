# Overlay title, Earth spin counter and captions on the rendered frames, add an original
# synthesized sound track, and encode the final 1080x1920 MP4.
# Run: python3 pipeline/friction/finish.py
import os, glob, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FPS, DUR, T_OFF, T_SLOW = 24, 24, 6.0, 12.0
T_ON = T_SLOW + (5.0 - (T_SLOW - T_OFF) / 50)   # spin returns after 5 real seconds
def real_since_stop(t): return (t - T_OFF) / 50 if t < T_SLOW else (T_SLOW - T_OFF) / 50 + (t - T_SLOW)
SRC = os.path.expanduser("~/ParallelEarth/renders/earth")
TMP = os.path.join(SRC, "final"); os.makedirs(TMP, exist_ok=True)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "parallel-earth", "03-earth-stops.mp4")
W, H = 1080, 1920
FB = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
F_TITLE = ImageFont.truetype(FB, 74); F_CAP = ImageFont.truetype(FB, 54)
F_BIG = ImageFont.truetype(FB, 78); F_LBL = ImageFont.truetype(FB, 26)

TITLE = "What if Earth\nstopped spinning\nfor 5 seconds?"
CAPTIONS = [
    (1.5, 6.0, "In New York, the ground is moving\neast at 1,270 km/h right now."),
    (6.0, 8.5, "Earth stops.\nEverything on it doesn't."),
    (8.5, 12.0, "1,270 km/h sideways.\nFaster than sound."),
    (12.0, T_ON, "Real time: it took 0.1 seconds."),
    (T_ON, 20.0, "The spin is back.\nThe park isn't."),
    (20.0, 24.0, "What would you grab onto?"),
]

def shadow_text(img, xy, text, font, fill=(255, 255, 255), anchor="ma", spacing=10):
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(sh)
    d.multiline_text(xy, text, font=font, fill=(0, 0, 0, 200), anchor=anchor, align="center", spacing=spacing)
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    ImageDraw.Draw(img).multiline_text(xy, text, font=font, fill=fill, anchor=anchor, align="center",
                                       spacing=spacing, stroke_width=3, stroke_fill=(0, 0, 0))

def counter(img, t):
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = 40, 470, 500, 690
    d.rounded_rectangle((x0, y0, x1, y1), 22, fill=(255, 255, 255, 235), outline=(20, 20, 20), width=4)
    off = T_OFF <= t < T_ON
    d.text((x0 + 24, y0 + 18), "EARTH'S SPIN HERE", font=F_LBL, fill=(40, 40, 40))
    d.text((x0 + 24, y0 + 56), "0 km/h" if off else "1,270 km/h", font=F_BIG, fill=(210, 40, 40) if off else (20, 20, 20))
    d.rounded_rectangle((x0 + 24, y0 + 158, x1 - 24, y0 + 176), 8, fill=(220, 220, 220))
    if not off: d.rounded_rectangle((x0 + 24, y0 + 158, x1 - 24, y0 + 176), 8, fill=(60, 180, 75))
    left = max(0.0, 5.0 - real_since_stop(t)) if off else (5.0 if t < T_OFF else 0.0)
    d.text((x0 + 24, y0 + 186), f"TIME LEFT  0:0{left:.3f}", font=F_LBL, fill=(40, 40, 40))
    if T_OFF <= t < T_SLOW or t >= T_SLOW and t < T_SLOW + 2:
        tag = "SLOW MOTION x50" if t < T_SLOW else "REAL TIME"
        col = (210, 40, 40) if t < T_SLOW else (60, 140, 60)
        w = d.textlength(tag, font=F_LBL) + 32
        d.rounded_rectangle((x0, y1 + 14, x0 + w, y1 + 58), 12, fill=col)
        d.text((x0 + 16, y1 + 22), tag, font=F_LBL, fill=(255, 255, 255))

frames = sorted(glob.glob(os.path.join(SRC, "f_[0-9]*.png")))
assert len(frames) == FPS * DUR, f"expected {FPS * DUR} frames, got {len(frames)}"
for i, f in enumerate(frames):
    t = i / FPS
    img = Image.open(f).convert("RGBA").resize((W, H), Image.LANCZOS)
    shadow_text(img, (W // 2, 130), TITLE, F_TITLE)
    counter(img, t)
    for a, b, txt in CAPTIONS:
        if a <= t < b: shadow_text(img, (W // 2, 1380), txt, F_CAP)
    img.convert("RGB").save(os.path.join(TMP, f"{i:04d}.jpg"), quality=92)

# ---------- original sound track (no third-party audio)
SR = 44100; N = SR * DUR; tt = np.arange(N) / SR
rng = np.random.default_rng(3)
def lp(x, k): return np.convolve(x, np.ones(k) / k, mode="same")
amb = lp(rng.standard_normal(N), 40) * 0.05                      # outdoor air bed
pad = sum(np.sin(2 * np.pi * f * tt) for f in (110, 164.8, 220)) * 0.03
pad *= np.clip(tt / 2, 0, 1)
mix = amb + pad
def at(t0, sig):
    i = int(t0 * SR); mix[i:i + len(sig)] += sig[:N - i]
n = int(6 * SR); s = np.arange(n) / SR                            # deep slowed-down roar through the slow-mo
at(T_OFF, lp(rng.standard_normal(n), 120) * np.exp(-0.25 * s) * 3.0)
n = int(2.5 * SR); s = np.arange(n) / SR                          # boom when the planet stops
at(T_OFF, np.sin(2 * np.pi * 38 * s) * np.exp(-1.5 * s) * 0.9)
n = int(0.05 * SR); s = np.arange(n) / SR
for k in range(5):                                                # real-time countdown ticks
    at(T_SLOW + k, np.sin(2 * np.pi * 1800 * s) * np.exp(-60 * s) * 0.25)
mix[int(T_SLOW * SR):int(T_ON * SR)] *= 0.25                       # eerie quiet, park empty
n = int(1.2 * SR); s = np.arange(n) / SR                          # spin returns
at(T_ON, np.sin(2 * np.pi * (60 + 200 * s) * s) * np.exp(-2 * s) * 0.4)
mix = np.clip(mix / max(1e-6, np.abs(mix).max()) * 0.8, -1, 1)
wav = os.path.join(TMP, "audio.wav")
with wave.open(wav, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())

subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(TMP, "%04d.jpg"),
                "-i", wav, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-preset", "medium",
                "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT], check=True)
print("WROTE", os.path.abspath(OUT))
