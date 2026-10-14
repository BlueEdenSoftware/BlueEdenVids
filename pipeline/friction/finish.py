# Overlay title, friction counter and captions on the rendered frames, add an original
# synthesized sound track, and encode the final 1080x1920 MP4.
# Run: python3 pipeline/friction/finish.py
import os, glob, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FPS, DUR, T_OFF, T_ON = 24, 22, 6.0, 11.0
SRC = os.path.expanduser("~/ParallelEarth/renders/friction")
TMP = os.path.join(SRC, "final"); os.makedirs(TMP, exist_ok=True)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "parallel-earth", "02-friction.mp4")
W, H = 1080, 1920
FB = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
F_TITLE = ImageFont.truetype(FB, 74); F_CAP = ImageFont.truetype(FB, 54)
F_BIG = ImageFont.truetype(FB, 96); F_LBL = ImageFont.truetype(FB, 26)

TITLE = "What if friction\ndisappeared for\n5 seconds?"
CAPTIONS = [
    (6.0, 8.5, "Friction just hit zero."),
    (8.5, 11.0, "Walking? Your foot slides out.\nStanding still? You're fine."),
    (11.0, 14.5, "Friction is back.\nEveryone stops at once."),
    (14.5, 22.0, "Which one were you:\nwalking or standing?"),
]

def shadow_text(img, xy, text, font, fill=(255, 255, 255), anchor="ma", spacing=10):
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(sh)
    d.multiline_text(xy, text, font=font, fill=(0, 0, 0, 200), anchor=anchor, align="center", spacing=spacing)
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    ImageDraw.Draw(img).multiline_text(xy, text, font=font, fill=fill, anchor=anchor, align="center",
                                       spacing=spacing, stroke_width=3, stroke_fill=(0, 0, 0))

def counter(img, t):
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = 40, 470, 420, 690
    d.rounded_rectangle((x0, y0, x1, y1), 22, fill=(255, 255, 255, 235), outline=(20, 20, 20), width=4)
    off = T_OFF <= t < T_ON
    d.text((x0 + 24, y0 + 18), "FRICTION", font=F_LBL, fill=(40, 40, 40))
    d.text((x0 + 24, y0 + 48), "0%" if off else "100%", font=F_BIG, fill=(210, 40, 40) if off else (20, 20, 20))
    bar = 0 if off else 1
    d.rounded_rectangle((x0 + 24, y0 + 158, x1 - 24, y0 + 176), 8, fill=(220, 220, 220))
    if bar: d.rounded_rectangle((x0 + 24, y0 + 158, x1 - 24, y0 + 176), 8, fill=(60, 180, 75))
    left = max(0.0, T_ON - t) if off else (5.0 if t < T_OFF else 0.0)
    d.text((x0 + 24, y0 + 186), f"TIME LEFT  0:0{left:.3f}", font=F_LBL, fill=(40, 40, 40))

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
n = int(0.8 * SR); s = np.arange(n) / SR                          # downward "zip" when friction drops
at(T_OFF - 0.1, np.sin(2 * np.pi * (900 * np.exp(-4 * s)) * s) * np.exp(-3 * s) * 0.35)
n = int(1.5 * SR); s = np.arange(n) / SR                          # low boom on the falls
at(T_OFF + 0.45, np.sin(2 * np.pi * 50 * s) * np.exp(-3 * s) * 0.6)
for k in range(5):                                                # countdown ticks
    n = int(0.05 * SR); s = np.arange(n) / SR
    at(T_OFF + k, np.sin(2 * np.pi * 1800 * s) * np.exp(-60 * s) * 0.25)
n = int(0.4 * SR); s = np.arange(n) / SR                          # skid stop
at(T_ON, lp(rng.standard_normal(n), 6) * np.exp(-8 * s) * 0.5)
mix[int(T_OFF * SR):int(T_ON * SR)] *= 0.6                        # eerie quiet while frictionless
mix = np.clip(mix / max(1e-6, np.abs(mix).max()) * 0.8, -1, 1)
wav = os.path.join(TMP, "audio.wav")
with wave.open(wav, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())

subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(TMP, "%04d.jpg"),
                "-i", wav, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-preset", "medium",
                "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT], check=True)
print("WROTE", os.path.abspath(OUT))
