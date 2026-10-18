# CloudLaunch — AWS Inventory Preflight (Phase 1 extension)

## Why check AWS?
An EC2 instance could already exist in AWS even if CloudLaunch has never seen it.
The request database alone is not an authoritative inventory of existing cloud resources.

## Current implementation
`cloudlaunch/aws_inventory.py` implements a read-only EC2 inventory search using an injected boto3-compatible EC2 client:
- Filters on `ProjectID`, `TaskID`, `Workload`, `Environment`, and non-terminated states.
- The caller must construct the EC2 client for the requested AWS account and region.
- Uses paginator to inspect all returned instances.
- Returns `REVIEW_EXISTING_INFRA` when candidates exist, even if instance size differs.
- Returns `BLOCKED_INVENTORY_UNAVAILABLE` if AWS lookup fails; never interpret lookup failure as proof of no duplicates.
- Returns `NO_TAGGED_MATCH_FOUND` if none match. This is **not proof** no untagged or differently tagged instance exists.

## Future integration
1. Validate and authenticate the user and AWS account authorization.
2. Validate request in the request database and check Terraform state/resource inventory.
3. Construct a read-only AWS EC2 client in the correct account and region with least-privilege `ec2:DescribeInstances` access.
4. Run `preflight_decision(client, request)`; stop and require admin review on an existing match or unavailable inventory.
5. Re-check inventory under a per-business-key concurrency lock immediately before any real provisioning, because time-of-check/time-of-use races exist.
6. Store evidence in the audit trail (account, region, matching IDs, timestamp, reviewer).
7. Only after approvals, GitHub PR checks, and a reviewed Terraform plan should Jenkins perform `terraform apply`.

## Limitations
- Tags must already be standardized on existing resources, otherwise an unrelated/untagged instance could be missed.
- A same-purpose server could live in another account or region: choose authorized inventory scope.
- Equal technical configuration does not imply the same business purpose.
- Never automatically import, adopt, delete, or update an existing instance without explicit admin approval.
- This helper is not yet wired into the CLI, database, Jenkins pipeline, or deployment gate.
- Unit tests simulate the EC2 API, so they do **not** verify real AWS access and do not create resources.

Run tests:
```bash
python3 -m unittest discover -s tests -v
```
