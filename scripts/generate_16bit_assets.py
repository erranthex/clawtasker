#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
THIRD = ROOT / 'third_party'
ASSETS = ROOT / 'web' / 'assets'
TEXTURES = ASSETS / 'textures'
SPRITES = ASSETS / 'sprites'
TEXTURES.mkdir(parents=True, exist_ok=True)
SPRITES.mkdir(parents=True, exist_ok=True)

OGA = Image.open(THIRD / 'oga_indoor_tileset_baseline.png').convert('RGBA')
TINY = Image.open(THIRD / 'kenney_tiny-town_preview.png').convert('RGBA')

MAGENTA = (255, 0, 255)
SKY_BG = (65, 153, 212)


def transparent_oga(img: Image.Image) -> Image.Image:
    img = img.copy()
    data = []
    for px in img.getdata():
        if px[:3] == MAGENTA:
            data.append((0, 0, 0, 0))
        else:
            data.append(px)
    img.putdata(data)
    return img


def transparent_tiny(img: Image.Image) -> Image.Image:
    img = img.copy()
    data = []
    for r, g, b, a in img.getdata():
        if abs(r - SKY_BG[0]) < 25 and abs(g - SKY_BG[1]) < 40 and abs(b - SKY_BG[2]) < 40:
            data.append((0, 0, 0, 0))
        else:
            data.append((r, g, b, a))
    img.putdata(data)
    return img


def crop_oga(box):
    return transparent_oga(OGA.crop(box))


def crop_tiny(box):
    return transparent_tiny(TINY.crop(box))


def scale(img: Image.Image, factor: int) -> Image.Image:
    return img.resize((img.width * factor, img.height * factor), Image.NEAREST)


def alpha_paste(dest: Image.Image, src: Image.Image, x: int, y: int) -> None:
    dest.alpha_composite(src, (int(x), int(y)))


def px(draw, x, y, w, h, fill, outline=None):
    draw.rectangle([x, y, x + w - 1, y + h - 1], fill=fill, outline=outline)


# -- Source snippets -------------------------------------------------------
rug_green = crop_oga((0, 0, 48, 32))
rug_red = crop_oga((48, 0, 96, 32))
chair_front = crop_oga((0, 48, 16, 80))
chair_side = crop_oga((16, 48, 32, 80))
chair_side_2 = crop_oga((32, 48, 48, 80))
table_round = crop_oga((64, 48, 96, 80))
bookshelf = crop_oga((48, 112, 64, 144))
board_tile = crop_oga((80, 128, 112, 144))
wood_left = crop_oga((0, 144, 16, 192))
wood_right = crop_oga((64, 144, 80, 192))
wood_bottom = crop_oga((16, 176, 64, 192))
torch = crop_oga((96, 16, 112, 32))
stone_tile = crop_tiny((0, 160, 16, 176))
path_tile = crop_tiny((16, 64, 32, 80))
leaf_tile = crop_tiny((192, 48, 208, 64))
bush_tile = crop_tiny((320, 32, 336, 48))
flower_tile = crop_tiny((80, 64, 96, 80))
wood_panel = crop_oga((16, 176, 32, 192))

# save source snippets for transparency
for name, im in {
    'rug_green': rug_green, 'rug_red': rug_red, 'chair_front': chair_front,
    'chair_side': chair_side, 'chair_side_2': chair_side_2, 'table_round': table_round,
    'bookshelf': bookshelf, 'board_tile': board_tile, 'wood_left': wood_left,
    'wood_right': wood_right, 'wood_bottom': wood_bottom, 'torch': torch,
}.items():
    scale(im, 2).save(TEXTURES / f'{name}.png')


# -- Utility drawing -------------------------------------------------------
def draw_parquet_floor(dest: Image.Image, draw: ImageDraw.ImageDraw, x0: int, y0: int, w: int, h: int) -> None:
    base1 = (128, 86, 49, 255)
    base2 = (146, 100, 60, 255)
    base3 = (108, 73, 45, 255)
    tile_w = 48
    tile_h = 24
    for y in range(y0, y0 + h, tile_h):
        row = (y - y0) // tile_h
        for x in range(x0, x0 + w, tile_w):
            col = (x - x0) // tile_w
            color = [base1, base2, base3][(row + col) % 3]
            px(draw, x, y, tile_w, tile_h, color)
            for line in range(x + 8, min(x + tile_w, x0 + w), 12):
                px(draw, line, y, 2, tile_h, (91, 58, 37, 180))
            if row % 2:
                px(draw, x, y, tile_w, 2, (164, 122, 77, 120))
    for y in range(y0, y0 + h, 24):
        draw.line((x0, y, x0 + w, y), fill=(94, 60, 38, 80), width=1)


def make_plant(scale_factor=2) -> Image.Image:
    pot = Image.new('RGBA', (16, 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(pot)
    px(d, 4, 14, 8, 8, (131, 88, 59, 255), (77, 47, 30, 255))
    px(d, 3, 13, 10, 2, (166, 115, 76, 255), (77, 47, 30, 255))
    foliage = bush_tile.crop((0, 0, 16, 16))
    foliage = scale(foliage, 1)
    pot.alpha_composite(foliage, (0, 0))
    return scale(pot, scale_factor)


def make_window() -> Image.Image:
    win = Image.new('RGBA', (120, 72), (0, 0, 0, 0))
    d = ImageDraw.Draw(win)
    px(d, 0, 0, 120, 72, (209, 234, 255, 255), (112, 147, 184, 255))
    px(d, 4, 4, 112, 64, (154, 206, 250, 255))
    px(d, 58, 4, 4, 64, (117, 161, 206, 255))
    px(d, 4, 34, 112, 4, (117, 161, 206, 255))
    px(d, 8, 8, 104, 16, (227, 244, 255, 90))
    return win


def make_desk(width=116, height=56, double_monitor=False, accent=(103, 193, 245, 255)) -> Image.Image:
    desk = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(desk)
    # desk body
    px(d, 0, 14, width, height - 14, (145, 101, 62, 255), (76, 51, 29, 255))
    px(d, 0, 18, width, 10, (168, 120, 78, 255))
    for lx in (8, width - 12):
        px(d, lx, height - 12, 6, 12, (91, 58, 37, 255))
    px(d, 18, 8, 28, 18, (56, 71, 97, 255), (24, 33, 48, 255))
    px(d, 20, 10, 24, 14, accent)
    px(d, 29, 26, 6, 6, (27, 39, 60, 255))
    if double_monitor:
        px(d, 54, 9, 24, 16, (56, 71, 97, 255), (24, 33, 48, 255))
        px(d, 56, 11, 20, 12, (158, 231, 255, 255))
        px(d, 63, 24, 6, 5, (27, 39, 60, 255))
    px(d, 18, 34, 44, 8, (233, 238, 244, 255), (122, 132, 149, 255))
    px(d, width - 24, 26, 8, 8, (197, 237, 170, 255), (68, 104, 57, 255))
    px(d, width - 22, 20, 4, 6, (95, 169, 76, 255))
    return desk


def make_sofa(width=108) -> Image.Image:
    h = 56
    img = Image.new('RGBA', (width, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    px(d, 0, 18, width, 26, (71, 104, 145, 255), (34, 53, 78, 255))
    px(d, 10, 8, width - 20, 16, (88, 125, 172, 255), (34, 53, 78, 255))
    px(d, 0, 14, 12, 30, (62, 92, 128, 255), (34, 53, 78, 255))
    px(d, width - 12, 14, 12, 30, (62, 92, 128, 255), (34, 53, 78, 255))
    px(d, 10, 44, width - 20, 8, (50, 72, 99, 255), (34, 53, 78, 255))
    return img


def make_coffee() -> Image.Image:
    img = Image.new('RGBA', (110, 70), (0,0,0,0))
    d = ImageDraw.Draw(img)
    px(d, 0, 22, 110, 28, (131, 88, 59, 255), (77, 47, 30, 255))
    px(d, 10, 10, 30, 20, (55, 63, 82, 255), (23, 29, 40, 255))
    px(d, 14, 14, 22, 12, (199, 234, 255, 255))
    for idx in range(3):
        px(d, 58 + idx * 14, 14, 8, 8, (243, 223, 176, 255), (166, 132, 77, 255))
        px(d, 60 + idx * 14, 10, 4, 4, (255,255,255,180))
    for lx in (8, 96):
        px(d, lx, 48, 6, 16, (91,58,37,255))
    return img


def make_board_wall(board_tile: Image.Image) -> Image.Image:
    tile = scale(board_tile, 2)
    w, h = tile.size
    board = Image.new('RGBA', (w * 2 + 20, h * 3 + 32), (0, 0, 0, 0))
    for row in range(3):
        for col in range(2):
            alpha_paste(board, tile, 10 + col * w, 10 + row * h)
    d = ImageDraw.Draw(board)
    note_colors = [(255, 222, 121, 255), (122, 210, 255, 255), (255, 168, 139, 255), (162, 239, 163, 255)]
    notes = [(18, 18), (80, 26), (34, 68), (98, 78), (30, 120), (86, 132), (24, 164), (88, 182)]
    for i, (x, y) in enumerate(notes):
        px(d, x, y, 18, 14, note_colors[i % len(note_colors)], (120, 82, 46, 255))
        px(d, x + 6, y + 4, 6, 2, (120, 82, 46, 180))
    return board


def make_review_station() -> Image.Image:
    img = Image.new('RGBA', (120, 74), (0,0,0,0))
    d = ImageDraw.Draw(img)
    px(d, 0, 22, 120, 28, (145, 101, 62, 255), (76,51,29,255))
    px(d, 16, 0, 52, 28, (44, 61, 88, 255), (21, 29, 40, 255))
    px(d, 20, 4, 44, 20, (196, 237, 255, 255))
    for i in range(3):
        px(d, 82, 6 + i * 14, 22, 10, (252, 249, 237, 255), (172, 160, 121, 255))
        px(d, 86, 10 + i * 14, 14, 2, (160, 156, 137, 255))
    for lx in (10, 104):
        px(d, lx, 48, 6, 18, (91,58,37,255))
    return img


def make_lamp() -> Image.Image:
    lamp = scale(torch, 2)
    return lamp


def office_background() -> Image.Image:
    W, H = 1360, 820
    img = Image.new('RGBA', (W, H), (9, 17, 31, 255))
    d = ImageDraw.Draw(img)
    # background walls and floor
    px(d, 0, 0, W, 152, (190, 222, 255, 255))
    px(d, 0, 112, W, 40, (162, 196, 236, 255))
    px(d, 0, 152, W, H - 152, (127, 89, 55, 255))
    draw_parquet_floor(img, d, 0, 152, W, H - 152)
    # side skirting and soft partitions
    px(d, 0, 150, W, 8, (100, 67, 42, 255))
    for x in (430, 820, 1120):
        px(d, x, 224, 6, 360, (97, 66, 41, 255))
        px(d, x - 6, 218, 18, 10, (132, 93, 62, 255))
    # windows
    window = make_window()
    for wx in (48, 202, 356, 916, 1070, 1224):
        alpha_paste(img, window, wx, 34)
    # rugs
    alpha_paste(img, scale(rug_green, 2), 256, 130)
    alpha_paste(img, scale(rug_red, 2), 590, 458)
    alpha_paste(img, scale(rug_red, 2), 94, 620)
    # board wall background strip
    px(d, 1150, 150, 182, 220, (74, 101, 128, 255), (43, 59, 80, 255))
    px(d, 1162, 162, 158, 196, (230, 212, 188, 255), (153, 123, 89, 255))
    board = make_board_wall(board_tile)
    alpha_paste(img, board, 1174, 174)
    # chief / ceo desks
    desk_a = make_desk(126, 58, True, (121, 223, 255, 255))
    desk_b = make_desk(126, 58, True, (121, 223, 255, 255))
    alpha_paste(img, desk_a, 72, 180)
    alpha_paste(img, scale(chair_side, 2), 102, 230)
    alpha_paste(img, desk_b, 276, 180)
    alpha_paste(img, scale(chair_side, 2), 306, 230)
    # desk pods
    desk_blue = make_desk(116, 56, True, (106, 178, 255, 255))
    desk_green = make_desk(116, 56, True, (124, 229, 182, 255))
    desk_amber = make_desk(116, 56, True, (255, 207, 120, 255))
    desk_pink = make_desk(116, 56, True, (241, 177, 255, 255))
    pod_positions = [
        (82, 282, desk_blue), (228, 282, desk_blue), (82, 394, desk_blue), (228, 394, desk_blue),
        (490, 282, desk_green), (636, 282, desk_green), (490, 394, desk_green), (636, 394, desk_green),
        (862, 282, desk_amber), (1008, 282, desk_amber), (862, 394, desk_amber), (1008, 394, desk_amber),
        (888, 620, desk_pink), (1034, 620, desk_pink), (1180, 620, desk_pink),
    ]
    for x, y, desk in pod_positions:
        alpha_paste(img, desk, x, y)
        alpha_paste(img, scale(chair_side_2, 2), x + 28, y + 52)
    # QA/review desks
    qa_desk = make_desk(122, 56, True, (248, 212, 116, 255))
    alpha_paste(img, qa_desk, 1158, 422)
    alpha_paste(img, scale(chair_side, 2), 1188, 472)
    alpha_paste(img, make_review_station(), 1160, 520)
    # scrum table and chairs
    alpha_paste(img, scale(table_round, 3), 612, 530)
    chair = scale(chair_front, 2)
    chair_side_big = scale(chair_side, 2)
    for x, y, asset in [
        (646, 500, chair), (736, 510, chair_side_big), (772, 582, chair),
        (694, 632, chair), (596, 606, chair_side_big), (578, 534, chair)
    ]:
        alpha_paste(img, asset, x, y)
    # lounge, coffee and shelf
    alpha_paste(img, make_sofa(116), 84, 652)
    alpha_paste(img, make_sofa(116), 234, 652)
    alpha_paste(img, make_coffee(), 386, 654)
    alpha_paste(img, scale(bookshelf, 3), 534, 624)
    # plants and lights
    plant = make_plant(3)
    for x, y in [(34, 166), (210, 166), (454, 166), (790, 166), (1088, 166), (1314, 166), (448, 672), (1290, 620), (784, 704)]:
        alpha_paste(img, plant, x, y)
    lamp = make_lamp()
    for x, y in [(24, 120), (240, 120), (456, 120), (872, 120), (1088, 120), (1304, 120)]:
        alpha_paste(img, lamp, x, y)
    # labels and subtle zone boxes (painted into map)
    label_specs = [
        ('CEO', 110, 154), ('CHIEF', 316, 154), ('ENGINEERING', 98, 248), ('RESEARCH', 522, 248),
        ('OPS + SECURITY', 872, 248), ('AGILE WALL', 1186, 154), ('SCRUM TABLE', 638, 486),
        ('VALIDATION', 1178, 392), ('STUDIO', 946, 586), ('LOUNGE', 114, 620),
    ]
    for text, x, y in label_specs:
        px(d, x, y, max(72, len(text) * 9), 18, (14, 24, 40, 215), (67, 92, 121, 255))
        d.text((x + 6, y + 3), text, fill=(236, 244, 255, 255))
    return img


# -- Sprites ---------------------------------------------------------------
AGENTS = {
    'orion':  {'skin':'#f2c4a1','hair':'#244054','outfit':'#39c7ba','trim':'#f2cf69','boots':'#17344e'},
    'codex':  {'skin':'#f0c39f','hair':'#1f2444','outfit':'#5f85ff','trim':'#6fd5ff','boots':'#18203e'},
    'violet': {'skin':'#efc29d','hair':'#312551','outfit':'#7b78ff','trim':'#a79eff','boots':'#1a1b3b'},
    'scout':  {'skin':'#efc29d','hair':'#425329','outfit':'#7cd39d','trim':'#9ef0d2','boots':'#223528'},
    'charlie':{'skin':'#eec19d','hair':'#483025','outfit':'#f2a654','trim':'#f4d17a','boots':'#432819'},
    'ralph':  {'skin':'#efc4a5','hair':'#254032','outfit':'#5ed393','trim':'#b2ea86','boots':'#173022'},
    'shield': {'skin':'#f1c1a2','hair':'#4a2030','outfit':'#ff7c82','trim':'#ffb1a3','boots':'#34151f'},
    'quill':  {'skin':'#efc3a2','hair':'#2c3247','outfit':'#98a7c8','trim':'#c9d3ea','boots':'#222737'},
    'pixel':  {'skin':'#f0c5a9','hair':'#452149','outfit':'#f57ad4','trim':'#ffbbef','boots':'#311c35'},
    'echo':   {'skin':'#efc19b','hair':'#425329','outfit':'#a7dd58','trim':'#e7f58f','boots':'#35441f'},
}


def hex_rgba(h: str):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4)) + (255,)


def draw_sprite_frame(palette, pose='idle') -> Image.Image:
    img = Image.new('RGBA', (32, 48), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    outline = (38, 34, 58, 255)
    skin = hex_rgba(palette['skin'])
    hair = hex_rgba(palette['hair'])
    outfit = hex_rgba(palette['outfit'])
    trim = hex_rgba(palette['trim'])
    boots = hex_rgba(palette['boots'])
    skin_shadow = tuple(max(0, c - 24) for c in skin[:3]) + (255,)
    cloth_shadow = tuple(max(0, c - 30) for c in outfit[:3]) + (255,)
    # shadow
    px(d, 10, 42, 12, 3, (0, 0, 0, 80))
    # head
    px(d, 11, 4, 10, 9, skin, outline)
    px(d, 10, 3, 12, 4, hair)
    px(d, 11, 5, 2, 2, (255, 237, 215, 255))
    px(d, 14, 8, 1, 1, (53, 44, 42, 255))
    px(d, 18, 8, 1, 1, (53, 44, 42, 255))
    # neck
    px(d, 14, 13, 4, 2, skin_shadow)
    # torso/cape
    px(d, 10, 15, 12, 13, outfit, outline)
    px(d, 22, 15, 2, 9, trim)
    px(d, 9, 17, 2, 8, trim)
    px(d, 12, 17, 8, 4, cloth_shadow)
    # arms
    left_arm = {'idle': (7, 17, 3, 10), 'walk_a': (7, 18, 3, 11), 'walk_b': (8, 16, 3, 10), 'seated': (8, 18, 3, 9), 'talk': (7, 14, 3, 11)}[pose]
    right_arm = {'idle': (22, 17, 3, 10), 'walk_a': (21, 16, 3, 10), 'walk_b': (22, 18, 3, 11), 'seated': (21, 18, 3, 9), 'talk': (23, 12, 3, 12)}[pose]
    px(d, *left_arm, skin, outline)
    px(d, *right_arm, skin, outline)
    # belt/trim
    px(d, 11, 27, 10, 2, trim)
    # legs
    if pose == 'seated':
        px(d, 10, 30, 5, 6, boots, outline)
        px(d, 17, 30, 5, 6, boots, outline)
        px(d, 5, 35, 8, 3, boots)
        px(d, 19, 35, 8, 3, boots)
    elif pose == 'walk_a':
        px(d, 11, 29, 4, 11, boots, outline)
        px(d, 18, 29, 4, 9, boots, outline)
        px(d, 17, 36, 6, 3, boots)
    elif pose == 'walk_b':
        px(d, 11, 29, 4, 9, boots, outline)
        px(d, 18, 29, 4, 11, boots, outline)
        px(d, 10, 36, 6, 3, boots)
    else:
        px(d, 11, 29, 4, 11, boots, outline)
        px(d, 18, 29, 4, 11, boots, outline)
    # small highlight
    px(d, 12, 18, 2, 2, (255,255,255,55))
    return img


def make_sheet(palette) -> Image.Image:
    poses = ['idle', 'walk_a', 'walk_b', 'seated', 'talk']
    sheet = Image.new('RGBA', (32 * len(poses), 48), (0,0,0,0))
    for i, pose in enumerate(poses):
        frame = draw_sprite_frame(palette, pose)
        alpha_paste(sheet, frame, i * 32, 0)
    return sheet


def main():
    office = office_background()
    office.save(TEXTURES / 'office_map_16bit.png')
    # smaller thumbnails for docs if needed
    office.resize((1020, 615), Image.NEAREST).save(TEXTURES / 'office_map_16bit_thumb.png')
    for agent_id, palette in AGENTS.items():
        make_sheet(palette).save(SPRITES / f'{agent_id}.png')
    # small decorative textures
    scale(path_tile, 2).save(TEXTURES / 'path_tile.png')
    scale(stone_tile, 2).save(TEXTURES / 'stone_tile.png')
    scale(leaf_tile, 3).save(TEXTURES / 'leaf_tile.png')
    print('Generated assets into', ASSETS)


if __name__ == '__main__':
    main()
