"""Explicit promotion gates, append-only registry, rollback and feedback export."""
from __future__ import annotations

from .config import Config
from .detector import validate_metadata
from .schema import key, now
from .storage import SQLiteStore


def promote(store: SQLiteStore, config: Config, evaluation: dict, audit: dict) -> dict:
    config.validate()
    model = validate_metadata(config)
    if evaluation.get("provenance", {}).get("kind") != "real_heldout":
        raise ValueError("Promotion requires real held-out annotations; fixtures cannot qualify")
    if not audit.get("valid") or audit.get("synthetic") or audit.get("dataset_version") != model["dataset_version"]:
        raise ValueError("Dataset audit missing, invalid, synthetic or version mismatch")
    if evaluation.get("model_sha256") != model["sha256"] or evaluation.get("dataset_manifest_sha256") != audit["manifest_sha256"]:
        raise ValueError("Evaluation is not bound to these weights and audited dataset")
    for dotted, threshold in config.data["promotion"].items():
        value = evaluation
        for component in dotted.split("."):
            value = value.get(component) if isinstance(value, dict) else None
        if type(value) not in (int, float) or not threshold <= value <= 1:
            raise ValueError(f"Promotion failed: {dotted}={value}, required >= {threshold}")
    ts = now()
    entry = {"timestamp": ts, "action": "promote", "model": model, "config_hash": config.digest,
             "evaluation_hash": key(evaluation), "dataset_audit_hash": key(audit)}
    entry["registry_id"] = key(entry)
    store.append("model_registry", entry["registry_id"], ts, entry)
    return entry


def rollback(store: SQLiteStore, registry_id: str) -> dict:
    previous = store.get("model_registry", registry_id)
    if not previous or previous["action"] != "promote":
        raise ValueError("Rollback target must be a previously promoted registry entry")
    ts = now()
    entry = {"timestamp": ts, "action": "rollback", "model": previous["model"], "target_registry_id": registry_id,
             "activation": "Set config weights/version/metadata to this immutable artifact and restart; running processes are not hot-swapped."}
    store.append("model_registry", key(entry), ts, entry)
    return entry


def drift_summary(store: SQLiteStore, camera_id: str, limit: int = 1000) -> dict:
    rows = store.recent("observations", camera_id, limit)
    from collections import Counter
    counts: Counter = Counter()
    confidence_sum = count = 0
    for row in rows:
        for track in row["tracks"]:
            if not track["missed"]:
                counts[track["class_id"]] += 1
                confidence_sum += track["confidence"]
                count += 1
    return {"camera_id": camera_id, "class_observation_histogram": dict(counts),
            "mean_confidence": confidence_sum/count if count else None,
            "purpose": "Drift monitoring hook; compare with a validated baseline, not an automatic accuracy estimate."}
