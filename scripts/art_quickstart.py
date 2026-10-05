"""ART quickstart demo: FGSM / PGD / CW on MNIST (CPU).

Template for Phase 1. Proves the attack stack works in our env and shows
students how to wrap a PyTorch model with IBM ART.

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
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import FIGURES_DIR, RAW_DIR, RESULTS_DIR, ensure_dirs  # noqa: E402
from src.utils.seed import set_seed  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="ART FGSM/PGD/CW quickstart on MNIST")
    p.add_argument("--fast", action="store_true", help="Use subset so it finishes in ~2 min")
    p.add_argument("--synthetic", action="store_true", help="Tiny random data, no download (for tests)")
    p.add_argument("--epochs", type=int, default=None, help="Training epochs (default 2 fast, 3 full)")
    p.add_argument("--eps", type=float, default=0.3, help="Main epsilon for FGSM/PGD")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--cleverhans", action="store_true", help="Also run CleverHans FGSM/PGD cross-check")
    p.add_argument("--cw-samples", type=int, default=None, help="Override CW eval sample count")
    return p.parse_args(argv)


def build_model():
    from src.models.baseline_mlp import SmallCNN

    return SmallCNN(num_classes=10)


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

    tf = transforms.Compose([transforms.ToTensor()])  # keep 0..1 so ART clip_values=(0,1)
    train_ds = datasets.MNIST(str(RAW_DIR), train=True, download=True, transform=tf)
    test_ds = datasets.MNIST(str(RAW_DIR), train=False, download=True, transform=tf)
    if fast:
        train_ds = Subset(train_ds, list(range(5000)))
    train_loader = DataLoader(train_ds, batch_size=128, shuffle=True, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=256, shuffle=False, num_workers=0)
    # Full test arrays for ART (numpy NCHW float32).
    x_test = test_ds.data.float().numpy() / 255.0  # type: ignore[attr-defined]
    x_test = x_test[:, None, :, :].astype(np.float32)
    import torch as _t  # local alias to avoid confusion

    y_test = test_ds.targets.numpy() if hasattr(test_ds.targets, "numpy") else _t.as_tensor(test_ds.targets).numpy()  # type: ignore[attr-defined]
    return train_loader, test_loader, x_test, y_test


def train_model(model, train_loader, test_loader, epochs: int, device: str = "cpu"):
    import torch
    import torch.nn as nn

    model.to(device)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.CrossEntropyLoss()
    model.train()
    for epoch in range(epochs):
        total, correct, loss_sum = 0, 0, 0.0
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad()
            out = model(xb)
            loss = criterion(out, yb)
            loss.backward()
            opt.step()
            loss_sum += loss.item() * len(xb)
            total += len(xb)
            correct += (out.argmax(1) == yb).sum().item()
        logger.info("epoch %d/%d loss=%.4f acc=%.4f", epoch + 1, epochs, loss_sum / total, correct / total)
    # Clean test accuracy
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for xb, yb in test_loader:
            xb, yb = xb.to(device), yb.to(device)
            correct += (model(xb).argmax(1) == yb).sum().item()
            total += len(xb)
    acc = correct / total
    logger.info("clean test accuracy: %.4f", acc)
    return acc


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


def eval_attack(y_true, y_pred_adv, x_orig, x_adv, eps) -> dict:
    import numpy as np

    acc_adv = float((y_pred_adv == y_true).mean())
    # Attack success rate: fraction of correctly-classified-orig that flip.
    # Here we approximate with overall misclassification on adv set; the
    # caller also logs clean accuracy for context.
    asr = float((y_pred_adv != y_true).mean())
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


def run_demo(args: argparse.Namespace) -> dict:
    ensure_dirs()
    set_seed(args.seed)

    fast = args.fast or args.synthetic
    epochs = args.epochs if args.epochs is not None else (2 if fast else 3)
    train_loader, test_loader, x_test_all, y_test_all = load_mnist(fast=fast, synthetic=args.synthetic)

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

    model = build_model()
    clean_acc = train_model(model, train_loader, test_loader, epochs=epochs)
    classifier = wrap_art(model)

    from art.attacks.evasion import CarliniL2Method, FastGradientMethod, ProjectedGradientDescent

    results: dict = {"clean_accuracy": clean_acc, "seed": args.seed, "epochs": epochs, "attacks": {}}

    # --- FGSM ---
    x_fgsm = x_test_all[:n_fgsm]
    y_fgsm = y_test_all[:n_fgsm]
    fgsm = FastGradientMethod(estimator=classifier, eps=args.eps)
    x_adv_fgsm = fgsm.generate(x=x_fgsm)
    pred_fgsm = classifier.predict(x_adv_fgsm).argmax(axis=1)
    r_fgsm = eval_attack(y_fgsm, pred_fgsm, x_fgsm, x_adv_fgsm, args.eps)
    r_fgsm.update({"method": "FGSM", "params": {"eps": args.eps}, "n_samples": n_fgsm})
    r_fgsm["clean_accuracy_subset"] = float((classifier.predict(x_fgsm).argmax(axis=1) == y_fgsm).mean())
    results["attacks"]["fgsm"] = r_fgsm
    logger.info("FGSM eps=%.3f clean=%.4f adv=%.4f asr=%.4f", args.eps, r_fgsm["clean_accuracy_subset"], r_fgsm["adv_accuracy"], r_fgsm["attack_success_rate"])

    # --- PGD ---
    x_pgd = x_test_all[:n_pgd]
    y_pgd = y_test_all[:n_pgd]
    pgd = ProjectedGradientDescent(estimator=classifier, eps=args.eps, eps_step=0.1, max_iter=10 if fast else 20)
    x_adv_pgd = pgd.generate(x=x_pgd)
    pred_pgd = classifier.predict(x_adv_pgd).argmax(axis=1)
    r_pgd = eval_attack(y_pgd, pred_pgd, x_pgd, x_adv_pgd, args.eps)
    r_pgd.update(
        {
            "method": "PGD",
            "params": {"eps": args.eps, "eps_step": 0.1, "max_iter": 10 if fast else 20},
            "n_samples": n_pgd,
        }
    )
    r_pgd["clean_accuracy_subset"] = float((classifier.predict(x_pgd).argmax(axis=1) == y_pgd).mean())
    results["attacks"]["pgd"] = r_pgd
    logger.info("PGD eps=%.3f clean=%.4f adv=%.4f asr=%.4f", args.eps, r_pgd["clean_accuracy_subset"], r_pgd["adv_accuracy"], r_pgd["attack_success_rate"])

    # --- CW L2 (slow: tiny subset) ---
    x_cw = x_test_all[:n_cw]
    y_cw = y_test_all[:n_cw]
    try:
        cw = CarliniL2Method(classifier=classifier, confidence=0.0, max_iter=10 if fast else 20, verbose=False)
        x_adv_cw = cw.generate(x=x_cw)
        pred_cw = classifier.predict(x_adv_cw).argmax(axis=1)
        r_cw = eval_attack(y_cw, pred_cw, x_cw, x_adv_cw, eps=0.0)
        r_cw.update(
            {"method": "CW-L2", "params": {"confidence": 0.0, "max_iter": 10 if fast else 20}, "n_samples": n_cw}
        )
        r_cw["clean_accuracy_subset"] = float((classifier.predict(x_cw).argmax(axis=1) == y_cw).mean())
        logger.info("CW-L2 clean=%.4f adv=%.4f asr=%.4f", r_cw["clean_accuracy_subset"], r_cw["adv_accuracy"], r_cw["attack_success_rate"])
    except Exception as e:  # CW can OOM/fail on some setups; record and continue
        logger.warning("CW-L2 failed: %s", e)
        r_cw = {"method": "CW-L2", "failed": True, "error": str(e), "n_samples": n_cw}
        x_adv_cw = x_cw
    results["attacks"]["cw_l2"] = r_cw

    # --- accuracy-vs-epsilon (FGSM + PGD) ---
    eps_grid = [0.0, 0.05, 0.1, 0.15, 0.2, 0.3] if not args.synthetic else [0.0, 0.1, 0.3]
    table = []
    for eps in eps_grid:
        f = FastGradientMethod(estimator=classifier, eps=eps)
        xa = f.generate(x=x_fgsm)
        acc_f = float((classifier.predict(xa).argmax(axis=1) == y_fgsm).mean())
        g = ProjectedGradientDescent(estimator=classifier, eps=eps, eps_step=0.05, max_iter=10)
        xb = g.generate(x=x_pgd)
        acc_p = float((classifier.predict(xb).argmax(axis=1) == y_pgd).mean())
        table.append({"eps": eps, "fgsm_acc": acc_f, "pgd_acc": acc_p})
    results["accuracy_vs_eps"] = table

    # --- CleverHans cross-check (optional, graceful skip) ---
    if args.cleverhans:
        results["cleverhans"] = cleverhans_check(model, x_fgsm, y_fgsm, args.eps)

    # --- save JSON + figures + MLflow ---
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_DIR / "art_quickstart_results.json", "w") as f:
        json.dump(results, f, indent=2)
    logger.info("wrote %s", RESULTS_DIR / "art_quickstart_results.json")

    save_figures(x_fgsm, x_adv_fgsm, x_adv_pgd, y_fgsm, pred_fgsm, table)
    log_mlflow(results, args)
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


def save_figures(x_orig, x_fgsm, x_pgd, y_true, y_pred_fgsm, table) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    # Grid: 5 originals vs FGSM vs PGD
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
    fig.savefig(FIGURES_DIR / "art_samples.png", dpi=120)
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
    plt.savefig(FIGURES_DIR / "art_accuracy_vs_eps.png", dpi=120)
    plt.close()
    logger.info("wrote figures to %s", FIGURES_DIR)


def log_mlflow(results: dict, args: argparse.Namespace) -> None:
    try:
        import mlflow
    except Exception as e:
        logger.warning("mlflow not available, skipping logging: %s", e)
        return
    mlflow.set_tracking_uri(f"file:{ROOT / 'mlruns'}")
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
                mlflow.log_metric(f"{k}_asr", v["attack_success_rate"])
        try:
            mlflow.log_artifact(str(RESULTS_DIR / "art_quickstart_results.json"))
            for p in ["art_samples.png", "art_accuracy_vs_eps.png"]:
                fp = FIGURES_DIR / p
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
