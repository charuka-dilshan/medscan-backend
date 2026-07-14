import torch
from torchvision import models, transforms
from PIL import Image
import json

# 1. Load the architecture (Must match what you used in train.py!)
num_classes = 3 # Change this to match your actual number of classes
model = models.mobilenet_v3_small()
model.classifier[3] = torch.nn.Linear(model.classifier[3].in_features, num_classes)
model.load_state_dict(torch.load("pill_model.pth"))
model.eval()

# 2. Prepare the image
img = Image.open("path_to_a_test_photo.jpg").convert("RGB")
preprocess = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])
img_tensor = preprocess(img).unsqueeze(0) # Add batch dimension

# 3. Predict
with torch.no_grad():
    logits = model(img_tensor)
    probs = torch.nn.functional.softmax(logits, dim=1)
    confidence, idx = torch.max(probs, dim=1)

with open('class_names.json', 'r') as f:
    classes = json.load(f)

print(f"Prediction: {classes[idx.item()]}")
print(f"Confidence: {confidence.item():.4f}")