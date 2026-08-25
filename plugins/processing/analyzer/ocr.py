"""OCR image text extraction module using Tesseract."""

import os
import uuid
import asyncio
from PIL import Image
import pytesseract
from app.helps.utils import logger
from settings.config import params


class OCRProcessor:
    """Extracts text from Discord image attachments asynchronously."""

    def __init__(self, tesseract_path: str = params.TESSERACT_PATH):
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

        if not os.path.exists(params.TEMP_PATH):
            os.makedirs(params.TEMP_PATH, exist_ok=True)

    @staticmethod
    async def extract_text(image_path: str) -> str:
        """Extract text from an image file path asynchronously."""
        try:
            loop = asyncio.get_event_loop()

            def _run_ocr(path):
                image = Image.open(path)
                return pytesseract.image_to_string(image)

            extracted_text = await loop.run_in_executor(None, _run_ocr, image_path)
            return extracted_text.strip()
        except Exception as e:
            logger.error(f"[ERROR OCR] Image text extraction failed for {image_path}: {e}", exc_info=True)
            raise

    async def process_attachment(self, attachment) -> str:
        """Download Discord attachment temporarily, run OCR, and cleanup."""
        local_filename = os.path.join(params.TEMP_PATH, f"{uuid.uuid4()}_{attachment.filename}")
        try:
            await attachment.save(local_filename)
            extracted_text = await self.extract_text(local_filename)
            return f"Description de l'image: {extracted_text}" if extracted_text else "Aucun texte détecté dans l'image."

        except Exception as e:
            logger.error(f"[ERROR OCR] Failed to process attachment: {e}", exc_info=True)
            return f"Une erreur s'est produite lors de l'analyse de l'image : {e}"
        finally:
            if os.path.exists(local_filename):
                try:
                    os.remove(local_filename)
                except Exception as e:
                    logger.error(f"[ERROR OCR] Failed to delete temp file {local_filename}: {e}", exc_info=True)