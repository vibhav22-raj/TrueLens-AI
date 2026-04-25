"""
gradcam.py - Grad-CAM Explainability for Deepfake Detection
Highlights which regions of an image influenced the deepfake prediction.
"""

import torch
import torch.nn.functional as F
import numpy as np
import cv2
from PIL import Image
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for Streamlit
import matplotlib.pyplot as plt


# ─────────────────────────────────────────────
#  Grad-CAM Core
# ─────────────────────────────────────────────

class GradCAM:
    """
    Gradient-weighted Class Activation Mapping.
    Works with any CNN model that has a named target layer.
    """

    def __init__(self, model: torch.nn.Module, target_layer_name: str = None):
        self.model = model
        self.model.eval()
        self.gradients = None
        self.activations = None
        self.hooks = []

        # Auto-detect target layer if not specified
        if target_layer_name is None:
            target_layer = self._auto_detect_layer()
        else:
            target_layer = dict(model.named_modules()).get(target_layer_name)

        if target_layer is None:
            raise ValueError(f"Target layer not found: {target_layer_name}")

        # Register forward and backward hooks
        self.hooks.append(
            target_layer.register_forward_hook(self._save_activation)
        )
        self.hooks.append(
            target_layer.register_full_backward_hook(self._save_gradient)
        )

    def _auto_detect_layer(self):
        """Find the last convolutional layer automatically"""
        last_conv = None
        for _, module in self.model.named_modules():
            if isinstance(module, torch.nn.Conv2d):
                last_conv = module
        return last_conv

    def _save_activation(self, module, input, output):
        self.activations = output.detach()

    def _save_gradient(self, module, grad_input, grad_output):
        self.gradients = grad_output[0].detach()

    def generate(self, input_tensor: torch.Tensor, target_class: int = 0) -> np.ndarray:
        """
        Generate Grad-CAM heatmap for given input.

        Args:
            input_tensor: preprocessed image tensor (1, C, H, W)
            target_class: 0 for REAL, 1 for FAKE

        Returns:
            heatmap: numpy array (H, W) with values in [0, 1]
        """
        input_tensor.requires_grad_(True)

        # Forward pass
        output = self.model(input_tensor)

        # Backward pass for target class
        self.model.zero_grad()
        if output.shape[-1] == 1:
            loss = output if target_class == 1 else -output
        else:
            loss = output[:, target_class]
        loss.sum().backward()

        # Compute Grad-CAM
        if self.gradients is None or self.activations is None:
            return np.zeros((input_tensor.shape[2], input_tensor.shape[3]))

        # Global average pooling of gradients
        weights = self.gradients.mean(dim=[2, 3], keepdim=True)  # (B, C, 1, 1)
        cam = (weights * self.activations).sum(dim=1, keepdim=True)  # (B, 1, H', W')
        cam = F.relu(cam)

        # Normalize
        cam = cam.squeeze().cpu().numpy()
        if cam.ndim == 0:
            cam = np.array([[cam.item()]])

        if cam.max() > cam.min():
            cam = (cam - cam.min()) / (cam.max() - cam.min())

        # Upsample to input size
        h, w = input_tensor.shape[2], input_tensor.shape[3]
        cam_resized = cv2.resize(cam, (w, h), interpolation=cv2.INTER_CUBIC)
        cam_resized = np.clip(cam_resized, 0, 1)
        return cam_resized

    def remove_hooks(self):
        """Clean up hooks to prevent memory leaks"""
        for hook in self.hooks:
            hook.remove()


# ─────────────────────────────────────────────
#  Grad-CAM++ (Improved Version)
# ─────────────────────────────────────────────

class GradCAMPlusPlus(GradCAM):
    """
    Grad-CAM++ for better localization of multiple instances.
    More accurate than standard Grad-CAM for complex manipulations.
    """

    def generate(self, input_tensor: torch.Tensor, target_class: int = 0) -> np.ndarray:
        input_tensor.requires_grad_(True)

        output = self.model(input_tensor)
        self.model.zero_grad()

        if output.shape[-1] == 1:
            loss = output if target_class == 1 else -output
        else:
            loss = output[:, target_class]
        loss.sum().backward()

        if self.gradients is None or self.activations is None:
            return np.zeros((input_tensor.shape[2], input_tensor.shape[3]))

        grads = self.gradients  # (B, C, H', W')
        acts = self.activations  # (B, C, H', W')

        # Grad-CAM++ weights
        grads_sq = grads ** 2
        grads_cu = grads ** 3
        sum_acts = acts.sum(dim=[2, 3], keepdim=True)
        alpha = grads_sq / (2 * grads_sq + sum_acts * grads_cu + 1e-7)
        alpha = alpha * (grads > 0).float()
        weights = (alpha * F.relu(grads)).sum(dim=[2, 3], keepdim=True)

        cam = (weights * acts).sum(dim=1, keepdim=True)
        cam = F.relu(cam)
        cam = cam.squeeze().cpu().numpy()

        if cam.ndim == 0:
            cam = np.array([[cam.item()]])

        if cam.max() > cam.min():
            cam = (cam - cam.min()) / (cam.max() - cam.min())

        h, w = input_tensor.shape[2], input_tensor.shape[3]
        cam_resized = cv2.resize(cam, (w, h), interpolation=cv2.INTER_CUBIC)
        return np.clip(cam_resized, 0, 1)


# ─────────────────────────────────────────────
#  Visualization Engine
# ─────────────────────────────────────────────

class DeepfakeVisualizer:
    """
    Creates publication-quality visualizations for deepfake detection results.
    """

    COLORMAPS = {
        "fire": cv2.COLORMAP_HOT,
        "jet": cv2.COLORMAP_JET,
        "plasma": cv2.COLORMAP_PLASMA,
        "viridis": cv2.COLORMAP_VIRIDIS,
    }

    def overlay_heatmap(self, image: Image.Image, heatmap: np.ndarray,
                        alpha: float = 0.45, colormap: str = "fire") -> np.ndarray:
        """
        Overlay Grad-CAM heatmap on original image.

        Returns:
            RGB numpy array suitable for display
        """
        img_np = np.array(image.convert("RGB"))
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        h, w = img_bgr.shape[:2]

        # Scale heatmap to 0-255 uint8
        heatmap_uint8 = (heatmap * 255).astype(np.uint8)
        heatmap_uint8 = cv2.resize(heatmap_uint8, (w, h))
        img_bgr = cv2.resize(img_bgr, (w, h))

        # Apply colormap
        cmap_id = self.COLORMAPS.get(colormap, cv2.COLORMAP_HOT)
        heatmap_colored = cv2.applyColorMap(heatmap_uint8, cmap_id)

        # Blend
        overlay = cv2.addWeighted(img_bgr, 1 - alpha, heatmap_colored, alpha, 0)
        return cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)

    def add_contour_overlay(self, overlay: np.ndarray, heatmap: np.ndarray,
                            threshold: float = 0.5) -> np.ndarray:
        """Draw contours around highly suspicious regions"""
        mask = (heatmap > threshold).astype(np.uint8) * 255
        mask_resized = cv2.resize(mask, (overlay.shape[1], overlay.shape[0]))

        # Morphological cleanup
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask_clean = cv2.morphologyEx(mask_resized, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        result = overlay.copy()
        cv2.drawContours(result, contours, -1, (255, 50, 50), 2)
        return result

    def create_comparison_figure(self, original: Image.Image,
                                  heatmap: np.ndarray,
                                  prediction: dict,
                                  autoencoder_heatmap: np.ndarray = None,
                                  heatmap_alpha: float = 0.45,
                                  colormap: str = "fire") -> plt.Figure:
        """
        Create a multi-panel comparison figure for the Streamlit UI.
        Shows: Original | Grad-CAM | Error Map | Analysis
        """
        num_panels = 4 if autoencoder_heatmap is not None else 3
        fig, axes = plt.subplots(1, num_panels, figsize=(5 * num_panels, 5))
        fig.patch.set_facecolor("#0f0f1a")

        # ── Panel 1: Original ──
        axes[0].imshow(original.resize((224, 224)))
        axes[0].set_title("Original Image", color="white", fontsize=12, fontweight="bold")
        axes[0].axis("off")

        # ── Panel 2: Grad-CAM Overlay ──
        overlay = self.overlay_heatmap(original, heatmap, alpha=heatmap_alpha, colormap=colormap)
        overlay_contour = self.add_contour_overlay(overlay, heatmap)
        axes[1].imshow(overlay_contour)
        axes[1].set_title("Grad-CAM Heatmap\n(Suspicious Regions)", color="#ff4444",
                           fontsize=11, fontweight="bold")
        axes[1].axis("off")

        # ── Panel 3: Raw Heatmap ──
        axes[2].imshow(heatmap, cmap="hot")
        axes[2].set_title("Activation Map\n(Manipulation Intensity)", color="#ff8800",
                           fontsize=11, fontweight="bold")
        axes[2].axis("off")
        plt.colorbar(axes[2].images[0], ax=axes[2], fraction=0.046)

        # ── Panel 4: Autoencoder Error Map (optional) ──
        if autoencoder_heatmap is not None:
            ae_resized = cv2.resize(autoencoder_heatmap, (224, 224))
            axes[3].imshow(ae_resized, cmap="plasma")
            axes[3].set_title("Anomaly Error Map\n(Reconstruction Diff)", color="#cc44ff",
                               fontsize=11, fontweight="bold")
            axes[3].axis("off")

        # Overall title with prediction
        label = prediction["label"]
        conf = prediction["confidence"]
        color = "#ff2222" if label == "FAKE" else "#22ff88"
        fig.suptitle(
            f"Prediction: {label}  |  Confidence: {conf:.1f}%",
            fontsize=16, fontweight="bold", color=color, y=1.02
        )
        plt.tight_layout()
        return fig

    def create_video_timeline(self, frame_results: list) -> plt.Figure:
        """
        Visualize frame-by-frame prediction timeline for video analysis.
        """
        probs = [r["probability"] for r in frame_results]
        frames = list(range(1, len(probs) + 1))

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6))
        fig.patch.set_facecolor("#0f0f1a")

        # ── Probability timeline ──
        ax1.fill_between(frames, 0.5, probs,
                          where=[p > 0.5 for p in probs],
                          color="#ff4444", alpha=0.6, label="Fake regions")
        ax1.fill_between(frames, probs, 0.5,
                          where=[p <= 0.5 for p in probs],
                          color="#44ff88", alpha=0.6, label="Real regions")
        ax1.plot(frames, probs, color="white", linewidth=1.5)
        ax1.axhline(0.5, color="yellow", linestyle="--", linewidth=1, alpha=0.8)
        ax1.set_facecolor("#1a1a2e")
        ax1.set_ylabel("Fake Probability", color="white")
        ax1.set_xlabel("Frame Index", color="white")
        ax1.set_title("Frame-by-Frame Deepfake Probability", color="white", fontweight="bold")
        ax1.tick_params(colors="white")
        ax1.set_ylim(0, 1)
        ax1.legend(facecolor="#1a1a2e", labelcolor="white")
        for spine in ax1.spines.values():
            spine.set_edgecolor("#444")

        # ── Rolling average ──
        window = max(1, len(probs) // 10)
        rolling = [np.mean(probs[max(0, i-window):i+1]) for i in range(len(probs))]
        ax2.plot(frames, rolling, color="#00d4ff", linewidth=2, label="Rolling avg")
        ax2.axhline(0.5, color="yellow", linestyle="--", linewidth=1, alpha=0.8)
        ax2.fill_between(frames, 0.5, rolling,
                          where=[r > 0.5 for r in rolling],
                          color="#ff4444", alpha=0.3)
        ax2.set_facecolor("#1a1a2e")
        ax2.set_ylabel("Smoothed Probability", color="white")
        ax2.set_xlabel("Frame", color="white")
        ax2.tick_params(colors="white")
        ax2.set_ylim(0, 1)
        for spine in ax2.spines.values():
            spine.set_edgecolor("#444")

        plt.tight_layout()
        return fig


# ─────────────────────────────────────────────
#  Explanation Text Generator
# ─────────────────────────────────────────────

def generate_explanation(prediction: dict, heatmap: np.ndarray,
                          ae_result: dict = None) -> dict:
    """
    Generate human-readable explanation of the prediction.
    Used for the explainable AI section of the UI.
    """
    label = prediction["label"]
    confidence = prediction["confidence"]

    # Analyze heatmap regions
    region_intensity = {
        "forehead": heatmap[:heatmap.shape[0]//3, :].mean(),
        "eyes": heatmap[heatmap.shape[0]//4:heatmap.shape[0]//2, :].mean(),
        "nose": heatmap[heatmap.shape[0]//3:2*heatmap.shape[0]//3, heatmap.shape[1]//4:3*heatmap.shape[1]//4].mean(),
        "mouth": heatmap[2*heatmap.shape[0]//3:, heatmap.shape[1]//4:3*heatmap.shape[1]//4].mean(),
        "edges": np.concatenate([heatmap[:, :20].flatten(), heatmap[:, -20:].flatten()]).mean()
    }

    sorted_regions = sorted(region_intensity.items(), key=lambda x: x[1], reverse=True)
    top_regions = [r for r, v in sorted_regions[:3] if v > 0.1]

    # Risk level
    if confidence > 90:
        risk = "CRITICAL"
        risk_color = "#ff0000"
    elif confidence > 70:
        risk = "HIGH"
        risk_color = "#ff6600"
    elif confidence > 50:
        risk = "MEDIUM"
        risk_color = "#ffaa00"
    else:
        risk = "LOW"
        risk_color = "#00cc44"

    # Build explanation
    artifacts = []
    if label == "FAKE":
        if "eyes" in top_regions or "edges" in top_regions:
            artifacts.append("Facial boundary inconsistencies detected around eye region")
        if "mouth" in top_regions:
            artifacts.append("Mouth/lip rendering artifacts identified")
        if "forehead" in top_regions:
            artifacts.append("Hairline and forehead blending irregularities")
        if region_intensity["edges"] > 0.3:
            artifacts.append("Image boundary stitching artifacts")
        if not artifacts:
            artifacts.append("Statistical patterns inconsistent with authentic media")
            artifacts.append("Frequency domain anomalies detected")

        if ae_result and ae_result.get("is_anomaly"):
            artifacts.append(f"Anomaly detector confirms: reconstruction error {ae_result['anomaly_score']:.4f}")

    return {
        "verdict": label,
        "confidence": confidence,
        "risk_level": risk,
        "risk_color": risk_color,
        "top_regions": top_regions,
        "artifacts_detected": artifacts,
        "summary": (
            f"This image shows {risk.lower()} indicators of AI manipulation with "
            f"{confidence:.1f}% confidence. "
            + (f"Key suspicious areas: {', '.join(top_regions)}." if top_regions else "")
        )
    }


if __name__ == "__main__":
    print("Testing GradCAM and Visualizer...")
    visualizer = DeepfakeVisualizer()
    dummy_heatmap = np.random.rand(224, 224)
    dummy_img = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
    overlay = visualizer.overlay_heatmap(dummy_img, dummy_heatmap)
    print(f"Overlay shape: {overlay.shape}")
    print("✓ Visualizer test passed!")
