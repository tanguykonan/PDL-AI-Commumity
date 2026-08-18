# ============================ PARAMÈTRE DU BOT DISCORD ============================
# ==================================================================================
# Auteur: @NYTHIQUE
# GitHub: https://github.com/Nythique
# Portfolio: https://nythique.github.io
# Date de création: 30/12/2025
# ==================================================================================
import asyncio
from PIL import Image
import pytesseract, os, uuid
from app.helps.utils import logger
from settings.config import params

class OCRProcessor:
    def __init__(self, tesseract_path=params.TESSERACT_PATH):
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

        if not os.path.exists(params.TEMP_PATH):
            os.makedirs(params.TEMP_PATH)

    @staticmethod
    async def extract_text(image_path):
        """Extrait le texte d'une image donnée."""
        try:
            loop = asyncio.get_event_loop()
            def _run_orc(path):
                    image = Image.open(path)
                    return pytesseract.image_to_string(image)
            extracted_text = await loop.run_in_executor(None, _run_orc, image_path)

            return extracted_text.strip()
        except Exception as e:
            logger.error(f"[ERROR OCR] Erreur lors de l'analyse de l'image {image_path} : {e}")
            print(f"[ERROR OCR] Erreur lors de l'analyse de l'image {image_path} : {e}")
            raise

    async def process_attachment(self, attachment):
        """Télécharger et analyse une pièce jointe Discord"""
        local_filename = os.path.join(params.TEMP_PATH, f"{uuid.uuid4()}_{attachment.filename}")
        try:
            await attachment.save(local_filename)

            extracted_text = await self.extract_text(local_filename)
            return "Description de l'image:" + extracted_text if extracted_text else "Aucun texte détecté dans l'image."
        
        except Exception as e:
            logger.error(f"[ERROR] Erreur lors du traitement de la pièce jointe : {e}")
            print(f"[ERROR] Erreur lors du traitement de la pièce jointe : {e}")
            return f"Une erreur s'est produite lors de l'analyse de l'image : {e}"
        finally:
            if os.path.exists(local_filename):
                try:
                    os.remove(local_filename)
                except Exception as e:
                    logger.error(f"[ERROR] Erreur lors de la suppression du fichier {local_filename} : {e}")
                    print(f"[ERROR] Erreur lors de la suppression du fichier {local_filename} : {e}")