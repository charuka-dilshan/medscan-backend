import re
from typing import Dict, List, Union


MEDICAL_KEYWORDS = {
    "medicine",
    "prescription",
    "medical",
    "tablet",
    "capsule",
    "dose",
    "dosage",
    "frequency",
    "daily",
    "morning",
    "evening",
    "night",
    "meal",
    "meals",
    "mg",
    "ml",
}


def calculate_ocr_quality(text: str) -> Dict[str, Union[float, List[str]]]:
    """
    Calculate a heuristic OCR quality score between 0.0 and 1.0.

    This is not EasyOCR's model confidence. It measures whether the
    extracted text appears readable and medically meaningful.
    """

    reasons: List[str] = []

    if not text or not text.strip():
        return {
            "score": 0.0,
            "reasons": ["OCR returned empty text"],
        }

    cleaned_text = text.strip()
    words = cleaned_text.split()
    lowercase_text = cleaned_text.lower()

    score = 0.0

    # 1. Minimum readable text length
    if len(cleaned_text) >= 20:
        score += 0.20
    else:
        reasons.append("Extracted text is too short")

    # 2. Minimum number of words
    if len(words) >= 4:
        score += 0.20
    else:
        reasons.append("Too few readable words were detected")

    # 3. Alphabetic character ratio
    readable_characters = sum(
        character.isalpha() or character.isdigit() or character.isspace()
        for character in cleaned_text
    )

    readable_ratio = readable_characters / len(cleaned_text)

    if readable_ratio >= 0.70:
        score += 0.20
    else:
        reasons.append("Text contains too many unreadable symbols")

    # 4. Medical keywords
    detected_keywords = [
        keyword
        for keyword in MEDICAL_KEYWORDS
        if keyword in lowercase_text
    ]

    if detected_keywords:
        score += 0.20
    else:
        reasons.append("No common medical keywords were detected")

    # 5. Dosage or frequency pattern
    dosage_pattern = r"\b\d+\s?(mg|ml|g|mcg)\b"
    frequency_words = (
        "daily",
        "twice",
        "morning",
        "evening",
        "night",
        "after meals",
        "before meals",
    )

    has_dosage = bool(
        re.search(
            dosage_pattern,
            lowercase_text,
            flags=re.IGNORECASE,
        )
    )

    has_frequency = any(
        frequency in lowercase_text
        for frequency in frequency_words
    )

    if has_dosage or has_frequency:
        score += 0.20
    else:
        reasons.append("No dosage or frequency information was detected")

    return {
        "score": round(min(score, 1.0), 2),
        "reasons": reasons,
    }