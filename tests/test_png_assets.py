from pathlib import Path
import unittest

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/flowz"


class PngAssetTests(unittest.TestCase):
    def test_logo_is_a_square_png(self):
        with Image.open(PLUGIN / "assets/logo.png") as logo:
            self.assertEqual(logo.format, "PNG")
            self.assertEqual(logo.width, logo.height)

    def test_icon_is_square_with_transparent_corners_and_opaque_center(self):
        with Image.open(PLUGIN / "assets/icon.png") as icon:
            self.assertEqual(icon.format, "PNG")
            self.assertEqual(icon.width, icon.height)
            self.assertEqual(icon.mode, "RGBA")
            alpha = icon.getchannel("A")
            self.assertEqual(alpha.getpixel((0, 0)), 0)
            self.assertEqual(alpha.getpixel((icon.width - 1, 0)), 0)
            self.assertEqual(alpha.getpixel((0, icon.height - 1)), 0)
            self.assertEqual(alpha.getpixel((icon.width - 1, icon.height - 1)), 0)
            self.assertGreater(alpha.getpixel((icon.width // 2, icon.height // 2)), 0)


if __name__ == "__main__":
    unittest.main()
