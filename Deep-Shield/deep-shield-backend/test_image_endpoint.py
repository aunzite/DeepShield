"""Quick test script to check if image analysis works"""
import sys
from services.image_service import analyze_image
from PIL import Image
import io

# Create a simple test image (red square)
img = Image.new('RGB', (300, 300), color='red')
buffer = io.BytesIO()
img.save(buffer, format='JPEG')
img_bytes = buffer.getvalue()

print("Testing image analysis...")
try:
    result = analyze_image(img_bytes)
    print("Success:", result)
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
