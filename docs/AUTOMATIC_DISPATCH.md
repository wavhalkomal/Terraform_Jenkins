# Automatic CloudLaunch request dispatch (local Jenkins)

The manual `Build with Parameters` workflow was only needed to prove provisioning and duplicate blocking. The dispatcher removes manual build startup for **newly added** merged request JSON files.

## Architecture

Employee opens PR adding `requests/REQ-XXXX.json` -> GitHub Actions checks PR -> reviewer merges to protected `main` -> local Jenkins `cloudlaunch-dispatch` polls GitHub -> dispatcher diffs new commits and queues `cloudlaunch-cd` with `REQUEST_FILE` automatically -> existing CD performs validation, AWS duplicate search, plan-only-create gate, human approval for new instance, Terraform apply.

Jenkins polls GitHub from inside your Mac, because GitHub cannot contact a service at `localhost:8080`. Poll interval: about 2 minutes while Jenkins and the Mac are running. GitHub PR merges **do not** bypass manual provisioning authorization.

## One-time setup

1. Review and merge the dispatcher PR into `main`. Require PR checks and prevent unreviewed direct pushes to `main` (GitHub branch rules). The dispatcher trusts code on main.
2. In Jenkins, create a new **Pipeline** job named **`cloudlaunch-dispatch`**. Select **Pipeline script from SCM**, SCM **Git**, repository `https://github.com/wavhalkomal/Terraform_Jenkins.git`, branch `*/main`, script path **`Jenkinsfile.cloudlaunch.dispatch`**. Leave the existing `cloudlaunch-cd` job unchanged; it reads `Jenkinsfile.cloudlaunch.cd` and uses `aws-jenkins-terraform` with a human input gate.
3. Click **Build Now ONCE** on `cloudlaunch-dispatch` after saving. The first run records the current main commit as a baseline and **does not dispatch existing REQ-1001/REQ-1002**. Subsequent changes to main are picked up automatically through SCM polling. The dispatcher requires a durable Jenkins workspace; avoid cleaning its workspace or deleting its cursor file.
4. Test by submitting a new PR that **adds** `requests/REQ-1003.json` with a distinct business purpose. Review and merge; leave Jenkins running. Expect the dispatcher to queue `cloudlaunch-cd` with the new filename, with no human entering the parameter. The downstream job still asks for human approval before provisioning.

## Limitations and safety

- Only newly **added** files in `requests/` ending in `.json` are dispatched. Edits to existing requests do not cause redeployment. If a request file is added and removed between polls, it will not be dispatched.
- The dispatcher has a persisted commit cursor in its Jenkins workspace. Workspace cleanup, job recreation, or a Git history rewrite requires an explicit re-baseline and may miss requests. In a production system, use durable request-processing records, retries, idempotent acknowledgements, audit trails, protected branches, and distributed locks. Queueing a downstream build is not proof that it finished successfully.
- Jenkins polling works only while Jenkins is running and can reach GitHub. `cloudlaunch-cd` queues builds with input approval still required. Duplicate requests intentionally fail before planning; this is expected.
- **Security:** Untrusted PR jobs must run in an isolated agent without AWS credentials or access to controller state. This lab Jenkins currently runs PR code on the controller; do not expose it to untrusted outside contributors.
- The request JSON is not proof of authenticated administrator approval; the current Jenkins CD uses a human `input` step. Do not call this production-ready approval workflow.
