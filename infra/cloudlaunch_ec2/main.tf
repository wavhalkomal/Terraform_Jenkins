terraform {
  required_version = ">= 1.10.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
  backend "s3" {}
}

provider "aws" {
  region = var.region
}

resource "aws_instance" "server" {
  ami           = var.ami_id
  instance_type = var.instance_type

  metadata_options {
    http_tokens = "required"
  }

  tags = {
    Name        = "${var.workload}-${var.environment}"
    ManagedBy   = "CloudLaunch"
    ProjectID   = lower(var.project_id)
    TaskID      = lower(var.task_id)
    Workload    = lower(var.workload)
    Environment = var.environment
    BusinessKey = substr(sha256(join("|", [lower(var.project_id), lower(var.task_id), lower(var.workload), lower(var.environment), lower(var.region)])), 0, 24)
    RequestID   = var.request_id
    RequestedBy = var.employee_id
  }
}

output "instance_id" {
  value = aws_instance.server.id
}
output "instance_state" {
  value = aws_instance.server.instance_state
}
output "instance_type" {
  value = aws_instance.server.instance_type
}
output "instance_ami" {
  value = aws_instance.server.ami
}
