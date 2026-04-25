import cv2
import numpy as np
import torch

try:
    import mediapipe as mp
    _HAS_MP = True
except Exception:
    _HAS_MP = False


def extract_frames(video_path, max_frames=32, stride=2):
    cap = cv2.VideoCapture(video_path)
    frames = []
    idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if idx % stride == 0:
            frames.append(frame)
            if len(frames) >= max_frames:
                break
        idx += 1
    cap.release()
    return frames


def frame_inconsistency_score(frames):
    if len(frames) < 2:
        return 0.0
    diffs = []
    prev = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
    for f in frames[1:]:
        cur = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        diff = np.mean(np.abs(cur.astype(np.float32) - prev.astype(np.float32)))
        diffs.append(diff)
        prev = cur
    return float(np.mean(diffs) / 255.0)


def landmark_instability_score(frames):
    if not _HAS_MP:
        return None
    mp_face = mp.solutions.face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1)
    pts = []
    for f in frames:
        rgb = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
        res = mp_face.process(rgb)
        if not res.multi_face_landmarks:
            continue
        lm = res.multi_face_landmarks[0].landmark
        coords = np.array([(p.x, p.y) for p in lm], dtype=np.float32)
        pts.append(coords)
    if len(pts) < 2:
        return None
    diffs = []
    for i in range(1, len(pts)):
        diffs.append(np.mean(np.linalg.norm(pts[i] - pts[i - 1], axis=1)))
    return float(np.mean(diffs))


def feature_consistency_score(feature_list):
    if len(feature_list) < 2:
        return 0.0
    diffs = []
    for i in range(1, len(feature_list)):
        diffs.append(torch.mean((feature_list[i] - feature_list[i - 1]) ** 2).item())
    return float(np.mean(diffs))
