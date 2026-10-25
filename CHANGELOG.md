# Changelog

All notable changes to this project are documented in this file. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Landing ingestion module for the Gobierno de Canarias APIs: HTTP extraction with retries and backoff, immutable
  NDJSON run folders and one audit row per run in `ops.ingestion_audit`.
- Bundle with the `landing` and `ops` schemas, the `gobierno_canarias` landing volume and the
  `ingest_gobierno_canarias_landing` job.
- CI: lint, formatting check and unit tests on every pull request.
- Contribution guide with the Definition of Done and the release process; pull request and issue templates.
