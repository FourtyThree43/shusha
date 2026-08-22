"""Vector SVG & High-DPI icon asset pipeline for Shusha-DM.

This module provides vector icon definitions and rasterizers using Pillow
to produce crisp, modern UI icons at arbitrary scaling factors across
Linux (Wayland/X11), macOS (Retina), and Windows.
"""

from __future__ import annotations

from typing import Any

from PIL import Image, ImageDraw

# Vector drawing definitions for modern download manager UI icons
ICON_VECTORS: dict[str, Any] = {
    "add": "plus",
    "start": "play",
    "pause": "pause",
    "remove": "trash",
    "refresh": "refresh",
    "settings": "gear",
    "logs": "log",
    "folder": "folder",
    "link": "link",
    "torrent": "magnet",
    "speed": "gauge",
    "pieces": "grid",
    "peers": "users",
    "servers": "server",
    "up": "arrow-up",
    "down": "arrow-down",
    "clear": "broom",
    "copy": "copy",
    "batch": "list-plus",
}


def render_vector_icon(
    icon_name: str,
    size: int = 24,
    color: str = "#00bc8c",
    bg_color: str | None = None,
) -> Image.Image:
    """Render a clean geometric vector icon image dynamically.

    Args:
        icon_name: Name identifier of the icon.
        size: Width/Height of the target square canvas in pixels.
        color: Stroke/Fill hex color code.
        bg_color: Optional background fill color.

    Returns:
        A PIL RGBA Image object.
    """
    img = Image.new("RGBA", (size, size), bg_color or (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pad = int(size * 0.15)
    w = size - pad * 2
    stroke = max(2, int(size * 0.08))

    shape = ICON_VECTORS.get(icon_name, "circle")

    if shape == "plus":
        mid = size // 2
        draw.line([(mid, pad), (mid, size - pad)], fill=color, width=stroke)
        draw.line([(pad, mid), (size - pad, mid)], fill=color, width=stroke)

    elif shape == "play":
        points = [(pad + 2, pad), (size - pad, size // 2), (pad + 2, size - pad)]
        draw.polygon(points, fill=color)

    elif shape == "pause":
        bar_w = max(3, w // 4)
        draw.rectangle([pad, pad, pad + bar_w, size - pad], fill=color)
        draw.rectangle([size - pad - bar_w, pad, size - pad, size - pad], fill=color)

    elif shape == "trash":
        draw.rectangle([pad, pad + 4, size - pad, size - pad], outline=color, width=stroke)
        draw.line([pad - 2, pad + 4, size - pad + 2, pad + 4], fill=color, width=stroke)
        draw.line([size // 2 - 3, pad, size // 2 + 3, pad], fill=color, width=stroke)

    elif shape == "refresh":
        draw.arc([pad, pad, size - pad, size - pad], 45, 315, fill=color, width=stroke)
        draw.polygon([(size - pad, pad), (size - pad + 4, pad + 6), (size - pad - 4, pad + 6)], fill=color)

    elif shape == "arrow-up":
        mid = size // 2
        draw.line([(mid, size - pad), (mid, pad)], fill=color, width=stroke)
        draw.polygon([(mid, pad - 2), (mid - 5, pad + 6), (mid + 5, pad + 6)], fill=color)

    elif shape == "arrow-down":
        mid = size // 2
        draw.line([(mid, pad), (mid, size - pad)], fill=color, width=stroke)
        draw.polygon([(mid, size - pad + 2), (mid - 5, size - pad - 6), (mid + 5, size - pad - 6)], fill=color)

    elif shape == "gear":
        draw.ellipse([pad + 3, pad + 3, size - pad - 3, size - pad - 3], outline=color, width=stroke)
        draw.ellipse([pad + 6, pad + 6, size - pad - 6, size - pad - 6], fill=color)

    elif shape == "magnet":
        draw.arc([pad, pad, size - pad, size - pad + 4], 0, 180, fill=color, width=stroke)
        draw.line([pad, pad + 6, pad, size - pad], fill=color, width=stroke)
        draw.line([size - pad, pad + 6, size - pad, size - pad], fill=color, width=stroke)

    elif shape == "grid":
        step = w // 3
        for x in range(3):
            for y in range(3):
                bx = pad + x * step
                by = pad + y * step
                draw.rectangle([bx, by, bx + step - 2, by + step - 2], fill=color)

    elif shape == "list-plus":
        draw.line([(pad, pad + 3), (size - pad - 6, pad + 3)], fill=color, width=stroke)
        draw.line([(pad, pad + 9), (size - pad - 6, pad + 9)], fill=color, width=stroke)
        draw.line([(pad, pad + 15), (size - pad - 6, pad + 15)], fill=color, width=stroke)
        mid_x = size - pad
        mid_y = size - pad
        draw.line([(mid_x, mid_y - 4), (mid_x, mid_y + 4)], fill=color, width=stroke)
        draw.line([(mid_x - 4, mid_y), (mid_x + 4, mid_y)], fill=color, width=stroke)

    else:
        # Default circle
        draw.ellipse([pad, pad, size - pad, size - pad], outline=color, width=stroke)

    return img
