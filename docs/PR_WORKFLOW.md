# Pull Request Validation and Deployment

## Workflow
1. Create a feature branch from `main`; do not edit `main` directly.
2. Make a change and push the feature branch.
3. Open a PR against `main`.
4. Jenkins **PR validation job** runs `Jenkinsfile.pr` in a **separate workspace**; it runs formatting, shell checks, unit tests, `terraform init -backend=false`, and `terraform validate`. It **never** loads AWS deployment credentials or calls `terraform apply`.
5. Review the diff and checks. After approval, merge the PR.
6. The existing **terraform-standalone** Jenkins job polls `main`, executes a Terraform plan, and requests manual approval before apply. **Do not approve** until reviewing the plan for changes to your existing instance.

## Jenkins configuration
- Keep current `terraform-standalone` job tied to branch `main`, running the root `Jenkinsfile`.
- Create a separate Pipeline-from-SCM job named `terraform-pr-validation`:
  - Repository URL: `https://github.com/wavhalkomal/Terraform_Jenkins.git`
  - Branch Specifier for first test: `*/feature/pr-validation-pipeline`
  - Script Path: `Jenkinsfile.pr`
  - Enable Poll SCM with `H/2 * * * *` for localhost Jenkins.
- To validate arbitrary future PRs automatically, migrate this validation job to a **GitHub Branch Source Multibranch Pipeline** with PR discovery enabled and a secure reachable webhook; an ordinary Pipeline-from-SCM job watching one feature branch is only an initial proof of concept. Branch-specific discovery/polling behavior should be tested.
- Never run untrusted PR code with production AWS credentials. For public repositories, limit who can run Jenkins PR jobs and isolate PR workspaces/agents.
- Publish a GitHub commit status or check for the validation job, then make it a required check using GitHub branch rules where supported. A local Jenkins build is not itself automatically a required GitHub check.

## State protection
The current deployment uses a local state file in `/var/jenkins_home/workspace/terraform-standalone/terraform.tfstate`. Preserve that path and the Jenkins volume. Do not use `git clean -fdx`, wipe the deployment workspace, or move/rename Terraform resources until state migration is planned and verified. PR validation runs in an independent workspace, not the deployment workspace.

## Next enhancements
- Add a separate Jenkins PR discovery job with GitHub Branch Source.
- Add GitHub required checks, protected main branch, and human review.
- Introduce request-specific Terraform variables and a remote state backend.
- Add Streamlit request and admin portals after the full Git→Jenkins→Terraform workflow is verified.
