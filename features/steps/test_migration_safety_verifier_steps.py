from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

scenarios("../migration_safety_verifier.feature")


def analyze_migration_safety(migration_code: str, rules_content: str) -> dict:
    """Statically analyze Alembic migration code against zero-downtime safety rules."""
    violations = []
    
    # RULE-LOCK-001: Mandatory Lock Timeout
    if "lock_timeout" not in migration_code:
        violations.append({
            "rule_id": "RULE-LOCK-001",
            "name": "Mandatory Lock Timeout",
            "message": "Migration contains DDL but does not configure lock_timeout",
            "severity": "CRITICAL"
        })
        
    # RULE-FK-002: Non-Blocking Foreign Keys
    if "create_foreign_key" in migration_code:
        if "postgresql_not_valid=True" not in migration_code:
            violations.append({
                "rule_id": "RULE-FK-002",
                "name": "Non-Blocking Foreign Keys",
                "message": "Foreign key created without postgresql_not_valid=True",
                "severity": "CRITICAL"
            })
            
    # RULE-FK-003: Indexed Foreign Key Columns
    if "create_foreign_key" in migration_code:
        has_index = "create_index" in migration_code
        if not has_index:
            violations.append({
                "rule_id": "RULE-FK-003",
                "name": "Indexed Foreign Key Columns",
                "message": "Foreign key column lacks companion index creation",
                "severity": "WARNING"
            })

    # RULE-IDX-004: Concurrent Index Creation
    if "create_index" in migration_code:
        if "postgresql_concurrently=True" not in migration_code or "autocommit_block" not in migration_code:
            violations.append({
                "rule_id": "RULE-IDX-004",
                "name": "Concurrent Index Creation",
                "message": "Index created without postgresql_concurrently=True or autocommit_block",
                "severity": "CRITICAL"
            })

    # Ensure all reported rule IDs are actively documented in the safety rules asset
    for v in violations:
        assert f"({v['rule_id']})" in rules_content, (
            f"Rule {v['rule_id']} reported by verifier but missing from safety_rules.md asset"
        )

    return {
        "violations": violations,
        "is_approved": len(violations) == 0,
        "violation_count": len(violations)
    }


@pytest.fixture
def safety_verifier():
    rules_file = Path(".claude/skills/dataops-migration-safety-verifier/assets/safety_rules.md")
    assert rules_file.exists(), f"Safety rules asset missing: {rules_file}"
    content = rules_file.read_text(encoding="utf-8")
    return {
        "rules_content": content,
        "migration_code": None,
        "analysis_result": None
    }


@given(parsers.parse('an unsafe Alembic migration script containing "{func}" without "{arg}"'))
def ingest_unsafe_migration(safety_verifier: dict, func: str, arg: str):
    unsafe_code = """
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
"""
    safety_verifier["migration_code"] = unsafe_code


@given(parsers.parse('a compliant zero-downtime Alembic migration with "{item1}", "{item2}", and companion concurrent index'))
def ingest_compliant_migration(safety_verifier: dict, item1: str, item2: str):
    compliant_code = """
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '2s';")
    op.create_foreign_key(
        "fk_orders_customer_id",
        "orders",
        "customers",
        ["customer_id"],
        ["id"],
        postgresql_not_valid=True,
    )
    with op.get_context().autocommit_block():
        op.create_index(
            "ix_orders_customer_id",
            "orders",
            ["customer_id"],
            postgresql_concurrently=True,
        )
    op.execute("ALTER TABLE orders VALIDATE CONSTRAINT fk_orders_customer_id;")

def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '2s';")
    op.drop_constraint("fk_orders_customer_id", "orders", type_="foreignkey")
    with op.get_context().autocommit_block():
        op.drop_index("ix_orders_customer_id", table_name="orders", postgresql_concurrently=True)
"""
    safety_verifier["migration_code"] = compliant_code


@given(parsers.parse('an unsafe Alembic migration script containing standard "{func}" without "{arg}"'))
def ingest_unsafe_index_migration(safety_verifier: dict, func: str, arg: str):
    unsafe_code = """
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '2s';")
    op.create_index(
        "ix_orders_order_date",
        "orders",
        ["order_date"],
    )

def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '2s';")
    op.drop_index("ix_orders_order_date", table_name="orders")
"""
    safety_verifier["migration_code"] = unsafe_code


@when("the migration safety verifier analyzes the migration")
def run_static_analysis(safety_verifier: dict):
    code = safety_verifier["migration_code"]
    rules_text = safety_verifier["rules_content"]
    safety_verifier["analysis_result"] = analyze_migration_safety(code, rules_text)


@then(parsers.parse('the verifier reports a violation for rule "{rule_id}"'))
def assert_rule_violation(safety_verifier: dict, rule_id: str):
    result = safety_verifier["analysis_result"]
    matched = [v for v in result["violations"] if v["rule_id"] == rule_id]
    assert len(matched) > 0, f"Expected violation for {rule_id}, got {result['violations']}"


@then(parsers.parse('the verifier flags the foreign key column as requiring an index under "{rule_id}"'))
def assert_index_required(safety_verifier: dict, rule_id: str):
    result = safety_verifier["analysis_result"]
    matched = [v for v in result["violations"] if v["rule_id"] == rule_id]
    assert len(matched) > 0, f"Expected index violation for {rule_id}, got {result['violations']}"


@then(parsers.parse('the verifier reports {count:d} safety violations'))
def assert_violation_count(safety_verifier: dict, count: int):
    result = safety_verifier["analysis_result"]
    assert result["violation_count"] == count, f"Expected {count} violations, got {result['violation_count']}: {result['violations']}"


@then("the migration is approved for zero-downtime deployment")
def assert_migration_approved(safety_verifier: dict):
    result = safety_verifier["analysis_result"]
    assert result["is_approved"] is True, "Migration should be approved for zero-downtime deployment"
