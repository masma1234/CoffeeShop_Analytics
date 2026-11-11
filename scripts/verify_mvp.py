"""Reproducible acceptance evidence. No weights or external camera required."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="New evidence directory; never overwritten")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    tests = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=root, text=True, capture_output=True, timeout=180)
    (output / "tests.txt").write_text(tests.stdout+tests.stderr, encoding="utf-8")
    if tests.returncode:
        print(tests.stderr)
        return tests.returncode
    commands = []
    with tempfile.TemporaryDirectory() as directory:
        work = Path(directory)
        base = [sys.executable, "-m", "coffee_ops", "--config", str(root / "config/example.json"), "--db", str(work / "ops.db")]
        def run(*arguments: str, expected: int = 0):
            result = subprocess.run(base+list(arguments), cwd=root, text=True, capture_output=True, timeout=120)
            commands.append({"arguments": [a.replace(str(work), "<temporary-workdir>") for a in arguments], "exit_code": result.returncode, "expected": expected})
            if result.returncode != expected:
                raise RuntimeError(result.stderr+result.stdout)
            return json.loads(result.stdout) if expected == 0 else result.stderr
        backend = run("doctor")
        demo = str(work / "demo")
        run("make-demo", "--directory", demo)
        run("import-pos", "--file", str(work / "demo/orders.json"))
        replay = ["replay", "--source", str(work / "demo/fixture.avi"), "--camera", "shop", "--run-id", "demo", "--start", "2026-01-01T09:00:00Z", "--fixture-detections", str(work / "demo/detections.json")]
        health = run(*replay)
        run("reconcile")
        report = run("report", "--date", "2026-01-01")
        prediction_path = work / "predictions.json"
        predictions = run("export-predictions", "--run-id", "demo", "--camera", "shop")
        prediction_path.write_text(json.dumps(predictions), encoding="utf-8")
        evaluation = run("evaluate", "--truth", str(work / "demo/ground-truth.json"), "--predictions", str(prediction_path))
        run(*replay)
        run("reconcile")
        repeated_report = run("report", "--date", "2026-01-01")
        if report != repeated_report:
            raise AssertionError("Repeated replay changed daily business totals")
        run("replay", "--source", str(work / "demo/fixture.avi"), "--camera", "shop", "--run-id", "weights-missing", "--start", "2026-01-01T09:00:00Z", expected=2)
        run("import-pos", "--file", str(work / "missing.csv"), expected=2)
        for name, value in (("fixture-evaluation.json", evaluation), ("daily-report.json", report), ("runtime.json", health)):
            (output / name).write_text(json.dumps(value, indent=2), encoding="utf-8")
        # Exercise the new directional/report/review commands through the public CLI.
        import cv2
        import numpy as np
        cfg=json.loads((root/"config/example.json").read_text())
        cfg["cameras"][0]["motion_threshold"]=1
        cfg["cameras"][0]["crossing_lines"]=[{"id":"door","start":[50,120],"end":[270,120],
            "inside_side":"positive","anchor":"center","hysteresis_pixels":5,"dwell_seconds":.2,"max_gap_seconds":1}]
        config_path=work/"traffic-config.json";config_path.write_text(json.dumps(cfg),encoding="utf-8")
        video_path=work/"traffic.avi"
        writer=cv2.VideoWriter(str(video_path),cv2.VideoWriter_fourcc(*"MJPG"),4,(320,240))
        if not writer.isOpened():raise OSError("MJPG writer unavailable")
        frames=[]
        try:
            for i,y in enumerate([80,80,80,160,160,160]):
                writer.write(np.zeros((240,320,3),np.uint8))
                frames.append({"frame":i,"detections":[{"class_id":0,"bbox":[155,y-10,165,y+10],"confidence":.95}]})
        finally:writer.release()
        fixture_path=work/"traffic-detections.json"
        fixture_path.write_text(json.dumps({"purpose":"pipeline_fixture_not_model_accuracy","frames":frames}),encoding="utf-8")
        base=[sys.executable,"-m","coffee_ops","--config",str(config_path),"--db",str(work/"traffic.db")]
        traffic_replay=["replay","--source",str(video_path),"--camera","shop","--run-id","traffic",
            "--start","2026-01-01T23:00:00Z","--fixture-detections",str(fixture_path)]
        run(*traffic_replay)
        local_args=["business-report","--date","2026-01-02","--timezone","Africa/Tunis","--camera","shop","--run-id","traffic"]
        local=run(*local_args)
        if local["traffic"]["person_entered"]!=1:raise AssertionError("CLI crossing count mismatch")
        all_events=run("export-predictions","--run-id","traffic","--camera","shop","--all-events")
        prediction_path=work/"traffic-predictions.json";prediction_path.write_text(json.dumps(all_events),encoding="utf-8")
        event_truth={"schema_version":1,"clip_id":"traffic","camera_id":"shop","recording_group":"fixture",
            "annotation_version":"1","time_origin_utc":"2026-01-01T23:00:00Z","duration_seconds":1.5,
            "scored_event_kinds":["person_entered","person_exited"],"event_tolerance_seconds":.01,
            "provenance":{"kind":"synthetic_logic_fixture"},"events":[{"kind":"person_entered",
            "seconds":.625,"line_id":"door","product_class":"person","status":"observed"}]}
        truth_path=work/"traffic-truth.json";truth_path.write_text(json.dumps(event_truth),encoding="utf-8")
        event_score=run("evaluate-events","--truth",str(truth_path),"--predictions",str(prediction_path))
        if (event_score["tp"],event_score["fp"],event_score["fn"])!=(1,0,0):raise AssertionError("CLI event score mismatch")
        eid=next(e["event_id"] for e in all_events["events"] if e["kind"]=="person_entered")
        review=run("review-crossing","--event-id",eid,"--decision","rejected","--note","Synthetic review workflow check")
        corrected=run(*local_args)
        run(*traffic_replay)
        if corrected!=run(*local_args) or corrected["traffic"]["person_entered"]!=0:
            raise AssertionError("Traffic correction/replay changed corrected totals")
        (output/"traffic-workflow.json").write_text(json.dumps({"fixture_only":True,"before_review":local,
            "after_review":corrected,"event_evaluation":event_score,"review_revision":review["revision"],
            "repeated_replay_identical":True},indent=2),encoding="utf-8")
    evidence = {"test_exit_code": tests.returncode, "commands": commands,
                "repeated_replay_identical_daily_report": True, "backend": backend,
                "environment": {"python": platform.python_version(), "platform": platform.platform(),
                    "packages": {p: importlib.metadata.version(p) for p in ("ultralytics", "opencv-python", "numpy", "scipy", "PyYAML", "psutil", "torch", "torchvision")}},
                "verified": ["unit/integration/failure/concurrency rules", "actual CPU model adapter with untrained test weights", "MJPG video replay with explicit fixture detections", "POS reconciliation", "persistent daily aggregates", "repeat replay idempotence", "failure exit codes"],
                "unverified": ["real trained-model accuracy", "real CPU model inference throughput", "live cameras/RTSP", "GPU acceleration", "long-duration deployment"]}
    (output / "acceptance.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps({"passed": True, "evidence_directory": str(output), "fixture_only": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
