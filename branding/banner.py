import random, cairosvg

def earths(cx, cy, r, gap):
    ax, bx = cx - gap / 2, cx + gap / 2
    s = r / 250  # polygons designed for r=250 centred at 430/594
    def poly(pts, ox):
        return " ".join(f"{ox + (x - (430 if ox == ax else 594)) * s:.1f},{cy + (y - 512) * s:.1f}" for x, y in pts)
    return f'''
  <clipPath id="cA"><circle cx="{ax}" cy="{cy}" r="{r}"/></clipPath>
  <clipPath id="cB"><circle cx="{bx}" cy="{cy}" r="{r}"/></clipPath>
  <circle cx="{bx}" cy="{cy}" r="{r}" fill="url(#earthB)"/>
  <g clip-path="url(#cB)" fill="#7a2e1c" opacity="0.55">
    <polygon points="{poly([(560,330),(680,300),(760,380),(700,440),(600,420)], bx)}"/>
    <polygon points="{poly([(620,520),(760,500),(800,610),(700,680),(640,620)], bx)}"/>
    <polygon points="{poly([(480,600),(560,580),(590,700),(500,740)], bx)}"/>
  </g>
  <circle cx="{ax}" cy="{cy}" r="{r}" fill="url(#earthA)"/>
  <g clip-path="url(#cA)" fill="#2f8f4e" opacity="0.9">
    <polygon points="{poly([(300,330),(420,300),(470,370),(410,430),(320,410)], ax)}"/>
    <polygon points="{poly([(380,500),(500,470),(540,570),(460,650),(390,600)], ax)}"/>
    <polygon points="{poly([(230,560),(300,540),(320,640),(250,690)], ax)}"/>
  </g>
  <g clip-path="url(#cA)"><circle cx="{bx}" cy="{cy}" r="{r}" fill="none" stroke="#f2a65a" stroke-width="{10*s:.1f}" opacity="0.95"/></g>
  <circle cx="{ax}" cy="{cy}" r="{r}" fill="none" stroke="#fff" stroke-width="{6*s:.1f}" opacity="0.35"/>'''

def banner(W, H, safe_w, safe_h, out, seed=7):
    random.seed(seed)
    cx, cy = W / 2, H / 2
    pts = []
    for _ in range(int(W * H / 9000)):
        x, y = random.uniform(0, W), random.uniform(0, H)
        if abs(y - cy) < safe_h * 0.55 and cx - safe_w / 2 - 20 < x < cx + safe_w / 2 + 20:
            continue  # keep the logo/text zone clean
        pts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{random.uniform(0.8,2.6)*W/2560:.2f}" opacity="{random.uniform(0.25,0.85):.2f}"/>')
    stars = "".join(pts)
    r = safe_h * 0.40
    ex = cx - safe_w / 2 + r * 1.55
    tx = ex + r * 1.75
    title = safe_h * 0.30
    sub = safe_h * 0.085
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <defs>
    <radialGradient id="bg" cx="40%" cy="50%" r="80%"><stop offset="0" stop-color="#16294a"/><stop offset="1" stop-color="#060b18"/></radialGradient>
    <linearGradient id="earthA" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3fc1c9"/><stop offset="1" stop-color="#1b5f8c"/></linearGradient>
    <linearGradient id="earthB" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f2a65a"/><stop offset="1" stop-color="#b8502e"/></linearGradient>
    <linearGradient id="haze" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#3fc1c9" stop-opacity="0"/><stop offset="0.5" stop-color="#3fc1c9" stop-opacity="0.10"/><stop offset="1" stop-color="#f2a65a" stop-opacity="0"/></linearGradient>
  </defs>
  <rect width="{W}" height="{H}" fill="url(#bg)"/>
  <rect y="{cy - H*0.12}" width="{W}" height="{H*0.24}" fill="url(#haze)" transform="rotate(-8 {cx} {cy})"/>
  <g fill="#fff">{stars}</g>
  {earths(ex, cy, r, r * 0.66)}
  <text x="{tx}" y="{cy + title*0.18}" font-family="Inter Display" font-weight="800" font-size="{title:.0f}" fill="#ffffff" letter-spacing="{-title*0.02:.1f}">Parallel <tspan fill="#f2a65a">Earth</tspan></text>
  <text x="{tx + title*0.03}" y="{cy + title*0.18 + sub*1.9}" font-family="Inter" font-weight="500" font-size="{sub:.0f}" fill="#9fb3cf" letter-spacing="{sub*0.18:.1f}">WHAT IF EARTH WERE DIFFERENT?</text>
  <text x="{tx + title*0.03}" y="{cy - title*0.62}" font-family="Inter" font-weight="600" font-size="{sub*0.8:.0f}" fill="#3fc1c9" letter-spacing="{sub*0.3:.1f}">NEW SCENARIO EVERY 2 DAYS</text>
</svg>'''
    open(out.replace(".png", ".svg"), "w").write(svg)
    cairosvg.svg2png(bytestring=svg.encode(), write_to=out, output_width=W, output_height=H)

# YouTube: 2560x1440, safe area 1546x423 (visible on all devices)
banner(2560, 1440, 1546, 423, "parallel-earth-youtube-banner.png")
# Facebook cover: 1640x624 upload, keep content in centre for mobile crop
banner(1640, 624, 1180, 400, "parallel-earth-facebook-cover.png")
print("ok")
