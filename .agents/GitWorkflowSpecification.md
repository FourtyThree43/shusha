Git Workflow — AI Agent Specification
Objective

Use dev as the sole active development and integration branch. Treat main as the production-only branch controlled manually by the project owner.

Branch Structure

main

Production-ready code only.
Never use it for normal development.
Never create feature branches from main.
Do not automatically merge dev into main.
Do not push directly to main.
Production releases are created manually by the project owner.

dev

Primary development and integration branch.
All new work ultimately enters through dev.
It may contain unreleased, experimental, or unstable changes.

feature/<feature-name>

Create exclusively from dev.
Implement and commit feature work here.
Merge back into dev.
Delete the feature branch after successful merge when appropriate.
Development Flow
feature/<name>
       │
       ▼
      dev
       │
       │  manual release by owner
       ▼
      main
       │
       ▼
   vX.Y.Z tag

Agent Rules
Always check the current branch before making changes.
Normal development must happen on dev or a feature branch created from dev.
Never create a feature branch from main.
Never intentionally commit development work directly to main.
Never automatically merge dev into main.
Never create or push a production release tag from dev.
Do not modify main unless explicitly instructed by the project owner to perform a manual release.
If the user asks to implement a feature, create/use an appropriate feature/<feature-name> branch from the latest dev when branch creation is appropriate.
Feature branches should be merged into dev, not main.
Keep dev as the integration point for all unreleased work.
Before any release operation, verify that the user explicitly requested the release.
Do not rewrite shared branch history with force pushes unless explicitly authorized.
Feature Branch Example
git switch dev
git pull origin dev
git switch -c feature/my-feature

# implement changes
git add .
git commit -m "Add my feature"

git push -u origin feature/my-feature


The resulting PR should be:

feature/my-feature → dev

Release Policy

A release is manual and owner-controlled.

The agent must not independently:

merge dev into main
push to main
create a production tag
deploy production
decide that dev is ready for production

When explicitly instructed to release, use the appropriate release procedure and create an annotated version tag.

Example:

git switch main
git pull origin main
git merge --no-ff dev -m "Release v1.0.0"
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin main --follow-tags

Tagging

Use semantic version tags:

v1.0.0
v1.1.0
v1.1.1


Use annotated tags:

git tag -a v1.0.0 -m "Release v1.0.0"


Tags must represent production releases on main.

Safety

If the requested operation would modify main, but the user has not explicitly requested a release or production operation:

Do not perform it.

Instead, continue the work on dev or an appropriate feature/* branch.
