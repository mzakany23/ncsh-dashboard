# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.1] - 2025-04-13

### Added
- Goal diff over time chart

## [1.2.0] - 2025-04-12

### Fixed
- Add Sentry for error reporting

## [1.1.9] - 2025-04-12

### Fixed
- Dynamic app versions on build via changelog

## [1.1.8] - 2025-04-12

### Fixed
- Improved accuracy of AI summaries by calculating and using actual win/loss/draw counts
- Enhanced Claude prompt with accurate match statistics for better analysis

## [1.1.7] - 2025-04-08

### Fixed
- Added smart database merging to preserve team groups from both S3 and LiteFS
- Fixed issue with fake team groups appearing in development environment
- Added scripts directory with merge_team_groups.py for database merging
- Improved entrypoint script to handle database conflicts intelligently

## [1.1.6] - 2025-04-08

### Fixed
- Fixed team groups persistence by ensuring database is properly pulled from S3 during deployment
- Ensured team groups are preserved across deployments via LiteFS volume

## [1.1.5] - 2025-04-07

### Fixed
- Added workflows permission to GitHub Actions deployment to fix tag creation
- Improved deployment workflow reliability

## [1.1.4] - 2025-04-07

### Fixed
- Fixed team groups persistence in LiteFS volume
- Removed unnecessary team group initialization code
- Improved UI consistency across dashboard sections
- Added consistent horizontal rules under all section headers
- Standardized loading spinner styles across all dashboard components
- Fixed section header spacing and alignment issues
- Fixed deployment issue with LiteFS volume mount by adding backup data directory

## [1.1.3] - 2025-04-07

### Fixed
- Improved UI consistency across dashboard sections
- Added consistent horizontal rules under all section headers
- Standardized loading spinner styles across all dashboard components
- Fixed section header spacing and alignment issues
- Fixed deployment issue with LiteFS volume mount by adding backup data directory
- Added automatic creation of default team groups when database is empty

## [1.1.2] - 2025-04-06

### Fixed
- Fixed duplicate callback issue in URL-based team group selection
- Added `prevent_initial_call='initial_duplicate'` to resolve conflicts between callbacks
- Improved team group persistence across page refreshes by prioritizing URL state
- Fixed spinner behavior for loading states

## [1.1.1] - 2025-04-06

### Fixed
- Fixed duplicate callback issue in URL-based team group selection
- Added `prevent_initial_call='initial_duplicate'` to resolve conflicts between callbacks
- Improved team group persistence across page refreshes by prioritizing URL state
- Fixed spinner behavior for loading states

## [1.1.0] - 2025-04-06

### Added
- AI-powered analysis feature using Claude API
- Intuitive AI analysis icon with hover tooltip
- Integrated AI summaries directly in the performance summary section
- Markdown rendering of AI analysis with styled output
- Typing animation effect for AI-generated content

### Changed
- Improved UI by using an icon instead of a separate section
- Enhanced styling for AI-generated content
- Streamlined user experience for generating insights

### Fixed
- Deployment configuration for Fly.io
- NA score handling in match results

## [1.0.0] - 2025-03-21

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

## [0.1.8] - 2025-04-06

### Fixed
- Removed S3 download logic from entrypoint script
- Using data files from Docker build context

## [0.1.7] - 2025-04-06

### Fixed
- Updated IAM permissions for S3 access in GitHub Actions

## [0.1.6] - 2025-04-06

### Fixed
- Added s3:HeadObject permission to IAM role for S3 access

## [0.1.5] - 2025-04-06

### Changed
- Enabled auto-scaling to zero when no traffic
- Set min_machines_running to 0 to allow complete scale down

## [0.1.4] - 2025-04-06

### Changed
- Moved data file handling to GitHub Actions build process
- Removed AWS dependencies from Docker container
- Updated deployment workflow to include data files in build context

## [0.1.3] - 2025-04-06

### Changed
- Updated Dockerfile to download parquet file from S3 instead of copying it locally
- Fixed deployment workflow to use correct AWS role and S3 bucket configuration

## [0.1.2] - 2025-04-06

### Added
- Added S3 database storage integration
- Added Terraform configuration for AWS IAM roles and policies
- Added GitHub Actions OIDC integration for secure S3 access
- Added AWS CLI to Dockerfile for S3 operations
- Added .gitignore entries for Terraform files

### Changed
- Updated Dockerfile to download database from S3 instead of creating it locally
- Updated GitHub Actions workflow to use OIDC for AWS authentication

## [0.1.1] - 2025-04-06

### Added
- LiteFS configuration for SQLite persistence
- Version-based deployment workflow
- GitHub Actions CI/CD pipeline

## [0.1.0] - 2025-04-06

### Added
- Initial release of NCSH Dashboard
- SQLite persistence with LiteFS
- GitHub Actions CI/CD pipeline
- Auth0 integration for authentication
- Basic metrics visualization