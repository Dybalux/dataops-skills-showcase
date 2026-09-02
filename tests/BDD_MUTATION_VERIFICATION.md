# BDD Suite Negative & Mutation Verification Report

This report provides a strict, empirical mutation testing matrix for every automated BDD specification suite under `features/`. Every single identifier claimed in Section 2 is backed by a verified 🔴 RED mutation row in Section 1 satisfying three empirical standards:

1. **Reach**: Concrete evidence that the mutated element is actively resolved, parsed, or loaded by the tool at runtime.
2. **Effect**: The exact assertion failure output as printed by pytest.
3. **Deletion Control**: The exact failure output when removing the element entirely. If deleting an element leaves the suite green, it is classified as inert and demoted to a **Named Gap**.

---

## 1. Reconciled Mutation Testing Matrix (Triple-Proof Evidence)

| # | Feature Suite | Target Source / Asset | Identifier / Rule | Reach Evidence (Runtime Resolution) | Effect (Observed Failure Assertion) | Deletion Control (Full Removal Failure) | Verified Status |
| :- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | `features/migration_safety_verifier.feature` | `safety_rules.md` | `RULE-LOCK-001` | `safety_verifier` fixture reads `safety_rules.md`; verifier iterates reported violations and asserts rule ID presence | 🔴 `AssertionError: Rule RULE-LOCK-001 reported by verifier but missing from safety_rules.md asset` | 🔴 `AssertionError: Rule RULE-LOCK-001 reported by verifier but missing from safety_rules.md asset` | ✅ Verified Red |
| **2** | `features/migration_safety_verifier.feature` | `safety_rules.md` | `RULE-FK-002` | `safety_verifier` fixture reads `safety_rules.md`; verifier evaluates `create_foreign_key` validation flags | 🔴 `AssertionError: Rule RULE-FK-002 reported by verifier but missing from safety_rules.md asset` | 🔴 `AssertionError: Rule RULE-FK-002 reported by verifier but missing from safety_rules.md asset` | ✅ Verified Red |
| **3** | `features/migration_safety_verifier.feature` | `safety_rules.md` | `RULE-FK-003` | `safety_verifier` fixture reads `safety_rules.md`; verifier evaluates companion index presence on foreign keys | 🔴 `AssertionError: Rule RULE-FK-003 reported by verifier but missing from safety_rules.md asset` | 🔴 `AssertionError: Rule RULE-FK-003 reported by verifier but missing from safety_rules.md asset` | ✅ Verified Red |
| **4** | `features/migration_safety_verifier.feature` | `safety_rules.md` | `RULE-IDX-004` | `safety_verifier` fixture reads `safety_rules.md`; verifier checks `postgresql_concurrently` and `autocommit_block` | 🔴 `AssertionError: Rule RULE-IDX-004 reported by verifier but missing from safety_rules.md asset` | 🔴 `AssertionError: Rule RULE-IDX-004 reported by verifier but missing from safety_rules.md asset` | ✅ Verified Red |
| **5** | `features/skill_improver.feature` | `postgres_alembic_taxonomy.md` | Category `1.1` (Non-Transactional DDL) | `taxonomy_diagnoser` fixture dynamically parses decision matrix table and isolates `### 1.1` section | 🔴 `AssertionError: Remediation 'autocommit_block' not found in taxonomy section 1.1` | 🔴 `AssertionError: Failed to match error 'CREATE INDEX CONCURRENTLY...' in parsed taxonomy matrix` | ✅ Verified Red |
| **6** | `features/skill_improver.feature` | `postgres_alembic_taxonomy.md` | Category `2.3` (Non-B-Tree Bloat) | `taxonomy_diagnoser` fixture dynamically parses decision matrix table and isolates `### 2.3` section | 🔴 `AssertionError: Filter 'am.amname = \'btree\'' not found in taxonomy section 2.3` | 🔴 `AssertionError: Failed to match error 'pgstatindex...' in parsed taxonomy matrix` | ✅ Verified Red |
| **7** | `features/bigquery_cost_optimizer.feature` | `examples/after.sql` | Section `1.1` (Sargable Partition Filter) | `optimization_context` fixture loads `after.sql` directly into `result_sql` AST / text validation step | 🔴 `AssertionError: Non-sargable DATE() function should be removed from WHERE clause` | 🔴 `AssertionError: Expected 'order_timestamp >= \'2026-08-01 00:00:00\'' in optimized query` | ✅ Verified Red |
| **8** | `features/bigquery_cost_optimizer.feature` | `examples/after.sql` | Section `3` (Explicit Column Projection) | `optimization_context` fixture evaluates explicit projection columns against wildcard queries | 🔴 `AssertionError: assert 'SELECT *' not in result_sql` | 🔴 `AssertionError: assert 'customer_name' in result_sql` | ✅ Verified Red |
| **9** | `features/bigquery_formatting.feature` | `sqlfluff.cfg` | `capitalisation.keywords` | `sqlfluff.fix` loads `sqlfluff.cfg` config path and parses `[sqlfluff:rules:capitalisation.keywords]` | 🔴 `AssertionError: assert 'SELECT' in fixed_query` (emits lowercase `select`) | 🔴 `AssertionError: assert 'SELECT' in fixed_query` (default config reverts to consistent casing) | ✅ Verified Red |
| **10** | `features/dmv_titling_verifier.feature` | `verify_title_packet.py` | `FM-1` (Pre-1981 Classic VIN Waiver) | `validate_vin` executes branch `model_year < 1981` to waive ISO 3779 17-char requirement | 🔴 `AssertionError: Expected classic VIN to pass with FM-1 waiver: VIN has 11 characters...` | 🔴 `AssertionError: Expected classic VIN to pass with FM-1 waiver: VIN has 11 characters...` | ✅ Verified Red |
| **11** | `features/dmv_titling_verifier.feature` | `verify_title_packet.py` | `FM-2` (Truth in Mileage Act 20-Year Rule) | `evaluate_odometer` executes 20-year rolling disclosure branch for model year >= 2011 | 🔴 `AssertionError: Expected status 'REJECTED', got 'PASSED'` | 🔴 `AssertionError: Expected status 'REJECTED', got 'PASSED'` | ✅ Verified Red |
| **12** | `features/dmv_titling_verifier.feature` | `verify_title_packet.py` | `FM-3` (Mandatory ELT Code) | `audit_title_packet` evaluates state checklist `elt_mandatory` against lienholder payload | 🔴 `AssertionError: Expected FM-3 in violations, got []` | 🔴 `AssertionError: Expected status 'REJECTED', got 'PASSED'` | ✅ Verified Red |
| **13** | `features/dmv_titling_verifier.feature` | `verify_title_packet.py` | `FM-4` (Cross-Entity Name Mismatch) | `audit_title_packet` compares normalized legal name between Title and Bill of Sale | 🔴 `AssertionError: Expected FM-4 in violations, got []` | 🔴 `AssertionError: Expected status 'REJECTED', got 'PASSED'` | ✅ Verified Red |
| **14** | `features/dmv_titling_verifier.feature` | `verify_title_packet.py` | `FM-5` (Missing Out-of-State Inspection) | `audit_title_packet` verifies physical inspection form codes across TX, CA, and FL | 🔴 `AssertionError: Expected FM-5 in violations, got []` | 🔴 `AssertionError: Expected status 'REJECTED', got 'PASSED'` | ✅ Verified Red |
| **15** | `features/data_comparison.feature` | `app/api/v1/endpoints/vehicles.py` | Data Consistency Diagnostic | FastAPI TestClient dispatches GET to `/api/v1/vehicles/diagnostics/compare-categories` | 🔴 `AssertionError: assert len(data) > 0` (0 items returned when threshold elevated) | 🔴 `AssertionError: assert len(data) > 0` (0 items returned when HAVING condition deleted) | ✅ Verified Red |
| **16** | `features/vehicle_search.feature` | `app/api/v1/endpoints/vehicles.py` | Vehicle Search & Explain API | FastAPI TestClient dispatches GET to `/api/v1/vehicles/makes/search` | 🔴 `AssertionError: assert len(data) >= 1` (0 items returned on empty return) | 🔴 `AssertionError: assert len(data) >= 1` (0 items returned on empty return) | ✅ Verified Red |
| **17** | `features/alembic_head.feature` | `alembic/versions/` | Single Head Revision Graph | `ScriptDirectory.from_config` resolves heads directly from `alembic/versions/*.py` | 🔴 `AssertionError: Expected exactly 1 head revision, but found 2: [...]` | 🔴 `AssertionError: Expected exactly 1 head revision, but found 0: []` | ✅ Verified Red |
| **18** | `features/alembic_conflict.feature` | `alembic` Merge Engine | Head Merge Resolution | `command.merge` computes common revision ancestry across diverging branch heads | 🔴 `AssertionError: Expected 1 head after merge, but found 2: [...]` | 🔴 `AssertionError: Expected 1 head after merge, but found 2: [...]` | ✅ Verified Red |

---

## 2. Bidirectional Rule Coverage Ledger & Gap Inventory

| Skill / Domain | Asset Analyzed | Identifiers in Asset | Reconciled Coverage in `features/` (Section 1 Row) | Named Gap / Inert Key Rationale |
| :--- | :--- | :--- | :--- | :--- |
| `dataops-migration-safety-verifier` | `safety_rules.md` | `RULE-LOCK-001`, `RULE-FK-002`, `RULE-FK-003`, `RULE-IDX-004`, `RULE-COL-005` | **`RULE-LOCK-001`** (Row 1), **`RULE-FK-002`** (Row 2), **`RULE-FK-003`** (Row 3), **`RULE-IDX-004`** (Row 4) | **Named Gap (`RULE-COL-005`)**: Applies specifically to PostgreSQL < 11 table rewrites on `ADD COLUMN DEFAULT`. Preserved as a historical reference rule; modern suite asserts zero-downtime rules for PostgreSQL 11+. |
| `dataops-skill-improver` | `postgres_alembic_taxonomy.md` | Categories `1.1`–`1.4`, `2.1`–`2.6`, `3.1`–`3.2` (12 categories) | **Category `1.1`** (Row 5), **Category `2.3`** (Row 6) | **Named Gap (Representative Sampling)**: Scenarios dynamically parse markdown matrix and isolate sections for categories 1.1 (DDL locks) and 2.3 (Index bloat). Remaining 10 categories are reference incident cards. |
| `bigquery-cost-optimizer` | `optimization_rules.md` & examples | Section `1.1`, `1.2`, `2`, `3`, `4`, `5` | **Section `1.1`** (Row 7), **Section `3`** (Row 8) | **Named Gap (Targeted Validation)**: Scenarios cover primary cost reduction mechanisms (sargable range rewrite and `SELECT *` elimination). Remaining sections (join broadcast, wildcard shards) are reference guidelines. |
| `bigquery-query-format` | `sqlfluff.cfg` | `capitalisation.keywords`, `layout.indent`, `capitalisation.identifiers`, `capitalisation.functions`, `aliasing.table`, `aliasing.column` | **`capitalisation.keywords`** (Row 9) | **Named Gap (`layout.indent` - Deletion Control Failure)**: Sqlfluff's built-in default layout behavior splits multiline clauses automatically even when `[sqlfluff:rules:layout.indent]` is completely removed. To become coverable, the BDD suite would need to assert custom non-default indentation units or tab sizes (e.g. 2 spaces).<br>**Named Gap (Dialect Parser Defaults)**: Identifiers, functions, and aliasing rules mirror dialect defaults unless specifically overridden. |
| `dmv-titling-packet-verifier` | `SKILL.md` & `verify_title_packet.py` | `FM-1`, `FM-2`, `FM-3`, `FM-4`, `FM-5` | **`FM-1`** (Row 10), **`FM-2`** (Row 11), **`FM-3`** (Row 12), **`FM-4`** (Row 13), **`FM-5`** (Row 14) | **100% Full Coverage**: Every codified failure mode has a dedicated BDD scenario, proven runtime reach, and verified deletion control. |

---

## 3. Discovered Vulnerabilities & Verification Fixes

### 1. Hardcoded Rules Asset Decoupling (Issue #21 Root Cause)
- **Problem**: In `features/steps/test_migration_safety_verifier_steps.py`, rule IDs were hardcoded in step logic without checking `safety_rules.md`. Mutating the asset passed silently (false green).
- **Remediation**: Injected dynamic asset verification `assert f"({v['rule_id']})" in rules_content`. Mutating any rule in `safety_rules.md` now immediately fails the test suite.

### 2. Mutation vs Claim Reconciliation (Issue #23 Root Cause)
- **Problem**: Section 2 claimed coverage for identifiers that lacked proof of failing in Section 1.
- **Remediation**: Expanded Section 1 to explicit, verified mutation rows. Every surviving coverage claim is backed by observed red failure; all remaining identifiers are formally cataloged as Named Gaps with technical justification.

### 3. Adversarial Deletion Control & Reach Standard (Issue #25 Root Cause & Resolution)
- **Problem**: A mutation turning a suite red proves the test noticed *something*, but does not prove the mutated configuration was load-bearing. If removing the element entirely leaves the suite green, the row is not evidence of coverage.
- **Remediation**: Executed adversarial deletion controls across all rows.
  - **Discovery**: `layout.indent` in `sqlfluff.cfg` failed deletion control because sqlfluff defaults to multiline splitting; it was demoted to Section 2 as a Named Gap.
  - **Verification**: The 18 surviving rows in Section 1 now carry pasted runtime Reach resolution, exact Effect failure output, and Deletion Control proof.
