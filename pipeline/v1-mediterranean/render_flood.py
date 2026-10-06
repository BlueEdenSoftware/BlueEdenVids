import sys, os, time
sys.path.insert(0, "/home/claude/pe/v2")
import timeline as T
from scene_map import MapScene, add_torrent, set_torrent
OUT = "/home/claude/pe/v2/frames"; os.makedirs(OUT, exist_ok=True)
s = MapScene(); add_torrent(s); s.sc.cycles.samples = 4
for i, t, k, sh in T.frames_for("flood"):
    path = f"{OUT}/{i:05d}.png"
    if os.path.exists(path): continue
    p = (t - sh[0]) / (sh[1] - sh[0])
    lv = T.level_at(t)
    s.set_level(lv, 0.0); set_torrent(s, lv, t)
    s.set_camera(lon=T.lerp(-4.5, -3.9, p), lat=36.0, heading=80, pitch=T.lerp(40, 34, p), dist=T.lerp(440, 380, p), fog=(1.1, 3.0))
    t0 = time.time(); s.render(path); print(f"frame {i} flood {time.time()-t0:.1f}s", flush=True)
print("FLOOD DONE", flush=True)
