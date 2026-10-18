"""CloudLaunch request registry: independent employee requests, duplicate warnings.

This module performs NO AWS writes and NO Jenkins/Terraform execution.
The sqlite database is a learning prototype; use PostgreSQL for a real service.
"""
import json
import sqlite3
import uuid
from pathlib import Path

FIELDS = ("employee_id", "project_id", "task_id", "workload", "environment", "region", "instance_type")
BUSINESS_FIELDS = ("project_id", "task_id", "workload", "environment", "region")
VALID_STATUSES = {"PENDING_REVIEW", "DUPLICATE_REVIEW", "APPROVED", "REJECTED", "DEPLOYING", "COMPLETED", "FAILED"}

def normalize(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Every field must be a nonempty string")
    return value.strip().casefold()

def validate(payload):
    if not isinstance(payload, dict):
        raise ValueError("Request must be a JSON object")
    missing = [key for key in FIELDS if key not in payload]
    if missing:
        raise ValueError("Missing fields: " + ", ".join(missing))
    data = {key: normalize(payload[key]) for key in FIELDS}
    if data["environment"] not in {"dev", "test", "prod"}:
        raise ValueError("Invalid environment")
    if data["region"] not in {"us-east-1", "us-east-2"}:
        raise ValueError("Unsupported region")
    if data["instance_type"] not in {"t3.micro", "t3.small", "t3.medium"}:
        raise ValueError("Unsupported instance type")
    return data

def business_key(data):
    return json.dumps([data[k] for k in BUSINESS_FIELDS], separators=(",", ":"))

def connect(db_path):
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path), timeout=30, isolation_level=None)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    con.executescript("""
    CREATE TABLE IF NOT EXISTS requests (
        request_id TEXT PRIMARY KEY,
        employee_id TEXT NOT NULL,
        idempotency_key TEXT NOT NULL,
        business_key TEXT NOT NULL,
        request_json TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
        reviewed_by TEXT,
        review_reason TEXT,
        UNIQUE(employee_id, idempotency_key)
    );
    CREATE INDEX IF NOT EXISTS ix_requests_business ON requests(business_key);
    """)
    return con

def submit_request(db_path, payload, idempotency_key):
    """Store distinct employees separately and flag similar business requirements.

    BEGIN IMMEDIATE ensures concurrent submissions cannot both overlook one another.
    Identical client retries return the same request rather than creating another.
    """
    data = validate(payload)
    token = normalize(idempotency_key)
    key = business_key(data)
    con = connect(db_path)
    try:
        con.execute("BEGIN IMMEDIATE")
        prior = con.execute(
            "SELECT * FROM requests WHERE employee_id=? AND idempotency_key=?",
            (data["employee_id"], token)
        ).fetchone()
        if prior:
            if json.loads(prior["request_json"]) != data:
                raise ValueError("Idempotency key reused for a different request")
            result = {"request_id": prior["request_id"], "status": prior["status"],
                      "action": "RETRIED_SAME_REQUEST", "similar_requests": []}
        else:
            matches = con.execute(
                "SELECT request_id,employee_id,status,created_at,request_json FROM requests WHERE business_key=?",
                (key,)
            ).fetchall()
            # Exclude rejected requests from blocking; retain them for audit and reporting.
            active = [m for m in matches if m["status"] != "REJECTED"]
            request_id = "REQ-" + uuid.uuid4().hex[:12].upper()
            status = "DUPLICATE_REVIEW" if active else "PENDING_REVIEW"
            con.execute(
                """INSERT INTO requests(request_id,employee_id,idempotency_key,business_key,request_json,status)
                   VALUES(?,?,?,?,?,?)""",
                (request_id, data["employee_id"], token, key, json.dumps(data, sort_keys=True), status)
            )
            # Previously submitted active requests are also marked for duplicate review.
            if active:
                con.execute(
                    """UPDATE requests SET status='DUPLICATE_REVIEW'
                       WHERE business_key=? AND status='PENDING_REVIEW'""", (key,)
                )
            result = {
                "request_id": request_id, "status": status,
                "action": "POTENTIAL_DUPLICATE" if active else "REQUEST_RECORDED",
                "similar_requests": [{"request_id": m["request_id"],
                                      "employee_id": m["employee_id"],
                                      "status": m["status"]} for m in active],
            }
        con.commit()
        return result
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

def list_records(db_path):
    con = connect(db_path)
    try:
        return [dict(r) for r in con.execute(
            """SELECT request_id,employee_id,status,created_at,reviewed_by,review_reason,
               request_json FROM requests ORDER BY created_at,request_id"""
        )]
    finally:
        con.close()

def duplicate_report(db_path):
    """Review list: all individual requests in business groups of 2 or more."""
    con = connect(db_path)
    try:
        groups = con.execute(
            """SELECT business_key, COUNT(*) AS total FROM requests
               WHERE status != 'REJECTED' GROUP BY business_key HAVING COUNT(*) > 1
               ORDER BY total DESC,business_key"""
        ).fetchall()
        return [{
            "business_key": json.loads(g["business_key"]),
            "request_count": g["total"],
            "employees": [dict(r) for r in con.execute(
                """SELECT request_id,employee_id,status,created_at FROM requests
                   WHERE business_key=? AND status!='REJECTED' ORDER BY created_at,request_id""",
                (g["business_key"],)
            )]
        } for g in groups]
    finally:
        con.close()
