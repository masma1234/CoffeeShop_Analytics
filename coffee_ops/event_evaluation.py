"""Event-only scoring with one-to-one scope matching and annotated exposure."""
from __future__ import annotations

from collections import Counter, defaultdict
import math
import numpy as np
from scipy.optimize import linear_sum_assignment

ABSTENTIONS = {"uncertain", "unobservable", "abstained", "candidate"}
SCORED_STATUSES = {"observed", "confirmed", "review_required"}
SCOPE = ("camera_id", "kind", "product_class", "source_zone", "destination_zone", "line_id")


def finite(value, name, minimum=0):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<minimum:
        raise ValueError(f"Invalid {name}")
    return float(value)


def validate_annotation_metadata(truth):
    """Critical v1 metadata checks; legacy frame-evaluation documents remain readable."""
    if truth.get("annotation_status","reviewed")!="reviewed":
        raise ValueError("Unreviewed label templates are not ground truth")
    if "schema_version" not in truth:
        return
    if type(truth["schema_version"]) is not int or truth["schema_version"] != 1:
        raise ValueError("Unsupported event annotation schema")
    for field in ["clip_id","camera_id","recording_group","annotation_version","time_origin_utc"]:
        if not isinstance(truth.get(field),str) or not truth[field].strip():
            raise ValueError(f"Missing annotation metadata: {field}")
    from .schema import utc
    utc(truth["time_origin_utc"])
    if "duration_seconds" not in truth:
        raise ValueError("Versioned annotations require duration_seconds")
    kinds=truth.get("scored_event_kinds")
    if not isinstance(kinds,list) or not kinds or any(not isinstance(k,str) or not k for k in kinds) or len(set(kinds))!=len(kinds):
        raise ValueError("Versioned annotations require unique scored_event_kinds")
    if not isinstance(truth.get("events"),list) or any(
        not isinstance(e,dict) or not {"kind","seconds","status"}<=e.keys() for e in truth["events"]):
        raise ValueError("Versioned event rows require kind, seconds and status")


def evaluate_events(truth: dict, predictions: dict) -> dict:
    validate_annotation_metadata(truth)
    if "schema_version" in predictions:
        validate_annotation_metadata(predictions)
        for field in ["clip_id","camera_id","recording_group","time_origin_utc","duration_seconds"]:
            if field in truth and truth[field]!=predictions[field]:
                raise ValueError("Annotation comparison requires the same clip, camera and time origin")
    if "events" not in truth:
        raise ValueError("Event annotations required; an empty list means verified zero events")
    raw_lists=[truth["events"],predictions.get("events",[])]
    if any(not isinstance(items,list) for items in raw_lists): raise ValueError("Events must be lists")
    cameras={c for c in [truth.get("camera_id"),predictions.get("camera_id")]+[
        e.get("camera_id") for items in raw_lists for e in items if isinstance(e,dict)] if c is not None}
    default_camera=truth.get("camera_id") or (next(iter(cameras)) if len(cameras)==1 else None)
    if len(cameras)>1 and any(e.get("camera_id") is None for items in raw_lists for e in items):
        raise ValueError("Missing camera identity is ambiguous in a multi-camera evaluation")
    tolerance_default=finite(truth.get("event_tolerance_seconds",1),"event tolerance")
    tolerances={k:finite(v,"event tolerance") for k,v in truth.get("event_tolerances_seconds",{}).items()}
    duration=truth.get("duration_seconds")
    if duration is not None: duration=finite(duration,"annotated duration",.000001)
    ignored: list[tuple[float, float]] = []
    for interval in truth.get("unscored_intervals",[]):
        a,b=finite(interval["start_seconds"],"interval start"),finite(interval["end_seconds"],"interval end")
        if duration is None or b<=a or b>duration or ignored and a<ignored[-1][1]:
            raise ValueError("Unscored intervals require duration, sorted disjoint bounds")
        ignored.append((a,b))
    exposure=duration-sum(b-a for a,b in ignored) if duration is not None else None
    excluded: Counter[str] = Counter()

    def read(items,name):
        if not isinstance(items,list) or len(items)>10000:
            raise ValueError("Expected at most 10000 events per clip")
        result=[]
        for item in items:
            event=dict(item)
            seconds=finite(event["seconds"],"event timestamp")
            if not isinstance(event.get("kind"),str) or not event["kind"]:
                raise ValueError("Event kind required")
            if truth.get("scored_event_kinds") and event["kind"] not in truth["scored_event_kinds"]:
                excluded[name+"_outside_task"]+=1
                continue
            if duration is not None and seconds>=duration: raise ValueError("Event outside half-open clip")
            if finite(event.get("confidence",1),"confidence")>1: raise ValueError("Confidence exceeds one")
            status=event.get("status","observed")
            if status not in ABSTENTIONS|SCORED_STATUSES: raise ValueError("Unsupported evidence status")
            event["camera_id"]=event.get("camera_id",default_camera)
            if truth.get("camera_id") is not None and event["camera_id"]!=truth["camera_id"]:
                raise ValueError("Use a separate annotated clip for each camera")
            if any(a<=seconds<b for a,b in ignored): excluded[name+"_unscored"]+=1
            elif status in ABSTENTIONS:
                if name=="truth":raise ValueError("Uncertain ground truth requires an unscored interval")
                excluded[name+"_abstained"]+=1
            else: result.append(event)
        return result

    gt,pred=read(truth["events"],"truth"),read(predictions.get("events",[]),"predictions")
    groups: defaultdict[tuple, list[list[int]]] = defaultdict(lambda:[[],[]])
    for which,items in enumerate([gt,pred]):
        for i,event in enumerate(items):
            scope=tuple(event.get(k) for k in SCOPE)
            if any(v is not None and not isinstance(v,str) for v in scope): raise ValueError("Invalid scope value")
            groups[scope][which].append(i)
    pairs: list[tuple[int, int]] = []
    for scope,(gi,pi) in groups.items():
        if len(gi)*len(pi)>2_000_000: raise ValueError("Match capacity exceeded; split independent clips")
        costs=np.full((len(gi),len(pi)),1e9)
        tolerance=tolerances.get(scope[1],tolerance_default)
        for i,a in enumerate(gi):
            for j,b in enumerate(pi):
                delta=abs(gt[a]["seconds"]-pred[b]["seconds"])
                if delta<=tolerance: costs[i,j]=delta/max(1,tolerance)
        rows,cols=linear_sum_assignment(costs)
        pairs.extend((gi[int(i)],pi[int(j)]) for i,j in zip(rows,cols) if costs[i,j]<1e9)

    def summary(g,p,tp):
        fp,fn=p-tp,g-tp
        hours=exposure/3600 if exposure else None
        return {"tp":tp,"fp":fp,"fn":fn,"event_precision":tp/p if p else None,
            "event_recall":tp/g if g else None,"event_f1":2*tp/(g+p) if g+p else None,
            "absolute_error":abs(p-g),"signed_count_bias":p-g,
            "percentage_error":100*abs(p-g)/g if g else None,
            "overcount_rate":max(0,p-g)/g if g else None,"undercount_rate":max(0,g-p)/g if g else None,
            "false_events_per_hour":fp/hours if hours else None,"missed_events_per_hour":fn/hours if hours else None}

    result=summary(len(gt),len(pred),len(pairs))
    result["per_class"]={kind:summary(sum(e["kind"]==kind for e in gt),sum(e["kind"]==kind for e in pred),
        sum(gt[i]["kind"]==kind for i,j in pairs)) for kind in sorted({e["kind"] for e in gt+pred})}
    errors=[abs(gt[i]["seconds"]-pred[j]["seconds"]) for i,j in pairs]
    ids=[e["event_id"] for e in pred if "event_id" in e]
    result.update(timestamp_mae_seconds=float(np.mean(errors)) if errors else None,
        matched_events=[{"truth":gt[i],"prediction":pred[j],"timestamp_error_seconds":abs(gt[i]["seconds"]-pred[j]["seconds"])} for i,j in pairs],
        missed_events=[e for i,e in enumerate(gt) if i not in {a for a,b in pairs}],
        false_events=[e for j,e in enumerate(pred) if j not in {b for a,b in pairs}],
        duplicate_event_rate=(len(ids)-len(set(ids)))/len(ids) if ids else None,
        annotated_exposure_seconds=exposure,excluded=dict(excluded),
        abstention_rate=excluded["predictions_abstained"]/len(predictions.get("events",[])) if predictions.get("events") else None,
        matching_policy="scope-exact maximum-cardinality assignment, then minimum timestamp error",
        provenance=truth.get("provenance",{"kind":"unspecified_not_promotable"}),
        uncertainty="No population confidence interval inferred from one clip.")
    return result
