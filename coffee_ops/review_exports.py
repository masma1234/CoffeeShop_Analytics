"""Streaming review artifacts; long videos do not require a full frame list in RAM."""
from __future__ import annotations
import json
from pathlib import Path
from .schema import key,utc


class DetectionJournal:
    def __init__(self,path,metadata):
        self.file=Path(path).open("x",encoding="utf-8");self.file.write('{"frames":[')
        self.first=True;self.metadata=metadata;self.closed=False

    def append(self,frame):
        if not self.first:self.file.write(",")
        self.file.write(json.dumps(frame,allow_nan=False));self.first=False

    def close(self,complete=False):
        if self.closed:return
        self.file.write('],"complete":'+json.dumps(complete))
        for k,v in self.metadata.items():self.file.write(","+json.dumps(k)+":"+json.dumps(v,allow_nan=False))
        self.file.write("}\n");self.file.close();self.closed=True


def event_rows(store,run_id,camera_id,start):
    for e in store.scan_run("events",run_id,camera_id):
        yield {**{k:v for k,v in e.items() if not k.startswith("_")},"seconds":(utc(e["timestamp"])-start).total_seconds()}


def frame_rows(store,run_id,camera_id,start):
    for obs in store.scan_run("observations",run_id,camera_id):
        occupancy=store.get("occupancy",obs["_id"])
        if occupancy is None:raise ValueError("Incomplete frame record")
        yield {"frame":occupancy["frame"],"seconds":(utc(obs["timestamp"])-start).total_seconds(),
            "detections":[{"class_id":t["class_id"],"bbox":t["bbox"],"confidence":t["confidence"],"track_id":t["track_id"]}
                          for t in obs["tracks"] if not t["missed"]],"tables":occupancy["tables"]}


def stream_json(path,metadata,arrays):
    with Path(path).open("x",encoding="utf-8") as f:
        f.write("{");first=True
        for k,v in metadata.items():
            if not first:f.write(",")
            f.write(json.dumps(k)+":"+json.dumps(v,allow_nan=False));first=False
        for k,iterator in arrays.items():
            if not first:f.write(",")
            f.write(json.dumps(k)+":[");initial=True
            for row in iterator:
                if not initial:f.write(",")
                f.write(json.dumps(row,allow_nan=False));initial=False
            f.write("]");first=False
        f.write("}\n")
