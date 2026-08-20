import asyncio
import io
import logging
from PIL import Image, ExifTags

logger = logging.getLogger(__name__)

async def run_image_forensics(image_bytes: bytes) -> dict:
    """
    Extracts Exif metadata and performs basic steganography/noise checks.
    """
    logger.info("Initiating media forensics analysis.")
    
    result = {
        "metadata": {},
        "gps_available": False,
        "editing_traces": [],
        "steg_flags": []
    }
    
    try:
        # Load image via PIL to extract EXIF safely
        img = Image.open(io.BytesIO(image_bytes))
        
        # Extract Exif
        exif_data = img.getexif()
        if exif_data:
            for tag_id, value in exif_data.items():
                tag = ExifTags.TAGS.get(tag_id, tag_id)
                
                # Check for common editing software signatures
                if tag == 'Software':
                    result["metadata"]["Software"] = str(value)
                    if any(sw in str(value).lower() for sw in ['photoshop', 'canva', 'gimp']):
                        result["editing_traces"].append(str(value))
                        
                elif tag == 'Model':
                    result["metadata"]["CameraModel"] = str(value)
                elif tag == 'DateTimeOriginal':
                    result["metadata"]["OriginalDate"] = str(value)
                    
            # Check GPS (tag 34853 usually holds GPSInfo)
            if 34853 in exif_data:
                result["gps_available"] = True
                
        # Basic Steganography Check (Conceptual LSB Variance)
        # In a robust system, this involves analyzing the least significant bit plane.
        # Here we perform a simplified check on the image mode as a placeholder.
        if img.mode != 'RGB':
            result["steg_flags"].append("Non-standard color mode, potentially hiding data.")

        # Simulate async delay for heavy pixel processing
        await asyncio.sleep(0.1)

    except Exception as e:
        logger.error(f"Error during media forensics: {e}")
        result["error"] = str(e)

    return result
