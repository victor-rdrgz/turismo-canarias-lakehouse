# Contributing

How work is planned, changed, reviewed and released in this repository.

## Planning

- Every change starts from a GitHub issue: a data source, a feature, a bug or a design question.
- Labels give the type (`bug`, `enhancement`, `documentation`, `question`) and the area (`area: ingestion`,
  `area: bundle`, `area: ci-cd`, `area: observability`, `area: data-source`). `priority: high` is fixed before the
  next release.
- Design decisions are recorded as ADRs in `docs/adr/`, numbered in order and never rewritten: a new ADR supersedes
  an old one.

## Branches and commits

- Trunk-based development: `main` is always deployable; work happens on short-lived branches from `main`.
- Branch names: `<type>/<short-description>`, for example `feat/landing-audit-task-run-id` or `fix/partial-runs`.
- Commits follow [Conventional Commits](https://www.conventionalcommits.org/):
  `<type>(<optional scope>): <description>`, with types `feat`, `fix`, `refactor`, `test`, `docs`, `build`, `ci`,
  `chore`.

## Pull requests

- One concern per pull request, small enough to review in one sitting. Larger work is split into stacked pull
  requests.
- The pull request title is a Conventional Commit: pull requests are squash-merged and the title becomes the commit
  on `main`. Head branches are deleted after the merge.
- The description links the issue (`Closes #<number>`) and completes the Definition of Done checklist.
- CI must pass before merging.

## Definition of Done

A change is done when:

1. It is linked to an issue and limited to one concern.
2. Unit tests cover the new or changed behaviour; `uv run ruff check .`, `uv run ruff format --check .` and
   `uv run pytest` pass.
3. `databricks bundle validate` passes for every target.
4. Changes to jobs, bundle resources or ingestion code are deployed to `dev` and verified with a job run: the job
   succeeds, landing contains the expected run folder and `ops.ingestion_audit` has the expected rows.
5. Design decisions have an ADR; README, data contracts and runbook are updated when affected.
6. The diff contains no secrets, credentials, personal data or AI assistant files.
7. `CHANGELOG.md` has an entry under `Unreleased`.

## Versioning and releases

- [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`, from `0.y.z` while the platform is in initial
  development.
- The version lives in `pyproject.toml`; the history in `CHANGELOG.md`
  ([Keep a Changelog](https://keepachangelog.com/) format).
- Release steps:
  1. A `chore(release): vX.Y.Z` pull request bumps the version in `pyproject.toml` and moves the `Unreleased`
     entries of `CHANGELOG.md` to the new version.
  2. After the merge, tag the merge commit on `main` and publish the release:
     `git tag -a vX.Y.Z -m "vX.Y.Z"`, `git push origin vX.Y.Z`, `gh release create vX.Y.Z --notes-from-tag`.
- A faulty release is fixed forward: revert the change on `main` and publish a new patch release.
