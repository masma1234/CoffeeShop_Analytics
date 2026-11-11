"""Observable pickup transitions and advisory interaction candidates, never sales."""
from __future__ import annotations

from dataclasses import dataclass,field
from datetime import datetime,timezone
import math

from .schema import Observation,key,stamp
from .zones import contains


@dataclass
class ProductState:
    observation: Observation
    seen: float
    outside_pickup: set = field(default_factory=set)
    inside_pickup: set = field(default_factory=set)
    person: int | None = None
    interaction_since: float | None = None
    motion: float = 0
    handled_reported: bool = False
    lost_reported: bool = False


class ProductEvidenceEngine:
    def __init__(self,config,camera_id,run_id):
        self.config,self.camera_id,self.run_id=config,camera_id,run_id
        self.parameters=config.data["rules"].get("product_evidence")
        self.zones={z["id"]:z for z in config.camera(camera_id)["zones"]}
        self.states={}

    def reset(self):self.states.clear()

    def event(self,kind,track,ts,frame,status="observed",source=None,destination=None,**facts):
        timestamp=stamp(datetime.fromtimestamp(ts,timezone.utc))
        return {"event_id":key(self.run_id,self.camera_id,frame,kind,track.track_id,source,destination),
            "schema_version":1,"kind":kind,"timestamp":timestamp,"camera_id":self.camera_id,"run_id":self.run_id,
            "track_id":track.track_id,"product_class":self.config.catalog[track.class_id]["name"],
            "source_zone":source,"destination_zone":destination,"status":status,"role":"unknown",
            "confidence":track.confidence,"evidence":{"frame":frame,"run_id":self.run_id,"timestamp":timestamp,
                "facts":facts,"confidence_notice":"Detector confidence/heuristic evidence, not calibrated action probability"}}

    def update(self,tracks,zone_tracks,movements,ts,frame,reliable):
        if not self.parameters:return []
        if not reliable:self.reset();return []
        p=self.parameters
        products={t.track_id:t for t in tracks if not t.missed and self.config.catalog[t.class_id]["kind"]=="product"}
        people=[t for t in tracks if not t.missed and self.config.catalog[t.class_id]["kind"]=="person"]
        output=[]
        for tid,track in products.items():
            state=self.states.get(tid)
            if state is None:
                state=ProductState(track,ts);self.states[tid]=state
                output.append(self.event("product_visible",track,ts,frame,
                    definition="Confirmed visibility episode; not a distinct physical or prepared item"))
            gap=ts-state.seen
            nearest=min(people,key=lambda t:math.dist(t.center,track.center),default=None)
            near=nearest is not None and math.dist(nearest.center,track.center)<=p["interaction_distance_pixels"]
            if gap>p["max_gap_seconds"] or not near or state.lost_reported:
                state.person=None;state.interaction_since=None;state.motion=0;state.handled_reported=False
            if gap>p["max_gap_seconds"] or state.lost_reported:
                state.outside_pickup.clear();state.inside_pickup.clear()
            if near:
                if state.person!=nearest.track_id:
                    state.person=nearest.track_id;state.interaction_since=ts;state.motion=0;state.handled_reported=False
                else:state.motion+=math.dist(state.observation.center,track.center)
                duration=ts-state.interaction_since
                if duration>=p["minimum_interaction_seconds"] and state.motion>=p["movement_pixels"] and not state.handled_reported:
                    output.append(self.event("product_handled_candidate",track,ts,frame,"candidate",
                        person_track_id=state.person,interaction_seconds=duration,observed_motion_pixels=state.motion,
                        limitation="Proximity and movement cannot establish hands, role or transaction"))
                    state.handled_reported=True
            for zone in self.zones.values():
                if zone["kind"]=="pickup":
                    if contains(zone["polygon"],track.center):state.inside_pickup.add(zone["id"])
                    else:state.outside_pickup.add(zone["id"])
            state.observation,state.seen,state.lost_reported=track,ts,False
        for movement in movements:
            if movement["kind"] not in {"placed","transferred","removed"}:continue
            tid=movement["track_id"];state=self.states.get(tid);track=products.get(tid)
            if state is None or track is None:continue
            source,dest=movement.get("source_zone"),movement.get("destination_zone")
            source_kind=self.zones.get(source,{}).get("kind");dest_kind=self.zones.get(dest,{}).get("kind")
            if dest_kind=="pickup":
                kind="item_placed_at_pickup" if dest in state.outside_pickup else "product_present_at_pickup"
                output.append(self.event(kind,track,ts,frame,source=source,destination=dest,
                    observed_outside_before_entry=dest in state.outside_pickup))
            if dest_kind=="preparation":
                output.append(self.event("preparation_completion_unobservable",track,ts,frame,"uncertain",source,dest,
                    reason="Container presence at preparation region is not visible completion evidence"))
            if source_kind=="pickup" and source in state.inside_pickup:
                output.append(self.event("item_left_pickup",track,ts,frame,source=source,destination=dest,
                    definition="Observed zone departure, recipient role and handover unknown"))
                if state.person is not None and state.interaction_since is not None and ts-state.interaction_since>=p["minimum_interaction_seconds"]:
                    output.append(self.event("candidate_handover",track,ts,frame,"candidate",source,dest,
                        person_track_id=state.person,interaction_seconds=ts-state.interaction_since,
                        limitation="Requires visible transfer review; no confirmed handover or customer role"))
        for tid,state in list(self.states.items()):
            if tid not in products and not state.lost_reported:
                output.append(self.event("unknown_product_state",state.observation,ts,frame,"uncertain",
                    reason="Track not currently observed; disappearance is not handover"))
                state.lost_reported=True
            if ts-state.seen>self.config.data["rules"]["disappear_seconds"]:del self.states[tid]
        return output
