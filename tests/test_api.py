"""Real loopback HTTP requests, with read-only database enforcement."""
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request,urlopen

from coffee_ops.api import create_server
from coffee_ops.config import Config
from coffee_ops.storage import SQLiteStore

ROOT=Path(__file__).resolve().parents[1]
TOKEN="unit-test-token-"+"x"*32


class APITests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.database=Path(self.temp.name)/"ops.db"
        store=SQLiteStore(self.database)
        for i in range(3):
            stamp=f"2026-01-01T09:00:0{i}Z"
            store.append("events",str(i),stamp,{"event_id":str(i),"timestamp":stamp,"camera_id":"shop",
                "run_id":"test","kind":"person_entered","status":"observed","evidence":{"image_path":"private/path.jpg"}})
        store.close()
        self.server=create_server(Config.load(ROOT/"config/example.json"),self.database,TOKEN,port=0)
        self.thread=threading.Thread(target=self.server.serve_forever,kwargs={"poll_interval":.01},daemon=True)
        self.thread.start();self.addCleanup(self.stop)
        self.url=f"http://127.0.0.1:{self.server.server_address[1]}"

    def stop(self):
        self.server.shutdown();self.server.server_close();self.thread.join(timeout=2)

    def request(self,path,token=TOKEN,**headers):
        h={"Authorization":"Bearer "+token,**headers} if token else headers
        try:
            with urlopen(Request(self.url+path,headers=h),timeout=3) as r:
                return r.status,json.loads(r.read()),dict(r.headers)
        except HTTPError as e:
            return e.code,json.loads(e.read()),dict(e.headers)

    def test_authentication_required_for_every_endpoint(self):
        for path in ["/v1/health","/v1/cameras","/v1/events?camera=shop"]:
            self.assertEqual(self.request(path,token=None)[0],401)
            self.assertEqual(self.request(path,token="wrong")[0],401)
        self.assertEqual(self.request("/v1/health")[0],200)

    def test_pagination_redaction_and_no_cache(self):
        status,data,headers=self.request("/v1/events?camera=shop&limit=2")
        self.assertEqual(status,200)
        self.assertEqual(len(data["events"]),2)
        self.assertNotIn("evidence",data["events"][0])
        self.assertEqual(headers["Cache-Control"],"no-store")
        following=self.request(f"/v1/events?camera=shop&limit=2&after={data['next_after']}")[1]
        self.assertEqual(len(following["events"]),1)

    def test_business_aggregate_reconciles_with_stored_events(self):
        status,result,_=self.request("/v1/business-report?date=2026-01-01&timezone=Africa%2FTunis&camera=shop")
        self.assertEqual(status,200)
        self.assertEqual(result["traffic"]["person_entered"],3)
        self.assertEqual(sum(h["person_entered"] for h in result["hourly"]),3)

    def test_invalid_queries_cross_origin_and_storage_errors_are_explicit(self):
        for path in ["/v1/events?camera=shop&limit=99999","/v1/status?camera=other",
                     "/v1/status?camera=shop&camera=shop","/v1/business-report?date=bad",
                     "/v1/business-report?date=2026-01-01&timezone=missing"]:
            self.assertEqual(self.request(path)[0],400,path)
        self.assertEqual(self.request("/v1/health",Origin="https://untrusted.example")[0],403)
        with patch("coffee_ops.api.SQLiteStore",side_effect=sqlite3.OperationalError("private detail")):
            status,data,_=self.request("/v1/health")
        self.assertEqual(status,503)
        self.assertNotIn("private",json.dumps(data))

    def test_read_only_mode_prevents_mutation_and_never_creates_missing_db(self):
        store=SQLiteStore(self.database,read_only=True)
        try:
            with self.assertRaises(sqlite3.OperationalError):
                store.append("events","forbidden","2026-01-01T00:00:00Z",{})
        finally:store.close()
        missing=Path(self.temp.name)/"missing"/"ops.db"
        with self.assertRaises(FileNotFoundError):SQLiteStore(missing,read_only=True)
        self.assertFalse(missing.parent.exists())
        with self.assertRaises(ValueError):create_server(Config.load(ROOT/"config/example.json"),self.database,"short")

    def test_cursor_outside_sqlite_range_returns_json_and_server_recovers(self):
        for after in ["9223372036854775808", "9"*500, "-1"]:
            status,data,_=self.request("/v1/events?camera=shop&after="+after)
            self.assertEqual(status,400)
            self.assertEqual(set(data),{"error"})
        self.assertEqual(self.request("/v1/events?camera=shop&after=9223372036854775807")[0],200)
        self.assertEqual(self.request("/v1/events?camera=shop")[0],200)

    def test_minimal_liveness_does_not_open_storage_or_expose_readiness(self):
        with patch("coffee_ops.api.SQLiteStore",side_effect=AssertionError("Must not open storage")):
            status,data,headers=self.request("/healthz",token=None)
        self.assertEqual((status,data),(200,{"status":"ok"}))
        self.assertEqual(headers["Cache-Control"],"no-store")
        for path in ["/healthz?detail=1","/v1/health","/v1/status?camera=shop"]:
            self.assertEqual(self.request(path,token=None)[0],401)
