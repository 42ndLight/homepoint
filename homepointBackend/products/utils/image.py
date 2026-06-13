import io
import requests
from PIL import Image

def optimize_and_resize_external_image(external_url: str, max_width: int = 800, quality: int = 75) -> io.BytesIO:
    # Use standard streaming to ensure safety against giant payload injection attacks
    with requests.get(external_url, stream=True, timeout=10) as response:
        response.raise_for_status()
        
        # Read content-length metadata check if populated
        content_length = response.headers.get('Content-Length')
        if content_length and int(content_length) > 25 * 1024 * 1024: # 25MB Max guardrail
            raise ValueError("Target download item size footprint breaks system limits.")
            
        input_buffer = io.BytesIO(response.content)

    with Image.open(input_buffer) as img:
        # Convert CMYK or RGBA layers gracefully to standard clean RGB format
        if img.mode in ("RGBA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.convert("RGBA").split()[3]) # alpha channel
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")
            
        # Scale handling matching dimensions
        width, height = img.size
        if width > max_width:
            aspect_ratio = height / width
            new_height = int(max_width * aspect_ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
        output_buffer = io.BytesIO()
        img.save(output_buffer, format="WEBP", quality=quality)
        output_buffer.seek(0)
        
        return output_buffer