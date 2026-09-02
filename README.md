# DataOps Skills — Showcase

Reusable skills for AI coding agents (Claude Code, Antigravity). A skill is a written contract that specifies how an agent handles a recurring technical or business-domain task: when it applies, the hard rules it must not break, decision gates, execution steps, and a clear definition of done.

This repository is a curated subset of a larger private library (10 skills, sandbox environment, BDD test suites). It contains the core components that showcase AI operations, process contracts, and verification rigor.

## What is in this showcase

- **`skills/dmv-titling-packet-verifier/`** — Audits vehicle titling and registration packets before DMV submission:
  - VIN check digit validation (ISO 3779 standard).
  - Federal odometer disclosure compliance (Truth in Mileage Act, 20-year rule for MY2011+).
  - State-specific forms for **TX** (130-U), **CA** (REG 343), **FL** (HSMV 82040), and **NY** (MV-82).
  - ELT lien code cross-verification and multi-document consistency checks.
  - Includes **12 executable BDD scenarios** (`features/dmv_titling_verifier.feature`) and sample execution outputs.

- **`skills/dataops-migration-safety-verifier/`** — Static analysis of database migrations (Alembic/PostgreSQL) to detect dangerous table locking DDL, missing foreign key indexes, and unindexed lock hazards before production deployment.

- **`tests/BDD_MUTATION_VERIFICATION.md`** — The mutation-testing verification report. (See below).

- **`examples/`** — Actual execution records committed as evidence of agent execution.

## The Verification Method

A test suite that passes proves very little on its own — it might remain green even if key assets break. Therefore, test suites in this library are mutation-tested:
1. Intentionally break or mutate the underlying asset/rule being tested.
2. Confirm that the test suite catches the failure and turns red.
3. Restore the asset.

The report records, per test suite:
- How the mutation reached the tool.
- The exact failure error generated.
- The result of deleting the tested element entirely (to verify it was load-bearing).

### Transparency & Discovery
During mutation testing, one configuration section previously marked as verified was discovered to be inert (the tool silently ignored it, and removing it left tests green). Rather than hiding the flaw, it is documented in `BDD_MUTATION_VERIFICATION.md` as a named gap with technical root-cause analysis.

## Running the Verification Suites

```bash
# Install dependencies
uv sync --extra dev

# Run BDD feature tests
uv run pytest features/ -q
```

## Scope & Engineering Context

Built over five days as part of an intensive DataOps skills development library. Reviewed across multiple iterative rounds with structured GitHub issue tracking (25 issues total, all in writing).
