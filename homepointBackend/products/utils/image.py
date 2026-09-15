# image.py

import io
import os

import requests
from django.conf import settings
from PIL import Image

from django.core.files.storage import default_storage
from django.core.exceptions import SuspiciousFileOperation


def _load_url_image(url):
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return io.BytesIO(response.content)


def _resolve_local_path(source):
    media_url = settings.MEDIA_URL
    if media_url and source.startswith(media_url):
        return os.path.join(settings.MEDIA_ROOT, source.removeprefix(media_url))
    return source


def _load_path_image(source):
    with open(_resolve_local_path(source), "rb") as image_file:
        return io.BytesIO(image_file.read())


def _load_file_image(source):
    if hasattr(source, "open"):
        source.open("rb")
    if hasattr(source, "seek"):
        source.seek(0)
    return io.BytesIO(source.read())


def _load_image_bytes(source):
    if isinstance(source, str):
        # 1. Check HTTP/HTTPS URLs first
        if source.startswith(("http://", "https://")):
            return _load_url_image(source)

        # 2. Check default_storage (S3/Tigris Bucket)
        try:
            if default_storage.exists(source):
                with default_storage.open(source, "rb") as f:
                    return io.BytesIO(f.read())
        except (SuspiciousFileOperation, ValueError):
            pass

        # 3. Fallback to local filesystem path
        return _load_path_image(source)

    if isinstance(source, bytes):
        return io.BytesIO(source)
    if hasattr(source, "read"):
        return _load_file_image(source)
    raise ValueError(f"Unable to load image data from source: {source!r}")


def _convert_to_webp_compatible_mode(image):
    if image.mode in ("RGBA", "P"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        mask = image.convert("RGBA").split()[3] if image.mode == "RGBA" else None
        background.paste(image, mask=mask)
        return background
    if image.mode != "RGB":
        return image.convert("RGB")
    return image


def _resize_image(image, max_width):
    if image.width <= max_width:
        return image
    aspect_ratio = image.height / image.width
    new_height = int(max_width * aspect_ratio)
    return image.resize((max_width, new_height), Image.Resampling.LANCZOS)


def _save_as_webp(image, quality):
    output_buffer = io.BytesIO()
    image.save(output_buffer, format="WEBP", quality=quality)
    output_buffer.seek(0)
    return output_buffer


def optimize_and_resize_image(
    image_source=None,
    external_url=None,
    max_width: int = 800,
    quality: int = 78,
) -> io.BytesIO:
    """
    Optimize an image source and return it as an in-memory WebP buffer.

    ``image_source`` may be a Django FieldFile, a file-like object, bytes, a
    local path, or an absolute URL. ``external_url`` is retained as a named
    fallback for callers that only have a URL.
    """
    source = image_source or external_url
    if not source:
        raise ValueError("No image source or external URL provided for optimization.")

    with Image.open(_load_image_bytes(source)) as image:
        image = _convert_to_webp_compatible_mode(image)
        image = _resize_image(image, max_width)
        return _save_as_webp(image, quality)