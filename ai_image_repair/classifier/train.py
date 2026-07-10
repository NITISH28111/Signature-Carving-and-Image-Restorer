import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import transforms, datasets
from torchvision.models import resnet50, ResNet50_Weights
from PIL import Image
import numpy as np

# ==== CONFIG ====
DATA_DIR = './dataset'
BATCH_SIZE = 8
IMG_SIZE = 224
NUM_EPOCHS = 10
LR = 1e-4
CLASS_NAMES = ['blurry', 'noisy', 'none']
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ==== LABEL ENCODING ====
label_map = {
    'blurry': [1, 0, 0],
    'noisy':  [0, 1, 0],
    'none':   [0, 0, 1],
}

# ==== DATASET WRAPPER ====
class MultiLabelDataset(datasets.ImageFolder):
    def __getitem__(self, index):
        path, _ = self.samples[index]
        image = self.loader(path)
        label_name = os.path.basename(os.path.dirname(path))
        label = torch.tensor(label_map[label_name], dtype=torch.float32)

        if self.transform is not None:
            image = self.transform(image)

        return image, label

# ==== TRANSFORMS (matching pretrained weights) ====
weights = ResNet50_Weights.DEFAULT
transform = weights.transforms()

# ==== LOAD DATA ====
train_dataset = MultiLabelDataset(DATA_DIR, transform=transform)
train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)

# ==== MODEL ====
model = resnet50(weights=weights)
model.fc = nn.Linear(model.fc.in_features, len(CLASS_NAMES))
model = model.to(DEVICE)

# ==== TRAIN ====
criterion = nn.BCEWithLogitsLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=LR)

print("Starting training with ResNet50...\n")
for epoch in range(NUM_EPOCHS):
    model.train()
    total_loss = 0

    for images, targets in train_loader:
        images = images.to(DEVICE)
        targets = targets.to(DEVICE)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    avg_loss = total_loss / len(train_loader)
    print(f"Epoch {epoch+1}/{NUM_EPOCHS} - Loss: {avg_loss:.4f}")

torch.save(model.state_dict(), "model_resnet50_multi_label.pth")
print("Training complete! Model saved to model_resnet50_multi_label.pth")

# ==== OPTIONAL: INFERENCE FUNCTION ====
def predict_image(image_path):
    model.eval()
    image = Image.open(image_path).convert("RGB")
    image = transform(image).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        logits = model(image)
        probs = torch.sigmoid(logits).cpu().numpy()[0]

    print(f"\nPrediction for: {image_path}")
    predicted_idx = np.argmax(probs)
    predicted_label = CLASS_NAMES[predicted_idx]
    print(f"Predicted Label: **{predicted_label.upper()}**\n")
    for i, cls in enumerate(CLASS_NAMES):
        print(f"{cls}: {probs[i]:.4f} confidence")

# ==== EXAMPLE ====
# Uncomment this to test a sample image
# predict_image("test_image.jpg")
