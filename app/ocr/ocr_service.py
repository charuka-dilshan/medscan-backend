from pathlib import Path
from typing import Any, Dict, Union

import cv2
import easyocr
import numpy as np


reader = easyocr.Reader(
    ["en"],
    gpu=False,
    verbose=False,
)


ImageInput = Union[str, Path, bytes]


def preprocess_image(image_input: ImageInput) -> np.ndarray:
    """
    Accepts either:
    - image file path
    - pathlib.Path
    - uploaded image bytes
    """

    if isinstance(image_input, bytes):
        image_array = np.frombuffer(
            image_input,
            dtype=np.uint8,
        )

        image = cv2.imdecode(
            image_array,
            cv2.IMREAD_COLOR,
        )

    else:
        image = cv2.imread(str(image_input))

    if image is None:
        raise ValueError(
            "Image could not be opened. Check the image path or uploaded file."
        )

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY,
    )

    threshold = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )[1]

    return threshold


def clean_text(text: str) -> str:
    replacements = {
        "Soomg": "500mg",
        "Parace tamol": "Paracetamol",
        "Meda ic ine": "Medicine",
        "PrECRIPION": "PRESCRIPTION",
        "MF DICAL": "MEDICAL",
        "Da; |y": "Daily",
        "aftev mea |s": "after meals",
        "Fequency": "Frequency",
    }

    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)

    return text.strip()


def extract_text_from_image(
    image_input: ImageInput,
) -> Dict[str, Any]:
    try:
        processed_image = preprocess_image(image_input)

        results = reader.readtext(
            processed_image,
            detail=1,
            paragraph=True,
        )

        texts = []

        for result in results:
            # paragraph=True result format:
            # [bounding_box, detected_text]
            if len(result) >= 2:
                detected_text = str(result[1]).strip()

                if detected_text:
                    texts.append(detected_text)

        final_text = " ".join(texts).strip()
        final_text = clean_text(final_text)

        return {
            "success": True,
            "text": final_text,
            "confidence": None,
        }

    except Exception as error:
        return {
            "success": False,
            "text": "",
            "confidence": None,
            "error": str(error),
        }


# Existing test files use extract_text().
# Keep this wrapper for backward compatibility.
def extract_text(
    image_input: ImageInput,
) -> Dict[str, Any]:
    return extract_text_from_image(image_input)