"""
cnn_model.py - EfficientNet-based Deepfake Detection Model
Uses pretrained EfficientNet-B4 with custom classification head
"""

import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
import timm
import os


# ─────────────────────────────────────────────
#  Model Architecture
# ─────────────────────────────────────────────

class DeepfakeDetector(nn.Module):
    """
    EfficientNet-B4 backbone with custom head for binary classification.
    Real (0) vs Fake (1)
    """

    def __init__(self, model_name: str = "efficientnet_b4", pretrained: bool = True, dropout: float = 0.4):
        super(DeepfakeDetector, self).__init__()

        # Load pretrained EfficientNet backbone
        self.backbone = timm.create_model(model_name, pretrained=pretrained, num_classes=0)
        feature_dim = self.backbone.num_features  # 1792 for B4

        # Custom classification head
        self.classifier = nn.Sequential(
            nn.Linear(feature_dim, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(512, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout / 2),
            nn.Linear(128, 1)  # Binary output
        )

        # Attention module for feature refinement
        self.attention = nn.Sequential(
            nn.Linear(feature_dim, feature_dim // 4),
            nn.ReLU(),
            nn.Linear(feature_dim // 4, feature_dim),
            nn.Sigmoid()
        )

    def forward(self, x):
        features = self.backbone(x)
        # Apply attention
        attn_weights = self.attention(features)
        features = features * attn_weights
        logits = self.classifier(features)
        return logits

    def get_features(self, x):
        """Extract feature embeddings"""
        return self.backbone(x)


# ─────────────────────────────────────────────
#  Transforms
# ─────────────────────────────────────────────

def get_transforms(phase: str = "val", image_size: int = 224):
    """
    Returns appropriate transforms for train/val/test phases.
    """
    if phase == "train":
        return transforms.Compose([
            transforms.Resize((image_size + 32, image_size + 32)),
            transforms.RandomCrop(image_size),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.1),
            transforms.RandomRotation(degrees=10),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])
    else:
        return transforms.Compose([
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])


# ─────────────────────────────────────────────
#  Inference Engine
# ─────────────────────────────────────────────

class DeepfakeInference:
    """
    High-level inference class for deepfake detection.
    Handles model loading, preprocessing, and prediction.
    """

    def __init__(self, model_path: str = None, device: str = None, image_size: int = 224):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.image_size = image_size
        self.transform = get_transforms("val", image_size)

        # Initialize model
        self.model = DeepfakeDetector(pretrained=(model_path is None))
        self.model = self.model.to(self.device)

        # Load weights if provided
        if model_path and os.path.exists(model_path):
            checkpoint = torch.load(model_path, map_location=self.device)
            self.model.load_state_dict(checkpoint.get("model_state_dict", checkpoint))
            print(f"[✓] Model loaded from: {model_path}")
        else:
            print("[!] Using pretrained backbone (no finetuned weights loaded)")

        self.model.eval()

    def preprocess(self, image: Image.Image) -> torch.Tensor:
        """Convert PIL image to model-ready tensor"""
        if image.mode != "RGB":
            image = image.convert("RGB")
        tensor = self.transform(image).unsqueeze(0)
        return tensor.to(self.device)

    @torch.no_grad()
    def predict(self, image: Image.Image) -> dict:
        """
        Run full inference on a single image.

        Returns:
            dict with keys: label, confidence, probability, raw_logit
        """
        tensor = self.preprocess(image)
        logit = self.model(tensor)
        probability = torch.sigmoid(logit).item()
        confidence = probability if probability >= 0.5 else 1 - probability
        label = "FAKE" if probability >= 0.5 else "REAL"

        return {
            "label": label,
            "probability": probability,
            "confidence": round(confidence * 100, 2),
            "raw_logit": logit.item(),
            "is_fake": probability >= 0.5
        }

    @torch.no_grad()
    def predict_batch(self, images: list) -> list:
        """Predict on a list of PIL images"""
        results = []
        for img in images:
            results.append(self.predict(img))
        return results

    def predict_video_frames(self, frames: list, sample_rate: int = 5) -> dict:
        """
        Analyze sampled frames from a video.

        Args:
            frames: list of PIL Images (video frames)
            sample_rate: analyze every Nth frame

        Returns:
            dict with per-frame results + aggregate verdict
        """
        sampled = frames[::sample_rate]
        frame_results = self.predict_batch(sampled)

        fake_probs = [r["probability"] for r in frame_results]
        avg_prob = np.mean(fake_probs) if fake_probs else 0.0
        fake_count = sum(1 for r in frame_results if r["is_fake"])
        fake_ratio = fake_count / len(frame_results) if frame_results else 0

        # Weighted aggregate: 60% avg probability + 40% fake frame ratio
        aggregate_score = 0.6 * avg_prob + 0.4 * fake_ratio
        label = "FAKE" if aggregate_score >= 0.5 else "REAL"
        confidence = aggregate_score if aggregate_score >= 0.5 else 1 - aggregate_score

        return {
            "label": label,
            "confidence": round(confidence * 100, 2),
            "aggregate_score": aggregate_score,
            "avg_fake_probability": avg_prob,
            "fake_frame_ratio": fake_ratio,
            "total_frames_analyzed": len(frame_results),
            "frame_results": frame_results
        }


# ─────────────────────────────────────────────
#  Training Utilities
# ─────────────────────────────────────────────

class FocalLoss(nn.Module):
    """
    Focal Loss for handling class imbalance in deepfake datasets.
    """

    def __init__(self, alpha: float = 0.25, gamma: float = 2.0):
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.bce = nn.BCEWithLogitsLoss(reduction="none")

    def forward(self, logits, targets):
        if targets.ndim == 1:
            targets = targets.float().unsqueeze(1)
        else:
            targets = targets.float()
        bce_loss = self.bce(logits, targets)
        pt = torch.exp(-bce_loss)
        focal_loss = self.alpha * (1 - pt) ** self.gamma * bce_loss
        return focal_loss.mean()


def get_optimizer(model, lr: float = 1e-4, weight_decay: float = 1e-5):
    """Differential learning rates: lower for backbone, higher for head"""
    backbone_params = {"params": model.backbone.parameters(), "lr": lr * 0.1}
    head_params = {"params": list(model.classifier.parameters()) +
                              list(model.attention.parameters()), "lr": lr}
    return torch.optim.AdamW([backbone_params, head_params],
                              weight_decay=weight_decay)


def train_one_epoch(model, loader, optimizer, criterion, device, scaler=None):
    """Single training epoch with mixed precision support"""
    model.train()
    total_loss, correct, total = 0.0, 0, 0

    for images, labels in loader:
        images = images.to(device)
        labels = labels.float().to(device)

        optimizer.zero_grad()

        if scaler:  # AMP training
            with torch.cuda.amp.autocast():
                logits = model(images)
                loss = criterion(logits, labels)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            logits = model(images)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()

        preds = (torch.sigmoid(logits) >= 0.5).squeeze(1).long()
        correct += (preds == labels.long()).sum().item()
        total += len(labels)
        total_loss += loss.item()

    return {"loss": total_loss / len(loader), "accuracy": correct / total}


def evaluate(model, loader, criterion, device):
    """Evaluate model on validation/test set"""
    model.eval()
    total_loss, correct, total = 0.0, 0, 0
    all_probs, all_labels = [], []

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            labels = labels.float().to(device)
            logits = model(images)
            loss = criterion(logits, labels)
            probs = torch.sigmoid(logits).squeeze(1)
            preds = (probs >= 0.5).long()
            correct += (preds == labels.long()).sum().item()
            total += len(labels)
            total_loss += loss.item()
            all_probs.extend(probs.cpu().numpy().tolist())
            all_labels.extend(labels.cpu().numpy().tolist())

    return {
        "loss": total_loss / len(loader),
        "accuracy": correct / total,
        "probabilities": all_probs,
        "labels": all_labels
    }


if __name__ == "__main__":
    # Quick test
    print("Testing DeepfakeDetector model...")
    model = DeepfakeDetector(pretrained=False)
    dummy = torch.randn(2, 3, 224, 224)
    out = model(dummy)
    print(f"Output shape: {out.shape}")
    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    print("✓ Model test passed!")
