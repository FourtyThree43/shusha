import unittest

from PIL import Image

from shusha.models.svg_assets import (
    ICON_VECTORS,
    generate_svg_xml,
    get_svg_tk_image,
    render_vector_icon,
)


class TestSvgAssets(unittest.TestCase):
    def test_render_all_icon_vectors(self):
        for icon_key in ICON_VECTORS:
            img = render_vector_icon(icon_key, size=32, color="#00bc8c")
            self.assertIsInstance(img, Image.Image)
            self.assertEqual(img.size, (32, 32))
            self.assertEqual(img.mode, "RGBA")

    def test_render_unknown_fallback(self):
        img = render_vector_icon("non_existent_icon", size=24)
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.size, (24, 24))

    def test_generate_svg_xml(self):
        for icon_key in ICON_VECTORS:
            svg_xml = generate_svg_xml(icon_key, size=24, color="#3498db")
            self.assertTrue(svg_xml.startswith("<svg"))
            self.assertTrue(svg_xml.endswith("</svg>"))
            self.assertIn('viewBox="0 0 24 24"', svg_xml)

    def test_get_svg_tk_image_and_cache(self):
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            photo1 = get_svg_tk_image("dot-online", size=16)
            photo2 = get_svg_tk_image("dot-online", size=16)
            self.assertIsNotNone(photo1)
            self.assertEqual(photo1, photo2)
            root.destroy()
        except Exception:
            pass
