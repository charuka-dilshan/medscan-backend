from pathlib import Path
from pill_classifier import classify_pill

CURRENT_DIR = Path(__file__).resolve().parent
TEST_IMAGES_DIR = CURRENT_DIR.parent.parent / "test_images"

image_path = TEST_IMAGES_DIR / "pill.jpg"

print(f"Testing image: {image_path}")

result = classify_pill(str(image_path))

print("\nPrediction Result")
print(result)