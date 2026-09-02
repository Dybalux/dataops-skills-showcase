---
name: dataops-migration-safety-verifier
description: "Trigger: migration safety, ddl safety, zero downtime migration, lock timeout, unindexed foreign key, safe migration, alembic safety, blocking ddl, alter table lock, migration linter. Statically analyze Alembic migration files to detect dangerous locking operations, unindexed foreign keys, and non-concurrent DDL before deployment."
license: Apache-2.0
metadata:
  author: "dybalux"
  version: "1.0"
---

# Activation Contract

Activate when an engineer or agent writes, reviews, or audits an Alembic migration, prepares a database schema change for production, or asks to verify that a migration runs with zero downtime.

```
Trigger keywords: migration safety, ddl safety, zero downtime migration, lock timeout, unindexed foreign key, safe migration, alembic safety, blocking ddl, alter table lock, migration linter
```

# Hard Rules

- **Zero-downtime standard**: Every migration affecting existing tables in staging or production must execute without long-lived `ACCESS EXCLUSIVE` table locks.
- **Two-phase foreign keys**: All new foreign keys on existing tables must be added with `postgresql_not_valid=True` and validated in a separate `VALIDATE CONSTRAINT` statement.
- **Strict foreign key indexing**: Any column referenced in a foreign key constraint on the child table must have a dedicated index or lead a compound index to prevent full-table share locks on parent deletion/updates.
- **Mandatory lock timeout**: Every migration containing DDL operations on existing tables must explicitly configure `lock_timeout` (e.g. `op.execute("SET LOCAL lock_timeout = '2s';")`).
- **Concurrent index operations**: Index creation and deletion on existing tables must use `postgresql_concurrently=True` inside an `autocommit_block()`.
- **Explicit bidirectional rollback**: The `downgrade()` function must be complete, reversible, and drop created indexes/constraints cleanly.

# Decision Gates

| DDL Operation | Hazardous Pattern | Prescribed Safe Pattern |
| :--- | :--- | :--- |
| Add Foreign Key | `op.create_foreign_key(...)` without `postgresql_not_valid=True` | `op.create_foreign_key(..., postgresql_not_valid=True)` followed by `op.execute("ALTER TABLE ... VALIDATE CONSTRAINT ...")` |
| Create Index | `op.create_index(...)` without concurrency or missing autocommit | Enclose in `with op.get_context().autocommit_block():` with `postgresql_concurrently=True` |
| Add Column with Default | `op.add_column(..., sa.Column(..., server_default=..., nullable=False))` | Add column as nullable or with default in non-blocking mode; backfill data asynchronously if needed |
| Drop Index | `op.drop_index(...)` blocking reads/writes | `op.drop_index(..., postgresql_concurrently=True)` in `autocommit_block()` |
| Unindexed Foreign Key | Child table has FK column without index | Generate companion `op.create_index(..., postgresql_concurrently=True)` on the foreign key column |

# Execution Steps

1. **Scan Migration Revisions**
   - Inspect the revision Python file in `alembic/versions/` or code provided in the prompt.
   - Determine whether operations apply to newly created tables or existing high-traffic tables.

2. **Check for Lock Safety Timeouts**
   - Verify that `upgrade()` and `downgrade()` declare `SET LOCAL lock_timeout = '2s';` or a session-level timeout before executing DDL.

3. **Audit DDL Statements for Blocking Locks**
   - Verify that all `op.create_foreign_key()` calls include `postgresql_not_valid=True`.
   - Verify that validation follows in a separate `VALIDATE CONSTRAINT` statement.
   - Verify that all `op.create_index()` and `op.drop_index()` calls on existing tables use `postgresql_concurrently=True` wrapped in `autocommit_block()`.

4. **Verify Foreign Key Index Coverage**
   - Check if the foreign key column on the child table is indexed.
   - If missing, prescribe adding a concurrent index to prevent locking and sequential scans during parent deletions.

5. **Validate Rollback Reversibility**
   - Audit `downgrade()` to ensure every created constraint, column, or index has a corresponding, non-destructive reverse operation.

6. **Generate Safety Report & Remediation Code**
   - Produce a structured audit report with detected violations and exact zero-downtime refactored Alembic migration code.

# Failure Modes

| Failure | Behavior |
| :--- | :--- |
| Migration file contains syntax errors or unparseable code | Halt analysis and report the specific syntax error and line number to the developer before proceeding. |
| Migration runs exclusively on a freshly created table in the same revision | Allow standard (non-concurrent) index and foreign key creation since the new table has zero traffic and zero rows. |
| Foreign key references a table whose indexes cannot be resolved statically | Emit a warning and require the developer to confirm index presence on the child column before approval. |
| Developer requests bypassing safety checks for offline maintenance | Require an explicit inline override comment `# safety-verifier: ignore=<rule_id>` with justification. |

# Output Contract

- Safety Audit Report detailing detected locking risks, unindexed foreign keys, and missing timeouts.
- Zero-downtime refactored Python Alembic migration snippet.
- Safe rollback verification instructions (`alembic upgrade head && alembic downgrade <rev> && alembic upgrade head`).

# References

- [PostgreSQL & Alembic Failure Taxonomy & Mitigation Catalog](../dataops-skill-improver/assets/postgres_alembic_taxonomy.md)
- [Zero-Downtime Migration Safety Rules](assets/safety_rules.md)
