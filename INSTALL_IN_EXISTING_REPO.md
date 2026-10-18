# Install CloudLaunch EC2 CI/CD extension

This archive contains **new files only**, designed to be copied into your existing `Terraform_Jenkins_repo` feature branch. It does not replace `main.tf`, `Jenkinsfile`, `Jenkinsfile.pr`, `cloudlaunch/`, or existing Terraform state.

1. In Terminal, remain on `feature/duplicate-request-detection` and run `git status` first. Commit/stash any unrelated changes before copying these files.
2. Download this zip, then expand its folders inside the existing repo root. You may use Finder to copy all archive contents into `Terraform_Jenkins_repo`, preserving folder structure.
3. Run `python3 -m unittest discover -s tests -v` and `python3 -m cloudlaunch_cd.workflow validate --file requests/REQ-1001.json`.
4. Run `git status` and review each new file, then `git add cloudlaunch_cd infra/cloudlaunch_ec2 requests tests/test_cloudlaunch_cd.py tests/test_cloudlaunch_plan.py Jenkinsfile.cloudlaunch.cd docs/CLOUDLAUNCH_END_TO_END.md`, commit and push feature branch. This updates draft PR #2.
5. Do not merge until PR CI succeeds and you have reviewed `docs/CLOUDLAUNCH_END_TO_END.md` and configured a dedicated Jenkins CD job + S3 backend.

**This package is an EC2-only demonstration of two tests, not a fully secure enterprise service.** It requires manual Jenkins setup and one human approval to create an EC2 instance. No Streamlit UI is included.
