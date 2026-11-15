"""Evaluate reviewed YOLO frame labels using an explicit name-to-model-ID mapping."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

from .evaluation import evaluate,match
from .schema import Detection,file_hash


def evaluate_review_frames(directory,labels_directory,classes_file,labels_reviewed=False):
    if not labels_reviewed:raise ValueError("Review all target labels, then explicitly pass --labels-reviewed")
    import ijson
    root=Path(directory).resolve();labels=Path(labels_directory)
    manifest=json.loads((root/"annotation_frames.json").read_text(encoding="utf-8"))
    rows=manifest["frames"]
    if not rows or len(rows)>100:raise ValueError("Expected 1..100 exported annotation frames")
    names=Path(classes_file).read_text(encoding="utf-8-sig").strip().splitlines()
    source={name:int(i) for i,name in manifest["source_classes"].items()}
    if not names or len(names)!=len(set(names)) or any(name not in source for name in names):
        raise ValueError("Each annotation class must have an exact unique model class name; no silent renaming")
    mapping={i:source[n] for i,n in enumerate(names)};wanted=set(mapping.values())
    label_index: dict[str, list[Path]] = {}
    for path in labels.rglob("*.txt"):label_index.setdefault(path.stem,[]).append(path)
    truth: list[dict[str, Any]] = []
    width,height=manifest["width"],manifest["height"]
    for row in rows:
        image=root/row["image"]
        if file_hash(str(image))!=row["image_sha256"]:raise ValueError("Exported annotation image changed")
        candidates=label_index.get(image.stem,[])
        if len(candidates)!=1:raise ValueError(f"Missing/ambiguous label for {image.name}; empty TXT must be an explicitly reviewed negative")
        detections=[]
        for line in candidates[0].read_text(encoding="utf-8-sig").strip().splitlines():
            parts=line.split()
            if len(parts)!=5:raise ValueError("Expected YOLO detection TXT rows")
            cid_float,cx,cy,w,h=map(float,parts);cid=int(cid_float)
            if cid!=cid_float or cid not in mapping:raise ValueError("Unknown annotation class ID")
            box=((cx-w/2)*width,(cy-h/2)*height,(cx+w/2)*width,(cy+h/2)*height)
            d=Detection(mapping[cid],box,1.)
            if box[2]>width or box[3]>height:raise ValueError("YOLO label outside image geometry")
            detections.append({"class_id":d.class_id,"bbox":list(d.bbox),"confidence":1.})
        truth.append({"frame":row["frame"],"seconds":row["seconds"],"detections":detections})
    ids={r["frame"] for r in truth}
    raw: list[dict[str, Any]] = []
    operating: list[dict[str, Any]] = []
    with (root/"detections.json").open("rb") as f:
        for frame in ijson.items(f,"frames.item"):
            if int(frame["frame"]) not in ids:continue
            items=[{"class_id":int(d["class_id"]),"bbox":list(map(float,d["bbox"])),"confidence":float(d["confidence"])}
                   for d in frame["detections"] if int(d["class_id"]) in wanted]
            base={"frame":int(frame["frame"]),"seconds":float(frame["seconds"])}
            raw.append({**base,"detections":items})
            operating.append({**base,"detections":[d for d in items if d["confidence"]>=manifest["thresholds"][str(d["class_id"])]]})
    truth_document={"frames":truth,"provenance":{"kind":"human_frame_annotations_split_independence_unverified"}}
    raw_report=evaluate(truth_document,{"frames":raw})
    operating_report=evaluate(truth_document,{"frames":operating})
    by_frame={r["frame"]:r for r in operating}
    errors: list[dict[str, Any]] = []
    for expected in truth:
        predicted=by_frame[expected["frame"]]["detections"];ground=expected["detections"]
        pairs=match(ground,predicted);good_gt={i for i,j in pairs};good_pred={j for i,j in pairs}
        for category,items,matched in [("detector_miss",ground,good_gt),("detector_false_positive",predicted,good_pred)]:
            errors.extend({"cause":category,"frame":expected["frame"],"seconds":expected["seconds"],"detection":d,
                "evidence":"Compared with explicitly reviewed complete target labels at IoU 0.5"} for i,d in enumerate(items) if i not in matched)
    return {"source_sha256":manifest["source_sha256"],"annotated_frames":len(truth),"scored_classes":names,
        "annotation_to_model_ids":mapping,"operating_point_detection":operating_report["detection"],
        "raw_proposal_AP":raw_report["detection"],"errors":errors,
        "limitations":["Detection-only evaluation of exported sampled frames; no event or tracking accuracy implied",
            "Recording group must stay in one split; this evaluation does not certify independent holdout selection",
            "No automatic training recommendation; review failure evidence and annotation completeness first"]}
