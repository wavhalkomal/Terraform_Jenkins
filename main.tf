terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

variable "rhel_ami_name" {
  description = "Official RHEL 9 image name/pattern. Set an exact name after the first deployment to keep the same image on later runs."
  type        = string
  default     = "RHEL-9.*_HVM-*-x86_64-*-Hourly2-GP3"

  validation {
    condition     = startswith(var.rhel_ami_name, "RHEL-9.") && !strcontains(var.rhel_ami_name, "BETA")
    error_message = "Use a stable RHEL 9 AMI name or pattern beginning with RHEL-9.; beta images are excluded."
  }
}

variable "ssh_key_name" {
  description = "Optional existing EC2 key-pair name in us-east-1. Keep the private key outside Git and Terraform."
  type        = string
  default     = null
}

variable "security_group_ids" {
  description = "Optional existing security groups in the default VPC. For SSH, allow TCP 22 only from your workstation or Ansible controller."
  type        = list(string)
  default     = []
}

# Look up a regional image published by the official Red Hat AWS account.
data "aws_ami" "rhel9" {
  most_recent = true
  owners      = ["309956199498"]

  filter {
    name   = "name"
    values = [var.rhel_ami_name]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }

  filter {
    name   = "state"
    values = ["available"]
  }
}

# Preserve the original resource address, type, and Name expected by Jenkins.
# Changing the AMI replaces an existing instance; inspect the plan before approval.
resource "aws_instance" "foo" {
  ami           = data.aws_ami.rhel9.id
  instance_type = "t2.micro"
  key_name      = var.ssh_key_name

  vpc_security_group_ids = length(var.security_group_ids) > 0 ? var.security_group_ids : null

  root_block_device {
    volume_size           = 30
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  tags = {
    Name = "TF-Instance"
    OS   = "RHEL-9"
  }
}

output "instance_id" {
  description = "ID of the Terraform-managed EC2 instance"
  value       = aws_instance.foo.id
}

output "instance_region" {
  description = "AWS region containing the EC2 instance"
  value       = aws_instance.foo.region
}

output "instance_ami" {
  description = "RHEL AMI used to create the server"
  value       = aws_instance.foo.ami
}

output "rhel_ami_name" {
  description = "Selected official image name; pin this using TF_VAR_rhel_ami_name for later builds"
  value       = data.aws_ami.rhel9.name
}

output "instance_public_ip" {
  description = "Public IPv4 address, if the selected default subnet assigns one"
  value       = aws_instance.foo.public_ip
}

output "instance_private_ip" {
  description = "Private address for an Ansible controller with network access to this VPC"
  value       = aws_instance.foo.private_ip
}

output "ssh_username" {
  description = "Default non-root SSH user for the official RHEL image"
  value       = "ec2-user"
}
