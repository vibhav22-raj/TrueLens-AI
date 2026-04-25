"""
Training script for deepfake detection models.
Supports local folder datasets and Hugging Face datasets (WildDeepfake).
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
import io

import numpy as np
import torch
from PIL import Image
from sklearn.metrics import f1_score, roc_auc_score
from torch.utils.data import ConcatDataset, DataLoader, Dataset
from torchvision import transforms

from .autoencoder import ConvAutoencoder, PerceptualLoss, train_autoencoder
from .cnn_model import DeepfakeDetector, FocalLoss, evaluate, get_optimizer, get_transforms, train_one_epoch

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

SPLIT_ALIASES = {
    "train": {"train", "training"},
    "val": {"val", "valid", "validate", "validation"},
    "test": {"test", "testing"},
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iter_images(root: Path) -> list[Path]:
    files: list[Path] = []
    for ext in IMAGE_EXTS:
        files.extend(root.rglob(f"*{ext}"))
    return files


def _matches_split_name(dir_name: str, split: str) -> bool:
    aliases = SPLIT_ALIASES.get(split, {split})
    return dir_name.strip().lower() in aliases


def _resolve_split_dir(root: Path, split: str) -> Path | None:
    for child in root.iterdir() if root.exists() else []:
        if child.is_dir() and _matches_split_name(child.name, split):
            return child
    return None


def _resolve_class_dir(split_dir: Path, label: str) -> Path | None:
    candidates = {label, label.capitalize(), label.upper()}
    for child in split_dir.iterdir() if split_dir.exists() else []:
        if child.is_dir() and child.name in candidates:
            return child
    return None


def _contains_real_fake(split_dir: Path) -> bool:
    return bool(_resolve_class_dir(split_dir, "real") and _resolve_class_dir(split_dir, "fake"))


def _find_split_dirs(root: Path, split: str) -> list[Path]:
    matches: list[Path] = []
    if not root.exists():
        return matches

    # Direct child split folder.
    direct = _resolve_split_dir(root, split)
    if direct and _contains_real_fake(direct):
        matches.append(direct)

    # Recursive search for split folders with real/fake.
    for path in root.rglob("*"):
        if not path.is_dir():
            continue
        if _matches_split_name(path.name, split) and _contains_real_fake(path):
            if path not in matches:
                matches.append(path)

    # If no split-named folder found for train, allow any folder containing real/fake.
    if not matches and split == "train":
        for path in root.rglob("*"):
            if not path.is_dir():
                continue
            if _contains_real_fake(path):
                matches.append(path)
        if matches:
            print(f"[warn] Using fallback train folders (no explicit train split found) under {root}")

    return matches


class FolderSplitDataset(Dataset):
    def __init__(self, split_dir: Path, phase: str, image_size: int, max_per_class: int | None):
        self.split_dir = split_dir
        self.phase = phase
        self.transform = get_transforms(phase, image_size)
        self.samples: list[tuple[str, int]] = []

        real_dir = _resolve_class_dir(split_dir, "real")
        fake_dir = _resolve_class_dir(split_dir, "fake")

        if not real_dir or not fake_dir:
            raise ValueError(f"Split dir missing real/fake folders: {split_dir}")

        real_files = [p for p in _iter_images(real_dir)]
        fake_files = [p for p in _iter_images(fake_dir)]

        if max_per_class:
            real_files = real_files[:max_per_class]
            fake_files = fake_files[:max_per_class]

        for p in real_files:
            self.samples.append((str(p), 0))
        for p in fake_files:
            self.samples.append((str(p), 1))

        print(f"[{phase}] Loaded from {split_dir}: {len(real_files)} real, {len(fake_files)} fake")

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        path, label = self.samples[idx]
        image = Image.open(path).convert("RGB")
        return self.transform(image), torch.tensor(label, dtype=torch.long)


class RealOnlyDataset(Dataset):
    def __init__(self, split_dir: Path, image_size: int = 128):
        real_dir = _resolve_class_dir(split_dir, "real")
        if not real_dir:
            raise ValueError(f"Real folder not found in {split_dir}")
        self.files = _iter_images(real_dir)
        self.transform = transforms.Compose(
            [
                transforms.Resize((image_size, image_size)),
                transforms.ToTensor(),
            ]
        )
        print(f"[AE Train] Loaded {len(self.files)} real images from {split_dir}")

    def __len__(self) -> int:
        return len(self.files)

    def __getitem__(self, idx: int):
        image = Image.open(self.files[idx]).convert("RGB")
        return self.transform(image), 0


class HFDatasetWrapper(Dataset):
    def __init__(
        self,
        dataset_name: str,
        split: str,
        image_col: str = "image",
        label_col: str = "label",
        image_size: int = 224,
        phase: str = "train",
        limit: int | None = None,
    ):
        from datasets import load_dataset

        self.transform = get_transforms(phase, image_size)
        self.dataset = load_dataset(dataset_name, split=split)
        self.image_col = image_col
        self.label_col = label_col
        self.limit = limit

    def __len__(self) -> int:
        if self.limit is None:
            return len(self.dataset)
        return min(self.limit, len(self.dataset))

    def _to_image(self, item: Any) -> Image.Image:
        if isinstance(item, Image.Image):
            return item.convert("RGB")
        if isinstance(item, dict):
            if "path" in item:
                return Image.open(item["path"]).convert("RGB")
            if "bytes" in item:
                return Image.open(io.BytesIO(item["bytes"])).convert("RGB")
        return Image.fromarray(np.array(item)).convert("RGB")

    def _to_label(self, value: Any) -> int:
        if isinstance(value, (int, np.integer)):
            return int(value)
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"real", "authentic"}:
                return 0
            if lowered in {"fake", "deepfake"}:
                return 1
        raise ValueError(f"Unsupported label value: {value}")

    def __getitem__(self, idx: int):
        row = self.dataset[idx]
        image = self._to_image(row[self.image_col])
        label = self._to_label(row[self.label_col])
        return self.transform(image), torch.tensor(label, dtype=torch.long)


def _build_local_datasets(
    roots: Iterable[str],
    split: str,
    image_size: int,
    max_per_class: int | None,
) -> list[Dataset]:
    datasets: list[Dataset] = []
    for root in roots:
        root_path = Path(root)
        split_dirs = _find_split_dirs(root_path, split)
        if not split_dirs:
            print(f"[warn] No split found for {split} in {root_path}")
            continue
        for split_dir in split_dirs:
            try:
                datasets.append(FolderSplitDataset(split_dir, split, image_size, max_per_class))
            except ValueError as exc:
                print(f"[warn] {exc}")
    return datasets


def _find_first_train_split(roots: Iterable[str]) -> Path | None:
    for root in roots:
        root_path = Path(root)
        split_dirs = _find_split_dirs(root_path, "train")
        if split_dirs:
            return split_dirs[0]
    return None


def _build_train_val_test(args):
    local_roots = args.local_dataset or []
    train_sets = _build_local_datasets(local_roots, "train", args.image_size, args.max_per_class)
    val_sets = _build_local_datasets(local_roots, "val", args.image_size, args.max_per_class)
    test_sets = _build_local_datasets(local_roots, "test", args.image_size, args.max_per_class)

    if args.hf_dataset:
        train_sets.append(
            HFDatasetWrapper(
                args.hf_dataset,
                split=args.hf_train_split,
                image_col=args.hf_image_col,
                label_col=args.hf_label_col,
                image_size=args.image_size,
                phase="train",
                limit=args.hf_limit,
            )
        )
        if args.hf_val_split:
            val_sets.append(
                HFDatasetWrapper(
                    args.hf_dataset,
                    split=args.hf_val_split,
                    image_col=args.hf_image_col,
                    label_col=args.hf_label_col,
                    image_size=args.image_size,
                    phase="val",
                    limit=args.hf_limit,
                )
            )
        if args.hf_test_split:
            test_sets.append(
                HFDatasetWrapper(
                    args.hf_dataset,
                    split=args.hf_test_split,
                    image_col=args.hf_image_col,
                    label_col=args.hf_label_col,
                    image_size=args.image_size,
                    phase="val",
                    limit=args.hf_limit,
                )
            )

    train_ds = ConcatDataset(train_sets) if train_sets else None
    val_ds = ConcatDataset(val_sets) if val_sets else None
    test_ds = ConcatDataset(test_sets) if test_sets else None
    return train_ds, val_ds, test_ds


def train_cnn(args, train_ds: Dataset, val_ds: Dataset, output_dir: Path):
    print("\n" + "=" * 60)
    print("Training EfficientNet-B4 Deepfake Detector")
    print("=" * 60)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")

    train_loader = DataLoader(
        train_ds,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=(device == "cuda"),
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=(device == "cuda"),
    )

    model = DeepfakeDetector(model_name=args.model_name, pretrained=(not args.no_pretrained)).to(device)
    criterion = FocalLoss(alpha=0.25, gamma=2.0)
    optimizer = get_optimizer(model, lr=args.lr)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    scaler = torch.cuda.amp.GradScaler() if device == "cuda" else None

    best_val_acc = 0.0
    history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": []}

    for epoch in range(1, args.epochs + 1):
        print(f"\n[Epoch {epoch}/{args.epochs}]")

        train_metrics = train_one_epoch(model, train_loader, optimizer, criterion, device, scaler)
        val_metrics = evaluate(model, val_loader, criterion, device)
        scheduler.step()

        history["train_loss"].append(train_metrics["loss"])
        history["train_acc"].append(train_metrics["accuracy"])
        history["val_loss"].append(val_metrics["loss"])
        history["val_acc"].append(val_metrics["accuracy"])

        print(
            f"  Train -> Loss: {train_metrics['loss']:.4f} | Acc: {train_metrics['accuracy']*100:.2f}%"
        )
        print(
            f"  Val   -> Loss: {val_metrics['loss']:.4f} | Acc: {val_metrics['accuracy']*100:.2f}%"
        )

        if val_metrics["accuracy"] > best_val_acc:
            best_val_acc = val_metrics["accuracy"]
            torch.save(
                {
                    "epoch": epoch,
                    "model_name": args.model_name,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "val_accuracy": best_val_acc,
                },
                output_dir / "deepfake_model.pth",
            )
            print(f"  Saved best CNN weights (val acc {best_val_acc*100:.2f}%)")

    with open(output_dir / "cnn_history.json", "w", encoding="utf-8") as handle:
        json.dump(history, handle, indent=2)

    print(f"\nCNN training complete. Best val accuracy: {best_val_acc*100:.2f}%")
    return model


def train_ae(args, train_split_dir: Path, output_dir: Path):
    print("\n" + "=" * 60)
    print("Training Convolutional Autoencoder")
    print("=" * 60)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    train_ds = RealOnlyDataset(train_split_dir, 128)
    train_loader = DataLoader(
        train_ds,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=(device == "cuda"),
    )

    model = ConvAutoencoder().to(device)
    criterion = PerceptualLoss(mse_weight=1.0, l1_weight=0.5)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, patience=5, factor=0.5, verbose=True
    )

    best_loss = float("inf")
    for epoch in range(1, args.ae_epochs + 1):
        result = train_autoencoder(model, train_loader, optimizer, criterion, device)
        scheduler.step(result["loss"])

        if epoch % 5 == 0 or epoch == 1:
            print(f"[AE Epoch {epoch}/{args.ae_epochs}] Loss: {result['loss']:.6f}")

        if result["loss"] < best_loss:
            best_loss = result["loss"]

            val_imgs = [Image.open(str(f)).convert("RGB") for f in train_ds.files[:500]]
            transform = transforms.Compose(
                [
                    transforms.Resize((128, 128)),
                    transforms.ToTensor(),
                ]
            )
            errors = []
            with torch.no_grad():
                for img in val_imgs:
                    tensor = transform(img).unsqueeze(0).to(device)
                    err = model.reconstruction_error(tensor, reduction="image")
                    errors.append(err.item())
            threshold = float(np.percentile(errors, 95))

            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "best_loss": best_loss,
                    "threshold": threshold,
                },
                output_dir / "autoencoder_model.pth",
            )

    print(f"\nAutoencoder training complete. Best loss: {best_loss:.6f}")
    return model


def evaluate_on_test(args, test_ds: Dataset, output_dir: Path, meta: dict[str, Any]):
    from sklearn.metrics import classification_report

    device = "cuda" if torch.cuda.is_available() else "cpu"
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, num_workers=args.num_workers)

    model = DeepfakeDetector(model_name=args.model_name, pretrained=False)
    checkpoint = torch.load(output_dir / "deepfake_model.pth", map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model = model.to(device)

    criterion = FocalLoss()
    results = evaluate(model, test_loader, criterion, device)

    probs = results["probabilities"]
    labels = results["labels"]

    thresholds = np.linspace(0.1, 0.9, 81)
    best_threshold = 0.5
    best_f1 = -1.0
    for t in thresholds:
        preds = [1 if p >= t else 0 for p in probs]
        score = f1_score(labels, preds)
        if score > best_f1:
            best_f1 = score
            best_threshold = float(t)

    y_pred = [1 if p >= best_threshold else 0 for p in probs]
    correct = sum(1 for p, y in zip(y_pred, labels) if p == y)
    accuracy = (correct / max(1, len(labels))) * 100
    auc = roc_auc_score(labels, probs) * 100
    f1 = f1_score(labels, y_pred) * 100

    print("\n" + "=" * 50)
    print("TEST SET EVALUATION")
    print("=" * 50)
    print(f"Accuracy : {accuracy:.2f}%")
    print(f"AUC-ROC  : {auc:.2f}%")
    print(f"F1 Score : {f1:.2f}%")
    print(f"Best Threshold: {best_threshold:.2f}")
    print("\n" + classification_report(results["labels"], y_pred, target_names=["Real", "Fake"]))

    metrics = {
        "updated_at": _utc_now_iso(),
        "accuracy": round(accuracy, 2),
        "auc_roc": round(auc, 2),
        "f1_score": round(f1, 2),
        "threshold": round(best_threshold, 3),
        "dataset": meta,
    }
    with open(output_dir / "metrics.json", "w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2)


def parse_args():
    parser = argparse.ArgumentParser(description="Deepfake Detection Training")
    parser.add_argument(
        "--local_dataset",
        action="append",
        default=[],
        help="Local dataset root (repeat for multiple). Example: Datasets/Celeb_V2",
    )
    parser.add_argument("--epochs", type=int, default=20, help="CNN training epochs")
    parser.add_argument("--ae_epochs", type=int, default=50, help="Autoencoder epochs")
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--image_size", type=int, default=224)
    parser.add_argument("--max_per_class", type=int, default=None)
    parser.add_argument("--train_cnn", dest="train_cnn", action="store_true")
    parser.add_argument("--no_train_cnn", dest="train_cnn", action="store_false")
    parser.add_argument("--train_ae", dest="train_ae", action="store_true")
    parser.add_argument("--no_train_ae", dest="train_ae", action="store_false")
    parser.add_argument("--evaluate", dest="evaluate", action="store_true")
    parser.add_argument("--no_evaluate", dest="evaluate", action="store_false")
    parser.set_defaults(train_cnn=True, train_ae=True, evaluate=True)
    parser.add_argument("--model_name", type=str, default="efficientnet_b4")
    parser.add_argument("--no_pretrained", action="store_true")
    parser.add_argument("--num_workers", type=int, default=0)
    parser.add_argument("--hf_dataset", type=str, default=None)
    parser.add_argument("--use_wilddeepfake", action="store_true", default=False)
    parser.add_argument("--hf_image_col", type=str, default="image")
    parser.add_argument("--hf_label_col", type=str, default="label")
    parser.add_argument("--hf_train_split", type=str, default="train")
    parser.add_argument("--hf_val_split", type=str, default="validation")
    parser.add_argument("--hf_test_split", type=str, default="test")
    parser.add_argument("--hf_limit", type=int, default=None)
    return parser.parse_args()


def main():
    args = parse_args()
    if args.use_wilddeepfake and not args.hf_dataset:
        args.hf_dataset = "xingjunm/WildDeepfake"

    repo_root = Path(__file__).resolve().parents[2]
    output_dir = repo_root / "model"
    output_dir.mkdir(parents=True, exist_ok=True)

    train_ds, val_ds, test_ds = _build_train_val_test(args)
    if train_ds is None or val_ds is None:
        raise RuntimeError("No training/validation data found. Check dataset paths.")

    print("Deepfake Training Pipeline")
    print(f"Local datasets: {args.local_dataset}")
    print(f"HF dataset: {args.hf_dataset}")
    print(f"Device: {'CUDA' if torch.cuda.is_available() else 'CPU'}")

    if args.train_cnn:
        train_cnn(args, train_ds, val_ds, output_dir)

    if args.train_ae:
        train_split_dir = _find_first_train_split(args.local_dataset) if args.local_dataset else None
        if train_split_dir is None:
            print("[warn] Autoencoder skipped: no local train split with real images found.")
        else:
            train_ae(args, train_split_dir, output_dir)

    if args.evaluate and test_ds is not None:
        meta = {
            "local_datasets": args.local_dataset,
            "hf_dataset": args.hf_dataset,
            "timestamp": _utc_now_iso(),
        }
        evaluate_on_test(args, test_ds, output_dir, meta)


if __name__ == "__main__":
    main()
