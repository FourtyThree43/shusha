"""Lucide icon vector pipeline and Tkinter PhotoImage generator (E11 Modern UI)."""

from __future__ import annotations

from typing import Any

from PIL import Image, ImageDraw, ImageTk

# Lucide-style icon drawing instructions
# Coordinates based on standard 24x24 viewBox grid
LUCIDE_ICONS: dict[str, list[tuple[str, Any]]] = {
    "dashboard": [
        ("rect", (3, 3, 7, 9)),
        ("rect", (14, 3, 7, 5)),
        ("rect", (14, 12, 7, 9)),
        ("rect", (3, 16, 7, 5)),
    ],
    "download": [
        ("line", (12, 4, 12, 16)),
        ("poly", ((8, 12), (12, 16), (16, 12))),
        ("line", (4, 20, 20, 20)),
    ],
    "upload": [
        ("line", (12, 16, 12, 4)),
        ("poly", ((8, 8), (12, 4), (16, 8))),
        ("line", (4, 20, 20, 20)),
    ],
    "inbox": [
        (
            "poly",
            ((4, 4), (20, 4), (20, 15), (16, 15), (14, 18), (10, 18), (8, 15), (4, 15)),
        ),
        ("line", (4, 15, 4, 20)),
        ("line", (4, 20, 20, 20)),
        ("line", (20, 20, 20, 15)),
    ],
    "video": [
        ("rect", (2, 5, 14, 14)),
        ("poly", ((16, 10), (22, 7), (22, 17), (16, 14))),
    ],
    "music": [
        ("circle", (6, 18, 3)),
        ("circle", (18, 16, 3)),
        ("line", (9, 18, 9, 6)),
        ("line", (21, 16, 21, 4)),
        ("line", (9, 6, 21, 4)),
    ],
    "play": [
        ("filled_poly", ((6, 4), (20, 12), (6, 20))),
    ],
    "pause": [
        ("rect", (6, 4, 4, 16)),
        ("rect", (14, 4, 4, 16)),
    ],
    "stop": [
        ("rect", (5, 5, 14, 14)),
    ],
    "trash": [
        ("line", (3, 6, 21, 6)),
        ("line", (19, 6, 19, 20)),
        ("line", (19, 20, 5, 20)),
        ("line", (5, 20, 5, 6)),
        ("line", (10, 11, 10, 17)),
        ("line", (14, 11, 14, 17)),
        ("line", (9, 6, 9, 3)),
        ("line", (9, 3, 15, 3)),
        ("line", (15, 3, 15, 6)),
    ],
    "plus": [
        ("line", (12, 5, 12, 19)),
        ("line", (5, 12, 19, 12)),
    ],
    "refresh": [
        ("arc", (4, 4, 16, 16, 45, 315)),
        ("poly", ((19, 4), (22, 9), (16, 9))),
    ],
    "search": [
        ("circle", (11, 11, 7)),
        ("line", (16, 16, 21, 21)),
    ],
    "filter": [
        ("poly", ((3, 4), (21, 4), (14, 12), (14, 19), (10, 21), (10, 12))),
    ],
    "settings": [
        ("circle", (12, 12, 3)),
        ("circle", (12, 12, 8)),
        ("line", (12, 2, 12, 5)),
        ("line", (12, 19, 12, 22)),
        ("line", (2, 12, 5, 12)),
        ("line", (19, 12, 22, 12)),
    ],
    "plugin": [
        ("rect", (4, 4, 16, 16)),
        ("circle", (12, 4, 3)),
        ("circle", (20, 12, 3)),
    ],
    "doctor": [
        ("poly", ((4, 4), (4, 12), (12, 20), (20, 12), (20, 4))),
        ("line", (12, 8, 12, 14)),
        ("line", (9, 11, 15, 11)),
    ],
    "activity": [
        ("poly", ((2, 12), (6, 12), (9, 4), (15, 20), (18, 12), (22, 12))),
    ],
    "terminal": [
        ("poly", ((4, 6), (10, 12), (4, 18))),
        ("line", (12, 18, 20, 18)),
    ],
    "globe": [
        ("circle", (12, 12, 9)),
        ("ellipse", (12, 12, 4, 9)),
        ("line", (3, 12, 21, 12)),
    ],
    "clipboard": [
        ("rect", (6, 4, 12, 17)),
        ("rect", (9, 2, 6, 4)),
    ],
    "shield": [
        ("poly", ((12, 3), (19, 6), (19, 12), (12, 21), (5, 12), (5, 6))),
    ],
    "folder": [
        ("poly", ((3, 5), (9, 5), (11, 8), (21, 8), (21, 19), (3, 19))),
    ],
    "check": [
        ("poly", ((4, 12), (9, 17), (20, 6))),
    ],
    "alert": [
        ("poly", ((12, 3), (22, 20), (2, 20))),
        ("line", (12, 9, 12, 13)),
        ("circle", (12, 17, 1)),
    ],
    "moon": [
        ("arc", (4, 4, 16, 16, 90, 270)),
    ],
    "sun": [
        ("circle", (12, 12, 4)),
        ("line", (12, 2, 12, 5)),
        ("line", (12, 19, 12, 22)),
        ("line", (2, 12, 5, 12)),
        ("line", (19, 12, 22, 12)),
    ],
}

_ICON_IMAGE_CACHE: dict[str, ImageTk.PhotoImage] = {}


def get_lucide_icon(
    name: str,
    size: int = 20,
    color: str = "#ffffff",
    stroke_width: int = 2,
) -> ImageTk.PhotoImage | None:
    """Generate a crisp, anti-aliased Lucide-style icon PhotoImage."""
    cache_key = f"{name}_{size}_{color}_{stroke_width}"
    if cache_key in _ICON_IMAGE_CACHE:
        return _ICON_IMAGE_CACHE[cache_key]

    instructions = LUCIDE_ICONS.get(name)
    if not instructions:
        # Fallback to download icon if missing
        instructions = LUCIDE_ICONS.get("download", [])

    # Render at 4x resolution for smooth anti-aliased downsampling
    scale = 4
    canvas_size = size * scale
    ratio = canvas_size / 24.0
    scaled_stroke = max(1, int(stroke_width * ratio))

    img = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    for item in instructions:
        cmd = item[0]
        params = item[1]

        if cmd == "line":
            x1, y1, x2, y2 = params
            draw.line(
                [(x1 * ratio, y1 * ratio), (x2 * ratio, y2 * ratio)],
                fill=color,
                width=scaled_stroke,
            )
        elif cmd == "rect":
            x, y, w, h = params
            draw.rounded_rectangle(
                [x * ratio, y * ratio, (x + w) * ratio, (y + h) * ratio],
                radius=max(1, int(2 * ratio)),
                outline=color,
                width=scaled_stroke,
            )
        elif cmd == "poly":
            points = [(pt[0] * ratio, pt[1] * ratio) for pt in params]
            draw.line(points, fill=color, width=scaled_stroke, joint="curve")
        elif cmd == "filled_poly":
            points = [(pt[0] * ratio, pt[1] * ratio) for pt in params]
            draw.polygon(points, fill=color)
        elif cmd == "circle":
            cx, cy, r = params
            draw.ellipse(
                [
                    (cx - r) * ratio,
                    (cy - r) * ratio,
                    (cx + r) * ratio,
                    (cy + r) * ratio,
                ],
                outline=color,
                width=scaled_stroke,
            )
        elif cmd == "ellipse":
            cx, cy, rx, ry = params
            draw.ellipse(
                [
                    (cx - rx) * ratio,
                    (cy - ry) * ratio,
                    (cx + rx) * ratio,
                    (cy + ry) * ratio,
                ],
                outline=color,
                width=scaled_stroke,
            )
        elif cmd == "arc":
            x, y, w, h, start_ang, end_ang = params
            draw.arc(
                [x * ratio, y * ratio, (x + w) * ratio, (y + h) * ratio],
                start=start_ang,
                end=end_ang,
                fill=color,
                width=scaled_stroke,
            )

    # High-quality Lanczos downsampling
    img_resized = img.resize((size, size), Image.Resampling.LANCZOS)
    try:
        photo = ImageTk.PhotoImage(img_resized)
        _ICON_IMAGE_CACHE[cache_key] = photo
        return photo
    except Exception:
        # Tk not initialized in headless test environment
        return None
