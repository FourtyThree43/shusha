"""Vector SVG & High-DPI icon asset pipeline for Shusha-DM.

This module provides vector icon generators (both raw W3C SVG XML and rasterized
Tkinter-compatible PhotoImage objects via Pillow) ensuring crisp, modern UI icons
at arbitrary scaling factors without relying on system fonts or emojis across
Linux (Wayland/X11), macOS (Retina), and Windows.
"""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageTk

# Vector icon definitions mapping
ICON_VECTORS: dict[str, str] = {
    "add": "plus",
    "start": "play",
    "pause": "pause",
    "stop": "square",
    "restart": "restart",
    "reconnect": "plug",
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
    "dot-online": "dot-online",
    "dot-offline": "dot-offline",
    "dot-warning": "dot-warning",
    "shield": "shield",
    "schedule": "clock",
    "network": "network",
}

# Image cache to retain references in Tkinter
_TK_IMAGE_CACHE: dict[str, ImageTk.PhotoImage] = {}


def generate_svg_xml(
    icon_name: str,
    size: int = 24,
    color: str = "#00bc8c",
) -> str:
    """Generate pure W3C compliant SVG XML text for an icon.

    Args:
        icon_name: Name of the icon.
        size: Viewbox dimension.
        color: Stroke/Fill hex color code.

    Returns:
        A valid SVG XML string.
    """
    shape = ICON_VECTORS.get(icon_name, "circle")

    if shape == "plus":
        body = (
            f'<line x1="12" y1="4" x2="12" y2="20" stroke="{color}" stroke-width="2.5" stroke-linecap="round"/>'
            f'<line x1="4" y1="12" x2="20" y2="12" stroke="{color}" stroke-width="2.5" stroke-linecap="round"/>'
        )
    elif shape == "play":
        body = f'<polygon points="6,4 20,12 6,20" fill="{color}"/>'
    elif shape == "pause":
        body = (
            f'<rect x="5" y="4" width="4" height="16" rx="1" fill="{color}"/>'
            f'<rect x="15" y="4" width="4" height="16" rx="1" fill="{color}"/>'
        )
    elif shape == "square":
        body = f'<rect x="4" y="4" width="16" height="16" rx="2" fill="{color}"/>'
    elif shape == "restart":
        body = (
            f'<path d="M4 12a8 8 0 0 1 14.93-4M20 12a8 8 0 0 1-14.93 4" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round"/>'
            f'<polyline points="20 4 20 10 14 10" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>'
        )
    elif shape == "plug":
        body = (
            f'<rect x="7" y="10" width="10" height="8" rx="2" fill="none" stroke="{color}" stroke-width="2"/>'
            f'<line x1="9" y1="4" x2="9" y2="10" stroke="{color}" stroke-width="2" stroke-linecap="round"/>'
            f'<line x1="15" y1="4" x2="15" y2="10" stroke="{color}" stroke-width="2" stroke-linecap="round"/>'
            f'<line x1="12" y1="18" x2="12" y2="22" stroke="{color}" stroke-width="2" stroke-linecap="round"/>'
        )
    elif shape == "dot-online":
        body = (
            '<circle cx="12" cy="12" r="7" fill="#00bc8c"/>'
            '<circle cx="12" cy="12" r="3" fill="#ffffff" opacity="0.6"/>'
        )
    elif shape == "dot-offline":
        body = (
            '<circle cx="12" cy="12" r="7" fill="#e74c3c"/>'
            '<circle cx="12" cy="12" r="3" fill="#ffffff" opacity="0.6"/>'
        )
    elif shape == "dot-warning":
        body = (
            '<circle cx="12" cy="12" r="7" fill="#f39c12"/>'
            '<circle cx="12" cy="12" r="3" fill="#ffffff" opacity="0.6"/>'
        )
    else:
        body = f'<circle cx="12" cy="12" r="8" stroke="{color}" stroke-width="2" fill="none"/>'

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">'
        f"{body}</svg>"
    )


def render_vector_icon(
    icon_name: str,
    size: int = 24,
    color: str = "#00bc8c",
    bg_color: str | None = None,
) -> Image.Image:
    """Render a clean geometric vector icon image dynamically using Pillow.

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

    elif shape == "square":
        draw.rectangle([pad, pad, size - pad, size - pad], fill=color)

    elif shape == "restart":
        draw.arc([pad, pad, size - pad, size - pad], 45, 315, fill=color, width=stroke)
        draw.polygon(
            [(size - pad, pad), (size - pad + 4, pad + 6), (size - pad - 4, pad + 6)],
            fill=color,
        )

    elif shape == "plug":
        mid_x = size // 2
        draw.rectangle(
            [pad + 3, pad + 6, size - pad - 3, size - pad - 2],
            outline=color,
            width=stroke,
        )
        draw.line([(pad + 5, pad), (pad + 5, pad + 6)], fill=color, width=stroke)
        draw.line([(size - pad - 5, pad), (size - pad - 5, pad + 6)], fill=color, width=stroke)
        draw.line([(mid_x, size - pad - 2), (mid_x, size - pad + 3)], fill=color, width=stroke)

    elif shape == "trash":
        draw.rectangle([pad, pad + 4, size - pad, size - pad], outline=color, width=stroke)
        draw.line([(pad - 2, pad + 4), (size - pad + 2, pad + 4)], fill=color, width=stroke)
        draw.line([(size // 2 - 3, pad), (size // 2 + 3, pad)], fill=color, width=stroke)

    elif shape == "refresh":
        draw.arc([pad, pad, size - pad, size - pad], 45, 315, fill=color, width=stroke)
        draw.polygon(
            [(size - pad, pad), (size - pad + 4, pad + 6), (size - pad - 4, pad + 6)],
            fill=color,
        )

    elif shape == "arrow-up":
        mid = size // 2
        draw.line([(mid, size - pad), (mid, pad)], fill=color, width=stroke)
        draw.polygon([(mid, pad - 2), (mid - 5, pad + 6), (mid + 5, pad + 6)], fill=color)

    elif shape == "arrow-down":
        mid = size // 2
        draw.line([(mid, pad), (mid, size - pad)], fill=color, width=stroke)
        draw.polygon(
            [(mid, size - pad + 2), (mid - 5, size - pad - 6), (mid + 5, size - pad - 6)],
            fill=color,
        )

    elif shape == "gear":
        draw.ellipse([pad + 3, pad + 3, size - pad - 3, size - pad - 3], outline=color, width=stroke)
        draw.ellipse([pad + 6, pad + 6, size - pad - 6, size - pad - 6], fill=color)

    elif shape == "magnet":
        draw.arc([pad, pad, size - pad, size - pad + 4], 0, 180, fill=color, width=stroke)
        draw.line([(pad, pad + 6), (pad, size - pad)], fill=color, width=stroke)
        draw.line([(size - pad, pad + 6), (size - pad, size - pad)], fill=color, width=stroke)

    elif shape == "grid":
        step = max(3, w // 3)
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

    elif shape == "dot-online":
        mid = size // 2
        r = max(4, size // 3)
        draw.ellipse([mid - r, mid - r, mid + r, mid + r], fill="#00bc8c")
        draw.ellipse([mid - r // 2, mid - r // 2, mid + r // 2, mid + r // 2], fill="#a3e9d4")

    elif shape == "dot-offline":
        mid = size // 2
        r = max(4, size // 3)
        draw.ellipse([mid - r, mid - r, mid + r, mid + r], fill="#e74c3c")
        draw.ellipse([mid - r // 2, mid - r // 2, mid + r // 2, mid + r // 2], fill="#f5b7b1")

    elif shape == "dot-warning":
        mid = size // 2
        r = max(4, size // 3)
        draw.ellipse([mid - r, mid - r, mid + r, mid + r], fill="#f39c12")
        draw.ellipse([mid - r // 2, mid - r // 2, mid + r // 2, mid + r // 2], fill="#fdebd0")

    elif shape == "clock":
        draw.ellipse([pad, pad, size - pad, size - pad], outline=color, width=stroke)
        mid = size // 2
        draw.line([(mid, mid), (mid, pad + 3)], fill=color, width=stroke)
        draw.line([(mid, mid), (size - pad - 3, mid)], fill=color, width=stroke)

    elif shape == "shield":
        points = [
            (pad, pad),
            (size - pad, pad),
            (size - pad, size // 2),
            (size // 2, size - pad),
            (pad, size // 2),
        ]
        draw.polygon(points, outline=color, width=stroke)

    elif shape == "folder":
        draw.rectangle([pad, pad + 4, size - pad, size - pad], outline=color, width=stroke)
        draw.line([(pad, pad + 4), (pad + 6, pad)], fill=color, width=stroke)
        draw.line([(pad + 6, pad), (pad + 12, pad)], fill=color, width=stroke)
        draw.line([(pad + 12, pad), (pad + 14, pad + 4)], fill=color, width=stroke)

    else:
        # Default circle
        draw.ellipse([pad, pad, size - pad, size - pad], outline=color, width=stroke)

    return img


def get_svg_tk_image(
    icon_name: str,
    size: int = 20,
    color: str = "#00bc8c",
    bg_color: str | None = None,
) -> ImageTk.PhotoImage | None:
    """Get a Tkinter-compatible PhotoImage for a vector icon with caching.

    Args:
        icon_name: Icon name identifier.
        size: Width/Height in pixels.
        color: Primary color hex.
        bg_color: Optional background color.

    Returns:
        ImageTk.PhotoImage or None if Tkinter display not available.
    """
    cache_key = f"{icon_name}_{size}_{color}_{bg_color}"
    if cache_key in _TK_IMAGE_CACHE:
        return _TK_IMAGE_CACHE[cache_key]

    try:
        pil_img = render_vector_icon(icon_name, size=size, color=color, bg_color=bg_color)
        photo = ImageTk.PhotoImage(pil_img)
        _TK_IMAGE_CACHE[cache_key] = photo
        return photo
    except Exception:
        return None
