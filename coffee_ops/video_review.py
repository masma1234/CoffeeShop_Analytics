"""Inspectable local-video prototype using existing tracker, events and ledger."""
from __future__ import annotations

from collections import Counter,deque
import copy
import csv
from dataclasses import asdict
from datetime import timedelta
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import time

from .config import Config,number
from .detector import FixtureDetector,YOLODetector
from .pipeline import Pipeline
from .resources import ResourceMonitor
from .review_exports import DetectionJournal,event_rows,frame_rows,stream_json
from .schema import file_hash,key,stamp,utc
from .storage import SQLiteStore
from .video_io import PTSVideoInput,PTSVideoWriter
from .video_overlay import render

ROOT=Path(__file__).resolve().parents[1]
REVISION="5650961749fa93567c0d46fc7f43ea4f9e914107"
FAILURE_CAUSES=["detector_miss","detector_false_positive","tracking_lost_or_switched","camera_occlusion",
    "incorrect_zone_geometry","incorrect_temporal_rule","event_deduplication_failure","genuinely_unobservable","annotation_ambiguity"]


def write_json(path,value):
    with Path(path).open("x",encoding="utf-8") as f:json.dump(value,f,indent=2,allow_nan=False)


def probe_video(source):
    if importlib.util.find_spec("av") is None:
        raise ImportError("Install requirements-video.txt in the isolated video/training environment (PyAV required)")
    reader=PTSVideoInput(source)
    try:
        first=next(iter(reader))
        return {**reader.metadata,"first_pts":first[1],"first_time_base":first[2],
            "timestamp_policy":"Exact original PTS retained in frame journal; capture offsets relative to first decoded PTS"}
    finally:reader.close()


def prepare_video(source,directory,model_directory=None,device="cpu"):
    destination=Path(directory).resolve()
    if destination.exists():raise FileExistsError("Choose a new video-configuration directory")
    model=Path(model_directory).resolve() if model_directory else ROOT/"var/model-benchmark/huggingface/hub/models--PekingU--rtdetr_v2_r18vd/snapshots"/REVISION
    if not all((model/f).is_file() for f in ["config.json","model.safetensors","preprocessor_config.json"]):
        raise FileNotFoundError("Local RT-DETR checkpoint missing. Supply --model-dir; no automatic model download. See docs/VIDEO_PROTOTYPE.md")
    source=Path(source).resolve();info=probe_video(source)
    model_config=json.loads((model/"config.json").read_text(encoding="utf-8"))
    if model_config.get("model_type")!="rt_detr_v2":raise ValueError("Expected exact RT-DETRv2 checkpoint")
    cfg=copy.deepcopy(Config.load(ROOT/"config/example.json").data)
    product_names={"cup","bottle","donut","cake"}
    cfg["classes"]=[{"id":int(i),"name":name,"kind":"person" if name=="person" else "product" if name in product_names else "other",
        "enabled":name=="person" or name in product_names,"threshold":.25} for i,name in sorted(model_config["id2label"].items(),key=lambda p:int(p[0]))]
    camera=cfg["cameras"][0];camera.update(id="video",width=info["width"],height=info["height"],zones=[],crossing_lines=[],thresholds={})
    digest=file_hash(str(model/"model.safetensors"));version="rtdetr-v2-"+digest[:12]
    cfg["model"].update(backend="rtdetr_v2",version=version,weights=str(model/"model.safetensors"),
        metadata=str(destination/"model_metadata.json"),checkpoint_directory=str(model),device=device,image_size=512,half=device.startswith("cuda"))
    cfg["pos"].update(mode="camera_only",sku_classes={})
    cfg["rules"]["authorized_product_zones"]={};cfg["rules"]["movement_seconds"]=.5;cfg["rules"]["low_confidence"]=.15
    cfg["rules"]["product_evidence"]={"interaction_distance_pixels":max(20,round(info["width"]*.12)),
        "movement_pixels":max(3,round(info["width"]*.006)),"minimum_interaction_seconds":.3,"max_gap_seconds":.5}
    cfg["evidence"]["capture"]=False;cfg["evidence"]["directory"]=str(destination/"evidence")
    cfg["storage"]["path"]=str(destination/"operations.sqlite3")
    Config(cfg,destination).validate()
    metadata={"version":version,"dataset_version":"pretrained-COCO; cafe accuracy unverified",
        "sha256":digest,"classes":model_config["id2label"],"backend":"rtdetr_v2",
        "checkpoint_files":{n:file_hash(str(model/n)) for n in ["config.json","preprocessor_config.json"]},
        "publisher":"PekingU/rtdetr_v2_r18vd" if model.name==REVISION else "user-supplied checkpoint",
        "revision":REVISION if model.name==REVISION else None,
        "license":"Apache-2.0 publisher model card" if model.name==REVISION else "User must verify supplied checkpoint terms",
        "license_source":"https://huggingface.co/PekingU/rtdetr_v2_r18vd",
        "notice":"Generic COCO classes; donuts/cakes do not cover every pastry or product"}
    destination.mkdir(parents=True,exist_ok=False)
    write_json(destination/"config.json",cfg);write_json(destination/"model_metadata.json",metadata)
    write_json(destination/"video_info.json",{**info,"source_sha256":file_hash(str(source)),"source_name":source.name,
        "calibration_status":"UNCONFIGURED: edit camera zones and crossing_lines; no invented scene geometry"})
    return {"config":str(destination/"config.json"),"model":metadata,"video":info,
        "next":"Edit zones/calibration, then annotate-video using the generated config"}


def review_video(config,source,directory,camera_id,run_id,start,*,database=None,sample_every=None,
                 max_frames=None,fixture=None,event_labels=None,export_frames_every=None):
    destination=Path(directory).resolve();source=Path(source).resolve();capture_start=utc(start)
    if destination.exists():raise FileExistsError("Output directory exists; preserve it and choose a new directory")
    camera=config.camera(camera_id);sampling=sample_every if sample_every is not None else camera["sample_every"]
    if type(sampling) is not int or sampling<1:raise ValueError("sample-every must be a positive integer")
    if max_frames is not None and (type(max_frames) is not int or max_frames<1):raise ValueError("max-frames must be positive")
    if export_frames_every is not None:number(export_frames_every,"frame export interval",.001)
    info=probe_video(source)
    if (info["width"],info["height"])!=(camera["width"],camera["height"]):raise ValueError("Video dimensions differ from calibration; prepare/recalibrate this video")
    identity=file_hash(str(source));source_stat=source.stat()
    labels_document=None
    if event_labels:
        from .event_evaluation import evaluate_events
        labels_path=Path(event_labels)
        if labels_path.stat().st_size>10_000_000:raise ValueError("Split annotation documents larger than 10 MB")
        labels_document=json.loads(labels_path.read_text(encoding="utf-8"))
        evaluate_events(labels_document,{"events":[]})  # Validate before loading a model or creating outputs.
        if labels_document.get("source_identity")!=identity:raise ValueError("Reviewed event labels must bind to this source_identity hash")
        if labels_document.get("camera_id")!=camera_id or utc(labels_document["time_origin_utc"])!=capture_start:
            raise ValueError("Event labels must use this camera and capture start")
    destination.mkdir(parents=True,exist_ok=False)
    write_json(destination/"run_manifest.json",{"source_sha256":identity,"source_name":source.name,"video":info,
        "camera_id":camera_id,"run_id":run_id,"capture_start":stamp(capture_start),"config_hash":config.digest,
        "config":config.data,"config_root":str(config.root),"sample_every":sampling,
        "scope":"synthetic fixture, not model accuracy" if fixture else "unlabeled local model inference unless independent labels supplied"})
    monitor=ResourceMonitor();monitor.start()
    store=reader=writer=detector=pipeline=raw_journal=None
    started=time.perf_counter();decoded=processed=0;last_offset=Fraction(0);recent=deque(maxlen=50)
    event_counts=Counter();timings=deque(maxlen=10000);exported=[];next_export=0.;sample_count=0;last_result={};complete=False;error=None
    try:
        store=SQLiteStore(database or config.path(config.data["storage"]["path"]))
        detector=FixtureDetector(fixture) if fixture else YOLODetector(config,camera_id)
        metadata=dict(detector.metadata)
        if fixture:metadata["fixture_sha256"]=file_hash(str(fixture))
        raw_journal=DetectionJournal(destination/"detections.json",{"model":metadata,"source_identity":identity,
            "scope":"Raw enabled-class detector proposals before tracker/class acceptance"})
        with store.camera_lease(camera_id,run_id,max(60,config.data["model"]["inference_timeout_seconds"]+30)) as owner:
            pipeline=Pipeline(config,store,camera_id,run_id,start,identity,metadata)
            pipeline.health("running")
            reader=PTSVideoInput(source)
            writer=PTSVideoWriter(destination/"annotated.mp4",camera["width"],camera["height"],info["rate"])
            with (destination/"frames.jsonl").open("x",encoding="utf-8") as journal:
                for index,pts,time_base,offset,image in reader:
                    frame_started=time.perf_counter();last_offset=offset;decoded+=1
                    store.renew_lease(camera_id,owner,max(60,config.data["model"]["inference_timeout_seconds"]+30))
                    sampled=index%sampling==0;detections=[];proposals=[]
                    if sampled:
                        detection_started=time.perf_counter();detections=detector.detect(image,index)
                        detector_ms=(time.perf_counter()-detection_started)*1000
                        proposals=getattr(detector,"last_raw_detections",detections)
                        last_result=pipeline.process(index,float(offset),detections,image=image)
                        pipeline.stage_latencies["detection"].append(detector_ms)
                        processed+=1
                        frame_record={"frame":index,"seconds":float(offset),"detections":[asdict(d) for d in proposals]}
                        raw_journal.append(frame_record)
                        for event in last_result["events"]:
                            exported_event={**event,"seconds":(utc(event["timestamp"])-capture_start).total_seconds()}
                            event_counts[event["kind"]]+=1;recent.append(exported_event)
                        while recent and float(offset)-recent[0]["seconds"]>5:recent.popleft()
                    canvas=render(image,config,camera_id,index,float(offset),last_result,detections,sampled,list(recent))
                    writer.write(canvas,offset)
                    elapsed_ms=(time.perf_counter()-frame_started)*1000;timings.append(elapsed_ms)
                    if sampled:pipeline.latencies[-1]=elapsed_ms
                    row={"frame":index,"source_pts":pts,"source_time_base":time_base,"seconds":float(offset),
                        "capture_timestamp":stamp(capture_start+timedelta(seconds=float(offset))),"sampled":sampled,
                        "raw_detections":[asdict(d) for d in proposals],"accepted_detections":[asdict(d) for d in detections],"tracks":last_result.get("tracks",[]) if sampled else [],
                        "events":[e["event_id"] for e in last_result.get("events",[])] if sampled else []}
                    journal.write(json.dumps(row,allow_nan=False)+"\n")
                    if export_frames_every is not None and sampled and float(offset)>=next_export and sample_count<100:
                        import cv2
                        frames_dir=destination/"annotation_frames";frames_dir.mkdir(exist_ok=True)
                        image_name=f"frame-{index:08d}.jpg"
                        if not cv2.imwrite(str(frames_dir/image_name),image):raise OSError("Annotation frame write failed")
                        exported.append({"image":"annotation_frames/"+image_name,"frame":index,"seconds":float(offset),
                            "recording_group":identity,"source_sha256":identity,"label_status":"unreviewed",
                            "image_sha256":file_hash(str(frames_dir/image_name))})
                        next_export=float(offset)+export_frames_every;sample_count+=1
                    if max_frames is not None and decoded>=max_frames:break
            writer.close();complete=True
            raw_journal.close(complete=True)
            health=pipeline.health("completed")
            with store.snapshot():
                stream_json(destination/"predictions.json",{"model":metadata,"camera_id":camera_id,"run_id":run_id,
                    "source_identity":identity,"runtime":health["runtime"]},
                    {"frames":frame_rows(store,run_id,camera_id,capture_start),"events":event_rows(store,run_id,camera_id,capture_start)})
                stream_json(destination/"events.json",{"camera_id":camera_id,"run_id":run_id,"source_identity":identity,"model":metadata},
                    {"events":event_rows(store,run_id,camera_id,capture_start)})
            with (destination/"events.csv").open("x",newline="",encoding="utf-8") as f:
                fields=["event_id","kind","status","timestamp","seconds","track_id","product_class","confidence","source_zone","destination_zone"]
                csv_writer=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");csv_writer.writeheader();csv_writer.writerows(event_rows(store,run_id,camera_id,capture_start))
            duration=(info.get("declared_duration_seconds") if max_frames is None else None) or float(last_offset+1/Fraction(info["rate"]))
            write_json(destination/"event_labels_template.json",{"schema_version":1,"annotation_status":"unreviewed",
                "clip_id":run_id,"camera_id":camera_id,"recording_group":identity,"annotation_version":"1",
                "time_origin_utc":stamp(capture_start),"source_identity":identity,"duration_seconds":duration,
                "scored_event_kinds":["preparation_completed","handover","customer_pickup","item_placed_at_pickup"],
                "event_tolerance_seconds":.5,"unscored_intervals":[],"events":None})
            write_json(destination/"annotation_frames.json",{"source_sha256":identity,"recording_group":identity,"frames":exported,
                "width":camera["width"],"height":camera["height"],"source_classes":{str(i):c["name"] for i,c in config.catalog.items()},
                "thresholds":{str(i):camera.get("thresholds",{}).get(str(i),c["threshold"]) for i,c in config.catalog.items()},
                "notice":"Annotate in CVAT/Label Studio; preserve source IDs/timestamps. No automatic ground truth."})
            with (destination/"annotation_classes.txt").open("x",encoding="utf-8") as f:
                f.write("\n".join(c["name"] for _,c in sorted(config.catalog.items()) if c["enabled"])+"\n")
            evaluation=None
            if event_labels:
                from .event_evaluation import evaluate_events
                truth=labels_document
                if truth.get("source_identity") not in {None,identity}:raise ValueError("Labels belong to a different source")
                if truth.get("duration_seconds",0)>duration+.001:raise ValueError("Labels extend beyond the processed clip; use labels for this exact interval")
                labeled_predictions=[]
                for event in event_rows(store,run_id,camera_id,capture_start):
                    if len(labeled_predictions)>=10000:raise ValueError("Split event evaluations into clips of at most 10000 events")
                    labeled_predictions.append(event)
                evaluation=evaluate_events(truth,{"events":labeled_predictions})
                write_json(destination/"event_evaluation.json",evaluation)
            errors=[]
            if evaluation:
                for category in ["missed_events","false_events"]:
                    for e in evaluation[category]:errors.append({"error":category,"event":e,"cause":"unclassified_needs_human_review",
                        "review_evidence":{"video":"annotated.mp4","seconds":e["seconds"],"frame_journal":"frames.jsonl"},"allowed_causes":FAILURE_CAUSES})
            write_json(destination/"error_report.json",{"status":"labeled_event_review" if evaluation else "awaiting_independent_labels",
                "errors":errors,"cause_taxonomy":FAILURE_CAUSES,"notice":"No automatic causal diagnosis or accuracy invented from unlabeled footage"})
            if source.stat().st_size!=source_stat.st_size or source.stat().st_mtime_ns!=source_stat.st_mtime_ns:raise ValueError("Source file changed during processing")
    except BaseException as exc:
        complete=False;error=f"{type(exc).__name__}: {exc}"
        if pipeline:
            try:pipeline.health("error",error,component="video_review")
            except Exception:pass
        raise
    finally:
        if reader:reader.close()
        if writer:writer.close(abort=not complete)
        if detector:detector.close()
        if raw_journal:raw_journal.close(complete=complete)
        resources=monitor.stop()
        if store:store.close()
        elapsed=time.perf_counter()-started
        counts=event_counts
        summary={"status":"completed" if complete else "failed","error":error,"fixture_only":bool(fixture),
            "decoded_frames":decoded,"inferred_frames":processed,"sample_every":sampling,"wall_seconds":elapsed,
            "processed_inference_fps":processed/elapsed if elapsed else None,"decoded_output_fps":decoded/elapsed if elapsed else None,
            "processed_media_span_seconds":float(last_offset),"source_video":info,"source_sha256":identity,
            "outputs_directory":str(destination),"database":str(database or config.path(config.data["storage"]["path"])),
            "event_counts_by_kind":dict(counts),"prepared_drinks":None,"confirmed_handovers":None,"customer_pickups":None,
            "semantic_notice":"Detector/zone motion supports visible transitions and advisory candidates, not validated preparation completion, transfer, customer role or paid sales.",
            "resources":resources,"model_worker_metrics":getattr(detector,"last_model_metrics",{}),
            "timestamp_notice":"Original PTS journal preserved. MP4 offsets quantized to 1/60000 second; audio omitted; odd dimensions padded at right/bottom.",
            "max_output_pts_rounding_error_seconds":writer.max_rounding_error if writer else None,
            "latency_scope":"Parent receipt through detector/tracker/storage/overlay/encoder enqueue; excludes asynchronous decode/mux completion. Total wall time includes worker load/flush.",
            "metric_availability":{"detection_AP":None,"tracking_IDF1":None,"table_accuracy":None,
                "event_accuracy":"event_evaluation.json" if event_labels and complete else None}}
        if timings:
            import numpy as np
            summary["frame_turnaround_ms"]={"p50":float(np.percentile(timings,50)),"p95":float(np.percentile(timings,95)),"p99":float(np.percentile(timings,99))}
        try:write_json(destination/"processing_summary.json",summary)
        except OSError:
            if complete:raise
    return summary
