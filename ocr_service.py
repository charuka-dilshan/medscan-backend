import easyocr
import numpy as np
import cv2

reader = easyocr.Reader(['en'], gpu=False)

def extract_text_from_image(file_bytes: bytes) -> dict:
    # Convert bytes to numpy array
    nparr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR) # Load as color to keep info
    
    # Run OCR on the raw image (no custom thresholding for now)
    results = reader.readtext(img, detail=1)
    
    print(f"--- DEBUG: Found {len(results)} items ---")
    
    raw_text = " ".join([text for (_, text, prob) in results])
    confidences = [prob for (_, _, prob) in results]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
    
    return {"text": raw_text, "confidence": avg_confidence}