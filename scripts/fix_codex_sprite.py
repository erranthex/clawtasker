#!/usr/bin/env python3
"""
Fix codex.png sprite: add visible white eye highlights in frames 0, 1, 2, and 4.

Both codex and ralph use the same dark-pixel eye structure (6×2 dark pixels per eye),
but codex's large beard consumes most of the face at the small canvas render size
(26×34 px from 96×128 source), making the eyes invisible.

Fix: add white-sclera pixels inside the existing dark eye blocks so the eyes survive
the ~0.27× downscale as bright contrast highlights.
"""
import base64
import io
from pathlib import Path
from PIL import Image

SPRITE_PATH = Path(__file__).resolve().parent.parent / "ui/public/assets/sprites/codex.png"
CONSTANTS_PATH = Path(__file__).resolve().parent.parent / "ui/src/modules/data/constants.js"

WHITE = (255, 255, 255, 255)
EYE_DARK = (16, 15, 19, 255)  # existing eye-dark color (barely distinguishable from bg)

img = Image.open(SPRITE_PATH).convert("RGBA")

# ── Frame 0 (x=0-95): front-facing idle ─────────────────────────────────────
# Left eye block:  x=36-41, y=18-19  → white sclera at x=37,40  pupil at x=38-39
# Right eye block: x=58-63, y=18-19  → white sclera at x=59,62  pupil at x=60-61
for y in (18, 19):
    # Left eye
    img.putpixel((37, y), WHITE)
    img.putpixel((40, y), WHITE)
    # Right eye
    img.putpixel((59, y), WHITE)
    img.putpixel((62, y), WHITE)

# ── Frame 1 (x=96-191): walk-A  ──────────────────────────────────────────────
# Side/3-quarter view: only one eye visible on the right side of face.
# Scan the frame for dark eye-like patches surrounded by skin and add highlights.
SKIN = (232, 184, 144, 255)
# Based on sprite geometry, frame 1 eye is roughly at y=18-19, x=96+38 to 96+45 area
# Use same offset logic: scan for the dark block in the skin area
for frame_ox in (96, 192):  # frames 1 and 2
    # In side-view frames, the face is narrower — one eye visible.
    # Scan row y=18 looking for a 4+ dark-pixel run inside skin on this frame
    for y in (18, 19):
        run_start = None
        for x in range(frame_ox + 28, frame_ox + 68):
            r, g, b, a = img.getpixel((x, y))
            is_dark = a > 50 and r < 30 and g < 30 and b < 30
            is_skin = a > 50 and r > 180 and 140 < g < 220 and 100 < b < 180
            if is_dark and run_start is None:
                run_start = x
            elif not is_dark and run_start is not None:
                run_len = x - run_start
                if 3 <= run_len <= 8:
                    # Found an eye-width dark run — add white highlight at position 1 and -2
                    img.putpixel((run_start + 1, y), WHITE)
                    img.putpixel((x - 2, y), WHITE)
                run_start = None

# ── Frame 4 (x=384-479): talk/point ─────────────────────────────────────────
frame_ox = 384
for y in (18, 19):
    run_start = None
    for x in range(frame_ox + 28, frame_ox + 68):
        r, g, b, a = img.getpixel((x, y))
        is_dark = a > 50 and r < 30 and g < 30 and b < 30
        if is_dark and run_start is None:
            run_start = x
        elif not is_dark and run_start is not None:
            run_len = x - run_start
            if 3 <= run_len <= 8:
                img.putpixel((run_start + 1, y), WHITE)
                img.putpixel((x - 2, y), WHITE)
            run_start = None

# ── Save modified PNG ─────────────────────────────────────────────────────────
img.save(SPRITE_PATH)
print(f"Saved modified sprite to {SPRITE_PATH}")

# ── Update constants.js SPR['codex'] base64 ──────────────────────────────────
buf = io.BytesIO()
img.save(buf, format="PNG")
new_b64 = base64.b64encode(buf.getvalue()).decode("ascii")

js = CONSTANTS_PATH.read_text(encoding="utf-8")

# Locate the three dict boundaries to only replace inside SPR
import re
spr_start = js.find("const SPR")
pt_start  = js.find("const PT")
heads_start = js.find("const HEADS")
# SPR is between spr_start and the smaller of pt_start/heads_start that comes after it
spr_end = min(p for p in (pt_start, heads_start) if p > spr_start)

# Find the codex entry inside SPR region
pattern = r'("codex"\s*:\s*"data:image/png;base64,)([A-Za-z0-9+/=]+)'
match = None
for m in re.finditer(pattern, js):
    if spr_start < m.start() < spr_end:
        match = m
        break

if match is None:
    print("WARNING: Could not find SPR['codex'] entry in constants.js — update manually")
else:
    new_js = js[:match.start(1)] + match.group(1) + new_b64 + js[match.end():]
    CONSTANTS_PATH.write_text(new_js, encoding="utf-8")
    print(f"Updated SPR['codex'] in constants.js at pos={match.start()}")

print("Done.")
