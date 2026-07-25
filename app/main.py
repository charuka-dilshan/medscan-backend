import json
import logging
from pathlib import Path
from typing import Any, Dict

import torch
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from torchvision import models, transforms

from app.ai.safety import evaluate_ocr_safety
from app.auth.router import router as auth_router
from app.dashboard.router import router as dashboard_router
from app.database import Base, engine, get_db
from app.health.router import router as health_router
from app.ml.pill_classifier import classify_pill
from app.ocr.groq_service import parse_prescription_text
from app.ocr.ocr_service import extract_text_from_image
from app.reminders.router import router as reminders_router
from app.services.scan_log_service import save_scan_log


# ==========================================
# PROJECT PATHS
# ==========================================

APP_DIR = Path(__file__).resolve().parent

CLASS_NAMES_PATH = APP_DIR / "ml" / "class_names.json"
MODEL_WEIGHTS_PATH = APP_DIR / "ml" / "pill_model.pth"


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
    version="1.0.0",
)


# Create database tables
Base.metadata.create_all(bind=engine)


# ==========================================
# CORS CONFIGURATION
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# REGISTER ROUTERS
# ==========================================

app.include_router(auth_router)
app.include_router(health_router)
app.include_router(dashboard_router)
app.include_router(reminders_router)


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
                "class_names.json must contain a JSON list."
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
            logger.exception(
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
# ROOT ENDPOINT
# ==========================================

@app.get(
    "/",
    tags=["System"],
)
async def root() -> Dict[str, str]:
    return {
        "message": "MedScan AI Backend is operational.",
        "status": "healthy",
    }


# ==========================================
# PILL PREDICTION ENDPOINT
# ==========================================

@app.post(
    "/predict",
    tags=["Pill Classification"],
)
async def predict_pill(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:

    contents = await file.read()

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    try:
        result = classify_pill(contents)

        if not result.get(
            "allow_ai_processing",
            False,
        ):
            save_scan_log(
                db,
                scan_type="pill",
                status="safety_block",
                allow_ai_processing=False,
                predicted_label=result.get("predicted_class"),
                confidence=result.get("confidence"),
                message=result.get(
                    "reason",
                    "Confidence below safety threshold.",
                ),
            )

            return {
                "status": "safety_block",
                **result,
            }

        save_scan_log(
            db,
            scan_type="pill",
            status="success",
            allow_ai_processing=True,
            predicted_label=result.get("predicted_class"),
            confidence=result.get("confidence"),
            message="Pill classification completed successfully.",
        )

        return {
            "status": "success",
            **result,
        }

    except HTTPException:
        raise

    except Exception as error:
        logger.exception(
            "Pill prediction route error."
        )

        raise HTTPException(
            status_code=500,
            detail="Pill prediction failed.",
        ) from error


# ==========================================
# FULL PRESCRIPTION SCAN ENDPOINT
# ==========================================

@app.post(
    "/scan-prescription",
    tags=["Prescription Scanner"],
)
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

        # Step 1: Extract text using EasyOCR
        ocr_result = extract_text_from_image(
            contents
        )

        # Step 2: Evaluate OCR safety
        safety_result = evaluate_ocr_safety(
            ocr_result
        )

        if not safety_result.get(
            "allow_ai_processing",
            False,
        ):
            return {
                "status": "safety_block",
                **safety_result,
            }

        raw_text = str(
            safety_result.get(
                "text",
                "",
            )
        ).strip()

        if not raw_text:
            return {
                "status": "safety_block",
                "safety_block": True,
                "allow_ai_processing": False,
                "message": "No readable prescription text was detected.",
            }

        # Step 3: Send OCR text to Groq only after safety passes
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
            "ocr_quality_score": safety_result.get(
                "quality_score",
                0,
            ),
            "prescription": ai_data,
        }

    except HTTPException:
        raise

    except Exception as error:
        logger.exception(
            "Scan prescription route error."
        )

        raise HTTPException(
            status_code=500,
            detail="Prescription scanning failed.",
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