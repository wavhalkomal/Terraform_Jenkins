"""Read-only EC2 inventory check for an approved infrastructure business identity.

The function accepts a boto3 EC2 client supplied by the caller. It never
creates clients or executes write operations. Callers MUST block provisioning
on errors and route matches to an authorized human review.
"""
from .requests import validate

def find_existing_ec2(ec2_client, payload):
    """Return EC2 candidates matching the business key in a single AWS region.

    Tag matching is exact in AWS. We normalize input, but existing resources
    with inconsistent/missing tags will not be discovered; this is a candidate
    search, not proof that no duplicate resources exist.
    """
    data = validate(payload)
    tags = {
        "ProjectID": data["project_id"],
        "TaskID": data["task_id"],
        "Workload": data["workload"],
        "Environment": data["environment"],
    }
    filters = [{"Name": "tag:" + key, "Values": [value]} for key, value in tags.items()]
    filters.append({"Name": "instance-state-name", "Values": [
        "pending", "running", "stopping", "stopped", "shutting-down"
    ]})
    results = []
    # Paginator correctly checks every page instead of just the first page.
    for page in ec2_client.get_paginator("describe_instances").paginate(Filters=filters):
        for reservation in page.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                results.append({
                    "instance_id": instance["InstanceId"],
                    "state": instance.get("State", {}).get("Name", "unknown"),
                    "instance_type": instance.get("InstanceType", "unknown"),
                    "same_instance_type": instance.get("InstanceType") == data["instance_type"],
                    "region": data["region"],
                    "tags": {t["Key"]: t["Value"] for t in instance.get("Tags", [])},
                })
    return results

def preflight_decision(ec2_client, payload):
    """Conservative gate: a match or AWS lookup failure means do not deploy."""
    try:
        matches = find_existing_ec2(ec2_client, payload)
    except Exception as exc:
        return {"decision": "BLOCKED_INVENTORY_UNAVAILABLE",
                "reason": type(exc).__name__, "matches": []}
    if matches:
        return {"decision": "REVIEW_EXISTING_INFRA", "matches": matches}
    return {"decision": "NO_TAGGED_MATCH_FOUND", "matches": []}
