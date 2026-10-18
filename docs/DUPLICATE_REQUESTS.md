# CloudLaunch — Duplicate Request Detection (Phase 1)

## Why
Two employees may be assigned the same business task and submit two requests for one EC2 instance. We must not accidentally deploy two servers.

## Terminology
- **Request:** One employee's submission (each employee gets their own request ID).
- **Deployment:** One canonical infrastructure requirement, initially `PENDING_REVIEW`.
- **Business key:** normalized `project_id + task_id + workload + environment + region`.
- **Idempotency key:** client-generated unique token reused if the same submission is retried.

## Behavior
- Different employees, same business key and instance size: two requests, **one deployment record**.
- Same employee retries with the same idempotency token: returns the same request.
- Same business key but different instance size: stopped for human review.
- Different business task: independent deployment record.
- Simultaneous local submissions: SQLite's `BEGIN IMMEDIATE` transaction plus a unique key prevent duplicate canonical records.

This is a local **business-logic prototype**, not a production multiuser application. Same identity matching is a heuristic and may need human confirmation: managers may intentionally order multiple servers for one task. Later add a distinct workload-instance identifier, ownership policies, audit logs, PostgreSQL, authenticated APIs, and an admin reconciliation flow.

## Run locally (Python standard library only)
From the repository root:

```bash
python3 -m unittest discover -s tests -v
python3 -m cloudlaunch.cli submit --db cloudlaunch_demo.sqlite3 --file examples/rahul_request.json --key click-rahul-1
python3 -m cloudlaunch.cli submit --db cloudlaunch_demo.sqlite3 --file examples/priya_request.json --key click-priya-1
python3 -m cloudlaunch.cli list --db cloudlaunch_demo.sqlite3
```

The two CLI submissions should return **different request IDs**, the **same deployment ID**, and `CREATED_FOR_REVIEW` then `LINKED_TO_EXISTING`. The listing should show `request_count: 2`.

## Safety
- No AWS calls, Jenkins builds, Terraform plans, or Terraform applies.
- **Do not run this demo on real infrastructure.** No real provisioning integration exists in this phase.
- Keep SQLite files local; do not commit them.
- The current `terraform-standalone` workspace state and EC2 resource are unchanged.
- Future phase: GitHub PR + Jenkins tests + review + Terraform plan + admin approval, all tied to the canonical deployment ID.
