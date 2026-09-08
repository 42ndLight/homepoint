# image.py

import io
import os

import requests
from django.conf import settings
from PIL import Image


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

    if isinstance(source, str):
        if source.startswith(("http://", "https://")):
            response = requests.get(source, timeout=15)
            response.raise_for_status()
            image_bytes = io.BytesIO(response.content)
        else:
            media_url = settings.MEDIA_URL
            path = (
                os.path.join(settings.MEDIA_ROOT, source.removeprefix(media_url))
                if media_url and source.startswith(media_url)
                else source
            )
            with open(path, "rb") as image_file:
                image_bytes = io.BytesIO(image_file.read())
    elif isinstance(source, bytes):
        image_bytes = io.BytesIO(source)
    elif hasattr(source, "read"):
        if hasattr(source, "open"):
            source.open("rb")
        if hasattr(source, "seek"):
            source.seek(0)
        image_bytes = io.BytesIO(source.read())
    else:
        raise ValueError(f"Unable to load image data from source: {source!r}")

    with Image.open(image_bytes) as img:
        # Convert CMYK, Palette, or RGBA layers to standard RGB format
        if img.mode in ("RGBA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            # Handle transparency mask if available
            mask = img.convert("RGBA").split()[3] if img.mode == "RGBA" else None
            background.paste(img, mask=mask)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")
            
        # Scale handling matching target max width
        width, height = img.size
        if width > max_width:
            aspect_ratio = height / width
            new_height = int(max_width * aspect_ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
        output_buffer = io.BytesIO()
        img.save(output_buffer, format="WEBP", quality=quality)
        output_buffer.seek(0)
        
        return output_buffer