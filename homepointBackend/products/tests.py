import io
import os
import tempfile
from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from PIL import Image

from .utils.image import optimize_and_resize_image


class OptimizeAndResizeImageTests(SimpleTestCase):
    def make_image(self, size=(1000, 500)):
        image_bytes = io.BytesIO()
        Image.new("RGB", size, "red").save(image_bytes, format="PNG")
        return image_bytes.getvalue()

    def test_optimizes_file_like_source(self):
        optimized = optimize_and_resize_image(io.BytesIO(self.make_image()))

        with Image.open(optimized) as image:
            self.assertEqual(image.format, "WEBP")
            self.assertEqual(image.size, (800, 400))

    def test_optimizes_media_relative_path(self):
        with tempfile.TemporaryDirectory() as media_root:
            raw_path = os.path.join(media_root, "raw.png")
            with open(raw_path, "wb") as image_file:
                image_file.write(self.make_image())

            with self.settings(MEDIA_ROOT=media_root, MEDIA_URL="/media/"):
                optimized = optimize_and_resize_image("/media/raw.png")

        with Image.open(optimized) as image:
            self.assertEqual(image.format, "WEBP")

    @patch("products.utils.image.requests.get")
    def test_optimizes_external_url(self, mock_get):
        response = Mock()
        response.content = self.make_image()
        mock_get.return_value = response

        optimized = optimize_and_resize_image(
            external_url="https://example.com/raw.png"
        )

        mock_get.assert_called_once_with("https://example.com/raw.png", timeout=15)
        response.raise_for_status.assert_called_once_with()
        with Image.open(optimized) as image:
            self.assertEqual(image.format, "WEBP")
