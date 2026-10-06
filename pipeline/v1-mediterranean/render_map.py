import sys, os, math, time
sys.path.insert(0, "/home/claude/pe/v2")
import timeline as T
from scene_map import MapScene

CAMS = {
    "gibraltar": dict(lon=-4.9, lat=36.0, heading=72, pitch=45, dist=600),
    "sicily":    dict(lon=11.9, lat=36.9, heading=15, pitch=45, dist=760),
    "wide":      dict(lon=10.0, lat=38.0, heading=80, pitch=30, dist=2100),
    "high":      dict(lon=17.0, lat=37.5, heading=85, pitch=55, dist=3300),
    "abyss":     dict(lon=19.0, lat=34.6, heading=40, pitch=16, dist=520, tz=-70, fog=(1.4, 4.0)),
    "high2":     dict(lon=15.0, lat=37.0, heading=100, pitch=65, dist=3600),
    "wide2":     dict(lon=12.0, lat=37.5, heading=60, pitch=28, dist=2500),
}
OUT = "/home/claude/pe/v2/frames"
os.makedirs(OUT, exist_ok=True)
s = MapScene()
s.sc.cycles.samples = 4
for i, t, k, sh in T.frames_for("map"):
    path = f"{OUT}/{i:05d}.png"
    if os.path.exists(path):
        continue
    c = dict(CAMS[sh[3]])
    p = (t - sh[0]) / (sh[1] - sh[0])
    c["dist"] *= T.lerp(1.06, 0.92, p)
    c["heading"] += T.lerp(-3, 3, p)
    if sh[3] == "abyss":
        c["tz"] = T.level_at(t) / 1000 * 25 + 12
    dam = 0.0 if t < 5.2 else T.ss((t - 5.2) / 1.6) if sh[3] == "gibraltar" else 1.0
    s.set_level(T.level_at(t), dam)
    s.set_camera(**c)
    t0 = time.time(); s.render(path)
    print(f"frame {i} {sh[3]} {time.time()-t0:.1f}s", flush=True)
print("MAP DONE", flush=True)
