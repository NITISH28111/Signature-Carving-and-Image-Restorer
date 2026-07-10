import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.transforms.functional as TF
from PIL import Image
import os
from runpy import run_path
from skimage import img_as_ubyte
from collections import OrderedDict
from natsort import natsorted
from glob import glob
import cv2
import argparse

parser = argparse.ArgumentParser(description='Demo MPRNet')
parser.add_argument('--input_dir', default='./samples/input/', type=str, help='Input images')
parser.add_argument('--result_dir', default='./samples/output/', type=str, help='Directory for results')
parser.add_argument('--task', required=True, type=str, help='Task to run', choices=['Deblurring', 'Denoising', 'Deraining'])

args = parser.parse_args()

# Add base dir resolution
base_dir = os.path.dirname(os.path.abspath(__file__))
task_dir = os.path.join(base_dir, args.task)

def save_img(filepath, img):
    cv2.imwrite(filepath, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))

def load_checkpoint(model, weights):
    checkpoint = torch.load(weights, map_location='cpu')
    try:
        model.load_state_dict(checkpoint["state_dict"])
    except:
        state_dict = checkpoint["state_dict"]
        new_state_dict = OrderedDict()
        for k, v in state_dict.items():
            name = k[7:]  # remove `module.`
            new_state_dict[name] = v
        model.load_state_dict(new_state_dict)

task = args.task
inp_dir = args.input_dir
out_dir = args.result_dir

os.makedirs(out_dir, exist_ok=True)

files = natsorted(glob(os.path.join(inp_dir, '*.jpg'))
                  + glob(os.path.join(inp_dir, '*.JPG'))
                  + glob(os.path.join(inp_dir, '*.png'))
                  + glob(os.path.join(inp_dir, '*.PNG')))

if len(files) == 0:
    raise Exception(f"No files found at {inp_dir}")

# Load corresponding model architecture and weights
load_file = run_path(os.path.join(task_dir, "MPRNet.py"))
model = load_file['MPRNet']()

# Move model to device (cuda if available, else cpu)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = model.to(device)

weights = os.path.join(task_dir, "pretrained_models", f"model_{task.lower()}.pth")
load_checkpoint(model, weights)
model.eval()

img_multiple_of = 8

for file_ in files:
    img = Image.open(file_).convert('RGB')

    # Resize if image too large
    max_dim = 512  # You can adjust this number
    w, h = img.size
    if max(w, h) > max_dim:
        scale = max_dim / max(w, h)
        img = img.resize((int(w*scale), int(h*scale)), Image.BICUBIC)

    input_ = TF.to_tensor(img).unsqueeze(0).to(device)

    # Pad the input if not_multiple_of 8
    h, w = input_.shape[2], input_.shape[3]
    H, W = ((h + img_multiple_of) // img_multiple_of) * img_multiple_of, ((w + img_multiple_of) // img_multiple_of) * img_multiple_of
    padh = H - h if h % img_multiple_of != 0 else 0
    padw = W - w if w % img_multiple_of != 0 else 0
    input_ = F.pad(input_, (0, padw, 0, padh), 'reflect')

    with torch.no_grad():
        restored = model(input_)

    # Handle model output - select first item if output is a tuple/list
    if isinstance(restored, (tuple, list)):
        restored = restored[0]
    
    # Remove batch dimension and clamp values
    restored = restored[0].clamp(0, 1)

    # Unpad the output
    restored = restored[:, :h, :w]

    # Convert to numpy array and save
    restored = restored.permute(1, 2, 0).cpu().detach().numpy()
    restored = img_as_ubyte(restored)

    f = os.path.splitext(os.path.split(file_)[-1])[0]
    save_img((os.path.join(out_dir, f+'.png')), restored)

    # Free GPU memory after each file
    torch.cuda.empty_cache()

print(f"Files saved at {out_dir}")