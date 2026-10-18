"""Run a read-only EC2 preflight from the developer's local environment.

Requires boto3 and AWS read permissions. This script NEVER applies Terraform.
"""
import argparse
import json
from .requests import validate
from .aws_inventory import preflight_decision
from .gate import evaluate_gate

def main():
    parser = argparse.ArgumentParser(description="Read-only AWS EC2 inventory preflight")
    parser.add_argument("--file", required=True, help="JSON request file")
    parser.add_argument("--profile", help="Optional AWS profile (uses default if absent)")
    parser.add_argument("--db", help="Local CloudLaunch database for preliminary gate")
    parser.add_argument("--request-id", help="Existing approved request ID (requires --db)")
    args = parser.parse_args()
    if bool(args.db) != bool(args.request_id):
        parser.error("--db and --request-id must be supplied together")
    with open(args.file, encoding="utf-8") as stream:
        data = validate(json.load(stream))
    try:
        import boto3
        session = boto3.Session(profile_name=args.profile) if args.profile else boto3.Session()
        client = session.client("ec2", region_name=data["region"])
        identity = session.client("sts", region_name=data["region"]).get_caller_identity()
        if args.db:
            result = evaluate_gate(args.db, args.request_id, client)
        else:
            result = preflight_decision(client, data)
        print(json.dumps({
            "aws_account": identity["Account"], "region": data["region"],
            "result": result
        }, indent=2))
        if result.get("decision") not in {"NO_TAGGED_MATCH_FOUND", "PASS_PRELIMINARY"}:
            raise SystemExit(2)
    except Exception as exc:
        # Never treat missing permissions or connectivity errors as a clean inventory.
        print(json.dumps({"decision": "BLOCKED_AWS_UNAVAILABLE",
                          "error_type": type(exc).__name__}, indent=2))
        raise SystemExit(2)

if __name__ == "__main__":
    main()
