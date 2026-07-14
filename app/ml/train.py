import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, models, transforms
from torch.utils.data import DataLoader
import json

# 1. Setup Data Directories
data_dir = './dataset'
batch_size = 16

# 2. Preprocessing & Augmentation
# We use ImageNet normalization stats as we are using pretrained weights
transform = {
    'train': transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomRotation(15),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
    'val': transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
}

# Load datasets
train_dataset = datasets.ImageFolder(f'{data_dir}/train', transform=transform['train'])
val_dataset = datasets.ImageFolder(f'{data_dir}/val', transform=transform['val'])

train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

# Save class mapping for the backend
with open('class_names.json', 'w') as f:
    json.dump(train_dataset.classes, f)

# 3. Model Setup (Transfer Learning)
model = models.mobilenet_v3_small(weights='DEFAULT')
# Freeze weights
for param in model.parameters():
    param.requires_grad = False

# Replace head: MobileNetV3 small uses model.classifier[3] for the final layer
num_classes = len(train_dataset.classes)
model.classifier[3] = nn.Linear(model.classifier[3].in_features, num_classes)

# 4. Loss and Optimizer
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.classifier[3].parameters(), lr=1e-4)

# 5. Training Loop
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

print("Starting training...")
for epoch in range(10): # Adjust epochs based on your convergence
    model.train()
    for inputs, labels in train_loader:
        inputs, labels = inputs.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

    print(f"Epoch {epoch+1} complete.")

# 6. Save the model
torch.save(model.state_dict(), "pill_model.pth")
print("Model saved as pill_model.pth")