"""Fail-closed pre-deployment decision logic; does not call Terraform or AWS writes."""
import json
from .requests import connect, validate, business_key
from .aws_inventory import preflight_decision

def evaluate_gate(db_path, request_id, ec2_client):
    """Read-only check. A 'PASS_PRELIMINARY' is never permission to run Terraform."""
    con = connect(db_path)
    try:
        row = con.execute("SELECT * FROM requests WHERE request_id=?", (request_id,)).fetchone()
        if row is None:
            return {"decision": "BLOCKED_UNKNOWN_REQUEST"}
        if row["status"] != "APPROVED":
            return {"decision": "BLOCKED_NOT_APPROVED", "status": row["status"]}
        data = validate(json.loads(row["request_json"]))
        others = con.execute(
            """SELECT request_id,employee_id,status FROM requests
               WHERE business_key=? AND request_id<>? AND status!='REJECTED'""",
            (business_key(data), request_id)
        ).fetchall()
        if others:
            return {"decision": "BLOCKED_DUPLICATE_REQUESTS", "matches": [dict(x) for x in others]}
        inventory = preflight_decision(ec2_client, data)
        if inventory["decision"] != "NO_TAGGED_MATCH_FOUND":
            return {"decision": "BLOCKED_AWS_CHECK", "inventory": inventory}
        return {"decision": "PASS_PRELIMINARY", "request_id": request_id,
                "note": "Read-only preliminary check only; not an authorization to deploy."}
    finally:
        con.close()
