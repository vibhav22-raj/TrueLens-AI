import cv2
import numpy as np
import torch
from PIL import Image
from torchvision import transforms


def get_transform(size=224):
    return transforms.Compose([
        transforms.Resize((size, size)),
        transforms.ToTensor(),
    ])


def read_image_bgr(path):
    img = cv2.imread(path)
    if img is None:
        raise ValueError(f"Failed to read image: {path}")
    return img


def bgr_to_tensor(img_bgr, size=224):
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(img_rgb)
    t = get_transform(size)(pil)
    return t.unsqueeze(0)


def tensor_to_bgr(t):
    t = t.squeeze(0).permute(1, 2, 0).detach().cpu().numpy()
    t = np.clip(t * 255.0, 0, 255).astype(np.uint8)
    return cv2.cvtColor(t, cv2.COLOR_RGB2BGR)
