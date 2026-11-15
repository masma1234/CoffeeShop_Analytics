"""Reproducible evaluation against independent annotations; no assumed metrics."""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment

from .schema import Detection, file_hash, now
from .config import Config
from .tracker import iou


def ratio(numerator: float, denominator: float) -> float | None:
    return numerator/denominator if denominator else None


def match(gt: list[dict], predictions: list[dict], threshold: float = 0.5) -> list[tuple[int, int]]:
    cost = np.full((len(gt), len(predictions)), 1e6)
    for i, a in enumerate(gt):
        for j, b in enumerate(predictions):
            overlap = iou(tuple(a["bbox"]), tuple(b["bbox"]))
            if a["class_id"] == b["class_id"] and overlap >= threshold:
                cost[i, j] = 1-overlap
    rows, cols = linear_sum_assignment(cost)
    return [(int(i), int(j)) for i, j in zip(rows, cols) if cost[i, j] < 1e6]


def average_precision(gt_frames: dict, pred_frames: dict, cid: int, threshold: float) -> float | None:
    total = sum(d["class_id"] == cid for f in gt_frames.values() for d in f.get("detections", []))
    if not total:
        return None
    ranked = sorted(((d["confidence"], fid, d) for fid, f in pred_frames.items() for d in f.get("detections", []) if d["class_id"] == cid), reverse=True, key=lambda x: x[0])
    used: set[tuple] = set()
    tp, fp = [], []
    for _, fid, det in ranked:
        candidates = [(iou(tuple(det["bbox"]), tuple(g["bbox"])), i) for i, g in enumerate(gt_frames.get(fid, {}).get("detections", [])) if g["class_id"] == cid and (fid, i) not in used]
        best = max(candidates, default=(0, -1))
        correct = best[0] >= threshold
        if correct:
            used.add((fid, best[1]))
        tp.append(int(correct))
        fp.append(int(not correct))
    if not tp:
        return 0.0
    cumulative_tp, cumulative_fp = np.cumsum(tp), np.cumsum(fp)
    recall = cumulative_tp/total
    precision = cumulative_tp/(cumulative_tp+cumulative_fp)
    return float(np.mean([max(precision[recall >= r], default=0.0) for r in np.linspace(0, 1, 101)]))


def evaluate(ground_truth: dict, predictions: dict) -> dict:
    if not ground_truth.get("frames"):
        raise ValueError("Evaluation requires annotated frames")
    gt = {f["frame"]: f for f in ground_truth["frames"]}
    pred = {f["frame"]: f for f in predictions["frames"]}
    if len(gt) != len(ground_truth["frames"]) or len(pred) != len(predictions["frames"]):
        raise ValueError("Duplicate evaluation frame IDs")
    if set(gt) != set(pred):
        raise ValueError("Predictions and ground truth must cover exactly the same annotated frames")
    classes = sorted({d["class_id"] for f in list(gt.values())+list(pred.values()) for d in f.get("detections", [])})
    counts: dict[int, Counter[str]] = {cid: Counter() for cid in classes}
    calibration = []
    identities: Counter = Counter()
    previous_id: dict = {}
    was_matched: dict = {}
    switches = fragments = total_gt = total_pred = 0
    track_times: dict = defaultdict(list)
    occupancy: Counter[str] = Counter()
    false_duration = 0.0
    detection_delays = []
    occupancy_started: dict = {}
    occupancy_detected: set = set()
    tracking_annotated = all("track_id" in d for f in list(gt.values())+list(pred.values()) for d in f.get("detections", []))
    frame_ids = sorted(gt)
    for index, fid in enumerate(frame_ids):
        gf, pf = gt[fid], pred[fid]
        gd, pd = gf.get("detections", []), pf.get("detections", [])
        for detections in (gd, pd):
            tids = [d["track_id"] for d in detections if "track_id" in d]
            if len(tids) != len(set(tids)):
                raise ValueError("Duplicate track ID in an annotated frame")
        for d in gd+pd:
            Detection(d["class_id"], tuple(d["bbox"]), d.get("confidence", 1.0))
        pairs = match(gd, pd)
        good_g, good_p = {i for i, _ in pairs}, {j for _, j in pairs}
        total_gt += len(gd)
        total_pred += len(pd)
        for i, d in enumerate(gd):
            counts[d["class_id"]]["tp" if i in good_g else "fn"] += 1
        for j, d in enumerate(pd):
            if j not in good_p:
                counts[d["class_id"]]["fp"] += 1
            calibration.append((d["confidence"], int(j in good_p)))
            if "track_id" in d:
                track_times[d["track_id"]].append(gf.get("seconds", fid))
        if tracking_annotated:
            for i, j in pairs:
                gid, pid = gd[i]["track_id"], pd[j]["track_id"]
                identities[(gid, pid)] += 1
                if gid in previous_id and previous_id[gid] != pid:
                    switches += 1
                if gid in previous_id and not was_matched.get(gid, True):
                    fragments += 1
                previous_id[gid], was_matched[gid] = pid, True
            for i, d in enumerate(gd):
                if i not in good_g:
                    was_matched[d["track_id"]] = False
        predicted_tables = {t["zone_id"]: t for t in pf.get("tables", [])}
        seconds = gf.get("seconds", float(fid))
        next_time = gt[frame_ids[index+1]].get("seconds", float(frame_ids[index+1])) if index+1 < len(frame_ids) else seconds
        if next_time < seconds:
            raise ValueError("Annotation timestamps must be chronological")
        for t in gf.get("tables", []):
            zid = t["zone_id"]
            expected, actual = t["status"], predicted_tables.get(zid, {}).get("status", "unknown")
            occupancy["total"] += 1
            occupancy["correct"] += expected == actual
            occupancy["pred_empty"] += actual == "empty"
            occupancy["true_empty"] += actual == expected == "empty"
            occupancy["gt_occupied"] += expected == "occupied"
            occupancy["true_occupied"] += actual == expected == "occupied"
            if expected != "occupied" and actual == "occupied":
                false_duration += max(0, next_time-seconds)
            if expected == "occupied":
                occupancy_started.setdefault(zid, seconds)
                if actual == "occupied" and zid not in occupancy_detected:
                    detection_delays.append(seconds-occupancy_started[zid])
                    occupancy_detected.add(zid)
            else:
                occupancy_started.pop(zid, None)
                occupancy_detected.discard(zid)
    per_class = {}
    for cid, c in counts.items():
        precision, recall = ratio(c["tp"], c["tp"]+c["fp"]), ratio(c["tp"], c["tp"]+c["fn"])
        aps = [average_precision(gt, pred, cid, float(t)) for t in np.linspace(0.5, 0.95, 10)]
        per_class[str(cid)] = {**c, "precision": precision, "recall": recall,
                              "f1": ratio(2*c["tp"], 2*c["tp"]+c["fp"]+c["fn"]),
                              "mAP50": aps[0], "mAP50_95": float(np.mean([a for a in aps if a is not None])) if aps[0] is not None else None}
    totals = sum(counts.values(), Counter())
    ece = 0.0
    for index in range(10):
        bucket = [(c, ok) for c, ok in calibration if min(int(c*10), 9) == index]
        if bucket:
            ece += len(bucket)/len(calibration)*abs(np.mean([c for c, _ in bucket])-np.mean([ok for _, ok in bucket]))
    gids, pids = sorted({g for g, _ in identities}, key=str), sorted({p for _, p in identities}, key=str)
    weights = np.array([[identities[(g, p)] for p in pids] for g in gids]).reshape(len(gids), len(pids))
    rows, cols = linear_sum_assignment(-weights)
    idtp = int(sum(weights[i, j] for i, j in zip(rows, cols)))
    gt_events, pred_events = ground_truth.get("events", []), predictions.get("events", [])
    from .event_evaluation import evaluate_events
    event_metrics = evaluate_events(ground_truth,predictions) if "events" in ground_truth else None
    event_matches = event_metrics["tp"] if event_metrics else 0
    event_ids = [e["event_id"] for e in pred_events if "event_id" in e]
    expected_sales = {r["event_id"]: r for r in ground_truth.get("reconciliations", [])}
    predicted_sales = {r["event_id"]: r for r in predictions.get("reconciliations", [])}
    confirmed = {k for k, v in predicted_sales.items() if v["status"] == "confirmed_sale"}
    true_sales = {k for k, v in expected_sales.items() if v["status"] == "confirmed_sale"}
    alerts = {k for k, v in predicted_sales.items() if v["status"] in {"needs_review", "payment_unmatched", "inventory_discrepancy"}}
    true_alerts = {k for k, v in expected_sales.items() if v["status"] in {"needs_review", "payment_unmatched", "inventory_discrepancy"}}
    maps50 = [c["mAP50"] for c in per_class.values() if c["mAP50"] is not None]
    maps95 = [c["mAP50_95"] for c in per_class.values() if c["mAP50_95"] is not None]
    sales_annotated = "reconciliations" in ground_truth
    result = {"provenance": ground_truth.get("provenance", {"kind": "unspecified_not_promotable"}),
            "frames": len(gt), "detection": {"precision": ratio(totals["tp"], totals["tp"]+totals["fp"]),
            "recall": ratio(totals["tp"], totals["tp"]+totals["fn"]), "f1": ratio(2*totals["tp"], 2*totals["tp"]+totals["fp"]+totals["fn"]),
            "mAP50": float(np.mean(maps50)) if maps50 else None, "mAP50_95": float(np.mean(maps95)) if maps95 else None,
            "calibration_ece": float(ece) if calibration else None, "per_class": per_class},
            "tracking": {"IDF1": ratio(2*idtp, total_gt+total_pred) if tracking_annotated else None,
            "MOTA": 1-(totals["fn"]+totals["fp"]+switches)/total_gt if total_gt and tracking_annotated else None,
            "HOTA": None, "ID_switches": switches if tracking_annotated else None, "fragmentation": fragments if tracking_annotated else None,
            "mean_track_lifetime_seconds": float(np.mean([max(v)-min(v) for v in track_times.values()])) if track_times else None},
            "occupancy": {"accuracy": ratio(occupancy["correct"], occupancy["total"]),
            "empty_table_precision": ratio(occupancy["true_empty"], occupancy["pred_empty"]),
            "occupied_table_recall": ratio(occupancy["true_occupied"], occupancy["gt_occupied"]),
            "mean_time_to_detection_seconds": float(np.mean(detection_delays)) if detection_delays else None,
            "false_occupancy_seconds": false_duration if occupancy["total"] else None},
            "counting": {"absolute_error": abs(len(pred_events)-len(gt_events)),
            "percentage_error": ratio(100*abs(len(pred_events)-len(gt_events)), len(gt_events)),
            "overcount_rate": ratio(max(0, len(pred_events)-len(gt_events)), len(gt_events)),
            "undercount_rate": ratio(max(0, len(gt_events)-len(pred_events)), len(gt_events)),
            "event_precision": ratio(event_matches, len(pred_events)), "event_recall": ratio(event_matches, len(gt_events)),
            "duplicate_event_rate": ratio(len(event_ids)-len(set(event_ids)), len(event_ids))},
            "reconciliation": {"confirmed_sale_precision": ratio(len(confirmed & true_sales), len(confirmed)) if sales_annotated else None,
            "unmatched_event_rate": ratio(len(alerts), len(predicted_sales)), "false_alert_rate": ratio(len(alerts-true_alerts), len(alerts)) if sales_annotated else None,
            "missed_sale_rate": ratio(len(true_sales-confirmed), len(true_sales)) if sales_annotated else None},
            "runtime": predictions.get("runtime"),
            "limitations": ["Detection AP uses 101-point interpolation; compare model.val separately.", "HOTA and GPU utilization are not implemented.", "No real-world accuracy can be inferred from logic fixtures."]}
    if "events" not in ground_truth:
        result["counting"] = {name: value if name == "duplicate_event_rate" else None for name, value in result["counting"].items()}
    else:
        result["counting"].update(event_metrics)
    return result


def model_evaluate(config: Config, data: str, split: str = "test") -> dict:
    from .detector import validate_metadata
    from ultralytics import YOLO
    metadata = validate_metadata(config)
    if not Path(data).is_file():
        raise FileNotFoundError(data)
    model = YOLO(str(config.path(config.data["model"]["weights"])))
    if model.names != {cid: c["name"] for cid, c in config.catalog.items()}:
        raise ValueError("Model class names/IDs mismatch")
    metrics = model.val(data=data, split=split, device=config.data["model"]["device"], plots=False)
    p, r = float(metrics.box.mp), float(metrics.box.mr)
    return {"timestamp": now(), "model": metadata, "dataset_yaml_sha256": file_hash(data),
            "split": split, "detection": {"precision": p, "recall": r, "f1": 2*p*r/(p+r) if p+r else 0,
            "mAP50": float(metrics.box.map50), "mAP50_95": float(metrics.box.map),
            "per_class": metrics.summary()}, "speed_ms": metrics.speed,
            "provenance": {"kind": "model_validation_requires_dataset_audit"},
            "promotion_eligible": False}
