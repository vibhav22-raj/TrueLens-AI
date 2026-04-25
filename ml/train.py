import argparse
import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm

from ml.datasets import ImageFolderDataset
from ml.models import CNNDetector, ConvAutoencoder


def train_cnn(model, loader, device, epochs=5, lr=1e-4):
    model.train()
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    ce = nn.CrossEntropyLoss()
    for epoch in range(epochs):
        pbar = tqdm(loader, desc=f"CNN Epoch {epoch+1}/{epochs}")
        for x, y in pbar:
            x, y = x.to(device), y.to(device)
            logits, _ = model(x)
            loss = ce(logits, y)
            opt.zero_grad()
            loss.backward()
            opt.step()
            pbar.set_postfix({"loss": loss.item()})


def train_ae(model, loader, device, epochs=5, lr=1e-4):
    model.train()
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    mse = nn.MSELoss()
    for epoch in range(epochs):
        pbar = tqdm(loader, desc=f"AE Epoch {epoch+1}/{epochs}")
        for x, _ in pbar:
            x = x.to(device)
            recon, _ = model(x)
            loss = mse(recon, x)
            opt.zero_grad()
            loss.backward()
            opt.step()
            pbar.set_postfix({"loss": loss.item()})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="Path to dataset root with real/ fake folders")
    parser.add_argument("--out", default="artifacts", help="Output directory")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--backbone", default="resnet18")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    dataset = ImageFolderDataset(args.data)
    loader = DataLoader(dataset, batch_size=args.batch, shuffle=True, num_workers=0)

    cnn = CNNDetector(backbone=args.backbone).to(device)
    ae = ConvAutoencoder().to(device)

    train_cnn(cnn, loader, device, epochs=args.epochs)
    train_ae(ae, loader, device, epochs=args.epochs)

    torch.save(cnn.state_dict(), os.path.join(args.out, "cnn.pt"))
    torch.save(ae.state_dict(), os.path.join(args.out, "ae.pt"))


if __name__ == "__main__":
    main()
