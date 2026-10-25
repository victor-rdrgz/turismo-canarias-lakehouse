## Summary

<!-- The problem, the approach and the result; why the change is needed and where the review should start. -->

Related issue: <!-- `Closes #<number>` when this pull request targets main; `#<number>` when it is stacked on another pull request; delete the line for trivial changes. -->

## Verification

<!-- Commands run and their result; for job or bundle changes, the dev job run and what was checked. -->

## Definition of Done

- [ ] One purpose, linked to its issue when there is one
- [ ] Unit tests added or updated (a bug fix includes a test that reproduces the bug); lint, format and tests pass
- [ ] `databricks bundle validate` passes for every target
- [ ] Job, bundle or ingestion changes deployed to `dev` and verified with a job run
- [ ] ADR, README, data contracts or runbook updated when affected
- [ ] No secrets, credentials, personal data or AI assistant files in the diff
- [ ] Label added (`bug`, `enhancement`, `documentation`, ...): the release notes are generated from it
