import argparse
import numpy as np
import matplotlib.pyplot as plt
import torch
from torch.utils.data import DataLoader

from ml.datasets import ImageFolderDataset
from ml.models import CNNDetector, ConvAutoencoder, EnsembleDetector
from ml.metrics import compute_metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--out", default="roc.png")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dataset = ImageFolderDataset(args.data)
    loader = DataLoader(dataset, batch_size=8, shuffle=False, num_workers=0)

    cnn = CNNDetector().to(device).eval()
    ae = ConvAutoencoder().to(device).eval()
    model = EnsembleDetector(cnn, ae)

    y_true = []
    y_prob = []
    with torch.no_grad():
        for x, y in loader:
            x = x.to(device)
            score, _, _ = model.score(x)
            y_true.extend(y.numpy())
            y_prob.extend(score.cpu().numpy())

    metrics = compute_metrics(np.array(y_true), np.array(y_prob))
    print(metrics)

    # ROC curve
    from sklearn.metrics import roc_curve
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    plt.figure()
    plt.plot(fpr, tpr, label="Ensemble ROC")
    plt.plot([0, 1], [0, 1], "--", color="gray")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve")
    plt.legend()
    plt.tight_layout()
    plt.savefig(args.out)


if __name__ == "__main__":
    main()
