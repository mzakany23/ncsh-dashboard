terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-2"
}

variable "github_org" {
  description = "GitHub organization name"
  type        = string
  default     = "mzakany23"
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
  default     = "ncsh-dashboard"
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket for team_groups.db"
  type        = string
}

data "aws_caller_identity" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
}