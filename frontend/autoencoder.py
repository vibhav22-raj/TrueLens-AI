"""
autoencoder.py - Convolutional Autoencoder for Anomaly Detection
Detects unusual patterns in images that CNNs might miss.
Trained only on REAL images → high reconstruction error = FAKE
"""

import torch
import torch.nn as nn
import numpy as np
from PIL import Image
import torchvision.transforms as transforms
import os


# ─────────────────────────────────────────────
#  Encoder Block
# ─────────────────────────────────────────────

class EncoderBlock(nn.Module):
    def __init__(self, in_ch, out_ch, stride=2):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 4, stride=stride, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, stride=1, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.LeakyReLU(0.2, inplace=True),
        )

    def forward(self, x):
        return self.block(x)


# ─────────────────────────────────────────────
#  Decoder Block
# ─────────────────────────────────────────────

class DecoderBlock(nn.Module):
    def __init__(self, in_ch, out_ch, stride=2):
        super().__init__()
        self.block = nn.Sequential(
            nn.ConvTranspose2d(in_ch, out_ch, 4, stride=stride, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, stride=1, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.block(x)


# ─────────────────────────────────────────────
#  Convolutional Autoencoder
# ─────────────────────────────────────────────

class ConvAutoencoder(nn.Module):
    """
    Deep Convolutional Autoencoder for anomaly detection.
    Input: 3×128×128 image
    Latent: 512-dim vector
    """

    def __init__(self, latent_dim: int = 512):
        super(ConvAutoencoder, self).__init__()

        # Encoder: 128 → 64 → 32 → 16 → 8 → 4
        self.encoder = nn.Sequential(
            EncoderBlock(3, 32),       # 128 → 64
            EncoderBlock(32, 64),      # 64 → 32
            EncoderBlock(64, 128),     # 32 → 16
            EncoderBlock(128, 256),    # 16 → 8
            EncoderBlock(256, 512),    # 8 → 4
        )

        # Bottleneck
        self.flatten = nn.Flatten()
        self.fc_encode = nn.Linear(512 * 4 * 4, latent_dim)
        self.fc_decode = nn.Linear(latent_dim, 512 * 4 * 4)

        # Decoder: 4 → 8 → 16 → 32 → 64 → 128
        self.decoder = nn.Sequential(
            DecoderBlock(512, 256),    # 4 → 8
            DecoderBlock(256, 128),    # 8 → 16
            DecoderBlock(128, 64),     # 16 → 32
            DecoderBlock(64, 32),      # 32 → 64
            DecoderBlock(32, 16),      # 64 → 128
            nn.Conv2d(16, 3, 3, padding=1),
            nn.Sigmoid()
        )

        self.latent_dim = latent_dim

    def encode(self, x):
        h = self.encoder(x)
        h = self.flatten(h)
        z = self.fc_encode(h)
        return z

    def decode(self, z):
        h = self.fc_decode(z)
        h = h.view(-1, 512, 4, 4)
        return self.decoder(h)

    def forward(self, x):
        z = self.encode(x)
        recon = self.decode(z)
        return recon, z

    def reconstruction_error(self, x, reduction="pixel"):
        """
        Compute per-pixel or per-image reconstruction error.
        High error → likely FAKE (anomalous)
        """
        with torch.no_grad():
            recon, _ = self.forward(x)
            diff = torch.abs(x - recon)  # Per-pixel absolute error

            if reduction == "pixel":
                return diff  # shape: (B, C, H, W)
            elif reduction == "image":
                return diff.mean(dim=[1, 2, 3])  # shape: (B,)
            elif reduction == "mean":
                return diff.mean().item()

    def get_error_map(self, x):
        """
        Returns grayscale error map for visualization.
        Used by Grad-CAM to show suspicious regions.
        """
        diff = self.reconstruction_error(x, reduction="pixel")
        # Average across channels → single-channel heatmap
        error_map = diff.mean(dim=1, keepdim=True)
        return error_map  # shape: (B, 1, H, W)


# ─────────────────────────────────────────────
#  Anomaly Inference
# ─────────────────────────────────────────────

class AnomalyDetector:
    """
    Wrapper for autoencoder-based anomaly detection.
    Thresholds computed from real images during calibration.
    """

    def __init__(self, model_path: str = None, device: str = None,
                 threshold: float = 0.05, image_size: int = 128):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.threshold = threshold
        self.image_size = image_size

        self.transform = transforms.Compose([
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            # Normalize to [0,1] for reconstruction
        ])

        self.model = ConvAutoencoder()
        self.model = self.model.to(self.device)

        if model_path and os.path.exists(model_path):
            checkpoint = torch.load(model_path, map_location=self.device)
            self.model.load_state_dict(checkpoint.get("model_state_dict", checkpoint))
            self.threshold = checkpoint.get("threshold", threshold)
            print(f"[✓] Autoencoder loaded from: {model_path} | Threshold: {self.threshold:.4f}")
        else:
            print("[!] Using untrained autoencoder (demo mode)")

        self.model.eval()

    def preprocess(self, image: Image.Image) -> torch.Tensor:
        if image.mode != "RGB":
            image = image.convert("RGB")
        return self.transform(image).unsqueeze(0).to(self.device)

    @torch.no_grad()
    def predict(self, image: Image.Image) -> dict:
        """
        Returns anomaly score and binary prediction.
        Score > threshold → FAKE (anomalous)
        """
        tensor = self.preprocess(image)
        error = self.model.reconstruction_error(tensor, reduction="image")
        score = error.item()
        is_anomaly = score > self.threshold
        confidence = min(score / (self.threshold * 2), 1.0) if is_anomaly else max(1 - score / self.threshold, 0.0)

        return {
            "anomaly_score": round(score, 6),
            "threshold": self.threshold,
            "is_anomaly": is_anomaly,
            "label": "FAKE" if is_anomaly else "REAL",
            "anomaly_confidence": round(confidence * 100, 2)
        }

    @torch.no_grad()
    def get_error_heatmap(self, image: Image.Image) -> np.ndarray:
        """
        Returns a numpy heatmap (H×W) of reconstruction error.
        Brighter = more suspicious region.
        """
        tensor = self.preprocess(image)
        error_map = self.model.get_error_map(tensor)

        # Convert to numpy and resize to original image size
        heatmap = error_map.squeeze().cpu().numpy()  # (H, W)
        # Normalize to 0-255
        if heatmap.max() > 0:
            heatmap = (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min())
        heatmap = (heatmap * 255).astype(np.uint8)
        return heatmap

    def calibrate_threshold(self, real_images: list, percentile: float = 95.0):
        """
        Compute threshold from real images.
        Call after loading the model with real validation data.
        """
        errors = []
        self.model.eval()
        with torch.no_grad():
            for img in real_images:
                tensor = self.preprocess(img)
                error = self.model.reconstruction_error(tensor, reduction="image")
                errors.append(error.item())

        self.threshold = float(np.percentile(errors, percentile))
        print(f"[✓] Calibrated threshold ({percentile}th percentile): {self.threshold:.6f}")
        return self.threshold


# ─────────────────────────────────────────────
#  Training Utilities
# ─────────────────────────────────────────────

class PerceptualLoss(nn.Module):
    """
    Combined MSE + SSIM-style loss for better reconstruction.
    """

    def __init__(self, mse_weight: float = 1.0, l1_weight: float = 0.5):
        super().__init__()
        self.mse = nn.MSELoss()
        self.l1 = nn.L1Loss()
        self.mse_w = mse_weight
        self.l1_w = l1_weight

    def forward(self, recon, target):
        return self.mse_w * self.mse(recon, target) + self.l1_w * self.l1(recon, target)


def train_autoencoder(model, loader, optimizer, criterion, device, epochs: int = 50):
    """
    Train autoencoder ONLY on real images.
    Loop:
    for epoch in range(epochs):
        result = train_one_ae_epoch(model, loader, optimizer, criterion, device)
        print(f"Epoch {epoch+1}: Loss={result['loss']:.6f}")
    """
    model.train()
    total_loss = 0.0

    for images, _ in loader:  # We ignore labels (train only on reals)
        images = images.to(device)
        optimizer.zero_grad()
        recon, _ = model(images)
        loss = criterion(recon, images)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        total_loss += loss.item()

    return {"loss": total_loss / len(loader)}


if __name__ == "__main__":
    print("Testing ConvAutoencoder...")
    model = ConvAutoencoder(latent_dim=512)
    dummy = torch.randn(2, 3, 128, 128)
    recon, z = model(dummy)
    print(f"Input: {dummy.shape} | Reconstruction: {recon.shape} | Latent: {z.shape}")
    error = model.reconstruction_error(dummy, reduction="image")
    print(f"Reconstruction error: {error}")
    print("✓ Autoencoder test passed!")
