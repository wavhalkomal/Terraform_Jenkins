# CloudLaunch — GitHub, Jenkins, Terraform & AWS EC2 CI/CD

CloudLaunch is a **tested EC2 infrastructure automation project**, not a Streamlit website.

## Implemented and verified

1. GitHub PR / GitHub Actions runs Python unit tests, validates repository changes, and checks Terraform code. **No AWS credentials are used by PR CI.**
2. Dedicated Jenkins `cloudlaunch-dispatch` polls `main` and automatically forwards newly added `requests/*.json` files to `cloudlaunch-cd`.
3. Jenkins `cloudlaunch-cd` validates each request, performs a **read-only AWS duplicate check**, and blocks requests for already-provisioned business infrastructure.
4. If eligible, it initializes an isolated S3 Terraform backend, validates that the plan creates exactly **one EC2 instance**, requests human approval, rechecks AWS and applies.
5. Jenkins and AWS logs record the result. Intended duplicate blocks can appear as Jenkins `FAILURE` (exit code 3), but **no Terraform apply occurs**.

### Verified end-to-end test cases

| Request | Scenario | Observed Jenkins result |
|---|---|---|
| `requests/REQ-1001.json` | Rahul requests payment-api EC2 | One real EC2 successfully created after human approval |
| `requests/REQ-1002.json` | Different employee requests same business infrastructure at a different size | `BLOCKED / ALREADY_PROVISIONED`, no new EC2 |
| `requests/REQ-1003.json` | GitHub merge automatically triggers dispatcher and CD | Automatically dispatched and blocked as duplicate, no Terraform apply |

**The test EC2 servers were subsequently deleted to avoid AWS charges.** Do not infer that the servers remain running. Terraform state may need reconciliation before any future deployment.

## Repository structure

- `.github/workflows/python-app.yml` — GitHub Actions validation
- `Jenkinsfile.pr` — Jenkins PR validation
- `Jenkinsfile.cloudlaunch.dispatch` — automatic request dispatcher (polls `main`)
- `Jenkinsfile.cloudlaunch.cd` — request-aware AWS Terraform deployment with approval and guardrails
- `cloudlaunch/` — Python requests, AWS inventory and duplicate-decision prototype
- `cloudlaunch_cd/` — request validation, AWS checks, independent state, Terraform plan guard
- `infra/cloudlaunch_ec2/` — Terraform CloudLaunch EC2 resource
- `requests/` — three original end-to-end request JSONs
- `tests/` — CI/CD and request guard unit tests
- `docs/AUTOMATIC_DISPATCH.md`, `docs/CLOUDLAUNCH_END_TO_END.md` — setup and workflow detail

Legacy standalone Jenkins/Terraform files (`Jenkinsfile`, `main.tf`, `post_deployment_check.sh`) are retained because they belong to the original working CI/CD test and may still be referenced by the `terraform-standalone` job. The `LICENSE` and Terraform provider lockfile also remain.

## Validate locally (no AWS deployment)

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q cloudlaunch cloudlaunch_cd tests
terraform -chdir=infra/cloudlaunch_ec2 fmt -check
terraform -chdir=infra/cloudlaunch_ec2 init -backend=false -input=false
terraform -chdir=infra/cloudlaunch_ec2 validate
```

## Operational safety after test cleanup

- The original EC2 instances are gone. **Disable automatic deployment-capable Jenkins jobs** unless you explicitly intend to provision new billable EC2 resources.
- Never delete Terraform state manually to hide resources. Reconcile old Jenkins local state and CloudLaunch S3 state separately after direct AWS termination.
- Never commit IAM keys, Terraform state, secrets or credentials.
- Do **not** rerun old request JSONs as new deployments without explicit intent and review.
- This is a functioning **controlled CI/CD project**, not a fully hardened public multi-tenant service. GitHub branch protection, narrowly scoped AWS roles, isolated Jenkins agents, operational notifications, persistent approvals and safe destroy/reconciliation workflows would be needed for production use.

## Additional technical detail

See [Automatic Dispatch](docs/AUTOMATIC_DISPATCH.md), [End-to-End CI/CD](docs/CLOUDLAUNCH_END_TO_END.md), and [Request Review and Preflight](docs/REVIEW_AND_PREFLIGHT.md).
