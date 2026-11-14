"""Explicit raw-feature box/integer policies; default is deny all mutations.

These policies describe feature-space approximations, not valid PE edits.
Coupled histogram/hash/structural operations require a future reviewed projector.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

import numpy as np

from src.models.frozen import transform


@dataclass(frozen=True)
class FeaturePolicy:
    record: dict
    dimension: int

    def __post_init__(self):
        r = self.record
        if (
            r.get("schema_version") != 1
            or r.get("status") not in {"reviewed_feature_space", "owner_authorized_feature_space"}
            or not isinstance(r.get("reviewer"), str)
            or not r["reviewer"].strip()
            or not isinstance(r.get("features"), list)
            or not r["features"]
        ):
            raise ValueError("A reviewed nonempty feature-space policy is required")
        seen = set()
        for f in r["features"]:
            i = f["index"]
            if type(i) is not int or not 0 <= i < self.dimension or i in seen:
                raise ValueError("Invalid or duplicate feature index")
            seen.add(i)
            lo, hi = f["minimum"], f["maximum"]
            if (
                not np.isfinite([lo, hi]).all()
                or lo >= hi
                or type(f["integer"]) is not bool
                or not isinstance(f.get("operation"), str)
                or not f["operation"].strip()
            ):
                raise ValueError("Each operation needs finite bounds and an integer flag")
            if f["integer"] and (lo < 0 or lo != int(lo) or hi != int(hi)):
                raise ValueError("Integer count bounds must be integral and nonnegative")
            if "nondecreasing" in f and type(f["nondecreasing"]) is not bool:
                raise ValueError("nondecreasing must be boolean")
            if "max_increase" in f and (
                not np.isfinite(f["max_increase"])
                or f["max_increase"] <= 0
                or (f["integer"] and f["max_increase"] != int(f["max_increase"]))
            ):
                raise ValueError("Invalid increase budget")
        if (
            r["status"] == "owner_authorized_feature_space"
            and r.get("security_review") != "pending"
        ):
            raise ValueError("Owner authorization must retain pending technical Security review")

    @property
    def digest(self):
        return hashlib.sha256(
            json.dumps(self.record, sort_keys=True, allow_nan=False).encode()
        ).hexdigest()

    @property
    def mask(self):
        mask = np.zeros(self.dimension, dtype=np.float32)
        mask[[f["index"] for f in self.record["features"]]] = 1
        return mask

    def bounds(self, original, mean, scale):
        """Finite model-space bounds; immutable coordinates get solver-only padding."""
        z = transform(original, mean, scale)
        low, high = z.min(axis=0) - 1, z.max(axis=0) + 1
        for f in self.record["features"]:
            i = f["index"]
            values = original[:, i]
            if np.any(values < f["minimum"]) or np.any(values > f["maximum"]):
                raise ValueError("Clean feature outside policy bounds")
            if f["integer"] and np.any(values != np.rint(values)):
                raise ValueError("Clean count feature is not integral")
            raw = np.zeros((2, self.dimension))
            raw[:, i] = [f["minimum"], f["maximum"]]
            low[i], high[i] = transform(raw, mean, scale)[:, i]
        return low.astype(np.float32), high.astype(np.float32)

    def project(self, candidate, original, mean, scale, epsilon=None):
        """Project raw bounds/counts, restore immutable values and enforce scaled Linf.

        Integer rounding may exceed an epsilon budget; revert those coordinates
        to their original feasible value. No rounding is differentiated through.
        """
        clean = transform(original, mean, scale)
        candidate = np.asarray(candidate, dtype=np.float64)
        if candidate.shape != clean.shape or not np.isfinite(candidate).all():
            raise ValueError("Invalid attack output")
        if epsilon is not None:
            candidate = np.clip(candidate, clean - epsilon, clean + epsilon)
        raw = np.asarray(original, dtype=np.float64).copy()
        for f in self.record["features"]:
            i = f["index"]
            # Clip in log space before inverse transformation to avoid overflow.
            endpoints = np.array([f["minimum"], f["maximum"]], dtype=np.float64)
            ends = np.sign(endpoints) * np.log1p(np.abs(endpoints))
            v = np.clip(candidate[:, i] * scale[i] + mean[i], *ends)
            v = np.sign(v) * np.expm1(np.abs(v))
            if f["integer"]:
                v = np.rint(v)
            lo, hi = f["minimum"], f["maximum"]
            if f.get("nondecreasing"):
                lo = np.maximum(lo, original[:, i])
            if "max_increase" in f:
                hi = np.minimum(hi, original[:, i] + f["max_increase"])
            raw[:, i] = np.clip(v, lo, hi)
        result = transform(raw, mean, scale)
        if epsilon is not None:
            excess = np.abs(result.astype(np.float64) - clean) > epsilon + 1e-6
            result[excess] = clean[excess]
        result[:, self.mask == 0] = clean[:, self.mask == 0]
        return result
