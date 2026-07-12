import easyocr
import cv2
import numpy as np

# Use a global variable to hold the reader, initialize it to None
_reader = None

def get_reader():
    global _reader
    if _reader is None:
        print("Initializing EasyOCR reader...")
        _reader = easyocr.Reader(['en'], gpu=False)
    return _reader

def extract_text_from_image(image_bytes: bytes) -> dict:
    reader = get_reader() # This ensures it exists
    
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Preprocessing
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
    kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
    sharpened = cv2.filter2D(denoised, -1, kernel)
    
    # Perform OCR
    results = reader.readtext(sharpened, detail=1)
    
    raw_text = " ".join([text for (_, text, prob) in results if prob > 0.3])
    return {"text": raw_text, "confidence": 0.9}