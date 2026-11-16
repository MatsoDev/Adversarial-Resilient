"""ART quickstart demo: FGSM / PGD / CW on MNIST (CPU).

Environment check for the attack stack, not a malware or intrusion result.

Outputs:
  docs/figures/art_samples.png        - original-vs-adversarial grid
  docs/figures/art_accuracy_vs_eps.png - accuracy-vs-epsilon curves
  docs/results/art_quickstart_results.json
  mlruns/ (local MLflow tracking, gitignored)

Usage:
  python scripts/art_quickstart.py --fast            # <~2 min, subset
  python scripts/art_quickstart.py --epochs 3        # full, >95% clean acc target
  python scripts/art_quickstart.py --synthetic       # no download, for tests
  python scripts/art_quickstart.py --cleverhans      # optional CH cross-check
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import FIGURES_DIR, RAW_DIR, RESULTS_DIR, ensure_dirs  # noqa: E402
from src.utils.seed import set_seed  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ART FGSM/PGD/CW quickstart on MNIST")
    parser.add_argument("--fast", action="store_true", help="Use subset so it finishes in ~2 min")
    parser.add_argument(
        "--synthetic", action="store_true", help="Tiny random data, no download (for tests)"
    )
    parser.add_argument(
        "--epochs", type=int, default=None, help="Training epochs (default 2 fast, 3 full)"
    )
    parser.add_argument("--eps", type=float, default=0.3, help="Main epsilon for FGSM/PGD")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--cleverhans", action="store_true", help="Also run CleverHans FGSM/PGD cross-check"
    )
    parser.add_argument(
        "--cw-samples", type=int, default=None, help="Override CW eval sample count"
    )
    return parser.parse_args(argv)


def load_mnist(fast: bool, synthetic: bool):
    """Return (train_loader, test_loader, x_test_np, y_test_np)."""
    import numpy as np
    import torch
    from torch.utils.data import DataLoader, Subset, TensorDataset
    from torchvision import datasets, transforms

    if synthetic:
        # Deterministic random data: no download, fast. Accuracy is meaningless
        # here; the smoke test only checks the pipeline returns finite numbers.
        rng = np.random.RandomState(0)
        x_train = rng.rand(256, 1, 28, 28).astype(np.float32)
        y_train = rng.randint(0, 10, size=(256,))
        x_test = rng.rand(64, 1, 28, 28).astype(np.float32)
        y_test = rng.randint(0, 10, size=(64,))
        train_ds = TensorDataset(torch.from_numpy(x_train), torch.from_numpy(y_train).long())
        test_ds = TensorDataset(torch.from_numpy(x_test), torch.from_numpy(y_test).long())
        return (
            DataLoader(train_ds, batch_size=64, shuffle=True),
            DataLoader(test_ds, batch_size=64),
            x_test,
            y_test,
        )

    transform = transforms.Compose([transforms.ToTensor()])  # keep 0..1 so ART clip_values=(0,1)
    train_ds = datasets.MNIST(str(RAW_DIR), train=True, download=True, transform=transform)
    test_ds = datasets.MNIST(str(RAW_DIR), train=False, download=True, transform=transform)
    if fast:
        train_ds = Subset(train_ds, list(range(5000)))
    train_loader = DataLoader(train_ds, batch_size=128, shuffle=True, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=256, shuffle=False, num_workers=0)
    # Full test arrays for ART (numpy NCHW float32).
    x_test = test_ds.data.float().numpy() / 255.0  # type: ignore[attr-defined]
    x_test = x_test[:, None, :, :].astype(np.float32)
    y_test = (
        test_ds.targets.numpy()
        if hasattr(test_ds.targets, "numpy")
        else torch.as_tensor(test_ds.targets).numpy()
    )  # type: ignore[attr-defined]
    return train_loader, test_loader, x_test, y_test


def train_model(model, train_loader, test_loader, epochs: int, device: str = "cpu"):
    import torch
    import torch.nn as nn

    model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.CrossEntropyLoss()
    model.train()
    for epoch in range(epochs):
        total, correct, loss_sum = 0, 0, 0.0
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            logits = model(xb)
            loss = criterion(logits, yb)
            loss.backward()
            optimizer.step()
            loss_sum += loss.item() * len(xb)
            total += len(xb)
            correct += (logits.argmax(1) == yb).sum().item()
        logger.info(
            "epoch %d/%d loss=%.4f acc=%.4f", epoch + 1, epochs, loss_sum / total, correct / total
        )
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for xb, yb in test_loader:
            xb, yb = xb.to(device), yb.to(device)
            correct += (model(xb).argmax(1) == yb).sum().item()
            total += len(xb)
    accuracy = correct / total
    logger.info("clean test accuracy: %.4f", accuracy)
    return accuracy


def wrap_art(model):
    """Wrap trained PyTorch model with ART PyTorchClassifier."""
    import torch.nn as nn
    from art.estimators.classification import PyTorchClassifier

    criterion = nn.CrossEntropyLoss()
    optimizer = __import__("torch").optim.Adam(model.parameters(), lr=1e-3)
    classifier = PyTorchClassifier(
        model=model,
        clip_values=(0.0, 1.0),
        loss=criterion,
        optimizer=optimizer,
        input_shape=(1, 28, 28),
        nb_classes=10,
    )
    return classifier


def eval_attack(y_true, y_pred_adv, x_orig, x_adv, eps, *, y_pred_clean) -> dict:
    """Measure paired rows; ASR counts clean-correct predictions made incorrect.

    ``y_pred_clean`` must follow the same row order as ``y_true``. ASR is None
    when no clean prediction is correct.
    """
    import numpy as np

    acc_adv = float((y_pred_adv == y_true).mean())
    correct = y_pred_clean == y_true
    asr_denominator = int(correct.sum())
    successful_attacks = int(np.count_nonzero(correct & (y_pred_adv != y_true)))
    asr = successful_attacks / asr_denominator if asr_denominator else None
    diff = (x_adv - x_orig).reshape(len(x_orig), -1)
    l2 = np.linalg.norm(diff, axis=1)
    linf = np.abs(diff).max(axis=1)
    return {
        "eps": eps,
        "adv_accuracy": acc_adv,
        "attack_success_rate": asr,
        "mean_l2": float(l2.mean()),
        "mean_linf": float(linf.mean()),
    }


def run_demo(args: argparse.Namespace, output_dir: Path | None = None) -> dict:
    """Run the demo and write JSON/figures/MLflow.

    By default outputs land in the repo (`docs/results`, `docs/figures`,
    `mlruns/`). Tests pass `output_dir` (e.g. pytest `tmp_path`) so synthetic
    runs never overwrite the committed demo artifacts.
    """
    ensure_dirs()
    set_seed(args.seed)

    results_dir = output_dir / "results" if output_dir else RESULTS_DIR
    figures_dir = output_dir / "figures" if output_dir else FIGURES_DIR
    tracking_dir = output_dir / "mlruns" if output_dir else ROOT / "mlruns"

    fast = args.fast or args.synthetic
    epochs = args.epochs if args.epochs is not None else (2 if fast else 3)
    train_loader, test_loader, x_test_all, y_test_all = load_mnist(
        fast=fast, synthetic=args.synthetic
    )

    # Eval subsets: keep CW small (slow). FGSM/PGD use up to 1000 samples.
    if args.synthetic:
        n_fgsm = n_pgd = 64
        n_cw = 10
    elif fast:
        n_fgsm = n_pgd = 1000
        n_cw = 20
    else:
        n_fgsm = n_pgd = 1000
        n_cw = 200
    if args.cw_samples is not None:
        n_cw = args.cw_samples

    from src.models.baseline_mlp import SmallCNN

    model = SmallCNN(num_classes=10)
    clean_acc = train_model(model, train_loader, test_loader, epochs=epochs)
    classifier = wrap_art(model)

    from art.attacks.evasion import CarliniL2Method, FastGradientMethod, ProjectedGradientDescent

    results: dict = {
        "clean_accuracy": clean_acc,
        "seed": args.seed,
        "epochs": epochs,
        "attacks": {},
    }

    x_fgsm = x_test_all[:n_fgsm]
    y_fgsm = y_test_all[:n_fgsm]
    pred_clean_fgsm = classifier.predict(x_fgsm).argmax(axis=1)
    fgsm = FastGradientMethod(estimator=classifier, eps=args.eps)
    x_adv_fgsm = fgsm.generate(x=x_fgsm)
    pred_fgsm = classifier.predict(x_adv_fgsm).argmax(axis=1)
    fgsm_metrics = eval_attack(
        y_fgsm, pred_fgsm, x_fgsm, x_adv_fgsm, args.eps, y_pred_clean=pred_clean_fgsm
    )
    fgsm_metrics.update({"method": "FGSM", "params": {"eps": args.eps}, "n_samples": n_fgsm})
    fgsm_metrics["clean_accuracy_subset"] = float((pred_clean_fgsm == y_fgsm).mean())
    results["attacks"]["fgsm"] = fgsm_metrics
    logger.info(
        "FGSM eps=%.3f clean=%.4f adv=%.4f asr=%s",
        args.eps,
        fgsm_metrics["clean_accuracy_subset"],
        fgsm_metrics["adv_accuracy"],
        fgsm_metrics["attack_success_rate"],
    )

    x_pgd = x_test_all[:n_pgd]
    y_pgd = y_test_all[:n_pgd]
    pred_clean_pgd = classifier.predict(x_pgd).argmax(axis=1)
    pgd = ProjectedGradientDescent(
        estimator=classifier, eps=args.eps, eps_step=0.1, max_iter=10 if fast else 20
    )
    x_adv_pgd = pgd.generate(x=x_pgd)
    pred_pgd = classifier.predict(x_adv_pgd).argmax(axis=1)
    pgd_metrics = eval_attack(
        y_pgd, pred_pgd, x_pgd, x_adv_pgd, args.eps, y_pred_clean=pred_clean_pgd
    )
    pgd_metrics.update(
        {
            "method": "PGD",
            "params": {"eps": args.eps, "eps_step": 0.1, "max_iter": 10 if fast else 20},
            "n_samples": n_pgd,
        }
    )
    pgd_metrics["clean_accuracy_subset"] = float((pred_clean_pgd == y_pgd).mean())
    results["attacks"]["pgd"] = pgd_metrics
    logger.info(
        "PGD eps=%.3f clean=%.4f adv=%.4f asr=%s",
        args.eps,
        pgd_metrics["clean_accuracy_subset"],
        pgd_metrics["adv_accuracy"],
        pgd_metrics["attack_success_rate"],
    )

    x_cw = x_test_all[:n_cw]
    y_cw = y_test_all[:n_cw]
    try:
        pred_clean_cw = classifier.predict(x_cw).argmax(axis=1)
        cw = CarliniL2Method(
            classifier=classifier, confidence=0.0, max_iter=10 if fast else 20, verbose=False
        )
        x_adv_cw = cw.generate(x=x_cw)
        pred_cw = classifier.predict(x_adv_cw).argmax(axis=1)
        cw_metrics = eval_attack(y_cw, pred_cw, x_cw, x_adv_cw, eps=0.0, y_pred_clean=pred_clean_cw)
        cw_metrics.update(
            {
                "method": "CW-L2",
                "params": {"confidence": 0.0, "max_iter": 10 if fast else 20},
                "n_samples": n_cw,
            }
        )
        cw_metrics["clean_accuracy_subset"] = float((pred_clean_cw == y_cw).mean())
        logger.info(
            "CW-L2 clean=%.4f adv=%.4f asr=%s",
            cw_metrics["clean_accuracy_subset"],
            cw_metrics["adv_accuracy"],
            cw_metrics["attack_success_rate"],
        )
    except Exception as e:  # CW can OOM/fail on some setups; record and continue
        logger.warning("CW-L2 failed: %s", e)
        cw_metrics = {"method": "CW-L2", "failed": True, "error": str(e), "n_samples": n_cw}
        x_adv_cw = x_cw
    results["attacks"]["cw_l2"] = cw_metrics

    eps_grid = [0.0, 0.05, 0.1, 0.15, 0.2, 0.3] if not args.synthetic else [0.0, 0.1, 0.3]
    epsilon_results = []
    for eps in eps_grid:
        fgsm_at_eps = FastGradientMethod(estimator=classifier, eps=eps)
        fgsm_samples = fgsm_at_eps.generate(x=x_fgsm)
        fgsm_accuracy = float((classifier.predict(fgsm_samples).argmax(axis=1) == y_fgsm).mean())
        pgd_at_eps = ProjectedGradientDescent(
            estimator=classifier, eps=eps, eps_step=0.05, max_iter=10
        )
        pgd_samples = pgd_at_eps.generate(x=x_pgd)
        pgd_accuracy = float((classifier.predict(pgd_samples).argmax(axis=1) == y_pgd).mean())
        epsilon_results.append({"eps": eps, "fgsm_acc": fgsm_accuracy, "pgd_acc": pgd_accuracy})
    results["accuracy_vs_eps"] = epsilon_results

    if args.cleverhans:
        results["cleverhans"] = cleverhans_check(model, x_fgsm, y_fgsm, args.eps)

    results_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    with open(results_dir / "art_quickstart_results.json", "w") as handle:
        json.dump(results, handle, indent=2)
        handle.write("\n")
    logger.info("wrote %s", results_dir / "art_quickstart_results.json")

    save_figures(x_fgsm, x_adv_fgsm, x_adv_pgd, y_fgsm, pred_fgsm, epsilon_results, figures_dir)
    log_mlflow(results, args, results_dir, figures_dir, tracking_dir)
    return results


def cleverhans_check(model, x_np, y_np, eps: float) -> dict:
    """Minimal CleverHans FGSM/PGD cross-check. Returns skipped dict if unavailable."""
    try:
        import numpy as _np
        import torch as _torch
        from cleverhans.torch.attacks.fast_gradient_method import fast_gradient_method
        from cleverhans.torch.attacks.projected_gradient_descent import projected_gradient_descent
    except Exception as e:
        logger.warning("CleverHans not available, skipping: %s", e)
        return {"skipped": True, "reason": str(e)}
    model.eval()
    out: dict = {}
    with _torch.no_grad():
        xb = _torch.from_numpy(x_np)
        for name, fn in [
            ("fgsm", lambda: fast_gradient_method(model, xb, eps, _np.inf)),
            ("pgd", lambda: projected_gradient_descent(model, xb, eps, 0.05, 10, _np.inf)),
        ]:
            try:
                xa = fn().numpy()
                pred = model(_torch.from_numpy(xa)).argmax(1).numpy()
                out[name] = {"adv_accuracy": float((pred == y_np).mean())}
            except Exception as e:
                out[name] = {"failed": True, "error": str(e)}
    return out


def save_figures(x_orig, x_fgsm, x_pgd, y_true, y_pred_fgsm, table, figures_dir: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    n = min(5, len(x_orig))
    fig, axes = plt.subplots(3, n, figsize=(2 * n, 6))
    for i in range(n):
        axes[0, i].imshow(x_orig[i, 0], cmap="gray", vmin=0, vmax=1)
        axes[0, i].set_title(f"orig y={y_true[i]}")
        axes[0, i].axis("off")
        axes[1, i].imshow(np.clip(x_fgsm[i, 0], 0, 1), cmap="gray", vmin=0, vmax=1)
        axes[1, i].set_title(f"FGSM pred={y_pred_fgsm[i]}")
        axes[1, i].axis("off")
        axes[2, i].imshow(np.clip(x_pgd[i, 0], 0, 1), cmap="gray", vmin=0, vmax=1)
        axes[2, i].set_title("PGD")
        axes[2, i].axis("off")
    fig.tight_layout()
    fig.savefig(figures_dir / "art_samples.png", dpi=120)
    plt.close(fig)

    eps = [r["eps"] for r in table]
    plt.figure(figsize=(6, 4))
    plt.plot(eps, [r["fgsm_acc"] for r in table], marker="o", label="FGSM")
    plt.plot(eps, [r["pgd_acc"] for r in table], marker="s", label="PGD")
    plt.xlabel("epsilon")
    plt.ylabel("adversarial accuracy")
    plt.title("MNIST accuracy vs epsilon")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(figures_dir / "art_accuracy_vs_eps.png", dpi=120)
    plt.close()
    logger.info("wrote figures to %s", figures_dir)


def log_mlflow(
    results: dict,
    args: argparse.Namespace,
    results_dir: Path,
    figures_dir: Path,
    tracking_dir: Path,
) -> None:
    try:
        import mlflow
    except Exception as e:
        logger.warning("mlflow not available, skipping logging: %s", e)
        return
    # MLflow >=3.7 requires an explicit opt-in for the local file store. The
    # demo is a local, single-user workflow and intentionally keeps mlruns/.
    os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")
    mlflow.set_tracking_uri(f"file:{tracking_dir}")
    mlflow.set_experiment("art_quickstart")
    with mlflow.start_run():
        mlflow.log_param("seed", args.seed)
        mlflow.log_param("epochs", results.get("epochs"))
        mlflow.log_param("eps", args.eps)
        mlflow.log_param("fast", args.fast)
        mlflow.log_metric("clean_accuracy", results.get("clean_accuracy", 0.0))
        for k, v in results.get("attacks", {}).items():
            if isinstance(v, dict) and "adv_accuracy" in v:
                mlflow.log_metric(f"{k}_adv_acc", v["adv_accuracy"])
                if v["attack_success_rate"] is not None:
                    mlflow.log_metric(f"{k}_asr", v["attack_success_rate"])
        try:
            mlflow.log_artifact(str(results_dir / "art_quickstart_results.json"))
            for p in ["art_samples.png", "art_accuracy_vs_eps.png"]:
                fp = figures_dir / p
                if fp.exists():
                    mlflow.log_artifact(str(fp))
        except Exception as e:
            logger.warning("mlflow artifact logging failed: %s", e)


def main(argv=None) -> int:
    args = parse_args(argv)
    run_demo(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
