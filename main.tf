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

# Retained from the successful Build #4. Changing the AMI may replace this EC2 instance.
resource "aws_instance" "foo" {
  ami           = "ami-05fa00d4c63e32376"
  instance_type = "t2.micro"

  tags = {
    Name = "TF-Instance"
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
