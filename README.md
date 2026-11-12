# AWS EC2 CI/CD with Jenkins and Terraform

This project creates one AWS EC2 instance through a Jenkins pipeline. GitHub stores the code, Terraform defines the instance, and Jenkins runs the deployment after your approval.

## How it works

1. Push a code change to GitHub.
2. GitHub Actions checks Terraform formatting, shell syntax, and Terraform configuration. It has no AWS credentials and does not deploy.
3. The existing Jenkins job polls GitHub about every two minutes while Jenkins is running.
4. Jenkins checks out the code, validates it, verifies the AWS identity, and generates a Terraform plan.
5. Review the plan in Jenkins Console Output and approve it as `kwavhal`.
6. Jenkins applies that exact saved plan and verifies the EC2 instance's running state, AWS status checks, type, name, and region.

Terraform uses its existing state to manage the same resource on later runs. A run with no infrastructure changes should not create another instance.

## The eight files

| File | Why it is here |
| --- | --- |
| `Jenkinsfile` | The single Jenkins deployment pipeline, including approval. |
| `main.tf` | AWS provider, EC2 definition, and instance outputs. |
| `post_deployment_check.sh` | AWS CLI checks after Terraform apply. |
| `.terraform.lock.hcl` | Keeps the existing AWS provider version and checksums reproducible. |
| `.github/workflows/terraform-validation.yml` | Validation on pushes and pull requests; no deployment. |
| `.gitignore` | Prevents local Terraform state, plans, credentials, and temporary files from being committed. |
| `README.md` | Setup and usage instructions. |
| `LICENSE` | Project license. |

## Existing deployment settings

| Setting | Value |
| --- | --- |
| AWS region | `us-east-1` |
| Terraform resource address | `aws_instance.foo` |
| EC2 type | `t2.micro` |
| EC2 Name tag | `TF-Instance` |
| AMI | `ami-05fa00d4c63e32376` |
| Jenkins AWS credential ID | `aws-jenkins-terraform` |
| Jenkins approver | `kwavhal` |

These settings are retained from the original standalone pipeline. The AMI must still be available to your AWS account in this region. Changing an AMI can replace an existing instance; review the Terraform plan first.

## Jenkins setup

Use your existing `terraform-standalone` Jenkins job and its existing workspace. This pipeline keeps local Terraform state in that workspace.

1. Start Docker Desktop and the existing Jenkins container (`docker start jenkins`, if stopped). Open <http://localhost:8080> on your Mac.
2. Ensure the Jenkins agent has Git, Bash, Terraform >= 1.6, and AWS CLI installed. The existing custom image was `jenkins-terraform-aws:1.2`.
3. Ensure Jenkins has Pipeline, Git, and Pipeline: AWS Steps installed; `withAWS` uses the AWS credential ID `aws-jenkins-terraform`.
4. In the existing job, use **Pipeline script from SCM**, Git URL `https://github.com/wavhalkomal/Terraform_Jenkins.git`, branch `*/main`, and Script Path `Jenkinsfile`.
5. Keep the existing Jenkins volume and job workspace. Do not add `deleteDir()`, workspace-cleaning steps, or `terraform init -upgrade` as part of normal builds.
6. Start a build when you intend to deploy. Review the AWS identity and plan, then approve the Manual Approval stage. Subsequent SCM changes are detected by the existing polling trigger.

AWS credentials need permission to inspect and manage this EC2 deployment. Keep credentials in Jenkins, never in Git. The host Mac's AWS profile and Jenkins credentials are separate.

## Validate locally without creating EC2

From the repository directory, with Terraform installed:

```bash
terraform fmt -check -recursive
bash -n post_deployment_check.sh
terraform init -backend=false -input=false -lockfile=readonly
terraform validate
```

Initialization downloads the locked provider; these commands do not create AWS resources. Actual `terraform plan` and `apply` belong in the existing Jenkins job with its original state and AWS credentials.

## Moving from the expanded CloudLaunch version

The request JSON dispatcher, duplicate-request Python prototype, alternative Terraform configuration, extra Jenkinsfiles, and their tests/documentation have been removed to keep this project focused on one EC2 pipeline.

- Keep the original `terraform-standalone` job configured with `Jenkinsfile`.
- Disable old jobs using `Jenkinsfile.cloudlaunch`, `Jenkinsfile.cloudlaunch.dispatch`, `Jenkinsfile.cloudlaunch.cd`, or `Jenkinsfile.pr`; those scripts no longer exist. Disable any old PR job that would run the deployment `Jenkinsfile` on untrusted branches. GitHub Actions now performs validation.
- This cleanup changes repository files only. It does not reconfigure Jenkins jobs, terminate AWS instances, delete Jenkins volumes, or remove any local/S3 Terraform state.
- The old CloudLaunch S3 state describes a separate deployment. Do not copy it into the standalone workspace or delete it as part of this cleanup.
- Earlier project notes record that the test instances were terminated. A future approved apply may create a new billable instance; only a fresh AWS inspection and Terraform plan show the current situation.

If the existing standalone workspace or state is missing, recover and inspect it before running a deployment. A new empty workspace can create a second instance if an earlier instance still exists.

## Troubleshooting

| Problem | Check |
| --- | --- |
| Jenkins is unavailable | Docker Desktop, `docker ps -a`, and the existing `jenkins` container. |
| No automatic build | Jenkins running, job enabled, `*/main` configured, and Poll SCM enabled after the first run. |
| Provider initialization fails | Network access and the tracked provider lockfile; do not delete state to fix this. |
| AWS identity or permissions fail | Jenkins credential ID, Pipeline: AWS Steps plugin, account, and region. |
| EC2 creation fails | AMI availability, default VPC/subnet, account quota, and EC2 permissions. |
| Plan unexpectedly creates/replaces a server | Correct job workspace/state and the requested Terraform change before approving. |
| Post-deployment checks fail | Jenkins Console Output and EC2 status; an instance can still exist after a failed build. |

To change the instance type or Name tag later, update both `main.tf` and the corresponding `EXPECTED_TYPE` or `EXPECTED_NAME` value in `Jenkinsfile`.
