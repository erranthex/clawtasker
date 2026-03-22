#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / 'third_party' / 'pocket-office-quest-v9'
WEB_ASSETS = ROOT / 'web' / 'assets'
UI_PUBLIC = ROOT / 'ui' / 'public' / 'assets'
DOCS = ROOT / 'docs'
VERSION = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
VTAG = VERSION.replace('.', '_').replace('-', '_')

PORTRAITS = WEB_ASSETS / 'portraits'
SPRITES = WEB_ASSETS / 'sprites'
TEXTURES = WEB_ASSETS / 'textures'

# Maps the 14 ClawTasker app agents to their Pocket Office Quest v9 characters.
# v9 has 12 characters; 14 agents means 2 sharing pairs are unavoidable.
# Sharing pairs are chosen for role coherence and visual separation:
#   ledger + iris  → mina  (both back-office / people-ops roles)
#   scout  + mercury → zara (both analyst / research-domain roles)
# All other agents map to a unique v9 character.
AGENT_MAP = {
    'ceo':     'aria',   # Creative Director  → CEO / leader
    'orion':   'kai',    # Tools Engineer     → Chief Agent / planner
    'codex':   'rex',    # Studio Lead        → Engineering Manager
    'violet':  'quinn',  # Research Analyst   → Intelligence Manager
    'charlie': 'rowan',  # IT Ranger          → Operations Manager
    'ralph':   'marco',  # QA Lead            → QA & Validation Lead  (exact match)
    'shield':  'finn',   # Security (v9-only) → Security Reviewer      (exact match)
    'pixel':   'yuki',   # Art Lead           → Design Lead            (exact match)
    'echo':    'sasha',  # UX Designer        → Distribution Specialist
    'quill':   'devon',  # Tech Writer        → Knowledge & People Manager
    'scout':   'zara',   # Analyst (v9-only)  → Trend Radar            [shares zara with mercury]
    'iris':    'mina',   # Operations Lead    → HR Specialist           [shares mina with ledger]
    'ledger':  'mina',   # Operations Lead    → Purchasing Specialist   [shares mina with iris]
    'mercury': 'zara',   # Analyst (v9-only)  → Media Analyst           [shares zara with scout]
}

AGENTS = {
    'ceo': {'name': 'You', 'role': 'CEO / Human operator', 'specialist': 'leadership', 'status': 'Active'},
    'orion': {'name': 'Orion', 'role': 'Chief Agent', 'specialist': 'planning', 'status': 'Working'},
    'codex': {'name': 'Codex', 'role': 'Engineering Manager', 'specialist': 'code', 'status': 'Working'},
    'violet': {'name': 'Violet', 'role': 'Intelligence Manager', 'specialist': 'research', 'status': 'Sync'},
    'scout': {'name': 'Scout', 'role': 'Trend Radar', 'specialist': 'research', 'status': 'Working'},
    'charlie': {'name': 'Charlie', 'role': 'Operations Manager', 'specialist': 'ops', 'status': 'Blocked'},
    'ralph': {'name': 'Ralph', 'role': 'QA Lead', 'specialist': 'qa', 'status': 'Validation'},
    'shield': {'name': 'Shield', 'role': 'Security Reviewer', 'specialist': 'security', 'status': 'Idle'},
    'quill': {'name': 'Quill', 'role': 'Knowledge & People Manager', 'specialist': 'docs', 'status': 'Working'},
    'pixel': {'name': 'Pixel', 'role': 'Designer', 'specialist': 'design', 'status': 'Working'},
    'echo': {'name': 'Echo', 'role': 'Distribution Specialist', 'specialist': 'distribution', 'status': 'Working'},
    'iris': {'name': 'Iris', 'role': 'HR Specialist', 'specialist': 'hr', 'status': 'Idle'},
    'ledger': {'name': 'Ledger', 'role': 'Purchasing Specialist', 'specialist': 'procurement', 'status': 'Working'},
    'mercury': {'name': 'Mercury', 'role': 'Media Analyst', 'specialist': 'media', 'status': 'Working'},
}

OFFICE_SLOTS = {
    'ceo_strip': [{'x': 650, 'y': 692}],
    'chief_desk': [{'x': 520, 'y': 694}],
    'code_pod': [{'x': 188, 'y': 262}, {'x': 292, 'y': 262}, {'x': 188, 'y': 406}, {'x': 292, 'y': 406}],
    'research_pod': [{'x': 986, 'y': 262}, {'x': 1096, 'y': 262}, {'x': 986, 'y': 406}, {'x': 1096, 'y': 406}],
    'ops_pod': [{'x': 188, 'y': 582}, {'x': 292, 'y': 582}, {'x': 188, 'y': 682}, {'x': 292, 'y': 682}],
    'qa_pod': [{'x': 988, 'y': 582}, {'x': 1096, 'y': 582}],
    'studio_pod': [{'x': 1028, 'y': 676}, {'x': 1118, 'y': 676}, {'x': 1208, 'y': 676}, {'x': 1298, 'y': 676}],
    'scrum_table': [{'x': 510, 'y': 214}, {'x': 640, 'y': 194}, {'x': 770, 'y': 214}, {'x': 510, 'y': 332}, {'x': 640, 'y': 350}, {'x': 770, 'y': 332}],
    'review_rail': [{'x': 910, 'y': 520}, {'x': 1014, 'y': 520}, {'x': 1118, 'y': 520}, {'x': 1222, 'y': 520}],
    'lounge': [{'x': 430, 'y': 680}, {'x': 520, 'y': 680}, {'x': 780, 'y': 680}, {'x': 870, 'y': 680}],
    'board_wall': [{'x': 640, 'y': 98}],
}

OFFICE_ASSIGNMENTS = {
    'ceo': ('ceo_strip', 0),
    'orion': ('chief_desk', 0),
    'codex': ('code_pod', 0),
    'scout': ('research_pod', 0),
    'violet': ('scrum_table', 1),
    'charlie': ('ops_pod', 0),
    'ralph': ('review_rail', 0),
    'shield': ('ops_pod', 2),
    'quill': ('studio_pod', 0),
    'pixel': ('studio_pod', 1),
    'echo': ('research_pod', 1),
    'iris': ('studio_pod', 2),
    'ledger': ('ops_pod', 1),
    'mercury': ('research_pod', 2),
}

STATUS_COLORS = {
    'Active': '#14b8a6',
    'Working': '#14b8a6',
    'Sync': '#ff5c5c',
    'Validation': '#f59e0b',
    'Blocked': '#ef4444',
    'Idle': '#64748b',
}

PALETTE = {
    'bg': '#071426',
    'surface': '#0b1931',
    'panel': '#0d1d36',
    'text': '#f4fbff',
    'muted': '#d6e2f2',
    'dim': '#8fa6c1',
    'border': '#1a2f4d',
    'accent': '#67e8d7',
    'accent2': '#77b9ff',
    'light': '#f8f9fa',
    'day_floor_a': '#d7d4cd',
    'day_floor_b': '#cbc7bf',
    'night_floor_a': '#2b3140',
    'night_floor_b': '#252b38',
    'wood': '#b88c5a',
    'wood_dark': '#8c6841',
    'glass_day': '#9ad4ff',
    'glass_night': '#355c89',
    'glow': '#7cd4ff',
    'paper': '#f6f7fb',
    'ink': '#11253c',
    'softgold': '#f1c46d',
    'cardbg': '#10213b',
}


try:
    FONT_XL = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 28)
    FONT_L = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22)
    FONT_M = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 16)
    FONT_S = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)
    FONT_XS = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 11)
except Exception:
    FONT_XL = FONT_L = FONT_M = FONT_S = FONT_XS = ImageFont.load_default()


def rgba(hex_color: str, a: int = 255):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4)) + (a,)


def ensure_dirs() -> None:
    for path in (PORTRAITS, SPRITES, TEXTURES, DOCS, UI_PUBLIC, VENDOR / 'compat'):
        path.mkdir(parents=True, exist_ok=True)


def crop_frame(sheet: Image.Image, direction: str) -> Image.Image:
    row_map = {'front': 0, 'left': 1, 'right': 2, 'back': 3}
    cell_w = sheet.width // 4
    cell_h = sheet.height // 4
    sx = 0
    sy = row_map[direction] * cell_h
    return sheet.crop((sx, sy, sx + cell_w, sy + cell_h))


def build_seated_variant(frame: Image.Image) -> Image.Image:
    seated = frame.copy()
    lower = frame.crop((0, frame.height // 2, frame.width, frame.height))
    seated.paste((0, 0, 0, 0), (0, frame.height // 2, frame.width, frame.height))
    lower = lower.resize((lower.width, max(10, lower.height // 2)), Image.Resampling.NEAREST)
    seated.alpha_composite(lower, (0, frame.height - lower.height))
    return seated


def build_talk_variant(frame: Image.Image) -> Image.Image:
    talk = frame.copy()
    d = ImageDraw.Draw(talk)
    x = int(talk.width * 0.72)
    y = int(talk.height * 0.30)
    d.rectangle((x, y - 8, x + 8, y + 6), fill=rgba('#f2c4a1'))
    d.rectangle((x + 4, y - 12, x + 12, y + 2), fill=rgba('#f2c4a1'))
    return talk


def upscale_strip(strip: Image.Image) -> Image.Image:
    return strip.resize((strip.width * 2, strip.height * 2), Image.Resampling.NEAREST)


def build_agent_strip(sheet_path: Path) -> Image.Image:
    sheet = Image.open(sheet_path).convert('RGBA')
    front = crop_frame(sheet, 'front')
    left = crop_frame(sheet, 'left')
    right = crop_frame(sheet, 'right')
    seated = build_seated_variant(front)
    talk = build_talk_variant(front)
    frames = [front, left, right, seated, talk]
    frame_w, frame_h = front.size
    strip = Image.new('RGBA', (frame_w * len(frames), frame_h), (0, 0, 0, 0))
    for i, frame in enumerate(frames):
        strip.alpha_composite(frame, (i * frame_w, 0))
    return upscale_strip(strip)


def text_width(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    return int(draw.textlength(text, font=font))


def pill(draw: ImageDraw.ImageDraw, x1, y1, x2, y2, text, fill, fg='#f8fafc'):
    draw.rounded_rectangle((x1, y1, x2, y2), radius=10, fill=fill, outline=rgba('#ffffff', 40), width=1)
    tw = text_width(draw, text, FONT_XS)
    draw.text((x1 + (x2 - x1 - tw) / 2, y1 + 5), text, fill=rgba(fg), font=FONT_XS)


def draw_floor(draw: ImageDraw.ImageDraw, mode: str, width: int, height: int, tile: int = 16):
    c1 = rgba(PALETTE['day_floor_a'] if mode == 'day' else PALETTE['night_floor_a'])
    c2 = rgba(PALETTE['day_floor_b'] if mode == 'day' else PALETTE['night_floor_b'])
    for y in range(0, height, tile):
        for x in range(0, width, tile):
            fill = c1 if ((x // tile) + (y // tile)) % 2 == 0 else c2
            draw.rectangle((x, y, x + tile - 1, y + tile - 1), fill=fill)


def draw_panel(draw, rect, fill, outline='#243043'):
    x1, y1, x2, y2 = rect
    draw.rounded_rectangle(rect, radius=8, fill=rgba(fill), outline=rgba(outline), width=1)
    draw.line((x1 + 2, y1 + 2, x2 - 2, y1 + 2), fill=rgba('#ffffff', 20), width=1)


def draw_window(draw, rect, mode: str):
    fill = PALETTE['glass_day'] if mode == 'day' else PALETTE['glass_night']
    x1, y1, x2, y2 = rect
    draw_panel(draw, rect, fill, '#6fa7d8' if mode == 'day' else '#5675aa')
    draw.line((x1 + 2, (y1 + y2) // 2, x2 - 2, (y1 + y2) // 2), fill=rgba('#dff4ff', 140), width=1)
    draw.line(((x1 + x2) // 2, y1 + 2, (x1 + x2) // 2, y2 - 2), fill=rgba('#dff4ff', 140), width=1)
    if mode == 'night':
        draw.ellipse((x1 + 4, y1 + 4, x1 + 14, y1 + 14), fill=rgba('#f7e7a7', 210))


def draw_monitor(draw, x, y, mode: str):
    draw_panel(draw, (x, y, x + 18, y + 14), '#1b2330' if mode == 'day' else '#0f1621', '#4b617d')
    glow = '#7ad7ff' if mode == 'day' else '#6aa4ff'
    draw.rectangle((x + 3, y + 3, x + 15, y + 10), fill=rgba(glow, 220))
    draw.rectangle((x + 7, y + 14, x + 11, y + 18), fill=rgba('#2d3644'))


def draw_chair(draw, x, y, color='#51606f'):
    draw.rounded_rectangle((x, y, x + 14, y + 12), radius=4, fill=rgba(color), outline=rgba('#111827', 100), width=1)
    draw.rectangle((x + 4, y + 12, x + 10, y + 16), fill=rgba(color))


def draw_plant(draw, x, y, mode: str):
    draw.rounded_rectangle((x, y + 10, x + 12, y + 20), radius=3, fill=rgba('#9a6a44'), outline=rgba('#6d4526', 180), width=1)
    green = '#6bcf8b' if mode == 'day' else '#4ba36f'
    draw.ellipse((x - 2, y, x + 14, y + 14), fill=rgba(green), outline=rgba('#2a6f46', 120), width=1)


def draw_desk_cluster(draw, x, y, width=76, height=40, mode='day', monitors=2, chairs=True):
    draw_panel(draw, (x, y, x + width, y + height), PALETTE['wood'])
    draw.rectangle((x + 4, y + 4, x + width - 4, y + 10), fill=rgba('#d8b28a', 180))
    for i in range(monitors):
        mx = x + 10 + i * 24
        draw_monitor(draw, mx, y + 10, mode)
    if chairs:
        draw_chair(draw, x + 12, y + height - 4)
        if monitors > 1:
            draw_chair(draw, x + 38, y + height - 4)


def draw_sync_table(draw, x, y, w=104, h=48, mode='day'):
    draw_panel(draw, (x, y, x + w, y + h), '#c89a67' if mode == 'day' else '#93693f', '#6f4b2d')
    draw.rectangle((x + 6, y + 6, x + w - 6, y + h - 6), fill=rgba('#ddba8b' if mode == 'day' else '#a57b4f'))
    for off in (12, 42, 72):
        draw_chair(draw, x + off, y - 10, '#64748b')
        draw_chair(draw, x + off, y + h - 2, '#64748b')


def draw_review_rail(draw, x, y, mode='day'):
    draw_panel(draw, (x, y, x + 108, y + 26), '#dde5ef' if mode == 'day' else '#2a3649', '#4f647f')
    for off in (10, 36, 62, 88):
        draw_monitor(draw, x + off, y + 4, mode)


def draw_sofa(draw, x, y, mode='day'):
    fill = '#6e8ab2' if mode == 'day' else '#475d7d'
    draw.rounded_rectangle((x, y, x + 42, y + 16), radius=6, fill=rgba(fill), outline=rgba('#243043'), width=1)
    draw.rounded_rectangle((x + 2, y - 6, x + 40, y + 4), radius=5, fill=rgba(fill), outline=rgba('#243043'), width=1)


def draw_board(draw, x, y, mode='day'):
    draw_panel(draw, (x, y, x + 94, y + 44), '#f5f0e1' if mode == 'day' else '#3d4556', '#8e7d64')
    colors = ['#64748b', '#14b8a6', '#f59e0b', '#22c55e']
    labels = ['Ready', 'Doing', 'Check', 'Done']
    xx = x + 6
    for color, label_text in zip(colors, labels):
        draw.rounded_rectangle((xx, y + 10, xx + 18, y + 28), radius=4, fill=rgba(color), outline=rgba('#111827', 60), width=1)
        draw.text((xx - 1, y + 31), label_text[0], fill=rgba('#475569' if mode == 'day' else '#e2e8f0'), font=FONT_XS)
        xx += 22


def draw_coffee_bar(draw, x, y, mode='day'):
    draw_panel(draw, (x, y, x + 54, y + 24), '#8f6b45', '#55351b')
    draw.rectangle((x + 8, y + 6, x + 20, y + 18), fill=rgba('#d2d6de'))
    draw.rectangle((x + 28, y + 6, x + 40, y + 18), fill=rgba('#d2d6de'))
    draw_plant(draw, x + 44, y - 4, mode)


def make_office_layout(mode: str) -> tuple[Image.Image, Image.Image]:
    width, height = 640, 384
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_floor(draw, mode, width, height)

    wall = '#f0f2f7' if mode == 'day' else '#1b2231'
    draw.rectangle((0, 0, width, 32), fill=rgba(wall))
    draw.rectangle((0, 0, 18, height), fill=rgba(wall))
    draw.rectangle((622, 0, 640, height), fill=rgba(wall))

    # windows
    draw_window(draw, (24, 8, 88, 28), mode)
    draw_window(draw, (98, 8, 162, 28), mode)
    draw_window(draw, (478, 8, 542, 28), mode)
    draw_window(draw, (552, 8, 616, 28), mode)

    # zones
    draw_board(draw, 273, 42, mode)
    draw_sync_table(draw, 268, 98, 104, 48, mode)

    # engineering desks left upper
    draw_desk_cluster(draw, 58, 90, mode=mode)
    draw_desk_cluster(draw, 58, 160, mode=mode)
    # research right upper
    draw_desk_cluster(draw, 470, 90, mode=mode)
    draw_desk_cluster(draw, 470, 160, mode=mode)
    # ops lower left
    draw_desk_cluster(draw, 58, 250, mode=mode)
    draw_desk_cluster(draw, 58, 314, mode=mode)
    # review rail lower right mid
    draw_review_rail(draw, 440, 246, mode=mode)
    # studio row lower right
    draw_desk_cluster(draw, 476, 314, mode=mode)
    draw_desk_cluster(draw, 558, 314, width=62, mode=mode, monitors=1)
    # chief + ceo desks
    draw_desk_cluster(draw, 218, 314, width=78, mode=mode, monitors=2)
    draw_desk_cluster(draw, 302, 314, width=78, mode=mode, monitors=2)
    # lounge
    draw_sofa(draw, 212, 248, mode=mode)
    draw_sofa(draw, 264, 248, mode=mode)
    draw_coffee_bar(draw, 326, 248, mode=mode)

    # plants and decor
    for pos in [(38, 54), (182, 54), (420, 54), (602, 54), (610, 292), (398, 320)]:
        draw_plant(draw, pos[0], pos[1], mode)

    if mode == 'night':
        tint = Image.new('RGBA', (width, height), rgba('#08111e', 96))
        img.alpha_composite(tint)
        glow = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        for rect in [(268, 98, 372, 146), (440, 246, 548, 272), (58, 90, 134, 130), (470, 90, 546, 130)]:
            x1, y1, x2, y2 = rect
            gd.rounded_rectangle((x1 - 6, y1 - 6, x2 + 6, y2 + 6), radius=14, fill=rgba('#6ba8ff', 24))
        img.alpha_composite(glow)

    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    fill = rgba('#09111a', 196) if mode == 'night' else rgba('#f8fafc', 210)
    fg = '#f8fafc' if mode == 'night' else '#172031'
    pill(od, 266, 34, 374, 54, 'BOARD WALL', fill, fg)
    pill(od, 258, 78, 382, 98, 'SYNC TABLE', fill, fg)
    pill(od, 44, 68, 150, 88, 'ENGINEERING', fill, fg)
    pill(od, 456, 68, 572, 88, 'RESEARCH', fill, fg)
    pill(od, 40, 228, 150, 248, 'OPS / SEC', fill, fg)
    pill(od, 434, 226, 554, 246, 'REVIEW', fill, fg)
    pill(od, 470, 292, 620, 312, 'DOCS / DESIGN', fill, fg)
    pill(od, 210, 292, 390, 312, 'CHIEF + CEO', fill, fg)
    pill(od, 214, 228, 352, 248, 'LOUNGE', fill, fg)
    return img, overlay


def save_texture_set(mode: str, office: Image.Image, overlay: Image.Image) -> None:
    names = [f'office_map_{mode}_32bit.png', f'office_overlay_{mode}_32bit.png']
    for base in (WEB_ASSETS, UI_PUBLIC):
        (base / 'textures').mkdir(parents=True, exist_ok=True)
        office.save(base / 'textures' / names[0])
        overlay.save(base / 'textures' / names[1])
        if mode == 'day':
            office.save(base / 'textures' / 'office_map_32bit.png')
            office.resize((320, 192), Image.Resampling.NEAREST).save(base / 'textures' / 'office_map_16bit_thumb.png')
            office.save(base / 'textures' / 'office_map_16bit.png')
            overlay.save(base / 'textures' / 'office_overlay_32bit.png')
    compat = VENDOR / 'compat'
    office.save(compat / f'office-layout-{mode}.png')
    overlay.save(compat / f'office-overlay-{mode}.png')


def sync_asset_copies() -> str:
    vendor_assets = VENDOR / 'assets' / 'avatars'
    for agent_id, avatar_key in AGENT_MAP.items():
        portrait_src = vendor_assets / f'{avatar_key}-portrait.png'
        sheet_src = vendor_assets / f'{avatar_key}-sheet.png'
        portrait = Image.open(portrait_src).convert('RGBA')
        strip = build_agent_strip(sheet_src)
        for base in (WEB_ASSETS, UI_PUBLIC):
            (base / 'portraits').mkdir(parents=True, exist_ok=True)
            (base / 'sprites').mkdir(parents=True, exist_ok=True)
            portrait.save(base / 'portraits' / f'{agent_id}.png')
            strip.save(base / 'sprites' / f'{agent_id}.png')

    for mode in ('day', 'night'):
        office, overlay = make_office_layout(mode)
        save_texture_set(mode, office, overlay)

    vendor_target = UI_PUBLIC / 'vendor' / 'pocket-office-quest-v9'
    if vendor_target.exists():
        shutil.rmtree(vendor_target)
    shutil.copytree(VENDOR, vendor_target)
    return 'generated-day-night-layouts'


def build_office_scene(mode='day', size=(1280, 768)) -> Image.Image:
    base = Image.open(UI_PUBLIC / 'textures' / f'office_map_{mode}_32bit.png').convert('RGBA').resize(size, Image.Resampling.NEAREST)
    overlay = Image.open(UI_PUBLIC / 'textures' / f'office_overlay_{mode}_32bit.png').convert('RGBA').resize(size, Image.Resampling.NEAREST)
    scene = Image.new('RGBA', size, (0, 0, 0, 0))
    scene.alpha_composite(base)
    scene.alpha_composite(overlay)
    return scene


def sprite_strip(agent_id: str) -> Image.Image:
    return Image.open(UI_PUBLIC / 'sprites' / f'{agent_id}.png').convert('RGBA')


def sprite_frame(agent_id: str, frame_idx: int) -> Image.Image:
    strip = sprite_strip(agent_id)
    cell_w = strip.width // 5
    return strip.crop((frame_idx * cell_w, 0, frame_idx * cell_w + cell_w, strip.height))


def portrait_img(agent_id: str) -> Image.Image:
    return Image.open(UI_PUBLIC / 'portraits' / f'{agent_id}.png').convert('RGBA')


def label(draw: ImageDraw.ImageDraw, xy, text, fill='#0f172a', fg='#f8fafc', font=FONT_XS):
    x, y = xy
    tw = text_width(draw, text, font)
    w = max(64, tw + 16)
    draw.rounded_rectangle((x - w // 2, y, x + w // 2, y + 20), radius=10, fill=rgba(fill, 236), outline=rgba('#ffffff', 30), width=1)
    draw.text((x - tw / 2, y + 4), text, fill=rgba(fg), font=font)


def render_office_preview(mode='day') -> None:
    office = build_office_scene(mode)
    d = ImageDraw.Draw(office)
    counters = [('Ready', 4, '#64748b'), ('Doing', 3, '#14b8a6'), ('Validation', 1, '#f59e0b'), ('Done', 2, '#22c55e')]
    x = 42
    fill_base = '#09111a' if mode == 'night' else '#f8fafc'
    fg = '#f8fafc' if mode == 'night' else '#172031'
    for label_text, value, fill in counters:
        d.rounded_rectangle((x, 18, x + 118, 52), radius=16, fill=rgba(fill_base, 224), outline=rgba(fill), width=1)
        d.text((x + 14, 24), label_text, fill=rgba('#cbd5e1' if mode == 'night' else '#475569'), font=FONT_XS)
        d.text((x + 72, 22), str(value), fill=rgba(fg), font=FONT_M)
        x += 128
    label(d, (1150, 20), f'{mode.title()} office', fill='#111827' if mode == 'night' else '#ffffff', fg='#f8fafc' if mode == 'night' else '#172031')

    for agent_id, (zone, index) in OFFICE_ASSIGNMENTS.items():
        slot = OFFICE_SLOTS[zone][index]
        status = AGENTS[agent_id]['status']
        frame_index = 3 if status == 'Working' and zone not in {'scrum_table', 'review_rail'} else 4 if zone in {'scrum_table', 'review_rail'} or status == 'Sync' else 0
        sprite = sprite_frame(agent_id if agent_id != 'ceo' else 'orion', frame_index)
        office.alpha_composite(sprite, (slot['x'] - sprite.width // 2, slot['y'] - sprite.height))
        label(d, (slot['x'], slot['y'] - sprite.height - 24), status, fill=STATUS_COLORS.get(status, '#0f172a'))
        label(d, (slot['x'], slot['y'] - 22), AGENTS[agent_id]['name'], fill='#ffffff' if mode == 'day' else '#0f172a', fg='#172031' if mode == 'day' else '#f8fafc')

    office.save(DOCS / (f'render_office_{mode}_v{VTAG}.png' if mode == 'night' else f'render_office_v{VTAG}.png'))


def render_office_floor() -> None:
    day = build_office_scene('day', size=(800, 480))
    night = build_office_scene('night', size=(800, 480))
    floor = Image.new('RGBA', (1660, 1090), rgba(PALETTE['bg']))
    d = ImageDraw.Draw(floor)
    d.text((42, 30), 'ClawTasker Office day / night layouts', fill=rgba(PALETTE['text']), font=FONT_XL)
    d.text((44, 66), 'Pocket Office Quest v9 characters + generated day/night office maps + deterministic seat anchors.', fill=rgba(PALETTE['muted']), font=FONT_S)
    floor.alpha_composite(day, (32, 110))
    floor.alpha_composite(night, (828, 110))
    label(d, (420, 120), 'DAY', fill='#ffffff', fg='#172031')
    label(d, (1210, 120), 'NIGHT', fill='#111827', fg='#f8fafc')
    floor.save(DOCS / f'render_office_floor_v{VTAG}.png')


def render_avatar_roster() -> None:
    agents = [aid for aid in AGENTS.keys() if aid != 'ceo']
    cols = 2
    card_w = 860
    card_h = 268
    rows = (len(agents) + cols - 1) // cols
    canvas = Image.new('RGBA', (cols * card_w + 120, rows * card_h + 184), rgba(PALETTE['bg']))
    d = ImageDraw.Draw(canvas)
    d.text((40, 28), 'Pocket Office Quest v9 - agent roster', fill=rgba(PALETTE['text']), font=FONT_XL)
    d.text((42, 66), 'Visible-face portrait cards, hero body poses, and directional rows generated from the supplied v9 character sheets.', fill=rgba(PALETTE['muted']), font=FONT_S)

    for idx, aid in enumerate(agents):
        row, col = divmod(idx, cols)
        x = 40 + col * card_w
        y = 112 + row * card_h
        d.rounded_rectangle((x, y, x + card_w - 28, y + card_h - 24), radius=24, fill=rgba(PALETTE['cardbg']), outline=rgba(PALETTE['border']), width=1)
        portrait_bg = Image.new('RGBA', (172, 196), rgba('#e8eef8'))
        d_bg = ImageDraw.Draw(portrait_bg)
        d_bg.rounded_rectangle((0, 0, 171, 195), radius=18, fill=rgba('#e8eef8'), outline=rgba('#c8d3e6'), width=2)
        portrait = portrait_img(aid).resize((138, 138), Image.Resampling.NEAREST)
        portrait_bg.alpha_composite(portrait, (17, 10))
        d_bg.rounded_rectangle((18, 152, 154, 182), radius=14, fill=rgba('#c7d2df'), outline=rgba('#92a1b5', 150), width=1)
        tw = text_width(d_bg, AGENTS[aid]['name'].upper(), FONT_XS)
        d_bg.text(((172 - tw) / 2, 161), AGENTS[aid]['name'].upper(), fill=rgba('#1f2937'), font=FONT_XS)
        canvas.alpha_composite(portrait_bg, (x + 20, y + 18))

        d.text((x + 210, y + 24), AGENTS[aid]['name'].upper(), fill=rgba(PALETTE['text']), font=FONT_L)
        d.text((x + 210, y + 56), AGENTS[aid]['role'], fill=rgba(PALETTE['accent2']), font=FONT_S)
        d.text((x + 210, y + 74), AGENTS[aid]['specialist'].title(), fill=rgba('#94a3b8'), font=FONT_XS)
        hero = sprite_frame(aid, 0).resize((144, 192), Image.Resampling.NEAREST)
        canvas.alpha_composite(hero, (x + 214, y + 88))
        d.text((x + 246, y + 230), 'Hero/front', fill=rgba('#b6c3d8'), font=FONT_XS)
        d.text((x + 386, y + 84), 'Directional poses', fill=rgba('#b6c3d8'), font=FONT_XS)
        for off, (img, label_text) in enumerate(zip([sprite_frame(aid, 1), sprite_frame(aid, 2), sprite_frame(aid, 3), sprite_frame(aid, 4)], ['Left', 'Right', 'Seated', 'Talk'])):
            pose = img.resize((96, 128), Image.Resampling.NEAREST)
            px = x + 382 + off * 108
            d.rounded_rectangle((px - 8, y + 102, px + 88, y + 230), radius=16, fill=rgba('#101621'), outline=rgba('#25314b'), width=1)
            canvas.alpha_composite(pose, (px, y + 110))
            d.text((px + 10, y + 232), label_text, fill=rgba('#8fa2b8'), font=FONT_XS)

    canvas.save(DOCS / f'render_avatars_v{VTAG}.png')


def render_team() -> None:
    team = Image.new('RGBA', (1680, 1160), rgba(PALETTE['bg']))
    d = ImageDraw.Draw(team)
    d.text((40, 30), 'Organisation chart', fill=rgba(PALETTE['text']), font=FONT_XL)
    d.text((42, 68), 'CEO -> chief agent -> manager lanes -> specialist teams using the Pocket Office Quest v9 roster family.', fill=rgba(PALETTE['muted']), font=FONT_S)

    def card(x, y, w, h, aid, extra=''):
        d.rounded_rectangle((x, y, x + w, y + h), radius=22, fill=rgba(PALETTE['panel']), outline=rgba(PALETTE['border']), width=1)
        portrait = portrait_img(aid if aid != 'ceo' else 'ceo').resize((96, 96), Image.Resampling.NEAREST)
        team.alpha_composite(portrait, (x + 22, y + 22))
        d.text((x + 136, y + 28), AGENTS[aid]['name'], fill=rgba(PALETTE['text']), font=FONT_L)
        d.text((x + 138, y + 60), AGENTS[aid]['role'], fill=rgba(PALETTE['muted']), font=FONT_S)
        d.text((x + 138, y + 88), AGENTS[aid]['specialist'].title(), fill=rgba('#14b8a6'), font=FONT_XS)
        if extra:
            d.text((x + 138, y + 114), extra, fill=rgba('#94a3b8'), font=FONT_XS)

    def team_box(x, y, w, h, manager_id, title, reports):
        d.rounded_rectangle((x, y, x + w, y + h), radius=24, fill=rgba('#151923'), outline=rgba(PALETTE['border']), width=1)
        card(x + 16, y + 16, w - 32, 138, manager_id, title)
        d.text((x + 24, y + 172), 'Direct reports', fill=rgba(PALETTE['muted']), font=FONT_XS)
        cx = x + 24
        cy = y + 200
        for idx, aid in enumerate(reports):
            box_w = 168
            d.rounded_rectangle((cx, cy, cx + box_w, cy + 98), radius=18, fill=rgba(PALETTE['panel']), outline=rgba(PALETTE['border']), width=1)
            portrait = portrait_img(aid).resize((58, 58), Image.Resampling.NEAREST)
            team.alpha_composite(portrait, (cx + 14, cy + 18))
            d.text((cx + 84, cy + 20), AGENTS[aid]['name'], fill=rgba(PALETTE['text']), font=FONT_M)
            d.text((cx + 84, cy + 46), AGENTS[aid]['role'], fill=rgba(PALETTE['muted']), font=FONT_XS)
            d.text((cx + 84, cy + 66), AGENTS[aid]['status'], fill=rgba('#94a3b8'), font=FONT_XS)
            cx += box_w + 14
            if (idx + 1) % 2 == 0:
                cx = x + 24
                cy += 110

    card(60, 118, 420, 150, 'ceo', 'Sets priorities, approvals, and company constraints.')
    card(560, 118, 480, 150, 'orion', 'Coordinates cross-team exceptions and keeps managers aligned.')
    team_box(40, 320, 360, 350, 'codex', 'Coordinates Engineering & Product', ['ralph', 'pixel'])
    team_box(420, 320, 360, 350, 'violet', 'Coordinates Research & Intelligence', ['scout', 'echo', 'mercury'])
    team_box(800, 320, 360, 350, 'charlie', 'Coordinates Operations & Security', ['shield', 'ledger'])
    team_box(1180, 320, 360, 350, 'quill', 'Coordinates People & Communications', ['iris'])
    team.save(DOCS / f'render_team_v{VTAG}.png')


def render_palette() -> None:
    canvas = Image.new('RGBA', (1260, 420), rgba(PALETTE['bg']))
    d = ImageDraw.Draw(canvas)
    d.text((34, 28), 'CEO Console default palette + Pocket Office v9 office scenes', fill=rgba(PALETTE['text']), font=FONT_XL)
    d.text((36, 66), 'The shell boots into the CEO Console dark preset by default while keeping OpenClaw-style structure, and the office adds readable day/night scene variants for the same roster.', fill=rgba(PALETTE['muted']), font=FONT_S)
    swatches = [
        ('CEO BG', PALETTE['bg']), ('Panel', PALETTE['panel']), ('Border', PALETTE['border']), ('Accent', PALETTE['accent']), ('Accent 2', PALETTE['accent2']),
        ('Light BG', '#eff5ff'), ('Day floor', PALETTE['day_floor_a']), ('Night floor', PALETTE['night_floor_a']), ('Window day', PALETTE['glass_day']), ('Window night', PALETTE['glass_night']),
    ]
    x = 34
    y = 116
    for i, (name, col) in enumerate(swatches):
        d.rounded_rectangle((x, y, x + 104, y + 104), radius=18, fill=rgba(col), outline=rgba('#ffffff', 20), width=1)
        d.text((x, y + 112), name, fill=rgba(PALETTE['text']), font=FONT_XS)
        d.text((x, y + 128), col.upper(), fill=rgba(PALETTE['dim']), font=FONT_XS)
        x += 118
        if i == 4:
            x = 34
            y += 176
    canvas.save(DOCS / f'render_palette_v{VTAG}.png')


def render_app_layout() -> None:
    """Dashboard view — v1.0.5: sprint card, notification bell, mission brief, workload."""
    W, H = 1600, 1000
    shell = Image.new('RGBA', (W, H), rgba('#061224'))
    d = ImageDraw.Draw(shell)

    def panel(rect, fill='#0b1931', outline='#183154'):
        d.rounded_rectangle(rect, radius=22, fill=rgba(fill), outline=rgba(outline, 235), width=1)
        x1, y1, x2, y2 = rect
        d.line((x1 + 18, y1 + 1, x2 - 18, y1 + 1), fill=rgba('#ffffff', 20), width=1)

    def pill_box(rect, fill='#122744', outline='#24456e', label='', fg='#d9e7f8'):
        d.rounded_rectangle(rect, radius=14, fill=rgba(fill), outline=rgba(outline, 225), width=1)
        if label:
            d.text((rect[0] + 12, rect[1] + 9), label, fill=rgba(fg), font=FONT_XS)

    def metric_card(x1, y1, label, value, color='#f7fbff', glow=None):
        d.rounded_rectangle((x1, y1, x1 + 188, y1 + 88), radius=18,
                             fill=rgba('#173154', 180), outline=rgba('#2d527c', 200), width=1)
        if glow:
            d.rounded_rectangle((x1 + 4, y1 + 4, x1 + 184, y1 + 84), radius=16,
                                 fill=rgba(glow, 14), outline=rgba(glow, 0), width=0)
        d.text((x1 + 16, y1 + 14), label, fill=rgba('#8fa6c1'), font=FONT_XS)
        d.text((x1 + 16, y1 + 40), value, fill=rgba(color), font=FONT_L)

    # glows
    d.ellipse((-120, -120, 480, 360), fill=rgba('#67e8d7', 22))
    d.ellipse((1160, -140, 1710, 310), fill=rgba('#77b9ff', 24))

    # ── sidebar ────────────────────────────────────────────────────────────
    panel((16, 16, 316, 984), fill='#071426', outline='#173154')
    d.rounded_rectangle((32, 32, 84, 84), radius=16, fill=rgba('#102744'), outline=rgba('#67e8d7', 160), width=1)
    d.text((96, 34), 'CEO CONSOLE', fill=rgba('#8fa6c1'), font=FONT_XS)
    d.text((96, 54), 'ClawTasker', fill=rgba('#f7fbff'), font=FONT_L)
    d.text((96, 80), 'Human-first control room', fill=rgba('#b9cde4'), font=FONT_XS)

    groups = [
        ('OPERATE',  ['Dashboard', 'Team', 'Calendar'], 'Dashboard'),
        ('WORK',     ['Board', 'Backlog', 'Approvals', 'Conversations'], None),
        ('OBSERVE',  ['Office', 'Runs', 'Access'], None),
    ]
    y = 128
    for group, items, active_item in groups:
        panel((28, y, 304, y + 32 + len(items) * 44), fill='#0a1830', outline='#173154')
        d.text((44, y + 12), group, fill=rgba('#8fa6c1'), font=FONT_XS)
        yy = y + 38
        for item in items:
            active = item == active_item
            bg = rgba('#142948') if active else rgba('#10213b', 200)
            d.rounded_rectangle((40, yy - 4, 292, yy + 30), radius=12, fill=bg,
                                 outline=rgba('#67e8d7', 160 if active else 0), width=1 if active else 0)
            d.ellipse((54, yy + 6, 64, yy + 16), fill=rgba('#67e8d7' if active else '#7b93af'))
            d.text((78, yy + 2), item, fill=rgba('#f7fbff' if active else '#d4e2f2'), font=FONT_M)
            yy += 42
        y += 40 + len(items) * 42 + 14

    panel((28, 722, 304, 830), fill='#0a1830', outline='#173154')
    d.text((44, 738), 'SYNC CONTRACT', fill=rgba('#8fa6c1'), font=FONT_XS)
    d.text((44, 760), 'Fast chief / specialist alignment', fill=rgba('#f7fbff'), font=FONT_XS)
    for i, line in enumerate(['Chief routes by exception.', 'Specialists update tasks directly.', 'Office mirrors task activity.']):
        d.text((54, 790 + i * 18), '•', fill=rgba('#67e8d7'), font=FONT_XS)
        d.text((68, 790 + i * 18), line, fill=rgba('#b9cde4'), font=FONT_XS)

    pill_box((28, 848, 148, 878), fill='#102744', outline='#24456e', label='Set token')
    pill_box((156, 848, 304, 878), fill='#1a3a20', outline='#2e6b3a', label='New directive', fg='#86efac')
    pill_box((28, 892, 304, 924), fill='#102744', outline='#24456e', label='Appearance — CEO Console dark', fg='#d9e7f8')

    # ── topbar ─────────────────────────────────────────────────────────────
    panel((332, 16, 1584, 108), fill='#07172c', outline='#183154')
    d.text((354, 30), 'DASHBOARD', fill=rgba('#8fa6c1'), font=FONT_XS)
    d.text((354, 52), 'CEO Command Center', fill=rgba('#f7fbff'), font=FONT_L)
    d.text((354, 80), 'v1.0.5 · Sprint tracking · Dependencies · Notifications · Project types', fill=rgba('#b9cde4'), font=FONT_XS)
    # live pill
    pill_box((1330, 34, 1480, 68), fill='#123a57', outline='#67e8d7', label='● Live snapshot', fg='#67e8d7')
    # notification bell
    d.rounded_rectangle((1494, 34, 1544, 68), radius=10, fill=rgba('#1c2f4a'), outline=rgba('#24456e'), width=1)
    d.text((1505, 44), '🔔', fill=rgba('#f7fbff'), font=FONT_M)
    d.ellipse((1530, 30, 1548, 48), fill=rgba('#ef4444'))
    d.text((1534, 32), '3', fill=rgba('#f8fafc'), font=FONT_XS)

    # ── row 1: metric cards ─────────────────────────────────────────────────
    metric_cards = [
        ('Done',        '2 / 15',   '#14b8a6', '#14b8a6'),
        ('Blocked',     '1',        '#ef4444', '#ef4444'),
        ('Validation',  '1',        '#f59e0b', '#f59e0b'),
        ('Active agents','10 / 14', '#f7fbff', None),
        ('Overloaded',  '1 agent',  '#f59e0b', '#f59e0b'),
        ('Sprint pts',  '12 / 34',  '#77b9ff', '#77b9ff'),
    ]
    mx = 354
    for i, (label, value, color, glow) in enumerate(metric_cards):
        metric_card(mx + i * 204, 124, label, value, color, glow)

    # ── Active sprint card ──────────────────────────────────────────────────
    panel((354, 228, 758, 340), fill='#0b1a31', outline='#1c3860')
    d.text((376, 244), 'ACTIVE SPRINT', fill=rgba('#8fa6c1'), font=FONT_XS)
    pill_box((800, 240, 924, 268), fill='#1a3a20', outline='#2e6b3a', label='Sprint Alpha', fg='#86efac')
    d.text((376, 266), 'Sprint Alpha  •  Mar 17–28', fill=rgba('#f7fbff'), font=FONT_M)
    d.text((376, 292), 'Goal: ship sprint/dependency/notification features', fill=rgba('#b9cde4'), font=FONT_XS)
    # burndown bar
    d.rounded_rectangle((376, 314, 728, 330), radius=4, fill=rgba('#10213b'), outline=rgba('#24456e'), width=1)
    d.rounded_rectangle((376, 314, 376 + int(352 * 0.35), 330), radius=4, fill=rgba('#14b8a6'), outline=rgba('#0d9488'), width=0)
    d.text((736, 316), '12 / 34 pts', fill=rgba('#67e8d7'), font=FONT_XS)

    # ── Mission brief ───────────────────────────────────────────────────────
    panel((776, 228, 1178, 340), fill='#0b1a31', outline='#1c3860')
    d.text((798, 244), 'MISSION BRIEF', fill=rgba('#8fa6c1'), font=FONT_XS)
    pill_box((1036, 240, 1160, 268), fill='#102744', outline='#24456e', label='100% staffed', fg='#86efac')
    d.text((798, 266), 'CEO Console v1.0.5 Release', fill=rgba('#f7fbff'), font=FONT_M)
    d.text((798, 292), 'Ship sprint, dependency, notification, and directive features.', fill=rgba('#b9cde4'), font=FONT_XS)
    d.rounded_rectangle((798, 314, 1148, 330), radius=4, fill=rgba('#10213b'), outline=rgba('#24456e'), width=1)
    d.rounded_rectangle((798, 314, 798 + int(350 * 0.73), 330), radius=4, fill=rgba('#77b9ff'), outline=rgba('#5b8fd4'), width=0)
    d.text((1052, 316), '73% done', fill=rgba('#77b9ff'), font=FONT_XS)

    # ── Risk / dependency radar ─────────────────────────────────────────────
    panel((1196, 228, 1584, 340), fill='#0b1a31', outline='#1c3860')
    d.text((1218, 244), 'RISK & DEPENDENCY RADAR', fill=rgba('#8fa6c1'), font=FONT_XS)
    risks = [('Deploy secret missing', 'critical', '#ef4444'),
             ('Validator not assigned', 'high', '#f59e0b')]
    yy = 268
    for risk_text, sev, col in risks:
        pill_box((1218, yy, 1218 + 60, yy + 22), fill=col, outline=col, label=sev, fg='#f8fafc')
        d.text((1288, yy + 4), risk_text, fill=rgba('#f7fbff'), font=FONT_XS)
        yy += 30
    d.text((1218, 316), '⛓  T-209 blocks T-211', fill=rgba('#8fa6c1'), font=FONT_XS)

    # ── Attention queue ─────────────────────────────────────────────────────
    panel((354, 356, 960, 660), fill='#0b1a31', outline='#1c3860')
    d.text((376, 372), 'ATTENTION QUEUE', fill=rgba('#8fa6c1'), font=FONT_XS)
    pill_box((1788, 368, 1916, 396), fill='#3b1f2d', outline='#61435a', label='Exception-only', fg='#f7fbff')
    queue = [
        ('Validation',       'Approval queue & validation rail',    'Ralph · T-201', 'CEO sign-off pending.',           '#6d5127'),
        ('Routing mismatch', 'Noon trend radar',                    'Scout · T-207', 'Best fit: Violet.',               '#4d304d'),
        ('Blocked',          'GitHub push workflow hardening',       'Charlie · T-209','Deploy secret missing.',          '#5a2631'),
        ('Overloaded',       'Orion has 5 active tasks',             'Orion',         'Threshold: >4 active tasks.',     '#7c4b1a'),
    ]
    yy = 402
    for badge, title, meta, note, fill in queue:
        d.rounded_rectangle((376, yy, 936, yy + 58), radius=14, fill=rgba('#10213b'), outline=rgba('#24456e', 220), width=1)
        pill_box((388, yy + 10, 388 + len(badge) * 8 + 16, yy + 36), fill=fill, outline=fill, label=badge, fg='#f7fbff')
        d.text((388 + len(badge) * 8 + 28, yy + 14), title, fill=rgba('#f7fbff'), font=FONT_M)
        d.text((388, yy + 40), f'{meta}  •  {note}', fill=rgba('#8fa6c1'), font=FONT_XS)
        yy += 68

    # ── Specialist load ─────────────────────────────────────────────────────
    panel((978, 356, 1584, 510), fill='#0b1a31', outline='#1c3860')
    d.text((1000, 372), 'SPECIALIST LOAD', fill=rgba('#8fa6c1'), font=FONT_XS)
    specs = [('Code','1A 0B'), ('Design','1A 0B'), ('QA','0A 1V'), ('Ops','1A 1B'),
             ('Research','2A 0B'),('Docs','1A 0B'),('Security','0A 0B'),('Media','1A 0B')]
    sx, sy = 1000, 404
    for i, (name, counts) in enumerate(specs):
        col, row = i % 4, i // 4
        x1 = sx + col * 144
        y1 = sy + row * 50
        d.rounded_rectangle((x1, y1, x1 + 132, y1 + 38), radius=10,
                             fill=rgba('#10213b'), outline=rgba('#24456e', 220), width=1)
        d.text((x1 + 10, y1 + 6), name, fill=rgba('#f7fbff'), font=FONT_XS)
        d.text((x1 + 10, y1 + 22), counts, fill=rgba('#8fa6c1'), font=FONT_XS)

    # ── Projects ────────────────────────────────────────────────────────────
    panel((978, 526, 1584, 660), fill='#0b1a31', outline='#1c3860')
    d.text((1000, 542), 'PROJECTS', fill=rgba('#8fa6c1'), font=FONT_XS)
    projects = [('Atlas Core', 'software', '#67e8d7'),
                ('Market Radar', 'business', '#77b9ff'),
                ('CEO Console', 'software', '#67e8d7')]
    yy = 568
    for name, ptype, col in projects:
        d.rounded_rectangle((1000, yy, 1564, yy + 26), radius=8,
                             fill=rgba('#10213b'), outline=rgba('#24456e', 220), width=1)
        d.text((1014, yy + 6), name, fill=rgba('#f7fbff'), font=FONT_XS)
        pill_box((1416, yy + 4, 1416 + 60, yy + 22), fill='#0f2a40', outline='#24456e', label=ptype, fg=col)
        yy += 30

    # ── System health ───────────────────────────────────────────────────────
    panel((354, 676, 960, 780), fill='#0b1a31', outline='#1c3860')
    d.text((376, 692), 'SYSTEM HEALTH', fill=rgba('#8fa6c1'), font=FONT_XS)
    health = [('Server','ok','#14b8a6'),('SSE stream','ok','#14b8a6'),('State file','ok','#14b8a6'),('OpenClaw','reachable','#f59e0b')]
    hx = 376
    for label, status, col in health:
        d.text((hx, 718), label, fill=rgba('#8fa6c1'), font=FONT_XS)
        pill_box((hx, 736, hx + len(status)*8+16, 758), fill='#0f2a1e' if col=='#14b8a6' else '#2d1f0a',
                 outline=col, label=status, fg=col)
        hx += 148

    # ── Mission feed ────────────────────────────────────────────────────────
    panel((978, 676, 1584, 780), fill='#0b1a31', outline='#1c3860')
    d.text((1000, 692), 'MISSION FEED', fill=rgba('#8fa6c1'), font=FONT_XS)
    feed = [('✓ Directive sent', 'Orion → fix deploy secret on T-209', '#1a3a20', '#86efac'),
            ('⛓ Dep cleared',  'T-208 unblocked after T-204 done',   '#102044', '#77b9ff'),
            ('● Briefing',     'Violet started 8AM AI market briefing','#1e4664', '#f7fbff')]
    yy = 716
    for badge, note, fill, fg in feed:
        d.rounded_rectangle((1000, yy, 1564, yy + 16), radius=6,
                             fill=rgba(fill), outline=rgba('#24456e', 180), width=1)
        d.text((1010, yy + 2), badge, fill=rgba(fg), font=FONT_XS)
        d.text((1010 + len(badge)*7+12, yy + 2), note, fill=rgba('#b9cde4'), font=FONT_XS)
        yy += 20

    # ── Recovery playbook ───────────────────────────────────────────────────
    panel((354, 796, 1584, 880), fill='#0b1a31', outline='#1c3860')
    d.text((376, 812), 'RECOVERY PLAYBOOK', fill=rgba('#8fa6c1'), font=FONT_XS)
    steps = ['1. python3 server.py', '2. Agents republish via /api/openclaw/publish', '3. Roster syncs via /api/openclaw/roster_sync', '4. State restores from state.backup.json']
    for i, step in enumerate(steps):
        d.text((376 + i * 300, 838), step, fill=rgba('#b9cde4'), font=FONT_XS)

    # ── Ticket system health ────────────────────────────────────────────────
    panel((354, 896, 1584, 968), fill='#0b1a31', outline='#1c3860')
    d.text((376, 912), 'TICKET SYSTEM HEALTH', fill=rgba('#8fa6c1'), font=FONT_XS)
    ticks = [('15 tasks','#f7fbff'),('1 missing validator','#f59e0b'),('1 routing mismatch','#f59e0b'),('Dedupe window: 30s','#b9cde4'),('Last publish: 2m ago','#b9cde4')]
    tx = 376
    for label, col in ticks:
        d.text((tx, 936), label, fill=rgba(col), font=FONT_XS)
        tx += len(label) * 7 + 32

    shell.save(DOCS / f'render_app_layout_v{VTAG}.png')


def render_calendar_view() -> None:
    """Calendar view rendering — week tabs, always-running strip, agent day lanes."""
    W, H = 1600, 900
    img = Image.new('RGBA', (W, H), rgba('#061224'))
    d = ImageDraw.Draw(img)

    def panel(rect, fill='#0b1931', outline='#183154'):
        d.rounded_rectangle(rect, radius=16, fill=rgba(fill), outline=rgba(outline, 220), width=1)
        x1, y1, x2, y2 = rect
        d.line((x1 + 12, y1 + 1, x2 - 12, y1 + 1), fill=rgba('#ffffff', 18), width=1)

    # glows
    d.ellipse((-80, -80, 400, 300), fill=rgba('#67e8d7', 18))

    # sidebar (condensed)
    panel((16, 16, 200, 884), fill='#071426', outline='#173154')
    d.text((32, 32), 'CEO CONSOLE', fill=rgba('#8fa6c1'), font=FONT_XS)
    d.text((32, 52), 'ClawTasker', fill=rgba('#f7fbff'), font=FONT_M)
    nav = ['Dashboard', 'Team', 'Calendar', 'Board', 'Backlog', 'Approvals',
           'Conversations', 'Office', 'Runs', 'Access', 'Appearance']
    yy = 90
    for item in nav:
        active = item == 'Calendar'
        if active:
            d.rounded_rectangle((26, yy - 4, 190, yy + 24), radius=10,
                                 fill=rgba('#142948'), outline=rgba('#67e8d7', 160), width=1)
        d.text((40, yy), item, fill=rgba('#f7fbff' if active else '#8fa6c1'), font=FONT_XS)
        yy += 32

    # topbar
    panel((216, 16, 1580, 88), fill='#07172c', outline='#183154')
    d.text((236, 30), 'CALENDAR', fill=rgba('#8fa6c1'), font=FONT_XS)
    d.text((236, 52), 'Weekly schedule by agent', fill=rgba('#f7fbff'), font=FONT_L)

    # week tabs
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    tx = 236
    for day in days:
        active = day == 'Wed'
        bg = '#142948' if active else '#10213b'
        border = rgba('#67e8d7', 200) if active else rgba('#24456e', 180)
        d.rounded_rectangle((tx, 104, tx + 96, 136), radius=10,
                             fill=rgba(bg), outline=border, width=1)
        col = '#f7fbff' if active else '#8fa6c1'
        d.text((tx + 20, 113), day, fill=rgba(col), font=FONT_M)
        if active:
            d.text((tx + 56, 113), ' ◀ today', fill=rgba('#67e8d7'), font=FONT_XS)
        tx += 108

    # always-running strip
    panel((216, 148, 1580, 192), fill='#0a1a2c', outline='#173154')
    d.ellipse((230, 162, 242, 174), fill=rgba('#14b8a6'))
    d.text((250, 162), 'Always Running', fill=rgba('#f7fbff'), font=FONT_M)
    always = ['8AM Market briefing', 'Heartbeat monitor', 'Roster sync watchdog', 'Event log flush']
    ax = 420
    for a in always:
        d.rounded_rectangle((ax, 158, ax + len(a)*7+20, 182), radius=8,
                             fill=rgba('#102744'), outline=rgba('#24456e'), width=1)
        d.text((ax + 10, 164), a, fill=rgba('#b9cde4'), font=FONT_XS)
        ax += len(a)*7 + 32

    # agent lanes header
    panel((216, 202, 1580, 240), fill='#071a2e', outline='#173154')
    agents_col = ['Agent', 'Orion', 'Codex', 'Violet', 'Scout', 'Charlie', 'Ralph', 'Echo', 'Pixel', 'Quill', 'Shield']
    times = ['08:00', '10:00', '12:00', '14:00', '16:00', '18:00']
    d.text((230, 216), 'Agent', fill=rgba('#8fa6c1'), font=FONT_XS)
    for i, t in enumerate(times):
        d.text((420 + i * 188, 216), t, fill=rgba('#8fa6c1'), font=FONT_XS)

    # calendar event rows
    SPECIALIST_COLORS = {
        'planning': '#3b5998', 'code': '#1e6b4e', 'research': '#4b3a6e',
        'ops': '#7a4e1a', 'qa': '#5c2a3a', 'distribution': '#2a4b5c',
        'design': '#4a2a6e', 'docs': '#2a4a3c', 'security': '#5c3a2a', 'media': '#3a3a5c',
    }
    events = [
        ('Orion',   'planning', '08:00', 'Sprint planning + task routing review', 240, 560),
        ('Codex',   'code',     '10:00', 'CEO Console backend hardening',          420, 420),
        ('Violet',  'research', '08:00', 'AI market signal briefing',              240, 280),
        ('Violet',  'research', '10:00', 'Competitor analysis review',             420, 280),
        ('Scout',   'research', '09:00', 'Trend radar noon briefing',              330, 280),
        ('Charlie', 'ops',      '10:00', 'GitHub push workflow — BLOCKED',         420, 280, True),
        ('Ralph',   'qa',       '11:00', 'Approval queue validation rail',         516, 420),
        ('Echo',    'distribution','14:00','Publish workflow & release notes',     800, 280),
        ('Pixel',   'design',   '13:00', 'Design sprint — UI tokens review',      706, 280),
        ('Quill',   'docs',     '15:00', 'Knowledge base sync',                   894, 280),
        ('Shield',  'security', '09:00', 'Security audit — idle today',           330, 280),
    ]

    agent_rows = {}
    row_y = 248
    for ev in events:
        agent = ev[0]
        if agent not in agent_rows:
            agent_rows[agent] = row_y
            row_y += 58

    for ev in events:
        agent, spec, time_str, title = ev[0], ev[1], ev[2], ev[3]
        bar_x, bar_w = ev[4], ev[5]
        blocked = len(ev) > 6 and ev[6]
        ay = agent_rows[agent]

        # agent name column
        d.text((230, ay + 8), agent, fill=rgba('#f7fbff'), font=FONT_XS)

        col = '#ef4444' if blocked else SPECIALIST_COLORS.get(spec, '#24456e')
        d.rounded_rectangle((bar_x, ay + 4, bar_x + bar_w, ay + 44), radius=10,
                             fill=rgba(col, 200), outline=rgba('#ffffff', 30), width=1)
        d.text((bar_x + 10, ay + 8), time_str, fill=rgba('#ffffff', 180), font=FONT_XS)
        d.text((bar_x + 10, ay + 24), title[:38], fill=rgba('#f4fbff'), font=FONT_XS)
        if blocked:
            d.text((bar_x + bar_w - 60, ay + 14), '⚠ blocked', fill=rgba('#fca5a5'), font=FONT_XS)

    # time grid lines
    for i, t in enumerate(times):
        gx = 420 + i * 188
        d.line((gx, 202, gx, row_y + 10), fill=rgba('#1a2f4d', 180), width=1)

    img.save(DOCS / f'render_calendar_v{VTAG}.png')
    print(f"  render_calendar saved")


def write_mapping_manifest(layout_source: str) -> None:
    manifest = {
        'version': VERSION,
        'source_library': 'Pocket Office Quest v9',
        'agent_avatar_mapping': AGENT_MAP,
        'office_layout_source': layout_source,
        'vendor_root': 'third_party/pocket-office-quest-v9',
        'notes': [
            'Portrait assets are copied directly from the supplied v9 library.',
            'Office sprite sheets are adapted into 5-frame horizontal strips for the ClawTasker office engine.',
            'The supplied v9 archive did not include standalone office-background bitmaps, so this release generates matching day and night office layouts as compatibility assets.',
            'The release ships both office_map_day_32bit.png and office_map_night_32bit.png plus matching overlays and a local toggle in the Office view.',
        ],
    }
    (DOCS / f'POCKET_OFFICE_MAPPING_v{VTAG}.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')


def main() -> None:
    if not VENDOR.exists():
        raise SystemExit(f'Missing vendor assets: {VENDOR}')
    ensure_dirs()
    layout_source = sync_asset_copies()
    render_office_preview('day')
    render_office_preview('night')
    render_office_floor()
    render_avatar_roster()
    render_team()
    render_palette()
    render_app_layout()
    render_calendar_view()
    write_mapping_manifest(layout_source)


if __name__ == '__main__':
    main()
