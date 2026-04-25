from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from models.autoencoder import AnomalyDetector
from models.cnn_model import DeepfakeInference
from models.gradcam import DeepfakeVisualizer, GradCAMPlusPlus
from models.utils import FaceExtractor, VideoProcessor, compute_frequency_artifacts, ensemble_predict
from app.core.config import settings


class ModelBundle:
    def __init__(self):
        repo_root = Path(__file__).resolve().parents[3]
        self.static_dir = Path(__file__).resolve().parents[2] / "static" / "heatmaps"
        self.static_dir.mkdir(parents=True, exist_ok=True)

        cnn_weights = repo_root / "model" / "deepfake_model.pth"
        ae_weights = repo_root / "model" / "autoencoder_model.pth"
        ae_fallback = repo_root / "model" / "autoencoder.pth"

        self.cnn_has_weights = cnn_weights.exists()
        self.ae_has_weights = ae_weights.exists() or ae_fallback.exists()

        self.face_extractor = FaceExtractor()
        self.video_processor = VideoProcessor(max_frames=48, sample_rate=4)
        self.visualizer = DeepfakeVisualizer()

        self.cnn = DeepfakeInference(model_path=str(cnn_weights) if self.cnn_has_weights else None)
        ae_path = None
        if ae_weights.exists():
            ae_path = ae_weights
        elif ae_fallback.exists():
            ae_path = ae_fallback
        self.autoencoder = AnomalyDetector(model_path=str(ae_path) if ae_path else None)


_model: ModelBundle | None = None
_metrics_cache: dict[str, Any] | None = None


def get_model() -> ModelBundle:
    global _model
    if _model is None:
        _model = ModelBundle()
    return _model


def _load_metrics() -> dict[str, Any] | None:
    global _metrics_cache
    if _metrics_cache is not None:
        return _metrics_cache
    repo_root = Path(__file__).resolve().parents[3]
    metrics_path = repo_root / "model" / "metrics.json"
    if not metrics_path.exists():
        _metrics_cache = None
        return None
    try:
        _metrics_cache = json.loads(metrics_path.read_text(encoding="utf-8"))
        return _metrics_cache
    except Exception:
        _metrics_cache = None
        return None


def _log_metrics_if_available() -> None:
    metrics = _load_metrics()
    if not metrics:
        return
    accuracy = metrics.get("accuracy")
    f1_score = metrics.get("f1_score")
    auc = metrics.get("auc_roc")
    updated_at = metrics.get("updated_at")
    threshold = metrics.get("threshold")
    print(
        f"[Model Metrics] accuracy={accuracy}% f1={f1_score}% auc={auc}% "
        f"threshold={threshold} updated_at={updated_at}"
    )


def _get_threshold(default: float = 0.5) -> float:
    metrics = _load_metrics()
    if not metrics:
        return default
    try:
        value = float(metrics.get("threshold", default))
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, value))


def _save_overlay(overlay_rgb: np.ndarray, upload_id: int) -> str:
    image = Image.fromarray(overlay_rgb.astype(np.uint8))
    out_path = get_model().static_dir / f"{upload_id}.png"
    image.save(out_path)
    return f"/static/heatmaps/{upload_id}.png"


def _image_prediction(bundle: ModelBundle, file_bytes: bytes, upload_id: int) -> dict[str, Any]:
    image = Image.open(BytesIO(file_bytes)).convert("RGB")
    faces = bundle.face_extractor.extract_faces(image)
    target = faces[0] if faces else image

    cnn_result = bundle.cnn.predict(target)
    threshold = _get_threshold()
    ae_result = None
    freq_result = None

    # Avoid bias from an untrained/missing autoencoder model.
    if bundle.ae_has_weights:
        ae_result = bundle.autoencoder.predict(target)
        freq_result = compute_frequency_artifacts(target)
        fused = ensemble_predict(cnn_result, ae_result, freq_result, threshold=threshold)
    else:
        cnn_prob = float(cnn_result.get("probability", 0.5))
        is_fake = cnn_prob >= threshold
        fused = {
            "label": "FAKE" if is_fake else "REAL",
            "probability": cnn_prob,
            "confidence": round((cnn_prob if is_fake else 1 - cnn_prob) * 100, 2),
            "is_fake": is_fake,
            "component_scores": {
                "cnn": round(cnn_prob * 100, 1),
            },
        }

    label = str(fused.get("label", "UNKNOWN")).upper()
    probability = float(fused.get("probability", 0.5))
    confidence = probability if label == "FAKE" else 1 - probability

    notes: list[str] = []
    if settings.show_model_warnings:
        if not bundle.cnn_has_weights:
            notes.append("CNN weights not found; using base pretrained model.")
        if not bundle.ae_has_weights:
            notes.append("Autoencoder weights not found; using CNN-only prediction.")

    heatmap_url: str | None = None
    gradcam = None
    try:
        gradcam = GradCAMPlusPlus(bundle.cnn.model)
        tensor = bundle.cnn.preprocess(target)
        heatmap = gradcam.generate(tensor, target_class=1 if label == "FAKE" else 0)
        overlay = bundle.visualizer.overlay_heatmap(target, heatmap, alpha=0.45, colormap="fire")
        heatmap_url = _save_overlay(overlay, upload_id)
    except Exception:
        notes.append("Heatmap generation skipped for this file.")
    finally:
        if gradcam is not None:
            gradcam.remove_hooks()

    return {
        "result": label,
        "verdict": label,
        "confidence": round(float(confidence), 4),
        "raw_score": round(float(probability), 4),
        "heatmap_url": heatmap_url,
        "note": " ".join(notes) if notes else None
    }


def _video_prediction(bundle: ModelBundle, file_bytes: bytes) -> dict[str, Any]:
    frames, metadata = bundle.video_processor.extract_frames_from_bytes(file_bytes)
    if not frames:
        return {
            "result": "UNKNOWN",
            "verdict": "UNKNOWN",
            "confidence": 0.5,
            "raw_score": 0.5,
            "heatmap_url": None,
            "note": "No readable frames found in this video."
        }

    face_frames = []
    for frame in frames:
        faces = bundle.face_extractor.extract_faces(frame)
        face_frames.append(faces[0] if faces else frame)

    video_result = bundle.cnn.predict_video_frames(face_frames, sample_rate=1)
    label = str(video_result.get("label", "UNKNOWN")).upper()
    aggregate_score = float(video_result.get("aggregate_score", 0.5))
    confidence_percent = float(video_result.get("confidence", 50.0))

    note = (
        f"Analyzed {video_result.get('total_frames_analyzed', len(face_frames))} frames "
        f"at ~{metadata.get('fps', 'n/a')} FPS."
    )

    if settings.show_model_warnings and not bundle.cnn_has_weights:
        note += " CNN weights not found; using base pretrained model."

    return {
        "result": label,
        "verdict": label,
        "confidence": round(confidence_percent / 100, 4),
        "raw_score": round(aggregate_score, 4),
        "heatmap_url": None,
        "note": note
    }


def run_prediction(
    file_bytes: bytes,
    filename: str,
    upload_id: int,
    content_type: str | None = None
) -> dict[str, Any]:
    _log_metrics_if_available()
    bundle = get_model()
    mime = (content_type or "").lower()
    file_lower = filename.lower()
    is_video = mime.startswith("video/") or file_lower.endswith((".mp4", ".mov", ".avi", ".mkv", ".webm"))

    try:
        if is_video:
            return _video_prediction(bundle, file_bytes)
        return _image_prediction(bundle, file_bytes, upload_id)
    except Exception as exc:
        return {
            "result": "UNKNOWN",
            "verdict": "UNKNOWN",
            "confidence": 0.5,
            "raw_score": 0.5,
            "heatmap_url": None,
            "note": f"Prediction failed: {exc}"
        }
