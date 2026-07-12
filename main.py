import torch
from torchvision import models, transforms
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import io
from PIL import Image

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