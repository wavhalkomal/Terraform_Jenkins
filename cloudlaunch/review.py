"""Local administrator review records. Prototype ONLY: no authenticated identity."""
from .requests import connect, normalize

def review_request(db_path, request_id, decision, reviewer, reason):
    """Record a review, but never authorize an infrastructure deployment directly."""
    if decision not in {"approve", "reject"}:
        raise ValueError("Decision must be approve or reject")
    reviewer, reason = normalize(reviewer), normalize(reason)
    con = connect(db_path)
    try:
        con.execute("BEGIN IMMEDIATE")
        current = con.execute(
            "SELECT request_id,status,business_key FROM requests WHERE request_id=?",
            (request_id,)
        ).fetchone()
        if current is None:
            raise ValueError("Unknown request ID")
        if current["status"] not in {"PENDING_REVIEW", "DUPLICATE_REVIEW"}:
            raise ValueError("Request has already been reviewed or processed")
        if decision == "approve":
            # Never approve while another non-rejected request for this task exists.
            duplicates = con.execute(
                """SELECT COUNT(*) FROM requests
                   WHERE business_key=? AND request_id<>? AND status!='REJECTED'""",
                (current["business_key"], request_id)
            ).fetchone()[0]
            if duplicates:
                raise ValueError("Other non-rejected matching requests exist; review or reject them first")
            status = "APPROVED"
        else:
            status = "REJECTED"
        con.execute(
            """UPDATE requests SET status=?,reviewed_by=?,review_reason=? WHERE request_id=?""",
            (status, reviewer, reason, request_id)
        )
        con.commit()
        return {"request_id": request_id, "status": status, "reviewed_by": reviewer,
                "reason": reason, "deployment_authorized": False}
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
