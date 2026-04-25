# Architecture

## System Overview
TrueLens AI is a CPU-first, hybrid deepfake detection platform with explainable outputs. It combines a CNN classifier with an autoencoder anomaly detector, then adds temporal analysis for video and visual explainability for all outputs.

## Text Diagram

[User] -> [UI Dashboard (Streamlit)] -> [FastAPI Backend]
                                |-> [Image/Video Preprocess]
                                |-> [Hybrid Model: CNN + Autoencoder]
                                |-> [Explainability: Grad-CAM + Recon Error]
                                |-> [Video Temporal Analysis]
                                |-> [Risk Score + Reporting]

## Pipeline Stages
1. Ingestion: image or short video upload
2. Preprocessing: resize, normalize, frame sampling
3. Model Inference
   - CNN classifier predicts manipulation probability
   - Autoencoder computes reconstruction error (anomaly score)
4. Ensemble Score
   - Weighted merge of CNN probability and anomaly score
5. Explainability
   - Grad-CAM heatmap for model attention
   - Reconstruction error heatmap for pixel-level anomalies
6. Video Temporal Analysis
   - Frame inconsistency score
   - Landmark instability score
7. Output
   - Final score + evidence heatmaps
   - Optional risk score for fake news usage

## Key Differentiators
- Hybrid ensemble improves robustness across manipulation types
- Explainability overlays for both discriminative and reconstruction signals
- Temporal and landmark-based instability for video reliability
- CPU-optimized inference and quantization-ready architecture
