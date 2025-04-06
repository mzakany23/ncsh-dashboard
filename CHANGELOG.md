# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2024-04-06

### Added
- AI-powered analysis feature using Claude API
- Generate button to create on-demand summaries and insights
- Markdown rendering of AI analysis with styled output

### Fixed
- Deployment configuration for Fly.io

## [1.0.0] - 2024-03-21

### Added
- Mobile-optimized interface with improved touch interactions
- Responsive date range picker with enhanced iPad support
- Team group management system with CRUD operations
- Advanced opponent filtering system (specific, worthy, team groups)
- Performance trend visualization
- Goal statistics charts
- Match result distribution analysis
- Opponent analysis section with detailed metrics
- Mobile menu toggle for better navigation on small screens

### Fixed
- Date range picker styling issues on mobile devices
- NA score handling in match results
- Team group selection and filtering edge cases
- Mobile layout and spacing inconsistencies
- Z-index conflicts in overlapping components
- Win/Loss calculation accuracy for NA scores

### Changed
- Improved mobile UI/UX with better touch targets
- Enhanced data visualization responsiveness
- Optimized database queries for better performance
- Streamlined team group management interface
- Refined opponent analysis metrics calculation

### Removed
- Win/Loss Distribution chart on mobile devices for cleaner interface
- Obsolete styling rules and unused components

## [0.1.8] - 2024-04-06

### Fixed
- Removed S3 download logic from entrypoint script
- Using data files from Docker build context

## [0.1.7] - 2024-04-06

### Fixed
- Updated IAM permissions for S3 access in GitHub Actions

## [0.1.6] - 2024-04-06

### Fixed
- Added s3:HeadObject permission to IAM role for S3 access

## [0.1.5] - 2024-04-06

### Changed
- Enabled auto-scaling to zero when no traffic
- Set min_machines_running to 0 to allow complete scale down

## [0.1.4] - 2024-04-06

### Changed
- Moved data file handling to GitHub Actions build process
- Removed AWS dependencies from Docker container
- Updated deployment workflow to include data files in build context

## [0.1.3] - 2024-04-06

### Changed
- Updated Dockerfile to download parquet file from S3 instead of copying it locally
- Fixed deployment workflow to use correct AWS role and S3 bucket configuration

## [0.1.2] - 2024-04-06

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