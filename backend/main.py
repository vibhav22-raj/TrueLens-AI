import io
import base64
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import cv2
import torch

from ml.pipeline import load_models, analyze_image, analyze_video

app = FastAPI(title="TrueLens AI API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEVICE = torch.device("cpu")
MODEL = load_models(device=DEVICE)


def _encode_image_b64(img_bgr):
    _, buf = cv2.imencode(".jpg", img_bgr)
    return base64.b64encode(buf.tobytes()).decode("utf-8")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze/image")
def analyze_image_endpoint(file: UploadFile = File(...)):
    data = file.file.read()
    np_arr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if img is None:
        return {"error": "Invalid image"}

    result = analyze_image(img, MODEL, device=DEVICE)
    return {
        "score": result["score"],
        "cnn_prob": result["cnn_prob"],
        "ae_score": result["ae_score"],
        "gradcam_b64": _encode_image_b64(result["gradcam"]),
        "reconmap_b64": _encode_image_b64(result["reconmap"]),
    }


@app.post("/analyze/video")
def analyze_video_endpoint(file: UploadFile = File(...)):
    data = file.file.read()
    tmp_path = "_tmp_video.mp4"
    with open(tmp_path, "wb") as f:
        f.write(data)

    result = analyze_video(tmp_path, MODEL, device=DEVICE)
    gradcam_b64 = _encode_image_b64(result["gradcam"]) if result["gradcam"] is not None else None

    return {
        "score": result["score"],
        "frame_scores": result["frame_scores"],
        "temporal_inconsistency": result["temporal_inconsistency"],
        "landmark_instability": result["landmark_instability"],
        "feature_inconsistency": result["feature_inconsistency"],
        "gradcam_b64": gradcam_b64,
    }
