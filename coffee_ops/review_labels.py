"""Evaluate reviewed YOLO frame labels using an explicit name-to-model-ID mapping."""
from __future__ import annotations
import json
import math
from pathlib import Path
from typing import Any

from .evaluation import evaluate,match
from .schema import Detection,file_hash


def evaluate_review_frames(directory,labels_directory,classes_file,labels_reviewed=False):
    if not labels_reviewed:raise ValueError("Review all target labels, then explicitly pass --labels-reviewed")
    import ijson
    root=Path(directory).resolve();labels=Path(labels_directory)
    manifest=json.loads((root/"annotation_frames.json").read_text(encoding="utf-8"))
    if not isinstance(manifest.get("source_sha256"),str) or not manifest["source_sha256"]:
        raise ValueError("Annotation manifest requires a source identity")
    rows=manifest["frames"]
    if not rows or len(rows)>100:raise ValueError("Expected 1..100 exported annotation frames")
    frame_ids=[row["frame"] for row in rows]
    if any(type(fid) is not int or fid<0 for fid in frame_ids) or len(set(frame_ids))!=len(frame_ids):
        raise ValueError("Annotation frame IDs must be unique nonnegative integers")
    if any(not isinstance(row["seconds"],(int,float)) or isinstance(row["seconds"],bool)
           or not math.isfinite(row["seconds"]) or row["seconds"]<0 for row in rows):
        raise ValueError("Annotation timestamps must be finite and nonnegative")
    if any(type(manifest[k]) is not int or manifest[k]<=0 for k in ("width","height")):
        raise ValueError("Annotation image dimensions must be positive integers")
    names=Path(classes_file).read_text(encoding="utf-8-sig").strip().splitlines()
    source={name:int(i) for i,name in manifest["source_classes"].items()}
    if len(source)!=len(manifest["source_classes"]):raise ValueError("Ambiguous source class names")
    if not names or len(names)!=len(set(names)) or any(name not in source for name in names):
        raise ValueError("Each annotation class must have an exact unique model class name; no silent renaming")
    mapping={i:source[n] for i,n in enumerate(names)};wanted=set(mapping.values())
    label_index: dict[str, list[Path]] = {}
    for path in labels.rglob("*.txt"):label_index.setdefault(path.stem,[]).append(path)
    truth: list[dict[str, Any]] = []
    width,height=manifest["width"],manifest["height"]
    for row in rows:
        image=(root/row["image"]).resolve()
        if not image.is_relative_to(root):raise ValueError("Annotation image must stay inside review directory")
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
    expected_times={row["frame"]:row["seconds"] for row in rows}
    # Stream metadata too: loading the whole journal would defeat bounded video exports.
    with (root/"detections.json").open("rb") as f:
        metadata={}
        for prefix,event,value in ijson.parse(f):
            if prefix in {"complete","source_identity"} and event in {"boolean","string","null","number"}:
                if prefix in metadata:raise ValueError("Duplicate detection journal metadata")
                metadata[prefix]=value
        if metadata.get("complete") is not True:raise ValueError("Detection journal must be complete")
        if metadata.get("source_identity")!=manifest["source_sha256"]:
            raise ValueError("Detection journal belongs to a different source")
    with (root/"detections.json").open("rb") as f:
        selected_ids=set()
        for frame in ijson.items(f,"frames.item"):
            fid=frame["frame"]
            if type(fid) is not int or fid<0:raise ValueError("Invalid detection frame ID")
            if fid not in ids:continue
            if fid in selected_ids:raise ValueError("Duplicate detection frame ID")
            selected_ids.add(fid)
            if not math.isfinite(float(frame["seconds"])) or abs(float(frame["seconds"])-expected_times[fid])>1e-6:
                raise ValueError("Detection timestamp differs from annotation manifest")
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
