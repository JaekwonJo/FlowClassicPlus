from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter


BASE_DIR = Path(__file__).resolve().parent
APP_ICON_PATH = BASE_DIR / "icon.ico"
APP_PREVIEW_PATH = BASE_DIR / "icon_preview_app.png"
FOLDER_ICON_PATH = BASE_DIR / "folder_icon.ico"
FOLDER_PREVIEW_PATH = BASE_DIR / "icon_preview_folder.png"
ICON_SIZES = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]


def _mix_color(color_a, color_b, ratio):
    ratio = max(0.0, min(1.0, float(ratio)))
    return tuple(int(color_a[i] + (color_b[i] - color_a[i]) * ratio) for i in range(4))


def _new_canvas(size):
    return Image.new("RGBA", (size, size), (0, 0, 0, 0))


def _rounded_gradient_panel(size, rect, radius, top_color, bottom_color, outline):
    panel = _new_canvas(size)
    panel_draw = ImageDraw.Draw(panel)
    left, top, right, bottom = [int(v) for v in rect]
    height = max(1, bottom - top)
    for y in range(height):
        color = _mix_color(top_color, bottom_color, y / max(1, height - 1))
        panel_draw.line((left, top + y, right, top + y), fill=color, width=1)

    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(rect, radius=radius, fill=255)
    panel.putalpha(mask)

    outline_layer = _new_canvas(size)
    outline_draw = ImageDraw.Draw(outline_layer)
    outline_draw.rounded_rectangle(rect, radius=radius, outline=outline, width=max(4, size // 96))
    return Image.alpha_composite(panel, outline_layer)


def _draw_star(draw, center, radius, color):
    cx, cy = center
    draw.line((cx - radius, cy, cx + radius, cy), fill=color, width=max(2, radius // 2))
    draw.line((cx, cy - radius, cx, cy + radius), fill=color, width=max(2, radius // 2))
    draw.line((cx - radius * 0.65, cy - radius * 0.65, cx + radius * 0.65, cy + radius * 0.65), fill=color, width=max(1, radius // 3))
    draw.line((cx - radius * 0.65, cy + radius * 0.65, cx + radius * 0.65, cy - radius * 0.65), fill=color, width=max(1, radius // 3))


def _draw_flow_mark(draw, box, primary, accent, cutout):
    left, top, right, bottom = [float(v) for v in box]
    width = right - left
    height = bottom - top

    stroke = max(28, int(width * 0.13))
    radius = stroke // 2
    x0 = left + width * 0.08
    x1 = left + width * 0.54
    y_top = top + height * 0.18
    y_mid = top + height * 0.47
    y_bot = top + height * 0.74

    draw.rounded_rectangle((x0, y_top - stroke * 0.5, x0 + stroke, y_bot), radius=radius, fill=primary)
    draw.rounded_rectangle((x0 + stroke * 0.45, y_top - stroke * 0.5, x1, y_top + stroke * 0.5), radius=radius, fill=primary)
    draw.rounded_rectangle((x0 + stroke * 0.35, y_mid - stroke * 0.5, left + width * 0.82, y_mid + stroke * 0.5), radius=radius, fill=primary)

    highlight_box = (x0 + stroke * 0.20, y_top - stroke * 0.22, left + width * 0.68, y_top + stroke * 0.08)
    draw.rounded_rectangle(highlight_box, radius=max(8, radius // 2), fill=accent)
    draw.rounded_rectangle(
        (x0 + stroke * 0.15, y_mid - stroke * 0.18, left + width * 0.60, y_mid + stroke * 0.04),
        radius=max(8, radius // 2),
        fill=accent,
    )

    tri_w = width * 0.16
    tri_h = height * 0.19
    tri_cx = left + width * 0.68
    tri_cy = top + height * 0.60
    triangle = [
        (tri_cx - tri_w * 0.48, tri_cy - tri_h * 0.58),
        (tri_cx - tri_w * 0.48, tri_cy + tri_h * 0.58),
        (tri_cx + tri_w * 0.62, tri_cy),
    ]
    draw.polygon(triangle, fill=cutout)


def create_app_icon(master_size=1024):
    img = _new_canvas(master_size)

    shadow = _new_canvas(master_size)
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_rect = (
        master_size * 0.16,
        master_size * 0.19,
        master_size * 0.86,
        master_size * 0.89,
    )
    shadow_draw.rounded_rectangle(shadow_rect, radius=int(master_size * 0.17), fill=(15, 47, 57, 115))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=28))
    img.alpha_composite(shadow)

    panel = _rounded_gradient_panel(
        master_size,
        (
            master_size * 0.13,
            master_size * 0.12,
            master_size * 0.87,
            master_size * 0.86,
        ),
        radius=int(master_size * 0.18),
        top_color=(255, 247, 235, 255),
        bottom_color=(241, 184, 78, 255),
        outline=(16, 61, 74, 255),
    )
    img.alpha_composite(panel)

    accent = Image.new("RGBA", (master_size, master_size), (0, 0, 0, 0))
    accent_draw = ImageDraw.Draw(accent)
    accent_draw.ellipse(
        (
            master_size * 0.60,
            master_size * 0.20,
            master_size * 0.82,
            master_size * 0.42,
        ),
        fill=(123, 225, 218, 90),
    )
    accent = accent.filter(ImageFilter.GaussianBlur(radius=22))
    img.alpha_composite(accent)

    draw = ImageDraw.Draw(img)
    _draw_flow_mark(
        draw,
        (
            master_size * 0.24,
            master_size * 0.23,
            master_size * 0.78,
            master_size * 0.78,
        ),
        primary=(11, 57, 70, 255),
        accent=(86, 211, 214, 255),
        cutout=(249, 225, 162, 255),
    )
    _draw_star(draw, (master_size * 0.78, master_size * 0.25), int(master_size * 0.05), (84, 213, 221, 255))
    _draw_star(draw, (master_size * 0.26, master_size * 0.77), int(master_size * 0.032), (255, 252, 245, 220))
    return img


def create_folder_icon(master_size=1024):
    img = _new_canvas(master_size)

    shadow = _new_canvas(master_size)
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        (
            master_size * 0.15,
            master_size * 0.30,
            master_size * 0.87,
            master_size * 0.85,
        ),
        radius=int(master_size * 0.10),
        fill=(18, 54, 62, 110),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=24))
    img.alpha_composite(shadow)

    back = _new_canvas(master_size)
    back_draw = ImageDraw.Draw(back)
    back_draw.rounded_rectangle(
        (
            master_size * 0.17,
            master_size * 0.26,
            master_size * 0.56,
            master_size * 0.50,
        ),
        radius=int(master_size * 0.08),
        fill=(255, 233, 185, 255),
    )
    back_draw.rounded_rectangle(
        (
            master_size * 0.17,
            master_size * 0.34,
            master_size * 0.84,
            master_size * 0.79,
        ),
        radius=int(master_size * 0.10),
        fill=(255, 215, 112, 255),
        outline=(17, 60, 74, 255),
        width=max(6, master_size // 110),
    )
    img.alpha_composite(back)

    front = _new_canvas(master_size)
    front_draw = ImageDraw.Draw(front)
    left = int(master_size * 0.14)
    top = int(master_size * 0.40)
    right = int(master_size * 0.86)
    bottom = int(master_size * 0.84)
    height = bottom - top
    for y in range(height):
        color = _mix_color((255, 198, 70, 255), (232, 155, 35, 255), y / max(1, height - 1))
        front_draw.line((left, top + y, right, top + y), fill=color, width=1)
    front_draw.rounded_rectangle(
        (left, top, right, bottom),
        radius=int(master_size * 0.10),
        outline=(13, 57, 71, 255),
        width=max(6, master_size // 110),
    )
    mask = Image.new("L", (master_size, master_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((left, top, right, bottom), radius=int(master_size * 0.10), fill=255)
    front.putalpha(ImageChops.multiply(front.getchannel("A"), mask))
    img.alpha_composite(front)

    emblem_plate = _rounded_gradient_panel(
        master_size,
        (
            master_size * 0.29,
            master_size * 0.48,
            master_size * 0.71,
            master_size * 0.79,
        ),
        radius=int(master_size * 0.08),
        top_color=(255, 246, 231, 255),
        bottom_color=(249, 223, 164, 255),
        outline=(16, 61, 74, 220),
    )
    img.alpha_composite(emblem_plate)

    draw = ImageDraw.Draw(img)
    _draw_flow_mark(
        draw,
        (
            master_size * 0.35,
            master_size * 0.54,
            master_size * 0.66,
            master_size * 0.77,
        ),
        primary=(12, 60, 73, 255),
        accent=(91, 213, 214, 255),
        cutout=(250, 226, 168, 255),
    )
    _draw_star(draw, (master_size * 0.74, master_size * 0.30), int(master_size * 0.045), (92, 219, 224, 255))
    return img


def save_icon(image, ico_path, preview_path):
    image.save(preview_path, format="PNG")
    image.save(ico_path, format="ICO", sizes=ICON_SIZES)


def main():
    save_icon(create_app_icon(), APP_ICON_PATH, APP_PREVIEW_PATH)
    save_icon(create_folder_icon(), FOLDER_ICON_PATH, FOLDER_PREVIEW_PATH)
    print(f"Created {APP_ICON_PATH.name} and {FOLDER_ICON_PATH.name}")


if __name__ == "__main__":
    main()
