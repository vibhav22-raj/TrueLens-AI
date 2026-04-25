import json
from collections import defaultdict

from ml.metrics import compute_metrics


def bias_report(samples, y_true, y_prob, group_key="source"):
    # samples: list of dicts with metadata including group_key
    groups = defaultdict(list)
    for i, s in enumerate(samples):
        groups[s.get(group_key, "unknown")].append(i)

    report = {}
    for g, idxs in groups.items():
        gt = [y_true[i] for i in idxs]
        pr = [y_prob[i] for i in idxs]
        report[g] = compute_metrics(gt, pr)
    return report


def save_report(report, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
