from pathlib import Path
from pprint import pprint

from app.ml.pill_classifier import classify_pill


PROJECT_ROOT = Path(__file__).resolve().parents[2]

IMAGE_PATH = (
    PROJECT_ROOT
    / "test_images"
    / "pill.jpg"
)


def main() -> None:
    if not IMAGE_PATH.exists():
        print(
            f"Image not found: {IMAGE_PATH}"
        )
        return

    image_bytes = IMAGE_PATH.read_bytes()

    result = classify_pill(
        image_bytes
    )

    print("\nPILL CLASSIFICATION RESULT:")
    pprint(result)

    if result["allow_ai_processing"]:
        print(
            "\nPASS: Pill classification passed "
            "the 85% safety rule."
        )

    else:
        print(
            "\nBLOCKED: The next AI stage "
            "must not run."
        )


if __name__ == "__main__":
    main()