import torch.nn.functional as F

def get_prediction(model, image_tensor):
    model.eval()
    with torch.no_grad():
        logits = model(image_tensor)
        probabilities = F.softmax(logits, dim=1) # This gives you the 0.0-1.0 range
        confidence, predicted_idx = torch.max(probabilities, dim=1)
        
    return confidence.item(), predicted_idx.item()