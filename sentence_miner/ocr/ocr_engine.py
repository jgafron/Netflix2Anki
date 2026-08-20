import pytesseract
from .preprocess import preprocess_image

def run_ocr(image_path, ocr_language='eng'):
    """Run OCR on the processed image."""
    # Preprocess the image before passing it to Tesseract
    processed_image_path = preprocess_image(image_path)

    # Run OCR on the preprocessed image
    text = pytesseract.image_to_string(processed_image_path, lang=ocr_language)

    return text