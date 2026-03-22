#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import math
import shutil

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / 'web'
UI_PUBLIC = ROOT / 'ui' / 'public'
ASSETS = WEB / 'assets'
SPRITES = ASSETS / 'sprites'
PORTRAITS = ASSETS / 'portraits'
TEXTURES = ASSETS / 'textures'
DOCS = ROOT / 'docs'
VERSION = '2.9.0'

for path in (SPRITES, PORTRAITS, TEXTURES, DOCS):
    path.mkdir(parents=True, exist_ok=True)

PALETTE = {
    'night': '#10182C',
    'deck': '#18253D',
    'deck_2': '#203252',
    'fog': '#EDF2F8',
    'paper': '#FAF8F0',
    'sand': '#EFE6D4',
    'tile_light': '#F0EBDE',
    'tile_mid': '#E5DDCA',
    'tile_dark': '#D3C8AF',
    'wall': '#DDCFAD',
    'trim': '#A17D4F',
    'trim_dark': '#704F2B',
    'wood': '#A57C4B',
    'wood_dark': '#6B4C2C',
    'screen': '#A3DBFF',
    'screen_dark': '#4A7FA1',
    'glass': '#D8F1FF',
    'glass_line': '#7FA5C0',
    'leaf': '#76C98F',
    'leaf_dark': '#4E8F63',
    'sofa_blue': '#6E91CF',
    'sofa_teal': '#4CB9B2',
    'board_frame': '#445A76',
    'board_ready': '#8ADBA8',
    'board_doing': '#86A9FF',
    'board_validation': '#F3C86F',
    'board_done': '#7DD48F',
    'mint': '#63D5A8',
    'blue': '#66A2FF',
    'amber': '#F1C567',
    'coral': '#F48A79',
    'lavender': '#B79BFF',
    'green': '#7ACB74',
    'pink': '#F39CD8',
    'slate': '#A2B4CC',
    'shadow': '#18202D',
    'outline': '#1C2230',
    'label_bg': '#122036',
}

AGENTS = {
    'orion':   {'name': 'Orion',   'role': 'Chief Agent', 'skin': '#F2CAA7', 'hair': '#3F536A', 'outfit': '#49CDB9', 'accent': '#F0C66E', 'boots': '#23344F', 'cloak': '#57E0CA', 'specialist': 'planning'},
    'codex':   {'name': 'Codex',   'role': 'Lead Engineer', 'skin': '#EFC7A0', 'hair': '#273260', 'outfit': '#5D86FF', 'accent': '#9FD3FF', 'boots': '#1C2544', 'cloak': '#7CA2FF', 'specialist': 'code'},
    'violet':  {'name': 'Violet',  'role': 'Research Analyst', 'skin': '#EFC8A3', 'hair': '#5E3F8D', 'outfit': '#8D75FF', 'accent': '#D7BCFF', 'boots': '#2B214A', 'cloak': '#B09BFF', 'specialist': 'research'},
    'scout':   {'name': 'Scout',   'role': 'Trend Scout', 'skin': '#EFC49B', 'hair': '#63753A', 'outfit': '#90D24D', 'accent': '#E6F59A', 'boots': '#394A22', 'cloak': '#B7DF63', 'specialist': 'research'},
    'charlie': {'name': 'Charlie', 'role': 'Infrastructure Engineer', 'skin': '#EFC6A0', 'hair': '#815D3C', 'outfit': '#F0A15A', 'accent': '#FFD59D', 'boots': '#563620', 'cloak': '#F5BF7A', 'specialist': 'ops'},
    'ralph':   {'name': 'Ralph',   'role': 'QA Manager', 'skin': '#F2C9A7', 'hair': '#3D5F49', 'outfit': '#63D490', 'accent': '#C7F2AA', 'boots': '#213E31', 'cloak': '#7EE2A4', 'specialist': 'qa'},
    'shield':  {'name': 'Shield',  'role': 'Security Lead', 'skin': '#EFC4A0', 'hair': '#6D2B3C', 'outfit': '#F07A7C', 'accent': '#FFB5AC', 'boots': '#421B28', 'cloak': '#FF8F99', 'specialist': 'security'},
    'quill':   {'name': 'Quill',   'role': 'Docs Writer', 'skin': '#F0C9A7', 'hair': '#49546A', 'outfit': '#A4B5D0', 'accent': '#ECF3FB', 'boots': '#2B3345', 'cloak': '#C6D4E6', 'specialist': 'docs'},
    'pixel':   {'name': 'Pixel',   'role': 'Designer', 'skin': '#F2C9A9', 'hair': '#8A466C', 'outfit': '#F28ED9', 'accent': '#FFD2F1', 'boots': '#4B2940', 'cloak': '#FFB3E9', 'specialist': 'design'},
    'echo':    {'name': 'Echo',    'role': 'Distribution', 'skin': '#EFC8A2', 'hair': '#526540', 'outfit': '#57CAC8', 'accent': '#B8F5EE', 'boots': '#29413E', 'cloak': '#79E2DE', 'specialist': 'distribution'},
}

try:
    FONT_XL = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 28)
    FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)
    FONT_MD = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 14)
    FONT_SM = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 12)
    FONT_XS = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 10)
except Exception:
    FONT_XL = FONT = FONT_MD = FONT_SM = FONT_XS = ImageFont.load_default()


def rgb(hex_value: str):
    hex_value = hex_value.lstrip('#')
    return tuple(int(hex_value[i:i+2], 16) for i in (0, 2, 4))


def rgba(value, alpha=255):
    if isinstance(value, tuple):
        if len(value) == 4:
            return value
        return (*value, alpha)
    return (*rgb(value), alpha)


def clamp(n):
    return max(0, min(255, int(n)))


def shade(color, factor: float):
    r, g, b = rgb(color) if isinstance(color, str) else color[:3]
    if factor >= 1:
        r = r + (255 - r) * (factor - 1)
        g = g + (255 - g) * (factor - 1)
        b = b + (255 - b) * (factor - 1)
    else:
        r *= factor
        g *= factor
        b *= factor
    return (clamp(r), clamp(g), clamp(b), 255)


def px_rect(draw, xy, fill, outline=None, width=1):
    draw.rectangle(xy, fill=fill, outline=outline, width=width)


def px_round(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def px_ellipse(draw, xy, fill, outline=None, width=1):
    draw.ellipse(xy, fill=fill, outline=outline, width=width)


def resize_nn(img: Image.Image, factor: int) -> Image.Image:
    return img.resize((img.width * factor, img.height * factor), Image.Resampling.NEAREST)


def save_png(img: Image.Image, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format='PNG')


def text(draw, pos, value, fill, font=FONT_SM):
    draw.text(pos, value, fill=fill, font=font)


# ---------- office art ----------

def draw_checker_floor(draw: ImageDraw.ImageDraw, w: int, h: int):
    tile = 20
    draw.rectangle((0, 0, w, h), fill=rgba(PALETTE['tile_light']))
    for y in range(0, h, tile):
        for x in range(0, w, tile):
            base = PALETTE['tile_mid'] if ((x // tile) + (y // tile)) % 2 else PALETTE['tile_light']
            draw.rectangle((x, y, x + tile - 1, y + tile - 1), fill=rgba(base))
            draw.line((x, y + tile // 2, x + tile // 2, y), fill=rgba(PALETTE['tile_dark']), width=1)
            draw.line((x + tile // 2, y + tile, x + tile, y + tile // 2), fill=rgba(PALETTE['tile_dark']), width=1)


def draw_wall_band(draw: ImageDraw.ImageDraw, w: int):
    draw.rectangle((0, 0, w, 36), fill=rgba(PALETTE['wall']))
    draw.rectangle((0, 36, w, 44), fill=rgba(PALETTE['trim']))
    draw.rectangle((0, 44, w, 54), fill=rgba(PALETTE['trim_dark']))


def draw_window(draw, x, y, w, h):
    px_round(draw, (x, y, x + w, y + h), 4, rgba(PALETTE['fog']), rgba(PALETTE['glass_line']), 2)
    draw.rectangle((x + 4, y + 4, x + w - 4, y + h - 4), fill=rgba(PALETTE['glass']))
    draw.line((x + w // 2, y + 4, x + w // 2, y + h - 4), fill=rgba(PALETTE['glass_line']), width=2)
    draw.line((x + 4, y + h // 2, x + w - 4, y + h // 2), fill=rgba(PALETTE['glass_line']), width=2)


def draw_poster(draw, x, y, w, h, a, b):
    px_round(draw, (x, y, x + w, y + h), 4, rgba(PALETTE['paper']), rgba(PALETTE['board_frame']), 2)
    draw.rectangle((x + 4, y + 4, x + w - 4, y + h - 4), fill=rgba(a))
    draw.rectangle((x + 8, y + 8, x + w - 8, y + h // 2), fill=rgba(b))
    for i in range(3):
        draw.line((x + 8, y + h // 2 + 6 + i * 5, x + w - 10, y + h // 2 + 6 + i * 5), fill=rgba('#D7D1BF'), width=1)


def draw_plant(draw, x, y, size=22):
    px_rect(draw, (x + 4, y + size - 8, x + size - 4, y + size), rgba('#B78B58'), rgba('#6B4C2C'), 2)
    for dx, dy, r in [(0, 8, 8), (6, 2, 9), (13, 6, 7), (8, 11, 9), (3, 12, 7)]:
        px_ellipse(draw, (x + dx, y + dy, x + dx + r, y + dy + r), rgba(PALETTE['leaf']), rgba(PALETTE['leaf_dark']), 1)


def draw_monitor(draw, x, y, w=18, h=12, accent='#A3DBFF'):
    px_round(draw, (x, y, x + w, y + h), 2, rgba('#E5EBF4'), rgba('#5A6F84'), 2)
    draw.rectangle((x + 2, y + 2, x + w - 2, y + h - 2), fill=rgba(accent))
    draw.line((x + 3, y + 4, x + w - 4, y + 4), fill=rgba('#F9FDFF'), width=1)
    draw.rectangle((x + w // 2 - 2, y + h, x + w // 2 + 2, y + h + 4), fill=rgba('#63778D'))
    draw.rectangle((x + w // 2 - 6, y + h + 4, x + w // 2 + 6, y + h + 6), fill=rgba('#3A485B'))


def draw_keyboard(draw, x, y, w=18, h=5):
    px_round(draw, (x, y, x + w, y + h), 2, rgba('#D9DEE8'), rgba('#6A778B'), 1)
    for i in range(1, 4):
        draw.line((x + 2, y + i, x + w - 3, y + i), fill=rgba('#F6FAFF'), width=1)


def draw_mug(draw, x, y, color):
    px_round(draw, (x, y, x + 6, y + 8), 2, rgba(color), rgba('#354359'), 1)
    px_ellipse(draw, (x + 5, y + 2, x + 8, y + 5), None, rgba('#354359'), 1)


def draw_notepad(draw, x, y, color='#FFF4D4'):
    px_rect(draw, (x, y, x + 10, y + 12), rgba(color), rgba('#7C6B50'), 1)
    for i in range(3):
        draw.line((x + 2, y + 3 + i * 3, x + 8, y + 3 + i * 3), fill=rgba('#C1B08D'), width=1)


def draw_bookshelf(draw, x, y, w=36, h=60):
    px_rect(draw, (x, y, x + w, y + h), rgba('#9B774D'), rgba('#60462D'), 2)
    colors = ['#7BA6FF', '#F1C567', '#EF7D7D', '#72D69F', '#D9A3FF']
    for shelf in range(1, 4):
        sy = y + shelf * 14
        draw.line((x + 2, sy, x + w - 2, sy), fill=rgba('#60462D'), width=2)
    idx = 0
    for shelf in range(4):
        sy = y + 3 + shelf * 14
        cx = x + 4
        while cx < x + w - 6:
            bw = 4 + (idx % 3)
            px_rect(draw, (cx, sy, cx + bw, sy + 10), rgba(colors[idx % len(colors)]), rgba('#2D3242'), 1)
            cx += bw + 2
            idx += 1


def draw_desk_back(draw, x, y, w=72, h=28, tint='#DCE8F6', accent='#66A2FF', kind='code'):
    px_round(draw, (x, y, x + w, y + h), 6, rgba(tint), rgba('#6A7E93'), 2)
    draw.rectangle((x + 3, y + 3, x + w - 4, y + 8), fill=shade(tint, 1.05))
    draw.line((x + 6, y + h - 4, x + w - 6, y + h - 4), fill=rgba(accent), width=2)
    draw_monitor(draw, x + 10, y - 14, 18, 12, PALETTE['screen'])
    if kind in ('code', 'research', 'studio'):
        draw_monitor(draw, x + 33, y - 14, 18, 12, '#D9F1FF' if kind == 'research' else '#FFCFE9' if kind == 'studio' else '#CBE3FF')
    draw_keyboard(draw, x + 12, y + 12, 16, 4)
    if kind == 'code':
        draw_notepad(draw, x + 42, y + 4, '#EEF4FF')
        for i, c in enumerate(['#66A2FF', '#F48A79', '#63D5A8', '#F1C567']):
            px_rect(draw, (x + 36 + i * 6, y + 12, x + 40 + i * 6, y + 16), rgba(c), rgba('#374559'), 1)
    elif kind == 'research':
        draw_notepad(draw, x + 42, y + 3, '#FFF5D4')
        draw_mug(draw, x + 58, y + 7, '#B79BFF')
    elif kind == 'chief':
        draw_notepad(draw, x + 42, y + 4, '#FFF5D4')
        draw_mug(draw, x + 58, y + 7, '#63D5A8')
    elif kind == 'ops':
        draw_mug(draw, x + 42, y + 7, '#F48A79')
        draw_notepad(draw, x + 54, y + 4, '#EDF2F8')
    elif kind == 'review':
        draw_notepad(draw, x + 7, y + 3, '#FFF5D4')
        draw_notepad(draw, x + 21, y + 3, '#EEF4FF')
        draw_monitor(draw, x + 40, y - 10, 16, 10, '#D4E8FF')
    elif kind == 'studio':
        draw_notepad(draw, x + 40, y + 4, '#FFD7EF')
        draw_mug(draw, x + 57, y + 7, '#66A2FF')


def draw_desk_front(draw, x, y, w=72, h=18, accent='#66A2FF'):
    px_round(draw, (x, y, x + w, y + h), 5, rgba('#8A7051'), rgba('#5B432B'), 2)
    draw.rectangle((x + 3, y + 3, x + w - 4, y + h - 4), fill=rgba('#B18B60'))
    draw.line((x + 5, y + 5, x + w - 5, y + 5), fill=rgba('#D4B07D'), width=2)
    draw.line((x + 8, y + h - 5, x + w - 8, y + h - 5), fill=rgba(accent), width=2)


def draw_chair(draw, x, y, accent):
    px_round(draw, (x, y, x + 14, y + 10), 3, rgba(accent), rgba('#334257'), 2)
    px_rect(draw, (x + 3, y + 10, x + 5, y + 16), rgba('#5A6F84'))
    px_rect(draw, (x + 9, y + 10, x + 11, y + 16), rgba('#5A6F84'))


def draw_sync_table_back(draw, x, y, w=126, h=54):
    left = x - w // 2
    top = y - h // 2
    px_round(draw, (left, top, left + w, top + h), 8, rgba('#DCC49E'), rgba('#866140'), 3)
    px_round(draw, (left + 6, top + 6, left + w - 6, top + h - 6), 6, rgba('#F2E6CC'), rgba('#B59769'), 2)
    draw.line((left + 12, top + h // 2, left + w - 12, top + h // 2), fill=rgba('#D4B07D'), width=2)
    # table legs
    for lx in (left + 16, left + w - 24):
        px_rect(draw, (lx, top + h - 4, lx + 6, top + h + 12), rgba('#8C6843'), rgba('#60462D'), 2)
    # tabletop objects
    for nx, ny, color in [(left + 18, top + 12, '#FFF5D4'), (left + 48, top + 12, '#EEF4FF'), (left + 78, top + 12, '#FFF5D4'), (left + 98, top + 14, '#E8F5EC')]:
        draw_notepad(draw, nx, ny, color)
    draw_mug(draw, left + 34, top + 14, '#66A2FF')
    draw_mug(draw, left + 92, top + 16, '#63D5A8')


def draw_sync_table_front(draw, x, y, w=126, h=54):
    # Keep the center table fully in the back layer so seated agents stay visible.
    return


def draw_sofa(draw, x, y, w=68, h=28, fill='#6E91CF'):
    px_round(draw, (x, y, x + w, y + h), 5, rgba(fill), rgba('#38547D'), 2)
    px_round(draw, (x + 6, y + 6, x + w - 7, y + h - 6), 4, shade(fill, 1.08), rgba('#87A4D4'), 1)
    draw.line((x + w // 2, y + 6, x + w // 2, y + h - 6), fill=rgba('#38547D'), width=2)


def draw_board(draw, x, y, w=88, h=116):
    px_round(draw, (x, y, x + w, y + h), 5, rgba('#F8FBFF'), rgba(PALETTE['board_frame']), 2)
    col_w = (w - 12) // 4
    cols = [
        (PALETTE['board_ready'], 'Ready'),
        (PALETTE['board_doing'], 'Doing'),
        (PALETTE['board_validation'], 'Review'),
        (PALETTE['board_done'], 'Done'),
    ]
    for i, (color, label) in enumerate(cols):
        cx = x + 6 + i * col_w
        px_round(draw, (cx, y + 8, cx + col_w - 5, y + h - 8), 3, shade(color, 1.15), rgba(shade(color, 0.72)), 1)
        text(draw, (cx + 4, y + 10), label[:5], rgba('#233044'), FONT_XS)
        for j in range(4):
            cy = y + 28 + j * 18
            px_round(draw, (cx + 4, cy, cx + col_w - 9, cy + 12), 2, rgba('#FFFFFF'), rgba(shade(color, 0.7)), 1)


def draw_board_counter(draw, x, y, label, value, fill):
    px_round(draw, (x, y, x + 62, y + 30), 5, rgba(PALETTE['label_bg']), rgba(fill), 2)
    text(draw, (x + 8, y + 4), label, rgba('#F6FBFF'), FONT_XS)
    text(draw, (x + 39, y + 8), str(value), rgba(fill), FONT_MD)


def make_office_maps():
    w, h = 680, 410
    back = Image.new('RGBA', (w, h), rgba(PALETTE['tile_light']))
    front = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(back)
    fdraw = ImageDraw.Draw(front)
    draw_checker_floor(draw, w, h)
    draw_wall_band(draw, w)
    # zone rugs / floor accents
    px_round(draw, (28, 138, 188, 276), 12, rgba('#EDF5FF'), rgba('#B5C8DE'), 2)
    px_round(draw, (212, 138, 392, 274), 12, rgba('#F2EDFF'), rgba('#C7B6FF'), 2)
    px_round(draw, (406, 138, 584, 274), 12, rgba('#EEF9F1'), rgba('#B2D8BF'), 2)
    px_round(draw, (22, 302, 230, 392), 12, rgba('#F1FAF2'), rgba('#B5D5C0'), 2)
    px_round(draw, (446, 304, 650, 390), 12, rgba('#F4F1FF'), rgba('#CABEFF'), 2)
    # windows and posters
    for x in [46, 120, 194, 268, 342, 416]:
        draw_window(draw, x, 6, 54, 24)
    draw_poster(draw, 502, 8, 48, 24, '#BFE1FF', '#78B95D')
    draw_poster(draw, 558, 8, 44, 24, '#FFEFC5', '#F1A85D')
    draw_poster(draw, 608, 8, 46, 24, '#F7D2EB', '#A384FF')
    # top desks
    draw_desk_back(draw, 28, 74, 78, 30, tint='#DAF0E7', accent=PALETTE['mint'], kind='chief')
    draw_desk_front(fdraw, 28, 98, 78, 18, accent=PALETTE['mint'])
    draw_chair(fdraw, 60, 110, PALETTE['mint'])
    draw_desk_back(draw, 148, 74, 98, 30, tint='#DCEAF7', accent=PALETTE['blue'], kind='chief')
    draw_desk_front(fdraw, 148, 98, 98, 18, accent=PALETTE['blue'])
    draw_chair(fdraw, 176, 110, PALETTE['blue'])
    draw_chair(fdraw, 208, 110, PALETTE['blue'])
    # board wall
    draw_board(draw, 576, 56, 92, 122)
    draw_board_counter(draw, 576, 182, 'Ready', 4, PALETTE['board_ready'])
    draw_board_counter(draw, 640, 182, 'Doing', 5, PALETTE['board_doing'])
    draw_board_counter(draw, 576, 214, 'Valid', 2, PALETTE['board_validation'])
    draw_board_counter(draw, 640, 214, 'Done', 4, PALETTE['board_done'])
    # desk pods
    for x, y in [(34, 156), (112, 156), (34, 216), (112, 216)]:
        draw_desk_back(draw, x, y, 72, 28, tint='#DCE8F6', accent=PALETTE['blue'], kind='code')
        draw_desk_front(fdraw, x, y + 24, 72, 18, accent=PALETTE['blue'])
        draw_chair(fdraw, x + 30, y + 42, PALETTE['blue'])
    for x, y in [(228, 156), (306, 156), (228, 216), (306, 216)]:
        draw_desk_back(draw, x, y, 72, 28, tint='#ECE6FF', accent=PALETTE['lavender'], kind='research')
        draw_desk_front(fdraw, x, y + 24, 72, 18, accent=PALETTE['lavender'])
        draw_chair(fdraw, x + 30, y + 42, PALETTE['lavender'])
    for x, y in [(422, 156), (500, 156), (422, 216), (500, 216)]:
        draw_desk_back(draw, x, y, 72, 28, tint='#E4F3E9', accent=PALETTE['green'], kind='ops')
        draw_desk_front(fdraw, x, y + 24, 72, 18, accent=PALETTE['green'])
        draw_chair(fdraw, x + 30, y + 42, PALETTE['green'])
    # library + coffee + plants
    draw_bookshelf(draw, 18, 126, 30, 74)
    draw_bookshelf(draw, 610, 298, 30, 74)
    draw_plant(draw, 186, 126, 22)
    draw_plant(draw, 388, 126, 22)
    draw_plant(draw, 596, 302, 22)
    px_round(draw, (18, 328, 52, 366), 4, rgba('#E2E8F1'), rgba('#73879B'), 2)
    draw_monitor(draw, 24, 334, 16, 10, '#2F6F92')
    draw_mug(draw, 34, 350, '#F1C567')
    # sync table
    draw_sync_table_back(draw, 350, 284, 128, 58)
    draw_sync_table_front(fdraw, 350, 284, 128, 58)
    for cx, cy, acc in [
        (292, 246, PALETTE['mint']), (350, 246, PALETTE['blue']), (408, 246, PALETTE['amber']),
        (292, 322, PALETTE['pink']), (350, 322, PALETTE['green']), (408, 322, PALETTE['lavender'])
    ]:
        draw_chair(draw, cx, cy, acc)
    # lounge
    draw_sofa(draw, 38, 330, 76, 30, PALETTE['sofa_blue'])
    draw_sofa(draw, 124, 330, 76, 30, PALETTE['sofa_teal'])
    px_round(draw, (90, 360, 148, 386), 6, rgba('#D9C6A2'), rgba('#8D744C'), 2)
    draw_mug(draw, 113, 366, '#F1C567')
    draw_notepad(draw, 97, 364)
    draw_plant(draw, 204, 336, 22)
    # review + studio
    for x in [598, 628]:
        draw_desk_back(draw, x, 250, 28, 98, tint='#F7F0E2', accent=PALETTE['amber'], kind='review')
        draw_desk_front(fdraw, x, 332, 28, 18, accent=PALETTE['amber'])
    for x, y in [(438, 322), (516, 322), (594, 322)]:
        draw_desk_back(draw, x, y, 72, 28, tint='#F7EAF3', accent=PALETTE['pink'], kind='studio')
        draw_desk_front(fdraw, x, y + 24, 72, 18, accent=PALETTE['pink'])
        draw_chair(fdraw, x + 30, y + 42, PALETTE['pink'])
    # labels
    for text_value, x, y in [
        ('CEO', 18, 56), ('Chief', 146, 56), ('Code pod', 40, 138), ('Research', 232, 138),
        ('Ops / Sec', 428, 138), ('Sync table', 310, 220), ('Review', 595, 238), ('Studio', 448, 304), ('Lounge', 48, 302)
    ]:
        text(draw, (x, y), text_value, rgba('#56697F'), FONT_XS)
    # slight polish
    gloss = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    g = ImageDraw.Draw(gloss)
    g.ellipse((32, 40, 250, 220), fill=(99, 213, 168, 24))
    g.ellipse((440, 50, 660, 230), fill=(102, 162, 255, 22))
    back = Image.alpha_composite(back, gloss)
    back = Image.blend(back, back.filter(ImageFilter.GaussianBlur(0.18)), 0.04)
    save_png(resize_nn(back, 2), TEXTURES / 'office_map_32bit.png')
    save_png(resize_nn(front, 2), TEXTURES / 'office_overlay_32bit.png')


# ---------- sprites and portraits ----------

def draw_head(draw, p, x, y, direction='front'):
    outline = rgba(PALETTE['outline'])
    skin = rgba(p['skin'])
    hair = rgba(p['hair'])
    hair_hi = shade(p['hair'], 1.08)
    # head
    px_rect(draw, (x + 5, y + 4, x + 12, y + 11), skin, outline, 1)
    px_rect(draw, (x + 4, y + 5, x + 13, y + 10), skin, None, 0)
    # ears
    if direction != 'back':
        px_rect(draw, (x + 4, y + 7, x + 4, y + 8), skin, outline, 1)
        px_rect(draw, (x + 13, y + 7, x + 13, y + 8), skin, outline, 1)
    # hair top + fringe
    px_rect(draw, (x + 4, y + 3, x + 13, y + 7), hair, outline, 1)
    px_rect(draw, (x + 3, y + 5, x + 5, y + 9), hair, outline, 1)
    px_rect(draw, (x + 11, y + 5, x + 14, y + 9), hair, outline, 1)
    px_rect(draw, (x + 6, y + 7, x + 8, y + 8), hair, None, 0)
    px_rect(draw, (x + 10, y + 7, x + 11, y + 8), hair, None, 0)
    draw.line((x + 5, y + 4, x + 12, y + 4), fill=hair_hi, width=1)
    if direction == 'front':
        draw.point((x + 7, y + 8), fill=outline)
        draw.point((x + 10, y + 8), fill=outline)
        draw.line((x + 8, y + 10, x + 9, y + 10), fill=rgba('#B56D68'), width=1)
    elif direction == 'left':
        draw.point((x + 7, y + 8), fill=outline)
    elif direction == 'right':
        draw.point((x + 10, y + 8), fill=outline)
    elif direction == 'back':
        px_rect(draw, (x + 5, y + 5, x + 12, y + 10), hair, outline, 1)
        draw.line((x + 6, y + 6, x + 11, y + 6), fill=hair_hi, width=1)


def draw_body(draw, p, x, y, pose='idle', direction='front', accessory='none'):
    outline = rgba(PALETTE['outline'])
    outfit = rgba(p['outfit'])
    outfit_hi = shade(p['outfit'], 1.08)
    cloak = rgba(p['cloak'])
    boots = rgba(p['boots'])
    boots_hi = shade(p['boots'], 1.1)
    skin = rgba(p['skin'])
    pants = shade(p['outfit'], 0.76)
    pants_hi = shade(p['outfit'], 0.9)
    accent = rgba(p['accent'])

    body_y = y + 12
    if pose == 'seated':
        body_y += 2

    # cloak/back
    if direction == 'back':
        px_rect(draw, (x + 4, body_y, x + 13, body_y + 10), cloak, outline, 1)
        draw.line((x + 5, body_y + 2, x + 12, body_y + 2), fill=shade(p['cloak'], 1.08), width=1)
    else:
        px_rect(draw, (x + 4, body_y, x + 13, body_y + 10), cloak, outline, 1)
        px_rect(draw, (x + 6, body_y, x + 11, body_y + 9), outfit, outline, 1)
        draw.line((x + 7, body_y + 1, x + 10, body_y + 1), fill=outfit_hi, width=1)
        draw.line((x + 8, body_y, x + 8, body_y + 9), fill=accent, width=1)
        draw.line((x + 6, body_y + 6, x + 11, body_y + 6), fill=boots, width=1)

    # arms
    if pose == 'talk':
        arms = [(x + 3, body_y + 1, x + 5, body_y + 8), (x + 11, body_y - 2, x + 14, body_y + 4)]
    elif pose == 'walk1':
        arms = [(x + 3, body_y + 2, x + 5, body_y + 9), (x + 11, body_y, x + 13, body_y + 7)]
    elif pose == 'walk2':
        arms = [(x + 3, body_y, x + 5, body_y + 7), (x + 11, body_y + 2, x + 13, body_y + 9)]
    else:
        arms = [(x + 3, body_y + 2, x + 5, body_y + 9), (x + 11, body_y + 2, x + 13, body_y + 9)]
    for ax1, ay1, ax2, ay2 in arms:
        px_rect(draw, (ax1, ay1, ax2, ay2), skin, outline, 1)
        draw.line((ax1, ay1 + 2, ax2, ay1 + 2), fill=accent, width=1)

    # accessory hints
    if direction != 'back':
        if accessory == 'chief':
            px_rect(draw, (x + 12, body_y + 2, x + 15, body_y + 6), rgba('#F3F7FB'), outline, 1)
        elif accessory == 'code':
            px_rect(draw, (x + 11, body_y + 2, x + 14, body_y + 5), rgba('#2C3B57'), outline, 1)
            draw.line((x + 11, body_y + 3, x + 14, body_y + 3), fill=rgba(PALETTE['screen']), width=1)
        elif accessory == 'research':
            px_rect(draw, (x + 1, body_y + 2, x + 4, body_y + 5), rgba('#FFF5D4'), outline, 1)
        elif accessory == 'ops':
            px_rect(draw, (x + 12, body_y + 3, x + 14, body_y + 5), rgba('#3B4657'), outline, 1)
            draw.point((x + 13, body_y + 4), fill=rgba(PALETTE['mint']))
        elif accessory == 'qa':
            px_rect(draw, (x + 1, body_y + 2, x + 4, body_y + 6), rgba('#FFF5D4'), outline, 1)
            draw.line((x + 2, body_y + 4, x + 3, body_y + 4), fill=rgba(PALETTE['green']), width=1)
        elif accessory == 'studio':
            for i, c in enumerate([PALETTE['blue'], PALETTE['coral'], PALETTE['mint']]):
                px_rect(draw, (x + 1 + i * 2, body_y + 2, x + 2 + i * 2, body_y + 4), rgba(c), outline, 1)

    # legs
    if pose == 'seated':
        legs = [(x + 6, body_y + 9, x + 10, body_y + 12), (x + 9, body_y + 12, x + 14, body_y + 15)]
    elif pose == 'walk1':
        legs = [(x + 6, body_y + 10, x + 8, body_y + 18), (x + 10, body_y + 10, x + 12, body_y + 15)]
    elif pose == 'walk2':
        legs = [(x + 6, body_y + 10, x + 8, body_y + 15), (x + 10, body_y + 10, x + 12, body_y + 18)]
    else:
        legs = [(x + 6, body_y + 10, x + 8, body_y + 18), (x + 10, body_y + 10, x + 12, body_y + 18)]
    for lx1, ly1, lx2, ly2 in legs:
        px_rect(draw, (lx1, ly1, lx2, ly2), pants, outline, 1)
        draw.line((lx1, ly1 + 1, lx2, ly1 + 1), fill=pants_hi, width=1)
        px_rect(draw, (lx1 - 1, ly2, lx2 + 1, ly2 + 2), boots, outline, 1)
        draw.line((lx1, ly2, lx2, ly2), fill=boots_hi, width=1)


def generate_agent_sheet(agent_id, p):
    accessory = {
        'orion': 'chief', 'codex': 'code', 'violet': 'research', 'scout': 'research', 'charlie': 'ops',
        'ralph': 'qa', 'shield': 'ops', 'quill': 'studio', 'pixel': 'studio', 'echo': 'studio'
    }.get(agent_id, 'none')
    frames = [
        ('idle', 'front'),
        ('walk1', 'left'),
        ('walk2', 'right'),
        ('seated', 'front'),
        ('talk', 'front'),
    ]
    base = Image.new('RGBA', (24 * len(frames), 32), (0, 0, 0, 0))
    for idx, (pose, direction) in enumerate(frames):
        frame = Image.new('RGBA', (24, 32), (0, 0, 0, 0))
        d = ImageDraw.Draw(frame)
        # shadow
        px_ellipse(d, (7, 27, 17, 30), (0, 0, 0, 50), None, 0)
        draw_head(d, p, 4, 0, direction='back' if direction == 'back' else 'front' if direction == 'front' else direction)
        draw_body(d, p, 4, 0, pose=pose, direction=direction, accessory=accessory)
        base.alpha_composite(frame, (idx * 24, 0))
    save_png(resize_nn(base, 2), SPRITES / f'{agent_id}.png')


def generate_portrait(agent_id, p):
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    outline = rgba(PALETTE['outline'])
    skin = rgba(p['skin'])
    hair = rgba(p['hair'])
    accent = rgba(p['accent'])
    outfit = rgba(p['outfit'])
    # shoulders and collar
    px_rect(d, (7, 21, 24, 31), outfit, outline, 1)
    px_rect(d, (11, 21, 20, 23), accent, None, 0)
    # neck
    px_rect(d, (14, 18, 17, 21), skin, outline, 1)
    # face
    px_rect(d, (9, 7, 22, 19), skin, outline, 1)
    px_rect(d, (10, 6, 21, 7), skin, None, 0)
    # hair
    px_rect(d, (7, 4, 24, 10), hair, outline, 1)
    px_rect(d, (8, 10, 10, 16), hair, outline, 1)
    px_rect(d, (21, 10, 23, 15), hair, outline, 1)
    d.line((9, 5, 22, 5), fill=shade(p['hair'], 1.08), width=1)
    # fringe
    px_rect(d, (11, 9, 13, 10), hair, None, 0)
    px_rect(d, (17, 9, 18, 10), hair, None, 0)
    # eyes and mouth
    d.point((13, 13), fill=outline)
    d.point((18, 13), fill=outline)
    d.line((14, 16, 17, 16), fill=rgba('#B56D68'), width=1)
    # specialist gem
    px_ellipse(d, (22, 4, 28, 10), accent, outline, 1)
    save_png(img, PORTRAITS / f'{agent_id}.png')


# ---------- preview renders ----------

UPSCALE_ANCHORS = {
    'ceo_strip': [(108, 230)],
    'chief_desk': [(350, 230), (412, 230)],
    'code_pod': [(108, 346), (264, 346), (108, 466), (264, 466)],
    'research_pod': [(498, 346), (656, 346), (498, 466), (656, 466)],
    'ops_pod': [(888, 346), (1048, 346), (888, 466), (1048, 466)],
    'qa_pod': [(1214, 528), (1270, 586)],
    'studio_pod': [(940, 692), (1096, 692), (1252, 692)],
    'scrum_table': [(618, 486), (704, 486), (790, 486), (618, 644), (704, 644), (790, 644)],
    'review_rail': [(1222, 568), (1278, 568), (1222, 628), (1278, 628)],
    'lounge': [(118, 706), (270, 706), (428, 706), (548, 682)],
    'board_wall': [(1234, 250)],
}


def sprite_frame(agent_id: str, frame_index: int) -> Image.Image:
    sheet = Image.open(SPRITES / f'{agent_id}.png').convert('RGBA')
    return sheet.crop((frame_index * 48, 0, frame_index * 48 + 48, 64))


def draw_office_agent(base: Image.Image, agent_id: str, name: str, label: str, x: int, y: int, frame_index: int = 0):
    sprite = sprite_frame(agent_id, frame_index)
    label_draw = ImageDraw.Draw(base)
    shadow = Image.new('RGBA', base.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    px_ellipse(sd, (x - 18, y - 8, x + 18, y + 2), (0, 0, 0, 40), None, 0)
    base.alpha_composite(shadow)
    base.alpha_composite(sprite, (x - 24, y - 64))
    # activity pill
    colors = {
        'Working': PALETTE['blue'], 'Validation': PALETTE['amber'], 'Blocked': PALETTE['coral'],
        'Idle': PALETTE['slate'], 'Sync': PALETTE['mint'], 'Review': PALETTE['amber']
    }
    pill_w = max(54, int(label_draw.textlength(label, font=FONT_XS)) + 14)
    px_round(label_draw, (x - pill_w // 2, y - 82, x + pill_w // 2, y - 64), 8, rgba(PALETTE['label_bg']), rgba(colors.get(label, PALETTE['slate'])), 1)
    label_draw.text((x - pill_w // 2 + 8, y - 78), label.upper(), fill=rgba('#F6FBFF'), font=FONT_XS)
    # nameplate
    name_w = max(58, int(label_draw.textlength(name, font=FONT_XS)) + 16)
    px_round(label_draw, (x - name_w // 2, y + 2, x + name_w // 2, y + 18), 8, rgba(PALETTE['label_bg']), rgba('#FFFFFF', 36), 1)
    label_draw.text((x - name_w // 2 + 8, y + 5), name, fill=rgba('#F6FBFF'), font=FONT_XS)


def draw_preview_renders():
    office_back = Image.open(TEXTURES / 'office_map_32bit.png').convert('RGBA')
    office_front = Image.open(TEXTURES / 'office_overlay_32bit.png').convert('RGBA')
    # office floor render
    floor = office_back.copy()
    placements = [
        ('orion', 'Orion', 'Sync', *UPSCALE_ANCHORS['scrum_table'][1], 4),
        ('codex', 'Codex', 'Working', *UPSCALE_ANCHORS['code_pod'][0], 3),
        ('violet', 'Violet', 'Working', *UPSCALE_ANCHORS['research_pod'][0], 3),
        ('charlie', 'Charlie', 'Blocked', *UPSCALE_ANCHORS['scrum_table'][4], 4),
        ('ralph', 'Ralph', 'Validation', *UPSCALE_ANCHORS['review_rail'][0], 4),
        ('quill', 'Quill', 'Working', *UPSCALE_ANCHORS['studio_pod'][0], 3),
        ('pixel', 'Pixel', 'Working', *UPSCALE_ANCHORS['studio_pod'][1], 3),
        ('echo', 'Echo', 'Idle', *UPSCALE_ANCHORS['lounge'][2], 0),
    ]
    for item in sorted(placements, key=lambda t: t[4]):
        draw_office_agent(floor, item[0], item[1], item[2], item[3], item[4], item[5])
    floor.alpha_composite(office_front)
    fd = ImageDraw.Draw(floor)
    px_round(fd, (920, 50, 1298, 98), 14, (16, 25, 44, 220), rgba('#FFFFFF', 28), 1)
    fd.text((942, 64), 'ClawTasker Open Office - GBA-inspired office engine', fill=rgba('#F6FBFF'), font=FONT_MD)
    fd.text((943, 82), 'Desk pods, sync table, board wall, review rail, lounge, and live status labels', fill=rgba('#C9D7E9'), font=FONT_XS)
    save_png(floor, DOCS / f'render_office_floor_v2_9_0.png')

    # office panel render
    app = Image.new('RGBA', (1600, 980), rgba(PALETTE['night']))
    d = ImageDraw.Draw(app)
    # shell gradients
    gradient = Image.new('RGBA', app.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(gradient)
    gd.ellipse((-120, -80, 360, 300), fill=(99, 213, 168, 40))
    gd.ellipse((1120, -100, 1660, 280), fill=(102, 162, 255, 36))
    app.alpha_composite(gradient)
    # sidebar
    px_round(d, (26, 22, 320, 956), 28, rgba(PALETTE['deck']), rgba('#FFFFFF', 30), 1)
    d.text((52, 54), 'ClawTasker', fill=rgba('#F6FBFF'), font=FONT_XL)
    d.text((54, 90), 'CEO Console 2.9.0', fill=rgba('#BFD0E2'), font=FONT_SM)
    nav_groups = [
        ('Chat', ['Conversations']),
        ('Control', ['Dashboard', 'Calendar', 'Board', 'Backlog', 'Approvals', 'Office']),
        ('Agent', ['Team', 'Runs', 'Access']),
        ('Settings', ['Appearance']),
    ]
    y = 142
    for label, items in nav_groups:
        d.text((56, y), label.upper(), fill=rgba('#7E92AC'), font=FONT_XS)
        y += 18
        for item in items:
            active = item == 'Office'
            if active:
                px_round(d, (42, y - 6, 286, y + 34), 18, rgba(PALETTE['deck_2']), rgba(PALETTE['mint']), 2)
            d.text((60, y), item, fill=rgba('#F6FBFF') if active else rgba('#AAB9CD'), font=FONT_MD)
            y += 46
        y += 14
    # main area
    px_round(d, (342, 22, 1574, 136), 28, (22, 36, 60, 228), rgba('#FFFFFF', 24), 1)
    d.text((374, 58), 'Office', fill=rgba('#F6FBFF'), font=FONT_XL)
    d.text((376, 94), 'Human-friendly open office view with deterministic movement and structured coordination.', fill=rgba('#C8D6E8'), font=FONT_SM)
    # filter chips
    chip_x = 1080
    for label, fill in [('All agents', PALETTE['mint']), ('All projects', PALETTE['blue']), ('All specialists', PALETTE['lavender'])]:
        width = int(d.textlength(label, font=FONT_SM)) + 34
        px_round(d, (chip_x, 58, chip_x + width, 88), 14, rgba(PALETTE['label_bg']), rgba(fill), 1)
        d.text((chip_x + 14, 67), label, fill=rgba('#F6FBFF'), font=FONT_SM)
        chip_x += width + 12
    # office panel + rail
    px_round(d, (342, 156, 1236, 954), 28, (20, 34, 56, 214), rgba('#FFFFFF', 20), 1)
    panel = floor.resize((862, 760), Image.Resampling.NEAREST)
    app.alpha_composite(panel, (358, 174))
    px_round(d, (1252, 156, 1574, 954), 28, (20, 34, 56, 214), rgba('#FFFFFF', 20), 1)
    d.text((1280, 190), 'Live office', fill=rgba('#F6FBFF'), font=FONT_MD)
    activity_cards = [
        ('Team sync table', 'Orion, Charlie, and Ralph align at the sync table on blockers and review path handoffs.', PALETTE['mint']),
        ('Validation', 'Ralph is paired with Violet on the weekly research brief acceptance checks.', PALETTE['amber']),
        ('Focus desks', 'Codex, Quill, and Pixel stay anchored to their desks while actively working.', PALETTE['blue']),
    ]
    y = 230
    for title, copy, fill in activity_cards:
        px_round(d, (1276, y, 1548, y + 118), 20, (16, 27, 45, 230), rgba(fill), 1)
        d.text((1294, y + 16), title, fill=rgba('#F6FBFF'), font=FONT_MD)
        d.text((1294, y + 48), copy, fill=rgba('#C6D4E6'), font=FONT_XS)
        y += 136
    save_png(app, DOCS / f'render_office_v2_9_0.png')

    # team render
    team = Image.new('RGBA', (1600, 880), rgba(PALETTE['night']))
    td = ImageDraw.Draw(team)
    td.text((42, 40), 'ClawTasker team and org chart', fill=rgba('#F6FBFF'), font=FONT_XL)
    td.text((44, 78), 'CEO -> chief agent -> specialist roster, using portrait icons derived from the new sprite family.', fill=rgba('#C8D6E8'), font=FONT_SM)
    # CEO card
    px_round(td, (48, 132, 480, 272), 24, (22, 36, 60, 228), rgba(PALETTE['mint']), 2)
    td.text((204, 162), 'You', fill=rgba('#F6FBFF'), font=FONT_XL)
    td.text((206, 202), 'CEO', fill=rgba('#BFD0E2'), font=FONT_MD)
    td.text((206, 230), 'Sets priorities, approvals, and operating constraints.', fill=rgba('#D4DEEB'), font=FONT_XS)
    # generic CEO portrait
    px_round(td, (78, 154, 170, 246), 20, rgba(PALETTE['deck_2']), rgba('#FFFFFF', 30), 1)
    td.ellipse((102, 172, 146, 216), fill=rgba('#F0C9A7'), outline=rgba(PALETTE['outline']))
    td.rectangle((90, 154, 158, 182), fill=rgba('#425B7A'), outline=rgba(PALETTE['outline']))
    td.rectangle((98, 216, 150, 242), fill=rgba('#6AA2FF'), outline=rgba(PALETTE['outline']))
    # chief card
    px_round(td, (560, 132, 1020, 272), 24, (22, 36, 60, 228), rgba(PALETTE['blue']), 2)
    td.text((720, 162), 'Orion', fill=rgba('#F6FBFF'), font=FONT_XL)
    td.text((722, 202), 'Chief Agent', fill=rgba('#BFD0E2'), font=FONT_MD)
    td.text((722, 230), 'Decomposes work, routes by specialist, and handles exceptions.', fill=rgba('#D4DEEB'), font=FONT_XS)
    chief = Image.open(PORTRAITS / 'orion.png').resize((96, 96), Image.Resampling.NEAREST)
    team.alpha_composite(chief, (592, 154))
    # specialists grid
    x_positions = [80, 470, 860, 1250]
    y_positions = [340, 580]
    ids = ['codex', 'violet', 'charlie', 'ralph', 'scout', 'shield', 'quill', 'pixel']
    for idx, aid in enumerate(ids):
        col = idx % 4
        row = idx // 4
        x = x_positions[col]
        y = y_positions[row]
        px_round(td, (x, y, x + 300, y + 180), 24, (22, 36, 60, 220), rgba('#FFFFFF', 24), 1)
        portrait = Image.open(PORTRAITS / f'{aid}.png').resize((88, 88), Image.Resampling.NEAREST)
        team.alpha_composite(portrait, (x + 20, y + 24))
        td.text((x + 122, y + 34), AGENTS[aid]['name'], fill=rgba('#F6FBFF'), font=FONT_MD)
        td.text((x + 122, y + 62), AGENTS[aid]['role'], fill=rgba('#BFD0E2'), font=FONT_XS)
        td.text((x + 122, y + 92), AGENTS[aid]['specialist'].title(), fill=rgba(AGENTS[aid]['accent']), font=FONT_XS)
        td.text((x + 122, y + 118), 'Status: Working', fill=rgba('#D4DEEB'), font=FONT_XS)
        td.text((x + 122, y + 140), 'Skills: execution, handoff, artifacts', fill=rgba('#AAB9CD'), font=FONT_XS)
    save_png(team, DOCS / 'render_team_v2_9_0.png')

    # app layout render
    dash = Image.new('RGBA', (1600, 980), rgba(PALETTE['night']))
    dd = ImageDraw.Draw(dash)
    dash.alpha_composite(gradient)
    px_round(dd, (26, 22, 320, 956), 28, rgba(PALETTE['deck']), rgba('#FFFFFF', 30), 1)
    dd.text((52, 54), 'ClawTasker', fill=rgba('#F6FBFF'), font=FONT_XL)
    dd.text((54, 90), 'CEO Console 2.9.0', fill=rgba('#BFD0E2'), font=FONT_SM)
    nav_groups = [
        ('Chat', ['Conversations']),
        ('Control', ['Dashboard', 'Calendar', 'Board', 'Backlog', 'Approvals', 'Office']),
        ('Agent', ['Team', 'Runs', 'Access']),
        ('Settings', ['Appearance']),
    ]
    y = 142
    for label, items in nav_groups:
        dd.text((56, y), label.upper(), fill=rgba('#7E92AC'), font=FONT_XS)
        y += 18
        for item in items:
            active = item == 'Dashboard'
            if active:
                px_round(dd, (42, y - 6, 286, y + 34), 18, rgba(PALETTE['deck_2']), rgba(PALETTE['blue']), 2)
            dd.text((60, y), item, fill=rgba('#F6FBFF') if active else rgba('#AAB9CD'), font=FONT_MD)
            y += 46
        y += 14
    px_round(dd, (342, 22, 1574, 136), 28, (22, 36, 60, 228), rgba('#FFFFFF', 24), 1)
    dd.text((372, 58), 'Dashboard', fill=rgba('#F6FBFF'), font=FONT_XL)
    dd.text((374, 94), 'The OpenClaw-style shell keeps dashboard, office, conversations, and appearance settings recognizable for existing users.', fill=rgba('#C8D6E8'), font=FONT_SM)
    # metrics
    metric_positions = [(360, 162), (654, 162), (948, 162), (1242, 162)]
    metric_values = [('Throughput', '17 / week', PALETTE['mint']), ('Validation', '3 queued', PALETTE['amber']), ('Blocked', '1 task', PALETTE['coral']), ('Utilization', '82%', PALETTE['blue'])]
    for (x, y), (label, value, fill) in zip(metric_positions, metric_values):
        px_round(dd, (x, y, x + 274, y + 114), 22, (20, 34, 56, 218), rgba(fill), 1)
        dd.text((x + 18, y + 18), label, fill=rgba('#D2DEEC'), font=FONT_SM)
        dd.text((x + 18, y + 52), value, fill=rgba('#F6FBFF'), font=FONT_XL)
    # dashboard split panels
    px_round(dd, (360, 300, 980, 944), 28, (20, 34, 56, 214), rgba('#FFFFFF', 20), 1)
    dd.text((386, 328), 'Open office snapshot', fill=rgba('#F6FBFF'), font=FONT_MD)
    office_small = floor.resize((580, 540), Image.Resampling.NEAREST)
    dash.alpha_composite(office_small, (380, 360))
    px_round(dd, (1006, 300, 1574, 620), 28, (20, 34, 56, 214), rgba('#FFFFFF', 20), 1)
    dd.text((1032, 328), 'Attention queue', fill=rgba('#F6FBFF'), font=FONT_MD)
    q_items = [
        ('Blocked deployment path', 'Charlie + Shield', PALETTE['coral']),
        ('Validation needed on market brief', 'Ralph + Violet', PALETTE['amber']),
        ('CEO approval for new campaign branch', 'Quill + Echo', PALETTE['mint']),
    ]
    y = 364
    for title, by, fill in q_items:
        px_round(dd, (1028, y, 1548, y + 72), 18, (16, 27, 45, 230), rgba(fill), 1)
        dd.text((1046, y + 16), title, fill=rgba('#F6FBFF'), font=FONT_SM)
        dd.text((1046, y + 40), by, fill=rgba('#C7D6E9'), font=FONT_XS)
        y += 92
    px_round(dd, (1006, 640, 1574, 944), 28, (20, 34, 56, 214), rgba('#FFFFFF', 20), 1)
    dd.text((1032, 668), 'Specialist roster', fill=rgba('#F6FBFF'), font=FONT_MD)
    mini_ids = ['orion', 'codex', 'violet', 'charlie', 'ralph']
    y = 706
    for aid in mini_ids:
        card_y = y
        px_round(dd, (1028, card_y, 1548, card_y + 38), 16, (16, 27, 45, 210), rgba('#FFFFFF', 18), 1)
        portrait = Image.open(PORTRAITS / f'{aid}.png').resize((26, 26), Image.Resampling.NEAREST)
        dash.alpha_composite(portrait, (1040, card_y + 6))
        dd.text((1076, card_y + 9), AGENTS[aid]['name'], fill=rgba('#F6FBFF'), font=FONT_XS)
        dd.text((1184, card_y + 9), AGENTS[aid]['role'], fill=rgba('#BFD0E2'), font=FONT_XS)
        dd.text((1470, card_y + 9), 'Working' if aid != 'orion' else 'Sync', fill=rgba(AGENTS[aid]['accent']), font=FONT_XS)
        y += 48
    save_png(dash, DOCS / 'render_app_layout_v2_9_0.png')

    # avatar roster render
    roster = Image.new('RGBA', (1600, 1050), rgba(PALETTE['night']))
    rd = ImageDraw.Draw(roster)
    rd.text((42, 36), 'ClawTasker pixel avatar roster', fill=rgba('#F6FBFF'), font=FONT_XL)
    rd.text((44, 72), 'Original 24x32 sprites exported as 48x64 sheets, plus matching 32x32 portraits for cards and org-chart use.', fill=rgba('#C8D6E8'), font=FONT_SM)
    cols = 2
    card_w, card_h = 740, 150
    pad_x, pad_y = 40, 30
    items = list(AGENTS.items())
    for idx, (aid, meta) in enumerate(items):
        row, col = divmod(idx, cols)
        x = 42 + col * (card_w + pad_x)
        y = 120 + row * (card_h + pad_y)
        px_round(rd, (x, y, x + card_w, y + card_h), 22, (20, 34, 56, 220), rgba(meta['accent']), 1)
        portrait = Image.open(PORTRAITS / f'{aid}.png').resize((96, 96), Image.Resampling.NEAREST)
        roster.alpha_composite(portrait, (x + 20, y + 24))
        rd.text((x + 134, y + 22), meta['name'], fill=rgba('#F6FBFF'), font=FONT_MD)
        rd.text((x + 134, y + 48), meta['role'], fill=rgba('#BFD0E2'), font=FONT_XS)
        rd.text((x + 134, y + 70), meta['specialist'].title(), fill=rgba(meta['accent']), font=FONT_XS)
        sheet = Image.open(SPRITES / f'{aid}.png').convert('RGBA')
        preview = Image.new('RGBA', (48 * 5, 64), (0, 0, 0, 0))
        preview.alpha_composite(sheet.crop((0, 0, 48, 64)), (0, 0))
        preview.alpha_composite(sheet.crop((48, 0, 96, 64)), (48, 0))
        preview.alpha_composite(sheet.crop((96, 0, 144, 64)), (96, 0))
        preview.alpha_composite(sheet.crop((144, 0, 192, 64)), (144, 0))
        preview.alpha_composite(sheet.crop((192, 0, 240, 64)), (192, 0))
        preview = preview.resize((preview.width * 2, preview.height * 2), Image.Resampling.NEAREST)
        roster.alpha_composite(preview, (x + 300, y + 8))
        rd.text((x + 300, y + 114), 'Idle   Walk-L   Walk-R   Seated   Talk', fill=rgba('#C7D6E9'), font=FONT_XS)
    save_png(roster, DOCS / 'render_avatars_v2_9_0.png')

    # palette render
    palette = Image.new('RGBA', (1200, 360), rgba(PALETTE['night']))
    pd = ImageDraw.Draw(palette)
    pd.text((34, 28), 'ClawTasker 2.9.0 palette', fill=rgba('#F6FBFF'), font=FONT_XL)
    pd.text((36, 68), 'Calmer navy surfaces, warmer interior tones, and clear specialist accents for long working sessions.', fill=rgba('#C8D6E8'), font=FONT_SM)
    swatches = [
        ('Midnight Ink', PALETTE['night']), ('Deck Slate', PALETTE['deck']), ('Mist Paper', PALETTE['paper']),
        ('Mint Pulse', PALETTE['mint']), ('Blue Current', PALETTE['blue']), ('Soft Gold', PALETTE['amber']),
        ('Coral Alert', PALETTE['coral']), ('Lavender Sync', PALETTE['lavender']), ('Moss Review', PALETTE['green']),
    ]
    x = 34
    y = 120
    for name, hexv in swatches:
        px_round(pd, (x, y, x + 116, y + 116), 18, rgba(hexv), rgba('#243248'), 2)
        pd.text((x, y + 128), name, fill=rgba('#F6FBFF'), font=FONT_XS)
        pd.text((x, y + 146), hexv.upper(), fill=rgba('#AAB9CD'), font=FONT_XS)
        x += 128
        if x > 1040:
            x = 34
            y += 190
    save_png(palette, DOCS / 'render_palette_v2_9_0.png')


def sync_ui_public_assets():
    target = UI_PUBLIC / 'assets'
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(ASSETS, target)


def main():
    make_office_maps()
    for agent_id, palette in AGENTS.items():
        generate_agent_sheet(agent_id, palette)
        generate_portrait(agent_id, palette)
    draw_preview_renders()
    sync_ui_public_assets()


if __name__ == '__main__':
    main()
