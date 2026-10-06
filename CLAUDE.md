# CLAUDE.md: Parallel Earth handoff

Handoff from a Claude cloud chat (started 2026-10-04) to Claude Code on Med's Mac. Read this first.

## Who and how to talk to him
- Med, 21, founder of Blue Eden Softwares SUARL (Tunis). Software/tech background. Communicates in English, French and Tunisian Arabic.
- Format rules (strict): bullet points with concrete, numbered steps, not long prose. **Never use em dashes (the long dash character).**
- He has ADHD and autism and asked to go step by step: one step at a time, one decision at a time.
- Wants brutal honesty: lead with the strongest counterargument, give confidence levels (high/moderate/low), no flattery, no capitulating without new evidence.
- Goal: **money**. Everything is judged by views and revenue.

## The project
- Faceless "What if..." 3D animation channel, English, called **Parallel Earth**.
- Accounts (all created, same name and logo): YouTube channel, Facebook Page, Instagram **@parallelearth.tv** (Professional), TikTok (region Tunisia, cannot change: needs 60 days of real use in the US).
- Bios, logo, YouTube banner, Facebook cover: done. Files in `branding/`.
- Monetization facts (verified Oct 2026):
  - YouTube Partner Program is available in Tunisia: **main revenue source** (1,000 subs + 10M Shorts views/90 days or 4,000 watch hours).
  - TikTok Creator Rewards: NOT available in Tunisia. TikTok = reach + brand deals only.
  - Facebook Content Monetization: invite-only, Tunisia eligibility unknown. He should check Professional Dashboard → Monetization.
  - Instagram: no view payouts. Reach + brand deals.

## Posting pipeline (working)
- **Metricool** free plan, one brand "Parallel Earth", blogId/brandId **7240771**, timezone Africa/Tunis. All 4 networks connected. Free plan limit: 20 scheduled posts per month.
- The Metricool MCP connector works in Claude (tools: createScheduledPost, getScheduledPosts, getBestTimeToPostByNetwork, analytics). Connect it in this Claude Code session too if available.
- Metricool needs media at a **public URL**. Solution: public GitHub repo **BlueEdenSoftware/BlueEdenVids** (this repo). Push the MP4, then pass
  `https://raw.githubusercontent.com/BlueEdenSoftware/blueedenvids/main/<path>.mp4` in `media`. Metricool copies it to its own storage.
- Post settings used: YouTube type `short`, madeForKids false, category SCIENCE_TECHNOLOGY; Instagram REEL; Facebook REEL; TikTok PUBLIC_TO_EVERYONE. One post with all 4 providers works.
- Gotcha: when reconnecting Facebook in Metricool, keep the Instagram permissions ON or Instagram disconnects.

## Published so far
- Video #1 "What if the Mediterranean Sea dried up?" (`parallel-earth/01-mediterranean.mp4`, 52 s, 1080x1920, 24 fps), posted 2026-10-05:
  - YouTube https://www.youtube.com/shorts/ts26hDdmDqY
  - Facebook https://facebook.com/reel/1775467466834393
  - Instagram https://www.instagram.com/reel/DeIPOSoiUjw/
  - TikTok video id 7693304415427661057
- Captions used: `pipeline/v1-mediterranean/post-01-captions.md`.
- TODO: around 2026-10-07, pull Metricool analytics (views, retention, viewer countries) and report what to change.

## Honest status and the big lesson
- v1 (2D renderer) scored 4/10; v2 (Blender, cloud CPU) about 6/10. Med is right that competitors are far ahead:
  - **Lunar Animation** (@lunarcheeseee, 168K followers, 2.9M likes, videos 1.6M to 9.2M views)
  - **moon animations** (@moon2animation, a copycat, 20K followers, 3.3M on one video)
  - **What if?** (@man_ia_c, 29.5K followers, electrons video 3.8M views, labeled AI-generated so the label does not kill reach)
- What they do that we did not:
  1. Hook "What if X hit **your** city?" or "for 5 seconds", set in a **famous real place everyone knows** (Central Park, New York, Burning Man, a cruise ship). Not local/Tunisian. My mistake was pushing a Tunisian/Mediterranean angle; it shrank the audience.
  2. **One hero location**, slow nearly static camera, dense believable scene (cruise ship, pier, fountain, promenade, lamp posts, benches, flower beds, dozens of low-poly people, cars).
  3. **One counter as the spine**: top-left, serif number, small caps subtitle (e.g. "ELECTRONS DISAPPEAR IN 0:04.800 / EVERY ATOM ON EARTH HAS THEM", "MAGNITUDE 0.0 / THE FAULT IS LOCKED").
  4. Big serif title (Georgia/EB Garamond style) centered at the top, a key word colored. Cinematic slow build then spectacle.
  5. They post often. Speed and volume win.
- Strongest risk (moderate confidence): we are at least the 4th account in this exact template; it may burn out in weeks. Win on volume + better topics + higher scene density.

## New plan (agreed direction)
1. Run Blender **locally on the Mac** (GPU via Metal) from the terminal: `blender -b -P script.py`. Much faster than the 2-core cloud box.
2. First run `scripts/probe.py` (Mac chip, RAM, Metal GPU, test render time). Adjust scene density to RAM.
3. Build a reusable **world kit** once from free CC0 assets (Mac has normal internet): Quaternius and Kenney packs (people, cars, city buildings, park props), Poly Haven (HDRI skies, textures). Scenes: Central-Park-style park with skyline, city street/crosswalk, beach promenade with pier, cruise ship deck.
4. Match the genre template exactly: serif title, one counter top-left, famous place, ground-level hero shot, event escalates in stages. 45 to 60 s, vertical 1080x1920.
5. Series 1 "for 5 seconds" (not yet covered by those accounts as far as seen):
   1. What if friction disappeared for 5 seconds? (next video, set in a Central-Park-like park)
   2. What if Earth stopped spinning for 5 seconds?
   3. What if the speed of light dropped to walking pace?
   4. What if the Sun vanished for 5 seconds?
   5. What if all metal turned liquid for 5 seconds?
   Other: What if a 1 km asteroid hit the ocean near your city? What if the Moon came twice as close?
6. Target 1 video per day on all 4 platforms. Weekly analytics review: double down on topics with best completion rate.
7. Facts: every number must be checked against a real source; give a sources line in the pinned comment.
8. Music: original or royalty-free only (no copyrighted tracks). Note that a trending sound added in-app often beats our own track on TikTok/IG.

## Repo layout
- `parallel-earth/` final MP4s served to Metricool (keep public).
- `pipeline/v1-mediterranean/` v2 Blender pipeline from the cloud (scene_map/scene_beach/scene_flood, timeline, compose2 overlay compositor with HUD/captions/labels, music2 synth score, terrain grids from ETOPO 10 arcmin). Paths inside point to `/home/claude/pe/v2/...` and must be updated before reuse. The compositor (PIL: serif-less Inter fonts) should switch to a serif title font to match the genre.
- `branding/` logo (two overlapping Earths, blue + orange, dark navy bg), banners, banner generator.
- `scripts/probe.py` Mac capability check.
- Commits end with: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## First steps for Claude Code on the Mac
1. Confirm Blender is installed (`/Applications/Blender.app/Contents/MacOS/Blender`), run probe.py headless, report chip/RAM/GPU/render time.
2. Create `~/ParallelEarth/assets`, download the CC0 packs, verify licenses.
3. Build the park world kit, render ONE hero frame, show Med next to Lunar's style before rendering a full video.
