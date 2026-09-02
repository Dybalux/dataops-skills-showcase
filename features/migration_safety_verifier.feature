Feature: Zero-Downtime Migration Safety Verifier
  As a DataOps Lead and Senior Architect
  I want to statically analyze Alembic migration files for DDL table locking hazards and unindexed foreign keys
  So that schema changes deploy to staging and production with zero downtime

  Scenario: Detect unsafe foreign key and missing lock timeout in migration
    Given an unsafe Alembic migration script containing "op.create_foreign_key" without "postgresql_not_valid=True"
    When the migration safety verifier analyzes the migration
    Then the verifier reports a violation for rule "RULE-LOCK-001"
    And the verifier reports a violation for rule "RULE-FK-002"
    And the verifier flags the foreign key column as requiring an index under "RULE-FK-003"

  Scenario: Verify zero-downtime two-phase migration is fully compliant
    Given a compliant zero-downtime Alembic migration with "lock_timeout", "postgresql_not_valid=True", and companion concurrent index
    When the migration safety verifier analyzes the migration
    Then the verifier reports 0 safety violations
    And the migration is approved for zero-downtime deployment

  Scenario: Detect non-concurrent index creation on existing table
    Given an unsafe Alembic migration script containing standard "op.create_index" without "postgresql_concurrently=True"
    When the migration safety verifier analyzes the migration
    Then the verifier reports a violation for rule "RULE-IDX-004"
