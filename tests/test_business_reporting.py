"""Capture-time reports across DST, outages, revisions, and replay overlap."""
from datetime import timedelta
from pathlib import Path
import tempfile
import unittest

from coffee_ops.business_reporting import business_report,business_window
from coffee_ops.schema import key,stamp,utc
from coffee_ops.storage import SQLiteStore


class BusinessReportTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=SQLiteStore(Path(self.temp.name)/"ops.db");self.addCleanup(self.store.close)

    def event(self,identity,timestamp,kind="person_entered",camera="shop"):
        e={"event_id":identity,"timestamp":timestamp,"kind":kind,"camera_id":camera,"run_id":"r",
           "status":"observed","product_class":"person"}
        self.store.append("events",identity,timestamp,e)

    def sample(self,seconds,status,run="r",camera="shop"):
        ts=stamp(utc("2026-01-01T00:00:00Z")+timedelta(seconds=seconds))
        self.store.append("occupancy",f"{camera}-{run}-{seconds}",ts,{"timestamp":ts,"camera_id":camera,"run_id":run,
            "tables":[{"zone_id":"T1","status":status}]})

    def test_tunis_local_midnight_and_camera_isolation(self):
        self.event("before","2026-01-01T22:59:59Z")
        self.event("inside","2026-01-01T23:00:00Z")
        self.event("last","2026-01-02T22:59:59Z","person_exited")
        self.event("after","2026-01-02T23:00:00Z")
        self.event("other","2026-01-02T10:00:00Z",camera="other")
        report=business_report(self.store,"2026-01-02","Africa/Tunis",camera_id="shop")
        self.assertEqual(report["traffic"]["person_entered"],1)
        self.assertEqual(report["traffic"]["person_exited"],1)
        self.assertIsNone(report["traffic"]["in_store_occupancy_estimate"])
        self.assertEqual(report["hourly"][0]["person_entered"],1)
        self.assertEqual(report["hourly"][-1]["person_exited"],1)

    def test_dst_short_long_days_and_distinct_repeated_hour(self):
        short=business_report(self.store,"2026-03-08","America/New_York")
        long=business_report(self.store,"2026-11-01","America/New_York")
        self.assertEqual(len(short["hourly"]),23)
        self.assertEqual(len(long["hourly"]),25)
        repeated=[h["local_start"] for h in long["hourly"] if "T01:00:00" in h["local_start"]]
        self.assertEqual(len(set(repeated)),2)
        self.assertEqual(long["duration_seconds"],25*3600)

    def test_shifted_day_and_ambiguous_or_nonexistent_boundaries(self):
        start,end=business_window("2026-01-01","Africa/Tunis",4)
        self.assertEqual(stamp(start),"2026-01-01T03:00:00.000000Z")
        self.assertEqual((end-start).total_seconds(),86400)
        for day,hour in [("2026-03-08",2),("2026-11-01",1)]:
            with self.assertRaises(ValueError):business_window(day,"America/New_York",hour)
        with self.assertRaises(ValueError):business_window("2026-01-01","UTC",True)

    def test_occupancy_is_time_weighted_and_never_filled_across_long_gaps(self):
        for seconds,status in [(0,"occupied"),(1,"occupied"),(10,"empty"),(12,"unknown"),(20,"empty")]:
            self.sample(seconds,status)
        table=business_report(self.store,"2026-01-01")["tables"][0]
        self.assertEqual(table["occupied_seconds"],6)
        self.assertEqual(table["empty_seconds"],7)
        self.assertEqual(table["unknown_seconds"],5)
        self.assertEqual(table["unobserved_seconds"],86400-18)
        self.assertEqual(table["observed_occupied_to_empty_transitions"],0)

    def test_continuous_turnover_and_restart_have_different_meaning(self):
        self.sample(0,"occupied");self.sample(2,"empty")
        self.sample(4,"occupied",run="new");self.sample(6,"empty",run="new")
        table=business_report(self.store,"2026-01-01")["tables"][0]
        self.assertEqual(table["observed_occupied_to_empty_transitions"],2)

    def test_overlapping_replays_need_explicit_run_selection(self):
        for run in ["original","replay"]:
            self.sample(0,"occupied",run);self.sample(2,"empty",run)
        with self.assertRaisesRegex(ValueError,"Overlapping"):
            business_report(self.store,"2026-01-01")
        selected=business_report(self.store,"2026-01-01",run_id="original")
        self.assertEqual(selected["tables"][0]["occupied_seconds"],2)

    def test_latest_refund_revision_changes_pos_totals_without_video_sale_claim(self):
        order={"id":"line-1","revision":1,"timestamp":"2026-01-01T23:30:00Z","camera_id":"shop",
            "zone_id":"counter","product_class":"coffee_cup","payment_status":"paid","quantity":2,"sku":"COFFEE"}
        self.store.append("orders","order-rev1",order["timestamp"],order)
        self.assertEqual(business_report(self.store,"2026-01-02","Africa/Tunis")["confirmed_sold_units"],{"COFFEE":2})
        revised=dict(order,revision=2,payment_status="refunded")
        self.store.append("orders","order-rev2",order["timestamp"],revised)
        self.assertEqual(business_report(self.store,"2026-01-02","Africa/Tunis")["confirmed_sold_units"],{})

    def test_empty_report_has_unknown_utilization_and_no_fabricated_observations(self):
        report=business_report(self.store,"2026-01-01")
        self.assertEqual(report["tables"],[])
        self.assertEqual(sum(h["person_entered"] for h in report["hourly"]),0)
        self.assertIsNone(report["traffic"]["sampling_coverage_fraction"])

    def test_traffic_coverage_requires_calibration_person_model_and_continuous_reliable_frames(self):
        start="2026-01-01T00:00:00Z"
        self.store.append("runs",key("r","shop"),start,{"config_hash":"cfg"})
        self.store.append("cameras",key("shop","cfg"),start,{"crossing_lines":[{"max_gap_seconds":1}]})
        self.store.append("class_catalog",key("cfg"),start,{"classes":[{"kind":"person","enabled":True}]})
        for seconds,reliable in [(0,True),(.5,True),(1,True),(2,False),(2.5,True),(3,True)]:
            ts=stamp(utc(start)+timedelta(seconds=seconds))
            self.store.append("frames",str(seconds),ts,{"run_id":"r","camera_id":"shop","reliable":reliable})
        report=business_report(self.store,"2026-01-01")
        self.assertEqual(report["traffic"]["observed_camera_seconds"],1.5)
        self.assertEqual(report["hourly"][0]["traffic_observed_camera_seconds"],1.5)
        self.assertAlmostEqual(report["traffic"]["sampling_coverage_fraction"],1.5/86400)

    def test_append_only_traffic_corrections_update_aggregates_and_deduplicate_retries(self):
        self.event("crossing","2026-01-01T09:00:00Z")
        self.assertEqual(business_report(self.store,"2026-01-01")["traffic"]["person_entered"],1)
        first=self.store.review_crossing("crossing","rejected","Boundary calibration error, reviewed clip")
        repeated=self.store.review_crossing("crossing","rejected","Boundary calibration error, reviewed clip")
        self.assertEqual(first,repeated)
        self.assertEqual(len(self.store.records("traffic_reviews")),1)
        self.assertEqual(business_report(self.store,"2026-01-01")["traffic"]["person_entered"],0)
        self.store.review_crossing("crossing","confirmed","Second review of full clip resolved ambiguity")
        self.assertEqual(business_report(self.store,"2026-01-01")["traffic"]["person_entered"],1)
        self.assertEqual(len(self.store.records("events")),1)
        self.assertEqual(self.store.get("events","crossing")["status"],"observed")
