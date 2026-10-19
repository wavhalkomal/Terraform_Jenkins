# CloudLaunch — End-to-End GitHub → Jenkins → Terraform → AWS CI/CD

**CloudLaunch is the CI/CD project we built and tested, not a Streamlit application.** This repository contains the original Terraform/Jenkins proof-of-concept, a request-aware CloudLaunch deployment pipeline, an automatic GitHub-to-Jenkins dispatcher, Python duplicate-prevention logic, GitHub Actions checks, and documentation.

> **Current cost-safety state:** The test EC2 instances were terminated after the successful tests. The Terraform states can still refer to those instances. Do not launch the deployment jobs until you intend to provision and have reviewed/reconciled the state and estimated AWS costs. Do not delete Jenkins volumes or Terraform state to "fix" this.

## 1. Tested end-to-end architecture

```text
Employee / engineer creates a new requests/REQ-xxxx.json file
    ↓
Git: branch → commit → push → GitHub pull request
    ↓
GitHub Actions + Jenkins PR validation (Python tests and Terraform validation)
    ↓
Reviewed PR merged to main
    ↓
Jenkins cloudlaunch-dispatch (SCM polling on local Mac, roughly every 2 minutes)
    ↓
Detects newly ADDED requests/*.json paths; queues cloudlaunch-cd
    ↓
CloudLaunch CD checks request → real AWS EC2 duplicate lookup
    ├── existing matching EC2 → BLOCKED / ALREADY_PROVISIONED; no Terraform apply
    └── no match → prepare isolated S3 backend → Terraform plan → one-EC2 plan guard
                                                ↓
                                       Jenkins human approval
                                                ↓
                                 repeat AWS duplicate check
                                                ↓
                                      Terraform apply to AWS
```

The dispatcher was verified to start automatically from an SCM change and trigger `cloudlaunch-cd`. The duplicate job deliberately ends as Jenkins **FAILURE** (exit 3) to stop provisioning; this is expected.

| Request | What was tested | Verified result |
|---|---|---|
| `REQ-1001` | First employee requests payment-api infrastructure | Jenkins approval and Terraform created **one real EC2 instance** |
| `REQ-1002` | Different employee requests same business purpose with a different size | Real AWS inventory detects original and **blocks creation** |
| `REQ-1003` | New request merged in GitHub | Dispatcher automatically queues downstream CD; **duplicate blocked** |

The created EC2 was later terminated to stop charges. This document does not claim any test EC2 is still running.

## 2. Technologies — what each does

| Technology | Use in CloudLaunch |
|---|---|
| **Git / GitHub** | Version control, feature branches, commits, pushes, pull requests and protected deployment branch |
| **GitHub Actions** | Runs Python tests and syntax checks when code is pushed or a PR is opened |
| **Docker** | Runs the Jenkins controller locally on the Mac with persistent Jenkins configuration and plugins |
| **Jenkins** | Executes pipeline stages, polls GitHub, dispatches requests, uses AWS credentials and pauses for human approval |
| **Python 3** | Request validation, business-key generation, AWS inventory / duplicate logic and automated tests |
| **Boto3** | Read-only EC2 checks inside approved Jenkins stages |
| **AWS CLI** | Checks current AWS identity, EC2 inventory and other AWS resources |
| **Terraform** | Describes and creates the EC2 instance and tracks infrastructure in state |
| **Amazon EC2** | Test AWS server(s) used to prove real provisioning |
| **Amazon S3** | Separate private Terraform state backend for CloudLaunch requests |

No Streamlit, front-end server, or website packages are required.

## 3. Repository layout — important files

```text
Terraform_Jenkins/
├── .github/workflows/python-app.yml      # GitHub Actions validation
├── Jenkinsfile                            # Original standalone EC2 deployment (legacy)
├── Jenkinsfile.pr                         # Validation-only PR pipeline
├── Jenkinsfile.cloudlaunch                # Validation-only CloudLaunch pipeline
├── Jenkinsfile.cloudlaunch.dispatch       # Automatically queues new merged requests
├── Jenkinsfile.cloudlaunch.cd             # Request-aware AWS duplicate checks & Terraform CD
├── main.tf                                # Original standalone Terraform EC2 (legacy)
├── post_deployment_check.sh               # Original standalone post-deployment EC2 checks
├── cloudlaunch/                           # Request storage/validation and review prototype
├── cloudlaunch_cd/                        # Real CD request validation, AWS gate, plan guard
├── infra/cloudlaunch_ec2/
│   ├── main.tf                            # CloudLaunch EC2 Terraform configuration
│   └── variables.tf                       # Terraform inputs
├── requests/
│   ├── REQ-1001.json                      # Successful EC2 creation test
│   ├── REQ-1002.json                      # First duplicate block
│   └── REQ-1003.json                      # Automatic dispatch / duplicate block
├── tests/                                 # Python unit tests
├── examples/                              # Local request examples
└── docs/                                  # CI/CD pipeline and safeguards documentation
```

Do not delete the legacy files just because their names differ: they belong to the original `terraform-standalone` Jenkins project.

## 4. Prerequisites and versions

Mac with Terminal, Git, Docker Desktop, AWS CLI v2, Python 3, and Terraform. Docker must be running before the Jenkins controller can be used. The tested custom Jenkins image was `jenkins-terraform-aws:1.2` (Terraform, Python, AWS CLI and plugins available in container). Terraform for `infra/cloudlaunch_ec2` requires >= 1.10; check your machine/container version before running commands.

```bash
git --version
docker --version
docker ps
python3 --version
terraform version
aws --version
```

The host Mac's AWS profile is separate from the AWS credentials installed in Jenkins; confirm your intended account before any AWS change.

## 5. Git workflow: clone, branch, commit, push, pull and PR

### Clone once and inspect

```bash
git clone https://github.com/wavhalkomal/Terraform_Jenkins.git
cd Terraform_Jenkins
git status
git branch -a
git remote -v
```

If you already cloned it, do not clone a second copy. In your existing project directory, get the latest reviewed changes:

```bash
git switch main
git pull --ff-only origin main
git log --oneline -5
```

### Make a feature branch

```bash
git switch main
git pull --ff-only origin main
git switch -c feature/my-ci-improvement
```

Edit your Jenkinsfile, Python tests, Terraform file or documentation. Review exactly which files changed:

```bash
git status --short
git diff
git diff --check
git add README.md
git status --short
git commit -m "docs: explain CloudLaunch workflow"
git push -u origin feature/my-ci-improvement
```

**Never use `git add .` blindly** if your working directory might include Terraform state, credentials, local logs or generated files. Check `git status` and `.gitignore`.

Go to the GitHub repository and open a pull request from your feature branch to `main`. Wait for GitHub Actions to pass and review the change before merging. Once merged, update the local checkout:

```bash
git switch main
git pull --ff-only origin main
git branch -d feature/my-ci-improvement
```

Useful commands:

```bash
git fetch origin                    # Download remote refs, don't merge
git diff main...feature/my-ci-improvement
git log --graph --oneline --all -12
git show HEAD
git restore -- README.md            # DISCARDS uncommitted edits to this file
```

**Important:** only newly **added** JSON files directly under `requests/` are dispatched. Editing old request JSONs does not trigger a new CloudLaunch CD request. Do not add a new request to `main` unless you're intentionally preparing to deploy infrastructure.

## 6. Docker: Jenkins controller on your Mac

Existing setup used a Jenkins Docker container named `jenkins` reachable from the Mac at `http://localhost:8080`. The custom image had Terraform, Python, Git, AWS CLI and Jenkins plugins.

### Inspect and control the existing container

```bash
docker ps -a
docker images
docker inspect jenkins --format '{{.Config.Image}}'
docker logs --tail 60 jenkins
docker exec jenkins sh -c 'pwd; git --version; terraform version; python3 --version; aws --version'
docker stop jenkins                 # Pause Jenkins and SCM polling
docker start jenkins                # Restart the existing persistent container
```

Avoid `docker rm jenkins`, `docker volume rm ...` or rebuilding/replacing the container until you have checked the mounted `/var/jenkins_home` volume and backed up all Jenkins configuration and **state**. Starting a replacement container without the existing Jenkins volume can lose jobs, plugins, credential IDs and job history.

Jenkins UI: <http://localhost:8080>. This localhost address is available only on your own Mac. GitHub cannot deliver a webhook to localhost. CloudLaunch therefore uses SCM polling rather than public Jenkins exposure.

### Docker components explained

- **Image:** the reusable filesystem/runtime template (`jenkins-terraform-aws:1.2` was used).
- **Container:** running Jenkins process named `jenkins`.
- **Volume:** persistent `/var/jenkins_home` data, including job configurations and workspaces.
- **Port mapping:** Mac's `localhost:8080` connects to container Jenkins' web interface (when mapped at container creation).

The command `docker exec` runs a shell command **inside the container**, not on AWS. `docker stop` does **not** destroy Jenkins or Terraform state.

## 7. AWS CLI: verify identity and cost-sensitive resources

Your original experiments used region `us-east-1` for CloudLaunch. AWS commands below are **read-only** unless explicitly stated otherwise.

```bash
aws sts get-caller-identity
aws ec2 describe-instances --region us-east-1 \
  --query 'Reservations[].Instances[].{ID:InstanceId,State:State.Name,Type:InstanceType}' \
  --output table
aws ec2 describe-volumes --region us-east-1 --output table
aws ec2 describe-addresses --region us-east-1 --output table
aws s3api head-bucket --bucket cloudlaunch-tfstate-562169195386-2026
```

The existing **S3 state bucket** `cloudlaunch-tfstate-562169195386-2026` holds Terraform state and should not be emptied or deleted as casual cleanup. S3 data itself can incur small storage charges. A successful `aws sts get-caller-identity` proves an identity was obtained; it does not prove sufficient, correctly scoped permissions.

**Never put AWS keys in code, request JSONs, logs, pull requests or the README.** The Jenkins CD uses the Jenkins credential ID `aws-jenkins-terraform` via `withAWS`. Existing proof-of-concept permissions were broad; production systems need narrowly scoped roles.

## 8. Python CLI and automated tests (safe: no EC2 creation)

Run tests on the Mac or in the Jenkins environment:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q cloudlaunch cloudlaunch_cd tests
python3 -m cloudlaunch_cd.workflow validate --file requests/REQ-1001.json
python3 -m cloudlaunch_cd.workflow validate --file requests/REQ-1002.json
python3 -m cloudlaunch_cd.workflow validate --file requests/REQ-1003.json
```

The `validate` command checks request fields and computes a **business identity/state key**, but does not create cloud resources. The business identity is based on project, task, workload, environment and region—not employee, EC2 size or AMI. This is why requests from different people for the same server can be blocked as duplicates.

Python `unittest` exercises duplicate normalization, fake AWS inventory responses, approval guards, Terraform plan actions and related logic. All tests must pass before merging.

## 9. Terraform commands — validation, plan, apply and state

### Safe syntax/format checks (no AWS provisioning)

```bash
terraform -chdir=infra/cloudlaunch_ec2 fmt -check
terraform -chdir=infra/cloudlaunch_ec2 init -backend=false -input=false
terraform -chdir=infra/cloudlaunch_ec2 validate
```

`fmt -check` verifies Terraform formatting. `init -backend=false` downloads/initializes providers without connecting to the real S3 state backend. `validate` checks Terraform configuration. None of these commands provisions EC2.

### What Jenkins does for a real approved CloudLaunch deployment

```text
python3 -m cloudlaunch_cd.workflow validate --file requests/REQ-xxxx.json
python3 -m cloudlaunch_cd.workflow check-aws --file requests/REQ-xxxx.json
python3 -m cloudlaunch_cd.workflow prepare --file requests/REQ-xxxx.json --output-dir <isolated-build-directory>

# IN THE ISOLATED JOB DIRECTORY WITH APPROVED BACKEND CONFIGURATION:
terraform init -backend-config=backend.hcl -input=false -no-color
terraform validate -no-color
terraform plan -input=false -out=tfplan -no-color
terraform show -json tfplan > tfplan.json
python3 -m cloudlaunch_cd.plan_guard tfplan.json

# THEN, ONLY AFTER A REAL JENKINS HUMAN APPROVAL AND A SECOND AWS DUPLICATE CHECK:
terraform apply -input=false -no-color tfplan
terraform output -json
```

The above is **an explanation**, not a command sequence to paste and run from the repository root. Backend configuration, approved credentials and isolated working directory are prepared within the Jenkins CD pipeline. Running `terraform plan`, `apply` or `destroy` from the wrong working directory or with the wrong state could unexpectedly create or destroy infrastructure.

Terraform concepts:
- **`.tf` files:** desired infrastructure specification.
- **`terraform init`:** initialize provider modules and state backend.
- **`terraform plan`:** compare current real resources/state against desired configuration.
- **`terraform apply`:** actually change AWS resources (billable).
- **State:** maps Terraform resource addresses to real infrastructure. CloudLaunch uses **isolated S3 state per business purpose**, while the legacy standalone job used local Jenkins workspace state.
- **Lock:** prevents two Terraform operations from concurrently modifying the same state.
- **`terraform destroy`:** permanently removes infrastructure; should only run against reviewed target state with intentional authorization, never against an unrelated workspace.

### Legacy Terraform example (separate from CloudLaunch)

The original `main.tf` and `Jenkinsfile` manage `aws_instance.foo` (tag `TF-Instance`). The CloudLaunch code manages `aws_instance.server` in `infra/cloudlaunch_ec2`. **These must not share Terraform state.**

## 10. Jenkins: job configuration and automatic triggering

Configure separate Jenkins **Pipeline from SCM** jobs:

| Jenkins job | Jenkinsfile path | Purpose |
|---|---|---|
| `terraform-standalone` | `Jenkinsfile` | Legacy separate EC2 Terraform pipeline; currently should remain disabled after test cleanup |
| `Terraform_Jenkins` / PR job | `Jenkinsfile.pr` | PR checks; no credentials or apply |
| `cloudlaunch-dispatch` | `Jenkinsfile.cloudlaunch.dispatch` | Poll `main`, discover **new** JSON requests and queue CD |
| `cloudlaunch-cd` | `Jenkinsfile.cloudlaunch.cd` | Read request, check real AWS, plan, approve, apply |
| Optional dry-run job | `Jenkinsfile.cloudlaunch` | Validation-only checks |

SCM URL: `https://github.com/wavhalkomal/Terraform_Jenkins.git`. Trusted deployment jobs use `main` (often configured as `*/main` in Jenkins UI).

The dispatcher Jenkinsfile contains `pollSCM('H/2 * * * *')`: Jenkins checks the GitHub repository about every two minutes *while the Mac and Jenkins are running*. It stores its processed-commit cursor in `.cloudlaunch-dispatch-last-commit` in the dispatcher workspace. Do not clean this workspace casually.

### Jenkins UI workflow

1. Open <http://localhost:8080>.
2. Open `cloudlaunch-dispatch` and confirm SCM trigger logs.
3. When a **new request file** is merged, look for `New request files to dispatch: [requests/REQ-xxxx.json]` and `Queued cloudlaunch-cd for requests/REQ-xxxx.json`.
4. Open `cloudlaunch-cd` and inspect its **Console Output** and individual stages.
5. Duplicate match prints `"decision": "BLOCKED"` and `"reason": "ALREADY_PROVISIONED"` and deliberately stops **before** Terraform Plan/Apply.
6. New, eligible request produces a plan, then waits for the authorized human input step. Only approval permits the final check and apply.

For an authorized manual diagnostic CD run, Jenkins' **Build with Parameters** takes:

```text
REQUEST_FILE = requests/REQ-xxxx.json
```

**Do not manually rerun `REQ-1001`, `REQ-1002`, or `REQ-1003` now.** The existing EC2 instances were removed, so earlier "duplicate" assumptions may no longer apply; a rerun can unexpectedly create a new billable EC2 instance.

**Production warning:** Jenkins PR validation currently runs on the Jenkins controller in this lab; untrusted contributors should use isolated no-secret agents instead. Human approval is in Jenkins, not an authenticated organization-wide service portal.

## 11. Example request JSON

The actual example file `requests/REQ-1001.json` contains the required fields:

```json
{
  "request_id": "REQ-1001",
  "employee_id": "rahul",
  "project_id": "pay-2026",
  "task_id": "task-450",
  "workload": "payment-api",
  "environment": "dev",
  "region": "us-east-1",
  "instance_type": "t3.micro",
  "ami_id": "ami-05fa00d4c63e32376"
}
```

A different employee submitting the same **project/task/workload/environment/region** is a business duplicate even if their `instance_type` differs. An AMI must exist in the target region; copying this historical example is **not** a guarantee of ongoing AMI availability.

For future **intentional** tests, create a new `requests/REQ-NEW.json` on a reviewed branch, run the tests, open a PR and merge only with explicit authorization and cost expectations.

## 12. Cleanup and Terraform state consistency

The test EC2 servers were terminated using AWS tools after the project succeeded, avoiding ongoing EC2 instance compute charges. That operation does **not** automatically repair Terraform state.

- CloudLaunch remote state: S3 bucket `cloudlaunch-tfstate-562169195386-2026`, per-business key `cloudlaunch/requests/a9d1426c620f7978a5f4471a/terraform.tfstate`.
- Legacy state: Jenkins workspace `/var/jenkins_home/workspace/terraform-standalone/terraform.tfstate`.
- Preserve state backups. Review `terraform plan -refresh-only` with each correct backend in a controlled environment before deciding on `state rm`, `apply -refresh-only`, or a fully authorized destroy/reconciliation operation. Do not perform those operations blindly.
- Keep deployment-capable Jenkins jobs disabled if AWS spend must remain zero. GitHub Actions unit tests do not create EC2.
- Check EBS volumes, snapshots, Elastic IP allocations, and S3 costs separately; terminating EC2 does not always remove them.

Safe inspections:

```bash
docker ps -a
aws sts get-caller-identity
aws ec2 describe-instances --region us-east-1 --output table
aws ec2 describe-volumes --region us-east-1 --output table
```

## 13. Troubleshooting

| Symptom | What to inspect |
|---|---|
| GitHub CI fails | Actions job logs, Python version, tests, YAML syntax |
| Jenkins not reachable | `docker ps -a`, `docker logs --tail 60 jenkins`, correct port mapping |
| No automatic dispatch | Jenkins job enabled, SCM Polling Log, Mac online, `main` branch configured |
| Dispatcher sees `[]` | Request must be **added** in `requests/` and merged; inspect Git diff and persisted cursor |
| Duplicate CD build shows red FAILURE | Read `check-aws` log; intentional `BLOCKED / ALREADY_PROVISIONED` is safety success |
| Terraform init fails | AWS identity, S3 backend access, provider installation, state lock |
| EC2 missing after test cleanup | Expected if terminated; never assume old state represents a live server |
| Terraform wants to recreate an EC2 | State and real AWS diverged; stop and reconcile before apply |
| AWS permissions fail | Validate scoped Jenkins AWS role and correct region/account without printing secrets |

## 14. Further reference docs

- [Automatic Jenkins Dispatch](docs/AUTOMATIC_DISPATCH.md)
- [End-to-End CloudLaunch EC2 Workflow](docs/CLOUDLAUNCH_END_TO_END.md)
- [AWS Inventory Duplicate Checks](docs/AWS_INVENTORY_CHECK.md)
- [Request Duplicate Matching](docs/DUPLICATE_REQUESTS.md)
- [PR and Validation Workflow](docs/PR_WORKFLOW.md)
- [Review and Preflight Safety](docs/REVIEW_AND_PREFLIGHT.md)

**Scope:** This project is a verified, controlled GitHub/Jenkins/Terraform/AWS CI/CD solution. It is **not** an authenticated multi-tenant enterprise SaaS system, and **no Streamlit app is part of this repository.**

Copyright © Komal Wavhal 2026
