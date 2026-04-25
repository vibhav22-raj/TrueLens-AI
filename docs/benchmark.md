# Benchmark Comparison

## Baselines
- CNN-only (ResNet18 or EfficientNet-B0)
- Autoencoder-only anomaly score

## Proposed Model
- Hybrid ensemble: 0.7 * CNN probability + 0.3 * AE anomaly score

## Evaluation
- Use `scripts/benchmark.py` to compare baselines vs ensemble
- Use `scripts/evaluate.py` to compute metrics and ROC curve

## Expected Behavior
- Ensemble improves robustness on mixed manipulation types
- Autoencoder catches novel or out-of-distribution fakes
- CNN stabilizes performance on known manipulations
