import argparse
import torch
from torch.utils.data import DataLoader

from ml.datasets import ImageFolderDataset
from ml.models import CNNDetector, ConvAutoencoder, EnsembleDetector
from ml.metrics import compute_metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--batch", type=int, default=8)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dataset = ImageFolderDataset(args.data)
    loader = DataLoader(dataset, batch_size=args.batch, shuffle=False, num_workers=0)

    cnn = CNNDetector().to(device).eval()
    ae = ConvAutoencoder().to(device).eval()
    ensemble = EnsembleDetector(cnn, ae)

    y_true = []
    y_prob_cnn = []
    y_prob_ens = []

    with torch.no_grad():
        for x, y in loader:
            x = x.to(device)
            logits, _ = cnn(x)
            prob = torch.softmax(logits, dim=1)[:, 1].cpu().numpy()
            ens_score, _, _ = ensemble.score(x)
            y_true.extend(y.numpy())
            y_prob_cnn.extend(prob)
            y_prob_ens.extend(ens_score.cpu().numpy())

    print("CNN-only:", compute_metrics(y_true, y_prob_cnn))
    print("Ensemble:", compute_metrics(y_true, y_prob_ens))


if __name__ == "__main__":
    main()
