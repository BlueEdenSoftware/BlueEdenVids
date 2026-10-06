"""Original score + sound design for v2 (fully synthesized, no third-party audio)."""
import numpy as np, wave
from scipy.signal import fftconvolve, butter, lfilter
import timeline as T

SR = 44100
DUR = T.DUR
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(7)
L = np.zeros(N); R = np.zeros(N)
CUTS = [s[0] for s in T.SHOTS[1:]]


def hz(m): return 440 * 2 ** ((m - 69) / 12)


def add(sig, start, pan=0.0, gain=1.0):
    i0 = int(start * SR); i1 = min(N, i0 + len(sig))
    if i1 <= i0: return
    s = sig[:i1 - i0] * gain
    L[i0:i1] += s * (1 - pan) * 0.7071 * 1.4142 / 2 * 2 ** 0.5
    R[i0:i1] += s * (1 + pan) * 0.7071 * 1.4142 / 2 * 2 ** 0.5


def env(n, a, r):
    e = np.ones(n); na = int(a * SR); nr = int(r * SR)
    e[:na] = np.linspace(0, 1, na) if na else 1
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e


def pad(notes, dur, amp=0.06, bright=0.25):
    n = int(dur * SR); tt = np.arange(n) / SR; s = np.zeros(n)
    for m in notes:
        for det in (-0.08, 0, 0.08):
            f = hz(m) * 2 ** (det / 12)
            s += np.sin(2 * np.pi * f * tt) + bright * np.sin(2 * np.pi * 2 * f * tt) + 0.1 * np.sin(2 * np.pi * 3 * f * tt)
    return amp * s / len(notes) * env(n, 1.2, 1.5)


def lowpass(x, fc):
    b, a = butter(2, fc / (SR / 2)); return lfilter(b, a, x)


def highpass(x, fc):
    b, a = butter(2, fc / (SR / 2), "high"); return lfilter(b, a, x)


def boom(amp=0.8, f0=60, dur=2.2):
    n = int(dur * SR); tt = np.arange(n) / SR
    f = f0 * (1 + 1.5 * np.exp(-tt * 18))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 2.2)
    s += lowpass(rng.standard_normal(n), 400) * np.exp(-tt * 9) * 0.6
    return amp * s


def whoosh(dur=0.7, amp=0.25):
    n = int(dur * SR); tt = np.arange(n) / SR
    x = rng.standard_normal(n)
    e = np.sin(np.pi * tt / dur) ** 2
    return amp * highpass(lowpass(x, 3500), 500) * e


def tick(amp=0.12):
    n = int(0.08 * SR); tt = np.arange(n) / SR
    return amp * np.sin(2 * np.pi * 1900 * tt) * np.exp(-tt * 90)


def pluck(m, amp=0.12, dur=2.5):
    n = int(dur * SR); tt = np.arange(n) / SR; f = hz(m)
    s = sum(np.sin(2 * np.pi * f * k * tt) * np.exp(-tt * (2.5 + k * 1.6)) / k for k in range(1, 6))
    return amp * s


# ---- hook (0-4.5): low drone + riser, sea pulling back ----
add(pad([33, 45, 52], 5.2, amp=0.09, bright=0.1), 0.0)
n = int(4.5 * SR); tt = np.arange(n) / SR
riser = highpass(rng.standard_normal(n), 800) * (tt / 4.5) ** 2.5 * 0.18
add(riser, 0.0)
surf = lowpass(rng.standard_normal(int(4.4 * SR)), 900) * 0.10 * np.exp(-np.arange(int(4.4 * SR)) / SR * 0.5)
add(surf, 0.0, pan=-0.3)

# ---- cuts: whoosh into each new shot, boom on the key ones ----
for c in CUTS:
    add(whoosh(), c - 0.45, pan=0.2)
for c, a in [(4.5, 0.7), (6.4, 0.9), (37.5, 0.5), (41.0, 1.0)]:
    add(boom(a), c)

# ---- drying sequence (9 - 37.5): A-minor progression + clock ticks + plucked motif ----
prog = [(9.0, [45, 57, 60, 64]), (13.5, [41, 53, 57, 60]), (18.5, [48, 55, 60, 64]), (23.0, [43, 55, 59, 62]),
        (28.5, [40, 52, 55, 59]), (33.5, [41, 53, 57, 62])]
for s, ch in prog:
    add(pad(ch, 6.2, amp=0.07), s - 0.3)
motif = [69, 72, 76, 74, 72, 69, 67, 69]
for k, s in enumerate(np.arange(9.0, 37.0, 0.875)):
    add(tick(0.08 if k % 2 else 0.12), s, pan=0.5)
    if k % 4 == 0:
        add(pluck(motif[(k // 4) % len(motif)], 0.07), s, pan=-0.3)

# ---- "Impossible?" (37.5-41): near silence, single high note ----
add(pluck(81, 0.08, 3.0), 37.6)
add(pad([57, 64], 3.4, amp=0.03, bright=0.0), 37.6)

# ---- flood (41-48): roar + drums + rising chords ----
n = int(7.2 * SR); tt = np.arange(n) / SR
rx = rng.standard_normal(n); roar = (lowpass(rx, 400) * (1 - tt / 7.2) + lowpass(rx, 2200) * (tt / 7.2)) * np.clip(tt / 1.2, 0, 1) * np.clip((7.2 - tt) / 0.8, 0, 1) * 0.55
add(roar, 41.0, pan=-0.1); add(lowpass(rng.standard_normal(n), 120) * 0.4 * np.clip(tt / 1.5, 0, 1) * np.clip((7.2 - tt) / 0.8, 0, 1), 41.0, pan=0.1)
for s in np.arange(41.0, 47.9, 0.5):
    add(boom(0.35 + 0.25 * (s - 41) / 7, 70, 0.6), s)
for s, ch in [(41.0, [45, 52, 57, 60, 64]), (43.4, [41, 48, 53, 57, 60]), (45.6, [43, 50, 55, 59, 62])]:
    add(pad(ch, 2.8, amp=0.11, bright=0.4), s)

# ---- return + loop (48-52): major resolution, gentle surf, fades to the hook drone level ----
add(pad([45, 57, 61, 64, 69], 4.2, amp=0.09, bright=0.2), 48.0)
add(lowpass(rng.standard_normal(int(4 * SR)), 900) * 0.10, 48.0, pan=-0.3)

# ---- reverb + master ----
ir_n = int(2.2 * SR); ir_t = np.arange(ir_n) / SR
irL = rng.standard_normal(ir_n) * np.exp(-ir_t * 2.6); irR = rng.standard_normal(ir_n) * np.exp(-ir_t * 2.6)
irL /= np.sqrt((irL ** 2).sum()); irR /= np.sqrt((irR ** 2).sum())
wl = fftconvolve(L, irL)[:N]; wr = fftconvolve(R, irR)[:N]
L2 = L * 0.8 + wl * 0.35; R2 = R * 0.8 + wr * 0.35
fade = np.clip(t / 0.05, 0, 1) * np.clip((DUR - t) / 0.08, 0, 1)
L2 *= fade; R2 *= fade
pk = max(np.abs(L2).max(), np.abs(R2).max())
L2 = np.tanh(L2 / pk * 1.3) / np.tanh(1.3) * 0.89; R2 = np.tanh(R2 / pk * 1.3) / np.tanh(1.3) * 0.89
pcm = (np.stack([L2, R2], 1) * 32767).astype(np.int16)
with wave.open("/home/claude/pe/v2/music2.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("ok", DUR)
