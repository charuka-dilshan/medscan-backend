from app.ocr.ocr_service import extract_text

image = "test_images/prescription.jpg"


result = extract_text(image)


print(result)