# dataops-migration-safety-verifier — Execution Evidence

**Date**: 2026-08-30  
**Target Revision**: `alembic/versions/demo_add_unindexed_fk.py`  
**Violations Detected**: `RULE-LOCK-001`, `RULE-FK-002`, `RULE-FK-003`

---

## 1. Raw Ingested Migration Code (Unsafe)

```python
"""add_orders_customer_fk

Revision ID: 4c9a8b12de34
Revises: 1a2b3c4d5e6f
Create Date: 2026-08-30 22:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    op.create_foreign_key(
        "fk_orders_customer_id",
        "orders",
        "customers",
        ["customer_id"],
        ["id"],
    )

def downgrade() -> None:
    op.drop_constraint("fk_orders_customer_id", "orders", type_="foreignkey")
```

---

## 2. Static Safety Analysis Report

```text
[CRITICAL] RULE-LOCK-001: Missing mandatory lock_timeout configuration.
  -> Impact: DDL will wait indefinitely behind long queries, blocking all inbound traffic.
  -> Remediation: Prepend upgrade() with op.execute("SET LOCAL lock_timeout = '2s';").

[CRITICAL] RULE-FK-002: Foreign key added without postgresql_not_valid=True.
  -> Impact: Full table scan with ACCESS EXCLUSIVE lock on 'orders'.
  -> Remediation: Set postgresql_not_valid=True and validate in a separate statement.

[WARNING] RULE-FK-003: Foreign key column 'orders.customer_id' lacks an index.
  -> Impact: Deletes/updates on 'customers' table will trigger sequential scans on 'orders'.
  -> Remediation: Create concurrent B-Tree index 'ix_orders_customer_id' in autocommit_block().
```

---

## 3. Zero-Downtime Refactored Migration

```python
"""add_orders_customer_fk (Zero-Downtime Safe)

Revision ID: 4c9a8b12de34
Revises: 1a2b3c4d5e6f
Create Date: 2026-08-30 22:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # 1. Safety lock timeout
    op.execute("SET LOCAL lock_timeout = '2s';")

    # 2. Add Foreign Key without locking existing rows
    op.create_foreign_key(
        "fk_orders_customer_id",
        "orders",
        "customers",
        ["customer_id"],
        ["id"],
        postgresql_not_valid=True,
    )

    # 3. Create supporting index concurrently
    with op.get_context().autocommit_block():
        op.create_index(
            "ix_orders_customer_id",
            "orders",
            ["customer_id"],
            postgresql_concurrently=True,
        )

    # 4. Validate foreign key constraint concurrently
    op.execute("ALTER TABLE orders VALIDATE CONSTRAINT fk_orders_customer_id;")

def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '2s';")
    op.drop_constraint("fk_orders_customer_id", "orders", type_="foreignkey")
    with op.get_context().autocommit_block():
        op.drop_index("ix_orders_customer_id", table_name="orders", postgresql_concurrently=True)
```

---

## 4. Automated Verification

Executed BDD scenario in `features/migration_safety_verifier.feature`:
- `test_detect_unsafe_foreign_key_and_missing_lock_timeout` -> **PASSED**
- `test_generate_zero_downtime_two_phase_migration` -> **PASSED**
