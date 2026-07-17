from typing import Any, Dict

from app.ai.quality_checker import calculate_ocr_quality


SAFETY_THRESHOLD = 0.85


SAFETY_MESSAGES = {
    "en": (
        "Safety Block: The prescription image could not be read "
        "with sufficient confidence. Please upload a clearer image "
        "or consult a registered medical professional."
    ),
    "si": (
        "ආරක්ෂක අවහිර කිරීම: බෙහෙත් වට්ටෝරු රූපය ප්‍රමාණවත් "
        "විශ්වාසයකින් කියවීමට නොහැකි විය. කරුණාකර පැහැදිලි රූපයක් "
        "උඩුගත කරන්න හෝ ලියාපදිංචි වෛද්‍ය වෘත්තිකයෙකුගෙන් විමසන්න."
    ),
    "ta": (
        "பாதுகாப்புத் தடுப்பு: மருந்துச் சீட்டு படத்தை போதுமான "
        "நம்பகத்தன்மையுடன் படிக்க முடியவில்லை. தெளிவான படத்தைப் "
        "பதிவேற்றவும் அல்லது பதிவுசெய்யப்பட்ட மருத்துவ நிபுணரை அணுகவும்."
    ),
}


def create_safety_block(
    reason: str,
    quality_score: float = 0.0,
) -> Dict[str, Any]:
    return {
        "success": False,
        "safety_block": True,
        "allow_ai_processing": False,
        "quality_score": quality_score,
        "reason": reason,
        "messages": SAFETY_MESSAGES,
    }


def evaluate_ocr_safety(
    ocr_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Check whether OCR output is safe enough for the next AI stage.

    Groq or medicine analysis should only run when
    allow_ai_processing is True.
    """

    if not ocr_result.get("success", False):
        return create_safety_block(
            reason="OCR processing failed",
        )

    text = str(ocr_result.get("text", "")).strip()

    if not text:
        return create_safety_block(
            reason="OCR returned empty text",
        )

    quality_result = calculate_ocr_quality(text)
    quality_score = float(quality_result["score"])
    reasons = quality_result["reasons"]

    if quality_score < SAFETY_THRESHOLD:
        reason = (
            "; ".join(reasons)
            if reasons
            else "OCR quality is below the safety threshold"
        )

        return create_safety_block(
            reason=reason,
            quality_score=quality_score,
        )

    return {
        "success": True,
        "safety_block": False,
        "allow_ai_processing": True,
        "quality_score": quality_score,
        "text": text,
        "message": "OCR output passed the 85% safety rule",
    }