from pprint import pprint

from app.ai.safety import evaluate_ocr_safety
from app.ocr.ocr_service import extract_text


IMAGE_PATH = "D:\\MY PROJECTS\\medscan\\medscan-backend\\test_images\\prescription.jpg"


def main() -> None:
    ocr_result = extract_text(IMAGE_PATH)

    print("\nOCR RESULT:")
    pprint(ocr_result)

    safety_result = evaluate_ocr_safety(ocr_result)

    print("\nSAFETY RESULT:")
    pprint(safety_result)

    if safety_result["allow_ai_processing"]:
        print("\nPASS: The next AI stage may run.")
    else:
        print("\nBLOCKED: Groq must not be called.")


if __name__ == "__main__":
    main()

ocr_result = {
    "success": True,
    "text": "abc ???",
    "confidence": None,
}