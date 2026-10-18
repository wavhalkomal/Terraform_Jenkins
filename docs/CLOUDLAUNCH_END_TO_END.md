# CloudLaunch — end-to-end EC2 CI/CD duplicate test

## Safety and purpose
This new CD path is independent from your current `terraform-standalone` Jenkins job, its workspace, its local Terraform state and its existing EC2 instance. PR CI never uses AWS credentials. A separate Jenkins CD job uses S3 remote Terraform state with locking, validates a request, checks AWS, plans exactly one new EC2, waits for an authorized human, checks AWS again, and only then applies Terraform.

The new CD job is **not automatically enabled** by adding its Jenkinsfile to GitHub. You must configure it in Jenkins and set the S3 bucket. EC2 and S3 resources may incur charges.

## Prerequisites (do once)
1. Create a new private S3 bucket in `us-east-1` with block-public-access, versioning and server-side encryption. Grant the CD AWS role IAM permissions to use objects under `cloudlaunch/requests/*`, including `.tflock` objects for Terraform `use_lockfile = true`. The role also needs EC2 describe, run, tagging, and the permissions required by EC2 provisioning. Restrict destructive permissions where possible. Use Terraform >= 1.10 and boto3 on the trusted Jenkins CD agent.
2. Set Jenkins environment variable `CLOUDLAUNCH_STATE_BUCKET` to that *pre-existing* bucket name. No AWS keys or bucket credentials belong in Git. Terraform state contains sensitive information and must be access controlled.
3. Create a new **Pipeline from SCM** Jenkins job `cloudlaunch-cd` with repo `https://github.com/wavhalkomal/Terraform_Jenkins`, branch `main`, Script Path `Jenkinsfile.cloudlaunch.cd`, and AWS credential `aws-jenkins-terraform` (or change Jenkinsfile to a scoped CloudLaunch role credential). Only trusted admins may trigger and approve builds. Review the pipeline configuration and avoid running this CD Jenkinsfile on untrusted PR branches.
4. Do **not** enable automatic SCM polling for CD during this test. Make sure the original `terraform-standalone` polling job won't unexpectedly run or change existing AWS infrastructure after a merge; temporarily disable its automatic SCM polling if needed, but NEVER delete or clean its Terraform state.
5. Require PR review and a trusted, **isolated** PR validation job with no AWS credentials and no access to the Jenkins controller's state directory. Avoid running untrusted PR Groovy on a Jenkins controller. Ensure GitHub status reporting works before enforcing required checks.

## Test 1: provisioning
1. Confirm the `ami_id` in `requests/REQ-1001.json` is available in its chosen region (AMI identifiers differ across time and regions). Use a *new* business purpose that doesn't already have an EC2 server; check account, VPC, and security-group expectations.
2. Create PR adding a new `requests/REQ-1001.json` (or change the sample so its business ID is unique). PR CI runs tests and Terraform static validation, with no provisioning.
3. After review, merge PR into main. Open the **new** Jenkins job `cloudlaunch-cd`, select Build with Parameters, and set `REQUEST_FILE=requests/REQ-1001.json`.
4. Jenkins obtains the JSON file from `main`; validates, reads EC2 inventory, prepares a unique S3 backend state key, runs `terraform plan`, and rejects all plan actions other than one EC2 create.
5. Inspect the plan and press **Approve EC2 creation** at the human gate. Jenkins checks AWS inventory again and applies the saved plan.
6. Jenkins prints Terraform outputs including new instance ID. Verify actual EC2 tags in AWS Console/CLI.

## Test 2: same server requested again
1. Make another PR adding `requests/REQ-1002.json` with a **different** `request_id` and `employee_id` but the same `project_id`, `task_id`, `workload`, `environment`, and `region`. You may deliberately change the instance type to prove that identical technical specs are not required for business duplicate detection.
2. PR CI tests syntax but does **not** read live AWS. Normally an enterprise admin should flag the duplicate before merge; for your controlled test, merge and invoke the new `cloudlaunch-cd` job with `REQUEST_FILE=requests/REQ-1002.json`.
3. The first AWS-check stage reports `BLOCKED` / `ALREADY_PROVISIONED`, with existing instance ID, lifecycle state, instance type, AMI, region and business tags, then the Jenkins build fails **as intended**. There is no new Terraform plan or apply.

## Project boundaries
- This demonstration **does not** enforce the previous local SQLite admin approval in Jenkins. The human approval in the new CD pipeline is real Jenkins approval. Full enterprise service still requires authenticated centralized PostgreSQL approvals, durable audit events, scoped authorization, automated request dispatcher, distributed cross-job locks, and inventory reconciliation for untagged/external resources.
- AWS lookups use only one account and request region. Untagged servers, other accounts or regions might be missed. A tag search is not an atomic create-if-absent operation; concurrent out-of-band infrastructure changes can race. Use policy enforcement and inventory for a production system.
- Request config under version control is reviewed and approved manually; **do not allow direct pushes by untrusted users**.
- A Terraform remote state backend and `disableConcurrentBuilds` provide protection for the single CD job, not all external provisioning systems.
- This pipeline blocks modifications, no-op plans and deletions, so its purpose is specifically to prove one EC2 is newly provisioned and a business-duplicate is rejected.
