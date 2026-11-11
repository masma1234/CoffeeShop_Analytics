"""Review overlays distinguish current detections, lost tracks and event evidence."""
from __future__ import annotations
import cv2
import numpy as np
from .tracker import iou


def render(image,config,camera_id,index,seconds,result,detections,sampled,events):
    canvas=image.copy();camera=config.camera(camera_id)
    scale=max(.4,min(1.,canvas.shape[1]/1000));font=cv2.FONT_HERSHEY_SIMPLEX
    def text(message,xy,color=(255,255,255)):
        cv2.putText(canvas,str(message),xy,font,scale,(0,0,0),3,cv2.LINE_AA)
        cv2.putText(canvas,str(message),xy,font,scale,color,1,cv2.LINE_AA)
    for zone in camera["zones"]:
        color=(0,220,255) if zone["kind"]=="preparation" else (255,150,0) if zone["kind"]=="pickup" else (180,150,180)
        points=np.array(zone["polygon"],dtype=np.int32)
        cv2.polylines(canvas,[points],True,color,2)
        text(f"{zone['id']} ({zone['kind']})",tuple(points[0]),color)
    for line in camera.get("crossing_lines",[]):
        cv2.line(canvas,tuple(map(round,line["start"])),tuple(map(round,line["end"])),(255,255,0),2)
        text(f"{line['id']} inside:{line['inside_side']}",tuple(map(round,line["start"])),(255,255,0))
    if sampled:
        for d in detections:
            if any(not t["missed"] and t["class_id"]==d.class_id and iou(tuple(t["bbox"]),d.bbox)>=.5 for t in result.get("tracks",[])):
                continue
            x1,y1,x2,y2=map(round,d.bbox)
            cv2.rectangle(canvas,(x1,y1),(x2,y2),(100,100,100),1)
            text(f"det {config.catalog[d.class_id]['name']} {d.confidence:.2f}",(x1,max(15,y1-3)),(160,160,160))
        for t in result.get("tracks",[]):
            x1,y1,x2,y2=map(round,t["bbox"]);lost=t["missed"]
            color=(100,100,255) if lost else (50,230,50)
            cv2.rectangle(canvas,(x1,y1),(x2,y2),color,2)
            tentative=t["hits"]<config.data["tracker"]["min_hits"]
            text(f"#{t['track_id']} {'LOST' if lost else '?' if tentative else ''} {config.catalog[t['class_id']]['name']} {t['confidence']:.2f}",(x1,min(canvas.shape[0]-5,y2+15)),color)
    text(f"frame {index} | source {seconds:.3f}s | {'SAMPLED' if sampled else 'NOT INFERRED - no current boxes'}",(8,20))
    y=42
    for table in result.get("tables",[]):
        text(f"{table['zone_id']}: {table['status']} people={table['people']}",(8,y));y+=20
    for event in events[-4:]:
        status=event["status"];color=(0,200,255) if status in {"candidate","uncertain","review_required"} else (100,255,100)
        text(f"{event['seconds']:.2f}s {event['kind']} [{status}] {event['confidence']:.2f}",(8,y),color);y+=20
    text("Presence/movement: preparation, handover and payment need separate evidence",(8,canvas.shape[0]-8),(0,220,255))
    return canvas
