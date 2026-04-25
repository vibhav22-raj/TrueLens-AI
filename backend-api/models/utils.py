"""
utils.py - Helper Utilities for Deepfake Detection System
Handles: face detection, video processing, metadata, metrics
"""

import cv2
import numpy as np
from PIL import Image, ExifTags
import torch
from torchvision import transforms
import os
import io
import base64
import hashlib
from typing import List, Tuple, Optional, Dict


# ─────────────────────────────────────────────
#  Face Detection & Extraction
# ─────────────────────────────────────────────

class FaceExtractor:
    """
    Detects and extracts faces from images for deepfake analysis.
    Falls back to full image if no face detected.
    """

    def __init__(self, padding: float = 0.3, min_face_size: int = 64):
        self.padding = padding
        self.min_face_size = min_face_size

        # Try to load OpenCV's DNN face detector (more accurate)
        self._load_detector()

    def _load_detector(self):
        """Load best available face detector"""
        # Try Haar cascade as fallback (always available)
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.cascade = cv2.CascadeClassifier(cascade_path)
        self.use_dnn = False

    def detect_faces(self, image: Image.Image) -> List[Tuple[int, int, int, int]]:
        """
        Returns list of (x, y, w, h) bounding boxes for detected faces.
        """
        img_np = np.array(image.convert("RGB"))
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        gray = cv2.equalizeHist(gray)

        faces = self.cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=4,
            minSize=(self.min_face_size, self.min_face_size),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        if len(faces) == 0:
            return []

        return [(int(x), int(y), int(w), int(h)) for x, y, w, h in faces]

    def extract_faces(self, image: Image.Image) -> List[Image.Image]:
        """
        Extract face crops from image with padding.
        Returns original image if no faces detected.
        """
        faces = self.detect_faces(image)
        img_np = np.array(image.convert("RGB"))
        h_img, w_img = img_np.shape[:2]

        if not faces:
            return [image]

        cropped_faces = []
        for x, y, w, h in faces:
            pad_x = int(w * self.padding)
            pad_y = int(h * self.padding)
            x1 = max(0, x - pad_x)
            y1 = max(0, y - pad_y)
            x2 = min(w_img, x + w + pad_x)
            y2 = min(h_img, y + h + pad_y)
            face_crop = Image.fromarray(img_np[y1:y2, x1:x2])
            cropped_faces.append(face_crop)

        return cropped_faces

    def draw_face_boxes(self, image: Image.Image,
                        labels: Optional[List[str]] = None) -> np.ndarray:
        """Draw face detection boxes on image"""
        faces = self.detect_faces(image)
        img_np = np.array(image.convert("RGB")).copy()

        for i, (x, y, w, h) in enumerate(faces):
            color = (255, 80, 80)
            cv2.rectangle(img_np, (x, y), (x + w, y + h), color, 2)
            if labels and i < len(labels):
                cv2.putText(img_np, labels[i], (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        return img_np


# ─────────────────────────────────────────────
#  Video Processing
# ─────────────────────────────────────────────

class VideoProcessor:
    """
    Handles video file loading and frame extraction for deepfake detection.
    """

    def __init__(self, max_frames: int = 60, sample_rate: int = 5):
        self.max_frames = max_frames
        self.sample_rate = sample_rate

    def extract_frames(self, video_path: str) -> Tuple[List[Image.Image], dict]:
        """
        Extract frames from a video file.

        Returns:
            frames: List of PIL Images
            metadata: dict with video info
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = total_frames / fps if fps > 0 else 0

        metadata = {
            "total_frames": total_frames,
            "fps": round(fps, 2),
            "width": width,
            "height": height,
            "duration_seconds": round(duration, 2),
            "codec": int(cap.get(cv2.CAP_PROP_FOURCC))
        }

        frames = []
        frame_idx = 0
        sampled = 0

        while cap.isOpened() and sampled < self.max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % self.sample_rate == 0:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(Image.fromarray(rgb_frame))
                sampled += 1
            frame_idx += 1

        cap.release()
        metadata["frames_extracted"] = len(frames)
        return frames, metadata

    def extract_frames_from_bytes(self, video_bytes: bytes) -> Tuple[List[Image.Image], dict]:
        """Extract frames from video bytes (Streamlit upload)"""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(video_bytes)
            tmp_path = tmp.name

        try:
            return self.extract_frames(tmp_path)
        finally:
            os.unlink(tmp_path)


# ─────────────────────────────────────────────
#  Image Metadata Analysis
# ─────────────────────────────────────────────

def extract_metadata(image: Image.Image) -> Dict:
    """
    Extract EXIF metadata and compute integrity indicators.
    """
    info = {
        "format": image.format or "Unknown",
        "mode": image.mode,
        "size": f"{image.width} × {image.height}",
        "megapixels": round((image.width * image.height) / 1_000_000, 2),
        "exif_found": False,
        "software": None,
        "camera_make": None,
        "camera_model": None,
        "date_taken": None,
        "gps": None,
        "edit_software_detected": False,
        "suspicious_flags": []
    }

    # Known AI / editing software signatures
    AI_SOFTWARE = ["stable diffusion", "midjourney", "dall-e", "firefly", "runway",
                   "deepfake", "faceswap", "fomm", "artbreeder", "generated"]
    EDIT_SOFTWARE = ["photoshop", "lightroom", "gimp", "affinity", "canva",
                     "snapseed", "pixlr", "facetune", "meitu"]

    try:
        exif_data = image._getexif()
        if exif_data:
            info["exif_found"] = True
            exif_decoded = {
                ExifTags.TAGS.get(tag, tag): val
                for tag, val in exif_data.items()
            }

            info["software"] = exif_decoded.get("Software", None)
            info["camera_make"] = exif_decoded.get("Make", None)
            info["camera_model"] = exif_decoded.get("Model", None)
            info["date_taken"] = exif_decoded.get("DateTimeOriginal", None)

            # GPS check
            if "GPSInfo" in exif_decoded:
                info["gps"] = "Present"

            # Software analysis
            sw = str(info["software"] or "").lower()
            if any(s in sw for s in AI_SOFTWARE):
                info["edit_software_detected"] = True
                info["suspicious_flags"].append(f"AI generation software detected: {info['software']}")
            elif any(s in sw for s in EDIT_SOFTWARE):
                info["edit_software_detected"] = True
                info["suspicious_flags"].append(f"Image editing software detected: {info['software']}")

    except Exception:
        pass  # JPEG without EXIF is normal

    # No EXIF but claims to be camera photo → suspicious
    if not info["exif_found"]:
        info["suspicious_flags"].append("No EXIF metadata (stripped or AI-generated)")

    # Unusual resolution ratios
    ratio = image.width / image.height if image.height > 0 else 1
    if ratio > 2.5 or ratio < 0.4:
        info["suspicious_flags"].append(f"Unusual aspect ratio: {ratio:.2f}")

    return info


def compute_frequency_artifacts(image: Image.Image) -> Dict:
    """
    Analyze frequency domain for GAN artifacts.
    GAN-generated images often show periodic patterns in FFT.
    """
    img_gray = np.array(image.convert("L")).astype(np.float32)
    fft = np.fft.fft2(img_gray)
    fft_shift = np.fft.fftshift(fft)
    magnitude = np.log(np.abs(fft_shift) + 1)

    # Normalize
    mag_norm = (magnitude - magnitude.min()) / (magnitude.max() - magnitude.min() + 1e-8)

    # Center crop ratio (high frequency content in center = artifacts)
    h, w = mag_norm.shape
    center = mag_norm[h//4:3*h//4, w//4:3*w//4]
    outer = np.concatenate([mag_norm[:h//4, :].flatten(),
                             mag_norm[3*h//4:, :].flatten()])

    center_energy = center.mean()
    outer_energy = outer.mean() if len(outer) > 0 else 0
    artifact_score = center_energy / (outer_energy + 1e-6)

    return {
        "frequency_artifact_score": round(float(artifact_score), 4),
        "center_energy": round(float(center_energy), 4),
        "high_freq_suspicious": artifact_score > 2.0
    }


# ─────────────────────────────────────────────
#  Ensemble Fusion
# ─────────────────────────────────────────────

def ensemble_predict(cnn_result: Dict, ae_result: Dict,
                     freq_result: Dict = None, threshold: float = 0.5) -> Dict:
    """
    Fuse predictions from CNN + Autoencoder + Frequency analysis.
    Returns weighted ensemble result.
    """
    # CNN probability (0=real, 1=fake)
    cnn_prob = cnn_result.get("probability", 0.5)

    # Autoencoder: convert anomaly confidence to probability
    ae_score = ae_result.get("anomaly_score", 0)
    ae_threshold = ae_result.get("threshold", 0.05)
    ae_prob = min(ae_score / (ae_threshold * 2 + 1e-8), 1.0)
    if not ae_result.get("is_anomaly", False):
        ae_prob = ae_prob * 0.5  # Dampen if not anomalous

    # Frequency
    freq_prob = 0.5  # Neutral default
    if freq_result:
        freq_score = freq_result.get("frequency_artifact_score", 1.0)
        freq_prob = min((freq_score - 1.0) / 3.0, 1.0) if freq_score > 1.0 else 0.0
        freq_prob = max(0.0, freq_prob)

    # Weighted fusion: CNN is most reliable
    if freq_result:
        weights = [0.60, 0.25, 0.15]
        ensemble_prob = weights[0] * cnn_prob + weights[1] * ae_prob + weights[2] * freq_prob
    else:
        weights = [0.70, 0.30]
        ensemble_prob = weights[0] * cnn_prob + weights[1] * ae_prob

    label = "FAKE" if ensemble_prob >= threshold else "REAL"
    conf = ensemble_prob if ensemble_prob >= threshold else 1 - ensemble_prob

    return {
        "label": label,
        "probability": ensemble_prob,
        "confidence": round(conf * 100, 2),
        "is_fake": ensemble_prob >= threshold,
        "component_scores": {
            "cnn": round(cnn_prob * 100, 1),
            "autoencoder": round(ae_prob * 100, 1),
            "frequency": round(freq_prob * 100, 1) if freq_result else "N/A"
        },
        "weights_used": weights
    }


# ─────────────────────────────────────────────
#  Evaluation Metrics
# ─────────────────────────────────────────────

def compute_metrics(y_true: list, y_prob: list, threshold: float = 0.5) -> Dict:
    """
    Compute comprehensive evaluation metrics.
    """
    from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                                  f1_score, roc_auc_score, confusion_matrix,
                                  roc_curve, precision_recall_curve)

    y_pred = [1 if p >= threshold else 0 for p in y_prob]

    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)

    fpr, tpr, roc_thresholds = roc_curve(y_true, y_prob)
    precision_curve, recall_curve, _ = precision_recall_curve(y_true, y_prob)

    return {
        "accuracy": round(accuracy_score(y_true, y_pred) * 100, 2),
        "precision": round(precision_score(y_true, y_pred, zero_division=0) * 100, 2),
        "recall": round(recall_score(y_true, y_pred, zero_division=0) * 100, 2),
        "f1_score": round(f1_score(y_true, y_pred, zero_division=0) * 100, 2),
        "auc_roc": round(roc_auc_score(y_true, y_prob) * 100, 2),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "roc_curve": {"fpr": fpr.tolist(), "tpr": tpr.tolist()},
        "pr_curve": {"precision": precision_curve.tolist(), "recall": recall_curve.tolist()}
    }


def pil_to_base64(image: Image.Image, format: str = "JPEG") -> str:
    """Convert PIL Image to base64 string"""
    buffered = io.BytesIO()
    image.save(buffered, format=format)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def compute_image_hash(image: Image.Image) -> str:
    """Compute perceptual hash for duplicate detection"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return hashlib.md5(buffered.getvalue()).hexdigest()


if __name__ == "__main__":
    print("Testing utilities...")
    extractor = FaceExtractor()
    dummy_img = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
    faces = extractor.detect_faces(dummy_img)
    print(f"Faces detected: {len(faces)}")

    meta = extract_metadata(dummy_img)
    print(f"Metadata: {meta}")

    freq = compute_frequency_artifacts(dummy_img)
    print(f"Frequency analysis: {freq}")
    print("✓ Utils test passed!")
