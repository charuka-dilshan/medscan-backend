import torch
from torchvision import models, transforms
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import io
from PIL import Image
from ocr_service import extract_text_from_image
from groq_service import parse_prescription_text
import logging

app = FastAPI(title="MedScan AI Backend")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Setup Transforms (MUST match training!)
val_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# 2. Load Classes
try:
    with open('ml/class_names.json', 'r') as f:
        class_names = json.load(f)
except Exception:
    class_names = ["pill_1", "pill_2"] # Fallback

# 3. Load Model
def load_my_model():
    model = models.mobilenet_v3_small(weights=None)
    num_classes = len(class_names)
    model.classifier[3] = torch.nn.Linear(model.classifier[3].in_features, num_classes)
    try:
        model.load_state_dict(torch.load("ml/pill_model.pth", map_location=torch.device('cpu')))
    except Exception as e:
        logger.error(f"Failed to load model weights: {e}")
    model.eval()
    return model

model = load_my_model()

# 🛡️ 85% MEDICAL SAFETY GUARDRAIL ENGINE
def verify_safety_threshold(confidence: float):
    # Confidence එක 0.85 ට වඩා අඩු නම් Endpoint එක මෙතනින්ම බ්ලොක් කරනවා
    if confidence < 0.85:
        logger.warning(f"⚠️ SAFETY BLOCK TRIGGERED: Low confidence score detected: {confidence:.4f}")
        raise HTTPException(
            status_code=422, 
            detail={
                "status": "safety_block",
                "confidence": confidence,
                "msg": "The analysis falls below the required 85% medical safety threshold. Please ensure good lighting and re-take the photo."
            }
        )
    return True

# 4. Endpoints

# Endpoint 1: Root Health Check
@app.get("/")
async def root():
    return {"message": "MedScan AI Backend is operational."}

# Endpoint 2: Pill Classification Image Model
@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    try:
        # Load and Transform
        image = Image.open(io.BytesIO(await file.read())).convert("RGB")
        image_tensor = val_transform(image).unsqueeze(0)
        
        # Inference
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

# Placeholder for your existing prescription logic
class OCRRequest(BaseModel):
    raw_text: str

# Endpoint 3: Parse Unstructured Prescription Text
@app.post("/parse-prescription")
def parse_prescription(request: OCRRequest):
    return {"status": "success", "data": "Prescription parsing logic goes here"}

# Endpoint 4: Full OCR Scanning & AI Structuring Pipeline
@app.post("/scan-prescription")
async def scan_prescription(file: UploadFile = File(...)):
    try:
        # 1. Read file
        contents = await file.read()
        
        # 2. OCR Extraction
        ocr_result = extract_text_from_image(contents)
        raw_text = ocr_result.get("text", "")
        ocr_confidence = ocr_result.get("confidence", 0.0) # Real OCR confidence extractor
        
        if not raw_text.strip():
            raise HTTPException(status_code=400, detail="OCR failed to find text.")

        # 🛡️ Enforce 85% safety rule for OCR Reading
        verify_safety_threshold(ocr_confidence)

        # 3. AI Parsing
        ai_data = parse_prescription_text(raw_text)
        
        if "error" in ai_data:
            raise HTTPException(status_code=500, detail="AI parsing failed.")

        # 4. Final Response
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

# 🚀 5. Uvicorn Server Initialization (ෆයිල් එකේ අන්තිමටම තියෙන්න ඕනේ!)
if __name__ == "__main__":
    import uvicorn
    # reload=True දාලා තියෙන්නේ කෝඩ් වෙනස් කරද්දී auto-restart වෙන්න
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)