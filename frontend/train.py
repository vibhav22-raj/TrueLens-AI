"""
train.py - Training Script for Deepfake Detection Models
Trains both CNN (EfficientNet) and Autoencoder models.

Usage:
    python frontend/train.py --data_dir /path/to/dataset --epochs 20 --batch_size 32

Dataset Structure Expected:
    data/
    ├── train/
    │   ├── real/   (real face images)
    │   └── fake/   (deepfake images)
    └── val/
        ├── real/
        └── fake/
"""

import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from sklearn.metrics import f1_score, roc_auc_score
import numpy as np
from PIL import Image
import os
import argparse
import json
from pathlib import Path

from cnn_model import DeepfakeDetector, FocalLoss, get_optimizer, get_transforms, train_one_epoch, evaluate
from autoencoder import ConvAutoencoder, PerceptualLoss, train_autoencoder


# ─────────────────────────────────────────────
#  Dataset
# ─────────────────────────────────────────────

class DeepfakeDataset(Dataset):
    """
    Custom dataset for deepfake detection.
    Expects folder structure: root/real/*.jpg and root/fake/*.jpg
    """

    def __init__(self, root_dir: str, phase: str = "train",
                 image_size: int = 224, max_per_class: int = None):
        self.root_dir = Path(root_dir)
        self.phase = phase
        self.transform = get_transforms(phase, image_size)
        self.samples = []

        real_dir = self.root_dir / "real"
        fake_dir = self.root_dir / "fake"

        exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

        real_files = [f for f in real_dir.iterdir() if f.suffix.lower() in exts]
        fake_files = [f for f in fake_dir.iterdir() if f.suffix.lower() in exts]

        if max_per_class:
            real_files = real_files[:max_per_class]
            fake_files = fake_files[:max_per_class]

        for f in real_files:
            self.samples.append((str(f), 0))  # 0 = real
        for f in fake_files:
            self.samples.append((str(f), 1))  # 1 = fake

        print(f"[{phase}] Loaded: {len(real_files)} real, {len(fake_files)} fake")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        image = Image.open(path).convert("RGB")
        return self.transform(image), torch.tensor(label, dtype=torch.long)


class RealOnlyDataset(Dataset):
    """Dataset containing only real images for autoencoder training"""

    def __init__(self, root_dir: str, image_size: int = 128):
        self.root_dir = Path(root_dir) / "real"
        self.transform = transforms.Compose([
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor()
        ])
        exts = {".jpg", ".jpeg", ".png", ".webp"}
        self.files = [f for f in self.root_dir.iterdir() if f.suffix.lower() in exts]
        print(f"[AE Train] Loaded {len(self.files)} real images")

    def __len__(self):
        return len(self.files)

    def __getitem__(self, idx):
        path = self.files[idx]
        image = Image.open(str(path)).convert("RGB")
        return self.transform(image), 0  # label unused


# ─────────────────────────────────────────────
#  Training: CNN
# ─────────────────────────────────────────────

def train_cnn(args):
    print("\n" + "═" * 60)
    print("   Training EfficientNet-B4 Deepfake Detector")
    print("═" * 60)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")

    # Datasets
    train_ds = DeepfakeDataset(os.path.join(args.data_dir, "train"), "train",
                                args.image_size, args.max_per_class)
    val_ds   = DeepfakeDataset(os.path.join(args.data_dir, "val"),   "val",
                                args.image_size, args.max_per_class)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,
                               num_workers=4, pin_memory=(device == "cuda"))
    val_loader   = DataLoader(val_ds,   batch_size=args.batch_size, shuffle=False,
                               num_workers=4, pin_memory=(device == "cuda"))

    # Model, optimizer, scheduler
    model = DeepfakeDetector(pretrained=True).to(device)
    criterion = FocalLoss(alpha=0.25, gamma=2.0)
    optimizer = get_optimizer(model, lr=args.lr)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    scaler = torch.cuda.amp.GradScaler() if device == "cuda" else None

    model_dir = Path(__file__).resolve().parent / "model"
    model_dir.mkdir(parents=True, exist_ok=True)

    best_val_acc = 0.0
    history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": []}

    for epoch in range(1, args.epochs + 1):
        print(f"\n[Epoch {epoch}/{args.epochs}]")

        train_metrics = train_one_epoch(model, train_loader, optimizer, criterion,
                                         device, scaler)
        val_metrics   = evaluate(model, val_loader, criterion, device)
        scheduler.step()

        history["train_loss"].append(train_metrics["loss"])
        history["train_acc"].append(train_metrics["accuracy"])
        history["val_loss"].append(val_metrics["loss"])
        history["val_acc"].append(val_metrics["accuracy"])

        print(f"  Train → Loss: {train_metrics['loss']:.4f} | Acc: {train_metrics['accuracy']*100:.2f}%")
        print(f"  Val   → Loss: {val_metrics['loss']:.4f}   | Acc: {val_metrics['accuracy']*100:.2f}%")

        # Save best model
        if val_metrics["accuracy"] > best_val_acc:
            best_val_acc = val_metrics["accuracy"]
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_accuracy": best_val_acc
            }, model_dir / "deepfake_model.pth")
            print(f"  ✓ Best model saved! Val Acc: {best_val_acc*100:.2f}%")

    # Save training history
    with open(model_dir / "cnn_history.json", "w") as f:
        json.dump(history, f, indent=2)

    print(f"\n✓ CNN Training Complete! Best Val Accuracy: {best_val_acc*100:.2f}%")
    return model


# ─────────────────────────────────────────────
#  Training: Autoencoder
# ─────────────────────────────────────────────

def train_ae(args):
    print("\n" + "═" * 60)
    print("   Training Convolutional Autoencoder")
    print("═" * 60)

    device = "cuda" if torch.cuda.is_available() else "cpu"

    train_ds = RealOnlyDataset(os.path.join(args.data_dir, "train"), 128)
    val_ds   = RealOnlyDataset(os.path.join(args.data_dir, "val"),   128)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,
                               num_workers=4, pin_memory=(device == "cuda"))

    model = ConvAutoencoder().to(device)
    criterion = PerceptualLoss(mse_weight=1.0, l1_weight=0.5)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5,
                                                            factor=0.5, verbose=True)

    model_dir = Path(__file__).resolve().parent / "model"
    model_dir.mkdir(parents=True, exist_ok=True)

    best_loss = float("inf")

    for epoch in range(1, args.ae_epochs + 1):
        result = train_autoencoder(model, train_loader, optimizer, criterion, device)
        scheduler.step(result["loss"])

        if epoch % 5 == 0 or epoch == 1:
            print(f"[AE Epoch {epoch}/{args.ae_epochs}] Loss: {result['loss']:.6f}")

        if result["loss"] < best_loss:
            best_loss = result["loss"]

            # Calibrate threshold on val real images
            model.eval()
            val_imgs = [Image.open(str(f)).convert("RGB")
                        for f in list(val_ds.files)[:500]]
            transform = transforms.Compose([
                transforms.Resize((128, 128)),
                transforms.ToTensor()
            ])
            errors = []
            with torch.no_grad():
                for img in val_imgs:
                    tensor = transform(img).unsqueeze(0).to(device)
                    err = model.reconstruction_error(tensor, reduction="image")
                    errors.append(err.item())
            threshold = float(np.percentile(errors, 95))

            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "best_loss": best_loss,
                "threshold": threshold
            }, model_dir / "autoencoder.pth")

    print(f"\n✓ Autoencoder Training Complete! Best Loss: {best_loss:.6f}")
    return model


# ─────────────────────────────────────────────
#  Evaluation on Test Set
# ─────────────────────────────────────────────

def evaluate_on_test(args):
    from sklearn.metrics import classification_report

    device = "cuda" if torch.cuda.is_available() else "cpu"
    test_ds = DeepfakeDataset(os.path.join(args.data_dir, "test"), "val",
                               args.image_size, args.max_per_class)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, num_workers=4)

    model = DeepfakeDetector(pretrained=False)
    checkpoint = torch.load(Path(__file__).resolve().parent / "model" / "deepfake_model.pth", map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model = model.to(device)

    criterion = FocalLoss()
    results = evaluate(model, test_loader, criterion, device)

    y_pred = [1 if p >= 0.5 else 0 for p in results["probabilities"]]
    print("\n" + "═" * 50)
    print("  TEST SET EVALUATION")
    print("═" * 50)
    print(f"  Accuracy : {results['accuracy']*100:.2f}%")
    print(f"  AUC-ROC  : {roc_auc_score(results['labels'], results['probabilities'])*100:.2f}%")
    print(f"  F1 Score : {f1_score(results['labels'], y_pred)*100:.2f}%")
    print("\n" + classification_report(results["labels"], y_pred,
                                        target_names=["Real", "Fake"]))


# ─────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="Deepfake Detection Training")
    parser.add_argument("--data_dir", type=str, default="data",
                        help="Root data directory with train/val/test subdirs")
    parser.add_argument("--epochs", type=int, default=20, help="CNN training epochs")
    parser.add_argument("--ae_epochs", type=int, default=50, help="Autoencoder epochs")
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--image_size", type=int, default=224)
    parser.add_argument("--max_per_class", type=int, default=None,
                        help="Limit samples per class for quick testing")
    parser.add_argument("--train_cnn", action="store_true", default=True)
    parser.add_argument("--train_ae", action="store_true", default=True)
    parser.add_argument("--evaluate", action="store_true", default=False)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    print("🛡️ DeepShield AI — Training Pipeline")
    print(f"Data dir: {args.data_dir}")
    print(f"Device: {'CUDA' if torch.cuda.is_available() else 'CPU'}")

    if args.train_cnn:
        train_cnn(args)

    if args.train_ae:
        train_ae(args)

    if args.evaluate:
        evaluate_on_test(args)

    print("\n✅ All training complete! Run: streamlit run frontend/streamlit_app.py")
