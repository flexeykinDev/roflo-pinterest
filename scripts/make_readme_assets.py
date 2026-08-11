"""Generates the illustrative PNGs used in README.md (icon states, tray
menu mockup, workflow diagram). Not real screenshots — there's no
grabbing a real desktop here — but drawn with the exact same glyph/palette
tray.py uses, so they match the real app pixel-for-pixel where it counts
(the icon itself) and are an honest mockup everywhere else (the menu box,
the workflow arrows).

Run whenever tray.py's palette/menu changes:
    python scripts/make_readme_assets.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFont

from tray import _make_icon_image, COLOR_IDLE_TOP, COLOR_IDLE_BOTTOM  # noqa: E402

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "readme")
os.makedirs(OUT_DIR, exist_ok=True)

FONT_DIR = r"C:\Windows\Fonts"
SCALE = 2  # draw at 2x, downsample for crisp anti-aliased text/edges

TEXT = (36, 41, 47)
SUBTEXT = (101, 109, 118)
CARD_BG = (255, 255, 255)
CARD_BORDER = (225, 228, 232)


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size * SCALE)


def _save(img: Image.Image, name: str) -> None:
    final = img.resize((img.width // SCALE, img.height // SCALE), Image.LANCZOS)
    path = os.path.join(OUT_DIR, name)
    final.save(path)
    print("wrote", os.path.abspath(path))


def _text_w(draw: ImageDraw.ImageDraw, text: str, f) -> int:
    return draw.textbbox((0, 0), text, font=f)[2]


# ---------------------------------------------------------------- icons ---
def make_icon_states() -> None:
    reg = font("segoeui.ttf", 15)
    sub = font("segoeui.ttf", 12)

    states = [
        ("idle", "Обычное состояние", "готов к работе"),
        ("busy", "Идёт действие", "сканирую / ставлю обои"),
        ("error", "Ошибка", "смотри уведомление"),
    ]

    icon_size = 96 * SCALE
    pad = 36 * SCALE
    gap = 56 * SCALE
    col_w = icon_size
    w = pad * 2 + col_w * 3 + gap * 2
    h = pad * 2 + icon_size + 14 * SCALE + 22 * SCALE + 18 * SCALE

    img = Image.new("RGB", (w, h), CARD_BG)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((1, 1, w - 2, h - 2), radius=18 * SCALE, outline=CARD_BORDER, width=2 * SCALE)

    x = pad
    for state, title, subtitle in states:
        icon = _make_icon_image(state, final_size=icon_size)
        img.paste(icon, (x, pad), icon)

        ty = pad + icon_size + 14 * SCALE
        tw = _text_w(d, title, reg)
        d.text((x + col_w / 2 - tw / 2, ty), title, font=reg, fill=TEXT)

        sy = ty + 22 * SCALE
        sw = _text_w(d, subtitle, sub)
        d.text((x + col_w / 2 - sw / 2, sy), subtitle, font=sub, fill=SUBTEXT)

        x += col_w + gap

    _save(img, "icon-states.png")


# ----------------------------------------------------------------- menu ---
def make_menu_mockup() -> None:
    reg = font("segoeui.ttf", 16)
    bold = font("segoeuib.ttf", 16)
    small = font("segoeui.ttf", 13)
    caption = font("segoeui.ttf", 14)

    menu_w = 340 * SCALE
    row_h = 42 * SCALE
    items = [
        ("Новые обои", bold, TEXT, True),
        ("Обновить пул (scraper)", reg, TEXT, True),
        ("Войти в Pinterest", reg, TEXT, True),
        (None, None, None, None),  # separator
        ("В пуле: 42 · показано: 128", small, SUBTEXT, False),
        (None, None, None, None),  # separator
        ("Выход", reg, TEXT, True),
    ]

    cap_text = "Правый клик по иконке в трее открывает это меню"
    cap_h = 30 * SCALE

    body_h = sum(6 * SCALE if it[0] is None else row_h for it in items)
    pad_top = 14 * SCALE
    menu_h = pad_top * 2 + body_h

    icon_size = 40 * SCALE
    top_area_h = icon_size + 26 * SCALE

    w = menu_w + 60 * SCALE
    h = cap_h + top_area_h + menu_h + 20 * SCALE

    img = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(img)

    cw = _text_w(d, cap_text, caption)
    d.text((w / 2 - cw / 2, 4 * SCALE), cap_text, font=caption, fill=SUBTEXT)

    icon = _make_icon_image("idle", final_size=icon_size)
    icon_x = w / 2 - icon_size / 2
    icon_y = cap_h
    img.paste(icon, (int(icon_x), int(icon_y)), icon)

    line_x = w / 2
    line_y0 = icon_y + icon_size + 4 * SCALE
    line_y1 = cap_h + top_area_h
    dash = 6 * SCALE
    y = line_y0
    while y < line_y1:
        d.line((line_x, y, line_x, min(y + dash, line_y1)), fill=CARD_BORDER, width=2 * SCALE)
        y += dash * 2

    menu_x = w / 2 - menu_w / 2
    menu_y = cap_h + top_area_h
    d.rounded_rectangle(
        (menu_x, menu_y, menu_x + menu_w, menu_y + menu_h),
        radius=10 * SCALE, fill=CARD_BG, outline=CARD_BORDER, width=2 * SCALE,
    )

    y = menu_y + pad_top
    for text, f, color, enabled in items:
        if text is None:
            d.line((menu_x + 14 * SCALE, y + 3 * SCALE, menu_x + menu_w - 14 * SCALE, y + 3 * SCALE),
                   fill=CARD_BORDER, width=2 * SCALE)
            y += 6 * SCALE
            continue
        ty = y + row_h / 2 - (f.size / 2)
        d.text((menu_x + 22 * SCALE, ty), text, font=f, fill=color)
        y += row_h

    _save(img, "menu-mockup.png")


# ------------------------------------------------------------- workflow ---
def make_workflow() -> None:
    reg = font("segoeui.ttf", 15)
    num_font = font("segoeuib.ttf", 16)

    steps = [
        "Скачай\nRofloPinterest.exe",
        "Запусти —\nиконка в трее",
        "«Войти в\nPinterest»",
        "«Обновить\nпул»",
        "«Новые\nобои»",
    ]

    box_w, box_h = 150 * SCALE, 92 * SCALE
    gap = 46 * SCALE
    pad = 30 * SCALE
    badge_r = 15 * SCALE

    w = pad * 2 + len(steps) * box_w + (len(steps) - 1) * gap
    h = pad * 2 + badge_r * 2 + 10 * SCALE + box_h + 34 * SCALE

    img = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(img)

    x = pad
    cy_badge = pad + badge_r
    box_y = pad + badge_r * 2 + 10 * SCALE
    centers = []

    for i, step in enumerate(steps, start=1):
        cx = x + box_w / 2
        centers.append(cx)

        top, bottom = COLOR_IDLE_TOP, COLOR_IDLE_BOTTOM
        d.ellipse((cx - badge_r, cy_badge - badge_r, cx + badge_r, cy_badge + badge_r), fill=top)
        nw = _text_w(d, str(i), num_font)
        d.text((cx - nw / 2, cy_badge - num_font.size / 2 - 2 * SCALE), str(i), font=num_font, fill=(255, 255, 255))

        d.rounded_rectangle(
            (x, box_y, x + box_w, box_y + box_h),
            radius=14 * SCALE, fill=(246, 248, 250), outline=CARD_BORDER, width=2 * SCALE,
        )
        lines = step.split("\n")
        ly = box_y + box_h / 2 - (len(lines) * 20 * SCALE) / 2
        for line in lines:
            lw = _text_w(d, line, reg)
            d.text((cx - lw / 2, ly), line, font=reg, fill=TEXT)
            ly += 22 * SCALE

        if i < len(steps):
            ax0 = x + box_w + 6 * SCALE
            ax1 = x + box_w + gap - 6 * SCALE
            ay = box_y + box_h / 2
            d.line((ax0, ay, ax1, ay), fill=SUBTEXT, width=2 * SCALE)
            d.polygon(
                [(ax1, ay - 6 * SCALE), (ax1 + 8 * SCALE, ay), (ax1, ay + 6 * SCALE)],
                fill=SUBTEXT,
            )

        x += box_w + gap

    # looping arrow: "Новые обои" -> back to itself
    last_cx = centers[-1]
    loop_y = box_y + box_h + 14 * SCALE
    d.arc((last_cx - 40 * SCALE, loop_y, last_cx + 40 * SCALE, loop_y + 24 * SCALE), 20, 160, fill=SUBTEXT, width=2 * SCALE)
    d.polygon(
        [(last_cx - 40 * SCALE, loop_y + 10 * SCALE), (last_cx - 48 * SCALE, loop_y + 2 * SCALE), (last_cx - 34 * SCALE, loop_y - 2 * SCALE)],
        fill=SUBTEXT,
    )
    label = "повторяй, когда нужны новые обои"
    lw = _text_w(d, label, reg)
    d.text((last_cx - lw / 2, loop_y + 26 * SCALE), label, font=font("segoeui.ttf", 12), fill=SUBTEXT)

    _save(img, "workflow.png")


if __name__ == "__main__":
    make_icon_states()
    make_menu_mockup()
    make_workflow()
