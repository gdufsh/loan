# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install with dev dependencies (editable)
pip install -e ".[dev]"

# Run all tests (coverage enforced at 80%)
python -m pytest

# Run a single test file
python -m pytest tests/unit/test_variable_installment.py -v

# Run a single test by name
python -m pytest tests/unit/test_variable_installment.py::TestInvariants::test_last_remaining_is_zero -v

# Run tests without coverage (faster iteration)
python -m pytest --no-cov

# Run the CLI
loan --help
loan -p 1000000 -r 3.25 -m 360
loan -p 1000000 -r 3.25 -m 360 --compare
loan -p 1000000 -r 3.25 -m 360 --rate-changes 1:24:2.5
```

## Architecture

The project is a CLI loan repayment schedule calculator. Data flows: `CLI args → LoanRequest → Strategy.generate() → Schedule → presentation`.

### Core models (`src/loan/models.py`)

All models are `frozen=True` dataclasses:

- `LoanRequest` — input: `principal`, `annual_rate` (% as Decimal, e.g. `3.25`), `months`, `method`, `rate_changes` (tuple of `(start, end, rate)` triples for variable-rate mode)
- `Installment` — one repayment period; includes `annual_rate` field (the per-period effective rate)
- `Schedule` — output: `installments` tuple + `total_payment`/`total_interest` totals
- `Comparison` — holds two `Schedule`s (EP vs EI) plus diff metrics

### Strategy pattern (`src/loan/strategies/`)

`STRATEGIES` dict in `__init__.py` maps method name → class:

| Key | Class | Logic |
|---|---|---|
| `equal-principal` | `EqualPrincipalStrategy` | Fixed principal per period; interest decreases each month |
| `equal-installment` | `EqualInstallmentStrategy` | Fixed payment (PMT formula); computed once, last period adjusted to zero remaining |
| `variable-installment` | `VariableRateInstallmentStrategy` | PMT recalculated **every period** from current `remaining` and `n_remaining` using the period's effective rate |

All strategies share the invariant: last-period principal = remaining balance (ensures exact zero).

### Decimal precision

All arithmetic uses `Decimal` with `getcontext().prec = 28` and `ROUND_HALF_UP` to `0.01`. Never use `float` for financial calculations.

### Variable rate module (`src/loan/rate_schedule.py`)

`parse_rate_changes(spec)` → parses `"x:y:rc[,x:y:rc,...]"` into tuple of `(start, end, rate)` segments.

`resolve_rate(period, default_rate, segments, cap_rate, months)` → validates all segments (no overlaps, `rate ≤ cap_rate`, `end ≤ months`) then returns the effective rate for `period`. Validation runs on every call; segments outside intervals fall back to `default_rate` (the cap rate).

`--rate-changes` and `--compare` are mutually exclusive (CLI enforces this).

### Presentation layer (`src/loan/presentation.py`)

`_has_variable_rate(schedule)` checks if any two installments differ in `annual_rate`. If true, renders an extra "年利率(%)" column showing the rate only on rows where it changes, and marks those rows with `<- 利率变更`.

### Validation (`src/loan/validation.py`)

`validate_request()` checks principal > 0, rate in [0, 100], months > 0. Rate-segment validation (overlaps, cap, months bounds) happens inside `resolve_rate()` at generation time, not in `validate_request()`.

### Error hierarchy (`src/loan/errors.py`)

`LoanError(ValueError)` → `InvalidLoanParameterError`, `UnknownStrategyError`, `InvalidRateScheduleError`. The CLI catches both `LoanError` and `ValueError` for the variable-rate path.

## Test layout

- `tests/conftest.py` — shared fixtures: `typical_request`, `short_request`, `zero_rate_request`
- `tests/unit/test_strategies.py` — EP and EI strategies
- `tests/unit/test_variable_installment.py` — `VariableRateInstallmentStrategy` (invariants, rate application, edge cases)
- `tests/unit/test_rate_schedule.py` — parse/validate/resolve for `rate_schedule`
- `tests/unit/test_comparison.py` — `build_comparison()`
- `tests/unit/test_presentation.py` — rendering helpers
- `tests/integration/test_cli.py` — full CLI invocations via `main(argv)`
