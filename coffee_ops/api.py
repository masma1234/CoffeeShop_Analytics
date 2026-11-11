"""Authenticated loopback-only read API for an offline pilot, not internet hosting."""
from __future__ import annotations

import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import sqlite3
from urllib.parse import parse_qs, urlsplit

from .business_reporting import business_report
from .reporting import current_status
from .schema import canonical
from .storage import SQLiteStore


class BoundedServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, handler):
        self.slots=threading.BoundedSemaphore(8)
        super().__init__(address,handler)

    def get_request(self):
        client,address=super().get_request()
        client.settimeout(5)
        return client,address

    def process_request(self,request,client_address):
        if not self.slots.acquire(blocking=False):
            try: request.sendall(b"HTTP/1.0 503 Service Unavailable\r\nContent-Length: 0\r\n\r\n")
            finally: self.shutdown_request(request)
            return
        try: super().process_request(request,client_address)
        except BaseException:
            self.slots.release()
            raise

    def process_request_thread(self,request,client_address):
        try: super().process_request_thread(request,client_address)
        finally: self.slots.release()


def create_server(config, database: str | Path, token: str, port: int = 8765) -> BoundedServer:
    if not isinstance(token,str) or len(token)<32 or not token.isascii() or any(c.isspace() for c in token):
        raise ValueError("Set COFFEE_OPS_API_TOKEN to at least 32 ASCII characters without whitespace")
    if type(port) is not int or not 0<=port<=65535: raise ValueError("Invalid API port")
    database=Path(database).resolve()
    with_store=SQLiteStore(database,read_only=True)
    with_store.close()
    expected=("Bearer "+token).encode()

    class Handler(BaseHTTPRequestHandler):
        server_version="CoffeeOpsPilot/1"
        sys_version=""

        def log_message(self,*args):
            pass  # Do not log request URLs, headers or credentials.

        def respond(self,code,value):
            body=canonical(value).encode()
            self.send_response(code)
            self.send_header("Content-Type","application/json; charset=utf-8")
            self.send_header("Content-Length",str(len(body)))
            self.send_header("Cache-Control","no-store")
            self.send_header("X-Content-Type-Options","nosniff")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            # Liveness only: no database, paths, metrics or credentials. Detailed
            # readiness remains behind bearer authentication at /v1/health.
            if self.path=="/healthz":
                self.respond(200,{"status":"ok"});return
            if not hmac.compare_digest(self.headers.get("Authorization","").encode(),expected):
                self.respond(401,{"error":"Bearer authentication required"});return
            if self.headers.get("Origin"):
                self.respond(403,{"error":"Cross-origin browser requests disabled"});return
            if len(self.path)>2048:
                self.respond(414,{"error":"Request URI too long"});return
            store=None
            try:
                url=urlsplit(self.path)
                query=parse_qs(url.query,strict_parsing=True,max_num_fields=8)
                if any(len(v)!=1 for v in query.values()): raise ValueError("Duplicate query parameter")
                params={k:v[0] for k,v in query.items()}
                store=SQLiteStore(database,timeout=2,read_only=True)
                if url.path=="/v1/health" and not params:
                    result={"storage":store.health(),"scope":"loopback read-only pilot"}
                elif url.path=="/v1/cameras" and not params:
                    result={"cameras":[c["id"] for c in config.data["cameras"]]}
                elif url.path in {"/v1/status","/v1/events"}:
                    allowed={"camera"} if url.path.endswith("status") else {"camera","limit","after"}
                    if params.keys()-allowed: raise ValueError("Unsupported query parameter")
                    camera=params["camera"];config.camera(camera)
                    if url.path.endswith("status"):
                        raw=current_status(store,camera)
                        # Exclude images, disk paths, detailed traces and exception strings.
                        result={k:raw[k] for k in ["camera_id","as_of","tables","empty_tables","occupied_tables","table_utilization_percent","storage"]}
                        health=raw["health"] or {}
                        result["health"]={k:health.get(k) for k in ["timestamp","status","processed_frames","last_capture_timestamp","reliable_frames","unreliable_frames","traffic_calibrated","runtime"]}
                    else:
                        rows=store.event_page(camera,int(params.get("limit",100)),int(params.get("after",0)))
                        fields={"_seq","event_id","kind","timestamp","confirmed_at","camera_id","run_id","track_id","line_id","product_class","status","role","confidence","source_zone","destination_zone"}
                        result={"events":[{k:v for k,v in r.items() if k in fields} for r in rows],
                                "next_after":rows[-1]["_seq"] if rows else int(params.get("after",0))}
                        for item in result["events"]:
                            review=store.latest("traffic_reviews","event_id",item["event_id"])
                            if review:item["review"]={k:review[k] for k in ["decision","revision"]}
                elif url.path=="/v1/business-report":
                    if params.keys()-{"date","timezone","start_hour","camera","run_id"}: raise ValueError("Unsupported query parameter")
                    if params.get("camera"):config.camera(params["camera"])
                    result=business_report(store,params["date"],params.get("timezone","UTC"),
                        int(params.get("start_hour",0)),params.get("camera"),run_id=params.get("run_id"))
                else:
                    self.respond(404,{"error":"Unknown endpoint"});return
                self.respond(200,result)
            except (ValueError,KeyError,TypeError): self.respond(400,{"error":"Invalid request or ambiguous report scope"})
            except (OSError,RuntimeError,sqlite3.Error): self.respond(503,{"error":"Storage/report unavailable"})
            finally:
                if store is not None:store.close()

    return BoundedServer(("127.0.0.1",port),Handler)


def serve(config,database: str | Path,token: str,port: int=8765):
    server=create_server(config,database,token,port)
    try: server.serve_forever(poll_interval=.2)
    except KeyboardInterrupt: pass
    finally: server.server_close()
    return {"status":"stopped"}
