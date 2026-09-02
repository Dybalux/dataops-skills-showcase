# Zero-Downtime Migration Safety Rules for PostgreSQL & Alembic

This reference outlines the static verification rules enforced by the `dataops-migration-safety-verifier` skill to ensure database schema migrations run safely in production without causing table lockouts or connection pool exhaustion.

---

## Rule 1: Mandatory Lock Timeout (RULE-LOCK-001)

### The Hazard
PostgreSQL DDL statements wait indefinitely for existing transactions to finish while queueing incoming transactions behind their `ACCESS EXCLUSIVE` lock request. This causes connection pool exhaustion in seconds.

### The Standard
All DDL migration scripts must set a short lock timeout:
```python
op.execute("SET LOCAL lock_timeout = '2s';")
```

---

## Rule 2: Non-Blocking Foreign Keys (RULE-FK-002)

### The Hazard
Standard `ALTER TABLE ... ADD CONSTRAINT ... FOREIGN KEY` acquires an `ACCESS EXCLUSIVE` lock and performs a full table validation scan, blocking all reads and writes for the duration of the scan.

### The Standard
1. Add the foreign key with `postgresql_not_valid=True`:
   ```python
   op.create_foreign_key(
       "fk_orders_customer_id",
       "orders",
       "customers",
       ["customer_id"],
       ["id"],
       postgresql_not_valid=True,
   )
   ```
2. Validate the constraint in a separate non-blocking statement:
   ```python
   # Re-issue lock_timeout if autocommit_block() was used previously, or set at session level
   op.execute("SET LOCAL lock_timeout = '2s';")
   op.execute("ALTER TABLE orders VALIDATE CONSTRAINT fk_orders_customer_id;")
   ```

---

## Rule 3: Indexed Foreign Key Columns (RULE-FK-003)

### The Hazard
When a row in the parent table (`customers`) is updated or deleted, PostgreSQL must verify the child table (`orders`). Without an index on `orders.customer_id`, PostgreSQL performs a sequential scan on `orders` while holding a share lock, killing database performance.

### The Standard
Ensure a dedicated or prefix B-Tree index exists on the child table's foreign key column:
```python
with op.get_context().autocommit_block():
    op.create_index(
        "ix_orders_customer_id",
        "orders",
        ["customer_id"],
        postgresql_concurrently=True,
    )
```

---

## Rule 4: Concurrent Index Creation & Dropping (RULE-IDX-004)

### The Hazard
Standard `CREATE INDEX` and `DROP INDEX` take `SHARE` and `ACCESS EXCLUSIVE` locks respectively, blocking table writes.

### The Standard
Always use concurrent index operations inside an `autocommit_block()`:
```python
with op.get_context().autocommit_block():
    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
        postgresql_concurrently=True,
    )
```

---

## Rule 5: Non-Blocking Column Additions (RULE-COL-005)

### The Hazard
Adding columns with non-constant default expressions or `NOT NULL` without defaults on PostgreSQL < 11 causes a full table rewrite.

### The Standard
Add column as nullable, backfill values in background worker batches, and set `NOT NULL` with a separate validated check constraint or alter column step.
