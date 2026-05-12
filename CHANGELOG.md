# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-05-12

### Added

- Equal-principal (`equal-principal`) repayment schedule generation
- Equal-installment (`equal-installment`) repayment schedule generation
- Variable-rate equal-installment (`variable-installment`) with per-segment interest rates (`--rate-changes x:y:rc`)
- Side-by-side comparison of equal-principal vs equal-installment (`--compare`)
- Variable-rate comparison: full-cap-rate baseline vs actual variable schedule (`--compare --rate-changes`)
- Per-period detail view with remaining balance columns (`--compare-detail`)
- Rich terminal output with color; plain-text fallback (`--no-color`)
- `--version` / `-v` flag
- Input validation with clear Chinese error messages
- `pipx install loan` support as a standalone CLI tool

[Unreleased]: https://github.com/gdufsh/loan/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/gdufsh/loan/releases/tag/v0.1.0
