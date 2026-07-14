import io
import json
import logging
import os
from PIL import Image

import torch
from torchvision import models, transforms
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# AI Developer ගේ modules (paths නිවැරදිව import කර ඇත)
from ocr_service import extract_text_from_image
from groq_service import parse_prescription_text

# Core Backend Routers (Developer 1 ගේ කොටස් ඉදිරියේදී සම්බන්ධ කිරීමට)
# 💡 සටහන: මේවා ඊළඟ පියවර වලදී අපි නිර්මාණය කරනවා.
# from app.auth.router import router as auth_router
# from app.health.router import router as health_router
# from app.reminders.router import router as reminders_router
# from app.dashboard.router import router as dashboard_router

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MedScan AI Backend",
    description="Core Backend & AI Integration Services for MedScan AI Project",
    version="1.0.0"
)

# 🌐 CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Flutter mobile/web එකෙන් ලේසියෙන්ම කතා කරන්න පුළුවන්
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 🤖 AI / ML MODULE INITIALIZATION (Member 1 & 2)
# ==========================================

# 1. Setup Transforms (MUST match training!)
val_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# 2. Load Classes safely
try:
    with open('ml/class_names.json', 'r') as f:
        class_names = json.load(f)
except Exception:
    class_names = ["pill_1", "pill_2"]  # Fallback classes if file missing

# 3. Load PyTorch Model Weights
def load_my_model():
    model = models.mobilenet_v3_small(weights=None)
    num_classes = len(class_names)
    model.classifier[3] = torch.nn.Linear(model.classifier[3].in_features, num_classes)
    try:
        model.load_state_dict(torch.load("ml/pill_model.pth", map_location=torch.device('cpu')))
    except Exception as e:
        logger.error(f"Failed to load model weights (pill_model.pth): {e}")
    model.eval()
    return model

model = load_my_model()

# ==========================================
# 🛡️ 85% MEDICAL SAFETY GUARDRAIL ENGINE
# ==========================================
def verify_safety_threshold(confidence: float):
    """
    Confidence score එක 85% (0.85) ට වඩා අඩු නම්, වෛද්‍ය ආරක්ෂාව සඳහා 
    දත්ත පද්ධතියට ඇතුල් කිරීම මෙතනින්ම වළක්වා HTTPException එකක් නිකුත් කරයි.
    """
    if confidence < 0.85:
        logger.warning(f"⚠️ SAFETY BLOCK TRIGGERED: Low confidence score: {confidence:.4f}")
        raise HTTPException(
            status_code=422, 
            detail={
                "status": "safety_block",
                "confidence": confidence,
                "msg": "The analysis falls below the required 85% medical safety threshold. Please ensure good lighting and re-take the photo."
            }
        )
    return True

# ==========================================
# 🚀 CORE ENDPOINTS & ROUTER REGISTRATION
# ==========================================

# Pydantic Schemas for AI endpoints
class OCRRequest(BaseModel):
    raw_text: str

@app.get("/")
async def root():
    """
    Server Health Check Endpoint
    """
    return {
        "message": "MedScan AI Backend is operational.",
        "status": "healthy"
    }

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """
    Pill Image Classification Endpoint (PyTorch Model)
    """
    try:
        image = Image.open(io.BytesIO(await file.read())).convert("RGB")
        image_tensor = val_transform(image).unsqueeze(0)
        
        with torch.no_grad():
            logits = model(image_tensor)
            probs = torch.nn.functional.softmax(logits, dim=1)
            confidence, predicted_idx = torch.max(probs, dim=1)
        
        conf_val = confidence.item()
        
        # 🛡️ Enforce 85% safety rule for Pill Detection
        verify_safety_threshold(conf_val)
        
        return {
            "status": "success", 
            "pill": class_names[predicted_idx.item()], 
            "confidence": conf_val
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Prediction Route Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/parse-prescription")
async def parse_prescription(request: OCRRequest):
    """
    Parse Unstructured Prescription Text placeholder
    """
    return {"status": "success", "data": "Prescription parsing logic goes here"}

@app.post("/scan-prescription")
async def scan_prescription(file: UploadFile = File(...)):
    """
    Full OCR Scanning & Groq Llama 3 AI Structuring Pipeline
    """
    try:
        contents = await file.read()
        
        # EasyOCR Extraction
        ocr_result = extract_text_from_image(contents)
        raw_text = ocr_result.get("text", "")
        ocr_confidence = ocr_result.get("confidence", 0.0)
        
        if not raw_text.strip():
            raise HTTPException(status_code=400, detail="OCR failed to find any text on the image.")

        # 🛡️ Enforce 85% safety rule for OCR Text Reading
        verify_safety_threshold(ocr_confidence)

        # Groq Llama 3 AI Parsing
        ai_data = parse_prescription_text(raw_text)
        
        if "error" in ai_data:
            raise HTTPException(status_code=500, detail="AI parsing engine failed to process text.")

        return {
            "status": "success",
            "raw_ocr_text": raw_text,
            "ocr_confidence": ocr_confidence,
            "prescription": ai_data
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Scan Prescription Route Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# FUTURE ROUTER REGISTRATION PLACEHOLDERS
# ==========================================
# 💡 Developer 1 ගේ අනෙකුත් මොඩියුල සාදා අවසන් වූ පසු මේවා සක්‍රීය කරනු ලැබේ.
# app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
# app.include_router(health_router, prefix="/profile", tags=["Health Profile"])
# app.include_router(reminders_router, prefix="/reminders", tags=["Reminders"])
# app.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])

if __name__ == "__main__":
    import uvicorn
    # app folder එක ඇතුලෙන් run වන නිසා "app.main:app" ලෙස වෙනස් කර ඇත
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)