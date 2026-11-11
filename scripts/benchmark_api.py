"""Fixed synthetic read-API workload; no P1, model accuracy or SLA claim."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
import hashlib
import http.client
import json
import math
from pathlib import Path
import platform
import sys
import tempfile
import threading
import time


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root",type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument("--requests",type=int,default=80)
    parser.add_argument("--concurrency",type=int,default=4)
    parser.add_argument("--profile",action="store_true",help="Separate instrumented diagnostic; do not compare its latency")
    args=parser.parse_args()
    if args.requests < 20 or not 1 <= args.concurrency <= 32: parser.error("Invalid workload size")
    root=args.source_root.resolve();sys.path.insert(0,str(root))
    import psutil
    from coffee_ops import api
    from coffee_ops.config import Config
    from coffee_ops.storage import SQLiteStore
    config=Config.load(root/"config/example.json")
    token="benchmark-only-"+"x"*32
    with tempfile.TemporaryDirectory() as temporary:
        database=Path(temporary)/"synthetic.db"
        with_store=SQLiteStore(database)
        with with_store.transaction():
            for i in range(200):
                stamp="2026-01-01T09:00:00Z"
                with_store.append("events",str(i),stamp,{"event_id":str(i),"timestamp":stamp,
                    "camera_id":"shop","run_id":"benchmark","kind":"person_entered","status":"observed"})
        with_store.close()
        database_sha=hashlib.sha256(database.read_bytes()).hexdigest()
        server=api.create_server(config,database,token,port=0)
        request_cpu=[];profiles=[];original=server.RequestHandlerClass
        class TimedHandler(original):
            def do_GET(self):
                if args.profile:
                    import cProfile
                    profile=cProfile.Profile();profile.enable()
                start=time.thread_time()
                try:super().do_GET()
                finally:
                    request_cpu.append(time.thread_time()-start)
                    if args.profile:
                        profile.disable();profiles.append(profile)
        server.RequestHandlerClass=TimedHandler
        thread=threading.Thread(target=server.serve_forever,kwargs={"poll_interval":.01},daemon=True);thread.start()
        paths=["/v1/events?camera=shop&limit=50&after=0"]*4+[
            "/v1/business-report?date=2026-01-01&timezone=UTC&camera=shop"]
        def request(index):
            start=time.perf_counter();connection=http.client.HTTPConnection(*server.server_address,timeout=15)
            try:
                connection.request("GET",paths[index%5],headers={"Authorization":"Bearer "+token})
                response=connection.getresponse();body=response.read()
                data=json.loads(body)
                valid=(len(data.get("events",[]))==50 if index%5!=4 else data.get("traffic",{}).get("person_entered")==200)
                return time.perf_counter()-start,response.status if valid else 599
            except (OSError,ValueError,http.client.HTTPException):return time.perf_counter()-start,598
            finally:connection.close()
        process=psutil.Process();rss=[];stop=threading.Event()
        def sample():
            while not stop.is_set():
                rss.append(process.memory_info().rss);stop.wait(.01)
        try:
            for i in range(10):
                if request(i)[1]!=200:raise RuntimeError("Warmup failed")
            request_cpu.clear();profiles.clear();cpu_start=process.cpu_times();started=time.perf_counter()
            monitor=threading.Thread(target=sample,daemon=True);monitor.start()
            with ThreadPoolExecutor(max_workers=args.concurrency) as pool:rows=list(pool.map(request,range(args.requests)))
            elapsed=time.perf_counter()-started;cpu_end=process.cpu_times()
            stop.set();monitor.join();rss.append(process.memory_info().rss)
        finally:
            server.shutdown();server.server_close();thread.join(timeout=2)
        def quantile(values,q):return sorted(values)[max(0,math.ceil(len(values)*q)-1)]*1000
        latencies=[r[0] for r in rows]
        status=Counter(r[1] for r in rows)
        result={"purpose":"synthetic_read_api_diagnostic_not_P1_or_hosted_capacity",
            "platform":platform.platform(),"python":platform.python_version(),
            "requests":args.requests,"concurrency":args.concurrency,"warmup_requests":10,
            "mix":"4 events pages (50 rows) : 1 business report; 200 stored events, no POS/frames",
            "database_sha256":database_sha,"database_bytes":database.stat().st_size,
            "source_sha256":{name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in ["coffee_ops/api.py","coffee_ops/storage.py"]},
            "p50_ms":quantile(latencies,.5),"p95_ms":quantile(latencies,.95),"p99_ms":quantile(latencies,.99),
            "throughput_rps":len(rows)/elapsed,"statuses":dict(status),"error_rate":1-status[200]/len(rows),
            "request_thread_cpu_ms_mean":sum(request_cpu)/len(request_cpu)*1000,
            "process_cpu_seconds":cpu_end.user+cpu_end.system-cpu_start.user-cpu_start.system,
            "peak_sampled_rss_bytes":max(rss),
            "limitations":"RSS/CPU include in-process HTTP client and harness; thread CPU excludes other threads. SQLite is in the API process, no separate DB server. No frontend/proxy/model inference."}
        if args.profile:
            import io,pstats
            stream=io.StringIO();stats=pstats.Stats(profiles[0],stream=stream)
            for profile in profiles[1:]:stats.add(profile)
            stats.sort_stats("cumulative").print_stats(20)
            result["instrumented_profile"]=stream.getvalue()
        print(json.dumps(result,allow_nan=False))
        return int(status[200]!=len(rows))


if __name__=="__main__":
    raise SystemExit(main())
