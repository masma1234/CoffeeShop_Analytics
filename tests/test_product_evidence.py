"""Narrow observable semantics; hidden or initially present cups are not prepared drinks."""
import copy
from dataclasses import replace
from pathlib import Path
import unittest

from coffee_ops.config import Config
from coffee_ops.event_engine import EventEngine
from coffee_ops.schema import Observation

ROOT=Path(__file__).resolve().parents[1]


def evidence_config():
    original=Config.load(ROOT/"config/example.json");data=copy.deepcopy(original.data)
    for z in data["cameras"][0]["zones"]:
        if z["id"]=="shelf":z["kind"]="preparation"
        elif z["id"]=="counter":z["kind"]="pickup"
    data["rules"]["movement_seconds"]=.2
    data["rules"]["product_evidence"]={"interaction_distance_pixels":200,"movement_pixels":3,
        "minimum_interaction_seconds":.2,"max_gap_seconds":.5}
    result=Config(data,original.root);result.validate();return result


def observation(x,ts,kind=1,tid=1):
    return Observation(tid,kind,(x-5,170,x+5,190),.95,0,ts,3,False,1)


class ProductEvidenceTests(unittest.TestCase):
    def run_stream(self,points,with_person=True):
        engine=EventEngine(evidence_config(),"shop","products");events=[]
        for i,x in enumerate(points):
            ts=i*.3;tracks=[observation(x,ts)]
            if with_person:tracks.append(observation(150,ts,0,2))
            e,_=engine.update(tracks,ts,i);events.extend(e)
        return events

    def test_initial_presence_is_not_placement_preparation_or_handover(self):
        events=self.run_stream([120]*10)
        kinds=[e["kind"] for e in events]
        self.assertEqual(kinds.count("product_visible"),1)
        self.assertEqual(kinds.count("product_present_at_pickup"),1)
        self.assertNotIn("item_placed_at_pickup",kinds)
        self.assertNotIn("preparation_completed",kinds)
        self.assertNotIn("handover",kinds)

    def test_visible_entry_departure_and_candidate_have_separate_events(self):
        events=self.run_stream([20,20,120,120,210,210])
        kinds=[e["kind"] for e in events]
        self.assertEqual(kinds.count("item_placed_at_pickup"),1)
        self.assertEqual(kinds.count("item_left_pickup"),1)
        candidate=next(e for e in events if e["kind"]=="candidate_handover")
        self.assertEqual(candidate["status"],"candidate")
        self.assertEqual(candidate["role"],"unknown")
        self.assertTrue(any(e["kind"]=="preparation_completion_unobservable" for e in events))
        self.assertFalse(any(e["kind"] in {"preparation_completed","handover","customer_pickup"} for e in events))

    def test_placement_needs_no_person_but_handover_candidate_needs_interaction(self):
        events=self.run_stream([20,20,120,120,210,210],with_person=False)
        self.assertEqual(sum(e["kind"]=="item_placed_at_pickup" for e in events),1)
        self.assertFalse(any(e["kind"]=="candidate_handover" for e in events))

    def test_occlusion_reappearance_does_not_establish_a_new_placement(self):
        engine=EventEngine(evidence_config(),"shop","occlusion");events=[]
        for i,(x,missed) in enumerate([(20,False),(20,False),(20,True),(120,False),(120,False)]):
            ts=i*.3;t=replace(observation(x,ts),missed=missed)
            e,_=engine.update([t],ts,i);events.extend(e)
        self.assertFalse(any(e["kind"]=="item_placed_at_pickup" for e in events))
        self.assertEqual(sum(e["kind"]=="unknown_product_state" for e in events),1)

    def test_unreliable_gap_cannot_confirm_pickup_departure_or_transfer(self):
        engine=EventEngine(evidence_config(),"shop","gap");events=[]
        for i,(x,reliable) in enumerate([(120,True),(120,True),(160,False),(210,True),(210,True)]):
            ts=i*.3;e,_=engine.update([observation(x,ts),observation(150,ts,0,2)],ts,i,reliable);events.extend(e)
        self.assertFalse(any(e["kind"] in {"candidate_handover","item_left_pickup"} for e in events))

    def test_repeat_stream_has_stable_ids_and_no_frame_cooldown_duplicates(self):
        a=self.run_stream([20,20,120,120,120,120,210,210])
        b=self.run_stream([20,20,120,120,120,120,210,210])
        self.assertEqual(a,b)
        self.assertEqual(len({e["event_id"] for e in a}),len(a))
