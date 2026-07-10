import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets
from torchvision.models import resnet50, ResNet50_Weights
from sklearn.metrics import classification_report
import numpy as np

# ==== CONFIG ====
CLASS_NAMES = ['blurry', 'noisy', 'none']
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_PATH = "model_resnet50_multi_label.pth"
DATA_PATH = "./test_data"  # <- Path to test/val dataset

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

# ==== TRANSFORM ====
transform = ResNet50_Weights.DEFAULT.transforms()

# ==== LOAD MODEL ====
def load_model():
    model = resnet50(weights=None)
    model.fc = nn.Linear(model.fc.in_features, len(CLASS_NAMES))
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model.to(DEVICE)
    model.eval()
    return model

# ==== EVALUATION ====
def evaluate(data_path):
    dataset = MultiLabelDataset(data_path, transform=transform)
    dataloader = DataLoader(dataset, batch_size=1, shuffle=False)

    model = load_model()
    y_true, y_pred = [], []

    with torch.no_grad():
        for images, targets in dataloader:
            images = images.to(DEVICE)
            logits = model(images)
            probs = torch.sigmoid(logits).cpu().numpy()
            pred = np.argmax(probs, axis=1)
            true = np.argmax(targets.numpy(), axis=1)

            y_true.extend(true)
            y_pred.extend(pred)

    print("\n=== Classification Report ===")
    print(classification_report(y_true, y_pred, target_names=CLASS_NAMES))

# ==== MAIN ====
if __name__ == "__main__":
    evaluate(DATA_PATH)
