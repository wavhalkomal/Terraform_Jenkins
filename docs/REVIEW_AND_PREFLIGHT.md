# CloudLaunch — Review and AWS preflight (no UI)

## What each component means
- `requests.py`: each employee submits an independent request. Matching project/task/workload/environment/region gets a duplicate warning.
- `review.py`: demo admin records **approve** or **reject** with a reason. If two non-rejected requests match, approval is refused until duplicates are resolved.
- `aws_inventory.py`: queries AWS EC2 **read only** by standardized tags.
- `gate.py`: checks request status, competing requests, and AWS inventory. Failures block.
- `live_aws.py`: real AWS read-only inventory command for a developer's Mac, using locally configured boto3 credentials.
- `cli.py`: create/list/review demo requests.

## Step 1: run all unit tests
```bash
python3 -m unittest discover -s tests -v
```
Unit tests mock AWS; **no AWS credentials are required**.

## Step 2: use your existing NEW-SCHEMA demonstration database
Use `cloudlaunch_new.sqlite3` created for this branch, not the older `cloudlaunch_demo.sqlite3` from the obsolete linked-deployment prototype.

```bash
python3 -m cloudlaunch.cli duplicates --db cloudlaunch_new.sqlite3
python3 -m cloudlaunch.cli list --db cloudlaunch_new.sqlite3
```
Note Rahul's and Priya's real REQ IDs from output. An admin should decide which single request reflects the actual business need; this is a **demo without login**, so don't treat `--reviewer` as proof of identity.

For example, assuming Priya's request is redundant:
```bash
python3 -m cloudlaunch.cli review --db cloudlaunch_new.sqlite3 --request-id REPLACE_PRIYA_REQ --decision reject --reviewer admin-demo --reason "Same manager task as Rahul"
python3 -m cloudlaunch.cli review --db cloudlaunch_new.sqlite3 --request-id REPLACE_RAHUL_REQ --decision approve --reviewer admin-demo --reason "Confirmed one server required"
```
This changes **only local SQLite records**. It does not trigger Jenkins or AWS provisioning.

## Step 3: read-only AWS check using your real AWS login
Install boto3 in your existing Python environment if required:
```bash
python3 -m pip install boto3
```
Verify which AWS identity will be queried:
```bash
aws sts get-caller-identity
```
Run the read-only inventory comparison in the request's AWS region:
```bash
python3 -m cloudlaunch.live_aws --file examples/rahul_request.json
```
If you've configured a named AWS profile, pass `--profile PROFILE_NAME`. Credentials must be configured locally using standard AWS tooling; **do not paste secret access keys** into ChatGPT or Git.

Result meanings:
- `NO_TAGGED_MATCH_FOUND`: nothing found with *all* standardized tags in that region/account; NOT proof there are no duplicates.
- `REVIEW_EXISTING_INFRA`: potential match found, manual review required.
- `BLOCKED_INVENTORY_UNAVAILABLE` or `BLOCKED_AWS_UNAVAILABLE`: read failed; block rather than assuming safe.

For the preliminary combined gate (after local admin review):
```bash
python3 -m cloudlaunch.live_aws --db cloudlaunch_new.sqlite3 --request-id REPLACE_RAHUL_REQ --file examples/rahul_request.json
```
`PASS_PRELIMINARY` is **not** approval to provision.

## Critical safety limitations
- This is prototype code, not a production authenticated approval system. No authorization or access control exists.
- `gate.py` is NOT connected to the existing `terraform-standalone` Jenkins pipeline. Therefore current Jenkins deployments are **not blocked** by this new gate.
- Real-world deployment protection requires integrating this preflight inside an isolated, request-aware Jenkins CD pipeline with strong credentials, audit logs, state isolation, and a final duplicate check close to apply.
- Current AWS tag matching is case-sensitive/exact, and many older servers may be untagged. Check other authorized regions/accounts and Terraform state inventories too.
- Approval must not be based on request fields alone; separately assess expected number of instances and business ownership.
- Keep the old EC2 project and Terraform local state untouched. Do not merge this draft PR before CI tests/review.
