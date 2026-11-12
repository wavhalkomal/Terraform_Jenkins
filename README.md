# Red Hat Linux EC2 CI/CD with Jenkins and Terraform

This project creates one Red Hat Enterprise Linux (RHEL) 9 EC2 server through the existing Jenkins pipeline. You can use this server as the target for the separate Linux software-installation project. GitHub stores the code, Terraform defines the instance, and Jenkins runs the deployment after your approval.

The working `Jenkinsfile` and `post_deployment_check.sh` are unchanged. The RHEL configuration and optional SSH inputs are in `main.tf`; this repository still has eight files. Package installation, Artifactory, ServiceNow, and Ansible orchestration belong in the separate software-installation project.

## How it works

1. Push a code change to GitHub.
2. GitHub Actions checks Terraform formatting, shell syntax, and Terraform configuration. It has no AWS credentials and does not deploy.
3. The existing Jenkins job polls GitHub about every two minutes while Jenkins is running.
4. Jenkins checks out the code, validates it, verifies the AWS identity, and generates a Terraform plan.
5. Review the plan in Jenkins Console Output and approve it as `kwavhal`.
6. Jenkins applies that exact saved plan and verifies the EC2 instance's running state, AWS status checks, type, name, and region.

Terraform uses its existing state to manage the same resource on later runs. By default, the AMI lookup selects the newest image matching the configured pattern. A new matching image can cause a replacement plan even when the Git code has not changed. After the first deployment, pin the selected image name as described below to keep your software-testing server stable.

## The eight files

| File | Why it is here |
| --- | --- |
| `Jenkinsfile` | The single Jenkins deployment pipeline, including approval. |
| `main.tf` | Official RHEL image lookup, optional SSH inputs, EC2 definition, and connection outputs. |
| `post_deployment_check.sh` | AWS CLI checks after Terraform apply. |
| `.terraform.lock.hcl` | Keeps the existing AWS provider version and checksums reproducible. |
| `.github/workflows/terraform-validation.yml` | Validation on pushes and pull requests; no deployment. |
| `.gitignore` | Prevents local Terraform state, plans, credentials, and temporary files from being committed. |
| `README.md` | Setup and usage instructions. |
| `LICENSE` | Project license. |

## Deployment settings

| Setting | Value |
| --- | --- |
| AWS region | `us-east-1` |
| Terraform resource address | `aws_instance.foo` |
| EC2 type | `t2.micro` |
| EC2 Name tag | `TF-Instance` |
| Operating system | RHEL 9, x86_64, standard hourly subscription image |
| AMI source | Official publisher account `309956199498`, looked up in `us-east-1` |
| AMI name pattern | `RHEL-9.*_HVM-*-x86_64-*-Hourly2-GP3` |
| Root disk | 30 GiB encrypted gp3; deleted when the instance is terminated |
| SSH user | `ec2-user` |
| Jenkins AWS credential ID | `aws-jenkins-terraform` |
| Jenkins approver | `kwavhal` |

The region, resource address, instance type, Name tag, Jenkins credentials, and approval remain as before. The original hard-coded AMI has been replaced by the official RHEL lookup. `t2.micro` is retained to match the unchanged Jenkins verification settings; its 1 GiB RAM is limited, so use it for small package-installation tests. Larger workloads need a separate size change together with Jenkins' `EXPECTED_TYPE` setting.

RHEL hourly subscription, EC2, EBS storage, and any public IPv4 address can incur AWS charges. Changing the AMI replaces an existing server; it does not convert its operating system in place. Back up any needed data before approving a replacement. Root-disk data is deleted on instance termination.

## SSH access for the software-installation project

The original project did not attach an SSH key. To connect to this RHEL target, configure these inputs **before approving its creation**:

1. In EC2, region **us-east-1**, choose or create an existing key pair whose private key you hold. Keep the private key outside this repository and Terraform state.
2. Choose or create a security group in the region's **default VPC**, matching this project's existing default-subnet behavior. Allow inbound TCP 22 from your workstation's public IP `/32` and/or the Ansible controller's actual source address. Do not allow SSH from the entire internet. The route table, subnet, and network ACLs must also permit the connection.
3. In the **existing Jenkins job workspace**, create an untracked `terraform.tfvars` file with your real values:

```hcl
ssh_key_name       = "YOUR_EXISTING_EC2_KEY_PAIR_NAME"
security_group_ids = ["sg-YOUR_EXISTING_SECURITY_GROUP_ID"]
```

The existing standalone workspace was `/var/jenkins_home/workspace/terraform-standalone` inside the Jenkins container; confirm the job's actual workspace before placing the file. `.gitignore` excludes `*.tfvars`. Terraform automatically loads the file, so the Jenkins script needs no changes. Alternatively set `TF_VAR_ssh_key_name` and `TF_VAR_security_group_ids` in the Jenkins job/agent environment; setting them only in your Mac terminal does not configure Jenkins.

Both inputs are optional for compatibility with the existing pipeline. If omitted, the server launches without an SSH key and uses the default security group; do not expect SSH access in that configuration. No new key pairs, security groups, inbound firewall rules, or IAM resources are created by this repository.

Jenkins' AWS credentials additionally need `ec2:DescribeImages` for AMI discovery. EC2 permissions must allow the chosen key pair, security groups, and encrypted EBS root volume; custom KMS restrictions can also affect launch. The default VPC must have an available subnet, as in the original project.

## Deploy and connect

1. Keep using the original `terraform-standalone` job, its workspace/state, and Script Path `Jenkinsfile`.
2. Configure SSH inputs above and run the build. In Terraform Plan, check the official RHEL AMI name, region, disk, and any proposed replacement.
3. Approve only when ready to create or replace the server. The unchanged post-deployment script verifies EC2 running state, AWS health checks, instance type, Name, and region; it does **not** log into the operating system.
4. In that Jenkins workspace, run `terraform output` to obtain `instance_id`, `instance_ami`, `rhel_ami_name`, `instance_public_ip`, `instance_private_ip`, and `ssh_username`.
5. Add the exact `rhel_ami_name` output to the same ignored `terraform.tfvars` file before later builds:

```hcl
# Replace the entire value with the exact output, not a wildcard pattern.
rhel_ami_name = "EXACT_RHEL_9_AMI_NAME_FROM_TERRAFORM_OUTPUT"
```

Pinning avoids automatic selection of newer images. If the pinned AMI is later deregistered, the lookup fails; deliberately review a newer image rather than removing state.

From your workstation, using its private key and the instance's current public IP:

```bash
chmod 400 /path/to/your-key.pem
ssh -i /path/to/your-key.pem ec2-user@YOUR_INSTANCE_PUBLIC_IP
cat /etc/redhat-release
cat /etc/os-release
sudo dnf repolist
```

The last commands verify the actual operating system and list repositories without installing software. If the subnet does not assign a public IP, use a VPN, bastion, or Ansible controller with private network access; a private IP alone is not reachable from the internet. A public IP can change after a stop/start. Keep the server's instance ID and current address for the installation project's inventory.

The official hourly image supplies RHEL repository access through AWS/Red Hat infrastructure, subject to network and entitlement configuration. Installing from approved Artifactory repositories and enforcing repository policy will be implemented in the separate software-installation project; this change does not configure that enforcement or install SSM Agent.

Official references: [identify official RHEL AMIs](https://repost.aws/knowledge-center/ec2-identify-latest-rhel-ami), [Red Hat AMI discovery](https://access.redhat.com/solutions/15356), and [EC2 Linux users](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/managing-users.html).

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
