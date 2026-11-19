"""OCR Service for 3D Garment Studio using OpenCV and Tesseract."""
import os
import cv2
import numpy as np
import pytesseract
from pytesseract import Output
from PIL import Image
from typing import Dict, Any, List, Tuple, Optional

# Ensure tesseract binary can be found
TESSERACT_CMD = os.environ.get("TESSERACT_CMD", "/opt/homebrew/bin/tesseract")
if os.path.exists(TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

class OCRService:
    @staticmethod
    def load_image_from_file(file_path: str) -> Image.Image:
        """Loads an image from PNG, JPG, or PDF file."""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(file_path)
                if len(doc) == 0:
                    raise ValueError("Uploaded PDF has no pages.")
                page = doc[0]
                # Render at 300 DPI (approx 4.16x scale from 72 DPI)
                zoom = 300.0 / 72.0
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                doc.close()
                return img
            except Exception as e:
                raise RuntimeError(f"Failed to extract image from PDF: {str(e)}")
        else:
            return Image.open(file_path).convert("RGB")

    @classmethod
    def preprocess_image(cls, pil_img: Image.Image) -> np.ndarray:
        """
        Enhances image contrast and removes noise for optimal OCR table extraction.
        """
        img_np = np.array(pil_img)
        # Convert RGB to Grayscale
        if len(img_np.shape) == 3:
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_np

        # If image is small, upscale it
        h, w = gray.shape[:2]
        if w < 1000:
            scale = 1200 / w
            gray = cv2.resize(gray, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)

        # Contrast enhancement using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Mild Gaussian blur to reduce pixel artifacts
        denoised = cv2.GaussianBlur(enhanced, (3, 3), 0)

        # Adaptive thresholding or Otsu
        _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

        return thresh

    @classmethod
    def extract_text_and_tokens(cls, file_path: str) -> Dict[str, Any]:
        """
        Extracts structured word tokens and raw text using Tesseract OCR.
        Returns:
            {
                "raw_text": str,
                "tokens": List[dict(text, conf, x, y, w, h, line_num, block_num)],
                "image_size": (width, height)
            }
        """
        pil_img = cls.load_image_from_file(file_path)
        width, height = pil_img.size

        # Preprocess
        processed_cv = cls.preprocess_image(pil_img)

        # Run Tesseract with dataframe/dict output
        # Use psm 6 (assume uniform block of text / table)
        custom_config = r'--oem 3 --psm 6'
        ocr_data = pytesseract.image_to_data(processed_cv, output_type=Output.DICT, config=custom_config)

        tokens = []
        n_boxes = len(ocr_data['text'])
        for i in range(n_boxes):
            text = ocr_data['text'][i].strip()
            conf = float(ocr_data['conf'][i])
            if text:
                tokens.append({
                    "text": text,
                    "conf": max(0.0, conf),
                    "x": int(ocr_data['left'][i]),
                    "y": int(ocr_data['top'][i]),
                    "w": int(ocr_data['width'][i]),
                    "h": int(ocr_data['height'][i]),
                    "line_num": int(ocr_data['line_num'][i]),
                    "block_num": int(ocr_data['block_num'][i]),
                    "par_num": int(ocr_data['par_num'][i])
                })

        # Also get formatted text string
        raw_text = pytesseract.image_to_string(processed_cv, config=custom_config)
        if not raw_text.strip():
            # Fallback to standard psm 3
            raw_text = pytesseract.image_to_string(pil_img)

        return {
            "raw_text": raw_text,
            "tokens": tokens,
            "image_size": (width, height)
        }
