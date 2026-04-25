# Deployment Guide

## Local (CPU)
1. Install dependencies:
   - `pip install -r requirements.txt`
2. Run API:
   - `uvicorn backend.main:app --reload`
3. Run UI:
   - `streamlit run frontend/streamlit_app.py`

## Optional Cloud
- Use a small CPU VM (2 vCPU, 4 GB RAM)
- Dockerize the backend and expose `8000`
- Serve Streamlit on `8501` or deploy static front-end and call API

## Model Artifacts
- Train models with `python -m ml.train --data data/train --out artifacts`
- Copy `artifacts/` into deployment package
