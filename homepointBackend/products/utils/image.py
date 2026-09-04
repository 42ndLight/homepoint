# image.py

import io
from PIL import Image

def optimize_and_resize_image(file_obj, max_width: int = 800, quality: int = 78) -> io.BytesIO:
    """
    Accepts a file-like object or Django FieldFile stream, resizes it if needed,
    converts it to WebP, and returns an in-memory BytesIO buffer.
    """
    # Reset pointer position in case the file stream was previously read
    if hasattr(file_obj, 'seek'):
        file_obj.seek(0)

    with Image.open(file_obj) as img:
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