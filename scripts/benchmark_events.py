"""Controlled synthetic event/sampling benchmark; no model accuracy claims."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import platform
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from coffee_ops.config import Config
from coffee_ops.event_evaluation import evaluate_events
from coffee_ops.pipeline import Pipeline
from coffee_ops.schema import Detection,file_hash,utc
from coffee_ops.storage import SQLiteStore


def run_case(scenario,sample_every):
    base=Config.load(ROOT/"config/example.json")
    data=copy.deepcopy(base.data)
    data["cameras"][0]["crossing_lines"]=[{"id":"door","start":[50,120],"end":[270,120],
        "inside_side":"positive","anchor":"center","hysteresis_pixels":5,
        "dwell_seconds":.2,"max_gap_seconds":1}]
    cfg=Config(data,base.root);cfg.validate()
    start="2026-01-01T00:00:00Z";origin=utc(start)
    predictions=[]
    with tempfile.TemporaryDirectory() as temporary:
        store=SQLiteStore(Path(temporary)/"ops.db")
        try:
            pipeline=Pipeline(cfg,store,"shop","sampling",start,"synthetic-points",{"version":"fixture"})
            elapsed_start=time.perf_counter()
            for frame in range(60):
                if frame%sample_every:continue
                seconds=frame/10
                y=160 if 1.05<seconds<1.35 else 80
                if scenario=="standing":y=80
                elif scenario=="boundary_jitter" and seconds>=1:y=120+(-3 if frame%2 else 3)
                detections=[Detection(0,(155,y-10,165,y+10),.95)]
                if scenario=="simultaneous":detections.append(Detection(0,(185,y-10,195,y+10),.95))
                result=pipeline.process(frame,seconds,detections)
                predictions.extend({**e,"seconds":(utc(e["timestamp"])-origin).total_seconds()}
                    for e in result["events"] if e["kind"] in {"person_entered","person_exited"})
            elapsed=time.perf_counter()-elapsed_start
            health=pipeline.health("completed")
        finally:store.close()
    events=[]
    if scenario in {"short_visit","simultaneous"}:
        for _ in range(2 if scenario=="simultaneous" else 1):
            events.extend({"kind":kind,"seconds":seconds,"camera_id":"shop","line_id":"door",
                "product_class":"person","source_zone":None,"destination_zone":None}
                for kind,seconds in [("person_entered",1.05),("person_exited",1.35)])
    truth={"events":events,"duration_seconds":6,"event_tolerance_seconds":.11,
           "provenance":{"kind":"synthetic_logic_fixture"}}
    return {"scenario":scenario,"sample_every":sample_every,"source_fps":10,
            "processed_frames":health["processed_frames"],"elapsed_seconds":elapsed,
            "config_hash":cfg.digest,"runtime":health["runtime"],"events":evaluate_events(truth,{"events":predictions})}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--output",required=True)
    args=p.parse_args();output=Path(args.output)
    if output.exists():raise FileExistsError(output)
    results={"purpose":"synthetic_event_semantics_and_sampling_not_real_camera_accuracy",
        "environment":{"platform":platform.platform(),"python":platform.python_version()},
        "measurement_scope":"Fixture detections, tracker, events and SQLite commits; no model inference or video decoding",
        "source_sha256":{name:file_hash(str(ROOT/name)) for name in ["coffee_ops/traffic.py","coffee_ops/pipeline.py","coffee_ops/event_evaluation.py","scripts/benchmark_events.py"]},
        "experiments":[run_case(scenario,sampling) for scenario in ["short_visit","simultaneous","standing","boundary_jitter"] for sampling in [1,2,4]]}
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("x",encoding="utf-8") as f:json.dump(results,f,indent=2,allow_nan=False)
    print(json.dumps([{"scenario":r["scenario"],"sample_every":r["sample_every"],"tp":r["events"]["tp"],"fp":r["events"]["fp"],"fn":r["events"]["fn"]} for r in results["experiments"]]))


if __name__=="__main__":main()
