"""Atomic deployment reservation after review + AWS preflight. NO Terraform apply.

A reservation prevents two CloudLaunch requests for one business task from
being released for provisioning simultaneously. This is not a distributed lock
against manual AWS changes or other provisioning systems.
"""
import json
import sqlite3
from .requests import connect, validate, business_key
from .aws_inventory import preflight_decision

def prepare_tables(con):
    con.executescript("""
        CREATE TABLE IF NOT EXISTS deployment_reservations (
            business_key TEXT PRIMARY KEY,
            request_id TEXT NOT NULL UNIQUE REFERENCES requests(request_id),
            status TEXT NOT NULL CHECK(status IN ('RESERVED','CANCELLED')),
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        );
        CREATE TABLE IF NOT EXISTS audit_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT NOT NULL,
            event TEXT NOT NULL,
            detail TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        );
    """)

def reserve_after_preflight(db_path, request_id, ec2_client):
    """Read AWS first, then reserve one business identity atomically.

    This function NEVER authorizes AWS writes. Re-check all conditions from
    an authenticated CI worker immediately before a future real apply.
    """
    con = connect(db_path)
    try:
        prepare_tables(con)
        row = con.execute("SELECT * FROM requests WHERE request_id=?", (request_id,)).fetchone()
        if row is None:
            return {"decision": "BLOCKED_UNKNOWN_REQUEST"}
        if row["status"] != "APPROVED":
            return {"decision": "BLOCKED_NOT_APPROVED", "status": row["status"]}
        data = validate(json.loads(row["request_json"]))
        inventory = preflight_decision(ec2_client, data)
        if inventory["decision"] != "NO_TAGGED_MATCH_FOUND":
            return {"decision": "BLOCKED_AWS_CHECK", "inventory": inventory}
        con.execute("BEGIN IMMEDIATE")
        current = con.execute("SELECT status,business_key FROM requests WHERE request_id=?", (request_id,)).fetchone()
        if current is None or current["status"] != "APPROVED":
            con.rollback()
            return {"decision": "BLOCKED_STATUS_CHANGED"}
        conflicts = con.execute(
            """SELECT request_id,employee_id,status FROM requests
               WHERE business_key=? AND request_id<>? AND status!='REJECTED'""",
            (current["business_key"], request_id)
        ).fetchall()
        if conflicts:
            con.rollback()
            return {"decision": "BLOCKED_DUPLICATE_REQUESTS", "matches": [dict(r) for r in conflicts]}
        existing = con.execute(
            "SELECT request_id,status FROM deployment_reservations WHERE business_key=?",
            (current["business_key"],)
        ).fetchone()
        if existing and existing["status"] == "RESERVED":
            con.rollback()
            return {"decision": "BLOCKED_ALREADY_RESERVED", "request_id": existing["request_id"]}
        if existing:
            con.execute(
                """UPDATE deployment_reservations SET request_id=?,status='RESERVED',
                   created_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE business_key=?""",
                (request_id, current["business_key"])
            )
        else:
            con.execute(
                "INSERT INTO deployment_reservations(business_key,request_id,status) VALUES(?,?,'RESERVED')",
                (current["business_key"], request_id)
            )
        con.execute(
            "INSERT INTO audit_events(request_id,event,detail) VALUES(?,?,?)",
            (request_id, "RESERVATION_CREATED",
             json.dumps({"aws_preflight": inventory["decision"], "requires_manual_deployment": True}))
        )
        con.commit()
        return {"decision": "RESERVED_FOR_REVIEW", "request_id": request_id,
                "terraform_apply_allowed": False}
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

def reservation_report(db_path):
    con = connect(db_path)
    try:
        prepare_tables(con)
        return [dict(r) for r in con.execute(
            """SELECT d.request_id,d.status,d.created_at,r.employee_id
               FROM deployment_reservations d JOIN requests r ON d.request_id=r.request_id
               ORDER BY d.created_at"""
        )]
    finally:
        con.close()

def audit_report(db_path):
    con = connect(db_path)
    try:
        prepare_tables(con)
        return [dict(r) for r in con.execute(
            "SELECT * FROM audit_events ORDER BY event_id"
        )]
    finally:
        con.close()
