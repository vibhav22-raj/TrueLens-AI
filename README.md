# TrueLens AI: Image Authenticity and Deepfake Detection

This repository contains a complete, deployable, CPU-first system for deepfake and manipulation detection with explainable outputs. The system is designed to be competition-winning by combining hybrid modeling, temporal analysis, and practical UX for real-world use.

## Highlights
- Hybrid ensemble: CNN classifier + autoencoder anomaly detector
- Multi-type manipulation coverage: GAN, face swap, splicing, retouching
- Explainable AI: Grad-CAM + reconstruction error heatmaps
- Video temporal analysis: frame consistency + landmark instability
- CPU-first optimization: quantization and lightweight backbones
- End-to-end product: API + UI dashboard + evaluation + deployment guide

## Repo Structure
- `backend/`: FastAPI backend service
- `frontend/`: Streamlit dashboard UI
- `ml/`: Models, training, explainability, evaluation
- `scripts/`: Benchmarking and utilities
- `docs/`: Architecture, datasets, deployment, PPT outline, USP

## Quick Start (CPU)
1. Install dependencies:
   - `pip install -r requirements.txt`
2. Run API:
   - `uvicorn backend.main:app --reload`
3. Run UI:
   - `streamlit run frontend/streamlit_app.py`

## New Premium SaaS Stack (Next.js + FastAPI)
### Frontend (Next.js)
1. `cd frontend-next`
2. `npm install`
3. `npm run dev`

### Backend (FastAPI + PostgreSQL)
1. `cd backend-api`
2. Create `.env` (see `backend-api/.env`)
3. `pip install -r requirements.txt`
4. `uvicorn app.main:app --reload`

### Default URLs
- Frontend: `http://localhost:3000`
- API: `http://localhost:8000`

## Notes
- Training is optional for demo usage; you can run inference with randomly initialized weights, but results are not meaningful until trained.
- For full accuracy, download recommended datasets from `docs/datasets.md` and train with `python -m ml.train`.

See `docs/architecture.md` for system design.
