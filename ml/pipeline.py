import os
import torch
import numpy as np
import cv2

from ml.models import CNNDetector, ConvAutoencoder, EnsembleDetector
from ml.explain import GradCAM, overlay_cam, reconstruction_error_map
from ml.utils import bgr_to_tensor, tensor_to_bgr
from ml.video import extract_frames, frame_inconsistency_score, landmark_instability_score, feature_consistency_score


def load_models(artifacts_dir="artifacts", backbone="resnet18", device=None):
    device = device or torch.device("cpu")
    cnn = CNNDetector(backbone=backbone)
    ae = ConvAutoencoder()
    cnn_path = os.path.join(artifacts_dir, "cnn.pt")
    ae_path = os.path.join(artifacts_dir, "ae.pt")
    if os.path.exists(cnn_path):
        cnn.load_state_dict(torch.load(cnn_path, map_location=device))
    if os.path.exists(ae_path):
        ae.load_state_dict(torch.load(ae_path, map_location=device))
    cnn.to(device).eval()
    ae.to(device).eval()
    ensemble = EnsembleDetector(cnn, ae)
    return ensemble


def analyze_image(image_bgr, model, device=None):
    device = device or torch.device("cpu")
    x = bgr_to_tensor(image_bgr).to(device)
    score, prob, recon_score = model.score(x)

    # Grad-CAM
    gradcam = GradCAM(model.cnn, target_layer_name="feature_extractor.layer4")
    cam = gradcam.generate(x)
    grad_overlay = overlay_cam(image_bgr, cam, alpha=0.5)

    # Reconstruction heatmap
    with torch.no_grad():
        recon, _ = model.ae(x)
    err_map = reconstruction_error_map(x, recon)
    err_overlay = overlay_cam(image_bgr, err_map, alpha=0.5)

    return {
        "score": float(score.item()),
        "cnn_prob": float(prob.item()),
        "ae_score": float(recon_score.item()),
        "gradcam": grad_overlay,
        "reconmap": err_overlay,
    }


def analyze_video(video_path, model, device=None, max_frames=24):
    device = device or torch.device("cpu")
    frames = extract_frames(video_path, max_frames=max_frames)
    if not frames:
        raise ValueError("No frames extracted from video")

    frame_scores = []
    feature_list = []
    example_overlay = None
    for i, frame in enumerate(frames):
        x = bgr_to_tensor(frame).to(device)
        with torch.no_grad():
            score, prob, recon_score = model.score(x)
            _, feats = model.cnn(x)
        frame_scores.append(float(score.item()))
        feature_list.append(feats.detach().cpu())
        if i == 0:
            # one representative Grad-CAM
            gradcam = GradCAM(model.cnn, target_layer_name="feature_extractor.layer4")
            cam = gradcam.generate(x)
            example_overlay = overlay_cam(frame, cam, alpha=0.5)

    temporal_score = frame_inconsistency_score(frames)
    landmark_score = landmark_instability_score(frames)
    feat_score = feature_consistency_score(feature_list)

    return {
        "score": float(np.mean(frame_scores)),
        "frame_scores": frame_scores,
        "temporal_inconsistency": temporal_score,
        "landmark_instability": landmark_score,
        "feature_inconsistency": feat_score,
        "gradcam": example_overlay,
    }
