import torch
from torchvision.models import resnet50, ResNet50_Weights
from torchvision import transforms
from PIL import Image
import numpy as np

# ==== CONFIG ====
MODEL_PATH = "model_resnet50_multi_label.pth"
CLASS_NAMES = ['blurry', 'noisy', 'none']
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ==== LOAD MODEL ====
def load_model():
    model = resnet50(weights=None)
    model.fc = torch.nn.Linear(model.fc.in_features, len(CLASS_NAMES))
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model.to(DEVICE)
    model.eval()
    return model

# ==== TRANSFORM (same as training) ====
transform = ResNet50_Weights.DEFAULT.transforms()

# ==== PREDICT FUNCTION ====
def predict_image(image_path, model):
    image = Image.open(image_path).convert("RGB")
    image = transform(image).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        logits = model(image)
        probs = torch.sigmoid(logits).cpu().numpy()[0]

    predicted_idx = np.argmax(probs)
    predicted_label = CLASS_NAMES[predicted_idx]

    print(f"\nPrediction for: {image_path}")
    print(f"Predicted Label: **{predicted_label.upper()}**\n")
    for i, cls in enumerate(CLASS_NAMES):
        print(f"{cls}: {probs[i]:.4f} confidence")

# ==== MAIN ====
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=str, required=True, help="Path to the image file")
    args = parser.parse_args()

    model = load_model()
    predict_image(args.image, model)
