# Terraform Configuration for GitHub Actions AWS Access

This directory contains Terraform configuration to set up AWS IAM roles and policies for GitHub Actions to access S3.

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. Terraform installed
3. S3 bucket already created

## Usage

1. Update `terraform.tfvars` with your actual values:
   - `s3_bucket_name`: Your S3 bucket name
   - `github_org`: Your GitHub organization
   - `github_repo`: Your GitHub repository name

2. Initialize Terraform:
   ```bash
   terraform init
   ```

3. Plan the changes:
   ```bash
   terraform plan
   ```

4. Apply the changes:
   ```bash
   terraform apply
   ```

5. After applying, update your GitHub Actions workflow with the role ARN output by Terraform.

## What This Creates

- IAM role for GitHub Actions with OIDC trust relationship
- IAM policy for S3 access
- Policy attachment to the role

## Security Notes

- The IAM role is scoped to your specific GitHub repository
- The S3 policy only allows read access to the specified bucket
- OIDC authentication is used instead of long-lived credentials