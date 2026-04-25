import os
from glob import glob
from PIL import Image
import torch
from torch.utils.data import Dataset
from torchvision import transforms


class ImageFolderDataset(Dataset):
    def __init__(self, root, size=224):
        self.samples = []
        self.transform = transforms.Compose([
            transforms.Resize((size, size)),
            transforms.ToTensor(),
        ])
        for label_name in ["real", "fake"]:
            label_dir = os.path.join(root, label_name)
            if not os.path.isdir(label_dir):
                continue
            for p in glob(os.path.join(label_dir, "**", "*.jpg"), recursive=True):
                self.samples.append((p, 0 if label_name == "real" else 1))
            for p in glob(os.path.join(label_dir, "**", "*.png"), recursive=True):
                self.samples.append((p, 0 if label_name == "real" else 1))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        img = Image.open(path).convert("RGB")
        return self.transform(img), torch.tensor(label, dtype=torch.long)
