import io
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

import torch
from PIL import Image, UnidentifiedImageError
from torchvision import models, transforms


# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# File paths
# ---------------------------------------------------------

# pill_classifier.py තිබෙන app/ml folder එක
CURRENT_DIR = Path(__file__).resolve().parent

CLASS_NAMES_PATH = CURRENT_DIR / "class_names.json"
MODEL_WEIGHTS_PATH = CURRENT_DIR / "pill_model.pth"


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

PILL_CONFIDENCE_THRESHOLD = 0.85


# ---------------------------------------------------------
# Image preprocessing
# ---------------------------------------------------------

image_transform = transforms.Compose(
    [
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ]
)


# ---------------------------------------------------------
# Load class names
# ---------------------------------------------------------

def load_class_names() -> List[str]:
    """
    Load pill class names from app/ml/class_names.json.
    """

    if not CLASS_NAMES_PATH.exists():
        logger.warning(
            "class_names.json not found at: %s. "
            "Using temporary class names.",
            CLASS_NAMES_PATH,
        )

        return [
            "paracetamol",
            "amoxicillin",
        ]

    try:
        with CLASS_NAMES_PATH.open(
            mode="r",
            encoding="utf-8",
        ) as file:
            class_names = json.load(file)

        if not isinstance(class_names, list):
            raise ValueError(
                "class_names.json must contain a JSON list."
            )

        if not class_names:
            raise ValueError(
                "class_names.json cannot be empty."
            )

        cleaned_class_names = [
            str(class_name).strip()
            for class_name in class_names
            if str(class_name).strip()
        ]

        if not cleaned_class_names:
            raise ValueError(
                "class_names.json does not contain valid class names."
            )

        return cleaned_class_names

    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"Invalid JSON inside class_names.json: {error}"
        ) from error

    except Exception as error:
        raise RuntimeError(
            f"Failed to load class names: {error}"
        ) from error


class_names = load_class_names()


# ---------------------------------------------------------
# Create model
# ---------------------------------------------------------

def create_model() -> torch.nn.Module:
    """
    Create MobileNetV3 Small classifier.

    The final classifier output size is based on
    the number of classes inside class_names.json.
    """

    model = models.mobilenet_v3_small(
        weights=None,
    )

    model.classifier[3] = torch.nn.Linear(
        in_features=model.classifier[3].in_features,
        out_features=len(class_names),
    )

    return model


# ---------------------------------------------------------
# Load trained model
# ---------------------------------------------------------

def load_model() -> Tuple[torch.nn.Module, bool]:
    """
    Load trained model weights from app/ml/pill_model.pth.

    Returns:
        model:
            PyTorch model.

        trained_weights_loaded:
            True if trained weights loaded successfully.
            False if the model file is missing or invalid.
    """

    model = create_model()
    trained_weights_loaded = False

    if not MODEL_WEIGHTS_PATH.exists():
        logger.warning(
            "pill_model.pth was not found at: %s. "
            "Predictions cannot be considered reliable.",
            MODEL_WEIGHTS_PATH,
        )

        model.eval()

        return model, trained_weights_loaded

    try:
        checkpoint = torch.load(
            MODEL_WEIGHTS_PATH,
            map_location=torch.device("cpu"),
            weights_only=True,
        )

        # Support models saved using:
        # torch.save(model.state_dict(), path)
        if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
            state_dict = checkpoint["model_state_dict"]
        else:
            state_dict = checkpoint

        model.load_state_dict(
            state_dict
        )

        trained_weights_loaded = True

        logger.info(
            "Pill classifier model loaded successfully from: %s",
            MODEL_WEIGHTS_PATH,
        )

    except Exception as error:
        logger.error(
            "Could not load pill model weights: %s",
            error,
        )

    model.eval()

    return model, trained_weights_loaded


pill_model, model_ready = load_model()


# ---------------------------------------------------------
# Safety block response
# ---------------------------------------------------------

def create_safety_block(
    reason: str,
    confidence: float = 0.0,
) -> Dict[str, Any]:
    """
    Create multilingual safety block response.
    """

    return {
        "success": False,
        "safety_block": True,
        "allow_ai_processing": False,
        "confidence": round(
            float(confidence),
            4,
        ),
        "reason": reason,
        "messages": {
            "en": (
                "Safety Block: The pill could not be identified "
                "with at least 85% confidence. Please upload a "
                "clearer image or consult a registered medical "
                "professional."
            ),
            "si": (
                "ආරක්ෂක අවහිර කිරීම: ඖෂධය අවම වශයෙන් 85%ක "
                "විශ්වාසයකින් හඳුනාගත නොහැකි විය. කරුණාකර "
                "පැහැදිලි රූපයක් ලබා දෙන්න හෝ ලියාපදිංචි "
                "වෛද්‍ය වෘත්තිකයෙකුගෙන් විමසන්න."
            ),
            "ta": (
                "பாதுகாப்புத் தடுப்பு: மாத்திரையை குறைந்தது "
                "85% நம்பகத்தன்மையுடன் அடையாளம் காண முடியவில்லை. "
                "தெளிவான படத்தைப் பதிவேற்றவும் அல்லது பதிவுசெய்யப்பட்ட "
                "மருத்துவ நிபுணரை அணுகவும்."
            ),
        },
    }


# ---------------------------------------------------------
# Load and prepare image
# ---------------------------------------------------------

def load_image(
    image_source: Union[bytes, str, Path],
) -> Image.Image:
    """
    Load an image from uploaded bytes or a local file path.
    """

    if isinstance(image_source, bytes):
        if not image_source:
            raise ValueError(
                "Uploaded image is empty."
            )

        try:
            return Image.open(
                io.BytesIO(image_source)
            ).convert("RGB")

        except UnidentifiedImageError as error:
            raise ValueError(
                "Uploaded file is not a valid image."
            ) from error

    image_path = Path(image_source)

    if not image_path.exists():
        raise FileNotFoundError(
            f"Pill image was not found: {image_path}"
        )

    try:
        return Image.open(
            image_path
        ).convert("RGB")

    except UnidentifiedImageError as error:
        raise ValueError(
            "Selected file is not a valid image."
        ) from error


def prepare_image(
    image_source: Union[bytes, str, Path],
) -> torch.Tensor:
    """
    Load and convert an image into a model input tensor.
    """

    image = load_image(
        image_source
    )

    image_tensor = image_transform(
        image
    ).unsqueeze(0)

    return image_tensor


# ---------------------------------------------------------
# Pill classification
# ---------------------------------------------------------

def classify_pill(
    image_source: Union[bytes, str, Path],
) -> Dict[str, Any]:
    """
    Classify a pill image and apply the 85% confidence rule.
    """

    try:
        if not model_ready:
            return create_safety_block(
                reason=(
                    "A trained pill classification model "
                    "has not been loaded."
                )
            )

        image_tensor = prepare_image(
            image_source
        )

        with torch.no_grad():
            logits = pill_model(
                image_tensor
            )

            probabilities = torch.softmax(
                logits,
                dim=1,
            )

            confidence_tensor, index_tensor = torch.max(
                probabilities,
                dim=1,
            )

        confidence = float(
            confidence_tensor.item()
        )

        predicted_index = int(
            index_tensor.item()
        )

        if predicted_index >= len(class_names):
            return create_safety_block(
                reason=(
                    "The predicted class index does not match "
                    "the available pill class names."
                ),
                confidence=confidence,
            )

        predicted_class = class_names[
            predicted_index
        ]

        if confidence < PILL_CONFIDENCE_THRESHOLD:
            return create_safety_block(
                reason=(
                    "Pill classification confidence is below "
                    "the 85% safety threshold."
                ),
                confidence=confidence,
            )

        return {
            "success": True,
            "safety_block": False,
            "allow_ai_processing": True,
            "pill": predicted_class,
            "confidence": round(
                confidence,
                4,
            ),
            "message": (
                "Pill classification passed "
                "the 85% safety threshold."
            ),
        }

    except FileNotFoundError as error:
        return create_safety_block(
            reason=str(error),
        )

    except ValueError as error:
        return create_safety_block(
            reason=str(error),
        )

    except Exception as error:
        logger.exception(
            "Pill classification failed."
        )

        return create_safety_block(
            reason=f"Pill classification failed: {error}",
        )