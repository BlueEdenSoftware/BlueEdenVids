# Parallel Earth: Mac capability check. Run inside Blender's Python console.
import bpy, platform, subprocess, os, time
out = []
out.append(f"Blender {bpy.app.version_string}")
out.append(f"macOS {platform.mac_ver()[0]}  arch {platform.machine()}")
try:
    chip = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True).stdout.strip()
    ram = int(subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True).stdout) / 2**30
    out.append(f"Chip {chip}  RAM {ram:.0f} GB")
except Exception as e:
    out.append(f"sysctl failed: {e}")
prefs = bpy.context.preferences.addons["cycles"].preferences
try:
    prefs.compute_device_type = "METAL"
    prefs.refresh_devices()
    out.append("Cycles GPU: " + ", ".join(d.name for d in prefs.devices if d.type == "METAL"))
except Exception as e:
    out.append(f"Metal not available: {e}")
# quick GPU test render
sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "GPU"; sc.cycles.samples = 32
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
folder = os.path.expanduser("~/ParallelEarth"); os.makedirs(folder, exist_ok=True)
sc.render.filepath = os.path.join(folder, "probe.png")
t = time.time()
try:
    bpy.ops.render.render(write_still=True)
    out.append(f"Test render 1080x1920 @32 samples: {time.time()-t:.1f}s")
except Exception as e:
    out.append(f"Render failed: {e}")
open(os.path.join(folder, "probe.txt"), "w").write("\n".join(out))
print("\n".join(out))
