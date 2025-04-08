# Build & Deployment Instructions

## Deploy Workflow

You must do these steps to ensure a build happens:

0. Check git tags cross referenced to CHANGELOG.md so you can understand the proper versioning

1. Create Pull Request:
   ```
   gh pr create --title "Fix team name matching and date filtering" --body "Improves the team name matching in fuzzy_match_teams function and fixes date/timezone handling"
   ```

2. Merge Pull Request to main:
   ```
   gh pr merge --delete --squash
   ```