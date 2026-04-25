# Dataset Bias Analysis

## Purpose
Measure performance gaps across data sources, demographics, or acquisition conditions.

## Inputs
- `samples` metadata list with fields such as `source`, `lighting`, `camera`, `region`
- `y_true` labels and `y_prob` prediction scores

## Output
- Per-group metrics: accuracy, precision, recall, F1, ROC AUC

## Usage
- Use `ml/bias.py` to compute and save reports
- Include bias report in the final evaluation folder
