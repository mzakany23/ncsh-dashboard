# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Added S3 database storage integration
- Added Terraform configuration for AWS IAM roles and policies
- Added GitHub Actions OIDC integration for secure S3 access
- Added AWS CLI to Dockerfile for S3 operations
- Added .gitignore entries for Terraform files

### Changed
- Updated Dockerfile to download database from S3 instead of creating it locally
- Updated GitHub Actions workflow to use OIDC for AWS authentication

## [0.1.1] - 2024-04-06

### Added
- LiteFS configuration for SQLite persistence
- Version-based deployment workflow
- GitHub Actions CI/CD pipeline

## [0.1.0] - 2024-04-06

### Added
- Initial release of NCSH Dashboard
- SQLite persistence with LiteFS
- GitHub Actions CI/CD pipeline
- Auth0 integration for authentication
- Basic metrics visualization