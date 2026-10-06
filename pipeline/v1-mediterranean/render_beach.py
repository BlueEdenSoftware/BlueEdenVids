import sys, os, time, math
sys.path.insert(0, "/home/claude/pe/v2")
import timeline as T
from scene_beach import BeachScene, CAMS
OUT = "/home/claude/pe/v2/frames"; os.makedirs(OUT, exist_ok=True)
s = BeachScene(); s.sc.cycles.samples = 5
for i, t, k, sh in T.frames_for("beach"):
    path = f"{OUT}/{i:05d}.png"
    if os.path.exists(path): continue
    p = (t - sh[0]) / (sh[1] - sh[0])
    lv = T.level_at(t)
    mode = "far" if sh[3] == "beach_far" else "start"
    s.set_state(lv, t, mode)
    c = dict(CAMS[sh[3]])
    loc = list(c["loc"]); tg = list(c["target"])
    if k == 0 or k == len(T.SHOTS) - 1:
        # hook and loop end share the same slow push so the last frame matches the first
        u = p if k == 0 else 1 - p
        loc[1] += 8 * u; loc[2] -= 2 * u
    else:
        loc[1] += 15 * p; loc[2] += 4 * p
    s.set_camera(tuple(loc), tuple(tg), c.get("lens", 22))
    t0 = time.time(); s.render(path); print(f"frame {i} {sh[3]} {time.time()-t0:.1f}s", flush=True)
print("BEACH DONE", flush=True)
