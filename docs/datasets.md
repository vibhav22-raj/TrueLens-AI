# Datasets (Lightweight and Offline-Friendly)

## Recommended
- FaceForensics++ (FF++): Multiple manipulation types, easy to subset
- Celeb-DF (v2): Realistic face swaps and blends
- DFDC Preview or sample subset: Video-based manipulations
- WildDeepfake: In-the-wild data for generalization
- CASIA2 / Columbia: Classic splicing and retouching benchmarks
- IMD2020: Image manipulation detection for splicing

## Lightweight Strategy
- Download low-quality or compressed subsets for CPU training
- Use class-balanced subsets with 2,000 to 5,000 images per class
- For videos, sample 10 to 30 frames per clip

## Offline Packaging
- Pre-download and store in `data/` with structure:
  - `data/train/real/`
  - `data/train/fake/`
  - `data/val/real/`
  - `data/val/fake/`

## Notes
- Build a small, diverse validation set to avoid bias
- Mix multiple sources to improve robustness against overfitting
