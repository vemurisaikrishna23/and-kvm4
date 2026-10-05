"""
IoT Admin dashboard analytics: one call, every section, for a date range.

Grouping by day/hour is done in Python in the project time zone (Asia/Kolkata):
rows are fetched by an aware datetime range, so no DB time-zone functions are needed.

Conventions shared with the rest of the backend:
- Dispensed volume/amount count as 0 for timed-out transactions (code 411),
  like DispensedTotalsMixin.
- Outcome from request_status: 3 completed, 4 interrupted, 5 failed, 0/1/2 in progress.
"""
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta

from django.db.models import Max
from django.utils import timezone

from existing_tables.models import Customers
from .models import (
    Camera,
    Dispenser_Gun_Mapping_To_Customer,
    Dispenser_Gun_Mapping_To_Vehicles,
    DispenserUnits,
    GunUnits,
    NodeUnits,
    OrderFuelDispensingDetails,
    RequestCameraSnapshot,
    RequestFuelDispensingDetails,
)

TIMEOUT_CODE = 411
MAX_RANGE_DAYS = 366

OUTCOME_BY_STATUS = {0: "in_progress", 1: "in_progress", 2: "in_progress", 3: "completed", 4: "interrupted", 5: "failed"}
CODE_LABEL = {
    0: "Pending", 200: "Ready", 201: "Started", 202: "Dispensing", 206: "Re-Dispensing",
    203: "Completed", 204: "Incomplete", 205: "Paused", 400: "In Active", 401: "Not Responding",
    402: "Not Responding", 410: "Terminated", 411: "Timeout", 420: "Power OFF",
}
REQUEST_TYPE_LABEL = {0: "Volume", 1: "Amount", 2: "Full Tank"}
REQUEST_VEHICLE_LABEL = {0: "Asset", 1: "VIN", 2: "User"}
MACHINE_STATUS_LABEL = {1: "Idle", 0: "Offline", 2: "Dispensing", 3: "Allocated", 4: "Error"}

FIELDS = (
    "id", "transaction_id", "request_created_at", "request_status", "dispense_status_code",
    "dispenser_received_volume", "dispenser_received_price", "dispense_time_taken",
    "customer_id", "customer_name", "dispenser_imeinumber", "dispenser_serialnumber",
    "delivery_location_id", "delivery_location_name", "asset_id", "asset_name",
    "request_type", "request_vehicle", "totalizer_validation", "snapshot_count",
)


class RangeError(ValueError):
    pass


def parse_range(from_s, to_s):
    """Inclusive IST date range; default last 30 days."""
    today = timezone.localdate()
    try:
        d_to = date.fromisoformat(to_s) if to_s else today
        d_from = date.fromisoformat(from_s) if from_s else d_to - timedelta(days=29)
    except ValueError:
        raise RangeError("Invalid date. Use YYYY-MM-DD.")
    if d_from > d_to:
        raise RangeError("'from' must be on or before 'to'.")
    if (d_to - d_from).days + 1 > MAX_RANGE_DAYS:
        raise RangeError(f"Range too long (max {MAX_RANGE_DAYS} days).")
    return d_from, d_to


def _bounds(d_from, d_to):
    tz = timezone.get_current_timezone()
    start = timezone.make_aware(datetime.combine(d_from, time.min), tz)
    end = timezone.make_aware(datetime.combine(d_to + timedelta(days=1), time.min), tz)
    return start, end


def _vol(r):
    if r["dispense_status_code"] == TIMEOUT_CODE:
        return 0.0, 0.0
    return float(r["dispenser_received_volume"] or 0), float(r["dispenser_received_price"] or 0)


def _summarise(rows):
    c = Counter(OUTCOME_BY_STATUS.get(r["request_status"], "in_progress") for r in rows)
    volume = amount = 0.0
    times = []
    for r in rows:
        v, a = _vol(r)
        volume += v
        amount += a
        if r["request_status"] == 3 and (r["dispense_time_taken"] or 0) > 0:
            times.append(float(r["dispense_time_taken"]))
    finished = c["completed"] + c["interrupted"] + c["failed"]
    return {
        "transactions": len(rows),
        "completed": c["completed"],
        "in_progress": c["in_progress"],
        "interrupted": c["interrupted"],
        "failed": c["failed"],
        "volume_l": round(volume, 2),
        "amount": round(amount, 2),
        "success_rate": round(c["completed"] * 100.0 / finished, 1) if finished else None,
        "avg_volume_per_completed_l": round(volume / c["completed"], 2) if c["completed"] else None,
        "avg_dispense_time_s": round(sum(times) / len(times), 1) if times else None,
        "active_customers": len({r["customer_id"] for r in rows if r["customer_id"]}),
        "active_dispensers": len({r["dispenser_imeinumber"] for r in rows if r["dispenser_imeinumber"]}),
        "active_locations": len({r["delivery_location_id"] for r in rows if r["delivery_location_id"]}),
        "active_assets": len({r["asset_id"] for r in rows if r["asset_id"]}),
    }


def _top(rows, key, name_key, limit, extra=None):
    agg = defaultdict(lambda: {"transactions": 0, "completed": 0, "volume_l": 0.0, "amount": 0.0, "name": None, "last": None})
    for r in rows:
        k = r[key]
        if k in (None, ""):
            continue
        a = agg[k]
        v, amt = _vol(r)
        a["transactions"] += 1
        a["completed"] += 1 if r["request_status"] == 3 else 0
        a["volume_l"] += v
        a["amount"] += amt
        a["name"] = a["name"] or r[name_key]
        if a["last"] is None or r["request_created_at"] > a["last"]:
            a["last"] = r["request_created_at"]
        if extra:
            for ek in extra:
                a[ek] = a.get(ek) or r[ek]
    items = []
    for k, a in agg.items():
        item = {
            "id": k,
            "name": a["name"],
            "transactions": a["transactions"],
            "completed": a["completed"],
            "volume_l": round(a["volume_l"], 2),
            "amount": round(a["amount"], 2),
            "last_activity": a["last"].isoformat() if a["last"] else None,
        }
        for ek in extra or ():
            item[ek] = a.get(ek)
        items.append(item)
    items.sort(key=lambda x: (x["volume_l"], x["transactions"]), reverse=True)
    return items[:limit]


def _fleet():
    du = DispenserUnits.objects
    conn = Counter((s or "unknown").lower() for s in du.values_list("connectivity_status", flat=True))
    cust = Dispenser_Gun_Mapping_To_Customer.objects.filter(assigned_status=True)
    veh = Dispenser_Gun_Mapping_To_Vehicles.objects.filter(assigned_status=True)
    ms = Counter(cust.values_list("machine_status", flat=True))
    gs = Counter(cust.values_list("gun_status", flat=True))
    cams = Camera.objects
    return {
        "dispensers": {
            "total": du.count(),
            "assigned": du.filter(assigned_status=True).count(),
            "connectivity": {"online": conn.get("online", 0), "offline": conn.get("offline", 0),
                             "unknown": sum(v for k, v in conn.items() if k not in ("online", "offline"))},
        },
        "guns": {"total": GunUnits.objects.count(), "assigned": GunUnits.objects.filter(assigned_status=True).count()},
        "nodes": {"total": NodeUnits.objects.count(), "assigned": NodeUnits.objects.filter(assigned_status=True).count()},
        "customer_assignments": {
            "total": cust.count(),
            "connected": cust.filter(connectivity_status=True).count(),
            "machine_status": [{"status": s, "label": MACHINE_STATUS_LABEL.get(s, str(s)), "count": ms.get(s, 0)}
                               for s in (2, 1, 3, 4, 0)],
            "gun_status": {"online": gs.get("online", 0), "offline": gs.get("offline", 0), "unavailable": gs.get("unavailable", 0)},
        },
        "vehicle_assignments": {"total": veh.count(), "connected": veh.filter(connectivity_status=True).count()},
        "cameras": {"total": cams.count(), "active": cams.filter(is_active=True).count()},
    }


def _attention(limit=12):
    """Assigned dispensers that need a look: error, offline/not connected; with last request time."""
    cust = (
        Dispenser_Gun_Mapping_To_Customer.objects.filter(assigned_status=True)
        .select_related("dispenser_unit")
        .order_by("-machine_status")
    )
    rows = list(cust)
    imeis = [m.dispenser_unit.imei_number for m in rows if m.dispenser_unit and m.dispenser_unit.imei_number]
    last = dict(
        RequestFuelDispensingDetails.objects.filter(dispenser_imeinumber__in=imeis)
        .values("dispenser_imeinumber").annotate(last=Max("request_created_at"))
        .values_list("dispenser_imeinumber", "last")
    )
    names = dict(Customers.objects.filter(id__in={m.customer for m in rows}).values_list("id", "name"))
    out = []
    for m in rows:
        du = m.dispenser_unit
        reasons = []
        if m.machine_status == 4:
            reasons.append("Error")
        if m.machine_status == 0:
            reasons.append("Offline")
        if not m.connectivity_status:
            reasons.append("Not connected")
        if m.gun_status == "offline":
            reasons.append("Gun offline")
        if not reasons:
            continue
        ts = last.get(du.imei_number) if du else None
        out.append({
            "mapping_id": m.id,
            "dispenser_serial_number": du.serial_number if du else None,
            "dispenser_imei": du.imei_number if du else None,
            "customer_id": m.customer,
            "customer_name": names.get(m.customer),
            "machine_status": MACHINE_STATUS_LABEL.get(m.machine_status, str(m.machine_status)),
            "connected": bool(m.connectivity_status),
            "gun_status": m.gun_status,
            "reasons": reasons,
            "last_request_at": ts.isoformat() if ts else None,
        })
    severity = {"Error": 0, "Offline": 1, "Not connected": 2, "Gun offline": 3}
    out.sort(key=lambda x: min(severity[r] for r in x["reasons"]))
    return {"count": len(out), "items": out[:limit]}


def build(d_from, d_to):
    start, end = _bounds(d_from, d_to)
    days = (d_to - d_from).days + 1
    p_to = d_from - timedelta(days=1)
    p_from = p_to - timedelta(days=days - 1)
    p_start, p_end = _bounds(p_from, p_to)

    R = RequestFuelDispensingDetails.objects
    rows = list(R.filter(request_created_at__gte=start, request_created_at__lt=end).values(*FIELDS))
    prev = list(R.filter(request_created_at__gte=p_start, request_created_at__lt=p_end).values(*FIELDS))

    # daily series + weekday x hour heatmap, in local time
    daily = {d_from + timedelta(days=i): {"transactions": 0, "completed": 0, "in_progress": 0, "interrupted": 0,
                                          "failed": 0, "volume_l": 0.0, "amount": 0.0} for i in range(days)}
    time_sum = Counter()
    time_n = Counter()
    # hour-of-day buckets over the whole range (used as the trend when a single day is selected)
    hourly = {h: {"transactions": 0, "completed": 0, "in_progress": 0, "interrupted": 0, "failed": 0,
                  "volume_l": 0.0, "amount": 0.0, "time_sum": 0.0, "time_n": 0} for h in range(24)}
    heat = Counter()
    for r in rows:
        local = timezone.localtime(r["request_created_at"])
        d = daily.get(local.date())
        if d is None:
            continue
        v, a = _vol(r)
        d["transactions"] += 1
        d[OUTCOME_BY_STATUS.get(r["request_status"], "in_progress")] += 1
        d["volume_l"] += v
        d["amount"] += a
        heat[(local.weekday(), local.hour)] += 1
        hb = hourly[local.hour]
        hb["transactions"] += 1
        hb[OUTCOME_BY_STATUS.get(r["request_status"], "in_progress")] += 1
        hb["volume_l"] += v
        hb["amount"] += a
        if r["request_status"] == 3 and (r["dispense_time_taken"] or 0) > 0:
            time_sum[local.date()] += float(r["dispense_time_taken"])
            time_n[local.date()] += 1
            hb["time_sum"] += float(r["dispense_time_taken"])
            hb["time_n"] += 1

    failures = Counter(r["dispense_status_code"] for r in rows if r["request_status"] in (4, 5))
    rtype = defaultdict(lambda: [0, 0.0])
    rveh = defaultdict(lambda: [0, 0.0])
    for r in rows:
        v, _ = _vol(r)
        rtype[r["request_type"]][0] += 1
        rtype[r["request_type"]][1] += v
        rveh[r["request_vehicle"]][0] += 1
        rveh[r["request_vehicle"]][1] += v
    tv = Counter(r["totalizer_validation"] for r in rows)

    orders = list(
        OrderFuelDispensingDetails.objects.filter(request_created_at__gte=start, request_created_at__lt=end)
        .values("request_status", "dispense_status_code", "dispenser_received_volume", "dispenser_received_price")
    )

    recent = sorted(rows, key=lambda r: r["request_created_at"], reverse=True)[:10]

    return {
        "range": {"from": d_from.isoformat(), "to": d_to.isoformat(), "days": days,
                  "previous_from": p_from.isoformat(), "previous_to": p_to.isoformat(),
                  "timezone": str(timezone.get_current_timezone())},
        "kpis": _summarise(rows),
        "previous": _summarise(prev),
        "daily": [{"date": d.isoformat(), **{k: (round(v, 2) if isinstance(v, float) else v) for k, v in vals.items()},
                   "avg_dispense_time_s": round(time_sum[d] / time_n[d], 1) if time_n[d] else None}
                  for d, vals in daily.items()],
        "hourly": [{"hour": h, "label": f"{h:02d}:00",
                    **{k: (round(v, 2) if isinstance(v, float) else v) for k, v in b.items() if k not in ("time_sum", "time_n")},
                    "avg_dispense_time_s": round(b["time_sum"] / b["time_n"], 1) if b["time_n"] else None}
                   for h, b in hourly.items()],
        "heatmap": [{"weekday": wd, "hour": h, "count": heat.get((wd, h), 0)} for wd in range(7) for h in range(24)],
        "failure_codes": [{"code": code, "label": CODE_LABEL.get(code, f"Code {code}"), "count": n}
                          for code, n in failures.most_common()],
        "request_types": [{"type": t, "label": REQUEST_TYPE_LABEL.get(t, str(t)), "count": v[0], "volume_l": round(v[1], 2)}
                          for t, v in sorted(rtype.items(), key=lambda x: (x[0] is None, x[0]))],
        "request_vehicles": [{"type": t, "label": REQUEST_VEHICLE_LABEL.get(t, str(t)), "count": v[0], "volume_l": round(v[1], 2)}
                             for t, v in sorted(rveh.items(), key=lambda x: (x[0] is None, x[0]))],
        "totalizer_validation": {"valid": tv.get(0, 0), "invalid": tv.get(1, 0), "pending": tv.get(2, 0)},
        "top_customers": _top(rows, "customer_id", "customer_name", 8),
        "top_dispensers": _top(rows, "dispenser_imeinumber", "dispenser_serialnumber", 10),
        "top_locations": _top(rows, "delivery_location_id", "delivery_location_name", 8),
        "top_assets": _top(rows, "asset_id", "asset_name", 8),
        "orders": {
            "transactions": len(orders),
            "completed": sum(1 for o in orders if o["request_status"] == 3),
            "volume_l": round(sum(float(o["dispenser_received_volume"] or 0) for o in orders
                                  if o["dispense_status_code"] != TIMEOUT_CODE), 2),
        },
        "cameras": {
            "snapshots": RequestCameraSnapshot.objects.filter(captured_at__gte=start, captured_at__lt=end).count(),
            "requests_with_snapshots": sum(1 for r in rows if (r["snapshot_count"] or 0) > 0),
        },
        "fleet": _fleet(),
        "attention": _attention(),
        "recent": [{
            "id": r["id"], "transaction_id": r["transaction_id"],
            "created_at": r["request_created_at"].isoformat() if r["request_created_at"] else None,
            "customer_name": r["customer_name"], "dispenser_serial_number": r["dispenser_serialnumber"],
            "location": r["delivery_location_name"], "asset_name": r["asset_name"],
            "outcome": OUTCOME_BY_STATUS.get(r["request_status"], "in_progress"),
            "status_code": r["dispense_status_code"], "status_label": CODE_LABEL.get(r["dispense_status_code"], str(r["dispense_status_code"])),
            "volume_l": round(_vol(r)[0], 2), "amount": round(_vol(r)[1], 2),
        } for r in recent],
        "generated_at": timezone.now().isoformat(),
    }
