import os
import pdfplumber
import pytesseract
from PIL import Image
from utils.logger import get_logger

logger = get_logger()

# Limit the amount of text extracted per document to avoid massive memory usage / embedding sizes.
MAX_CHARS = 2000

def extract_text(file_path: str) -> str:
    """
    Attempts to read the contents of a file and extract text.
    Supports PDF and common image formats.
    Returns the extracted text, or an empty string if unsupported or failed.
    """
    ext = os.path.splitext(file_path)[1].lower()
    text = ""
    try:
        if ext == '.pdf':
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages[:3]:  # read up to 3 pages
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                        
        elif ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            # For pytesseract to work on Windows, the Tesseract executable must be installed.
            try:
                img = Image.open(file_path)
                text = pytesseract.image_to_string(img)
            except pytesseract.TesseractNotFoundError:
                logger.warning("Tesseract not found. Install it for image OCR support.")
            except Exception as e:
                logger.error(f"Image OCR failed for {file_path}: {e}")
                
        elif ext in ['.txt', '.md', '.csv']:
            # Read raw text directly
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read(MAX_CHARS)
                
    except Exception as e:
        logger.error(f"Failed to extract text from {file_path}. Error: {e}")
    
    return text[:MAX_CHARS]
