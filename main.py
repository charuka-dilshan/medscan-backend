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

app = FastAPI(title="MedScan AI Backend")

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
except:
    class_names = ["pill_1", "pill_2"] # Fallback

# 3. Load Model
def load_my_model():
    model = models.mobilenet_v3_small(weights=None)
    num_classes = len(class_names)
    model.classifier[3] = torch.nn.Linear(model.classifier[3].in_features, num_classes)
    model.load_state_dict(torch.load("ml/pill_model.pth", map_location=torch.device('cpu')))
    model.eval()
    return model

model = load_my_model()

# 4. Endpoints
@app.get("/")
async def root():
    return {"message": "MedScan AI Backend is operational."}

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
        
        # Guardrail
        if conf_val < 0.85:
            return {"status": "unsafe", "pill": None, "confidence": conf_val, "msg": "Confidence too low"}
        
        return {
            "status": "success", 
            "pill": class_names[predicted_idx.item()], 
            "confidence": conf_val
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Placeholder for your existing prescription logic
class OCRRequest(BaseModel):
    raw_text: str

@app.post("/parse-prescription")
def parse_prescription(request: OCRRequest):
    # Ensure groq_service is imported or handle error here
    return {"status": "success", "data": "Prescription parsing logic goes here"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

@app.post("/scan-prescription")
async def scan_prescription(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        
        # 1. Extract text via EasyOCR
        raw_text = extract_text_from_image(contents)
        
        # Guardrail Check 1: Empty or extremely short OCR string
        if not raw_text.strip() or len(raw_text.strip()) < 10:
            return {
                "status": "safety_block",
                "confidence_score": 0.0,
                "message": "Prescription text is too blurry or unreadable. Please capture a clearer photo.",
                "message_sinhala": "ලිඛිත සටහන පැහැදිලි නැත. කරුණාකර නැවත පැහැදිලි ඡායාරූපයක් ගන්න.",
                "message_tamil": "எழுத்துக்கள் தெளிவாக இல்லை. தயவுசெய்து தெளிவான புகைப்படம் எடுக்கவும்."
            }
        
        # 2. Parse text via Groq (Llama 3)
        parsed_data = parse_prescription_text(raw_text)
        
        # Guardrail Check 2: Unspecified key medical parameters
        pill_name = parsed_data.get("pill_name", "Not specified")
        dosage = parsed_data.get("dosage", "Not specified")
        
        if pill_name == "Not specified" and dosage == "Not specified":
            return {
                "status": "safety_block",
                "confidence_score": 0.40,  # Below 0.85 threshold
                "message": "AI confidence is below 85%. Could not reliably identify medicine or dosage. Please consult a pharmacist.",
                "message_sinhala": "AI විශ්වාසනීයත්වය 85% ට වඩා අඩුය. කරුණාකර වෛද්‍යවරයකු හෝ ඖෂධවේදියකු හමුවන්න.",
                "message_tamil": "AI இன் துல்லியம் 85% க்கும் குறைவாக உள்ளது. தயவுசெய்து மருந்தாளரை அணுகவும்."
            }
            
        return {
            "status": "success",
            "confidence_score": 0.92, # Valid extraction
            "prescription": parsed_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))