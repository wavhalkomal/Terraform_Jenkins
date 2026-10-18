# CloudLaunch Backend — architecture and safe completion checklist

## Current demonstrated workflow (no Streamlit)
1. Employee submits JSON to `python3 -m cloudlaunch.cli submit`.
2. SQLite saves each employee request separately, with unique request ID and retry token.
3. Potential duplicates get `DUPLICATE_REVIEW`; admin sees names and request IDs with `duplicates`.
4. Demo administrator issues `review --decision reject|approve --reason ...`.
5. Read-only AWS EC2 inventory via `python3 -m cloudlaunch.live_aws` verifies standardized business tags for one region/account.
6. `cloudlaunch.gate.evaluate_gate` checks local request status, duplicates and AWS candidates.
7. **New:** `cloudlaunch.deployment_guard.reserve_after_preflight` adds an atomic local reservation and audit event. It NEVER applies Terraform; tests use fake AWS.
8. **New:** `Jenkinsfile.cloudlaunch` is a separate **validation-only** pipeline to run Python tests + Terraform validation. It must use a separate Jenkins job/workspace.

## Commands for current local prototype
```bash
git pull origin feature/duplicate-request-detection
python3 -m unittest discover -s tests -v
python3 -m cloudlaunch.cli list --db cloudlaunch_new.sqlite3
python3 -m cloudlaunch.live_aws --db cloudlaunch_new.sqlite3 --request-id REQ-D641347C979E --file examples/rahul_request.json
```

For a zero-AWS demo of the reservation mechanism, run unit tests:
```bash
python3 -m unittest tests.test_deployment_guard -v
```

## What is explicitly NOT complete
- **No production authenticated user/admin API**: reviewer names are unverified labels, not identity.
- **No PostgreSQL** yet: SQLite demo file is not appropriate for enterprise distributed deployment.
- **No Terraform-managed inventory reconciliation**: AWS tag search alone misses untagged instances.
- **No request-aware Jenkins CD** that enforces the guard at apply time. Existing `terraform-standalone` job must remain untouched.
- **No real EC2 creation by CloudLaunch**. `PASS_PRELIMINARY` and `RESERVED_FOR_REVIEW` are NOT deploy permissions.
- **No multi-region/multi-account inventory**, budget, IAM scopes, secrets management, remote Terraform state, distributed locking, drift checks, or final apply-time authorization.
- **No true user-facing monitoring/dashboard**. CLI JSON reports are available only.
- GitHub PR checks/status reporting and Jenkins PR isolation/security require verification before merging.

## Production architecture to build
Authenticated API -> PostgreSQL requests & audit records -> request duplicate decision -> authorized AWS inventory across scoped accounts/regions -> manager/admin signoff -> dedicated GitHub PR -> isolated CI checks -> Terraform plan in isolated backend state -> compare plan against policy and expected budget -> Jenkins manual deployment approval -> final inventory recheck under distributed lock -> apply plan -> AWS verification -> event timeline and alerts.

Important safety rules:
- Never share one Terraform state between independent users.
- Never allow a PR-validation job to access AWS credentials or Jenkins controller secrets.
- Never deploy merely because an AWS tag search returns no matches.
- Use an enforced identity/authorization boundary; do not trust a user-supplied admin label.
- Preserve existing Terraform state in `/var/jenkins_home/workspace/terraform-standalone/terraform.tfstate`.
- Do not clean, destroy, or overwrite the old `terraform-standalone` workspace.
- Changes on this feature branch do not affect the existing deployment job until merged, but the existing job polls `main`; review a plan before merging or triggering that job.

## What tests prove
- Deterministic business-key matching and case normalization.
- Each employee receives an independent request record.
- Concurrent requests and idempotency behave as designed in a single SQLite file.
- Read-only AWS helper handles multiple result pages, candidates and failures.
- Local admin logic enforces duplicate resolution.
- Reservation logic blocks duplicate or repeated claims and records audit events.

Tests use fake EC2 responses. They do **not** demonstrate real multiuser scaling, live AWS resource reconciliation, or end-to-end CI/CD provisioning.
