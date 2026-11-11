"""Directional geometry, continuity, replay and source-secret regression tests."""
import copy
from dataclasses import replace
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from coffee_ops.config import Config
from coffee_ops.pipeline import Pipeline
from coffee_ops.runtime import replay
from coffee_ops.schema import Detection, Observation, key, utc
from coffee_ops.storage import SQLiteStore
from coffee_ops.traffic import TrafficEngine

ROOT=Path(__file__).resolve().parents[1]


def traffic_config():
    cfg=Config.load(ROOT/"config/example.json")
    data=copy.deepcopy(cfg.data)
    data["cameras"][0]["crossing_lines"]=[{"id":"door","start":[50,120],"end":[270,120],
        "inside_side":"positive","anchor":"center","hysteresis_pixels":5,
        "dwell_seconds":.2,"max_gap_seconds":1}]
    cfg=Config(data,cfg.root);cfg.validate()
    return cfg


def person(y,ts,tid=1,x=160):
    return Observation(tid,0,(x-5,y-10,x+5,y+10),.9,0,ts,3,False,1)


class TrafficTests(unittest.TestCase):
    def engine(self): return TrafficEngine(traffic_config(),"shop","test")

    def run_points(self,engine,points,start=0,tid=1,x=160):
        result=[]
        for i,y in enumerate(points):
            ts=start+i*.25
            result.extend(engine.update([person(y,ts,tid,x)],ts,round(ts*4)))
        return result

    def test_entry_return_direction_dwell_and_interpolated_capture_time(self):
        events=self.run_points(self.engine(),[80,80,160,160,80,80])
        self.assertEqual([e["kind"] for e in events],["person_entered","person_exited"])
        self.assertEqual(utc(events[0]["timestamp"]).timestamp(),.375)
        self.assertEqual(utc(events[0]["confirmed_at"]).timestamp(),.75)
        self.assertEqual(events[0]["role"],"unknown")
        self.assertNotEqual(events[0]["event_id"],events[1]["event_id"])

    def test_boundary_jitter_stationary_person_and_incomplete_dwell(self):
        self.assertEqual(self.run_points(self.engine(),[80,80,118,121,119,122,80,80]),[])
        self.assertEqual(self.run_points(self.engine(),[160]*20),[])
        self.assertEqual(self.run_points(self.engine(),[80,80,160,80,80]),[])

    def test_crossing_infinite_extension_is_not_door_crossing(self):
        self.assertEqual(self.run_points(self.engine(),[80,80,160,160],x=10),[])

    def test_missing_unreliable_long_gap_and_new_id_never_bridge(self):
        for mode in ["missing","missed","unreliable","gap","new_id"]:
            engine=self.engine();self.run_points(engine,[80,80])
            if mode=="missing":engine.update([],.5,2)
            elif mode=="missed":engine.update([replace(person(120,.5),missed=True)],.5,2)
            elif mode=="unreliable":engine.update([person(120,.5)],.5,2,False)
            start=2 if mode=="gap" else .75
            self.assertEqual(self.run_points(engine,[160,160],start,tid=2 if mode=="new_id" else 1),[],mode)

    def test_simultaneous_people_and_products_have_separate_semantics(self):
        engine=self.engine();events=[]
        for i,y in enumerate([80,80,160,160]):
            ts=i*.25
            observations=[person(y,ts,1,140),person(y,ts,2,180),replace(person(y,ts,3,200),class_id=1)]
            events.extend(engine.update(observations,ts,i))
        self.assertEqual(len(events),2)
        self.assertEqual({e["track_id"] for e in events},{1,2})

    def test_reverse_inside_side_and_invalid_geometry(self):
        cfg=traffic_config();cfg.camera("shop")["crossing_lines"][0]["inside_side"]="negative"
        events=self.run_points(TrafficEngine(cfg,"shop","run"),[80,80,160,160])
        self.assertEqual(events[0]["kind"],"person_exited")
        for field,value in [("end",[50,120]),("hysteresis_pixels",0),("dwell_seconds",float("nan")),
                            ("max_gap_seconds",True),("anchor","face"),("start",[-1,0])]:
            bad=traffic_config();bad.camera("shop")["crossing_lines"][0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):bad.validate()

    def test_expired_track_state_is_bounded(self):
        engine=self.engine()
        for i in range(2000):
            engine.update([person(80,float(i),i+1)],float(i),i)
            self.assertLessEqual(len(engine.states),1)

    def test_transaction_failure_requires_replay_and_replay_is_idempotent(self):
        cfg=traffic_config();cfg.data["tracker"]["min_hits"]=1
        with tempfile.TemporaryDirectory() as folder:
            store=SQLiteStore(Path(folder)/"ops.db")
            try:
                def pipeline():return Pipeline(cfg,store,"shop","crossing","2026-01-01T00:00:00Z","fixture",{"version":"fixture"})
                stream=[80,80,160,160]
                original=store.append
                pipe=pipeline()
                for i,y in enumerate(stream[:3]):pipe.process(i,i*.25,[Detection(0,(155,y-10,165,y+10),.9)])
                def failing(kind,*args):
                    if kind=="events":raise sqlite3.OperationalError("injected event write failure")
                    return original(kind,*args)
                with patch.object(store,"append",side_effect=failing),self.assertRaises(sqlite3.OperationalError):
                    pipe.process(3,.75,[Detection(0,(155,150,165,170),.9)])
                self.assertTrue(pipe.failed)
                for _ in range(2):
                    pipe=pipeline()
                    for i,y in enumerate(stream):pipe.process(i,i*.25,[Detection(0,(155,y-10,165,y+10),.9)])
                events=[e for e in store.scan("events") if e["kind"]=="person_entered"]
                self.assertEqual(len(events),1)
                health=pipe.health("completed")
                self.assertEqual(health["reliable_frames"],4)
                self.assertIn("events",health["runtime"]["stage_latency_ms"])
            finally:store.close()

    def test_live_source_url_credentials_are_not_persisted(self):
        class Detector:
            def detect(self,*args):return []
            def close(self):pass
        class Reader:
            dropped=type("Dropped",(),{"value":0})()
            def __init__(self,*args,**kwargs):pass
            def __iter__(self):yield 0,0.,np.zeros((240,320,3),dtype=np.uint8)
            def close(self):pass
        with tempfile.TemporaryDirectory() as folder:
            store=SQLiteStore(Path(folder)/"ops.db")
            try:
                with patch("coffee_ops.runtime.VideoInput",Reader):
                    replay(traffic_config(),store,Detector(),"rtsp://operator:secret@camera.local/feed",
                           "shop","live-secret","2026-01-01T00:00:00Z",{"version":"fixture"},live=True,max_frames=1)
                run=store.get("runs",key("live-secret","shop"))
                self.assertTrue(run["source_identity"].startswith("live:"))
                self.assertNotIn("secret",run["source_identity"])
                self.assertNotIn("rtsp",run["source_identity"])
            finally:store.close()
