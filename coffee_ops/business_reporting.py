"""Local business-day read models with explicit observation coverage."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from .schema import key, stamp, utc
from .storage import SQLiteStore


def business_window(day: str, timezone: str = "UTC", start_hour: int = 0) -> tuple[datetime, datetime]:
    if type(start_hour) is not int or not 0 <= start_hour <= 23:
        raise ValueError("Business day start hour must be 0..23")
    zone = ZoneInfo(timezone)
    target = date.fromisoformat(day)
    if target.year in {1,9999}:
        raise ValueError("Business day outside supported report range")
    boundaries = []
    for d in [target, target+timedelta(days=1)]:
        local = datetime.combine(d, time(start_hour), zone)
        if local.replace(fold=0).utcoffset() != local.replace(fold=1).utcoffset():
            raise ValueError("Business boundary is ambiguous/nonexistent; choose a stable start hour")
        converted = utc(local)
        if converted.astimezone(zone).replace(tzinfo=None) != local.replace(tzinfo=None):
            raise ValueError("Business boundary does not exist in this timezone")
        boundaries.append(converted)
    if boundaries[1] <= boundaries[0]:
        raise ValueError("Empty business day")
    return tuple(boundaries)


def business_report(store: SQLiteStore, day: str, timezone: str = "UTC", start_hour: int = 0,
                    camera_id: str | None = None, max_observation_gap: float = 5, run_id: str | None = None) -> dict:
    from .config import number
    number(max_observation_gap, "report observation gap", .001, 3600)
    start, end = business_window(day, timezone, start_hour)
    start_s, end_s = start.timestamp(), end.timestamp()
    zone = ZoneInfo(timezone)
    hours = []
    cursor = start
    while cursor < end:
        stop = min(cursor+timedelta(hours=1), end)
        hours.append({"utc_start":stamp(cursor),"local_start":cursor.astimezone(zone).isoformat(),
                      "duration_seconds":(stop-cursor).total_seconds(),
                      "person_entered":0,"person_exited":0,"visual_product_events":{},
                      "traffic_observed_camera_seconds":0.})
        cursor = stop
    counts, products, sales = Counter(), Counter(), Counter()
    excluded_traffic = Counter()
    with store.snapshot():
        for event in store.between("events", stamp(start), stamp(end), camera_id,run_id):
            kind = event["kind"]
            if kind in {"person_entered","person_exited"}:
                review=store.latest("traffic_reviews","event_id",event["event_id"])
                if review and review["decision"] in {"rejected","uncertain"}:
                    excluded_traffic[review["decision"]]+=1
                    continue
            if event.get("status") not in {"observed", "confirmed"}:
                continue
            bucket = hours[min(len(hours)-1, int((utc(event["timestamp"])-start).total_seconds()//3600))]
            if kind in {"person_entered", "person_exited"}:
                counts[kind] += 1
                bucket[kind] += 1
            elif kind in {"placed", "transferred", "removed"}:
                label = f"{event['product_class']}:{kind}"
                products[label] += 1
                bucket["visual_product_events"][label] = bucket["visual_product_events"].get(label, 0)+1
        for order in store.orders_between(stamp(start), stamp(end), camera_id):
            if order["payment_status"] == "paid":
                sales[order["sku"]] += order["quantity"]
        previous, duration, transitions = {}, defaultdict(Counter), Counter()
        run_ranges = defaultdict(dict)

        def integrate(sample, until):
            t = utc(sample["timestamp"]).timestamp()
            seconds = max(0., min(until,t+max_observation_gap,end_s)-max(t,start_s))
            for table in sample["tables"]:
                identity = (sample["camera_id"], table["zone_id"])
                status = table["status"] if table["status"] in {"occupied","empty"} else "unknown"
                duration[identity][status] += seconds

        for sample in store.between("occupancy", stamp(start-timedelta(seconds=max_observation_gap)), stamp(end), camera_id,run_id):
            camera = sample["camera_id"]
            seconds = utc(sample["timestamp"]).timestamp()
            interval = run_ranges[camera].setdefault(sample["run_id"],[seconds,seconds])
            interval[1] = seconds
            before = previous.get(camera)
            if before is not None:
                # Run boundaries and gaps never bridge occupancy state or turnover.
                continuous = before["run_id"] == sample["run_id"] and (
                    utc(sample["timestamp"])-utc(before["timestamp"])).total_seconds() <= max_observation_gap
                integrate(before, utc(sample["timestamp"]).timestamp())
                if continuous and start_s <= utc(sample["timestamp"]).timestamp():
                    old = {t["zone_id"]:t["status"] for t in before["tables"]}
                    for table in sample["tables"]:
                        if old.get(table["zone_id"]) == "occupied" and table["status"] == "empty":
                            transitions[(camera,table["zone_id"])] += 1
            previous[camera] = sample
        for sample in previous.values(): integrate(sample,end_s)
        for ranges in run_ranges.values():
            ordered=sorted(ranges.values())
            if any(b[0]<=a[1] for a,b in zip(ordered,ordered[1:])):
                raise ValueError("Overlapping camera runs; select --run-id instead of double-counting replays")
        # Traffic coverage needs adjacent reliable frames AND the historical run's
        # person catalog/calibration. A zero count without those is unobserved time.
        prior_frames,run_gates,covered_cameras={},{},set()
        for frame in store.between("frames",stamp(start-timedelta(seconds=max_observation_gap)),stamp(end),camera_id,run_id):
            camera,run=frame["camera_id"],frame["run_id"]
            gate_key=(camera,run)
            if gate_key not in run_gates:
                session=store.get("runs",key(run,camera)) or {}
                config_hash=session.get("config_hash")
                calibration=store.get("cameras",key(camera,config_hash)) or {}
                catalog=store.get("class_catalog",key(config_hash)) or {}
                lines=calibration.get("crossing_lines",[])
                enabled=bool(lines) and any(c["kind"]=="person" and c["enabled"] for c in catalog.get("classes",[]))
                run_gates[gate_key]=min([max_observation_gap]+[l["max_gap_seconds"] for l in lines]) if enabled else None
            gap=run_gates[gate_key]
            previous_frame=prior_frames.get(camera)
            if gap is not None:
                covered_cameras.add(camera)
            if gap is not None and previous_frame and previous_frame["run_id"]==run and frame["reliable"] is True and previous_frame["reliable"] is True:
                a=utc(previous_frame["_timestamp"]).timestamp();b=utc(frame["_timestamp"]).timestamp()
                if 0<b-a<=gap:
                    a,b=max(a,start_s),min(b,end_s)
                    while a<b:
                        index=min(len(hours)-1,int((a-start_s)//3600))
                        stop=min(b,start_s+(index+1)*3600)
                        hours[index]["traffic_observed_camera_seconds"]+=stop-a
                        a=stop
            prior_frames[camera]=frame
        tables = []
        total_seconds = end_s-start_s
        for (camera, table), times in sorted(duration.items()):
            known = times["occupied"]+times["empty"]
            tables.append({"camera_id":camera,"table_id":table,
                "occupied_seconds":times["occupied"],"empty_seconds":times["empty"],
                "unknown_seconds":times["unknown"],"unobserved_seconds":max(0,total_seconds-sum(times.values())),
                "known_coverage_fraction":known/total_seconds,
                "utilization_percent":100*times["occupied"]/known if known else None,
                "observed_occupied_to_empty_transitions":transitions[(camera,table)]})
        watermarks = {k:store.watermark(k) for k in ["events","occupancy","orders","traffic_reviews","frames"]}
    return {"business_date":day,"timezone":timezone,"business_day_start_hour":start_hour,
        "utc_start":stamp(start),"utc_end_exclusive":stamp(end),"duration_seconds":end_s-start_s,
        "camera_id":camera_id,"run_id":run_id,"data_watermarks":watermarks,"hourly":hours,
        "traffic":{"person_entered":counts["person_entered"],"person_exited":counts["person_exited"],
                   "net_observed_crossings":counts["person_entered"]-counts["person_exited"],
                   "in_store_occupancy_estimate":None,"roles":"unknown",
                   "excluded_after_review":dict(excluded_traffic),
                   "observed_camera_seconds":sum(h["traffic_observed_camera_seconds"] for h in hours),
                   "calibrated_cameras_with_frames":sorted(covered_cameras),
                   "sampling_coverage_fraction":sum(h["traffic_observed_camera_seconds"] for h in hours)/(len(covered_cameras)*(end_s-start_s)) if covered_cameras else None,
                   "coverage_notice":"Reliable adjacent sampled frames with configured lines/person detection; not a guarantee every crossing was observable. Zero counts without coverage are not verified zero traffic.",
                   "notice":"Crossings are not globally unique customers; initial occupancy and unseen doors are unknown."},
        "tables":tables,"visual_product_events":dict(products),"confirmed_sold_units":dict(sales),
        "confirmed_sales_source":"paid_POS_only","max_observation_gap_seconds":max_observation_gap,
        "pos_scope":"business day/camera; independent of selected video run",
        "occupancy_method":"time-weighted observed intervals, capped at observation gap; unknown/unobserved excluded",
        "payment_notice":"Video alone cannot confirm preparation, handover or payment."}
