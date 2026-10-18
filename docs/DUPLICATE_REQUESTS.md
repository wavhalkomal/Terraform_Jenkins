# CloudLaunch — Duplicate request detection (without UI)

## The business problem
Multiple employees may receive one manager task and submit separate EC2 requests. Creating a server for each submission can waste money and cause resource sprawl.

## What currently works in this draft
- Every employee submission is an **independent request** with its own `REQ-...` ID. Requests are **not merged**.
- A normalized business fingerprint uses project, task, workload, environment and region. Instance size conflicts also flag review instead of being treated as distinct work.
- A repeated submission with the same employee + idempotency token returns the original request, without duplication.
- When multiple active requests have the same fingerprint, earlier pending requests and the new one are labeled `DUPLICATE_REVIEW`. The `duplicates` command lists employee IDs, request IDs, and timestamps.
- SQLite transactions serialize concurrent local submissions.
- Unit tests include 100 simultaneous employee requests.
- The separate `aws_inventory.py` helper performs **read-only** matching by AWS tags when a boto3 EC2 client is supplied. It is not connected to CLI or provisioning yet.

## Run on your Mac
On the feature branch `feature/duplicate-request-detection` in the repository root:

```bash
python3 -m unittest discover -s tests -v
python3 -m cloudlaunch.cli submit --db cloudlaunch_demo.sqlite3 --file examples/rahul_request.json --key rahul-click-1
python3 -m cloudlaunch.cli submit --db cloudlaunch_demo.sqlite3 --file examples/priya_request.json --key priya-click-1
python3 -m cloudlaunch.cli duplicates --db cloudlaunch_demo.sqlite3
python3 -m cloudlaunch.cli list --db cloudlaunch_demo.sqlite3
```

Expect two separate REQ IDs, a duplicate warning for Priya, and the duplicate report showing both employee IDs. **No EC2 is provisioned.**

## Critical limits
- This is SQLite prototype code, NOT a production authenticated backend. Use PostgreSQL, authorized APIs, and an audit trail before deployment integration.
- Project/workload/task matching is an imperfect heuristic. A legitimate request for multiple servers could look identical. Every flagged request needs human review.
- The current database does not yet implement admin approve/reject actions.
- Existing databases from the prior prototype have a different schema. Use a NEW demo database name; do not point the new code at the old prototype database.
- AWS inventory filtering only finds correctly tagged instances within a supplied AWS account and region. Missing tags and other accounts/regions can conceal an existing server.
- There is **no integrated deployment blocking gate** yet. Do not rely on this prototype to prevent your existing Jenkins job from provisioning.
- Keep `terraform-standalone`, its workspace, local state, and current EC2 instance unchanged.
