"""Atomic request reconciliation; no Jenkins, Terraform or AWS calls."""
import json
import sqlite3
import uuid
from pathlib import Path

FIELDS = ("employee_id", "project_id", "task_id", "workload", "environment", "region", "instance_type")

def normalize(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("All request fields must be nonempty strings")
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

def connect(db_path):
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path), timeout=30, isolation_level=None)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    con.executescript("""
        CREATE TABLE IF NOT EXISTS deployments (
            deployment_id TEXT PRIMARY KEY,
            business_key TEXT NOT NULL UNIQUE,
            project_id TEXT NOT NULL,
            task_id TEXT NOT NULL,
            workload TEXT NOT NULL,
            environment TEXT NOT NULL,
            region TEXT NOT NULL,
            instance_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDING_REVIEW'
        );
        CREATE TABLE IF NOT EXISTS requests (
            request_id TEXT PRIMARY KEY,
            deployment_id TEXT NOT NULL REFERENCES deployments(deployment_id),
            employee_id TEXT NOT NULL,
            idempotency_key TEXT NOT NULL,
            request_json TEXT NOT NULL,
            UNIQUE(employee_id, idempotency_key)
        );
    """)
    return con

def submit_request(db_path, payload, idempotency_key):
    """Same business task shares a deployment; mismatched sizing needs review.

    SQLite BEGIN IMMEDIATE serializes competing writers, including simultaneous
    submissions from separate processes against the same local database file.
    """
    data = validate(payload)
    token = normalize(idempotency_key)
    key_fields = ("project_id", "task_id", "workload", "environment", "region")
    business_key = json.dumps([data[k] for k in key_fields], separators=(",", ":"))
    con = connect(db_path)
    try:
        con.execute("BEGIN IMMEDIATE")
        prior = con.execute("""SELECT r.request_id,r.deployment_id,r.request_json,d.status
            FROM requests r JOIN deployments d USING (deployment_id)
            WHERE r.employee_id=? AND r.idempotency_key=?""",
            (data["employee_id"], token)).fetchone()
        if prior:
            if json.loads(prior["request_json"]) != data:
                raise ValueError("Idempotency key reused for a different request")
            result = dict(request_id=prior["request_id"], deployment_id=prior["deployment_id"],
                          action="RETRIED_SAME_REQUEST", status=prior["status"])
        else:
            match = con.execute("SELECT * FROM deployments WHERE business_key=?", (business_key,)).fetchone()
            if match and match["instance_type"] != data["instance_type"]:
                raise ValueError("Matching task has a different instance type; administrator review required")
            if match:
                deployment_id, action, status = match["deployment_id"], "LINKED_TO_EXISTING", match["status"]
            else:
                deployment_id = "DEP-" + uuid.uuid4().hex[:12].upper()
                con.execute("""INSERT INTO deployments
                    (deployment_id,business_key,project_id,task_id,workload,environment,region,instance_type)
                    VALUES (?,?,?,?,?,?,?,?)""",
                    (deployment_id, business_key, data["project_id"], data["task_id"],
                     data["workload"], data["environment"], data["region"], data["instance_type"]))
                action, status = "CREATED_FOR_REVIEW", "PENDING_REVIEW"
            request_id = "REQ-" + uuid.uuid4().hex[:12].upper()
            con.execute("INSERT INTO requests VALUES (?,?,?,?,?)",
                        (request_id, deployment_id, data["employee_id"], token, json.dumps(data, sort_keys=True)))
            result = dict(request_id=request_id, deployment_id=deployment_id, action=action, status=status)
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
        return [dict(row) for row in con.execute("""SELECT d.deployment_id,d.project_id,d.task_id,
            d.workload,d.environment,d.region,d.instance_type,d.status,
            COUNT(r.request_id) AS request_count
            FROM deployments d LEFT JOIN requests r USING (deployment_id)
            GROUP BY d.deployment_id ORDER BY d.deployment_id""")]
    finally:
        con.close()
