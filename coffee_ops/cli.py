"""JSON CLI is the MVP API. Errors return a nonzero exit status."""
from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import sys
from pathlib import Path
from typing import Any

from .config import Config
from .schema import canonical, file_hash, key, now, utc
from .storage import SQLiteStore


class JSONLog(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return canonical({"timestamp": now(), "level": record.levelname, "message": record.getMessage()})


def write_result(result: object, output: str | None) -> None:
    encoded = json.dumps(result, indent=2, allow_nan=False)
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Reports are immutable artifacts; stdout remains available for shell pipelines.
        with path.open("x", encoding="utf-8") as stream:
            stream.write(encoded+"\n")
    print(encoded)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Coffee operations JSON CLI; video observations are not sales")
    p.add_argument("--config", default="config/example.json")
    p.add_argument("--db", help="Override configured SQLite path")
    p.add_argument("--output", help="Write a new JSON artifact; refuses overwrite")
    sub = p.add_subparsers(dest="command", required=True)
    replay = sub.add_parser("replay")
    replay.add_argument("--source", required=True)
    replay.add_argument("--camera", required=True)
    replay.add_argument("--run-id", required=True)
    replay.add_argument("--start", required=True, help="UTC/offset-aware capture start timestamp")
    replay.add_argument("--fixture-detections", help="Explicit synthetic logic test adapter")
    replay.add_argument("--live", action="store_true")
    replay.add_argument("--max-frames", type=int)
    sub.add_parser("validate-config")
    sub.add_parser("doctor")
    api = sub.add_parser("serve", help="Authenticated read-only API, bound to 127.0.0.1")
    api.add_argument("--port", type=int, default=8765)
    prepare = sub.add_parser("prepare-video", help="Inspect local PTS and generate an exact RT-DETR config; downloads nothing")
    prepare.add_argument("--source", required=True)
    prepare.add_argument("--directory", required=True)
    prepare.add_argument("--model-dir")
    prepare.add_argument("--device", default="cpu")
    video = sub.add_parser("annotate-video", help="Local PTS-preserving MP4, event exports and processing summary")
    video.add_argument("--source", required=True)
    video.add_argument("--directory", required=True)
    video.add_argument("--camera", required=True)
    video.add_argument("--run-id", required=True)
    video.add_argument("--start", required=True)
    video.add_argument("--sample-every", type=int)
    video.add_argument("--max-frames", type=int)
    video.add_argument("--fixture-detections", help="Explicit synthetic test adapter; never a model fallback")
    video.add_argument("--event-labels")
    video.add_argument("--export-frames-every", type=float, help="Optional annotation JPEG interval, at most 100 frames")
    frame_eval = sub.add_parser("evaluate-video-frames", help="Evaluate reviewed YOLO labels for exported review frames")
    frame_eval.add_argument("--review-directory", required=True)
    frame_eval.add_argument("--labels-dir", required=True)
    frame_eval.add_argument("--classes", required=True)
    frame_eval.add_argument("--labels-reviewed", action="store_true")
    demo = sub.add_parser("make-demo")
    demo.add_argument("--directory", required=True)
    pos = sub.add_parser("import-pos")
    pos.add_argument("--file", required=True)
    sub.add_parser("reconcile")
    report = sub.add_parser("report")
    report.add_argument("--date", required=True)
    business = sub.add_parser("business-report", help="Local business day; UTC report command remains available")
    business.add_argument("--date", required=True)
    business.add_argument("--timezone", default="UTC")
    business.add_argument("--day-start-hour", type=int, default=0)
    business.add_argument("--camera")
    business.add_argument("--run-id")
    business.add_argument("--max-observation-gap", type=float, default=5)
    crossing_review = sub.add_parser("review-crossing")
    crossing_review.add_argument("--event-id", required=True)
    crossing_review.add_argument("--decision", choices=["confirmed","rejected","uncertain"], required=True)
    crossing_review.add_argument("--note", required=True)
    status = sub.add_parser("status")
    status.add_argument("--camera", required=True)
    history = sub.add_parser("history")
    history.add_argument("--kind", default="events")
    history.add_argument("--limit", type=int, default=1000)
    history.add_argument("--after", type=int, default=0)
    alerts = sub.add_parser("alerts")
    alerts.add_argument("--after", type=int, default=0)
    unresolved = sub.add_parser("unresolved")
    unresolved.add_argument("--after", type=int, default=0)
    feedback = sub.add_parser("feedback")
    feedback.add_argument("--alert-id", required=True)
    feedback.add_argument("--resolution", choices=["open", "resolved", "dismissed"], required=True)
    feedback.add_argument("--false-positive", choices=["yes", "no", "unknown"], default="unknown")
    feedback.add_argument("--note", default="")
    export_feedback = sub.add_parser("export-feedback")
    export_feedback.add_argument("--file", required=True)
    export_feedback.add_argument("--kind", choices=["feedback", "model_feedback"], default="feedback")
    model_feedback = sub.add_parser("model-feedback")
    model_feedback.add_argument("--file", required=True, help="JSON: outcome false_positive/false_negative, evidence, class_id, note")
    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("--truth", required=True)
    evaluate.add_argument("--predictions", required=True)
    events_eval = sub.add_parser("evaluate-events", help="Event-only annotations; frames not required")
    events_eval.add_argument("--truth", required=True)
    events_eval.add_argument("--predictions", required=True)
    export = sub.add_parser("export-predictions")
    export.add_argument("--run-id", required=True)
    export.add_argument("--camera", required=True)
    export.add_argument("--all-events", action="store_true")
    model_eval = sub.add_parser("evaluate-model")
    model_eval.add_argument("--data", required=True)
    model_eval.add_argument("--split", choices=["val", "test"], default="test")
    extract = sub.add_parser("extract-frames")
    extract.add_argument("--video", required=True)
    extract.add_argument("--directory", required=True)
    extract.add_argument("--every", type=int, default=30)
    dataset = sub.add_parser("validate-dataset")
    dataset.add_argument("--manifest", required=True)
    dataset.add_argument("--minimum-examples", type=int, default=20)
    split = sub.add_parser("split-dataset")
    split.add_argument("--manifest", required=True)
    split.add_argument("--seed", default="42")
    sub.add_parser("prune-evidence")
    promote = sub.add_parser("promote")
    promote.add_argument("--evaluation", required=True)
    promote.add_argument("--dataset-audit", required=True)
    rollback = sub.add_parser("rollback")
    rollback.add_argument("--registry-id", required=True)
    drift = sub.add_parser("drift")
    drift.add_argument("--camera", required=True)
    return p


def read_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))



def dispatch(args: argparse.Namespace, config: Config, store: SQLiteStore | None) -> object:
    cmd = args.command
    if cmd == "doctor":
        from .health import backend_health
        return backend_health()
    if cmd == "serve":
        import os
        from .api import serve
        return serve(config,args.db or config.path(config.data["storage"]["path"]),
                     os.environ.get("COFFEE_OPS_API_TOKEN",""),args.port)
    if cmd == "prepare-video":
        from .video_review import prepare_video
        return prepare_video(args.source,args.directory,args.model_dir,args.device)
    if cmd == "annotate-video":
        from .video_review import review_video
        return review_video(config,args.source,args.directory,args.camera,args.run_id,args.start,
            database=args.db,sample_every=args.sample_every,max_frames=args.max_frames,
            fixture=args.fixture_detections,event_labels=args.event_labels,export_frames_every=args.export_frames_every)
    if cmd == "evaluate-video-frames":
        from .review_labels import evaluate_review_frames
        return evaluate_review_frames(args.review_directory,args.labels_dir,args.classes,args.labels_reviewed)
    if cmd == "validate-config":
        return {"valid": True, "config_hash": config.digest, "version": config.data["version"]}
    if cmd == "make-demo":
        from .demo import make_demo
        return make_demo(args.directory)
    if cmd == "evaluate-events":
        from .event_evaluation import evaluate_events
        result = evaluate_events(read_json(args.truth),read_json(args.predictions))
        result.update(ground_truth_sha256=file_hash(args.truth),predictions_sha256=file_hash(args.predictions))
        return result
    if cmd in {"extract-frames", "validate-dataset", "split-dataset"}:
        from .dataset import extract_frames, split_manifest, validate_dataset
        if cmd == "extract-frames":
            return extract_frames(args.video, args.directory, args.every)
        if cmd == "validate-dataset":
            return validate_dataset(args.manifest, args.minimum_examples)
        return split_manifest(args.manifest, args.seed)
    if cmd == "prune-evidence":
        from .pipeline import prune_evidence
        return {"removed_files": prune_evidence(config)}
    if store is None:
        raise ValueError(f"Database required for command: {cmd}")
    if cmd == "replay":
        from .detector import FixtureDetector, YOLODetector
        from .runtime import replay
        config.camera(args.camera)
        utc(args.start)
        if args.max_frames is not None and args.max_frames < 1:
            raise ValueError("max-frames must be positive")
        if not args.live and not Path(args.source).is_file():
            raise FileNotFoundError(f"Video unavailable: {args.source}")
        detector = FixtureDetector(args.fixture_detections) if args.fixture_detections else YOLODetector(config, args.camera)
        try:
            metadata = dict(detector.metadata)
            if args.fixture_detections:
                metadata["fixture_sha256"] = file_hash(args.fixture_detections)
            source = int(args.source) if args.live and args.source.isdecimal() else args.source
            return replay(config, store, detector, source, args.camera, args.run_id, args.start, metadata, args.live, args.max_frames)
        finally:
            detector.close()
    if cmd == "import-pos":
        from .pos_adapter import FilePOSAdapter, MockPOSAdapter, import_orders
        if config.data["pos"]["mode"] == "camera_only":
            raise ValueError("POS import disabled in camera-only mode")
        adapter = MockPOSAdapter(read_json(args.file)) if config.data["pos"]["mode"] == "mock" else FilePOSAdapter(args.file)
        return {"imported_lines": import_orders(store, adapter, config.data["pos"])}
    if cmd == "reconcile":
        from .reconciliation import reconcile
        return reconcile(store, config.data["pos"])
    if cmd == "report":
        from .reporting import daily_report
        return daily_report(store, args.date)
    if cmd == "business-report":
        from .business_reporting import business_report
        if args.camera:
            config.camera(args.camera)
        return business_report(store,args.date,args.timezone,args.day_start_hour,args.camera,args.max_observation_gap,args.run_id)
    if cmd == "review-crossing":
        return store.review_crossing(args.event_id,args.decision,args.note)
    if cmd == "status":
        from .reporting import current_status
        return current_status(store, args.camera)
    if cmd == "history":
        return store.records(args.kind, limit=args.limit, after=args.after)
    if cmd == "alerts":
        from .reporting import active_alerts
        return active_alerts(store, after=args.after)
    if cmd == "unresolved":
        from .reporting import unresolved_events
        return unresolved_events(store, after=args.after)
    if cmd == "feedback":
        return store.feedback(args.alert_id, args.resolution, {"yes": True, "no": False, "unknown": None}[args.false_positive], args.note)
    if cmd == "model-feedback":
        item = read_json(args.file)
        if item["outcome"] not in {"false_positive", "false_negative"} or not item["evidence"] or item["class_id"] not in config.catalog:
            raise ValueError("Invalid model feedback")
        item["timestamp"] = now()
        store.append("model_feedback", key(item), item["timestamp"], item)
        return item
    if cmd == "export-feedback":
        with Path(args.file).open("x", encoding="utf-8") as output:
            count = 0
            for row in store.scan(args.kind):
                output.write(canonical(row)+"\n")
                count += 1
        return {"records": count, "file": args.file, "purpose": "Human review and labeling queue; not automatic training labels"}
    if cmd in {"evaluate", "evaluate-model"}:
        from .evaluation import evaluate, model_evaluate
        result = evaluate(read_json(args.truth), read_json(args.predictions)) if cmd == "evaluate" else model_evaluate(config, args.data, args.split)
        if cmd == "evaluate":
            result.update({"ground_truth_sha256": file_hash(args.truth), "predictions_sha256": file_hash(args.predictions)})
            truth = read_json(args.truth)
            pred = read_json(args.predictions)
            result["model_sha256"] = pred.get("model", {}).get("sha256")
            result["dataset_manifest_sha256"] = truth.get("dataset_manifest_sha256")
        if not store.get("evaluation_results", key(result)):
            store.append("evaluation_results", key(result), now(), result)
        return result
    if cmd == "export-predictions":
        from .exports import export_predictions
        return export_predictions(store, args.run_id, args.camera, args.all_events)
    if cmd in {"promote", "rollback", "drift"}:
        from .mlops import drift_summary, promote, rollback
        if cmd == "promote":
            return promote(store, config, read_json(args.evaluation), read_json(args.dataset_audit))
        if cmd == "rollback":
            return rollback(store, args.registry_id)
        return drift_summary(store, args.camera)
    raise ValueError(f"Unknown command: {cmd}")


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JSONLog())
    log = logging.getLogger("coffee_ops")
    log.handlers = [handler]
    log.setLevel(logging.INFO)
    store = None
    try:
        if args.output:
            output = Path(args.output)
            if output.exists() or output.is_symlink():
                raise FileExistsError(f"Output artifact already exists: {output}")
            output.parent.mkdir(parents=True, exist_ok=True)
        config = Config.load(args.config)
        pure_commands = {"doctor", "validate-config", "make-demo", "extract-frames", "validate-dataset", "split-dataset", "prune-evidence", "serve", "evaluate-events", "prepare-video", "annotate-video", "evaluate-video-frames"}
        if args.command not in pure_commands:
            store = SQLiteStore(args.db or config.path(config.data["storage"]["path"]))
        result = dispatch(args, config, store)
        write_result(result, args.output)
        return 2 if isinstance(result, dict) and result.get("valid") is False else 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, EOFError, ImportError, sqlite3.Error) as exc:
        log.error("%s: %s", type(exc).__name__, exc)
        if store is not None:
            timestamp = now()
            item = {"timestamp": timestamp, "command": args.command, "error_type": type(exc).__name__, "reason": str(exc)}
            try:
                store.append("failures", key(item), timestamp, item)
                if args.command in {"replay", "import-pos"}:
                    from .alerts import alert
                    kind = "POS_integration_unavailable" if args.command == "import-pos" else "inference_unavailable"
                    item = alert(kind, timestamp, getattr(args, "camera", "all"), str(exc), 1.0, {}, [], key(item), "error")
                    store.append("alerts", item["alert_id"], timestamp, item)
                    current_health = store.latest("health", "camera_id", args.camera) if args.command == "replay" else None
                    preserve_health = current_health and (current_health["status"] == "running" or
                        (current_health["run_id"] == args.run_id and current_health["status"] == "error"))
                    if args.command == "replay" and not preserve_health:
                        health = {"timestamp": timestamp, "camera_id": args.camera, "run_id": args.run_id,
                                  "status": "error", "detector": "unavailable", "camera": "unknown",
                                  "tracker": "unknown", "storage": "ok", "pos": "unknown",
                                  "event_queue": {"status": "stopped"}, "runtime": None, "reason": str(exc)}
                        store.append("health", key(health), timestamp, health)
            except sqlite3.Error as storage_error:
                log.error("Cannot persist failure: %s", storage_error)
        return 2
    finally:
        if store is not None:
            store.close()
