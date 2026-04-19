# Changelog

All notable changes to CleanSchema will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] — 2026-04-18

First public release.

### Added
- Streamlit-based local UI with three-step flow (drop → review → download)
- 13 built-in PII/sensitive-data classifiers
- Realistic synthetic replacement via Faker
- Join-consistent remapping (repeated values get the same synthetic substitute)
- Salary preservation within ±15% of source value
- Date shifting within ±5 years of source value
- CSV, TSV, XLSX, XLS support
- One-click launchers for macOS (`run.command`), Windows (`run.bat`), and Linux (`run.sh`)
- Per-platform virtualenv isolation so user system Python is never touched
- Override checkbox on every classified column
- Sample dataset (`examples/employees_sample.csv`)
- Unit test suite for both detector and synthesizer

### Privacy guarantees
- No network requests
- No telemetry
- No account or login
- Streamlit binds to `localhost` only
- All processing in browser tab memory; clean file delivered as direct download

[1.2.0]: https://github.com/rjboogey/cleanschema/releases/tag/v1.2.0
