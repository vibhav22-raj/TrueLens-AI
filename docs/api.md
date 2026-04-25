# API Reference

## POST /analyze/image
- Body: multipart file upload
- Response:
  - `score`: ensemble manipulation score
  - `cnn_prob`: CNN probability
  - `ae_score`: autoencoder anomaly score
  - `gradcam_b64`: base64 Grad-CAM overlay
  - `reconmap_b64`: base64 reconstruction overlay

## POST /analyze/video
- Body: multipart file upload
- Response:
  - `score`: average frame score
  - `frame_scores`: list of per-frame scores
  - `temporal_inconsistency`: frame difference metric
  - `landmark_instability`: face landmark jitter (if available)
  - `feature_inconsistency`: feature drift score
  - `gradcam_b64`: representative Grad-CAM frame
