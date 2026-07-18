import io
import json
import logging
from app.auth.router import router as auth_router
from app.health.router import router as health_router
from app.dashboard.router import router as dashboard_router
from app.reminders.router import router as reminders_router
from pathlib import Path
from typing import Any, Dict


import torch
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from pydantic import BaseModel
from torchvision import models, transforms

from app.ai.safety import evaluate_ocr_safety
from app.ocr.ocr_service import extract_text_from_image
from app.ocr.groq_service import parse_prescription_text
from app.ml.pill_classifier import classify_pill


# ==========================================
# PROJECT PATHS
# ==========================================

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent

CLASS_NAMES_PATH = PROJECT_ROOT / "ml" / "class_names.json"
MODEL_WEIGHTS_PATH = PROJECT_ROOT / "ml" / "pill_model.pth"


# ==========================================
# LOGGING
# ==========================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==========================================
# FASTAPI APPLICATION
# ==========================================

app = FastAPI(
    title="MedScan AI Backend",
    description="Core Backend & AI Integration Services for MedScan AI Project",
    version="1.0.0"
)
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(health_router, prefix="/profile", tags=["Health Profile"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(reminders_router, prefix="/reminders", tags=["Reminders"])


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# IMAGE TRANSFORM
# ==========================================

validation_transform = transforms.Compose(
    [
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            [0.485, 0.456, 0.406],
            [0.229, 0.224, 0.225],
        ),
    ]
)


# ==========================================
# LOAD PILL CLASS NAMES
# ==========================================

def load_class_names() -> list[str]:
    try:
        with CLASS_NAMES_PATH.open(
            "r",
            encoding="utf-8",
        ) as file:
            loaded_classes = json.load(file)

        if not isinstance(loaded_classes, list):
            raise ValueError(
                "class_names.json must contain a JSON list"
            )

        return loaded_classes

    except Exception as error:
        logger.warning(
            "Could not load class names from %s: %s",
            CLASS_NAMES_PATH,
            error,
        )

        return [
            "pill_1",
            "pill_2",
        ]


class_names = load_class_names()


# ==========================================
# LOAD PILL CLASSIFICATION MODEL
# ==========================================

def load_pill_model() -> torch.nn.Module:
    model = models.mobilenet_v3_small(
        weights=None,
    )

    number_of_classes = len(class_names)

    model.classifier[3] = torch.nn.Linear(
        model.classifier[3].in_features,
        number_of_classes,
    )

    if MODEL_WEIGHTS_PATH.exists():
        try:
            state_dict = torch.load(
                MODEL_WEIGHTS_PATH,
                map_location=torch.device("cpu"),
            )

            model.load_state_dict(state_dict)

            logger.info(
                "Pill model loaded successfully from %s",
                MODEL_WEIGHTS_PATH,
            )

        except Exception as error:
            logger.error(
                "Failed to load pill model weights: %s",
                error,
            )

    else:
        logger.warning(
            "Pill model weights were not found at %s. "
            "The model is using untrained weights.",
            MODEL_WEIGHTS_PATH,
        )

    model.eval()

    return model


pill_model = load_pill_model()


# ==========================================
# PILL SAFETY THRESHOLD
# ==========================================

PILL_CONFIDENCE_THRESHOLD = 0.85


def create_pill_safety_block(
    confidence: float,
) -> Dict[str, Any]:
    return {
        "status": "safety_block",
        "safety_block": True,
        "allow_ai_processing": False,
        "confidence": confidence,
        "messages": {
            "en": (
                "Safety Block: The pill could not be identified "
                "with sufficient confidence. Please take another "
                "clear photo or consult a registered medical professional."
            ),
            "si": (
                "ආරක්ෂක අවහිර කිරීම: ඖෂධය ප්‍රමාණවත් විශ්වාසයකින් "
                "හඳුනාගත නොහැකි විය. කරුණාකර පැහැදිලි ඡායාරූපයක් "
                "නැවත ලබාගන්න හෝ ලියාපදිංචි වෛද්‍ය වෘත්තිකයෙකුගෙන් "
                "විමසන්න."
            ),
            "ta": (
                "பாதுகாப்புத் தடுப்பு: மாத்திரையை போதுமான "
                "நம்பகத்தன்மையுடன் அடையாளம் காண முடியவில்லை. "
                "தெளிவான படத்தை மீண்டும் எடுக்கவும் அல்லது பதிவுசெய்யப்பட்ட "
                "மருத்துவ நிபுணரை அணுகவும்."
            ),
        },
    }


def verify_pill_safety_threshold(
    confidence: float,
) -> None:
    if confidence < PILL_CONFIDENCE_THRESHOLD:
        logger.warning(
            "Pill safety block triggered. Confidence: %.4f",
            confidence,
        )

        raise HTTPException(
            status_code=422,
            detail=create_pill_safety_block(confidence),
        )


# ==========================================
# REQUEST MODELS
# ==========================================

class OCRRequest(BaseModel):
    raw_text: str


# ==========================================
# ROOT ENDPOINT
# ==========================================

@app.get("/")
async def root() -> Dict[str, str]:
    return {
        "message": "MedScan AI Backend is operational.",
        "status": "healthy",
    }


# ==========================================
# PILL PREDICTION ENDPOINT
# ==========================================

@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
):
    contents = await file.read()

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    result = classify_pill(
        contents
    )

    if not result.get(
        "allow_ai_processing",
        False,
    ):
        raise HTTPException(
            status_code=422,
            detail=result,
        )

    return {
        "status": "success",
        **result,
    }


# ==========================================
# FULL PRESCRIPTION SCAN ENDPOINT
# ==========================================

@app.post("/scan-prescription")
async def scan_prescription(
    file: UploadFile = File(...),
) -> Dict[str, Any]:
    try:
        contents = await file.read()

        if not contents:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is empty.",
            )

        # Step 1: EasyOCR extraction
        ocr_result = extract_text_from_image(
            contents
        )

        # Step 2: OCR 85% safety evaluation
        safety_result = evaluate_ocr_safety(
            ocr_result
        )

        if not safety_result.get(
            "allow_ai_processing",
            False,
        ):
            raise HTTPException(
                status_code=422,
                detail=safety_result,
            )

        raw_text = str(
            safety_result.get(
                "text",
                "",
            )
        ).strip()

        # Step 3: Groq is called only after safety passes
        ai_data = parse_prescription_text(
            raw_text
        )

        if isinstance(ai_data, dict) and "error" in ai_data:
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "ai_parsing_failed",
                    "error": ai_data["error"],
                },
            )

        return {
            "status": "success",
            "safety_block": False,
            "allow_ai_processing": True,
            "raw_ocr_text": raw_text,
            "ocr_quality_score": safety_result[
                "quality_score"
            ],
            "prescription": ai_data,
        }

    except HTTPException:
        raise

    except Exception as error:
        logger.exception(
            "Scan prescription route error"
        )

        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error


# ==========================================
# LOCAL DEVELOPMENT
# ==========================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )