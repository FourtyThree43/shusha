import unittest

from PIL import Image

from shusha.models.svg_assets import ICON_VECTORS, render_vector_icon


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
